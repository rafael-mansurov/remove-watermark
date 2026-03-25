(() => {
  const LOADER_HTML = `
    <svg width="100" height="100" viewBox="0 0 100 100" aria-hidden="true">
      <defs>
        <mask id="webpLoaderClip">
          <polygon points="0,0 100,0 100,100 0,100" fill="black"/>
          <polygon points="25,25 75,25 50,75" fill="white"/>
          <polygon points="50,25 75,75 25,75" fill="white"/>
          <polygon points="35,35 65,35 50,65" fill="white"/>
          <polygon points="35,35 65,35 50,65" fill="white"/>
          <polygon points="35,35 65,35 50,65" fill="white"/>
          <polygon points="35,35 65,35 50,65" fill="white"/>
        </mask>
      </defs>
    </svg>
    <div class="webp-loader-box"></div>
  `;

  function buildWebpLoader() {
    const el = document.createElement('div');
    el.className = 'webp-loader';
    el.setAttribute('aria-hidden', 'true');
    el.innerHTML = LOADER_HTML;
    return el;
  }

  function init() {
    document.querySelectorAll('[data-webp-loader]').forEach(placeholder => {
      placeholder.replaceWith(buildWebpLoader());
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.buildWebpLoader = buildWebpLoader;
})();
