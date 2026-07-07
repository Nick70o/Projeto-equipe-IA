import { buscarProduto, listarClientes, criarVenda, obterConfiguracoes, criarCobrancaPix, consultarStatusPix } from './api.js';
import { formatarMoeda, debounce, showToast } from './utils.js';

/**
 * Estado da venda em memória. Cada item: { id, nome, precoUnitario, quantidade, estoqueDisponivel, diasVencimento }
 * REGRA DE NEGÓCIO ASSUMIDA: "próximo do vencimento" = diasVencimento <= 30 (a confirmar com backend-dev).
 */
let itensVenda = [];
let formaPagamentoSelecionada = null;
let clienteFiadoSelecionado = null;

/**
 * Se true, o Pix passa a gerar cobrança real via Mercado Pago (QR Code) e a
 * venda só é confirmada após o pagamento ser detectado pelo polling de status.
 * Se false (padrão/fallback), o Pix continua instantâneo via POST /vendas.
 */
let pixGatewayAtivo = false;
let pollingPixIntervalId = null;
let vendaPixEmAndamentoId = null;

const buscaProdutoInput = document.getElementById('busca-produto');
const sugestoesProdutoEl = document.getElementById('sugestoes-produto');
const itensVendaBody = document.getElementById('itens-venda-body');
const valorSubtotalEl = document.getElementById('valor-subtotal');
const valorTotalEl = document.getElementById('valor-total');
const descontoInput = document.getElementById('desconto');
const btnFinalizar = document.getElementById('btn-finalizar');

const modalFechamento = document.getElementById('modal-fechamento');
const modalTotalEl = document.getElementById('modal-total');
const btnCancelarFechamento = document.getElementById('btn-cancelar-fechamento');
const btnConfirmarVenda = document.getElementById('btn-confirmar-venda');
const modalErroEl = document.getElementById('modal-erro');
const blocoDinheiro = document.getElementById('bloco-dinheiro');
const valorRecebidoInput = document.getElementById('valor-recebido');
const valorTrocoEl = document.getElementById('valor-troco');
const blocoFiado = document.getElementById('bloco-fiado');
const buscaClienteFiadoInput = document.getElementById('busca-cliente-fiado');
const sugestoesClienteFiadoEl = document.getElementById('sugestoes-cliente-fiado');
const clienteFiadoSelecionadoEl = document.getElementById('cliente-fiado-selecionado');

const modalConfirmacao = document.getElementById('modal-confirmacao');
const textoConfirmacaoEl = document.getElementById('texto-confirmacao');
const btnNovaVenda = document.getElementById('btn-nova-venda');
const btnImprimir = document.getElementById('btn-imprimir');

const fechamentoSelecaoEl = document.getElementById('fechamento-selecao');
const fechamentoPixAguardandoEl = document.getElementById('fechamento-pix-aguardando');
const pixQrcodeImg = document.getElementById('pix-qrcode-img');
const pixCopiaColaInput = document.getElementById('pix-copia-cola');
const btnCopiarPix = document.getElementById('btn-copiar-pix');
const pixStatusTextoEl = document.getElementById('pix-status-texto');
const pixErroEl = document.getElementById('pix-erro');
const btnCancelarPix = document.getElementById('btn-cancelar-pix');

/* ---------- Configuração do gateway de Pix (Mercado Pago) ---------- */

(async function carregarConfiguracaoPixGateway() {
  try {
    const config = await obterConfiguracoes();
    pixGatewayAtivo = Boolean(config?.pix_gateway_ativo);
  } catch (erro) {
    // Falha ao consultar configuração: mantém o comportamento padrão (Pix instantâneo, sem gateway).
    pixGatewayAtivo = false;
  }
})();

/* ---------- Busca de produto (autocomplete) ---------- */

const executarBusca = debounce(async (termo) => {
  if (!termo.trim()) {
    sugestoesProdutoEl.classList.add('hidden');
    sugestoesProdutoEl.innerHTML = '';
    return;
  }
  try {
    const resultados = await buscarProduto(termo);
    renderSugestoesProduto(resultados || []);
  } catch (erro) {
    showToast(erro.message, 'erro');
  }
}, 250);

buscaProdutoInput.addEventListener('input', (e) => executarBusca(e.target.value));

buscaProdutoInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    const primeiraSugestao = sugestoesProdutoEl.querySelector('[data-produto]');
    if (primeiraSugestao) {
      adicionarItem(JSON.parse(primeiraSugestao.dataset.produto));
    }
  }
});

function renderSugestoesProduto(produtos) {
  if (!produtos.length) {
    sugestoesProdutoEl.innerHTML = '<li class="px-4 py-3 text-legenda text-textmuted">Nenhum produto encontrado.</li>';
    sugestoesProdutoEl.classList.remove('hidden');
    return;
  }
  sugestoesProdutoEl.innerHTML = produtos.map((p) => `
    <li>
      <button type="button" data-produto='${JSON.stringify(p).replace(/'/g, '&apos;')}'
        class="w-full text-left px-4 py-3 hover:bg-primary-light flex justify-between items-center gap-2 border-b border-border last:border-0">
        <span>
          <span class="font-medium">${p.nome}</span>
          <span class="text-legenda block">Estoque: ${p.estoque_atual ?? '—'} un.</span>
        </span>
        <span class="text-corpo-forte">${formatarMoeda(p.preco_venda)}</span>
      </button>
    </li>`).join('');
  sugestoesProdutoEl.classList.remove('hidden');

  sugestoesProdutoEl.querySelectorAll('button[data-produto]').forEach((btn) => {
    btn.addEventListener('click', () => adicionarItem(JSON.parse(btn.dataset.produto)));
  });
}

document.addEventListener('click', (e) => {
  if (!sugestoesProdutoEl.contains(e.target) && e.target !== buscaProdutoInput) {
    sugestoesProdutoEl.classList.add('hidden');
  }
});

/* ---------- Itens da venda ---------- */

function adicionarItem(produto) {
  const existente = itensVenda.find((i) => i.id === produto.id);
  const estoqueDisponivel = produto.estoque_atual ?? Infinity;

  if (existente) {
    if (existente.quantidade + 1 > estoqueDisponivel) {
      showToast(`Estoque insuficiente — restam ${estoqueDisponivel} unidades`, 'erro');
      return;
    }
    existente.quantidade += 1;
  } else {
    if (estoqueDisponivel <= 0) {
      showToast(`Estoque insuficiente — restam ${estoqueDisponivel} unidades`, 'erro');
      return;
    }
    itensVenda.push({
      id: produto.id,
      nome: produto.nome,
      precoUnitario: produto.preco_venda,
      quantidade: 1,
      estoqueDisponivel,
      diasVencimento: produto.dias_para_vencer ?? null,
    });
  }

  buscaProdutoInput.value = '';
  sugestoesProdutoEl.classList.add('hidden');
  buscaProdutoInput.focus();
  renderItensVenda();
}

function alterarQuantidade(id, delta) {
  const item = itensVenda.find((i) => i.id === id);
  if (!item) return;
  const novaQtd = item.quantidade + delta;
  if (novaQtd < 1) return;
  if (novaQtd > item.estoqueDisponivel) {
    showToast(`Estoque insuficiente — restam ${item.estoqueDisponivel} unidades`, 'erro');
    return;
  }
  item.quantidade = novaQtd;
  renderItensVenda();
}

function definirQuantidadeManual(id, valor) {
  const item = itensVenda.find((i) => i.id === id);
  if (!item) return;
  const qtd = parseInt(valor, 10);
  if (Number.isNaN(qtd) || qtd < 1) return;
  if (qtd > item.estoqueDisponivel) {
    showToast(`Estoque insuficiente — restam ${item.estoqueDisponivel} unidades`, 'erro');
    renderItensVenda();
    return;
  }
  item.quantidade = qtd;
  renderItensVenda();
}

function removerItem(id) {
  itensVenda = itensVenda.filter((i) => i.id !== id);
  renderItensVenda();
}

