from enum import Enum


class PredictionStatus(str, Enum):
    DRAFT = "draft"
    SENT_TO_MODERATION = "sent_to_moderation"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    RESULT_CONFIRMED = "result_confirmed"


class MatchOutcome(str, Enum):
    HOME_WIN = "home_win"
    DRAW = "draw"
    AWAY_WIN = "away_win"


class HitMiss(str, Enum):
    HIT = "hit"
    MISS = "miss"
    PENDING = "pending"
