# refinement.md — sphinx-doc__sphinx-8269

Maps every operation in `implementation_classifyLink` to its `patch.diff`
counterpart in the anchor-enabled outcome classification of `check_uri`
(sphinx/builders/linkcheck.py). Tags: **R** type-refinement, **A-consumed** proof
uses a callee axiom, **A-reference** op left as the real repo callee in G-CONF
(not axiomatized), **I** identical concrete op.

## Patch (post-patch anchor branch + the HTTPError dispatch it feeds)
```python
if anchor and self.app.config.linkcheck_anchors:
    response = requests.get(req_url, stream=True, config=self.app.config,
                            auth=auth_info, **kwargs)
    response.raise_for_status()                     # <-- the added statement
    found = check_anchor(response, unquote(anchor))
    if not found:
        raise Exception(__("Anchor '%s' not found") % anchor)
...
except HTTPError as err:
    if err.response.status_code == 401:
        return 'working', ' - unauthorized', 0
    elif err.response.status_code == 503:
        return 'ignored', str(err), 0
    else:
        return 'broken', str(err), 0
```

The single added token is `response.raise_for_status()`. Its effect: an HTTP
error status (`400 ≤ code < 600`) raises `HTTPError` BEFORE `check_anchor` runs,
so the error status — routed through the existing `except HTTPError` dispatch —
settles the outcome, taking precedence over the fragment search.

## Modeling decision
The observable behavior is the `(status, info, code)` triple `check_uri` returns
on the anchor-enabled path. It is a function of:

- `statusCode` — the reply's HTTP status (the value `raise_for_status` inspects);
- `anchorFound` — whether the fragment is present (`check_anchor` result);
- the explanatory messages `httpErrMsg` (`str(err)`) and `anchorErrMsg`
  (`"Anchor '…' not found"`);
- `onSuccess` — the outcome of the unchanged success/redirect tail.

The fix's operation (`raise_for_status` + the `except HTTPError` routing) is the
thing that changed, so it is modeled DEEPLY: the `400 ≤ statusCode < 600` raise
threshold and the `401 → working / 503 → ignored / else → broken` dispatch are
spelled out in the impl. The messages and the success outcome are kept as
arbitrary inputs so the spec pins only WHICH observation governs and which
message/outcome each branch routes through — exactly the bug. No callee is
axiomatized: `check_anchor` and `raise_for_status` are not consumed as opaque
contracts; their behaviors enter as inputs (`anchorFound`) or are modeled deeply
(the raise threshold + dispatch).

## Operation correspondence
| # | Lean op (`implementation_classifyLink`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if 400 ≤ statusCode ∧ statusCode < 600 then …` | `response.raise_for_status()` raising `HTTPError` for any status in `[400,600)`, caught by `except HTTPError` | R | models the added statement's effect deeply: `requests`' `raise_for_status` raises exactly for `400 ≤ code < 600`. `statusCode:Nat ↔ response.status_code:int`. |
| 2 | `if statusCode = 401 then return ⟨"working"," - unauthorized",0⟩` | `if err.response.status_code == 401: return 'working',' - unauthorized',0` | I | identical literal triple. |
| 3 | `if statusCode = 503 then return ⟨"ignored", httpErrMsg, 0⟩` | `elif … == 503: return 'ignored', str(err), 0` | R | `httpErrMsg:String ↔ str(err):str`; status label/code identical. |
| 4 | `return ⟨"broken", httpErrMsg, 0⟩` (other error codes) | `else: return 'broken', str(err), 0` | R | `httpErrMsg ↔ str(err)`. |
| 5 | `if anchorFound = false then return ⟨"broken", anchorErrMsg, 0⟩` | `found = check_anchor(...)`; `if not found: raise Exception("Anchor '…' not found")` → caught by `except Exception` → `return 'broken', str(err), 0` | R | reached ONLY when status is not an error (op 1 false). `anchorFound:Bool ↔ found:bool`; `anchorErrMsg:String ↔ str(err) = "Anchor '…' not found"`. (`is_ssl_error` is false for this constructed message, so the `except Exception` else-arm fires.) |
| 6 | `return onSuccess` | the unchanged success/redirect tail (`if response.url… == req_url…: return 'working','',0` / `redirected …`) reached when status fine and fragment found | A-reference | the unchanged downstream continuation; left abstract (`onSuccess`, universally quantified) — NOT axiomatized, NOT consumed. Bound to the REAL tail's value in G-CONF. |

## R/I legs ⇒ G-CONF
Ops 1–5 (the deeply-modeled raise threshold + HTTPError dispatch + the anchor
branch, all R/I) are the differential-tested content. Op 6 is the A-reference:
`onSuccess` stands for the unchanged success/redirect tail; G-CONF binds it to the
real tail outcome (it does NOT substitute an axiom model). `conf_skip = false`:
the impl region has genuine R/I content (the status-precedence classification is
the fixed behavior), so `conformance_check.py` differential-tests the shadow
against a faithful replica of the patched `check_uri` classification over ≥10^5
fuzzed inputs.

## No A-consumed row
The proof consumes no property of any opaque callee (`onSuccess` is universally
quantified; `raise_for_status`/`check_anchor` enter as the deeply-modeled
threshold and the `anchorFound` input). So `meta.json axioms = []`. Op 6 is an
A-reference solely to document the G-CONF binding to the real success tail; there
is no `opaque`/`axiom` declaration in `Solution.lean`, and `axiom_check.py` is a
skip stub.

## F2P alignment
`test_raises_for_invalid_status` runs `linkcheck` against a local server that
replies `500 Internal Server Error` for a link `http://localhost:7777/#anchor`
(so `linkcheck_anchors=True` and a `#anchor` fragment ⇒ the anchor branch). The
expected output is `[broken] … 500 Server Error: Internal Server Error for url:
…` — i.e. the HTTP-level message, not "Anchor not found". The discriminating
clause is op 1: with `statusCode = 500` (error, not 401/503) the spec pins
`⟨"broken", httpErrMsg, 0⟩`. The prepatch impl never consults the status and
returns `⟨"broken", anchorErrMsg, 0⟩` (fragment absent on the error page) —
wrong message ⇒ `correct_classifyLink` is unclosable on that branch (G-DIFF).
`patch.diff` (gold verbatim) makes the harness resolve.
