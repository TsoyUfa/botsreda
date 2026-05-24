from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass
class NotionClient:
    token: str
    notion_version: str = "2022-06-28"
    base_url: str = "https://api.notion.com/v1"

    def create_database(self, parent_page_id: str, title: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }
        return self._request("POST", "/databases", payload)

    def query_database(
        self,
        database_id: str,
        filter_obj: Optional[Dict[str, Any]] = None,
        start_cursor: Optional[str] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if filter_obj:
            payload["filter"] = filter_obj
        if start_cursor:
            payload["start_cursor"] = start_cursor
        if page_size:
            payload["page_size"] = page_size
        return self._request("POST", f"/databases/{database_id}/query", payload)

    def get_page(self, page_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/pages/{page_id}", None)

    def create_page(self, database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"parent": {"database_id": database_id}, "properties": properties}
        return self._request("POST", "/pages", payload)

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"properties": properties}
        return self._request("PATCH", f"/pages/{page_id}", payload)

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json",
        }
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(request) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            raise RuntimeError(f"Notion API error {exc.code}: {error_body}") from exc
