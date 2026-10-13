# properties.py — G-PBT spec-lane manifest for django__django-13741 (velvet).
# NOT a Velvet module: a record of adversarial falsification cases the runner
# executes. Every case is a full Solution.lean variant that shares the FROZEN
# spec (only the impl region differs, so `markers.same_spec` holds by
# construction and the `prove_correct` header survives verbatim); each is judged
# by the real verifier, and every expect="reject" case additionally ships a
# machine-checked refutation `witness`.
#
# Ported from the nagini sibling's battery. The case-by-case porting ledger is
# the OMISSIONS footer at the bottom of this file — one entry per nagini case
# without a counterpart here, each with the reason it has none. (An earlier
# revision of this header pointed at an `assessment` key in the port handoff,
# which is not part of the shipped bundle; the ledger now lives in the artifact
# that makes the claim.) The short version is that this bundle models a strictly
# NARROWER surface than nagini does.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read off the frozen Solution.lean)
# ---------------------------------------------------------------------------
#   method readonlyDigestFieldLocked (userFlag : Option Bool) return (out : Bool)
#
#   ONE input binder, `userFlag : Option Bool`, and THREE observable points:
#     none        -- the caller left the flag unspecified
#     some true   -- explicitly specified as non-editable
#     some false  -- explicitly specified as editable
#   No `require`, so the precondition admits all three; the reject witnesses
#   below probe all three of them (pts=3), which is the whole domain.
#
#   Because the binder has exactly three observable points, the whole function
#   space `Option Bool → Bool` is EIGHT functions: the frozen one and 7 wrong
#   ones. The four reject cases below cover the wrong ones that are single-point
#   or complementary deviations, and each single-point deviation gets its own
#   case, so no point's constraint is attested only jointly with another's.
#
#   Three top-level `ensures` clauses, of which only ONE is attackable:
#     (a) out = lockedDefault userFlag            <-- the sole OUTPUT clause;
#         load-bearing, and the only clause any impl can violate. Every rival
#         attacks it, at the distinct points of the binder.
#     (b) ∀ initial data, noEditChange (lockedDefault none) initial data = false
#     (c) ∀ data initial, noEditValue (lockedDefault none) data initial = initial
#         Clauses (b)/(c) are IMPL-INDEPENDENT: neither mentions `out`. They
#         assert consequences of the framework's pre-existing non-editable
#         handling at the caller-unspecified default, and are discharged
#         identically for every impl from the frozen contract set. So no rival
#         can be built to violate them — they are not an unattacked clause, they
#         are unattackABLE, and the coverage criterion applies to (a) alone.
#
# Because the carrier is a three-valued `Option Bool` and the spec function is
# transparent, the refutations do NOT need to condition on an opaque term: each
# witness states its counterexample at a concrete literal input and closes by
# `decide`. No hypotheses are bound, so no witness can be a forgery-from-
# contradiction.

from pathlib import Path

INSTANCE = "django__django-13741"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The impl region body, verbatim, as the unique region-surgery anchor. The
# bare `userFlag.getD true` is NOT unique in the file (the pure-region spec
# function spells it too), so the anchor carries its `let out :=` / `return out`
# frame — which also places it ENTIRELY inside `-- impl-start` / `-- impl-end`,
# so no edit can reach the frozen spec.
# ---------------------------------------------------------------------------
_IMPL = """    let out := userFlag.getD true
    return out"""


# ---------------------------------------------------------------------------
# Witness preamble.
#
# The refutation is stated through Velvet's own tester machinery, which reaches
# the `method` contract that a bare predicate application cannot. One wrinkle
# has to be handled explicitly: `prove_postcondition_decidable_for`'s automatic
# instance search decides unbounded quantifiers only over `Nat`/`Int`, so it
# gets stuck on clauses (b)/(c), whose binders range over `List Char`. Left
# stuck, `decide` cannot reduce the tester and BOTH builds fail — an
# inconclusive result on a witness that was never tried.
#
# So the two quantified conjuncts are discharged by the command's own `by`
# hook, from the contract facts the frozen file already carries. This ASSUMES
# NOTHING: `isTrue` demands a proof, and `grind` supplies it from the frozen
# `@[grind]` lemmas. It introduces no `axiom`/`sorry`/`admit`/`native_decide`
# and no new obligation — it only makes the already-true impl-independent
# conjuncts computable so that `decide` can get at the OUTPUT conjunct, which
# is the one under attack. Measured: with the hook, each rival's build exits 0
# at its own point and the frozen solution's build exits 1 at every point
# ("`decide` proved that the proposition ... is false").
# ---------------------------------------------------------------------------
_WITNESS_PREAMBLE = """extract_program_for readonlyDigestFieldLocked
prove_precondition_decidable_for readonlyDigestFieldLocked
prove_postcondition_decidable_for readonlyDigestFieldLocked by
  all_goals exact isTrue (by intro a b; grind)
derive_tester_for readonlyDigestFieldLocked

"""