function renderItensVenda() {
  if (!itensVenda.length) {
    itensVendaBody.innerHTML = '<tr id="linha-vazia"><td colspan="5" class="text-center text-textmuted py-8">Nenhum item adicionado. Busque um produto acima para começar.</td></tr>';
  } else {
    itensVendaBody.innerHTML = itensVenda.map((item) => {
      const subtotal = item.precoUnitario * item.quantidade;
      const alertaValidade = item.diasVencimento !== null && item.diasVencimento <= 30
        ? `<span class="badge badge-warning" title="Produto próximo do vencimento">Vence em ${item.diasVencimento} dias</span>`
        : '';
      return `
      <tr>
        <td data-label="Produto">
          <span class="font-medium">${item.nome}</span>
          ${alertaValidade ? `<div class="mt-1">${alertaValidade}</div>` : ''}
        </td>
        <td data-label="Qtd">
          <div class="flex items-center gap-1">
            <button type="button" class="btn-qtd btn-secondary !h-8 !px-2" data-acao="menos" data-id="${item.id}" aria-label="Diminuir quantidade">−</button>
            <input type="number" min="1" value="${item.quantidade}" data-id="${item.id}" class="input-qtd input-base !h-8 w-16 text-center" aria-label="Quantidade de ${item.nome}">
            <button type="button" class="btn-qtd btn-secondary !h-8 !px-2" data-acao="mais" data-id="${item.id}" aria-label="Aumentar quantidade">+</button>
          </div>
        </td>
        <td data-label="Preço unit.">${formatarMoeda(item.precoUnitario)}</td>
        <td data-label="Subtotal" class="text-corpo-forte">${formatarMoeda(subtotal)}</td>
        <td data-label="Remover">
          <button type="button" class="btn-remover text-danger hover:opacity-70" data-id="${item.id}" aria-label="Remover ${item.nome} da venda">🗑️</button>
        </td>
      </tr>`;
    }).join('');
  }

  itensVendaBody.querySelectorAll('.btn-qtd').forEach((btn) => {
    // data-id vem do DOM como string; itensVenda guarda id como number (vindo da API) — Number() evita
    // que a comparação estrita em find()/filter() nunca encontre o item.
    btn.addEventListener('click', () => alterarQuantidade(Number(btn.dataset.id), btn.dataset.acao === 'mais' ? 1 : -1));
  });
  itensVendaBody.querySelectorAll('.input-qtd').forEach((input) => {
    input.addEventListener('change', () => definirQuantidadeManual(Number(input.dataset.id), input.value));
  });
  itensVendaBody.querySelectorAll('.btn-remover').forEach((btn) => {
    btn.addEventListener('click', () => removerItem(Number(btn.dataset.id)));
  });

  atualizarTotais();
}

function calcularSubtotal() {
  return itensVenda.reduce((soma, item) => soma + item.precoUnitario * item.quantidade, 0);
}

function atualizarTotais() {
  const subtotal = calcularSubtotal();
  const desconto = parseFloat(descontoInput.value) || 0;
  const total = Math.max(subtotal - desconto, 0);

  valorSubtotalEl.textContent = formatarMoeda(subtotal);
  valorTotalEl.textContent = formatarMoeda(total);
  btnFinalizar.disabled = itensVenda.length === 0;
}

descontoInput.addEventListener('input', atualizarTotais);

/* ---------- Modal de fechamento ---------- */

btnFinalizar.addEventListener('click', abrirModalFechamento);

function abrirModalFechamento() {
  if (!itensVenda.length) return;
  modalTotalEl.textContent = valorTotalEl.textContent;
  modalErroEl.classList.add('hidden');
  modalFechamento.classList.remove('hidden');
}

function fecharModalFechamento() {
  pararPollingPix();
  modalFechamento.classList.add('hidden');
  formaPagamentoSelecionada = null;
  clienteFiadoSelecionado = null;
  clienteFiadoSelecionadoEl.textContent = '';
  buscaClienteFiadoInput.value = '';
  valorRecebidoInput.value = '';
  document.querySelectorAll('.btn-forma').forEach((b) => b.classList.remove('!bg-primary', '!text-white'));
  blocoDinheiro.classList.add('hidden');
  blocoFiado.classList.add('hidden');
  voltarParaSelecaoFormaPagamento();
}

btnCancelarFechamento.addEventListener('click', fecharModalFechamento);

/* ---------- Pix com gateway (Mercado Pago): estado de espera do pagamento ---------- */

