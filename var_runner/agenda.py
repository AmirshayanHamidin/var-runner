"""Git-based state: parse and serialize a RESEARCH_AGENDA.md file.

The agenda file is the loop's only memory (VAR rule 3: the repo is the lab
notebook). It has three recognized sections, each a markdown H2 heading:

    ## Queue       - numbered or bulleted list of pending work items
    ## Log         - append-only list of incidents / completed-run notes
    ## Guardrails  - list of hard rules the loop must load into Guardrails

Reads of the live remote must be cache-busted (see cache_busted_url), because
stale CDN caches have caused real incidents (qrc-shot-wall agenda log).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field


@dataclass
class Agenda:
    queue: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)

    def next_item(self) -> str | None:
        """Return the first queue item, or None if the queue is empty
        (empty queue means: switch to audit mode, VAR rule 5)."""
        return self.queue[0] if self.queue else None

    def pop_item(self) -> str | None:
        return self.queue.pop(0) if self.queue else None

    def append_log(self, entry: str) -> None:
        self.log.append(entry)

    def to_markdown(self) -> str:
        def sec(title: str, items: list[str]) -> str:
            body = "\n".join(f"- {i}" for i in items) if items else "(empty)"
            return f"## {title}\n\n{body}\n"

        return "# RESEARCH AGENDA\n\n" + "\n".join(
            [sec("Queue", self.queue), sec("Log", self.log), sec("Guardrails", self.guardrails)]
        )


_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_ITEM_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")


def parse_agenda(text: str) -> Agenda:
    """Parse RESEARCH_AGENDA.md text into an Agenda.

    Unknown sections are ignored. Items are single-line list entries;
    continuation lines (indented, non-list) are appended to the previous item.
    """
    agenda = Agenda()
    matches = list(_SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        name = m.group(1).strip().lower()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        target = {"queue": agenda.queue, "log": agenda.log, "guardrails": agenda.guardrails}.get(name)
        if target is None:
            continue
        for line in body.splitlines():
            im = _ITEM_RE.match(line.strip())
            if im:
                target.append(im.group(1))
            elif line.startswith(("  ", "\t")) and line.strip() and target:
                target[-1] += " " + line.strip()
    return agenda


def cache_busted_url(url: str, ts: int | None = None) -> str:
    """Append a ?nocache=<timestamp> (or &nocache=) parameter to defeat CDN caches."""
    ts = int(time.time()) if ts is None else ts
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}nocache={ts}"
