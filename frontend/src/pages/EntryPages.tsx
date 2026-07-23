import {
  Bookmark,
  Check,
  ChevronRight,
  Dumbbell,
  Heart,
  LoaderCircle,
  MessageCircle,
  MoreHorizontal,
  Play,
  Search,
  Share2,
  Sparkles,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import { useActionCard, useActionCards } from "../api";
import { BUSINESS_API_BASE_URL, businessApi } from "../business-api";
import {
  ActionCardContent,
  AddToPlanDialog,
  AppShell,
  PageHeader,
  VideoFrame,
} from "../components";
import type { ActionCardResponse } from "../domain";
import { actionCards, demoVideos, demoVideoUrl, getDemoExperience, type DemoVideo } from "../mocks/data";
import { useAppStore } from "../store";

export function DouyinPage() {
  const navigate = useNavigate();
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive douyin-page">
        <div className="page-header">
          <span style={{ fontWeight: 800 }}>抖音精选</span>
          <button className="icon-button" aria-label="更多"><MoreHorizontal size={20} /></button>
        </div>
        <div className="video-frame" style={{ height: "calc(100dvh - 180px)", aspectRatio: "auto" }}>
          <video src={demoVideoUrl} muted playsInline loop autoPlay preload="metadata" />
          <div className="video-frame__scrim" style={{ paddingRight: 72 }}>
            <strong style={{ fontSize: "1.1rem" }}>侧平举总是手臂酸？新手先记住这 3 点</strong>
            <p>@GoFit Demo Coach</p>
            <p>#练肩 #健身新手 #动作教学</p>
          </div>
          <div style={{ position: "absolute", right: 12, bottom: 26, display: "grid", gap: 14 }}>
            {[Heart, MessageCircle, Bookmark].map((Icon, index) => (
              <button key={index} className="icon-button" aria-label={["点赞", "评论", "收藏"][index]}>
                <Icon size={21} />
              </button>
            ))}
          </div>
        </div>
        <button
          className="button button--primary button--wide"
          style={{ marginTop: 14 }}
          onClick={() => navigate("/import/video_lateral_raise_demo")}
        >
          <Share2 size={19} />用练过打开
        </button>
      </main>
    </AppShell>
  );
}

const processingSteps = ["正在理解视频内容", "正在定位关键片段", "正在整理动作要点", "动作卡已生成"];

export function ImportPage() {
  const { videoId = "video_lateral_raise_demo" } = useParams();
  const selectedVideo = actionCards[videoId]?.actionCard.sourceVideo;
  const selectedDemoVideo = demoVideos.find((video) => video.videoId === videoId);
  const [step, setStep] = useState(0);
  const [resultCardId, setResultCardId] = useState<string | null>(null);
  const [apiMessage, setApiMessage] = useState("正在提交到业务后端");
  const [apiError, setApiError] = useState<string | null>(null);
  useEffect(() => {
    if (step >= processingSteps.length - 1) return;
    const timer = window.setTimeout(() => setStep((value) => value + 1), 650);
    return () => window.clearTimeout(timer);
  }, [step]);
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        setApiError(null);
        const imported = await businessApi.importVideo({
          videoId,
          title: selectedVideo?.title,
          creatorName: selectedVideo?.creatorName,
          sourceUrl: selectedVideo?.sourceUrl,
          assetFileName: selectedDemoVideo?.assetFileName,
        });
        if (cancelled) return;
        setApiMessage(imported.message);
        if (imported.status === "COMPLETED" && imported.cardId) {
          setResultCardId(imported.cardId);
          setStep(processingSteps.length - 1);
          setApiMessage("动作卡已生成");
          return;
        }
        const pollingDeadline = Date.now() + 5 * 60 * 1000;
        while (Date.now() < pollingDeadline && !cancelled) {
          await new Promise((resolve) => window.setTimeout(resolve, 1500));
          if (cancelled) return;
          const processing = await businessApi.processingStatus(imported.videoId);
          if (processing.status === "COMPLETED" && processing.cardId) {
            setResultCardId(processing.cardId);
            setStep(processingSteps.length - 1);
            setApiError(null);
            setApiMessage("动作卡已生成");
            return;
          }
          if (processing.status === "FAILED") throw new Error(processing.errorMessage ?? "动作卡生成失败");
          setApiMessage("AI 中心仍在处理，页面会自动等待结果");
        }
        if (!cancelled) setApiError("AI 处理超过 5 分钟，请稍后刷新页面重试。");
      } catch (error) {
        if (cancelled) return;
        setApiError(error instanceof Error ? error.message : "业务后端连接失败");
        setApiMessage("导入失败，请检查业务后端或人工素材 manifest");
      }
    };
    void run();
    return () => { cancelled = true; };
  }, [selectedDemoVideo?.assetFileName, selectedVideo?.creatorName, selectedVideo?.sourceUrl, selectedVideo?.title, videoId]);
  const done = step === processingSteps.length - 1 && Boolean(resultCardId);
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="正在生成动作卡" back />
        <VideoFrame compact title={selectedVideo?.title} creator={selectedVideo?.creatorName} src={selectedDemoVideo?.assetFileName ? `${BUSINESS_API_BASE_URL}/media/videos/${encodeURIComponent(selectedDemoVideo.assetFileName)}` : undefined} />
        <section className="section">
          <p className="eyebrow">AI 内容重构</p>
          <h1>{done ? "动作卡准备好了" : "把视频变成能练的步骤"}</h1>
          <p className="muted">每条内容都保留原视频时间和证据，方便随时核对。</p>
        </section>
        <ol className="processing-list">
          {processingSteps.map((label, index) => (
            <li key={label} className={`processing-item ${index === step && !done ? "processing-item--active" : ""}`}>
              <span className="processing-item__icon">
                {index < step || done ? <Check size={18} /> : index === step ? <LoaderCircle size={18} /> : index + 1}
              </span>
              <div>
                <strong>{label}</strong>
                {index === step && !done ? <div className="muted" style={{ fontSize: ".78rem", marginTop: 3 }}>{apiMessage}</div> : null}
              </div>
            </li>
          ))}
        </ol>
        {done ? (
          <Link className="button button--primary button--wide" to={`/cards/${resultCardId}?mode=learn`}>
            打开动作卡<ChevronRight size={19} />
          </Link>
        ) : null}
        {apiError ? <p className="error-box" style={{ marginTop: 12 }}>{apiError}</p> : null}
      </main>
    </AppShell>
  );
}

