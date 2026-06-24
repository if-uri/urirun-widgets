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
import re
from typing import Any
from urllib.parse import quote


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


# --- dashboard widgets (mirror of assets/widgets/{attachment,chat-message,artifact-grid,
# widget-card,dashboard}.js). These are NOT service-views — they are rendered explicitly, so
# they live in DASHBOARD_RENDERERS, never in RENDERERS (which must stay in lockstep with the
# JS dispatch map). Each entry takes the parsed `data` payload. ----------------------------
def _file_preview_url(path: Any) -> str:
    return f"/api/file?path={quote(str(path))}" if path else ""


def _is_pdf_attachment(att: dict) -> bool:
    return bool(att and (att.get("kind") == "document-pdf" or str(att.get("path", "")).lower().endswith(".pdf")))


def _is_scanner_frame(att: dict) -> bool:
    if not att:
        return False
    return (att.get("kind") in ("receipt-crop", "image", "camera-scan")
            or str(att.get("uri", "")).startswith("scanner://host/capture/"))


def _attachment_visual_url(att: dict) -> str:
    if "visualPreviewUrl" in att:
        return _text(att.get("visualPreviewUrl"))
    if att.get("previewExists") is False:
        return ""
    meta = att.get("meta") or {}
    disp = _text(meta.get("displayImage") or meta.get("displayPath") or meta.get("previewImage") or meta.get("image") or "")
    return _file_preview_url(disp) if disp else ""


def render_attachment(att: dict) -> str:
    att = att or {}
    meta = att.get("meta") or {}
    ocr = meta.get("ocr") or {}
    is_pdf = _is_pdf_attachment(att)
    file_available = att.get("fileExists") is not False
    kind_class = " attachment-qr" if att.get("kind") == "qr-code" else (" attachment-pdf" if is_pdf else "")
    visual_url = _attachment_visual_url(att) if is_pdf else _text(att.get("previewUrl") or "")
    pdf_url = _text(att.get("previewUrl") or att.get("filePreviewUrl") or "") if is_pdf and file_available else ""
    if is_pdf and pdf_url:
        preview = f'<iframe class="attachment-pdf-frame" src="{esc(pdf_url)}" title="{esc(_basename(att.get("path")))}" loading="lazy"></iframe>'
    elif visual_url:
        preview = f'<img src="{esc(visual_url)}" alt="{esc(_basename(att.get("path")))}" loading="lazy">'
    elif is_pdf:
        preview = f'<div class="attachment-pdf-preview"><span>PDF</span><small>{esc(_basename(att.get("path")))}</small></div>'
    else:
        preview = '<div class="subtle">preview unavailable</div>'
    file_url = _text(att.get("previewUrl") or att.get("filePreviewUrl") or "") if file_available else ""
    open_l = f'<a href="{esc(file_url)}" target="_blank" rel="noreferrer">open</a>' if file_url else ""
    download = f'<a href="{esc(file_url)}" download>download</a>' if file_url else ""
    missing = '<span class="pill down">missing file</span>' if att.get("fileExists") is False else ""
    detail_att = att if file_available else {**att, "previewUrl": "", "filePreviewUrl": ""}
    if ocr.get("ok"):
        ocr_line = f'<div class="subtle">OCR {esc(ocr.get("backend") or "")}: {esc(_text(ocr.get("text"))[:160])}</div>'
    elif ocr.get("error"):
        ocr_line = f'<div class="subtle">OCR: {esc(ocr.get("error"))}</div>'
    else:
        ocr_line = ""
    dims = f'· {meta.get("width")}x{meta.get("height")}' if meta.get("width") and meta.get("height") else ""
    return (f'<div class="attachment{kind_class}">{preview}'
            f'<div class="mono">{esc(_basename(att.get("path")))}</div>'
            f'<div class="subtle">{esc(att.get("kind") or "file")} {dims} {missing}</div>'
            f'<div class="artifact-actions">{open_l}{download}</div>{ocr_line}'
            f'<details><summary>metadata</summary><pre>{_json_pre(detail_att)}</pre></details></div>')


def message_attachments(message: dict) -> list[dict]:
    detail = message.get("detail") or {}
    document = detail.get("document") or {}
    attachments = message.get("attachments")
    if not isinstance(attachments, list):
        attachments = detail.get("attachments") if isinstance(detail.get("attachments"), list) else []
    has_pdf = any(_is_pdf_attachment(a) for a in attachments)
    out = []
    for att in attachments:
        if _is_pdf_attachment(att):
            out.append(att)
        elif has_pdf and _is_scanner_frame(att):
            continue
        elif _is_scanner_frame(att) and not (document.get("ok") and document.get("path")):
            continue
        else:
            out.append(att)
    return out