function mostrarEsperaPix(cobranca) {
  fechamentoSelecaoEl.classList.add('hidden');
  fechamentoPixAguardandoEl.classList.remove('hidden');
  fechamentoPixAguardandoEl.classList.add('flex');
  pixErroEl.classList.add('hidden');
  pixStatusTextoEl.textContent = 'Aguardando confirmação do pagamento...';
  pixQrcodeImg.src = `data:image/png;base64,${cobranca.qr_code_base64}`;
  pixCopiaColaInput.value = cobranca.qr_code_copia_cola || '';
  vendaPixEmAndamentoId = cobranca.venda_id;
  btnCancelarPix.focus();

  pollingPixIntervalId = setInterval(() => verificarStatusPix(cobranca.venda_id), 3000);
}

function voltarParaSelecaoFormaPagamento() {
  fechamentoPixAguardandoEl.classList.add('hidden');
  fechamentoPixAguardandoEl.classList.remove('flex');
  fechamentoSelecaoEl.classList.remove('hidden');
  vendaPixEmAndamentoId = null;
}

function pararPollingPix() {
  if (pollingPixIntervalId) {
    clearInterval(pollingPixIntervalId);
    pollingPixIntervalId = null;
  }
}

async function verificarStatusPix(idVenda) {
  try {
    const { status } = await consultarStatusPix(idVenda);
    if (status === 'pago') {
      pararPollingPix();
      modalFechamento.classList.add('hidden');
      const total = Math.max(calcularSubtotal() - (parseFloat(descontoInput.value) || 0), 0);
      textoConfirmacaoEl.textContent = `Venda #${idVenda} concluída — Total ${formatarMoeda(total)}`;
      modalConfirmacao.classList.remove('hidden');
    } else if (status === 'expirado' || status === 'cancelado') {
      pararPollingPix();
      pixErroEl.textContent = 'Pagamento não confirmado — tente novamente ou escolha outra forma de pagamento.';
      pixErroEl.classList.remove('hidden');
      voltarParaSelecaoFormaPagamento();
    }
    // status "pendente": continua o polling normalmente.
  } catch (erro) {
    // Falha pontual de rede na consulta de status não interrompe o polling — tenta de novo no próximo ciclo.
  }
}

btnCancelarPix.addEventListener('click', () => {
  pararPollingPix();
  voltarParaSelecaoFormaPagamento();
});

btnCopiarPix.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(pixCopiaColaInput.value);
    showToast('Código Pix copiado.', 'sucesso');
  } catch (erro) {
    pixCopiaColaInput.select();
    showToast('Não foi possível copiar automaticamente — selecione e copie manualmente.', 'aviso');
  }
});

document.querySelectorAll('.btn-forma').forEach((btn) => {
  btn.addEventListener('click', () => {
    formaPagamentoSelecionada = btn.dataset.forma;
    document.querySelectorAll('.btn-forma').forEach((b) => b.classList.remove('!bg-primary', '!text-white'));
    btn.classList.add('!bg-primary', '!text-white');
    blocoDinheiro.classList.toggle('hidden', formaPagamentoSelecionada !== 'dinheiro');
    blocoFiado.classList.toggle('hidden', formaPagamentoSelecionada !== 'fiado');
  });
});

valorRecebidoInput.addEventListener('input', () => {
  const total = Math.max(calcularSubtotal() - (parseFloat(descontoInput.value) || 0), 0);
  const recebido = parseFloat(valorRecebidoInput.value) || 0;
  valorTrocoEl.textContent = formatarMoeda(Math.max(recebido - total, 0));
});

const buscarClienteDebounced = debounce(async (termo) => {
  if (!termo.trim()) {
    sugestoesClienteFiadoEl.classList.add('hidden');
    return;
  }
  try {
    const clientes = await listarClientes(termo);
    renderSugestoesCliente(clientes || []);
  } catch (erro) {
    showToast(erro.message, 'erro');
  }
}, 250);

buscaClienteFiadoInput.addEventListener('input', (e) => buscarClienteDebounced(e.target.value));

