# mapping.md — pytest-dev__pytest-7432

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e6e300e729dd33956e5448d8be9a0b1540b4e53a`, states the type
abstraction, and records callee provenance.

Repo file under change: `src/_pytest/skipping.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `finalize_skip_location(rep, definition_file, definition_line, …)` | `pytest_runtest_makereport(item, call)` — `src/_pytest/skipping.py:260` (body lines 261–305) | the modeled changed function (the runtest-makereport hook) |
| `RunReport` (`loc_is_triple`, `loc_file`, `loc_line`, `loc_reason`, `outcome`, `xfail_note_present`, `note_reason`, `explanation`, `explanation_reason`) | the `rep` report object (`_pytest.reports.TestReport`) — its `rep.longrepr` field in **both** of the roles that field plays (a positional source-location triple, and the rendered standard verdict shown to the user), its `rep.outcome`, and its `rep.wasxfail` annotation with the reason that annotation carries | minimal twin carrying every observable field the hook writes; the hook writes `rep.longrepr`, `rep.outcome` and `rep.wasxfail` and nothing else, and each of those writes lands in one of these nine fields |
| `rep.loc_is_triple` | `type(rep.longrepr) is tuple` — `skipping.py:297` | whether the recorded location is the positional `(filename, line, reason)` triple that carries a correctable source line |
| `rep.loc_line` | the line element of `rep.longrepr` (`_, line, _ = rep.longrepr`) and its rewrite `rep.longrepr = str(filename), line + 1, reason` — `skipping.py:302,305` | the recorded source line of the report |
| `rep.loc_file` | the filename element of `rep.longrepr`, written as `str(filename)` by the correction — `skipping.py:305` | the file the recorded location names |
| `rep.loc_reason` | the reason element of `rep.longrepr`, unpacked at `skipping.py:302` (`_, _, reason = rep.longrepr`) and re-emitted unchanged at `:305` | the skip reason the recorded location already carried |
| `rep.note_reason` | the value assigned to `rep.wasxfail` — `"reason: " + call.excinfo.value.msg` at `skipping.py:277`, `xfailed.reason` at `:286` and `:293` | which reason the expected-failure annotation carries |
| `rep.explanation` | which of the two standard verdict templates `rep.longrepr` was assigned, if either: `"Unexpected success"` / `"Unexpected success: …"` at `skipping.py:269,271` (→ `EXPLANATION_UNEXPECTED_SUCCESS`), `"[XPASS(strict)] …"` at `:290` (→ `EXPLANATION_STRICT_UNEXPECTED_PASS`), neither (→ `EXPLANATION_NONE`: no verdict was stated and whatever account the run itself produced in that slot stands) | which standard verdict the report states to the user |
| `rep.explanation_reason` | the reason interpolated into that template — `item._store[unexpectedsuccess_key]` at `skipping.py:267` (rendered by `:269`/`:271`), `xfailed.reason` at `:290`; when no verdict is stated, the identity of the account the run produced | which reason the stated verdict carries |
| `definition_line` | `item.reportinfo()[:2]` → `line` — `skipping.py:303` (the zero-based test-definition line; the correction stores `line + 1`). `Optional[int]`: `None` is the reporting machinery answering that the run item has no definition line at all (`Item.reportinfo`, `nodes.py:654-655`), which is why the repo asks only inside the correction's guard and asserts the answer at `:304` | the test's own definition line, where the reporting machinery can name one |
| `definition_file` | `item.reportinfo()[:2]` → `filename` — `skipping.py:303`, stored as `str(filename)` at `:305` | the file the test is defined in |
| `declared_reason` | `xfailed.reason` — `skipping.py:286`, `:290`, `:293` | the reason the expected-failure mark declared |
| `raised_reason` | `call.excinfo.value.msg` — `skipping.py:277` | the reason an imperative `pytest.xfail(...)` raised |
| `success_reason` | `item._store[unexpectedsuccess_key]` — `skipping.py:267` | the reason recorded alongside a unittest unexpected success |
| `skipped_by_mark` | `item._store.get(skipped_by_mark_key, True)` — `skipping.py:295` | the run was skipped by a `skip`/`skipif` mark |
| `rep.outcome` | `rep.outcome` (`_pytest.reports`: `passed`/`failed`/`skipped` are properties over it, `reports.py:139-141`) — written at `skipping.py:272,278,283,285,289,292` | the report's classified outcome, as one of three codes |
| `rep.xfail_note_present` | whether `rep.wasxfail` has been set — `skipping.py:277,286,293` | whether the report carries an expected-failure annotation (presence only; the reason text is not modelled) |
| `rep_already_skipped` | `rep.skipped` read BEFORE the classification — `skipping.py:279` (`not rep.skipped`) | the report was already in the skipped state on entry |
| `rep_skipped` | `rep.skipped` read AT the correction — `skipping.py:296`, i.e. *after* the classification may have reassigned `rep.outcome` | the report is in the skipped state at the point the correction is decided |
| `exception_raised` | `call.excinfo` truthy — `skipping.py:280` | the run raised something |
| `xfail_raises_mismatch` | `raises is not None and not isinstance(call.excinfo.value, raises)` — `skipping.py:281-282` | the raised exception does not match the mark's `raises` filter |
| `phase_is_call` | `call.when == "call"` — `skipping.py:287` | the run phase is the test call itself |
| `xfail_strict` | `xfailed.strict` — `skipping.py:288` | the evaluated xfail mark is strict |
| `unexpected_success` | `unexpectedsuccess_key in item._store and rep.when == "call"` — `skipping.py:266` (branch 1) | unittest unexpected-success classification |
| `suppress_xfail_reporting` | `item.config.option.runxfail` — `skipping.py:273` (branch 2, `pass`) | the `--runxfail` toggle: report expected-failure outcomes as if unmarked |
| `xfail_exception` | `call.excinfo and isinstance(call.excinfo.value, xfail.Exception)` — `skipping.py:275` (branch 3) | an imperative `pytest.xfail(...)` was raised |
| `xfailed_present` | `xfailed` truthy (`item._store.get(xfailed_key, None)`) — `skipping.py:279` (branch 4 guard, with `not rep.skipped`) | an xfail mark was evaluated for the item |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `rep.longrepr` positional triple `(str filename, int line, str reason)` | `RunReport.loc_is_triple: bool` + `loc_file` + `loc_line: int` + `loc_reason` | `loc_is_triple` ↔ `type(rep.longrepr) is tuple`; the other three ↔ the triple's three elements, element for element. All three are carried, not just the line: the correction re-emits `str(filename)` and the same `reason`, and "re-emits them unchanged" is a claim about this function that has to be *pinned* rather than assumed, since an implementation free to rewrite the file or drop the reason would be admitted otherwise. |
| `item.reportinfo()[:2]` line (zero-based), which is `Optional[int]` in the repo's own signature | `definition_line: Optional[int]` (`>= 0` where present) | identity on the `int` case, and `None` ↔ `None`; the correction stores `definition_line + 1` exactly as the repo stores `line + 1`. The carrier is PARTIAL because the repo's is: `Item.reportinfo` (`src/_pytest/nodes.py:654-655` @ base) answers `(self.fspath, None, "")` for a run item it cannot locate in source, and `Item` is a public base class the suite itself subclasses (`class MyItem(pytest.Item)` at `testing/test_skipping.py:1064` and `:1139`). The repo asks the question at `skipping.py:303` — *inside* the `type(rep.longrepr) is tuple` guard at `:297` — and asserts the answer is present at `:304`; that assert is not a claim about every report, it is a claim about the reports that reach it. The model mirrors the assert's PLACEMENT, not just its content: `Requires(Implies(skipped_by_mark and rep_skipped and rep.loc_is_triple, definition_line is not None and definition_line >= 0))`, i.e. a definition line is supplied under exactly the correction's own three conditions and nowhere else, and the impl region asserts it there (`assert definition_line is not None`) exactly as `:304` does. An unconditional `definition_line >= 0` precondition would be UNFAITHFUL here — it would assert of every report what the repo asserts only of the ones the correction applies to — and would admit an implementation that consumes the definition line before knowing the correction applies, whose faithful patch must hoist the `reportinfo()`/`assert` pair and then dies on those two `MyItem` reports. |
| each branch predicate (membership/attribute/isinstance test) | a `bool` parameter | identity on the predicate's truth value. The model abstracts *what* each predicate tests to its boolean result; the spec/skeleton only depend on the truth values, not the underlying objects, so this is a sound R-refinement (the F2P scenario fixes these booleans to concrete values — see §3). |
| `rep.outcome` (the strings `"passed"`, `"failed"`, `"skipped"`) | `RunReport.outcome: int` (`OUTCOME_PASSED`/`OUTCOME_FAILED`/`OUTCOME_SKIPPED`) | a three-valued bijection on the outcome strings the hook writes. Nagini bans string comparison in specifications, so the three values are carried as distinct `int` codes; nothing else about the report's outcome is modelled. |
| `rep.wasxfail` (an annotation whose value is a reason string) | `RunReport.xfail_note_present: bool` + `note_reason: int` + `note_style: int` | presence ↔ `hasattr(rep, "wasxfail")`; `note_reason` ↔ WHICH of the reasons in scope was assigned there, as an opaque token: `note_reason == raised_reason` for `skipping.py:277`, `== declared_reason` for `:286` and `:293`. An implementation that annotated with some other case's reason, or with an invented one, is rejected. The *rendering* is carried too, by `note_style`, because it is not presentation: the string assigned to `rep.wasxfail` is printed VERBATIM to the user (`terminal.py:1102-1106` does `reason = rep.wasxfail; if reason: lines.append("  " + str(reason))`), and the three assignments are not the same function of their reason — `:277` writes `"reason: " + msg` while `:286` and `:293` write the reason alone. `NOTE_STYLE_LEAD_IN` ↔ the `:277` form, `NOTE_STYLE_VERBATIM` ↔ the `:286`/`:293` form, `NOTE_STYLE_ABSENT` ↔ no annotation. Both directions are pinned by the hidden suite and neither is free: `testing/test_skipping.py:172` asserts `callreport.wasxfail == ""` and `:187` asserts `== "this is an xfail"` (a lead-in on a mark arm breaks both), while `:333`/`:351` match `"*reason:*hello*"` on the imperative arm (dropping the lead-in there breaks both). A carrier holding only `(presence, reason token)` would make the two renderings the SAME point, admitting an implementation that hoists the three writes to one shared site — which resolves F2P and breaks `TestXFail::test_xfail_imperative` and `::test_xfail_imperative_in_setup_function`. The style is deliberately NOT derived from the reason token: two cases may be given equal tokens and still render them differently, so it is an observable of its own. |
| the strings written to `rep.longrepr` by the classification (`"Unexpected success…"` at `skipping.py:269,271`; `"[XPASS(strict)] …"` at `:290`) | `RunReport.explanation: int` (`EXPLANATION_NONE` / `EXPLANATION_UNEXPECTED_SUCCESS` / `EXPLANATION_STRICT_UNEXPECTED_PASS`) + `explanation_reason: int` | WHICH of the two verdicts a case states, and WHICH reason it interpolates, are behaviour and are pinned. So is the text each verdict is rendered as, and that text is a function of the VERDICT, not a free choice: `EXPLANATION_STRICT_UNEXPECTED_PASS` ↔ `"[XPASS(strict)] " + reason` (`:290`) and `EXPLANATION_UNEXPECTED_SUCCESS` ↔ `"Unexpected success: " + reason`, or bare `"Unexpected success"` on an empty reason (`:269`/`:271`). Because the rendering is determined by the token, a shared verdict-stating site that dispatches on `explanation` reproduces it exactly, so nothing further need be carried — but a site that renders both verdicts through ONE template does not, and is what the model's per-verdict text claim excludes. This is not an optional refinement: the hidden suite asserts these strings directly — `testing/test_skipping.py::TestXFail::test_xfail_xpassed_strict` asserts `str(callreport.longrepr) == "[XPASS(strict)] nope"` and `test_strict_xfail[True]` matches `"*XPASS(strict)*unsupported feature*"` — so a model that carried only the *outcome* code of those branches would admit an implementation that sets `rep.outcome = "failed"` and writes no message, which resolves F2P and breaks both of those PASS_TO_PASS tests. `EXPLANATION_NONE` additionally means "no verdict stated, and the account the run itself produced in that slot still stands", so a case that overwrote a genuine failure's own repr with something else is rejected too. Note the classification branches are therefore **not** modelled as `pass`: each one's outcome, annotation *and* stated-verdict effect is reproduced (see refinement.md, "Why the earlier branches are modelled with their effects"). |

