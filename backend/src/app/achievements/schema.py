from datetime import datetime

from pydantic import BaseModel


class AchievementResponse(BaseModel):

    key: str
    title: str
    description: str
    condition: str
    icon: str
    target: int
    progress: int
    xp_reward: int
    is_unlocked: bool
    unlocked_at: datetime | None = None
