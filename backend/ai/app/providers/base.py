from typing import Protocol

from app.models.action_card import ActionCardBuildRequest, ActionCardBuildResult


class ActionCardGenerator(Protocol):
    def generate(self, request: ActionCardBuildRequest) -> ActionCardBuildResult:
        """Generate a candidate result from already-aligned evidence."""
        ...

