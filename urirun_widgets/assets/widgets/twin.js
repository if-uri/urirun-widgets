// twin widget — reversible-process step snapshot. view.view === 'twin'.
// data.narration: string; data.status: 'applied'|'blocked';
// data.forward: string; data.inverse: string|null; data.reversible: boolean
// data.before, data.after: {fingerprint, stateSig, url}
// data.env: {platform, best, controllable, osLevelReliable, strategies, surface}
// data.constraints: [{kind:'blocked'|'missing'|'degraded', what, reason, fix}]
import { esc, renderServiceViewShell } from '../render-helpers.js';

export function renderTwinServiceView(view) {
  const data = view.data || {};
  const reversible = data.reversible !== false;
  const status = data.status || 'unknown';
  const before = data.before || {};
  const after = data.after || {};
  const env = data.env || null;
  const constraints = Array.isArray(data.constraints) ? data.constraints : [];

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

  // env panel — dlaczego planner wybrał tę trasę
  let envPanel = '';
  if (env) {
    const strat = env.strategies || {};
    const stratBadges = Object.entries(strat)
      .map(([k, v]) => `<span class="twin-env-badge${v ? '' : ' off'}">${esc(k)}</span>`)
      .join('');
    const surface = env.surface ? `<span class="twin-env-surface">${esc(env.surface)}</span>` : '';
    const osWarn = env.osLevelReliable === false
      ? `<span class="twin-env-badge off" title="OS-level screen capture zawodny">portal⚠</span>` : '';
    envPanel = `<div class="twin-env">
      <span class="twin-label">env:</span>
      <span class="twin-env-platform">${esc(env.platform || '?')}</span>
      <span class="twin-env-badge best">best:${esc(env.best || '?')}</span>
      ${stratBadges}${osWarn}${surface}
    </div>`;
  }

  // constraints panel — co było niemożliwe i dlaczego
  let constraintsPanel = '';
  if (constraints.length) {
    const items = constraints.map(c => {
      const cls = c.kind === 'blocked' ? 'twin-constraint-blocked'
                : c.kind === 'missing' ? 'twin-constraint-missing'
                : 'twin-constraint-degraded';
      const fix = c.fix ? `<span class="twin-constraint-fix">→ ${esc(c.fix)}</span>` : '';
      return `<div class="twin-constraint ${cls}">
        <span class="twin-constraint-what">${esc(c.what)}</span>
        <span class="twin-constraint-reason">${esc(c.reason)}</span>
        ${fix}
      </div>`;
    }).join('');
    constraintsPanel = `<div class="twin-constraints"><span class="twin-label">ograniczenia:</span>${items}</div>`;
  }

  const body = `<div class="twin-panel">${narration}${fwd}${inv}${states}${envPanel}${constraintsPanel}</div>`;
  return renderServiceViewShell(view, body);
}
