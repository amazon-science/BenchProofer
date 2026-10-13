# mapping.md — pydata__xarray-7229

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3aa75c8d00a4a2d4acf10d80f76b937cadb666b7`, states the type
abstraction, and records the provenance of the modelled behaviour.

Repo file under change: `xarray/core/computation.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rebuild_attrs(x_attrs, x_coord_attrs, x_var_attrs, top_unmatched, named_slot)` | the `keep_attrs is True` attribute-rebuild logic of `where(cond, x, y, keep_attrs=None)` — `xarray/core/computation.py:1775` (the modeled changed behaviour: lines 1860-1863 pre-patch; the post-patch level-by-level rebuild block with its two regimes) | the modeled changed function (preserve the second argument's attributes at every level, placing the top-level mapping at the level matching the source's structure) |
| `WhereResult` (`attrs`, `coord_attrs`, `var_attrs`) | the `result` object returned by `apply_ufunc(...)` inside `where` (a `Dataset` / `DataArray` / `Variable`): `result.attrs` is its top-level / global mapping; `result[c].attrs` (`c` over `result.coords`) are its per-coordinate mappings; `result[v].attrs` (`v` over `result.data_vars`) are its per-data-var mappings | the modeled output object; only the attribute mappings are touched |
| `x_attrs` | `getattr(x, "attrs", {})` — the second positional argument's OWN top-level (variable / global) attribute mapping | source top-level mapping identity |
| `x_coord_attrs` | the list `[getattr(getattr(x, c, None), "attrs", {}) for c in result.coords]` — the second argument's OWN mapping **AT** each output coordinate name `c`, the name resolved **on `x`** (see the name-resolution note below, which is where the empty mapping does and does not arise) | source per-coordinate mapping identities, aligned positionally with the output's coordinates |
| `x_var_attrs` | the list `[getattr(getattr(x, v, None), "attrs", {}) for v in result.data_vars]` — the second argument's OWN mapping **AT** each output data-var name `v`, the name resolved **on `x`** (same note) | source per-data-var mapping identities, aligned positionally with the output's data-vars |
| `top_unmatched` | the regime guard `isinstance(y, Dataset) and not isinstance(x, Dataset)` — `True` when the THIRD argument forces the output to a Dataset that the second argument was not | regime selector (promotion vs ordinary) |
| `named_slot` | the position of the output data-var named `getattr(x, "name", None)` within `list(result.data_vars)`, or `-1` when `x.name` is absent from the output | index of the output data-var that receives x's top-level mapping in the promotion regime |

The closure variable `x` of both the old lambda
(`keep_attrs = lambda attrs, context: getattr(x, "attrs", {})`) and the
post-patch rebuild block is the second positional argument of `where`.

**Name resolution — an output level's NAME is resolved ON `x`, not looked up
among the levels `x` carries.** The post-patch block reaches the source of a
level with `getattr(getattr(x, name, None), "attrs", {})`
(`xarray/core/computation.py:1889` for data-vars, `:1892` for coordinates), so
the source of an output level is the mapping of whatever `x` answers to that
level's name with:

  * a name `x` carries as a coordinate / data-var → that level's own mapping
    (the ordinary case, and the only one the F2P test exercises);
  * a name `x` answers with nothing (the `getattr` default `None`) or with
    something that has no `attrs` (`values`, `data`, `shape`, `dims`, `name`,
    `attrs` itself, an accessor …) → `{}`;
  * a name `x` answers with a **derived view of itself** → that view's `attrs`,
    which IS `x`'s own whole-object mapping and is **not** `{}`. Measured
    against the patched callee with a `DataArray` `x`: `T`, `variable`, `real`
    and `imag` each return `x.attrs`. The property wins over `__getattr__`, so
    `T` resolves to the transpose even when `x` also carries a coordinate named
    `T`, and that coordinate's own mapping is then NOT what the output level
    takes.

Consequence: an output coordinate named `T` that `x` does not carry takes
`x.attrs`, not `{}`. The contract's uniform clause
`Result().coord_attrs[k] == x_coord_attrs[k]` is exactly right about this under
the abstraction above — the defect was in the prose gloss "a coordinate `x` does
not carry contributes 0", which is false of the callee on those names. It has
been corrected in `model.py` / `model_prepatch.py`'s docstring, in
`refinement.md` A2/A3, and in `axiom_check.py`, whose expectation formula
(`dict(x[c].attrs) if c in x.coords else {}`) encoded the wrong reading and is
now the callee's own expression (`_level_attrs`). `conformance_check.py` was
already deriving the carrier with the callee's expression, so its shadow/oracle
comparison was never wrong; boundary and fuzz cases over these names were added
so the gate exercises the class instead of only documenting it, and
`axiom_check.py` gained a `_check_name_resolution` scenario that fails if the
"levels `x` carries" reading is ever restored.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an attribute mapping (a Python `dict` of attrs) | `int` opaque identity | distinct mappings ↔ distinct identities; the empty mapping `{}` (also what a scalar argument carries via `getattr(scalar, "attrs", {})`) ↔ identity `0`. Only mapping *identity* is observed by the F2P test (`assert_identical` compares the attrs dicts for equality), so identity equality is faithful. |
| `result` (`Dataset`/`DataArray`/`Variable`) | `WhereResult` with fields `attrs: int`, `coord_attrs: List[int]`, `var_attrs: List[int]` | `result.attrs` ↔ `WhereResult.attrs`; `[result[c].attrs for c in result.coords]` ↔ `WhereResult.coord_attrs` (by coordinate order); `[result[v].attrs for v in result.data_vars]` ↔ `WhereResult.var_attrs` (by data-var order). **The three carriers are modelled as SEPARATE fields, NOT folded into one** — see the soundness note below. |
| `x` (`Dataset`/`DataArray`/`Variable`/scalar) | the triple `x_attrs: int`, `x_coord_attrs: List[int]`, `x_var_attrs: List[int]` | x's top-level mapping ↔ `x_attrs`; x's mapping AT the name of output coordinate `i` ↔ `x_coord_attrs[i]`; x's mapping AT the name of output data-var `i` ↔ `x_var_attrs[i]` — `0` when x answers with nothing or with something carrying no `attrs` at that name, and `x_attrs` when it answers with a derived view of itself (§1 name resolution). Read-only: required AND ensured at fractional permission, with each `ToSeq` pinned to its old value (directive 5). |
| the regime test `isinstance(y, Dataset) and not isinstance(x, Dataset)` and the matching-data-var lookup | `top_unmatched: bool`, `named_slot: int` | the structural promotion test ↔ the boolean; the position of the output data-var named `x.name` ↔ `named_slot` (`-1` when absent). |
| iterating `result.coords` / `result.data_vars` and assigning `result[c].attrs` / `result[v].attrs` | the per-regime `while` loops building `out_coords` / `out_vars` | per-output-level assignment ↔ list append; "always fill coord attrs of x" (each from the SAME source coordinate) ↔ `out_coords.append(x_coord_attrs[i])`; ordinary data-var fill ↔ `out_vars.append(x_var_attrs[j])`; promotion matching-var fill ↔ `out_vars[named_slot] = x_attrs`. |

`str` (coordinate names, data-var names, attr keys/values) are not indexed in
the model — only mapping *identities* matter — so no `List[int]`-of-code-points
carrier is needed; identities suffice and keep the proof in the decidable
fragment.

**Soundness note — do NOT fold carriers a regime separates (SPEC_GUIDE §2).**
The global mapping, the per-data-var mappings and the per-coordinate mappings
travel TOGETHER in the ordinary regime (each output level takes x's own
same-level mapping), but the promotion regime SEPARATES them: it sets the global
to `{}` and routes x's top-level mapping to the matching data-var instead. A
single model field abstracting "global == x's top-level" therefore breaks on the
promotion branch (the gold patch sets `{}` there). Each carrier that any
reachable F2P branch separates is modelled as its OWN field, and the regime is
made explicit (`top_unmatched`), so the contract states the correct value in each
regime rather than a fold that is true only in one. (An earlier revision folded
them and asserted `Result().attrs == x_attrs` unconditionally — an over-claim
the gold patch itself violates on the promotion sub-case; that defect is the
reason for the separate `var_attrs` field and the `top_unmatched` guard.)

## 3. Callee provenance — A-reference deep model (checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**. The operations that changed are
the attribute-preservation rules themselves, modelled **deeply** by
`rebuild_attrs`:

  * per coordinate `i` (EVERY regime): `Result().coord_attrs[i] ==
    x_coord_attrs[i]` (output coordinate mapping = x's OWN mapping AT that
    coordinate's name, §1 name resolution), with
    `len(Result().coord_attrs) == len(x_coord_attrs)`;
  * ordinary regime (`not top_unmatched`): top-level `Result().attrs == x_attrs`, and
    per data-var `i` `Result().var_attrs[i] == x_var_attrs[i]`;
  * promotion regime (`top_unmatched`): top-level `Result().attrs == 0` (EMPTY global),
    and the matching data-var `Result().var_attrs[named_slot] == x_attrs`
    (when `named_slot >= 0`); non-matching slots are unconstrained (the gold
    patch leaves them as `apply_ufunc` produced).

**Real callee modelled:** `xarray.where(cond, x, y, keep_attrs=True)`
(`xarray/core/computation.py:where`). Post-patch, after `apply_ufunc` produces
`result`, the function rebuilds attrs from `x` at each level of the output. The
ordinary branch: `result.attrs = getattr(x, "attrs", {})`; for each data var
`v`, `result[v].attrs = getattr(getattr(x, v, None), "attrs", {})`. The
promotion branch (`isinstance(y, Dataset) and not isinstance(x, Dataset)`):
`result.attrs = {}`; `if getattr(x, "name", None) in result.data_vars:
result[x.name].attrs = getattr(x, "attrs", {})`. And in BOTH branches, for each
coordinate `c`: `result[c].attrs = getattr(getattr(x, c, None), "attrs", {})` —
"always fill coord attrs of x". This is exactly the per-level, same-source-level
rule (with regime-dependent top-level placement) the deep model encodes.

Pre-patch (the bug, introduced in PR #6461), `keep_attrs is True` was turned
into a single callable `lambda attrs, context: getattr(x, "attrs", {})` handed
to `apply_ufunc`; the merge machinery applies that callable at EVERY level —
including each coordinate AND (in the promotion case) the global level — so every
coordinate's attrs, and the promotion-case global attrs, were overwritten with
x's single top-level (variable) mapping instead of the level-appropriate value.
(Empirically reproduced in the pinned container: pre-patch the 2-Datasets case
yields global/var/coord all == x's top-level mapping; the promotion case yields
global == x's top-level mapping instead of `{}`.)

**Flag dependency:** the modelled behaviour is the `keep_attrs=True` branch (the
default-`False` and other-strategy branches are unchanged and route through
`apply_ufunc` unchanged). The where call's `join="exact"` / `dataset_join=
"exact"` align coordinates so the output's coordinates correspond one-to-one
with x's coordinates by name; this alignment is what makes the positional
`x_coord_attrs` / `x_var_attrs` correspondences faithful.

**Soundness check (G-AX):** `axiom_check.py` builds real DataArrays / Datasets
with DISTINCT top-level, data-var and coordinate attribute mappings, runs the
real post-patch `xr.where(..., keep_attrs=True)` in-container, and asserts EVERY
modelled field on EVERY scenario:
(1) output top-level attrs == x's top-level attrs in the ordinary regime, and ==
`{}` (EMPTY) in the promotion regime;
(2) each output coordinate's attrs == x's OWN mapping AT that coordinate's name
(and, when that differs from x's top-level attrs, NOT x's top-level attrs — the
pre-patch bug);
(3) each output data-var's attrs == x's OWN mapping AT that data-var's name in
the ordinary regime, and the matching data-var == x's top-level attrs in the
promotion regime;
(4) a scalar source contributes empty mappings —
over the 7 F2P scenarios (3 DataArrays; x scalar; y scalar; x+y scalar; cond+y
scalar; 2 Datasets — global+var+coord; DataArray promoted to Dataset —
global-empty+matching-var+coord), plus 7 NAME-RESOLUTION scenarios
(`_check_name_resolution`: output coordinate names x carries nothing under —
four it answers with a derived view of itself, `T` / `variable` / `real` /
`imag`, which must take x's OWN whole-object mapping, and three it answers with
no mapping, `values` / `shape` / `zzz`, which must take `{}`), plus 2000
randomized fuzz cases (DataArray and promotion). Every expectation is computed by
the single helper `_level_attrs`, the callee's own expression, so the "attrs of
the level x carries of that name, else `{}`" reading cannot creep back in
unnoticed: it would fail the four derived-view scenarios. The promotion-case
GLOBAL assertion — the field whose omission previously masked the over-claim — is
explicit and fires (exit 1) against the buggy base callee, as does the coordinate
rule on the very first F2P scenario (measured: `F2P 3-DataArrays [coord 'a'
attrs]: observed {'attr': 'x_da'} != expected {'attr': 'x_coord'}`). Imports only `xarray` / `numpy`. The container ships the
base_commit source, so the check MUST be run with the gold patch applied
(`apply_gold=True`, `gold_patch_path=patch.diff`); standalone against the
unpatched base it correctly exits 1. Exit 0 iff sound.

## G-CONF — differential conformance (shadow vs the real patched function)

`conformance_check.py` refutes the refinement leg: does the MODEL agree with the
REAL patched repo function it claims to model? Neither G-VERIFY (impl meets
spec) nor G-PBT (no wrong impl meets spec) looks at the repository at all.

**Shadow.** The `# impl-start` / `# impl-end` regions of `model.py` (both
`WhereResult.__init__` and `rebuild_attrs`), copied VERBATIM with only the
contract calls (`Requires` / `Ensures` / `Invariant` / `Assert`) and the
`# invariants-start` / `-end` markers deleted — no restructuring, renaming or
simplification. `PSeq` is realized by an immutable-tuple shim and `ToSeq`
materializes one. There are no `@Pure` helpers and no `@ContractOnly` callees
(§3), so the whole region is executable R/I content: `conf_skip` does NOT apply
and is not set.

