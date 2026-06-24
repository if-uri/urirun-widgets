# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Server-side mirror of the chat-stream widgets. The JS assets are the browser source of truth
# (loaded into chatStreamList); this is the same dispatch in Python so a widget can be rendered
# headless — for an email digest, an SVG snapshot, a test, or any surface without a DOM. The
# template strings here track the JS one-to-one; keep the two in step when a widget changes.

from __future__ import annotations

import html
import json
from typing import Any


def esc(value: Any) -> str:
    """HTML-escape like the JS `esc` (quotes included)."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _basename(path: Any) -> str:
    p = _text(path)
    if not p:
        return ""
    parts = [seg for seg in p.replace("\\", "/").split("/") if seg]
    return parts[-1] if parts else p


def _stream_status_class(status: str) -> str:
    if status == "accepted":
        return "up"
    if status in ("rejected", "failed"):
        return "down"
    return "running"


def _stream_doc_label(candidate: dict) -> str:
    doc = (candidate or {}).get("detectedDocument") or {}
    parts = [doc.get("type"), doc.get("date"),
             doc.get("contractor") or doc.get("supplier") or doc.get("category"), doc.get("amount")]
    return " · ".join(esc_none(p) for p in parts if p) or "document candidate"


def esc_none(v: Any) -> str:
    return _text(v)


def _json_pre(obj: Any) -> str:
    return esc(json.dumps(obj, indent=2, ensure_ascii=False))


def _shell(view: dict, body: str) -> str:
    status = view.get("status") or "running"
    return (
        '<div class="stream-card">'
        '<div class="stream-head">'
        f'<strong>{esc(view.get("title") or view.get("id") or "service view")}</strong>'
        f'<span class="pill {_stream_status_class(status)}">{esc(view.get("status") or view.get("kind") or "live")}</span>'
        '</div>'
        '<div class="stream-meta">'
        f'<span class="subtle">{esc(view.get("target") or view.get("serviceId") or "")}</span>'
        f'<span class="subtle">{esc(view.get("updatedAt") or "")}</span>'
        '</div>'
        f'{body}'
        f'<details><summary>URI / JSON</summary><pre>{_json_pre(view)}</pre></details>'
        '</div>'
    )


def render_table(view: dict) -> str:
    data = view.get("data") or {}
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    explicit = data.get("columns") if isinstance(data.get("columns"), list) else []
    if explicit:
        columns = [c if isinstance(c, str) else (c.get("key") or c.get("name") or c.get("label"))
                   for c in explicit]
        columns = [c for c in columns if c]
    else:
        columns = list(dict.fromkeys(k for row in rows for k in (row or {}).keys()))
    if columns:
        head = "".join(f"<th>{esc(c)}</th>" for c in columns)
        body_rows = "".join(
            "<tr>" + "".join(f"<td>{esc(_text((row or {}).get(c)))}</td>" for c in columns) + "</tr>"
            for row in rows)
        table = (f'<div class="service-table-wrap"><table><thead><tr>{head}</tr></thead>'
                 f'<tbody>{body_rows}</tbody></table></div>')
    else:
        table = '<div class="subtle">no rows</div>'
    return _shell(view, table)


def render_image(view: dict) -> str:
    data = view.get("data") or {}
    if isinstance(data.get("images"), list):
        images = data["images"]
    else:
        images = [x for x in [data.get("url") or data.get("previewUrl") or data.get("src")] if x]
    if images:
        frames = []
        for image in images:
            item = {"url": image} if isinstance(image, str) else image
            src = item.get("url") or item.get("previewUrl") or item.get("src") or ""
            label = item.get("label")
            frames.append(
                '<div class="stream-frame">'
                f'<img src="{esc(src)}" alt="{esc(label or view.get("title") or "service image")}" loading="lazy">'
                + (f'<div class="subtle">{esc(label)}</div>' if label else "")
                + '</div>')
        body = f'<div class="stream-frames">{"".join(frames)}</div>'
    else:
        body = '<div class="subtle">no image</div>'
    return _shell(view, body)


def render_video(view: dict) -> str:
    data = view.get("data") or {}
    url = data.get("url") or data.get("src") or data.get("streamUrl")
    body = (f'<video class="service-media" src="{esc(url)}" controls muted playsinline></video>'
            if url else '<div class="subtle">no video stream</div>')
    return _shell(view, body)


def render_iframe(view: dict) -> str:
    data = view.get("data") or {}
    url = data.get("url") or data.get("src") or data.get("href")
    body = (f'<iframe class="service-frame" src="{esc(url)}" title="{esc(view.get("title") or "service page")}" loading="lazy"></iframe>'
            if url else '<div class="subtle">no page url</div>')
    return _shell(view, body)


def render_form(view: dict) -> str:
    data = view.get("data") or {}
    fields = data.get("fields") if isinstance(data.get("fields"), list) else []
    action_uri = data.get("actionUri") or data.get("uri") or view.get("actionUri") or ""
    parts = []
    for field in fields:
        name = field.get("name") or field.get("key") or field.get("label") or "field"
        ftype = field.get("type") or "text"
        value = field.get("value") or field.get("default") or ""
        checked = "checked" if ftype == "checkbox" and (field.get("checked") or value is True or value == "true") else ""
        readonly = "readonly" if field.get("readonly") else ""
        parts.append(
            '<label class="stack">'
            f'<span class="subtle">{esc(field.get("label") or name)}</span>'
            f'<input type="{esc(ftype)}" name="{esc(name)}" value="{esc(value)}" {checked} {readonly}>'
            '</label>')
    inner = "".join(parts) or '<div class="subtle">no fields</div>'
    tail = (f'<div class="mono">{esc(action_uri)}</div><button type="submit">Run URI</button>'
            if action_uri else '<div class="subtle">no action URI</div>')
    body = (f'<form class="service-form-preview" data-service-form data-action-uri="{esc(action_uri)}">'
            f'{inner}{tail}</form>')
    return _shell(view, body)


def render_graph(view: dict) -> str:
    data = view.get("data") or {}
    nodes = data.get("nodes") if isinstance(data.get("nodes"), list) else []
    edges = data.get("edges") if isinstance(data.get("edges"), list) else []
    node_html = "".join(f'<div class="mono">{esc(n.get("id") or n.get("name") or json.dumps(n))}</div>'
                        for n in nodes) or '<div class="subtle">none</div>'
    edge_html = "".join(f'<div class="mono">{esc(e.get("from") or e.get("source") or "")} -&gt; '
                        f'{esc(e.get("to") or e.get("target") or "")}</div>'
                        for e in edges) or '<div class="subtle">none</div>'
    body = (f'<div class="service-graph"><div class="item"><strong>nodes</strong>{node_html}</div>'
            f'<div class="item"><strong>edges</strong>{edge_html}</div></div>')
    return _shell(view, body)


def render_generic(view: dict) -> str:
    data = view.get("data") or {}
    status = view.get("status") or "running"
    return (
        '<div class="stream-card">'
        '<div class="stream-head">'
        f'<strong>{esc(view.get("title") or view.get("id") or "service view")}</strong>'
        f'<span class="pill {_stream_status_class(status)}">{esc(view.get("status") or view.get("kind") or "live")}</span>'
        '</div>'
        '<div class="stream-meta">'
        f'<span class="subtle">{esc(view.get("target") or view.get("serviceId") or "")}</span>'
        f'<span class="subtle">{esc(view.get("updatedAt") or "")}</span>'
        '</div>'
        f'<details open><summary>service data</summary><pre>{_json_pre(data)}</pre></details>'
        '</div>'
    )


def _render_stream_frame(candidate: dict) -> str:
    quality = (candidate or {}).get("quality") or {}
    score = f'{float(quality.get("score") or 0):.1f}'
    preview = (f'<img src="{esc(candidate.get("previewUrl"))}" alt="{esc(_stream_doc_label(candidate))}" loading="lazy">'
               if candidate.get("previewUrl") else "")
    return ('<div class="stream-frame">'
            f'{preview}'
            f'<div class="mono">#{esc(candidate.get("frameIndex") or "")} · {score}</div>'
            f'<div class="subtle">{esc(_stream_doc_label(candidate))}</div>'
            '</div>')


def render_scanner_stream(view: dict) -> str:
    streams = (view.get("data") or {}).get("streams")
    streams = streams if isinstance(streams, list) else []
    title = view.get("title") or "phone scanner stream"
    out = []
    for stream in streams:
        best = stream.get("best") or {}
        quality = best.get("quality") or {}
        document = stream.get("document") or {}
        status = stream.get("status") or "running"
        accepted = status == "accepted" and document.get("path")
        best_score = f'{float(quality.get("score") or 0):.1f}'
        frames = stream.get("candidates") or []
        dl = (f'<div><a href="{esc(document.get("previewUrl") or "")}" download>'
              f'{esc(_basename(document.get("path")))}</a></div>') if accepted else ""
        frames_html = (f'<div class="stream-frames">{"".join(_render_stream_frame(c) for c in frames)}</div>'
                       if frames else "")
        err = f' · {esc(stream.get("error"))}' if stream.get("error") else ""
        out.append(
            '<div class="stream-card">'
            '<div class="stream-head">'
            f'<strong>{esc(title)}</strong>'
            f'<span class="pill {_stream_status_class(status)}">{esc(status)}</span>'
            '</div>'
            '<div class="stream-meta">'
            f'<span class="subtle">{esc(stream.get("seriesId") or "")}</span>'
            f'<span class="subtle">{esc(stream.get("updatedAt") or "")}</span>'
            '</div>'
            f'<div><strong>{esc(_stream_doc_label(best))}</strong></div>'
            f'<div class="subtle">{esc(stream.get("count") or 0)} frame(s) · best score {esc(best_score)}{err}</div>'
            f'{dl}{frames_html}'
            f'<details><summary>URI / JSON</summary><pre>{_json_pre(stream)}</pre></details>'
            '</div>')
    return "".join(out)


def _render_scanner_artifact_frame(item: dict) -> str:
    label = " · ".join(_text(x) for x in [item.get("type"), item.get("date"),
                       item.get("contractor") or item.get("supplier") or item.get("category"),
                       item.get("amount")] if x) or item.get("label") or _basename(item.get("path") or item.get("uri") or "")
    preview = (f'<img src="{esc(item.get("previewUrl"))}" alt="{esc(label)}" loading="lazy">'
               if item.get("previewUrl") else "")
    href = item.get("filePreviewUrl") or item.get("previewUrl") or ""
    open_link = f'<a href="{esc(href)}" target="_blank" rel="noreferrer">open</a>' if href else ""
    return ('<div class="stream-frame">'
            f'{preview}'
            f'<div class="mono">{esc(item.get("kind") or "artifact")}</div>'
            f'<div class="subtle">{esc(label)}</div>'
            f'{open_link}</div>')


def render_scanner_status(view: dict) -> str:
    data = view.get("data") or {}
    service = data.get("service") or {}
    camera = data.get("cameraStatus") or {}
    recent = data.get("recentArtifacts") if isinstance(data.get("recentArtifacts"), list) else []
    ready = "ready" if camera.get("ready") else ("error" if camera.get("ok") is False else "not ready")
    track = camera.get("track") or {}
    cam_err = f'<div class="subtle">{esc(camera.get("error"))}</div>' if camera.get("error") else ""
    frames = (f'<div class="stream-frames">{"".join(_render_scanner_artifact_frame(a) for a in recent)}</div>'
              if recent else '<div class="subtle">No scanner artifacts yet</div>')
    body = (
        '<div class="service-graph">'
        '<div class="item"><strong>service</strong>'
        f'<div><span class="pill {"up" if service.get("reachable") else "down"}">{esc(service.get("status") or "unknown")}</span></div>'
        f'<div class="mono">{esc(service.get("url") or "")}</div></div>'
        '<div class="item"><strong>browser camera</strong>'
        f'<div><span class="pill {"up" if camera.get("ready") else "down"}">{esc(ready)}</span></div>'
        f'<div class="subtle">{esc(camera.get("width") or 0)}x{esc(camera.get("height") or 0)} · {esc(track.get("readyState") or "")}</div>'
        f'<div class="mono">{esc(track.get("label") or camera.get("uri") or "")}</div>'
        f'{cam_err}</div></div>'
        f'{frames}')
    return _shell(view, body)


# view-key -> python renderer. Mirrors WIDGETS in assets/render.js.
RENDERERS = {
    "scanner-status": render_scanner_status,
    "scanner-stream": render_scanner_stream,
    "table": render_table,
    "image": render_image,
    "image-list": render_image,
    "video": render_video,
    "iframe": render_iframe,
    "page": render_iframe,
    "web": render_iframe,
    "form": render_form,
    "graph": render_graph,
}


def render_service_view(view: dict) -> str:
    """Render one view to an HTML string, dispatching on view['view'] (generic fallback)."""
    return RENDERERS.get((view or {}).get("view"), render_generic)(view or {})


__all__ = ["render_service_view", "RENDERERS", "esc"]
