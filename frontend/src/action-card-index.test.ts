import { describe, expect, it } from "vitest";
import { createActionCardIndex } from "./action-card-index";
import { actionCards } from "./mocks/data";

describe("createActionCardIndex", () => {
  const index = createActionCardIndex(Object.values(actionCards));

  it("resolves current video action card ids", () => {
    expect(index.get("video_lateral_raise_demo")?.actionCard.actionName).toBe("哑铃侧平举");
  });

  it("resolves legacy plan card ids without exposing English slugs", () => {
    expect(index.get("lateral-raise")?.actionCard.actionName).toBe("哑铃侧平举");
    expect(index.get("lat-pulldown")?.actionCard.actionName).toBe("高位下拉");
    expect(index.get("reverse-fly")?.actionCard.actionName).toBe("俯身反向飞鸟");
  });
});
