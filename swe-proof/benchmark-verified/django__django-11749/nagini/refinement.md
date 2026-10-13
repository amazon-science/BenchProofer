# refinement.md — django__django-11749

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_forwarded` impl region and the deep `forwarded_seq` / `forward`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model is validated == a real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The selection site — the `parse_args +=` comprehension (`django/core/management/__init__.py:135-138`)

Gold hunk (pre-patch → post-patch):
```
  parser_actions = list(get_actions(parser))
+ mutually_exclusive_required_options = {
+     opt
+     for group in parser._mutually_exclusive_groups
+     for opt in group._group_actions if group.required
+ }
  parse_args += [
      '{}={}'.format(min(opt.option_strings), arg_options[opt.dest])
-     for opt in parser_actions if opt.required and opt.dest in options
+     for opt in parser_actions if (
+         opt.dest in options and
+         (opt.required or opt in mutually_exclusive_required_options)
+     )
  ]
```

| # | model.py impl op (`select_forwarded`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `actions: List[int]` | `parser_actions` (`= list(get_actions(parser))`) iterated by the comprehension | R | each `argparse` action ↔ its 3-bit encoding; ordered list ↔ `List[int]` same order (mapping.md §2). |
| A2 | `supplied(a) = (a % 2 == 1)` | `opt.dest in options` | R | bit-0 ↔ the dict-membership test; a pure boolean fact of the action (mapping.md §2). |
| A3 | `mandatory(a) = ((a // 2) % 2 == 1)` | `opt.required` | R | bit-1 ↔ `argparse.Action.required`. |
| A4 | `in_mandated_set(a) = ((a // 4) % 2 == 1)` | `opt in mutually_exclusive_required_options`, the set `{opt for group in parser._mutually_exclusive_groups for opt in group._group_actions if group.required}` | R | bit-2 ↔ the per-action boolean "member of a `required` mutually-exclusive group". The group scan that builds the set is folded into this single per-action boolean (mapping.md §2); it reads only `group.required` and `group._group_actions` and contributes one membership bit per action. |
| A5 | the filter predicate `supplied(a) and (mandatory(a) or in_mandated_set(a))` | `opt.dest in options and (opt.required or opt in mutually_exclusive_required_options)` | I | identical boolean expression under the A2/A3/A4 renamings: same operands, same `and`/`or` structure, same short-circuit-irrelevant pure logic. |
| A6 | result is `forwarded_seq(ToSeq(actions))` — the order-preserving sub-list of `actions` satisfying `forward`, built by the backward loop | the list comprehension `[ '{}={}'.format(...) for opt in parser_actions if <pred> ]` | R | the comprehension is an order-preserving filter of `parser_actions` by `<pred>`; the model is an order-preserving filter of `actions` by `forward`. Each surviving action ↔ exactly one appended formatted string; the per-action string `'{}={}'.format(min(opt.option_strings), arg_options[opt.dest])` is a pure function of the action and is **identical pre- and post-patch**, so the only changed observable is set membership + order, which `forwarded_seq` pins exactly (mapping.md §2). |

The discriminating content of the change — forwarding an option that is a
member of a *mandated set of alternatives* but is **not** individually
mandatory — lives in the `or in_mandated_set(a)` disjunct (model) ⇔ the
`or opt in mutually_exclusive_required_options` disjunct (real). The pre-patch
predicate was `opt.required and opt.dest in options`, i.e. only the
`mandatory(a) and supplied(a)` conjunction; `model_prepatch.py` reproduces
exactly that and **fails** the loop invariant
`ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i))` on any declared option
with `supplied ∧ in_mandated_set ∧ ¬mandatory` — which is precisely the
configuration the F2P test `test_mutually_exclusive_group_required_options`
constructs (`--foo-id`/`--foo-name` in a `required=True` group, each member
`required=False`). This is the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
forwarding predicate, and in particular the new disjunct that admits members of
a mandated alternative set — is modeled **deeply** (the spelled-out boolean
`forward` and the order-preserving fold `forwarded_seq` in the `pure` region,
consumed by `select_forwarded`), not hidden behind an axiom. There is **no
`@ContractOnly` axiom**: the change introduces no unchanged opaque callee the
proof must over-approximate (the group scan reduces to a per-action boolean,
the formatted string is unchanged), so there is nothing to axiomatize and no
G-AX obligation (mapping.md §3).

## C. verify(model) ⇒ resolved

`select_forwarded` verifies only if its output equals the exact
order-preserving filter `forwarded_seq` of the declared options under the
post-patch predicate `forward` (A5/A6), which forwards an option iff the caller
supplied it AND (it is individually mandatory OR it is a member of a mandated
alternative set). By R (action ↔ 3-bit encoding; ordered list ↔ `List[int]`;
the unchanged per-action formatted string) the verified selection equals the
gold comprehension's forwarded set on every configuration of declared options,
including the F2P configuration. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ); there is no axiom-soundness trust point (no `@ContractOnly`).
