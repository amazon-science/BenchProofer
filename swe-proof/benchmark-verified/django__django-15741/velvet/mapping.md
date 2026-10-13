# mapping.md — django__django-15741

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8c0886b068ba4e224dd78104b93c9638b860b398`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Repo file under change: `django/utils/formats.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `lookupValue (nm : Name)` | `get_format(format_type, lang=None, use_l10n=None)` — `django/utils/formats.py:100` (changed body line 116) | the modeled changed function (format resolver) |
| `Name` carrier (`eager` / `deferred`) | the `format_type` argument: either a concrete `str`, or a **lazy** string proxy (`django.utils.functional.lazy`, e.g. `gettext_lazy("DATE_FORMAT")`) | the input that may arrive deferred |
| `Name.content` | the underlying text the (possibly lazy) `format_type` denotes | the resolved character content of the name |
| `force (nm)` | `str(format_type)` — `django/utils/formats.py:116` (post-patch, the added line) | coercion that forces a lazy proxy to its concrete `str`; identity on an already-concrete `str` |
| `resolveName` *(axiom — A-consumed)* | the downstream resolution of an already-concrete format name to its value: the cache key/`getattr(module, format_type, …)` / `getattr(settings, format_type)` chain in `get_format`'s body (`django/utils/formats.py:117-145`) | unchanged callee: maps a concrete name to its format value |

The pre-patch behavior the change repairs (refinement audit only, not in the
consumer spec view): without the coercion, a lazy `format_type` reaches
`getattr(module, format_type, None)` (`formats.py:131`) / the cache tuple, and
`getattr` raises `TypeError: attribute name must be string` — i.e. a deferred
name cannot be used as a lookup name in its unforced state.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `format_type` argument | `Name` | a concrete `str s` ↔ `Name.eager s.toList`; a lazy proxy denoting text `s` ↔ `Name.deferred s.toList` |
| underlying text content of `format_type` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `str(format_type)` coercion (`formats.py:116`, the added line) | `force : Name → List Char` | `str(proxy)` forces a lazy proxy to its concrete text; `str(s)` is the identity on an existing `str`. `force` is total: it succeeds on both carriers (`eager`/`deferred`), exactly as `str(...)` never raises on a string-like value — this is why the patched function never crashes on a lazy input. |
| `get_format`'s downstream resolution of a concrete name to its format value | `resolveName : List Char → List Char` (A-consumed) | a function of the **resolved name only**: identical resolved content ⇒ identical value (the property the coercion restores). Pins no specific value (directive 7: weakest sufficient contract). |
| the lookup outcome | `Except LookupErr (List Char)` | `Except.ok v` ↔ a successful return of a format value; `Except.error .unresolvedName` ↔ the pre-patch `TypeError` raised when an unforced lazy name reaches the lookup |

`Name` is the abstraction the issue turns on: the same content can arrive eager
or deferred, and the only observable difference pre-patch is that the deferred
carrier crashes the lookup. The carrier of the content is `List Char` because
the lookup name is a per-code-point string used as an attribute name.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolveName` ↔ `get_format`'s downstream name→value resolution (A-consumed)
**Callee:** the resolution body of `get_format` that consumes an *already
concrete* `format_type` — building `cache_key = (format_type, lang)`, the cache
hit/miss, `getattr(module, format_type, None)` over the format modules, and the
`getattr(settings, format_type)` fallback (`django/utils/formats.py:117-145`).
This code is **unchanged** by the patch; the patch only guarantees its input is
a concrete `str`.

The axiom encodes the **weakest** property the spec needs: the resolution is a
function of the resolved name content alone — for two names with the same forced
content it returns the same value. We deliberately pin **no** specific value
(directive 7). This is exactly the property the F2P tests rely on:
`get_format(gettext_lazy("DATE_FORMAT"))` must equal `get_format("DATE_FORMAT")`
because, once forced, the lazy and eager names carry identical content.

**Flag/config dependency:** `get_format`'s resolution depends on language and
`USE_L10N` state, which are held fixed during a lookup; G-AX pins them (a fixed
configured settings + active language) so the observed map is a pure function of
the (resolved) `format_type` content for the comparison it makes.

**Soundness check (G-AX):** the G-AX harness (`gates.gate_ax`) runs
`axiom_check.py` in the instance image at **base_commit WITHOUT applying
patch.diff** (only G-CONF applies the gold patch). So the in-container
`get_format` is the **pre-patch** function — which is correct, because the axiom
`resolveName` and the coercion `force` are about machinery the patch does NOT
change. The script therefore validates, on **concrete `str` inputs only** (it
never feeds a lazy proxy into `get_format` — that would reach through the
*changed* function and reproduce the pre-patch bug, a directive-7 violation):
(a) **force** is total + content-preserving — `str(gettext_lazy(name))` returns a
`str` equal to `name` for an untranslated name (a pure proxy coercion that works
pre-patch); (b) **resolveName well-definedness** — two distinct concrete `str`
objects with equal content resolve to **equal** values and neither raises
(resolution is a function of content, not identity); and (c) the **forced
content** resolves identically to the **eager content** (the composition
`resolveName (force nm)` the spec relies on), again on concrete strings. Over
every entry of `FORMAT_SETTINGS` + non-setting boundary names + 2000 fuzz names.
Imports django (already installed in the instance image) + stdlib. Exit 0 iff
sound. We pin **no** specific returned value (directive 7). The patched
function's own lazy-handling (that `get_format(lazy)` returns the eager value
without raising) is covered by G-RESOLVE/G-GOLD + the harness F2P tests, NOT by
an axiom.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15741`**.

**conf_skip = true.** The impl region of `lookupValue` is, after the R-refinement
`force ↔ str(format_type)`, a single A-consumed callee application
(`resolveName (force nm)`): there is no R/I *computational* content to
transliterate and differentially test against `patch.diff` independently of the
unchanged downstream resolver. The behavior the patch adds — that forcing a
deferred name succeeds and yields content identical to the eager form — is the
A-consumed property, whose soundness is covered by G-AX (axiom_check.py).
`conformance_check.py` therefore exits with `status=skip`.
