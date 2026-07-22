import * as Dialog from "@radix-ui/react-dialog";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  ChevronRight,
  CircleAlert,
  Dumbbell,
  ExternalLink,
  Heart,
  Play,
  ShieldAlert,
  Sparkles,
  ThumbsUp,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import { createActionCardIndex } from "../action-card-index";
import { useActionCard, useActionCards, useExperiences } from "../api";
import {
  ActionCardContent,
  AppShell,
  Buddy,
  Evidence,
  PageHeader,
  sensationOptions,
  TrainingDataView,
} from "../components";
import type { Sensation, TrainingSession } from "../domain";
import { actionCards, getDemoExperience } from "../mocks/data";
import { useAppStore } from "../store";

function sensationLabel(value?: Sensation) {
  return sensationOptions.find((option) => option.value === value)?.label ?? "未记录";
}

function nextOrComplete(
  session: TrainingSession,
  setCurrentIndex: (sessionId: string, index: number) => void,
  completeSession: (sessionId: string) => void,
  navigate: ReturnType<typeof useNavigate>,
) {
  if (session.currentIndex >= session.items.length - 1) {
    completeSession(session.id);
    navigate(`/train/${session.id}/complete`);
    return;
  }
  setCurrentIndex(session.id, session.currentIndex + 1);
}

