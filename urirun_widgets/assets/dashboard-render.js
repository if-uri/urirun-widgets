// dashboard-render — explicit dashboard widget dispatcher.
//
// Service widgets are selected by a service view's `view` key and rendered by renderServiceView.
// Dashboard widgets are selected by name: artifacts, chat messages, attachments, contacts, etc.
// Keeping this map in urirun-widgets lets host_dashboard consume one stable function instead of
// importing every individual renderer by name.
import { renderAttachment } from './widgets/attachment.js';
import { renderChatMessage } from './widgets/chat-message.js';
import { renderArtifactFileGrid } from './widgets/artifact-grid.js';
import { renderMetrics, renderTasks, renderNodes, renderRoutes, renderContacts } from './widgets/dashboard.js';
import { renderWidgetCard } from './widgets/widget-card.js';

export const DASHBOARD_WIDGETS = {
  'attachment': (data) => renderAttachment(data.att || data),
  'chat-message': (data) => renderChatMessage(data.message || data, data.selectedIds || []),
  'artifact-grid': (data) => renderArtifactFileGrid(data.items || [], data.selectedIds || []),
  'widget-card': (data) => renderWidgetCard(data.service || {}, data.view || null),
  'metrics': (data) => renderMetrics(data.summary || data),
  'task-table': (data) => renderTasks(data.tasks || []),
  'nodes': (data) => renderNodes(data.nodes || []),
  'routes': (data) => renderRoutes(data.routes || []),
  'contacts': (data) => renderContacts(data.contacts || [], data.selectedTargets || []),
};

export function renderDashboardWidget(name, data) {
  const fn = DASHBOARD_WIDGETS[name];
  return fn ? fn(data || {}) : '';
}
