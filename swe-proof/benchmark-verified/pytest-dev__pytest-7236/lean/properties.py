"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7236 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for the case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end``), so
``markers.same_spec`` holds by construction and the single
``theorem correct_deferTeardown`` STATEMENT stays byte-identical.
``expect:"verify"`` passes iff the case is in scope AND the file elaborates with
the obligation closed (no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff the case is in
scope AND it does NOT verify AND its refutation ``witness`` holds of the rival
while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh design.
The nagini bundle models the decision as a PROCEDURE over a mutable record --
two read-only observation fields plus one mutated decision flag, pinned by a
biconditional postcondition and two read-only pins. This Lean bundle models the
SAME single purely-functional core as a total ``Bool``-valued function of the
case's observable conditions, and the same GROUNDED postcondition: the result is
equated to a fully-unfolded rule over the inputs, with no opaque answer key an
implementation could echo. Every nagini value-level case carries over as an
attack on that equation or as a faithful correct positive; the nagini
frame/permission-mutation class is VACUOUS here (see ``assessment``).

DEFENDED SURFACE (one modeled behavior, one obligation, one top-level clause).
``problem_spec_deferTeardown isAsync usePdb skipped result`` pins EXACTLY:

  * (C0) ``result = teardownDeferralRule isAsync usePdb skipped``, i.e.
    ``result = (!isAsync && usePdb && !skipped)``.

The clause is a complete three-way conjunction, so it is total over the input
space: ANY implementation whose decision differs from the rule at even one of
the eight points is refuted. There is no unconstrained output component and no
sub-domain the spec leaves open, which is what makes each rival below refutable
at a literal input rather than only by conditioning.

BINDER STRUCTURE (this is what the port had to get right, not the case count).
The spec predicate has THREE input binders and all three are load-bearing:

  * ``isAsync`` — the case is driven entirely by the asynchronous framework path;
  * ``usePdb``  — the interactive post-mortem debugger option is active;
  * ``skipped`` — the case has been marked to skip.

The nagini sibling's carrier has only TWO observation inputs: its record models
the debugger option and the skip marker, and the asynchronous-path condition is
not an input there at all. So this port carries a rival with NO nagini
counterpart (``weak-ignore-async``) purely to move the third binder -- otherwise
``isAsync`` would be held at ``false`` by every witness, and an implementation
that arranged postponement on the asynchronous path would satisfy every probed
point and the battery would never notice. Across the SIX reject witnesses each
binder takes both values and the probed points are six DISTINCT input triples:

    case                     isAsync  usePdb  skipped
    weak-prepatch             false    true    true
    weak-invert               false    true    false
    weak-ignore-option        false    false   false
    weak-ignore-async         true     true    false
    weak-always               true     false   false
    weak-async-skip-corner    true     true    true   <- added by audit

The last row is an AUDIT ADDITION, and the reason is a real gap rather than
tidiness: the original five all held ``skipped=false`` whenever ``isAsync=true``,
so a rival that arranged postponement on the asynchronous path for exactly a
SKIPPED case agreed with the rule at every point the battery probed. Three of
the eight points -- ``(true,true,true)``, ``(false,false,true)`` and
``(true,false,true)`` -- were unprobed. The new rival takes the first; the other
two were probed by audit-only rivals that each perturbed the rule at exactly one
of them, and each was refuted at its own point (rival witness exit 0, gold exit
1), so those points are measured but not carried as shipped cases.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION -- VACUOUS. Two of nagini's nine cases attack
    the write capability on its read-only observation fields: they satisfy the
    decision postcondition by overwriting an INPUT, and are rejected by the
    permission system rather than by the postcondition. That whole class is
    fractional-permission machinery. Lean is referentially transparent: the
    observations arrive as immutable ``Bool`` parameters, there is no mutable
    field, no aliasing, and no read-only cell to overwrite, so the two read-only
    pins the nagini spec needs do not exist here (nothing could have changed
    them). No substitute probe is fabricated. AUDIT REFINEMENT of the reason:
    the nearest expressible analogue -- an impl that SHADOWS its own input
    binders (``let isAsync := false`` before computing the rule) -- was built and
    does fail verification, but it fails as an ordinary VALUE error (`rfl`
    reports the shadowed body unequal to the rule at ``(false,true,true)``), not
    by any frame or permission mechanism. So the class does not vanish for want
    of syntax; it COLLAPSES into the partial-domain/value class already covered,
    which is why carrying it would add a duplicate rather than a new probe.

  * DIVERGENCE / NON-TERMINATION -- VACUOUS, and genuinely so. The nagini
    sibling carries no ``diverge-*``/``nonterm-*`` case, and none could be ported
    regardless: ``implementation_deferTeardown`` is a total Lean ``def``, so a
    non-terminating rival cannot be written at all. This is NOT the velvet
    ``partial``-semantics spec hole described in ``the corpus-wide termination-semantics finding``
    -- there is no ``set_option loom.semantics.termination`` here and no rival
    that the frozen spec admits.

  * UNGROUNDED-ORACLE ECHO -- VACUOUS. The rule is a fully unfolded Boolean
    expression over the three inputs, not an axiomatized oracle, so there is
    nothing to echo: producing the decision IS doing the work.

  * PARTIAL-DOMAIN / VALUE -- APPLIES, and is the whole battery. Each rival is
    correct on most of the eight-point domain and diverges on a named
    sub-domain: dropping the skip conjunct (the discriminating sub-domain the
    fix is about); inverting it; dropping the debugger-option conjunct; dropping
    the asynchronous-path conjunct; and arranging postponement unconditionally.

WITNESSES. On a tactic-proof backend "did not verify" is in general the DEFAULT
outcome of reshaping an implementation -- the frozen script closes by ``rfl``
under a three-way case split -- so a rejection alone attributes nothing to the
spec. Measured here with real builds: all five rivals below fail with
``Tactic `rfl` failed``. NOTE, corrected by audit: on THIS carrier the frozen
script is more robust than that argument assumes. Because the case split reduces
every input to literals, ``rfl`` closes any impl that is a correct decision
procedure regardless of its shape -- a guard with its conjuncts COMMUTED
(``!skipped && usePdb``), the same guard renested as two ifs, a De Morgan form,
a ``match`` on the triple, a ``cond`` chain, and a ``let mut`` accumulator were
each built and each VERIFIES (exit 0). So a rejection here is in fact evidence
of wrongness rather than of mere reshaping. The witnesses are retained anyway,
because that robustness is a measured property of this three-Bool carrier and
not something the gate can confirm, and because they upgrade each rejection from
"the tactic did not close" to a machine-checked counterexample at a named point.
Every ``expect="reject"`` case therefore carries a Lean snippet
that states ``¬ problem_spec_deferTeardown`` at one concrete literal triple and
closes by ``decide``. Each witness binds NOTHING in its head -- the carrier is
fully transparent, every input is a ``Bool`` literal, so conditioning on the
carrier is unnecessary and there are no hypotheses whose joint satisfiability
could be in question (no ``witness-inconsistent`` risk). Each was checked with
two real ``lake env lean`` builds: it ELABORATES against its rival and FAILS on
the frozen solution, where ``decide`` reports the negation false at exactly the
probed point. So each discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-does-not-resolve
break). Each reject case's ``refinement`` names the concrete test behavior its
faithful counterpart would break -- either the F2P case itself (a non-asynchronous
skipped case run with the debugger option active, which asserts that no teardown
side effect is observed) or a PASS_TO_PASS companion (the same option with a
non-skipped case, which asserts teardown still eventually runs; the ordinary
no-option teardown grid; or the asynchronous-path suite). A rival that verified
while breaking one of those would be a genuine spec hole, not an artifact.

