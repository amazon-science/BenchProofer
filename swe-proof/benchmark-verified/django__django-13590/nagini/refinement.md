# refinement.md — django__django-13590

The operation-by-operation correspondence between `model.py`'s implementation
(the `resolve_sequence` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof/impl uses this
axiom's contract about an *unchanged* callee), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The list/tuple branch — `Query.resolve_lookup_value` (`django/db/models/sql/query.py:1077-1083`)

Gold hunk:
```
 elif isinstance(value, (list, tuple)):
     # The items of the iterable may be expressions and therefore need
     # to be resolved independently.
-    return type(value)(
+    values = (
         self.resolve_lookup_value(sub_value, can_reuse, allow_joins)
         for sub_value in value
     )
+    type_ = type(value)
+    if hasattr(type_, '_make'):  # namedtuple
+        return type_(*values)
+    return type_(values)
 return value
```

| # | model.py impl op (`resolve_sequence`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: List[int]` | `value` (a `list`/`tuple`/`namedtuple` of sub-values) | R | the sequence of opaque sub-values ↔ `List[int]` of sub-value identities (mapping.md §2). |
| A2 | parameter `field_named: bool` | `hasattr(type_, '_make')` — `type(value)` is a namedtuple | R | the container-kind discriminator ↔ the boolean `field_named` (mapping.md §2). The gold computes it from `type_`; the model carries it as the input flag describing the kind. |
| A3 | the per-element `resolve_one(value[i])` mapped over the sequence, accumulated as `resolved` (the loop) ⇔ `resolved_seq(ToSeq(value))` | the generator `(self.resolve_lookup_value(sub_value, can_reuse, allow_joins) for sub_value in value)` | A-consumed (`resolve_one`) | the unchanged recursive resolution is axiomatized as the deterministic pure `resolve_one`; the proof consumes its purity to make `resolved_seq` a well-defined element-wise map. The loop IS that element-wise map (`ToSeq(resolved) == resolved_seq(ToSeq(value))`). The recursion is unchanged by the patch; only the reconstruction around the generator changes. |
| A4 | `if field_named: build_container(resolved, field_named, True) else build_container(resolved, field_named, False)` | `type_ = type(value); if hasattr(type_, '_make'): return type_(*values); return type_(values)` | A-consumed (`build_container`, `well_formed_container`) **+ I (the spread choice)** | the *constructor* is the UNCHANGED callee, axiomatized as `build_container`; the *spread choice* is the changed operation and lives in the impl (the `if field_named` branch picking `spread=True`/`False`). The constructor's contract: a WELL-FORMED, non-raising construction requires the convention to match the kind (`Requires(field_named == spread)`) and, on success, returns the elements verbatim **and grants the `well_formed_container` token** on its output for that kind. `resolve_sequence`'s OWN postcondition requires that token (see §B), so a verifying impl is forced to perform a convention-matching (non-raising) construction. The branch picks `spread = field_named` — `spread=True` (`type_(*values)`) for a field-named kind, `spread=False` (`type_(values)`) for a plain kind — exactly the gold. |

## B. The soundness fix: the discriminator is a control-flow effect, so it is lifted into the contract of the function under change

The batch03 verdict's machine-checked G-EQ break: the only real-world difference
between the pre-patch `type(value)(values)` and the gold `type(value)(*values)`
for a field-named kind is whether the namedtuple constructor **RAISES TypeError**
— the produced *contents* are identical either way (if the single-iterable path
even returned). A `List[int]`-contents abstraction cannot witness a raise, so **no
value-level postcondition** (`ToSeq(Result()) == resolved_seq(ToSeq(value))`) can
separate gold from the bug. The prior spec parked the discriminator in the
*precondition* of an auxiliary `build_container` that `resolve_sequence` was free
NOT to call (verdict CEs: `return resolved`, and `if field_named: return
resolved`), so it verified-and-was-wrong.

This re-spec lifts the raise/succeed effect into the contract of the function
under change via an **unforgeable capability token**:

- `build_container` (the unchanged constructor) **grants** the abstract predicate
  `well_formed_container(ToSeq(Result()), field_named)` on its output, but ONLY
  when `field_named == spread` (its precondition for a well-formed, non-raising
  construction). A field-named kind under the single-iterable convention violates
  that precondition — the construction would raise — so no token is granted.
- `resolve_sequence`'s OWN postcondition **requires**
  `Ensures(well_formed_container(ToSeq(Result()), field_named))`. The token is an
  abstract `@ContractOnly @Predicate` with no body; Nagini cannot `Fold` it, so no
  impl can fabricate it. The ONLY producer is a convention-matching
  `build_container` call.

Therefore, for a field-named kind, the only way to discharge the postcondition is
to route the result through the spread (non-raising) construction — exactly the
gold fix. The discriminating obligation now sits on the contract of the function
under change, not on an optional helper.

**Counterexamples now rejected (all share the frozen spec, all FAIL to verify):**
- `atk_1` (`return resolved`, never construct — the verdict's CE): FAILS,
  *insufficient permission to* `well_formed_container(ToSeq(Result()), field_named)`.
- `atk_3` (`if field_named: return resolved` — the namedtuple-path bug, the
  verdict's CE): FAILS on the token on the field-named branch.
- `atk_4` (`build_container(resolved, field_named, False)` unconditionally — the
  literal pre-patch single-iterable): FAILS the precondition `field_named ==
  spread`.
- `atk_5` (`build_container(resolved, False, False)` — claim a plain kind to dodge
  the precondition): FAILS, the token granted is `well_formed_container(_, False)`,
  not `(_, field_named)`.

**The one verifying attack is SOUND (verify ⇒ resolves):**
- `atk_6` builds correctly (spread for the field-named kind, earning the token on
  the built contents) but returns the value-equal materialized `resolved` list.
  It verifies — the abstract token is keyed by the `(contents, kind)` *value*, so a
  value-equal list holds it. Its faithful refinement under the re-iterable
  `List[int]` carrier *executes the spread construction* (no raise) and returns the
  materialized list, which the `__range` lookup accepts. **Confirmed in the pinned
  eval image:** `test_range_lookup_namedtuple` (F2P) + the relevant P2P PASS. So
  `atk_6` is a *correct, resolving* impl — admitting it is not a soundness defect;
  the load-bearing fix behaviour (the spread construction does not raise) is
  present.

A structurally-different **positive control** (`pos_control2`: a single
computed-`spread` call site `spread = field_named; build_container(resolved,
field_named, spread)` instead of the gold's two literal branches) verifies — the
spec is non-vacuous.

## C. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it constructs by always handing the
builder the single iterable (`spread=False`) regardless of kind — exactly the
pre-patch `return type(value)(<generator>)`. With the byte-identical frozen spec
it **fails** verification on `model_prepatch.py:170` — *"The precondition of method
build_container might not hold. Assertion (field_named == spread) might not hold."*
— because a field-named kind (`field_named == True`) cannot well-form from the
single-iterable convention (`spread == False`). That is precisely the F2P
behaviour: `test_range_lookup_namedtuple` filters on a 2-field
`EmployeeRange(minimum=51, maximum=100)`; pre-patch the namedtuple is rebuilt as
`EmployeeRange(<generator>)`, raising `TypeError: __new__() missing 1 required
positional argument: 'maximum'` (confirmed by running the bug's refinement
in-container).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed* —
the spread choice (`type_(values)` vs `type_(*values)`, gated on the kind) — is in
the impl (step A4, the `if field_named` branch), an **I** (identical concrete
control-flow choice over the `spread` bool). Its downstream control-flow EFFECT
(the field-named single-iterable construction RAISES) is modeled by the unchanged
constructor's `build_container` contract: a token-granting (well-formed,
non-raising) construction is reachable only under the matching convention. Two
consumed axioms, both about **unchanged** callees:
- `resolve_one` (A-consumed) — the unchanged recursive per-element resolution;
- `build_container` + `well_formed_container` (A-consumed) — the unchanged
  container *constructor* (the patch changes how it is called, not the
  constructor). G-AX validates both against the real Python semantics
  (`axiom_check.py`, in-container rc=0). We never axiomatize the function under
  change (`resolve_sequence` / the spread choice).

## E. verify(model) ⇒ resolved

`resolve_sequence` verifies only if (A3) each element is the independent
resolution of the corresponding input element (`ToSeq(Result()) ==
resolved_seq(ToSeq(value))`, `len(Result()) == len(value)`), AND (A4 + §B) its
result holds `well_formed_container(ToSeq(Result()), field_named)` — a token only a
convention-matching (non-raising) `build_container` call grants. For a field-named
kind that forces the spread construction. By R the verified reconstruction equals
the gold `type_ = type(value); if hasattr(type_, '_make'): return type_(*values);
return type_(values)` over `values = (resolve(sub) for sub in value)`. By G-AX the
constructor contract and `resolve_one` match the real callees. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited unchanged callees — and the gold patch resolves
(G-RESOLVE, confirmed in-container). The trust points are exactly the two of PLAN
§1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
