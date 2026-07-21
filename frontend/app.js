const STORAGE_KEY = "gofit-demo-state-v1";
const API_BASE = localStorage.getItem("gofit-api-base") || "http://127.0.0.1:8000/api/v1";
const COVER_BY_ID = {
  "lateral-raise": "art-1",
  "front-raise": "art-2",
  "reverse-fly": "art-3",
  "lat-pulldown": "art-4"
};

let cards = [
  {
    id: "lateral-raise",
    name: "哑铃侧平举",
    creator: "阿哲的训练课",
    title: "新手肩部训练：侧平举这样做，肩中束更容易找到感觉",
    area: "肩部",
    main: "肩中束",
    assist: "肩前束、斜方肌",
    equipment: "哑铃",
    cover: "art-1",
    source: "来自本视频",
    cue: "肩放松 → 肘带动 → 缓慢落",
    steps: [
      ["站稳，手肘微屈，哑铃贴近身体两侧", "00:08"],
      ["先想象用手肘向两侧打开，而不是甩手", "00:16"],
      ["抬到与肩平齐即可，停住一拍", "00:24"],
      ["控制下放，保持肩膀远离耳朵", "00:31"]
    ],
    tip: "不要为了抬得更高而耸肩；动作幅度以肩部持续发力为准。",
    experienceCount: 68,
    videoCount: 4
  },
  {
    id: "front-raise",
    name: "哑铃前平举",
    creator: "阿哲的训练课",
    title: "肩部前束训练：前平举动作细节",
    area: "肩部",
    main: "肩前束",
    assist: "胸上束",
    equipment: "哑铃",
    cover: "art-2",
    source: "来自本视频",
    cue: "核心收紧 → 手臂前举 → 控制落下",
    steps: [["双脚站稳，哑铃放在大腿前侧", "00:07"], ["手臂向前举至视线下方", "00:19"], ["停住后缓慢还原", "00:28"]],
    tip: "重量不需要很大，身体不要为了完成次数而后仰。",
    experienceCount: 21,
    videoCount: 2
  },
  {
    id: "reverse-fly",
    name: "俯身反向飞鸟",
    creator: "训练室 101",
    title: "后束肩入门：俯身反向飞鸟",
    area: "肩部",
    main: "三角肌后束",
    assist: "菱形肌",
    equipment: "哑铃",
    cover: "art-3",
    source: "来自本视频",
    cue: "髋部折叠 → 肘向外开 → 回到起点",
    steps: [["髋部折叠，背部保持稳定", "00:11"], ["肘部向外打开，手腕保持放松", "00:22"], ["用控制感完成回落", "00:34"]],
    tip: "先把动作做小，感受后肩，而不是追求哑铃高度。",
    experienceCount: 32,
    videoCount: 3
  },
  {
    id: "lat-pulldown",
    name: "高位下拉",
    creator: "背部训练笔记",
    title: "高位下拉：新手找到背部发力的三个提示",
    area: "背部",
    main: "背阔肌",
    assist: "肱二头肌",
    equipment: "高位下拉器",
    cover: "art-4",
    source: "来自本视频",
    cue: "肩胛下沉 → 肘向下 → 慢慢回",
    steps: [["坐稳并让肩膀远离耳朵", "00:09"], ["想象肘部向裤兜方向移动", "00:18"], ["不要借身体后仰完成下拉", "00:29"]],
    tip: "如果手臂先酸，先减轻重量并重新找回肩胛下沉。",
    experienceCount: 45,
    videoCount: 3
  }
];

let experienceGroups = [
  { title: "降低重量", count: 24, videos: 4, summary: "先减轻重量，让肩部完成完整轨迹，手臂不需要抢着发力。", split: "少数人建议保留重量，但都强调动作要慢。", comments: [["小鹿练肩", "我把 7.5kg 换成 4kg 之后，肩中束终于有感觉了。"], ["一周三练", "重量轻一点反而更容易控制住下放。"]] },
  { title: "由手肘带动", count: 19, videos: 3, summary: "把注意力从手掌移到手肘，想象手肘向两侧打开。", split: "也有人更习惯想象手背向外，但核心都是避免甩动。", comments: [["阿白", "教练让我想手肘，不要想哑铃，动作立刻稳定很多。"], ["椰子水", "手肘带动之后，肩膀没有那么容易耸起来。"]] },
  { title: "避免耸肩", count: 16, videos: 4, summary: "保持肩膀远离耳朵，不为了更高的幅度牺牲肩部位置。", split: "暂无明显分歧，评论里都把耸肩当作常见代偿。", comments: [["今天也练", "我以前总想抬到头顶，结果斜方肌特别酸。"], ["小满训练中", "肩膀下沉后，动作幅度小一点也更有感觉。"]] }
];

const defaultState = {
  view: "source",
  selectedCard: "lateral-raise",
  selectedPlan: "shoulder-day",
  activeTab: "full",
  selectedFeedback: null,
  selectedBody: null,
  useful: [],
  savedCards: ["lateral-raise"],
  plans: [
    { id: "shoulder-day", name: "今天练肩", cardIds: ["lateral-raise", "front-raise"], uses: 3, updated: "今天 09:40" },
    { id: "back-last-time", name: "上次练背", cardIds: ["lat-pulldown", "reverse-fly"], uses: 1, updated: "7 月 16 日" }
  ],
  session: null,
  history: [
    { name: "哑铃侧平举", felt: "目标部位有感觉", date: "昨天", color: "good" },
    { name: "高位下拉", felt: "没找到明显感觉", date: "7 月 16 日", color: "neutral" }
  ]
};

let state = loadState();
let processingTimer = null;

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!response.ok) throw new Error(`API ${response.status}: ${path}`);
  if (response.status === 204) return null;
  return response.json();
}

