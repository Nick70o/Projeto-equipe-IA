import { listarLotes, darBaixaLote } from './api.js';
import { formatarData, diasRestantes, showToast } from './utils.js';

const lotesBody = document.getElementById('lotes-body');
const cardsFiltro = document.querySelectorAll('.card-filtro');

let filtroAtivo = null;
let lotesCache = [];

function classificar(dias) {
  if (dias < 0) return 'vencido';
  if (dias <= 30) return '30';
  if (dias <= 90) return '90';
  return null;
}

function atualizarContadores(lotes) {
  const contagens = { vencido: 0, 30: 0, 90: 0 };
  lotes.forEach((lote) => {
    const dias = diasRestantes(lote.data_validade);
    const classe = classificar(dias);
    if (classe) contagens[classe] += 1;
  });
  document.getElementById('contagem-vencidos').textContent = contagens.vencido;
  document.getElementById('contagem-30').textContent = contagens['30'];
  document.getElementById('contagem-90').textContent = contagens['90'];
}

function linhaClasse(dias) {
  if (dias < 0) return 'linha-critica';
  if (dias <= 30) return 'linha-alerta';
  return '';
}

function badgeDias(dias) {
  if (dias < 0) return `<span class="badge badge-error">Vencido há ${Math.abs(dias)} dias</span>`;
  return `<span class="badge badge-warning">Vence em ${dias} dias</span>`;
}

function renderTabela(lotes) {
  let listaFiltrada = lotes;
  if (filtroAtivo) {
    listaFiltrada = lotes.filter((l) => classificar(diasRestantes(l.data_validade)) === filtroAtivo);
  }

  listaFiltrada = [...listaFiltrada].sort((a, b) => new Date(a.data_validade) - new Date(b.data_validade));

  if (!listaFiltrada.length) {
    lotesBody.innerHTML = '<tr><td colspan="6" class="text-center text-textmuted py-8">Nenhum lote encontrado para este filtro.</td></tr>';
    return;
  }

  lotesBody.innerHTML = listaFiltrada.map((lote) => {
    const dias = diasRestantes(lote.data_validade);
    return `
    <tr class="${linhaClasse(dias)}">
      <td data-label="Produto" class="font-medium">${lote.produto_nome}</td>
      <td data-label="Lote">${lote.numero_lote || lote.id}</td>
      <td data-label="Quantidade">${lote.quantidade}</td>
      <td data-label="Data de validade">${formatarData(lote.data_validade)}</td>
      <td data-label="Dias restantes">${badgeDias(dias)}</td>
      <td data-label="Ação">
        <button type="button" class="btn-secondary !h-9 !px-3 text-legenda btn-baixa" data-id="${lote.id}">Dar baixa (descarte)</button>
      </td>
    </tr>`;
  }).join('');

  lotesBody.querySelectorAll('.btn-baixa').forEach((btn) => {
    btn.addEventListener('click', () => confirmarBaixa(btn.dataset.id));
  });
}

async function confirmarBaixa(idLote) {
  if (!window.confirm('Confirma o descarte deste lote?')) return;
  try {
    await darBaixaLote(idLote);
    showToast('Baixa registrada com sucesso');
    await carregarLotes();
  } catch (erro) {
    showToast(erro.message, 'erro');
  }
}

cardsFiltro.forEach((card) => {
  card.addEventListener('click', () => {
    const filtro = card.dataset.filtro;
    filtroAtivo = filtroAtivo === filtro ? null : filtro;
    cardsFiltro.forEach((c) => c.classList.toggle('ring-2', c === card && filtroAtivo));
    renderTabela(lotesCache);
  });
});

async function carregarLotes() {
  try {
    const lotes = await listarLotes();
    lotesCache = lotes || [];
    atualizarContadores(lotesCache);
    renderTabela(lotesCache);
  } catch (erro) {
    lotesBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-8">${erro.message}</td></tr>`;
  }
}

carregarLotes();
