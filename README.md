# Agente de Passagem SP–CG

Dois programas, o mesmo padrão: coletar → filtrar → avisar no Telegram.

## `life/` — Life Inbox

Um briefing por dia com o que a sua vida está pedindo de você: Gmail e Google
Calendar entram, quatro baldes saem (agenda, pedem ação, dinheiro, ruído).
Roda local, somente leitura, custo zero.

```bash
python -m life.main --demo --stdout
```

Setup completo em **[docs/life-inbox.md](docs/life-inbox.md)**.

## `src/` — Monitor de voos SP → CGR

Procura voo direto ida e volta (quinta/sexta → domingo, 60–90 dias à frente) e
avisa quando o total fica abaixo do limite. Roda 1×/dia no GitHub Actions.

Segredos necessários: `SERPAPI_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