def render_chat_message(message: dict, selected_ids=()) -> str:
    message = message or {}
    sel = set(selected_ids or ())
    detail = message.get("detail") or {}
    timeline = detail.get("timeline") or []
    lines = "\n".join(f"{'ok' if s.get('ok') else 'fail'} · {s.get('target') or ''} · {s.get('uri')}" for s in timeline)
    attachments = message_attachments(message)
    role = message.get("role") or "system"
    mid = message.get("id")
    checkbox = (f'<input type="checkbox" name="chatMessageSelect" value="{esc(mid)}" '
                f'{"checked" if mid in sel else ""}>') if mid else ""
    delete_btn = f'<button type="button" class="danger" data-chat-delete="{esc(mid)}">Delete</button>' if mid else ""
    copy_md_btn = (f'<button type="button" data-chat-copy-md="{esc(mid)}" '
                   'title="Copy message as Markdown">Copy MD</button>') if mid else ""
    # Re-run the command: only on user messages that carry a prompt (the command text).
    repeat_btn = (f'<button type="button" data-chat-repeat="{esc(mid)}" '
                  'title="Powtorz komende">Repeat</button>') if (mid and role == "user"
                  and str(message.get("content") or "").strip()) else ""
    atts = (f'<div class="attachments">{"".join(render_attachment(a) for a in attachments)}</div>'
            if attachments else "")
    return (f'<div class="message {esc(role)}">'
            f'<div class="message-head"><span class="message-title">{checkbox}<strong>{esc(role)}</strong></span>'
            f'<span class="message-actions"><span class="subtle">{esc(message.get("created_at") or "")}</span>{repeat_btn}{copy_md_btn}{delete_btn}</span></div>'
            f'<div>{esc(message.get("content") or "")}</div>'
            f'{f"<pre>{esc(lines)}</pre>" if lines else ""}{atts}'
            f'{f"<details><summary>URI / JSON</summary><pre>{_json_pre(detail)}</pre></details>" if detail else ""}</div>')


def _artifact_visual_path(item: dict) -> str:
    path = str(item.get("path") or "")
    meta = item.get("meta") or {}
    if path.lower().endswith(".pdf"):
        return _text(meta.get("displayImage") or meta.get("displayPath") or meta.get("previewImage") or meta.get("image") or "")
    return path


def _artifact_visual_url(item: dict) -> str:
    if "previewUrl" in item:
        return _text(item.get("previewUrl"))
    if item.get("previewExists") is False:
        return ""
    return _file_preview_url(_artifact_visual_path(item))


def _is_image(path: str) -> bool:
    return bool(re.search(r"\.(png|jpe?g|webp|gif)$", path or "", re.I))


def artifact_thumb(item: dict) -> str:
    path = str(item.get("path") or "")
    visual = _artifact_visual_path(item)
    url = _artifact_visual_url(item)
    ext = (re.search(r"\.([a-z0-9]+)$", path, re.I) or [None, "file"])[1].lower() if path else "file"
    if path.lower().endswith(".pdf"):
        if url and _is_image(visual):
            return f'<div class="artifact-thumb"><img src="{esc(url)}" alt="{esc(_basename(visual))}" loading="lazy"></div>'
        return f'<div class="artifact-thumb artifact-thumb-pdf"><span>PDF</span><small>{esc(_basename(path))}</small></div>'
    if not url:
        return '<div class="artifact-thumb artifact-thumb-missing">missing<br>file</div>' if path else '<div class="artifact-thumb">uri</div>'
    if _is_image(visual):
        return f'<div class="artifact-thumb"><img src="{esc(url)}" alt="{esc(_basename(visual))}" loading="lazy"></div>'
    return f'<div class="artifact-thumb">{esc(ext)}</div>'


