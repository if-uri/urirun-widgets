// video widget — a video/stream player. view.view === 'video'.
// data.url | data.src | data.streamUrl.
import { esc, renderServiceViewShell } from '../render-helpers.js';

export function renderVideoServiceView(view) {
  const data = view.data || {};
  const url = data.url || data.src || data.streamUrl;
  const body = url
    ? `<video class="service-media" src="${esc(url)}" controls muted playsinline></video>`
    : `<div class="subtle">no video stream</div>`;
  return renderServiceViewShell(view, body);
}
