# Especificação de Design — Sistema de Gestão para Farmácia (Local/Web)

## Suposições registradas
Como o pedido não detalhou alguns pontos, assumi o seguinte (ajustar se divergir da realidade do cliente):
- Uso majoritário em desktop/notebook com mouse e teclado no balcão; pode haver leitor de código de barras (entrada via teclado, sem hardware especial).
- Tela de PDV é acionada dezenas/centenas de vezes por dia — é a ação mais frequente do sistema e deve ser otimizada para velocidade, não para "bonito".
- Um único responsável (dono/gerente) acessa relatórios financeiros; atendentes comuns podem não precisar ver essa tela — sugerido controle de perfil simples (Atendente / Responsável), a confirmar com backend-dev sobre autenticação.
- Ambiente de trabalho: uso prolongado, muitas vezes com luz de loja forte — prioridade máxima para contraste e legibilidade, zero decoração supérflua.
- Sem necessidade de responsividade mobile completa (é uso local em balcão), mas o layout deve funcionar bem em telas de 1280–1440px (notebook comum) e também não quebrar em tablets (768px), caso o cliente use um tablet no caixa.

---

## 1. Objetivo do sistema (visão geral)

**Ação principal do sistema como um todo:** permitir que o atendente registre uma venda no PDV o mais rápido possível, com baixa automática e correta do estoque, minimizando erro humano e cliques.

**Métrica de sucesso:** tempo médio para concluir uma venda simples (1-3 itens) abaixo de 20 segundos, sem erros de digitação de preço/quantidade, e zero divergência entre estoque físico e sistema.

Todas as outras telas (estoque, validade, fiado, relatórios) são de suporte a essa operação central e devem ser acessíveis em no máximo 1-2 cliques a partir de qualquer tela.

---

## 2. Estrutura de navegação

### Navegação principal (menu lateral fixo, sempre visível)
Ícone + rótulo, ordem por frequência de uso:

1. **PDV / Venda** (tela inicial padrão ao abrir o sistema)
2. **Estoque**
3. **Validade / Lotes**
4. **Clientes e Fiado**
5. **Relatórios**
6. **Configurações** (rodapé do menu, uso raro: dados da farmácia, usuários)

- Menu lateral esquerdo, ~72px larguras retraído (só ícones) e ~220px expandido (ícone + texto). Em telas ≥1280px inicia expandido; em 768–1279px inicia retraído com botão para expandir.
- Cabeçalho superior fixo: nome da farmácia (ou logo), nome do usuário logado, data/hora do sistema, botão de logout.
- Sem breadcrumbs necessários — a estrutura é rasa (nunca mais de 2 níveis).

### Mapa de telas
```
/pdv                → Tela de Venda (padrão ao logar)
/pdv/fechamento      → Resumo antes de confirmar venda (pode ser modal, não página separada)
/estoque             → Lista de produtos
/estoque/novo        → Cadastro de produto (modal ou página)
/estoque/:id         → Edição de produto + histórico de entrada/saída
/validade            → Painel de alertas de vencimento
/clientes            → Lista de clientes
/clientes/:id        → Ficha do cliente (histórico + fiado)
/relatorios          → Dashboard financeiro
/configuracoes       → Dados da farmácia, usuários, perfis
```

---

## 3. Fluxo principal: venda no balcão até baixa no estoque

Passo a passo que a interface deve suportar sem fricção:

1. Atendente abre o sistema → cai direto na tela **PDV**, com o cursor já focado no campo de busca de produto.
2. Digita nome do produto OU código de barras (leitor de código de barras "digita" no campo e aperta Enter automaticamente) → sistema busca em tempo real (autocomplete) exibindo nome, preço, estoque disponível.
3. Seleciona o produto (Enter ou clique) → produto entra na lista da venda com quantidade 1; atendente pode ajustar quantidade direto na linha (input numérico com +/- e edição manual).
4. Repete para múltiplos itens. A lista de itens da venda fica sempre visível à direita ou abaixo, com subtotal por item e total geral atualizado em tempo real, em destaque (maior fonte, cor de contraste).
5. Se o produto está **próximo do vencimento** (definido pela regra de validade), exibir um selo/aviso discreto na linha do item ("Vence em 15 dias") — não bloqueia a venda, apenas informa.
6. Se o produto está com **estoque zerado ou insuficiente** para a quantidade pedida, bloquear o incremento e mostrar aviso claro ("Estoque insuficiente: restam 2 unidades").
7. Atendente clica em **"Finalizar Venda"** (botão primário, grande, fixo no canto inferior direito ou barra fixa no rodapé da tela de PDV — sempre visível sem rolar).
8. Abre modal de fechamento: forma de pagamento (Dinheiro / Cartão / Pix / Fiado), campo de valor recebido (se dinheiro, calcula troco automaticamente), e se "Fiado" for selecionado, exige vincular a um cliente cadastrado (busca rápida ou cadastro rápido inline).
9. Confirma → sistema:
   - Dá baixa automática no estoque de cada item vendido.
   - Se fiado, lança valor na conta do cliente.
   - Gera registro na venda para relatórios.
   - Mostra tela de confirmação simples ("Venda #1234 concluída — Total R$ 45,90") com opção de imprimir/gerar recibo (se aplicável) e botão "Nova Venda" que limpa a tela e volta ao passo 1.

