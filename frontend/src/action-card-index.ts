import type { ActionCardResponse } from "./domain";

export function createActionCardIndex(cards: ActionCardResponse[]) {
  const cardMap = new Map<string, ActionCardResponse>();
  for (const response of cards) {
    const cardId = response.actionCard.sourceVideo.videoId;
    cardMap.set(cardId, response);

    const demoId = /^video_(.+)_demo$/.exec(cardId);
    if (demoId) cardMap.set(demoId[1].replaceAll("_", "-"), response);
  }
  return cardMap;
}
