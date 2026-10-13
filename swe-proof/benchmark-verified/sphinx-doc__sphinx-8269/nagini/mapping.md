# mapping.md — sphinx-doc__sphinx-8269

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1e2ccd8f0eca0870cf6f8fce6934e2da8eba9b72`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `sphinx/builders/linkcheck.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `classify_fragment_link(status, fragment_present)` | the fragment-checking branch of the nested `check_uri()` in `CheckExternalLinksBuilder.check_thread` — `sphinx/builders/linkcheck.py:136` (`def check_uri`), specifically the `if anchor and self.app.config.linkcheck_anchors:` block (`:165-172`) together with the shared exception dispatch at `:186-199` | the modeled changed function: the slice that classifies a fragment-bearing link's outcome (the patch adds the transport-status gate inside the `if` block) |
| `raise_on_error_status(status)` *(axiom — A-consumed)* | `requests.models.Response.raise_for_status()` — the bound method called as `response.raise_for_status()`, the line the patch ADDS at `sphinx/builders/linkcheck.py:169` (post-patch); the SAME call already present on the non-fragment path at `:179` and `:185` | the UNCHANGED library routine that raises on an HTTP error status; the patch only adds a new call site to it |
| `is_error_status(status)` | the `if 400 <= self.status_code < 500` / `elif 500 <= self.status_code < 600` ranges inside `raise_for_status` (CPython `requests/models.py`) | pure spec: a status in `[400, 600)` is a transport error |
| `fragment_present` (bool param) | the boolean `found = check_anchor(response, unquote(anchor))` — `sphinx/builders/linkcheck.py:169` (pre-patch) / `:170` (post-patch) | the UNCHANGED document-scanner verdict (whether the `#anchor` is in the body), abstracted to one bit; `check_anchor` (`:62-77`) is not touched by the patch |
| `TransportError` (exception) | `requests.exceptions.HTTPError` — raised by `raise_for_status`, caught by `except HTTPError as err:` at `sphinx/builders/linkcheck.py:186` | the transport error both the fragment and non-fragment paths signal/handle |
| `FragmentAbsent` (exception) | the generic `raise Exception(__("Anchor '%s' not found") % anchor)` at `sphinx/builders/linkcheck.py:172`, caught by the broad `except Exception as err:` at `:195` | the fragment-absent signal (the "Anchor not found" path) |
| `WORKING/FAILED/IGNORED` | the first element of the `(status, info, code)` tuple `check_uri` returns: `'working'` / `'broken'` / `'ignored'` (`:189,192,194,197,199,201`); the model code `FAILED` (1) refines the repo string `'broken'` | pure spec: the status-class codes |
| `DATUM_NONE/DATUM_TRANSPORT/DATUM_FRAGMENT_ABSENT` | the SECOND element `info` of the returned tuple: `''`/`' - unauthorized'` (none-class), `str(err)` of the `HTTPError` (transport), `str(err)` of the generic "Anchor not found" `Exception` (fragment-absent) (`:189-199`) | pure spec: the datum-kind codes distinguishing which error string accompanies a broken result |

The change is a single one-line hunk: `response.raise_for_status()` is added
immediately after `response = requests.get(...)` inside the
`if anchor and self.app.config.linkcheck_anchors:` block (`:169` post-patch).
Everything around it — `check_anchor`, the `Anchor not found` raise, and the
shared `except HTTPError` / `except Exception` dispatch below — is byte-for-byte
unchanged. The non-fragment branch (`:174-185`) already called
`raise_for_status`; the patch brings the fragment branch into line with it.

