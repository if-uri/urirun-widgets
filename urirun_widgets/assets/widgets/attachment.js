// attachment widget — one chat attachment: a scan/PDF/image/QR preview + OCR line + metadata.
// The core "scanning in chat" view. Rendered per message by chat-message.js.
import { esc, text, basename, filePreviewUrl } from '../render-helpers.js';

export function attachmentVisualPreviewUrl(att) {
  const meta = att.meta || {};
  const displayPath = text(meta.displayImage || meta.displayPath || meta.previewImage || meta.image || '');
  return displayPath ? filePreviewUrl(displayPath) : '';
}

export function isPdfAttachment(att) {
  return att && (att.kind === 'document-pdf' || /\.pdf$/i.test(text(att.path)));
}

export function isScannerFrameAttachment(att) {
  if (!att) return false;
  const kind = text(att.kind);
  const uri = text(att.uri);
  return ['receipt-crop', 'image', 'camera-scan'].includes(kind) || uri.startsWith('scanner://host/capture/');
}

export function renderAttachment(att) {
  const meta = att.meta || {};
  const ocr = meta.ocr || {};
  const isPdf = isPdfAttachment(att);
  const kindClass = att.kind === 'qr-code' ? ' attachment-qr' : isPdf ? ' attachment-pdf' : '';
  const visualUrl = isPdf ? attachmentVisualPreviewUrl(att) : text(att.previewUrl || '');
  const pdfUrl = isPdf ? text(att.previewUrl || '') : '';
  const preview = isPdf && pdfUrl
    ? `<iframe class="attachment-pdf-frame" src="${esc(pdfUrl)}" title="${esc(basename(att.path))}" loading="lazy"></iframe>`
    : (visualUrl
      ? `<img src="${esc(visualUrl)}" alt="${esc(basename(att.path))}" loading="lazy">`
      : (isPdf
        ? `<div class="attachment-pdf-preview"><span>PDF</span><small>${esc(basename(att.path))}</small></div>`
        : `<div class="subtle">preview unavailable</div>`));
  const open = att.previewUrl ? `<a href="${esc(att.previewUrl)}" target="_blank" rel="noreferrer">open</a>` : '';
  const download = att.previewUrl ? `<a href="${esc(att.previewUrl)}" download>download</a>` : '';
  const ocrLine = ocr.ok
    ? `<div class="subtle">OCR ${esc(ocr.backend || '')}: ${esc(text(ocr.text).slice(0, 160))}</div>`
    : (ocr.error ? `<div class="subtle">OCR: ${esc(ocr.error)}</div>` : '');
  return `<div class="attachment${kindClass}">
    ${preview}
    <div class="mono">${esc(basename(att.path))}</div>
    <div class="subtle">${esc(att.kind || 'file')} ${meta.width && meta.height ? `· ${meta.width}x${meta.height}` : ''}</div>
    <div class="artifact-actions">${open}${download}</div>
    ${ocrLine}
    <details><summary>metadata</summary><pre>${esc(JSON.stringify(att, null, 2))}</pre></details>
  </div>`;
}
