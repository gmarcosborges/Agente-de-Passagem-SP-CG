#!/usr/bin/env bash
# Wrapper para agendar o briefing diario. Ajuste PROJETO para o seu caminho.
set -euo pipefail

PROJETO="${LIFE_INBOX_PROJECT:-$HOME/Agente-de-Passagem-SP-CG}"
cd "$PROJETO"

if [ -d .venv ]; then
  source .venv/bin/activate
fi

python3 -m life.main "$@" >> "$HOME/.life-inbox/run.log" 2>&1
