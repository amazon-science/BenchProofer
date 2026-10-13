# mapping.md — django__django-16612

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 55bcbd8d172b689811fae17cde2f09218dd74e9c`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled/deep-modeled construct.

Repo file under change: `django/contrib/admin/sites.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `appendSlashRedirect (encodedPath) (encodedQuery)` | the redirect-destination expression of `AdminSite.catch_all_view` — `django/contrib/admin/sites.py:456` (inside the `should_append_slash` branch, body of `catch_all_view`, def at line 447) | the modeled changed expression: the value handed to `HttpResponsePermanentRedirect(...)` when an append-slash redirect fires |
| `redirectTarget (encodedPath) (encodedQuery)` *(deep model — A-reference)* | `HttpRequest.get_full_path(force_append_slash=True)` → `HttpRequest._get_full_path(self.path, True)` — `django/http/request.py:177,183` | pure spec: the trailing-slash redirect destination; deep model of the unchanged community builder, validated `redirectTarget == get_full_path(force_append_slash=True)` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): `"%s/" % request.path` (`sites.py:456`) — appends a
slash to the bare path and never consults the query string.

Unchanged callees folded into the input carrier by R-refinement (§2): the two
percent-encoders `escape_uri_path` (`django/utils/encoding.py:195`) and
`iri_to_uri` (`django/utils/encoding.py:111`), invoked inside `_get_full_path`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§3) and G-CONF (§4) use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF / G-AX disagreements (the falsifiability the plan §4 trust statement
refers to).

`_get_full_path(path, force_append_slash=True)` (`django/http/request.py:183`)
computes, verbatim:

```python
return "%s%s%s" % (
    escape_uri_path(path),
    "/" if force_append_slash and not path.endswith("/") else "",
    ("?" + iri_to_uri(self.META.get("QUERY_STRING", "")))
    if self.META.get("QUERY_STRING", "") else "",
)
```

| repo reality | Lean carrier | bijection |
|---|---|---|
| `escape_uri_path(path)` — the URL-encoded request path | `encodedPath : List Char` | the **output** of the unchanged path encoder is the carrier: `escape_uri_path(request.path)` (a Python `str`) ↔ `encodedPath` (its `.toList`-shaped `List Char`). The encoder is reused unmodified by both pre- and post-patch surroundings; refining its output into the input is sound because the change never touches the encoder. `str` concat ↔ `List` `++`; empty `str` ↔ `[]`. |
| `iri_to_uri(QUERY_STRING)` — the URL-encoded query string (empty iff `QUERY_STRING` empty; `iri_to_uri("") == ""`) | `encodedQuery : List Char` | the **output** of the unchanged query encoder is the carrier: `iri_to_uri(request.META.get("QUERY_STRING",""))` ↔ `encodedQuery`. `encodedQuery = []` ↔ the request has no query string (the Python guard is `if self.META.get("QUERY_STRING", "")`, and `iri_to_uri("") == ""`, so "encoded query empty" ⇔ "raw query empty"). |
| `"/" if force_append_slash and not path.endswith("/") else ""` | `if encodedPath.getLast? = some '/' then [] else ['/']` | `force_append_slash=True` is fixed at the call site (`catch_all_view` passes it). `path.endswith("/")` ⇔ `encodedPath.getLast? = some '/'`: `escape_uri_path` keeps `/` in its safe set (`safe="/:@&+$,-_.!~*'()"`, `encoding.py:202`), so the encoded path ends in `/` iff the raw path does. |
| `'?'` separator + `HttpResponsePermanentRedirect(...)` wrapper | `'?' :: encodedQuery`; wrapper omitted | the `'?'` literal is identical on both sides. `HttpResponsePermanentRedirect(s)` issues a 301 to the string `s` and is observationally the identity on the destination string the F2P tests compare (`assertRedirects(..., status_code=301)`). |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the redirect target is a per-character string assembly.

## 3. Deep-model provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `redirectTarget` deep model ↔ `get_full_path(force_append_slash=True)` (A-reference)
**Callee:** `HttpRequest.get_full_path(force_append_slash=True)` which delegates
to `_get_full_path(self.path, True)` (`django/http/request.py:177,183`). The
changed expression's destination is modeled **deeply** by `redirectTarget` in
the `pure` region; there is **no consumed axiom**. The model reproduces the
three-component `"%s%s%s"` assembly of `_get_full_path` under the type
refinement of §2:

  * component 1 `escape_uri_path(path)` ↔ `encodedPath` (R, §2),
  * component 2 `"/" if force and not path.endswith("/") else ""`
    ↔ `if encodedPath.getLast? = some '/' then [] else ['/']`,
  * component 3 `("?" + iri_to_uri(QS)) if QS else ""`
    ↔ `if encodedQuery = [] then [] else '?' :: encodedQuery`.

`force_append_slash` is hard-`True` at the modeled call site, so the model fixes
it. The single behavioural change the F2P tests observe is that component 3 — the
preserved query string — is now part of the destination (the pre-patch
`"%s/" % request.path` emitted only `path + "/"`).

**Soundness check (G-AX):** `axiom_check.py` constructs real `HttpRequest`
objects over boundary + fuzzed (path, query-string) pairs, calls the REAL
`request.get_full_path(force_append_slash=True)`, and asserts it equals
`redirectTarget(escape_uri_path(path), iri_to_uri(qs))` byte-for-byte (the deep
model composed with the two real encoders). Imports only `django` (the repo
under test) + stdlib. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16612`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `redirectTarget`'s assembly (R/I-tagged ops) to Python and
bridges the two encoder outputs via the real `escape_uri_path` / `iri_to_uri`
(the §2 bijection), diffing against the patched `get_full_path`-based behaviour
of the real `catch_all_view` redirect destination.
