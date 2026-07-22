from fastapi import APIRouter, Depends

from app.models.recommendation import (
    RecommendationRankRequest,
    RecommendationRankResult,
)
from app.recommendation.ranker import RecommendationRanker


router = APIRouter(tags=["recommendations"])
_ranker = RecommendationRanker()


def get_ranker() -> RecommendationRanker:
    return _ranker


@router.post("/recommendations/rank", response_model=RecommendationRankResult)
def rank_recommendations(
    request: RecommendationRankRequest,
    ranker: RecommendationRanker = Depends(get_ranker),
) -> RecommendationRankResult:
    return ranker.rank(request)
