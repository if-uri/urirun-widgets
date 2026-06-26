// attachment widget — one chat attachment: a scan/PDF/image/QR preview + OCR line + metadata.
// The core "scanning in chat" view. Rendered per message by chat-message.js.
import { esc, text, basename, filePreviewUrl } from '../render-helpers.js';

export function attachmentVisualPreviewUrl(att) {
  if (att && att.visualPreviewUrl !== undefined) return text(att.visualPreviewUrl);
  if (att && att.previewExists === false) return '';
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
  if (att.kind === 'twin-monitor') {
    const url = esc(att.uri || '/twin');
    return `<div class="attachment attachment-widget" style="width:100%;"><iframe src="${url}" title="Digital Twin Monitor" style="width:100%;height:450px;border:1px solid var(--border-color);border-radius:4px;" loading="lazy"></iframe></div>`;
  }
  const meta = att.meta || {};
  const isPdf = isPdfAttachment(att);
  const fileAvailable = att.fileExists !== false;
  const kindClass = att.kind === 'qr-code' ? ' attachment-qr' : isPdf ? ' attachment-pdf' : '';
  const visualUrl = isPdf ? attachmentVisualPreviewUrl(att) : text(att.previewUrl || '');
  const pdfUrl = isPdf && fileAvailable ? text(att.previewUrl || att.filePreviewUrl || '') : '';
  const preview = isPdf && pdfUrl
    ? `<iframe class="attachment-pdf-frame" src="${esc(pdfUrl)}" title="${esc(basename(att.path))}" loading="lazy"></iframe>`
    : (visualUrl
      ? `<img src="${esc(visualUrl)}" alt="${esc(basename(att.path))}" loading="lazy">`
      : (isPdf
        ? `<div class="attachment-pdf-preview"><span>PDF</span><small>${esc(basename(att.path))}</small></div>`
        : `<div class="subtle">preview unavailable</div>`));
  const fileUrl = fileAvailable ? text(att.previewUrl || att.filePreviewUrl || '') : '';
  const open = fileUrl ? `<a href="${esc(fileUrl)}" target="_blank" rel="noreferrer">open</a>` : '';
  const download = fileUrl ? `<a href="${esc(fileUrl)}" download>download</a>` : '';
  const missing = att.fileExists === false ? '<span class="pill down">missing file</span>' : '';
  const detailAtt = fileAvailable ? att : {...att, previewUrl: '', filePreviewUrl: ''};
  const ocr = att.ocr || {};
  const ocrLine = ocr.ok
    ? `<div class="subtle">OCR ${esc(ocr.backend || '')}: ${esc(text(ocr.text).slice(0, 160))}</div>`
    : (ocr.error ? `<div class="subtle">OCR: ${esc(ocr.error)}</div>` : '');
  return `<div class="attachment${kindClass}">
    ${preview}
    <div class="mono">${esc(basename(att.path))}</div>
    <div class="subtle">${esc(att.kind || 'file')} ${meta.width && meta.height ? `· ${meta.width}x${meta.height}` : ''} ${missing}</div>
    <div class="artifact-actions">${open}${download}</div>
    ${ocrLine}
    <details><summary>metadata</summary><pre>${esc(JSON.stringify(detailAtt, null, 2))}</pre></details>
  </div>`;
}
