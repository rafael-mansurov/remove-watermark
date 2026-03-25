(() => {
  const footer = document.getElementById('sharedFooter');
  if (!footer) return;

  const primaryHref = footer.getAttribute('data-primary-href') || '#';
  const primaryLabel = footer.getAttribute('data-primary-label') || 'Главная';

  footer.innerHTML = `
    <a class="btn btn-ghost" href="${primaryHref}">${primaryLabel}</a>
    <a class="btn btn-ghost" href="https://web.tribute.tg/d/HpN" target="_blank" rel="noopener noreferrer">
      <i data-lucide="coffee" style="width:13px;height:13px;stroke-width:2" aria-hidden="true"></i>
      Поддержать
    </a>
    <a class="btn btn-primary" href="https://t.me/mansurov_rafael" target="_blank" rel="noopener noreferrer">
      <svg width="15" height="13" viewBox="0 0 16 14" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path fill-rule="evenodd" clip-rule="evenodd" d="M9.69184 2.00737C8.25888 2.60345 5.39488 3.83705 1.09992 5.70833C0.402477 5.98569 0.0371331 6.25697 0.00387711 6.52225C-0.0523389 6.97065 0.509141 7.14721 1.27376 7.38761C1.27894 7.38924 1.28414 7.39088 1.28934 7.39251C1.38851 7.42371 1.49102 7.45596 1.596 7.49009C2.34824 7.73465 3.36008 8.02073 3.88616 8.03209C4.36336 8.04241 4.89592 7.84569 5.48392 7.44193C9.4968 4.73305 11.5683 3.36393 11.6983 3.33441C11.7901 3.31353 11.9172 3.28737 12.0034 3.36393C12.0895 3.44049 12.081 3.58553 12.0719 3.62441C12.0163 3.86153 9.81232 5.91057 8.67168 6.97097C8.6685 6.97392 8.66534 6.97687 8.66218 6.9798C8.31167 7.3057 8.06345 7.53649 8.01232 7.58961C7.89688 7.70953 7.77912 7.82305 7.666 7.93209C6.9672 8.60577 6.44312 9.11097 7.69504 9.93601C8.29501 10.3314 8.77548 10.6586 9.25451 10.9847L9.2584 10.9874C9.78288 11.3446 10.3061 11.7009 10.983 12.1446C11.1554 12.2576 11.3201 12.375 11.4805 12.4894C12.091 12.9246 12.6394 13.3155 13.3169 13.2532C13.7106 13.217 14.1172 12.8468 14.3237 11.7427C14.8118 9.13353 15.7712 3.48009 15.9929 1.15049C16.0123 0.946331 15.9878 0.685131 15.9682 0.570491C15.9486 0.455851 15.9076 0.292411 15.7586 0.171531C15.5821 0.0282511 15.3095 -0.00190902 15.1877 9.09819e-05C14.6335 0.010011 13.7834 0.305611 9.69184 2.00737Z" fill="currentColor"/></svg>
      Связаться со\u00a0мной
    </a>
  `;

  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
})();
