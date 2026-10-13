# refinement.md — django__django-12262

The operation-by-operation correspondence between `model.py`'s implementation
(the `bind_keywords` impl region, with the deep `outcome` / `acceptable` /
`contains` models) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == a real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `parse_bits` keyword-handling branch (`django/template/library.py:258-283`)

Gold hunk (the entire patch):
```
- if param not in params and param not in unhandled_kwargs and varkw is None:
+ if param not in params and param not in kwonly and varkw is None:
```

The modeled function `bind_keywords` is the keyword-binding decision of
`parse_bits`, reduced to its outcome code (0 OK / 1 UNEXPECTED / 2 DUPLICATE).

| # | model.py impl op (`bind_keywords` / `outcome`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `supplied: List[int]` walked front to back | the `for bit in bits:` loop restricted to the `if kwarg:` (keyword) branch; `param` = the extracted keyword's parameter name | R | each kwarg-bit ↔ its `param` name code; `bits` order ↔ `supplied` order (mapping.md §2). The orthogonal positional `else` branch is elided under R (mapping.md §3). |
| A2 | `not acceptable(positional, keyword_only, catch_all, name)` ⇒ return 1 | `if param not in params and param not in kwonly and varkw is None:` ⇒ raise `TemplateSyntaxError("…unexpected keyword argument…")` | R + I | `acceptable` is `catch_all or contains(positional,·) or contains(keyword_only,·)`; its negation is `not catch_all and not (param in params) and not (param in kwonly)` = `param not in params and param not in kwonly and varkw is None` (`varkw is None` ↔ `not catch_all`, mapping.md §2). This is the **fixed** condition (`kwonly`, not `unhandled_kwargs`) — the single content of the patch. Return code 1 ↔ the UNEXPECTED raise. |
| A3 | `contains(seen, name)` ⇒ return 2 | `elif param in kwargs:` ⇒ raise `TemplateSyntaxError("…multiple values for keyword argument…")` | R + I | `seen` ↔ the recorded-`kwargs` keys (mapping.md §2); `contains(seen, name)` ↔ `param in kwargs`. Return code 2 ↔ the DUPLICATE raise. The `elif` ordering (UNEXPECTED checked before DUPLICATE) is mirrored exactly by A2-before-A3. |
| A4 | `seen = seen + PSeq(name)` then continue | `else:` record `kwargs[str(param)] = value` (and consume from `unhandled_params`/`unhandled_kwargs`) | R | recording the keyword ↔ extending `seen`. The bookkeeping of `unhandled_params` / `unhandled_kwargs` removal is post-fix irrelevant to the modeled decision (the fixed condition no longer reads `unhandled_kwargs`); the value stored is never inspected by the pinned behaviour (mapping.md §3). |
| A5 | loop exhausts ⇒ return 0 | the keyword loop completes without raising | R | the OK outcome (code 0). |
| A6 | `Requires(MustTerminate(2))` + loop `Invariant(MustTerminate(len(supplied) - i + 1))` | the real keyword loop is a bounded `for bit in bits:` scan over a finite token list — `parse_bits` always returns or raises | R | totality. Nagini is a partial-correctness verifier by default, so without this obligation a diverging implementation (e.g. `while True: pass` before the scan) satisfies the value postcondition vacuously while its faithful real counterpart hangs template compilation and resolves nothing. The obligation pins the real binder's boundedness; it excludes only non-terminating impls, never a correct one (the measure `len(supplied) - i` strictly decreases and is bounded below). |

The discriminating content of the change — testing membership in the FULL
keyword-only set `kwonly` rather than in the *required* subset `unhandled_kwargs`
— lives in step A2: `contains(keyword_only, name)` (model) ⇔ `param in kwonly`
(real). The pre-patch tested `param not in unhandled_kwargs`, where
`unhandled_kwargs` excludes defaulted keyword-only params and is consumed as
each keyword is bound; `model_prepatch.py` reproduces that exactly
(`still_required = contains(keyword_only, name) and not
contains(keyword_only_with_default, name) and not contains(seen, name)`,
i.e. the live value of `unhandled_kwargs`) and **fails** the postcondition
`Result() == outcome(...)`, which is the spec sensing the change (G-DIFF).

## B. No axioms, no A-reference library callee

The changed operation is a pure membership test in the binder's own control
flow. It is modeled **deeply** (`outcome` / `acceptable` / `contains` in the
`pure` region, consumed by `bind_keywords`); there is **no `@ContractOnly`
axiom** the proof depends on (no A-consumed row), and the deep model does not
stand in for any library callee (no A-reference row in the proof sense). The two
callees the real loop invokes — `token_kwargs` (keyword extraction) and
`parser.compile_filter` (value compilation) — are unchanged and orthogonal to
the pinned decision (they never affect the `param`-membership branch), so they
are elided under the R-refinement of A1/A4, not axiomatized (mapping.md §3).

`axiom_check.py` nonetheless validates the deep `outcome` model **== the real
post-patch `parse_bits` keyword decision** (a faithful transcription, including
the real `unhandled_kwargs` construction/consumption) over an exhaustive small
enumeration + 40 000 fuzz inputs, and confirms the pre-patch differential on
both issue witnesses. This is a deep-model fidelity check (A-reference *against
the real function under change*, not a library callee); it is recorded for audit
but is **not a consumed axiom** — the Nagini proof depends on none.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
membership test in the UNEXPECTED guard — is modeled **deeply** (step A2,
`contains(keyword_only, name)`), spelled out over `PSeq[int]`, not hidden behind
an axiom about the function under change. There is no consumed axiom of any
kind.

## D. verify(model) ⇒ resolved

`bind_keywords` verifies only if its returned outcome equals `outcome(...)`,
i.e. the FIRST problematic keyword is classified as UNEXPECTED iff it names no
declared parameter (positional OR **keyword-only**, regardless of default) with
no catch-all, and as DUPLICATE iff it repeats an already-bound name (A2/A3). By
R (the type bijections of mapping.md §2 — names↔int codes, `varkw is None`↔
`not catch_all`, raises↔outcome codes) the verified decision equals the
post-patch `parse_bits` keyword branch on the tested inputs; G-AX confirms the
deep model equals that real branch over exhaustive + fuzz inputs. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The single trust
point is refinement fidelity (this document, G-EQ); there is no axiom-soundness
trust point because the bundle consumes no axiom.

The F2P tests this transfers to:
- `simple_keyword_only_default kwarg=37` and `inclusion_keyword_only_default
  kwarg=37` — a defaulted keyword-only param supplied once: OK (A2 keeps it
  acceptable because it is in `kwonly`); pre-patch raised UNEXPECTED.
- `simple_keyword_only_param kwarg=42 kwarg=37`, `simple_keyword_only_default
  kwarg=42 kwarg=37`, `inclusion_keyword_only_default kwarg=37 kwarg=42` — a
  keyword-only param supplied twice: DUPLICATE / "received multiple values"
  (A3); pre-patch raised the wrong UNEXPECTED message.
