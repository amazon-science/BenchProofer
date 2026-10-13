# RELAXED_LEAKAGE — pydata__xarray-7229 (nagini)

Disposition: **KEEP with relaxed leakage.** `meta.json` carries
`relaxed_leakage: true` and `gates.G-LEAK.status = "relaxed"`, pointing here.

Describes `model.py` sha256 `91ae5471fb96b2715739edb3d3ddd976d1fc307bdb541cd913d45ff64021c659`
(spec_view `c5792264b219ccb970a1459f877d3cf5256db8943a60974dab87ab4974570ac8`,
recomputed from the shipped file by
`swebench_unified.markers.region_hashes(model.py, nagini)` — the same function
G-HYGIENE records in its own gate `data`; `meta.json`'s TOP-LEVEL
`region_hashes` block is a build-time record of an earlier revision of this
bundle and is not recomputed on a re-gate, so it is that older file's hashes, not
the shipped one's).
Every measurement below was re-run against that exact file; if either hash stops
matching the shipped bundle, this file is stale and its quotes should not be
trusted.

The predecessor two revisions back, `model.py` `53f771bd…` (spec_view
`450b30e7…`), differed from `377052712f…` (spec_view `b07fb799…`, the pair this
file pinned before the refresh recorded in the next paragraph) in the module
**docstring only**: a gloss sentence stating that a level the source does not
carry contributes the empty mapping was false of the real callee, which resolves
a level's name ON the source
(`getattr(getattr(x, name, None), "attrs", {})`), and was corrected. Measured
across that correction: `region_hashes` for `axioms`, `pure`, `pre-conditions`,
`post-conditions`, `invariants` and `impl` are UNCHANGED, only `spec_view` moved,
and `same_spec(model.py, model_prepatch.py)` remains **True** (the identical
correction was made in the twin). So every quotation of a `Requires` / `Ensures`
/ `Invariant` below still quotes the shipped bytes, and no disclosure was added
or removed: the corrected sentence discloses less about the source's structure
than the false one did, since it no longer claims what the source carries.

The step after that -- `377052712f…` to the shipped `91ae5471…` -- is what made
this file stale until the two hashes above were refreshed, and it is recorded
here rather than quietly absorbed, because the staleness clause did its job and
fired. `377052712f…` is a real ancestor, the file at commit `2ca141e69`; it too
differs from the shipped bytes in the module **docstring only**. Re-measured with
`swebench_unified.markers.region_hashes` on both files: `axioms`
(`b78a2051…`), `pure` (`0559ca0b…`), `pre-conditions` (`1eb978e0…`),
`post-conditions` (`3bb952da…`), `invariants` (`a0fdfc47…`) and `impl`
(`2f0e4b8d…`) are byte-identical across the step, all six, and only `spec_view`
moved (`b07fb799…` -> `c5792264…`); `same_spec(model.py, model_prepatch.py)` is
still **True** on the shipped pair. `diff -u` between the two files is 101 lines
-- 72 added, 6 removed, net 66 (259 lines to 325) -- in three hunks spanning the
predecessor's lines 32-37, 41-51 and 56-62, every one of them inside the module
docstring, which ends at line 70 of the predecessor and at line 136 of the
shipped file. So every quotation of a `Requires` / `Ensures` / `Invariant` below
still quotes the shipped bytes. But a docstring-only step lands **entirely** on
`spec_view`, which is precisely the surface the leakage gate and the panel-3 role
measure, so "docstring only" is not by itself a licence: the step added four
whole paragraphs at `model.py:35-83` and extended two more, and one of the four
-- the roster paragraph at `model.py:59-74` -- is a second disclosure needing its
own justification. §7 gives it one.

The lexical screen on the spec view passes (`leakage.screen(...) -> passed=True,
hard_failures=[], warnings=[]`, re-run on the above `model.py`). Counted over
that spec view: `keep_attrs`, `apply_ufunc`, `Dataset`, `isinstance`, `getattr`,
`data_var`, `promot`, `regime`, `rename`, `global`, `patch`, `fix` and `bug` all
appear **0** times, and the patched file path appears 0 times. The only
repository words present at all are the instance id `pydata__xarray-7229` on the
module docstring's first line (the bundle's own identity, which the consumer
already has) and the output class name `WhereResult`; the routine's name is
public in the `problem_statement` title, `` `xr.where(..., keep_attrs=True)`
overwrites coordinate attributes ``. What is disclosed beyond that is
**semantic**, and this file records it, why it cannot be removed, and how the
disclosure was reduced to its irreducible core.

