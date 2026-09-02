"""Placeholder local — último recurso, nunca inventa URL remota."""

from __future__ import annotations

from futebol.assetsmgr.providers.base import PlayerRecord, TeamRecord


class FallbackProvider:
    name = 'fallback'

    def available(self) -> bool:
        return True

    def get_teams(self) -> list[TeamRecord]:
        return []

    def get_players(self) -> list[PlayerRecord]:
        return []

    def get_team_logo(self, team: TeamRecord) -> str | None:
        return None

    def get_player_image(self, player: PlayerRecord) -> str | None:
        return None

    def placeholder_team(self) -> str:
        return 'placeholders/team.png'

    def placeholder_player(self) -> str:
        return 'placeholders/player.png'
