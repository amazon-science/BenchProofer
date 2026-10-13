# mapping.md — sphinx-doc__sphinx-8721

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 82ef497a8c88f0f6e50d84520e7276bfbf65025d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled callee.

Repo file under change: `sphinx/ext/viewcode.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `gatedPageEmission (fmt, ebookOptIn, hasModules, generated)` | `collect_pages(app)` — `sphinx/ext/viewcode.py:180` | the modeled changed function (the `html-collect-pages` generator that yields rendered source pages) |
| `fmt : List Char` | `app.builder.name` — the active builder's `name` attr (e.g. `'html'` `sphinx/builders/html/__init__.py:180`, `'singlehtml'` `sphinx/builders/singlehtml.py:34`, `'epub'` `sphinx/builders/epub3.py:64`) | R: the output-format name as a character sequence |
| `ebookOptIn : Bool` | `env.config.viewcode_enable_epub` — config value (default `False`, registered `sphinx/ext/viewcode.py:281`) | R: the project's opt-in flag for e-book source pages |
| `hasModules : Bool` | `hasattr(env, '_viewcode_modules')` — the early `return` guard at `viewcode.py:181-182` | R: whether any source modules were collected during the build |
| `generated : List Page` | the pages the unchanged emission body `yield`s — the `for modname, entry in status_iterator(...)` loop and the trailing index page (`viewcode.py:189-279`) | I (opaque carrier): the unchanged tail; its internal content is not what the fix changes |
| `isCombinedFormat` (pure) | `app.builder.name == "singlehtml"` (`viewcode.py:185` post-patch) | pure spec: the single-combined-document format test |
| `isEbookFormat` (pure) | `app.builder.name.startswith("epub")` (`viewcode.py:187` post-patch) | pure spec: the e-book-family test |
| `shouldSuppress` (pure) | the pair of inserted early-return guards (`viewcode.py:185-188` post-patch) | pure spec: whether the rendered pages are suppressed |
| `collectedPages` (pure) | the observable result of `collect_pages` (the set of yielded page names) | pure spec: the emitted page list |

**Modeled scope (both inserted guards).** The gold patch adds two guards; this
bundle models both: the single-combined-document guard
(`app.builder.name == "singlehtml": return`) and the e-book opt-in guard
(`startswith("epub") and not viewcode_enable_epub: return`). The e-book guard
is the behaviour the public issue describes and the tests exercise; the
combined-document guard is the other early return of the same hunk, and the
model must include it to stay faithful to the patched `collect_pages` (which
emits nothing under that format). The combined-document clause is absent from
the `problem_statement` (and `hints_text` is empty), so a faithful spec
necessarily discloses it — a proven `problem_statement ↔ gold` mismatch,
dispositioned per spec_guide directive 6 as relaxed leakage
(`RELAXED_LEAKAGE.md`; `meta.json relaxed_leakage = true`,
`gates.G-LEAK.status = "relaxed"`).

No axiomatized callees: `==`, `str.startswith` and `not` are modeled deeply as
`List Char` equality, `List.isPrefixOf` and boolean negation. There is no
unchanged callee whose contract the proof consumes — see refinement.md §C.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `app.builder.name` (a Python `str`) | `fmt : List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `s == "singlehtml"` ↔ `fmt == "singlehtml".toList`; `s.startswith("epub")` ↔ `"epub".toList.isPrefixOf fmt` |
| `env.config.viewcode_enable_epub` (a `bool`) | `ebookOptIn : Bool` | identity on `Bool` |
| `hasattr(env, '_viewcode_modules')` (a `bool`) | `hasModules : Bool` | identity on `Bool`; `True` ↔ modules were collected |
| the yielded `(pagename, context, templatename)` triples | `generated : List Page`, `Page.name : List Char` | the fix observes only WHETHER (and which) pages are emitted; `Page` carries the page name (`pagename`, a posix path str ↔ `List Char`). The context/template payload is unchanged and unobserved by the F2P test (which checks file *existence*), so it is dropped from the carrier. |
| `collect_pages` yields the page sequence | `out : List Page` | `out = []` ↔ the generator yields no pages (no `_modules/...` files written); a non-empty `out` ↔ the same pages the unchanged body produces |

The F2P test `test_viewcode_epub_default` asserts
`not (app.outdir / '_modules/spam/mod1.xhtml').exists()`, i.e. NO source page is
emitted under the default epub build; `test_viewcode_epub_enabled`
(`viewcode_enable_epub=True`) asserts the page IS emitted. Both are exactly the
`out = []` vs `out = generated` distinction `collectedPages` pins. The
combined-document clause is untested by the instance but is refuted mechanically
by G-CONF against the real patched `collect_pages`.

## 3. Callee provenance (no kind-A consumed axioms)

The gating decision is built entirely from operations modeled deeply over the
input carriers:

- **`app.builder.name == "singlehtml"`** — Python `str` equality, modeled as
  `List Char` equality (`isCombinedFormat`). The single-combined-document
  builder's exact name is `'singlehtml'` (`sphinx/builders/singlehtml.py:34`);
  an exact-name test is the faithful recognizer the patch uses.
- **`app.builder.name.startswith("epub")`** — Python `str.startswith`, modeled
  as `List.isPrefixOf` over `List Char` (`isEbookFormat`). The e-book builders
  in this tree all have names beginning `epub` (`epub` / `epub3` share the
  `name = 'epub'` of `Epub3Builder`, `sphinx/builders/epub3.py:64`); a prefix
  test is the faithful family recognizer the patch uses.
- **`not env.config.viewcode_enable_epub`** — boolean negation of the config
  flag, modeled as `!ebookOptIn`.
- **`hasattr(env, '_viewcode_modules')`** — the pre-existing early-return guard,
  unchanged by the patch; modeled as the boolean `hasModules`.

`generated` is an opaque carrier for the unchanged emission body (the
`status_iterator` loop + index page). The fix does not touch how pages are
rendered — only whether the emission runs at all — so the body is tagged **I**
and need not be transliterated; G-CONF holds `fmt`/`ebookOptIn`/`hasModules`
fixed and checks that the patched generator emits something iff the shadow says
`out = generated` (non-empty) and emits nothing iff `out = []`.

There is therefore no `axiom_check.py` for this bundle: no axiom is consumed and
no deep model stands in for an unchanged callee's exact output values. `meta.json`
records `axioms: []` and `G-AX: skip`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8721`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`isCombinedFormat` / `isEbookFormat` / `shouldSuppress` / `collectedPages`
(all R/I-tagged ops) to Python and diffs the *gating decision* (emit-vs-suppress)
against the patched `collect_pages` driven over a corpus of builder names
(`html`, `singlehtml`, `epub`, `epub2`, `epub3`, `latex`, `text`, `dirhtml`,
random strings) crossed with the opt-in flag and the has-modules flag.
