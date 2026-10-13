# mapping.md — sphinx-doc__sphinx-8269

## Instance
- repo: sphinx-doc/sphinx
- base_commit: 1e2ccd8f0eca0870cf6f8fce6934e2da8eba9b72
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`CheckExternalLinksBuilder.check_thread.check_uri` (sphinx/builders/linkcheck.py)
classifies one external link into a `Tuple[str, str, int]` of
`(status, info, code)`. When fragment-level validation is enabled
(`linkcheck_anchors` is true and the URL carries a `#fragment`), the builder
takes the anchor-checking branch (linkcheck.py:165-172 @ base_commit):

```python
if anchor and self.app.config.linkcheck_anchors:
    # Read the whole document and see if #anchor exists
    response = requests.get(req_url, stream=True, config=self.app.config,
                            auth=auth_info, **kwargs)
    found = check_anchor(response, unquote(anchor))
    if not found:
        raise Exception(__("Anchor '%s' not found") % anchor)
```

The reply's HTTP status was never inspected on this branch: a 4xx/5xx error
response would be passed straight to `check_anchor`, the fragment would be absent,
and the link was reported as `broken` with the message `"Anchor '…' not found"` —
masking the real server error. The gold patch inserts one statement so the HTTP
status is consulted FIRST:

```python
     response = requests.get(req_url, stream=True, config=self.app.config,
                             auth=auth_info, **kwargs)
+    response.raise_for_status()
     found = check_anchor(response, unquote(anchor))
```

`response.raise_for_status()` (requests) raises `requests.exceptions.HTTPError`
for any status code in `[400, 600)`. The surrounding `try/except HTTPError`
(linkcheck.py:186-194) then dispatches by status code:

```python
except HTTPError as err:
    if err.response.status_code == 401:
        return 'working', ' - unauthorized', 0
    elif err.response.status_code == 503:
        return 'ignored', str(err), 0
    else:
        return 'broken', str(err), 0
```

So once `raise_for_status()` fires, an error status determines the outcome on its
own — `401 → working`, `503 → ignored`, every other 4xx/5xx → `broken` carrying
the HTTP-level message — and the fragment search never runs. Only a non-error
status reaches `check_anchor`; a missing fragment then yields
`broken / "Anchor '…' not found"`, and a present fragment continues to the
success/redirect classification below.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_classifyLink` | the anchor-enabled outcome classification of `check_uri` (sphinx/builders/linkcheck.py:165-199) — the `if anchor and linkcheck_anchors` branch plus the `except HTTPError` / `except Exception` dispatch it feeds |
| `problem_spec_classifyLink` | the post-condition that classification must satisfy |
| `Outcome` (structure) | the `Tuple[str, str, int]` return type `(status, info, code)` |
| `statusCode` (input) | `response.status_code` of the GET reply (the status `raise_for_status()` inspects) |
| `anchorFound` (input) | `check_anchor(response, unquote(anchor))` — whether the fragment is present |
| `httpErrMsg` (input) | `str(err)` for the raised `HTTPError` (the HTTP-level message) |
| `anchorErrMsg` (input) | `__("Anchor '%s' not found") % anchor` (the fragment-level message) |
| `onSuccess` (input) | the outcome of the unchanged success/redirect continuation reached when the status is fine and the fragment is present (`('working','',0)` / `('redirected',…)`) |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `statusCode : Nat` | `response.status_code : int` (HTTP status, ≥100) | `raise_for_status()` raises iff `400 ≤ code < 600` |
| `anchorFound : Bool` | `found : bool` from `check_anchor` | `true ↔ True` |
| `httpErrMsg : String` | `str(err)` for the `HTTPError` (bytes-for-bytes `str`) | arbitrary message; pinned per-branch |
| `anchorErrMsg : String` | `"Anchor '%s' not found" % anchor` (`str`) | arbitrary message; pinned per-branch |
| `onSuccess : Outcome` | the `(status, info, code)` returned by the unchanged success/redirect tail | arbitrary outcome; deferred to unchanged |
| `Outcome ⟨status, info, code⟩` | `(status: str, info: str, code: int)` | field-wise; `String↔str`, `Int↔int` |
| result `: Outcome` | the `(status, info, code)` triple `check_uri` returns | field-wise bijection |

`String ↔ str` is the byte-for-byte identity; `Int ↔ int` identity.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The fix's new operation
  (`response.raise_for_status()` + the `except HTTPError` status dispatch) is the
  operation the patch changes, so it is modeled DEEPLY in the impl (the
  `400 ≤ code < 600` raise threshold and the 401/503/else routing), NOT
  axiomatized (SPEC_GUIDE §0.7). The two server observations (`status_code`,
  `check_anchor` result) and the explanatory messages / success outcome are
  modeled as arbitrary inputs, so the spec holds for every choice of them and
  pins only WHICH observation governs. There is no `opaque`/`axiom` callee in
  `Solution.lean`; `axiom_check.py` is a skip stub.
- Flag dependency: this classification is reached only when
  `linkcheck_anchors=True` AND the URL has a non-ignored `#fragment` (the branch
  guard `anchor and self.app.config.linkcheck_anchors`). That guard selects the
  branch; it is not a parameter of the modeled outcome function. Recorded so G-AX
  / G-CONF fuzz the anchor-enabled configuration.

## G-CONF fuzz seed
- pinned seed: `8269`
- ≥10^5 fuzzed `(statusCode, anchorFound, httpErrMsg, anchorErrMsg, onSuccess)`
  tuples, with `statusCode` drawn to cover the 4xx/5xx error band (incl. the
  boundaries 399/400/401/503/599/600), the 1xx/2xx/3xx non-error range, and the
  special codes 401 and 503. The oracle is a faithful in-process replica of the
  patched `check_uri` classification (raise_for_status threshold + HTTPError
  dispatch + anchor branch); the shadow is the op-for-op transliteration of
  `implementation_classifyLink`.
