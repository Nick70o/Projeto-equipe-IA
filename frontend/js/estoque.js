import { listarEstoque, registrarMovimentacaoEstoque } from './api.js';
import { formatarMoeda, debounce, showToast } from './utils.js';

const estoqueBody = document.getElementById('estoque-body');
const filtroBusca = document.getElementById('filtro-busca');
const filtroCategoria = document.getElementById('filtro-categoria');
const filtroEstoqueBaixo = document.getElementById('filtro-estoque-baixo');

const modalMovimentacao = document.getElementById('modal-movimentacao');
const formMovimentacao = document.getElementById('form-movimentacao');
const movProdutoNomeEl = document.getElementById('movimentacao-produto-nome');
const movErroEl = document.getElementById('mov-erro');
const btnCancelarMovimentacao = document.getElementById('btn-cancelar-movimentacao');

let produtoEmMovimentacao = null;
let produtosCache = [];

function linhaClasses(produto) {
  if ((produto.estoque_atual ?? 0) <= 0) return 'linha-critica';
  if (produto.estoque_atual <= produto.estoque_minimo) return 'linha-alerta';
  return '';
}

function badgeEstoque(produto) {
  if ((produto.estoque_atual ?? 0) <= 0) return '<span class="badge badge-error">Sem estoque</span>';
  if (produto.estoque_atual <= produto.estoque_minimo) return '<span class="badge badge-warning">Estoque baixo</span>';
  return '';
}

function renderTabela(produtos) {
  if (!produtos.length) {
    estoqueBody.innerHTML = '<tr><td colspan="6" class="text-center text-textmuted py-8">Nenhum produto cadastrado ainda. Clique em \'+ Novo Produto\' para começar.</td></tr>';
    return;
  }
  estoqueBody.innerHTML = produtos.map((p) => `
    <tr class="${linhaClasses(p)}">
      <td data-label="Nome"><span class="font-medium">${p.nome}</span> ${badgeEstoque(p)}</td>
      <td data-label="Categoria">${p.categoria || '—'}</td>
      <td data-label="Estoque atual" class="text-corpo-forte">${p.estoque_atual ?? 0}</td>
      <td data-label="Estoque mínimo">${p.estoque_minimo ?? '—'}</td>
      <td data-label="Preço de venda">${formatarMoeda(p.preco_venda)}</td>
      <td data-label="Ações">
        <div class="flex gap-2">
          <a href="produto.html?id=${p.id}" class="btn-secondary !h-9 !px-3 text-legenda inline-flex items-center">Editar</a>
          <button type="button" class="btn-secondary !h-9 !px-3 text-legenda btn-abrir-mov" data-id="${p.id}" data-nome="${p.nome}">Entrada/Saída</button>
        </div>
      </td>
    </tr>`).join('');

  estoqueBody.querySelectorAll('.btn-abrir-mov').forEach((btn) => {
    btn.addEventListener('click', () => abrirModalMovimentacao(btn.dataset.id, btn.dataset.nome));
  });
}

async function carregarProdutos() {
  const filtros = {};
  // O backend (GET /produtos) não aceita filtro por texto "q" nem por "categoria"
  // atualmente — apenas apenas_estoque_baixo. Filtragem por busca/categoria é
  // aplicada no cliente logo abaixo, sobre o resultado já carregado.
  if (filtroEstoqueBaixo.checked) filtros.apenas_estoque_baixo = 'true';

  try {
    const produtos = await listarEstoque(filtros);
    produtosCache = produtos || [];
    renderTabela(filtrarLocalmente(produtosCache));
    preencherCategorias(produtosCache);
  } catch (erro) {
    estoqueBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-8">${erro.message}</td></tr>`;
  }
}

function filtrarLocalmente(produtos) {
  const termo = filtroBusca.value.trim().toLowerCase();
  const categoria = filtroCategoria.value;
  return produtos.filter((p) => {
    const bateTermo = !termo || p.nome.toLowerCase().includes(termo);
    const bateCategoria = !categoria || p.categoria === categoria;
    return bateTermo && bateCategoria;
  });
}

function preencherCategorias(produtos) {
  if (filtroCategoria.dataset.preenchido) return;
  const categorias = [...new Set(produtos.map((p) => p.categoria).filter(Boolean))];
  categorias.forEach((cat) => {
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = cat;
    filtroCategoria.appendChild(opt);
  });
  if (categorias.length) filtroCategoria.dataset.preenchido = 'true';
}

const buscarComDebounce = debounce(carregarProdutos, 300);
filtroBusca.addEventListener('input', buscarComDebounce);
filtroCategoria.addEventListener('change', carregarProdutos);
filtroEstoqueBaixo.addEventListener('change', carregarProdutos);

/* ---------- Modal de movimentação rápida ---------- */

function abrirModalMovimentacao(id, nome) {
  produtoEmMovimentacao = id;
  movProdutoNomeEl.textContent = `Produto: ${nome}`;
  formMovimentacao.reset();
  movErroEl.classList.add('hidden');
  modalMovimentacao.classList.remove('hidden');
}

function fecharModalMovimentacao() {
  modalMovimentacao.classList.add('hidden');
  produtoEmMovimentacao = null;
}

btnCancelarMovimentacao.addEventListener('click', fecharModalMovimentacao);

formMovimentacao.addEventListener('submit', async (e) => {
  e.preventDefault();
  movErroEl.classList.add('hidden');

  const tipo = formMovimentacao.querySelector('input[name="tipo-mov"]:checked').value;
  const quantidade = parseInt(document.getElementById('mov-quantidade').value, 10);
  const motivo = document.getElementById('mov-motivo').value;
  const observacao = document.getElementById('mov-observacao').value;

  if (!quantidade || quantidade < 1) {
    movErroEl.textContent = 'Preencha este campo para continuar.';
    movErroEl.classList.remove('hidden');
    return;
  }

  try {
    await registrarMovimentacaoEstoque(produtoEmMovimentacao, { tipo, quantidade, motivo, observacao });
    showToast('Entrada registrada com sucesso');
    fecharModalMovimentacao();
    carregarProdutos();
  } catch (erro) {
    movErroEl.textContent = erro.message;
    movErroEl.classList.remove('hidden');
  }
});

carregarProdutos();