**Version pin (verify against the worktree, not memory).** At this
`base_commit` (Sphinx **3.3.0**, instance created 2020-10-03) the
`except HTTPError` dispatch consists of EXACTLY the three arms above —
`401 → 'working'`, `503 → 'ignored'`, `else → 'broken', str(err)` — and there
is NO rate-limiting handling anywhere in the tree:
`git grep -E 'limit_rate|rate-limited|next_check|DEFAULT_DELAY' -- sphinx/`
at `1e2ccd8f0eca0870cf6f8fce6934e2da8eba9b72` returns nothing, `check_uri` has
no `429` branch, and `'rate-limited'` is not a status the builder can emit.
A 429 response therefore falls into the `else` arm and returns
`('broken', str(err), 0)` — exactly the model's `(FAILED, DATUM_TRANSPORT)`
(postcondition clause 3). The linkcheck rate-limiting feature
(`limit_rate`, the `'rate-limited'` status, `DEFAULT_DELAY = 60.0`) was added
to `sphinx/builders/linkcheck.py` only in Sphinx **3.4** (Dec 2020) and
POST-DATES this instance; lines `:200-211` here are the redirect handling, not
a 429 branch. Any faithfulness comparison must be made against the checked-out
worktree at `base_commit`, not against a later Sphinx release.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the HTTP status of `response` (`response.status_code`, an `int`) | `status: int` | identity on the integer status code. `is_error_status(status)` ⟺ `raise_for_status` would raise ⟺ `400 <= status_code < 600`. |
| `found = check_anchor(response, unquote(anchor))` (a `bool`) | `fragment_present: bool` | `check_anchor` returns `True` iff the `#anchor` id/name is present in the response body (`AnchorCheckParser`, `:46-59`); abstracted to the single bit. It is UNCHANGED by the patch and inspected only after the (new) status gate, so its verdict is the sole observable. |
| `response.raise_for_status()` returns normally / raises `HTTPError` | `raise_on_error_status(status)` returns normally / raises `TransportError` | the gate's only observable is whether the status is an error: it returns `None` (normal) iff `status_code` is not in `[400,600)`, else raises `HTTPError` (`requests/models.py`, see §3.1). Abstracted by `status`; `HTTPError` ↔ `TransportError`. |
| the returned `(status, info, code)` tuple's class + info-string identity | `Tuple[int, int]` of `(status-class, datum-kind)` codes | the F2P test (`test_raises_for_invalid_status`) observes the written line `[broken] ...: 500 Server Error: Internal Server Error for url: ...` — i.e. status-class `broken` AND that the info string is the HTTP transport error (`str(HTTPError)`), NOT `Anchor 'anchor' not found`. The two info origins are abstracted to `DATUM_TRANSPORT` vs `DATUM_FRAGMENT_ABSENT`; the third tuple element `code` is always `0` on these paths and is not modelled. `raise InvalidURL`-style messages are not behaviour the test inspects beyond which error string appears, captured exactly by the datum-kind code. |
| `raise Exception("Anchor '%s' not found")` / `except Exception` | `raise FragmentAbsent()` / `except FragmentAbsent` | user-defined exception stands in for the builtin `Exception` (a builtin exception in an `Exsures` crashes the Nagini translator); only the raised/not-raised control flow and which datum results is observed. The SSL-ignored sub-case of the broad `except Exception` is outside the modelled slice (no fragment link in the F2P test is an SSL error; `is_ssl_error` is orthogonal to the status gate). |

The `requests`/`HTTPError`/`check_anchor` objects are not Nagini-expressible;
the slice is modelled over `int` + `bool` + the two exception classes, with the
status gate as the one axiomatized callee.

| the fragment branch always delivers its verdict: `raise_for_status` is two range checks + return/raise, `check_anchor` a bounded document scan, each dispatch arm a single `return` — `check_uri` returns (or raises into the shared dispatch) on every input | `Requires(MustTerminate(2))` on `classify_fragment_link`; `Requires(MustTerminate(1))` consumed on the axiomatized gate | total-correctness obligation, no value content: Nagini verifies partial correctness by default, so without it a diverging impl (`while True: pass`) satisfies every postcondition vacuously while its faithful real patch hangs the checker thread and fails the F2P test by timeout (the G-PANEL-1 atk_4 hole). Every `(status, fragment_present)` input remains admissible. |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `raise_on_error_status` ↔ `requests.models.Response.raise_for_status` (A-consumed)