def render_artifact_grid(items: list, selected_ids=()) -> str:
    rows = items if isinstance(items, list) else []
    sel = set(selected_ids or ())
    if not rows:
        return '<div class="item subtle">No artifacts recorded</div>'
    header = ('<div class="artifact-file-row header"><div></div><div>Preview</div><div>File</div>'
              '<div>URI / document</div><div>Created</div></div>')
    out = [header]
    for item in rows:
        meta = item.get("meta") or {}
        doc = (meta.get("document") or {}).get("metadata") or meta.get("detectedDocument") or meta.get("metadata") or {}
        meta_line = " · ".join(_text(x) for x in [doc.get("type") or meta.get("type"), doc.get("date") or meta.get("date"),
                               doc.get("contractor") or doc.get("supplier") or doc.get("category") or meta.get("contractor"),
                               doc.get("amount") or meta.get("amount")] if x)
        iid = _text(item.get("id"))
        path = _text(item.get("path"))
        url = _text(item.get("filePreviewUrl")) if "filePreviewUrl" in item else (
            "" if item.get("fileExists") is False else _file_preview_url(path))
        open_l = f'<a href="{esc(url)}" target="_blank" rel="noreferrer">open</a>' if url else ""
        dl = f'<a href="{esc(url)}" download>download</a>' if url else ""
        missing = '<span class="pill down">missing file</span>' if path and item.get("fileExists") is False else ""
        dup = int(item.get("duplicateCount") or 0)
        dups = f'<span class="pill">{dup} records</span>' if dup > 1 else ""
        out.append(
            f'<div class="artifact-file-row"><div><input type="checkbox" name="artifactSelect" value="{esc(iid)}" '
            f'{"checked" if iid in sel else ""}></div>{artifact_thumb(item)}'
            f'<div><div class="artifact-name"><strong>{esc(_basename(path or item.get("uri") or item.get("id")))}</strong>'
            f'<span class="pill">{esc(item.get("kind") or "artifact")}</span>{dups}{missing}</div>'
            f'<div class="mono">{esc(path or item.get("uri") or "")}</div>'
            f'<div class="artifact-actions">{open_l}{dl}</div></div>'
            f'<div><div class="mono">{esc(item.get("uri") or "")}</div>'
            f'{f"<div class=\"artifact-meta-line\">{esc(meta_line)}</div>" if meta_line else ""}</div>'
            f'<div><div class="subtle">{esc(item.get("created_at") or "")}</div>'
            f'{f"<button type=\"button\" class=\"danger\" data-artifact-delete=\"{esc(iid)}\">Delete</button>" if iid else ""}'
            f'{f"<details><summary>metadata</summary><pre>{_json_pre(meta)}</pre></details>" if item.get("meta") else ""}</div></div>')
    return f'<div class="artifact-file-grid">{"".join(out)}</div>'


def metric(label: str, value: Any, note: Any) -> str:
    return f'<div class="metric"><strong>{esc(_text(value) or 0)}</strong><span>{esc(label)}</span><p class="subtle">{esc(_text(note))}</p></div>'


def render_metrics(summary: dict) -> str:
    summary = summary or {}
    c = summary.get("taskCounts") or {}
    return "".join([
        metric("open tasks", c.get("open") or 0, "planfile"),
        metric("running", c.get("in_progress") or 0, "in progress"),
        metric("blocked", c.get("blocked") or 0, "needs operator"),
        metric("nodes online", summary.get("nodesOnline") or 0, f'{summary.get("nodeCount") or 0} configured'),
        metric("URI processes", summary.get("routeCount") or 0, "mesh routes"),
    ])


def render_tasks(tasks: list) -> str:
    rows = tasks if isinstance(tasks, list) else []
    body = "".join(
        f'<tr><td class="mono">{esc(t.get("id"))}</td>'
        f'<td><strong>{esc(t.get("name"))}</strong><div class="subtle">{esc(_text(t.get("description"))[:120])}</div></td>'
        f'<td><span class="status {esc(t.get("status"))}">{esc(t.get("status"))}</span>'
        f'<div class="subtle">{esc(_text((t.get("execution") or {}).get("state")))}</div></td>'
        f'<td>{esc(_text((t.get("execution") or {}).get("queue")) or "default")}</td>'
        f'<td>{esc(_text(t.get("priority")) or "normal")}</td>'
        f'<td><div class="actions"><button data-action="start" data-id="{esc(t.get("id"))}">Start</button>'
        f'<button data-action="complete" data-id="{esc(t.get("id"))}">Done</button>'
        f'<button class="danger" data-action="block" data-id="{esc(t.get("id"))}">Block</button></div></td></tr>'
        for t in rows)
    return body or '<tr><td colspan="6"><div class="item subtle">No tasks</div></td></tr>'