function normalizeCard(item, index = 0) {
  const data = item.cardData || {};
  const summary = item.experienceSummary || {};
  return {
    id: item.id,
    exerciseId: item.exerciseId,
    videoId: item.videoId,
    name: item.actionName,
    creator: item.sourceVideo?.creatorName || data.creator || "未知创作者",
    title: item.sourceVideo?.title || data.title || item.actionName,
    area: item.bodyRegion,
    main: (item.primaryMuscles || []).join("、") || "目标肌群",
    assist: (item.secondaryMuscles || []).join("、") || "辅助肌群",
    equipment: (item.equipment || []).join("、") || "徒手",
    cover: COVER_BY_ID[item.id] || `art-${(index % 4) + 1}`,
    source: data.source || "来自本视频",
    cue: data.cue || item.actionName,
    steps: data.steps || [],
    tip: data.tip || "训练时保持动作可控。",
    experienceCount: Number(summary.commentCount || data.experienceCount || 0),
    videoCount: Number(summary.sourceVideoCount || data.videoCount || 0),
    isSaved: Boolean(item.isSaved)
  };
}

function normalizePlan(item) {
  return {
    id: item.id,
    name: item.name,
    cardIds: (item.items || []).map(row => row.cardId),
    itemIds: (item.items || []).map(row => row.id),
    uses: item.useCount || 0,
    updated: item.updatedAt ? "刚刚同步" : "刚刚",
    api: true
  };
}

function normalizeSession(item) {
  return {
    id: item.id,
    planId: item.planId,
    cardIds: (item.items || []).map(row => row.cardId),
    itemIds: (item.items || []).map(row => row.id),
    index: item.currentIndex || 0,
    completed: (item.items || [])
      .filter(row => row.itemStatus && row.itemStatus !== "PENDING")
      .map(row => ({
        cardId: row.cardId,
        feedback: row.feedbackType,
        feedbackLabel: feedbackLabel(row.feedbackType)
      })),
    status: item.status === "IN_PROGRESS" ? "active" : "completed",
    api: true
  };
}

function normalizeExperience(result) {
  return (result.groups || []).map(group => ({
    title: group.methodName,
    count: group.mentionCount,
    videos: group.sourceVideoCount,
    summary: group.summary,
    split: group.hasDisagreement ? "存在不同意见，建议结合原评论理解。" : "暂无明显分歧。",
    comments: (group.comments || []).map(comment => [
      comment.authorName,
      comment.content
    ])
  }));
}

async function syncBackendState({ quiet = false } = {}) {
  try {
    const [cardResult, planResult] = await Promise.all([
      api("/action-cards"),
      api("/plans")
    ]);
    cards = cardResult.items.map(normalizeCard);
    state.savedCards = cards.filter(card => card.isSaved).map(card => card.id);
    state.plans = planResult.items.map(normalizePlan);
    if (planResult.activeSession) {
      state.activeSessionId = planResult.activeSession.id;
    }
    state.apiConnected = true;
    state.apiBase = API_BASE;
    if (!cards.some(card => card.id === state.selectedCard)) state.selectedCard = cards[0]?.id || "lateral-raise";
    if (!state.plans.some(plan => plan.id === state.selectedPlan)) state.selectedPlan = state.plans[0]?.id || state.selectedPlan;
    saveState();
    render();
  } catch (error) {
    state.apiConnected = false;
    saveState();
    if (!quiet) toast("业务后端未连接，已切回浏览器 Mock");
  }
}

function loadState() {
  try { return { ...defaultState, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") }; }
  catch { return structuredClone(defaultState); }
}
function saveState() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
function getCard(id = state.selectedCard) { return cards.find(card => card.id === id) || cards[0]; }
function getPlan(id = state.selectedPlan) { return state.plans.find(plan => plan.id === id) || state.plans[0]; }
function cardById(id) { return cards.find(card => card.id === id) || cards[0]; }
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char])); }
function route(view, data = {}) {
  state.view = view;
  Object.assign(state, data);
  saveState();
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}
function toast(message) {
  const root = document.getElementById("toast-root");
  root.innerHTML = `<div class="toast">${escapeHtml(message)}</div>`;
  const item = root.firstElementChild;
  requestAnimationFrame(() => item.classList.add("show"));
  setTimeout(() => item.classList.remove("show"), 2300);
}
function navItem(view, label, symbol) { return `<button class="nav-item ${state.view === view ? "active" : ""}" data-action="nav" data-view="${view}"><span class="nav-symbol">${symbol}</span>${label}</button>`; }
function shell(content) {
  const sourceMode = state.view === "source";
  return `<div class="app-shell ${sourceMode ? "source-shell" : ""}">
    <aside class="sidebar">
      <div class="brand"><div class="brand-mark">练</div><div><strong>练过</strong><small>从看过到练过</small></div></div>
      <nav class="nav-list">${navItem("plans", "练单", "01")} ${navItem("library", "动作库", "02")} ${navItem("me", "我的", "03")}</nav>
      <div class="sidebar-note"><p>${state.apiConnected ? "业务 API 已连接" : "本地演示空间"}</p><div class="status-row"><span class="status-dot"></span>${state.apiConnected ? "Business API 在线" : "浏览器 Mock 运行中"}</div></div>
    </aside>
    <main class="main">
      <header class="topbar"><div class="breadcrumbs"><span>GoFit</span><b>/</b><b>${breadcrumb()}</b></div><div class="top-actions"><button class="btn btn-ghost" data-action="nav" data-view="source">↩ 模拟抖音</button><span class="demo-chip">HACKATHON MVP</span><div class="avatar">季</div></div></header>
      <div class="content">${content}</div>
      <nav class="mobile-nav">${navItem("plans", "练单", "01")} ${navItem("library", "动作库", "02")} ${navItem("me", "我的", "03")}</nav>
    </main>
  </div>`;
}
function breadcrumb() { return ({ source: "模拟抖音", processing: "视频接入", card: "动作卡", plans: "练单", detail: "练单详情", library: "动作库", training: "训练中", feedback: "体感反馈", experience: "练友经验", safety: "安全提示", complete: "训练完成", me: "我的" })[state.view] || "练过"; }

function render() {
  if (processingTimer) { clearInterval(processingTimer); processingTimer = null; }
  const pages = { source: renderSource, processing: renderProcessing, card: renderCard, plans: renderPlans, detail: renderDetail, library: renderLibrary, training: renderTraining, feedback: renderFeedback, experience: renderExperience, safety: renderSafety, complete: renderComplete, me: renderMe };
  document.getElementById("app").innerHTML = shell(pages[state.view] ? pages[state.view]() : renderSource());
  bindActions();
}

