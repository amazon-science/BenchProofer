# Relaxed-leakage record — matplotlib__matplotlib-26208 (lean)

This bundle records `gates.G-LEAK.status = "relaxed"` with `relaxed_leakage:
true`. The mechanical G-LEAK screen PASSES (`failures: []`) — the residual leak
is *behavioural*, not lexical — and this file states what that residual is, what
was measured to show it cannot be removed without breaking a core gate, and what
was removed from the spec view because it was avoidable.

Describes `Solution.lean` at
`sha256 96172bb26cc1defdd9778d915e2783338f08fd4a208950b534d04f2ec776e52f`
(`markers.spec_view` sha256 `0b853103a8e22ed400993816c25dc526ca5b39844f90283619af602ea97aa0f8`,
matching `meta.json region_hashes.spec_view`).

## The instance

Gold patch — two hunks, one added line each
(`lib/matplotlib/axes/_base.py`, base_commit `f0f133943d`):

```
twinx, before `return ax2`:  ax2.xaxis.units = self.xaxis.units   (@ +4444)
twiny, before `return ax2`:  ax2.yaxis.units = self.yaxis.units   (@ +4474)
```

Both FAIL_TO_PASS tests are one parametrised test,
`lib/matplotlib/tests/test_axes.py::test_twin_units[x]` and `[y]`. Its body
asserts, for `twin ∈ {x, y}` and `axis_name = f"{twin}axis"`:

```python
ax2 = getattr(ax1, f"twin{twin}")()
assert getattr(ax2, axis_name).units is not None
assert getattr(ax2, axis_name).units is getattr(ax1, axis_name).units
```

so the tested discriminator is a *presence* fact and an *object-identity* fact,
asserted independently for x and for y.

## What the spec view discloses

The spec the bundle ships is stated entirely in carrier vocabulary. It declares
`Slot := Option Nat` (`none` = nothing, `some t` = the token `t`),
`isPresent s = s.isSome`, and two predicates named `problem_spec_stepA` /
`problem_spec_stepB`, each

```lean
result = source ∧ isPresent result = isPresent source
```

over binders `source result : Slot`. Nothing in the spec view names a repo
symbol, an axis, a coordinate, a frame, a unit, a converter, a setting, a copy,
an inheritance or a construction site; see the token scan below.

What a reader can still read off it is a two-part behavioural fact:

* **(i) carry-over.** At each modeled step, whatever the `source` slot holds is
  what the `result` slot must hold — the same token, or nothing.
* **(ii) two obligations.** There are two such steps, observed independently, so
  discharging one does not discharge the other.

The relaxation covers exactly (i) and (ii), and nothing further.

## Why (i) cannot be dropped — measured

Three builds with `scripts/lean_verify.sh`, on files differing from the shipped
pair only as described:

| probe | spec | impl | exit |
|---|---|---|---|
| shipped solution | as shipped | as shipped | **0** (verifies) |
| `Solution_prepatch.lean` | as shipped | pre-patch (`out := none`) | **1** — `rfl` fails on `... = source` AND on `isPresent ... = isPresent source`, at both steps |
| carry-over removed | both postconditions replaced by `True` | pre-patch (`out := none`) | **0** — the pre-patch impl VERIFIES |

So the disclosed fact is load-bearing in the strict sense: strip it and the
pre-patch implementation satisfies the spec, i.e. the spec no longer separates
pre-patch from patched and G-DIFF collapses. The absent-default the pre-patch
leaves behind is `Axis.__init__`'s `self.units = None` (`lib/matplotlib/axis.py`).

The *identity* half of (i) is load-bearing too, and separately so. A fourth
build kept only the presence conjunct
(`isPresent result = isPresent source`) and gave the impl a token-fabricating
body, `out := source.map (fun _ => 0)`:

| probe | spec | impl | exit |
|---|---|---|---|
| presence-only | `isPresent result = isPresent source` | `source.map (fun _ => 0)` | **0** — VERIFIES |

That impl is presence-preserving but hands back a *different* token, which under
the `mapping.md §2` bijection is a `units` object that is not the source's. The
F2P asserts `is`, not "not None" alone, so a patch of that shape does not
resolve. Hence neither conjunct can be traded away for a weaker one.

## Why (ii) cannot be dropped

