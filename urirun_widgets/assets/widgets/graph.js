// graph widget — nodes + edges. view.view === 'graph'.
// data.nodes: [{id|name}]; data.edges: [{from|source, to|target}].
import { esc, renderServiceViewShell } from '../render-helpers.js';

export function renderGraphServiceView(view) {
  const data = view.data || {};
  const nodes = Array.isArray(data.nodes) ? data.nodes : [];
  const edges = Array.isArray(data.edges) ? data.edges : [];
  const body = `<div class="service-graph">
    <div class="item"><strong>nodes</strong>${nodes.map((node) => `<div class="mono">${esc(node.id || node.name || JSON.stringify(node))}</div>`).join('') || '<div class="subtle">none</div>'}</div>
    <div class="item"><strong>edges</strong>${edges.map((edge) => `<div class="mono">${esc(edge.from || edge.source || '')} -> ${esc(edge.to || edge.target || '')}</div>`).join('') || '<div class="subtle">none</div>'}</div>
  </div>`;
  return renderServiceViewShell(view, body);
}
