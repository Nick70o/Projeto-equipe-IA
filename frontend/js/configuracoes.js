import { obterConfiguracoes, atualizarConfiguracoes } from './api.js';
import { showToast } from './utils.js';

const togglePixGateway = document.getElementById('toggle-pix-gateway');

async function carregarConfiguracoes() {
  try {
    const config = await obterConfiguracoes();
    togglePixGateway.setAttribute('aria-checked', String(Boolean(config?.pix_gateway_ativo)));
  } catch (erro) {
    showToast(erro.message, 'erro');
  } finally {
    togglePixGateway.disabled = false;
  }
}

togglePixGateway.addEventListener('click', async () => {
  const ativoAtual = togglePixGateway.getAttribute('aria-checked') === 'true';
  const novoValor = !ativoAtual;

  // Atualização otimista — reverte em caso de erro na API
  togglePixGateway.setAttribute('aria-checked', String(novoValor));
  togglePixGateway.disabled = true;
  try {
    await atualizarConfiguracoes({ pix_gateway_ativo: novoValor });
    showToast(novoValor ? 'Pix com QR Code ativado.' : 'Pix com QR Code desativado.', 'sucesso');
  } catch (erro) {
    togglePixGateway.setAttribute('aria-checked', String(ativoAtual));
    showToast(erro.message, 'erro');
  } finally {
    togglePixGateway.disabled = false;
  }
});

carregarConfiguracoes();