def render_nodes(nodes: list) -> str:
    rows = nodes if isinstance(nodes, list) else []
    return "".join(
        f'<div class="item"><div><strong>{esc(n.get("name"))}</strong> '
        f'<span class="pill {"up" if n.get("reachable") else "down"}">{"up" if n.get("reachable") else "down"}</span></div>'
        f'<div class="mono">{esc(n.get("url"))}</div>'
        f'<div class="subtle">{len(n.get("routes") or [])} routes{_node_error_suffix(n)}</div></div>'
        for n in rows) or '<div class="item subtle">No nodes configured</div>'


def _node_error_suffix(node: dict) -> str:
    error = (node or {}).get("error")
    return f" · {esc(error)}" if error else ""


def render_routes(routes: list) -> str:
    rows = routes if isinstance(routes, list) else []
    return "".join(
        f'<div class="item"><div class="mono">{esc(r.get("uri"))}</div>'
        f'<div class="subtle">{esc(_text(r.get("node")))} · {esc(_text(r.get("kind")))} · {esc(_text(r.get("adapter")))}</div></div>'
        for r in rows[:30]) or '<div class="item subtle">No routes discovered</div>'


def contact_card(contact: dict, selected_targets=()) -> str:
    sel = set(selected_targets or ())
    pill = "down" if contact.get("reachable") is False else ("up" if contact.get("status") == "running" or contact.get("reachable") else "")
    input_id = "chat-target-" + re.sub(r"[^a-zA-Z0-9_-]", "-", str(contact.get("id") or "target"))
    acts = "".join(filter(None, [
        f'<button type="button" data-contact-action="invoke-uri" data-uri="{esc(contact.get("startUri"))}" data-target="{esc(contact.get("id"))}">Start</button>' if contact.get("startUri") else "",
        f'<button type="button" data-contact-action="invoke-uri" data-uri="{esc(contact.get("restartUri"))}" data-target="{esc(contact.get("id"))}">Restart</button>' if contact.get("restartUri") else "",
        f'<button type="button" data-contact-action="open-url" data-url="{esc(contact.get("url"))}" data-target="{esc(contact.get("id"))}">Open</button>' if contact.get("url") else "",
    ]))
    return (f'<div class="contact-card"><input id="{esc(input_id)}" type="checkbox" name="chatTarget" '
            f'value="{esc(contact.get("id"))}" {"checked" if contact.get("id") in sel else ""} {"disabled" if contact.get("disabled") else ""}>'
            f'<span class="contact-body"><label class="contact-title" for="{esc(input_id)}">{esc(contact.get("label"))}</label>'
            f'<span class="pill {pill}">{esc(contact.get("status") or contact.get("kind"))}</span>'
            f'<span class="contact-meta">{esc(contact.get("url") or contact.get("meta") or "")}</span>'
            f'{f"<span class=\"contact-actions\">{acts}</span>" if acts else ""}</span></div>')


def render_contacts(contacts: list, selected_targets=()) -> str:
    rows = contacts if isinstance(contacts, list) else []
    return "".join(contact_card(c, selected_targets) for c in rows) or '<div class="item subtle">No contacts</div>'


def _service_widget_links(service: dict, view: dict) -> str:
    target = service.get("id") or view.get("target") or view.get("serviceId") or ""
    links = []
    if target:
        links.append(f'<a href="/services/view?target={quote(str(target))}" target="_blank" rel="noreferrer">HTML widget</a>')
        links.append(f'<a href="/services/view.svg?target={quote(str(target))}" target="_blank" rel="noreferrer">SVG</a>')
    if service.get("url"):
        links.append(f'<a href="{esc(service.get("url"))}" target="_blank" rel="noreferrer">open service</a>')
    return f'<div class="artifact-actions">{"".join(links)}</div>' if links else ""


def render_widget_card(service: dict, view: dict | None) -> str:
    service = service or {}
    sv = view or {}
    status = service.get("status") or sv.get("status") or "live"
    target = service.get("id") or sv.get("target") or sv.get("serviceId") or ""
    if view:
        preview = render_service_view(view)
    elif service.get("url"):
        preview = render_iframe({"title": f'{service.get("name") or target or "service"} page', "view": "page",
                                 "data": {"url": service["url"]}})
    else:
        preview = '<div class="stream-card"><div class="subtle">No live view published yet for this service.</div></div>'
    up = "up" if status in ("running", "up", "live") else "down"
    return (f'<div class="widget-card"><div class="stream-head"><div>'
            f'<strong>{esc(service.get("label") or service.get("name") or sv.get("title") or target or "service")}</strong>'
            f'<div class="mono">{esc(target)}</div></div><span class="pill {up}">{esc(status)}</span></div>'
            f'<div class="subtle">{esc(service.get("url") or service.get("bindUrl") or sv.get("updatedAt") or "")}</div>'
            f'{_service_widget_links(service, sv)}<div class="widget-preview">{preview}</div></div>')


