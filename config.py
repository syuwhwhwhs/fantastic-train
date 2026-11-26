"""Configuration loader for RoXeT Emoji Extractor (reads .env next to this file)."""
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get(name: str) -> str:
    value = os.getenv(name, "").strip().strip('"').strip("'")
    if not value:
        sys.exit(f"Missing {name}. Fill it in {BASE_DIR / '.env'} (see .env.example).")
    return value


@dataclass(frozen=True)
class Config:
    bot_token: str
    owner_ids: frozenset


def load_config() -> Config:
    token = _get("BOT_TOKEN")
    try:
        owners = frozenset(int(x) for x in re.split(r"[,\s]+", _get("OWNER_ID")) if x)
    except ValueError:
        sys.exit("OWNER_ID must be numeric (several IDs allowed, comma-separated).")
    if not owners:
        sys.exit("OWNER_ID must contain at least one numeric Telegram user ID.")
    return Config(token, owners)
