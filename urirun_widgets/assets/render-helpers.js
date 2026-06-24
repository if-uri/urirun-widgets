// Author: Tom Sapletta · https://tom.sapletta.com
// Part of the ifURI solution.
//
// Shared helpers for the chat-stream widgets. These are extracted VERBATIM from the host
// dashboard so the widget views render identically whether they run inside chatStreamList in
// chat-main or standalone — the repo is now the canonical home of these views. Every widget
// module imports from here.

// HTML-escape any value for safe interpolation into a template string (XSS guard).
export function esc(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Coerce a value to a display string (null/undefined -> '').
export function text(value) {
  if (value == null) return '';
  if (typeof value === 'object') {
    try { return JSON.stringify(value); } catch (_e) { return String(value); }
  }
  return String(value);
}

// Last path segment of a path or URI.
export function basename(path) {
  const p = text(path);
  if (!p) return '';
  return p.split(/[\\/]/).filter(Boolean).pop() || p;
}

export function streamStatusClass(status) {
  if (status === 'accepted') return 'up';
  if (status === 'rejected' || status === 'failed') return 'down';
  return 'running';
}

export function streamDocLabel(candidate) {
  const doc = candidate && candidate.detectedDocument ? candidate.detectedDocument : {};
  const parts = [doc.type, doc.date, doc.contractor || doc.supplier || doc.category, doc.amount].filter(Boolean);
  return parts.join(' · ') || 'document candidate';
}

export function renderStreamFrame(candidate) {
  const quality = candidate && candidate.quality ? candidate.quality : {};
  const score = Number(quality.score || 0).toFixed(1);
  const preview = candidate && candidate.previewUrl
    ? `<img src="${esc(candidate.previewUrl)}" alt="${esc(streamDocLabel(candidate))}" loading="lazy">`
    : '';
  return `<div class="stream-frame">
    ${preview}
    <div class="mono">#${esc(candidate && candidate.frameIndex || '')} · ${score}</div>
    <div class="subtle">${esc(streamDocLabel(candidate))}</div>
  </div>`;
}

export function renderScannerArtifactFrame(item) {
  const label = [item.type, item.date, item.contractor || item.supplier || item.category, item.amount].filter(Boolean).join(' · ')
    || item.label || basename(item.path || item.uri || '');
  const preview = item.previewUrl
    ? `<img src="${esc(item.previewUrl)}" alt="${esc(label)}" loading="lazy">`
    : '';
  const href = item.filePreviewUrl || item.previewUrl || '';
  return `<div class="stream-frame">
    ${preview}
    <div class="mono">${esc(item.kind || 'artifact')}</div>
    <div class="subtle">${esc(label)}</div>
    ${href ? `<a href="${esc(href)}" target="_blank" rel="noreferrer">open</a>` : ''}
  </div>`;
}

// The card shell every data-driven service view shares: head (title + status pill), meta row,
// the widget-specific body, and a collapsible URI/JSON dump.
export function renderServiceViewShell(view, body) {
  return `<div class="stream-card">
    <div class="stream-head">
      <strong>${esc(view.title || view.id || 'service view')}</strong>
      <span class="pill ${streamStatusClass(view.status || 'running')}">${esc(view.status || view.kind || 'live')}</span>
    </div>
    <div class="stream-meta">
      <span class="subtle">${esc(view.target || view.serviceId || '')}</span>
      <span class="subtle">${esc(view.updatedAt || '')}</span>
    </div>
    ${body}
    <details><summary>URI / JSON</summary><pre>${esc(JSON.stringify(view, null, 2))}</pre></details>
  </div>`;
}
