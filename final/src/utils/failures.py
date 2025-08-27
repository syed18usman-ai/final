from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def append_failure(logs_dir: str, reason: str, payload: Dict[str, Any]) -> None:
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    line = {
        "time": datetime.utcnow().isoformat(),
        "reason": reason,
        "payload": payload,
    }
    with open(Path(logs_dir) / "failed_items.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
