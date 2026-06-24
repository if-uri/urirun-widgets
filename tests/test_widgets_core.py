"""Offline tests for the widget connector: bindings, catalogue, asset serving, the ES bundle,
and the Python server-side renderer mirroring the chatStreamList views."""
import json
import re

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
    assert "function renderTableServiceView(" in js
    assert "const WIDGETS" in js


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
    # Each known view must render to non-empty HTML on minimal data (catches a renderer
    # that drifted into requiring a field, or one wired to a missing helper).
    for view_key in render.RENDERERS:
        r = c.render_view(view=view_key, data="{}")
        assert r["ok"], f"{view_key} render failed: {r}"
        assert isinstance(r["html"], str) and r["html"].strip(), f"{view_key} produced empty HTML"
