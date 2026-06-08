from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from frontmatter import parse_frontmatter, serialize_frontmatter
from mapper import note_to_properties, notion_properties_to_body, notion_properties_to_frontmatter
from notion_api import NotionClient

DEFAULT_DB_TITLES = {
    "process": "Processes",
    "task": "Tasks",
    "metric": "Metrics",
    "finance": "Finance",
}


@dataclass
class Note:
    path: Path
    relative_path: str
    title: str
    frontmatter: Dict[str, Any]
    body: str
    last_modified: datetime


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def save_config(config_path: Path, config: Dict[str, Any]) -> None:
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def resolve_path(config_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (config_path.parent / path).resolve()


def setup_logging(log_path: Optional[Path]) -> None:
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
    )


def iter_markdown_files(vault_root: Path, scan_paths: Iterable[str]) -> Iterable[Path]:
    ignore_dirs = {".obsidian", ".git", "node_modules", "__pycache__", "notion_sync"}
    for scan_path in scan_paths:
        base = (vault_root / scan_path).resolve()
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            if any(part in ignore_dirs or part.startswith(".") for part in path.parts):
                continue
            yield path


def build_note(path: Path, vault_root: Path) -> Optional[Note]:
    text = path.read_text(encoding="utf-8")
    parsed = parse_frontmatter(text)
    if not parsed.frontmatter.get("type"):
        return None
    relative_path = str(path.relative_to(vault_root)).replace("\\", "/")
    title = str(parsed.frontmatter.get("title") or path.stem)
    last_modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return Note(
        path=path,
        relative_path=relative_path,
        title=title,
        frontmatter=parsed.frontmatter,
        body=parsed.body,
        last_modified=last_modified,
    )


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def format_datetime(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def find_page_by_path(
    client: NotionClient,
    database_id: str,
    property_name: str,
    path_value: str,
) -> Optional[str]:
    filter_obj = {"property": property_name, "rich_text": {"equals": path_value}}
    result = client.query_database(database_id, filter_obj)
    pages = result.get("results") or []
    if not pages:
        return None
    return pages[0].get("id")


def update_local_note(note: Note, updates: Dict[str, Any], body: Optional[str]) -> None:
    frontmatter = dict(note.frontmatter)
    frontmatter.update(updates)
    frontmatter_block = serialize_frontmatter(frontmatter)
    new_body = body if body is not None else note.body
    content = f"{frontmatter_block}\n{new_body.lstrip(chr(10))}"
    note.path.write_text(content, encoding="utf-8")


def create_conflict_file(
    conflicts_dir: Path,
    note: Note,
    page_id: str,
    notion_body: Optional[str],
) -> None:
    conflicts_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    conflict_name = f"{note.path.stem}.notion.{timestamp}.md"
    conflict_path = conflicts_dir / conflict_name
    frontmatter = {
        "conflict_from": "notion",
        "source_notion_id": page_id,
        "original_path": note.relative_path,
        "conflict_time": format_datetime(datetime.now(timezone.utc)),
    }
    body = notion_body or ""
    content = f"{serialize_frontmatter(frontmatter)}\n{body.lstrip(chr(10))}"
    conflict_path.write_text(content, encoding="utf-8")


def is_safe_path(vault_root: Path, candidate: Path) -> bool:
    try:
        resolved = candidate.resolve()
        return resolved == vault_root.resolve() or vault_root.resolve() in resolved.parents
    except FileNotFoundError:
        return False


def create_local_note_from_notion(
    vault_root: Path,
    relative_path: str,
    page: Dict[str, Any],
    property_map: Dict[str, str],
    note_type: str,
    page_id: str,
    synced_at: str,
) -> None:
    target_path = (vault_root / relative_path).resolve()
    if not is_safe_path(vault_root, target_path):
        logging.warning("Skip unsafe path from Notion: %s", relative_path)
        return
    if any(part.startswith(".") for part in target_path.parts):
        logging.warning("Skip hidden path from Notion: %s", relative_path)
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = notion_properties_to_frontmatter(page["properties"], property_map)
    if not frontmatter.get("type"):
        frontmatter["type"] = note_type
    frontmatter["notion_id"] = page_id
    frontmatter["last_synced_at"] = synced_at
    body = notion_properties_to_body(page["properties"], property_map) or ""
    content = f"{serialize_frontmatter(frontmatter)}\n{body.lstrip(chr(10))}"
    target_path.write_text(content, encoding="utf-8")


def read_rich_text_property(prop: Optional[Dict[str, Any]]) -> Optional[str]:
    if not prop:
        return None
    texts = prop.get("rich_text") or []
    return "".join(item.get("plain_text", "") for item in texts)


def sync_inbound_pages(
    client: NotionClient,
    vault_root: Path,
    database_ids: Dict[str, str],
    property_map: Dict[str, str],
    synced_at: str,
    dry_run: bool,
) -> None:
    for note_type, database_id in database_ids.items():
        if not database_id:
            continue
        start_cursor = None
        while True:
            result = client.query_database(database_id, start_cursor=start_cursor, page_size=100)
            pages = result.get("results") or []
            for page in pages:
                path_prop = page.get("properties", {}).get(property_map["path"])
                relative_path = read_rich_text_property(path_prop)
                if not relative_path:
                    continue
                target_path = (vault_root / relative_path).resolve()
                if target_path.exists():
                    continue
                logging.info("Create local note from Notion: %s", relative_path)
                if not dry_run:
                    create_local_note_from_notion(
                        vault_root,
                        relative_path,
                        page,
                        property_map,
                        note_type,
                        page.get("id"),
                        synced_at,
                    )
            if not result.get("has_more"):
                break
            start_cursor = result.get("next_cursor")


def sync_notes(config_path: Path, config: Dict[str, Any], dry_run: bool) -> None:
    token = os.getenv(config.get("notion_token_env", "NOTION_TOKEN"))
    if not token:
        raise RuntimeError("Missing Notion token. Set NOTION_TOKEN environment variable.")

    vault_root = resolve_path(config_path, config["vault_root"])
    scan_paths = config.get("scan_paths") or ["."]
    property_map = config["property_map"]
    database_ids = config["database_ids"]
    allow_create_from_notion = bool(config.get("allow_create_from_notion"))

    client = NotionClient(token=token)
    notes: List[Note] = []
    for file_path in iter_markdown_files(vault_root, scan_paths):
        note = build_note(file_path, vault_root)
        if note:
            notes.append(note)

    logging.info("Found %s notes to sync", len(notes))
    now = format_datetime(datetime.now(timezone.utc))
    conflicts_dir = resolve_path(config_path, config.get("conflicts_dir", "conflicts"))

    for note in notes:
        note_type = str(note.frontmatter.get("type"))
        database_id = database_ids.get(note_type)
        if not database_id:
            logging.info("Skip note without database id: %s", note.relative_path)
            continue

        page_id = note.frontmatter.get("notion_id")
        if not page_id:
            page_id = find_page_by_path(
                client,
                database_id,
                property_map["path"],
                note.relative_path,
            )

        needs_id_update = False
        page = None
        if page_id:
            try:
                page = client.get_page(page_id)
            except RuntimeError as exc:
                logging.warning("Failed to load page %s: %s", page_id, exc)
                page = None
            if page and not note.frontmatter.get("notion_id"):
                needs_id_update = True

        local_last_synced = parse_datetime(note.frontmatter.get("last_synced_at"))
        local_changed = local_last_synced is None or note.last_modified > local_last_synced
        notion_last_edited = parse_datetime(page.get("last_edited_time")) if page else None
        notion_changed = (
            page is not None
            and (local_last_synced is None or (notion_last_edited and notion_last_edited > local_last_synced))
        )

        if page is None:
            if dry_run:
                logging.info("DRY RUN create page for %s", note.relative_path)
                continue
            properties = note_to_properties(
                note.__dict__ | {"last_synced_at": now},
                property_map,
            )
            created = client.create_page(database_id, properties)
            update_local_note(note, {"notion_id": created.get("id"), "last_synced_at": now}, None)
            logging.info("Created page for %s", note.relative_path)
            continue

        if local_last_synced is None:
            if notion_last_edited and notion_last_edited > note.last_modified:
                logging.info("First sync: update local from Notion %s", note.relative_path)
                if not dry_run:
                    updates = notion_properties_to_frontmatter(page["properties"], property_map)
                    updates["notion_id"] = page_id
                    updates["last_synced_at"] = now
                    body = notion_properties_to_body(page["properties"], property_map)
                    update_local_note(note, updates, body)
            else:
                logging.info("First sync: update Notion from local %s", note.relative_path)
                if not dry_run:
                    properties = note_to_properties(
                        note.__dict__ | {"last_synced_at": now},
                        property_map,
                    )
                    client.update_page(page_id, properties)
                    update_local_note(note, {"notion_id": page_id, "last_synced_at": now}, None)
            continue

        if local_changed and notion_changed:
            logging.warning("Conflict detected for %s", note.relative_path)
            if not dry_run:
                notion_body = notion_properties_to_body(page["properties"], property_map)
                create_conflict_file(conflicts_dir, note, page_id, notion_body)
            continue

        if local_changed:
            logging.info("Update Notion from local %s", note.relative_path)
            if not dry_run:
                properties = note_to_properties(
                    note.__dict__ | {"last_synced_at": now},
                    property_map,
                )
                client.update_page(page_id, properties)
                update_local_note(note, {"notion_id": page_id, "last_synced_at": now}, None)
            continue

        if notion_changed:
            logging.info("Update local from Notion %s", note.relative_path)
            if not dry_run:
                updates = notion_properties_to_frontmatter(page["properties"], property_map)
                updates["notion_id"] = page_id
                updates["last_synced_at"] = now
                body = notion_properties_to_body(page["properties"], property_map)
                update_local_note(note, updates, body)
            continue

        logging.info("No changes for %s", note.relative_path)
        if needs_id_update and not dry_run:
            update_local_note(note, {"notion_id": page_id, "last_synced_at": now}, None)

    if allow_create_from_notion:
        sync_inbound_pages(
            client,
            vault_root,
            database_ids,
            property_map,
            now,
            dry_run,
        )


def init_databases(config_path: Path, config: Dict[str, Any], write_config: bool) -> None:
    token = os.getenv(config.get("notion_token_env", "NOTION_TOKEN"))
    if not token:
        raise RuntimeError("Missing Notion token. Set NOTION_TOKEN environment variable.")

    schema_path = resolve_path(config_path, config.get("schema_path", "schema.json"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    parent_page_id = config.get("parent_page_id")
    if not parent_page_id or "PASTE_NOTION_PARENT_PAGE_ID_HERE" in parent_page_id:
        raise RuntimeError("parent_page_id is missing in config.")

    client = NotionClient(token=token)
    database_ids = dict(config.get("database_ids") or {})

    for note_type, title in DEFAULT_DB_TITLES.items():
        if database_ids.get(note_type):
            logging.info("Database already configured for %s", note_type)
            continue
        created = client.create_database(parent_page_id, title, schema["properties"])
        database_ids[note_type] = created.get("id")
        logging.info("Created database %s: %s", title, created.get("id"))

    if write_config:
        config["database_ids"] = database_ids
        save_config(config_path, config)
        logging.info("Config updated with new database IDs")
    else:
        logging.info("Database IDs: %s", database_ids)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Obsidian notes with Notion.")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config.json")),
        help="Path to config.json",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create Notion databases")
    init_parser.add_argument("--write-config", action="store_true", help="Write DB IDs to config file")

    sync_parser = subparsers.add_parser("sync", help="Sync notes")
    sync_parser.add_argument("--dry-run", action="store_true", help="Only show planned changes")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config_path = Path(args.config).expanduser()
    config = load_config(config_path)
    log_path = resolve_path(config_path, config.get("log_path")) if config.get("log_path") else None
    setup_logging(log_path)

    if args.command == "init":
        init_databases(config_path, config, args.write_config)
    elif args.command == "sync":
        sync_notes(config_path, config, args.dry_run)


if __name__ == "__main__":
    main()
