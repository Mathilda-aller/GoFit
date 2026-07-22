import { describe, expect, it } from "vitest";
import rawLateralRaise from "./mocks/lateral-raise.json";
import { actionCardResponseSchema } from "./domain";

describe("AI action card contract", () => {
  it("accepts the complete lateral raise fixture", () => {
    const result = actionCardResponseSchema.parse(rawLateralRaise);

    expect(result.status).toBe("READY");
    expect(result.standardAction.standardActionId).toBe("action_lateral_raise");
    expect(result.actionCard.learningSide.steps).toHaveLength(4);
    expect(result.actionCard.learningSide.commonErrors[0]?.errorDemo.evidenceIds).toContain("vision_error");
    expect(result.actionCard.trainingSide.quickTips).toHaveLength(3);
    expect(result.provider).toEqual({ name: "fixed-fixture", version: "1.1.0" });
  });

  it("rejects a card that loses evidence ids", () => {
    const invalid = structuredClone(rawLateralRaise) as Record<string, unknown>;
    const actionCard = invalid.actionCard as Record<string, unknown>;
    const trainingSide = actionCard.trainingSide as Record<string, unknown>;
    const quickCue = trainingSide.quickCue as Record<string, unknown>;
    delete quickCue.evidenceIds;

    expect(() => actionCardResponseSchema.parse(invalid)).toThrow();
  });
});
