"""Offline tests for the widget connector: bindings, catalogue, asset serving, the ES bundle,
and the Python server-side renderer mirroring the chatStreamList views."""
import json
import re
from pathlib import Path

import urirun_widgets.core as c
from urirun_widgets import catalog, render


def _js_widget_view_keys() -> set[str]:
    """View keys declared in the JS `WIDGETS` dispatch map (render.js)."""
    js = catalog.read_asset("render.js")
    block = js.split("const WIDGETS", 1)[1].split("}", 1)[0]
    return set(re.findall(r"'([a-z0-9-]+)'\s*:", block))


def _catalog_concrete_view_keys() -> set[str]:
    """Concrete view keys in the catalogue, excluding the generic '*' fallback."""
    keys: set[str] = set()
    for spec in catalog.CATALOG.values():
        keys.update(v for v in spec.get("views", []) if v != "*")
    return keys


def test_bindings_valid():
    b = c.urirun_bindings()
    uris = set(b["bindings"])
    assert "widget://host/registry/query/list" in uris
    assert "widget://host/widget/query/render" in uris
    for spec in b["bindings"].values():
        assert spec["python"]["module"].endswith("core")
        assert spec["uri"].startswith("widget://")


def test_catalogue_lists_core_widgets():
    r = c.list_widgets()
    ids = {w["id"] for w in r["widgets"]}
    for wid in ("scanner-stream", "scanner-status", "table", "image", "form", "graph", "generic"):
        assert wid in ids


def test_get_widget_returns_js_source():
    r = c.get_widget(name="table")
    assert r["ok"] and r["id"] == "table"
    assert "renderTableServiceView" in r["js"]
    # a `view` key also resolves to its widget
    assert c.get_widget(name="page")["id"] == "iframe"


def test_get_unknown_widget():
    r = c.get_widget(name="nope")
    assert r["ok"] is False and "unknown widget" in r["error"]


def test_render_table_matches_data():
    data = {"rows": [{"nip": "7781422455", "gross": 1230.0}, {"nip": "1132871234", "gross": 615.0}]}
    r = c.render_view(view="table", data=json.dumps(data), title="VAT register")
    assert r["ok"] and r["widget"] == "table"
    html = r["html"]
    assert "<table>" in html and "7781422455" in html and "1230.0" in html
    assert "<th>nip</th>" in html and "<th>gross</th>" in html
    assert "VAT register" in html


def test_render_escapes_html():
    r = c.render_view(view="table", data=json.dumps({"rows": [{"x": "<script>alert(1)</script>"}]}))
    assert "<script>alert(1)" not in r["html"]
    assert "&lt;script&gt;" in r["html"]


def test_render_unknown_view_falls_back_to_generic():
    r = c.render_view(view="totally-unknown", data=json.dumps({"a": 1}))
    assert r["ok"] and r["widget"] == "generic"
    assert "service data" in r["html"]


def test_render_full_view_object_in_data():
    view = {"view": "graph", "title": "deps",
            "data": {"nodes": [{"id": "a"}], "edges": [{"from": "a", "to": "b"}]}}
    r = c.render_view(data=json.dumps(view))
    assert r["ok"] and r["widget"] == "graph"
    assert "a -&gt; b" in r["html"] and "deps" in r["html"]


def test_bundle_js_is_concatenated_module_without_imports():
    r = c.bundle_js()
    assert r["ok"] and r["format"] == "esm"
    js = r["js"]
    # active cross-file imports stripped; dispatcher + a couple of renderers present as plain funcs
    assert "from './" not in js and "from '../" not in js
    assert "function renderServiceView(" in js
    assert "function renderDashboardWidget(" in js
    assert "function renderTableServiceView(" in js
    assert "const WIDGETS" in js
    assert "const DASHBOARD_WIDGETS" in js


def test_bundle_css_self_contained():
    r = c.bundle_css()
    assert r["ok"] and r["format"] == "css"
    assert ".stream-card" in r["css"] and ":root" in r["css"]


def test_python_and_js_widget_sets_match_bidirectionally():
    # The Python renderer (render.py RENDERERS) and the JS dispatcher (render.js WIDGETS)
    # must cover EXACTLY the same view keys -- neither may add a view the other lacks.
    # The previous one-directional check missed a view added to JS but not mirrored in Python.
    python_keys = set(render.RENDERERS)
    js_keys = _js_widget_view_keys()
    assert python_keys, "render.py RENDERERS is empty (parsing/structure changed?)"
    assert js_keys, "could not parse JS WIDGETS map (structure changed?)"
    missing_in_js = python_keys - js_keys
    missing_in_python = js_keys - python_keys
    assert not missing_in_js, f"views in Python but not JS: {sorted(missing_in_js)}"
    assert not missing_in_python, f"views in JS but not Python: {sorted(missing_in_python)}"


