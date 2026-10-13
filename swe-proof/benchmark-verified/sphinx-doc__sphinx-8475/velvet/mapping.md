# mapping.md — sphinx-doc__sphinx-8475

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3ea1ec84cc610f7a9f4f6b354e264565254923ff`, states the type
abstraction (the bijection G-AX and G-CONF use to bridge Lean↔Python), and gives
the provenance of the modeled failure hierarchy.

Repo file under change: `sphinx/builders/linkcheck.py`.
`spec_provenance: cold` (derived from problem_statement + gold patch + repo
source at base_commit only).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveLinkStatus (headProbe getProbe : Probe)` | `check_uri()` — `sphinx/builders/linkcheck.py:129` (the HEAD-then-GET attempt block, lines 168–204) | the modeled changed function: how the two attempts and the failures of the first map to a reported status |
| `Probe` (`reached`/`failed`) | the outcome of one `requests.head`/`requests.get` + `response.raise_for_status()` call (`linkcheck.py:170–174`, `178–180`) | a single attempt at the target: either a response was obtained and accepted (`reached`, recording whether `response.url` equals `req_url`), or it raised (`failed`) |
| `RequestFailure` (`statusError`/`redirectLoop`/`otherFailure`) | the exception raised by `raise_for_status()` / the request — `requests.exceptions.HTTPError`, `requests.exceptions.TooManyRedirects`, or any other `Exception` | the three failure shapes the dispatch distinguishes (mapping.md §3) |
| `LinkStatus` (`working`/`ignored`/`broken`/`redirected`) | the status string the `(status, info, code)` triple carries (`linkcheck.py:181–204`) | the reported link status |
| `classifyReached (sameTarget : Bool)` | `linkcheck.py:192–204`: `working` if `response.url.rstrip('/') == req_url.rstrip('/')`, else `redirected` | classify a reached target by whether its final location is the requested one |
| `classifyUnhandled (e : RequestFailure)` | the top-level `except HTTPError as err: …` / `except Exception as err:` block (`linkcheck.py:181–191`) | classify a failure that was NOT retried and reached the top-level handler |
| `retriable (e : RequestFailure)` | the **inner** `except (HTTPError, TooManyRedirects):` clause membership (`linkcheck.py:175` post-patch) | whether the first attempt's failure triggers the full-fetch retry |

`retriable` is the operation the patch **changes** (it widens the inner catch
set); it is modeled deeply (concrete, an I/R op), not an axiom. `RequestFailure`'s
three-way split is the **unchanged** exception hierarchy of `requests`, modeled
deeply and validated against the real classes by G-AX — an **A-reference**, not a
consumed axiom. There are no consumed axioms.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§3) and G-CONF (§4.1) use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| one attempt's outcome (`response` obtained, or an exception raised) | `Probe` | a returned response ↔ `Probe.reached b`, where `b = (response.url.rstrip('/') == req_url.rstrip('/'))`; a raised exception `ex` ↔ `Probe.failed (classifyEx ex)` (see §3) |
| the raised exception object | `RequestFailure` | `HTTPError` with `err.response.status_code = c` ↔ `RequestFailure.statusError c`; `TooManyRedirects` ↔ `RequestFailure.redirectLoop`; any other `Exception` ↔ `RequestFailure.otherFailure` |
| the reported status string | `LinkStatus` | `'working'` ↔ `.working`; `'ignored'` ↔ `.ignored`; `'broken'` ↔ `.broken`; `'redirected'` ↔ `.redirected` |
| `response.url` vs `req_url` (trailing `/` ignored) | `sameTarget : Bool` | `True` (equal) ↔ `true`; `False` ↔ `false` |
| the inner catch-set membership test (`except (...)`) | `retriable : RequestFailure → Bool` | `isinstance(ex, (HTTPError, TooManyRedirects))` ↔ `retriable (classifyEx ex)` |

`status_code` values the dispatch reads explicitly are `401` (→ `working`) and
`503` (→ `ignored`); every other status code is `broken` (only the *equality
classes* 401 / 503 / other matter, so the `Nat` carrier loses no observed
distinction). The anchor branch (`linkcheck.py:166–168`, `requests.get` only,
when `anchor and linkcheck_anchors`) and the auth/header plumbing are unchanged
by the patch and not part of the modeled HEAD-then-GET dispatch; they are elided
(identity) per the carrier.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 The failure hierarchy `RequestFailure` ↔ `requests.exceptions` (A-reference)

**Callees (unchanged by the patch):** the exception classes
`requests.exceptions.HTTPError` and `requests.exceptions.TooManyRedirects`, and
the dispatch primitive `isinstance`. The patch's only edit is to widen the inner
`except HTTPError` to `except (HTTPError, TooManyRedirects)` (`linkcheck.py:175`)
and add `TooManyRedirects` to the import (`linkcheck.py:23`).

The single soundness-critical fact the model encodes is the **class topology**:

* `TooManyRedirects` is **not** a subclass of `HTTPError` (and vice versa); both
  derive from `requests.exceptions.RequestException` (→ `IOError`/`OSError` →
  `Exception`).

Therefore, pre-patch, a HEAD attempt that exhausts the redirect budget raises
`TooManyRedirects`, which the inner `except HTTPError` does **not** catch; the
exception escapes the retry and is caught only by the top-level
`except Exception as err: return 'broken', …` — modeled as
`retriable .redirectLoop = false` (pre-image) so the failure flows to
`classifyUnhandled .redirectLoop = .broken`. Post-patch the inner clause catches
it, so the full-fetch retry runs — modeled as `retriable .redirectLoop = true`.

`classifyUnhandled` encodes the top-level handler's status reading:
`HTTPError` with `status_code == 401 → 'working'`, `== 503 → 'ignored'`, else
`'broken'`; `TooManyRedirects` and any other `Exception` are not `HTTPError`, so
they fall to `except Exception → 'broken'`.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`requests.exceptions` (the same classes the patched module imports, in-container)
and asserts, by executing real `isinstance` / `raise … except` dispatch over the
boundary classes plus fuzzed status codes:
* `TooManyRedirects` is **not** caught by `except HTTPError`, but **is** caught by
  `except (HTTPError, TooManyRedirects)` — i.e. `retriable` is faithful to both
  the pre- and post-patch catch sets;
* an `HTTPError` is caught by both, and its `status_code` reads route to
  `working`/`ignored`/`broken` exactly as `classifyUnhandled` says;
* an unrelated `Exception` is caught by neither inner clause and routes to
  `broken` at the top level — matching `retriable .otherFailure = false` and
  `classifyUnhandled .otherFailure = .broken`.
Imports only stdlib + `requests` (present in the instance image). Exit 0 iff
every obligation holds.

## 4. G-CONF — conformance (conf_skip = true)

`conf_skip = true`. See `conformance_check.py` for the full justification. In
short: the impl region's only observable is the reported status of a link, which
`check_uri` produces from the **live outcomes of `requests.head` / `requests.get`
against a real HTTP endpoint** (the F2P test stands up an
`InfiniteRedirectOnHeadHandler` HTTP server and runs the full
`app.builder.build_all()` linkcheck pipeline). There is no DB-/network-free,
input-dependent R/I shadow to fuzz over ≥10⁵ inputs: the discriminating fact is
which `except` clause catches the HEAD attempt's `TooManyRedirects`, which is
exercised only by the live request machinery. The two A-reference legs (the catch
topology and the status-code routing) are carried by `axiom_check.py` (G-AX);
spec-tightness is carried by G-VERIFY + G-DIFF + G-MUT. The (unused) fuzz seed is
pinned at **`8475`** for reproducibility of the stub.
