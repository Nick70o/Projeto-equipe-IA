/**
 * Camada de acesso à API (FastAPI).
 * O backend não usa prefixo "/api": os routers são incluídos direto com
 * prefixos como /produtos, /lotes, /clientes, /vendas, /relatorios.
 * Todas as funções retornam Promises e lançam erro em caso de falha de rede/HTTP,
 * para ser tratado pela camada de UI (ex.: showToast de erro).
 */

const API_BASE = 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, config);
  } catch (networkError) {
    throw new Error('Não foi possível salvar. Verifique se o sistema está aberto corretamente e tente novamente.');
  }
  if (!response.ok) {
    let detail = '';
    try {
      const body = await response.json();
      detail = body.detail || body.message || '';
    } catch (_) { /* corpo sem JSON */ }
    throw new Error(detail || `Erro na comunicação com o servidor (HTTP ${response.status}).`);
  }
  if (response.status === 204) return null;
  return response.json();
}

/* ---------- Produtos ---------- */
export const buscarProduto = (termo) => request(`/produtos/buscar?q=${encodeURIComponent(termo)}`);
export const listarEstoque = (filtros = {}) => {
  const params = new URLSearchParams(filtros);
  return request(`/produtos?${params.toString()}`);
};
export const obterProduto = (id) => request(`/produtos/${id}`);
export const criarProduto = (produto) => request('/produtos', { method: 'POST', body: JSON.stringify(produto) });
export const atualizarProduto = (id, produto) => request(`/produtos/${id}`, { method: 'PUT', body: JSON.stringify(produto) });
export const registrarMovimentacaoEstoque = (idProduto, movimentacao) =>
  request(`/produtos/${idProduto}/movimentacoes`, { method: 'POST', body: JSON.stringify(movimentacao) });
export const listarHistoricoMovimentacoes = (idProduto) => request(`/produtos/${idProduto}/movimentacoes`);
export const criarLote = (idProduto, lote) =>
  request(`/produtos/${idProduto}/lotes`, { method: 'POST', body: JSON.stringify(lote) });

/* ---------- Lotes / Validade ---------- */
export const listarLotes = (filtros = {}) => {
  const params = new URLSearchParams(filtros);
  return request(`/lotes?${params.toString()}`);
};
// O backend não tem endpoint dedicado de "baixa/descarte": a remoção do lote
// é feita via DELETE /lotes/{id} (não há suporte a registrar o motivo do descarte).
export const darBaixaLote = (idLote) => request(`/lotes/${idLote}`, { method: 'DELETE' });

/* ---------- Vendas / PDV ---------- */
export const criarVenda = (venda) => request('/vendas', { method: 'POST', body: JSON.stringify(venda) });
export const obterVenda = (id) => request(`/vendas/${id}`);
export const listarVendas = (filtros = {}) => {
  const params = new URLSearchParams(filtros);
  return request(`/vendas?${params.toString()}`);
};

/* ---------- Clientes / Fiado ---------- */
export const listarClientes = (termo = '') => request(`/clientes?q=${encodeURIComponent(termo)}`);
export const obterCliente = (id) => request(`/clientes/${id}`);
export const criarCliente = (cliente) => request('/clientes', { method: 'POST', body: JSON.stringify(cliente) });
export const atualizarCliente = (id, cliente) => request(`/clientes/${id}`, { method: 'PUT', body: JSON.stringify(cliente) });
export const registrarPagamentoFiado = (idCliente, pagamento) =>
  request(`/clientes/${idCliente}/pagamentos`, { method: 'POST', body: JSON.stringify(pagamento) });
export const listarHistoricoCompras = (idCliente) => request(`/vendas?cliente_id=${encodeURIComponent(idCliente)}`);
export const listarHistoricoPagamentos = (idCliente) => request(`/clientes/${idCliente}/pagamentos`);

/* ---------- Configurações ---------- */
export const obterConfiguracoes = () => request('/configuracoes');
export const atualizarConfiguracoes = (config) => request('/configuracoes', { method: 'PUT', body: JSON.stringify(config) });

/* ---------- Vendas / Pix com gateway (Mercado Pago) ---------- */
export const criarCobrancaPix = (payload) => request('/vendas/pix/cobranca', { method: 'POST', body: JSON.stringify(payload) });
export const consultarStatusPix = (idVenda) => request(`/vendas/pix/status/${idVenda}`);

/* ---------- Relatórios ---------- */
export const obterIndicadores = (periodo) => request(`/relatorios/indicadores?periodo=${encodeURIComponent(periodo)}`);
export const obterFaturamentoSerie = (periodo) => request(`/relatorios/faturamento-por-dia?periodo=${encodeURIComponent(periodo)}`);
export const obterProdutosMaisVendidos = (periodo) => request(`/relatorios/produtos-mais-vendidos?periodo=${encodeURIComponent(periodo)}`);