AXIOM lane: EMPTY. ``meta.json`` records ``axioms: []`` and
``deep_model_references: []`` -- the bundle declares no ``opaque`` callee and
consumes no ``axiom``; the decision is a pure Boolean function of three plain
observations. The nagini ``AXIOM_TESTS`` (also empty there) are dropped: the
axiom lane belongs to G-AX.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7236"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is unique in Solution.lean (asserted by _swap at import)
# and lies ENTIRELY inside the region it names, so no swap can reach the spec.
# ---------------------------------------------------------------------------

# The whole executable body of the impl region (everything after the `Id.run do`
# signature line). Rivals that restructure the control flow swap this.
_I_BODY = """  if isAsync then
    -- asynchronous path: the framework runs the case directly; no postponement
    return false
  -- synchronous path: arrange postponement only under the debugger option, and
  -- only when this case is going to actually run its teardown
  if usePdb && !skipped then
    return true
  return false"""

# The trailing decision test alone (the second half of the body), for rivals
# that keep the asynchronous-path early exit verbatim and attack only the guard.
_I_GUARD = """  if usePdb && !skipped then
    return true
  return false"""

# The asynchronous-path early exit alone, for a rival that keeps the synchronous
# guard verbatim and attacks only what the asynchronous path returns.
_I_ASYNC_EXIT = """  if isAsync then
    -- asynchronous path: the framework runs the case directly; no postponement
    return false"""