function renderSource() {
  const feedCards = [cards[0], cards[1], cards[3]];
  return `<div class="feed-stage"><div class="feed-intro"><span class="eyebrow">P00 · 抖音视频流</span><h1>先刷到，再练过。</h1><p>从一条健身视频开始，把“看过”变成训练时用得上的动作卡。</p></div><section class="feed-viewport" aria-label="模拟抖音视频流">${feedCards.map((card, index) => `<article class="feed-item ${card.cover}" data-card="${card.id}"><div class="feed-overlay"><div class="feed-topline"><span class="feed-logo">抖音精选</span><span class="feed-follow">＋ 关注</span></div><button class="feed-play" data-action="play" aria-label="播放视频">▶</button><div class="feed-copy"><div class="feed-creator"><span class="creator-avatar">${card.creator.slice(0, 1)}</span><b>@${card.creator}</b><span class="feed-tag">健身教学</span></div><h2>${card.title}</h2><p>#${card.area} #动作教学 #练过</p><button class="btn btn-soft feed-open" data-action="open-processing" data-card="${card.id}">用练过打开 <span>↗</span></button></div><div class="feed-actions"><button data-action="feed-action" aria-label="点赞">♡<small>${index === 0 ? "12.8w" : index === 1 ? "7.4w" : "9.1w"}</small></button><button data-action="feed-action" aria-label="评论">◌<small>${index === 0 ? "2146" : "863"}</small></button><button data-action="feed-action" aria-label="收藏">☆<small>收藏</small></button><button data-action="feed-action" aria-label="分享">↗<small>分享</small></button></div></div></article>`).join("")}</section><div class="feed-hint"><span>上下滑动继续浏览</span><span>点击“用练过打开”进入动作卡</span></div></div>`;
}

function renderProcessing() {
  const current = Number(state.processingStep || 0);
  const steps = ["正在读取画面、语音和字幕", "正在确认动作和关键时间", "正在整理步骤、提示和肌群", "正在生成示范片段和动作卡"];
  setTimeout(() => {
    let next = Number(state.processingStep || 0) + 1;
    if (next >= steps.length) { state.processingStep = steps.length; saveState(); route("card", { activeTab: "full" }); return; }
    state.processingStep = next; saveState(); render();
  }, 850);
  return `<div class="processing"><div class="eyebrow">P01 · AI MOCK PIPELINE</div><div class="processing-orb">AI</div><h1>把视频整理成动作卡</h1><p class="lede" style="margin-inline:auto">不需要填写提示词。这里用 mock 模拟 AI 中心的处理状态，后续可替换为真实任务接口。</p><div class="steps">${steps.map((step, index) => `<div class="processing-step ${index === current ? "active" : ""} ${index < current ? "done" : ""}"><span class="step-icon">${index < current ? "✓" : index === current ? "·" : ""}</span><span>${step}</span>${index === current ? "<span style=\"margin-left:auto;font-size:11px\">处理中</span>" : ""}</div>`).join("")}</div><button class="btn btn-ghost" data-action="nav" data-view="source">← 返回原视频</button></div>`;
}

function renderCard() {
  const card = getCard();
  const full = state.activeTab !== "quick";
  return `<div class="page-heading"><div><div class="eyebrow">P02 · VIDEO ACTION CARD</div><h1>${card.name}</h1><p class="lede">${card.title}</p></div><button class="btn btn-secondary" data-action="nav" data-view="source">返回原视频</button></div>
    <div class="card-layout"><section class="action-visual ${card.cover}"><div class="visual-top"><span class="source-label">${card.source}</span><span>动作卡 · ${card.videoCount} 条关联视频</span></div><div class="visual-bottom"><h2>${card.name}</h2><p>一句话作用：保持肩部稳定，用可控的外展动作找到目标肌群。</p><span class="source-label">${card.creator} · 原视频 01:02</span></div></section>
    <section class="card-panel"><div class="tabs"><button class="tab ${full ? "active" : ""}" data-action="card-tab" data-tab="full">完整步骤</button><button class="tab ${!full ? "active" : ""}" data-action="card-tab" data-tab="quick">训练速记</button></div><div class="eyebrow">标准动作 · ${card.name}</div><div class="tag-row"><span class="tag">主要 · ${card.main}</span><span class="tag soft">辅助 · ${card.assist}</span><span class="tag soft">${card.equipment}</span></div>${full ? `<h3>动作步骤</h3><div class="step-list">${card.steps.map((item, index) => `<div class="step-item"><span class="step-number">0${index + 1}</span><p>${item[0]}</p><span class="timestamp">${item[1]}</span></div>`).join("")}</div><div class="keyline"></div><div class="tip-box"><strong>本视频关键提示</strong>${card.tip}</div>` : `<h3>动作暗号</h3><div style="font-size:25px;font-weight:800;letter-spacing:-.05em;line-height:1.25;margin:18px 0 22px">${card.cue}</div><div class="tip-box"><strong>训练时只记住这三件事</strong>动作做小一点、肩膀远离耳朵、下放慢一点。</div><div class="keyline"></div><p class="muted">当前为训练速记模式，查看完整步骤可回看本视频的时间戳证据。</p>`}<div class="card-actions"><button class="btn btn-primary" data-action="add-card" data-card="${card.id}">＋ 加入练单</button><button class="btn btn-secondary" data-action="toggle-save">${state.savedCards.includes(card.id) ? "已收藏" : "收藏动作卡"}</button></div><button class="experience-link" data-action="open-experience"><span>练友经验 · 整理自 ${card.videoCount} 条同动作视频的 ${card.experienceCount} 条公开评论</span><span>→</span></button></section></div>`;
}

