from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class TeamRecord:
    id: int
    name: str
    short_name: str
    slug: str = ''
    logo_url: str = ''
    source: str = ''
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlayerRecord:
    id: int
    name: str
    slug: str = ''
    team_id: int = 0
    position: str = ''
    photo_url: str = ''
    source: str = ''
    generic_photo: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class AssetProvider(Protocol):
    name: str

    def available(self) -> bool: ...
    def get_teams(self) -> list[TeamRecord]: ...
    def get_players(self) -> list[PlayerRecord]: ...
    def get_team_logo(self, team: TeamRecord) -> str | None: ...
    def get_player_image(self, player: PlayerRecord) -> str | None: ...