| the fact that `rep.longrepr` is ONE attribute holding *either* shape — a positional triple (`reports.py:311`, via `ExceptionInfo`/`Skipped`) *or* a rendered verdict string (`skipping.py:269,271,290`) — so the two writes cannot coexist | `loc_is_triple` + the three positional fields *versus* `explanation` + `explanation_reason`, coupled by `LOC_ABSENT` | The nine fields are two VIEWS OF ONE SLOT, not two slots. Stating a verdict therefore ANNIHILATES a positional location that stood there: `states_own_verdict(...) ⇒ not loc_is_triple ∧ loc_file == loc_line == loc_reason == LOC_ABSENT`. `LOC_ABSENT` is the designated "there is no positional location" token — carried as `-1`, a value no real line, file token or reason token takes, so "the slot holds no location" is *observable* rather than merely unconstrained. This is behaviour, not bookkeeping: the two cases that state a verdict (case (a) at `:266-272` and the strict sub-case at `:288-290`) assign a `str` to the same attribute the correction later unpacks at `:302`, which is precisely why the correction's `type(rep.longrepr) is tuple` guard at `:297` reads the shape AS IT STANDS AFTER the classification and not as the run left it. Witnessed against the real hook (G-AX leg (2b)) and compared on 4496 points per G-CONF run. Without this coupling the model claimed the location survived a stated verdict, which is false on a reachable state — see refinement.md, "The two steps meet in one place". |

