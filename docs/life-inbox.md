# Life Inbox — v0

Um briefing por dia, com o que a sua vida está pedindo de você.

Coleta email e agenda, separa em quatro baldes (**agenda**, **pedem ação**,
**dinheiro**, **ruído**) e manda uma mensagem curta no Telegram às 7h.

Roda no GitHub Actions: **sem computador ligado e sem custo.**

## Princípios

1. **Custo zero.** GitHub Actions grátis, Telegram grátis, nenhuma chamada de LLM
   no v0 — a triagem é por regras, e regra não cobra nada.
2. **Não escreve nada.** A caixa é aberta em modo `readonly` e os cabeçalhos são
   lidos com `BODY.PEEK`, que não marca email como lido. Nada aqui altera sua vida.
3. **Só metadado.** Remetente, assunto, data e labels. **O corpo do email nunca é
   baixado** — o que não se armazena não vaza.
4. **O briefing nunca vai pro log.** Ele tem assunto de email dentro; sai direto
   pro Telegram, e o job se recusa a rodar em repositório público.
5. **A saída é curta.** Se precisar de rolagem, a triagem está ruim: conserta a
   regra em `life/brain/rules.py`, não aumenta a mensagem.

## Por que IMAP e não OAuth

O coletor OAuth (`collectors/gmail.py`) existe e funciona — mas só serve pra rodar
na sua máquina. Um app OAuth em modo *Testing* no Google **invalida o refresh token
a cada 7 dias**: o briefing quebraria toda semana, e sair do modo Testing exige
verificação do Google porque `gmail.readonly` é escopo restrito.

Senha de app não expira. Por isso o caminho da nuvem usa IMAP.

O preço: a senha de app dá acesso total ao IMAP (ler **e** apagar), não só leitura.
As mitigações estão nos princípios 2 e 3 acima — a sessão é `readonly` e nada é
escrito — mas o risco real fica: quem roubar essa senha lê seu email. Ela vive
como secret do GitHub (criptografado, nunca exposto a fork ou pull request) e você
revoga em um clique na sua conta Google se precisar.

O código escolhe o coletor sozinho: **tem `IMAP_USER`? usa IMAP. Senão, tem
`credentials.json`? usa OAuth.** Mesmo comando nos dois ambientes.

---

## Setup (~15 min, uma vez)

### 0. Deixe o repositório privado — antes de tudo

`Settings` → `General` → `Danger Zone` → `Change visibility` → **Private**.

Em repositório público **o log das Actions é visível pra qualquer pessoa**, e este
job lida com o seu email. O workflow tem uma trava que falha de propósito enquanto
o repo for público. Actions em repo privado continua grátis: o plano Free dá 2.000
minutos/mês e este job usa ~60.

### 1. Senha de app do Google

Precisa de verificação em duas etapas ativa na conta.

1. <https://myaccount.google.com/apppasswords>
2. Crie uma com o nome `Life Inbox` → copie as 16 letras
3. Se o IMAP der erro de login: Gmail → Ver todas as configurações →
   Encaminhamento e POP/IMAP → **Ativar IMAP**

### 2. Endereço secreto da agenda

Google Calendar → passe o mouse no calendário → ⋮ → **Configurações e
compartilhamento** → role até **Endereço secreto em formato iCal** → copie a URL.

Essa URL *é* a credencial: quem tiver ela lê sua agenda. Vai como secret, nunca no
código. Pra somar mais de um calendário, separe as URLs por vírgula.

### 3. Telegram

