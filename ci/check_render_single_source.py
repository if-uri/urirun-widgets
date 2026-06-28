#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""Single-source gate for WIDGET-VIEW rendering.

`urirun-widgets` is the declared source of truth for how a service view renders (`render.py` +
the `widget://host/bundle/query/{js,css}` catalogue the dashboard loads). But the host still
VENDORS a third copy of the same renderers:

  - `host/dashboard.js`        — the `render*ServiceView` / `renderWidget*` JS family (bundle fallback)
  - `host/widgets.py`          — `select_service_view`, `service_widget_summary`
  - `host/html_templates.py`   — `service_widget_html`, `service_widget_svg`

This is the same anti-pattern the contract gate kills, for UI: one render, defined in two places.
This gate COUNTS widget-VIEW render definitions in the host and RATCHETS them down to zero as the
host finishes consuming the bundle. It does NOT touch the dashboard CONTROLLER (URL state, node CRUD
forms, chat submit, polling, target selection) — those are operator-app behaviour, not a widget view,
and stay in the host. Only the *view* renderers that duplicate `urirun-widgets` are tracked.

  python ci/check_render_single_source.py <host-dir> [--baseline ci/render_baseline.json] [--strict]

`--strict` fails on ANY host-vendored renderer (the goal once the bundle is the only source).
Without `--strict`, it fails only when a NEW renderer appears beyond the baseline (ratchet).
"""
from __future__ import annotations

import json
import os
import re
import sys

# Widget-VIEW renderers only — the ones that duplicate urirun_widgets/render.py.
# (NOT renderNodeCard/renderChatHistory/renderUrlState/… — those are the dashboard controller.)
_JS = re.compile(r"function\s+(render[A-Za-z]*ServiceViews?|renderWidget(?:Card|Dashboard)|renderServiceViewShell)\b")
# Render-owned NAMES the host must never DEFINE (only CONSUME). Policy matches the authoritative
# docs/ARCHITECTURE.md ("host nie powinien definiować render*ServiceView / service_widget_*") and the
# hub-side AST gate (urirun test_widgets): the host delegates through NEUTRAL-named wrappers
# (e.g. `_standalone_service_html` → urirun_widgets.render), so a render-OWNED name in host = a 3rd copy.
# `_?` so an underscore-prefixed alias of a render name is caught too.
_PY = re.compile(r"^def\s+(_?(?:service_widget_html|service_widget_svg|select_service_view|service_widget_summary|render_service_view|render_svg))\b",
                 re.MULTILINE)
_SKIP = ("__pycache__", ".git", "node_modules", "venv", ".venv", "build", "dist")


def _py_vendored(text: str) -> list[str]:
    """Render-owned NAME definitions in host Python. The host must CONSUME urirun-widgets render via a
    neutral-named wrapper, never DEFINE a render-owned name (even one that delegates) — that is the
    third copy's seed. Delegation is fine; reusing the catalogue's name for it is not."""
    return [m.group(1) for m in _PY.finditer(text)]


def vendored_renderers(host_dir: str) -> dict[str, list[str]]:
    """{file: [renderer names]} for every widget-VIEW renderer DEFINED (not delegated) under host_dir."""
    found: dict[str, list[str]] = {}
    for dp, dirs, files in os.walk(host_dir):
        dirs[:] = [d for d in dirs if d not in _SKIP]
        for fn in files:
            if not (fn.endswith(".js") or fn.endswith(".py")):
                continue
            path = os.path.join(dp, fn)
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if fn.endswith(".js"):
                names = [n[0] if isinstance(n, tuple) else n for n in _JS.findall(text)]
            else:
                names = _py_vendored(text)
            if names:
                found[os.path.relpath(path, host_dir)] = sorted(set(names))
    return found


def _baseline(path: "str | None") -> set[str]:
    if not path or not os.path.exists(path):
        return set()
    doc = json.load(open(path))
    return set(doc.get("known_vendored", doc if isinstance(doc, list) else []))


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    bpath = None
    args = []
    i = 0
    rest = [a for a in argv if a != "--strict"]
    while i < len(rest):
        if rest[i] == "--baseline":
            bpath = rest[i + 1]; i += 2
        else:
            args.append(rest[i]); i += 1
    host = args[0] if args else "."

    found = vendored_renderers(host)
    all_names = sorted({n for names in found.values() for n in names})
    known = _baseline(bpath)
    new = [n for n in all_names if n not in known]

    print(f"Źródło prawdy renderu widgetów: urirun-widgets/render.py + widget://host/bundle/query/js")
    print(f"Host wendoruje {len(all_names)} rendererów-widoków w {len(found)} plikach:")
    for f, names in sorted(found.items()):
        print(f"  {f}: {', '.join(names)}")
    print("  → dokończ konsumpcję bundla i SKASUJ te kopie (host konsumuje, nie wendoruje)")

    if strict and all_names:
        print(f"\nSTRICT: {len(all_names)} rendererów wciąż w host — bundle nie jest jedynym źródłem")
        return 1
    if bpath:
        print(f"\nBaseline: {len(known)} znanych kopii ({bpath})")
        if new:
            print(f"NOWE KOPIE renderu w host ({len(new)}): {new} — render widgetu należy do urirun-widgets")
            return 1
        print("  brak nowych kopii względem baseline (ratchet OK; cel: burn-down do 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
