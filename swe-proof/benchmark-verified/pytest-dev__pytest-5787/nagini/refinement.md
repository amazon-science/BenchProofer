# refinement.md — pytest-dev__pytest-5787

The operation-by-operation correspondence between `model.py`'s implementation
(the `serialize_chain` and `deserialize_chain` impl regions, and the deep
`copy_link` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This is a **two-site** change — two cooperating functions are modeled, each as
its own contracted function with its own impl region (the per-function regions
repeat). There are correspondingly two independently-fixed behaviours and two
verification-failing `model_prepatch*.py` (one per site).

## A. The serialize site — `_to_json` / `_report_to_json` (`reports.py:154`)

Gold replaces the nested `disassembled_report` (which serialized only the
single outermost `reprtraceback`/`reprcrash`) with `_report_to_json`, whose
`serialize_longrepr` emits a `result["chain"]` carrying EVERY link of an
`ExceptionChainRepr.chain`, in order (`result["chain"] = None` for a
single-stage failure).

| # | model.py impl op (`serialize_chain`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `chain: List[int]` | the failure `report` whose `longrepr` is an `ExceptionChainRepr` with `.chain` a list of links | R | a list of link tuples ↔ `List[int]` of link tokens (mapping.md §2). |
| A2 | the loop `out = out + [chain[i]]` for `i` in `0..len(chain)`, i.e. `out` carries every link in order | `serialize_longrepr`: `result["chain"] = [ (serialize_repr_traceback(tb), serialize_repr_crash(crash), description) for tb,crash,description in rep.longrepr.chain ]` (every link, in order) | A-reference | the changed serialize operation is modeled **deeply**: the verified loop emits one output link per input link, preserving count and order (postcondition `len(Result()) == len(chain)` and the per-index `Forall`). There is no consumed `serialize` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX runs the real `report._to_json()` on chained reports and asserts the emitted chain has the same length and per-link content (mapping.md §3.1). |
| A3 | each emitted link is `copy_link(chain[i])` (the content-preserving copy) | the per-link `serialize_repr_traceback`/`serialize_repr_crash`/`serialize_repr_entry`, which are unchanged `__dict__.copy()` operations | A-reference + I | the per-link copy is content-preserving ⇒ modeled as the identity `copy_link`; it is the UNCHANGED part of the behaviour. G-AX checks each link's reconstructed content (traceback text + description) matches. |

## B. The deserialize site — `_from_json` / `_report_kwargs_from_json` (`reports.py:204`)

Gold replaces the body that always rebuilt a single `ReprExceptionInfo`
(`reprtraceback`, `reprcrash`) with `_report_kwargs_from_json`, which — when
`reportdict["longrepr"]["chain"]` is truthy — rebuilds EVERY link and
constructs `ExceptionChainRepr(chain)` (else `ReprExceptionInfo`).

| # | model.py impl op (`deserialize_chain`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `transport: List[int]` | `reportdict["longrepr"]["chain"]`, a list of serialized links | R | a list of serialized link tuples ↔ `List[int]` of link tokens (mapping.md §2). |
| B2 | the loop `out = out + [transport[i]]` for `i` in `0..len(transport)`, i.e. `out` reproduces every transport link in order | the loop `chain.append((deserialize_repr_traceback(tb), deserialize_repr_crash(crash), description))` over `reportdict["longrepr"]["chain"]`, then `ExceptionChainRepr(chain)` | A-reference | the changed deserialize operation is modeled **deeply**: the verified loop reproduces one output link per transport link, preserving count and order (postcondition `len(Result()) == len(transport)` and the per-index `Forall`). No consumed axiom. G-AX runs the real `report_class._from_json(...)` and asserts the rebuilt chain has the same length and per-link content (mapping.md §3.1). |
| B3 | each reproduced link is `copy_link(transport[i])` (content-preserving) | the per-link `deserialize_repr_traceback`/`deserialize_repr_crash`/`deserialize_repr_entry`, the unchanged reconstruction | A-reference + I | the per-link reconstruction is content-preserving ⇒ identity `copy_link`. |

## C. Composition — the round-trip identity

`deserialize_chain(serialize_chain(chain))` reproduces `chain` exactly (length
and every link), because A2/A3 give `serialize` preserves all links and B2/B3
give `deserialize` reproduces all transport links. This IS the property the F2P
tests demand: `loaded_report.longrepr.chain == report.longrepr.chain` for a
chain of length ≥ 2 (`test_chained_exceptions[TestReport]` and
`[CollectReport]`). The two prepatch skeletons each break exactly one half:

- `model_prepatch.py` (site A): serialize emits only `chain[len(chain)-1]` (the
  outermost link — the pre-patch `disassembled_report` serialized only
  `rep.longrepr.reprtraceback`/`reprcrash`, i.e. `chain[-1]`), so the transport
  form has length 1. It **fails** `len(Result()) == len(chain)` whenever
  `len(chain) >= 2` — exactly the spec sensing the collapse (G-DIFF).
- `model_prepatch_2.py` (site B): deserialize always rebuilds a single link from
  the outermost transport entry (the pre-patch `_from_json` always built one
  `ReprExceptionInfo`), so the rebuilt chain has length 1. It **fails**
  `len(Result()) == len(transport)` whenever `len(transport) >= 2` (G-DIFF).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* — serialize and deserialize of the failure representation — are
modeled **deeply** (the spelled-out, verified per-link loops), not hidden behind
an axiom about the function under change: there is **no consumed `@ContractOnly`
axiom** at all. The only callee the deep model leans on is the per-link
structural copy, which is UNCHANGED and content-preserving, captured as the
identity `copy_link` and audited as an **A-reference** by G-AX.

## E. verify(model) ⇒ resolved

`serialize_chain` verifies only if its output carries every link in order
(A2/A3); `deserialize_chain` verifies only if it reproduces every transport link
in order (B2/B3). By R (link-tuple ↔ token, list order ↔ list order) the
verified loops equal the real `_report_to_json` / `_report_kwargs_from_json` on
the tested chained reports; by G-AX the deep model equals the real callees
(A-reference) over the four F2P-relevant cases. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
