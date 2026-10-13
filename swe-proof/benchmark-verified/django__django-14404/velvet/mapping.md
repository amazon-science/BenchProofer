# mapping.md — django__django-14404

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = de32fe83a2e4a20887972c69a0693b94eb25a88b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled/deep-modeled construct.

Repo file under change: `django/contrib/admin/sites.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `appendSlashRedirect (mountPrefix) (localPath)` | the redirect-destination expression of `AdminSite.catch_all_view` — `django/contrib/admin/sites.py:430` (inside the `should_append_slash` branch; def at line 420, `path = '%s/' % …` built at line 423, handed to `HttpResponsePermanentRedirect` at line 430) | the modeled changed expression: the value handed to `HttpResponsePermanentRedirect(...)` when an append-slash redirect fires |
| `fullPath (mountPrefix) (localPath)` *(deep model — A-reference)* | `HttpRequest.path` — the request's full externally-visible path. For a WSGI request it is `'%s/%s' % (script_name.rstrip('/'), path_info.replace('/', '', 1))` (`WSGIRequest.__init__`, `django/core/handlers/wsgi.py:75-76`) | pure spec: the request's full path = mount-point prefix ++ local path; deep model of the unchanged framework attribute `request.path`, validated `fullPath == request.path` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `redirectTarget (mountPrefix) (localPath)` | the patched expression `'%s/' % request.path` (`sites.py:430` post-patch) | pure spec: the full path with a single trailing '/' appended |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): `'%s/' % request.path_info` (`sites.py:423,430`) —
appends a slash to the per-request **local** path only, dropping the deployment
mount-point prefix.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§3) and G-CONF (§4) use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF / G-AX disagreements (the falsifiability the plan §4 trust statement
refers to).

The WSGI request computes (`wsgi.py:75-76`), verbatim:

```python
self.path = '%s/%s' % (script_name.rstrip('/'),
                       path_info.replace('/', '', 1))
```

Because `path_info` always begins with a single `/` (`get_path_info` returns it,
falling back to `'/'`, wsgi.py:69,154), `path_info.replace('/', '', 1)` strips
exactly that one leading slash, and the `'%s/%s'` template re-inserts it. Hence
`request.path == script_name.rstrip('/') + path_info`, i.e. the mount-point
prefix immediately followed by the local path.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the deployment mount-point prefix `script_name.rstrip('/')` (`wsgi.py:75`; `script_name` is `FORCE_SCRIPT_NAME` when set, else the WSGI `SCRIPT_NAME` — `get_script_name`, wsgi.py:159-187) | `mountPrefix : List Char` | `script_name.rstrip('/')` (a Python `str`) ↔ `mountPrefix` (its `.toList`-shaped `List Char`); empty `str` (root mount) ↔ `[]`; `str` concat ↔ `List` `++` |
| the per-request local path `request.path_info` (`wsgi.py:71`; always begins with `/`) | `localPath : List Char` | `request.path_info` ↔ `localPath`; the leading-`/` invariant is preserved by the carrier (no separate slash op is modeled because the prefix carries no trailing slash after `rstrip` and the local path carries the joining slash) |
| `request.path` — full externally-visible path (`wsgi.py:75`) | `fullPath mountPrefix localPath = mountPrefix ++ localPath` | the concatenation IS the framework's `'%s/%s' % (prefix, local[1:])` once the leading-slash bookkeeping is discharged (above); validated byte-for-byte by G-AX |
| `'%s/' % request.path` — the patched redirect destination (`sites.py:430`) | `redirectTarget mountPrefix localPath = fullPath … ++ ['/']` | the `'%s/'` template appends exactly one `'/'`; `str` concat ↔ `List` `++` |
| `HttpResponsePermanentRedirect(s)` wrapper (`sites.py:430`) | identity (omitted) | issues a 301 to the string `s`; observationally the identity on the destination string the F2P tests compare (`assertRedirects(..., status_code=301, fetch_redirect_response=False)`) |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the redirect target is a per-character string assembly.

## 3. Deep-model provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `fullPath` deep model ↔ `request.path` (A-reference)
**Callee/attribute:** `HttpRequest.path`, computed for a WSGI request by
`WSGIRequest.__init__` (`django/core/handlers/wsgi.py:75-76`). The changed
expression's destination is modeled **deeply** by `fullPath` (and `redirectTarget`)
in the `pure` region; there is **no consumed axiom**. The model reproduces the
framework's full-path assembly under the type refinement of §2:

  * `request.path == script_name.rstrip('/') + path_info`
    ↔ `fullPath mountPrefix localPath = mountPrefix ++ localPath`,
  * `'%s/' % request.path`
    ↔ `redirectTarget mountPrefix localPath = fullPath … ++ ['/']`.

The single behavioural change the F2P tests observe is that the destination is
assembled from `request.path` (which **includes** the mount-point prefix) rather
than `request.path_info` (which **drops** it); when the application is served
under a non-empty `SCRIPT_NAME` / `FORCE_SCRIPT_NAME`, the pre-patch destination
left the application's mount point and the redirect was wrong.

**Soundness check (G-AX):** `axiom_check.py` builds real WSGI requests (via
`RequestFactory`) over boundary + fuzzed `(script_name, path_info)` pairs,
reads the REAL `request.path`, and asserts it equals
`fullPath(script_name.rstrip('/'), request.path_info)` byte-for-byte, and that
the patched destination `'%s/' % request.path` equals
`redirectTarget(mountPrefix, localPath)`. Imports only `django` (the repo under
test) + stdlib. Exit 0 iff sound.

**Note on the carrier alphabet (G-AX / G-CONF):** the WSGI `environ` round-trips
`SCRIPT_NAME` / `PATH_INFO` through an ISO-8859-1 / UTF-8 byte boundary
(`get_bytes_from_wsgi`, wsgi.py:190-200), so non-ASCII characters cannot survive
a real `RequestFactory` request faithfully. The deep model is a pure
content-agnostic **concatenation**, independent of character identity, so the
ASCII URL-safe fuzz alphabet exercises it completely; the byte boundary is a
property of the WSGI transport, not of the modeled operation.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14404`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `redirectTarget`'s assembly (R/I-tagged ops) to Python and
derives the two carriers from a real `HttpRequest` via the §2 bijection
(`mountPrefix ↔ script_name.rstrip('/')`, `localPath ↔ request.path_info`),
diffing against the patched `'%s/' % request.path` behaviour of the real
`catch_all_view` redirect destination.