def test_catalog_views_match_renderer_keys():
    # The catalogue's declared view keys (minus the '*' generic fallback) must line up
    # with both renderers, so a new catalogue entry can't silently lack a renderer.
    catalog_keys = _catalog_concrete_view_keys()
    python_keys = set(render.RENDERERS)
    assert catalog_keys == python_keys, (
        f"catalogue vs Python renderer drift: "
        f"catalog-only={sorted(catalog_keys - python_keys)}, "
        f"renderer-only={sorted(python_keys - catalog_keys)}"
    )


def test_every_python_renderer_renders_without_error():
    # Each known view must render on minimal data without raising or hitting a missing
    # helper (catches a renderer that drifted to require a field or lost a dependency).
    # Live/stream widgets legitimately render nothing without data, so assert ok + a string
    # rather than non-empty HTML.
    for view_key in render.RENDERERS:
        r = c.render_view(view=view_key, data="{}")
        assert r["ok"], f"{view_key} render failed: {r}"
        assert isinstance(r["html"], str), f"{view_key} did not return HTML string"


# --- dashboard widgets (attachment / chat-message / artifact-grid / widget-card / metrics /
# task-table / nodes / routes / contacts) — extracted from host_dashboard, rendered explicitly
# (no `view` key), so they live in DASHBOARD_RENDERERS, never in the RENDERERS/WIDGETS map. ---

def test_dashboard_widgets_in_catalog_with_no_concrete_view():
    r = c.list_widgets()
    ids = {w["id"] for w in r["widgets"]}
    for wid in ("attachment", "chat-message", "artifact-grid", "widget-card",
                "metrics", "task-table", "nodes", "routes", "contacts"):
        assert wid in ids, wid
    # they must NOT introduce concrete view keys (would break the RENDERERS↔WIDGETS invariant)
    assert _catalog_concrete_view_keys() == set(render.RENDERERS)


def test_dashboard_renderers_match_catalog_dashboard_widgets():
    # every dashboard renderer has a catalogue entry and vice-versa (the views==[] ones)
    dashboard_catalog_ids = {wid for wid, spec in catalog.CATALOG.items()
                             if not [v for v in spec.get("views", []) if v != "*"] and wid != "generic"}
    assert dashboard_catalog_ids == set(render.DASHBOARD_RENDERERS)


# --- connector + contract examples -----------------------------------------

def _contract_kernel():
    import pytest

    return pytest.importorskip("urirun_contract")


def _widget_contracts():
    uc = _contract_kernel()
    return {
        "widget/query/render": uc.Contract(
            version="v1",
            effect="query",
            inp={
                "view": "?str",
                "data": "?str",
                "title": "?str",
                "status": "?str",
                "target": "?str",
                "widget": "?str",
            },
            out={
                "ok": "const:true",
                "connector": "const:widget",
                "kind": "const:render",
                "live": "const:false",
                "html": "str",
            },
            examples=(
                {
                    "payload": {"view": "table", "data": "{\"rows\":[{\"nip\":\"7781422455\"}]}"},
                    "result": {
                        "ok": True,
                        "connector": "widget",
                        "kind": "render",
                        "live": False,
                        "html": "<table></table>",
                    },
                },
            ),
        ),
        "bundle/query/js": uc.Contract(
            version="v1",
            effect="query",
            out={
                "ok": "const:true",
                "connector": "const:widget",
                "kind": "const:bundle",
                "live": "const:false",
                "format": "const:esm",
                "js": "str",
            },
            examples=(
                {
                    "payload": {},
                    "result": {
                        "ok": True,
                        "connector": "widget",
                        "kind": "bundle",
                        "live": False,
                        "format": "esm",
                        "js": "export function renderServiceView() {}",
                    },
                },
            ),
        ),
    }


def test_widget_manifest_examples_satisfy_contracts():
    uc = _contract_kernel()
    contracts = _widget_contracts()
    uc.conform(contracts)

    manifest = json.loads((Path(c.__file__).with_name("connector.manifest.json")).read_text())
    examples = {item["uri"]: item for item in manifest["examples"]}

    render_payload = examples["widget://host/widget/query/render"]["payload"]
    uc.check(contracts["widget/query/render"].inp, render_payload, "manifest render payload")
    render_result = c.render_view(**render_payload)
    assert uc.envelope_violation(contracts["widget/query/render"], render_result) is None

    bundle_payload = examples["widget://host/bundle/query/js"]["payload"]
    uc.check(contracts["bundle/query/js"].inp, bundle_payload, "manifest bundle payload")
    bundle_result = c.bundle_js()
    assert uc.envelope_violation(contracts["bundle/query/js"], bundle_result) is None


