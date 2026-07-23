import * as Dialog from "@radix-ui/react-dialog";
import {
  ArrowLeft,
  BookOpen,
  Check,
  ChevronRight,
  CircleUserRound,
  Clock3,
  Dumbbell,
  ExternalLink,
  Heart,
  House,
  Library,
  ListChecks,
  Play,
  Plus,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router";
import type { ActionCardResponse, Sensation } from "./domain";
import { useAppStore } from "./store";

export function Brand() {
  return (
    <Link className="brand" to="/plans" aria-label="练过首页">
      <span className="brand__mark" aria-hidden="true">
        <Check size={20} strokeWidth={3} />
      </span>
      <span>练过</span>
    </Link>
  );
}

export function PageHeader({
  title,
  back = false,
  action,
}: {
  title: string;
  back?: boolean;
  action?: ReactNode;
}) {
  const navigate = useNavigate();
  return (
    <header className="page-header page-header--centered">
      <div className="page-header__side page-header__side--start">
        {back ? (
          <button className="icon-button" onClick={() => navigate(-1)} aria-label="返回">
            <ArrowLeft size={20} />
          </button>
        ) : (
          <Brand />
        )}
      </div>
      {back ? <h1 className="page-header__title">{title}</h1> : null}
      <div className="page-header__side page-header__side--end">
        {action ?? <span className="page-header__placeholder" aria-hidden="true" />}
      </div>
    </header>
  );
}

export function AppShell({ children, navigation = true }: { children: ReactNode; navigation?: boolean }) {
  return (
    <div className="phone-shell">
      {children}
      {navigation ? <BottomNavigation /> : null}
    </div>
  );
}

function BottomNavigation() {
  const links = [
    { to: "/plans", label: "练单", icon: ListChecks },
    { to: "/library", label: "动作库", icon: Library },
    { to: "/me", label: "我的", icon: CircleUserRound },
  ];
  return (
    <nav className="bottom-nav" aria-label="主导航">
      {links.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} aria-label={label}>
          <Icon size={21} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export function VideoFrame({
  compact = false,
  title = "侧平举新手教学",
  creator = "GoFit Demo Coach",
  src,
}: {
  compact?: boolean;
  title?: string;
  creator?: string;
  src?: string;
}) {
  const [portrait, setPortrait] = useState(true);
  return (
    <div className={`video-frame ${compact ? "video-frame--compact" : ""} ${portrait ? "video-frame--portrait" : ""}`}>
      <video
        src={src}
        muted
        playsInline
        loop
        autoPlay
        preload="metadata"
        onLoadedMetadata={(event) => setPortrait(event.currentTarget.videoHeight > event.currentTarget.videoWidth)}
      />
      <div className="video-frame__scrim">
        <strong>{title}</strong>
        <p>{creator}</p>
      </div>
    </div>
  );
}

function formatTime(ms: number) {
  const seconds = Math.floor(ms / 1000);
  return `00:${String(seconds).padStart(2, "0")}`;
}

export function Evidence({ ids }: { ids: string[] }) {
  return (
    <div className="evidence" aria-label="来源证据">
      {ids.map((id) => (
        <span key={id}>#{id}</span>
      ))}
    </div>
  );
}

function TimeRange({ startMs, endMs }: { startMs: number; endMs: number }) {
  return (
    <span className="time-link">
      <Clock3 size={13} />
      {formatTime(startMs)}–{formatTime(endMs)}
    </span>
  );
}

type ClipRange = {
  startMs: number;
  endMs: number;
  mediaUrl?: string;
};

function LoopingClip({
  clip,
  label,
  caption = "正确示范",
}: {
  clip: ClipRange;
  label: string;
  caption?: string;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [portrait, setPortrait] = useState(true);
  const isCuratedFile = Boolean(clip.mediaUrl);
  const startSeconds = isCuratedFile ? 0 : clip.startMs / 1000;
  const endSeconds = isCuratedFile ? Number.POSITIVE_INFINITY : clip.endMs / 1000;

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const startClip = () => {
      setPortrait(video.videoHeight > video.videoWidth);
      video.currentTime = startSeconds;
      void video.play().catch(() => undefined);
    };
    video.addEventListener("loadedmetadata", startClip);
    if (video.readyState >= 1) startClip();
    return () => video.removeEventListener("loadedmetadata", startClip);
  }, [startSeconds]);

  return (
    <figure className={`looping-clip ${portrait ? "looping-clip--portrait" : ""}`}>
      <video
        ref={videoRef}
        src={clip.mediaUrl}
        muted
        playsInline
        autoPlay
        loop={isCuratedFile}
        preload="metadata"
        aria-label={label}
        onTimeUpdate={(event) => {
          if (event.currentTarget.currentTime >= endSeconds) {
            event.currentTarget.currentTime = startSeconds;
            void event.currentTarget.play().catch(() => undefined);
          }
        }}
      />
      <figcaption>{caption}</figcaption>
    </figure>
  );
}

function reminderTimeRange(
  reminderEvidenceIds: string[],
  card: ActionCardResponse["actionCard"],
): ClipRange {
  const overlaps = (ids: string[]) => ids.some((id) => reminderEvidenceIds.includes(id));
  const relatedError = card.learningSide.commonErrors.find((error) =>
    overlaps([...error.evidenceIds, ...error.errorDemo.evidenceIds]),
  );
  if (relatedError) return relatedError.errorDemo;

  const relatedStep = card.learningSide.steps.find((step) => overlaps(step.evidenceIds));
  if (relatedStep) return relatedStep;
  return card.learningSide.correctDemo;
}

export function MuscleMap({ primary, secondary }: { primary: string[]; secondary: string[] }) {
  return (
    <div className="muscle-panel">
      <svg viewBox="0 0 120 180" role="img" aria-label="肩部肌群示意图">
        <circle cx="60" cy="22" r="15" fill="var(--body-muted)" />
        <path
          d="M45 42 C36 47 31 61 33 80 L39 121 C41 137 48 151 60 162 C72 151 79 137 81 121 L87 80 C89 61 84 47 75 42 C68 46 52 46 45 42Z"
          fill="var(--body-muted)"
        />
        <path d="M44 46 C30 48 20 60 18 77 L28 82 C31 66 38 61 48 58Z" fill="var(--accent)" />
        <path d="M76 46 C90 48 100 60 102 77 L92 82 C89 66 82 61 72 58Z" fill="var(--accent)" />
        <path d="M48 48 Q60 56 72 48 L70 66 Q60 72 50 66Z" fill="var(--body-accent-muted)" />
        <path d="M30 80 L39 84 L34 135 L24 132Z" fill="var(--body-muted)" />
        <path d="M90 80 L81 84 L86 135 L96 132Z" fill="var(--body-muted)" />
      </svg>
      <div>
        <span className="chip chip--accent">主要肌群</span>
        <h3 style={{ marginTop: 8 }}>{primary.join("、")}</h3>
        <p>辅助：{secondary.join("、") || "无"}</p>
      </div>
    </div>
  );
}

export function TrainingDataView({
  response,
  footerLabel,
  footerAction,
}: {
  response: ActionCardResponse;
  footerLabel?: string;
  footerAction?: ReactNode;
}) {
  const card = response.actionCard;
  const cueSteps = card.trainingSide.quickCue.text.split("→").map((step) => step.trim()).filter(Boolean);
  const hasCueSequence = cueSteps.length > 1;
  return (
    <div className="training-data-view">
      <section className="training-action-header">
        <h1>{card.actionName}</h1>
        <p>来自 {card.sourceVideo.creatorName}</p>
      </section>

      <div className="training-content">
        <LoopingClip
          clip={card.learningSide.correctDemo}
          label={`${card.actionName}正确动作演示`}
          caption="正确示范"
        />
        <p className="training-cue-line" aria-label={card.trainingSide.quickCue.text}>
          {hasCueSequence ? (
            <span className="cue-sequence" aria-hidden="true">
              <span className="cue-slider" />
              {cueSteps.map((step, index) => (
                <span className="cue-stage" key={`${step}-${index}`}>
                  <span className="cue-phrase">{step}</span>
                  {index < cueSteps.length - 1 ? <span className="cue-arrow">→</span> : null}
                </span>
              ))}
            </span>
          ) : (
            <span className="cue-text" aria-hidden="true">
              {card.trainingSide.quickCue.text}
            </span>
          )}
        </p>
        <ul className="training-tips">
          {card.trainingSide.quickTips.map((tip) => (
            <li key={tip.text}>
              <Check size={17} aria-hidden="true" />
              <strong>{tip.text}</strong>
            </li>
          ))}
        </ul>
        {footerLabel && footerAction ? (
          <div className="training-detail-row">
            <span>{footerLabel}</span>
            {footerAction}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function ActionCardContent({
  response,
  mode,
  quickFooter,
}: {
  response: ActionCardResponse;
  mode: "learn" | "quick";
  quickFooter?: {
    label: string;
    action: ReactNode;
  };
}) {
  const card = response.actionCard;
  if (mode === "quick") {
    return <TrainingDataView response={response} footerLabel={quickFooter?.label} footerAction={quickFooter?.action} />;
  }

  return (
    <>
      <div className="learn-card-intro">
        <h1>{card.actionName}</h1>
        <div className="chip-row action-hashtags">
          <span className="chip">#{card.bodyRegion}</span>
          {card.equipment.map((item) => <span className="chip" key={item}>#{item}</span>)}
          {card.primaryMuscles.map((item) => <span className="chip chip--accent" key={item}>#{item}</span>)}
        </div>
        <p>来自《{card.sourceVideo.title}》视频</p>
      </div>

      <div className="learn-card-flow">
          <section className="learn-module">
            <div className="section-heading"><div><p className="eyebrow">01</p><h2>完整动作</h2></div></div>
            <LoopingClip clip={card.learningSide.correctDemo} label={`${card.actionName}正确动作演示`} />
            <ol className="step-list learn-step-list">
              {card.learningSide.steps.map((step) => (
                <li className="step-item" key={step.order}>
                  <span className="step-number">{step.order}</span>
                  <div><p>{step.instruction}</p><TimeRange startMs={step.startMs} endMs={step.endMs} /></div>
                </li>
              ))}
            </ol>
          </section>

          <section className="learn-module">
            <div className="section-heading"><div><p className="eyebrow">02</p><h2>关键提醒</h2></div></div>
            <ul className="reminder-list">
              {card.learningSide.keyReminders.map((reminder) => {
                const time = reminderTimeRange(reminder.evidenceIds, card);
                return (
                  <li key={reminder.text}>
                    <Sparkles size={18} aria-hidden="true" />
                    <div><strong>{reminder.text}</strong><TimeRange startMs={time.startMs} endMs={time.endMs} /></div>
                  </li>
                );
              })}
            </ul>
          </section>

          <section className="learn-module learn-module--errors">
            <div className="section-heading"><div><p className="eyebrow">03</p><h2>错误纠正</h2></div></div>
            <div className="error-evidence-heading">
              <div><strong>错误片段</strong><p>从原视频定位到 {card.learningSide.commonErrors.length} 段</p></div>
              {card.learningSide.commonErrors.length > 1 ? <span>左右滑动查看</span> : null}
            </div>
            {card.learningSide.commonErrors.length ? <div className="error-clip-track" aria-label={`错误片段，共 ${card.learningSide.commonErrors.length} 段`}>
              {card.learningSide.commonErrors.map((error, index) => (
                <LoopingClip
                  key={error.errorDemo.candidateId}
                  clip={error.errorDemo}
                  label={`${card.actionName}错误动作演示：${error.mistake}`}
                  caption={`错误示范 ${String(index + 1).padStart(2, "0")}`}
                />
              ))}
            </div> : <p className="muted">本视频未提供人工确认的错误示范。</p>}

            <div className="error-findings">
              <div className="error-findings__heading">
                <span className="error-label"><TriangleAlert size={15} />常见错误</span>
                <span className="chip">{card.learningSide.commonErrors.length} 项</span>
              </div>
              <div className="error-list">
                {card.learningSide.commonErrors.map((error, index) => (
                  <article className="error-correction" key={error.mistake}>
                    <span className="error-correction__index">{String(index + 1).padStart(2, "0")}</span>
                    <div className="error-correction__copy">
                      <h3>{error.mistake}</h3>
                      <p><strong>这样调整：</strong>{error.correction}</p>
                      <TimeRange startMs={error.errorDemo.startMs} endMs={error.errorDemo.endMs} />
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </section>
      </div>
    </>
  );
}

export function AddToPlanDialog({ cardId, children }: { cardId: string; children: ReactNode }) {
  const plans = useAppStore((state) => state.plans);
  const addCardToPlan = useAppStore((state) => state.addCardToPlan);
  const createPlan = useAppStore((state) => state.createPlan);
  const navigate = useNavigate();
  const choose = async (planId: string) => {
    await addCardToPlan(planId, cardId);
    navigate(`/plans/${planId}`);
  };
  const create = async () => {
    const planId = await createPlan("今天练肩", cardId);
    navigate(`/plans/${planId}`);
  };
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>{children}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content" aria-describedby={undefined}>
          <div className="dialog-handle" />
          <Dialog.Title asChild><h2>加入哪份练单？</h2></Dialog.Title>
          <p className="muted">动作卡会加入末尾，之后可以调整顺序。</p>
          <div className="option-list">
            {plans.map((plan) => (
              <Dialog.Close asChild key={plan.id}>
                <button className="option-button" onClick={() => void choose(plan.id)}>
                  <span><strong>{plan.name}</strong><br /><small className="muted">{plan.cardIds.length} 个动作</small></span>
                  <ChevronRight size={18} />
                </button>
              </Dialog.Close>
            ))}
            <Dialog.Close asChild>
              <button className="option-button" onClick={() => void create()}>
                <span><strong>新建“今天练肩”</strong><br /><small className="muted">从这张卡开始</small></span>
                <Plus size={18} />
              </button>
            </Dialog.Close>
          </div>
          <Dialog.Close asChild>
            <button className="button button--neutral button--wide" style={{ marginTop: 14 }}>取消</button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export const sensationOptions: Array<{
  value: Sensation;
  label: string;
  description: string;
}> = [
  { value: "TARGET_FELT", label: "目标部位有感觉", description: "记录这次良好体感" },
  { value: "OTHER_FELT", label: "其他部位更酸", description: "选择实际更明显的部位" },
  { value: "NO_FEELING", label: "没找到明显感觉", description: "看看练友怎么调整" },
  { value: "TOO_HARD", label: "动作有点吃力", description: "下次推荐会参考" },
  { value: "DISCOMFORT", label: "出现不适", description: "先停止当前动作" },
];

export function Buddy({ highlighted = true }: { highlighted?: boolean }) {
  return (
    <svg viewBox="0 0 100 130" role="img" aria-label={highlighted ? "肩部已记录的健身搭子" : "健身搭子"}>
      <circle cx="50" cy="20" r="14" fill="var(--ink)" />
      <path d="M36 40 Q50 33 64 40 L69 82 Q62 92 50 92 Q38 92 31 82Z" fill="var(--body-surface)" />
      <path className="buddy__arm buddy__arm--left" d="M36 43 Q23 48 18 67 L28 71 Q33 58 42 56Z" fill={highlighted ? "var(--accent)" : "var(--body-surface)"} />
      <path className="buddy__arm buddy__arm--right" d="M64 43 Q77 48 82 67 L72 71 Q67 58 58 56Z" fill={highlighted ? "var(--accent)" : "var(--body-surface)"} />
      <path d="M37 87 L47 87 L44 124 L32 124Z" fill="var(--ink)" />
      <path d="M63 87 L53 87 L56 124 L68 124Z" fill="var(--ink)" />
    </svg>
  );
}

export const icons = {
  BookOpen,
  ChevronRight,
  Dumbbell,
  ExternalLink,
  Heart,
  House,
  Play,
  Plus,
  Sparkles,
  TriangleAlert,
  X,
};