function renderPlans() {
  const active = state.session && state.session.status === "active";
  return `<div class="page-heading"><div><div class="eyebrow">P03 · TRAINING PLANS</div><h1>你的练单。</h1><p class="lede">把具体的视频动作卡放进可重复使用的训练安排，开始训练时会生成独立记录。</p></div><button class="btn btn-primary" data-action="new-plan">＋ 新建练单</button></div>${active ? `<div class="panel" style="padding:18px;margin-bottom:18px;background:#fff6e7;border-color:#f0d39d"><div style="display:flex;justify-content:space-between;gap:15px;align-items:center"><div><b>还有一场训练没有结束</b><div class="muted">${escapeHtml(getPlan(state.session.planId).name)} · 已完成 ${state.session.index}/${state.session.cardIds.length}</div></div><button class="btn btn-primary" data-action="continue-training">继续训练 →</button></div></div>` : ""}<div class="section-label"><h2>我的练单</h2><span>${state.plans.length} 份已保存</span></div><div class="plans-grid">${state.plans.map((plan, index) => `<article class="plan-card ${index === 0 ? "featured" : ""}"><div class="plan-card-head"><div><h3>${escapeHtml(plan.name)}</h3><span class="card-meta">最近使用 ${plan.updated}</span></div><span class="count-pill">${plan.cardIds.length} 个动作</span></div><div class="plan-exercises">${plan.cardIds.map(id => `<span class="exercise-chip">${cardById(id).name}</span>`).join("")}</div><div class="plan-footer"><span class="card-meta">已使用 ${plan.uses} 次</span><div><button class="btn btn-secondary" data-action="open-plan" data-plan="${plan.id}">查看详情</button> <button class="btn btn-soft" data-action="start-plan" data-plan="${plan.id}">开始训练</button></div></div></article>`).join("")}</div><div class="section-label"><h2>最近练过</h2><span>反馈会影响下次推荐</span></div><div class="panel" style="padding:10px 18px">${state.history.map(row => `<div class="history-row"><div><b>${row.name}</b><div class="muted">${row.date}</div></div><span class="result-felt">${row.felt}</span></div>`).join("")}</div>`;
}

function renderDetail() {
  const plan = getPlan();
  const recommendations = state.recommendations?.[plan.id] || cards.filter(card => !plan.cardIds.includes(card.id)).slice(0, 2).map(card => ({ card, reasonText: `${card.main} · 和当前练单衔接自然` }));
  return `<div class="detail-header"><div><div class="eyebrow">P03A · EDIT PLAN</div><h1>${escapeHtml(plan.name)}</h1><span class="edit-name">自动保存 · ${plan.updated}</span></div><button class="btn btn-primary" data-action="start-plan" data-plan="${plan.id}">开始训练 →</button></div><div class="plan-summary"><div class="summary-stat"><b>${plan.cardIds.length}</b><span>个视频动作</span></div><div class="summary-stat"><b>${plan.uses}</b><span>使用次数</span></div><div class="summary-stat"><b>肩部</b><span>主要覆盖</span></div></div><div class="edit-layout"><section class="list-panel"><div class="section-label" style="margin:0 0 8px"><h2>动作顺序</h2><span>拖动调整 · 已保存</span></div>${plan.cardIds.length ? plan.cardIds.map((id, index) => { const card = cardById(id); return `<div class="plan-item"><span class="drag">0${index + 1}</span><div class="thumb thumb-${(index % 3) + 1}"></div><div><b>${card.name}</b><div class="muted">${card.creator} · ${card.main}</div></div><div class="item-actions"><button class="icon-btn" title="上移" data-action="move-item" data-direction="up" data-index="${index}">↑</button><button class="icon-btn" title="下移" data-action="move-item" data-direction="down" data-index="${index}">↓</button><button class="icon-btn" title="删除" data-action="remove-item" data-index="${index}">×</button></div></div>`; }).join("") : `<div class="empty-state">这份练单还没有动作。<br /><button class="btn btn-soft" style="margin-top:14px" data-action="select-card">添加第一张动作卡</button></div>`}<button class="btn btn-secondary btn-wide" style="margin-top:17px" data-action="select-card">＋ 添加动作</button></section><aside class="recommend-box"><div class="eyebrow">练单助手 · ${state.apiConnected ? "业务 API" : "本地 mock"}</div><h3>接下来可以考虑</h3><p>根据当前动作、肌群和历史体感，给你最多 3 个候选。是否加入由你决定。</p>${recommendations.map(item => `<div class="recommend-item"><b>${item.card.name}</b><span>${item.reasonText}</span><button class="btn" data-action="add-to-plan" data-card="${item.card.id}">加入这份练单</button></div>`).join("") || `<div class="muted">暂时没有合适候选。</div>`}</aside></div>`;
}

function renderLibrary() {
  return `<div class="page-heading"><div><div class="eyebrow">P05 · ACTION LIBRARY</div><h1>动作库。</h1><p class="lede">每一张卡都对应一条具体来源视频。标准动作只用于关联，不会混淆原视频内容。</p></div><button class="btn btn-secondary" data-action="nav" data-view="source">模拟抖音入口</button></div><div class="section-label"><h2>已整理动作</h2><span>${cards.length} 张视频动作卡</span></div><div class="library-grid">${cards.map(card => `<article class="library-card"><div class="library-art ${card.cover}"><span class="source-label">${card.source}</span><button class="save-button" data-action="save-card" data-card="${card.id}">${state.savedCards.includes(card.id) ? "★" : "☆"}</button></div><div class="library-card-body"><div class="library-card-head"><div><h3>${card.name}</h3><div class="muted">${card.creator}</div></div><span class="count-pill">${card.main}</span></div><p class="card-meta" style="margin:12px 0 0">${card.cue}</p><button class="btn btn-secondary" data-action="open-card" data-card="${card.id}">查看动作卡 →</button></div></article>`).join("")}</div>`;
}

function renderTraining() {
  const session = state.session || { cardIds: ["lateral-raise"], index: 0 };
  const card = cardById(session.cardIds[session.index] || session.cardIds[0]);
  const completed = session.completed || [];
  const progress = Math.round((session.index / session.cardIds.length) * 100);
  const recorded = session.currentRecorded;
  return `<div class="training-wrap"><div class="training-top"><div><div class="eyebrow">P06 · TRAINING SESSION</div><h2 style="margin:5px 0 0">${escapeHtml(getPlan(session.planId).name)}</h2><div class="muted">第 ${session.index + 1} / ${session.cardIds.length} 个动作</div><div class="session-progress"><span style="width:${progress}%"></span></div></div><button class="btn btn-secondary" data-action="exit-training">退出训练</button></div><div class="training-grid"><section class="training-card"><span class="session-badge">训练速记 · ${card.area}</span><div><h1>${card.name}</h1><p>${card.cue}</p><span class="source-label">${card.creator} · 来自本视频</span></div></section><aside class="training-side"><div class="eyebrow">现在只看这几件事</div><h2 style="font-size:23px">让动作保持简单。</h2><div class="training-tip"><b>动作提示</b>${card.tip}</div><h3>目标肌群</h3><div class="muscle-map"><div class="muscle active">主要<br /><b>${card.main}</b></div><div class="muscle">辅助<br /><b>${card.assist.split("、")[0]}</b></div></div><div class="keyline"></div>${recorded ? `<button class="btn btn-primary btn-wide" data-action="continue-after-feedback">继续下一个动作 →</button>` : `<button class="btn btn-primary btn-wide" data-action="open-feedback">练过了，记录体感 →</button>`}<button class="btn btn-ghost btn-wide" data-action="open-card" data-card="${card.id}">查看完整动作步骤</button></aside></div></div>`;
}

