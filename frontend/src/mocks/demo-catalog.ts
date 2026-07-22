export type DemoBodyRegion = "肩部" | "背部";

export type DemoComment = {
  id: string;
  videoId: string;
  videoTitle: string;
  authorName: string;
  content: string;
  sourceUrl: string;
  problemTag: "ARMS_FELT_MORE";
  riskType: "NORMAL";
};

export type DemoCatalogItem = {
  cardId: string;
  exerciseId: string;
  actionName: string;
  aliases: string[];
  bodyRegion: DemoBodyRegion;
  primaryMuscles: string[];
  secondaryMuscles: string[];
  equipment: string[];
  video: {
    videoId: string;
    title: string;
    creatorName: string;
    sourceUrl: string;
    assetFileName: string;
    durationLabel: string;
    previewSecond: number;
  };
  card: {
    cue: string;
    steps: string[];
    reminder: string;
    mistake: string;
    correction: string;
    additionalErrors?: Array<{
      mistake: string;
      correction: string;
    }>;
    tips: string[];
  };
  experience: {
    problemTitle: string;
    methodName: string;
    summary: string;
    disagreement: string;
    projectedMentions: number;
  };
  comments: DemoComment[];
};

type CatalogInput = Omit<DemoCatalogItem, "cardId" | "comments"> & {
  comments: Array<[authorName: string, content: string]>;
};

function defineItem(input: CatalogInput): DemoCatalogItem {
  return {
    ...input,
    cardId: input.video.videoId,
    comments: input.comments.map(([authorName, content], index) => ({
      id: `comment_${input.video.videoId}_${index + 1}`,
      videoId: input.video.videoId,
      videoTitle: input.video.title,
      authorName,
      content,
      sourceUrl: `${input.video.sourceUrl}#comment-${index + 1}`,
      problemTag: "ARMS_FELT_MORE",
      riskType: "NORMAL",
    })),
  };
}

