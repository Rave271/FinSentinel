import json
from pathlib import Path
from typing import List


DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "nifty50_symbols.json"


def load_nifty50_symbols() -> List[str]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return [str(item).upper() for item in json.load(handle)]


NIFTY50_SYMBOLS = load_nifty50_symbols()
