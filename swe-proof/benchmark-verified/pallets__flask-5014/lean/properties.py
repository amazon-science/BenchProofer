"""properties.py — G-PBT falsification battery for pallets__flask-5014 (lean).

NOT a Lean module: a record of the adversarial cases the G-PBT gate executes.
Each SPEC case is a COMPLETE ``Solution.lean`` variant that shares the FROZEN
spec byte-for-byte — region surgery touches only text inside the single
``-- impl-start``/``-- impl-end`` region and, for the positives, the tactic body
inside ``-- proof-start``/``-- proof-end``; both regions the consumer spec view
elides, so ``markers.same_spec`` holds by construction and the
``theorem correct_construct`` STATEMENT survives byte-identically. ``expect:
"verify"`` passes iff (in scope AND verifies); ``expect:"reject"`` passes iff (in
scope AND does NOT verify AND its refutation ``witness`` discriminates: the
witness must ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one modeled function; the spec is a three-branch input→output
relation over the single input binder ``name : String``):

    problem_spec_construct (name) (result) :=
      if name = ""                 then result = Except.error <empty failure>
      else if name.contains '.'    then result = Except.error <dot failure>
      else                              result = Except.ok { name := name }

    theorem correct_construct : ∀ (name : String),
      problem_spec_construct name (implementation_construct name)

There is NO precondition (the obligation binds ``name`` universally, with no
hypothesis) and NO axiom: the ``axioms`` region is empty and both tests
(``name = ""`` and ``name.contains '.'``) are TRANSPARENT total operations on the
input carrier. Nothing here is an opaque answer-key, so there is no oracle to
echo — the only way to satisfy a branch is to compute the decision the branch
describes. Every witness below is therefore stated at a CONCRETE literal name;
no conditioning on an opaque term is needed and no witness binds a hypothesis
(hence no joint-satisfiability obligation arises).

WHAT THE SPEC DEFENDS, and the attacks it must survive. The three branches are
independent top-level clauses and each is attacked by at least one rival:

  * PRESENCE (``name = "" → <empty failure>``) is the DISCRIMINATING behavior of
    this change: an absent name must FAIL rather than construct. The sole F2P
    demands exactly that. Before the change an empty name fell through to a
    successful construction (``Solution_prepatch.lean`` reproduces that and its
    obligation is unclosable — G-DIFF). ``reject-drop-empty-guard`` is that bug.
  * DOT-FREENESS (``name.contains '.' → <dot failure>``) is the pre-existing
    requirement this change leaves in place; a P2P relies on it.
    ``reject-drop-dot-guard`` removes it, and ``reject-partial-leading-dot``
    weakens it to the FIRST code point only, so it holds on the leading-dot
    sub-domain and fails on the interior-dot sub-domain.
  * SUCCESSFUL CONSTRUCTION (``else result = Except.ok { name := name }``) pins
    BOTH that an acceptable name succeeds and that the constructed value records
    the supplied name UNCHANGED — the frame-discipline analogue on a
    referentially transparent carrier (spec_guide §0.5: the unchanged part of the
    output is pinned explicitly, so nothing is left free for a wrong impl to fill
    in). ``reject-over-reject`` attacks the first half (an acceptable name is
    refused); ``reject-mangle-recorded-name`` attacks the second (an acceptable
    name succeeds, but the recorded name is not the one supplied).

BINDER COVERAGE. The postcondition depends on the single input ``name``, and the
six reject witnesses vary it across FIVE distinct points, one per sub-decision
the spec makes:

  * ``""``     — absent name (dot-free): the presence branch.
  * ``"."``    — a leading dot: the dot branch at the front.
  * ``"a.b"``  — an interior dot: the dot sub-domain a head-only check misses,
                 and (for ``reject-sanitize-recorded-name``) the point where the
                 dot branch and the recorded-value conjunct are broken together.
  * ``"ok"``   — acceptable (non-empty, dot-free): the success branch's decision.
  * ``"test"`` — acceptable: the success branch's RECORDED-VALUE half.

``"a.b"`` is the one point two rivals share, and deliberately: the two rivals
refuted there differ in WHAT they do at it (one stores the dotted name intact,
the other stores a rewritten one), so the witnesses discriminate different
clauses at the same input rather than restating one point twice.

ADVERSARIAL READ of the nagini classes on this carrier (full accounting at the
foot of this file):

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling carries this as
    MANDATORY because its two list inputs are held at a fractional heap
    permission an impl can illegally write through. Lean is referentially
    transparent: ``name`` is an immutable value, there is no heap and no
    aliasing, so there is no read-only input to overwrite. Per the porting map
    this class is vacuous here; no substitute is fabricated. Its INTENT — "the
    part of the output the change does not compute must not be left free" —
    survives as the recorded-name half of the success branch, attacked by
    ``reject-mangle-recorded-name``.
  * DIVERGENCE / NON-TERMINATION — nothing to port (the nagini sibling carries no
    ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case) and NOT shippable here,
    for a reason measured rather than assumed. The frozen file sets no
    ``loom.semantics.termination`` option at all: it is plain Lean, where a
    ``def`` must be total, so the correct disposition for a diverging rival is
    REJECTED. A diverging rival IS writable — ``partial def spin (n : Nat) :
    Except BPError BPState := spin (n + 1)`` with ``implementation_construct
    name := spin 0``, which needs an ``Inhabited BPState`` instance to compile
    and then passes ``variant_problems`` cleanly — and it is duly rejected
    (``Tactic `rfl` failed: ... spin 0 is not definitionally equal to
    Except.error BPError.emptyName``). What blocks SHIPPING it is the witness
    half, not the rejection: ``spin 0`` is irreducible, so a witness stating
    ``¬ problem_spec_construct "" (implementation_construct "")`` against it dies
    at ``failed to synthesize Decidable ¬if True then spin 0 = ...`` — the
    stuck-``Decidable``-instance screen, i.e. the claim is undecidable against
    that impl and the build's exit code carries no information about it. A
    ``witness_reference`` cannot rescue it either: the reference must be REFUTED
    by the witness, but the witness's rival-side build is the half that fails
    here. So the class is a KNOWN LIMIT of the witness requirement on an
    irreducible impl, not a vacuous class and not a spec hole — the spec does
    reject the rival, we simply cannot attribute that rejection to the spec by
    the machine-checked route this gate requires.
    (This is NOT the ``partial``-semantics vacuity class, which is a property of
    the velvet carrier rather than of any spec: under
    ``set_option loom.semantics.termination "partial"`` a non-terminating impl
    satisfies every clause vacuously, so velvet bundles carry an explicit
    total-semantics obligation to foreclose it. Lean's total ``def`` elaborator
    forecloses it outright, so the vacuity claim here is about the CARRIER, not a
    spec hole.)
  * UNGROUNDED-ORACLE ECHO — N/A: both decisions are transparent operations on
    ``name`` (spec_guide §0.8), so there is no answer-key to echo. The cheapest
    honest correct impl is carried as a positive control instead
    (``pos-control-if-expression``).
  * WRONG-CHANNEL / CONTROL-FLOW-EFFECT — omitted, see the accounting note: this
    carrier DOES distinguish the two failures, so such a rival is expressible and
    its witness would discriminate, but it has no honest ``refinement`` argument.
  * AXIOM lane — DROPPED. The axiom lane is G-AX's job and this gate ignores
    ``AXIOM_TESTS``; this bundle also declares no axiom at all (mapping.md §
    "Callee provenance": the ``axioms`` region is empty).

WITNESS MECHANICS. Each reject witness states the spec predicate DIRECTLY at one
concrete name — ``¬ problem_spec_construct <lit> (implementation_construct
<lit>)`` — in a file whose ``proof`` region has been emptied, so no tactic script
can interfere. ``decide`` cannot settle these goals: ``String.contains`` is
``s.any (· == c)`` and its ``Decidable`` instance does not reduce. Measured on
this bundle: ``decide`` on ``("a.b").contains '.' = true`` fails with ``its
`Decidable` instance instDecidableEqBool ("a.b".contains '.') true did not reduce
to `isTrue` or `isFalse```, ``rfl`` fails on the left-hand side, and ``simp``
reports ``made no progress``. The unfolding lemma that does
close it is ``simp [String.contains, String.any_eq]`` — the "find the ``_def``
lemma and hand it to ``simp``" pattern — so every witness discharges the dot test
that way first. ``decide`` cannot close the branch afterwards either: there is
no ``DecidableEq (Except BPError BPState)`` on this carrier (measured: ``failed
to synthesize Decidable ¬Except.ok { name := "." } = Except.error
BPError.dottedName``), so each witness finishes on a CONSTRUCTOR CLASH under
``simp`` instead.

AUDIT REPAIR — the gold-side failure used to attest NOTHING. Five of the six
witnesses (all but reject-mangle-recorded-name) used to end at ``simp [Id.run,
hd]`` and were recorded as discriminating on exit codes alone. Rebuilt with the
gate's own primitives, gold failed with ``unsolved goals hd : ".".contains '.' =
true ⊢ ¬pure (Except.error BPError.dottedName) = Except.error
BPError.dottedName`` — the ``Id``-carrier residue: the script never reduced
``pure``, so the specification was never applied to a value. The deciding test is
the OPPOSITE-CLAIM CONTROL, and it failed IDENTICALLY: the same script with the
leading ``¬`` dropped (i.e. claiming gold DOES satisfy the branch) gave the same
exit 1 and the same goal minus the ``¬``, for all five. Gold's exit code did not
depend on what was claimed, so it was evidence of nothing.

Each of the five now EVALUATES both sides at its literal instead. Everything this
carrier stalls on is supplied as a named fact — the dot test by ``hd``, the
presence test by ``decide`` (``String.decEq`` does reduce on literals), the
front test by ``decide`` where a rival uses one — and ``simp only [Id.run, bind,
pure, ...]`` then reduces ``implementation_construct <lit>`` to a constructor.
The rival's own value at that name is stated as ``hval`` and CLOSED by that
evaluation (never assumed); the spec's firing clause is selected with
``if_pos``/``if_neg`` over the same facts, and the demand it makes is refuted by
the clash. Measured with the gate's primitives (1800 s cap, every build reached
a verdict): rival exit 0 for all five, and gold exit 1 with the two values
exhibited —

    reject-drop-empty-guard        ⊢ Except.error BPError.emptyName = Except.ok { name := "" }
    reject-drop-dot-guard         ⊢ Except.error BPError.dottedName = Except.ok { name := "." }
    reject-partial-leading-dot    ⊢ Except.error BPError.dottedName = Except.ok { name := "a.b" }
    reject-over-reject            ⊢ Except.ok { name := "ok" } = Except.error BPError.emptyName
    reject-sanitize-recorded-name ⊢ Except.error BPError.dottedName = Except.ok { name := "a.b".replace "." "" }

— i.e. gold returns exactly what the branch demands, which is why the refutation
is unavailable there. The opposite-claim control was re-run on each repaired
witness: with gold's value in ``hval`` and the claim positive
(``problem_spec_construct <lit> (implementation_construct <lit>)``), the SAME
script VERIFIES against gold, all five (exit 0, 6.0-8.4 s). The failure is
therefore claim-dependent, which is the property the exit code alone could not
show. reject-mangle-recorded-name was left as it was and is out of this repair's
scope: its gold build already reduces INSIDE the spec's own equation (``Tactic
`decide` proved that the proposition ¬"test" = "test" is false``), i.e. both
recorded names were evaluated to literals there, so what gold prints already
depends on what is claimed. No opposite-claim control is recorded for it: a
positive claim written by hand under a shortened prefix stalled on the ``do``
residue before reaching the spec (``⊢ (if "test" = "" then ... else do
PUnit.unit PUnit.unit Except.ok { name := "test" }) = Except.ok { name :=
"test" }``), which measures that script and not this case.

No witness binds a head hypothesis, uses ``sorry``/``admit``/``native_decide``,
or names anything the frozen solution does not declare.
"""
from pathlib import Path

