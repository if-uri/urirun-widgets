// generic widget — the fallback for any view whose `view` key has no dedicated renderer.
// Dumps the data as pretty JSON inside the card. Never throws on unknown shapes.
import { esc, streamStatusClass } from '../render-helpers.js';

export function renderGenericServiceView(view) {
  const data = view.data || {};
  return `<div class="stream-card">
    <div class="stream-head">
      <strong>${esc(view.title || view.id || 'service view')}</strong>
      <span class="pill ${streamStatusClass(view.status || 'running')}">${esc(view.status || view.kind || 'live')}</span>
    </div>
    <div class="stream-meta">
      <span class="subtle">${esc(view.target || view.serviceId || '')}</span>
      <span class="subtle">${esc(view.updatedAt || '')}</span>
    </div>
    <details open><summary>service data</summary><pre>${esc(JSON.stringify(data, null, 2))}</pre></details>
  </div>`;
}
