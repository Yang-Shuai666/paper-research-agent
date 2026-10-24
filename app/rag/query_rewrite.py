import json
import logging
import re
import threading
from functools import lru_cache
from pathlib import Path

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
SYSTEM_PROMPT = (
    "Translate the user question into a concise English search query for academic "
    "paper retrieval. Keep technical terms and acronyms. "
    "Output only the English query, no explanation."
)


class QueryRewriter:
    def __init__(
        self,
        settings: Settings | None = None,
        cache_path: str | Path | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.cache_path = Path(cache_path or self.settings.query_rewrite_cache_path)
        self._lock = threading.Lock()
        self._cache = self._load_cache()

    def rewrite(self, query: str) -> str:
        if not CJK_RE.search(query):
            return query
        with self._lock:
            cached = self._cache.get(query)
        if cached:
            return cached
        if not self.settings.deepseek_api_key:
            return query

        try:
            translated = self._translate(query)
        except Exception as error:  # noqa: BLE001 - retrieval must degrade gracefully
            logger.warning("Query rewrite failed, using original query: %s", error)
            return query
        if not translated:
            return query

        with self._lock:
            self._cache[query] = translated
            self._save_cache()
        return translated

    def _translate(self, query: str) -> str:
        with httpx.Client(timeout=self.settings.query_rewrite_timeout) as client:
            response = client.post(
                f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.deepseek_api_key}"},
                json={
                    "model": self.settings.deepseek_model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": query},
                    ],
                },
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content.strip().strip('"')

    def _load_cache(self) -> dict[str, str]:
        if not self.cache_path.exists():
            return {}
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return {str(key): str(value) for key, value in data.items()}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.cache_path)


@lru_cache
def get_rewriter() -> QueryRewriter:
    return QueryRewriter()
