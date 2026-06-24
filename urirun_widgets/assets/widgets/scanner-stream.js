// scanner-stream widget — the live phone-scanner stream as rendered in chatStreamList.
// view.view === 'scanner-stream'; view.data.streams is an array of stream objects.
import { esc, basename, streamStatusClass, streamDocLabel, renderStreamFrame } from '../render-helpers.js';

export function renderScannerStream(stream, title = 'phone scanner stream') {
  const best = stream.best || {};
  const quality = best.quality || {};
  const document = stream.document || {};
  const status = stream.status || 'running';
  const accepted = status === 'accepted' && document.path;
  const bestScore = Number(quality.score || 0).toFixed(1);
  const frames = stream.candidates || [];
  return `<div class="stream-card">
    <div class="stream-head">
      <strong>${esc(title)}</strong>
      <span class="pill ${streamStatusClass(status)}">${esc(status)}</span>
    </div>
    <div class="stream-meta">
      <span class="subtle">${esc(stream.seriesId || '')}</span>
      <span class="subtle">${esc(stream.updatedAt || '')}</span>
    </div>
    <div><strong>${esc(streamDocLabel(best))}</strong></div>
    <div class="subtle">${esc(stream.count || 0)} frame(s) · best score ${esc(bestScore)}${stream.error ? ` · ${esc(stream.error)}` : ''}</div>
    ${accepted ? `<div><a href="${esc(document.previewUrl || `/api/file?path=${encodeURIComponent(document.path)}`)}" download>${esc(basename(document.path))}</a></div>` : ''}
    ${frames.length ? `<div class="stream-frames">${frames.map(renderStreamFrame).join('')}</div>` : ''}
    <details><summary>URI / JSON</summary><pre>${esc(JSON.stringify(stream, null, 2))}</pre></details>
  </div>`;
}

// A scanner-stream view holds many streams; render each card and concatenate.
export function renderScannerStreamView(view) {
  const streams = view.data && Array.isArray(view.data.streams) ? view.data.streams : [];
  return streams.map((stream) => renderScannerStream(stream, view.title || 'phone scanner stream')).join('');
}