`str` indexing/iteration is banned in Nagini; no string is indexed here — the
location is carried as an `int` line number and a triple-shape flag, which is
exactly the granularity the F2P test observes.

## 3. Callee provenance

**No `@ContractOnly` axiom is consumed and no deep model stands in for an
unchanged callee.** The fix is a pure control-flow restructuring of one hook
(`pytest_runtest_makereport`): the final `elif` that performs the skip-location
correction is split off into an independent `if` so the unrelated `--runxfail`
toggle (branch 2, `pass`) can no longer suppress it. There is therefore nothing
to axiomatize — the changed operation IS the branch structure, which is modelled
directly (`model.py` impl region). `# axioms-start/end` is intentionally empty.

### 3.1 Behavioural soundness check (G-AX) — the real hook end-to-end
Because the correspondence is "the modeled boolean control-flow == the real
hook's control-flow," `axiom_check.py` validates it by driving the REAL,
patched `pytest_runtest_makereport` in-container, as a real pytest run over
generated test files. Two families, one per modelled step.

*Step 2, the correction.* A `@pytest.mark.skip` test is run with and without
`--runxfail`, and the reported skip location is asserted to point at the
test-definition line (`test_sample.py:3` for the shipped sample — the item's
first decorator line, which is `reportinfo()`'s zero-based 2 plus one) in BOTH
configurations — i.e. the correction fires independently of `--runxfail`, exactly
the `Implies(skipped_by_mark and rep_skipped and loc_is_triple, loc_line ==
definition_line + 1)` postcondition. Both the file and the exact line are
asserted, so a correction that pointed into pytest internals *or* at the wrong
line of the right file is caught.

*Step 1, the classification.* The model does not model the classification
branches as `pass`, so those pins are claims about the real system and are
checked against it. Five scenarios, each read back out of pytest's own report
rendering with `-rxX` / `-rf`:

| scenario | asserted | model clause witnessed |
|---|---|---|
| strict xfail that passes | `1 failed`, the verdict `[XPASS(strict)] <mark reason>` is stated, and the run is NOT summarised as an `XPASS` | strict sub-case of (d): `outcome == OUTCOME_FAILED`, `explanation == EXPLANATION_STRICT_UNEXPECTED_PASS`, `explanation_reason == declared_reason`, annotation untouched |
| the same test under `--runxfail` | `1 passed` and NO verdict stated | case (b): the toggle decides nothing and shields (d) — while step 2 above shows it does NOT shield the correction |
| non-strict xfail that passes | `XPASS …` summary line whose trailing reason is the mark's, and no `[XPASS(strict)]` anywhere | non-strict sub-case of (d): `outcome == OUTCOME_PASSED`, `xfail_note_present`, `note_reason == declared_reason`, `explanation == Old(explanation)` |
| imperative `pytest.xfail(raised)` on an item that ALSO carries a mark with a DIFFERENT reason | `1 xfailed`, the raised reason appears, the mark's reason appears nowhere | case (c): `outcome == OUTCOME_SKIPPED`, `note_reason == raised_reason` — and its precedence over (d) |
| unittest unexpected success | `1 failed` and the `Unexpected success` verdict stated | case (a) |

It also confirms the pre-patch chain (reconstructed inline) reports the wrong,
internal location when `--runxfail` is set, witnessing the discriminating clause.
stdlib + pytest only; exit 0 iff the real behaviour matches the model. Only an
`ImportError` (pytest not installed at all) downgrades to SKIP — a *disagreement*
always fails, so the check cannot pass by not running. Mutation-checked both
ways: against the REAL **unpatched** container it exits 1 (`SKIPPED [1]
../../testbed/src/_pytest/skipping.py:239` under `--runxfail`), and with the
strict arm's `rep.longrepr` write deleted from the installed repo it exits 1 on
the strict-verdict assertion.

The F2P scenario (`test_xfail_run_with_skip_mark[test_input1-expected1]`,
`["-rs", "--runxfail"]`) fixes the booleans to: `skipped_by_mark = True`,
`rep_skipped = True`, `loc_is_triple = True`, `unexpected_success = False`,
`suppress_xfail_reporting = True` (because `--runxfail`), `xfail_exception =
False`, `xfailed_present = False`. The model's postcondition then forces
`loc_line == definition_line + 1` (the correct, item-definition location),
while the pre-patch `elif` chain leaves it at the internal line.

The PASS_TO_PASS xfail-reporting scenarios pin the other direction. E.g. a
non-strict xfail mark on a test that unexpectedly passes fixes
`xfailed_present = True`, `rep_already_skipped = False`, `exception_raised =
False`, `phase_is_call = True`, `xfail_strict = False`, and the classification
postcondition then forces `outcome == OUTCOME_PASSED` with the annotation set —
which an implementation that drops or reorders that case cannot satisfy.

## G-CONF (differential conformance)

`conformance_check.py` diffs the SHADOW — the `# impl-start`/`# impl-end` region
of `model.py` (`finalize_skip_location`) copied verbatim with only the contract
calls removed — against the ORACLE, which is the REAL patched repo function
**called, not transliterated**:
`_pytest.skipping.pytest_runtest_makereport` (`src/_pytest/skipping.py:260`,
body 261–305). `@hookimpl` merely tags the function, so the module-level object
is an ordinary generator: the check drives it with `next(gen)` /
`gen.send(outcome)` and reads the in-place mutation of `rep.longrepr`. No line
of the hook's control flow — in particular the `elif` → `if` split that *is* the
gold patch — is retyped by this script. (The `lean/` sibling instead uses a
hand-written replica of the post-patch control flow; calling the real function
is strictly stronger, since a mis-transcribed replica would agree with a
mis-transcribed shadow.)

**Pinned seed: `SEED = 7432`.** Inputs checked: **100000** — the finite
structural space (1890 points: 5 exception kinds × 3 phases × 2 `--runxfail` ×
3 `skipped_by_mark` store states × 7 `Xfail` shapes — including two with an
EMPTY declared reason, the boundary at which the repo's rendering of a stated
verdict degenerates — × 3 unexpected-success states, which likewise separate "no
recorded reason" from "an empty one") is enumerated EXHAUSTIVELY against 5
boundary definition-lines, after an explicit boundary list containing the exact
F2P shape; seeded fuzz over the same space then fills the count to 1e5.

**Type bridge (§2 inverted).** Generation runs in the CONCRETE direction and
the abstract carrier is *derived*, never chosen: the report is built by the real
factory `TestReport.from_item_and_call` (`src/_pytest/reports.py:292`) from a
really-raised `ExceptionInfo`, so `rep.outcome` and the shape of `rep.longrepr`
are decided by repo code; all nine `RunReport` fields and the boolean predicates
are then read off that realized state exactly as §1 specifies. Nothing modelled
is assumed: the three location elements, the annotation's reason token and the
stated verdict with its reason are each *derived* from the realized report by an
inverse of the §2 abstraction (`_project`) and then compared.

The compared observable is the 7-component tuple `(loc_is_triple, loc_triple,
outcome, xfail_note_present, note_reason, explanation, explanation_reason)`, so
the classification cases are diffed against the real hook in every dimension the
spec pins — including the two standard verdict strings, which the earlier 4-tuple
observable did not read at all and which is exactly the freedom a passing shadow
could have used to drop `"[XPASS(strict)] …"` unnoticed. Because the abstraction
is many-to-one on the reason strings, the inverse maps each realized string back
to WHICH reason in scope produced it (`("declared", …)` / `("raised", …)` /
`("success", …)`), and any string the model does not account for projects to an
opaque `("own", repr(...))` token that only compares equal to itself; a shadow
that invents a message therefore disagrees rather than being abstracted away.
Sentinel values stand in for "there is no such reason in scope" and a write of a
sentinel is reported as a disagreement in its own right, so the projection cannot
be satisfied by writing a field the real hook leaves alone.

One subtlety the bridge handles explicitly:
the report's skipped state is read at two points by the modeled behaviour
(`skipping.py:279` before classification, `:296` at the correction) and the repo
re-reads a *mutable* attribute, so the two reads can disagree. The second read is
therefore DERIVED — the shadow is run once with the correction's guard made
unsatisfiable and the classified outcome is read off the result — rather than
sampled freely, which is what previously manufactured the phantom (I1)
disagreements. This cannot mask a wrong classification, since the classified
outcome is itself part of the compared tuple.

**Domain realizability (why the abstract booleans are not sampled freely).**
Sampling the branch booleans freely yielded, for an earlier revision, 34 apparent
disagreements, excluded on two claimed repo invariants. Only ONE of the two
survived; the other was false, and excluding on it hid a real omission in the
model. Both are still re-asserted mechanically at startup by
`_assert_domain_invariants()` — the surviving one as a filter, the refuted one as
a positive witness of the behaviour it used to deny:

* **(I1)** `xfail_exception ∧ loc_is_triple` is unsatisfiable — a triple
  `longrepr` requires a `Skipped` excinfo (`reports.py:311`), while
  `xfail.Exception` (`XFailed`) subclasses `Failed`, not `Skipped`. (2 of the 34;
  still excluded.)
* **(I2)** **REFUTED.** `unexpected_success ∧ loc_is_triple` *is* satisfiable, and
  nothing is excluded on it any more (it was 32 of the 34). The old argument was
  that `unexpectedsuccess_key` is written only by
  `TestCaseFunction.addUnexpectedSuccess` (`src/_pytest/unittest.py:232`), which
  CPython's `TestCase.run` calls only when `outcome.success` holds, and
  `unittest.case._Outcome.testPartExecutor` clears `success` on any `SkipTest`.
  But `TestCase.run` only sees the skips raised *inside* it:
  `CallInfo.from_call(lambda: item.runtest(), "call")` (`runner.py:255`) is one
  level out, so a `pytest.skip` raised from a call-phase hookwrapper lands its
  `Skipped` excinfo on the same `CallInfo` whose `addUnexpectedSuccess` already
  wrote the store key. Probed in-container (see G-AX leg (2b)): the call report
  arrives `skipped` with a tuple `longrepr`, and the hook leaves it `failed` with
  `'Unexpected success'`. Those 15,382 points are now generated and compared, and
  `branch_hits.verdict_annihilated_a_location` (4496 at seed 7432) requires the
  domain to keep reaching them.

Only the INPUT is constrained; the oracle's answer is never filtered — and (I2)
is the cautionary case, since it was *phrased* as an input restriction but was
derived from the very output disagreement it went on to hide. Excluded points are
counted and reported (`unrealizable_excluded`, now 0), so a domain that collapsed
to nothing would be visible instead of green.

Two further invariants guard the *projection* (§2 read backwards) rather than the
domain, since the abstraction is many-to-one on strings and a sloppy inverse
could score a wrong reason as agreeing:

* **(I3)** no declared reason in the generated space renders into the imperative
  arm's `"reason: "` template, so recovering the annotation's ORIGIN from its
  text is unambiguous on this domain.
* **(I4)** no account the run itself produces in `rep.longrepr` (over every
  exception kind × phase) projects to either standard verdict, so "the run's own
  account still stands" (`EXPLANATION_NONE`) is distinguishable from "this
  verdict was stated".

Both are re-asserted at startup alongside (I1) and the (I2) witness, so the
reasoning cannot rot if the repo's wording changes.

**Non-vacuity.** The run asserts the modeled correction actually fired at the
F2P `--runxfail` shape (`branch_hits.f2p_runxfail_and_corrected > 0`) **and** that
every classification case the spec pins was reached (the four sub-cases of the
xfail-mark case among them), **and** that each newly-observed slot was actually
written by the oracle: both verdicts were stated (`verdict_unexpected_success_stated`,
`verdict_strict_xpass_stated`), a verdict carrying an empty reason was reached
(`verdict_reason_empty`, the boundary where the repo's two spellings diverge),
the annotation was seen carrying each of its two possible origins
(`annotation_carries_declared`, `annotation_carries_raised`), and a verdict was
stated over a report that arrived carrying a positional location
(`verdict_annihilated_a_location` — the coupling §2 pins, and the counter the
refuted (I2) exclusion used to make unreachable). The run exits 1 if
any of them was never exercised — a domain that skipped a case, or that never
made the repo state a verdict, would be comparing that case against nothing.
Mutation-tested three
ways: run against the REAL **unpatched** /testbed it exits 1, reporting the
disagreement at the F2P point (repo leaves the internal line 338; the model
requires `definition_line + 1 = 2`); `--selftest-prepatch` swaps in the pre-patch
chain and demands refutation; and deleting the strict arm's verdict write from
the shadow (keeping `rep.outcome = OUTCOME_FAILED`) is refuted too — shadow
`(False, None, 1, False, None, 0, ('own', 'None'))` against oracle
`(False, None, 1, False, None, 2, ('declared', 'r-strict'))` — which is the
demonstration that this check can no longer be blind to the P2P-breaking omission
described in §2. stdlib + the repo under test only.
