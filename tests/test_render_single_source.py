# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""The widget-render single-source gate: host vendored renderers are tracked + ratcheted.

urirun-widgets is the source of truth for service-view rendering; the host's `render*ServiceView`
(JS) and `service_widget_*` (Python) are a vendored third copy to burn down. The gate flags ONLY
view renderers — never the dashboard controller (node CRUD, chat, polling)."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ci"))
import check_render_single_source as g  # noqa: E402


def _host(tmp_path, js="", widgets_py="", html_py="", controller_js=""):
    h = tmp_path / "host"
    h.mkdir()
    (h / "dashboard.js").write_text(js + "\n" + controller_js)
    (h / "widgets.py").write_text(widgets_py)
    (h / "html_templates.py").write_text(html_py)
    return str(h)


def test_detects_vendored_view_renderers(tmp_path):
    host = _host(tmp_path,
                 js="function renderTableServiceView(v){}\nfunction renderWidgetCard(w){}\n",
                 widgets_py="def select_service_view(x):\n    ...\n",
                 html_py="def service_widget_html(v):\n    return ''\n")
    found = g.vendored_renderers(host)
    names = {n for v in found.values() for n in v}
    assert names == {"renderTableServiceView", "renderWidgetCard",
                     "select_service_view", "service_widget_html"}


def test_ignores_dashboard_controller_renderers(tmp_path):
    """renderNodeCard / renderChatHistory / renderUrlState are operator-app, NOT widget views."""
    host = _host(tmp_path, controller_js=(
        "function renderNodeCard(n){}\nfunction renderChatHistory(){}\n"
        "function renderUrlState(){}\nfunction renderHostConfigRow(){}\n"))
    assert g.vendored_renderers(host) == {}


def test_strict_fails_while_host_still_vendors(tmp_path):
    host = _host(tmp_path, js="function renderServiceView(v){}\n")
    assert g.main([host, "--strict"]) == 1


def test_ratchet_passes_when_no_new_copy(tmp_path, monkeypatch):
    host = _host(tmp_path, js="function renderServiceView(v){}\n")
    bl = tmp_path / "baseline.json"
    bl.write_text('{"known_vendored": ["renderServiceView"]}')
    assert g.main([host, "--baseline", str(bl)]) == 0


def test_ratchet_fails_on_new_copy(tmp_path):
    host = _host(tmp_path, js="function renderServiceView(v){}\nfunction renderGraphServiceView(v){}\n")
    bl = tmp_path / "baseline.json"
    bl.write_text('{"known_vendored": ["renderServiceView"]}')   # the new graph renderer is not allowed
    assert g.main([host, "--baseline", str(bl)]) == 1


def test_ifuri_host_has_no_vendored_widget_renderers_when_sibling_exists():
    host = Path(__file__).resolve().parents[2] / "urirun" / "adapters" / "python" / "urirun" / "host"
    if not host.exists():
        pytest.skip("if-uri monorepo sibling not present")
    assert g.main([str(host), "--strict"]) == 0