**Oracle.** `xarray.core.computation.where(cond, x, y, keep_attrs=True)` —
`xarray/core/computation.py:1775` @ base_commit, the symbol §1 binds — is
**CALLED, not transliterated**. The gate applies `patch.diff` to /testbed before
the script runs, so the post-patch rebuild block (patched lines 1875-1892) is
what executes. Two further real calls supply inputs, never answers:
`where(..., keep_attrs=False)` gives only the output SKELETON (the `coords` /
`data_vars` names and order that §2's positional carriers align against, taken
from the metadata-dropping path so the frame is independent of the rebuild under
test), and the real upstream `apply_ufunc(duck_array_ops.where, ...)` with
`where`'s own kwargs gives the "as apply_ufunc produced it" baseline for the
unmodelled promotion slots.

**Type bridge (§2, inverted).** Concrete real inputs are built first and the
model carriers are derived from them by §2's abstraction function, so every
input satisfies `rebuild_attrs`'s `Requires` by construction. An attrs `dict`
maps to an opaque `int` via a per-case interning table (`{}` ↔ 0, distinct
contents ↔ distinct non-zero ids); the same table interns x's mappings and the
result's, so model identity equality IS dict equality. `x_attrs` ←
`getattr(x, "attrs", {})`; `x_coord_attrs[i]` / `x_var_attrs[i]` ←
`getattr(getattr(x, name_i, None), "attrs", {})` over the skeleton's coord /
data-var order; `top_unmatched` ← `isinstance(y, Dataset) and not isinstance(x,
Dataset)`; `named_slot` ← the index of `getattr(x, "name", None)` in the
skeleton's `data_vars`, else -1 (which is what makes
`Implies(top_unmatched, -1 <= named_slot < len(x_var_attrs))` hold). The oracle's
real `result` abstracts back the same way, and all three levels are compared.

