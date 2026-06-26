// twin widget — reversible-process step snapshot. view.view === 'twin'.
// data.narration: string; data.status: 'applied'|'blocked';
// data.forward: string; data.inverse: string|null; data.reversible: boolean
// data.before, data.after: {fingerprint, stateSig, url}
import { esc, renderServiceViewShell } from '../render-helpers.js';

export function renderTwinServiceView(view) {
  const data = view.data || {};
  const reversible = data.reversible !== false;
  const status = data.status || 'unknown';
  const before = data.before || {};
  const after = data.after || {};

  const narration = data.narration
    ? `<div class="twin-narration${status === 'blocked' ? ' blocked' : ''}">${esc(data.narration)}</div>`
    : '';
  const fwd = data.forward
    ? `<div class="twin-cmd twin-forward"><span class="twin-label">forward:</span> <code>${esc(data.forward)}</code></div>`
    : '';
  const inv = (reversible && data.inverse)
    ? `<div class="twin-cmd twin-inverse"><span class="twin-label">inverse:</span> <code>${esc(data.inverse)}</code></div>`
    : (!reversible
        ? `<div class="twin-cmd twin-blocked"><span class="twin-label">inverse:</span> <span class="twin-none">NONE — irreversible</span></div>`
        : '');

  const stateCard = (label, s) => {
    if (!s || !s.fingerprint) return '';
    return `<div class="twin-state">
      <span class="twin-label">${esc(label)}</span>
      <span class="twin-fp">${esc(s.fingerprint)}</span>
      ${s.url ? `<span class="twin-url">${esc(s.url)}</span>` : ''}
    </div>`;
  };

  const states = (before.fingerprint || after.fingerprint)
    ? `<div class="twin-states">${stateCard('before', before)}<div class="twin-state-arrow">&#x2192;</div>${stateCard('after', after)}</div>`
    : '';

  const body = `<div class="twin-panel">${narration}${fwd}${inv}${states}</div>`;
  return renderServiceViewShell(view, body);
}
