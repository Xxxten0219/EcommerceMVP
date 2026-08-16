import json
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.agent import ToolCall
from app.models.analytics import ImportBatch
from app.schemas.tools import (
    ImportBatchStatusInput,
    ImportBatchStatusOutput,
    InventoryPressureInput,
    InventoryStatusInput,
    RestockInput,
    SalesMetricsInput,
    SalesTrendInput,
)
from app.services.metrics import (
    calculate_inventory_pressure,
    calculate_sales_trend,
    query_inventory_status,
    query_sales_metrics,
    recommend_restock,
)


@dataclass(frozen=True)
class ToolExecutionContext:
    session: Session
    agent_run_id: str
    conversation_id: str
    project_id: str


@dataclass(frozen=True)
class ToolDefinition:
    input_model: type[BaseModel]
    handler: Callable[[ToolExecutionContext, BaseModel], BaseModel]


def _sales_handler(context: ToolExecutionContext, payload: BaseModel) -> BaseModel:
    return query_sales_metrics(context.session, SalesMetricsInput.model_validate(payload))


def _inventory_handler(context: ToolExecutionContext, payload: BaseModel) -> BaseModel:
    return query_inventory_status(context.session, InventoryStatusInput.model_validate(payload))


def _trend_handler(_: ToolExecutionContext, payload: BaseModel) -> BaseModel:
    return calculate_sales_trend(SalesTrendInput.model_validate(payload))


def _pressure_handler(_: ToolExecutionContext, payload: BaseModel) -> BaseModel:
    return calculate_inventory_pressure(InventoryPressureInput.model_validate(payload))


def _restock_handler(_: ToolExecutionContext, payload: BaseModel) -> BaseModel:
    return recommend_restock(RestockInput.model_validate(payload))


def _import_status_handler(context: ToolExecutionContext, payload: BaseModel) -> BaseModel:
    input_data = ImportBatchStatusInput.model_validate(payload)
    if input_data.project_id != context.project_id:
        raise ValueError("Tool project_id does not match Agent Run project")
    batch = context.session.get(ImportBatch, input_data.batch_id)
    if not batch or batch.project_id != input_data.project_id:
        raise ValueError("Import batch not found in this project")
    return ImportBatchStatusOutput(
        batch_id=batch.id,
        project_id=batch.project_id,
        status=batch.status,
        total_rows=batch.total_rows,
        success_rows=batch.success_rows,
        failed_rows=batch.failed_rows,
        error_message=batch.error_message,
    )


TOOL_REGISTRY = {
    "query_sales_metrics": ToolDefinition(SalesMetricsInput, _sales_handler),
    "query_inventory_status": ToolDefinition(InventoryStatusInput, _inventory_handler),
    "calculate_sales_trend": ToolDefinition(SalesTrendInput, _trend_handler),
    "calculate_inventory_pressure": ToolDefinition(InventoryPressureInput, _pressure_handler),
    "recommend_restock": ToolDefinition(RestockInput, _restock_handler),
    "get_import_batch_status": ToolDefinition(ImportBatchStatusInput, _import_status_handler),
}


class ToolRunner:
    def __init__(self, context: ToolExecutionContext):
        self.context = context

    def run(self, tool_name: str, raw_input: dict) -> BaseModel:
        started = perf_counter()
        call = ToolCall(
            agent_run_id=self.context.agent_run_id,
            conversation_id=self.context.conversation_id,
            tool_name=tool_name,
            input_json=json.dumps(raw_input, ensure_ascii=False, default=str),
            status="running",
        )
        self.context.session.add(call)
        self.context.session.flush()
        try:
            definition = TOOL_REGISTRY.get(tool_name)
            if not definition:
                raise ValueError(f"Tool is not registered: {tool_name}")
            validated = definition.input_model.model_validate(raw_input)
            output = definition.handler(self.context, validated)
            call.status = "succeeded"
            call.output_summary_json = json.dumps(
                output.model_dump(mode="json"), ensure_ascii=False
            )
            return output
        except Exception as error:
            call.status = "failed"
            call.error_message = str(error)[:1000]
            raise
        finally:
            call.duration_ms = max(0, round((perf_counter() - started) * 1000))
            self.context.session.commit()
