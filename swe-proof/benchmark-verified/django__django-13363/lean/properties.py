"""properties.py — G-PBT falsification battery for django__django-13363 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside a ``-- impl-start`` / ``-- impl-end`` region — and, for
a case that legitimately re-proves, inside a ``-- proof-start`` / ``-- proof-end``
region — is changed, so ``markers.same_spec`` holds and every ``theorem
correct_*`` STATEMENT stays byte-identical). ``expect="verify"`` passes iff the
variant elaborates with its obligation closed (no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect="reject"`` passes
iff the variant does NOT verify AND the case's ``witness`` holds of the rival
while FAILING on the frozen solution.

DEFENDED SURFACE. Two byte-identical modeled functions build a database cast SQL
string from an already-compiled inner fragment ``lhs`` and a chosen conversion
zone. Each has ONE load-bearing (and only) postcondition clause:

  problem_spec_truncDateCast lhs useTz requestedZone currentZone result : Prop
    result = castDate lhs (conversionZoneName useTz requestedZone currentZone)
  problem_spec_truncTimeCast lhs useTz requestedZone currentZone result : Prop
    result = castTime lhs (conversionZoneName useTz requestedZone currentZone)

where the deeply-modeled selection is
  conversionZoneName useTz requestedZone currentZone
    = if useTz then some (requestedZone.getD currentZone) else none
i.e. OFF -> no zone; ON with a supplied zone -> that zone (supplied HONOURED);
ON without one -> the ambient default. ``castDate`` / ``castTime`` are UNCHANGED
collaborators, declared ``opaque`` (no constraining axiom): the clause is
grounded in the actual inputs, not an answer-key (spec_guide directive 8). The
clause pins TWO things at once — (a) the selected zone is exactly the deep model
(the F2P discriminator: a supplied zone must win over the ambient one), and
(b) the compiled inner fragment is passed to the cast UNCHANGED (frame: the cast
is applied to ``lhs`` itself, directive 5).

BINDER STRUCTURE. Each spec depends on all four inputs. ``useTz`` gates the
whole selection; ``requestedZone`` is the supplied zone that must take precedence
when present; ``currentZone`` is the ambient fallback; ``lhs`` is the framed
passthrough. The four reject witnesses per obligation VARY every input binder
(useTz {true,false}, requestedZone {some,none}, currentZone and lhs at distinct
literals), so no rival is refuted at a pinned binder — and each of the selection's
three arms plus the frame is witnessed on BOTH obligations (see the arm table in
the accounting block, which is what a rejection COUNT cannot certify).

CARRIER NOTES on the nagini classes (see the accounting block at the bottom for
the full port ledger):

  * FRAME / PERMISSION MUTATION — the nagini sibling holds each read-only input
    at ``Acc(.,1/2)`` and its mandatory rivals WRITE to them (``.append``). Lean
    is referentially transparent: every input is an immutable value with no heap
    footprint and no ``mut`` alias, so there is no read-only field to overwrite
    and that class is VACUOUS here (porting map). It is NOT fabricated. What the
    frame OBLIGATION becomes on this carrier is directive-5 pinning — the spec
    fixes the cast's first argument to ``lhs`` — and THAT is attacked directly by
    a rival that hands the cast a different (constant) fragment.

  * OPAQUE CALLEE. ``castDate`` / ``castTime`` carry no axiom, so a literal input
    does not COMPUTE and ``decide`` gets stuck on the opaque application. Every
    reject witness therefore CONDITIONS on the carrier: it assumes only that the
    cast distinguishes the two zones (or the two fragments) it is handed — e.g.
    ``castDate "x" (some "B") ≠ castDate "x" (some "A")`` — and derives that the
    rival's result then differs from the spec's. That single, satisfiable
    hypothesis is exactly the sub-domain where the rival is wrong; against gold
    the same statement reduces to ``castDate _ z ≠ castDate _ z`` and fails.

  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a cast APPLIED to input-
    derived arguments, not an axiomatized answer-key. ``pos-echo`` returns the
    deep model directly and is value- and definitionally-correct, an honest
    cheapest positive control (not a wrong echo).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl — the frozen ``cases useTz <;> cases requestedZone <;> rfl`` is
tuned to the frozen do-block — so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet proving the
rival CONTRADICTS the spec at one concrete (carrier-conditioned) input. Each was
checked with real ``lake`` builds to ELABORATE against its rival, to FAIL against
the frozen solution (so it discriminates rather than asserting a tautology), and
to leave ``False`` UNDERIVABLE from its lone hypothesis (so the refuted input
exists).

Each was ALSO put through the forgery test, because a gold-side failure is
admissible evidence only if it CHANGES when the claim changes. Asserting the
OPPOSITE (dropping the ``¬``, i.e. claiming gold is correct at that input) makes
gold SUCCEED and the rival FAIL — the inverse of the witness — and revealing the
post-``simp`` goal shows it is ``False`` on gold (the equation was PROVED) versus
the concrete disequation on the rival. So gold's exit code carries information
about the claim, and none of these rejections rests on a tactic mismatch.

AXIOM lane: EMPTY. ``castDate`` / ``castTime`` are unchanged collaborators
applied identically on both sides and consume no behavioral axiom; the axiom
lane is G-AX's job and this gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "django__django-13363"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean, verified at load) ----
# The load-bearing shape of each impl region: the mutable do-block that selects
# the conversion zone and hands it, with `lhs`, to the (unchanged) cast. Every
# impl reshape lands entirely inside the matching `-- impl-start`/`-- impl-end`.
_IMPL_DATE = (
    "  let mut tzname : Option String := none\n"
    "  if useTz then\n"
    "    match requestedZone with\n"
    "    | none => tzname := some currentZone\n"
    "    | some z => tzname := some z\n"
    "  return castDate lhs tzname")
_IMPL_TIME = (
    "  let mut tzname : Option String := none\n"
    "  if useTz then\n"
    "    match requestedZone with\n"
    "    | none => tzname := some currentZone\n"
    "    | some z => tzname := some z\n"
    "  return castTime lhs tzname")

# Frozen tactic bodies (each lies wholly inside a `-- proof-start`/`-- proof-end`
# region). Only a positive that legitimately re-proves touches these; the reject
# rivals leave them frozen (they are judged by their witness).
_PROOF_DATE = (
    "  intro lhs useTz requestedZone currentZone\n"
    "  unfold problem_spec_truncDateCast implementation_truncDateCast"
    " conversionZoneName\n"
    "  cases useTz <;> cases requestedZone <;> rfl")
_PROOF_TIME = (
    "  intro lhs useTz requestedZone currentZone\n"
    "  unfold problem_spec_truncTimeCast implementation_truncTimeCast"
    " conversionZoneName\n"
    "  cases useTz <;> cases requestedZone <;> rfl")


def _with_impls(new_date, new_time):
    """Solution.lean with ONLY the two impl bodies replaced (spec/proof intact)."""
    return _swap(_swap(_BASE, _IMPL_DATE, new_date), _IMPL_TIME, new_time)


def _reject_date(new_date):
    """Reshape ONLY the date impl; the time impl (and both proofs) stay frozen."""
    return _swap(_BASE, _IMPL_DATE, new_date)


def _reject_time(new_time):
    """Reshape ONLY the time impl; the date impl (and both proofs) stay frozen."""
    return _swap(_BASE, _IMPL_TIME, new_time)


# ---- witness scaffold. The spec is a bare predicate over `opaque` casts, so a
# ---- witness CONDITIONS on the carrier: one hypothesis `h` that the cast
# ---- distinguishes the two arguments the rival and the spec disagree on. After
# ---- `unfold ...; simp`, the goal is exactly `h`. Checked in a file whose frozen
# ---- obligations are elided by the gate, so no tactic script masks the verdict.
def _admiss(proof_date, proof_time):
    """Solution.lean with a ground instance prepended INSIDE each proof region.

    The frozen obligation is then closed verbatim after it, so the statement
    stays byte-identical and nothing is assumed (a `have` is not a new
    declaration).
    """
    return _swap(_swap(_BASE, _PROOF_DATE, proof_date), _PROOF_TIME, proof_time)


# The admissibility ground instance. On a TOTAL carrier the analogue of a
# precondition admitting a normal input is the obligation being SATISFIABLE at a
# concrete F2P-shaped input — conversion ON with a caller-supplied zone `Z1` that
# differs from the ambient `Z0` — which this discharges BY EVALUATION (`_adm_sel`
# computes the selection; `conversionZoneName` is deeply modeled over
# Bool/Option/String, so it reduces even though the casts are opaque) and then
# uses to build the postcondition at that input (`_adm_ground`) before closing
# the frozen obligation verbatim. Load-bearing, not decoration: measured, the
# same case with `_adm_sel` claiming the AMBIENT zone (`= some "Z0"`) FAILS with
# `⊢ False`, so the `have` really pins supplied-over-ambient at that input.
def _admiss_body(op, cast, proof):
    return (
        f"  have _adm_sel : conversionZoneName true (some \"Z1\") \"Z0\"\n"
        f"      = some \"Z1\" := by\n"
        f"    unfold conversionZoneName; simp\n"
        f"  have _adm_ground : problem_spec_trunc{op}Cast \"c\" true"
        f" (some \"Z1\")\n"
        f"      \"Z0\" ({cast} \"c\" (some \"Z1\")) := by\n"
        f"    unfold problem_spec_trunc{op}Cast\n"
        f"    rw [_adm_sel]\n"
        + proof)


def _witness(op, args, hyp):
    return (
        f"example {hyp} :\n"
        f"    ¬ problem_spec_trunc{op}Cast {args}\n"
        f"      (implementation_trunc{op}Cast {args}) := by\n"
        f"  unfold problem_spec_trunc{op}Cast implementation_trunc{op}Cast"
        " conversionZoneName\n"
        "  simp\n"
        "  exact h\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps every
    # `theorem correct_*` statement byte-identical. Both defend BOTH obligations
    # (the variant reshapes both impls at once).
    # =====================================================================
    {
        "id": "pos-echo-deep-model",
        "kind": "soundness",
        "expect": "verify",
        # Honest cheapest impl: return the deeply-modeled selection applied to the
        # cast directly, dropping the mutable do-block. The result is now
        # definitionally `castX lhs (conversionZoneName ...)`, so the obligation
        # closes with `intro ...; rfl` (proof retuned; statement byte-identical).
        # Verified with a real build.
        "module": _swap(_swap(
            _with_impls(
                "  castDate lhs (conversionZoneName useTz requestedZone"
                " currentZone)",
                "  castTime lhs (conversionZoneName useTz requestedZone"
                " currentZone)"),
            _PROOF_DATE, "  intro lhs useTz requestedZone currentZone\n  rfl"),
            _PROOF_TIME, "  intro lhs useTz requestedZone currentZone\n  rfl"),
        "rationale": "structurally different CORRECT reshape: returns the deep "
                     "model applied to the cast directly, so `result = castX lhs "
                     "(conversionZoneName ...)` holds definitionally on every "
                     "input — it must verify, else SPEC-TOO-STRONG. Proof retuned "
                     "to `intro ...; rfl`; no new axiom/lemma, statements "
                     "unchanged. Defends both obligations.",
    },
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Guard-clause / early-return shape: select and wrap the zone in the SAME
        # `Id.run do`, returning at each branch instead of assigning a mutable
        # slot. Definitionally equal to the frozen impl on every input, so the
        # FROZEN proof (`cases useTz <;> cases requestedZone <;> rfl`) still
        # closes it — no proof authoring. Verified with a real build.
        "module": _with_impls(
            "  if useTz then\n"
            "    match requestedZone with\n"
            "    | some z => return castDate lhs (some z)\n"
            "    | none => return castDate lhs (some currentZone)\n"
            "  return castDate lhs none",
            "  if useTz then\n"
            "    match requestedZone with\n"
            "    | some z => return castTime lhs (some z)\n"
            "    | none => return castTime lhs (some currentZone)\n"
            "  return castTime lhs none"),
        "rationale": "structurally different CORRECT reshape: an early-return "
                     "guard-clause form that selects and wraps the same zone on "
                     "every branch, so `result = castX lhs (conversionZoneName "
                     "...)` holds on every input — must verify, else "
                     "SPEC-TOO-STRONG. The frozen `cases ... <;> rfl` still closes "
                     "it (the impl is definitionally the same). Defends both "
                     "obligations.",
    },
    {
        "id": "pos-extensional-zone",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. Both positives above are DEFINITIONALLY equal to the
        # frozen impl: `pos-early-return` is closed by the frozen `rfl` script and
        # `pos-echo-deep-model` by a bare `rfl`. So neither exercises the spec as a
        # PROPOSITION — each only re-checks that `rfl` still reduces. This positive
        # computes the selected zone through `Option.map`, which is EXTENSIONALLY
        # the deep model but NOT definitionally equal to it: measured, the frozen
        # `cases ... <;> rfl` FAILS on it ("Tactic `rfl` failed: ... (Option.map
        # (fun s => s ++ "") (some val)).getD currentZone is not definitionally
        # equal to (some val).getD currentZone"), and it closes only once the
        # tactic is retuned to `simp`. That makes it the one positive here whose
        # verification is a statement about the spec's CONTENT rather than about
        # the frozen impl's syntactic form. Verified with a real build (exit 0).
        "module": _swap(_swap(
            _with_impls(
                "  let z : Option String :=\n"
                "    if useTz then"
                " some ((requestedZone.map (fun s => s ++ \"\")).getD currentZone)\n"
                "    else none\n"
                "  return castDate lhs z",
                "  let z : Option String :=\n"
                "    if useTz then"
                " some ((requestedZone.map (fun s => s ++ \"\")).getD currentZone)\n"
                "    else none\n"
                "  return castTime lhs z"),
            _PROOF_DATE,
            "  intro lhs useTz requestedZone currentZone\n"
            "  unfold problem_spec_truncDateCast implementation_truncDateCast"
            " conversionZoneName\n"
            "  cases useTz <;> cases requestedZone <;> simp"),
            _PROOF_TIME,
            "  intro lhs useTz requestedZone currentZone\n"
            "  unfold problem_spec_truncTimeCast implementation_truncTimeCast"
            " conversionZoneName\n"
            "  cases useTz <;> cases requestedZone <;> simp"),
        "rationale": "structurally different CORRECT reshape that is NOT "
                     "definitionally equal to the frozen impl: the zone is built "
                     "with `Option.map` so `(requestedZone.map (·++\"\")).getD "
                     "currentZone` only EXTENSIONALLY equals `requestedZone.getD "
                     "currentZone`. The frozen `rfl` script provably does not "
                     "close it (measured), so it must be re-proven by `simp` — "
                     "which is what makes it a real SPEC-TOO-STRONG probe rather "
                     "than a re-check that `rfl` reduces. Defends both "
                     "obligations; statements byte-identical, no new axiom/lemma.",
    },

    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        # SECOND-AUDIT ADDITION. The prior port recorded the nagini sibling's
        # `admiss-f2p-shaped` as VACUOUS because `correct_trunc*Cast` carries no
        # precondition hypothesis. That reason is wrong: on a total carrier the
        # analogue is the obligation being UNSATISFIABLE at an F2P-shaped input,
        # which a positive that discharges it at that concrete input tests
        # directly. Dropping the lane silently removed the only direction of this
        # gate that detects PRECOND-TOO-STRONG. Measured: exit 0, and the
        # negative control (`_adm_sel` claiming the ambient zone wins) FAILS with
        # `⊢ False`, so the ground instance is load-bearing.
        "module": _admiss(
            _admiss_body("Date", "castDate", _PROOF_DATE),
            _admiss_body("Time", "castTime", _PROOF_TIME)),
        "rationale": "ADMISSIBILITY / PRECOND-TOO-STRONG. The obligation is "
                     "discharged at a concrete F2P-shaped input — conversion ON "
                     "with a caller-supplied zone `Z1` distinct from the ambient "
                     "`Z0` — by EVALUATION: `_adm_sel` computes "
                     "`conversionZoneName true (some \"Z1\") \"Z0\" = some \"Z1\"` "
                     "(the selection is deeply modeled over Bool/Option/String, so "
                     "it reduces despite the opaque casts), and `_adm_ground` then "
                     "builds the postcondition at that input; the frozen "
                     "obligation is closed verbatim afterwards. If the modeled "
                     "behavior were unsatisfiable at the normal input this would "
                     "FAIL — the total-carrier analogue of a precondition that "
                     "admits nothing. Nothing is assumed: statements are "
                     "byte-identical, the ground instances are `have`s inside the "
                     "existing tactic bodies, and no new declaration/axiom/`sorry` "
                     "appears. Defends both obligations.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete carrier-conditioned input and the refinement argument for why its
    # faithful real counterpart would NOT resolve the failing F2P test. Two
    # rivals per obligation; across each obligation's witnesses every input
    # binder is varied.
    # =====================================================================
    {
        "id": "date-ignore-requested-zone",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: when conversion is on, use the ambient zone
        # unconditionally and DISCARD the caller-supplied zone.
        "module": _reject_date(
            "  let mut tzname : Option String := none\n"
            "  if useTz then\n"
            "    tzname := some currentZone\n"
            "  return castDate lhs tzname"),
        "refinement": "this is the literal pre-patch behaviour: with conversion "
                      "on it uses the ambient zone and silently drops any "
                      "caller-supplied zone. The faithful real patch is exactly "
                      "the reported bug — aggregating a date in a non-ambient zone "
                      "computes in the wrong zone — so the F2P test asserting a "
                      "supplied zone is honoured FAILS. It does NOT resolve.",
        "rationale": "REJECT from `result = castDate lhs (conversionZoneName ...)`: "
                     "on useTz=true with a supplied zone the deep model selects "
                     "that zone but the rival passes the ambient one. Refuted at "
                     "(useTz=true, requestedZone=some, currentZone distinct): "
                     "conditioning only on `castDate x (some B) ≠ castDate x "
                     "(some A)`, the rival's result differs from the spec's. "
                     "Discrimination comes from requestedZone vs currentZone.",
        "witness": _witness(
            "Date", '"x" true (some "A") "B"',
            '(h : castDate "x" (some "B") ≠ castDate "x" (some "A"))'),
    },
    {
        "id": "date-zone-when-off",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong on the useTz=false sub-domain: applies the ambient zone even when
        # conversion is off (no zone should be used at all).
        "module": _reject_date(
            "  return castDate lhs (some currentZone)"),
        "refinement": "its faithful real patch applies a conversion zone even "
                      "when timezone support is off, so the cast converts when it "
                      "must not. Naive-datetime PASS_TO_PASS cases (conversion "
                      "off) would emit zone-converted SQL and break; it does NOT "
                      "resolve.",
        "rationale": "REJECT from `result = castDate lhs (conversionZoneName ...)`: "
                     "when useTz=false the deep model selects `none` but the rival "
                     "passes `some currentZone`. Refuted at (useTz=false, "
                     "requestedZone=none, currentZone=C): conditioning only on "
                     "`castDate y (some C) ≠ castDate y none`, the rival differs "
                     "from the spec. Pins the useTz=false sub-domain; varies "
                     "useTz and requestedZone against the sibling date rival.",
        "witness": _witness(
            "Date", '"y" false none "C"',
            '(h : castDate "y" (some "C") ≠ castDate "y" none)'),
    },
    {
        "id": "time-branch-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Branch swap on the useTz=true sub-domains: a supplied zone yields the
        # ambient name and an absent one yields no zone — both discriminating arms
        # diverge from the deep model.
        "module": _reject_time(
            "  let mut tzname : Option String := none\n"
            "  if useTz then\n"
            "    match requestedZone with\n"
            "    | none => tzname := none\n"
            "    | some z => tzname := some currentZone\n"
            "  return castTime lhs tzname"),
        "refinement": "its faithful real patch swaps the supplied/ambient arms: a "
                      "supplied zone yields the ambient name and the ambient case "
                      "yields no zone. The F2P supplied-zone assertion fails (the "
                      "supplied zone is discarded), so it does NOT resolve.",
        "rationale": "REJECT from `result = castTime lhs (conversionZoneName ...)`: "
                     "on useTz=true with no supplied zone the deep model selects "
                     "the ambient `currentZone` but the rival selects `none`. "
                     "Refuted at (useTz=true, requestedZone=none, currentZone=D): "
                     "conditioning only on `castTime z none ≠ castTime z (some "
                     "D)`, the rival differs from the spec. Discrimination comes "
                     "from the useTz=true/requestedZone=none arm.",
        "witness": _witness(
            "Time", '"z" true none "D"',
            '(h : castTime "z" none ≠ castTime "z" (some "D"))'),
    },
    {
        "id": "time-drop-inner-fragment",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame attack (directive 5): selects the RIGHT zone but hands the cast a
        # constant empty fragment instead of the compiled inner `lhs`. The spec
        # pins the cast's first argument to `lhs`; this rival breaks that pin.
        "module": _reject_time(
            "  let mut tzname : Option String := none\n"
            "  if useTz then\n"
            "    match requestedZone with\n"
            "    | none => tzname := some currentZone\n"
            "    | some z => tzname := some z\n"
            "  return castTime \"\" tzname"),
        "refinement": "its faithful real patch passes an empty inner SQL fragment "
                      "to the cast instead of the compiled expression, producing "
                      "malformed cast SQL for every query. The passthrough "
                      "PASS_TO_PASS cases (which read back the wrapped "
                      "expression) would break; it does NOT resolve.",
        "rationale": "REJECT from the FRAME part of `result = castTime lhs "
                     "(conversionZoneName ...)`: the cast must be applied to `lhs` "
                     "itself, but the rival applies it to a constant `\"\"`. "
                     "Refuted at lhs=q (useTz=false so the zone matches gold): "
                     "conditioning only on `castTime \"\" none ≠ castTime q none`, "
                     "the rival differs from the spec. This is the directive-5 "
                     "frame clause, the referentially-transparent analogue of the "
                     "nagini read-only-input obligation; it varies lhs (the only "
                     "witness that does) plus useTz and requestedZone against the "
                     "sibling time rival.",
        "witness": _witness(
            "Time", '"q" false (some "A") "K"',
            '(h : castTime "" none ≠ castTime "q" none)'),
    },

    # =====================================================================
    # AUDIT ADDITIONS — attribution gaps the four rivals above leave open.
    # Each rival's rejection was already the DEFAULT outcome of reshaping an
    # impl; what was missing is a witness STATED at the arm in question, which
    # is the only thing that attributes a rejection to a clause. Each of the
    # three below was rebuilt by hand: witness ELABORATES on its rival (exit 0),
    # FAILS on the frozen solution (exit 1, and the failure is the SEMANTIC
    # `h ... but is expected to have type False` — gold satisfies the spec
    # there), and its lone hypothesis leaves `False` underivable (probe exit 1).
    # =====================================================================
    {
        "id": "time-ignore-requested-zone",
        "kind": "uniqueness",
        "expect": "reject",
        # The F2P discriminator on the TIME obligation. The four original rivals
        # witness the truncTimeCast obligation only at (useTz=true,
        # requestedZone=none) and at (useTz=false, ...) — so the arm the fix is
        # actually ABOUT, a supplied zone winning over the ambient one, was
        # attributed on the date obligation and NOT on the time one, even though
        # the bundle models the two sites as independently observable behaviors
        # (one prepatch file each). This rival is the pre-patch behavior at the
        # time site, refuted at the supplied-zone arm.
        "module": _reject_time(
            "  let mut tzname : Option String := none\n"
            "  if useTz then\n"
            "    tzname := some currentZone\n"
            "  return castTime lhs tzname"),
        "refinement": "this is the pre-patch behaviour at the time-cast site: "
                      "with conversion on it uses the ambient zone and drops any "
                      "caller-supplied zone. The faithful real patch leaves the "
                      "reported defect in place for time casts — a time value "
                      "aggregated in a non-ambient zone is computed in the wrong "
                      "zone — so the F2P assertion that a supplied zone is "
                      "honoured FAILS. It does NOT resolve.",
        "rationale": "REJECT from `result = castTime lhs (conversionZoneName ...)`: "
                     "on useTz=true with a supplied zone the deep model selects "
                     "that zone but the rival passes the ambient one. Refuted at "
                     "(useTz=true, requestedZone=some P, currentZone=Q): "
                     "conditioning only on `castTime m (some Q) ≠ castTime m "
                     "(some P)`, the rival's result differs from the spec's. "
                     "Attributes the supplied-over-ambient precedence on the TIME "
                     "obligation, which no other witness here states.",
        "witness": _witness(
            "Time", '"m" true (some "P") "Q"',
            '(h : castTime "m" (some "Q") ≠ castTime "m" (some "P"))'),
    },
    {
        "id": "date-ambient-fallback-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong on the (useTz=true, requestedZone=none) arm of the DATE
        # obligation: uses no zone at all instead of falling back to the ambient
        # default. Neither date witness above is stated on this arm, so the
        # ambient-fallback half of the selection was unattributed for truncDate.
        "module": _reject_date(
            "  if useTz then\n"
            "    return castDate lhs requestedZone\n"
            "  return castDate lhs none"),
        "refinement": "its faithful real patch uses no conversion zone whenever "
                      "the caller supplied none, instead of the ambient default. "
                      "Timezone-aware PASS_TO_PASS cases that supply no explicit "
                      "zone (the common path) would stop converting to the "
                      "ambient zone and emit unconverted SQL; it does NOT "
                      "resolve.",
        "rationale": "REJECT from `result = castDate lhs (conversionZoneName ...)`: "
                     "on useTz=true with no supplied zone the deep model selects "
                     "the ambient `currentZone`, but the rival passes `none`. "
                     "Refuted at (useTz=true, requestedZone=none, currentZone=E): "
                     "conditioning only on `castDate p none ≠ castDate p (some "
                     "E)`, the rival differs from the spec. Attributes the "
                     "ambient-FALLBACK arm of the selection on the date "
                     "obligation, the arm the two sibling date witnesses skip.",
        "witness": _witness(
            "Date", '"p" true none "E"',
            '(h : castDate "p" none ≠ castDate "p" (some "E"))'),
    },
    {
        "id": "date-frame-swapped-fragment",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame attack (directive 5) on the DATE obligation. `time-drop-inner-
        # fragment` pins the cast's first argument only for truncTimeCast; the
        # date obligation had no frame rival at all. This one is additionally
        # sharper than a constant: it hands the cast another IN-SCOPE input
        # (`currentZone`), so it cannot be dismissed as an obviously malformed
        # constant and the refutation genuinely needs `lhs ≠ currentZone`.
        "module": _reject_date(
            "  let mut tzname : Option String := none\n"
            "  if useTz then\n"
            "    match requestedZone with\n"
            "    | none => tzname := some currentZone\n"
            "    | some z => tzname := some z\n"
            "  return castDate currentZone tzname"),
        "refinement": "its faithful real patch casts the zone NAME instead of the "
                      "compiled inner expression, so every date cast wraps the "
                      "wrong operand and the emitted SQL no longer references the "
                      "queried column. Every date PASS_TO_PASS case would break; "
                      "it does NOT resolve.",
        "rationale": "REJECT from the FRAME part of `result = castDate lhs "
                     "(conversionZoneName ...)`: the cast must be applied to `lhs` "
                     "itself, but this rival applies it to `currentZone`. Refuted "
                     "at (lhs=g, useTz=true, requestedZone=some S, "
                     "currentZone=T): conditioning only on `castDate T (some S) ≠ "
                     "castDate g (some S)` — the zone argument is IDENTICAL on "
                     "both sides, so the refutation isolates the framed fragment "
                     "alone. Gives the date obligation the directive-5 frame "
                     "clause that only the time obligation had, and varies lhs "
                     "against every other date witness.",
        "witness": _witness(
            "Date", '"g" true (some "S") "T"',
            '(h : castDate "T" (some "S") ≠ castDate "g" (some "S"))'),
    },
    {
        "id": "time-zone-when-off",
        "kind": "uniqueness",
        "expect": "reject",
        # THIRD-AUDIT ADDITION, closing a FALSE ATTRIBUTION rather than a mere
        # gap. The accounting block's arm table credited `time-branch-swap` with
        # the (useTz=false) arm of the time obligation. It does not hold that
        # arm: that rival only swaps the two useTz=true branches, so on the whole
        # useTz=false arm it is OBSERVABLY IDENTICAL to the frozen impl. Measured
        # directly, not argued — this elaborated against that rival at exit 0:
        #     example : ∀ (lhs : String) (rz : Option String) (cz : String),
        #         implementation_truncTimeCast lhs false rz cz
        #           = castTime lhs (conversionZoneName false rz cz) := by
        #       intro lhs rz cz
        #       unfold implementation_truncTimeCast conversionZoneName
        #       cases rz <;> rfl
        # and its witness is stated at useTz=TRUE, so nothing attributed the
        # OFF arm on the time obligation at all. This rival is wrong on exactly
        # that arm (it applies the ambient zone when no conversion should occur),
        # mirroring `date-zone-when-off` on the other modeled function.
        "module": _reject_time(
            "  return castTime lhs (some currentZone)"),
        "refinement": "its faithful real patch applies a conversion zone even "
                      "when timezone support is off, so the time cast converts "
                      "when it must not. Naive-datetime PASS_TO_PASS cases "
                      "(conversion off) would emit zone-converted SQL and break; "
                      "it does NOT resolve.",
        "rationale": "REJECT from `result = castTime lhs (conversionZoneName ...)`: "
                     "when useTz=false the deep model selects `none` but the rival "
                     "passes `some currentZone`. Refuted at (useTz=false, "
                     "requestedZone=none, currentZone=F): conditioning only on "
                     "`castTime r (some F) ≠ castTime r none`, the rival differs "
                     "from the spec. Attributes the (useTz=false) no-zone arm on "
                     "the TIME obligation, which the arm table previously credited "
                     "to `time-branch-swap` — a rival provably indistinguishable "
                     "from gold across that entire arm.",
        "witness": _witness(
            "Time", '"r" false none "F"',
            '(h : castTime "r" (some "F") ≠ castTime "r" none)'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 3 partial-domain rivals)
# plus a 2-case AXIOM lane. This bundle models the SAME two functions the sibling
# does (date + time cast), each with the single load-bearing clause
# `result = castX lhs (conversionZoneName ...)`; there is no separate precondition
# and no heap.
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-control-early-return         -> pos-early-return           PORTED
#   pos-control-echo-grounded-oracle -> pos-echo-deep-model        PORTED
#   admiss-f2p-shaped                -> admiss-f2p-shaped          PORTED (audit 2)
#   frame-mut-current_name           -> time-drop-inner-fragment   RE-EXPRESSED
#   frame-mut-tzinfo                 -> date-frame-swapped-fragment RE-EXPRESSED
#   partial-domain-ignore-tzinfo     -> date-ignore-requested-zone PORTED
#                                     + time-ignore-requested-zone (both sites)
#   partial-domain-off-wrong         -> date-zone-when-off         PORTED
#                                     + time-zone-when-off (audit 3; both sites)
#   partial-domain-branch-swap       -> time-branch-swap           PORTED
#   (no sibling case)                -> date-ambient-fallback-dropped  AUDIT ADD
#   (no sibling case)                -> pos-extensional-zone           AUDIT ADD
#   AXIOM_TESTS (2)                  -> (none)                     DROPPED (G-AX)
#
# AUDIT REVISIONS (independent re-derivation of the port's claims; the four
#   original rivals and two original positives all behave as declared, and no
#   new wrong impl was found that the frozen spec ADMITS, so there is no spec
#   hole here — what the audit found was UNDER-ATTRIBUTION, which a recorded
#   SOUND cannot see):
#   * The two original positives are both DEFINITIONALLY equal to the frozen
#     impl (one is closed by the frozen `rfl` script, the other by a bare
#     `rfl`), so neither tested the spec as a proposition. `pos-extensional-zone`
#     was added: an `Option.map`-built zone that is only EXTENSIONALLY the deep
#     model, on which the frozen `rfl` provably FAILS (measured) and which
#     closes only under `simp`.
#   * The F2P discriminator — a supplied zone winning over the ambient one — was
#     witnessed on the DATE obligation only. Since the bundle treats the two
#     sites as independently observable (one prepatch file each),
#     `time-ignore-requested-zone` was added to attribute it on the TIME
#     obligation too.
#   * No witness was stated on the (useTz=true, requestedZone=none) arm of the
#     date obligation, leaving the ambient-FALLBACK half of the selection
#     unattributed there: `date-ambient-fallback-dropped` closes it.
#   * The directive-5 frame clause was pinned only for truncTimeCast;
#     `date-frame-swapped-fragment` gives the date obligation its own frame
#     rival, and hands the cast an in-scope input rather than a constant so the
#     refutation isolates the framed fragment with the zone argument held equal.
#
# PORTED (positives): the sibling's early-return positive and its grounded-oracle
#   echo both port directly. `pos-early-return` is a guard-clause reshape the
#   FROZEN proof still closes; `pos-echo-deep-model` returns the deep model
#   applied to the cast and re-proves with `rfl`. Each defends both obligations.
#   Both, however, are DEFINITIONALLY equal to the frozen impl, so each is a
#   cheap control: it confirms the obligation still reduces, not that the spec
#   admits a genuinely differently-computed correct impl. `pos-extensional-zone`
#   (audit addition) is the positive that carries that weight here.
# PORTED (admissibility) — CORRECTED BY THE SECOND AUDIT. This was previously
#   recorded here as VACUOUS, on the reason that `correct_trunc*Cast` carries no
#   precondition hypothesis (the `∀` is unguarded, the behavior total). That
#   reason does not survive: on a total carrier the analogue of "the precondition
#   admits a normal input" is "the obligation is SATISFIABLE at an F2P-shaped
#   input", and a positive that discharges the obligation at that concrete input
#   — by evaluation, as a `have`, before closing the frozen obligation verbatim —
#   tests it directly. `admiss-f2p-shaped` now does exactly that at (useTz=true,
#   requestedZone=some "Z1", currentZone="Z0"), the shape where a supplied zone
#   must beat the ambient one. It is not the trivial reflexivity of the deep
#   model: the ground instance COMPUTES the selection, and the negative control
#   asserting the ambient zone wins there fails with `⊢ False` (measured). Without
#   this case the battery tested only SPEC-TOO-WEAK and SPEC-TOO-STRONG, dropping
#   one of the three directions this gate exists to cover.
# RE-EXPRESSED / VACUOUS (frame mutation): the sibling's TWO frame rivals WRITE
#   (`.append`) to inputs held at `Acc(.,1/2)`. Lean is referentially
#   transparent — every input is an immutable value, no `mut` alias, no heap — so
#   the write-to-a-read-only-input class is VACUOUS (porting map). What the frame
#   OBLIGATION becomes here is the directive-5 pinning of the cast's inner
#   fragment to `lhs`, and `time-drop-inner-fragment` attacks THAT directly (the
#   rival hands the cast a constant fragment). The two sibling rivals differed
#   only in WHICH read-only object they wrote, a distinction with no counterpart
#   on an aliasing-free carrier — but the OBLIGATION they stand for is
#   per-function here, and one frame rival attributes it for one function only,
#   so `date-frame-swapped-fragment` (audit addition) supplies the date one.
# PORTED (partial-domain rivals): ignore-tzinfo -> date-ignore-requested-zone
#   (the literal pre-patch bug); off-wrong -> date-zone-when-off (applies a zone
#   when conversion is off); branch-swap -> time-branch-swap. The sibling split
#   these across one modeled function; here they are spread over the two modeled
#   functions so both obligations are attacked.
#
# SECOND AUDIT (independent re-derivation; all 10 pre-existing cases behave as
#   declared and were re-measured with real builds, so nothing was removed):
#   * Attack B′ (the FORGERY test), which the first audit did NOT run, was run on
#     all 7 reject cases — required because their `gold_signature` is a type
#     mismatch rather than a plain evaluation, and "it looks semantic" is not
#     evidence. Both halves were built. FLIP: dropping the `¬` so the file asserts
#     gold IS correct at that input makes gold SUCCEED (exit 0) and the rival FAIL
#     (exit 1) — the exact inverse of the witness, so gold's exit code demonstrably
#     tracks the CLAIM and is not a constant. REVEAL: replacing `exact h` with a
#     deliberate type error prints the post-`simp` goal, which on gold is `False`
#     (simp PROVED the spec equation there) and on each rival is the concrete
#     disequation, e.g. `¬castDate "x" (some "B") = castDate "x" (some "A")`. That
#     pair is a genuine refutation on all 7; none is hollow.
#   * The `admissibility` lane was mis-recorded as vacuous; it is expressible here
#     and is now landed (see above). This was the one real defect found.
#   * Attack D (3 further wrong impls, each given the strengthened `first | rfl |
#     simp | simp_all | (simp only [Id.run]; rfl) | aesop` script so it got its
#     best chance) all REJECTED with semantic `unsolved goals` on the arm each
#     attacks: an OFF-arm `some ""`-vs-`none` collapse trap (`⊢ castDate lhs
#     (some "") = castDate lhs none`), a single-arm near miss at
#     (useTz=false, requestedZone=none), and a frame rival whose wrong fragment
#     still MENTIONS lhs (`currentZone ++ lhs`). No spec hole.
#   * Attack E (2 further correct reshapes, both non-defeq so the frozen `rfl`
#     cannot close them) both VERIFIED under `simp`: a list round-trip
#     (`(requestedZone.toList ++ [currentZone]).head!`) and an ambient-side
#     `currentZone ++ ""` — the latter probing the arm the shipped Option.map
#     positive leaves definitional. No soundness hole.
#
# THIRD AUDIT (independent; 38 + 14 + 8 + 3 real builds). All 11 pre-existing
#   cases behave as declared and nothing was removed. One defect found, and it
#   was in the PROSE rather than in a case:
#   * FALSE ATTRIBUTION in the arm table. It credited `time-branch-swap` with the
#     (useTz=false) no-zone arm of the time obligation. That rival is observably
#     IDENTICAL to gold across that entire arm (proved, exit 0) and its witness is
#     stated at useTz=true, so the OFF arm was unattributed for truncTimeCast
#     while the table claimed it. Fixed by landing `time-zone-when-off` (rival
#     exit 0 / gold exit 1 / probe exit 1 / forgery-flip inverts) and by
#     correcting the table. This is exactly the class a recorded SOUND cannot
#     see: every case behaved as declared, and the accounting still overstated
#     which clauses were demonstrated.
#   * Attack B′ re-run independently on all 7 pre-existing reject cases (14
#     builds). FLIP: gold 0 / rival 1, the inverse of the witness. REVEAL: gold's
#     post-`simp` goal is `⊢ False` (simp PROVED the spec equation there) and each
#     rival's is the concrete disequation. Confirms the first audit's finding on
#     evidence gathered afresh; no case is hollow.
#   * Attack C: each of the 8 rivals is observably distinct from gold on the arm
#     its witness names — the reveal probes show the rival goal is a disequation
#     between two DIFFERENT opaque applications, never a collapsed one. No
#     vacuous rival. (`time-branch-swap` is distinct on its credited ambient arm;
#     only its former OFF-arm credit was wrong.)
#   * Attack D (5 further wrong impls) all REJECTED: a cross-flavour cast swap
#     (date impl calling the time cast), an always-convert impl ignoring useTz, an
#     empty-supplied-zone fallback, a never-convert impl, and an OFF-arm `some ""`
#     collapse trap — the last confirming the carrier does NOT collapse `some ""`
#     into `none`. No spec hole.
#   * Attack E (4 further correct reshapes) all VERIFIED: `Option.orElse`, a match
#     on the (useTz, requestedZone) PAIR, an `isSome` guard, and `lhs ++ ""` (a
#     frame-side reshape that is correct but not defeq — it needs `simp`, and the
#     spec admits it). No soundness hole.
#   * The admissibility case was re-derived independently: shipped module exit 0,
#     and its negative control (`_adm_sel` claiming the ambient zone wins) fails
#     with `⊢ False` plus `castDate "c" (some "Z1") = castDate "c" (some "Z0")`,
#     so the ground instance genuinely pins supplied-over-ambient.
#
# FOURTH AUDIT (independent; 68 + 9 + 8 real builds). All 12 cases behave as
#   declared and nothing was removed. One defect found, again in the PROSE:
#   * STALE COUNTS in the accounting. Three claims still described the 3-rivals-
#     per-obligation battery that predated the third audit's `time-zone-when-off`:
#     the header's "three reject witnesses per obligation", the coverage block's
#     "three reject rivals each", and the truncTimeCast binder lists, which omitted
#     lhs=r and currentZone=F. Understatement rather than overstatement (the arm
#     table itself was already correct and complete), so it could not mint a false
#     SOUND — but a ledger that miscounts its own cases is exactly what an auditor
#     has to be able to trust, so all three were corrected.
#   * Attack A re-run mechanically over all 12 modules: every `theorem correct_*`
#     statement, both `problem_spec_*` defs, `conversionZoneName`, and both
#     `opaque` declarations are byte-identical to the frozen file in every case;
#     each variant's diff touches only impl and/or proof regions.
#   * Attack B/B′ re-run on all 8 reject cases (32 builds), rebuilding the gate's
#     own files via `pbt_witness.witness_file`: witness on rival exit 0, on gold
#     exit 1, consistency probe exit 1 for all 8. FLIP (drop the `¬`, so the file
#     claims gold IS correct at that input) inverts on all 8 — gold 0, rival 1 —
#     so gold's exit code demonstrably tracks the claim. REVEAL (`trace_state`
#     before the closing step) shows gold's post-`simp` goal is `⊢ False` (simp
#     PROVED the spec equation there) while each rival's is the concrete
#     disequation between two DIFFERENT opaque applications, e.g.
#     `⊢ ¬castDate "x" (some "B") = castDate "x" (some "A")`. No hollow case.
#   * Attack C: the reveal goals double as the vacuity check — every rival's goal
#     is a disequation between two distinct opaque applications, never a collapsed
#     one, so no rival is definitionally equal to gold at its witnessed input.
#   * Attack D (4 NEW wrong impls, each given a strengthened `first | rfl | simp |
#     simp_all | (simp only [Id.run]; rfl) | aesop | decide` script so it got its
#     best chance) all REJECTED with semantic `unsolved goals` naming the attacked
#     arm: an (useTz=false, requestedZone=some) "off but supplied" flag confusion
#     (`⊢ castDate lhs (some val) = castDate lhs none`), a frame near-miss wrong at
#     exactly one lhs value, a supplied-zone-name mangle (`some (val ++ "!")`), and
#     an empty-selected-zone-collapses-to-none trap. No spec hole.
#   * Attack E (4 NEW correct reshapes) all VERIFIED (exit 0): a `cond`-based
#     selection, a dependent-`if`/match shape, a factored impl-region HELPER def
#     (`auditPickZone`, a decomposition the frozen impl does not have), and an
#     `Option.orElse` with an ambient-side `"" ++ currentZone` round-trip. No
#     soundness hole.
#   * The three load-bearing PROSE claims were each machine-checked rather than
#     read. `pos-extensional-zone`'s claim that the frozen `rfl` script does not
#     close it: confirmed (exit 1, `Option.map ... is not definitionally equal`).
#     `pos-early-return`'s definitional equality: confirmed. The third audit's
#     arm-table correction: confirmed with gold controls — the OFF-arm identity
#     holds of `time-branch-swap` (exit 0) and of gold (exit 0), while the
#     ambient-arm identity holds of gold (exit 0) and FAILS of that rival (exit 1),
#     so it really is indistinguishable from gold across the whole OFF arm and
#     really is distinct on the arm it is credited with.
#   * The admissibility negative control was re-derived: `_adm_sel` claiming the
#     ambient zone wins fails with `⊢ False` at BOTH obligations, so the ground
#     instance genuinely pins supplied-over-ambient at the F2P-shaped input.
#
# BINDER / OBLIGATION coverage. Both obligations are DEFENDED (three soundness
#   positives plus the admissibility ground instance reshape/annotate both) and
#   ATTACKED (FOUR reject rivals each, one per clause-arm: the selection's three
#   arms plus the frame). Per obligation the witnesses vary EVERY input binder: for
#   truncDateCast lhs {x,y,p,g}, useTz {true,false}, requestedZone {some,none},
#   currentZone {B,C,E,T}; for truncTimeCast lhs {z,q,m,r}, useTz {true,false},
#   requestedZone {none,some}, currentZone {D,K,Q,F}. Each witness conditions on
#   ONE satisfiable hypothesis about the opaque cast (the only way to attack an
#   uncomputable opaque callee); each was built to ELABORATE on its rival, FAIL
#   on gold, and leave `False` underivable from its hypothesis.
#
#   The three ARMS of the selection, plus the frame, are now each attributed on
#   BOTH obligations — which is the property a rejection count cannot express:
#     (useTz=true, requestedZone=some z) -> z         date-ignore-requested-zone
#                                                     time-ignore-requested-zone
#     (useTz=true, requestedZone=none)   -> ambient   date-ambient-fallback-dropped
#                                                     time-branch-swap
#     (useTz=false, _)                   -> no zone   date-zone-when-off
#                                                     time-zone-when-off
#     frame: cast applied to `lhs` itself             date-frame-swapped-fragment
#                                                     time-drop-inner-fragment
#   The (useTz=false) time entry was CORRECTED by the third audit. It previously
#   read `time-branch-swap`, which was false: that rival swaps only the two
#   useTz=true branches, so across the whole useTz=false arm it is observably
#   IDENTICAL to the frozen impl (machine-checked at exit 0 — see the case
#   comment on `time-zone-when-off` for the exact snippet), and its witness is
#   stated at useTz=true. Nothing attributed the OFF arm for truncTimeCast, so
#   the table claimed a clause the manifest never demonstrated. `time-zone-when-
#   off` now supplies it. `time-branch-swap` is retained on its real merit: it
#   is genuinely wrong on, and witnessed at, the (useTz=true, requestedZone=none)
#   ambient-fallback arm, which is the only arm it is credited with above.
#   Note the binder-variation caveat the coverage reporter cannot check: in the
#   three (useTz=false) witnesses the `requestedZone` value is IRRELEVANT to the
#   spec's verdict (the selection short-circuits to `none`), so their varying it
#   is several spellings of one point, not a second discriminating input. The
#   meaningful requestedZone variation lives in the useTz=true witnesses above.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; `castDate`/`castTime` are
#   unchanged collaborators applied identically on both sides and consume no
#   behavioral axiom, so there is nothing to probe and the gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
