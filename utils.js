// Общие функции, которые используются на нескольких страницах.

/** Проверяет, поддерживается ли формат файла (изображение). */
function isSupportedImage(file) {
  const t = (file.type || '').toLowerCase();
  if (t.startsWith('image/jpeg') || t.startsWith('image/png') || t.startsWith('image/webp') || t.startsWith('image/bmp') || t.startsWith('image/gif')) {
    return true;
  }
  if (t === 'image/heic' || t === 'image/heif' || t.includes('heic') || t.includes('heif')) {
    return true;
  }
  const n = (file.name || '').toLowerCase();
  return /\.(jpe?g|png|webp|bmp|gif|heic|heif)$/i.test(n);
}

/** Определяет, является ли файл снимком iPhone (HEIC/HEIF). */
function isHeicLike(file) {
  const t = (file.type || '').toLowerCase();
  if (t === 'image/heic' || t === 'image/heif' || t.includes('heic') || t.includes('heif')) return true;
  const n = (file.name || '').toLowerCase();
  return /\.(heic|heif)$/i.test(n);
}

/** Загружает библиотеку конвертации HEIC один раз, повторные вызовы ждут первого. */
let heic2anyLoadPromise = null;
function ensureHeic2anyLoaded() {
  if (typeof window.heic2any === 'function') return Promise.resolve();
  if (heic2anyLoadPromise) return heic2anyLoadPromise;
  heic2anyLoadPromise = new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = APP_CONFIG.HEIC2ANY_SRC;
    s.async = true;
    s.onload = () => {
      if (typeof window.heic2any === 'function') resolve();
      else {
        heic2anyLoadPromise = null;
        reject(new Error('heic2any'));
      }
    };
    s.onerror = () => {
      heic2anyLoadPromise = null;
      reject(new Error('heic2any network'));
    };
    document.head.appendChild(s);
  });
  return heic2anyLoadPromise;
}

/** Форматирует размер файла: байты → читаемый вид (B / KB / MB). */
function fmtSize(bytes) {
  if (!Number.isFinite(bytes)) return '—';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}
