import rawLateralRaise from "./lateral-raise.json";
import {
  actionCardResponseSchema,
  type ActionCardResponse,
  type ExperienceGroup,
} from "../domain";

const lateralRaise = actionCardResponseSchema.parse(rawLateralRaise);

function variant(
  base: ActionCardResponse,
  values: {
    requestId: string;
    standardActionId: string;
    videoId: string;
    title: string;
    creator: string;
    actionName: string;
    bodyRegion: string;
    primary: string[];
    secondary: string[];
    equipment: string[];
    cue: string;
    tips: string[];
  },
): ActionCardResponse {
  return {
    ...structuredClone(base),
    requestId: values.requestId,
    standardAction: {
      standardActionId: values.standardActionId,
      confidence: 0.96,
      decision: "MATCHED",
    },
    actionCard: {
      ...structuredClone(base.actionCard),
      sourceVideo: {
        videoId: values.videoId,
        title: values.title,
        creatorName: values.creator,
        sourceUrl: `https://example.test/videos/${values.videoId}`,
      },
      actionName: values.actionName,
      bodyRegion: values.bodyRegion,
      primaryMuscles: values.primary,
      secondaryMuscles: values.secondary,
      equipment: values.equipment,
      trainingSide: {
        ...structuredClone(base.actionCard.trainingSide),
        quickCue: {
          text: values.cue,
          evidenceIds: ["asr_setup", "asr_raise", "asr_lower"],
        },
        quickTips: values.tips.map((text, index) => ({
          text,
          evidenceIds: [`asr_tip_${index + 1}`],
        })),
      },
    },
  };
}

export const actionCards: Record<string, ActionCardResponse> = {
  video_lateral_raise_demo: lateralRaise,
  video_front_raise_demo: variant(lateralRaise, {
    requestId: "demo_action_card_002",
    standardActionId: "action_front_raise",
    videoId: "video_front_raise_demo",
    title: "前平举，肩前束这样找感觉",
    creator: "阿元练肩",
    actionName: "哑铃前平举",
    bodyRegion: "肩部",
    primary: ["三角肌前束"],
    secondary: ["三角肌中束"],
    equipment: ["哑铃"],
    cue: "核心稳 → 向前抬 → 控制落",
    tips: ["身体不要后仰。", "抬至接近肩高。", "下放保持控制。"],
  }),
  video_reverse_fly_demo: variant(lateralRaise, {
    requestId: "demo_action_card_003",
    standardActionId: "action_reverse_fly",
    videoId: "video_reverse_fly_demo",
    title: "反向飞鸟，别让斜方肌抢活",
    creator: "小贺的训练笔记",
    actionName: "俯身反向飞鸟",
    bodyRegion: "肩部",
    primary: ["三角肌后束"],
    secondary: ["斜方肌中部"],
    equipment: ["哑铃"],
    cue: "俯身稳 → 向外展 → 慢慢收",
    tips: ["背部保持稳定。", "手肘向外展开。", "避免耸肩。"],
  }),
  video_shoulder_press_demo: variant(lateralRaise, {
    requestId: "demo_action_card_004",
    standardActionId: "action_shoulder_press",
    videoId: "video_shoulder_press_demo",
    title: "坐姿推肩，新手稳定版本",
    creator: "GoFit Demo Coach",
    actionName: "坐姿哑铃推肩",
    bodyRegion: "肩部",
    primary: ["三角肌前束"],
    secondary: ["三角肌中束", "肱三头肌"],
    equipment: ["哑铃", "训练凳"],
    cue: "背贴稳 → 向上推 → 稳稳落",
    tips: ["腰背贴住靠垫。", "不要锁死手肘。", "回落到舒适位置。"],
  }),
};

export const cardIds = Object.keys(actionCards);

export const recommendations = [
  {
    cardId: "video_reverse_fly_demo",
    reason: "补充当前还没有覆盖的肩后束",
  },
  {
    cardId: "video_front_raise_demo",
    reason: "同样练肩，主要肌群与当前动作不同",
  },
  {
    cardId: "video_shoulder_press_demo",
    reason: "这是你收藏但还没有练过的动作",
  },
];

export const experienceGroups: ExperienceGroup[] = [
  {
    id: "lighter-weight",
    title: "先把重量降下来",
    summary: "不少练友发现，重量过大时手臂和斜方肌更容易抢着发力。先减轻重量，更容易保持肩膀放松。",
    mentions: 21,
    sourceVideos: 4,
    disagreement: "有人认为重量不是唯一原因，动作路径同样重要。",
    comments: [
      {
        id: "comment_001",
        content: "我从 7.5kg 降到 5kg 后，第一次能控制住下放，肩中束感觉明显多了。",
        videoTitle: "侧平举新手教学",
        creatorName: "GoFit Demo Coach",
      },
      {
        id: "comment_002",
        content: "别急着追重量，先找得到肩的感觉再加。",
        videoTitle: "侧平举别再耸肩了",
        creatorName: "阿元练肩",
      },
    ],
  },
  {
    id: "lead-with-elbows",
    title: "想象由手肘带动",
    summary: "把注意力从手里的哑铃移到手肘，向两侧展开，而不是用手把重量甩起来。",
    mentions: 18,
    sourceVideos: 3,
    disagreement: "暂无明显分歧。",
    comments: [
      {
        id: "comment_003",
        content: "肘带动这个提示对我特别有用，手臂终于没那么抢了。",
        videoTitle: "3 个侧平举细节",
        creatorName: "训练中的小林",
      },
      {
        id: "comment_004",
        content: "想象肘部往墙两边走，比想象抬哑铃更好理解。",
        videoTitle: "肩中束动作讲解",
        creatorName: "教练可乐",
      },
    ],
  },
  {
    id: "relax-shoulders",
    title: "别为了抬高而耸肩",
    summary: "抬到接近肩高就够了。继续追求高度时，斜方肌可能更容易参与。",
    mentions: 16,
    sourceVideos: 4,
    disagreement: "不同人的舒适活动范围不同，不必强求完全相同的高度。",
    comments: [
      {
        id: "comment_005",
        content: "以前总想着越高越好，控制高度后肩部反而更有感觉。",
        videoTitle: "侧平举新手教学",
        creatorName: "GoFit Demo Coach",
      },
      {
        id: "comment_006",
        content: "肩膀先沉下来再开始，这句话救了我的斜方肌。",
        videoTitle: "侧平举别再耸肩了",
        creatorName: "阿元练肩",
      },
    ],
  },
];

export const demoVideoUrl = new URL("../../../飞书20260721-193601.mp4", import.meta.url).href;
