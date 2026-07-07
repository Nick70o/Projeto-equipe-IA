import { obterProduto, criarProduto, atualizarProduto, criarLote } from './api.js';
import { showToast } from './utils.js';

const params = new URLSearchParams(window.location.search);
const produtoId = params.get('id');

const tituloPagina = document.getElementById('titulo-pagina');
const form = document.getElementById('form-produto');
const erroEl = document.getElementById('produto-erro');
const checkboxLote = document.getElementById('p-controla-lote');
const secaoLotes = document.getElementById('secao-lotes');
const listaLotes = document.getElementById('lista-lotes');
const btnAddLote = document.getElementById('btn-add-lote');
const templateLote = document.getElementById('template-lote');

const campos = {
  nome: document.getElementById('p-nome'),
  categoria: document.getElementById('p-categoria'),
  codigoBarras: document.getElementById('p-codigo-barras'),
  fornecedor: document.getElementById('p-fornecedor'),
  unidade: document.getElementById('p-unidade'),
  precoCusto: document.getElementById('p-preco-custo'),
  precoVenda: document.getElementById('p-preco-venda'),
  estoqueAtual: document.getElementById('p-estoque-atual'),
  estoqueMinimo: document.getElementById('p-estoque-minimo'),
};

checkboxLote.addEventListener('change', () => {
  secaoLotes.classList.toggle('hidden', !checkboxLote.checked);
});

function adicionarLinhaLote(numero = '', quantidade = '', validade = '') {
  const clone = templateLote.content.cloneNode(true);
  clone.querySelector('.lote-numero').value = numero;
  clone.querySelector('.lote-quantidade').value = quantidade;
  clone.querySelector('.lote-validade').value = validade;
  clone.querySelector('.btn-remover-lote').addEventListener('click', (e) => {
    e.target.closest('.linha-lote').remove();
  });
  listaLotes.appendChild(clone);
}

btnAddLote.addEventListener('click', () => adicionarLinhaLote());

function coletarLotes() {
  return [...listaLotes.querySelectorAll('.linha-lote')].map((linha) => ({
    numero_lote: linha.querySelector('.lote-numero')?.value?.trim() || '',
    quantidade: parseInt(linha.querySelector('.lote-quantidade').value, 10) || 0,
    data_validade: linha.querySelector('.lote-validade').value,
  })).filter((l) => l.quantidade > 0 && l.data_validade && l.numero_lote);
}

async function carregarParaEdicao() {
  tituloPagina.textContent = 'Editar Produto';
  try {
    const produto = await obterProduto(produtoId);
    campos.nome.value = produto.nome || '';
    campos.categoria.value = produto.categoria || '';
    campos.codigoBarras.value = produto.codigo_barras || '';
    campos.fornecedor.value = produto.fornecedor || '';
    campos.unidade.value = produto.unidade_medida || 'unidade';
    campos.precoCusto.value = produto.preco_custo ?? '';
    campos.precoVenda.value = produto.preco_venda ?? '';
    campos.estoqueAtual.value = produto.estoque_atual ?? '';
    campos.estoqueMinimo.value = produto.estoque_minimo ?? '';
    if (produto.controla_lote) {
      checkboxLote.checked = true;
      secaoLotes.classList.remove('hidden');
      (produto.lotes || []).forEach((l) => adicionarLinhaLote(l.numero_lote, l.quantidade, l.data_validade?.slice(0, 10)));
    }
  } catch (erro) {
    showToast(erro.message, 'erro');
  }
}

if (produtoId) {
  carregarParaEdicao();
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  erroEl.classList.add('hidden');

  if (!form.checkValidity()) {
    erroEl.textContent = 'Preencha este campo para continuar.';
    erroEl.classList.remove('hidden');
    form.reportValidity();
    return;
  }

  const payload = {
    nome: campos.nome.value.trim(),
    categoria: campos.categoria.value.trim(),
    codigo_barras: campos.codigoBarras.value.trim() || null,
    fornecedor: campos.fornecedor.value.trim() || null,
    unidade_medida: campos.unidade.value,
    preco_custo: parseFloat(campos.precoCusto.value) || null,
    preco_venda: parseFloat(campos.precoVenda.value),
    estoque_atual: parseInt(campos.estoqueAtual.value, 10),
    estoque_minimo: parseInt(campos.estoqueMinimo.value, 10) || 0,
    controla_lote: checkboxLote.checked,
  };

  const lotesParaCriar = checkboxLote.checked ? coletarLotes() : [];

  try {
    let idProdutoSalvo = produtoId;
    if (produtoId) {
      await atualizarProduto(produtoId, payload);
    } else {
      const produtoCriado = await criarProduto(payload);
      idProdutoSalvo = produtoCriado.id;
    }

    // O backend não aceita lotes junto do produto: criamos cada lote em sequência
    // via POST /produtos/{id}/lotes após o produto ser salvo com sucesso.
    for (const lote of lotesParaCriar) {
      await criarLote(idProdutoSalvo, lote);
    }

    showToast('Produto salvo com sucesso');
    window.location.href = 'estoque.html';
  } catch (erro) {
    erroEl.textContent = erro.message;
    erroEl.classList.remove('hidden');
  }
});