export function TrainingPage() {
  const { sessionId = "" } = useParams();
  const session = useAppStore((state) => state.sessions.find((candidate) => candidate.id === sessionId));
  const setCurrentIndex = useAppStore((state) => state.setCurrentIndex);
  const skipItem = useAppStore((state) => state.skipItem);
  const submitFeedback = useAppStore((state) => state.submitFeedback);
  const completeSession = useAppStore((state) => state.completeSession);
  const navigate = useNavigate();
  const [sheetOpen, setSheetOpen] = useState(false);
  const [sheetStep, setSheetStep] = useState<"sensation" | "region" | "buddy" | "help">("sensation");
  const [selectedSensation, setSelectedSensation] = useState<Sensation | null>(null);
  const [fullOpen, setFullOpen] = useState(false);

  const item = session?.items[session.currentIndex];
  const { data: response, isPending: isCardPending } = useActionCard(item?.cardId);
  if (!session || isCardPending) return <MissingSession />;
  if (!item || !response) return <MissingSession />;
  const card = response.actionCard;
  const demoExperience = getDemoExperience(response.standardAction.standardActionId);

  const closeSheet = () => {
    setSheetOpen(false);
    setSheetStep("sensation");
    setSelectedSensation(null);
  };
  const advance = () => {
    closeSheet();
    const latestSession = useAppStore.getState().sessions.find((candidate) => candidate.id === session.id);
    if (latestSession?.status === "COMPLETED") navigate(`/train/${session.id}/complete`);
  };
  const chooseSensation = async (value: Sensation) => {
    setSelectedSensation(value);
    if (value === "OTHER_FELT") {
      setSheetStep("region");
      return;
    }
    await submitFeedback(session.id, item.id, value);
    if (value === "DISCOMFORT") {
      closeSheet();
      navigate(`/safety?sessionId=${session.id}&itemId=${item.id}`);
      return;
    }
    setSheetStep(value === "TARGET_FELT" ? "buddy" : "help");
  };
  const chooseRegion = async (region: string) => {
    await submitFeedback(session.id, item.id, "OTHER_FELT", region);
    setSheetStep("help");
  };
  const skip = async () => {
    const atEnd = session.currentIndex >= session.items.length - 1;
    await skipItem(session.id, item.id);
    if (atEnd) {
      completeSession(session.id);
      navigate(`/train/${session.id}/complete`);
    }
  };

  return (
    <AppShell navigation={false}>
      <main className="page page--immersive training-screen">
        <div className="training-header">
          <button className="icon-button" onClick={() => navigate("/plans")} aria-label="保存进度并退出"><X size={20} /></button>
          <div className="training-header__title">
            <strong>{session.planName}</strong>
            <div className="training-header__progress">{session.currentIndex + 1} / {session.items.length}</div>
          </div>
          <span className="chip chip--accent">训练中</span>
        </div>
        <div className="progress-track" aria-label={`训练进度 ${session.currentIndex + 1}/${session.items.length}`}>
          <span style={{ width: `${((session.currentIndex + 1) / session.items.length) * 100}%` }} />
        </div>

        <TrainingDataView
          response={response}
          footerLabel="需要更详细的动作指导？"
          footerAction={(
            <button className="training-details-button" onClick={() => setFullOpen(true)}>
              <span>查看完整动作</span><ChevronRight size={16} />
            </button>
          )}
        />

        <div className="sticky-actions">
          <div className="button-row training-nav-controls">
            <button className="button button--neutral" disabled={session.currentIndex === 0} onClick={() => setCurrentIndex(session.id, session.currentIndex - 1)}><ArrowLeft size={18} />上一个</button>
            <button className="button button--neutral" onClick={() => void skip()}>跳过</button>
          </div>
          {item.state === "COMPLETED" ? (
            <button className="button button--primary button--wide" style={{ marginTop: 10 }} onClick={() => nextOrComplete(session, setCurrentIndex, completeSession, navigate)}>
              <ArrowRight size={20} />{session.currentIndex === session.items.length - 1 ? "完成训练" : "继续下一个动作"}
            </button>
          ) : (
            <button className="button button--primary button--wide" style={{ marginTop: 10 }} onClick={() => setSheetOpen(true)}><Check size={20} />练过</button>
          )}
        </div>

        <Dialog.Root open={sheetOpen} onOpenChange={(open) => open ? setSheetOpen(true) : closeSheet()}>
          <Dialog.Portal>
            <Dialog.Overlay className="dialog-overlay" />
            <Dialog.Content className="dialog-content" aria-describedby={undefined}>
              <div className="dialog-handle" />
              {sheetStep === "sensation" ? (
                <>
                  <Dialog.Title asChild><h2>这次练下来感觉怎么样？</h2></Dialog.Title>
                  <p className="muted">只记录真实体感，不判断动作是否标准。</p>
                  <div className="option-list">
                    {sensationOptions.map((option) => (
                      <button className="option-button" key={option.value} onClick={() => void chooseSensation(option.value)}>
                        <span><strong>{option.label}</strong><br /><small className="muted">{option.description}</small></span>
                        <ChevronRight size={18} />
                      </button>
                    ))}
                  </div>
                </>
              ) : null}

              {sheetStep === "region" ? (
                <>
                  <Dialog.Title asChild><h2>哪个部位感觉更明显？</h2></Dialog.Title>
                  <p className="muted">这会帮助匹配更相关的练友经验。</p>
                  <div className="option-list">
                    {["手臂", "斜方肌", "前臂", "其他"].map((region) => (
                      <button className="option-button" key={region} onClick={() => void chooseRegion(region)}><strong>{region}</strong><ChevronRight size={18} /></button>
                    ))}
                  </div>
                  <button className="button button--neutral button--wide" style={{ marginTop: 10 }} onClick={() => setSheetStep("sensation")}>返回上一问</button>
                </>
              ) : null}

              {sheetStep === "buddy" ? (
                <div className="buddy-feedback">
                  <div className="buddy-orbit"><Buddy /></div>
                  <Dialog.Title asChild><h2>{card.bodyRegion}这次有接到信号</h2></Dialog.Title>
                  <p className="muted">已记录“目标部位有感觉”。完成很重要，真实记录也很重要。</p>
                  <button className="button button--primary button--wide" onClick={advance}>继续下一个动作<ArrowRight size={18} /></button>
                </div>
              ) : null}

              {sheetStep === "help" ? (
                <>
                  <span className="chip chip--accent"><Sparkles size={14} />已记录</span>
                  <Dialog.Title asChild><h2 style={{ marginTop: 12 }}>{sensationLabel(selectedSensation ?? undefined)}</h2></Dialog.Title>
                  <p className="muted">当前动作暗号：{card.trainingSide.quickCue.text}</p>
                  <div className="notice">
                    <strong>找到一组相关练友经验</strong>
                    <p className="muted">演示数据：{demoExperience.sourceVideoCount} 条同动作视频下的 {demoExperience.commentCount} 条关联评论。</p>
                  </div>
                  <Link
                    className="button button--soft button--wide"
                    style={{ marginTop: 12 }}
                    to={`/experience/${response.standardAction.standardActionId}?videoId=${card.sourceVideo.videoId}&sessionId=${session.id}&from=train`}
                    onClick={closeSheet}
                  >
                    查看练友经验<ChevronRight size={18} />
                  </Link>
                  <button className="button button--primary button--wide" style={{ marginTop: 9 }} onClick={advance}>先继续训练</button>
                </>
              ) : null}
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>

        <Dialog.Root open={fullOpen} onOpenChange={setFullOpen}>
          <Dialog.Portal>
            <Dialog.Overlay className="dialog-overlay" />
            <Dialog.Content className="dialog-content dialog-content--reading" aria-describedby={undefined}>
              <Dialog.Close asChild>
                <button className="dialog-handle-button" type="button" aria-label="收起完整动作">
                  <span className="dialog-handle" />
                </button>
              </Dialog.Close>
              <div className="dialog-reading-scroll">
                <Dialog.Title asChild><h2>完整动作</h2></Dialog.Title>
                <p className="muted">查看动作步骤、关键提醒和错误纠正。</p>
                <ActionCardContent response={response} mode="learn" />
                <Dialog.Close asChild><button className="button button--primary button--wide" style={{ marginTop: 18 }}>回到训练</button></Dialog.Close>
              </div>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </main>
    </AppShell>
  );
}

