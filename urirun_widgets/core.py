# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# widget:// connector — the chat-stream widgets (the HTML views chatStreamList renders in
# chat-main when scanning) behind a URI. The browser source of truth is the standalone ES
# modules under assets/; this connector lists the catalogue, serves a single widget's JS, serves
# the whole catalogue as one importable bundle (+ CSS), and renders service views or named
# dashboard widgets server-side via the Python mirror for headless surfaces.
#
#   widget://host/registry/query/list                  → the widget catalogue
#   widget://host/widget/query/get?name=table          → one widget: metadata + JS source
#   widget://host/widget/query/render?view=table       → server-side HTML for a view/widget + `data`
#   widget://host/bundle/query/js                       → all widgets as one ES module
#   widget://host/bundle/query/css                      → the shared stylesheet

from __future__ import annotations

import json
from typing import Any

import urirun

from . import catalog
from . import render as _render

CONNECTOR_ID = "widget"
WIDGET = urirun.connector(CONNECTOR_ID, scheme="widget", target="host",
                          meta={"label": "Chat-stream HTML widgets"})


@WIDGET.handler("registry/query/list", isolated=True,
                meta={"label": "List the chat-stream widget catalogue", "cliAlias": "list"})
def list_widgets() -> dict[str, Any]:
    """List every chat-stream widget (id, title, the `view` keys it handles, data shape) — the
    catalogue chatStreamList draws from."""
    rows = [{"id": wid, "title": spec["title"], "views": spec["views"],
             "summary": spec["summary"], "dataShape": spec["dataShape"], "asset": spec["asset"]}
            for wid, spec in catalog.CATALOG.items()]
    return {"ok": True, "connector": CONNECTOR_ID, "kind": "registry", "live": False,
            "count": len(rows), "widgets": rows}


@WIDGET.handler("widget/query/get", isolated=True,
                meta={"label": "Get one widget: metadata + JS source", "cliAlias": "get"})
def get_widget(name: str = "") -> dict[str, Any]:
    """Return one widget by id (e.g. table, scanner-stream): its metadata and the standalone ES
    module source that renders it. `name` may also be a `view` key (e.g. page → iframe widget)."""
    if name in catalog.CATALOG:
        wid = name
    elif name in catalog.VIEW_INDEX:
        wid = catalog.VIEW_INDEX[name]
    else:
        return {"ok": False, "error": f"unknown widget '{name}'", "connector": CONNECTOR_ID,
                "known": list(catalog.CATALOG)}
    spec = catalog.CATALOG[wid]
    try:
        source = catalog.read_asset(spec["asset"])
    except OSError as exc:
        return {"ok": False, "error": str(exc), "connector": CONNECTOR_ID}
    return {"ok": True, "connector": CONNECTOR_ID, "kind": "widget", "live": False,
            "id": wid, "title": spec["title"], "views": spec["views"],
            "dataShape": spec["dataShape"], "asset": spec["asset"], "js": source}


def _coerce_view(view: str, data: str, title: str, status: str, target: str) -> dict[str, Any] | dict[str, str]:
    """Build a view object from flat args, or parse a full view object from `data`."""
    payload: Any = {}
    if data:
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            return {"__error__": f"data is not valid JSON: {exc}"}
    # If `data` already is a full view object (has a 'view' key) use it as-is; else wrap it.
    if isinstance(payload, dict) and "view" in payload and "data" in payload:
        return payload
    view_obj: dict[str, Any] = {"view": view, "data": payload if isinstance(payload, dict) else {}}
    if title:
        view_obj["title"] = title
    if status:
        view_obj["status"] = status
    if target:
        view_obj["target"] = target
    return view_obj


@WIDGET.handler("widget/query/render", isolated=True,
                meta={"label": "Render a view to HTML server-side (Python mirror)", "cliAlias": "render"})
