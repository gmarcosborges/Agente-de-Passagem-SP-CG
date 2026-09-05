"""Configuracao central do Life Inbox.

Regra de ouro deste projeto: nada sensivel mora dentro do repositorio.
Credenciais, token e banco ficam em ~/.life-inbox (ou LIFE_INBOX_HOME).
"""
import os
from pathlib import Path

from dateutil import tz

BRT = tz.gettz("America/Sao_Paulo")


def _load_dotenv():
    """Le um .env simples da raiz do projeto, sem dependencia extra."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()

HOME = Path(os.environ.get("LIFE_INBOX_HOME", Path.home() / ".life-inbox"))
DB_PATH = Path(os.environ.get("LIFE_INBOX_DB", HOME / "life.db"))
CREDENTIALS_PATH = Path(os.environ.get("GOOGLE_CREDENTIALS", HOME / "credentials.json"))
TOKEN_PATH = Path(os.environ.get("GOOGLE_TOKEN", HOME / "token.json"))

# Janelas de coleta.
EMAIL_LOOKBACK_HOURS = int(os.environ.get("EMAIL_LOOKBACK_HOURS", "24"))
CALENDAR_LOOKAHEAD_HOURS = int(os.environ.get("CALENDAR_LOOKAHEAD_HOURS", "48"))
EMAIL_MAX_RESULTS = int(os.environ.get("EMAIL_MAX_RESULTS", "150"))


def ensure_home():
    HOME.mkdir(parents=True, exist_ok=True)
    os.chmod(HOME, 0o700)
    return HOME