INSTANCE = "pallets__flask-5014"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Surgery anchors. Both lie ENTIRELY inside a region the spec view elides and
# both are unique in Solution.lean (asserted at load, so any drift in the frozen
# file breaks this manifest loudly instead of silently mis-anchoring).
#
#   _IMPL  — the whole `def implementation_construct` body, strictly inside
#            `-- impl-start`/`-- impl-end`.
#   _PROOF — the frozen tactic body, strictly inside `-- proof-start`/
#            `-- proof-end` (it starts AFTER `:= by`, so the `theorem
#            correct_construct` STATEMENT is untouched by every swap).
# ---------------------------------------------------------------------------
_IMPL = """def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name = "" then
    return Except.error BPError.emptyName
  if name.contains '.' then
    return Except.error BPError.dottedName
  let st : BPState := { name := name }
  return Except.ok st"""
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

_PROOF = """  intro name
  unfold problem_spec_construct implementation_construct
  by_cases he : name = ""
  · simp only [Id.run, he, if_true]; rfl
  · by_cases hd : name.contains '.'
    · simp only [Id.run, he, hd, if_false, if_true]; rfl
    · simp only [Id.run, he, hd, if_false]; rfl"""
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _reproved(new_impl, new_proof):
    """A positive control: reshape the impl AND retune the tactic body so the
    UNCHANGED obligation closes for the new shape. Both edits stay inside the
    elided regions; the theorem statement is byte-identical."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


def _rival(new_impl):
    """A reject rival: replace ONLY the impl, leaving the frozen tactic body in
    place (Rule 2 — the obligation survives with a byte-identical statement).
    The frozen script is tuned to the frozen impl's form, so it no longer closes
    and the variant does not verify; the rejection is ATTRIBUTED to the spec by
    the machine-checked `witness`, never inferred from that tactic breakage."""
    return _swap(_BASE, _IMPL, new_impl)


# `String.contains` is `s.any (· == c)`, whose `Decidable` instance does not
# reduce, so `decide` is stuck on the dot test at every literal. This is the
# unfolding-lemma pair that settles it (see WITNESS MECHANICS above); every
# witness discharges the dot test with it before reducing the branch.
def _dot(lit, value):
    return (f"  have hd : ({lit}).contains '.' = {value} := by\n"
            f"    simp [String.contains, String.any_eq]\n")


# The presence test, unlike the dot test, DOES reduce on a literal
# (`String.decEq` is structural), so `decide` settles it and the spec's first
# branch can be selected by name.
def _ne(lit):
    return f"  have hne : ¬ (({lit} : String) = \"\") := by decide\n"


def _witness_eval(lit, rival_value, facts, simp_set, branch):
    """A refutation that EVALUATES both sides at the concrete name `lit`.

    `facts` discharges every test this carrier stalls on at that name, `simp_set`
    is what those facts let `simp only` use to reduce `implementation_construct
    lit` to a CONSTRUCTOR, `rival_value` is what that reduction yields for the
    rival (a `have` the build must close, never an assumption), and `branch`
    selects the spec clause that fires at `lit` via `if_pos`/`if_neg` over the
    same facts. What is left is a constructor clash, which `simp` closes.

    Why not the shorter `simp [Id.run, hd]` this file used to ship: see WITNESS
    MECHANICS. That script left the `Id` carrier unreduced, so gold died on
    `⊢ ¬pure X = X` and the opposite claim died identically — the exit code was
    independent of what was claimed. Reducing to a constructor is what makes
    gold's failure exhibit the value gold actually returns, and makes the same
    script VERIFY against gold once `hval` names gold's value instead.
    """
    return (f"example : ¬ problem_spec_construct {lit} "
            f"(implementation_construct {lit}) := by\n"
            + facts
            + f"  have hval : implementation_construct {lit} = {rival_value} := by\n"
            + "    unfold implementation_construct\n"
            + f"    simp only [Id.run, bind, pure, {simp_set}]\n"
            + "  unfold problem_spec_construct\n"
            + f"  rw [{branch}, hval]\n"
            + "  simp\n")


# reject-mangle-recorded-name's refutation is a different shape (it descends into
# the constructed value's recorded name and lands on `decide`), so it keeps its
# own tail. No default tail is offered: the one this helper used to default to
# left the carrier unreduced (see WITNESS MECHANICS).
def _witness(lit, dot_value, tail):
    return (f"example : ¬ problem_spec_construct {lit} "
            f"(implementation_construct {lit}) := by\n"
            + _dot(lit, dot_value)
            + "  unfold problem_spec_construct implementation_construct\n"
            + tail)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each carries its own retuned
    # tactic body and was closed out-of-band with a real build; neither weakens
    # the obligation, adds a lemma, or assumes anything.
    # =====================================================================
    {
        "id": "pos-control-if-expression",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest HONEST correct shape: a pure nested conditional EXPRESSION
        # (no do-block, no early returns) that also swaps the presence test for
        # the carrier's dedicated emptiness predicate. Same decision on every
        # input, different control-flow and a different spelling of the presence
        # test — so the proof must bridge `name.isEmpty` and `name = ""` rather
        # than close by `rfl` on the frozen form.
        "module": _reproved(
            """def implementation_construct (name : String) : Except BPError BPState :=
  if name.isEmpty then
    Except.error BPError.emptyName
  else if name.contains '.' then
    Except.error BPError.dottedName
  else
    Except.ok { name := name }""",
            """  intro name
  unfold problem_spec_construct implementation_construct
  by_cases he : name = ""
  · have h1 : name.isEmpty = true := by rw [String.isEmpty_iff]; exact he
    rw [if_pos he, h1]
    simp only [if_true]
  · have h0 : name.isEmpty = false := by
      rw [Bool.eq_false_iff, ne_eq, String.isEmpty_iff]; exact he
    rw [if_neg he, h0]
    simp only [Bool.false_eq_true, if_false]
    by_cases hd : name.contains '.'
    · rw [hd]; simp only [if_true]
    · rw [Bool.not_eq_true] at hd
      rw [hd]; simp only [Bool.false_eq_true, if_false]"""),
        "rationale": "both decisions are TRANSPARENT total operations on `name`, so "
                     "the honest cheapest correct impl is to compute them; this one "
                     "does, as a pure nested conditional expression rather than a "
                     "do-block with early exits, and spells the presence test with the "
                     "carrier's emptiness predicate instead of the literal equality the "
                     "frozen impl uses. It agrees with the frozen impl on every input, "
                     "so all three branches of `problem_spec_construct` must still "
                     "discharge; if it does not verify, the spec is over-fit to the "
                     "frozen control-flow shape => SPEC-TOO-STRONG. Re-expresses the "
                     "nagini pos-control-merged-guard (the cheapest honest impl over "
                     "the grounded decisions); a literal single-guard MERGE is not "
                     "available on this carrier because the two failures are distinct "
                     "outcomes the spec pins separately. Doubles as evidence the spec "
                     "is not echo-vulnerable: there is no opaque answer-key here, so "
                     "any WRONG decision fails its branch.",
    },
    {
        "id": "pos-control-reorder-guards",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the two checks: dot test FIRST, presence test second. The
        # accept set and both failure assignments are unchanged, because the
        # absent name carries no dot — which the retuned proof has to establish
        # explicitly (the frozen script never needs that fact).
        "module": _reproved(
            """def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name.contains '.' then
    return Except.error BPError.dottedName
  if name = "" then
    return Except.error BPError.emptyName
  let st : BPState := { name := name }
  return Except.ok st""",
            """  intro name
  unfold problem_spec_construct implementation_construct
  by_cases he : name = ""
  · subst he
    have hnd : ("" : String).contains '.' = false := by
      simp [String.contains, String.any_eq]
    rw [hnd]
    simp only [Id.run, Bool.false_eq_true, if_false, if_true]
    rfl
  · by_cases hd : name.contains '.'
    · simp only [Id.run, he, hd, if_false, if_true]; rfl
    · rw [Bool.not_eq_true] at hd
      simp only [Id.run, he, hd, Bool.false_eq_true, if_false]; rfl"""),
        "rationale": "a correct impl with the two checks REORDERED (dot test before "
                     "presence test). The two are independent and the absent name "
                     "carries no dot, so the accept set AND the failure assigned to "
                     "each rejected name are both unchanged — the reorder is invisible "
                     "to all three branches of the spec. Must verify; if not, the spec "
                     "is over-fit to the frozen check order => SPEC-TOO-STRONG. Ports "
                     "the nagini pos-control-reorder-guard directly. Note the retuned "
                     "proof must PROVE the absent name is dot-free (a fact the frozen "
                     "script never needs), so this positive exercises spec branch "
                     "precedence and not merely a syntactic permutation.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-self-call. That case
    # self-calls on an F2P-shaped acceptable name to establish that the
    # PRECONDITION admits a normal input. This obligation has NO precondition
    # (`∀ (name : String)`, no hypothesis), so nothing can exclude any input and
    # the classic probe is vacuous IN ITS NAGINI FORM. The analogue on a TOTAL
    # carrier is not "is the precondition satisfiable" but "is the obligation
    # SATISFIABLE AT the F2P-shaped input" — i.e. can the post-image actually be
    # discharged at the concrete absent name `""`, by EVALUATION, rather than
    # only vacuously across a universally quantified domain. A spec whose
    # presence branch demanded something no computation can produce at `""`
    # (PRECOND-TOO-STRONG on a total carrier) would fail exactly there while
    # still looking universally fine.
    #
    # AUDIT NOTE (repair). The previous version of this case shipped
    # `"module": _BASE` — the frozen solution byte-for-byte. It therefore
    # "verified" for the single reason that the frozen solution verifies, which
    # G-GOLD already establishes, and probed NOTHING: no admissibility claim was
    # exercised, and a spec unsatisfiable at the F2P input would have been
    # recorded as PASSING here. Replaced with a variant whose proof region
    # discharges the obligation AT THE CONCRETE F2P-SHAPED INPUT FIRST, as two
    # standalone `have`s closed by evaluation (`""` on the presence branch, an
    # acceptable `"ok"` on the success branch), and only THEN closes the frozen
    # obligation verbatim. Both `have`s are real Lean proof obligations that must
    # reduce, so if either concrete point were unsatisfiable this case now FAILS
    # where the old one passed. The impl region is untouched (the frozen impl),
    # and the theorem STATEMENT is byte-identical — the surgery is inside the
    # elided proof region only.
    # =====================================================================
    {
        "id": "admiss-total-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, """  have hF2P : problem_spec_construct "" (implementation_construct "") := by
    unfold problem_spec_construct implementation_construct
    simp only [Id.run, if_pos (rfl : ("" : String) = "")]
    rfl
  have hAcc : problem_spec_construct "ok" (implementation_construct "ok") := by
    have hd : ("ok").contains '.' = false := by
      simp [String.contains, String.any_eq]
    unfold problem_spec_construct implementation_construct
    simp only [Id.run, if_neg (show ¬ ("ok" : String) = "" by decide), hd,
      Bool.false_eq_true, if_false]
    rfl
