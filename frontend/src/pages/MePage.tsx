import { ChevronRight, Dumbbell, RotateCcw, Settings2, ShieldCheck } from "lucide-react";
import { Link } from "react-router";
import { AppShell, Buddy, PageHeader } from "../components";
import { actionCards } from "../mocks/data";
import { useAppStore } from "../store";

export function MePage() {
  const sessions = useAppStore((state) => state.sessions);
  const collected = useAppStore((state) => state.collectedCardIds);
  const resetDemo = useAppStore((state) => state.resetDemo);
  const completedItems = sessions.flatMap((session) => session.items).filter((item) => item.state === "COMPLETED");
  const discomfortItems = sessions.flatMap((session) => session.items).filter((item) => item.state === "STOPPED_DISCOMFORT");
  const latest = completedItems[0];
  return (
    <AppShell>
      <main className="page">
        <PageHeader title="我的" action={<button className="icon-button" aria-label="设置"><Settings2 size={20} /></button>} />
        <p className="eyebrow">真实完成，比完美记录更重要</p>
        <h1>我的</h1>
        <section className="section hero-panel">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 118px", alignItems: "center", gap: 8 }}>
            <div>
              <span className="chip chip--accent">我的健身搭子</span>
              <h2 style={{ marginTop: 12 }}>小练</h2>
              <p>{latest ? `最近记住了你的${actionCards[latest.cardId]?.actionCard.bodyRegion ?? "训练"}记录。` : "完成第一次训练后，我会记住你练过的部位。"}</p>
            </div>
            <div className="buddy-orbit" style={{ width: 112, height: 112, margin: 0 }}><Buddy highlighted={Boolean(latest)} /></div>
          </div>
        </section>

        <section className="section">
          <div className="section-heading"><h2>我的记录</h2></div>
          <div className="surface" style={{ padding: "4px 18px" }}>
            <div className="summary-row"><span>累计练过动作</span><strong>{completedItems.length}</strong></div>
            <div className="summary-row"><span>收藏动作卡</span><strong>{collected.length}</strong></div>
            <div className="summary-row"><span>完成训练次数</span><strong>{sessions.filter((session) => session.status === "COMPLETED").length}</strong></div>
          </div>
        </section>

        <section className="section">
          <div className="section-heading"><h2>最近练过</h2></div>
          <div className="surface" style={{ padding: "0 18px" }}>
            {completedItems.length ? completedItems.slice(0, 4).map((item) => (
              <Link className="summary-row" key={item.id} to={`/cards/${item.cardId}`}>
                <span><strong>{actionCards[item.cardId]?.actionCard.actionName}</strong><br /><small className="muted">{actionCards[item.cardId]?.actionCard.primaryMuscles.join("、")}</small></span>
                <ChevronRight size={18} />
              </Link>
            )) : <div className="empty-state" style={{ minHeight: 150 }}><div><Dumbbell size={25} /><p className="muted">完成训练后，动作记录会出现在这里。</p></div></div>}
          </div>
        </section>

        {discomfortItems.length ? (
          <section className="section error-box">
            <ShieldCheck size={22} color="var(--danger)" />
            <h3 style={{ marginTop: 8 }}>不适记录</h3>
            <p className="muted">有 {discomfortItems.length} 个动作已暂停主动推荐，可在后续设置中明确恢复。</p>
          </section>
        ) : null}

        <section className="section">
          <button className="button button--neutral button--wide" onClick={() => {
            if (window.confirm("确定重置演示数据吗？练单和训练记录会恢复为初始状态。")) resetDemo();
          }}><RotateCcw size={17} />重置 Demo 数据</button>
          <p className="muted" style={{ textAlign: "center", fontSize: ".72rem" }}>仅用于 Hackathon 演示与调试</p>
        </section>
      </main>
    </AppShell>
  );
}
