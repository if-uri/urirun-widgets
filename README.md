# urirun-widgets

**Chat-stream HTML widgets** — connector ekosystemu [ifURI / urirun](https://github.com/if-uri/urirun).
Schemat URI: `widget://`

Widoki HTML, które okno czatu (`chat-main`) renderuje w `chatStreamList` podczas skanowania — teraz jako wspólny, adresowany przez URI katalog, zamiast funkcji wklejonych w dashboard hosta. Źródłem prawdy dla przeglądarki są samodzielne moduły ES w `assets/widgets/` (każdy renderuje jeden rodzaj `view`, dokładnie tak jak robi to host). Connector listuje katalog, serwuje JS pojedynczego widgetu, serwuje cały katalog jako jeden import (`bundle`) oraz renderuje widok po stronie serwera (mirror w Pythonie) dla powierzchni bez DOM.

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

## Trasy

- `widget://host/registry/query/list` — katalog widgetów (id, obsługiwane `view`, kształt `data`).
- `widget://host/widget/query/get?name=table` — metadane + źródło ES jednego widgetu (`name` może być też kluczem `view`, np. `page` → `iframe`).
- `widget://host/bundle/query/js` — helpery + wszystkie widgety + dyspozytor `renderServiceView` sklejone w **jeden moduł ES**, do załadowania całego katalogu w `chatStreamList` jednym importem.
- `widget://host/bundle/query/css` — wspólny arkusz stylów (samowystarczalny; zmienne motywu host może nadpisać).
- `widget://host/widget/query/render?view=table` — render widoku do HTML **po stronie serwera** (mirror w Pythonie) dla e-maila/SVG/testów. Podaj `view` + `data` (JSON) albo pełny obiekt widoku w `data`.

### Użycie w chacie

```js
// załaduj cały katalog widgetów z connectora
import { renderServiceView } from 'widget://host/bundle/query/js';
chatStreamList.innerHTML = views.map(renderServiceView).join('');
```

```bash
# render po stronie serwera (headless)
urirun-widget render --view table --data '{"rows":[{"nip":"7781422455","gross":1230.0}]}'
```

## Źródło prawdy a render serwerowy

Moduły JS (`assets/`) to źródło prawdy dla przeglądarki. `render.py` to ich wierny odpowiednik w Pythonie używany przez `widget/query/render` — przy zmianie widgetu aktualizuj oba (test `test_python_and_js_widget_sets_match` pilnuje pokrycia zestawu `view`).

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
