# mapping.md — sphinx-doc__sphinx-8269

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1e2ccd8f0eca0870cf6f8fce6934e2da8eba9b72`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled / deeply-modeled callee.

Repo file under change: `sphinx/builders/linkcheck.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `checkFragmentBranch (statusCode : Int) (found : Bool)` | the fragment-checking branch of the nested `check_uri()` (`sphinx/builders/linkcheck.py:166-194`) — the `if anchor and self.app.config.linkcheck_anchors:` arm plus the shared `except HTTPError` status handler | the modeled changed function |
| `isErrorStatus (sc : Int)` *(deep model — A-reference)* | `requests.models.Response.raise_for_status()` — `requests/models.py` (called at `linkcheck.py:169` post-patch). Raises `HTTPError` iff `400 <= status_code < 600` | deep model of the unchanged status validator; validated `isErrorStatus == real raise_for_status raises` by axiom_check.py (G-AX) |
| `classifyError (sc : Int)` | the `except HTTPError as err:` handler (`linkcheck.py:186-194`): `401 -> ('working', ' - unauthorized', 0)`, `503 -> ('ignored', str(err), 0)`, else `('broken', str(err), 0)` | the unchanged status-handler (identical-op transliteration) |
| `classify (sc : Int) (found : Bool)` | the post-patch control flow of the fragment branch as a whole | pure spec: the verdict of the fragment branch on a non-redirected response |
| `check_anchor(response, unquote(anchor))` → `found : Bool` | `check_anchor` — `linkcheck.py:62` | the fragment-presence predicate; modeled as the opaque input `found`. UNCHANGED by the patch, observed only as a Bool, so no axiom needed (its result is a method input). |

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): in the `if anchor and ... linkcheck_anchors:` arm the
response status was **not** validated before `check_anchor` was consulted, so a
response carrying an error status with the fragment absent produced
`raise Exception(__("Anchor '%s' not found") % anchor)` (→ `('broken',
"Anchor '…' not found", 0)`) instead of the `HTTPError` verdict.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `response.status_code` (HTTP status int) | `Int` (`statusCode`) | identity on the integers; the modeled domain is `0 ≤ sc` but the predicate is total over `Int` |
| `check_anchor(response, anchor)` result (`bool`) | `Bool` (`found`) | `True ↔ true`, `False ↔ false` |
| the `(status, info, code)` 3-tuple `check_uri` returns | `Verdict` structure (`status : Status`, `detail : Detail`, `code : Int`) | `status` ↔ the literal `'working'/'broken'/'ignored'/'redirected'`; `detail` ↔ the *provenance* of `info` (`httpError` ↔ `str(HTTPError)`, `anchorNotFound` ↔ `"Anchor '…' not found"`, `unauthorized` ↔ `" - unauthorized"`, `none` ↔ `""`); `code` ↔ the third tuple element |

`Detail` abstracts the human-readable `info` string by its *source* rather than
its exact bytes: the F2P test distinguishes the HTTP-error message from the
fragment-absent message, and those are exactly the two `Detail` constructors the
discriminating clause separates. `code` is `0` on every branch the model
covers (the redirected branch, which alone emits a non-zero code, is outside the
modeled fragment branch — see §3).

## 3. Modeled scope & callee provenance

### 3.1 `isErrorStatus` deep model ↔ `Response.raise_for_status()` (A-reference)
**Callee:** `requests.models.Response.raise_for_status()`. The patch inserts a
call to this validator into the fragment-checking arm. Its behaviour is modeled
**deeply** by `isErrorStatus` (4xx/5xx ⇒ error), so there is **no consumed
axiom** about it. Source (vendored `requests` in the instance image):

```python
def raise_for_status(self):
    http_error_msg = ""
    if 400 <= self.status_code < 500:
        http_error_msg = "%s Client Error: %s for url: %s" % (...)
    elif 500 <= self.status_code < 600:
        http_error_msg = "%s Server Error: %s for url: %s" % (...)
    if http_error_msg:
        raise HTTPError(http_error_msg, response=self)
```

So `raise_for_status()` raises `HTTPError` iff `400 <= status_code < 600`, which
is exactly `isErrorStatus`. G-AX (`axiom_check.py`) runs the real
`raise_for_status` over the full status range + fuzz and asserts the
raises/no-raise boundary equals `isErrorStatus`.

### 3.2 Scope: which arm, and what is held opaque
The modeled `classify` covers the **non-redirected** outcomes of the
fragment-checking arm: the response was received (no connection/SSL exception),
`check_anchor` produced a Bool `found`, and the response URL matched the request
URL (no redirect). Under these conditions the verdict is a total function of
`(statusCode, found)`. The redirect leg (`response.url != req_url`), the
connection-error leg (`is_ssl_error` / generic `Exception`), and the
HEAD/GET-retry leg of the *non*-anchor branch are outside the modeled fragment
branch and are not claimed by the spec; they are unchanged by the patch.
`check_anchor` itself is unchanged and enters the model only as the `found`
input (no axiom).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8269`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the entire impl region (`isErrorStatus`, `classifyError`, the
nested-`if` control flow — all R/I-tagged ops) to Python and compares against
`patch.diff`'s behaviour, driving the patched `check_uri` fragment branch
through a stub `requests` response so the real `raise_for_status` /
`check_anchor` boundary is exercised end-to-end.
