(() => {
  function renderLucideIcons() {
    if (!window.lucide || typeof window.lucide.createIcons !== 'function') return;
    window.lucide.createIcons();
  }

  function upgradeCommandPromptIcons() {
    const prompts = document.querySelectorAll('.cmd-prompt');
    prompts.forEach((el) => {
      if (!el) return;
      const txt = (el.textContent || '').trim();
      if (txt !== '$') return;
      el.innerHTML = '<i data-lucide="terminal" style="width:13px;height:13px;stroke-width:2" aria-hidden="true"></i>';
    });
    renderLucideIcons();
  }

  function initAnimatedDetails() {
    const detailsBlocks = Array.from(document.querySelectorAll('details'));
    detailsBlocks.forEach((detailsEl) => {
      if (detailsEl.dataset.detailsAnimated === '1') return;
      const summary = detailsEl.querySelector('summary');
      const body = detailsEl.querySelector('.details-body');
      if (!summary || !body) return;
      detailsEl.dataset.detailsAnimated = '1';

      let animating = false;
      const duration = 280;

      summary.addEventListener('click', (e) => {
        e.preventDefault();
        if (animating) return;
        animating = true;

        if (!detailsEl.open) {
          detailsEl.open = true;
          const fullHeight = body.scrollHeight;
          body.style.overflow = 'hidden';
          body.style.maxHeight = '0px';
          body.style.opacity = '0';
          body.style.transform = 'translateY(-8px)';

          requestAnimationFrame(() => {
            body.style.transition = 'max-height ' + duration + 'ms ease, opacity ' + duration + 'ms ease, transform ' + duration + 'ms ease';
            body.style.maxHeight = fullHeight + 'px';
            body.style.opacity = '1';
            body.style.transform = 'translateY(0)';
          });

          setTimeout(() => {
            body.style.transition = '';
            body.style.maxHeight = '';
            body.style.overflow = '';
            body.style.opacity = '';
            body.style.transform = '';
            animating = false;
          }, duration + 40);
          return;
        }

        const fullHeight = body.scrollHeight;
        body.style.overflow = 'hidden';
        body.style.maxHeight = fullHeight + 'px';
        body.style.opacity = '1';
        body.style.transform = 'translateY(0)';

        requestAnimationFrame(() => {
          body.style.transition = 'max-height ' + duration + 'ms ease, opacity ' + duration + 'ms ease, transform ' + duration + 'ms ease';
          body.style.maxHeight = '0px';
          body.style.opacity = '0';
          body.style.transform = 'translateY(-8px)';
        });

        setTimeout(() => {
          body.style.transition = '';
          body.style.maxHeight = '';
          body.style.overflow = '';
          body.style.opacity = '';
          body.style.transform = '';
          requestAnimationFrame(() => {
            detailsEl.open = false;
          });
          animating = false;
        }, duration + 40);
      });
    });
  }

  window.copyCmd = function copyCmd(btn, text) {
    const prev = btn.textContent;
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = 'Скопировано';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.textContent = prev;
        btn.classList.remove('copied');
      }, 1800);
    });
  };

  function initSharedInstructionsUi() {
    upgradeCommandPromptIcons();
    initAnimatedDetails();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSharedInstructionsUi, { once: true });
  } else {
    initSharedInstructionsUi();
  }
})();
