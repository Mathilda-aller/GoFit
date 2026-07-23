import rawLateralRaise from "./lateral-raise.json";
import frontRaiseCover from "./covers/front-raise.webp";
import lateralRaiseCover from "./covers/lateral-raise.webp";
import reverseFlyCover from "./covers/reverse-fly.webp";
import shoulderPressCover from "./covers/shoulder-press.webp";
import {
  actionCardResponseSchema,
  type ActionCardResponse,
  type ExperienceGroup,
} from "../domain";
import {
  demoCatalog,
  relatedPeerComments,
  videoWorkflowRequests,
  type DemoCatalogItem,
  type DemoComment,
} from "./demo-catalog";

export { demoCatalog, videoWorkflowRequests } from "./demo-catalog";
export type { DemoCatalogItem, DemoComment } from "./demo-catalog";

export const demoVideoUrl = "/api/v1/media/videos/01-lateral-raise.mp4";

const lateralRaiseTemplate = actionCardResponseSchema.parse(rawLateralRaise);

function evidenceId(item: DemoCatalogItem, suffix: string) {
  return `${item.video.videoId}_${suffix}`;
}

function actionCardFromCatalog(item: DemoCatalogItem, index: number): ActionCardResponse {
  const stepDuration = 7000;
  const steps = item.card.steps.map((instruction, stepIndex) => {
    const startMs = 3000 + stepIndex * stepDuration;
    return {
      order: stepIndex + 1,
      instruction,
      startMs,
      endMs: startMs + stepDuration - 1000,
      evidenceIds: [evidenceId(item, `step_${stepIndex + 1}`)],
    };
  });
  const demoStartMs = steps[0]?.startMs ?? 3000;
  const demoEndMs = steps.at(-1)?.endMs ?? 21000;
  const demoEvidenceIds = steps.flatMap((step) => step.evidenceIds);
  const correctDemo = {
    kind: "CORRECT_DEMO" as const,
    candidateId: evidenceId(item, "correct_demo"),
    startMs: demoStartMs,
    endMs: demoEndMs,
    evidenceIds: demoEvidenceIds,
    mediaUrl: demoVideoUrl,
  };
  const errorStartMs = demoEndMs + 1000;
  const catalogErrors = [
    { mistake: item.card.mistake, correction: item.card.correction },
    ...(item.card.additionalErrors ?? []),
  ];

  return actionCardResponseSchema.parse({
    ...structuredClone(lateralRaiseTemplate),
    requestId: `demo_action_card_${String(index + 1).padStart(3, "0")}`,
    standardAction: {
      standardActionId: item.exerciseId,
      confidence: 0.96,
      decision: "MATCHED",
    },
    actionCard: {
      sourceVideo: {
        videoId: item.video.videoId,
        title: item.video.title,
        creatorName: item.video.creatorName,
        sourceUrl: item.video.sourceUrl,
      },
      actionName: item.actionName,
      bodyRegion: item.bodyRegion,
      primaryMuscles: item.primaryMuscles,
      secondaryMuscles: item.secondaryMuscles,
      equipment: item.equipment,
      learningSide: {
        correctDemo,
        steps,
        keyReminders: [{
          text: item.card.reminder,
          evidenceIds: [evidenceId(item, "reminder")],
        }],
        commonErrors: catalogErrors.map((error, errorIndex) => {
          const evidenceIds = [evidenceId(item, `error_${errorIndex + 1}`)];
          const startMs = errorStartMs + errorIndex * 6000;
          return {
            mistake: error.mistake,
            correction: error.correction,
            errorDemo: {
              kind: "ERROR_DEMO" as const,
              candidateId: evidenceId(item, `error_demo_${errorIndex + 1}`),
              startMs,
              endMs: startMs + 5000,
              evidenceIds,
              mediaUrl: demoVideoUrl,
            },
            evidenceIds,
          };
        }),
      },
      trainingSide: {
        loopDemo: correctDemo,
        quickCue: {
          text: item.card.cue,
          evidenceIds: demoEvidenceIds,
        },
        quickTips: item.card.tips.map((text, tipIndex) => ({
          text,
          evidenceIds: [evidenceId(item, `tip_${tipIndex + 1}`)],
        })),
      },
    },
    provider: { name: "demo-catalog", version: "1.0.0" },
  });
}

