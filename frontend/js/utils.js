/** Utilitários de formatação e helpers de UI compartilhados entre telas. */

export function formatarMoeda(valor) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor || 0);
}

export function formatarData(dataISO) {
  if (!dataISO) return '—';
  const d = new Date(dataISO);
  if (Number.isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('pt-BR').format(d);
}

export function formatarDataHora(dataISO) {
  if (!dataISO) return '—';
  const d = new Date(dataISO);
  if (Number.isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(d);
}

export function mascararTelefone(valor) {
  const digitos = valor.replace(/\D/g, '').slice(0, 11);
  if (digitos.length <= 10) {
    return digitos
      .replace(/^(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2');
  }
  return digitos
    .replace(/^(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2');
}

export function diasRestantes(dataValidadeISO) {
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const validade = new Date(dataValidadeISO);
  validade.setHours(0, 0, 0, 0);
  return Math.round((validade - hoje) / 86400000);
}

export function debounce(fn, atraso = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), atraso);
  };
}

/** Toast simples de feedback (sucesso/erro), sem dependências. */
export function showToast(mensagem, tipo = 'sucesso') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  const cores = {
    sucesso: 'bg-[--color-success-bg] text-[--color-success] border-[--color-success]',
    erro: 'bg-[--color-error-bg] text-[--color-error] border-[--color-error]',
    aviso: 'bg-[--color-warning-bg] text-[--color-warning] border-[--color-warning]',
  };
  toast.className = `pointer-events-auto border-l-4 ${cores[tipo] || cores.sucesso} rounded-md shadow-md px-4 py-3 text-sm font-medium animate-[fadeIn_.15s_ease-out]`;
  toast.textContent = mensagem;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = 'opacity .3s ease';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}
