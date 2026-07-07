/* global Chart */
import { obterIndicadores, obterFaturamentoSerie, obterProdutosMaisVendidos } from './api.js';
import { formatarMoeda, formatarData, showToast } from './utils.js';

const botoesPeriodo = document.querySelectorAll('#filtro-periodo button');
let periodoAtivo = 'hoje';
let grafico = null;

function marcarBotaoAtivo() {
  botoesPeriodo.forEach((btn) => {
    btn.classList.toggle('!bg-primary', btn.dataset.periodo === periodoAtivo);
    btn.classList.toggle('!text-white', btn.dataset.periodo === periodoAtivo);
  });
}

botoesPeriodo.forEach((btn) => {
  btn.addEventListener('click', () => {
    if (btn.dataset.periodo === 'personalizado') {
      showToast('Filtro personalizado ainda não disponível nesta versão.', 'aviso');
      return;
    }
    periodoAtivo = btn.dataset.periodo;
    marcarBotaoAtivo();
    carregarTudo();
  });
});

async function carregarIndicadores() {
  try {
    const dados = await obterIndicadores(periodoAtivo);
    document.getElementById('ind-faturamento').textContent = formatarMoeda(dados.faturamento);
    document.getElementById('ind-lucro').textContent = formatarMoeda(dados.lucro_estimado);
    document.getElementById('ind-ticket').textContent = formatarMoeda(dados.ticket_medio);
    document.getElementById('ind-vendas').textContent = dados.numero_vendas ?? 0;
  } catch (erro) {
    showToast(erro.message, 'erro');
  }
}

async function carregarGrafico() {
  try {
    const serie = await obterFaturamentoSerie(periodoAtivo);
    const ctx = document.getElementById('grafico-faturamento');
    const labels = (serie || []).map((p) => formatarData(p.dia));
    const valores = (serie || []).map((p) => p.faturamento);

    if (grafico) grafico.destroy();
    grafico = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Faturamento (R$)',
          data: valores,
          borderColor: '#0F766E',
          backgroundColor: 'rgba(15, 118, 110, 0.15)',
          fill: true,
          tension: 0.25,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    });
  } catch (erro) {
    showToast(erro.message, 'erro');
  }
}

async function carregarRanking() {
  const corpo = document.getElementById('ranking-body');
  try {
    const ranking = await obterProdutosMaisVendidos(periodoAtivo);
    if (!ranking || !ranking.length) {
      corpo.innerHTML = '<tr><td colspan="3" class="text-center text-textmuted py-8">Nenhuma venda registrada neste período.</td></tr>';
      return;
    }
    corpo.innerHTML = ranking.map((p, i) => `
      <tr>
        <td class="font-medium">${i + 1}. ${p.produto_nome}</td>
        <td>${p.quantidade_vendida}</td>
        <td class="text-corpo-forte">${formatarMoeda(p.faturamento_gerado)}</td>
      </tr>`).join('');
  } catch (erro) {
    corpo.innerHTML = `<tr><td colspan="3" class="text-center text-danger py-8">${erro.message}</td></tr>`;
  }
}

function carregarTudo() {
  carregarIndicadores();
  carregarGrafico();
  carregarRanking();
}

marcarBotaoAtivo();
carregarTudo();