**Unmodelled promotion slots — tested, not skipped.** §3 records that in the
promotion regime the non-matching data-var slots are unconstrained ("the gold
patch leaves them as `apply_ufunc` produced"); the model's input tuple carries
nothing about `cond`, so they are outside the abstraction's domain and the impl
writes 0 there as a placeholder. The check turns that documented claim into a
testable one: for `top_unmatched and j != named_slot` the oracle's slot abstracts to
0 iff its attrs are UNCHANGED from the real `apply_ufunc` baseline, and to a -1
sentinel (never equal to the shadow's 0) otherwise. A rebuild that wrote
anything into a non-matching slot therefore FAILS the check.

**Domain edge (stated, not hidden).** `where(True, 1, 0)` — cond, x and y all
plain scalars — returns a bare `numpy.ndarray` with no attribute levels at all,
so it has no `WhereResult` image under the §2 bijection and is excluded from
generation. This does not narrow the modelled behaviour: the F2P "x and y as a
scalar" case (`where(cond, 1, 0)` with cond a DataArray) still yields a real
DataArray with attribute levels and IS checked. A real call that raises is
counted as an error and FAILS the run rather than being dropped.

**Domain edge 2 — the modelled callee must DELIVER a result (stated, not
hidden).** `rebuild_attrs`'s contract is total (`MustTerminate(6)` + unconditional
`Ensures(Acc(Result().attrs))`), so the abstraction is defined only for calls on
which the real callee delivers an output at all. THREE distinct things can
abandon the call instead, and all three are OUTSIDE the modelled domain: a
source-side level-name lookup, an output-side roster lookup, and — logically
prior to both — the argument combination itself. None is expressible as a
`Requires`: §2 maps an attrs dict to an OPAQUE int, the model carries no name
carrier and no array carrier, so the restriction belongs here and in `model.py`'s
"admissible" prose rather than in a precondition. All three are measured
against the PATCHED worktree, not read off the source:

  * **Source-side, the level-name lookup raises.** `getattr(x, name, None)`
    suppresses only `AttributeError`. `dataarray.py:372` registers
    `dt = utils.UncachedAccessor(CombinedDatetimelikeAccessor)`;
    `UncachedAccessor.__get__` is a bare `return self._accessor(obj)`, and
    `accessor_dt.py:573` `__new__` raises `TypeError` for a non-datetime-like
    object. Measured: for a numeric- or str-dtype `x`, `getattr(x, "dt", None)`
    raises `TypeError`, and an output coordinate named `dt` therefore makes
    `where` propagate it. Sweeping every public `DataArray` attribute name,
    `dt` is the ONLY raiser (numeric and str dtype); a datetime-dtype `x` has
    none, and a `Dataset` source has none. So the earlier gloss "an accessor …
    → `{}`" holds only for accessors that construct unconditionally (`plot`,
    `str`, measured `{}`), not for `dt` on a non-datetime source.
  * **Output-side, the level-ROSTER name diverts.** The ordinary branch reaches
    the sub-variable roster as `getattr(result, "data_vars", [])` AFTER
    `result.attrs = getattr(x, "attrs", {})`. A `DataArray` has no real
    `data_vars` property, and `AttrAccessMixin.__getattr__`
    (`common.py:270-279`) consults `DataArray._attr_sources`, which yields
    `self.attrs` (`dataarray.py:842-845`). So when `x`'s whole-object mapping
    carries the key `data_vars`, that VALUE is walked in place of the roster.
    Measured: `'temperature'` → `KeyError('t')` (a str iterates per character),
    `['q']`/`'q'`/`{'q':1}` → `KeyError('q')`, `['zz']` → `KeyError('zz')`,
    `5`/`None` → `TypeError` (not iterable). It is a real divergence of the
    patched callee: at `base_commit` the same input returns normally.
    Scoped by measurement: it needs the ORDINARY regime AND a non-`Dataset`
    output. A `Dataset` output is immune (its genuine `data_vars` property
    shadows the lookup), a `Variable` output is immune (no `__getattr__`, so the
    `[]` default is used), and the promotion regime never runs the branch.
    Benign, and therefore still IN domain (measured to satisfy every clause):
    a diverted value that is walkable and every entry of which names a level
    the output carries — `[]`, `''`, `['a']`, `['a','b']`, `('a',)`, `{'a':1}`,
    and a dimension name `['d']`; the coord loop afterwards rewrites those
    levels with the same expression, so the observable result is unchanged.
  * **Prior to both — the three arguments may not COMBINE into anything
    carrying attribute levels.** Whether `cond`, `x` and `y` combine, and what
    shape the combination has, is settled by `apply_ufunc` before any attribute
    is carried over. Measured: the same argument sets fail identically with
    `keep_attrs=False` AND at `base_commit`, so this is a property of the
    argument combination and not of the rebuild. Two sub-cases: arguments that
    raise during combination at all (e.g. `x` a `dict`, or an attrs VALUE used
    as array data — `computation.py:478` `args = tuple(getattr(arg,
    "data_vars", arg) for arg in args)` replaces an ARGUMENT with its attrs
    value in `apply_dataset_vfunc`, so a source whose mapping records
    `data_vars` can have that payload broadcast as DATA), and arguments that
    combine into something with no attribute mapping of any kind (all-scalar /
    all-`ndarray` operands → a bare `numpy.ndarray`, which is the "Domain edge"
    above, now enforced by the same predicate instead of only excluded from
    generation).

