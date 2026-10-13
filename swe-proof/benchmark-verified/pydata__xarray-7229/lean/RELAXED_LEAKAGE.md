# RELAXED_LEAKAGE — pydata__xarray-7229 (lean)

Disposition: **KEEP with relaxed leakage.** `meta.json` carries
`relaxed_leakage: true` and `gates.G-LEAK.status = "relaxed"`, pointing here.

Describes `Solution.lean` sha256
`880d1f91a65b89974c6fa12076456c794b1a609384fcbf4dad6c98a2d2ffde82`, whose spec
view (`swebench_unified.markers.spec_view(Solution.lean, lean)`) is 170 lines,
sha256 `aa5d7b44edf16a6a95e0f0f94ed56da5548dd9d9d4e6b9881c284402ca63c000`.
Region hashes recomputed from the shipped file by
`markers.region_hashes(Solution.lean, lean)` — the same function G-HYGIENE
records in its own gate `data`, which matches on all six:

| region | sha256 (first 16) |
|---|---|
| `axioms` | `392d0bd933569869` |
| `pure` | `25e99c6fb9a8f58c` |
| `post-conditions` | `903f669a40e59359` |
| `impl` | `f5579ae4390a0563` |
| `proof` | `b3081002cd482e9f` |
| `spec_view` | `aa5d7b44edf16a6a` |

`meta.json`'s TOP-LEVEL `region_hashes` block is a build-time record of an
earlier revision of this bundle and is not recomputed on a re-gate, so its
entries are that older file's hashes, not the shipped one's; only
`markers.region_hashes` (what G-HYGIENE records) tracks disk. Every measurement
below was re-run against the exact file named above. If either hash stops
matching the shipped bundle, this file is stale and its quotes should not be
trusted.

`markers.same_spec(Solution.lean, Solution_prepatch.lean, lean)` = **True**: the
two twins are byte-identical through line 162, so every clause quoted below
quotes both.

This file describes the LEAN leg only. The sibling `velvet/RELAXED_LEAKAGE.md`
describes a different modeled method (`rebuildAttrs`) and the sibling
`nagini/RELAXED_LEAKAGE.md` describes `model.py` sha `377052712f22…`; neither is
a claim about this spec view and neither is inherited here. §4 records a
measurement that contradicts velvet's stated unavoidability rationale for this
bundle.

The lexical screen on the spec view passes:
`leakage.screen(Solution.lean, lean, gold_patch, problem_statement)` →
`passed=True, hard_failures=[], warnings=[]`, re-run against the above file. It
passes for structural reasons, not because there is nothing to record:
`leakage._patch_changed_symbols(patch)` = `{'where'}`, which is public in the
`problem_statement` title, and the tokens `xarray`, `Dataset`, `isinstance`,
`getattr`, `data_vars`, `apply_ufunc`, `keep_attrs`, `promot`, `patch`, `fix` and
`bug` appear **0** times in the view, as does the patched file path
`xarray/core/computation.py`. What is disclosed is **semantic**, and the screen
is blind to it. This file records what that disclosure is, why it cannot be
removed, and what it does not cover.

