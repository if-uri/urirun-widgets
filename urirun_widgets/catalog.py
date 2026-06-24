# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# The widget catalogue: one entry per chat-stream view, naming the `view` keys it handles, the
# standalone JS asset that renders it in the browser, and the shape of `data` it expects. The
# widget:// connector reads this to list/serve widgets, and the Python renderer (render.py)
# mirrors the same set for server-side/headless rendering.

from __future__ import annotations

import os
from typing import Any

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
WIDGETS_DIR = os.path.join(ASSETS_DIR, "widgets")


# id -> definition. `views` are the values a service's `view` field can take to select it.
CATALOG: dict[str, dict[str, Any]] = {
    "scanner-stream": {
        "title": "Scanner stream",
        "views": ["scanner-stream"],
        "asset": "widgets/scanner-stream.js",
        "summary": "Live phone-scanner stream: best candidate, per-frame thumbnails, accept/reject status.",
        "dataShape": {"streams": "[{seriesId,status,count,best,candidates,document,updatedAt,error}]"},
    },
    "scanner-status": {
        "title": "Scanner status",
        "views": ["scanner-status"],
        "asset": "widgets/scanner-status.js",
        "summary": "Phone-scanner service + browser-camera health and recent artifacts.",
        "dataShape": {"service": "{status,url,reachable}", "cameraStatus": "{ready,width,height,track,error}",
                      "recentArtifacts": "[{kind,type,date,previewUrl,...}]"},
    },
    "table": {
        "title": "Table",
        "views": ["table"],
        "asset": "widgets/table.js",
        "summary": "Tabular data; columns inferred from rows or given explicitly.",
        "dataShape": {"rows": "[object]", "columns": "[string|{key}] (optional)"},
    },
    "image": {
        "title": "Image / gallery",
        "views": ["image", "image-list"],
        "asset": "widgets/image.js",
        "summary": "One image or a gallery of images with labels.",
        "dataShape": {"images": "[string|{url|previewUrl|src,label}]", "url": "string (single)"},
    },
    "video": {
        "title": "Video",
        "views": ["video"],
        "asset": "widgets/video.js",
        "summary": "A video/stream player.",
        "dataShape": {"url": "string", "src": "string", "streamUrl": "string"},
    },
    "iframe": {
        "title": "Embedded page",
        "views": ["iframe", "page", "web"],
        "asset": "widgets/iframe.js",
        "summary": "An embedded page in an iframe.",
        "dataShape": {"url": "string", "src": "string", "href": "string"},
    },
    "form": {
        "title": "Form",
        "views": ["form"],
        "asset": "widgets/form.js",
        "summary": "A fillable form that runs an action URI on submit.",
        "dataShape": {"fields": "[{name,label,type,value,checked,readonly}]", "actionUri": "string"},
    },
    "graph": {
        "title": "Graph",
        "views": ["graph"],
        "asset": "widgets/graph.js",
        "summary": "Nodes and edges listing.",
        "dataShape": {"nodes": "[{id|name}]", "edges": "[{from|source,to|target}]"},
    },
    "generic": {
        "title": "Generic (fallback)",
        "views": ["*"],
        "asset": "widgets/generic.js",
        "summary": "Fallback for any view without a dedicated renderer; pretty-prints the data.",
        "dataShape": {"*": "any"},
    },
}

# Order assets are concatenated into the bundle: helpers, every widget, then the dispatcher.
BUNDLE_ORDER = [
    "render-helpers.js",
    "widgets/scanner-status.js",
    "widgets/scanner-stream.js",
    "widgets/table.js",
    "widgets/image.js",
    "widgets/video.js",
    "widgets/iframe.js",
    "widgets/form.js",
    "widgets/graph.js",
    "widgets/generic.js",
    "render.js",
]

# view-key -> catalogue id (so a published `view` resolves to its widget).
VIEW_INDEX: dict[str, str] = {}
for _wid, _spec in CATALOG.items():
    for _v in _spec["views"]:
        VIEW_INDEX[_v] = _wid


def read_asset(rel: str) -> str:
    """Read an asset file relative to the assets dir. Raises FileNotFoundError if missing."""
    path = os.path.normpath(os.path.join(ASSETS_DIR, rel))
    if not path.startswith(ASSETS_DIR):
        raise ValueError(f"asset path escapes assets dir: {rel}")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def widget_for_view(view_key: str) -> str:
    """Return the catalogue id that handles `view_key` (falls back to 'generic')."""
    return VIEW_INDEX.get(view_key, "generic")


__all__ = ["CATALOG", "BUNDLE_ORDER", "VIEW_INDEX", "ASSETS_DIR", "read_asset", "widget_for_view"]