**Atalhos de teclado recomendados** (reduzem tempo por venda): F2 ou Enter para focar busca, F9 para finalizar venda, Esc para cancelar item selecionado. Definir a lista final com o frontend-dev/backend-dev.

---

## 4. Estrutura de seções por tela

### 4.1 Tela PDV / Venda
- **Cabeçalho da tela:** número da venda em andamento (rascunho), nome do atendente.
- **Área de busca (topo, dominante):** campo grande de busca de produto/código de barras, autocomplete com foto opcional/ícone de categoria, preço e estoque disponível na lista de sugestões.
- **Lista de itens da venda (corpo, ocupa maior área):** tabela com colunas Produto | Qtd (editável) | Preço unit. | Subtotal | Remover (ícone lixeira). Linha destacada ao passar o mouse.
- **Painel lateral/rodapé de totais (sempre visível, fixo):** Subtotal, Desconto (opcional, campo simples), Total em destaque (fonte grande, cor primária), botão "Finalizar Venda".
- **Alertas inline:** validade próxima (ícone amarelo) e estoque insuficiente (ícone vermelho, bloqueante) diretamente na linha do item.

### 4.2 Tela Estoque
- **Cabeçalho:** título "Estoque", botão primário "+ Novo Produto" (canto superior direito), campo de busca/filtro por nome ou categoria.
- **Filtros secundários:** categoria, estoque baixo (checkbox "mostrar apenas estoque baixo").
- **Tabela de produtos:** colunas Nome | Categoria | Estoque atual | Estoque mínimo | Preço de venda | Ações (editar/entrada/saída).
  - Linha com estoque abaixo do mínimo: fundo levemente vermelho/laranja claro + ícone de alerta.
  - Linha com estoque zerado: destaque mais forte (vermelho).
- **Ação rápida "Entrada/Saída":** modal simples com campo quantidade, motivo (compra, ajuste, perda, devolução) e observação opcional — não deve exigir passar pela edição completa do produto.

### 4.3 Cadastro/Edição de Produto (modal ou página)
Campos: Nome*, Categoria*, Código de barras, Fornecedor (opcional), Preço de custo, Preço de venda*, Estoque atual*, Estoque mínimo (para alertas), Unidade de medida (unidade, caixa, ml, mg), controla lote/validade (sim/não).
Se "controla lote/validade" = sim, exibe seção adicional para cadastrar lote + data de validade (pode ter múltiplos lotes por produto).

### 4.4 Tela Validade / Lotes
- **Cabeçalho:** título "Controle de Validade", filtro por período (Vence em 30 / 60 / 90 dias, ou "já vencido").
- **Cards de resumo (topo):** 3 cards — "Vencidos" (vermelho), "Vence em 30 dias" (laranja), "Vence em 90 dias" (amarelo) — com contagem, clicáveis para filtrar a tabela abaixo.
- **Tabela:** Produto | Lote | Quantidade | Data de validade | Dias restantes | Ação (dar baixa/descartar).
- Ordenação padrão: data de validade mais próxima primeiro.

### 4.5 Tela Clientes e Fiado
- **Lista de clientes:** busca por nome/telefone, coluna com saldo devedor em destaque (vermelho se > 0), botão "+ Novo Cliente".
- **Ficha do cliente (ao clicar):**
  - Dados cadastrais (nome, telefone, endereço opcional).
  - Saldo devedor atual em destaque grande no topo.
  - Botão "Registrar Pagamento" (abate do saldo).
  - Histórico de compras (tabela: data, itens, valor, forma de pagamento) e histórico de pagamentos de fiado.

