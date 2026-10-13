# refinement.md — django__django-10880

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`aggregateAsSql` `do` block, plus the deep `renderCall`/`distinctQualifier`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (a deep model validated == the real callee by G-AX),
or **I** (identical concrete op). EVERY step is R, A, or I; there is no kind-3
(changed inexpressible op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `Aggregate.as_sql` (`django/db/models/aggregates.py:71`)

Gold hunk:
```
- extra_context['distinct'] = 'DISTINCT' if self.distinct else ''
+ extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''
```

| # | Solution.lean impl op (`aggregateAsSql`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `function : List Char` | template placeholder `%(function)s` (value `data['function']`, e.g. `'COUNT'`) | R | `str` ↔ `List Char` (mapping.md §3). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | param `distinct : Bool` | `self.distinct` truthiness | R | Python truthy ↔ `true`, falsy ↔ `false` (mapping.md §3); the ctor stores the `bool` arg. |
| A3 | param `expressions : List Char` | template placeholder `%(expressions)s` (rendered, comma-joined arg SQL) | R | `str` ↔ `List Char` (mapping.md §3). The arg SQL is produced by `compiler.compile`, opaque to the distinct behavior. |
| A4 | `qualifier := if distinct then "DISTINCT ".toList else []` (the `distinctQualifier` model) | `extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''` | I | the CHANGED op, modeled DEEPLY and concretely: `"DISTINCT "` (keyword + separator) when deduplicating, `""` otherwise. Transliterated 1:1 by G-CONF. The trailing separator is the entire behavioural change. |
| A5 | `out := function ++ ['('] ++ qualifier ++ expressions ++ [')']` (the `renderCall` model) | `template % data` with `Aggregate.template = '%(function)s(%(distinct)s%(expressions)s)'` in `Func.as_sql` | A-reference + I | the generic, UNCHANGED renderer is modeled deeply by `renderCall`; the equality of that deep model to the real `template % data` is the **A-reference** G-AX validates. The `++` concatenations are **I** (concrete, transliterated by G-CONF). mapping.md §3.1. |
| A6 | `return out` (`List Char`) | the returned `sql` string of `as_sql` (`sql, params` tuple; `params` unaffected) | R | `str` ↔ `List Char`; the F2P test inspects the captured SQL text. |

Discriminating content of the change — the trailing separator after `DISTINCT`
— lives in `distinctQualifier true = "DISTINCT ".toList` (model) ⇔ the
`'DISTINCT '` literal (real). The pre-patch emitted `'DISTINCT'` (no separator),
gluing the keyword onto the following argument text (`COUNT(DISTINCTCASE WHEN
…)`); `Solution_prepatch.lean` reproduces that (`"DISTINCT"`) and **fails**
`out = renderCall function distinct expressions` (G-DIFF), because the frozen
`distinctQualifier true = "DISTINCT "` requires the separator.

## B. No consumed axioms

There are no **A-consumed** rows. The only callee this operation invokes that
the patch does not change — the generic function-call renderer (`Func.as_sql`'s
`template % data`) — is modeled **deeply** (`renderCall`, A-reference, G-AX-
validated), not hidden behind a consumed axiom. The operation that genuinely
changed (the qualifier text) is the spelled-out `distinctQualifier` (I), not an
axiom about the function under change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The single changed operation — the qualifier
string — is a finite character concatenation, directly expressible and modeled
concretely (A4). Nothing is hidden.

## D. verify(Solution) ⇒ resolved

`aggregateAsSql` verifies only if its output equals
`renderCall function distinct expressions` with `distinctQualifier true =
"DISTINCT "` (A4/A5) — i.e. the keyword is emitted WITH its trailing separator
when deduplicating. By R (`str ↔ List Char`, `Bool ↔ truthiness`) the verified
result equals the patched `Aggregate.as_sql` output on the tested inputs; by
G-AX the deep model `renderCall` equals the real `template % data` renderer
(A-reference); by G-CONF the R/I transliteration of `distinctQualifier`/
`renderCall` agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited renderer — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-model soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
