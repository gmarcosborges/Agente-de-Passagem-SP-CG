# Agente de Passagem SP–CG

Dois programas, o mesmo padrão: coletar → filtrar → avisar no Telegram.
Os dois rodam sozinhos no GitHub Actions, sem servidor e sem custo.

## `life/` — Life Inbox

Um briefing às 7h com o que a sua vida está pedindo de você: email e agenda
entram, quatro baldes saem (agenda, pedem ação, dinheiro, ruído).

Somente leitura, só metadado, e o briefing nunca vai parar no log — vai direto
pro Telegram.

```bash
python -m life.main --demo --stdout    # vê o formato, sem tocar em nada seu
```

Setup completo em **[docs/life-inbox.md](docs/life-inbox.md)**.
Segurança explicada sem jargão em **[docs/seguranca.md](docs/seguranca.md)**.
Secrets: `IMAP_USER`, `IMAP_PASSWORD`, `CALENDAR_ICS_URL`, `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_CHAT_ID`.

> Este repositório precisa ser **privado** pra rodar o Life Inbox: log de Actions
> em repo público é visível pra qualquer pessoa. O workflow falha de propósito
> enquanto não for.

## `src/` — Monitor de voos SP → CGR

Procura voo direto ida e volta (quinta/sexta → domingo, 60–90 dias à frente) e
avisa quando o total fica abaixo do limite. Roda 1×/dia.

Secrets: `SERPAPI_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
