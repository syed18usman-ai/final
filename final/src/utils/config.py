from pathlib import Path
from typing import Any, Dict
import yaml


def load_config(path: str | Path = "configs/config.yaml") -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