export const actionCards: Record<string, ActionCardResponse> = Object.fromEntries(
  demoCatalog.map((item, index) => [item.cardId, actionCardFromCatalog(item, index)]),
);

export const cardIds = demoCatalog.map((item) => item.cardId);

export type DemoVideo = {
  videoId: string;
  title: string;
  creatorName: string;
  actionName: string;
  bodyRegion: string;
  durationLabel: string;
  previewUrl: string;
  previewSecond: number;
  posterUrl?: string;
  assetFileName: string;
  workflowRequestId: string;
};

const posterByVideoId: Partial<Record<string, string>> = {
  video_lateral_raise_demo: lateralRaiseCover,
  video_front_raise_demo: frontRaiseCover,
  video_reverse_fly_demo: reverseFlyCover,
  video_shoulder_press_demo: shoulderPressCover,
};

export const demoVideos: DemoVideo[] = demoCatalog.map((item) => ({
  videoId: item.video.videoId,
  title: item.video.title,
  creatorName: item.video.creatorName,
  actionName: item.actionName,
  bodyRegion: item.bodyRegion,
  durationLabel: item.video.durationLabel,
  previewUrl: demoVideoUrl,
  previewSecond: item.video.previewSecond,
  posterUrl: posterByVideoId[item.video.videoId],
  assetFileName: item.video.assetFileName,
  workflowRequestId: `workflow_${item.video.videoId}`,
}));

export const recommendations = [
  { cardId: "video_face_pull_demo", reason: "补充肩后束和肩胛控制" },
  { cardId: "video_lat_pulldown_demo", reason: "加入一个背部纵向拉动作" },
  { cardId: "video_seated_row_demo", reason: "用水平拉覆盖背部中段" },
];

function commentsFor(item: DemoCatalogItem): DemoComment[] {
  if (item.exerciseId === "action_lateral_raise") {
    return [...item.comments, ...relatedPeerComments.filter((comment) => comment.videoId.startsWith("video_lateral_raise"))];
  }
  if (item.exerciseId === "action_lat_pulldown") {
    return [...item.comments, ...relatedPeerComments.filter((comment) => comment.videoId.startsWith("video_lat_pulldown"))];
  }
  return item.comments;
}

export type DemoExperience = {
  exerciseId: string;
  exerciseName: string;
  problemTitle: string;
  commentCount: number;
  sourceVideoCount: number;
  groups: ExperienceGroup[];
};

export const experienceByExerciseId: Record<string, DemoExperience> = Object.fromEntries(
  demoCatalog.map((item) => {
    const comments = commentsFor(item);
    const sourceVideoCount = new Set(comments.map((comment) => comment.videoId)).size;
    const group: ExperienceGroup = {
      id: `experience_${item.exerciseId}_arms_felt_more`,
      title: item.experience.methodName,
      summary: item.experience.summary,
      mentions: item.experience.projectedMentions,
      sourceVideos: sourceVideoCount,
      disagreement: item.experience.disagreement,
      comments: comments.map((comment) => ({
        id: comment.id,
        content: comment.content,
        videoTitle: comment.videoTitle,
        creatorName: comment.authorName,
      })),
    };
    return [item.exerciseId, {
      exerciseId: item.exerciseId,
      exerciseName: item.actionName,
      problemTitle: item.experience.problemTitle,
      commentCount: item.experience.projectedMentions,
      sourceVideoCount,
      groups: [group],
    }];
  }),
);

export function getDemoExperience(exerciseId: string): DemoExperience {
  return experienceByExerciseId[exerciseId] ?? experienceByExerciseId.action_lateral_raise;
}

// 保留旧导出，供尚未迁移的调用方获得默认侧平举经验。
export const experienceGroups = getDemoExperience("action_lateral_raise").groups;