def render_view(view: str = "", data: str = "", title: str = "", status: str = "",
                target: str = "", widget: str = "") -> dict[str, Any]:
    """Render a widget to an HTML string with the Python mirror — for headless surfaces (email,
    SVG, tests). For a chat-stream service view: give the `view` key (table, image, form, ...)
    and `data` (JSON for the view's data payload), or a full view object as `data`. For a
    dashboard widget (attachment, chat-message, artifact-grid, widget-card, metrics, task-table,
    nodes, routes, contacts): give `widget` and `data` (the widget's payload). Unknown view keys
    fall back to the generic JSON dump, never an error."""
    if widget:
        renderer = _render.DASHBOARD_RENDERERS.get(widget)
        if renderer is None:
            return {"ok": False, "error": f"unknown dashboard widget '{widget}'",
                    "connector": CONNECTOR_ID, "known": sorted(_render.DASHBOARD_RENDERERS)}
        try:
            payload = json.loads(data) if data else {}
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": f"data is not valid JSON: {exc}", "connector": CONNECTOR_ID}
        if not isinstance(payload, dict):
            return {"ok": False, "error": "data must be a JSON object", "connector": CONNECTOR_ID}
        return {"ok": True, "connector": CONNECTOR_ID, "kind": "render", "live": False,
                "widget": widget, "html": renderer(payload)}
    view_obj = _coerce_view(view, data, title, status, target)
    if "__error__" in view_obj:
        return {"ok": False, "error": view_obj["__error__"], "connector": CONNECTOR_ID}
    if not view_obj.get("view"):
        return {"ok": False, "error": "provide a view key (or a full view object in data)",
                "connector": CONNECTOR_ID, "known": list(catalog.VIEW_INDEX)}
    html = _render.render_service_view(view_obj)
    return {"ok": True, "connector": CONNECTOR_ID, "kind": "render", "live": False,
            "view": view_obj.get("view"), "widget": catalog.widget_for_view(view_obj.get("view")),
            "html": html}


@WIDGET.handler("bundle/query/js", isolated=True,
                meta={"label": "All widgets as one importable ES module bundle", "cliAlias": "bundle-js"})
def bundle_js() -> dict[str, Any]:
    """Return the whole widget catalogue concatenated into one ES module — helpers, every
    widget, then the renderServiceView dispatcher — so chatStreamList can load the full set
    from a single import. Inter-file `import` lines are stripped; the modules share one scope."""
    chunks = []
    for rel in catalog.BUNDLE_ORDER:
        src = catalog.read_asset(rel)
        # The files are one cohesive module once concatenated, so drop their cross-imports and
        # turn local `export` declarations into plain declarations. A trailing `export { ... }`
        # re-export block (possibly multi-line) is dropped whole — the symbols already exist.
        cleaned_lines = []
        in_export_block = False
        for line in src.splitlines():
            stripped = line.lstrip()
            if in_export_block:
                if "}" in line:
                    in_export_block = False
                continue
            if stripped.startswith("import ") or stripped.startswith("import{"):
                continue
            if stripped.startswith("export {") or stripped.startswith("export{"):
                if "}" not in stripped:
                    in_export_block = True
                continue
            line = line.replace("export function ", "function ").replace("export const ", "const ")
            cleaned_lines.append(line)
        chunks.append(f"// ----- {rel} -----\n" + "\n".join(cleaned_lines))
    bundle = ("// urirun-widgets bundle — generated from assets/; entry points are\n"
              "// renderServiceView(view) and renderDashboardWidget(name, data).\n"
              "// Concatenated module, single scope.\n\n" + "\n\n".join(chunks))
    return {"ok": True, "connector": CONNECTOR_ID, "kind": "bundle", "live": False,
            "format": "esm", "files": catalog.BUNDLE_ORDER, "js": bundle}


@WIDGET.handler("bundle/query/css", isolated=True,
                meta={"label": "The shared widget stylesheet", "cliAlias": "bundle-css"})
def bundle_css() -> dict[str, Any]:
    """Return the shared widgets.css that styles every chat-stream widget (self-contained, with
    default theme variables a host can override)."""
    return {"ok": True, "connector": CONNECTOR_ID, "kind": "bundle", "live": False,
            "format": "css", "css": catalog.read_asset("widgets.css")}


@WIDGET.handler("widget/query/svg", isolated=True,
                meta={"label": "Render a service view as a compact SVG card", "cliAlias": "svg"})
def render_svg(view: str = "", data: str = "", width: int = 720, height: int = 180,
               title: str = "", status: str = "", target: str = "") -> dict[str, Any]:
    """Render a service view as a compact SVG card (a badge for an email, README or status
    page), mirroring the host's /services/view.svg. Give the `view` key + `data`, or a full
    view object as `data`. Returns the SVG markup."""
    view_obj = _coerce_view(view, data, title, status, target)
    if "__error__" in view_obj:
        return {"ok": False, "error": view_obj["__error__"], "connector": CONNECTOR_ID}
    svg = _render.render_svg(view_obj, width=width, height=height)
    return {"ok": True, "connector": CONNECTOR_ID, "kind": "svg", "live": False,
            "view": view_obj.get("view"), "format": "svg", "svg": svg}


def main(argv: list[str] | None = None) -> int:
    return WIDGET.cli(argv, manifest_prose=urirun.load_manifest(__package__))


urirun_bindings = WIDGET.bindings