# name -> callable(data: dict) -> html. `data` is the parsed JSON payload from the render route.
DASHBOARD_RENDERERS = {
    "attachment": lambda d: render_attachment(d.get("att", d)),
    "chat-message": lambda d: render_chat_message(d.get("message", d), d.get("selectedIds", ())),
    "artifact-grid": lambda d: render_artifact_grid(d.get("items", []), d.get("selectedIds", ())),
    "widget-card": lambda d: render_widget_card(d.get("service", {}), d.get("view")),
    "metrics": lambda d: render_metrics(d.get("summary", d)),
    "task-table": lambda d: render_tasks(d.get("tasks", [])),
    "nodes": lambda d: render_nodes(d.get("nodes", [])),
    "routes": lambda d: render_routes(d.get("routes", [])),
    "contacts": lambda d: render_contacts(d.get("contacts", []), d.get("selectedTargets", ())),
}


# --- server-side SVG card (mirror of host _service_widget_svg / _service_widget_summary) ---
def _service_widget_summary(view: dict) -> dict[str, str]:
    title = str(view.get("title") or view.get("id") or "service view")
    status = str(view.get("status") or "unknown")
    data = view.get("data") if isinstance(view.get("data"), dict) else {}
    streams = data.get("streams") or []
    if streams and isinstance(streams[0], dict):
        stream = streams[0]
        best = stream.get("best") if isinstance(stream.get("best"), dict) else {}
        doc = best.get("detectedDocument") if isinstance(best.get("detectedDocument"), dict) else {}
        parts = [doc.get("type"), doc.get("date"), doc.get("contractor") or doc.get("supplier") or doc.get("category"), doc.get("amount")]
        subtitle = " · ".join(str(p) for p in parts if p) or str(stream.get("seriesId") or "")
        return {"title": title, "status": status, "subtitle": subtitle, "detail": f"{stream.get('count') or 0} frame(s)"}
    return {"title": title, "status": status,
            "subtitle": str(view.get("target") or view.get("serviceId") or ""),
            "detail": str(view.get("updatedAt") or "")}


def render_svg(view: dict, width: int = 720, height: int = 180) -> str:
    """Render a service view as a compact SVG card (badge/email), mirroring the host's
    /services/view.svg endpoint."""
    view = view or {}
    summary = _service_widget_summary(view)
    w = max(320, min(1200, int(width or 720)))
    h = max(120, min(600, int(height or 180)))
    status = summary["status"]
    color = "#34d399" if status in ("accepted", "running") else "#fb7185" if status in ("failed", "rejected", "stopped") else "#aaa49a"
    e = lambda s: esc(s)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{e(summary["title"])}">'
            f'<rect width="100%" height="100%" rx="8" fill="#11100f"/>'
            f'<rect x="10" y="10" width="{w - 20}" height="{h - 20}" rx="8" fill="#13251f" stroke="#2dd4bf" stroke-opacity=".45"/>'
            f'<text x="24" y="42" fill="#f4f1e9" font-family="system-ui, sans-serif" font-size="18" font-weight="700">{e(summary["title"])}</text>'
            f'<rect x="{w - 130}" y="24" width="100" height="28" rx="14" fill="{color}" fill-opacity=".16"/>'
            f'<text x="{w - 80}" y="43" text-anchor="middle" fill="{color}" font-family="system-ui, sans-serif" font-size="13">{e(status)}</text>'
            f'<text x="24" y="78" fill="#f4f1e9" font-family="system-ui, sans-serif" font-size="15">{e(summary["subtitle"])}</text>'
            f'<text x="24" y="108" fill="#aaa49a" font-family="system-ui, sans-serif" font-size="13">{e(summary["detail"])}</text>'
            f'<text x="24" y="{h - 24}" fill="#aaa49a" font-family="ui-monospace, monospace" font-size="11">{e(str(view.get("id") or view.get("target") or ""))}</text>'
            f'</svg>')


__all__ = ["render_service_view", "RENDERERS", "DASHBOARD_RENDERERS", "render_svg", "esc"]
