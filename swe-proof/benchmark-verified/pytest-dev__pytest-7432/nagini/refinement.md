# refinement.md — pytest-dev__pytest-7432

The operation-by-operation correspondence between `model.py`'s implementation
(the `finalize_skip_location` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (the proof uses an
axiom's `Ensures`), **A-reference** (a deep model validated == a real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change — `pytest_runtest_makereport` (`src/_pytest/skipping.py:294`)

Gold hunk (the only change):
```
             else:
                 rep.outcome = "passed"
                 rep.wasxfail = xfailed.reason
-    elif (
+
+    if (
         item._store.get(skipped_by_mark_key, True)
         and rep.skipped
         and type(rep.longrepr) is tuple
     ):
```

i.e. the skip-location-correction block, previously the final `elif` of the
outcome-classification `if/elif` chain, becomes an independent `if`. Its body
(the location rewrite) is unchanged.

| # | model.py impl op (`finalize_skip_location`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| 1 | `if unexpected_success: rep.explanation = EXPLANATION_UNEXPECTED_SUCCESS; rep.explanation_reason = success_reason; rep.outcome = OUTCOME_FAILED` | `if unexpectedsuccess_key in item._store and rep.when == "call": reason = item._store[unexpectedsuccess_key]; rep.longrepr = "Unexpected success: {}".format(reason) / "Unexpected success"; rep.outcome = "failed"` (branch 1, skipping.py:266-272) | R + I | the predicate is R-refined to a `bool` (mapping.md §2); the **outcome effect** is R-refined (`"failed"` ↔ `OUTCOME_FAILED`) and reproduced (**I**). The `longrepr` write is *also* reproduced, at the granularity of mapping.md §2: WHICH standard verdict is stated (`EXPLANATION_UNEXPECTED_SUCCESS` ↔ the `"Unexpected success…"` template, :269/:271) and WHICH reason it interpolates (`success_reason` ↔ `item._store[unexpectedsuccess_key]`, :267). The *wording* of the template, and the `if reason:` choice between the two spellings, are presentation and are abstracted away (both spellings state the same verdict about the same recorded reason). Control-flow position (first branch) is **I**. |
| 2 | `elif suppress_xfail_reporting: pass` | `elif item.config.option.runxfail: pass  # don't interfere` (branch 2, skipping.py:273) | R + I | `--runxfail` toggle R-refined to a `bool`; body is literally `pass` in the repo (**I**). Its behavioural content is *twofold* and both parts are modelled: it changes nothing itself, **and** by occupying a chain position it shields the later classification cases. This is the branch whose `elif` linkage previously also suppressed the location correction. |
| 3 | `elif xfail_exception: rep.xfail_note_present = True; rep.note_reason = raised_reason; rep.note_style = NOTE_STYLE_LEAD_IN; rep.outcome = OUTCOME_SKIPPED` | `elif call.excinfo and isinstance(call.excinfo.value, xfail.Exception): rep.wasxfail = "reason: " + call.excinfo.value.msg; rep.outcome = "skipped"` (branch 3, skipping.py:275-278) | R + I | predicate R-refined to a `bool`; the four effects R-refine as `"skipped"` ↔ `OUTCOME_SKIPPED`, *the presence of* the `wasxfail` annotation ↔ `xfail_note_present`, *which reason it carries* ↔ `note_reason == raised_reason` (`call.excinfo.value.msg`, :277), and *the style it renders that reason in* ↔ `note_style == NOTE_STYLE_LEAD_IN` — the `"reason: " + …` form of :277, as against the bare reason the mark arms write at :286/:293 — per mapping.md §2. Both the annotation's **origin** and its **rendering** are pinned: an implementation annotating with the mark's reason instead of the raised one is rejected, and so is one that reads the raised reason without this arm's lead-in (`test_xfail_imperative` matches `"*reason:*hello*"` on the line `terminal.py:1104` prints from this very string). This branch states no verdict, and that too is pinned — it leaves `rep.longrepr` alone, so the account the run produced there survives. Chain position **I**. |
| 4 | `elif (not rep_already_skipped) and xfailed_present:` with the four-way sub-classification on `exception_raised` / `xfail_raises_mismatch` / `phase_is_call` / `xfail_strict` | `elif not rep.skipped and xfailed:` and its nested arms (branch 4, skipping.py:279-293) | R + I | predicate R-refined (`not rep_already_skipped and xfailed_present` ↔ `not rep.skipped and xfailed`). Each of the four repo arms is reproduced in **every** slot it writes: raises-mismatch → `failed`, nothing else (:283); raises-match → `skipped` + annotation carrying `xfailed.reason` (:285-286); strict xpass → `failed` **and the stated verdict** `"[XPASS(strict)] " + xfailed.reason` ↔ `explanation == EXPLANATION_STRICT_UNEXPECTED_PASS and explanation_reason == declared_reason` (:289-290); non-strict xpass → `passed` + annotation carrying `xfailed.reason` (:292-293). The strict arm's `longrepr` write is not optional detail: it is what distinguishes a strict xpass from an ordinary failure, and the P2P suite reads that very string (see "Why the earlier branches…" below). The fifth, implicit arm (an exception-free non-`call` phase) does nothing, and is likewise modelled as doing nothing — in all five slots. Chain position **I**. |
| 4b | the two reads of the report's skipped state (`rep_already_skipped` in step 4, `rep_skipped` in step 5) | `not rep.skipped` (:279) and `rep.skipped` (:296) — two separate reads of a mutable attribute | R | the repo re-reads `rep.skipped` after the classification may have reassigned `rep.outcome`, so the two reads can disagree. They are therefore carried by **two distinct parameters**, not one: collapsing them would make the model unable to express the real system's behaviour on any input where the classification changes the outcome to `skipped`. G-CONF derives the second read from the classified outcome rather than generating it freely, for exactly this reason. |
| 5 | `if skipped_by_mark and rep_skipped and rep.loc_is_triple:` (a SEPARATE `if`, not `elif`) | `if (item._store.get(skipped_by_mark_key, True) and rep.skipped and type(rep.longrepr) is tuple):` (the patched independent `if`) | R + I | the three predicates R-refine to `skipped_by_mark`, `rep_skipped`, `rep.loc_is_triple` (mapping.md §1–2); the **structural change is the `elif`→`if` split**, reproduced identically (**I**) — the block no longer hangs off the chain. |
| 6 | `assert definition_line is not None; rep.loc_file = definition_file; rep.loc_line = definition_line + 1` | `_, _, reason = rep.longrepr; filename, line = item.reportinfo()[:2]; assert line is not None; rep.longrepr = str(filename), line + 1, reason` (skipping.py:302-305 @ base) | R + I | the location rewrite, element for element. The line element becomes `line + 1` (`definition_line` ↔ `line`, R, mapping.md §2); the file element becomes `str(filename)` from the same `reportinfo()` pair (↔ `definition_file`); the reason element is re-emitted unchanged (↔ the `loc_reason == Old(loc_reason)` conjunct). All three are pinned rather than carried implicitly: "the correction moves where the report points and changes nothing about what it says" is a claim about this function, and a rewrite that pointed at some other file, or dropped the skip reason, would otherwise verify. `assert line is not None` (`:304`) ↔ the model's `assert definition_line is not None` at the SAME position — inside the correction's guard — discharged by the conditioned availability precondition `Requires(Implies(skipped_by_mark and rep_skipped and rep.loc_is_triple, definition_line is not None and definition_line >= 0))`. The placement is load-bearing and is itself part of the refinement: the repo asks `reportinfo()` for the definition location *inside* the `type(rep.longrepr) is tuple` guard (`:297`) and the assert therefore claims only that the reports reaching the correction can be located in source, not that every report can. Modelling it as an unconditional `definition_line >= 0` precondition would say the latter, which is false of the repo (`Item.reportinfo` answers `line = None`, `nodes.py:654-655`) and would admit an implementation that reads the definition line before the guard — whose faithful patch must hoist the `reportinfo()`/`assert` pair out of the guard and then leaves the two `MyItem` reports of `test_skipping.py:1064`/`:1139` unfinalised. The arithmetic `+ 1` is **I**. |

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — the
`elif`→independent-`if` restructuring of the location-correction block — is an
ordinary control-flow operation Nagini expresses directly, so it is modelled
**deeply** (the impl region literally is the branch chain followed by a separate
`if`), not hidden behind any axiom. There is **no consumed axiom and no
A-reference deep model**: the changed function calls no opaque callee that the
proof depends on.

### Why the earlier branches are modelled with their effects, not as `pass`

The F2P test observes only the corrected location, so it is tempting to model
branches 1–4 as bare `pass` and pin only `loc_line`. That is unsound as a
*specification*, and demonstrably so: with those bodies empty and no clause
constraining the outcome, an implementation may drop, reorder or merge the
classification cases and still satisfy every postcondition — while the
corresponding repository edit deletes real expected-failure handling that the
**PASS_TO_PASS** suite observes (the `xfail` reporting tests). A spec that admits
such an implementation does not enforce `verify ⇒ correct`.

The correction is therefore not the only observable. Everything this hook writes
is an observable, and the hook writes exactly three attributes: `rep.outcome`,
`rep.wasxfail` and `rep.longrepr`. All three are pinned per classification case
(post-conditions group B), each at the granularity mapping.md §2 fixes:

* **outcome** — the three-valued code, per case.
* **annotation** — its presence, *which reason it carries*, and *the style that
  reason is rendered in*: `raised_reason` behind the lead-in for the imperative
  arm (:277), `declared_reason` verbatim for the two mark arms (:286, :293).
  Presence alone would admit an implementation that annotates a test with another
  test's reason, or with an invented one; presence-plus-reason still admits one
  that renders every annotation the same way, which the imperative-xfail P2P
  tests detect (see "Rendering is also behaviour" below).
* **stated verdict** — the `rep.longrepr` write, as *which* of the two standard
  verdicts is stated and *which* reason it interpolates:
  `EXPLANATION_UNEXPECTED_SUCCESS` with `success_reason` for branch 1
  (:267-271), `EXPLANATION_STRICT_UNEXPECTED_PASS` with `declared_reason` for
  the strict xpass arm (:290), and `EXPLANATION_NONE` — *no verdict stated and
  the run's own account left standing* — everywhere else.

The stated verdict is the leg it is most tempting to drop, and dropping it is a
real hole rather than a stylistic one. The strict xpass arm writes BOTH
`rep.outcome = "failed"` (:289) and `rep.longrepr = "[XPASS(strict)] " +
xfailed.reason` (:290). A model that pinned only the outcome code admits an
implementation that omits :290 — which still resolves F2P, and breaks
`testing/test_skipping.py::TestXFail::test_xfail_xpassed_strict` (it asserts
`str(callreport.longrepr) == "[XPASS(strict)] nope"`) and
`test_strict_xfail[True]` (it matches `"*XPASS(strict)*unsupported feature*"`),
both of which are **PASS_TO_PASS**. That is precisely a `verify ∧ ¬correct`
witness, so the verdict slot has to be observable in the carrier and pinned in
every case. The same argument applies in the other direction to
`EXPLANATION_NONE`: a case that stated *something* where the repo states nothing
would overwrite the account the run itself produced in `rep.longrepr` — for a
genuinely failing test, its traceback — so "states no verdict" is pinned as
`explanation == Old(explanation) and explanation_reason == Old(explanation_reason)`
rather than left free.

**Rendering is also behaviour, and is pinned too.** It is tempting to treat the
`"reason: "` prefix at :277 and the two `"Unexpected success…"` spellings at
:269/:271 as presentation, but the strings these writes produce are shown to the
user unaltered — `terminal.py:1102-1106` reads `reason = rep.wasxfail` and
appends `"  " + str(reason)` — and the hidden suite reads them directly. So the
carrier records, per case, not only WHICH reason reaches WHICH slot but the STYLE
that slot renders it in (`note_style`), because the three annotating writes are
**not the same function of their reason**: :277 writes `"reason: " + msg`, while
:286 and :293 write the reason alone.

Both directions are pinned by PASS_TO_PASS assertions, so neither style is free
and the claim does not over-reach:

* `testing/test_skipping.py:172` asserts `callreport.wasxfail == ""` and `:187`
  asserts `callreport.wasxfail == "this is an xfail"` — exact equality on a mark
  arm, so **any** lead-in there fails.
* `:333` and `:351` match `"*reason:*hello*"` against the reported line for an
  imperatively raised expected failure, so **dropping** the lead-in there fails.
  (`fnmatch("  reason: hello", "*reason:*hello*")` is true;
  `fnmatch("  hello", …)` is false.)

Without this observable the two renderings are the SAME point of the
abstraction, and an implementation that hoists the three annotating writes to
one shared site carrying each arm's reason token is *abstractly identical to
gold* — it satisfies every clause over `(xfail_note_present, note_reason)`. Its
faithful refinement has one write, hence one rendering, and it resolves F2P while
breaking `TestXFail::test_xfail_imperative` and
`::test_xfail_imperative_in_setup_function`. That is a `verify ∧ ¬correct`
witness, which is why the style is carried per case rather than left to the
implementation. It is deliberately **not** modelled as a function of the reason
token: two cases may be given equal tokens (nothing separates `raised_reason`
from `declared_reason` in the precondition) and must still render differently, so
dispatching on the token would be ambiguous exactly where it matters.

The verdict slot's text is pinned the same way but needs no extra observable,
because there the rendering **is** determined by which verdict is stated:
`EXPLANATION_STRICT_UNEXPECTED_PASS` reads `"[XPASS(strict)] " + reason` (:290)
and `EXPLANATION_UNEXPECTED_SUCCESS` reads `"Unexpected success: " + reason`, or
bare `"Unexpected success"` on an empty reason (:269/:271). A shared
verdict-stating site that dispatches on the token therefore reproduces both texts
and is admitted; one that renders both verdicts through a single template does
not, and `test_xfail_xpassed_strict` (which asserts
`str(callreport.longrepr) == "[XPASS(strict)] nope"`) detects it.

What remains deliberately **not** pinned: the concrete text of any reason, and
any iteration or evaluation order beyond the priority of the cases themselves —
neither is a guarantee of the function, and pinning them would reject correct
alternative implementations. Reasons are therefore still carried as opaque `int`
tokens; what the repair adds is the *style* each slot reads its token in, not the
token's text.

### The two steps meet in one place

`rep.longrepr` is a SINGLE attribute playing two roles, and the two steps of this
hook both write it. Step (1) writes a rendered verdict string into it (`"Unexpected
success…"` at `skipping.py:269,271`; `"[XPASS(strict)] …"` at `:290`); step (2)
unpacks a positional `(filename, line, reason)` triple out of it and re-emits a
corrected one (`:302`, `:305`). The report therefore keeps ONE account of itself,
which is *either* a location *or* a verdict — never both — and the two writes
cannot coexist.

That makes the two steps couple in exactly one direction, and only there:

* **A case that states a verdict annihilates a location that stood there.** The
  string assignment replaces the tuple, so after case (a) or the strict sub-case
  of case (d) there is no file, no line and no reason left to correct. The model
  pins this as `states_own_verdict(...) ⇒ not loc_is_triple ∧ loc_file ==
  loc_line == loc_reason == LOC_ABSENT`, with `LOC_ABSENT` the designated
  "no positional location" token, so the emptiness is *observable* rather than
  merely unconstrained. `states_own_verdict` is a `@Pure` function over the same
  classification predicates, i.e. it names the two cases that write the slot; it
  is *not* a new input and adds no freedom.
* **A case that states no verdict leaves the shape alone** —
  `¬states_own_verdict(...) ⇒ loc_is_triple == Old(loc_is_triple)`. Step (1) can
  only destroy triple-ness, never create it.
* **Condition (C) of step (2) is read on the account AS IT STANDS**, not as the
  run left it: the repo's guard is `type(rep.longrepr) is tuple` at `:297`, which
  executes *after* the classification. So the correction clause's antecedent is
  `skipped_by_mark ∧ rep_skipped ∧ Old(loc_is_triple) ∧ ¬states_own_verdict(...)`.

An earlier revision of this spec instead asserted `loc_is_triple ==
Old(loc_is_triple)` unconditionally, and pinned the location as untouched whenever
the correction did not fire. Both clauses are FALSE on a reachable state: a report
can arrive carrying a skip triple *and* a recorded unexpected success (the skip is
raised outside `TestCase.run`, from a call-phase hookwrapper, so it lands on the
same `CallInfo` — see mapping.md's refuted (I2)), and the hook then replaces the
triple with `'Unexpected success'`. G-AX leg (2b) exhibits that transition against
the real hook; G-CONF now compares those 15,382 points instead of excluding them.

**What this coupling deliberately does NOT constrain: the order of the two
writes.** An implementation that applies the correction *before* the
classification, so it writes into a slot a verdict is about to overwrite, verifies
— and should. It is a dead store: the two orders agree on every one of the 16,384
abstract inputs (all 11 branch booleans × the shape flag × two `definition_file`
tokens, including `LOC_ABSENT` itself, × two `definition_line` values). Since the
postconditions speak about post-states, and the post-states are identical, no
clause can separate them without rejecting a correct implementation. What *is*
rejected is any version of that reordering whose write SURVIVES: snapshotting the
pre-classification shape and correcting afterwards, or restoring `loc_is_triple`
after a verdict, both fail on the annihilation clause.

The load-bearing independence claim is untouched by all of this. `states_own_verdict`
does not mention `suppress_xfail_reporting` except inside the strict sub-case,
exactly as the repo has it (branch 1 precedes the `--runxfail` branch at `:273`,
the strict arm follows it), so the correction is still specified to fire under
`--runxfail`, and that is still the single clause the pre-patch twin violates.

## verify(model) ⇒ resolved

`finalize_skip_location` verifies only if **both** of the following hold.

*The correction (group A, the F2P direction).* It fires on exactly its own three
conditions, **independently** of the classification: the postcondition
`Implies(skipped_by_mark and rep_skipped and Old(loc_is_triple) and not
states_own_verdict(…), loc_is_triple and loc_line == definition_line + 1 and
loc_file == definition_file and loc_reason == Old(loc_reason))` cannot hold if the
correction is gated behind
`not (unexpected_success or suppress_xfail_reporting or xfail_exception or …)`.
The `¬states_own_verdict(…)` conjunct is not such a gate: it excludes only the two
cases that leave *no location to correct* (previous section), and in particular
says nothing about `suppress_xfail_reporting` on its own. The pre-patch `elif`
chain violates exactly this clause (G-DIFF: `model_prepatch` fails on it, at
`p.py:296:9:307:10`) because the `suppress_xfail_reporting` (`--runxfail`) branch,
when taken, suppresses the correction.

*The classification (group B, the P2P direction).* Every case's outcome, its
annotation (presence **and** the reason that annotation carries) and its stated
verdict (**which** verdict, **which** reason, or none-and-untouched) are pinned as
the first-applicable case of the priority order, so the classification cannot be
dropped, reordered, merged, or thinned out one slot at a time. This is what
forbids an implementation that satisfies group A while destroying the
expected-failure reporting the P2P suite depends on — including the narrow
version of that destruction that keeps every outcome code correct and merely
stops telling the user why a strict xfail failed, which
`TestXFail::test_xfail_xpassed_strict` and `test_strict_xfail[True]` detect.

Group A also pins the correction in all three elements of the location, so an
implementation that redirects the report to the right line of the wrong file, or
that silently discards the skip reason it re-emits, is rejected as well.

### The definition line is partial, and WHERE it is read is behaviour

The test's own definition location is not an input the hook is handed; it is an
answer it obtains, and the question has no answer for a run item the reporting
machinery cannot locate in source (`Item.reportinfo` returns
`(self.fspath, None, "")`, `src/_pytest/nodes.py:654-655` @ base). `Item` is a
public base class, and pytest's own suite subclasses it: `class MyItem(pytest.Item)`
at `testing/test_skipping.py:1064` (`test_xfail_item`) and `:1139`
(`test_mark_xfail_item`). Those two reports reach this hook with no definition
line at all.

The repo is only safe because of WHERE it asks: `filename, line = item.reportinfo()[:2]`
and `assert line is not None` sit *inside* the `type(rep.longrepr) is tuple` guard
(`skipping.py:297-304`), which those reports never enter. The model therefore
carries the definition line as `Optional[int]` and supplies it under exactly that
guard — `Requires(Implies(skipped_by_mark and rep_skipped and rep.loc_is_triple,
definition_line is not None and definition_line >= 0))` — rather than as an
unconditional `definition_line >= 0` precondition over the whole domain. Two
consequences, both intended:

* Every report is admissible with **no** definition line, and must still be
  finalised: the completion budget `definition_line_budget(definition_line)` is
  total and is owed on those inputs too (battery: `admiss-absent`,
  `rej-abandon-absent`). This is the PRESERVATION half of the behaviour — the
  correction must not make the finalisation of the reports it does not touch
  conditional on a location those reports do not have.
* An implementation may read the definition line only where one is supplied, i.e.
  under the correction's own guard (`pos-preguard-hoist` is the admitted early
  read; `rej-hoist-unconditional`, `rej-hoist-assert` and
  `rej-hoist-partial-guard` are the rejected ones), or after handling absence
  itself (`pos-absent-branch`, `pos-budget-echo`). The distinction is exactly the
  one the repo draws with the placement of its assert, and it is the difference
  between a patch that resolves and a patch whose `FAIL_TO_PASS` passes while
  `test_xfail_item` and `test_mark_xfail_item` fail.

By R (each predicate ↔ its boolean; the location triple ↔
`loc_is_triple`/`loc_file`/`loc_line`/`loc_reason`, element for element;
`definition_line` ↔ `item.reportinfo()` line and `definition_file` ↔ its
filename; `"failed"`/`"skipped"`/`"passed"` ↔ the outcome codes; the annotation's
presence ↔ `xfail_note_present` and its reason's origin ↔ `note_reason`; the two
standard verdict templates ↔ `explanation` with the reason they interpolate ↔
`explanation_reason`) the verified skeleton is the gold-patched
`pytest_runtest_makereport` on the F2P scenario
(`@pytest.mark.skip` + `--runxfail`) — both report the item-definition location —
*and* on the xfail scenarios the P2P suite exercises. The gold patch resolves
(G-RESOLVE). The only trust point is
refinement fidelity (this document, G-EQ); there is no axiom-soundness trust
point because no axiom is consumed. G-AX (`axiom_check.py`) independently
confirms the deep correspondence by running the real patched hook end-to-end
(mapping.md §3.1).
