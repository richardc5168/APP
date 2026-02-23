from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
import yaml
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class SourceSpec:
    url: str
    grade: str
    topic_tags: list[str]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _compact(text: str) -> str:
    return " ".join((text or "").split())


def _clip(text: str, limit: int) -> str:
    compact = _compact(text)
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "…"


def _load_sources(path: Path) -> list[SourceSpec]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list) or not sources:
        raise SystemExit(f"No sources found in {path}")

    out: list[SourceSpec] = []
    for i, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise SystemExit(f"Invalid source entry #{i}: expected mapping")
        url = str(source.get("url") or "").strip()
        grade = str(source.get("grade") or "").strip()
        topic_tags = [str(x).strip() for x in (source.get("topic_tags") or []) if str(x).strip()]
        if not url:
            raise SystemExit(f"Invalid source entry #{i}: missing url")
        if grade not in ("5", "6"):
            raise SystemExit(f"Invalid source entry #{i}: grade must be 5 or 6")
        if not topic_tags:
            raise SystemExit(f"Invalid source entry #{i}: missing topic_tags")
        out.append(SourceSpec(url=url, grade=grade, topic_tags=topic_tags))
    return out


def _fetch_page(url: str) -> tuple[str, str]:
    response = requests.get(url, timeout=15, headers={"User-Agent": "ai-math-web/external-web-ingest"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    title = _compact(soup.title.get_text(" ", strip=True) if soup.title else url) or url
    body = _compact(soup.get_text(" ", strip=True))
    return title, body


def _make_note(*, note_id: str, source: SourceSpec, title: str, body_text: str, quoted: str) -> dict[str, Any]:
    summary = (
        "本筆記整理分數應用解題流程：先辨識量與單位，再選擇分數運算（通分、乘除或比率），"
        "最後做合理性檢查。"
    )
    return {
        "note_id": note_id,
        "source_url": source.url,
        "title": title,
        "retrieved_at": _now_iso(),
        "grade": source.grade,
        "topic_tags": source.topic_tags,
        "summary": _clip(summary, 200),
        "key_steps": [
            "先圈出題目中的整體量、部分量與單位。",
            "依題意選擇運算：折扣/比率用乘法，平均分配用除法，時間路程先做單位統一。",
            "列式後先估算，再精算。",
            "回代檢查答案是否合理且單位一致。",
        ],
        "common_mistakes": [
            "把折扣率當成付款率直接代入。",
            "平均分配時分母用錯（把份數和人數混淆）。",
            "路程時間題未先統一單位。",
            "分數乘除後忘記約分。",
            "算完沒有做反向檢查。",
        ],
        "example_patterns": [
            "購物折扣：原價×(1-折扣率)求現價。",
            "平均分配：總量÷份數求每份。",
            "單位換算：先換成同單位後再做分數運算。",
            "路程時間：距離=速度×時間，先統一時間或距離單位。",
        ],
        "quotes": [
            {
                "text": _clip(quoted, 25),
                "citation": source.url,
            }
        ],
        "trace_excerpt": _clip(body_text, 200),
    }


def _mock_note(source: SourceSpec, note_id: str) -> dict[str, Any]:
    return _make_note(
        note_id=note_id,
        source=source,
        title=f"(mock) {source.url}",
        body_text="offline mode generated trace text",
        quoted="分數題先看整體與部分",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="data/external_web_notes/sources.yaml")
    parser.add_argument("--out", default="data/external_web_notes/external_web_fraction_app_notes.jsonl")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)

    source_path = Path(args.sources)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    specs = _load_sources(source_path)

    lines: list[str] = []
    for index, spec in enumerate(specs, start=1):
        note_id = f"extnote_{index:04d}"
        try:
            if args.offline:
                note = _mock_note(spec, note_id)
            else:
                title, body = _fetch_page(spec.url)
                note = _make_note(note_id=note_id, source=spec, title=title, body_text=body, quoted=body)
        except Exception as error:
            note = _mock_note(spec, note_id)
            note["summary"] = _clip(f"collector_fallback: {type(error).__name__}", 200)
        lines.append(json.dumps(note, ensure_ascii=False))

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_path} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