function renderFeedback() {
  const card = currentSessionCard();
  const options = [["TARGET_FELT", "目标部位有感觉", "肩中束在工作"], ["OTHER_FELT", "其他部位更酸", "选择实际感觉的位置"], ["NO_FEELING", "没找到明显感觉", "记录下来，下次调整"], ["TOO_HARD", "动作有点吃力", "这次先留下训练信号"], ["DISCOMFORT", "出现不适", "停止当前动作并查看安全提示"]];
  return `<div class="feedback-panel"><div class="eyebrow">P07 · BODY FEEDBACK</div><h1>这一组，身体怎么说？</h1><p class="lede">${card.name} · 你的反馈会保留在本次训练里，不会自动公开。</p><div class="feedback-card"><div class="feedback-options">${options.map(item => `<button class="feedback-option ${state.selectedFeedback === item[0] ? "selected" : ""}" data-action="choose-feedback" data-feedback="${item[0]}"><b>${item[1]}</b><span>${item[2]}</span></button>`).join("")}</div>${state.selectedFeedback === "OTHER_FELT" ? `<div><h3>哪里更有感觉？</h3><div class="body-options">${["手臂", "斜方肌", "前臂", "胸部"].map(body => `<button class="body-option ${state.selectedBody === body ? "selected" : ""}" data-action="choose-body" data-body="${body}">${body}</button>`).join("")}</div></div>` : ""}<button class="btn btn-primary btn-wide" data-action="submit-feedback">保存这次体感</button><button class="btn btn-ghost btn-wide" data-action="nav" data-view="training">返回训练</button></div></div>`;
}

function renderExperience() {
  const card = currentSessionCard();
  const question = state.experienceQuestion || "手臂更有感觉";
  const groups = state.currentExperienceGroups || experienceGroups;
  const sourceNote = state.currentExperienceNote || `AI 整理自 ${card.videoCount} 条同动作视频下的 ${card.experienceCount} 条公开评论`;
  return `<div class="experience-header"><div><div class="eyebrow">P08 · PEER EXPERIENCE</div><h1>练友经验。</h1><p class="lede">${card.name} · ${question}</p></div><div class="experience-source">${sourceNote}</div></div><div class="question-tabs"><button class="question-tab ${question === "手臂更有感觉" ? "active" : ""}">手臂更有感觉</button><button class="question-tab ${question === "目标肌群无感" ? "active" : ""}">目标肌群无感</button><button class="question-tab ${question === "重量或动作控制" ? "active" : ""}">重量或动作控制</button></div><div class="panel" style="padding:19px;margin-bottom:18px"><div class="eyebrow">当前视频是否提到</div><p style="margin:8px 0 0;font-size:12px;color:var(--muted)">当前视频在 <b style="color:var(--ink)">00:24</b> 提到：不要为了抬高而耸肩。下面的解决方法来自其他同动作视频的公开评论。</p></div><div class="experience-list">${groups.map((group, index) => `<article class="experience-card"><div class="experience-card-head"><div><h3>${group.title}</h3><p>${group.summary}</p></div><span class="mention">${group.count} 条 · ${group.videos} 视频</span></div><div style="display:flex;justify-content:space-between;align-items:center;gap:12px"><span class="muted">${group.split}</span><button class="btn btn-secondary" data-action="toggle-comments" data-index="${index}">查看依据</button></div><div class="comment-list" id="comments-${index}">${group.comments.map(comment => `<div class="comment"><strong>${comment[0]}</strong>${comment[1]}<div style="margin-top:6px;color:var(--green);font-size:10px">查看来源视频 · 对我有用</div></div>`).join("")}</div></article>`).join("") || `<div class="empty-state">暂时没有足够的同动作公开评论可以整理。</div>`}</div><div style="display:flex;gap:9px;margin-top:19px"><button class="btn btn-primary" data-action="back-training">返回训练</button><button class="btn btn-secondary" data-action="mark-useful">${state.useful.length ? "已标记有用" : "这组经验对我有用"}</button></div>`;
}

function renderSafety() {
  const card = currentSessionCard();
  return `<div class="safety-panel"><div class="safety-icon">!</div><div class="eyebrow" style="color:#a94029">P09 · SAFETY ROUTE</div><h1>先停止当前动作。</h1><p>练过不能判断不适的原因。如果不适持续、明显或突然出现，请停止训练并咨询教练、康复师或医疗专业人员。</p><div class="panel" style="padding:15px;background:rgba(255,255,255,.62);border-color:#f0c9bd"><b>当前动作：${card.name}</b><div class="muted" style="margin-top:3px">这条记录会被保存，并从之后的主动推荐中暂时排除。</div></div><div class="safety-actions"><button class="btn btn-danger" data-action="end-current">结束这个动作</button><button class="btn btn-secondary" data-action="exit-complete">退出本次训练</button><button class="btn btn-ghost" data-action="open-card" data-card="${card.id}">查看原视频的一般提示</button></div></div>`;
}

