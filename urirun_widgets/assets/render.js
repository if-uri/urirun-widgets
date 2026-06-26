// Author: Tom Sapletta · https://tom.sapletta.com
// Part of the ifURI solution.
//
// The chat-stream widget dispatcher. `renderServiceView(view)` maps a view's `view` key to the
// right widget renderer — the same dispatch the host dashboard runs for chatStreamList, now
// importable from this repo so any surface (chat-main, a standalone page, an email preview) can
// load the whole catalogue from one module — import renderServiceView from the bundle served by
// widget://host/bundle/query/js, then:  chatStreamList.innerHTML = views.map(renderServiceView).join('');

import { renderScannerStatusServiceView } from './widgets/scanner-status.js';
import { renderScannerStreamView } from './widgets/scanner-stream.js';
import { renderTableServiceView } from './widgets/table.js';
import { renderImageServiceView } from './widgets/image.js';
import { renderVideoServiceView } from './widgets/video.js';
import { renderIframeServiceView } from './widgets/iframe.js';
import { renderFormServiceView } from './widgets/form.js';
import { renderGraphServiceView } from './widgets/graph.js';
import { renderGenericServiceView } from './widgets/generic.js';
import { renderTwinServiceView } from './widgets/twin.js';

// view-key -> renderer. Keys mirror the `view` field a service publishes.
export const WIDGETS = {
  'scanner-status': renderScannerStatusServiceView,
  'scanner-stream': renderScannerStreamView,
  'table': renderTableServiceView,
  'image': renderImageServiceView,
  'image-list': renderImageServiceView,
  'video': renderVideoServiceView,
  'iframe': renderIframeServiceView,
  'page': renderIframeServiceView,
  'web': renderIframeServiceView,
  'form': renderFormServiceView,
  'graph': renderGraphServiceView,
  'twin': renderTwinServiceView,
};

export function renderServiceView(view) {
  const fn = WIDGETS[view && view.view] || renderGenericServiceView;
  return fn(view);
}

export {
  renderScannerStatusServiceView, renderScannerStreamView, renderTableServiceView,
  renderImageServiceView, renderVideoServiceView, renderIframeServiceView,
  renderFormServiceView, renderGraphServiceView, renderGenericServiceView,
  renderTwinServiceView,
};
