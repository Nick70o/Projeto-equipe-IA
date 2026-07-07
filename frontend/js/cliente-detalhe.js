import { obterCliente, listarHistoricoCompras, listarHistoricoPagamentos, registrarPagamentoFiado } from './api.js';
import { formatarMoeda, formatarData, showToast } from './utils.js';

const params = new URLSearchParams(window.location.search);
const clienteId = params.get('id');

const nomeEl = document.getElementById('cliente-nome');
const contatoEl = document.getElementById('cliente-contato');
const saldoEl = document.getElementById('cliente-saldo');
const comprasBody = document.getElementById('historico-compras-body');
const pagamentosBody = document.getElementById('historico-pagamentos-body');

const btnRegistrarPagamento = document.getElementById('btn-registrar-pagamento');
const modalPagamento = document.getElementById('modal-pagamento');
const formPagamento = document.getElementById('form-pagamento');
const btnCancelarPagamento = document.getElementById('btn-cancelar-pagamento');
const pgErro = document.getElementById('pg-erro');

async function carregarFicha() {
  if (!clienteId) {
    nomeEl.textContent = 'Cliente não encontrado';
    return;
  }
  try {
    const cliente = await obterCliente(clienteId);
    nomeEl.textContent = cliente.nome;
    contatoEl.textContent = [cliente.telefone, cliente.endereco].filter(Boolean).join(' · ') || 'Sem dados de contato adicionais.';
    saldoEl.textContent = `Saldo devedor: ${formatarMoeda(cliente.saldo_devedor)}`;
    saldoEl.classList.toggle('text-danger', (cliente.saldo_devedor || 0) > 0);
    saldoEl.classList.toggle('text-primary', !(cliente.saldo_devedor > 0));
  } catch (erro) {
    showToast(erro.message, 'erro');
  }

  try {
    const compras = await listarHistoricoCompras(clienteId);
    renderCompras(compras || []);
  } catch (erro) {
    comprasBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-8">${erro.message}</td></tr>`;
  }

  try {
    const pagamentos = await listarHistoricoPagamentos(clienteId);
    renderPagamentos(pagamentos || []);
  } catch (erro) {
    pagamentosBody.innerHTML = `<tr><td colspan="3" class="text-center text-danger py-8">${erro.message}</td></tr>`;
  }
}

function renderCompras(compras) {
  if (!compras.length) {
    comprasBody.innerHTML = '<tr><td colspan="4" class="text-center text-textmuted py-8">Nenhuma compra registrada ainda.</td></tr>';
    return;
  }
  comprasBody.innerHTML = compras.map((v) => `
    <tr>
      <td data-label="Data">${formatarData(v.data)}</td>
      <td data-label="Itens">${v.quantidade_itens ?? v.itens?.length ?? '—'}</td>
      <td data-label="Valor" class="text-corpo-forte">${formatarMoeda(v.total)}</td>
      <td data-label="Forma de pagamento">${v.forma_pagamento || '—'}</td>
    </tr>`).join('');
}

function renderPagamentos(pagamentos) {
  if (!pagamentos.length) {
    pagamentosBody.innerHTML = '<tr><td colspan="2" class="text-center text-textmuted py-8">Nenhum pagamento registrado ainda.</td></tr>';
    return;
  }
  pagamentosBody.innerHTML = pagamentos.map((p) => `
    <tr>
      <td data-label="Data">${formatarData(p.data)}</td>
      <td data-label="Valor pago" class="text-corpo-forte">${formatarMoeda(p.valor)}</td>
    </tr>`).join('');
}

btnRegistrarPagamento.addEventListener('click', () => {
  formPagamento.reset();
  pgErro.classList.add('hidden');
  modalPagamento.classList.remove('hidden');
});
btnCancelarPagamento.addEventListener('click', () => modalPagamento.classList.add('hidden'));

formPagamento.addEventListener('submit', async (e) => {
  e.preventDefault();
  pgErro.classList.add('hidden');
  const valor = parseFloat(document.getElementById('pg-valor').value);
  if (!valor || valor <= 0) {
    pgErro.textContent = 'Preencha este campo para continuar.';
    pgErro.classList.remove('hidden');
    return;
  }
  try {
    // O schema PagamentoFiadoCreate do backend só aceita "valor" — o campo
    // "observacao" não existe e seria descartado silenciosamente pela API.
    await registrarPagamentoFiado(clienteId, { valor });
    showToast('Pagamento registrado com sucesso');
    modalPagamento.classList.add('hidden');
    carregarFicha();
  } catch (erro) {
    pgErro.textContent = erro.message;
    pgErro.classList.remove('hidden');
  }
});

carregarFicha();