export function DemoVideoListPage() {
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive demo-video-page">
        <PageHeader title="演示视频" back />
        <section className="demo-video-intro">
          <p className="eyebrow">内置演示内容</p>
          <h1>选择一条视频开始解析</h1>
          <p>这里展示预先准备好的健身视频。选择后会进入完整的视频解析流程。</p>
        </section>

        <section className="section" aria-labelledby="demo-video-list-title">
          <div className="section-heading">
            <div>
              <h2 id="demo-video-list-title">视频列表</h2>
              <p className="muted">{demoVideos.length} 条可用于演示</p>
            </div>
            <span className="chip chip--accent">已就绪</span>
          </div>
          <div className="surface demo-video-list">
            {demoVideos.map((video) => (
              <Link className="demo-video-item" key={video.videoId} to={`/import/${video.videoId}`}>
                <DemoVideoCover video={video} />
                <span className="demo-video-copy">
                  <strong>{video.title}</strong>
                  <span>{video.creatorName}</span>
                  <small>{video.actionName} · {video.bodyRegion}</small>
                </span>
                <ChevronRight className="demo-video-chevron" size={19} aria-hidden="true" />
              </Link>
            ))}
          </div>
        </section>
      </main>
    </AppShell>
  );
}

function DemoVideoCover({ video }: { video: DemoVideo }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  useEffect(() => {
    const element = videoRef.current;
    if (!element || video.posterUrl) return;
    const seekToPreview = () => {
      element.currentTime = Math.min(video.previewSecond, Math.max(0, element.duration - 0.1));
    };
    element.addEventListener("loadedmetadata", seekToPreview);
    if (element.readyState >= 1) seekToPreview();
    return () => element.removeEventListener("loadedmetadata", seekToPreview);
  }, [video.posterUrl, video.previewSecond]);

  return (
    <span className="demo-video-cover" aria-hidden="true">
      {video.posterUrl ? (
        <img src={video.posterUrl} alt="" />
      ) : (
        <video
          ref={videoRef}
          src={video.previewUrl}
          muted
          playsInline
          autoPlay
          preload="metadata"
          onSeeked={(event) => event.currentTarget.pause()}
        />
      )}
      <span className="demo-video-cover__play"><Play size={16} fill="currentColor" /></span>
      <span className="demo-video-cover__duration">{video.durationLabel}</span>
    </span>
  );
}