Fale com o [@BotFather](https://t.me/botfather) → `/newbot` → guarde o token.
Mande uma mensagem qualquer pro seu bot e abra
`https://api.telegram.org/bot<TOKEN>/getUpdates` pra achar seu `chat_id`.

### 4. Secrets no GitHub

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`:

| Secret | Valor |
|---|---|
| `IMAP_USER` | seu-email@gmail.com |
| `IMAP_PASSWORD` | a senha de app (16 letras) |
| `CALENDAR_ICS_URL` | a URL secreta do iCal |
| `TELEGRAM_BOT_TOKEN` | token do BotFather |
| `TELEGRAM_CHAT_ID` | seu chat id |

### 5. Testar

`Actions` → **Life Inbox** → `Run workflow`. O briefing chega no Telegram em ~1 min.
Depois disso ele roda sozinho às 7h (10:00 UTC), todo dia.

> Duas coisas do agendador do GitHub, pra não assustar: o horário pode atrasar
> alguns minutos em horário de pico, e workflows agendados são **desativados
> automaticamente após 60 dias sem nenhum commit no repositório**. Um commit
> qualquer religa.

---

## Rodar na sua máquina (opcional)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m life.main --demo --stdout     # vê o formato, sem tocar em nada seu
```

Com um `.env` local (veja `.env.example`), o mesmo comando roda de verdade:

```bash
python -m life.main --stdout       # imprime em vez de enviar
python -m life.main --fonte gmail  # só uma fonte
python -m life.main --sem-banco    # não grava nada
python -m life.main                # coleta e envia
```

Localmente também dá pra usar OAuth somente leitura em vez de senha de app: salve
a credencial de "Aplicativo para computador" do Google Cloud em
`~/.life-inbox/credentials.json` e o código passa a usá-la. Aí o histórico vai pro
SQLite em `~/.life-inbox/life.db` (permissão `600`), que é o que permite responder
"o que mudou desde ontem". Na nuvem o job roda com `--sem-banco`: o runner é
descartado no fim, então nada da sua vida fica lá.

## Como está organizado

```
life/
  config.py               caminhos, janelas, leitura do .env
  store.py                SQLite: uma tabela events pra todas as fontes
  google_auth.py          OAuth read-only (caminho local)
  collectors/
    __init__.py           escolhe nuvem ou local automaticamente
    gmail_imap.py         email por IMAP + senha de app   (nuvem)
    gcalendar_ics.py      agenda pela URL secreta iCal    (nuvem)
    gmail.py              email por OAuth readonly        (local)
    gcalendar.py          agenda por OAuth readonly       (local)
  brain/rules.py          triagem por regras — o coração do projeto
  outputs/telegram.py     saída (cai pro terminal se não configurado)
  brief.py                monta a mensagem
  main.py                 orquestra: coleta → grava → resume
```

**Adicionar uma fonte** = escrever um `coletar()` que devolve dicts no formato de
`events` e registrar em `collectors/__init__.py`. Um coletor que falha não derruba
os outros — o briefing sai com o resto e avisa o que quebrou.

## Dívidas conhecidas do v0

- A triagem é por palavra-chave: vai errar. Anote os erros da primeira semana e a
  gente ajusta as listas em `rules.py`.
- As categorias do Gmail (Promoções, Social) chegam pelo IMAP de forma menos
  confiável que pela API. Se muita promoção passar pelo filtro, é aí.
- Sem estado de "já vi isso" na nuvem: o briefing mostra as últimas 24h, não o que
  você ainda não leu.
- O monitor de voos (`src/`) ainda roda separado, no seu próprio workflow.

## Próximos passos possíveis

| Passo | O que ganha |
|---|---|
| Migrar o monitor de voos pra `collectors/flights.py` | uma coleta só, um briefing só |
| Coletor financeiro (OFX/CSV, depois Open Finance) | o balde "dinheiro" com valores reais, não estimados do assunto |
| Vault Obsidian em Git privado | memória de longo prazo que o agente lê e escreve |
| Telegram como entrada | você manda nota/áudio e o agente arquiva |
| LLM (Claude API) só no balde `info` | resolve o que a regra não dá conta — e só aí aparece custo |
| iCloud via CalDAV / Apple Health via Atalhos | o lado Apple, sem depender de API que não existe |