**The exclusion is exact in BOTH directions, and enforced rather than assumed.**
The predicate is *not* "every output level name answers on `x`": that form is
itself a NARROWING defect, and an injection control refuted it. WHICH names are
interrogated depends on the regime, so the predicate must too
(`_interrogated_names`, `conformance_check.py`): the output's COORDINATE names
are interrogated in both regimes, but the output's SUB-VARIABLE names are
interrogated only in the ORDINARY regime — in the promotion regime the source
reaches its sub-variable through its own `name` alone and no name-to-mapping
lookup is put at that level. The over-broad form excluded
`promotion, x.name='dt'`, a call the real patched callee DELIVERS
(`promotion, x.name='dt'  C-declines  delivered=True  <<< EXCLUDED BUT
DELIVERED`); with the regime split the same sweep reports `=== FLAGS: 0`.
The corrected predicate — "the arguments combine into an output carrying
attribute levels; every name the routine ACTUALLY INTERROGATES answers on `x`;
and the roster, where it is obtained, is obtained AS a roster (walkable, each
entry naming a level the output carries)" — was validated differentially against
the patched callee over **6 174 constructed calls** spanning attrs keys
`{attr, long_name, units, standard_name, data_vars, coords}` × roster/diversion
payloads × extra coordinate names × DataArray/Dataset/Variable/scalar sources:
**5 638 in-domain with 0 clause failures and 0 in-domain-but-raised; 536
excluded of which 536 genuinely failed to deliver; 0 excluded-but-delivered**
(`A-no-image` 259, `B-roster` 130, `C-name-declines` 147). A second sweep over
~50 exotic shapes (coordinates and data-vars named after every public property
and dunder-ish accessor, non-string and MultiIndex coord names, `Variable`
operands, non-xarray operands) reports `FLAGS: 0`.

