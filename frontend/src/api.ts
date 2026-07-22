import { useQuery } from "@tanstack/react-query";
import { actionCards, cardIds } from "./mocks/data";

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export const mockRepository = {
  async getActionCard(cardId: string) {
    await wait(120);
    return actionCards[cardId] ?? null;
  },
  async listActionCards() {
    await wait(160);
    return cardIds.map((id) => actionCards[id]);
  },
};

export function useActionCard(cardId: string | undefined) {
  return useQuery({
    queryKey: ["action-card", cardId],
    queryFn: () => mockRepository.getActionCard(cardId ?? ""),
    enabled: Boolean(cardId),
    staleTime: Infinity,
  });
}

export function useActionCards() {
  return useQuery({
    queryKey: ["action-cards"],
    queryFn: mockRepository.listActionCards,
    staleTime: Infinity,
  });
}
