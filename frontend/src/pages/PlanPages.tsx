import * as Dialog from "@radix-ui/react-dialog";
import {
  ArrowDown,
  ArrowUp,
  ChevronRight,
  Dumbbell,
  Lightbulb,
  Play,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";
import { useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { createActionCardIndex } from "../action-card-index";
import { useActionCards, useRecommendations } from "../api";
import { AppShell, PageHeader } from "../components";
import { useAppStore } from "../store";

function useCardMap() {
  const { data: cards = [] } = useActionCards();
  return useMemo(() => createActionCardIndex(cards), [cards]);
}

export function PlansPage() {
  const plans = useAppStore((state) => state.plans);
  const sessions = useAppStore((state) => state.sessions);
  const createPlan = useAppStore((state) => state.createPlan);
  const deletePlan = useAppStore((state) => state.deletePlan);
  const startSession = useAppStore((state) => state.startSession);
  const cardsById = useCardMap();
  const navigate = useNavigate();
  const activeSession = sessions.find((session) => session.status === "IN_PROGRESS");
  const create = async () => {
    const planId = await createPlan();
    navigate(`/plans/${planId}`);
  };
  const start = async (planId: string) => {
    const sessionId = await startSession(planId);
    if (sessionId) navigate(`/train/${sessionId}`);
  };
  return (
    <AppShell>
      <main className="page">
        <PageHeader title="练单" />
        <div className="hero-panel">
          <p className="eyebrow">把收藏真正练起来</p>
          <h1>今天，想练哪里？</h1>
          <p>自己挑动作，练单助手只给少量候选，最后由你决定。</p>
          <button className="button button--primary" onClick={() => void create()}><Plus size={18} />新建练单</button>
        </div>

        {activeSession ? (
          <section className="section notice">
            <span className="chip chip--warm">训练进行中</span>
            <h3 style={{ marginTop: 10 }}>{activeSession.planName}</h3>
            <p className="muted">已完成 {activeSession.items.filter((item) => item.state === "COMPLETED").length} / {activeSession.items.length}，进度已经保存。</p>
            <Link className="button button--primary" to={`/train/${activeSession.id}`}><Play size={17} />继续训练</Link>
          </section>
        ) : null}

        <section className="section">
          <div className="section-heading"><div><h2>我的练单</h2><p className="muted">保存后可以反复使用</p></div><span className="chip">{plans.length} 份</span></div>
          {plans.length === 0 ? (
            <div className="surface empty-state"><div><Dumbbell size={28} /><h3>还没有保存的练单</h3><p className="muted">新建一份，把想练的视频动作卡放进去。</p><button className="button button--primary" onClick={() => void create()}>新建练单</button></div></div>
          ) : (
            plans.map((plan) => (
              <article className="surface plan-card" key={plan.id}>
                <div className="plan-card__header">
                  <Link to={`/plans/${plan.id}`}><h3>{plan.name}</h3></Link>
                  <DeletePlanDialog planName={plan.name} onDelete={() => deletePlan(plan.id)} />
                </div>
                <div className="plan-card__meta"><span>{plan.cardIds.length} 个动作</span><span>使用 {plan.useCount} 次</span></div>
                <div className="chip-row">
                  {plan.cardIds.slice(0, 3).map((cardId) => <span className="chip" key={cardId}>{cardsById.get(cardId)?.actionCard.actionName ?? "待同步动作"}</span>)}
                </div>
                <div className="button-row" style={{ marginTop: 16 }}>
                  <Link className="button button--neutral" to={`/plans/${plan.id}`}>查看练单</Link>
                  <button className="button button--primary" disabled={!plan.cardIds.length} onClick={() => void start(plan.id)}><Play size={17} />开始</button>
                </div>
              </article>
            ))
          )}
        </section>
      </main>
    </AppShell>
  );
}

function DeletePlanDialog({ planName, onDelete }: { planName: string; onDelete: () => void | Promise<void> }) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className="mini-button plan-delete-button" aria-label={`删除练单${planName}`}><span aria-hidden="true"><Trash2 size={15} /></span></button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content" aria-describedby="delete-plan-description">
          <div className="dialog-handle" />
          <Dialog.Title asChild><h2>删除“{planName}”？</h2></Dialog.Title>
          <p className="muted" id="delete-plan-description">练单会从当前列表归档，已有训练记录会保留。</p>
          <div className="button-row" style={{ marginTop: 20 }}>
            <Dialog.Close asChild><button className="button button--neutral">取消</button></Dialog.Close>
            <Dialog.Close asChild><button className="button button--danger" onClick={() => void onDelete()}><Trash2 size={17} />确认删除</button></Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function PlanDetailPage() {
  const { planId = "" } = useParams();
  const plan = useAppStore((state) => state.plans.find((candidate) => candidate.id === planId));
  const renamePlan = useAppStore((state) => state.renamePlan);
  const removeCard = useAppStore((state) => state.removeCardFromPlan);
  const moveCard = useAppStore((state) => state.moveCard);
  const addCard = useAppStore((state) => state.addCardToPlan);
  const markUninterested = useAppStore((state) => state.markUninterested);
  const uninterested = useAppStore((state) => state.uninterestedCardIds);
  const startSession = useAppStore((state) => state.startSession);
  const cardsById = useCardMap();
  const { data: recommendationItems = [] } = useRecommendations(planId);
  const navigate = useNavigate();
  if (!plan) return <MissingPlan />;

  const cards = plan.cardIds.map((id) => cardsById.get(id)).filter((response) => response !== undefined);
  const primary = [...new Set(cards.flatMap((response) => response.actionCard.primaryMuscles))];
  const candidates = recommendationItems.filter(({ cardId }) => !plan.cardIds.includes(cardId) && !uninterested.includes(cardId));
  const start = async () => {
    const sessionId = await startSession(plan.id);
    if (sessionId) navigate(`/train/${sessionId}`);
  };
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="练单详情" back action={<span className="chip chip--accent"><Save size={13} />已保存</span>} />
        <div className="plan-name-field">
          <label className="eyebrow" htmlFor="plan-name">练单名称</label>
          <input
            id="plan-name"
            className="search-input plan-name-input"
            defaultValue={plan.name}
            onBlur={(event) => void renamePlan(plan.id, event.target.value)}
          />
          <p className="muted">{plan.cardIds.length} 个动作 · 已使用 {plan.useCount} 次</p>
        </div>

        <section className="muscle-coverage-summary section" aria-label={`肌群覆盖 ${primary.length ? primary.join("、") : "等待添加动作"}`}>
          <small>肌群覆盖</small>
          <strong>{primary.length ? primary.join("、") : "等待添加动作"}</strong>
        </section>

        <section className="section">
          <div className="section-heading"><div><h2>动作顺序</h2><p className="muted">支持上移、下移和删除</p></div><span className="chip">{plan.cardIds.length}</span></div>
          <div className="surface" style={{ padding: "0 15px" }}>
            {plan.cardIds.length ? plan.cardIds.map((cardId, index) => {
              const response = cardsById.get(cardId);
              if (!response) return null;
              return (
                <div className="plan-item" key={cardId}>
                  <span className="step-number">{index + 1}</span>
                  <Link className="list-card__content" to={`/cards/${cardId}`}>
                    <strong>{response.actionCard.actionName}</strong>
                    <p>{response.actionCard.sourceVideo.creatorName}</p>
                  </Link>
                  <div className="plan-item__actions">
                    <button className="mini-button" aria-label="上移" disabled={index === 0} onClick={() => void moveCard(plan.id, cardId, -1)}><ArrowUp size={16} /></button>
                    <button className="mini-button" aria-label="下移" disabled={index === plan.cardIds.length - 1} onClick={() => void moveCard(plan.id, cardId, 1)}><ArrowDown size={16} /></button>
                    <button className="mini-button" aria-label="移除" onClick={() => void removeCard(plan.id, cardId)}><Trash2 size={16} /></button>
                  </div>
                </div>
              );
            }) : (
              <div className="empty-state" style={{ minHeight: 190 }}><div><h3>练单还是空的</h3><p className="muted">加入一个动作就可以开始训练。</p></div></div>
            )}
          </div>
          <Link className="button button--soft button--wide" style={{ marginTop: 10 }} to={`/plans/${plan.id}/select`}><Plus size={17} />添加动作</Link>
        </section>

        {plan.cardIds.length ? (
          <details className="compact-disclosure section plan-assistant" open>
            <summary>
              <span className="plan-assistant__title"><Lightbulb size={18} /><span><small>练单助手</small><strong>接下来可以考虑 {candidates.length} 个动作</strong></span></span>
              <ChevronRight size={18} />
            </summary>
            <div className="compact-disclosure__body">
              {candidates.length ? candidates.map(({ cardId, response, reason }) => {
                const card = response.actionCard;
                return (
                  <div className="recommendation" key={cardId}>
                    <Link to={`/cards/${cardId}`}><strong>{card.actionName}</strong><div className="muted" style={{ fontSize: ".78rem", marginTop: 3 }}>{card.sourceVideo.creatorName} · {card.primaryMuscles.join("、")}</div></Link>
                    <div className="recommendation__reason"><Lightbulb size={14} />{reason}</div>
                    <div className="button-row">
                      <button className="button button--neutral" onClick={() => markUninterested(cardId)}><X size={16} />不感兴趣</button>
                      <button className="button button--soft" onClick={() => void addCard(plan.id, cardId)}><Plus size={16} />加入</button>
                    </div>
                  </div>
                );
              }) : <p className="muted" style={{ padding: "16px 0" }}>暂时没有更合适的候选，你可以从动作库继续添加。</p>}
            </div>
          </details>
        ) : null}

        <div className="sticky-actions">
          <button className="button button--primary button--wide" onClick={() => void start()} disabled={!plan.cardIds.length}><Play size={19} />开始训练</button>
        </div>
      </main>
    </AppShell>
  );
}

export function SelectActionPage() {
  const { planId = "" } = useParams();
  const plan = useAppStore((state) => state.plans.find((candidate) => candidate.id === planId));
  const addCard = useAppStore((state) => state.addCardToPlan);
  const { data: cards = [] } = useActionCards();
  const navigate = useNavigate();
  if (!plan) return <MissingPlan />;
  const add = async (cardId: string) => {
    await addCard(planId, cardId);
    navigate(`/plans/${planId}`);
  };
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="选择动作" back />
        <p className="eyebrow">加入 {plan.name}</p>
        <h1>选一张视频动作卡</h1>
        <p className="muted">同一个标准动作也可能有不同创作者的讲法，加入的是具体视频卡。</p>
        <div className="chip-row" style={{ marginTop: 18 }}><span className="chip chip--accent">肩部</span><span className="chip chip--accent">背部</span><span className="chip">全部</span></div>
        <section className="section surface" style={{ padding: "0 16px" }}>
          {cards.map((response) => {
            const card = response.actionCard;
            const added = plan.cardIds.includes(card.sourceVideo.videoId);
            return (
              <div className="list-card" key={card.sourceVideo.videoId}>
                <div className="list-card__media"><Dumbbell size={22} /></div>
                <Link className="list-card__content" to={`/cards/${card.sourceVideo.videoId}`}>
                  <strong>{card.actionName}</strong><p>{card.sourceVideo.creatorName} · {card.primaryMuscles.join("、")}</p>
                </Link>
                <button className={`button ${added ? "button--neutral" : "button--soft"}`} style={{ minHeight: 40, padding: "0 12px" }} disabled={added} onClick={() => void add(card.sourceVideo.videoId)}>
                  {added ? "已加入" : "加入"}
                </button>
              </div>
            );
          })}
        </section>
      </main>
    </AppShell>
  );
}

function MissingPlan() {
  return (
    <AppShell navigation={false}><main className="page page--immersive"><PageHeader title="练单不存在" back /><div className="empty-state"><div><h2>没有找到这份练单</h2><p className="muted">它可能已经被删除。</p><Link className="button button--primary" to="/plans">返回练单</Link></div></div></main></AppShell>
  );
}
