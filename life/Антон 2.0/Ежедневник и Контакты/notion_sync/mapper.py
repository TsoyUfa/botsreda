from __future__ import annotations

from typing import Any, Dict, List, Optional


def chunk_text(text: str, chunk_size: int = 2000) -> List[str]:
    chunks: List[str] = []
    remaining = text or ""
    while remaining:
        chunks.append(remaining[:chunk_size])
        remaining = remaining[chunk_size:]
    if not chunks:
        chunks.append("")
    return chunks


def build_rich_text(text: str) -> List[Dict[str, Any]]:
    return [{"type": "text", "text": {"content": chunk}} for chunk in chunk_text(text)]


def note_to_properties(
    note: Dict[str, Any],
    property_map: Dict[str, str],
    include_content: bool = True,
) -> Dict[str, Any]:
    frontmatter = note["frontmatter"]
    properties: Dict[str, Any] = {}

    title_prop = property_map["title"]
    title_value = frontmatter.get("title") or note["title"]
    properties[title_prop] = {"title": build_rich_text(str(title_value))}

    _set_select(properties, property_map, "type", frontmatter.get("type"))
    _set_select(properties, property_map, "status", frontmatter.get("status"))
    _set_select(properties, property_map, "area", frontmatter.get("area"))
    _set_select(properties, property_map, "owner", frontmatter.get("owner"))
    _set_select(properties, property_map, "review", frontmatter.get("review"))
    _set_date(properties, property_map, "due", frontmatter.get("due"))

    _set_rich_text(properties, property_map, "kpi", frontmatter.get("kpi"))
    _set_tags(properties, property_map, "tags", frontmatter.get("tags"))

    _set_rich_text(properties, property_map, "path", note["relative_path"])
    _set_date(properties, property_map, "last_synced_at", note.get("last_synced_at"))

    if include_content:
        _set_rich_text(properties, property_map, "content", note.get("body", ""))

    return properties


def notion_properties_to_frontmatter(
    properties: Dict[str, Any],
    property_map: Dict[str, str],
) -> Dict[str, Any]:
    def get_prop(key: str) -> Optional[Dict[str, Any]]:
        name = property_map.get(key)
        return properties.get(name) if name else None

    frontmatter: Dict[str, Any] = {}
    frontmatter["type"] = _read_select(get_prop("type"))
    frontmatter["status"] = _read_select(get_prop("status"))
    frontmatter["area"] = _read_select(get_prop("area"))
    frontmatter["owner"] = _read_select(get_prop("owner"))
    frontmatter["review"] = _read_select(get_prop("review"))
    frontmatter["due"] = _read_date(get_prop("due"))
    frontmatter["kpi"] = _read_rich_text(get_prop("kpi"))
    tags = _read_multi_select(get_prop("tags"))
    if tags:
        frontmatter["tags"] = tags
    frontmatter["last_synced_at"] = _read_date(get_prop("last_synced_at"))
    return {k: v for k, v in frontmatter.items() if v not in (None, "")}


def notion_properties_to_body(
    properties: Dict[str, Any],
    property_map: Dict[str, str],
) -> Optional[str]:
    name = property_map.get("content")
    if not name or name not in properties:
        return None
    return _read_rich_text(properties.get(name))


def _set_select(properties: Dict[str, Any], property_map: Dict[str, str], key: str, value: Any) -> None:
    if value is None or value == "":
        return
    prop_name = property_map.get(key)
    if prop_name:
        properties[prop_name] = {"select": {"name": str(value)}}


def _set_date(properties: Dict[str, Any], property_map: Dict[str, str], key: str, value: Any) -> None:
    if value is None or value == "":
        return
    prop_name = property_map.get(key)
    if prop_name:
        properties[prop_name] = {"date": {"start": str(value)}}


def _set_rich_text(properties: Dict[str, Any], property_map: Dict[str, str], key: str, value: Any) -> None:
    if value is None:
        return
    prop_name = property_map.get(key)
    if prop_name:
        properties[prop_name] = {"rich_text": build_rich_text(str(value))}


def _set_tags(properties: Dict[str, Any], property_map: Dict[str, str], key: str, value: Any) -> None:
    if not value:
        return
    if isinstance(value, str):
        tags = [item.strip() for item in value.split(",") if item.strip()]
    else:
        tags = list(value)
    prop_name = property_map.get(key)
    if prop_name:
        properties[prop_name] = {"multi_select": [{"name": tag} for tag in tags]}


def _read_select(prop: Optional[Dict[str, Any]]) -> Optional[str]:
    if not prop:
        return None
    select = prop.get("select")
    return select.get("name") if select else None


def _read_multi_select(prop: Optional[Dict[str, Any]]) -> List[str]:
    if not prop:
        return []
    options = prop.get("multi_select") or []
    return [item.get("name") for item in options if item.get("name")]


def _read_date(prop: Optional[Dict[str, Any]]) -> Optional[str]:
    if not prop:
        return None
    date_obj = prop.get("date")
    return date_obj.get("start") if date_obj else None


def _read_rich_text(prop: Optional[Dict[str, Any]]) -> Optional[str]:
    if not prop:
        return None
    texts = prop.get("rich_text") or []
    return "".join(item.get("plain_text", "") for item in texts)
