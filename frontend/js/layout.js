/**
 * Monta o menu lateral fixo, o cabeçalho superior e a barra inferior (mobile)
 * em todas as telas, a partir do atributo data-page do <body>.
 * Evita duplicar o HTML da navegação em cada página.
 */

const NAV_ITEMS = [
  { id: 'pdv', href: 'pdv.html', label: 'PDV / Venda', icon: '🧾' },
  { id: 'estoque', href: 'estoque.html', label: 'Estoque', icon: '📦' },
  { id: 'validade', href: 'validade.html', label: 'Validade / Lotes', icon: '⏳' },
  { id: 'clientes', href: 'clientes.html', label: 'Clientes e Fiado', icon: '👥' },
  { id: 'relatorios', href: 'relatorios.html', label: 'Relatórios', icon: '📊' },
];

const NAV_FOOTER_ITEM = { id: 'configuracoes', href: 'configuracoes.html', label: 'Configurações', icon: '⚙️' };

// 4 itens mais usados para a bottom bar (360px), conforme spec seção 6.
const BOTTOM_ITEMS = NAV_ITEMS.slice(0, 4);

function linkClasses(active) {
  return active
    ? 'bg-[--color-primary-light] text-[--color-primary] font-semibold'
    : 'text-[--color-text-muted] hover:bg-[--color-background] hover:text-[--color-text]';
}

function renderSidebar(activePage) {
  const root = document.getElementById('sidebar-root');
  if (!root) return;

  const itemsHtml = NAV_ITEMS.map((item) => `
    <a href="${item.href}"
       class="flex items-center gap-3 rounded-md px-3 py-2.5 text-[15px] transition-colors ${linkClasses(item.id === activePage)}"
       aria-current="${item.id === activePage ? 'page' : 'false'}">
      <span class="text-lg leading-none" aria-hidden="true">${item.icon}</span>
      <span class="nav-label whitespace-nowrap">${item.label}</span>
    </a>`).join('');

  root.innerHTML = `
    <aside id="sidebar" class="hidden md:flex md:flex-col fixed inset-y-0 left-0 z-30 bg-[--color-surface] border-r border-[--color-border] transition-[width] duration-150 w-[72px] xl:w-[220px]">
      <div class="flex items-center gap-2 h-16 px-3 border-b border-[--color-border] shrink-0">
        <span class="text-2xl" aria-hidden="true">💊</span>
        <span class="nav-label font-semibold text-[--color-text] truncate">Farmácia</span>
      </div>
      <nav class="flex-1 flex flex-col gap-2 p-3 overflow-y-auto" aria-label="Navegação principal">
        ${itemsHtml}
      </nav>
      <div class="p-3 border-t border-[--color-border]">
        <a href="${NAV_FOOTER_ITEM.href}"
           class="flex items-center gap-3 rounded-md px-3 py-2.5 text-[15px] transition-colors ${linkClasses(NAV_FOOTER_ITEM.id === activePage)}"
           aria-current="${NAV_FOOTER_ITEM.id === activePage ? 'page' : 'false'}">
          <span class="text-lg leading-none" aria-hidden="true">${NAV_FOOTER_ITEM.icon}</span>
          <span class="nav-label whitespace-nowrap">${NAV_FOOTER_ITEM.label}</span>
        </a>
      </div>
    </aside>`;
}

function renderTopbar() {
  const root = document.getElementById('topbar-root');
  if (!root) return;
  const agora = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date());
  root.innerHTML = `
    <header class="fixed top-0 right-0 left-0 md:left-[72px] xl:left-[220px] z-20 h-16 bg-[--color-surface] border-b border-[--color-border] flex items-center justify-between px-4 md:px-6">
      <div class="flex items-center gap-2 md:hidden">
        <span class="text-xl" aria-hidden="true">💊</span>
        <span class="font-semibold text-[--color-text]">Farmácia</span>
      </div>
      <div class="hidden md:block font-semibold text-[--color-text]">Farmácia Sistema Local</div>
      <div class="flex items-center gap-4 text-sm text-[--color-text-muted]">
        <span class="hidden sm:inline" id="topbar-datahora">${agora}</span>
        <span class="hidden sm:inline">|</span>
        <span class="font-medium text-[--color-text]">Atendente</span>
        <button type="button" class="rounded-md border border-[--color-border] px-3 py-1.5 hover:bg-[--color-background]" aria-label="Sair do sistema">Sair</button>
      </div>
    </header>`;

  const relogio = document.getElementById('topbar-datahora');
  if (relogio) {
    setInterval(() => {
      relogio.textContent = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date());
    }, 30000);
  }
}

function renderBottombar(activePage) {
  const root = document.getElementById('bottombar-root');
  if (!root) return;
  const itemsHtml = BOTTOM_ITEMS.map((item) => `
    <a href="${item.href}" class="flex flex-col items-center justify-center flex-1 py-2 text-xs gap-0.5 ${item.id === activePage ? 'text-[--color-primary] font-semibold' : 'text-[--color-text-muted]'}">
      <span class="text-lg leading-none" aria-hidden="true">${item.icon}</span>
      <span>${item.label.split(' / ')[0].split(' ')[0]}</span>
    </a>`).join('');
  root.innerHTML = `
    <nav class="md:hidden fixed bottom-0 inset-x-0 z-30 bg-[--color-surface] border-t border-[--color-border] flex" aria-label="Navegação inferior">
      ${itemsHtml}
      <a href="${NAV_FOOTER_ITEM.href}" class="flex flex-col items-center justify-center flex-1 py-2 text-xs gap-0.5 ${NAV_FOOTER_ITEM.id === activePage ? 'text-[--color-primary] font-semibold' : 'text-[--color-text-muted]'}">
        <span class="text-lg leading-none" aria-hidden="true">☰</span>
        <span>Mais</span>
      </a>
    </nav>`;
}

export function montarLayout() {
  const page = document.body.dataset.page || '';
  renderSidebar(page);
  renderTopbar();
  renderBottombar(page);
}

document.addEventListener('DOMContentLoaded', montarLayout);