function renderComplete() {
  const session = state.session || { cardIds: ["lateral-raise"], completed: [] };
  const results = session.completed || [];
  return `<div class="page-heading"><div><div class="eyebrow">P10 · SESSION COMPLETE</div><p class="lede">本次训练已保存。原来的练单仍然保留，可以下次再次使用。</p></div></div><section class="complete-hero"><div><h1>今天练过 ${results.length} 个动作。</h1><p>${results.some(row => row.feedback === "OTHER_FELT") ? "你留下的体感会帮助下一次选择动作。" : "你的训练记录已经被记下来了。"}</p></div><div class="complete-mark">✓</div></section><div class="result-list">${results.map(row => `<div class="result-item"><div><b>${cardById(row.cardId).name}</b><span>${cardById(row.cardId).main} · ${row.feedbackLabel || "已完成"}</span></div><span class="result-felt">${row.feedbackLabel || "已完成"}</span></div>`).join("")}</div><div class="panel" style="padding:18px;margin-top:18px;background:#f3fbf2"><b>下次选择动作时，会参考这几条体感记录。</b><p class="muted" style="margin:5px 0 0">练友经验仍然只作为参考，不会自动替你决定练单。</p></div><div style="display:flex;gap:9px;margin-top:19px"><button class="btn btn-primary" data-action="nav" data-view="plans">返回练单</button><button class="btn btn-secondary" data-action="nav" data-view="me">查看我的记录</button></div>`;
}

function renderMe() {
  const latest = state.history[0];
  return `<div class="page-heading"><div><div class="eyebrow">P11 · YOUR SPACE</div><h1>我的。</h1><p class="lede">训练是你的记录，健身搭子只负责陪你记住那些已经做过的事。</p></div></div><div class="profile-hero"><section class="buddy-panel"><div class="eyebrow" style="color:#b9edc7">MY TRAINING BUDDY</div><h2>肩部，最近被你练过了。</h2><p>搭子小满陪你完成了 4 次训练，最近一次记录到：${latest ? latest.name : "还没有训练记录"}。</p><div class="buddy-art"></div></section><section class="profile-stats"><div class="profile-stat"><b>12</b><span>累计练过动作</span></div><div class="profile-stat"><b>4</b><span>陪伴完成训练</span></div><div class="profile-stat"><b>肩部</b><span>最近训练部位</span></div><div class="profile-stat"><b>2</b><span>已保存练单</span></div></section></div><div class="section-label"><h2>最近练过</h2><span>私密记录</span></div><div class="panel" style="padding:10px 18px">${state.history.map(row => `<div class="history-row"><div><b>${row.name}</b><div class="muted">${row.date} · 训练反馈仅自己可见</div></div><span class="result-felt">${row.felt}</span></div>`).join("")}</div>`;
}

function currentSessionCard() { const session = state.session || { cardIds: [state.selectedCard], index: 0 }; return cardById(session.cardIds[session.index] || state.selectedCard); }
function bindActions() {
  document.querySelectorAll("[data-action]").forEach(element => element.addEventListener("click", handleAction));
}

async function loadPlanRecommendations(planId) {
  if (!state.apiConnected) return;
  try {
    const result = await api(`/recommendations?planId=${encodeURIComponent(planId)}`);
    state.recommendations = state.recommendations || {};
    state.recommendations[planId] = (result.items || []).map(item => ({
      card: normalizeCard(item.card),
      reasonText: item.reasonText
    }));
    saveState();
  } catch {
    state.recommendations = state.recommendations || {};
  }
}

async function syncPlan(planId) {
  if (!state.apiConnected) return getPlan(planId);
  const result = await api(`/plans/${encodeURIComponent(planId)}`);
  const plan = normalizePlan(result);
  const index = state.plans.findIndex(item => item.id === plan.id);
  if (index >= 0) state.plans[index] = plan;
  else state.plans.unshift(plan);
  state.selectedPlan = plan.id;
  saveState();
  return plan;
}

async function loadExperience(problemTag = "ARMS_FELT_MORE") {
  const card = currentSessionCard();
  if (!state.apiConnected || !card.exerciseId) return;
  try {
    const result = await api(`/experiences?exerciseId=${encodeURIComponent(card.exerciseId)}&problemTag=${encodeURIComponent(problemTag)}&currentVideoId=${encodeURIComponent(card.videoId || "")}&fromTraining=${state.view === "training"}`);
    state.currentExperienceGroups = normalizeExperience(result);
    state.currentExperienceNote = result.sourceNote;
    saveState();
  } catch {
    state.currentExperienceGroups = null;
    state.currentExperienceNote = null;
  }
}

async function handleAction(event) {
  const el = event.currentTarget;
  const action = el.dataset.action;
  if (action === "nav") return route(el.dataset.view);
  if (action === "play") return toast("演示视频已准备，点击“用练过打开”开始体验");
  if (action === "open-processing") { state.selectedCard = el.dataset.card || state.selectedCard; state.processingStep = 0; return route("processing"); }
  if (action === "card-tab") { state.activeTab = el.dataset.tab; saveState(); return render(); }
  if (action === "open-card") { state.selectedCard = el.dataset.card; return route("card", { activeTab: "full" }); }
  if (action === "toggle-save" || action === "save-card") {
    const id = el.dataset.card || state.selectedCard;
    if (state.apiConnected) {
      try {
        const saved = !state.savedCards.includes(id);
        await api(`/action-cards/${encodeURIComponent(id)}/saved`, { method: saved ? "POST" : "DELETE" });
        await syncBackendState({ quiet: true });
        return toast(saved ? "已收藏到动作库" : "已取消收藏");
      } catch {
        toast("收藏接口暂时不可用，先用本地状态");
      }
    }
    state.savedCards = state.savedCards.includes(id) ? state.savedCards.filter(item => item !== id) : [...state.savedCards, id]; saveState(); render(); return toast(state.savedCards.includes(id) ? "已收藏到动作库" : "已取消收藏");
  }
  if (action === "open-experience") { await loadExperience("ARMS_FELT_MORE"); return route("experience", { experienceQuestion: "手臂更有感觉" }); }
  if (action === "new-plan") return showNewPlanModal();
  if (action === "open-plan") { state.selectedPlan = el.dataset.plan; await loadPlanRecommendations(el.dataset.plan); return route("detail"); }
  if (action === "start-plan") return startPlan(el.dataset.plan);
  if (action === "continue-training") return route("training");
  if (action === "select-card") return showCardPicker();
  if (action === "add-to-plan") { await addCardToPlan(el.dataset.card, state.selectedPlan); return; }
  if (action === "move-item") return moveItem(Number(el.dataset.index), el.dataset.direction);
  if (action === "remove-item") return removeItem(Number(el.dataset.index));
  if (action === "open-feedback") { state.selectedFeedback = null; state.selectedBody = null; return route("feedback"); }
  if (action === "continue-after-feedback") return advanceSession();
  if (action === "choose-feedback") { state.selectedFeedback = el.dataset.feedback; state.selectedBody = null; saveState(); return render(); }
  if (action === "choose-body") { state.selectedBody = el.dataset.body; saveState(); return render(); }
  if (action === "submit-feedback") return submitFeedback();
  if (action === "toggle-comments") { const comment = document.getElementById(`comments-${el.dataset.index}`); comment.classList.toggle("open"); return; }
  if (action === "mark-useful") { if (!state.useful.includes("experience")) state.useful.push("experience"); saveState(); render(); return toast("已记录，这个标记只帮助你整理训练经验"); }
  if (action === "back-training") return route("training");
  if (action === "end-current") return finishCurrent(true);
  if (action === "exit-complete") return completeSession(false);
  if (action === "exit-training") { if (confirm("保存当前进度并退出训练吗？")) { saveState(); route("plans"); } return; }
}