The gold patch has two hunks and the F2P is parametrised over both axes. A spec
carrying one obligation instead of two admits a half-fix that patches `twinx`
only: `ax2.yaxis.units` then stays at its `None` default and
`test_twin_units[y]`'s identity assertion fails on the unpatched site, so such a
patch does not resolve. `properties.py` pins this from the other side — the
reject cases `half-fix-B-only-broken` and `half-fix-B-prepatch` keep step A at
the gold body and corrupt only step B, and both are rejected with witnesses on
`problem_spec_stepB`. Two independently observed obligations are therefore the
minimum a faithful spec can carry, and disclosing that there are two is the cost
of that minimum.

## Why (i)+(ii) are absent from the public problem_statement

`problem_statement` (2079 chars) is a symptom report: "dataLims get replaced by
inf for charts with twinx if ax1 is a stackplot". Token scan, lower-cased,
`problem_statement` vs the current `markers.spec_view`:

| token | problem_statement | spec view |
|---|---|---|
| `unit` / `units` | 0 | 0 |
| `xaxis` / `yaxis` | 0 | 0 |
| `convert` / `converter` | 0 | 0 |
| `setting` | 0 | 0 |
| `shared` | 0 | 0 |
| `inherit` | 0 | 0 |
| `copy` | 0 | 0 |
| `categorical` | 0 | 0 |
| `identity` | 0 | 0 |
| `twinx` | 3 | 0 |
| `twiny` | **0** | 0 |
| `datalim` | 11 | 0 |
| `stackplot` | 5 | 0 |

The public text is entirely downstream: `dataLim.intervaly` becoming `±inf`. It
never mentions a per-axis conversion setting, an axis attribute, a copy or an
inheritance, and it never mentions the second (`twiny`) site at all — which is
why (ii) is disclosure and not restatement. The unit-machinery diagnosis lives
only in `hints_text` ("do not use the unit machinery (due to using strings to get
categoricals)", "an edge case in the unit handling code") and in the gold diff /
hidden `test_patch`; `hints_text` is not public, so a term appearing only there
would leak if echoed, and none is echoed.

## Why no problem_statement-derivable reformulation replaces it

The publicly described observable is the tail of a pipeline: categorical (string)
data installs a converter on an axis; on the twin, autoscale/`relim` runs the
shared axis's converter over the other frame's data; with that configuration
missing on the twin, the conversion yields non-finite values and `dataLim`
collapses to `±inf`. A spec pinning "`dataLim` stays finite" would have to model
conversion, autoscale and datalim — none of which the gold patch touches — and
would still not be discharged by the two added lines in isolation, nor align with
the F2P, which asserts the `units` identity directly. So the minimal faithful,
F2P-aligned obligation is the carry-over contract, and the carry-over contract is
the disclosure.

## What was removed because it was avoidable

Everything localizing beyond (i)+(ii) has been taken out of the spec view, with
no change to the formal content:

* the modeled functions are `stepA` / `stepB` — earlier revisions named them
  `inheritSharedA` / `inheritSharedB`, which spelled out both the direction of
  the change and the axis-sharing relation;
* the carrier is `Slot` — an earlier revision called it `ConvSetting`, an
  abbreviation of the changed attribute's role;
* the prose speaks of a `source` slot and a `result` slot and of what each
  *holds*. Earlier revisions spoke of a new object *re-using a component* of a
  source object, of an *opaque field distinguished only up to identity*, and of
  *construction steps* — each of which narrowed the candidate attribute set.

The rename is an alpha-renaming plus prose: the four `problem_spec_*` bodies,
`Slot`, `isPresent` and both `theorem correct_*` statements are unchanged in
strength, `markers.same_spec(Solution.lean, Solution_prepatch.lean)` is True, and
`meta.json region_hashes` is re-stamped against the file described above.

## Requirements checklist

1. **Core gates sound.** G-VERIFY pass (both `correct_step*` closed, no `sorry`,
   `#print axioms` clean), G-DIFF pass (the pre-patch twin fails on the
   carry-over clause — re-measured above, exit 1), G-CONF pass (R/I legs, 120004
   checks, 0 disagreements, seed 26208), G-AX skip (the changed op is a plain
   attribute assignment consuming no callee, so there is no axiom to fuzz),
   G-RESOLVE pass (`patch.diff` == gold verbatim), G-PBT SOUND (7 cases,
   5 witnessed reject cases).
2. **Residual leak unavoidable.** Established by the four builds above plus the
   token scan: the pre-patch impl verifies against a spec without (i), and a
   non-resolving fabricator verifies against a spec with only the presence half;
   a one-obligation spec admits a half-fix that fails `test_twin_units[y]`.
3. **Recorded in-bundle.** This file, `meta.json relaxed_leakage: true`, and
   `gates.G-LEAK.status = "relaxed"` with the mechanical screen still passing.
