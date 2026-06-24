// iframe widget — an embedded page. view.view === 'iframe' | 'page' | 'web'.
// data.url | data.src | data.href.
import { esc, renderServiceViewShell } from '../render-helpers.js';

export function renderIframeServiceView(view) {
  const data = view.data || {};
  const url = data.url || data.src || data.href;
  const body = url
    ? `<iframe class="service-frame" src="${esc(url)}" title="${esc(view.title || 'service page')}" loading="lazy"></iframe>`
    : `<div class="subtle">no page url</div>`;
  return renderServiceViewShell(view, body);
}