async function startPlan(planId) {
  const plan = getPlan(planId);
  if (state.apiConnected) {
    try {
      const result = await api(`/plans/${encodeURIComponent(planId)}/sessions`, { method: "POST" });
      state.selectedPlan = plan.id;
      state.session = normalizeSession(result);
      saveState();
      return route("training");
    } catch {
      toast("训练接口暂时不可用，先使用本地训练记录");
    }
  }
  state.selectedPlan = plan.id;
  state.session = { id: `session-${Date.now()}`, planId: plan.id, cardIds: [...plan.cardIds], index: 0, completed: [], status: "active" };
  plan.uses += 1; plan.updated = "刚刚"; saveState(); route("training");
}
async function submitFeedback() {
  if (!state.selectedFeedback) return toast("请选择一种体感");
  if (state.selectedFeedback === "OTHER_FELT" && !state.selectedBody) return toast("请选择实际更有感觉的部位");
  const feedbackCard = currentSessionCard();
  const currentProblemTag = state.selectedFeedback === "OTHER_FELT" ? "ARMS_FELT_MORE" : state.selectedFeedback === "NO_FEELING" ? "NO_TARGET_FEELING" : null;
  if (state.apiConnected && state.session?.api) {
    try {
      const itemId = state.session.itemIds[state.session.index];
      const result = await api(`/sessions/${encodeURIComponent(state.session.id)}/feedback`, {
        method: "POST",
        body: JSON.stringify({
          itemId,
          feedbackType: state.selectedFeedback,
          feltMuscles: state.selectedBody ? [state.selectedBody] : []
        })
      });
      state.session = normalizeSession(result.session);
      if (result.shouldShowSafety) {
        saveState();
        return route("safety");
      }
      if (result.problemTag && result.problemTag !== "DISCOMFORT") {
        saveFeedbackToHistory(feedbackCard, { pushSession: false });
        state.session.currentRecorded = true;
        state.experienceQuestion = result.problemTag === "ARMS_FELT_MORE" ? `${state.selectedBody || "其他部位"}更有感觉` : "目标肌群无感";
        await loadExperience(result.problemTag);
        saveState();
        return route("experience");
      }
      saveFeedbackToHistory(feedbackCard, { pushSession: false });
      return advanceSession();
    } catch {
      toast("反馈接口暂时不可用，先保存到本地");
    }
  }
  if (state.selectedFeedback === "DISCOMFORT") { saveState(); return route("safety"); }
  if (["OTHER_FELT", "NO_FEELING"].includes(state.selectedFeedback)) { saveFeedbackToHistory(); if (state.session) state.session.currentRecorded = true; state.experienceQuestion = state.selectedFeedback === "OTHER_FELT" ? `${state.selectedBody || "其他部位"}更有感觉` : "目标肌群无感"; await loadExperience(currentProblemTag); saveState(); return route("experience"); }
  return finishCurrent(false);
}
function feedbackLabel(value) { return ({ TARGET_FELT: "目标部位有感觉", OTHER_FELT: "其他部位更酸", NO_FEELING: "没找到明显感觉", TOO_HARD: "动作有点吃力", DISCOMFORT: "出现不适" })[value] || value; }
function saveFeedbackToHistory(card = currentSessionCard(), { pushSession = true } = {}) {
  state.history.unshift({ name: card.name, felt: feedbackLabel(state.selectedFeedback), date: "刚刚", color: "neutral" });
  if (pushSession && state.session) state.session.completed.push({ cardId: card.id, feedback: state.selectedFeedback, feedbackLabel: feedbackLabel(state.selectedFeedback), body: state.selectedBody });
}
function advanceSession() {
  if (!state.session) return route("plans");
  state.session.currentRecorded = false;
  state.selectedFeedback = null;
  state.selectedBody = null;
  if (state.session.api) {
    saveState();
    return state.session.status === "active" ? route("training") : route("complete");
  }
  if (state.session.index < state.session.cardIds.length - 1) { state.session.index += 1; saveState(); return route("training"); }
  return completeSession(true);
}
function finishCurrent(safetyStopped) {
  const card = currentSessionCard();
  if (!safetyStopped) { saveFeedbackToHistory(); }
  else if (state.session) state.session.completed.push({ cardId: card.id, feedback: "DISCOMFORT", feedbackLabel: "因不适停止" });
  state.selectedFeedback = null; state.selectedBody = null;
  return advanceSession();
}
function completeSession(finished) { if (state.session) state.session.status = finished ? "completed" : "ended"; saveState(); route("complete"); }
async function addCardToPlan(cardId, planId) {
  const plan = getPlan(planId);
  if (state.apiConnected) {
    try {
      const result = await api(`/plans/${encodeURIComponent(planId)}/items`, {
        method: "POST",
        body: JSON.stringify({ cardId })
      });
      const synced = normalizePlan(result);
      const index = state.plans.findIndex(item => item.id === synced.id);
      if (index >= 0) state.plans[index] = synced;
      state.selectedPlan = synced.id;
      await loadPlanRecommendations(synced.id);
      saveState();
      render();
      return toast(`已加入「${synced.name}」`);
    } catch {
      toast("加入练单接口暂时不可用，先使用本地状态");
    }
  }
  if (!plan.cardIds.includes(cardId)) { plan.cardIds.push(cardId); plan.updated = "刚刚"; saveState(); render(); toast(`已加入「${plan.name}」`); } else toast("这张卡已经在这份练单里了");
}
async function removeItem(index) {
  const plan = getPlan();
  if (state.apiConnected && plan.itemIds?.[index]) {
    try {
      const result = await api(`/plans/${encodeURIComponent(plan.id)}/items/${encodeURIComponent(plan.itemIds[index])}`, { method: "DELETE" });
      const synced = normalizePlan(result);
      const planIndex = state.plans.findIndex(item => item.id === synced.id);
      if (planIndex >= 0) state.plans[planIndex] = synced;
      saveState();
      render();
      return toast("已从练单移除");
    } catch {
      toast("删除接口暂时不可用，先使用本地状态");
    }
  }
  plan.cardIds.splice(index, 1); plan.updated = "刚刚"; saveState(); render(); toast("已从练单移除");
}
async function moveItem(index, direction) {
  const plan = getPlan(); const target = direction === "up" ? index - 1 : index + 1; if (target < 0 || target >= plan.cardIds.length) return;
  [plan.cardIds[index], plan.cardIds[target]] = [plan.cardIds[target], plan.cardIds[index]];
  if (plan.itemIds) [plan.itemIds[index], plan.itemIds[target]] = [plan.itemIds[target], plan.itemIds[index]];
  plan.updated = "刚刚";
  if (state.apiConnected && plan.itemIds) {
    try {
      await api(`/plans/${encodeURIComponent(plan.id)}`, {
        method: "PATCH",
        body: JSON.stringify({ orderedItemIds: plan.itemIds })
      });
    } catch {
      toast("排序接口暂时不可用，先使用本地状态");
    }
  }
  saveState(); render();
}

