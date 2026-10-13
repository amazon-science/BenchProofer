"""properties.py — G-PBT falsification battery for django__django-11292 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region — the region the consumer spec view elides — is changed,
so ``markers.same_spec`` holds and every ``prove_correct <name>`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (two contracted methods, both pure over free inputs):

  registeredCommandOptions (requiresSystemChecks : Bool) (commonOptions : List String)
      return (out : List String)
    require skipChecksFlag ∉ commonOptions
    ensures requiresSystemChecks = true  → out = commonOptions ++ [skipChecksFlag]   -- R1
    ensures requiresSystemChecks = false → out = commonOptions                       -- R2
    ensures requiresSystemChecks = true  → skipChecksFlag ∈ out                      -- R3
    ensures requiresSystemChecks = false → skipChecksFlag ∉ out                      -- R4
    ensures ∀ s, s ∈ commonOptions → s ∈ out                                         -- R5

  shouldRunSystemChecks (requiresSystemChecks : Bool) (skipRequested : Bool)
      return (result : Bool)
    ensures result = (requiresSystemChecks && (! skipRequested))                     -- S1

registeredCommandOptions assembles the recognised option list: when the command
performs validation the opt-out option is appended to those it already
recognises, otherwise the list is unchanged. Its post pins BOTH the exact list
(R1/R2), the membership of the opt-out option keyed on the validation flag
(R3/R4), and the frame preservation of every already-recognised option (R5).
shouldRunSystemChecks decides whether the validation step runs: exactly when the
command performs validation AND the user did not ask to skip. S1 pins the output
for all four (requiresSystemChecks, skipRequested) combinations. Both methods are
pure boolean / list-frame logic over FREE inputs; there is no opaque answer-key
oracle in any load-bearing clause, so every clause is grounded in the inputs.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling has no heap
    parameters here (both nagini functions take pass-by-value bools); on this
    referentially-transparent carrier there is likewise no `mut` parameter, no
    aliasing, and no permission system to subvert. `commonOptions` is an
    immutable value; R5 pins the frame explicitly by post rather than by a
    read-only permission. No substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. Every clause is a boolean/list
    function of the method's own arguments (`commonOptions ++ [skipChecksFlag]`,
    `requiresSystemChecks && ! skipRequested`); there is no answer key to echo.
    The honest cheapest CORRECT reshapes are carried as POSITIVE controls.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. The nagini file's central
    leverage is a rival correct on 3 of the 4 (rv, rs) combinations but diverging
    on ONE — most importantly the discriminating combination (rv=T, rs=T) the
    whole gold change exists to fix. Each such rival is ported: it corresponds to
    a faithful real patch that would NOT resolve the F2P (`test_skip_checks`), and
    the spec MUST reject it.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. Every frozen impl region
    is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

WITNESS MECHANICS ON THIS BUNDLE. Both postconditions are DECIDABLE — every
clause is a boolean / decidable-equality fact over `List String` and `Bool`, no
opaque callee — so the tester+`decide` path is live (unlike the sibling
11276, whose round-trip constants mention an opaque `entityDecode`). Each reject
witness reaches the post-image through Velvet's own tester machinery
(`derive_tester_for <name>` → `<name>Tester args = false := by decide`, which
says the extracted program's result violates the method's postcondition at that
concrete input). Every argument is a concrete literal that `decide` reduces
(bools and short string lists), so no witness binds a hypothesis and no
consistency probe is needed. Checked in a file whose `prove_correct` blocks are
stripped, so no tactic script can mask the verdict. Each witness was checked
out-of-band with scripts/lean_verify.sh: every one ELABORATES against its rival
(exit 0) and FAILS against gold (a `decide` refutation error) — the frozen
solution satisfies the spec at every input, so `…Tester <input> = false` is
false of gold and `decide` refutes it there.

Independently re-derived by audit: all 8 reject witnesses rebuilt by hand,
rival exit 0 / gold exit 1 for every one, and every gold-side failure read as
the SEMANTIC form `Tactic 'decide' proved that the proposition <name>Tester
<input> = false is false` — not an unknown identifier, type error, unfolding
failure or timeout. So each rejection is attributable to a postcondition clause
at a named input rather than to the frozen tactic script's shape.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real stdlib callee (argparse store_true);
that is G-AX's job (axiom_check.py / mapping.md) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11292"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors: the WHOLE frozen impl body of each method, i.e.
# ---- everything strictly BETWEEN that method's `-- impl-start` / `-- impl-end`.
# ---- Every variant replaces exactly one of these, so each edit lies wholly
# ---- inside one impl region and same_spec holds by construction (asserted by
# ---- _swap: substring present AND unique in the file).
_REG_IMPL = (
    "    let out : List String :=\n"
    "      if requiresSystemChecks then\n"
    "        commonOptions ++ [skipChecksFlag]\n"
    "      else\n"
    "        commonOptions\n"
    "    return out"
)

_SRC_IMPL = (
    "    let result : Bool := requiresSystemChecks && (! skipRequested)\n"
    "    return result"
)

assert _BASE.count(_REG_IMPL) == 1, "registeredCommandOptions impl region drifted"
assert _BASE.count(_SRC_IMPL) == 1, "shouldRunSystemChecks impl region drifted"


def _reg(new_body):
    """Full Solution.lean variant with ONLY registeredCommandOptions' impl body
    replaced. The frozen `prove_correct registeredCommandOptions by loom_solve`
    is left as-is: a correct reshape still closes under it; a wrong rival's
    obligation fails to elaborate (that is the rejection), and the witness — not
    the tactic breakage — attributes that rejection to the spec."""
    return _swap(_BASE, _REG_IMPL, new_body)


def _src(new_body):
    """Full Solution.lean variant with ONLY shouldRunSystemChecks' impl body
    replaced (proof left frozen; same discipline as _reg)."""
    return _swap(_BASE, _SRC_IMPL, new_body)


# ---- witness builders. Both postconditions are decidable, so the tester path is
# ---- live: `<name>Tester <args> = false` says the extracted program violates
# ---- the method's postcondition at that concrete input. registeredCommandOptions
# ---- carries a `require`, so its tester needs the precondition-decidability
# ---- directive too; shouldRunSystemChecks has no `require` and omits it.
def _wit_reg(args):
    return (
        "extract_program_for registeredCommandOptions\n"
        "prove_precondition_decidable_for registeredCommandOptions\n"
        "prove_postcondition_decidable_for registeredCommandOptions\n"
        "derive_tester_for registeredCommandOptions\n\n"
        f"example : registeredCommandOptionsTester {args} = false := by\n"
        "  decide\n"
    )


def _wit_src(args):
    return (
        "extract_program_for shouldRunSystemChecks\n"
        "prove_postcondition_decidable_for shouldRunSystemChecks\n"
        "derive_tester_for shouldRunSystemChecks\n\n"
        f"example : shouldRunSystemChecksTester {args} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Every reshape returns a value definitionally equal to the
    # gold one, so each closes under the frozen `loom_solve` (no reproof needed).
    # =====================================================================
    {
        "id": "pos-reg-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape registeredCommandOptions: stage the conditionally-added option
        # into a local list `extra` and append it uniformly, instead of branching
        # the whole result. Same value for every input (`extra` is `[flag]` iff
        # the command validates, else `[]`), different control shape.
        "module": _reg(
            "    let extra : List String := if requiresSystemChecks then [skipChecksFlag] else []\n"
            "    let out : List String := commonOptions ++ extra\n"
            "    return out"),
        "rationale": (
            "a correct impl of registeredCommandOptions with a DIFFERENT control "
            "shape (append a staged `extra` list uniformly rather than branching "
            "the whole result) must verify; the value flow is unchanged so R1–R5 "
            "still discharge and the frozen proof closes as-is. Ports the nagini "
            "pos-pos-bool-collapse (a structurally-different but correct impl of "
            "the flag-offer function). If it fails => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-src-demorgan",
        "kind": "soundness",
        "expect": "verify",
        # Reshape shouldRunSystemChecks via De Morgan: run iff NOT (skip OR no
        # validation). Same truth table as `rv && ! rs`, different boolean form.
        "module": _src(
            "    let result : Bool := ! ((! requiresSystemChecks) || skipRequested)\n"
            "    return result"),
        "rationale": (
            "a correct De Morgan re-expression of the gate (`! ((! rv) || rs)` == "
            "`rv && ! rs`) must verify against S1; the truth table over all four "
            "(rv, rs) combinations is identical, so it closes under the frozen "
            "proof. Ports nagini pos-wrv-direct-boolean. If it fails => "
            "SPEC-TOO-STRONG (over-fit to the `&&` code form)."),
    },
    {
        "id": "pos-src-branch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape shouldRunSystemChecks into explicit per-combination branching
        # that yields the identical truth table (no `&&`/`!` at all).
        "module": _src(
            "    if requiresSystemChecks then\n"
            "      if skipRequested then\n"
            "        return false\n"
            "      else\n"
            "        return true\n"
            "    else\n"
            "      return false"),
        "rationale": (
            "branch-reordered, per-combination decision equal to the gold truth "
            "table (validation runs iff the command validates and the user did "
            "not skip); a correct re-expression must verify. Ports nagini "
            "pos-wrv-demorgan-nested. If it fails => SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # ADMISSIBILITY — a PORT of nagini admiss-self-call-fshaped, which asserted
    # (by an in-body `Assert` over a self-call) that the F2P-shaped input is
    # in-domain. The velvet counterpart is a CROSS-METHOD call: the body of
    # shouldRunSystemChecks invokes registeredCommandOptions at an F2P-shaped
    # input (a validating command whose already-recognised options do not include
    # the opt-out option), which makes the callee's `require` a REAL proof
    # obligation on the caller — the `let ... ← ...` raises
    # `require_1 : skipChecksFlag ∉ commonOptions` instantiated at the concrete
    # frame. If the precondition were too strong to admit an ordinary
    # command-option frame the call would not discharge => PRECOND-TOO-STRONG.
    #
    # AUDIT NOTE (why this is not the frozen module). An earlier revision of this
    # case shipped `module=_BASE` — byte-identical to the frozen solution — on the
    # argument that the empty-precondition probe "has no non-degenerate
    # counterpart on this referentially-transparent carrier". That claim was
    # measured FALSE and the case was vacuous: it re-ran exactly the G-VERIFY
    # fact and could not have failed for any reason touching the precondition.
    # The cross-call below is the non-degenerate counterpart, and it is load-
    # bearing: with the FROZEN proof script left untouched it FAILS (exit 1,
    # `unsolved goals / case require_1: skipChecksFlag ∉ commonOptions`), i.e. the
    # call genuinely raises the precondition obligation rather than smuggling it
    # past the solver; discharging it needs the extra `simp [skipChecksFlag]`
    # step, which is a legitimate REPROOF (variant_scope permits a variant to
    # reprove; only the obligation's statement is frozen).
    # =====================================================================
    {
        "id": "admiss-cross-call-fshaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _SRC_IMPL,
                  "    let _admitted ← registeredCommandOptions true [\"--opt-a\", \"--opt-b\"]\n"
                  "    let result : Bool := requiresSystemChecks && (! skipRequested)\n"
                  "    return result"),
            "prove_correct shouldRunSystemChecks by\n  loom_solve",
            "prove_correct shouldRunSystemChecks by\n  loom_solve <;> simp [skipChecksFlag]"),
        "rationale": (
            "the option-assembly method's `require` (the opt-out option is not "
            "already among those recognised) must ADMIT an ordinary "
            "command-option frame for a validating command — the F2P-shaped "
            "input. Calling it from the gate method's body turns that "
            "precondition into a real obligation on the caller at a concrete "
            "frame; it discharges, so the precondition is not too strong and the "
            "joint post-image (R1–R5 with S1) is satisfiable at an in-domain "
            "point. Ports nagini admiss-self-call-fshaped (its in-body assertion "
            "over a self-call at the F2P-shaped input). If it fails => "
            "PRECOND-TOO-STRONG."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real patch
    # would NOT resolve the F2P. The (requiresSystemChecks, skipRequested) binders
    # of S1 and the (requiresSystemChecks, commonOptions) binders of R1–R5 are
    # varied across the witnesses (rv ∈ {T,F}, rs ∈ {T,F}, commonOptions ∈
    # {empty, non-empty}).
    # =====================================================================
    {
        "id": "rival-src-drop-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack: the pre-fix gate that IGNORES the skip request and
        # runs validation whenever it is required (correct on 3/4 combos, wrong at
        # rv=T, rs=T — the discriminating combination the whole fix exists for).
        "module": _src("    let result : Bool := requiresSystemChecks\n    return result"),
        "refinement": (
            "this is the pre-fix decision: validation runs whenever the command "
            "performs it, disregarding the skip request. Its faithful real patch "
            "runs the validation step for a validating command even when the user "
            "asked to skip it, so the failing test (a validating command with a "
            "broken configuration invoked WITH the skip request, expecting a clean "
            "run) STILL ERRORS => F2P NOT resolved. This is the exact defect the "
            "fix corrects."),
        "rationale": (
            "REJECT from S1 (`result = rv && ! rs`): at (rv=T, rs=T) gold demands "
            "False (skip honoured) but the rival returns True. Refuted at input "
            "`true true`. Ports nagini weak-wrv-drop-skip-discriminating. If it "
            "verified => SPEC-TOO-WEAK (admits the bug)."),
        "witness": _wit_src("true true"),
    },
    {
        "id": "rival-src-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Inverted-polarity gate: run validation precisely when the skip WAS
        # requested for a validating command — the opposite of the fix. Correct at
        # (F,*); wrong at (T,F) [gold True, rival False] and (T,T) [gold False,
        # rival True].
        "module": _src("    let result : Bool := requiresSystemChecks && skipRequested\n    return result"),
        "refinement": (
            "wires the gate with inverted polarity (run the validation step only "
            "when the user asked to skip). A faithful real patch of this shape "
            "would (a) NOT run validation for a normal validating command — "
            "breaking the default-validation PASS_TO_PASS behaviour — and (b) run "
            "it exactly when the user asked to skip, so the failing test STILL "
            "ERRORS on the broken configuration. F2P NOT resolved."),
        "rationale": (
            "REJECT from S1: at (rv=T, rs=F) gold demands True (validate a normal "
            "command) but the rival returns False. Refuted at input `true false` "
            "— a DISTINCT point from rival-src-drop-skip (which is CORRECT at "
            "(T,F) and only wrong at (T,T)), so the battery varies `skipRequested`. "
            "Ports nagini weak-wrv-inverted-skip-polarity. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _wit_src("true false"),
    },
    {
        "id": "rival-src-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Never run validation for any command (correct at (F,*) and (T,T); wrong
        # at (T,F) — a validating command with no skip request).
        "module": _src("    let result : Bool := false\n    return result"),
        "refinement": (
            "never runs the validation step for any command. A faithful real "
            "patch that disables validation unconditionally lets a validating "
            "command run with a broken configuration WITHOUT any skip request — "
            "breaking the PASS_TO_PASS expectation that validation runs by default "
            "and admitting silently invalid configs. It happens to honour the skip "
            "case, but fails the no-skip case."),
        "rationale": (
            "REJECT from S1: at (rv=T, rs=F) gold demands True but the constant "
            "rival returns False. Refuted at input `true false`. Ports nagini "
            "weak-wrv-flip-no-skip-combo (a rival that skips validation even when "
            "no skip was requested). Distinct rival from rival-src-inverted (a "
            "constant, not a polarity flip); both expose the (T,F) clause but by "
            "different impls. If it verified => SPEC-TOO-WEAK."),
        "witness": _wit_src("true false"),
    },
    {
        "id": "rival-src-ignore-rv",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the validation flag entirely: run validation iff the user did NOT
        # request a skip. Correct at (T,F), (T,T), (F,T); wrong at (F,F) — a
        # non-validating command with no skip request, where gold does not run
        # validation but this rival does. Varies requiresSystemChecks to false.
        "module": _src("    let result : Bool := ! skipRequested\n    return result"),
        "refinement": (
            "disregards whether the command performs validation and keys the "
            "decision solely on the skip request. A faithful real patch of this "
            "shape would run the validation step for a NON-validating command "
            "whenever no skip was requested — invoking validation on commands "
            "that must not run it, breaking the PASS_TO_PASS behaviour of "
            "non-validating commands. F2P NOT resolved."),
        "rationale": (
            "REJECT from S1 (`result = rv && ! rs`): at (rv=F, rs=F) gold demands "
            "False (a non-validating command never validates) but the rival "
            "returns True. Refuted at input `false false` — the ONLY reject "
            "witness with requiresSystemChecks=false, so that binder is varied "
            "across the shouldRunSystemChecks reject surface. No direct nagini "
            "sibling (nagini's will_run_validation rivals all held rv=T); ADDED to "
            "vary the validation-flag binder. If it verified => SPEC-TOO-WEAK."),
        "witness": _wit_src("false false"),
    },
    {
        "id": "rival-reg-never-add",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix option assembly: NEVER offer the opt-out option (correct at
        # requiresSystemChecks=false, wrong at true). This is the literal pre-fix
        # behaviour — no registration of the flag.
        "module": _reg("    let out : List String := commonOptions\n    return out"),
        "refinement": (
            "this is the pre-fix assembly with NO opt-out option registered. The "
            "option is never offered, so a supplied skip request is dropped for a "
            "validating command and the downstream gate runs validation "
            "regardless => the failing test errors on the broken configuration. "
            "F2P NOT resolved (this is the exact pre-fix state)."),
        "rationale": (
            "REJECT from R1/R3 (`rv=true → out = commonOptions ++ [flag]` and "
            "`rv=true → flag ∈ out`): at requiresSystemChecks=true the rival omits "
            "the opt-out option. Refuted at input `true []`. Ports nagini "
            "weak-pos-constant-false. If it verified => SPEC-TOO-WEAK."),
        "witness": _wit_reg("true []"),
    },
    {
        "id": "rival-reg-always-add",
        "kind": "uniqueness",
        "expect": "reject",
        # Offer the opt-out option for EVERY command (correct at
        # requiresSystemChecks=true, wrong at false).
        "module": _reg("    let out : List String := commonOptions ++ [skipChecksFlag]\n    return out"),
        "refinement": (
            "registers the opt-out option UNCONDITIONALLY, exposing it even for "
            "non-validating commands. A real patch of this shape would accept the "
            "skip request where the gold parser rejects it, changing the accepted-"
            "argument set (and help/usage) for non-validating commands and "
            "breaking their PASS_TO_PASS argument tests; the gold guards the "
            "registration on the validation flag. Faithful patch does NOT resolve "
            "cleanly."),
        "rationale": (
            "REJECT from R2/R4 (`rv=false → out = commonOptions` and `rv=false → "
            "flag ∉ out`): at requiresSystemChecks=false the rival offers the "
            "opt-out option anyway. Refuted at input `false []` — varies "
            "`requiresSystemChecks` to false, a DISTINCT point from "
            "rival-reg-never-add. Ports nagini weak-pos-constant-true. If it "
            "verified => SPEC-TOO-WEAK."),
        "witness": _wit_reg("false []"),
    },
    {
        "id": "rival-reg-drop-common",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame violation: return ONLY the conditionally-added option, dropping
        # every already-recognised option. Correct on the opt-out membership
        # (R3/R4) but violates the frame (R5) and the exact list (R1/R2) whenever
        # commonOptions is non-empty.
        "module": _reg(
            "    let out : List String := if requiresSystemChecks then [skipChecksFlag] else []\n"
            "    return out"),
        "refinement": (
            "drops every already-recognised option, keeping only the "
            "conditionally-added opt-out option. A real patch that rebuilt the "
            "option set from scratch this way would stop recognising the "
            "framework and command-specific options the parser already accepted, "
            "breaking essentially every argument-parsing PASS_TO_PASS test. F2P "
            "NOT resolved."),
        "rationale": (
            "REJECT from R5 (`∀ s ∈ commonOptions → s ∈ out`) and R1 "
            "(`rv=true → out = commonOptions ++ [flag]`): with a non-empty "
            "commonOptions the rival drops its members. Refuted at input "
            "`true [\"--x\"]` — varies the `commonOptions` binder to non-empty, "
            "attacking the frame clause R5 that no other rival touches (the nagini "
            "sibling has no heap/frame parameter, so this is the referentially-"
            "transparent frame attack: R5 pins the frame by post). If it verified "
            "=> SPEC-TOO-WEAK."),
        "witness": _wit_reg('true ["--x"]'),
    },
    {
        "id": "rival-reg-drop-common-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Frame violation on the OTHER polarity of requiresSystemChecks: correct
        # when the command validates, but for a NON-validating command it discards
        # every already-recognised option. Violates R2 (`rv=false → out =
        # commonOptions`) and R5 at requiresSystemChecks=FALSE with a non-empty
        # commonOptions — a point NO other reject case reaches: rival-reg-drop-
        # common breaks the frame only at rv=true, and rival-reg-always-add is
        # witnessed at the empty frame, so R2/R5 were never jointly probed at
        # (false, non-empty). ADDED by audit.
        "module": _reg(
            "    let out : List String :=\n"
            "      if requiresSystemChecks then\n"
            "        commonOptions ++ [skipChecksFlag]\n"
            "      else\n"
            "        []\n"
            "    return out"),
        "refinement": (
            "keeps the correct assembly for a validating command but rebuilds a "
            "NON-validating command's option set as empty, so such a command "
            "stops recognising the framework and command-specific options it "
            "already accepted. Every argument-parsing PASS_TO_PASS test for a "
            "non-validating command breaks, and the option set the failing test "
            "depends on is only accidentally intact. F2P NOT resolved cleanly."),
        "rationale": (
            "REJECT from R2 (`rv=false → out = commonOptions`) and R5 (`∀ s ∈ "
            "commonOptions → s ∈ out`): at requiresSystemChecks=false with a "
            "non-empty commonOptions the rival drops its members. Refuted at "
            "input `false [\"--x\"]` — the ONLY reject witness combining "
            "requiresSystemChecks=false with a NON-EMPTY commonOptions, so the "
            "frame clause is now attacked on both polarities of the validation "
            "flag rather than only at rv=true. No nagini sibling (that carrier "
            "has no list frame); ADDED by audit to close a measured coverage gap. "
            "If it verified => SPEC-TOO-WEAK."),
        "witness": _wit_reg('false ["--x"]'),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                         -> here
#   -----------------------------------------------------------------------
#   pos-pos-bool-collapse               -> pos-reg-local            RE-SHAPED
#   pos-wrv-direct-boolean              -> pos-src-demorgan         RE-EXPRESSED
#   pos-wrv-demorgan-nested             -> pos-src-branch           PORTED
#   admiss-self-call-fshaped            -> admiss-cross-call-fshaped PORTED
#   weak-wrv-drop-skip-discriminating   -> rival-src-drop-skip      PORTED
#   weak-wrv-inverted-skip-polarity     -> rival-src-inverted       PORTED
#   weak-wrv-flip-no-skip-combo         -> rival-src-const-false    PORTED
#   (no direct sibling)                 -> rival-src-ignore-rv      ADDED (rv=F binder)
#   weak-pos-constant-false             -> rival-reg-never-add      PORTED
#   weak-pos-constant-true              -> rival-reg-always-add     PORTED
#   (no direct sibling)                 -> rival-reg-drop-common    ADDED (R5 frame, rv=T)
#   (no direct sibling)          -> rival-reg-drop-common-false     ADDED by audit
#                                                                   (R2/R5 frame, rv=F)
#   AXIOM_TESTS (2)                     -> (none)                   DROPPED (G-AX lane)
#
# 12 velvet SPEC cases: 3 soundness, 1 admissibility, 8 uniqueness. Both modeled
# obligations are DEFENDED (positives) and ATTACKED (rivals): shouldRunSystemChecks
# by pos-src-demorgan / pos-src-branch and the three src rivals;
# registeredCommandOptions by pos-reg-local and the four reg rivals.
#
# CARRIER NARROWING. The nagini file models two boolean functions
# (parser_offers_skip, will_run_validation) over the boolean cross-product. This
# bundle widens the option-offer function to its real carrier: a `List String`
# result whose post pins the exact list (R1/R2), the opt-out membership (R3/R4),
# AND the frame of already-recognised options (R5). So the two nagini
# parser_offers_skip rivals port to reg-never-add / reg-always-add, and R5 gains
# a dedicated frame rival (reg-drop-common) with no nagini counterpart — the
# nagini function had no list frame to violate.
#
# CLAUSE / BINDER / POINT COVERAGE.
#   * S1 (shouldRunSystemChecks) is attacked at (T,T) [drop-skip], (T,F)
#     [inverted, const-false], and (F,F) [ignore-rv]; combined with the positives'
#     full truth table the four (rv, rs) combinations are all exercised, and BOTH
#     binders vary across the reject witnesses — `requiresSystemChecks` takes true
#     (drop-skip/inverted/const-false) and false (ignore-rv), `skipRequested`
#     takes true (drop-skip) and false (inverted/const-false/ignore-rv).
#   * R1/R3 attacked by reg-never-add at (true, []); R2/R4 by reg-always-add at
#     (false, []); R5 by reg-drop-common at (true, ["--x"]); R2/R5 jointly by
#     reg-drop-common-false at (false, ["--x"]). `requiresSystemChecks` varies
#     T↔F and `commonOptions` varies empty↔non-empty across reject witnesses,
#     and the two vary INDEPENDENTLY: all four (rv, empty/non-empty) corners are
#     now reached. Before the audit added reg-drop-common-false the frame clause
#     was probed only at rv=true, so a rival that mangled a NON-validating
#     command's option frame was unattacked; it is now case 12 and is rejected.
#   * Reject witness points: `true true`, `true false` (two rivals),
#     `false false`, `true []`, `false []`, `true ["--x"]`, `false ["--x"]` —
#     6 distinct points, no binder held fixed by every witness.
#
# SPEC OBSERVATION recorded by audit (NOT a hole; no case asserts otherwise).
#   R1 pins the exact LIST `out = commonOptions ++ [skipChecksFlag]`, i.e. it
#   fixes the ORDER in which the opt-out option is appended, whereas mapping.md
#   §2 declares the behavioural carrier to be membership ("argument acceptance is
#   membership-based; ordering only affects help display, not what parses"). So a
#   faithful correct impl that PREPENDS the option instead of appending it is
#   rejected by R1 even though it is membership-identical to gold at every input
#   (machine-checked: the prepend variant fails with `unsolved goals ... (if
#   requiresSystemChecks = true then skipChecksFlag :: commonOptions else
#   commonOptions) = commonOptions ++ [skipChecksFlag]`, while `s ∈ flag :: co ↔
#   s ∈ co ++ [flag]` is provable). This makes R1 STRONGER than the declared
#   carrier requires. It is recorded rather than shipped as a positive control:
#   the spec is frozen, R1's extra strength cannot admit a wrong impl (it only
#   narrows what verifies), and turning it into an expect="verify" case would be
#   authoring a case designed to fail. Escalated in the audit payload instead.
#
# FRAME-MUTATION: VACUOUS as a permission attack (no `mut`, no heap, no aliasing).
#   The frame OBLIGATION survives as R5 (`∀ s ∈ commonOptions → s ∈ out`) and is
#   attacked directly by rival-reg-drop-common — the referentially-transparent
#   analogue of the nagini permission-frame concern.
# DIVERGENCE: VACUOUS. No nagini diverge case to port; `total` semantics forbids a
#   vacuously-verifying non-terminating impl. None written, none claimed dropped.
# DROPPED (AXIOM_TESTS): the nagini file's argparse store_true axiom-soundness /
#   containment probes are G-AX's job (axiom_check.py / mapping.md); the G-PBT
#   gate ignores AXIOM_TESTS regardless.
#
# WITNESS MECHANICS: both postconditions are decidable (no opaque callee), so
#   every witness uses the tester+`decide` path at concrete literals — no
#   hypothesis is bound, so no consistency probe is needed. All EIGHT checked with
#   scripts/lean_verify.sh: rival build exit 0, gold build exit 1 with a `decide`
#   refutation naming the concrete input.
#
# SPEC-TOO-WEAK PROBE (audit, attack D). Seven NEW wrong impls beyond the rivals
#   above were built against the frozen spec; every one was REJECTED, so no spec
#   hole was found on either obligation: an extra bogus option alongside the
#   opt-out one, the opt-out option registered twice, a reversed option frame, an
#   XOR gate, a negated gate, and a gate that ignores the validation flag. Two
#   control probes confirm the spec is not rejecting for spurious reasons: an impl
#   that differs from gold ONLY where the `require` is violated VERIFIES (correct —
#   the precondition genuinely restricts the domain), and a self-recursive gate
#   body fails on TERMINATION (`failed to infer structural recursion`), which is
#   the `total`-semantics guarantee this file claims, measured rather than assumed.
AXIOM_TESTS = []
