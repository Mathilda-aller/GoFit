import { z } from "zod";

export const evidenceMediaSchema = z.object({
  kind: z.enum(["CORRECT_DEMO", "ERROR_DEMO"]),
  candidateId: z.string(),
  startMs: z.number(),
  endMs: z.number(),
  evidenceIds: z.array(z.string()),
});

const sourcedTextSchema = z.object({
  text: z.string(),
  evidenceIds: z.array(z.string()),
});

export const actionCardResponseSchema = z.object({
  schemaVersion: z.string(),
  requestId: z.string(),
  status: z.enum(["READY", "NEEDS_REVIEW", "FAILED"]),
  standardAction: z.object({
    standardActionId: z.string(),
    confidence: z.number(),
    decision: z.string(),
  }),
  actionCard: z.object({
    sourceVideo: z.object({
      videoId: z.string(),
      title: z.string(),
      creatorName: z.string(),
      sourceUrl: z.string(),
    }),
    actionName: z.string(),
    bodyRegion: z.string(),
    primaryMuscles: z.array(z.string()),
    secondaryMuscles: z.array(z.string()),
    equipment: z.array(z.string()),
    learningSide: z.object({
      correctDemo: evidenceMediaSchema,
      steps: z.array(
        z.object({
          order: z.number(),
          instruction: z.string(),
          startMs: z.number(),
          endMs: z.number(),
          evidenceIds: z.array(z.string()),
        }),
      ),
      keyReminders: z.array(sourcedTextSchema),
      commonErrors: z.array(
        z.object({
          mistake: z.string(),
          correction: z.string(),
          errorDemo: evidenceMediaSchema,
          evidenceIds: z.array(z.string()),
        }),
      ),
    }),
    trainingSide: z.object({
      loopDemo: evidenceMediaSchema,
      quickCue: sourcedTextSchema,
      quickTips: z.array(sourcedTextSchema),
    }),
  }),
  warnings: z.array(z.string()),
  needsReviewReasons: z.array(z.string()),
  provider: z.object({
    name: z.string(),
    version: z.string(),
  }),
});

export type ActionCardResponse = z.infer<typeof actionCardResponseSchema>;
export type ActionCard = ActionCardResponse["actionCard"];

export type Plan = {
  id: string;
  name: string;
  cardIds: string[];
  updatedAt: string;
  useCount: number;
};

export type Sensation =
  | "TARGET_FELT"
  | "OTHER_FELT"
  | "NO_FEELING"
  | "TOO_HARD"
  | "DISCOMFORT";

export type TrainingItem = {
  id: string;
  cardId: string;
  state: "NOT_STARTED" | "COMPLETED" | "SKIPPED" | "STOPPED_DISCOMFORT";
  sensation?: Sensation;
  feltRegion?: string;
};

export type TrainingSession = {
  id: string;
  planId: string;
  planName: string;
  status: "IN_PROGRESS" | "COMPLETED" | "ENDED";
  currentIndex: number;
  startedAt: string;
  items: TrainingItem[];
};

export type ExperienceGroup = {
  id: string;
  title: string;
  summary: string;
  mentions: number;
  sourceVideos: number;
  disagreement: string;
  comments: Array<{
    id: string;
    content: string;
    videoTitle: string;
    creatorName: string;
  }>;
};
