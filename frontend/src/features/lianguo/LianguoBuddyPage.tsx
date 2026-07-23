import { useMemo } from "react";
import { useNavigate } from "react-router";
import { useMe } from "../../api";
import { useAppStore } from "../../store";
import { getBuddyTrainingCount } from "./buddy-progress";
import { LianguoFitness } from "./kit";

export function LianguoBuddyPage() {
  const navigate = useNavigate();
  const { data: me } = useMe();
  const sessions = useAppStore((state) => state.sessions);
  const buddyProgress = useAppStore((state) => state.buddyProgress);
  const completeBuddyTraining = useAppStore((state) => state.completeBuddyTraining);
  const purchaseBuddyItem = useAppStore((state) => state.purchaseBuddyItem);
  const equipBuddyItem = useAppStore((state) => state.equipBuddyItem);
  const resetBuddyProgress = useAppStore((state) => state.resetBuddyProgress);
  const completedItems = useMemo(
    () => sessions.flatMap((session) => session.items).filter((item) => item.state === "COMPLETED"),
    [sessions],
  );
  const localTrainingCount = getBuddyTrainingCount(buddyProgress);
  const existingTrainingCount = Math.max(me?.completedActionCount ?? 0, completedItems.length);
  const totalTrainingCount = existingTrainingCount + localTrainingCount;

  return (
    <LianguoFitness
      stateMode="controlled"
      user={{ id: me?.userId ?? "local_buddy_user", nickname: me?.nickname ?? "小练用户" }}
      totalTrainingCount={totalTrainingCount}
      totalTrainingXp={buddyProgress.totalTrainingXp}
      availableXp={buddyProgress.availableXp}
      ownedItemIds={buddyProgress.ownedItemIds}
      equippedOutfit={buddyProgress.equippedOutfit}
      recentTrainings={buddyProgress.recentTrainings}
      onCompleteTraining={completeBuddyTraining}
      onPurchaseItem={purchaseBuddyItem}
      onEquipItem={equipBuddyItem}
      onRestart={resetBuddyProgress}
      onClose={() => {
        void navigate("/me");
      }}
    />
  );
}
