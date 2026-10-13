# refinement.md — django__django-11749

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`selectForwarded` `do` block + the deep `forwarded`/`forwardedAll` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — **A-consumed** / **A-reference**), or **I** (identical
concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the forward-selection it changes, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The forward-selection site — `call_command` (`django/core/management/__init__.py:135`)

The patch (a) adds a precomputed set of options belonging to *required* mutually
exclusive groups, and (b) widens the comprehension predicate that decides which
supplied options are re-passed to `parser.parse_args()`:

```
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

| # | Solution.lean impl op (`selectForwarded`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `options : List OptionView` | the actions iterated by `for opt in parser_actions`, each reduced to the three observations the predicate reads | R | record ↔ the per-option observations; G-CONF bridges each field via mapping.md §2. |
| A2 | `forwarded a` left conjunct `a.supplied` | `opt.dest in options` | I + R | the supplied-by-caller test; Python truth ↔ `Bool` (mapping.md §2). Present in BOTH pre- and post-patch predicates. |
| A3 | `forwarded a` right disjunct `a.individuallyRequired` | `opt.required` | I + R | the option's own required flag; the sole mandatory route pre-patch. |
| A4 | `forwarded a` right disjunct `a.inRequiredGroup` | `opt in mutually_exclusive_required_options` (the ADDED set over `parser._mutually_exclusive_groups` / `group._group_actions` / `group.required`) | I + R | the changed decision, modeled **deeply** and concretely: membership of a required mutually exclusive group is the second mandatory route the patch introduces. The set-membership truth ↔ `inRequiredGroup` (mapping.md §2). |
| A5 | verdict `true` ↔ option appended to `parse_args`; `false` ↔ omitted | the comprehension keeping vs dropping the `'{}={}'.format(...)` element | R | `true`↔kept, `false`↔skipped (mapping.md §2). The unchanged `'{}={}'.format(min(opt.option_strings), arg_options[opt.dest])` formatting of a kept option is outside the predicate the patch edits, so it carries no separate refinement obligation beyond "kept iff verdict true". |
| A6 | `result := forwarded a :: result`, backward `while` fold over `options` | the comprehension visiting each action once and keeping/dropping it | I | per-element transliteration; `forwardedAll` is the order-preserving keep-mask (G-CONF compares element-wise). |

Discriminating content of the change lives at A4: `forwarded` forwards a
supplied option that is mandatory by EITHER route (individually required, or in
a required group). `Solution_prepatch.lean` uses `a.supplied &&
a.individuallyRequired` (the pre-patch `opt.required and opt.dest in options`),
which omits the `inRequiredGroup` disjunct and so classifies a supplied
group-only-required option `false`, **failing** `out = forwardedAll options` on
that option's term (G-DIFF). This is exactly the F2P scenario
`test_mutually_exclusive_group_required_options`: `call_command(..., foo_id=1)`
where `--foo-id` is part of a `required=True` mutually exclusive group but is not
itself `required` — pre-patch it is not forwarded, so `parse_args` omits it and
the parser raises "one of the arguments --foo-id --foo-name is required".

## B. No additional change sites

The patch touches a single function (`call_command`), and within it a single
comprehension predicate plus the helper set that feeds it. The set construction
(`mutually_exclusive_required_options`) only *produces* the `inRequiredGroup`
observation the model takes as a free input (mapping.md §3); it carries no
separate refinement obligation. The surrounding option remapping, formatting,
`parse_args` call, unknown-option check, and `execute` are unchanged and precede
/ follow the modeled predicate (mapping.md §1); they are not part of the spec
view.

## C. No axioms, no A-references, no kind-3 steps

Every step is R or I. The operation that genuinely *changed* — the
forward-this-option predicate — is modeled **deeply** and concretely by
`forwarded` (steps A2–A4), not hidden behind an axiom about the function under
change. There is **no consumed axiom** and **no deep-model A-reference**: the
decision assumes no callee contract. The set-membership / `dest in options` /
flag reads run to produce the three observations the model takes as free inputs;
`axiom_check.py` is therefore a `status=skip` stub (mapping.md §3). No operation
is an inexpressible kind-3.

## D. verify(Solution) ⇒ resolved

`selectForwarded` verifies only if its output equals `forwardedAll`, i.e. each
option's verdict is exactly `supplied && (individuallyRequired || inRequiredGroup)`
— the supplied option is forwarded when mandatory by EITHER route (A2–A4). By R
(`OptionView` ↔ the three action observations; `true`/`false` ↔ kept/dropped in
`parse_args`) the verified selector equals the patched comprehension on every
action; by G-CONF the R/I transliteration of `forwarded` agrees with the patched
predicate — driven by real `argparse` parsers with real mutually exclusive
groups — on the full Boolean matrix + fuzzed parsers (incl. the F2P
required-group case). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axiom trust points (G-AX is a skip); the sole trust
point is refinement fidelity (this doc, G-EQ + G-CONF).