function renderSugestoesCliente(clientes) {
  if (!clientes.length) {
    sugestoesClienteFiadoEl.innerHTML = '<li class="px-3 py-2 text-legenda text-textmuted">Nenhum cliente encontrado.</li>';
    sugestoesClienteFiadoEl.classList.remove('hidden');
    return;
  }
  sugestoesClienteFiadoEl.innerHTML = clientes.map((c) => `
    <li><button type="button" data-cliente='${JSON.stringify(c).replace(/'/g, '&apos;')}' class="w-full text-left px-3 py-2 hover:bg-primary-light border-b border-border last:border-0">
      ${c.nome} <span class="text-legenda">${c.telefone || ''}</span>
    </button></li>`).join('');
  sugestoesClienteFiadoEl.classList.remove('hidden');
  sugestoesClienteFiadoEl.querySelectorAll('button[data-cliente]').forEach((btn) => {
    btn.addEventListener('click', () => {
      clienteFiadoSelecionado = JSON.parse(btn.dataset.cliente);
      clienteFiadoSelecionadoEl.textContent = `Cliente selecionado: ${clienteFiadoSelecionado.nome}`;
      sugestoesClienteFiadoEl.classList.add('hidden');
      buscaClienteFiadoInput.value = clienteFiadoSelecionado.nome;
    });
  });
}

btnConfirmarVenda.addEventListener('click', async () => {
  modalErroEl.classList.add('hidden');

  if (!formaPagamentoSelecionada) {
    modalErroEl.textContent = 'Preencha este campo para continuar.';
    modalErroEl.classList.remove('hidden');
    return;
  }
  if (formaPagamentoSelecionada === 'fiado' && !clienteFiadoSelecionado) {
    modalErroEl.textContent = 'Selecione o cliente para lançar esta venda como fiado';
    modalErroEl.classList.remove('hidden');
    return;
  }

  const subtotal = calcularSubtotal();
  const desconto = parseFloat(descontoInput.value) || 0;
  const total = Math.max(subtotal - desconto, 0);

  // Pix com gateway ativo (Mercado Pago): gera cobrança com QR Code e aguarda confirmação
  // de pagamento antes de considerar a venda concluída.
  if (formaPagamentoSelecionada === 'pix' && pixGatewayAtivo) {
    const payloadCobranca = {
      itens: itensVenda.map((i) => ({ produto_id: i.id, quantidade: i.quantidade })),
      desconto,
      cliente_id: clienteFiadoSelecionado ? clienteFiadoSelecionado.id : undefined,
    };

    btnConfirmarVenda.disabled = true;
    try {
      const cobranca = await criarCobrancaPix(payloadCobranca);
      mostrarEsperaPix(cobranca);
    } catch (erro) {
      modalErroEl.textContent = erro.message;
      modalErroEl.classList.remove('hidden');
    } finally {
      btnConfirmarVenda.disabled = false;
    }
    return;
  }

  const payload = {
    itens: itensVenda.map((i) => ({ produto_id: i.id, quantidade: i.quantidade, preco_unitario: i.precoUnitario })),
    subtotal,
    desconto,
    total,
    forma_pagamento: formaPagamentoSelecionada,
    cliente_id: formaPagamentoSelecionada === 'fiado' ? clienteFiadoSelecionado.id : null,
    valor_recebido: formaPagamentoSelecionada === 'dinheiro' ? parseFloat(valorRecebidoInput.value) || 0 : null,
  };

  btnConfirmarVenda.disabled = true;
  try {
    const venda = await criarVenda(payload);
    fecharModalFechamento();
    modalFechamento.classList.add('hidden');
    textoConfirmacaoEl.textContent = `Venda #${venda?.id ?? '—'} concluída — Total ${formatarMoeda(total)}`;
    modalConfirmacao.classList.remove('hidden');
  } catch (erro) {
    modalErroEl.textContent = erro.message;
    modalErroEl.classList.remove('hidden');
  } finally {
    btnConfirmarVenda.disabled = false;
  }
});

btnNovaVenda.addEventListener('click', () => {
  itensVenda = [];
  descontoInput.value = 0;
  renderItensVenda();
  modalConfirmacao.classList.add('hidden');
  buscaProdutoInput.focus();
});

btnImprimir.addEventListener('click', () => window.print());

/* ---------- Atalhos de teclado ---------- */

document.addEventListener('keydown', (e) => {
  if (e.key === 'F2') {
    e.preventDefault();
    buscaProdutoInput.focus();
  } else if (e.key === 'F9') {
    e.preventDefault();
    if (!btnFinalizar.disabled) abrirModalFechamento();
  } else if (e.key === 'Escape') {
    if (!modalFechamento.classList.contains('hidden')) fecharModalFechamento();
  }
});

renderItensVenda();
buscaProdutoInput.focus();