### 4.6 Tela Relatórios (Dashboard financeiro)
- **Filtro de período no topo:** hoje / semana / mês / personalizado.
- **Cards de indicadores (linha superior):** Faturamento total, Lucro estimado, Ticket médio, Nº de vendas — números grandes, um dominante (Faturamento).
- **Gráfico de faturamento ao longo do tempo:** gráfico de linha ou barras simples (evitar bibliotecas pesadas — usar algo leve tipo Chart.js).
- **Tabela "Produtos mais vendidos":** ranking top 10, colunas Produto | Qtd vendida | Faturamento gerado.
- Sem filtros excessivos — priorizar clareza sobre customização avançada.

---

## 5. Tokens de design

### Cores
Paleta pensada para uso prolongado, alto contraste, sóbria (ambiente de saúde/farmácia), com cor de destaque em verde-azulado (associação a saúde/confiança) e vermelho/laranja reservados exclusivamente para alertas.

```
--color-primary:        #0F766E   (verde-azulado escuro — ações principais, botão Finalizar Venda)
--color-primary-hover:  #0B5D57
--color-primary-light:  #CCFBF1   (fundos leves, selecionado)

--color-surface:        #FFFFFF   (fundo de cards/tabelas)
--color-background:     #F4F6F7   (fundo geral da aplicação)
--color-border:         #D9DEE1

--color-text:           #1F2937   (texto principal, quase preto)
--color-text-muted:     #5B6672   (texto secundário, legendas)
--color-text-inverse:   #FFFFFF   (texto sobre cor primária/escura)

--color-success:        #15803D   (confirmações, estoque ok)
--color-success-bg:     #DCFCE7

--color-warning:        #B45309   (validade próxima, estoque baixo)
--color-warning-bg:     #FEF3C7

--color-error:          #B91C1C   (estoque zerado, vencido, saldo devedor)
--color-error-bg:       #FEE2E2

--color-focus:          #0F766E   (outline de foco em inputs, 2px)
```