**Callee:** `requests.models.Response.raise_for_status(self)` (CPython package
`requests`, `requests/models.py`). Its body computes an error message and
raises only inside the two range checks:

```python
def raise_for_status(self):
    http_error_msg = ''
    ...
    if 400 <= self.status_code < 500:
        http_error_msg = u'%s Client Error: %s for url: %s' % (...)
    elif 500 <= self.status_code < 600:
        http_error_msg = u'%s Server Error: %s for url: %s' % (...)
    if http_error_msg:
        raise HTTPError(http_error_msg, response=self)
```

So it raises `HTTPError` **exactly** when `400 <= status_code < 600`, and
returns `None` (normal completion) on every other status (`< 400`, e.g. 200/3xx,
or `>= 600`). This is precisely the axiom:

  * `Ensures(status < 400 or status >= 600)` — normal completion ⟹ non-error
    status;
  * `Exsures(TransportError, 400 <= status and status < 600)` — the transport
    error is signalled ⟹ an error status.

This is the WEAKEST contract the proof needs: `classify_fragment_link` never
inspects the error message, it only sequences the status gate before the
document scan and dispatches on the raised/not-raised outcome plus the raw
`status` (for the 401/503 special cases, which it reads directly, not from the
error object). The axiom makes NO claim about the message text or about which
concrete responses carry which status — only the raise/no-raise partition by
range. It is NOT `@Pure` (it is used by control flow / `Exsures`, not inside an
`Ensures` expression).

The new code calls it as `response.raise_for_status()`; `sphinx.util.requests`
is a thin wrapper over the standard `requests` package (`setup.py` pins
`requests>=2.5.0`), so the method under abstraction is the upstream `requests`
one. The patch does not change `raise_for_status`; it only adds a call to it.

**Soundness check (G-AX):** `axiom_check.py` constructs a real
`requests.models.Response` with a chosen `status_code` (boundary values around
the 400 / 500 / 600 range edges, the special 401 / 503, sub-400 and >=600 codes,
plus randomized fuzz over the whole `int` range), calls the real
`raise_for_status()`, and asserts for each that the call raises `HTTPError`
EXACTLY when `400 <= status < 600` and returns normally otherwise — i.e. the
real callee is total over `{error-status → HTTPError, else → None}` with the
range boundary matching the axiom. Imports only the standard-library-style
`requests` package (the very package the patch calls), nothing repo-specific.
Exit 0 iff every observation meets the axiom.

### 3.2 `fragment_present` ↔ `check_anchor(response, anchor)` (R, not an axiom)

`check_anchor` (`sphinx/builders/linkcheck.py:62-77`) feeds the response body to
an `AnchorCheckParser` and returns `True` iff a tag with `id`/`name` equal to
the anchor is found. It is UNCHANGED by the patch and its verdict is abstracted
to the boolean parameter `fragment_present` (a pure branch selector), not
modelled as a `@ContractOnly` axiom: the proof reasons over the abstract bit
directly, so it is an R-refinement of the scanner's verdict, not a consumed
axiom. Its behaviour is therefore not a trust point. (Recorded here for the
G-EQ / refinement audit.)

## G-CONF — differential conformance (`conformance_check.py`)

**Pinned fuzz seed: `SEED = 8269`** (shared with the velvet and lean siblings).
Input count: **100092 = 92 boundary + 100000 seeded fuzz**, every one of them
Requires-satisfying (the only precondition is `MustTerminate(2)`, a
total-correctness obligation with no value content, so every
`(status: int, fragment_present: bool)` pair is admissible — §2, last row).

