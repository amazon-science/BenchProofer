# refinement.md — django__django-16877

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`escapeEach` `do` block, plus the deep models `escSeq`/`condEscape`/`escapedSeq`)
and `patch.diff` (the gold patch, which ADDS the `escapeseq` filter). Each step is
tagged **R** (type refinement; state the bijection), **A-reference** (a deep model
validated == the real callee by G-AX), or **I** (identical concrete op). There are
no **A-consumed** axioms in this bundle.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §4.1);
the A-reference leg and this narrative are audited by **G-EQ** / G-AX. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The added filter — `escapeseq(value)` (`django/template/defaultfilters.py:447`)

Gold hunk (additions only):
```
+@register.filter(is_safe=True)
+def escapeseq(value):
+    """..."""
+    return [conditional_escape(obj) for obj in value]
```

| # | Solution.lean impl op (`escapeEach`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `items : List Elem` | `value` (an iterable) arg of `escapeseq` | R | `value` ↔ `List Elem`, order-preserving (mapping.md §2). G-CONF bridges element-wise via `obj ↔ ⟨list(str(obj)), hasattr(obj,"__html__")⟩`. |
| A2 | the backward `while` fold building `acc`, one element per step, prepending `condEscape items[i-1]!` | the list comprehension `[ … for obj in value]` (left-to-right, order-preserving) | I | the comprehension and the backward fold both produce the per-element results in input order; the backward loop prepends so the final order matches. Concrete list-building op, transliterated by G-CONF. |
| A3 | `condEscape e = if e.safe then e.chars else escapedSeq e.chars` | `conditional_escape(obj)` | A-reference | the per-element transformation is modeled **deeply**: `condEscape` (with `escapedSeq`/`entity`) IS `conditional_escape` (safe → `__html__()` unchanged; else `html.escape(str(obj))`). No consumed axiom. G-AX validates `condEscape == conditional_escape` over fuzzed safe/non-safe elements (mapping.md §3.1). The `if`, `++`, fold ops are **I** (concrete). |
| A4 | result `out : List (List Char)` returned | the returned `list` | R | the per-element escaped/passthrough results; `mark_safe`/`SafeString` content-identity (mapping.md §2). |

Discriminating content of the change — the per-element conditional: an element
already marked safe is emitted **unchanged**, a non-safe element is HTML-escaped —
lives in `condEscape e = if e.safe then e.chars else escapedSeq e.chars`. This is
the behaviour the F2P tests pin: list `a = ["x&y", "<p>"]` (non-safe) must escape
to `x&amp;y`, `&lt;p&gt;`; list `b = [mark_safe("x&y"), mark_safe("<p>")]` (safe)
must pass through as `x&y`, `<p>`. A wrong impl that escapes unconditionally fails
on `b`; `Solution_prepatch.lean` reproduces exactly that and **fails**
`out = escSeq items` (G-DIFF) — its unsolved goal is
`escapedSeq e.chars = condEscape e`, which is false when `e.safe = true`.

## B. No consumed axioms, no second site

`escapeseq` is a NEW function that calls only the UNCHANGED `conditional_escape`.
There is no urlize/decode site, no callee swap, and no axiom the proof consumes.
The single callee `conditional_escape` is modeled deeply (A-reference), so its
fidelity is a G-AX obligation, not a trusted contract. The `axioms` region of
`Solution.lean` is empty.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The behaviour the patch introduces — escape
each element individually, respecting the per-element safe flag — is modeled
**deeply** (`escSeq` / `condEscape` / `escapedSeq`, all in the `pure` region and
the verified loop), not hidden behind an axiom about the function under spec.

## D. verify(Solution) ⇒ resolved

`escapeEach` verifies only if its output equals `escSeq items` — the element-wise
conditional escape with the per-element safe flag respected (A3) and order
preserved (A2). By R (`value ↔ List Elem`, `obj ↔ ⟨chars, safe⟩`, `mark_safe`/
`str()` content-identities) the verified `escapeEach` equals
`[conditional_escape(obj) for obj in value]` on the tested inputs; by G-AX the deep
model `condEscape` equals the real `conditional_escape` (A-reference, and beneath
it `escapedSeq == html.escape`); by G-CONF the R/I transliteration of the fold
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs (safe and non-safe). Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: callee-model soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
