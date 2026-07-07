import { listarClientes, criarCliente } from './api.js';
import { formatarMoeda, mascararTelefone, debounce, showToast } from './utils.js';

const clientesBody = document.getElementById('clientes-body');
const buscaCliente = document.getElementById('busca-cliente');

const modalNovoCliente = document.getElementById('modal-novo-cliente');
const btnNovoCliente = document.getElementById('btn-novo-cliente');
const btnCancelarNovoCliente = document.getElementById('btn-cancelar-novo-cliente');
const formNovoCliente = document.getElementById('form-novo-cliente');
const telefoneInput = document.getElementById('nc-telefone');
const ncErro = document.getElementById('nc-erro');

telefoneInput.addEventListener('input', () => {
  telefoneInput.value = mascararTelefone(telefoneInput.value);
});

function renderTabela(clientes) {
  if (!clientes.length) {
    clientesBody.innerHTML = '<tr><td colspan="4" class="text-center text-textmuted py-8">Nenhum cliente cadastrado ainda.</td></tr>';
    return;
  }
  clientesBody.innerHTML = clientes.map((c) => `
    <tr>
      <td data-label="Nome" class="font-medium">${c.nome}</td>
      <td data-label="Telefone">${c.telefone || '—'}</td>
      <td data-label="Saldo devedor" class="${c.saldo_devedor > 0 ? 'text-danger text-corpo-forte' : ''}">${formatarMoeda(c.saldo_devedor)}</td>
      <td data-label="Ações"><a href="cliente-detalhe.html?id=${c.id}" class="btn-secondary !h-9 !px-3 text-legenda inline-flex items-center">Ver ficha</a></td>
    </tr>`).join('');
}

async function carregarClientes() {
  try {
    const clientes = await listarClientes(buscaCliente.value.trim());
    renderTabela(clientes || []);
  } catch (erro) {
    clientesBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-8">${erro.message}</td></tr>`;
  }
}

buscaCliente.addEventListener('input', debounce(carregarClientes, 300));

btnNovoCliente.addEventListener('click', () => {
  formNovoCliente.reset();
  ncErro.classList.add('hidden');
  modalNovoCliente.classList.remove('hidden');
});
btnCancelarNovoCliente.addEventListener('click', () => modalNovoCliente.classList.add('hidden'));

formNovoCliente.addEventListener('submit', async (e) => {
  e.preventDefault();
  ncErro.classList.add('hidden');
  const nome = document.getElementById('nc-nome').value.trim();
  if (!nome) {
    ncErro.textContent = 'Preencha este campo para continuar.';
    ncErro.classList.remove('hidden');
    return;
  }
  try {
    await criarCliente({
      nome,
      telefone: telefoneInput.value.trim() || null,
      endereco: document.getElementById('nc-endereco').value.trim() || null,
    });
    showToast('Cliente cadastrado com sucesso');
    modalNovoCliente.classList.add('hidden');
    carregarClientes();
  } catch (erro) {
    ncErro.textContent = erro.message;
    ncErro.classList.remove('hidden');
  }
});

carregarClientes();
