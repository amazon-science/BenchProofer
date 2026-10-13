# refinement.md — sphinx-doc__sphinx-8269

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `checkFragmentBranch` `do` block, plus the `classify` / `classifyError` /
`isErrorStatus` pure models it computes) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (callee — **A-consumed** where the
proof uses an axiom's `ensures`, **A-reference** where a deep model is validated
== the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the modeled fragment branch, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — the anchor/fragment-checking arm of `check_uri()`

Gold hunk (`sphinx/builders/linkcheck.py:166-169`):
```
                  response = requests.get(req_url, stream=True, config=self.app.config,
                                          auth=auth_info, **kwargs)
+                 response.raise_for_status()
                  found = check_anchor(response, unquote(anchor))
```

The inserted `response.raise_for_status()` validates the response status before
`check_anchor` is consulted; a raised `HTTPError` is caught by the **unchanged**
shared `except HTTPError as err:` handler (`linkcheck.py:186-194`).

| # | Solution.lean impl op (`checkFragmentBranch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `statusCode : Int` | `response.status_code` of the received response | R | HTTP status int ↔ `Int` (mapping.md §2). G-CONF bridges via a real `requests.Response` carrying `status_code`. |
| A2 | param `found : Bool` | `found = check_anchor(response, unquote(anchor))` | R | `check_anchor`'s `bool` ↔ `Bool` (mapping.md §1, §2). `check_anchor` is UNCHANGED; it enters the model only as the input `found`, so no axiom. |
| A3 | `if isErrorStatus statusCode then …` | `response.raise_for_status()` raising `HTTPError`, caught by the shared handler | A-reference | the inserted validator is modeled **deeply** by `isErrorStatus` (4xx/5xx ⇒ error); there is **no consumed axiom**. G-AX (`axiom_check.py`) validates `isErrorStatus == real raise_for_status raises` over the status range. The "route to the status handler on error" control flow is the gold patch's effect (error ⇒ HTTPError ⇒ handler, before `found` is ever used). |
| A4 | `classifyError statusCode` (the 401 / 503 / else dispatch) | the unchanged `except HTTPError as err:` body: `401 → ('working',' - unauthorized',0)`, `503 → ('ignored',str(err),0)`, else `('broken',str(err),0)` | I | identical concrete dispatch, transliterated. The dispatch key is `err.response.status_code`; G-AX confirms that equals the response's `status_code` on every raising status (so the I-leg reads a genuine field). `Detail.unauthorized`/`Detail.httpError` ↔ the `info` strings' sources (mapping.md §2). |
| A5 | the non-error leg: `if found then working/none else broken/anchorNotFound` | on a non-raising response: `found = check_anchor(...)`; `if not found: raise Exception("Anchor '%s' not found")` (→ caught by `except Exception`, non-ssl ⇒ `('broken', str(err), 0)`); else the URL-match leg returns `('working','',0)` | I | identical control flow, transliterated. `found` ⇒ reachable (`working`/`none`); `¬found` ⇒ the fragment-absent notice (`broken`/`anchorNotFound`). The modeled scope is the non-redirected response (mapping.md §3.2); the redirect leg is unchanged and out of scope. |

Discriminating content of the change — on an **error status with the fragment
absent** the post-patch verdict is `broken` / `httpError` (the response-status
message), whereas the pre-patch verdict was `broken` / `anchorNotFound` (the
fragment-absent notice). This lives in the leading `if isErrorStatus statusCode`
guard of `classify` (model) ⇔ the inserted `response.raise_for_status()` (real).
`Solution_prepatch.lean` omits that guard (consults `found` directly) and so
**fails** `out = classify statusCode found` on, e.g., `statusCode = 500,
found = false` (G-DIFF): prepatch ⇒ `broken`/`anchorNotFound`, spec ⇒
`broken`/`httpError`. This is exactly the F2P observation
(`test_raises_for_invalid_status`): a 500 response must report
`500 Server Error …`, not `Anchor 'anchor' not found`.

## B. No consumed axioms

There are no **A-consumed** rows: the only unchanged callee the decision depends
on (the status validator) is modeled deeply (A-reference, A3), and `check_anchor`
is an opaque Bool input (A2), not an axiom. The `classifyError` dispatch and the
found-routing are identical concrete ops (I, A4/A5).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — inserting the
status validation ahead of the fragment check — is modeled by the leading
`if isErrorStatus …` guard (an A-reference deep model of `raise_for_status` plus
identical-op control flow), not hidden behind an axiom about the function under
change.

## D. verify(Solution) ⇒ resolved

`checkFragmentBranch` verifies only if its output equals `classify statusCode
found`, i.e. only if it validates the status FIRST (routing every 4xx/5xx to the
status handler, with the 401/503/else dispatch) and consults `found` ONLY on a
non-error response (A3–A5). By R (`status_code ↔ Int`, `check_anchor bool ↔
Bool`, `info`-source ↔ `Detail`) the verified branch equals the patched
`check_uri` fragment branch on the modeled non-redirected inputs; by G-AX the
deep model `isErrorStatus` equals the real `raise_for_status` raise boundary
(A-reference) and the HTTPError dispatch key is the genuine status code; by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the one audited deep model — and the gold
patch resolves (G-RESOLVE). Trust points are exactly plan §1.1: the A-reference
deep-model soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
