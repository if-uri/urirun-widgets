// chat-message widget — one chat message: role, content, URI timeline, and its attachments.
// Depends on the attachment widget. `selectedIds` (Set or array) drives the selection checkbox.
import { esc } from '../render-helpers.js';
import { renderAttachment, isPdfAttachment, isScannerFrameAttachment } from './attachment.js';

// Pick the attachments worth showing for a message: prefer the PDF; hide raw scanner frames
// once a PDF (or accepted document) exists. (Faithful to the host, minus its self-recursion bug.)
export function messageAttachments(message) {
  const detail = message.detail || {};
  const document = detail.document || {};
  const attachments = Array.isArray(message.attachments) ? message.attachments
    : (Array.isArray(detail.attachments) ? detail.attachments : []);
  const hasPdf = attachments.some(isPdfAttachment);
  return attachments.filter((att) => {
    if (isPdfAttachment(att)) return true;
    // A confirmed previewUrl means a real file is there (e.g. a KVM screenshot stored with
    // kind "image" or "screenshot") — never suppress it regardless of scanner-frame rules.
    if (att.previewUrl) return true;
    if (hasPdf && isScannerFrameAttachment(att)) return false;
    if (isScannerFrameAttachment(att) && !(document.ok && document.path)) return false;
    return true;
  });
}

function _messageButtons(message, role, selectedIds) {
  const has = (id) => selectedIds && (typeof selectedIds.has === 'function' ? selectedIds.has(id) : selectedIds.includes(id));
  if (!message.id) return { checkbox: '', deleteButton: '', copyMarkdownButton: '', repeatButton: '' };
  const id = message.id;
  const selected = has(id) ? 'checked' : '';
  const checkbox = `<input type="checkbox" name="chatMessageSelect" value="${esc(id)}" ${selected}>`;
  const deleteButton = `<button type="button" class="danger" data-chat-delete="${esc(id)}">Delete</button>`;
  const copyMarkdownButton = `<button type="button" data-chat-copy-md="${esc(id)}" title="Copy message as Markdown">Copy MD</button>`;
  // Re-run the command: only on user messages that carry a prompt (the command text).
  const repeatButton = (role === 'user' && (message.content || '').trim())
    ? `<button type="button" data-chat-repeat="${esc(id)}" title="Powtorz komende">Repeat</button>` : '';
  return { checkbox, deleteButton, copyMarkdownButton, repeatButton };
}

function _humanTaskBanner(detail) {
  const escalation = detail.escalation || {};
  const task = detail.humanTask || escalation.humanTask || {};
  const next = detail.next || escalation.next || {};
  const notify = detail.notify || escalation.notify || {};
  const active = detail.kind === 'human-task' || detail.humanEscalation === true || task.id || notify.sound === 'beep';
  if (!active) return '';
  const title = task.title || detail.humanAction || next.instruction || 'Human action required';
  const url = task.surfaceUrl || detail.dashboardUrl || next.dashboardUrl || '';
  return `<div class="human-task-alert" style="border:1px solid var(--warn,#f59e0b);background:rgba(245,158,11,.10);border-radius:4px;padding:8px 10px;margin:6px 0">
    <strong>Human task</strong>
    <span>${esc(title)}</span>
    ${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open</a>` : ''}
  </div>`;
}

export function renderChatMessage(message, selectedIds) {
  const detail = message.detail || {};
  const timeline = detail.timeline || [];
  const lines = timeline.map((step) => `${step.ok ? 'ok' : 'fail'} · ${step.target || ''} · ${step.uri}`).join('\n');
  const attachments = messageAttachments(message);
  const role = message.role || 'system';
  const { checkbox, deleteButton, copyMarkdownButton, repeatButton } = _messageButtons(message, role, selectedIds);
  return `<div class="message ${esc(role)}">
    <div class="message-head">
      <span class="message-title">${checkbox}<strong>${esc(role)}</strong></span>
      <span class="message-actions">
        <span class="subtle">${esc(message.created_at || '')}</span>
        ${repeatButton}
        ${copyMarkdownButton}
        ${deleteButton}
      </span>
    </div>
    ${_humanTaskBanner(detail)}
    <div>${esc(message.content || '')}</div>
    ${lines ? `<pre>${esc(lines)}</pre>` : ''}
    ${attachments.length ? `<div class="attachments">${attachments.map(renderAttachment).join('')}</div>` : ''}
    ${Object.keys(detail).length ? `<details><summary>URI / JSON</summary><pre>${esc(JSON.stringify(detail, null, 2))}</pre></details>` : ''}
  </div>`;
}
