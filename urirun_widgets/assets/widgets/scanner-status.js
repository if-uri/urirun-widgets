// scanner-status widget — phone-scanner service health + recent artifacts.
// view.view === 'scanner-status'.
import { esc, renderScannerArtifactFrame, renderServiceViewShell } from '../render-helpers.js';

export function renderScannerStatusServiceView(view) {
  const data = view.data || {};
  const service = data.service || {};
  const camera = data.cameraStatus || {};
  const recent = Array.isArray(data.recentArtifacts) ? data.recentArtifacts : [];
  const ready = camera.ready ? 'ready' : (camera.ok === false ? 'error' : 'not ready');
  const track = camera.track || {};
  const body = `<div class="service-graph">
      <div class="item">
        <strong>service</strong>
        <div><span class="pill ${service.reachable ? 'up' : 'down'}">${esc(service.status || 'unknown')}</span></div>
        <div class="mono">${esc(service.url || '')}</div>
      </div>
      <div class="item">
        <strong>browser camera</strong>
        <div><span class="pill ${camera.ready ? 'up' : 'down'}">${esc(ready)}</span></div>
        <div class="subtle">${esc(camera.width || 0)}x${esc(camera.height || 0)} · ${esc(track.readyState || '')}</div>
        <div class="mono">${esc(track.label || camera.uri || '')}</div>
        ${camera.error ? `<div class="subtle">${esc(camera.error)}</div>` : ''}
      </div>
    </div>
    ${recent.length ? `<div class="stream-frames">${recent.map(renderScannerArtifactFrame).join('')}</div>` : '<div class="subtle">No scanner artifacts yet</div>'}`;
  return renderServiceViewShell(view, body);
}