export function ExperiencePage() {
  const { exerciseId = "action_lateral_raise" } = useParams();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("sessionId");
  const currentVideoId = searchParams.get("videoId") ?? undefined;
  const fromTraining = searchParams.get("from") === "train";
  const helpful = useAppStore((state) => state.helpfulExperienceIds);
  const markHelpful = useAppStore((state) => state.markHelpful);
  const { data: experience } = useExperiences(exerciseId, currentVideoId, fromTraining);
  const { data: availableCards = [] } = useActionCards();
  const demoExperience = getDemoExperience(exerciseId);
  const groups = experience?.frontendGroups ?? demoExperience.groups;
  const [expanded, setExpanded] = useState<string | null | undefined>(undefined);
  const effectiveExpanded = expanded === undefined ? groups[0]?.id : expanded;
  const matchedResponse = availableCards.find((response) => response.standardAction.standardActionId === exerciseId)
    ?? Object.values(actionCards).find((response) => response.standardAction.standardActionId === exerciseId);
  const matchedCard = matchedResponse?.actionCard ?? actionCards.video_lateral_raise_demo.actionCard;
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="练友经验" back />
        <div className="experience-kicker">AI 整理 · 来自练友</div>
        <h1 className="experience-title">{experience?.problemTitle ?? demoExperience.problemTitle}</h1>
        <p className="experience-source">
          {experience?.sourceNote ?? `演示来源：${demoExperience.sourceVideoCount} 条${matchedCard.actionName}相关视频下的 ${demoExperience.commentCount} 条关联评论`}。个人经验，不是诊断。
        </p>

        <section className="section experience-section">
          <div className="section-heading experience-section__heading">
            <div><h2>大家常提到的方法</h2><p className="muted">点开可查看原评论依据</p></div>
          </div>
          <div className="experience-list">
            {groups.map((group) => {
              const isExpanded = effectiveExpanded === group.id;
              const isHelpful = helpful.includes(group.id);
              return (
                <article className="experience-group" key={group.id}>
                  <button
                    className="experience-group__trigger"
                    onClick={() => setExpanded(isExpanded ? null : group.id)}
                    aria-expanded={isExpanded}
                  >
                    <span className="experience-group__lead" aria-hidden="true">－</span>
                    <h3>{group.title}</h3>
                    <ChevronDown className="experience-group__chevron" size={18} />
                  </button>
                  <p className="experience-group__summary">{group.summary}</p>
                  <p className="experience-group__meta">{group.mentions} 条评论提到 · 来自 {group.sourceVideos} 条视频</p>
                  {isExpanded ? (
                    <div className="experience-group__details">
                      <div className="experience-evidence">
                        <div className="experience-disagreement">
                          <strong>不同意见</strong>
                          <p>{group.disagreement}</p>
                        </div>
                        <div className="experience-comments" aria-label="相关练友评论">
                          {group.comments.map((comment) => (
                            <div className="experience-comment" key={comment.id}>
                              <p>“{comment.content}”</p>
                              <small>{comment.creatorName} · {comment.videoTitle}</small>
                              <button className="time-link"><ExternalLink size={13} />查看原视频或评论</button>
                            </div>
                          ))}
                        </div>
                      </div>
                      <button className={`button ${isHelpful ? "button--soft" : "button--neutral"} experience-helpful`} disabled={isHelpful} onClick={() => markHelpful(group.id)}><ThumbsUp size={16} />{isHelpful ? "已标记有用" : "对我有用"}</button>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        </section>
        <section className="section experience-video-source">
          <strong>来自本视频</strong>
          <p>当前视频在 00:22 提到：{matchedCard.learningSide.keyReminders[0]?.text ?? "保持动作控制。"}</p>
          <button className="time-link"><Play size={13} />查看原片段</button>
        </section>
        {fromTraining && sessionId ? (
          <div className="sticky-actions"><Link className="button button--primary button--wide" to={`/train/${sessionId}`}>返回训练</Link></div>
        ) : null}
      </main>
    </AppShell>
  );
}

export function SafetyPage() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("sessionId") ?? "";
  const itemId = searchParams.get("itemId") ?? "";
  const session = useAppStore((state) => state.sessions.find((candidate) => candidate.id === sessionId));
  const endSession = useAppStore((state) => state.endSession);
  const navigate = useNavigate();
  const item = session?.items.find((candidate) => candidate.id === itemId) ?? session?.items[session.currentIndex];
  const { data: response } = useActionCard(item?.cardId);
  if (!session) return <MissingSession />;
  const card = response?.actionCard;
  const finishAction = () => navigate(session.status === "COMPLETED" ? `/train/${session.id}/complete` : `/train/${session.id}`);
  const exitTraining = async () => {
    await endSession(session.id);
    navigate(`/train/${session.id}/complete`);
  };
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="安全提示" back />
        <div className="safety-hero"><ShieldAlert size={34} /></div>
        <p className="eyebrow" style={{ color: "var(--danger)" }}>出现不适</p>
        <h1>先停止当前动作</h1>
        <p className="muted">练过不能判断不适原因。持续、明显或突然的不适，建议咨询教练、康复师或医疗专业人员。</p>
        <section className="section error-box">
          <strong>当前动作</strong>
          <h3 style={{ marginTop: 7 }}>{card?.actionName ?? "当前动作"}</h3>
          <p>已记录为“因不适停止”，之后不会主动推荐这张卡。</p>
        </section>
        <section className="section">
          <div className="button-row">
            <button className="button button--neutral" onClick={() => void exitTraining()}>退出本次训练</button>
            <button className="button button--primary" onClick={finishAction}>结束这个动作</button>
          </div>
          <Link className="button button--soft button--wide" style={{ marginTop: 10 }} to={`/cards/${item?.cardId}?mode=learn`}>查看原视频的一般动作提示</Link>
          <button className="button button--danger button--wide" style={{ marginTop: 10 }}><CircleAlert size={17} />举报危险内容</button>
        </section>
      </main>
    </AppShell>
  );
}

export function CompletePage() {
  const { sessionId = "" } = useParams();
  const session = useAppStore((state) => state.sessions.find((candidate) => candidate.id === sessionId));
  const { data: availableCards = [] } = useActionCards();
  const cardsById = useMemo(() => createActionCardIndex(availableCards), [availableCards]);
  if (!session) return <MissingSession />;
  const completed = session.items.filter((item) => item.state === "COMPLETED").length;
  const skipped = session.items.filter((item) => item.state === "SKIPPED").length;
  const stopped = session.items.filter((item) => item.state === "STOPPED_DISCOMFORT").length;
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="训练总结" />
        <div className="buddy-feedback">
          <div className="buddy-orbit"><Buddy highlighted={stopped === 0} /></div>
          <p className="eyebrow">{session.status === "COMPLETED" ? "本次训练完成" : "本次训练已结束"}</p>
          <h1>今天练过 {completed} 个动作</h1>
          <p className="muted">每一条体感都已保存，下次候选会参考这些记录。</p>
        </div>
        <section className="section surface" style={{ padding: "4px 18px" }}>
          <div className="summary-row"><span>完成</span><strong>{completed}</strong></div>
          <div className="summary-row"><span>跳过</span><strong>{skipped}</strong></div>
          <div className="summary-row"><span>因不适停止</span><strong>{stopped}</strong></div>
        </section>
        <section className="section">
          <div className="section-heading"><h2>动作记录</h2></div>
          <div className="surface" style={{ padding: "0 18px" }}>
            {session.items.map((item) => {
              const card = cardsById.get(item.cardId)?.actionCard ?? actionCards[item.cardId]?.actionCard;
              return (
                <Link className="summary-row" key={item.id} to={`/cards/${item.cardId}`}>
                  <span><strong>{card?.actionName ?? "待同步动作"}</strong><br /><small className="muted">{sensationLabel(item.sensation)}</small></span>
                  <ChevronRight size={18} />
                </Link>
              );
            })}
          </div>
        </section>
        <div className="button-row" style={{ marginTop: 22 }}>
          <Link className="button button--neutral" to={`/plans/${session.planId}`}>查看来源练单</Link>
          <Link className="button button--primary" to="/plans">返回练单</Link>
        </div>
      </main>
    </AppShell>
  );
}

function MissingSession() {
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="训练记录不存在" back />
        <div className="empty-state"><div><Dumbbell size={30} /><h2>没有找到这次训练</h2><p className="muted">返回练单重新开始一次训练。</p><Link className="button button--primary" to="/plans">返回练单</Link></div></div>
      </main>
    </AppShell>
  );
}