def test_widget_contract_reaches_registry_and_mcp_output_schema():
    uc = _contract_kernel()
    v2_mcp = __import__("urirun_runtime.v2_mcp", fromlist=["to_mcp_tools"])

    contracts = _widget_contracts()
    uc.attach_contracts(c.WIDGET, contracts)

    registry = c.WIDGET.registry()
    tools = {tool["_uri"]: tool for tool in v2_mcp.to_mcp_tools(registry)}
    render_tool = tools["widget://host/widget/query/render"]
    assert render_tool["outputSchema"]["properties"]["html"] == {"type": "string"}
    assert render_tool["outputSchema"]["properties"]["connector"] == {"const": "widget"}
    assert render_tool["outputSchema"]["examples"][0]["kind"] == "render"


def test_render_attachment_widget():
    att = {"path": "/scans/FV-1.pdf", "kind": "document-pdf", "previewUrl": "/api/file?path=/scans/FV-1.pdf",
           "meta": {"ocr": {"ok": True, "backend": "paddle", "text": "FAKTURA VAT"}}}
    r = c.render_view(widget="attachment", data=json.dumps({"att": att}))
    assert r["ok"] and r["widget"] == "attachment"
    assert "attachment-pdf-frame" in r["html"] and "FAKTURA VAT" in r["html"]


def test_render_attachment_missing_pdf_does_not_embed_stale_file_url():
    att = {"path": "/scans/missing.pdf", "kind": "document-pdf", "previewUrl": "/api/file?path=/scans/missing.pdf",
           "fileExists": False, "previewExists": False, "visualPreviewUrl": "", "meta": {}}
    r = c.render_view(widget="attachment", data=json.dumps({"att": att}))
    assert r["ok"] and r["widget"] == "attachment"
    assert "attachment-pdf-frame" not in r["html"]
    assert "/api/file?path=/scans/missing.pdf" not in r["html"]
    assert "missing file" in r["html"]


def test_render_attachment_twin_monitor():
    att = {"kind": "twin-monitor", "path": "Digital Twin Widget",
           "uri": "/twin?source=live&execute=1&prompt=test", "fileExists": False}
    r = c.render_view(widget="attachment", data=json.dumps({"att": att}))
    assert r["ok"] and r["widget"] == "attachment"
    assert "iframe" in r["html"]
    assert "/twin?source=live" in r["html"]
    assert "attachment-widget" in r["html"]
    assert "preview unavailable" not in r["html"]


def test_render_chat_message_with_attachment():
    # a qr-code attachment is always shown; scanner frames are hidden unless an accepted
    # document exists (see message_attachments filtering).
    msg = {"role": "user", "content": "skan paragonu", "id": "m1",
           "attachments": [{"path": "/s/qr.png", "kind": "qr-code", "previewUrl": "/api/file?path=/s/qr.png"}]}
    r = c.render_view(widget="chat-message", data=json.dumps({"message": msg, "selectedIds": ["m1"]}))
    assert r["ok"] and r["widget"] == "chat-message"
    assert "skan paragonu" in r["html"] and "checked" in r["html"] and "attachment" in r["html"]
    assert 'data-chat-copy-md="m1"' in r["html"] and "Copy MD" in r["html"]


def test_chat_message_repeat_button_only_on_user_commands():
    # Repeat re-runs a command, so it appears only on user messages that carry a prompt,
    # never on system/result messages.
    user = c.render_view(widget="chat-message", data=json.dumps({"message": {"role": "user", "content": "wyslij do lenovo", "id": "u1"}}))
    system = c.render_view(widget="chat-message", data=json.dumps({"message": {"role": "system", "content": "done", "id": "s1"}}))
    assert 'data-chat-repeat="u1"' in user["html"] and "Repeat" in user["html"]
    assert "data-chat-repeat=" not in system["html"]


def test_render_artifact_grid():
    items = [{"id": "a1", "path": "/s/FV.pdf", "kind": "invoice", "uri": "doc://host/x",
              "created_at": "2026-06-24", "meta": {"detectedDocument": {"type": "faktura", "amount": 1230}}}]
    r = c.render_view(widget="artifact-grid", data=json.dumps({"items": items, "selectedIds": ["a1"]}))
    assert r["ok"] and "artifact-file-row" in r["html"] and "faktura" in r["html"] and "checked" in r["html"]


def test_render_metrics_and_tasks():
    m = c.render_view(widget="metrics", data=json.dumps({"summary": {"taskCounts": {"open": 3}, "nodesOnline": 2}}))
    assert m["ok"] and "open tasks" in m["html"] and ">3<" in m["html"]
    t = c.render_view(widget="task-table", data=json.dumps({"tasks": [{"id": "T1", "name": "Do it", "status": "open"}]}))
    assert t["ok"] and "T1" in t["html"] and "Do it" in t["html"]


