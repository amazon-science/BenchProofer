# mapping.md — psf__requests-1142

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 22623bd8c265b78b161542663ee980738441c307`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each callee.

Repo file under change: `requests/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `contentLength (payload : Payload) (carriesBody : Bool)` | `PreparedRequest.prepare_content_length(self, body)` — `requests/models.py:387` | the modeled changed function (decides the announced payload size) |
| `Payload` (`seekable n` / `measurable n` / `absent`) | the three branches the method discriminates `body` into: `hasattr(body,'seek') and hasattr(body,'tell')` (a file-like, queried via `body.seek/tell`), else `body is not None` (an in-memory buffer, sized via `len(body)`), else `body is None` | pure spec: the observable shape of the request payload |
| `carriesBody : Bool` | the projection of `self.method` the patched branch tests: `self.method not in ('GET', 'HEAD')` | pure spec: whether the request method conventionally carries an entity body |
| `announcedSize (p) (carriesBody)` | the value written to `self.headers['Content-Length']`, or its absence | pure spec: the announced size as a whole (`some n` = header value `str(n)`; `none` = no `Content-Length` header attached) |

No axioms: the method calls `body.seek` / `body.tell` / `len(body)` only to
*obtain a size already determined by the payload shape*; that size is carried as
data in the `Payload` carrier (`seekable n` / `measurable n`), so there is no
unchanged callee whose contract must be assumed or read back opaquely. The
membership test `self.method not in ('GET','HEAD')` is a pure boolean over an
in-memory string, modeled directly as `carriesBody`. Hence no `axiom_check.py`;
G-AX skips.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `body` argument, dispatched by the method's branch structure | `Payload` | a `body` with `seek`+`tell` (a file-like object) whose `body.tell()` after `seek(0,2)` is `n` ↔ `seekable n`; a non-`None` `body` without seek/tell whose `len(body)` is `n` ↔ `measurable n`; `body is None` ↔ `absent` |
| the announced size: `self.headers['Content-Length']` value vs its absence | `Option Nat` | the header set to `str(n)` ↔ `some n`; **no** `Content-Length` key present in `self.headers` ↔ `none`. (`Content-Length` is the only header this method ever writes, so "header absent" is observable as `'Content-Length' not in headers`.) |
| `self.method` (already upper-cased at prepare time, `models.py:272`) | `carriesBody : Bool` | `self.method not in ('GET','HEAD')` ↔ `carriesBody = true`; `self.method in ('GET','HEAD')` ↔ `carriesBody = false`. Only this single membership projection of the method is touched; the rest of the method object is irrelevant to the announcement. |

`Payload` records `Nat` sizes because a content length is a non-negative byte
count; Python `body.tell()` / `len(body)` are `>= 0` for the inputs this method
sees. The carrier abstracts away *how* the size is obtained (seek/tell vs len) —
that is unchanged code (the I-bridge, refinement.md §B) — and pins only the
*announcement decision*, which is what the patch changes.

### 2.1 Why `carriesBody`, not `GET`/`HEAD`, in the spec view

The patched discriminator is the set `('GET', 'HEAD')`. The public
`problem_statement` is entirely about *which request methods should not be forced
to carry a `Content-Length` header* ("GET requests shouldn't contain by default
'content-length' header", "most UAs do not send the Content-Length header for GET
requests"). The abstract property the patch keys on — *the request method
conventionally carries no entity body* — is exactly the issue's subject, so it is
PS-derivable and modeled as the boolean `carriesBody` WITHOUT naming the concrete
method tokens. The concrete binding `carriesBody ⟺ method ∉ {GET, HEAD}` lives
here (mapping.md), not in the consumer spec view, so G-LEAK stays clean and no
relaxed-leakage disposition is needed. G-CONF instantiates the binding over BOTH
`GET` and `HEAD` (and body-carrying methods) so the differential exercises the
full tested behavior, including the `HEAD` half of the F2P test.

## 3. Callee provenance (kind-A)

None. This bundle has no axioms and no A-reference deep models: every value the
method announces is determined by the payload shape (carried as `Payload` data)
and one boolean method property (`carriesBody`). There is no unchanged callee
whose contract must be assumed or validated. G-AX skips (`meta.json` records no
axioms; no `axiom_check.py` is shipped).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`1142`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `announcedSize`/the `match` (R/I-tagged ops) to Python and bridges
the payload-shape obtaining of sizes (`seek`/`tell`/`len`, the unchanged I-bridge)
plus the method membership over the real `prepare_content_length`.