function showNewPlanModal() {
  showModal(`<div class="modal-head"><h2>新建一份练单</h2><button class="close" data-action="close-modal">×</button></div><p class="muted">先给它一个名字，之后再挑选具体的视频动作卡。</p><input id="new-plan-name" class="form-input" value="未命名练单" autofocus /><button class="btn btn-primary btn-wide" data-action="create-plan">创建并添加动作</button>`);
}
function showCardPicker() {
  showModal(`<div class="modal-head"><div><div class="eyebrow">P04 · PICK ACTION</div><h2>添加一张动作卡</h2></div><button class="close" data-action="close-modal">×</button></div><p class="muted">推荐只提供候选，不会自动加入。</p>${cards.map(card => `<button class="plan-choice" data-action="choose-card-for-plan" data-card="${card.id}"><span><b>${card.name}</b><span>${card.main} · ${card.creator}</span></span><span class="choice-arrow">＋</span></button>`).join("")}`);
}
function showAddPlanModal(cardId) {
  showModal(`<div class="modal-head"><div><div class="eyebrow">ADD TO PLAN</div><h2>加入哪份练单？</h2></div><button class="close" data-action="close-modal">×</button></div><p class="muted">加入的是具体视频动作卡：${getCard(cardId).name}。</p>${state.plans.map(plan => `<button class="plan-choice" data-action="choose-plan" data-plan="${plan.id}" data-card="${cardId}"><span><b>${escapeHtml(plan.name)}</b><span>${plan.cardIds.length} 个动作 · 最近编辑</span></span><span class="choice-arrow">→</span></button>`).join("")}<button class="plan-choice" data-action="create-plan-with-card" data-card="${cardId}"><span><b>新建练单</b><span>创建草稿并加入这张卡</span></span><span class="choice-arrow">＋</span></button>`);
}
function showModal(content) { document.body.insertAdjacentHTML("beforeend", `<div class="modal-backdrop" id="modal-backdrop"><div class="modal">${content}</div></div>`); document.querySelectorAll("#modal-backdrop [data-action]").forEach(element => element.addEventListener("click", handleModalAction)); }
function closeModal() { document.getElementById("modal-backdrop")?.remove(); }
async function handleModalAction(event) {
  const el = event.currentTarget; const action = el.dataset.action;
  if (action === "close-modal") return closeModal();
  if (action === "create-plan") {
    const name = document.getElementById("new-plan-name").value.trim() || "未命名练单";
    if (state.apiConnected) {
      try {
        const result = await api("/plans", { method: "POST", body: JSON.stringify({ name }) });
        const plan = normalizePlan(result);
        state.plans.unshift(plan);
        state.selectedPlan = plan.id;
        closeModal();
        saveState();
        return route("detail");
      } catch {
        toast("创建练单接口暂时不可用，先用本地草稿");
      }
    }
    const plan = { id: `plan-${Date.now()}`, name, cardIds: [], uses: 0, updated: "刚刚" }; state.plans.unshift(plan); state.selectedPlan = plan.id; closeModal(); saveState(); return route("detail");
  }
  if (action === "choose-plan") { await addCardToPlan(el.dataset.card, el.dataset.plan); closeModal(); state.selectedPlan = el.dataset.plan; return route("detail"); }
  if (action === "create-plan-with-card") {
    if (state.apiConnected) {
      try {
        const result = await api("/plans", { method: "POST", body: JSON.stringify({ name: "未命名练单", initialCardId: el.dataset.card }) });
        const plan = normalizePlan(result);
        state.plans.unshift(plan);
        state.selectedPlan = plan.id;
        closeModal();
        saveState();
        return route("detail");
      } catch {
        toast("创建练单接口暂时不可用，先用本地草稿");
      }
    }
    const plan = { id: `plan-${Date.now()}`, name: "未命名练单", cardIds: [el.dataset.card], uses: 0, updated: "刚刚" }; state.plans.unshift(plan); state.selectedPlan = plan.id; closeModal(); saveState(); return route("detail");
  }
  if (action === "choose-card-for-plan") { await addCardToPlan(el.dataset.card, state.selectedPlan); closeModal(); return; }
}

const originalHandleAction = handleAction;
handleAction = async function(event) {
  if (event.currentTarget.dataset.action === "add-card") return showAddPlanModal(event.currentTarget.dataset.card);
  return originalHandleAction(event);
};

render();
syncBackendState({ quiet: true });
