from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

FRONTMATTER_BOUNDARY = "---"


@dataclass
class FrontmatterResult:
    frontmatter: Dict[str, object]
    body: str
    has_frontmatter: bool


def parse_frontmatter(text: str) -> FrontmatterResult:
    if not text.startswith(FRONTMATTER_BOUNDARY):
        return FrontmatterResult(frontmatter={}, body=text, has_frontmatter=False)

    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_BOUNDARY:
        return FrontmatterResult(frontmatter={}, body=text, has_frontmatter=False)

    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == FRONTMATTER_BOUNDARY:
            end_index = idx
            break

    if end_index is None:
        return FrontmatterResult(frontmatter={}, body=text, has_frontmatter=False)

    raw_frontmatter = lines[1:end_index]
    body = "\n".join(lines[end_index + 1 :])
    return FrontmatterResult(
        frontmatter=_parse_frontmatter_lines(raw_frontmatter),
        body=body,
        has_frontmatter=True,
    )


def _parse_frontmatter_lines(lines: List[str]) -> Dict[str, object]:
    data: Dict[str, object] = {}
    for line in lines:
        if not line.strip():
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        data[key] = _parse_value(value)
    return data


def _parse_value(value: str) -> object:
    if value == "":
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip() for item in inner.split(",") if item.strip()]
    return value


def serialize_frontmatter(frontmatter: Dict[str, object]) -> str:
    ordered_keys = [
        "type",
        "status",
        "area",
        "owner",
        "review",
        "due",
        "kpi",
        "tags",
        "notion_id",
        "last_synced_at",
    ]
    used = set()
    lines: List[str] = [FRONTMATTER_BOUNDARY]
    for key in ordered_keys:
        if key in frontmatter:
            lines.append(_format_line(key, frontmatter[key]))
            used.add(key)
    for key in sorted(k for k in frontmatter.keys() if k not in used):
        lines.append(_format_line(key, frontmatter[key]))
    lines.append(FRONTMATTER_BOUNDARY)
    return "\n".join(lines)


def _format_line(key: str, value: object) -> str:
    if isinstance(value, list):
        return f"{key}: [{', '.join(value)}]"
    if value is None:
        return f"{key}:"
    return f"{key}: {value}"


def update_frontmatter(text: str, updates: Dict[str, object]) -> str:
    result = parse_frontmatter(text)
    merged = dict(result.frontmatter)
    merged.update(updates)
    frontmatter_block = serialize_frontmatter(merged)
    body = result.body.lstrip("\n")
    return f"{frontmatter_block}\n{body}"