# The frozen proof's `intro` line -- inside the proof region -- so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro isAsync usePdb skipped"


# ---------------------------------------------------------------------------
# Witness scaffold. The carrier is three `Bool`s, so the refutation is stated at
# a literal triple and `decide` settles it; `unfold` is needed because the spec
# names the rule helper and the impl is an `Id.run do` block. Binds nothing.
# ---------------------------------------------------------------------------
def _witness(isAsync, usePdb, skipped):
    pt = f"{isAsync} {usePdb} {skipped}"
    return (
        f"example : ¬ problem_spec_deferTeardown {pt}\n"
        f"    (implementation_deferTeardown {pt}) := by\n"
        "  unfold problem_spec_deferTeardown teardownDeferralRule "
        "implementation_deferTeardown\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) -- structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Both keep the
    # frozen proof body verbatim (confirmed by real builds), so neither weakens
    # the obligation and neither needs a helper lemma.
    # =====================================================================
    {
        "id": "pos-uncond",
        "kind": "soundness",
        "expect": "verify",
        # Branch-FREE reshape: no early exits at all. The decision is computed
        # for every case in one expression -- with the three conjuncts in a
        # DIFFERENT order than the frozen guard, so this is not a syntactic
        # no-op -- bound to a local, and returned unconditionally. Ports
        # nagini's pos-uncond (there: compute the decision into a local and
        # assign it unconditionally instead of writing a literal under a guard;
        # here the mutable flag is a return value, so the reshape is the same
        # idea on this carrier).
        "module": _swap(_BASE, _I_BODY, """  -- single-exit reshape: the decision is computed for every case in one
  -- branch-free expression and returned unconditionally
  let arranged := !isAsync && !skipped && usePdb
  return arranged"""),
        "rationale": "structurally-different CORRECT impl: every branch and "
                     "early return is removed and the decision is computed as a "
                     "single branch-free conjunction (in a permuted conjunct "
                     "order) bound to a local. It agrees with the rule at all "
                     "eight input points, so C0 still holds -- else "
                     "SPEC-TOO-STRONG. The frozen proof body closes it unchanged "
                     "(the case split still reduces both sides to literals), so "
                     "the `correct_deferTeardown` statement is byte-identical "
                     "and nothing is assumed. Ports nagini's pos-uncond. "
                     "AUDIT NOTE on how much this positive proves: because the "
                     "case split grounds both sides at literals, the frozen "
                     "script closes EVERY correct reshape tried on this carrier "
                     "(commuted guard, renested ifs, De Morgan, `match`, `cond`, "
                     "`let mut` accumulator -- six built, six exit 0). So this "
                     "case establishes that the spec admits a faithful "
                     "single-exit impl, but it is a weak SPEC-TOO-STRONG probe: "
                     "no correct impl was found that this spec rejects.",
    },
    {
        "id": "pos-ifelse",
        "kind": "soundness",
        "expect": "verify",
        # Fully-nested explicit if/else: one test per input, every leaf written
        # out, no fallthrough. The frozen impl instead falls through the
        # asynchronous test and folds two conditions into one conjunction, so
        # the control-flow shape genuinely differs. Ports nagini's pos-ifelse
        # (explicit else arm where the gold omits it).
        "module": _swap(_BASE, _I_BODY, """  if isAsync then
    return false
  else
    if skipped then
      return false
    else
      if usePdb then
        return true
      else
        return false"""),
        "rationale": "second structurally-different CORRECT impl: the folded "
                     "conjunction and the fallthrough are replaced by a fully "
                     "nested if/else that tests one observation per level, in a "
                     "different order, with every leaf written explicitly. Same "
                     "decision at all eight points, so C0 holds -- else "
                     "SPEC-TOO-STRONG. Frozen proof body closes it unchanged; "
                     "statement byte-identical, no new axiom/lemma. Ports "
                     "nagini's pos-ifelse.",
    },

    # =====================================================================
    # ADMISSIBILITY -- confirm the obligation is SATISFIABLE (non-vacuous) at
    # exactly the discriminating F2P-shaped input. The frozen theorem carries no
    # precondition hypotheses, so nagini's "the Requires facts are establishable
    # on a normal input" probe re-expresses as: discharge the spec predicate by
    # evaluation at the F2P triple as a `have`, then close the frozen obligation
    # verbatim. Nothing is assumed: no new declaration, statement byte-identical,
    # the ground instance is a `have` prepended inside the existing tactic body.
    # =====================================================================
    {
        "id": "admiss-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, """  have _ground : problem_spec_deferTeardown false true true
      (implementation_deferTeardown false true true) := by
    unfold problem_spec_deferTeardown teardownDeferralRule implementation_deferTeardown
    decide
""" + _P_INTRO),
        "rationale": "the obligation is discharged by evaluation at the "
                     "discriminating F2P-shaped triple (non-asynchronous, "
                     "debugger option active, marked to skip -> no postponement) "
                     "as a `have`, and the frozen obligation is then closed "
                     "verbatim. Must verify: if the modeled behavior were "
                     "unsatisfiable at exactly a normal F2P input the spec would "
                     "be vacuous there -- the analogue of PRECOND-TOO-STRONG. "
                     "Ports nagini's admiss-pdb-skipped, which builds the same "
                     "scenario; on this carrier there is no precondition to "
                     "establish, so the probe pins the postcondition at that "
                     "input instead. Nothing is assumed and no declaration is "
                     "added.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals -- wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries the refinement argument that its
    # faithful counterpart would NOT resolve, and a witness pinning the
    # violation at one concrete input (seen to discriminate: two real builds).
    # =====================================================================

    # ---- the fix itself: drop the skip conjunct -------------------------
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GUARD, """  if usePdb then
    return true
  return false"""),
        "refinement": "this is the PRE-PATCH decision: on the synchronous path "
                      "postponement is arranged whenever the debugger option is "
                      "active, without consulting whether the case was marked to "
                      "skip. It is the behavior under repair, so its faithful "
                      "counterpart is the unfixed code: the F2P case runs a "
                      "skipped, non-asynchronous case with the option active and "
                      "asserts that no teardown side effect is recorded, but the "
                      "arranged postponement causes the stored teardown to be "
                      "invoked explicitly afterwards and the side effect appears "
                      "-> the F2P still FAILS. It does NOT resolve; the bundle's "
                      "own prepatch variant (G-DIFF) is exactly this impl and is "
                      "recorded as failing verification.",
        "rationale": "REJECT from C0: the rule requires "
                     "`!isAsync && usePdb && !skipped` but the rival computes "
                     "`!isAsync && usePdb`, so the two differ on precisely the "
                     "sub-domain `isAsync=false, usePdb=true, skipped=true` -- "
                     "the single point the fix is about, and the point the "
                     "witness probes. Correct at the other seven points, so the "
                     "rejection is attributable to the `skipped` binder alone.",
        "witness": _witness("false", "true", "true"),
    },

    # ---- invert the skip conjunct --------------------------------------
    {
        "id": "weak-invert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GUARD, """  if usePdb && skipped then
    return true
  return false"""),
        "refinement": "drops the negation on the skip observation, so "
                      "postponement is arranged for exactly the cases that must "
                      "not have it and withheld from the ones that must. Its "
                      "faithful counterpart breaks BOTH directions: the F2P "
                      "skipped case still gets a postponed teardown invoked "
                      "afterwards (F2P FAILS), and the PASS_TO_PASS companion -- "
                      "a non-skipped case run with the debugger option active, "
                      "which asserts teardown is still eventually run for every "
                      "test so the option does not leak instance state -- no "
                      "longer has its teardown postponed or explicitly invoked, "
                      "changing the moment the case interacts with the results "
                      "object. It does NOT resolve.",
        "rationale": "REJECT from C0 on TWO sub-domains: the rival computes "
                     "`!isAsync && usePdb && skipped`, which differs from the "
                     "rule at both `(false, true, false)` and `(false, true, "
                     "true)`. Probed at `(false, true, false)` -- the "
                     "not-skipped point -- rather than at weak-prepatch's "
                     "skipped point, so the two rivals do not share a witness "
                     "and each rationale's sub-domain is the one actually "
                     "demonstrated.",
        "witness": _witness("false", "true", "false"),
    },

    # ---- drop the debugger-option conjunct -----------------------------
    {
        "id": "weak-ignore-option",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_GUARD, """  if !skipped then
    return true
  return false"""),
        "refinement": "drops the debugger-option half of the guard, so "
                      "postponement is arranged for EVERY non-skipped "
                      "synchronous case, option or not. Correct on the whole "
                      "option-active sub-domain, so the F2P and its companion "
                      "both still pass -- but its faithful counterpart postpones "
                      "and then explicitly re-invokes teardown for the entire "
                      "ordinary suite, which changes the moment each case "
                      "interacts with the results object. The no-option "
                      "PASS_TO_PASS teardown grid observes that directly: one "
                      "case asserts a teardown side effect is already visible to "
                      "a later test in the same run, and another asserts a "
                      "failing teardown and a failing test body are reported as "
                      "one failure plus one error in that order. Reordering "
                      "teardown relative to result reporting breaks them -> it "
                      "does NOT resolve.",
        "rationale": "REJECT from C0 on the option-INACTIVE sub-domain: the rule "
                     "requires `false` whenever `usePdb=false`, but the rival "
                     "returns `true` for any non-skipped synchronous case. "
                     "Probed at `(false, false, false)`, which moves the "
                     "`usePdb` binder off the value the two rivals above hold it "
                     "at -- without this case a rival that ignored the option "
                     "entirely would agree with gold at every point the battery "
                     "probed.",
        "witness": _witness("false", "false", "false"),
    },

    # ---- drop the asynchronous-path conjunct (NO nagini counterpart) ----
    {
        "id": "weak-ignore-async",
        "kind": "uniqueness",
        "expect": "reject",
        # Removes the asynchronous-path early exit entirely, so the decision is
        # taken from the other two observations alone. This rival exists to move
        # the `isAsync` binder: nagini's carrier has no such input, so nothing
        # there attacks it, and every other witness here holds it at one value.
        "module": _swap(_BASE, _I_BODY, """  if usePdb && !skipped then
    return true
  return false"""),
        "refinement": "removes the asynchronous-path exclusion, arranging "
                      "postponement for an asynchronous case too whenever the "
                      "option is active and the case is not skipped. Correct on "
                      "the whole synchronous sub-domain, so the F2P and its "
                      "option companion both still pass. Its faithful "
                      "counterpart reaches into a case the framework drives "
                      "entirely itself and swaps out its teardown step, so the "
                      "asynchronous PASS_TO_PASS suite -- which counts the "
                      "teardown invocations of its own cases and asserts an "
                      "exact tally, and asserts an exact passed/failed outcome "
                      "split -- observes a suppressed or twice-driven teardown "
                      "and its tally assertion fails -> it does NOT resolve.",
        "rationale": "REJECT from C0 on the ASYNCHRONOUS sub-domain: the rule "
                     "requires `false` whenever `isAsync=true`, but the rival "
                     "ignores that observation and returns `true` at "
                     "`(true, true, false)`, where the witness probes it. NO "
                     "nagini counterpart -- its carrier does not model this "
                     "observation at all -- so this rival is new work for the "
                     "port, and it is what keeps `isAsync` from being a binder "
                     "every witness holds fixed (an impl mishandling only the "
                     "asynchronous path would otherwise pass the whole battery).",
        "witness": _witness("true", "true", "false"),
    },

    # ---- arrange postponement unconditionally --------------------------
    {
        "id": "weak-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_BODY, """  return true"""),
        "refinement": "arranges postponement for every case unconditionally. Its "
                      "faithful counterpart postpones and later explicitly "
                      "re-invokes teardown for every test -- skipped or not, "
                      "asynchronous or not, option or not -- so the F2P skipped "
                      "case records the teardown side effect it asserts absent "
                      "(F2P FAILS), and the no-option teardown-ordering grid and "
                      "the asynchronous suite are disturbed as well. It does NOT "
                      "resolve.",
        "rationale": "REJECT from C0 wherever the rule is `false`, i.e. at seven "
                     "of the eight points. Carried as the coarse supporting "
                     "near-miss alongside the four reasoned attacks, exactly as "
                     "nagini's pd-always is. Probed at `(true, false, false)` -- "
                     "the point where BOTH the asynchronous exclusion and the "
                     "option conjunct independently force `false` -- which is a "
                     "fifth distinct input triple and is the only witness holding "
                     "`isAsync=true` together with `usePdb=false`.",
        "witness": _witness("true", "false", "false"),
    },

    # ---- ADDED BY AUDIT: the asynchronous-path RETURN VALUE -------------
    # Coverage gap this closes. The five rivals above probe five distinct
    # triples, but all five hold `skipped=false` whenever `isAsync=true`: the
    # three points with `skipped=true` other than the F2P point -- namely
    # `(true,true,true)`, `(false,false,true)` and `(true,false,true)` -- were
    # unprobed. So a rival could postpone on the asynchronous path for exactly
    # the SKIPPED case and satisfy every point the shipped battery probed. This
    # rival does that: it keeps the synchronous guard byte-for-byte and changes
    # only what the asynchronous path returns, so its rejection is attributable
    # to the asynchronous path's interaction with the skip observation alone --
    # a sub-domain no other case reaches. Audit-built, both witness legs re-run.
    {
        "id": "weak-async-skip-corner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_ASYNC_EXIT, """  if isAsync then
    return usePdb && skipped"""),
        "refinement": "keeps the synchronous decision exactly right and changes "
                      "only the asynchronous path, arranging postponement there "
                      "for a case that is marked to skip while the debugger "
                      "option is active. Correct on the whole synchronous "
                      "sub-domain, so the F2P case and its option companion both "
                      "still pass -- which is precisely why it is worth carrying: "
                      "its faithful counterpart reaches into a case the framework "
                      "drives entirely itself and, for a skipped case, swaps out "
                      "the teardown step and arranges for a stored teardown to be "
                      "invoked explicitly afterwards even though nothing ran. The "
                      "asynchronous PASS_TO_PASS suite counts its own cases' "
                      "teardown invocations and asserts an exact tally plus an "
                      "exact passed/failed split, so it observes the extra "
                      "invocation -> it does NOT resolve.",
        "rationale": "REJECT from C0 on the ASYNCHRONOUS-AND-SKIPPED sub-domain: "
                     "the rule requires `false` whenever `isAsync=true`, but the "
                     "rival returns `usePdb && skipped` there, so it differs from "
                     "the rule at `(true, true, true)` -- where the witness probes "
                     "it. That triple is a SIXTH distinct input point and the only "
                     "one in the battery holding all three binders at `true`; "
                     "without it no case combines `isAsync=true` with "
                     "`skipped=true`. Verified by audit builds: the variant fails "
                     "verification (exit 1, `Tactic `rfl` failed`), the witness "
                     "elaborates against the rival (exit 0), and on the frozen "
                     "solution the same witness fails semantically (exit 1, "
                     "`decide` proves the negation false at that point).",
        "witness": _witness("true", "true", "true"),
    },
]