def test_render_unknown_dashboard_widget():
    r = c.render_view(widget="nope", data="{}")
    assert r["ok"] is False and "unknown dashboard widget" in r["error"]


def test_render_svg_card():
    view = {"view": "scanner-stream", "title": "scan", "status": "accepted",
            "data": {"streams": [{"count": 3, "best": {"detectedDocument": {"type": "faktura", "amount": 1230}}}]}}
    r = c.render_svg(data=json.dumps(view), width=600, height=160)
    assert r["ok"] and r["format"] == "svg"
    assert r["svg"].startswith("<svg") and "faktura" in r["svg"] and "accepted" in r["svg"]


def test_dashboard_widget_assets_are_valid_in_bundle():
    # the new modules must be included in the bundle and survive import-stripping
    js = c.bundle_js()["js"]
    for fn in ("renderAttachment", "renderChatMessage", "renderArtifactFileGrid",
               "renderWidgetCard", "renderMetrics", "renderTasks", "renderContacts",
               "renderDashboardWidget"):
        assert f"function {fn}(" in js, fn
    assert "from './" not in js and "from '../" not in js


def test_dashboard_widget_dispatcher_asset_is_in_bundle():
    js = c.bundle_js()["js"]
    assert "'artifact-grid': (data) => renderArtifactFileGrid" in js
    assert "'chat-message': (data) => renderChatMessage" in js
    assert "'contacts': (data) => renderContacts" in js


def test_render_twin_applied():
    data = {
        "narration": "Nawiguję do LinkedIn",
        "status": "applied",
        "forward": "goto('https://linkedin.com')",
        "inverse": "history_back()",
        "reversible": True,
        "before": {"fingerprint": "browser_new_tab", "stateSig": "sig_002", "url": "about:blank"},
        "after":  {"fingerprint": "linkedin_feed",   "stateSig": "sig_003", "url": "https://linkedin.com/feed"},
    }
    r = c.render_view(view="twin", data=json.dumps(data), title="Twin Monitor")
    assert r["ok"] and r["widget"] == "twin"
    html = r["html"]
    assert "twin-panel" in html
    assert "Nawiguję do LinkedIn" in html
    assert "goto(" in html and "https://linkedin.com" in html
    assert "history_back()" in html
    assert "browser_new_tab" in html and "linkedin_feed" in html
    assert "NONE" not in html  # reversible, so no NONE label


def test_render_twin_blocked_irreversible():
    data = {
        "narration": "Akcja bez inwersu",
        "status": "blocked",
        "forward": "click('Wyślij')",
        "inverse": None,
        "reversible": False,
        "before": {"fingerprint": "fp_before", "url": "https://linkedin.com"},
        "after":  {"fingerprint": "fp_after",  "url": "https://linkedin.com"},
    }
    r = c.render_view(view="twin", data=json.dumps(data))
    assert r["ok"] and r["widget"] == "twin"
    html = r["html"]
    assert "twin-blocked" in html and "NONE" in html and "irreversible" in html
    assert "twin-narration blocked" in html


def test_twin_in_catalogue_and_bundle():
    # twin must appear in the catalogue list
    ids = {w["id"] for w in c.list_widgets()["widgets"]}
    assert "twin" in ids
    # twin renderer must survive bundle import-stripping
    js = c.bundle_js()["js"]
    assert "function renderTwinServiceView(" in js
    assert "'twin': renderTwinServiceView" in js


def test_datashape_fields_referenced_consistently_in_js_and_python():
    """Content-drift guard (deeper than view-keys): for each widget, the JS source and the
    Python mirror must reference the SAME subset of the catalogue's declared dataShape
    fields. A field rendered by one implementation but ignored by the other trips this."""
    import inspect
    import urirun_widgets.render as render
    drift = {}
    for wid, spec in catalog.CATALOG.items():
        keys = [k for k in (spec.get("dataShape") or {}) if k != "*"]
        if not keys:
            continue
        js = catalog.read_asset(spec["asset"])
        views = [v for v in spec.get("views", []) if v != "*"]
        func = render.RENDERERS.get(views[0]) if views else render.DASHBOARD_RENDERERS.get(wid)
        if func is None:
            continue
        py = inspect.getsource(func)
        js_has = {k for k in keys if k in js}
        py_has = {k for k in keys if k in py}
        if js_has != py_has:
            drift[wid] = {"jsOnly": sorted(js_has - py_has), "pythonOnly": sorted(py_has - js_has)}
    assert not drift, f"dataShape field drift between JS and Python: {drift}"
