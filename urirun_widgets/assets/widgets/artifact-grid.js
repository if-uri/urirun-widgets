// artifact-grid widget — the file grid of stored artifacts (scans, PDFs, images) with preview
// thumbnails, metadata summary and open/download/delete actions. Pure: pass the items and the
// set of selected ids; returns the grid HTML (the host's version wrote straight to the DOM).
import { esc, text, basename, filePreviewUrl } from '../render-helpers.js';

function artifactFileUrl(item) {
  if (item && item.filePreviewUrl !== undefined) return text(item.filePreviewUrl);
  if (item && item.fileExists === false) return '';
  return filePreviewUrl(item && item.path ? String(item.path) : '');
}

function artifactVisualPath(item) {
  const path = item && item.path ? String(item.path) : '';
  const meta = item && item.meta ? item.meta : {};
  if (/\.pdf$/i.test(path)) {
    return text(meta.displayImage || meta.displayPath || meta.previewImage || meta.image || '');
  }
  return path;
}

function artifactVisualPreviewUrl(item) {
  if (item && item.previewUrl !== undefined) return text(item.previewUrl);
  if (item && item.previewExists === false) return '';
  return filePreviewUrl(artifactVisualPath(item));
}

export function artifactThumb(item) {
  const path = item && item.path ? String(item.path) : '';
  const visualPath = artifactVisualPath(item);
  const url = artifactVisualPreviewUrl(item);
  const ext = (path.match(/\.([a-z0-9]+)$/i) || [, 'file'])[1].toLowerCase();
  if (/\.pdf$/i.test(path)) {
    if (url && /\.(png|jpe?g|webp|gif)$/i.test(visualPath)) {
      return `<div class="artifact-thumb"><img src="${esc(url)}" alt="${esc(basename(visualPath))}" loading="lazy"></div>`;
    }
    return `<div class="artifact-thumb artifact-thumb-pdf"><span>PDF</span><small>${esc(basename(path))}</small></div>`;
  }
  if (!url) return path ? `<div class="artifact-thumb artifact-thumb-missing">missing<br>file</div>` : `<div class="artifact-thumb">uri</div>`;
  if (/\.(png|jpe?g|webp|gif)$/i.test(visualPath)) {
    return `<div class="artifact-thumb"><img src="${esc(url)}" alt="${esc(basename(visualPath))}" loading="lazy"></div>`;
  }
  return `<div class="artifact-thumb">${esc(ext)}</div>`;
}

function artifactMetaSummary(item) {
  const meta = item.meta || {};
  const doc = (meta.document && meta.document.metadata) || meta.detectedDocument || meta.metadata || {};
  return [doc.type || meta.type, doc.date || meta.date,
    doc.contractor || doc.supplier || doc.category || meta.contractor,
    doc.amount || meta.amount].filter(Boolean).join(' · ');
}

function _isSelected(id, selectedIds) {
  if (!id || !selectedIds) return false;
  return typeof selectedIds.has === 'function' ? selectedIds.has(id) : selectedIds.includes(id);
}

function _rowControls(id, url, path, item) {
  const openLink = url ? `<a href="${esc(url)}" target="_blank" rel="noreferrer">open</a>` : '';
  const download = url ? `<a href="${esc(url)}" download>download</a>` : '';
  const missing = (path && item.fileExists === false) ? '<span class="pill down">missing file</span>' : '';
  const deleteBtn = id ? `<button type="button" class="danger" data-artifact-delete="${esc(id)}">Delete</button>` : '';
  const metaDetails = item.meta ? `<details><summary>metadata</summary><pre>${esc(JSON.stringify(item.meta, null, 2))}</pre></details>` : '';
  return { openLink, download, missing, deleteBtn, metaDetails };
}

export function renderArtifactFileRow(item, selectedIds) {
  const id = text(item.id);
  const path = text(item.path);
  const name = basename(path || item.uri || item.id);
  const url = artifactFileUrl(item);
  const metaLine = artifactMetaSummary(item);
  const selected = _isSelected(id, selectedIds) ? 'checked' : '';
  const duplicateCount = Number(item.duplicateCount || 0);
  const duplicates = duplicateCount > 1 ? `<span class="pill">${duplicateCount} records</span>` : '';
  const { openLink, download, missing, deleteBtn, metaDetails } = _rowControls(id, url, path, item);
  return `<div class="artifact-file-row">
    <div><input type="checkbox" name="artifactSelect" value="${esc(id)}" ${selected}></div>
    ${artifactThumb(item)}
    <div>
      <div class="artifact-name"><strong>${esc(name)}</strong><span class="pill">${esc(item.kind || 'artifact')}</span>${duplicates}${missing}</div>
      <div class="mono">${esc(path || item.uri || '')}</div>
      <div class="artifact-actions">${openLink}${download}</div>
    </div>
    <div>
      <div class="mono">${esc(item.uri || '')}</div>
      ${metaLine ? `<div class="artifact-meta-line">${esc(metaLine)}</div>` : ''}
    </div>
    <div>
      <div class="subtle">${esc(item.created_at || '')}</div>
      ${deleteBtn}
      ${metaDetails}
    </div>
  </div>`;
}

export function renderArtifactFileGrid(items, selectedIds) {
  const rows = Array.isArray(items) ? items : [];
  if (!rows.length) return `<div class="item subtle">No artifacts recorded</div>`;
  const header = `<div class="artifact-file-row header"><div></div><div>Preview</div><div>File</div><div>URI / document</div><div>Created</div></div>`;
  return `<div class="artifact-file-grid">${header}${rows.map((item) => renderArtifactFileRow(item, selectedIds)).join('')}</div>`;
}