The prepatch-strip test ("delete the clause and see whether the pre-patch twin
starts verifying") does **not** settle unavoidability for this bundle. It was
run and it does not: §4 records the measurement. The load-bearing leg is
FAIL_TO_PASS / `verify ⟹ correct`, in §3.

## 1. What the spec view discloses

Two places in the view state one structural exception to an otherwise uniform
rebuild rule.

Prose, view lines 36–42:

> There is one special shape: when the third argument `b` is a container object
> but the second argument `a` is not, the result is a container into which `a` is
> promoted as a single data variable. In that shape the result's top-level bag is
> emptied, only the data variable matching `a`'s own name receives `a`'s
> top-level bag (every other data variable keeps whatever bag the combination
> routine gave it), and the coordinate components are still rebuilt by resolving
> their names against `a` exactly as above.

Executable, view lines 125–134, inside `retainedResult` (the `pure` region, which
the view keeps):

```lean
  else if b.isContainer && !a.isContainer then
    -- promotion shape: `a` becomes a single data variable in a container result
    let dvs :=
      match a.name with
      | some nm =>
          r.dataVars.map (fun c => if c.name == nm then { c with attrs := a.topAttrs } else c)
      | none => r.dataVars
    { r with topAttrs := []
           , dataVars := dvs
           , coords := rebuildFrom a r.coords }
```

The surrounding rule — *rebuild each level of the result from the same-named
level of the second argument, coordinates included* — is derivable from the
public `problem_statement` and is not a disclosure. The statement contrasts two
levels and says which way round they belong ("coordinate attributes are getting
overwritten by variable attributes … Coordinate attributes should be
preserved"), so *each level keeps its own mapping* is the minimal reading of the
reported defect. The **structural exception** above generalises nothing in the
statement, and it is the relaxed disclosure.

## 2. The problem_statement ↔ gold mismatch

The public statement reports exactly one behaviour, over a same-type example:

> "`xr.where(..., keep_attrs=True)` overwrites coordinate attributes … coordinate
> attributes are getting overwritten by variable attributes … Coordinate
> attributes should be preserved."
> Example: `xr.where(True, ds.air, ds.air, keep_attrs=True)`.

The gold `xarray/core/computation.py::where` additionally pins a case the public
statement never mentions (post-patch lines 1880–1884, re-derived by applying
`patch.diff` in the instance image):

```python
if isinstance(y, Dataset) and not isinstance(x, Dataset):
    # handle special case where x gets promoted to Dataset
    result.attrs = {}
    if getattr(x, "name", None) in result.data_vars:
        result[x.name].attrs = getattr(x, "attrs", {})
```

Case-insensitive token counts over this instance's `instance.json`, re-measured
for this file:

| token | problem_statement | hints_text | present in spec view |
|---|---|---|---|
| `promot` | **0** | 0 | yes |
| `special shape` | **0** | 0 | yes |
| `data_var` / `data variable` | **0** | 0 | yes |
| `container` | **0** | 0 | yes |
| `x.name` / `own name` | **0** | 0 | yes |
| `emptied` | **0** | 0 | yes |
| `isinstance` | **0** | 0 | no |
| `single-variable` / `multi-variable` | **0** | 0 | no |
| `coord` | 3 (the public behaviour) | 0 | yes |
| `preserv` | 1 (the public behaviour) | 0 | — |

`Dataset` case-sensitively: **0** occurrences in the statement. The two
case-insensitive `dataset` substrings were checked in context and are unrelated:
`xr.tutorial.load_dataset("air_temperature")` and the attribute key
`'dataset': 'NMC Reanalysis'` inside a printed `attrs` dump. `hints_text` adds
nothing on this facet. The structural exception's only homes are the gold diff
and the hidden `test_patch`, whose last case builds its expected object with no
top-level `attrs=` keyword at all.

## 3. Why faithful + non-leaking is impossible here

The argument is on the **FAIL_TO_PASS / `verify ⟹ correct`** leg, and both halves
were re-measured in a `mktemp -d` scratch directory; the bundle was not modified
and the repository working tree was not written.

**(a) The clause cannot be removed from the spec while keeping the gold
implementation.** `A_specstrip.lean` = the shipped `Solution.lean` with ONLY the
`else if b.isContainer && !a.isContainer then …` branch deleted from
`retainedResult`; the impl and proof regions are byte-unchanged.

```
$ bash scripts/lean_verify.sh <scratch>/A_specstrip.lean 400
... error: unsolved goals / rfl failed
EXIT=1
```

The residual goal shows the promotion-shape left side against the uniform-rebuild
right side. So the gold-faithful implementation does not verify against a
promotion-free spec — G-GOLD would fail.

**(b) A spec without the clause admits an implementation that verifies.**
`B2_bothstrip.lean` = the same promotion-free spec with the impl region also
de-faceted (the `if b.isContainer && !a.isContainer` dispatch replaced by the
ordinary path alone, coordinate rebuild intact) and the proof adjusted:

```
$ bash scripts/lean_verify.sh <scratch>/B2_bothstrip.lean 400
EXIT=0
```

**(c) That implementation's repository counterpart fails the sole F2P test.**
`FAIL_TO_PASS = ["xarray/tests/test_computation.py::test_where_attrs"]`. Measured
in image `swebench/sweb.eval.x86_64.pydata_1776_xarray-7229:latest` against
`/testbed` at `base_commit 3aa75c8d00a4a2d4acf10d80f76b937cadb666b7` with
`patch.diff` and the instance `test_patch` applied (both `git apply --check`
clean):

```
POSITIVE CONTROL (unmodified gold):
$ python -m pytest xarray/tests/test_computation.py::test_where_attrs -x -q
1 passed in 0.86s

STRUCTURAL EXCEPTION REPLACED BY THE ORDINARY PATH (coordinate loop byte-intact):
$ python -m pytest xarray/tests/test_computation.py::test_where_attrs -x -q
1 failed
  test_computation.py:1984: AssertionError
  Left and right Dataset objects are not identical
  Differing data variables:
  L   x        (a) int64 1 0
      attr: x_da
  R   x        (a) int64 1 0
  Attributes only on the right object:
      attr: x_da
```

The failing assertion is the F2P's own last block,
`xr.where(cond, x.rename("x"), ds_y, keep_attrs=True)`.

Composing (b) and (c): a spec that dropped this sub-behaviour would verify an
implementation whose repository counterpart does not pass the instance's test —
the exact pairing `verify ⟹ correct` forbids, and the hole G-EQ and G-PANEL-1
exist to catch. The disclosure is in the **behaviour**, not in prose that could
be deleted; and prose-only softening would not reduce it either, because
`retainedResult` at view lines 125–134 states the same branch as executable code
that the view retains.

## 4. The prepatch-strip test does not settle this bundle

The usual unavoidability test is to delete the clause and check whether the
pre-patch twin starts verifying. Run here, it does not.
`C_nopromo_prepatch.lean` = the promotion-free spec of §3(a) with
`Solution_prepatch.lean`'s implementation region grafted in verbatim and the
`sorry` replaced by a real tactic attempt:

```
$ bash scripts/lean_verify.sh <scratch>/C_nopromo_prepatch.lean 400
error: Tactic `rfl` failed: The left-hand side
  ... dataVars := List.map (fun c => { name := c.name, attrs := a.topAttrs }) ...
      coords   := List.map (fun c => { name := c.name, attrs := a.topAttrs }) ...
EXIT=1
```

The coordinate clause **alone** rejects the twin, so the twin discrimination
G-DIFF measures survives without this facet. Unavoidability rests on §3 only.
`velvet/RELAXED_LEAKAGE.md` for this instance argues unavoidability the other way
("removing the promotion facet would make the prepatch pass and break G-DIFF");
that argument is **false for this bundle**, which is why this file does not
reuse it.

## 5. Which disclosures this relaxation covers, and which it does not

Minimisation is bounded here by faithfulness: each row below was checked for
whether it is publicly derivable or forced by agreement with the real callee.
One row is the relaxed disclosure; the other five are not disclosures of the
gold's shape.

| view lines | disclosure | status |
|---|---|---|
| 22–28, 98 | the combination routine is handed the retention flag | public: the pre-patch source already passes `keep_attrs=keep_attrs` into that call (`computation.py:1865-1874` at base), and the patch leaves all seven call arguments untouched |
| 26–27, 123–124 | flag false → the combined object is returned verbatim | public: pre-patch behaviour, unchanged by the patch |
| 30–34, 44–47, 136–138 | rebuild from the SECOND argument, component by component, coordinates by name | PS-derivable: the statement's title plus "Coordinate attributes should be preserved", and the base docstring at `computation.py:1792` already says "If True, keep the attrs of `x`" |
| 12–20, 102–112 (`reserved`, `lookupAttrs`) | resolution consults the object's own reserved answers before its like-named components | forced by faithfulness, not by the patch. The real expression `getattr(getattr(x, nm, None), "attrs", {})` reads the name ON the object, so a name the class answers with a view of the whole object contributes that object's top-level bag. Measured: a coordinate named `real` on the second argument yields the second argument's TOP-LEVEL bag, not the coordinate's own. Not an F2P discriminator — the F2P's coordinate is named `a`, which no class answers |
| 49–62, 143–144 (`produces`) | some inputs yield no object at all | a partiality binder. It records that raise-vs-return is not a function of the data this record carries; it discloses no shape of the patch |
| **36–42, 125–134** | **the structural exception of §1** | **the relaxed disclosure** |

Two facets of the exception were checked for whether a less disclosing form is
available, and neither is:

* Restating the guard on the RESULT (`r.isContainer && !a.isContainer`) instead
  of on the third argument would be **unfaithful**. Measured on gold in the
  image, with the first argument a Dataset and the other two plain arrays: the
  result IS a container (`type(result) == Dataset`) while
  `isinstance(y, Dataset)` is `False`, and the real call takes the OTHER branch —
  `result.attrs == {'attr': 'x_da'}` (not emptied), the data variable `v` `{}`,
  the coordinate `a` `{'attr': 'x_coord'}`. A result-side guard would predict an
  emptied top-level bag there and disagree with the callee.
* "every other data variable keeps whatever bag the combination routine gave it"
  is the accurate statement and is weaker than naming a value: the real branch
  writes only `result[x.name]`, so the other slots keep what the upstream
  combination produced and are observably non-empty. Claiming they take the empty
  bag would be shorter and wrong.

## 6. Requirements check

1. **The core is sound.** The recorded stamps in `meta.json` are the authority.
   Against this exact `Solution.lean` `880d1f91…`: G-VERIFY pass (5.2s, 1
   `correct_*` theorem closed, axioms clean), G-DIFF pass
   (`Solution_prepatch.lean`: verification failed, with `same_spec` True), G-GOLD
   pass, G-MUT pass (20/20, 100%), G-PBT pass (SOUND, 13 spec cases),
   G-HYGIENE pass, G-INTEGRITY pass (`instance.json` byte-identical,
   additions-only), G-CONF pass (120000 inputs, seed 7229, 0 disagreements),
   G-AX pass (skip: no consumed callee axiom — `select_combine` is an
   A-reference, the unchanged `apply_ufunc` combine), G-RESOLVE resolved, G-EQ
   pass (23 admissible attacks re-run of 23 submitted, none breaks the spec;
   positive control verifies), G-PANEL-1 pass, G-PANEL-2 pass.
2. **The leak is genuinely unavoidable**, on the F2P / `verify ⟹ correct` leg
   established in §3 by three measurements, with the competing prepatch-strip
   rationale explicitly refuted in §4.
3. **The disclosure is minimised to its irreducible core**, bounded by
   faithfulness: §5 records the two candidate reductions that were measured
   against the real callee and rejected as inaccurate, and the five view facets
   that are public, PS-derivable or faithfulness-forced rather than disclosures
   of the gold's shape. Nothing in the view names the repository symbol beyond
   the public routine name, the file, the type test that selects the case, or the
   combination mechanism; the exception is stated as an abstract structural
   relation over containers and named components.
4. **Documented in-bundle** (this file), which `gates/integrity.py` allowlists.

## 7. What remains disclosed, precisely

That the routine distinguishes one structural relation between its second and
third arguments — third a container, second not — and that in that relation the
result's top-level bag is emptied while the second argument's top-level bag lands
on the result's data variable carrying its name, the remaining data variables
being left as the combination routine produced them. Nothing about the
repository's own type test, the module, the combination mechanism, or the name of
the container class is named in the spec view.