Contraste verificado: `--color-text` (#1F2937) sobre `--color-background` (#F4F6F7) e `--color-surface` (#FFFFFF) supera 12:1 (AA/AAA). `--color-text-inverse` sobre `--color-primary` supera 5:1.

### Tipografia
Fonte única do Google Fonts para reduzir peso de carregamento: **Inter** (pesos 400, 500, 600, 700).

```
h1  — 28px / 700 / line-height 1.3   (título de página, ex.: "Estoque")
h2  — 22px / 600 / line-height 1.3   (título de seção/card)
h3  — 18px / 600 / line-height 1.4   (subtítulos, cabeçalho de tabela em destaque)
h4  — 16px / 600 / line-height 1.4   (labels de destaque)

corpo        — 15px / 400 / line-height 1.5   (texto padrão, tabelas)
corpo-forte  — 15px / 600 / line-height 1.5   (valores importantes em tabela, ex. saldo)
legenda      — 13px / 400 / line-height 1.4   (auxiliares, timestamps, ajuda)

botão        — 15px / 600 / line-height 1   (texto de botões)
valor-destaque — 32px / 700 / line-height 1.2  (Total da venda, saldo devedor, indicadores do dashboard)
```

Números importantes (total da venda, saldo do cliente, indicadores financeiros) sempre usam `valor-destaque` ou `corpo-forte` para garantir leitura rápida à distância.

### Escala de espaçamento (base 4/8px)
`4, 8, 12, 16, 24, 32, 48, 64` — usar exclusivamente estes valores para padding, margin e gaps.
- Espaçamento interno de cards/tabelas: 16px.
- Espaçamento entre seções de uma página: 24–32px.
- Espaçamento entre itens de menu lateral: 8px.
- Altura mínima de área clicável (botões, linhas de tabela com ação): 40px (conforto para uso repetitivo no balcão).

### Componentes-base (padrões a manter em todo o sistema)
- Botão primário: fundo `--color-primary`, texto branco, radius 6px, altura 44px, padding horizontal 20px.
- Botão secundário: fundo transparente, borda 1px `--color-border`, texto `--color-text`.
- Inputs: altura 44px, borda 1px `--color-border`, radius 6px, foco com outline 2px `--color-focus`.
- Tabelas: cabeçalho com fundo `--color-background` e texto `--color-text-muted` em maiúsculas 13px; linhas com hover em `--color-primary-light` leve.
- Alertas/badges: pill (radius total), fundo `-bg` correspondente, texto na cor sólida (ex.: badge de validade usa `--color-warning-bg` + texto `--color-warning`).

---

## 6. Comportamento responsivo

### 360px (uso emergencial em celular/tablet pequeno — cenário secundário)
- Menu lateral vira menu inferior fixo (bottom bar) com os 4 itens mais usados (PDV, Estoque, Validade, Clientes) + botão "mais" para o resto.
- Tela de PDV: busca de produto no topo, lista de itens em cards empilhados (não tabela), total fixo no rodapé com botão Finalizar Venda ocupando largura total.
- Tabelas (Estoque, Clientes, Relatórios) viram lista de cards: cada linha vira um card com label + valor empilhados verticalmente.
- Gráficos do dashboard simplificados ou ocultos, priorizando os cards de indicadores numéricos.

### 768px (tablet — cenário provável em alguns balcões)
- Menu lateral retrátil (ícones apenas), expansível por toque.
- Tela de PDV: busca + lista de itens em coluna única, mas já em formato de tabela (não cards); painel de total fixo no rodapé.
- Tabelas de Estoque/Clientes/Validade mantêm formato de tabela, mas com menos colunas visíveis (ocultar colunas secundárias como "Fornecedor"; acessível ao expandir a linha).

### 1280px+ (desktop/notebook — cenário principal esperado)
- Menu lateral expandido (ícone + texto) sempre visível.
- Tela de PDV em duas colunas: busca + lista de itens à esquerda (proporção ~65%), painel de totais e forma de pagamento fixo à direita (~35%), sem necessidade de rolar para finalizar a venda.
- Tabelas completas com todas as colunas visíveis.
- Dashboard de relatórios em grid: 4 cards de indicadores lado a lado, gráfico full-width abaixo, tabela de produtos mais vendidos ao lado ou abaixo do gráfico.

---

## 7. Microcopy sugerida (PT-BR)

### Geral
- Botão principal do PDV: **"Finalizar Venda"**
- Botão de nova venda após concluir: **"Nova Venda"**
- Botão cadastro: **"+ Novo Produto"**, **"+ Novo Cliente"**
- Campo de busca do PDV (placeholder): **"Buscar produto por nome ou código de barras..."**
- Confirmação de venda: **"Venda #{numero} concluída — Total R$ {valor}"**

### Estoque
- Título da página: **"Estoque"**
- Alerta de estoque baixo (badge): **"Estoque baixo"**
- Alerta de estoque zerado: **"Sem estoque"**
- Erro de quantidade insuficiente: **"Estoque insuficiente — restam {n} unidades"**
- Confirmação de entrada de estoque: **"Entrada registrada com sucesso"**

### Validade
- Título da página: **"Controle de Validade"**
- Card de resumo: **"Vencidos"**, **"Vencem em 30 dias"**, **"Vencem em 90 dias"**
- Badge na linha do item (PDV/estoque): **"Vence em {n} dias"**
- Ação: **"Dar baixa (descarte)"**

### Clientes e Fiado
- Título da página: **"Clientes"**
- Saldo devedor em destaque: **"Saldo devedor: R$ {valor}"**
- Botão: **"Registrar Pagamento"**
- Sem histórico: **"Nenhuma compra registrada ainda."**
- Ao vincular fiado na venda: **"Selecione o cliente para lançar esta venda como fiado"**

### Relatórios
- Título da página: **"Relatórios"**
- Cards: **"Faturamento"**, **"Lucro estimado"**, **"Ticket médio"**, **"Vendas realizadas"**
- Tabela: **"Produtos mais vendidos"**
- Filtro de período: **"Hoje"**, **"Últimos 7 dias"**, **"Este mês"**, **"Personalizado"**

### Erros e vazios (tom direto, sem jargão técnico)
- Campo obrigatório vazio: **"Preencha este campo para continuar."**
- Erro de conexão com o servidor local: **"Não foi possível salvar. Verifique se o sistema está aberto corretamente e tente novamente."**
- Lista vazia (estoque): **"Nenhum produto cadastrado ainda. Clique em '+ Novo Produto' para começar."**
