import os
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = REPO_ROOT / ".env"


load_dotenv(ENV_PATH, override=False)


def get_env(name: str, default=None):
    return os.environ.get(name, default)
