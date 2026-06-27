// widget-card widget — wraps a service + its live view into a dashboard card, with links to the
// standalone HTML/SVG widget pages. Uses renderServiceView from the dispatcher to draw the body.
import { esc } from '../render-helpers.js';
import { renderServiceView, renderIframeServiceView } from '../render.js';

export function serviceWidgetLinks(service, view) {
  const target = service.id || view.target || view.serviceId || '';
  const links = [];
  if (target) {
    links.push(`<a href="/services/view?target=${encodeURIComponent(target)}" target="_blank" rel="noreferrer">HTML widget</a>`);
    links.push(`<a href="/services/view.svg?target=${encodeURIComponent(target)}" target="_blank" rel="noreferrer">SVG</a>`);
  }
  if (service.url) links.push(`<a href="${esc(service.url)}" target="_blank" rel="noreferrer">open service</a>`);
  return links.length ? `<div class="artifact-actions">${links.join('')}</div>` : '';
}

function _cardPreview(service, target, status, safeView, view) {
  if (view) return renderServiceView(view);
  if (service.url) {
    const fallback = { title: `${service.name || target || 'service'} page`, target, status, view: 'page', data: { url: service.url } };
    return renderIframeServiceView(fallback);
  }
  return `<div class="stream-card"><div class="subtle">No live view published yet for this service.</div></div>`;
}

export function renderWidgetCard(service, view) {
  const safeView = view || {};
  const status = service.status || safeView.status || 'live';
  const target = service.id || safeView.target || safeView.serviceId || '';
  const title = service.label || service.name || safeView.title || target || 'service';
  const subtitle = service.url || service.bindUrl || safeView.updatedAt || '';
  const statusCls = (status === 'running' || status === 'up' || status === 'live') ? 'up' : 'down';
  const preview = _cardPreview(service, target, status, safeView, view);
  return `<div class="widget-card">
    <div class="stream-head">
      <div>
        <strong>${esc(title)}</strong>
        <div class="mono">${esc(target)}</div>
      </div>
      <span class="pill ${statusCls}">${esc(status)}</span>
    </div>
    <div class="subtle">${esc(subtitle)}</div>
    ${serviceWidgetLinks(service, safeView)}
    <div class="widget-preview">${preview}</div>
  </div>`;
}
