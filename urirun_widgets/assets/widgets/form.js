// form widget — a fillable form that posts back a URI. view.view === 'form'.
// data.fields: array of {name|key,label,type,value|default,checked,readonly};
// data.actionUri: the URI run on submit (wired by the host via [data-service-form]).
import { esc, renderServiceViewShell } from '../render-helpers.js';

function _renderField(field) {
  const name = field.name || field.key || field.label || 'field';
  const type = field.type || 'text';
  const value = field.value || field.default || '';
  const isChecked = type === 'checkbox' && (field.checked || value === true || value === 'true');
  const checked = isChecked ? 'checked' : '';
  const readonly = field.readonly ? 'readonly' : '';
  return `<label class="stack">
    <span class="subtle">${esc(field.label || name)}</span>
    <input type="${esc(type)}" name="${esc(name)}" value="${esc(value)}" ${checked} ${readonly}>
  </label>`;
}

export function renderFormServiceView(view) {
  const data = view.data || {};
  const fields = Array.isArray(data.fields) ? data.fields : [];
  const actionUri = data.actionUri || data.uri || view.actionUri || '';
  const fieldHtml = fields.map(_renderField).join('') || '<div class="subtle">no fields</div>';
  const actionHtml = actionUri
    ? `<div class="mono">${esc(actionUri)}</div><button type="submit">Run URI</button>`
    : '<div class="subtle">no action URI</div>';
  const body = `<form class="service-form-preview" data-service-form data-action-uri="${esc(actionUri)}">
    ${fieldHtml}
    ${actionHtml}
  </form>`;
  return renderServiceViewShell(view, body);
}
