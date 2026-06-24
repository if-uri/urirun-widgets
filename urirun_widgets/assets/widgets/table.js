// table widget — tabular service data. view.view === 'table'.
// data.rows: array of objects; data.columns: optional explicit column list (string or {key}).
import { esc, text, renderServiceViewShell } from '../render-helpers.js';

export function renderTableServiceView(view) {
  const data = view.data || {};
  const rows = Array.isArray(data.rows) ? data.rows : [];
  const explicitColumns = Array.isArray(data.columns) ? data.columns : [];
  const columns = explicitColumns.length
    ? explicitColumns.map((column) => typeof column === 'string' ? column : column.key || column.name || column.label).filter(Boolean)
    : [...new Set(rows.flatMap((row) => Object.keys(row || {})))];
  const table = columns.length
    ? `<div class="service-table-wrap"><table>
        <thead><tr>${columns.map((column) => `<th>${esc(column)}</th>`).join('')}</tr></thead>
        <tbody>${rows.map((row) => `<tr>${columns.map((column) => `<td>${esc(text(row && row[column]))}</td>`).join('')}</tr>`).join('')}</tbody>
      </table></div>`
    : `<div class="subtle">no rows</div>`;
  return renderServiceViewShell(view, table);
}