""" + _PROOF),
        "rationale": "the obligation quantifies over EVERY `name` with no precondition, "
                     "so on this total carrier the admissibility question is not "
                     "\"does a guard admit the input\" but \"is the obligation "
                     "DISCHARGEABLE AT the F2P-shaped input\". This case answers it "
                     "by CONSTRUCTION at two concrete points before closing the frozen "
                     "obligation: `problem_spec_construct \"\" (implementation_construct "
                     "\"\")` — the F2P-shaped absent name, where the presence branch "
                     "pins failure — and `problem_spec_construct \"ok\" "
                     "(implementation_construct \"ok\")` — an acceptable name of the "
                     "shape the P2P suite constructs, where the success branch pins "
                     "BOTH the outcome and the recorded name. Each is a standalone "
                     "`have` that must reduce by evaluation, so a spec whose branch "
                     "demanded something unreachable at either point would fail HERE, "
                     "which is the PRECOND-TOO-STRONG signal on a total carrier. "
                     "Re-aimed from the nagini admiss-self-call: its "
                     "precondition-admits-the-F2P-input half has no literal counterpart "
                     "on a precondition-free obligation, but its INTENT — the spec must "
                     "be satisfiable at a normal, F2P-shaped input, not merely "
                     "vacuously universal — is exercised directly. Impl region "
                     "untouched; only the elided proof region carries the two `have`s.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked refutation witness
    # at a DISTINCT concrete name (ELABORATES against the rival, FAILS against
    # the frozen solution — both halves confirmed out-of-band with real builds)
    # and the refinement argument for why its faithful real counterpart would
    # NOT resolve the instance.
    # =====================================================================
    {
        "id": "reject-drop-empty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug: drop the presence check, so an absent (and therefore
        # dot-free) name falls through to a SUCCESSFUL construction instead of
        # failing. Correct on every non-empty input; wrong at `""`.
        "module": _rival(
            """def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name.contains '.' then
    return Except.error BPError.dottedName
  let st : BPState := { name := name }
  return Except.ok st"""),
        "refinement": "drops the presence requirement — precisely the behavior before "
                      "this change, which accepted an absent name and constructed the "
                      "component (Solution_prepatch.lean reverts to exactly this). Its "
                      "faithful real counterpart is the unmodified constructor, which is "
                      "what FAILS the sole F2P (an absent name must be refused with a "
                      "ValueError, but the unmodified code constructs successfully) — it "
                      "would NOT resolve. This is the bug the change removes, so a "
                      "verifying rival here would be a true verify-does-not-imply-resolve "
                      "break.",
        "rationale": "REJECT from the PRESENCE branch (`name = \"\" → <empty failure>`): "
                     "at `name = \"\"` the spec demands the empty-name failure, but this "
                     "impl finds no dot and returns a successful construction, so the "
                     "branch is violated. The DISCRIMINATING clause of the change, and a "
                     "partial-domain break — correct on every non-empty name, wrong only "
                     "at the absent one, which is why the witness must probe `\"\"` "
                     "specifically. If it verified => SPEC-TOO-WEAK (the spec admits the "
                     "very bug).",
        # Repaired by audit (see WITNESS MECHANICS): the old witness stopped
        # at the `Id`-carrier residue `⊢ ¬pure (Except.error BPError.emptyName)
        # = Except.error BPError.emptyName`, and the opposite claim failed
        # identically. This one evaluates the rival at `""` (dot-free, so the
        # rival constructs) and refutes the presence branch's demand; gold's
        # build now prints `⊢ Except.error BPError.emptyName = Except.ok
        # { name := "" }` — the failure the branch demands, which is why the
        # refutation is unavailable there.
        "witness": _witness_eval(
            '""', 'Except.ok { name := "" }',
            _dot('""', "false"),
            "hd, Bool.false_eq_true, if_false, if_true",
            'if_pos (rfl : ("" : String) = "")'),
    },
    {
        "id": "reject-drop-dot-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the dot check, so a dotted name is constructed instead of
        # failing. Correct on every dot-free input; wrong on every dotted one.
        "module": _rival(
            """def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name = "" then
    return Except.error BPError.emptyName
  let st : BPState := { name := name }
  return Except.ok st"""),
        "refinement": "drops the dot requirement this change leaves in place. Its "
                      "faithful real counterpart removes the guard that refuses a name "
                      "carrying the reserved separator, which FAILS the P2P asserting "
                      "such a name raises a ValueError (the suite constructs a dotted "
                      "name and expects the refusal) — so the instance would NOT resolve "
                      "even though the F2P's own absent-name case still passes. A "
                      "verifying rival here is therefore a real verify-not-resolve break, "
                      "not an artifact.",
        "rationale": "REJECT from the DOT branch (`name.contains '.' → <dot failure>`), a "
                     "clause independent of the presence branch the previous rival "
                     "attacks: at `name = \".\"` the spec demands the dot failure, but "
                     "this impl finds the name non-empty and constructs successfully. "
                     "Witness at `\".\"` — a distinct binder value from `\"\"`, and the "
                     "leading-dot point specifically. If it verified => SPEC-TOO-WEAK "
                     "(the dot guarantee is hollow).",
        # Repaired by audit (see WITNESS MECHANICS): evaluates the rival at
        # `"."` — non-empty, so it constructs — and refutes the dot branch's
        # demand. Gold's build prints `⊢ Except.error BPError.dottedName =
        # Except.ok { name := "." }`.
        "witness": _witness_eval(
            '"."', 'Except.ok { name := "." }',
            _dot('"."', "true") + _ne('"."'),
            "if_neg hne, hd, if_true",
            "if_neg hne, if_pos hd"),
    },
    {
        "id": "reject-partial-leading-dot",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the dot branch: test only the FIRST code point, so a name
        # whose dot is interior is constructed. Agrees with gold on the absent
        # name AND on every leading-dot name — strictly more of the domain than
        # reject-drop-dot-guard — so it needs its own witness at an INTERIOR dot.
        "module": _rival(
            """def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name = "" then
    return Except.error BPError.emptyName
  if name.front = '.' then
    return Except.error BPError.dottedName
  let st : BPState := { name := name }
  return Except.ok st"""),
        "refinement": "weakens the dot requirement to the FIRST code point only, so a "
                      "name whose separator sits in the interior is accepted. Its "
                      "faithful real counterpart tests only a leading separator, which "
                      "accepts the interior-dotted name the suite uses and so FAILS the "
                      "P2P asserting that name is refused with a ValueError — it would "
                      "NOT resolve.",
        "rationale": "REJECT from the DOT branch on the INTERIOR-dot sub-domain: at "
                     "`name = \"a.b\"` the spec demands the dot failure, but this impl "
                     "sees a non-dot first code point and constructs successfully. A "
                     "genuine partial-domain break, and a NEAR-MISS of "
                     "reject-drop-dot-guard: it agrees with the frozen solution on the "
                     "absent name and on EVERY leading-dot name, so the leading-dot "
                     "witness `\".\"` does not refute it and it carries its own witness "
                     "at the interior-dot point `\"a.b\"` — the sub-domain its rationale "
                     "claims. That is what shows the dot decision must span the WHOLE "
                     "name, not just its head. Ports the nagini "
                     "rival-partial-domain-leading-dot. If it verified => SPEC-TOO-WEAK "
                     "(domain-incomplete dot check).",
        # Repaired by audit (see WITNESS MECHANICS). The rival's head-only
        # test is discharged as `hf` (`String.front` reduces on a literal, so
        # `decide` settles it) alongside the two the frozen impl uses, so the
        # rival evaluates to a SUCCESS at the interior-dot name while the dot
        # branch demands a failure. Gold's build prints `⊢ Except.error
        # BPError.dottedName = Except.ok { name := "a.b" }`.
        "witness": _witness_eval(
            '"a.b"', 'Except.ok { name := "a.b" }',
            _dot('"a.b"', "true") + _ne('"a.b"')
            + "  have hf : ¬ ((\"a.b\").front = '.') := by decide\n",
            "if_neg hne, if_neg hf, hd, if_true",
            "if_neg hne, if_pos hd"),
    },
    {
        "id": "reject-over-reject",
        "kind": "uniqueness",
        "expect": "reject",
        # OVER-REJECTION: fail for every name, so an acceptable name never
        # constructs. Correct on the absent name, wrong on the whole accept
        # sub-domain — the only rival that varies the binder to an ACCEPTED
        # input's outcome.
        "module": _rival(
            """def implementation_construct (name : String) : Except BPError BPState := Id.run do
  return Except.error BPError.emptyName"""),
        "refinement": "refuses every name unconditionally. Its faithful real counterpart "
                      "raises a ValueError for any name at all, which FAILS every P2P "
                      "that constructs a component with an ordinary name — and the suite "
                      "constructs one in dozens of tests — so the instance would NOT "
                      "resolve.",
        "rationale": "REJECT from the SUCCESS branch (`else result = Except.ok { name := "
                     "name }`) on its outcome half: at the acceptable name `\"ok\"` "
                     "(non-empty, dot-free) the spec demands a successful construction, "
                     "but this impl reports a failure. The only rival that probes the "
                     "ACCEPT sub-domain, which is what demonstrates the spec pins "
                     "acceptance and not merely refusal — a spec constraining only the "
                     "two failure branches would admit this impl. Witness at `\"ok\"`. "
                     "Ports the nagini rival-over-reject. If it verified => "
                     "SPEC-TOO-WEAK (admits refusing acceptable names).",
        # Repaired by audit (see WITNESS MECHANICS). This is the one witness
        # that refutes the SUCCESS branch, so the clash runs the other way: the
        # rival evaluates to a failure at an acceptable name while the branch
        # demands `Except.ok { name := "ok" }`. Gold's build prints `⊢ Except.ok
        # { name := "ok" } = Except.error BPError.emptyName`.
        "witness": _witness_eval(
            '"ok"', 'Except.error BPError.emptyName',
            _dot('"ok"', "false") + _ne('"ok"')
            + "  have hnd : ¬ ((\"ok\").contains '.' = true) := by simp [hd]\n",
            "if_neg hne, hd, Bool.false_eq_true, if_false",
            "if_neg hne, if_neg hnd"),
    },
    {
        "id": "reject-mangle-recorded-name",
        "kind": "uniqueness",
        "expect": "reject",
        # The accept/reject DECISION is exactly gold's — every name is routed to
        # the same outcome — but the constructed value records a TRUNCATED name.
        # This is the referentially-transparent analogue of the nagini
        # frame-mutation intent: the component of the output the change does not
        # decide must still be pinned to the input (spec_guide §0.5).
        "module": _rival(
            """def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name = "" then
    return Except.error BPError.emptyName
  if name.contains '.' then
    return Except.error BPError.dottedName
  let st : BPState := { name := name.take 1 }
  return Except.ok st"""),
        "refinement": "keeps the accept/reject decision exactly right and corrupts only "
                      "the value recorded on success (it stores a truncated name). Its "
                      "faithful real counterpart stores a prefix of the supplied name "
                      "instead of the name itself; the F2P's absent-name refusal still "
                      "passes, but every P2P that resolves an endpoint through the "
                      "component's own name breaks (a component registered under a "
                      "truncated name cannot be addressed by the name the test uses) — "
                      "so it would NOT resolve. That the failure lands in the P2P set "
                      "rather than the F2P is exactly why this rival matters: a spec "
                      "that pinned only the accept/reject decision would verify it.",
        "rationale": "REJECT from the SUCCESS branch on its RECORDED-VALUE half (`result "
                     "= Except.ok { name := name }`, the `{ name := name }` part): at the "
                     "acceptable name `\"test\"` the impl succeeds — the decision is "
                     "gold's — but records a different name, so the equality fails. This "
                     "is the frame-discipline probe on a referentially transparent "
                     "carrier (spec_guide §0.5): the part of the output the change does "
                     "not decide must be pinned to the input, or a wrong impl can put "
                     "anything there. It carries the INTENT of the nagini frame-mutation "
                     "rivals, whose heap-permission mechanics are vacuous here, without "
                     "fabricating a heap. Distinct from reject-over-reject: that rival "
                     "gets the outcome wrong, this one gets the outcome RIGHT on every "
                     "input and only the payload wrong, so no other witness refutes it. "
                     "Witness at `\"test\"`. If it verified => SPEC-TOO-WEAK (the "
                     "recorded name unconstrained).",
        "witness": _witness(
            '"test"', "false",
            tail="  intro h\n"
                 "  rw [if_neg (show ¬ (\"test\" : String) = \"\" by decide), hd] at h\n"
                 "  simp only [Bool.false_eq_true, if_false, Id.run, pure] at h\n"
                 "  injection h with h2\n"
                 "  injection h2 with h3\n"
                 "  exact absurd h3 (by decide)\n"),
    },
    # =====================================================================
    # ADDED BY AUDIT. The five rivals above each break ONE clause in isolation:
    # a branch's decision, or the success branch's payload. None of them attacks
    # the COMBINATION — an impl that repairs a dotted name instead of refusing
    # it, so the dot branch is violated AND the recorded-name conjunct is
    # violated, by the same single edit, at the same input. That is the shape a
    # spec pinning only "some failure occurs for some dotted names" or only
    # "the recorded name is some function of the input" would admit, and it is
    # not covered by reject-drop-dot-guard (which returns a plain success with
    # the name INTACT) nor by reject-mangle-recorded-name (whose accept/reject
    # decision is exactly gold's). Both halves machine-checked out of band.
    # =====================================================================
    {
        "id": "reject-sanitize-recorded-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Accepts a dotted name and STRIPS the dots from the recorded value,
        # rather than refusing it. Violates the dot branch (no failure at a
        # dotted name) and the success branch's payload conjunct (the recorded
        # name is not the supplied one) in one edit, at one input.
        "module": _rival(
            """def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name = "" then
    return Except.error BPError.emptyName
  let st : BPState := { name := name.replace "." "" }
  return Except.ok st"""),
        "refinement": "accepts a name carrying the reserved separator and silently "
                      "rewrites it to a separator-free one instead of refusing it. Its "
                      "faithful real counterpart strips the separator rather than "
                      "raising, which FAILS the P2P asserting a dotted name is refused "
                      "with a ValueError (it constructs successfully instead of "
                      "raising) — and ALSO breaks every P2P that addresses the "
                      "component by the name it was given, since the stored name no "
                      "longer matches. It would NOT resolve on either count, so this is "
                      "a real verify-not-resolve break rather than an artifact.",
        "rationale": "REJECT from the DOT branch AND the SUCCESS branch's recorded-value "
                     "conjunct simultaneously: at `name = \"a.b\"` the spec demands the "
                     "dot failure, but this impl constructs successfully — and the value "
                     "it constructs records `\"ab\"`, not the supplied `\"a.b\"`, so even "
                     "a spec that only required SOME successful construction there would "
                     "still be violated. Distinct from every other rival in the set: "
                     "reject-drop-dot-guard also accepts a dotted name but stores it "
                     "UNCHANGED, and reject-mangle-recorded-name also corrupts the "
                     "payload but routes every name to gold's own outcome. This is the "
                     "only rival whose single edit breaks two independent clauses at one "
                     "input, which is what shows the two are pinned CONJOINTLY and not "
                     "as alternatives. If it verified => SPEC-TOO-WEAK.",
        # Repaired by audit (see WITNESS MECHANICS). The rival's recorded name
        # `("a.b").replace "." ""` is left UNEVALUATED on purpose: `String.replace`
        # is not kernel-reducible here (`rfl`, `decide` and `simp` all fail to
        # settle `("a.b").replace "." "" = "ab"`, the last with `String.replace.loop`
        # stuck), and the refutation does not need its value — the dot branch
        # demands a FAILURE and this rival returns a success whatever it records.
        # Gold's build prints `⊢ Except.error BPError.dottedName = Except.ok
        # { name := "a.b".replace "." "" }`.
        "witness": _witness_eval(
            '"a.b"', 'Except.ok { name := ("a.b").replace "." "" }',
            _dot('"a.b"', "true") + _ne('"a.b"'),
            "if_neg hne, hd, if_true",
            "if_neg hne, if_pos hd"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING (which cases ported, which did not, and why).
#
# The nagini sibling contracts a wider surface over TWO inputs — the name plus a
# second, module-identifying argument — covering the presence guard, the dot
# guard, AND a base-initialiser exception channel keyed on that second input,
# with both list inputs held read-only at a fractional heap permission. This
# lean bundle models ONLY the name validation and the field the
# validation stores (`implementation_construct (name : String) : Except BPError
# BPState`, mapping.md § "The observable behavior"): the base initialisation is
# abstracted out of the modeled state entirely because it is unchanged by this
# fix and orthogonal to the observable. That is CARRIER NARROWING, so several
# nagini cases have no counterpart at all — case-count parity is not the target.
#
#   nagini case                       -> here                           disposition
#   -----------------------------------------------------------------------------------
#   pos-control-merged-guard          -> pos-control-if-expression      RE-EXPRESSED
#   pos-control-reorder-guard         -> pos-control-reorder-guards      PORTED
#   admiss-self-call                  -> admiss-total-domain             RE-AIMED
#   rival-drop-empty-guard            -> reject-drop-empty-guard         PORTED
#   rival-drop-dot-guard              -> reject-drop-dot-guard           PORTED
#   rival-partial-domain-leading-dot  -> reject-partial-leading-dot      PORTED
#   rival-over-reject                 -> reject-over-reject              PORTED
#   frame-mutate-name                 -> reject-mangle-recorded-name     RE-EXPRESSED
#   frame-mutate-import-name          -> (none)                          VACUOUS
#   rival-wrong-exc-on-reject         -> (none)                          OMITTED (no
#                                                                        refinement)
#   AXIOM_TESTS (3, base initialiser) -> (none)                          DROPPED (G-AX)
#   (no diverge-*/nonterm-*/weak-diverge case exists in the nagini sibling)
#   (none)                            -> reject-sanitize-recorded-name   ADDED BY AUDIT
#
# 9 lean SPEC cases: 2 soundness, 1 admissibility, 6 uniqueness.
#
# RE-EXPRESSED (pos-control-merged-guard -> pos-control-if-expression): the
#   nagini positive merges the two reject guards into one disjunctive guard,
#   arguing that the cheapest HONEST impl still has to compute the grounded dot
#   test. A literal merge is unavailable here because the two failures are
#   DISTINCT outcomes the spec assigns separately, so the same argument is made
#   with the cheapest honest shape this carrier does admit: a pure nested
#   conditional expression that also swaps the presence test for the carrier's
#   emptiness predicate.
# RE-AIMED (admiss-self-call -> admiss-total-domain): the nagini case exists to
#   show the fractional-permission PRECONDITION admits an F2P-shaped input. This
#   obligation has no precondition at all, so that LITERAL probe is vacuous;
#   re-aimed at the total-carrier analogue — the obligation being DISCHARGEABLE
#   at exactly an F2P-shaped input. AUDIT REPAIR: the case previously shipped the
#   frozen solution byte-for-byte as its module, so it verified because gold
#   verifies (which G-GOLD already says) and tested nothing at all. It now
#   discharges the obligation at the concrete absent name `""` and at an
#   acceptable name `"ok"` as standalone `have`s, by evaluation, BEFORE closing
#   the frozen obligation verbatim — so an unsatisfiable branch at either
#   concrete point now fails this case instead of passing it.
# RE-EXPRESSED (frame-mutate-name -> reject-mangle-recorded-name): the nagini
#   frame rivals write through a read-only reference and must fail on PERMISSION,
#   not on a value mismatch. Lean has no heap, no aliasing and no fractional
#   permission, so that MECHANISM is vacuous (porting map) and no heap is
#   fabricated. Its INTENT — the output component the fix does not compute must
#   be pinned to the input, or a wrong impl fills it freely (spec_guide §0.5) —
#   is live here, because the success branch pins the RECORDED NAME as well as
#   the outcome. reject-mangle-recorded-name attacks exactly that conjunct and
#   is refuted by a witness at an acceptable name, with a real refinement
#   argument (a truncated recorded name breaks the P2P endpoint resolution).
# VACUOUS (frame-mutate-import-name): the second read-only input does not exist
#   on this carrier — the module-identifying argument is not modeled at all
#   (mapping.md § "Callee provenance": the base initialisation is abstracted out,
#   being unchanged and orthogonal), and there is no heap to mutate. No
#   substitute fabricated.
# OMITTED, NOT VACUOUS (rival-wrong-exc-on-reject) — reported rather than
#   shipped. Unlike the velvet sibling's single-Bool carrier, THIS carrier does
#   distinguish the two failures (`BPError.emptyName` vs `BPError.dottedName`),
#   so the channel-swap rival IS expressible and a discriminating witness does
#   exist for it. It is omitted because it has no honest `refinement` argument:
#   both modeled failures refine to the SAME real observable (a ValueError), and
#   the F2P and the dotted-name P2P both assert only `pytest.raises(ValueError)`
#   with no message match, so a faithful real counterpart that reported the two
#   failures the other way round WOULD still resolve the instance. Shipping it
#   would assert a verify-does-not-imply-resolve break that does not exist. Note
#   what this says about the frozen spec: pinning WHICH failure occurs is
#   STRONGER than the tests require — safe for the `verify => resolve`
#   direction, but it means no rival can be built on that distinction alone.
# DROPPED (AXIOM_TESTS): the three nagini probes fuzz a @ContractOnly base-init
#   axiom against the real callee — G-AX's lane, ignored by this gate. This
#   bundle declares no axiom at all (the `axioms` region is empty), so there is
#   nothing for them to describe here.
#
# AUDIT ADDENDUM — attacks run against the FROZEN spec that did NOT break it.
#   Recorded because a spec's strength is only as evidenced as the attacks it
#   survived, and these were real builds, not arguments. Every one was REJECTED
#   (exit 1) as it should be:
#     - swap the two failure channels (empty name reports the dot failure and
#       vice versa) — rejected; witness at `""` discriminates (rival 0 / gold 1).
#       Not shipped as a case, for the refinement reason recorded above: both
#       modeled failures refine to the same real observable.
#     - merge the two channels (both failures report the empty-name error) —
#       rejected; witness at `"."` discriminates. Same refinement objection.
#     - weaken the dot test to a TRAILING-dot blind spot (`(name.dropRight
#       1).contains '.'`) — rejected; witness at `"a."` discriminates.
#     - over-strict presence test (`name.length < 2`, refusing a one-character
#       name) — rejected; witness at `"a"` discriminates. This is the
#       PRECOND-TOO-STRONG direction from the rival side: the spec does pin that
#       a one-character acceptable name SUCCEEDS.
#     - `name.trim = ""` as the presence test (whitespace-only names refused) —
#       rejected, but NOT shippable: `String.trim` is not kernel-reducible
#       (`decide`, `decide +kernel`, `rfl` and `simp` all fail to settle
#       `(" " : String).trim = ""`), so no witness can be stated at a
#       whitespace-only point. A tooling limit, recorded rather than hidden.
#   And correct RESHAPES that the spec ACCEPTS (the spec-too-strong direction),
#   each verified as its own build beyond the two shipped positives: a
#   `match name.isEmpty, name.contains '.' with` three-way match; an
#   `Except.bind` pipeline that checks the dot first and re-checks emptiness on
#   the constructed value; and a two-stage impl routing through an impl-region
#   helper `def classify : String -> Option BPError`. All three VERIFY, so the
#   spec is not over-fit to the frozen control-flow shape.
#
# CLAUSE / BINDER / POINT COVERAGE (what the coverage tool does not check for
#   itself). The one obligation `correct_construct` is DEFENDED by three
#   expect="verify" cases and ATTACKED by six expect="reject" rivals. All three
#   independent top-level branches of `problem_spec_construct` are attacked:
#   presence (reject-drop-empty-guard), dot-freeness (reject-drop-dot-guard and,
#   on the interior sub-domain, reject-partial-leading-dot), and success — both
#   its outcome half (reject-over-reject) and its recorded-value half
#   (reject-mangle-recorded-name) — plus the two CONJOINED in one edit at one
#   input (reject-sanitize-recorded-name). The single input binder `name` is
#   varied across FIVE distinct witness points (pts=5): "" / "." / "a.b" / "ok" /
#   "test". The two near-miss pairs are separated at the input that distinguishes
#   them (leading vs interior dot; wrong outcome vs wrong payload). Both sides of
#   the accept/reject decision are probed, so no sub-decision is held at a single
#   value across the reject set.
AXIOM_TESTS = []
