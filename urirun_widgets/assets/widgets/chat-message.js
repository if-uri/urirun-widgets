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
    <div>${esc(message.content || '')}</div>
    ${lines ? `<pre>${esc(lines)}</pre>` : ''}
    ${attachments.length ? `<div class="attachments">${attachments.map(renderAttachment).join('')}</div>` : ''}
    ${Object.keys(detail).length ? `<details><summary>URI / JSON</summary><pre>${esc(JSON.stringify(detail, null, 2))}</pre></details>` : ''}
  </div>`;
}
