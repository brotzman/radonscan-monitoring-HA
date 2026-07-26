(() => {
  'use strict';
  const focusMain = () => {
    const main = document.getElementById('mainContent');
    if (main) main.focus({preventScroll:true});
  };
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const modal = document.getElementById('modal');
      if (modal && !modal.classList.contains('hidden')) {
        document.getElementById('modalClose')?.click();
        return;
      }
      document.getElementById('sidebarBackdrop')?.click();
    }
  });
  document.addEventListener('click', event => {
    const nav = event.target.closest?.('[data-view]');
    if (nav && window.matchMedia('(max-width: 860px)').matches) {
      window.setTimeout(focusMain, 0);
    }
  });
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  document.documentElement.dataset.reducedMotion = reduceMotion.matches ? 'true' : 'false';
  reduceMotion.addEventListener?.('change', e => document.documentElement.dataset.reducedMotion = e.matches ? 'true' : 'false');
})();
