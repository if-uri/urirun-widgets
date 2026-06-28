# urirun-widgets

**Chat-stream HTML widgets** — connector ekosystemu [ifURI / urirun](https://github.com/if-uri/urirun).
Schemat URI: `widget://`

Widoki HTML, które okno czatu (`chat-main`) renderuje w `chatStreamList` podczas skanowania — teraz jako wspólny, adresowany przez URI katalog, zamiast funkcji wklejonych w dashboard hosta. Źródłem prawdy dla przeglądarki są samodzielne moduły ES w `assets/widgets/`. Connector listuje katalog, serwuje JS pojedynczego widgetu, serwuje cały katalog jako jeden import (`bundle`) oraz renderuje widok po stronie serwera (mirror w Pythonie) dla powierzchni bez DOM.

The HTML views chatStreamList renders in chat-main when scanning, collected into one URI-addressable catalogue.

## Widgety

| id | obsługuje `view` | plik |
|----|------------------|------|
| `scanner-stream` | `scanner-stream` | `assets/widgets/scanner-stream.js` |
| `scanner-status` | `scanner-status` | `assets/widgets/scanner-status.js` |
| `table` | `table` | `assets/widgets/table.js` |
| `image` | `image`, `image-list` | `assets/widgets/image.js` |
| `video` | `video` | `assets/widgets/video.js` |
| `iframe` | `iframe`, `page`, `web` | `assets/widgets/iframe.js` |
| `form` | `form` | `assets/widgets/form.js` |
| `graph` | `graph` | `assets/widgets/graph.js` |
| `generic` | *(fallback)* | `assets/widgets/generic.js` |

Wspólne helpery: `assets/render-helpers.js` · Dyspozytor `renderServiceView`: `assets/render.js` · Style: `assets/widgets.css`.

Widgety dashboardowe są renderowane jawnie po nazwie, a nie po polu `view`:

| id | użycie | plik |
|----|--------|------|
| `attachment` | pojedynczy załącznik czatu | `assets/widgets/attachment.js` |
| `chat-message` | wiadomość czatu z timeline URI i załącznikami | `assets/widgets/chat-message.js` |
| `artifact-grid` | tabela/grid artefaktów z preview, metadata i akcjami | `assets/widgets/artifact-grid.js` |
| `widget-card` | karta usługi z live view | `assets/widgets/widget-card.js` |
| `metrics`, `task-table`, `nodes`, `routes`, `contacts` | panele dashboardu | `assets/widgets/dashboard.js` |

Dyspozytor dashboardowy: `assets/dashboard-render.js` (`renderDashboardWidget(name, data)`).

## Trasy

- `widget://host/registry/query/list` — katalog widgetów (id, obsługiwane `view`, kształt `data`).
- `widget://host/widget/query/get?name=table` — metadane + źródło ES jednego widgetu (`name` może być też kluczem `view`, np. `page` → `iframe`).
- `widget://host/bundle/query/js` — helpery + wszystkie widgety + dyspozytory `renderServiceView(view)` i `renderDashboardWidget(name, data)` sklejone w **jeden moduł ES**.
- `widget://host/bundle/query/css` — wspólny arkusz stylów (samowystarczalny; zmienne motywu host może nadpisać).
- `widget://host/widget/query/render?view=table` — render widoku do HTML **po stronie serwera** (mirror w Pythonie) dla e-maila/SVG/testów. Podaj `view` + `data` (JSON) albo pełny obiekt widoku w `data`.

### Użycie w chacie

```js
// załaduj cały katalog widgetów z connectora
import { renderServiceView } from 'widget://host/bundle/query/js';
chatStreamList.innerHTML = views.map(renderServiceView).join('');
```

```js
// dashboard: artefakty albo wiadomości czatu po nazwie widgetu
import { renderDashboardWidget } from 'widget://host/bundle/query/js';
artifactFileGrid.innerHTML = renderDashboardWidget('artifact-grid', { items, selectedIds });
```

```bash
# render po stronie serwera (headless)
urirun-widget render --view table --data '{"rows":[{"nip":"7781422455","gross":1230.0}]}'
urirun-widget render --widget artifact-grid --data '{"items":[{"id":"a1","path":"/tmp/FV.pdf"}]}'
```

## Źródło prawdy a render serwerowy

Moduły JS (`assets/`) to źródło prawdy dla przeglądarki. `render.py` to ich wierny odpowiednik w Pythonie używany przez `widget/query/render` — przy zmianie widgetu aktualizuj oba. Testy pilnują osobno pokrycia `view` (`RENDERERS`) i dashboard widgets (`DASHBOARD_RENDERERS`).

### Trzecia kopia: host (do skasowania)

Host (`urirun/host/`) wciąż **wendoruje** te renderery — niewidoczna trzecia kopia, która z umowy
„aktualizuj oba" wypada:

- `dashboard.js` — rodzina `render*ServiceView` / `renderWidget*` (fallback inline; konsumpcja bundla
  `widget://host/bundle/query/js` jest już wpięta przez `loadWidgetBundleViaUri`)
- `widgets.py` — `select_service_view`, `service_widget_summary`
- `html_templates.py` — `service_widget_html`, `service_widget_svg`

**Burn-down (ratchet):** `ci/check_render_single_source.py <host-dir> --baseline ci/render_baseline.json`
liczy te kopie i blokuje NOWE; cel = `--strict` zielony, gdy bundle jest jedynym źródłem. Plan:
(1) `dashboard.js` ładuje bundle i NIC nie renderuje inline; (2) serwer woła `urirun-widgets` `render.py`
zamiast `html_templates.service_widget_*`; (3) skasuj inline'owe renderery hosta; (4) zaciśnij baseline → 0.

**NIE migruje do widgetów:** kontroler dashboardu (`renderNodeCard`, `renderChatHistory`, `renderUrlState`,
formularze CRUD node'ów, submit czatu, polling, wybór targetów) — to app operatora (`urirun-service-chat`),
nie katalog widgetów. Widget renderuje *widok*, nie *prowadzi dashboard*.

## Wymagania

- **python:** `urirun`

## Instalacja (dev)

```bash
pip install -e .
pytest -q
```

## Powiązane

- Rdzeń: [if-uri/urirun](https://github.com/if-uri/urirun)
- Modele danych: [if-uri/urirun-artifacts](https://github.com/if-uri/urirun-artifacts)
- Hub connectorów: [connect.ifuri.com](https://connect.ifuri.com)

---
Kategoria: UI · Słowa kluczowe: widget, html, chat, chatstreamlist, scanner, view, dashboard, ui · Wydawca: if-uri
