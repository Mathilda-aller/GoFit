import { describe, expect, it } from "vitest";
import { demoCatalog, relatedPeerComments, videoWorkflowRequests } from "./demo-catalog";
import { actionCards, demoVideos, experienceByExerciseId, getDemoExperience } from "./data";

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

  it("gives every feed item its own real source video", () => {
    expect(demoVideos).toHaveLength(10);
    expect(new Set(demoVideos.map((video) => video.previewUrl)).size).toBe(10);
    for (const video of demoVideos) {
      expect(video.previewUrl).toBe(`/api/v1/media/videos/${encodeURIComponent(video.assetFileName)}`);
    }
  });

  it("resolves distinct mock experiences from frontend actions, business exercises, and video cards", () => {
    expect(getDemoExperience("action_reverse_fly").problemTitle).toBe("反向飞鸟手臂更酸？");
    expect(getDemoExperience("exercise_reverse_fly").problemTitle).toBe("反向飞鸟手臂更酸？");
    expect(getDemoExperience("action_lateral_raise", "video_reverse_fly_demo").problemTitle).toBe("反向飞鸟手臂更酸？");

    const experiences = demoCatalog.map((item) => getDemoExperience(item.exerciseId, item.video.videoId));
    expect(new Set(experiences.map((experience) => experience.problemTitle)).size).toBe(demoCatalog.length);
    expect(new Set(experiences.map((experience) => experience.groups[0]?.id)).size).toBe(demoCatalog.length);
  });
});
