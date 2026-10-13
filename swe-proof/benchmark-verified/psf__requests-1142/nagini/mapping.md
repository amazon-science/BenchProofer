# mapping.md — psf__requests-1142

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 22623bd8c265b78b161542663ee980738441c307`, states the type
abstraction, and records callee provenance. The change touches a single repo
function.

Repo file under change: `requests/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prepare_content_length(headers, method, seekable, stream_len, body_present, body_len)` | `PreparedRequest.prepare_content_length(self, body)` — `requests/models.py:388` | the modeled changed function (announces the body-size header) |
| `headers` (param, `Dict[int,int]`) | `self.headers` — the request's `CaseInsensitiveDict` (`requests/models.py:259`, built fresh in `prepare_headers`, `models.py:324-330`) | the header map mutated in place |
| `size_header()` (key token `0`) | the literal header name `'Content-Length'` (`models.py:389,392,395`) | the body-size header's name |
| `method` (param, `int` token) | `self.method` — the uppercased HTTP verb (`models.py:255,268-272`) | the request method, read-only here |
| `method_get()` / `method_head()` (tokens `1` / `2`) | the literals `'GET'` / `'HEAD'` in `self.method not in ('GET','HEAD')` (post-patch `models.py:395-396`) | the two payload-less methods |
| `seekable`, `stream_len` | `hasattr(body,'seek') and hasattr(body,'tell')`; `body.tell()` after `body.seek(0,2)` (`models.py:390-392`) | seekable-stream branch guard + measured length |
| `body_present`, `body_len` | `body is not None`; `len(body)` (`models.py:394-395`) | non-stream-body branch guard + body length |

The values announced in the header are `str(...)` of integers in the repo
(`str(body.tell())`, `str(len(body))`, `'0'`); the model carries them as the
underlying integers (the `str(...)` is an injective formatting step that the
F2P/P2P tests observe only through equality of the rendered value — see §2).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.headers` (`CaseInsensitiveDict`) | `Dict[int, int]` | a header NAME ↔ an int key token; the body-size header is `size_header()==0`. Membership `'Content-Length' in self.headers` ↔ `size_header() in headers`. The map is observed only through presence-of-key and per-key value, which the int-keyed dict reproduces exactly. The postcondition's whole-map frame (`Forall k != size_header(): membership and value unchanged`) is faithful: the real function's only header write is to `'Content-Length'` (`models.py:389-396` post-patch), so every other header of `self.headers` survives the call untouched. |
| header VALUE `str(n)` | the int `n` | `str` is injective on the announced integers, and the tests compare values by equality (`'Content-Length' not in headers`; `pr.body == 'life=42'` ⇒ a present, equal length). Modeling the value as the int `n` preserves every observed equality/membership. |
| `self.method` (`str`, uppercased) | `int` identity token | `'GET'` ↔ `method_get()`, `'HEAD'` ↔ `method_head()`, any other verb ↔ any other token. The operation tests `method` only by equality against `'GET'`/`'HEAD'`, which the token equalities reproduce. `str` indexing is banned in Nagini, so a token is the faithful carrier. |
| `body` object | `seekable`/`stream_len`/`body_present`/`body_len` | the operation observes `body` ONLY via `hasattr(body,'seek') and hasattr(body,'tell')`, `body.tell()` (after a round-trip seek), `body is not None`, and `len(body)`. Those four observations are lifted to the four parameters. `seekable ⇒ body_present` (a seekable stream is a non-None body) is a precondition. |
| `body.seek(0,2)…tell()…seek(0,0)` | reading `stream_len` | the two seeks restore the stream position; the only value flowing out is `body.tell()`, captured as `stream_len`. No state of `body` is observed afterward, so the seek round-trip is the identity for the purposes of this operation. |

## 3. Callee provenance (kind-A)

None. The changed operation — the guarded announcement of the body-size header —
is modeled **deeply** (spelled out in the impl region): the three branches and
the new method guard are concrete control flow over the lifted observations.
There is no unchanged opaque callee the proof relies on, hence no `@ContractOnly`
axiom and no A-consumed / A-reference row. (`super_len`, called in
`prepare_body` to compute the stream length, is upstream of this function and
its result enters here only as the already-observed `stream_len`; it is not
invoked by `prepare_content_length`.)

`axiom_check.py` therefore contains no axiom-soundness obligation; it instead
re-derives the decision table of the modeled function and checks it against the
behaviour the gold patch produces (a deep-model self-consistency check), so the
G-AX harness has a concrete, stdlib-only oracle to run.
