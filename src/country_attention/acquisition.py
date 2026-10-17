"""Public HTTP downloads with immutable, content-addressed cache and receipts."""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx


class CachedHTTP:
    def __init__(self, root: Path, *, offline: bool = False, refresh: bool = False):
        self.root = root
        self.offline = offline
        self.refresh = refresh
        self.receipts: list[dict] = []
        self.root.mkdir(parents=True, exist_ok=True)

    def get_json(self, url: str, params: dict | None = None):
        request = httpx.Request("GET", url, params=params)
        full_url = str(request.url)
        key = hashlib.sha256(full_url.encode()).hexdigest()[:24]
        receipt_path = self.root / f"{key}.json"
        if receipt_path.exists() and not self.refresh:
            receipt = json.loads(receipt_path.read_text())
            body_path = self.root / receipt["body_file"]
            body = body_path.read_bytes()
            if hashlib.sha256(body).hexdigest() != receipt["sha256"]:
                raise ValueError(f"Cache checksum mismatch: {body_path}")
            self.receipts.append(receipt)
            return json.loads(body)
        if self.offline:
            raise FileNotFoundError(f"No cached response for {full_url}")
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            for attempt in range(3):
                response = client.get(
                    full_url, headers={"User-Agent": "country-attention-research/0.1"}
                )
                if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                    # Google is never retried here: this client only downloads World Bank data.
                    time.sleep(min(2 ** (attempt + 1), 8))
                    continue
                response.raise_for_status()
                body = response.content
                data = response.json()
                break
        digest = hashlib.sha256(body).hexdigest()
        body_path = self.root / f"{digest}.body.json"
        body_path.write_bytes(body)
        receipt = {
            "url": full_url,
            "retrieved_at": datetime.now(UTC).isoformat(),
            "sha256": digest,
            "body_file": body_path.name,
            "http_status": response.status_code,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        self.receipts.append(receipt)
        return data


def world_bank_pages(client: CachedHTTP, path: str, **params) -> list[dict]:
    rows, page, pages = [], 1, 1
    while page <= pages:
        data = client.get_json(
            f"https://api.worldbank.org/v2/{path}",
            {
                "format": "json",
                "per_page": 20000,
                **params,
                "page": page,
            },
        )
        if not isinstance(data, list) or len(data) != 2 or not isinstance(data[0], dict):
            raise ValueError(f"Unexpected World Bank response for {path}: {str(data)[:160]}")
        if data[1] is None or not isinstance(data[1], list):
            raise ValueError(f"World Bank returned no result rows for {path}")
        pages = int(data[0]["pages"])
        if pages < 1 or int(data[0]["page"]) != page:
            raise ValueError("Invalid World Bank pagination")
        rows.extend(data[1])
        page += 1
    return rows