def _witness(arg):
    """A refutation at one concrete point of the sole input binder."""
    return (_WITNESS_PREAMBLE
            + f"example : readonlyDigestFieldLockedTester {arg} = false := by\n"
              "  decide\n")


SPEC_TESTS = [
    # ------------------------------------------------------------- soundness
    {
        "id": "pos-control-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _IMPL,
            "    let out := match userFlag with\n"
            "      | some b => b\n"
            "      | none => true\n"
            "    return out",
        ),
        "rationale": "Ports the nagini positive control `mf-pos-control-ternary`: "
        "a structurally DIFFERENT but behaviourally identical impl — an explicit "
        "case split on the optional flag, with the caller-supplied arm written "
        "FIRST, in place of the frozen one-line defaulting expression. Must "
        "verify against the output clause `out = lockedDefault userFlag` at all "
        "three points of the binder; if it did not, that clause would be "
        "SPEC-TOO-STRONG (pinned to a spelling rather than to a behaviour). The "
        "frozen `prove_correct ... loom_solve` block is kept as-is and closes "
        "unchanged, so the obligation is REPROVEN for the new shape, not "
        "weakened. Recorded outcome: verifies.",
    },
    # --------------------------------------------------------- admissibility
    {
        "id": "admiss-unspecified-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _IMPL,
            "    -- admissibility: the caller-unspecified arm returns the DECIDED\n"
            "    -- claim that the unspecified default is the non-editable one, so\n"
            "    -- the arm's value is `true` only if that default really holds.\n"
            "    let unspecifiedIsLocked := decide (lockedDefault none = true)\n"
            "    let out := match userFlag with\n"
            "      | none => unspecifiedIsLocked\n"
            "      | some b => b\n"
            "    return out",
        ),
        "rationale": "Ports the nagini admissibility case `mf-admiss-caller`, "
        "which built the field on the shape the newly-covered test constructs "
        "(nothing specified by the caller) and ASSERTED the headline default is "
        "reachable with the value that test pins. Velvet has no statement-level "
        "`Assert`, and a self-call (`let u ← readonlyDigestFieldLocked none`) is "
        "not available either — it makes the method recursive and the build dies "
        "on termination inference (`the type Option Bool does not have a "
        "`.brecOn` recursor`), which is a tooling wall, not a spec fact. So the "
        "assertion is carried in the VALUE instead: the unspecified arm returns "
        "`decide (lockedDefault none = true)`, which is `true` exactly when the "
        "unspecified default is the non-editable one. That makes the case "
        "load-bearing rather than a restatement — writing the same shape with "
        "`= false` does NOT verify (`unsolved goals` on `ensures_3`), so this "
        "case would break if the headline default were anything else. Must "
        "verify: the method has no `require`, so the precondition must admit all "
        "three points including the unspecified one, and the postcondition must "
        "be establishable there with the default the change is about. A failure "
        "would be PRECOND-TOO-STRONG. Recorded outcome: verifies.\n"
        "NOTE (audit): the shape this case originally shipped returned "
        "`lockedDefault none` in the unspecified arm. That is a pure ECHO of the "
        "spec's own defaulting function — it verifies for whatever value that "
        "function has, so it demonstrated reachability but pinned nothing about "
        "WHICH default is reached (measured: an impl that echoes "
        "`lockedDefault userFlag` wholesale also verifies, exit 0). Replaced "
        "with the decided form above, which the `= false` control shows is "
        "sensitive to the default's actual value.",
    },
    # ------------------------------------------------------------ uniqueness
    {
        "id": "weak-unspecified-defaults-editable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _IMPL,
            "    let out := userFlag.getD false\n"
            "    return out",
        ),
        "witness": _witness("none"),
        "rationale": "Ports nagini's `mf-disabled-default-false`, the headline "
        "rival. Rejected by the output clause `out = lockedDefault userFlag` at "
        "`userFlag = none`: with nothing specified by the caller the flag must "
        "come out non-editable, and this rival supplies the opposite fallback. "
        "Note this is a NEAR-MISS — it agrees with the frozen spec at BOTH "
        "explicit points (`some b` defaults away to `b` either way) and diverges "
        "only on the unspecified one, so its witness is placed at exactly that "
        "point. Witness confirmed to discriminate: it elaborates against this "
        "rival and fails against the frozen solution.",
        "refinement": "This is the pre-change behaviour: with the flag left "
        "unspecified the construction falls through to the framework's own "
        "fallback (editable) instead of the desired non-editable default. Its "
        "faithful real patch is therefore the tree as it stood BEFORE the change "
        "— the newly-added defaulting step simply absent. The single "
        "newly-covered test constructs the field with nothing specified and "
        "asserts the resulting flag is non-editable, so that tree fails it and "
        "the instance does NOT resolve. A verifying rival here would be a true "
        "verify-does-not-imply-resolve break on the one clause the change is "
        "about.",
    },
    {
        "id": "weak-overrides-explicit-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _IMPL,
            "    -- Ignores the caller's choice: always non-editable.\n"
            "    let out := true\n"
            "    return out",
        ),
        "witness": _witness("(some false)"),
        "rationale": "Ports nagini's `mf-ignore-explicit-disabled`. Rejected by "
        "the output clause at `userFlag = some false`: an explicitly supplied "
        "flag must be honoured verbatim, and this rival overwrites it. The "
        "complementary near-miss to the case above — it is CORRECT at the "
        "unspecified point and at `some true`, and wrong only at `some false`, "
        "so its witness is placed there. That is a distinct point from every "
        "other witness in this battery, which is what makes the battery show "
        "that the spec depends on the binder's value rather than merely on its "
        "presence. Witness confirmed to discriminate.",
        "refinement": "Faithfully realised, this is a construction step that "
        "unconditionally IMPOSES the non-editable flag rather than merely "
        "supplying it when the caller specified nothing. A caller who explicitly "
        "asks for an editable field would silently get a non-editable one — a "
        "divergence the fill-if-absent semantics the change relies on never "
        "causes. It breaks the pre-existing contract that an explicitly passed "
        "construction argument reaches the base class untouched, on which the "
        "already-passing form-construction tests depend, so it does not "
        "faithfully resolve.",
    },
    {
        "id": "weak-constant-editable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _IMPL,
            "    -- Constant: the flag is never non-editable, whatever was asked.\n"
            "    let out := false\n"
            "    return out",
        ),
        "witness": _witness("(some true)"),
        "rationale": "Ports nagini's `df-always-false` — the constant-answer "
        "rival, which there stood in for the bespoke hard-coded override the "
        "change deletes. Rejected by the output clause. This rival is wrong on "
        "TWO points (`none` and `some true`), which is what separates it from "
        "`weak-unspecified-defaults-editable`: that one is wrong only at the "
        "unspecified point, whereas this one additionally discards an explicit "
        "request. Its witness is therefore placed at `some true` — the point "
        "that distinguishes the two rivals — rather than at the point they "
        "share, so the sub-domain this rival's rationale claims is the sub-domain "
        "the manifest actually demonstrates. Witness confirmed to discriminate.",
        "refinement": "Faithfully realised, this is a construction that reports "
        "the field as editable unconditionally — neither supplying the desired "
        "default when nothing was specified, nor honouring an explicit request "
        "for a non-editable field. It fails the newly-covered test on the first "
        "count (that test constructs with nothing specified and asserts the flag "
        "is non-editable), and it additionally regresses callers that ask for a "
        "non-editable field explicitly, whose stored value would become "
        "user-overwritable. It does not resolve.",
    },
    {
        "id": "weak-drops-explicit-locked",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _IMPL,
            "    -- Supplies the desired default when nothing was specified, but\n"
            "    -- reports every EXPLICITLY specified field as editable.\n"
            "    let out := match userFlag with\n"
            "      | none => true\n"
            "      | some _ => false\n"
            "    return out",
        ),
        "witness": _witness("(some true)"),
        "rationale": "Added by audit to close the one SINGLE-POINT deviation the "
        "battery did not isolate. Rejected by the output clause at `userFlag = "
        "some true`. The battery's three original rivals deviate from the frozen "
        "spec at `none` only, at `some false` only, and at `{none, some true}` "
        "jointly; that leaves `some true` covered only by a rival that is ALSO "
        "wrong at `none`, so no case attributed a rejection to `some true` "
        "ALONE. This rival is correct at the other two points — it supplies the "
        "desired default when nothing was specified, and it agrees at `some "
        "false` — so its witness at `some true` is the minimal counterexample for "
        "that point. With this case the battery's rivals plus the frozen impl "
        "enumerate every single-point deviation of the binder. Witness rebuilt "
        "during the audit: exit 0 against the rival, exit 1 against the frozen "
        "solution with `decide` proving the tester claim false.",
        "refinement": "Faithfully realised, this is a construction that fills the "
        "flag in when the caller specified nothing but then forces every "
        "explicitly specified field to editable — the mirror of "
        "`weak-overrides-explicit-flag`, discarding an explicit request in the "
        "other direction. It passes the newly-covered test (which specifies "
        "nothing) yet regresses every caller that explicitly asks for a "
        "non-editable field, whose stored value would become user-overwritable. "
        "It breaks the pre-existing contract that an explicitly passed "
        "construction argument reaches the base class untouched, which the "
        "already-passing form-construction tests depend on, so it does not "
        "faithfully resolve. It is the rival that shows the spec constrains the "
        "explicit-`true` point independently of the unspecified one.",
    },
]


