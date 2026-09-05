# Life Inbox — v0

Um briefing por dia, com o que a sua vida está pedindo de você.

Coleta Gmail e Google Calendar, separa em quatro baldes (**agenda**, **pedem ação**,
**dinheiro**, **ruído**) e manda uma mensagem curta no Telegram.

## Princípios

1. **Custo zero.** Google Cloud grátis, SQLite local, cron do sistema, Telegram grátis.
   Nenhuma chamada de LLM no v0 — a triagem é por regras, e regra não cobra nada.
2. **Somente leitura.** Os escopos são `gmail.readonly` e `calendar.readonly`.
   O v0 lê a sua vida, não mexe nela.
3. **Nada sai da sua máquina.** Banco, credencial e token ficam em `~/.life-inbox`
   com permissão `700`/`600`. O `.gitignore` bloqueia `*.db`, `credentials.json`
   e `token.json` — nada da sua vida entra no repositório.
4. **A saída é curta.** Se o briefing precisar de rolagem, a triagem está ruim:
   conserta a regra em `life/brain/rules.py`, não aumenta a mensagem.

## Instalação

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m life.main --demo --stdout      # vê o formato, sem tocar em nada seu
```

### Credencial do Google (~5 min, grátis)

1. <https://console.cloud.google.com> → criar projeto
2. **APIs e serviços** → ativar **Gmail API** e **Google Calendar API**
3. **Credenciais** → Criar credencial → **ID do cliente OAuth** → tipo
   **Aplicativo para computador**
4. Baixe o JSON e salve em `~/.life-inbox/credentials.json`

Na primeira execução o navegador abre pedindo autorização. O token fica salvo em
`~/.life-inbox/token.json` e renova sozinho depois disso.

> A tela de consentimento vai avisar que o app "não foi verificado". É esperado:
> o app é seu, publicado só pra você, e a verificação do Google só existe pra
> quem distribui pra terceiros. Basta se adicionar como usuário de teste.

### Telegram (opcional)

Sem `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` no `.env`, o briefing sai no terminal.
Com eles, chega no celular. O bot se cria pelo [@BotFather](https://t.me/botfather).

## Uso

```bash
python -m life.main                # coleta e envia o briefing
python -m life.main --stdout       # imprime em vez de enviar
python -m life.main --demo         # dados falsos, não chama o Google
python -m life.main --fonte gmail  # roda só uma fonte
python -m life.main --sem-banco    # não grava nada
```

### Agendar

Linux (crontab -e), 7h todo dia:

```
0 7 * * * /caminho/do/projeto/scripts/life-inbox.sh
```

macOS: `cron` funciona, mas se a tampa fica fechada prefira `launchd` com
`StartCalendarInterval` — ele executa o job atrasado quando a máquina acorda,
o `cron` simplesmente perde a janela.

## Como está organizado

```
life/
  config.py            caminhos, janelas, leitura do .env
  store.py             SQLite: uma tabela events pra todas as fontes
  google_auth.py       OAuth read-only, token com permissão 600
  collectors/
    gmail.py           metadados das últimas 24h (não baixa corpo)
    gcalendar.py       compromissos das próximas 48h
  brain/rules.py       triagem por regras — o coração do projeto
  outputs/telegram.py  saída (cai pro terminal se não configurado)
  brief.py             monta a mensagem
  main.py              orquestra: coleta → grava → resume
```

**Adicionar uma fonte nova** = escrever um `coletar()` que devolve dicts no formato
de `events` e registrar em `COLETORES` no `main.py`. Um coletor que falha não
derruba os outros.

## Dívidas conhecidas do v0

- A triagem é por palavra-chave: vai errar. O ajuste é editar as listas em
  `rules.py` conforme os erros aparecem — vale anotar os falsos negativos da
  primeira semana.
- Só a agenda primária do Google. Calendários compartilhados ficam de fora.
- O monitor de voos (`src/`) ainda roda separado, no GitHub Actions. Migrar ele
  pra `life/collectors/flights.py` é a próxima consolidação natural.
- Sem estado de "já vi isso": o briefing mostra o que é novo desde a última
  coleta, não o que você já leu.

## Próximos passos possíveis

| Passo | O que ganha |
|---|---|
| Migrar o monitor de voos pra dentro | uma coleta só, um briefing só |
| Coletor financeiro (OFX/CSV, depois Open Finance) | o balde "dinheiro" com valores reais, não estimados do assunto |
| Vault Obsidian em Git privado | memória de longo prazo que o agente lê e escreve |
| Telegram como entrada | você manda nota/áudio e o agente arquiva |
| LLM (Claude API) só no balde `info` | resolve o que a regra não dá conta — e só aí aparece custo |
| iCloud via CalDAV / Apple Health via Atalhos | o lado Apple, sem depender de API que não existe |
