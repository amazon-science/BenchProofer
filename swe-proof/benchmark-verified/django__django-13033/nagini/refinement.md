# refinement.md — django__django-13033

The operation-by-operation correspondence between `model.py`'s implementation
(the `ordering_mode` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == a real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The decision predicate — `find_ordering_name` (`compiler.py:730`)

Gold hunk (whitespace-reformatted across lines; the only token change is the
right-hand operand of the third conjunct):
```
- if field.is_relation and opts.ordering and getattr(field, 'attname', None) != name and name != 'pk':
+ if (
+     field.is_relation and
+     opts.ordering and
+     getattr(field, 'attname', None) != pieces[-1] and
+     name != 'pk'
+ ):
```

| # | model.py impl op (`ordering_mode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `points_to_relation` | `field.is_relation` | R | `bool` ↔ `bool`, identity (mapping.md §2). |
| A2 | `has_default_ordering` | `opts.ordering` (used as a boolean) | R | the predicate consumes only the truthiness of the `Meta.ordering` tuple; `has_default_ordering = bool(opts.ordering)` (mapping.md §2). |
| A3 | `relation_own_column != path_terminal(path_segments)` | `getattr(field, 'attname', None) != pieces[-1]` | R | `relation_own_column` ↔ the field's attribute name as `PSeq[int]`; `path_terminal(path_segments) = path_segments[len-1]` ↔ `pieces[-1]` (the final segment). `str` `!=` ↔ `PSeq` `!=`. **This is the changed conjunct** — the operand moved from the whole joined `name` to the final segment `pieces[-1]`. |
| A4 | `name != PK()` | `name != 'pk'` | I | identical comparison; `'pk'` ↔ `PK() = PSeq(112,107)` (mapping.md §1). |
| A5 | `and` of A1–A4; `mode = 1` if true else `0`; `return mode` | the `if (...)` guard selecting the related-default-ordering branch (`mode 1`) vs. the direct-target branch (`mode 0`) | I + R | boolean `and` is identical; the two branches abstract to `Result() ∈ {0,1}` (mapping.md §2). The machinery inside each branch (recursive `find_ordering_name` over `opts.ordering`, `OrderBy`, `trim_joins`) is UNCHANGED by the patch, so it is not part of the modeled delta — only which branch is selected is observable and modeled. |

The discriminating content of the change lives in step **A3**: the operand is
`pieces[-1]` (the final segment), not the whole `name`. When the user orders by
a multi-segment path whose final segment IS the relation's attribute name
(the issue's `record__root_id`, where `attname == "root_id" == pieces[-1]` but
`attname != "record__root_id" == name`), the patched predicate is `False`
(direct column, ascending, single join — correct), while the pre-patch predicate
`attname != name` is `True` (wrongly substitutes the related model's default
`-id` ordering, extra join, descending — the bug). `model_prepatch.py`
reproduces the pre-patch operand (model-side `relation_own_column != name`,
repo-side `attname != name`) and **fails** the postcondition
`(Result() == 1) == (... and relation_own_column != path_terminal(path_segments) and ...)`,
which is exactly the spec sensing the change (G-DIFF).

## B. The split invariant (precondition, not an axiom)

`ordering_mode`'s precondition
`Implies(len(path_segments) > 1, name != path_terminal(path_segments))` encodes
the semantics of `pieces = name.split(LOOKUP_SEP)` (`compiler.py:724`): a
multi-segment path contains the separator and so is unequal to its final
segment alone. This is the exact relation the real code establishes one line
before the changed `if`, NOT a contract on an opaque callee — there is **no
`@ContractOnly` axiom** in this bundle. Its soundness is checked out-of-band by
`axiom_check.py` (G-AX style) against real `str.split('__')` (mapping.md §3). It
is the fact that makes the pre-patch operand (`!= name`) observably wrong
precisely on the multi-segment attname case: with `len(pieces) > 1` and
`attname == pieces[-1]`, we have `attname != name` forced `True` while
`attname != pieces[-1]` is `False` (model-side: `relation_own_column != name`
vs. `relation_own_column != path_terminal(path_segments)`).

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
comparison operand of the third conjunct — is modeled **deeply** and exactly as
a `PSeq` inequality against the final segment (`path_terminal(path_segments)`),
not hidden behind an axiom. No consumed axiom (A-consumed) and no
deep-model-of-a-callee (A-reference) appear: the changed predicate is pure,
expressible boolean and sequence logic over the inputs.

## D. verify(model) ⇒ resolved

`ordering_mode` verifies only if `mode` equals the patched predicate using the
FINAL SEGMENT (`path_terminal(path_segments)`, step A3). By R (str ↔ PSeq, bool
identities, branch-outcome ↔ `mode`) the verified predicate equals the gold
`if field.is_relation and opts.ordering and getattr(field,'attname',None) !=
pieces[-1] and name != 'pk'`. The branch the predicate selects is the only thing
the patch changes; everything it guards is unchanged and behaviour-preserving.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The trust
points: refinement fidelity (this document, G-EQ) and the split invariant
(axiom_check.py); there is no callee axiom to trust.
