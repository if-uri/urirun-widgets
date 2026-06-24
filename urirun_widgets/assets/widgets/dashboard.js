// dashboard widgets — small data→HTML views from the host dashboard (metrics, task table,
// nodes, routes, contacts). Extracted as PURE functions that return HTML (the host's versions
// wrote straight into the DOM by element id). Pass plain data; selection state is a parameter.
import { esc, text, empty } from '../render-helpers.js';

export function metric(label, value, note) {
  return `<div class="metric"><strong>${esc(text(value) || 0)}</strong><span>${esc(label)}</span><p class="subtle">${esc(text(note))}</p></div>`;
}

export function renderMetrics(summary) {
  const counts = (summary && summary.taskCounts) || {};
  return [
    metric('open tasks', counts.open || 0, 'planfile'),
    metric('running', counts.in_progress || 0, 'in progress'),
    metric('blocked', counts.blocked || 0, 'needs operator'),
    metric('nodes online', (summary && summary.nodesOnline) || 0, `${(summary && summary.nodeCount) || 0} configured`),
    metric('URI processes', (summary && summary.routeCount) || 0, 'mesh routes'),
  ].join('');
}

export function renderTasks(tasks) {
  const rows = Array.isArray(tasks) ? tasks : [];
  return rows.map((ticket) => {
    const exec = ticket.execution || {};
    return `<tr>
      <td class="mono">${esc(ticket.id)}</td>
      <td><strong>${esc(ticket.name)}</strong><div class="subtle">${esc(text(ticket.description).slice(0, 120))}</div></td>
      <td><span class="status ${esc(ticket.status)}">${esc(ticket.status)}</span><div class="subtle">${esc(text(exec.state))}</div></td>
      <td>${esc(text(exec.queue) || 'default')}</td>
      <td>${esc(text(ticket.priority) || 'normal')}</td>
      <td><div class="actions">
        <button data-action="start" data-id="${esc(ticket.id)}">Start</button>
        <button data-action="complete" data-id="${esc(ticket.id)}">Done</button>
        <button class="danger" data-action="block" data-id="${esc(ticket.id)}">Block</button>
      </div></td>
    </tr>`;
  }).join('') || `<tr><td colspan="6">${empty('No tasks')}</td></tr>`;
}

export function renderNodes(nodes) {
  const rows = Array.isArray(nodes) ? nodes : [];
  return rows.map((node) => `<div class="item">
    <div><strong>${esc(node.name)}</strong> <span class="pill ${node.reachable ? 'up' : 'down'}">${node.reachable ? 'up' : 'down'}</span></div>
    <div class="mono">${esc(node.url)}</div>
    <div class="subtle">${(node.routes || []).length} routes${node.error ? ` · ${esc(node.error)}` : ''}</div>
  </div>`).join('') || empty('No nodes configured');
}

export function renderRoutes(routes) {
  const rows = Array.isArray(routes) ? routes : [];
  return rows.slice(0, 30).map((route) => `<div class="item">
    <div class="mono">${esc(route.uri)}</div>
    <div class="subtle">${esc(text(route.node))} · ${esc(text(route.kind))} · ${esc(text(route.adapter))}</div>
  </div>`).join('') || empty('No routes discovered');
}

export function contactCard(contact, selectedTargets) {
  const sel = Array.isArray(selectedTargets) ? selectedTargets : [];
  const checked = sel.includes(contact.id) ? 'checked' : '';
  const disabled = contact.disabled ? 'disabled' : '';
  const pillClass = contact.reachable === false ? 'down' : (contact.status === 'running' || contact.reachable ? 'up' : '');
  const inputId = `chat-target-${String(contact.id || 'target').replace(/[^a-zA-Z0-9_-]/g, '-')}`;
  const actions = [
    contact.startUri ? `<button type="button" data-contact-action="invoke-uri" data-uri="${esc(contact.startUri)}" data-target="${esc(contact.id)}">Start</button>` : '',
    contact.restartUri ? `<button type="button" data-contact-action="invoke-uri" data-uri="${esc(contact.restartUri)}" data-target="${esc(contact.id)}">Restart</button>` : '',
    contact.url ? `<button type="button" data-contact-action="open-url" data-url="${esc(contact.url)}" data-target="${esc(contact.id)}">Open</button>` : '',
  ].filter(Boolean).join('');
  return `<div class="contact-card">
    <input id="${esc(inputId)}" type="checkbox" name="chatTarget" value="${esc(contact.id)}" ${checked} ${disabled}>
    <span class="contact-body">
      <label class="contact-title" for="${esc(inputId)}">${esc(contact.label)}</label>
      <span class="pill ${pillClass}">${esc(contact.status || contact.kind)}</span>
      <span class="contact-meta">${esc(contact.url || contact.meta || '')}</span>
      ${actions ? `<span class="contact-actions">${actions}</span>` : ''}
    </span>
  </div>`;
}

export function renderContacts(contacts, selectedTargets) {
  const rows = Array.isArray(contacts) ? contacts : [];
  return rows.map((contact) => contactCard(contact, selectedTargets)).join('') || empty('No contacts');
}
