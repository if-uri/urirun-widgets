// scanner-status widget — phone-scanner service health + recent artifacts.
// view.view === 'scanner-status'.
import { esc, renderScannerArtifactFrame, renderServiceViewShell } from '../render-helpers.js';

function _renderCameraPanel(camera) {
  const track = camera.track || {};
  const ready = camera.ready ? 'ready' : (camera.ok === false ? 'error' : 'not ready');
  const pill = camera.ready ? 'up' : 'down';
  const label = track.label || camera.uri || '';
  const dims = `${esc(camera.width || 0)}x${esc(camera.height || 0)} · ${esc(track.readyState || '')}`;
  const err = camera.error ? `<div class="subtle">${esc(camera.error)}</div>` : '';
  return `<div class="item">
    <strong>browser camera</strong>
    <div><span class="pill ${pill}">${esc(ready)}</span></div>
    <div class="subtle">${dims}</div>
    <div class="mono">${esc(label)}</div>
    ${err}
  </div>`;
}

export function renderScannerStatusServiceView(view) {
  const data = view.data || {};
  const service = data.service || {};
  const camera = data.cameraStatus || {};
  const recent = Array.isArray(data.recentArtifacts) ? data.recentArtifacts : [];
  const servicePill = service.reachable ? 'up' : 'down';
  const framesHtml = recent.length
    ? `<div class="stream-frames">${recent.map(renderScannerArtifactFrame).join('')}</div>`
    : '<div class="subtle">No scanner artifacts yet</div>';
  const body = `<div class="service-graph">
      <div class="item">
        <strong>service</strong>
        <div><span class="pill ${servicePill}">${esc(service.status || 'unknown')}</span></div>
        <div class="mono">${esc(service.url || '')}</div>
      </div>
      ${_renderCameraPanel(camera)}
    </div>
    ${framesHtml}`;
  return renderServiceViewShell(view, body);
}