export const demoCatalog: DemoCatalogItem[] = [
  defineItem({
    exerciseId: "action_lateral_raise",
    actionName: "哑铃侧平举",
    aliases: ["侧平举", "站姿哑铃侧平举"],
    bodyRegion: "肩部",
    primaryMuscles: ["三角肌中束"],
    secondaryMuscles: ["三角肌前束", "斜方肌"],
    equipment: ["哑铃"],
    video: { videoId: "video_lateral_raise_demo", title: "侧平举总是手臂酸？新手先记住这 3 点", creatorName: "阿哲的训练课", sourceUrl: "https://example.test/videos/lateral-raise", assetFileName: "01-lateral-raise.mp4", durationLabel: "00:42", previewSecond: 1 },
    card: { cue: "肩放松 → 肘带动 → 缓慢落", steps: ["自然站稳，双手持哑铃，肩膀保持放松。", "肘部微屈，用手肘带动手臂向两侧抬起。", "抬到接近肩高后，控制速度缓慢下放。"], reminder: "手腕保持中立，肩膀始终远离耳朵。", mistake: "为了抬高而耸肩或借惯性甩起。", correction: "减轻重量，只抬到能维持肩部发力的高度。", additionalErrors: [{ mistake: "下放过快，突然卸力。", correction: "保持肩部张力，用大约 2 秒缓慢下放，不要让哑铃直接掉下来。" }], tips: ["不要耸肩。", "抬到接近肩高。", "控制下放。"] },
    experience: { problemTitle: "手臂比肩中束更有感觉？", methodName: "先减轻重量，再用手肘带动", summary: "练友普遍提到，重量过大时手臂和斜方肌更容易抢力；先减重，再想象手肘向两侧打开。", disagreement: "少数人认为动作路径比重量更关键。", projectedMentions: 21 },
    comments: [["小白肩训", "从 7.5kg 降到 5kg 后，下放终于能控制住，肩中束感觉明显多了。"], ["今天练肩", "想手肘往两边推开，不要想着手腕把哑铃拎起来。"]],
  }),
  defineItem({
    exerciseId: "action_shoulder_press",
    actionName: "坐姿哑铃推肩",
    aliases: ["哑铃推肩", "坐姿推举"],
    bodyRegion: "肩部",
    primaryMuscles: ["三角肌前束", "三角肌中束"],
    secondaryMuscles: ["肱三头肌"],
    equipment: ["哑铃", "训练凳"],
    video: { videoId: "video_shoulder_press_demo", title: "坐姿推肩：新手先把躯干稳定住", creatorName: "GoFit Demo Coach", sourceUrl: "https://example.test/videos/shoulder-press", assetFileName: "02-shoulder-press.mp4", durationLabel: "00:51", previewSecond: 10 },
    card: { cue: "背贴稳 → 向上推 → 稳稳落", steps: ["调整靠背，双脚踩稳，哑铃停在耳朵两侧。", "收紧核心，沿舒适路径向上推起。", "肘部不锁死，缓慢回落到起始位置。"], reminder: "全程让腰背保持稳定，不用后仰换取高度。", mistake: "腰部过度反弓，哑铃在头顶碰撞。", correction: "降低重量并缩小回落幅度，让前臂尽量保持竖直。", tips: ["背部贴住靠垫。", "手肘不要锁死。", "回落保持控制。"] },
    experience: { problemTitle: "推肩时手臂先累？", methodName: "先稳定躯干和前臂", summary: "练友建议先把靠背、脚位和前臂角度固定，再逐步增加重量。", disagreement: "靠背角度因肩关节舒适度而异。", projectedMentions: 14 },
    comments: [["训练打卡员", "把靠背调好、脚踩稳以后，推的时候不再一直晃。"], ["慢慢加重量", "我把重量降了一档，前臂保持竖直后肩膀参与感更清楚。"]],
  }),
  defineItem({
    exerciseId: "action_reverse_fly",
    actionName: "俯身反向飞鸟",
    aliases: ["反向飞鸟", "俯身飞鸟"],
    bodyRegion: "肩部",
    primaryMuscles: ["三角肌后束"],
    secondaryMuscles: ["菱形肌", "斜方肌中部"],
    equipment: ["哑铃"],
    video: { videoId: "video_reverse_fly_demo", title: "反向飞鸟：别让斜方肌抢活", creatorName: "小贺的训练笔记", sourceUrl: "https://example.test/videos/reverse-fly", assetFileName: "03-reverse-fly.mp4", durationLabel: "00:48", previewSecond: 7 },
    card: { cue: "俯身稳 → 肘向外 → 慢慢收", steps: ["髋部向后折叠，保持脊柱自然。", "肘部微屈，向身体两侧展开。", "后肩收紧后停顿，再控制回到起点。"], reminder: "动作幅度不必很大，优先保持后肩持续发力。", mistake: "耸肩并用手腕把哑铃甩高。", correction: "放松手腕，让手肘沿弧线向外展开。", tips: ["背部保持稳定。", "手肘向外展开。", "避免耸肩。"] },
    experience: { problemTitle: "反向飞鸟总是上背酸？", methodName: "把动作做小，手肘向外", summary: "练友更容易通过小幅度、慢速度和放松手腕找到后肩。", disagreement: "不同俯身角度会改变上背参与程度。", projectedMentions: 16 },
    comments: [["后束补课", "幅度做小以后，终于不是斜方肌先酸了。"], ["不甩哑铃", "手肘往外走、手腕放松这个提示特别有用。"]],
  }),
  defineItem({
    exerciseId: "action_front_raise",
    actionName: "哑铃前平举",
    aliases: ["前平举", "站姿前举"],
    bodyRegion: "肩部",
    primaryMuscles: ["三角肌前束"],
    secondaryMuscles: ["胸大肌上部"],
    equipment: ["哑铃"],
    video: { videoId: "video_front_raise_demo", title: "前平举：身体别跟着重量后仰", creatorName: "阿元练肩", sourceUrl: "https://example.test/videos/front-raise", assetFileName: "04-front-raise.mp4", durationLabel: "00:36", previewSecond: 4 },
    card: { cue: "核心稳 → 向前抬 → 控制落", steps: ["双脚站稳，哑铃放在大腿前侧。", "核心收紧，手臂向前举至接近肩高。", "短暂停顿后缓慢回到起点。"], reminder: "躯干保持安静，不要用后仰制造惯性。", mistake: "重量过大，身体前后摆动。", correction: "减轻重量，单侧交替完成也可以。", tips: ["身体不要后仰。", "抬至接近肩高。", "下放保持控制。"] },
    experience: { problemTitle: "前平举时腰背代偿？", methodName: "收紧核心并降低重量", summary: "练友建议先消除身体摆动，再考虑次数和重量。", disagreement: "双手同时或交替完成都有人偏好。", projectedMentions: 11 },
    comments: [["肩前束日记", "重量轻一点、肚子收紧以后，腰不再跟着晃。"], ["动作先做稳", "抬到肩高就够了，再高我就会不自觉后仰。"]],
  }),
  defineItem({
    exerciseId: "action_face_pull",
    actionName: "绳索面拉",
    aliases: ["面拉", "绳索面部拉"],
    bodyRegion: "肩部",
    primaryMuscles: ["三角肌后束"],
    secondaryMuscles: ["冈下肌", "斜方肌中部"],
    equipment: ["龙门架", "绳索把手"],
    video: { videoId: "video_face_pull_demo", title: "绳索面拉：拉向眉眼，不是拉向胸口", creatorName: "训练家101", sourceUrl: "https://example.test/videos/face-pull", assetFileName: "05-face-pull.mp4", durationLabel: "00:54", previewSecond: 8 },
    card: { cue: "肩胛稳 → 拉向脸 → 外旋停", steps: ["绳索调到面部高度，双手握住绳端。", "肩胛保持稳定，肘部向外拉开。", "绳端来到脸两侧后停顿，再缓慢还原。"], reminder: "手肘和肩膀保持舒适，不要为了外旋强行加大范围。", mistake: "把绳索拉向胸口，变成普通划船。", correction: "降低重量，让绳索朝眉眼方向移动。", tips: ["绳索保持面部高度。", "肘部向外打开。", "回程不要卸力。"] },
    experience: { problemTitle: "面拉只感觉到手臂？", methodName: "调高绳索并把肘向外打开", summary: "练友认为绳索高度和拉向脸部的路径，是找到后肩的关键。", disagreement: "拉向额头或鼻梁的具体高度因人而异。", projectedMentions: 13 },
    comments: [["后肩加餐", "把绳索调到眼睛高度后，动作终于不像划船了。"], ["圆肩自救中", "重量轻一点，拉到脸旁停一下，后肩感觉会更明显。"]],
  }),
  defineItem({
    exerciseId: "action_lat_pulldown",
    actionName: "高位下拉",
    aliases: ["下拉", "宽握高位下拉"],
    bodyRegion: "背部",
    primaryMuscles: ["背阔肌"],
    secondaryMuscles: ["大圆肌", "肱二头肌"],
    equipment: ["高位下拉器"],
    video: { videoId: "video_lat_pulldown_demo", title: "高位下拉：新手找到背部发力的 3 个提示", creatorName: "背部训练笔记", sourceUrl: "https://example.test/videos/lat-pulldown", assetFileName: "06-lat-pulldown.mp4", durationLabel: "00:58", previewSecond: 9 },
    card: { cue: "肩胛下沉 → 肘向下 → 慢慢放", steps: ["坐稳并固定大腿，双手握住横杆。", "先让肩胛下沉，再想象手肘向裤兜移动。", "横杆接近上胸后，控制手臂向上还原。"], reminder: "躯干只需轻微后倾，不要反复借力摆动。", mistake: "用手臂硬拉，并大幅向后仰。", correction: "减轻重量，先完成肩胛下沉再弯曲手肘。", tips: ["先沉肩。", "用手肘向下拉。", "回程保持控制。"] },
    experience: { problemTitle: "高位下拉只有手臂酸？", methodName: "先沉肩，再让手肘向下", summary: "练友反复提到先减重、完成肩胛下沉，再把注意力放在手肘路径上。", disagreement: "握距宽窄会影响每个人的舒适感。", projectedMentions: 24 },
    comments: [["背阔肌寻路", "先沉肩再拉之后，二头肌没有以前那么快酸了。"], ["下拉学习中", "想象肘往裤兜走，比想着把杆拉下来更容易找到背。"]],
  }),
  defineItem({
    exerciseId: "action_seated_cable_row",
    actionName: "坐姿绳索划船",
    aliases: ["坐姿划船", "绳索划船"],
    bodyRegion: "背部",
    primaryMuscles: ["背阔肌", "菱形肌"],
    secondaryMuscles: ["斜方肌中部", "肱二头肌"],
    equipment: ["坐姿划船器"],
    video: { videoId: "video_seated_row_demo", title: "坐姿划船：别把身体变成钟摆", creatorName: "背练研究所", sourceUrl: "https://example.test/videos/seated-row", assetFileName: "07-seated-cable-row.mp4", durationLabel: "00:49", previewSecond: 6 },
    card: { cue: "坐稳 → 肘向后 → 肩胛合", steps: ["双脚踩稳，躯干保持自然直立。", "手肘贴近身体向后移动，把手拉向腹部。", "肩胛自然靠拢后，控制手臂向前伸。"], reminder: "前后移动来自肩胛和手臂，不靠躯干大幅摆动。", mistake: "身体前后甩动，用惯性完成划船。", correction: "降低重量，让胸口始终朝前。", tips: ["躯干保持稳定。", "手肘贴近身体。", "回程不要含胸塌腰。"] },
    experience: { problemTitle: "划船时手臂先没力？", methodName: "固定躯干，让手肘贴身向后", summary: "练友建议先减少身体摆动，再用手肘向后带动把手。", disagreement: "回程是否允许轻微前伸存在不同习惯。", projectedMentions: 17 },
    comments: [["划船不摇摆", "把重量降下来不再前后晃，背中间反而更有感觉。"], ["背日记录", "手肘贴着身体往后走，比用手拉把手好理解。"]],
  }),
  defineItem({
    exerciseId: "action_one_arm_dumbbell_row",
    actionName: "单臂哑铃划船",
    aliases: ["单臂划船", "哑铃划船"],
    bodyRegion: "背部",
    primaryMuscles: ["背阔肌"],
    secondaryMuscles: ["菱形肌", "肱二头肌"],
    equipment: ["哑铃", "训练凳"],
    video: { videoId: "video_one_arm_row_demo", title: "单臂哑铃划船：髋和肩别跟着翻", creatorName: "力量新手村", sourceUrl: "https://example.test/videos/one-arm-row", assetFileName: "08-one-arm-dumbbell-row.mp4", durationLabel: "00:46", previewSecond: 5 },
    card: { cue: "躯干稳 → 肘向髋 → 慢慢放", steps: ["一手一膝支撑训练凳，背部保持自然。", "工作侧手肘朝髋部方向向后拉。", "哑铃接近身体后停顿，再完全控制下放。"], reminder: "保持骨盆和肩膀朝向地面，避免翻转身体。", mistake: "向上提哑铃时同时转动躯干。", correction: "缩小幅度并收紧核心，让手肘朝髋部移动。", tips: ["支撑侧保持稳定。", "手肘拉向髋部。", "下放时背阔肌拉长。"] },
    experience: { problemTitle: "单臂划船总是肩膀酸？", methodName: "固定躯干，手肘拉向髋部", summary: "练友更推荐先稳住骨盆和肩线，再寻找手肘靠近髋部的路径。", disagreement: "哑铃靠近腰部的具体位置因臂长而异。", projectedMentions: 15 },
    comments: [["左背补课", "不再转身体以后，重量虽然轻了，但背阔肌感觉更连续。"], ["单臂划船打卡", "肘往裤兜拉这个提示，比单纯往上提好用。"]],
  }),
  defineItem({
    exerciseId: "action_chest_supported_row",
    actionName: "上斜凳俯卧划船",
    aliases: ["胸托划船", "俯卧哑铃划船"],
    bodyRegion: "背部",
    primaryMuscles: ["菱形肌", "斜方肌中部"],
    secondaryMuscles: ["背阔肌", "三角肌后束"],
    equipment: ["哑铃", "上斜训练凳"],
    video: { videoId: "video_chest_supported_row_demo", title: "胸托划船：不借腰也能练到上背", creatorName: "稳稳练背", sourceUrl: "https://example.test/videos/chest-supported-row", assetFileName: "09-chest-supported-row.mp4", durationLabel: "00:44", previewSecond: 7 },
    card: { cue: "胸贴凳 → 肘向后 → 顶端停", steps: ["调整上斜凳，让胸口稳定贴住靠垫。", "双手持哑铃，手肘沿舒适角度向后拉。", "肩胛靠拢后停顿，再缓慢伸直手臂。"], reminder: "胸口不要离开靠垫，颈部保持自然。", mistake: "为了拉高而抬起胸口、伸展腰背。", correction: "减轻重量，在胸口不离凳的范围内完成。", tips: ["胸口贴住靠垫。", "颈部保持自然。", "顶端停顿一秒。"] },
    experience: { problemTitle: "胸托划船还是手臂累？", methodName: "放松握力并在顶端停顿", summary: "练友建议减少死握，在胸托稳定的前提下感受肩胛靠拢。", disagreement: "手肘打开角度会改变上背和背阔肌侧重。", projectedMentions: 12 },
    comments: [["上背训练日", "胸口一直贴着凳子，终于不会靠腰把重量甩起来。"], ["握力别太紧", "手只像钩子一样挂住，顶端停一下，上背感觉更清楚。"]],
  }),
  defineItem({
    exerciseId: "action_straight_arm_pulldown",
    actionName: "直臂下压",
    aliases: ["直臂下拉", "绳索直臂下压"],
    bodyRegion: "背部",
    primaryMuscles: ["背阔肌"],
    secondaryMuscles: ["大圆肌", "肱三头肌长头"],
    equipment: ["龙门架", "直杆"],
    video: { videoId: "video_straight_arm_pulldown_demo", title: "直臂下压：保持手肘角度，别做成肱三头下压", creatorName: "背阔肌说明书", sourceUrl: "https://example.test/videos/straight-arm-pulldown", assetFileName: "10-straight-arm-pulldown.mp4", durationLabel: "00:47", previewSecond: 6 },
    card: { cue: "髋后坐 → 直臂压 → 背阔收", steps: ["面对龙门架站稳，髋部轻微向后。", "手肘保持微屈但角度固定，把横杆压向大腿。", "背阔肌收紧后，控制横杆回到头部前上方。"], reminder: "动作来自肩关节，不要反复弯曲手肘。", mistake: "手肘不断屈伸，把动作做成三头肌下压。", correction: "降低重量并固定手肘角度，想象用腋窝向下夹。", tips: ["手肘角度固定。", "横杆压向大腿。", "回程让背阔肌拉长。"] },
    experience: { problemTitle: "直臂下压只有手臂酸？", methodName: "锁定手肘角度，用腋窝向下夹", summary: "练友常用固定手肘和“腋窝向下夹”的提示减少手臂主导。", disagreement: "直杆或绳索的手感因人而异。", projectedMentions: 18 },
    comments: [["背阔肌上线", "手肘不再反复弯以后，动作终于不是三头下压了。"], ["直臂练习生", "想象腋窝夹住东西往下压，背两侧会更容易发力。"]],
  }),
];

