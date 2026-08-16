import json
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agents.scope import resolve_scope
from app.models.agent import AgentRun, ToolCall
from app.models.common import utc_now
from app.models.communication import Message
from app.models.organization import Project
from app.providers.text import get_text_provider
from app.repositories.communication import list_messages
from app.schemas.agent import AgentRunRead, ToolCallRead
from app.schemas.communication import MessageRead
from app.schemas.tools import SalesMetricsOutput, SalesTrendOutput
from app.services.communication import create_user_message, require_conversation_access
from app.skills.selection import render_selection_analysis, run_selection_workflow
from app.tools.registry import ToolExecutionContext, ToolRunner

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = {
    "artwork": "你是美工工作流助手，只解释图片版本与编辑状态。",
    "sales": "你是销售分析助手，只依据受控工具结果解释销售数据。",
    "selection": "你是选品助手，只依据受控工具和确定性规则解释结果。",
}


def _tool_call_read(call: ToolCall) -> ToolCallRead:
    return ToolCallRead(
        id=call.id,
        tool_name=call.tool_name,
        input=json.loads(call.input_json),
        output_summary=json.loads(call.output_summary_json) if call.output_summary_json else None,
        status=call.status,
        duration_ms=call.duration_ms,
        error_message=call.error_message,
        created_at=call.created_at,
    )


def _message_read(message: Message) -> MessageRead:
    return MessageRead(
        id=message.id,
        conversation_id=message.conversation_id,
        user_id=message.user_id,
        role=message.role,
        content=message.content,
        metadata_json=message.metadata_json,
        created_at=message.created_at,
    )


def run_to_read(run: AgentRun, assistant: Message | None = None) -> AgentRunRead:
    return AgentRunRead(
        id=run.id,
        department_id=run.department_id,
        user_id=run.user_id,
        project_id=run.project_id,
        conversation_id=run.conversation_id,
        provider=run.provider,
        model_name=run.model_name,
        status=run.status,
        input_summary=run.input_summary,
        output_summary=run.output_summary,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
        assistant_message=_message_read(assistant) if assistant else None,
        tool_calls=[_tool_call_read(call) for call in run.tool_calls],
    )


def run_basic_agent(
    session: Session, conversation_id: str, user_id: str, content: str
) -> AgentRunRead:
    conversation = require_conversation_access(session, conversation_id, user_id)
    project_record = session.get(Project, conversation.project_id)
    if not project_record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    department = project_record.department
    provider = get_text_provider()
    create_user_message(session, conversation_id, user_id, content)

    run = AgentRun(
        department_id=department.id,
        user_id=user_id,
        project_id=project_record.id,
        conversation_id=conversation_id,
        provider=provider.name,
        model_name=provider.model_name,
        status="running",
        input_summary=content[:1000],
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    try:
        try:
            previous_scope = json.loads(project_record.structured_scope_json)
        except json.JSONDecodeError:
            previous_scope = {}
        scope = resolve_scope(content, previous_scope)
        project_record.structured_scope_json = json.dumps(scope, ensure_ascii=False)
        runner = ToolRunner(
            ToolExecutionContext(
                session=session,
                agent_run_id=run.id,
                conversation_id=conversation_id,
                project_id=project_record.id,
            )
        )
        outputs: list[tuple[str, dict]] = []
        selection_analysis = None
        if department.code == "selection":
            selection_analysis, outputs = run_selection_workflow(runner, scope)
        elif department.code == "sales":
            sales = runner.run(
                "query_sales_metrics",
                {
                    "site": scope["site"],
                    "platform": scope["platform"],
                    "start_date": scope["start_date"],
                    "end_date": scope["end_date"],
                    "category": scope.get("category"),
                    "product_name": scope.get("product_name"),
                    "granularity": "month",
                },
            )
            outputs.append(("query_sales_metrics", sales.model_dump(mode="json")))
            sales_output = SalesMetricsOutput.model_validate(sales)
            if len(sales_output.series) >= 2:
                trend = runner.run(
                    "calculate_sales_trend",
                    {"series": [item.model_dump() for item in sales_output.series]},
                )
                outputs.append(("calculate_sales_trend", trend.model_dump(mode="json")))

        history = list_messages(session, conversation_id, 10)
        provider_text = provider.generate(
            [
                {"role": "system", "content": SYSTEM_PROMPTS[department.code]},
                {
                    "role": "system",
                    "content": f"项目摘要：{project_record.summary or '暂无'}",
                },
                {
                    "role": "system",
                    "content": f"当前结构化范围：{json.dumps(scope, ensure_ascii=False)}",
                },
                *[{"role": item.role, "content": item.content} for item in history],
                {
                    "role": "system",
                    "content": f"最新工具结果：{json.dumps(outputs, ensure_ascii=False)}",
                },
            ]
        )
        details = []
        sales_data = next((value for name, value in outputs if name == "query_sales_metrics"), None)
        trend_data = next(
            (value for name, value in outputs if name == "calculate_sales_trend"), None
        )
        if sales_data:
            details.append(
                f"数据范围：{scope['start_date']} 至 {scope['end_date']}，"
                f"销量 {sales_data['units_sold']}，销售额 ${sales_data['revenue']:,.2f}，"
                f"毛利率 {sales_data['gross_margin_rate']:.1%}，"
                f"退款率 {sales_data['refund_rate']:.1%}。"
            )
        if trend_data:
            validated_trend = SalesTrendOutput.model_validate(trend_data)
            details.append(
                f"趋势：{validated_trend.direction}，"
                f"最近环比 {validated_trend.latest_mom_rate:.1%}。"
            )
        if selection_analysis:
            details = [render_selection_analysis(selection_analysis)]
        answer = provider_text + ("\n\n" + "\n".join(details) if details else "")

        for tool_name, output in outputs:
            session.add(
                Message(
                    conversation_id=conversation_id,
                    role="tool",
                    content=json.dumps(output, ensure_ascii=False),
                    metadata_json=json.dumps({"tool_name": tool_name}, ensure_ascii=False),
                )
            )
        assistant = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            metadata_json=json.dumps({"agent_run_id": run.id}, ensure_ascii=False),
        )
        session.add(assistant)
        run.status = "completed"
        run.output_summary = answer[:2000]
        run.completed_at = utc_now()
        project_record.summary = answer[:1000]
        conversation.updated_at = utc_now()
        session.commit()
        session.refresh(run)
        session.refresh(assistant)
        logger.info(
            "agent_run run_id=%s department=%s status=completed tool_count=%s",
            run.id,
            department.code,
            len(run.tool_calls),
        )
        return run_to_read(run, assistant)
    except Exception as error:
        session.rollback()
        failed_run = session.get(AgentRun, run.id)
        if failed_run:
            failed_run.status = "failed"
            failed_run.error_message = str(error)[:1000]
            failed_run.completed_at = utc_now()
            session.commit()
            logger.exception(
                "agent_run run_id=%s department=%s status=failed",
                failed_run.id,
                department.code,
            )
        raise
