from dataclasses import dataclass, field
from typing import Callable, Optional

from .i18n import tr


@dataclass
class Command:
    id: str
    title_key: str       # ключ перевода, например "file.save"
    category: str        # "File" / "Edit" / "View" — категория не переводится (id)
    callback: Callable[[], None]
    shortcut: Optional[str] = None
    keywords: list = field(default_factory=list)

    @property
    def title(self) -> str:
        return tr(self.title_key)

    @property
    def full_title(self) -> str:
        cat = tr(f"menu.{self.category}") if self.category in ("File", "Edit", "View") else self.category
        return f"{cat}: {self.title}"

    @property
    def search_text(self) -> str:
        parts = [self.full_title] + list(self.keywords)
        return " ".join(parts)


class CommandRegistry:
    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, cmd: Command):
        if cmd.id in self._commands:
            raise ValueError(f"Команда с id={cmd.id} уже зарегистрирована")
        self._commands[cmd.id] = cmd

    def get(self, cmd_id: str) -> Optional[Command]:
        return self._commands.get(cmd_id)

    def all(self) -> list[Command]:
        return list(self._commands.values())

    def execute(self, cmd_id: str):
        cmd = self._commands.get(cmd_id)
        if cmd:
            cmd.callback()


def fuzzy_score(query: str, target: str) -> int:
    if not query:
        return 0
    q = query.lower()
    t = target.lower()
    score = 0
    ti = 0
    last_match = -1
    for qc in q:
        found = t.find(qc, ti)
        if found == -1:
            return -1
        if found == 0 or t[found - 1] in " :/\\_-.":
            score += 10
        if last_match != -1 and found == last_match + 1:
            score += 5
        score += 1
        ti = found + 1
        last_match = found
    score -= len(t) // 10
    return score