import { useEffect, useState } from "react";

import { fetchSelectionOverview } from "../api/selection";
import type { DemoUser, Project } from "../types/domain";
import type { SelectionAnalysis } from "../types/selection";

const products = ["龙门架", "跑步机", "哑铃", "健身凳", "拉力器"];

type SelectionOverviewProps = {
  project: Project;
  currentUser: DemoUser;
};

export function SelectionOverview({ project, currentUser }: SelectionOverviewProps) {
  const [productName, setProductName] = useState("龙门架");
  const [analysis, setAnalysis] = useState<SelectionAnalysis | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setAnalysis(null);
    setError("");
    void fetchSelectionOverview(project.id, currentUser.id, productName)
      .then(setAnalysis)
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "选品概览加载失败");
      });
  }, [currentUser.id, productName, project.id]);

  return (
    <section className="import-workspace selection-overview">
      <header className="import-heading">
        <div>
          <p className="kicker">DETERMINISTIC RESTOCK SKILL</p>
          <h1>选品决策概览</h1>
          <p>销售与库存指标和 Agent 共用同一后端计算服务。</p>
        </div>
        <label className="overview-picker">
          商品
          <select value={productName} onChange={(event) => setProductName(event.target.value)}>
            {products.map((product) => <option key={product}>{product}</option>)}
          </select>
        </label>
      </header>

      {error && <div className="inline-notice error-notice">{error}</div>}
      {!analysis && !error && <div className="inline-notice">正在通过受控指标服务计算…</div>}
      {analysis && (
        <>
          <div className="import-stats selection-stats">
            <div><span>18 个月销量</span><strong>{analysis.sales.units_sold}</strong></div>
            <div><span>毛利率</span><strong>{(analysis.sales.gross_margin_rate * 100).toFixed(1)}%</strong></div>
            <div><span>库存覆盖</span><strong>{analysis.pressure.coverage_days?.toFixed(1) ?? "--"} 天</strong></div>
            <div><span>建议补货</span><strong>{analysis.restock.recommended_quantity} 件</strong></div>
          </div>
          <div className="decision-grid">
            <article>
              <span>确定性建议</span>
              <h2>{analysis.restock.should_restock ? "建议增购" : "暂不增购"}</h2>
              <p>{analysis.restock.rationale}</p>
              <small>{analysis.human_confirmation_notice}</small>
            </article>
            <article>
              <span>风险清单</span>
              {analysis.risks.map((risk) => <p key={risk}>• {risk}</p>)}
            </article>
          </div>
        </>
      )}
    </section>
  );
}
