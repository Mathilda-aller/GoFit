RULE_VERSION = "p0-v1"
MAX_RECOMMENDATIONS = 3

SCORE_SELECTED_BODY_REGION = 30
SCORE_CURRENT_BODY_REGION = 20
SCORE_MUSCLE_COVERAGE_COMPLEMENT = 18
SCORE_HISTORY_TARGET_FELT = 8
MAX_HISTORY_TARGET_FELT = 24
SCORE_SAVED_NOT_TRIED = 10
SCORE_HIGHLY_REPETITIVE = -20
SCORE_NO_FEELING = -8
MIN_NO_FEELING = -24
SCORE_TOO_HARD = -6
MIN_TOO_HARD = -18

BODY_REGION_LABELS = {
    "ARM": "手臂",
    "BACK": "背部",
    "CHEST": "胸部",
    "CORE": "核心",
    "GLUTE": "臀部",
    "LEG": "腿部",
    "SHOULDER": "肩部",
}

MUSCLE_LABELS = {
    "BICEPS": "肱二头肌",
    "DELTOID_ANTERIOR": "肩前束",
    "DELTOID_LATERAL": "肩中束",
    "DELTOID_POSTERIOR": "肩后束",
}

REASON_TEMPLATES = {
    "HISTORY_TARGET_FELT": "你之前练这个动作时，目标部位感觉不错。",
    "MUSCLE_COVERAGE_COMPLEMENT": "补充当前还没有覆盖的{muscle_label}。",
    "MUSCLE_COVERAGE_COMPLEMENT_GENERIC": "补充当前还没有覆盖的具体肌群。",
    "SAME_BODY_REGION": "同样训练{body_region_label}，可以作为接下来的候选。",
    "SAME_BODY_REGION_GENERIC": "与当前练单属于同一身体大区，可以作为接下来的候选。",
    "SAVED_NOT_TRIED": "这是你收藏但还没有练过的动作。",
}
