"""widget:// connector — the chat-stream HTML widgets (the views chatStreamList renders in
chat-main when scanning), behind a URI. Lists the catalogue, serves single-widget JS, serves
the whole catalogue as one ES module bundle (+ CSS), and renders a view server-side."""
from .core import (WIDGET, bundle_css, bundle_js, get_widget, list_widgets, main, render_svg,
                   render_view, urirun_bindings)
from . import catalog, render
from .render import render_service_view

__all__ = ["WIDGET", "list_widgets", "get_widget", "render_view", "render_svg", "bundle_js",
           "bundle_css", "main", "urirun_bindings", "catalog", "render", "render_service_view"]
