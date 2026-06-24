// image widget — one or many images. view.view === 'image' | 'image-list'.
// data.images: array of url|{url|previewUrl|src,label}; or data.url/previewUrl/src for one.
import { esc, renderServiceViewShell } from '../render-helpers.js';

export function renderImageServiceView(view) {
  const data = view.data || {};
  const images = Array.isArray(data.images) ? data.images : [data.url || data.previewUrl || data.src].filter(Boolean);
  const body = images.length
    ? `<div class="stream-frames">${images.map((image) => {
        const item = typeof image === 'string' ? { url: image } : image;
        return `<div class="stream-frame">
          <img src="${esc(item.url || item.previewUrl || item.src || '')}" alt="${esc(item.label || view.title || 'service image')}" loading="lazy">
          ${item.label ? `<div class="subtle">${esc(item.label)}</div>` : ''}
        </div>`;
      }).join('')}</div>`
    : `<div class="subtle">no image</div>`;
  return renderServiceViewShell(view, body);
}