**The check FAILS if an excluded call delivers.** `compare()` is ordered domain
first, abstraction second, and `_excluded()` carries the bidirectional
cross-check: an out-of-domain call that the real callee nevertheless completes
is appended as `{"kind": "excluded-but-delivered", ...}` and fails the run.
Injection control: deliberately over-broadening the regime split produced
exactly 1 `excluded-but-delivered`, and over-broadening edge 1 likewise — so the
branch is capable of firing and is not decorative. `_KEYS` /`_ROSTER_KEYS`
(`conformance_check.py`) carry the shadowing roster names so the generator
REACHES the excluded class (the full run records **`out_of_domain: 9700`** of
100 026 inputs, rather than never drawing it), and `axiom_check.py` pins **7
in-domain members of the very shapes it excludes** — including the promoted-`dt`
case, where it asserts the global mapping is `{}`, the named slot carries `x`'s
whole-object mapping, and every coordinate obeys the uniform rule — so a future
edit that re-broadens the exclusion into a narrowing fails the gate.

**Inputs.** The modelled space is infinite (arbitrary attribute mappings), so:
26 boundary cases first — the 7 F2P scenarios verbatim from the test patch, plus
no-coords (empty coord carrier), two distinct coord levels, x-coord-empty /
x-top-empty, a coord absent from x, scalar x, two Datasets with two data vars
each, x-Dataset + y-DataArray, empty-mapping Datasets, five promotion cases
(`named_slot` = 0, 1, -1 via absent name, -1 via scalar x, single-var), and five
NAME-RESOLUTION cases for the §1 rule — an output coordinate named `T` and one
named `variable` (names `x` answers with a derived view of ITSELF, so the level
must take `x`'s own whole-object mapping and NOT `{}`), one named `values` and one
named `zzz` (answered with something carrying no mapping / with nothing, so `{}`),
and one where `x` ALSO carries a coordinate named `T`, which the derived-view
lookup shadows — then 100 000 seeded fuzz cases over the same construction, whose
extra-coordinate name is itself drawn from `{extra, zzz, T, variable, real, imag,
values}` so the class is fuzzed and not only enumerated. **Pinned seed: 7229**
(module constant `SEED`; `N_FUZZ = 100_000`).

**Re-measured verdict: `G-CONF=pass`** — 100 026 inputs (26 boundary + 100 000
fuzz), **0 disagreements, 0 errors**, against the real patched callee
(`meta.json`'s stamp is the authoritative in-container timing).
Coverage: ordinary regime 68 601, promotion regime 21 725 (8 114 with a matching
named data-var, 13 611 without), 32 632 cases with data-vars, 24 456
unmodelled-slot observations all confirmed untouched-vs-baseline, 1 empty-coord
carrier, **5 273 inputs in which at least one level's carrier differs between
the two readings of "x's mapping at this name"** (the `name_resolved_on_x`
counter: the §1 name-resolution class is reached by ~5% of inputs, not just by the
5 boundary cases), and **`out_of_domain: 9 700`** — the excluded class of Domain
edge 2 is now REACHED by ~10% of inputs and cross-checked in both directions on
every one of them, rather than never being drawn.

**Negative control (capable of failing).** Against the UNPATCHED base in the
same container — pre-patch `where` turns `keep_attrs is True` into a single
`lambda attrs, context: getattr(x, "attrs", {})` broadcast to every level — the
check exits 1 with **23 of the 26 boundary cases disagreeing**, including 6 of
the 7 F2P scenarios and all 5 name-resolution cases; the first fuzz case
disagrees too and the "≥ 3 disagreements" abort then stops the sweep, so the run
reports 24 disagreements over 27 inputs. Each comparison family fires: coord
level (pre-patch coord mappings come out as x's top-level mapping), global level
(promotion regime keeps x's top-level mapping instead of emptying it), and the
unmodelled-slot rule (the pre-patch broadcast writes into non-matching slots, so
they diverge from the `apply_ufunc` baseline, abstract to -1 and disagree with
the shadow's 0 — the rule is a real check, not a wildcard). The 3 static
boundary cases are static for stated reasons, measured: `F2P:x scalar` and
`ord:Datasets with empty mappings` because x carries only empty mappings, so the
pre-patch broadcast broadcasts `{}` and that is also what the patched per-level
rebuild computes; `ord:no coords (empty coord carrier)` because the input has no
coordinate and no data-var level at all, leaving only the ordinary-regime top
level, which both readings take from x's whole-object mapping. Scalar x is not a
blind spot of the control — the sibling `F2P:x and y scalar` DOES move, since
with y scalar too nothing conflicts with cond's coordinate mapping in the
pre-patch merge and that coordinate comes out `{'attr': 'cond_coord'}` where the
patched rebuild empties it.
