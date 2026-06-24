"""Offline tests for the widget connector: bindings, catalogue, asset serving, the ES bundle,
and the Python server-side renderer mirroring the chatStreamList views."""
import json

import urirun_widgets.core as c
from urirun_widgets import catalog, render


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
    assert "function renderTableServiceView(" in js
    assert "const WIDGETS" in js


def test_bundle_css_self_contained():
    r = c.bundle_css()
    assert r["ok"] and r["format"] == "css"
    assert ".stream-card" in r["css"] and ":root" in r["css"]


def test_python_and_js_widget_sets_match():
    # The Python renderer and the JS dispatcher must cover the same view keys.
    js = catalog.read_asset("render.js")
    for view_key in render.RENDERERS:
        assert f"'{view_key}'" in js, f"{view_key} missing from JS WIDGETS map"