**Shadow.** `shadow_classify_fragment_link` is the `# impl-start` / `# impl-end`
region of `model.py` copied VERBATIM (that region contains no contract calls —
`Requires` sits in the pre-conditions region — so nothing needed stripping);
the `# pure-start` code helpers copy over with `@Pure` dropped. The one
`@ContractOnly` callee, `raise_on_error_status`, is bodyless in the model, so it
is wired to the REAL callee it axiomatizes (§3.1):
`requests.models.Response.raise_for_status()` invoked on a genuine `Response`
carrying the generated `status_code`, with `HTTPError` translated to
`TransportError`. The `[400,600)` partition is therefore exercised, not assumed.

**Oracle: the real patched function, CALLED.**
`CheckExternalLinksBuilder.check_thread.check_uri` (§1). It is a closure and not
importable by name, so the script locates it structurally with `ast`
(`ClassDef CheckExternalLinksBuilder` → `FunctionDef check_thread` → nested
`FunctionDef check_uri` / `get_request_headers`), lifts its exact source text
from the patched `/testbed/sphinx/builders/linkcheck.py` with
`ast.get_source_segment` (no pattern text hard-coded), and `exec`s that text
with `self`, `uri`, `kwargs` bound to in-process stand-ins. Every executed
statement is the repository's own: the real `check_anchor` scan, the real
`raise Exception(__("Anchor '%s' not found"))`, the real `raise_for_status`
gate, the real three-arm `except HTTPError` dispatch. The ONLY substitution is
the network — the module-global `requests` name is replaced by an object whose
`.get`/`.head` return a genuine `requests.models.Response`; no classification
logic is replaced. Startup guards abort (never silently pass) unless the
extracted text contains the patch's gate inside the fragment branch AND that
gate precedes the `check_anchor(` call; run without the gold patch the script
exits 1 on that guard.

**Type bridge (§2, inverted).** Forward: `status` is the identity on
`response.status_code`; `fragment_present` becomes a response BODY that does or
does not carry a tag with `id == "anchor"`, so the real `check_anchor` derives
the bit itself. Backward: `(status, info, code)` → `(status-class, datum-kind)`,
with `info` classified by ORIGIN via identity against the strings the two real
sources produce for that very response — the observed `str(HTTPError)` from the
real `raise_for_status`, and the real `__("Anchor '%s' not found") % anchor` —
and `''` / `' - unauthorized'` → `DATUM_NONE`. Any class/info/code outside that
map is reported as a disagreement, never bucketed silently. `response.url` is
held equal to `req_url`: the `'redirected'` sub-case is governed by a dimension
OUTSIDE the modeled input space (refinement.md A7) and is unreachable from any
generated input.

**Boundary coverage.** The F2P shape `(500, fragment absent)` and its
fragment-present twin; both edges of the error window (399/400, 599/600); the
specially-dispatched 401 and 503; 429 (no rate-limit branch exists at this
`base_commit`, §1 version pin); informational / success / redirect statuses;
`0`, negatives and `±10**6`/`10**12` — each crossed with both fragment bits. The
script asserts at the end that all four reachable impl outcomes actually fired
(`(WORKING,NONE)`, `(IGNORED,TRANSPORT)`, `(FAILED,TRANSPORT)`,
`(FAILED,FRAGMENT_ABSENT)`) and fails if any arm was never exercised; the
recorded histogram is `{(0,0): 31417, (1,1): 37449, (1,2): 28380, (2,1): 2846}`.

**Refutation capability (checked, not asserted).** Five mutated shadows were run
against the unmodified oracle and every one exited 1 on a boundary input:
(a) the gate call deleted — the `model_prepatch.py` defect — caught at
`(500, absent)`; (b) the 401 arm returning `(FAILED, TRANSPORT)` — caught at 401;
(c) the general-error arm carrying `DATUM_FRAGMENT_ABSENT` — caught at 500;
(d) the gate paraphrased as `401 <= status < 600` instead of calling the real
method — caught at 400; (e) the 503 arm carrying `DATUM_NONE` — caught at 503.

Exit 0 iff zero disagreements; the final stdout line is a JSON report.
stdlib + the `requests` package (a hard sphinx dependency and the very package
the patch calls).
