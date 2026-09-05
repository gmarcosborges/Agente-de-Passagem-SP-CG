"""Triagem barata, por regras.

Filosofia: regra resolve 95% e custa zero. So o que sobra e caro.
Quando o v1 ganhar um LLM, ele so olha o que cair em "info" aqui.

Baldes:
  acao        - alguem espera algo de voce
  dinheiro    - saiu, entrou ou vai sair dinheiro
  compromisso - hora marcada
  info        - relevante mas nao exige nada
  ruido       - promocao, newsletter, rede social
"""
import re
import unicodedata

RE_VALOR = re.compile(r"R\$\s*([\d]{1,3}(?:\.\d{3})*|\d+)(?:,(\d{2}))?", re.I)

TERMOS_DINHEIRO = (
    "fatura", "boleto", "cobranca", "cobrancas", "pagamento", "pagar",
    "vencimento", "vence", "nota fiscal", "nfe", "recibo", "comprovante",
    "debito automatico", "pix", "transferencia", "mensalidade", "parcela",
    "reembolso", "estorno", "saldo", "extrato", "cartao de credito",
    "assinatura renovada", "sua compra", "pedido confirmado",
)

TERMOS_ACAO = (
    "confirme", "confirmar", "confirmacao", "responda", "aguardando",
    "pendente", "pendencia", "prazo", "ate hoje", "ultimo dia", "expira",
    "acao necessaria", "requer atencao", "assine", "assinatura pendente",
    "documento para assinar", "verifique", "atualize", "convite",
    "aprovacao", "aprove", "resposta necessaria",
)

TERMOS_RUIDO = (
    "newsletter", "promocao", "promocoes", "desconto", "black friday",
    "oferta imperdivel", "cupom", "novidades da semana", "webinar",
    "ultimas vagas", "nao perca",
)

REMETENTES_ROBO = ("no-reply", "noreply", "nao-responda", "donotreply", "mailer-daemon")


def normalizar(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def extrair_valor(texto):
    """Devolve o maior valor em R$ encontrado, ou None."""
    valores = []
    for inteiro, centavos in RE_VALOR.findall(texto or ""):
        try:
            valores.append(float(inteiro.replace(".", "") + "." + (centavos or "00")))
        except ValueError:
            continue
    return max(valores) if valores else None


def _tem(texto, termos):
    return any(t in texto for t in termos)


def classificar_email(assunto, remetente, labels, tem_unsubscribe=False):
    """Classifica um email nos baldes. Ordem importa: dinheiro > acao > ruido."""
    texto = normalizar(f"{assunto} {remetente}")
    labels = set(labels or [])

    if _tem(texto, TERMOS_DINHEIRO):
        return "dinheiro"

    # Promocional pelo proprio Google, ou newsletter declarada: ruido.
    if "CATEGORY_PROMOTIONS" in labels or "CATEGORY_SOCIAL" in labels:
        return "ruido"
    if _tem(texto, TERMOS_RUIDO):
        return "ruido"
    if tem_unsubscribe and "IMPORTANT" not in labels:
        return "ruido"

    if _tem(texto, TERMOS_ACAO):
        return "acao"

    # Gente de verdade escrevendo direto pra voce quase sempre quer algo.
    remetente_norm = normalizar(remetente)
    robo = any(r in remetente_norm for r in REMETENTES_ROBO)
    if not robo and "CATEGORY_PERSONAL" in labels and "UNREAD" in labels:
        return "acao"

    return "info"
