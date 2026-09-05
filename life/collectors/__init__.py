"""Escolhe qual coletor usar em cada dominio, conforme o que esta configurado.

Dois caminhos pro mesmo dado, e o codigo decide sozinho:

  nuvem (roda sem computador ligado)  IMAP + senha de app / URL secreta iCal
  local (sua maquina)                 OAuth somente leitura

O caminho da nuvem vem primeiro porque credencial que nao expira e o que
mantem um cron diario vivo.
"""
from life.config import CREDENTIALS_PATH


def disponiveis(apenas=None):
    """Devolve [(nome, funcao_coletar)] pros coletores utilizaveis agora."""
    escolhidos = []

    from life.collectors import gmail_imap
    if gmail_imap.configurado():
        escolhidos.append(("gmail", gmail_imap.coletar))
    elif CREDENTIALS_PATH.exists():
        from life.collectors import gmail
        escolhidos.append(("gmail", gmail.coletar))

    from life.collectors import gcalendar_ics
    if gcalendar_ics.configurado():
        escolhidos.append(("gcalendar", gcalendar_ics.coletar))
    elif CREDENTIALS_PATH.exists():
        from life.collectors import gcalendar
        escolhidos.append(("gcalendar", gcalendar.coletar))

    if apenas:
        escolhidos = [(n, f) for n, f in escolhidos if n in apenas]
    return escolhidos