# ---------------------------------------------------------------------------
# OMISSIONS ledger — every nagini case with no counterpart here, and why.
#
# The nagini sibling models a WIDER surface: two functions (`make_field` and
# `differs`) over a `required`/`disabled` pair plus a list-valued comparison,
# under a permission logic. This bundle models ONE function returning the single
# non-editability flag. Each drop below is a surface the frozen spec does not
# have, not a case that was hard to land.
#
#   mf-required-default-true — nagini's `required` binder does not exist here.
#     The frozen method takes ONE input (`userFlag : Option Bool`) and returns
#     ONE `Bool`; there is no second flag to default wrongly. INEXPRESSIBLE: a
#     rival would have to invent a binder, which changes the spec and is
#     rejected by variant_scope, not merely unproven.
#
#   df-pos-control-reorder, df-drop-short-circuit, df-none-not-empty,
#   df-admiss-self-call — all four are about `differs`/`has_changed`: a second
#     modeled METHOD that compares stored and submitted values. Here the
#     change-suppression behaviour is not a modeled method at all; it is
#     axiomatized (`noEditChange` / `noEditValue`) as pre-existing base-class
#     behaviour, and appears only in the two impl-INDEPENDENT `ensures` clauses
#     (b)/(c), neither of which mentions `out`. INEXPRESSIBLE as rivals: those
#     clauses are discharged from the frozen `@[grind]` contract lemmas for EVERY
#     impl, so no impl-region edit can make either fail. Demonstrated during the
#     audit: dropping the witness preamble's `by` hook leaves clauses (b)/(c)
#     with undecided `Decidable (∀ (data initial : List Char), ...)` goals over
#     an axiomatized constant — the impl is not a term in them.
#     df-none-not-empty additionally needs the None-vs-empty normalisation
#     boundary, which lives inside the axiomatized hooks and has no carrier here.
#
#   df-frame-mutate-disabled, df-frame-mutate-data — frame-mutation probes.
#     INEXPRESSIBLE by carrier: Lean is functional, with no aliasing and no
#     fractional permission, so there is no read-only-input write to attempt
#     (spec_guide §0.5). The directive-5 obligation translates to "a
#     non-mutated parameter must not be declared `mut`", and the frozen method
#     declares `userFlag` without `mut` and returns a fresh `Bool`, so the
#     nagini permission-violation class has no image here.
#
# What replaces the dropped coverage: the binder has exactly THREE observable
# points, so `Option Bool → Bool` has exactly 8 total functions — the frozen one
# and 7 wrong ones. The four reject cases above, together with the audit's own
# probes, cover every wrong function, and every SINGLE-point deviation is
# isolated by its own case. That is exhaustive on this carrier in a way the
# wider nagini surface could only sample.
# ---------------------------------------------------------------------------


# The axiom lane is G-AX's job; this gate ignores it.
AXIOM_TESTS = []