export function CardPage() {
  const { cardId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const mode = searchParams.get("mode") === "quick" ? "quick" : "learn";
  const { data: response, isPending } = useActionCard(cardId);
  const collected = useAppStore((state) => cardId ? state.collectedCardIds.includes(cardId) : false);
  const toggleCollected = useAppStore((state) => state.toggleCollected);

  if (isPending) return <LoadingPage />;
  if (!response || !cardId) return <NotFoundPage />;
  const experience = getDemoExperience(response.standardAction.standardActionId);
  return (
    <AppShell navigation={false}>
      <main className={`page page--immersive card-page ${mode === "quick" ? "card-page--quick" : ""}`}>
        <PageHeader
          title="视频动作卡"
          back
          action={
            <button className="icon-button" onClick={() => void toggleCollected(cardId)} aria-label={collected ? "取消收藏" : "收藏"}>
              <Bookmark size={19} fill={collected ? "var(--accent)" : "none"} />
            </button>
          }
        />
        <div className="tabs" role="tablist" aria-label="动作卡模式">
          <button className="tab" role="tab" aria-selected={mode === "learn"} onClick={() => setSearchParams({ mode: "learn" })}>完整步骤</button>
          <button className="tab" role="tab" aria-selected={mode === "quick"} onClick={() => setSearchParams({ mode: "quick" })}>训练速记</button>
        </div>
        <div className="card-content">
          <ActionCardContent
            response={response}
            mode={mode}
            quickFooter={mode === "quick" ? {
              label: experience.problemTitle,
              action: (
                <Link className="training-details-button" to={`/experience/${response.standardAction.standardActionId}?videoId=${cardId}`}>
                  <span>查看练友经验</span><ChevronRight size={16} />
                </Link>
              ),
            } : undefined}
          />
        </div>
        <div className="sticky-actions">
          <AddToPlanDialog cardId={cardId}>
            <button className="button button--primary button--wide"><Dumbbell size={19} />加入练单</button>
          </AddToPlanDialog>
        </div>
      </main>
    </AppShell>
  );
}

function ActionListItem({ response, action }: { response: ActionCardResponse; action?: React.ReactNode }) {
  const card = response.actionCard;
  return (
    <div className="list-card">
      <Link className="list-card__media" to={`/cards/${card.sourceVideo.videoId}`} aria-label={`查看${card.actionName}`}>
        <Dumbbell size={23} />
      </Link>
      <Link className="list-card__content" to={`/cards/${card.sourceVideo.videoId}`}>
        <strong>{card.actionName}</strong>
        <p>{card.sourceVideo.creatorName} · {card.primaryMuscles.join("、")}</p>
      </Link>
      {action}
    </div>
  );
}

export function LibraryPage() {
  const { data: cards = [] } = useActionCards();
  const [query, setQuery] = useState("");
  const collectedCardIds = useAppStore((state) => state.collectedCardIds);
  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return cards;
    return cards.filter(({ actionCard: card }) =>
      [card.actionName, card.bodyRegion, card.sourceVideo.title, ...card.primaryMuscles, ...card.equipment]
        .join(" ")
        .toLowerCase()
        .includes(keyword),
    );
  }, [cards, query]);
  return (
    <AppShell>
      <main className="page">
        <PageHeader title="动作库" />
        <p className="eyebrow">视频变成你的训练工具</p>
        <h1>动作库</h1>
        <p className="muted">这里保存的是具体视频动作卡，每张都保留创作者与来源。</p>
        <div style={{ position: "relative", marginTop: 18 }}>
          <Search size={18} style={{ position: "absolute", left: 15, top: 16, color: "var(--muted)" }} />
          <input className="search-input" style={{ paddingLeft: 43 }} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索动作、肌群或器械" />
        </div>
        <Link className="button button--soft button--wide" style={{ marginTop: 10 }} to="/demo-videos">
          <Sparkles size={18} />粘贴抖音链接
        </Link>
        <section className="section">
          <div className="section-heading">
            <div><h2>{query ? "搜索结果" : "全部动作卡"}</h2><p className="muted">{filtered.length} 张可用</p></div>
          </div>
          <div className="surface" style={{ padding: "0 16px" }}>
            {filtered.map((response) => {
              const cardId = response.actionCard.sourceVideo.videoId;
              return (
                <ActionListItem
                  key={cardId}
                  response={response}
                  action={
                    <AddToPlanDialog cardId={cardId}>
                      <button className="mini-button" aria-label={`将${response.actionCard.actionName}加入练单`}><ChevronRight size={18} /></button>
                    </AddToPlanDialog>
                  }
                />
              );
            })}
          </div>
        </section>
        {collectedCardIds.length ? <p className="muted" style={{ fontSize: ".8rem", textAlign: "center" }}>已收藏 {collectedCardIds.length} 张视频动作卡</p> : null}
      </main>
    </AppShell>
  );
}

function LoadingPage() {
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="加载中" back />
        <div className="surface" style={{ height: 320, background: "var(--surface-raised)" }} />
      </main>
    </AppShell>
  );
}

function NotFoundPage() {
  return (
    <AppShell navigation={false}>
      <main className="page page--immersive">
        <PageHeader title="没有找到" back />
        <div className="empty-state">
          <div><h2>这张动作卡暂时不存在</h2><p className="muted">返回动作库选择一张已经准备好的卡片。</p><Link className="button button--primary" to="/library">去动作库</Link></div>
        </div>
      </main>
    </AppShell>
  );
}
