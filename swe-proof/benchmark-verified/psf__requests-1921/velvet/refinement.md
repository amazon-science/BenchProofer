# refinement.md — psf__requests-1921

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `effectiveCollection` `do` block together with the deep `effective` /
`combined` / `combinedSeq` model in the `pure` region) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses the axiom's `ensures`,
**A-reference** where a deep model is validated == the real op by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg and this narrative are audited by **G-EQ**. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The combine-and-drop site — `merge_setting` (`requests/sessions.py:34`)

Gold hunk (dict-merge branch):
```
      for (k, v) in request_setting.items():
          if v is None:
              del merged_setting[k]
+
+     merged_setting = dict((k, v) for (k, v) in merged_setting.items() if v is not None)
+
      return merged_setting
```

| # | Solution.lean impl op (`effectiveCollection` / `pure`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `session request : List Int` over key positions `0 .. n-1` | `session_setting`, `request_setting` dicts (Mapping branch) | R | dict ↔ `List Int` indexed by key position; "key absent" ↔ value `absent`(=0) (mapping.md §2). Only the per-key value mapping is observed by the tested behaviour. |
| A2 | `effective sv rv = if rv ≠ absent then rv else sv` (the `if rv ≠ absent then rv else sv` loop branch) | building `merged` from the per-session collection then overlaying the per-request collection so the per-request value wins on shared keys (`sessions.py:54-55`) | R | overlay/precedence merge ↔ `effective`; absence on one side ↔ `absent` there. The order/representation coercions on the way in are value-mapping-preserving (mapping.md §2; G-CONF drives the real callees). |
| A3 | `combined sv rv = if effective sv rv = noneVal then absent else effective sv rv`, applied element-wise by `combinedSeq` (the `if ev = noneVal then absent else ev` loop branch building `result`) | the gold final pass dropping EVERY key whose merged value is the unset value (`sessions.py:62`, post-patch) | A-reference | the changed combine-and-drop op is modeled **deeply**: `effective` / `combined` / `combinedSeq` (spelled out in the `pure` region) and the verified loop ARE the precedence merge plus the all-sides unset-drop. No consumed axiom — the proof depends on none. The deep model is validated **== the real op** out-of-band: G-CONF / G-AX drive the real combine-and-drop and assert `combined == real op` per key, including that a per-session-side unset value is dropped exactly when the gold drop runs (mapping.md §3.1). |
| A4 | `result` returned (`List Int`, no position holding `noneVal` — postcondition `∀ x ∈ out, x ≠ noneVal`, proven by `combinedSeq_mem_ne_noneVal`) | `return merged_setting` (no key mapping to the unset value) | R | dict ↔ `List Int`; a position holding `absent` ↔ the key absent from the returned collection; a position holding a real value ↔ that key present with that value. The F2P test observes only that the dropped key is absent. |

Discriminating content of the change — drop a key whose **effective** value
(after precedence) is the unset value **regardless of which side contributed
it** — lives in `combined` keying off `effective sv rv` (the post-merge value)
rather than off `rv` (the per-request value). The pre-image behaviour dropped a
key only when the per-request value was the unset value;
`Solution_prepatch.lean` reproduces that (the loop branch keys off
`rv = noneVal` instead of `ev = noneVal`) and **fails** the loop invariant
`result = combinedSeq (session.drop i) (request.drop i)` — which propagates to
the postcondition `out = combinedSeq session request` (G-DIFF). On the key with
`rv = absent` and `sv = noneVal` the buggy skeleton yields `noneVal` whereas
`combined` requires `absent`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely *changed*
— the drop of every key whose effective value is the unset value — is modeled
**deeply** (the spelled-out per-key `combined` consumed by the verified loop,
step A3, an **A-reference**), not hidden behind an axiom about the function
under change: there is no consumed axiom. The only out-of-band trust point is
the A-reference G-CONF / G-AX validate (`combined` == the real combine-and-drop).

## C. verify(Solution) ⇒ resolved

`effectiveCollection` verifies only if its output equals, per key, the
precedence merge with every unset-valued key dropped (A3) — in particular no
result position holds `noneVal` (postcondition `∀ x ∈ out, x ≠ noneVal`). By R
(dict ↔ `List Int` over key positions; `absent` ↔ key-absent; the
per-request-wins overlay; the value-mapping-preserving coercions) the verified
result equals the gold combine-and-drop on the tested inputs; by G-CONF the deep
model equals the real op (the A-reference). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited A-reference — and the gold patch resolves (G-RESOLVE). The trust points
are exactly A-reference soundness (G-CONF / G-AX) and refinement fidelity (this
document, G-EQ).
