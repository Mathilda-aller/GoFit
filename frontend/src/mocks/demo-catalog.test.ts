import { describe, expect, it } from "vitest";
import { demoCatalog, relatedPeerComments, videoWorkflowRequests } from "./demo-catalog";
import { actionCards, experienceByExerciseId } from "./data";

describe("demo catalog relationships", () => {
  it("contains five shoulder and five back actions with stable one-to-one video cards", () => {
    expect(demoCatalog).toHaveLength(10);
    expect(demoCatalog.filter((item) => item.bodyRegion === "肩部")).toHaveLength(5);
    expect(demoCatalog.filter((item) => item.bodyRegion === "背部")).toHaveLength(5);
    expect(new Set(demoCatalog.map((item) => item.video.videoId)).size).toBe(10);
    expect(Object.keys(actionCards)).toEqual(demoCatalog.map((item) => item.cardId));
  });

  it("provides a workflow request and source-linked comments for every demo video", () => {
    expect(videoWorkflowRequests).toHaveLength(10);
    for (const item of demoCatalog) {
      const request = videoWorkflowRequests.find((candidate) => candidate.sourceVideo.videoId === item.video.videoId);
      expect(request?.standardActionCandidates[0]?.standardActionId).toBe(item.exerciseId);
      expect(request?.videoPath).toContain(item.video.assetFileName);
      expect(item.comments.length).toBeGreaterThan(0);
      expect(item.comments.every((comment) => comment.videoId === item.video.videoId)).toBe(true);
      expect(experienceByExerciseId[item.exerciseId]?.groups.length).toBeGreaterThan(0);
    }
    expect(new Set(relatedPeerComments.map((comment) => comment.videoId)).size).toBe(4);
  });
});