The prepatch-strip test ("delete the clause and see whether the pre-patch twin
starts verifying") does **not** settle unavoidability for this bundle. It was
run and it does not: §4 records the measurement. The load-bearing leg is
FAIL_TO_PASS / G-EQ, in §3. That is the leg for the structural facet of §1. The
second facet, the roster carve-out at `model.py:59-74`, is admitted on a
different leg again -- faithfulness over the domain, measured against the real
callee, not the graded tests -- and §7 states it and says in terms what the strip
test does and does not settle about it.

## 1. What the spec view discloses

`rebuild_attrs` states one uniform rule — each level of the output takes the
mapping of the corresponding level of the source — over three carriers
(`x_attrs`, `x_coord_attrs[k]`, `x_var_attrs[k]`), plus a two-case structural
relation between the source and the output, carried by the parameters
`top_unmatched` and `named_slot` and by three clauses:

```python
Ensures(Implies(not top_unmatched, Result().attrs == x_attrs))
Ensures(Implies(top_unmatched, Result().attrs == 0))
Ensures(Implies(not top_unmatched, Forall(int, lambda k: (
    Implies(0 <= k and k < len(x_var_attrs),
            Result().var_attrs[k] == x_var_attrs[k]),
    [[Result().var_attrs[k]]]))))
Ensures(Implies(top_unmatched and 0 <= named_slot,
                Result().var_attrs[named_slot] == x_attrs))
```

The first half — *rebuild every level from the same-named level of the source,
coordinates included* — is derivable from the public `problem_statement` and is
not a disclosure. The statement itself contrasts two levels and says which way
round they belong ("coordinate attributes are getting overwritten by variable
attributes … Coordinate attributes should be preserved"), so *each level keeps
its own mapping* is the minimal reading of the reported defect, and the
per-sub-variable clause is that same rule at the level the statement names as the
one doing the overwriting. The **second-case sub-behaviour** (when the output
carries a level of named sub-variables the source lacks: the output's top-level
mapping is empty and the source's whole-object mapping goes to the sub-variable
carrying its name) generalises nothing in the statement — it is a structural
exception to the uniform rule, and it is the relaxed disclosure.

It is not the only one. The docstring step recorded at the top of this file put a
second facet on the spec view: the roster paragraph at `model.py:59-74`, which
states how the output's roster of named sub-variables is obtained and which calls
that leaves outside the specified behaviour. It is a separate disclosure with a
separate justification, and it is dispositioned in §7; §§2-4 below concern the
structural facet named in this section.

## 2. The problem_statement ↔ gold mismatch

The public statement reports exactly one behaviour, over a same-type example:

> "`xr.where(..., keep_attrs=True)` overwrites coordinate attributes … coordinate
> attributes are getting overwritten by variable attributes … Coordinate
> attributes should be preserved."
> Example: `xr.where(True, ds.air, ds.air, keep_attrs=True)`.

The gold `xarray/core/computation.py::where` additionally pins a case the public
statement never mentions:

```python
if isinstance(y, Dataset) and not isinstance(x, Dataset):
    result.attrs = {}
    if getattr(x, "name", None) in result.data_vars:
        result[x.name].attrs = getattr(x, "attrs", {})
```

Case-insensitive token counts over this instance's `instance.json`
(`problem_statement` / `hints_text`), re-measured for this file:

| token | problem_statement | hints_text |
|---|---|---|
| `promot` | **0** | 0 |
| `data_var` / `data var` | **0** | 0 |
| `x.name` | **0** | 0 |
| `isinstance` | **0** | 0 |
| `single-variable` / `multi-variable` | **0** | 0 |
| `global` | **0** | 0 |
| `rename` | **0** | 0 |
| `empty` | **0** | 0 |
| `scalar` | **0** | 1 |
| `{}` | **0** | 2 |
| `dataset` | 2 — both unrelated | 2 |
| `coord` | 3 (the public behaviour) | 0 |
| `preserv` | 1 (the public behaviour) | 0 |

Both `dataset` hits in the statement are unrelated, checked in context:
`xr.tutorial.load_dataset("air_temperature")` and the attribute key
`'dataset': 'NMC Reanalysis'` inside a printed `attrs` dump. The structural
two-case relation appears nowhere in the public text; its only homes are the gold
diff and the hidden `test_patch`, whose last case builds its expected object with
no `attrs=` keyword at all — the emptied top-level assertion.

## 3. Why faithful + non-leaking is impossible here

The argument is on the **FAIL_TO_PASS / G-EQ** leg — `verify ⟹ correct` — and both
halves were re-measured for this file, in a `mktemp -d` scratch directory; the
bundle was not modified.

**(a) A spec without the second case admits an implementation that verifies.**
Built `expB_defacet_uniform.py` = the shipped `model.py` with every occurrence of
the structural relation deleted from the contract: `Implies(not top_unmatched,
Result().attrs == x_attrs)` + `Implies(top_unmatched, Result().attrs == 0)`
collapsed to `Result().attrs == x_attrs`; the `not top_unmatched` guard dropped
from the sub-variable `Forall`; the `named_slot` clause removed; the
`top_unmatched`-guarded `Requires` removed — asserted that neither
`top_unmatched` nor `named_slot` survives anywhere between
`# pre-conditions-start` and `# impl-start`. Its implementation takes every level
from the same-index source slot and the top level from the source's whole-object
mapping in **all** cases:

```
$ bash scripts/nagini_verify.sh <scratch>/expB_defacet_uniform.py
Verification successful
Verification took 17.55 seconds.
```

**(b) That implementation's repository counterpart fails the sole F2P test.**
`FAIL_TO_PASS = ["xarray/tests/test_computation.py::test_where_attrs"]`. A copy of
the instance worktree at `base_commit 3aa75c8d00a4a2d4acf10d80f76b937cadb666b7`
with `patch.diff` and the instance `test_patch` applied (both clean) was run
against the real `xarray.core.computation.where`, and against a variant whose
second-case branch is replaced by the ordinary path with the coordinate loop left
byte-intact. Interpreter: numpy 1.26.4 / pandas 2.0.3, transliterated
`test_where_attrs` body with `xarray.testing.assert_identical`.

```
POSITIVE CONTROL (unmodified gold):  F2P: PASS
SECOND CASE REMOVED:                 F2P: FAIL
  Left and right Dataset objects are not identical
  Differing data variables:
  L   x        (a) int64 1 0
      attr: x_da
  R   x        (a) int64 1 0
  Attributes only on the right object:
      attr: x_da
```

So a spec that dropped this sub-behaviour would verify an implementation that
does not pass the instance's test — the exact failure `verify ⟹ correct` forbids.
The disclosure is in the **behaviour**, not in prose that could be deleted.

## 4. The prepatch-strip test does not settle this bundle

The usual unavoidability test is to delete the clause and check whether the
pre-patch twin starts verifying. Run here, it does not, so it neither supports
nor refutes the disclosure; the earlier `velvet/RELAXED_LEAKAGE.md` for this
instance argues unavoidability that way ("removing the promotion facet would make
the prepatch pass and break G-DIFF"), and that argument is **false for this
bundle**. Measured: `expA_defacet_prepatch.py` = the de-faceted contract of
§3(a) with `model_prepatch.py`'s implementation region grafted in verbatim —

```
$ bash scripts/nagini_verify.sh <scratch>/expA_defacet_prepatch.py
Verification failed
Errors:
expA_defacet_prepatch.py:145:13:148:38: error: Postcondition of rebuild_attrs
might not hold. Assertion Forall(int, (lambda k: (Implies(((0 <= k) and
(k < len(x_coord_attrs))), (Result().coord_attrs[k] == x_coord_attrs[k])),
[[Result().coord_attrs[k]]]))) might not hold.
Verification took 29.14 seconds.
```

— i.e. the coordinate clause **alone** rejects the twin, so the twin
discrimination G-DIFF measures survives without the second case. Unavoidability
rests on §3 (F2P / G-EQ) only.

## 5. Requirements check

1. **The core is sound.** Every other gate reaches a pass on the current bundle;
   the recorded stamps in `meta.json` are the authority, and every one of them is
   now stamped against the SHIPPED `model.py` `91ae5471…`: each gate's
   `sources."model.py"` reads that hash, re-checked entry by entry. As recorded
   there: G-VERIFY pass (`verified in 22.9s`, `meta.json:437`), G-DIFF pass
   (`model_prepatch.py: verification failed`, `meta.json:90`, with `same_spec`
   True), G-GOLD pass (`meta.json:124`), G-MUT pass (`killed 20/20 (100%)`,
   `meta.json:202`), G-PBT pass (`SOUND: 10 spec case(s) behaved as expected`,
   `meta.json:403`), G-HYGIENE pass, G-INTEGRITY pass (`instance.json`
   byte-identical, additions-only, `meta.json:165`), G-CONF pass (100026 inputs,
   0 disagreements, 0 errors, the real patched callee called as oracle,
   `meta.json:72`), G-AX pass, G-RESOLVE resolved (`meta.json:421`), G-EQ pass
   (17 admissible attacks re-run of 17 submitted, none breaks the spec,
   `meta.json:108`), and G-PANEL pass with G-PANEL-1 `SOUND` (`meta.json:271`),
   G-PANEL-2 `FAITHFUL` (`meta.json:284`, status `pass` at `meta.json:293`,
   `sources."model.py"` `91ae5471…` at `meta.json:291`) and G-PANEL-3 pass. The
   earlier revisions this log tracks -- `f0667750`, `53f771bd`, `377052712f…` --
   are no longer the files any gate is stamped against; what carries their
   measurements forward is the region-hash invariance recorded in the notes at
   the top, `pre-conditions` / `post-conditions` / `invariants` / `impl` being
   byte-for-byte identical at every step from `53f771bd` to the shipped file (the
   `53f771bd` → `377052712f…` step is recorded there, the `377052712f…` →
   `91ae5471…` step re-measured there), with only the docstring, and hence only
   `spec_view`, ever moving. Measured, not asserted, for the `f0667750` →
   `53f771bd` step: tokenizing both files, dropping comments and docstrings and
   applying the two renames (`promoted_idx`→`named_slot`, `promote`→
   `top_unmatched`) makes the token streams **identical**, so no `Requires` /
   `Ensures` / `Invariant` and no line of either implementation region changed
   between the audited file and the shipped one.
2. **The leak is genuinely unavoidable**, on the F2P/G-EQ leg established in §3
   by two independent measurements, with the competing prepatch-strip rationale
   explicitly refuted in §4. That covers the structural facet. The second facet,
   the roster carve-out at `model.py:59-74`, is unavoidable on the FAITHFULNESS
   leg instead, and §7 establishes it separately: the carve-out is what keeps the
   modelled routine total over the inputs the real callee raises on, the formal
   `Requires` carry no equivalent, and §7 also records that the prepatch-strip
   test is silent about it rather than supporting it.
3. **The disclosure is minimised.** The prose of the spec region was rewritten to
   state the contract as one uniform level-correspondence rule instead of
   narrating two named regimes and what the output is "never" allowed to be.
   Removed: the regime labels and the "because the THIRD argument forced it"
   causal aside; the "in short … are NEVER all overwritten … not blindly at the
   output's top level when the output was promoted" paragraph, which told the
   reader which of two candidate behaviours to choose; and the axiom-region
   sentence describing the modelled behaviour as a change. Also removed as
   unfaithful, not merely as narration: the parenthetical claiming the output's
   other sub-variable slots take the empty mapping — measured against the real
   callee those slots keep what the upstream combination produced and are
   observably non-empty, so the contract now says it makes no claim about them.
   Finally the two parameters were renamed away from the repository's own word
   for the case (`promote` → `top_unmatched`, `promoted_idx` → `named_slot`) and
   the remaining "regime"/"promotion" comments were reworded, so nothing in the
   spec view names the mechanism. Every `Requires` / `Ensures` / `Invariant`,
   both signatures and both implementation regions are byte-identical up to those
   renames across the whole change; `model.py` and `model_prepatch.py` remain
   `same_spec`.

   One later docstring correction belongs in this log, because minimisation is no
   licence to be wrong: the gloss "a level of the output the second argument does
   not carry contributes the empty mapping" was concise but **false** of the real
   callee, which resolves an output level's name on the source object itself, so a
   name the source answers with a derived view of itself contributes the source's
   own whole-object mapping instead. That sentence was replaced by the accurate
   rule, in both twins identically. The replacement is longer prose that discloses
   no more: it names no repository symbol, no file and no attribute; measured over
   the corrected spec view, `keep_attrs`, `apply_ufunc`, `Dataset`, `isinstance`,
   `getattr`, `data_var`, `promot`, `regime`, `rename`, `global`, `patch`, `fix`
   and `bug` each still appear **0** times, and `leakage.screen(...)` still
   returns `passed=True, hard_failures=[], warnings=[]`.

   The same applies to the docstring step that produced the shipped file. It is
   the largest addition in this log -- 72 lines added against 6 removed, measured
   above -- and minimisation does not license shortening it back, for the reason
   §7 gives: the paragraphs fix the DOMAIN the `Requires` are claims about, and
   the `Requires` do not fix it themselves. Re-measured on the shipped spec view,
   the whole thirteen-token list above still stands at **0** each, and so do
   `coords`, `default`, `KeyError` and `crash`; `leakage.screen(...)` still
   returns `passed=True, hard_failures=[], warnings=[]`. The one word the step
   adds is `roster`, this file's and the docstring's own abstract term for the
   thing, which is not the repository's name for it.
4. **Documented in-bundle** (this file), which `G-INTEGRITY` allowlists.

## 6. What remains disclosed, precisely

That the routine distinguishes two structural relations between the source and
the output, and that in the second one the output's top-level mapping is empty
while the source's whole-object mapping lands on the output sub-variable carrying
its name. Nothing about the repository symbol, the file, the combination
mechanism, or the type test that selects the case is named in the spec view; the
parameters are stated as an abstract structural relation over integer attribute
identities.

And, since the docstring step recorded at the top of this file, one further thing:
that the output's roster of named sub-variables is itself obtained by a
whole-object interrogation of the OUTPUT under the roster's own name, at a point
where the output already carries the source's whole-object mapping, so that a
source whose mapping records an entry under that name can put a bogus roster in
place of the real one. That is the whole of the second facet, and §7 dispositions
it. Like the first it names no repository symbol, no file, no attribute key and
no type test: measured over the shipped spec view, `data_var`, `getattr`,
`coords`, `default`, `KeyError` and `crash` each appear **0** times, and the one
word carrying the facet, `roster`, appears **0** times in the `problem_statement`
and **0** times in `hints_text`, so it is this specification's own abstract term
and not the repository's.

## 7. The roster carve-out is faithfulness-forced, not test-forced

The docstring step recorded at the top of this file added four whole paragraphs
to the module docstring, at `model.py:35-83`, and one of the four is a disclosure
that §§1-4 do not reach: the
roster paragraph at `model.py:59-74`. It states that the routine has to obtain
the output's roster of named sub-variables in order to visit them, that it
obtains it by the same kind of whole-object interrogation of the OUTPUT under the
roster's own name, at a point where the output already carries the source's
whole-object mapping, and that a source whose whole-object mapping happens to
record an entry under that name can therefore cause a bogus roster to be visited
in place of the real one -- with calls whose substituted answer cannot be walked,
or names something the output does not carry, left OUTSIDE the specified
behaviour. Those 16 lines occur as a contiguous substring of
`swebench_unified.markers.spec_view(model.py, nagini)`, checked directly, so the
paragraph is on the surface this gate measures and it needs a disposition of its
own rather than the one §3 gives the structural facet.

Its disposition is **FAITHFULNESS-FORCED, not test-forced**. The carve-out is
what makes the modelled routine TOTAL over exactly the inputs the real callee
raises on. The measurement is G-PANEL-2's, taken against the shipped bytes and
read back here rather than re-derived: over a probe of 6000 draws, **5201** inputs
COMBINE -- the same call with `keep_attrs=False` succeeds with attribute levels --
and of those the `keep_attrs=True` call raised on **118**, every one of the 118
covered by a carve-out the docstring states explicitly, either a declined name
interrogation or a non-walkable/bogus roster, for **0** genuine totality
violations (`meta.json` `gates."G-PANEL-2".note`, item 6, at `meta.json:289`,
copied into the panel rollup at `meta.json:238` and published at `verdict.md:673`,
Role 3 item 6). The bogus-roster half was probed
directly rather than assumed: shadowing the source's own mapping under the
roster's name with `['a']`, `[]`, `'a'` and `['a','a']` leaves every clause
holding, while `['nope']` and `5` raise, which is the carve-out's negative side
and the reason its positive side is not an over-claim (same note, item 7). That
role records `agent_verdict: FAITHFUL` (`meta.json:284`) and `status: pass`
(`meta.json:293`) against `sources."model.py"` `91ae5471…` (`meta.json:291`) --
the shipped file, not an ancestor.

The formal contract carries no equivalent. `rebuild_attrs`'s entire
`pre-conditions` region is four `Requires`: two list permissions at 1/2, one bound
on `named_slot` under `top_unmatched`, and `MustTerminate(6)`
(`model.py:192-206`). Recomputed over the marked regions of the shipped file, the
words `roster`, `walk` and `declin` appear **0** times in `axioms`, `pure`,
`pre-conditions`, `post-conditions`, `invariants` and `impl` alike. So nothing in
the contract excludes a bogus roster, and the admissibility is carried by the
docstring or by nothing. The same docstring step makes the coupling explicit in
the artifact: it also rewrote the totality paragraph, now at `model.py:94-103`,
from the unscoped "This rebuilding is a TOTAL operation: for every admissible
input it runs to completion" of `377052712f…` to "On the calls the two paragraphs
above leave inside the specified behaviour, this rebuilding is a TOTAL
operation", adding that "Totality is a promise about that domain and is not a
claim that a result exists for the interrogations described above as unanswered
or as answered with a bogus roster". That rewrite is hunk 2 of the 101-line diff
measured above, so the roster paragraph and the totality promise arrived as one
change, and deleting the first leaves the second unscoped.

A spec that dropped the paragraph would therefore take one of two losses, and
there is no third option. Either it keeps `MustTerminate(6)`
(`model.py:205`), whose stated force is that the postconditions are promised of
EVERY run rather than only of runs reaching a result, and then it promises
totality over 118 measured inputs on which the patched library does not return at
all -- an over-claim against the reference. Or it keeps the domain honest by
letting those inputs in, and then it admits an implementation that returns a
result where the patched library raises, which is a divergence from the patched
library on those same 118 inputs. Either way the spec stops being faithful, and
G-PANEL-2's totality leg is what is stranded.

**What the strip test settles, and what it does not.** The prescribed
unavoidability test was run on exactly this paragraph, and its outcome is recorded
in this cell's own audit record, at `verdict.md:731`, inside Role 4's
`Counterexample / evidence` block: `strip_narration.py` -- the shipped
`model.py` with the added
docstring paragraphs deleted and nothing else touched, region hashes for
`axioms` / `pure` / `pre-conditions` / `post-conditions` / `invariants` / `impl`
all unchanged -- still verifies, and `strip_narration_prepatch.py` -- the same
stripped docstring with `model_prepatch.py`'s implementation region grafted in,
`same_spec` True -- still FAILS, on `Implies(top_unmatched, Result().attrs == 0)`.
Read for what it measures, that settles exactly one thing: the paragraph is **not**
needed for the pre-patch twin to be rejected, so it earns nothing from G-DIFF and
nothing from the graded tests. A reader who concluded that the graded tests force
this paragraph would be wrong, and this file does not claim they do -- just as §4
declines the same argument for the other facet. What the strip test cannot see is
the DOMAIN: it compares two artifacts carrying identical `Requires`, so deleting
prose that fixes which inputs those `Requires` are claims ABOUT changes no proof
obligation the verifier discharges, while changing what the specification asserts
about the real callee. Totality over a domain is not a fact any single verifier
run reports. It is what G-PANEL-2 measured against the library, and it is the leg
this paragraph stands on.

**What a reader can re-run.** `swebench_unified.markers.region_hashes(model.py,
nagini)` for the two hashes pinned at the top of this file and for the six regions
unchanged across the last step; `swebench_unified.markers.spec_view(model.py,
nagini)` to confirm `model.py:59-74` is inside the measured surface;
`swebench_unified.leakage.screen(model.py, nagini, patch, problem_statement,
test_patch)` for `passed=True, hard_failures=[], warnings=[]` on the shipped file;
items 6 and 7 of `gates."G-PANEL-2".note` in `meta.json` for the 5201 / 118 / 0
totality figures and for the bogus-roster probe; the four `Requires` at
`model.py:192-206` for the absence of any formal counterpart; and a token count
over the instance's `problem_statement` and `hints_text` for `roster` at **0** in
both, which is why the paragraph is not derivable from the public text and needs
this admission at all.
