"""Autenticacao Google, somente leitura.

Escopos read-only de proposito: o v0 le a sua vida, nao mexe nela.
O token fica em ~/.life-inbox/token.json com permissao 600 e nunca
entra no git.
"""
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from life.config import CREDENTIALS_PATH, TOKEN_PATH, ensure_home

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

SEM_CREDENCIAL = f"""
Faltou o arquivo de credencial do Google: {CREDENTIALS_PATH}

Como conseguir (leva ~5 min e nao custa nada):
  1. https://console.cloud.google.com -> crie um projeto
  2. "APIs e servicos" -> ative Gmail API e Google Calendar API
  3. "Credenciais" -> Criar credencial -> ID do cliente OAuth
     -> Tipo: Aplicativo para computador
  4. Baixe o JSON e salve como {CREDENTIALS_PATH}
"""


def get_credentials():
    ensure_home()
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise SystemExit(SEM_CREDENCIAL)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        os.chmod(TOKEN_PATH, 0o600)

    return creds


def service(name, version):
    return build(name, version, credentials=get_credentials(), cache_discovery=False)
