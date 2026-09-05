# Segurança, explicado sem termo técnico

Este documento existe pra você conseguir responder três perguntas sem precisar
entender o código: **onde ficam meus emails, quem consegue chegar neles, e o que
eu faço se algo der errado.**

## Onde ficam meus emails? Em lugar nenhum.

O programa **não guarda** os seus emails. O que acontece às 7h da manhã:

1. Um computador emprestado liga sozinho
2. Ele pergunta ao Gmail: "o que chegou nas últimas 24h?"
3. Recebe só o **remetente, o assunto e a data** — nunca o texto de dentro
4. Separa em quatro grupos e escreve um resumo
5. Manda o resumo pro seu Telegram
6. **O computador é destruído**, com tudo que estava nele

Leva menos de um minuto. Não sobra cópia em lugar nenhum. Não existe um "banco de
dados dos seus emails" nessa versão — é de propósito: o que não se guarda não vaza.

## O que fica guardado, então?

Só a **chave** pra chegar nos seus emails — não os emails. São cinco informações,
que ficam num cofre do GitHub chamado *Secrets*:

| O que é | Pra que serve |
|---|---|
| Seu endereço de email | dizer qual caixa abrir |
| Senha de app | a chave da caixa |
| Link secreto da agenda | ler seus compromissos |
| Token do bot do Telegram | falar com você |
| Seu ID no Telegram | saber pra quem mandar |

Esse cofre é criptografado. Nem a tela do GitHub mostra o conteúdo depois que você
salva — dá pra trocar, nunca pra ler de volta.

## Quem consegue chegar nesse cofre?

**Só quem entra na sua conta do GitHub.** Não existe outro caminho.

Por isso as duas defesas que importam de verdade são estas, e as duas são suas:

1. **O repositório precisa ser privado.** Se for público, o "diário de bordo" de
   cada execução fica visível pra qualquer pessoa na internet. As senhas continuam
   escondidas mesmo assim — mas um deslize futuro no código poderia jogar assunto
   de email nesse diário, e aí seria público pra sempre. O programa se recusa a
   rodar enquanto o repositório for público.
2. **Verificação em duas etapas na sua conta do GitHub.** É o que impede alguém de
   entrar com a sua senha roubada. Sem isso, todo o resto é enfeite.
   → <https://github.com/settings/security>

## "E se roubarem a senha de app?"

Primeiro, o que ela **não** é: **não é a senha da sua conta Google.** Quem tiver
ela em mãos:

- ❌ **não** consegue entrar na sua conta Google
- ❌ **não** consegue abrir o Gmail no navegador
- ❌ **não** consegue ver seu Drive, suas fotos, seu Pay
- ❌ **não** consegue trocar a sua senha
- ✅ consegue ler e apagar os seus emails, por programa

Ou seja: é sério, mas o estrago é limitado à caixa de email — e some na hora em que
você cancelar a senha, sem mexer em mais nada da sua vida digital.

### Como cancelar, se desconfiar de qualquer coisa

<https://myaccount.google.com/apppasswords> → achar `Life Inbox` → **Remover**.

Pronto. No mesmo segundo o acesso morre. Sua senha normal do Google continua
funcionando, seu email continua funcionando, e o programa simplesmente para de
rodar até você gerar outra.

Vale fazer isso sem medo à toa: é reversível em dois minutos.

## O que ainda é exposição, sendo honesto

Três coisas que não dá pra esconder de você:

1. **A senha de app lê e apaga.** O Google não oferece uma versão "só leitura"
   dela. Existe um jeito mais seguro (autorização somente-leitura, que torna
   impossível apagar), mas ele exige um cadastro bem mais chato no Google e tende a
   quebrar sozinho a cada 7 dias. O código já suporta os dois caminhos — é uma
   escolha sua, não uma limitação.
2. **O resumo chega pelo Telegram**, que guarda as conversas nos servidores dele.
   Os assuntos dos seus emails passam por lá. É uma conversa privada entre você e
   um bot que só você conhece, mas não é um cofre.
3. **Você confia no GitHub e no Telegram.** São empresas grandes e sérias, mas são
   terceiros. Zero terceiros só é possível com um computador seu ligado 24h — que
   foi justamente o que a gente descartou.

## Checklist de proteção

- [ ] Repositório **privado** (`Settings` → `General` → `Danger Zone`)
- [ ] Verificação em duas etapas no **GitHub**
- [ ] Verificação em duas etapas no **Google**
- [ ] Senha de app com nome `Life Inbox`, pra você saber qual cancelar
- [ ] Nunca colar senha dentro de arquivo de código — só no cofre de *Secrets*