// 评论聚合需要“同动作、跨视频”。这四条来源只用于练友经验，不进入 10 条主演示视频列表。
export const relatedPeerComments: DemoComment[] = [
  { id: "comment_lateral_related_1", videoId: "video_lateral_raise_light", videoTitle: "侧平举手臂先酸？先把重量降下来", authorName: "肩部新手", content: "重量减半后能慢慢放下来，肩旁边终于有持续感觉。", sourceUrl: "https://example.test/videos/lateral-raise-light#comment-1", problemTag: "ARMS_FELT_MORE", riskType: "NORMAL" },
  { id: "comment_lateral_related_2", videoId: "video_lateral_raise_elbow", videoTitle: "侧平举不要用手腕提", authorName: "慢慢练", content: "手肘带着走、手腕放松，动作小一点也可以。", sourceUrl: "https://example.test/videos/lateral-raise-elbow#comment-1", problemTag: "ARMS_FELT_MORE", riskType: "NORMAL" },
  { id: "comment_pulldown_related_1", videoId: "video_lat_pulldown_elbow", videoTitle: "高位下拉：肘部向裤兜走", authorName: "背训第一月", content: "不想着拉杆，只想着肘向下，二头没那么抢了。", sourceUrl: "https://example.test/videos/lat-pulldown-elbow#comment-1", problemTag: "ARMS_FELT_MORE", riskType: "NORMAL" },
  { id: "comment_pulldown_related_2", videoId: "video_lat_pulldown_light", videoTitle: "高位下拉先别急着加重量", authorName: "新手练背", content: "减重后先沉肩，再开始下拉，背阔肌的拉伸感明显很多。", sourceUrl: "https://example.test/videos/lat-pulldown-light#comment-1", problemTag: "ARMS_FELT_MORE", riskType: "NORMAL" },
];

export const videoWorkflowRequests = demoCatalog.map((item) => ({
  requestId: `workflow_${item.video.videoId}`,
  sourceVideo: {
    videoId: item.video.videoId,
    title: item.video.title,
    creatorName: item.video.creatorName,
    sourceUrl: item.video.sourceUrl,
  },
  videoPath: `../../demo-videos/${item.video.assetFileName}`,
  standardActionCandidates: [{
    standardActionId: item.exerciseId,
    name: item.actionName,
    aliases: item.aliases,
    bodyRegion: item.bodyRegion,
    primaryMuscles: item.primaryMuscles,
    secondaryMuscles: item.secondaryMuscles,
    equipment: item.equipment,
  }],
}));
