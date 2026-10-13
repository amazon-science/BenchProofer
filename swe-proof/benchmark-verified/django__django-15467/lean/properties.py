# properties.py — G-PBT falsification battery for django__django-15467 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   emptyLabel : Bool → Bool → Option String → Option String
#   Three inputs describe the decision: `radioBranch` (true exactly when the
#   single-choice control is the one being built), `blank` (true when the relation
#   is optional), and `provided` (the caller-supplied placeholder, if any). The
#   single postcondition `problem_spec_emptyLabel` pins the resolved placeholder
#   in EVERY case with no slack:
#     result = if radioBranch
#                then (if blank then some (provided.getD noneLabel) else none)
#                else provided
#   Reading off the independent top-level regions of that predicate:
#     (K1) CARRY-THROUGH: when radioBranch is false the result is `provided`
#          unchanged — the caller's value is carried through untouched.
#     (K2) REQUIRED relation: radioBranch ∧ ¬blank ⇒ result is `none` (no
#          placeholder entry is offered).
#     (K3) CALLER-WINS: radioBranch ∧ blank ∧ provided = some s ⇒ result = some s
#          (the caller's own label is preserved verbatim). This is the
#          DISCRIMINATING clause the F2P test exercises.
#     (K4) DEFAULT: radioBranch ∧ blank ∧ provided = none ⇒ result =
#          some noneLabel (the standard default placeholder).
#   `noneLabel` is a FIXED constant string ("None"), not an input-parameterized
#   answer-key: every output is grounded in the three inputs, so there is no
#   ungrounded-oracle echo to build. All clauses are transparent (`Option`/`Bool`
#   under `if`/`getD`), so witnesses need no conditioning on any carrier — `decide`
#   reduces the predicate at any literal input.
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled a mutable
# `kwargs` dict with a FULL-permission write and five Ensures clauses (E1..E5)
# split between (a) the key/post-state coupling of the dict (E1: key present;
# E2: post-state == return) and (b) the value decision (E3/E4/E5). This backend
# models the purely functional core — a single `Option String` RESULT, the value
# forwarded into the form field — so the dict's key-presence and post-state-pin
# clauses (E1/E2) have NO counterpart: there is no separate return-vs-post-state
# to decouple and no key to leave unset. nagini's value-decision clauses port
# directly onto this carrier's regions:
#     E3 (not permits_empty ⇒ absent) ≈ K2 (required ⇒ none)   [see note below]
#     E4 (permits_empty ∧ present ⇒ caller value)  ≈ K3 (caller wins)
#     E5 (permits_empty ∧ absent  ⇒ default)        ≈ K4 (default)
#   nagini's `permits_empty` conflated two of this carrier's binders: it fired the
#   changed assignment only inside the radio branch, so its "forbids-empty" arm is
#   really "radio branch taken AND relation required" — split here into `radioBranch`
#   and `blank`. That split EXPOSES a binder nagini's carrier could not vary
#   independently: `radioBranch = false` (the caller already chose the widget),
#   whose carry-through (K1) is attacked by a rival with no nagini counterpart.
#
# LANES THAT DO NOT PORT:
#   * nagini E1/E2 (KEY-PRESENCE + POST-STATE-PIN of the mutable dict), in their
#     STRUCTURAL form only. This backend's result is a single referentially-transparent
#     value: there is no post-state distinct from the return, so the store-default/
#     return-caller rival (a return that disagrees with the write) genuinely has no
#     counterpart — the two are one object here.
#     AUDIT CORRECTION: the port also recorded the no-write rival (nagini `atk-no-write`)
#     as vacuous under this same heading, and that was WRONG. "The key was never
#     written" has no counterpart, but the BEHAVIOUR it encodes — the resolution step
#     never ran, so the caller's value is forwarded without any decision being made —
#     is a plain value-level divergence and is fully expressible. Landed as
#     `riv-resolution-never-runs`, whose witness was SEEN to hold of the rival and to
#     be refuted on the frozen solution.
#   * FRAME / PERMISSION-MUTATION (nagini's full-permission write discipline). Lean
#     is referentially transparent — no aliasing, no fractional permission — so a
#     "mutate a read-only input" rival is not expressible. VACUOUS here.
#   * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class.
#     AUDIT CORRECTION: the port recorded this class as vacuous because "a
#     non-terminating implementation cannot be written at all". That reason is
#     FALSE and was measured false. This bundle sets no
#     `loom.semantics.termination` option (it is vanilla Lean), and two shapes were
#     built:
#       (a) a bare self-recursive `def` with no decreasing measure — the MODULE
#           fails to elaborate, `fail to show termination for
#           implementation_emptyLabel`. So the total-`def` claim holds only for
#           this shape, and its rejection is a termination obligation, not a spec
#           one;
#       (b) `partial def implementation_emptyLabel … := implementation_emptyLabel
#           radioBranch blank provided` — this DOES elaborate as a declaration and
#           PASSES variant_scope (checked: no problems), so a diverging rival is
#           writable here after all.
#     What makes (b) unshippable is not inexpressibility but the absence of a
#     discriminator: a `partial def` is irreducible, so no witness can hold of it.
#     Three were built against it — `decide` after `unfold`, `simp [spec, impl]`,
#     and `decide +kernel` — and all three FAILED on the rival (the half a witness
#     must pass), because `unfold` cannot unfold a `partial def`. A witness-less
#     reject case is exactly what this gate refuses, so there is nothing to land;
#     the class is recorded as a KNOWN HOLE in the spec's reach, and the reason is
#     the irreducibility of the rival, not the impossibility of writing one.
#   * ADMISSIBILITY — NOT N/A. The port recorded this lane as N/A on the ground
#     that the lean obligation carries no precondition hypothesis, so nothing could
#     be PRECOND-TOO-STRONG. That is the wrong test: on a total carrier the
#     analogue of an over-strong precondition is the obligation being UNSATISFIABLE
#     at an F2P-shaped input, which a positive that discharges the spec predicate
#     at that concrete input tests directly. Landed as `adm-ground-points` below.
#   * AXIOM_TESTS (nagini had none). The one changed operation (dict.get with a
#     default) is modeled DEEPLY here as `provided.getD noneLabel` over transparent
#     carriers, so there is no consumed axiom; the axiom lane belongs to G-AX
#     regardless and this gate ignores it.
from pathlib import Path

INSTANCE = "django__django-15467"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the branch-reorder positive) swaps THIS block.
_IMPL = (
    "def implementation_emptyLabel\n"
    "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
    "  Id.run do\n"
    "    let mut emptyLabel := provided\n"
    "    if radioBranch then\n"
    "      emptyLabel := if blank then some (provided.getD noneLabel) else none\n"
    "    return emptyLabel"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the pure-if-expression positive, whose different impl shape needs an (equally cheap,
# honest) reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro radioBranch blank provided\n"
    "  unfold problem_spec_emptyLabel implementation_emptyLabel\n"
    "  cases radioBranch <;> rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-branch-reorder: structurally-DIFFERENT but behaviourally identical. Instead of
# mutating a `let mut` accumulator and updating it once inside the radio branch, the
# decision is expressed as nested `if`s with early `return`s (the required and default
# sub-cases returned directly, carry-through as the fall-through), AND the default
# fallback is written with `<|>` (`Option.orElse`) rather than `getD`. The output
# equals the frozen impl's on every input. The frozen `theorem correct_emptyLabel`
# STATEMENT is byte-identical; the proof is reproven with the cheapest tactic the new
# shape admits — no new axiom/lemma/sorry.
#
# AUDIT NOTE (why `<|>` and not the plain early-return reorder): as ported, this
# case's impl still spelled the optional arm `some (provided.getD noneLabel)`, so
# after `Id.run` reduction it was DEFINITIONALLY the frozen impl — measured, not
# argued: the ported module closed under the FROZEN narrow body
# `cases radioBranch <;> rfl` (exit 0) and even under a bare `rfl` with no `unfold`
# and no case split at all (exit 0), exactly as the frozen solution itself does
# (also exit 0 under bare `rfl`). A positive whose obligation closes by bare `rfl`
# cannot fail for any reason connected to spec strength, so the case passed honestly
# while testing nothing. Swapping `getD` for `<|>` breaks that definitional
# coincidence: the repaired module FAILS under bare `rfl` (exit 1) and FAILS under
# the frozen narrow body (exit 1, `Tactic 'rfl' failed`), and VERIFIES (exit 0) only
# with the `cases provided` split. If it FAILS => SPEC-TOO-STRONG (postcondition
# over-fit to one syntactic impl shape).
_POS_REORDER = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_emptyLabel\n"
        "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
        "  Id.run do\n"
        "    if radioBranch then\n"
        "      if blank then\n"
        "        return (provided <|> some noneLabel)\n"
        "      else\n"
        "        return none\n"
        "    return provided",
    ),
    _PROOF,
    "  intro radioBranch blank provided\n"
    "  unfold problem_spec_emptyLabel implementation_emptyLabel\n"
    "  cases radioBranch <;> cases blank <;> cases provided <;> rfl",
)

# adm-ground-points (ADDED BY AUDIT): the ADMISSIBILITY positive the port dropped as
# "N/A, the obligation binds no precondition". On a total carrier the lane's content
# is not a Requires to admit but the obligation being SATISFIABLE at the inputs the
# real suite exercises — an obligation vacuous or contradictory at an F2P-shaped
# point would still discharge `∀ …` if the spec predicate were unsatisfiable there.
# So this case discharges `problem_spec_emptyLabel` BY EVALUATION at four concrete
# ground points, each as a `have`, and only then closes the frozen obligation
# VERBATIM (the frozen tactic body is left byte-identical underneath):
#   (true, true, some "Custom empty label") — the F2P-shaped point (caller wins, K3)
#   (true, false, none)                    — the required arm (K2)
#   (true, true, none)                     — the default arm (K4)
#   (false, true, some "Custom empty label") — carry-through (K1)
# Nothing is assumed: no new declaration, no axiom/lemma/sorry, statement
# byte-identical. If it FAILS => the obligation is not satisfiable at a normal input
# (the total-carrier analogue of PRECOND-TOO-STRONG).
_ADM_GROUND = _swap(
    _BASE,
    _PROOF,
    "  have _f2p : problem_spec_emptyLabel true true (some \"Custom empty label\")\n"
    "      (implementation_emptyLabel true true (some \"Custom empty label\")) := by\n"
    "    unfold problem_spec_emptyLabel implementation_emptyLabel\n"
    "    decide\n"
    "  have _required : problem_spec_emptyLabel true false none\n"
    "      (implementation_emptyLabel true false none) := by\n"
    "    unfold problem_spec_emptyLabel implementation_emptyLabel\n"
    "    decide\n"
    "  have _default : problem_spec_emptyLabel true true none\n"
    "      (implementation_emptyLabel true true none) := by\n"
    "    unfold problem_spec_emptyLabel implementation_emptyLabel\n"
    "    decide\n"
    "  have _carry : problem_spec_emptyLabel false true (some \"Custom empty label\")\n"
    "      (implementation_emptyLabel false true (some \"Custom empty label\")) := by\n"
    "    unfold problem_spec_emptyLabel implementation_emptyLabel\n"
    "    decide\n"
    + _PROOF,
)

# pos-pure-if-expression: a structurally different CORRECT impl written as a pure
# `if`-expression (no `Id.run do` monad, no `let mut`, no early return) AND with the
# default-fallback spelled out as an explicit `match` on `provided` instead of `getD`.
# Semantics identical on every input. The theorem STATEMENT is byte-identical; the
# proof must case-split on `provided` (`cases radioBranch <;> cases blank <;> cases
# provided <;> rfl`) — no new axiom/lemma/sorry.
#
# AUDIT NOTE (why the `match` and not just the pure `if`): a pure `if`-expression that
# still wrote `some (provided.getD noneLabel)` is, token-for-token, the spec predicate's
# own right-hand side, so its `correct_` obligation closed by bare `rfl` and the case
# could not have failed for any reason connected to spec strength — a positive that
# tests nothing while passing honestly. Expanding `getD` into a `match` makes the impl
# NOT definitionally the spec's RHS: SEEN to require the wider tactic (the same impl
# carrying the frozen `cases radioBranch <;> rfl` body fails with `Tactic 'rfl'
# failed`), so this positive now genuinely exercises the postcondition's ability to
# admit a reshaped correct impl. If it FAILS => SPEC-TOO-STRONG (the postcondition is
# bound to one syntactic impl shape rather than the behaviour).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_emptyLabel\n"
        "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
        "  if radioBranch then\n"
        "    (if blank then\n"
        "        (match provided with | some s => some s | none => some noneLabel)\n"
        "      else none)\n"
        "  else provided",
    ),
    _PROOF,
    "  intro radioBranch blank provided\n"
    "  unfold problem_spec_emptyLabel implementation_emptyLabel\n"
    "  cases radioBranch <;> cases blank <;> cases provided <;> rfl",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# riv-truthiness-or-form (nagini atk-truthiness-or-form): the issue's `or`-form —
# keep the caller's placeholder ONLY when it is truthy, otherwise fall back to the
# default. Modeled here as: in the optional-relation arm, a `some ""` (falsy) caller
# label is replaced by the default instead of preserved. Correct on a NON-EMPTY
# caller label (the truthy F2P case) but drops a falsy present value. Attacks K3.
_RIV_TRUTHINESS = _swap(
    _BASE,
    _IMPL,
    "def implementation_emptyLabel\n"
    "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
    "  Id.run do\n"
    "    let mut emptyLabel := provided\n"
    "    if radioBranch then\n"
    "      emptyLabel := if blank then\n"
    "          (match provided with\n"
    "            | some s => if s = \"\" then some noneLabel else some s\n"
    "            | none => some noneLabel)\n"
    "        else none\n"
    "    return emptyLabel",
)

# riv-prepatch-ignore-caller (nagini atk-prepatch-unconditional-default): the literal
# PRE-PATCH behaviour — in the optional-relation arm, always emit the default and
# discard any caller-supplied placeholder. Correct on the required arm and on the
# no-override optional case, WRONG whenever the caller supplied a label. Attacks K3.
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_emptyLabel\n"
    "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
    "  Id.run do\n"
    "    let mut emptyLabel := provided\n"
    "    if radioBranch then\n"
    "      emptyLabel := if blank then some noneLabel else none\n"
    "    return emptyLabel",
)

# riv-required-uses-default (nagini atk-forbids-empty-uses-default): in the REQUIRED
# arm, emit the default placeholder instead of `none`. Correct on both optional arms,
# wrong only on the required arm. Attacks K2 (the P2P sub-domain that pins `none` for
# a required relation).
_RIV_REQUIRED = _swap(
    _BASE,
    _IMPL,
    "def implementation_emptyLabel\n"
    "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
    "  Id.run do\n"
    "    let mut emptyLabel := provided\n"
    "    if radioBranch then\n"
    "      emptyLabel := if blank then some (provided.getD noneLabel) else some noneLabel\n"
    "    return emptyLabel",
)

# riv-optional-absent-drops-default (nagini atk-permits-absent-uses-sentinel): in the
# optional arm with NO caller-supplied label, emit `none` (no placeholder) instead of
# the default. Correct on the present and required arms, wrong only on
# optional+no-override. Attacks K4.
_RIV_ABSENT = _swap(
    _BASE,
    _IMPL,
    "def implementation_emptyLabel\n"
    "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
    "  Id.run do\n"
    "    let mut emptyLabel := provided\n"
    "    if radioBranch then\n"
    "      emptyLabel := if blank then\n"
    "          (match provided with | some s => some s | none => none)\n"
    "        else none\n"
    "    return emptyLabel",
)

# riv-ignore-radiobranch: NO direct nagini counterpart — this backend split nagini's
# single `permits_empty` guard into `radioBranch` and `blank`, exposing the
# carry-through binder K1 that nagini's carrier could not vary. This rival ignores
# `radioBranch` entirely and applies the placeholder decision unconditionally, so it
# overwrites the caller's carried-through value when the caller had already chosen the
# widget. Correct whenever radioBranch is true, WRONG when radioBranch is false.
# Attacks K1.
_RIV_CARRY = _swap(
    _BASE,
    _IMPL,
    "def implementation_emptyLabel\n"
    "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
    "  Id.run do\n"
    "    let mut emptyLabel := provided\n"
    "    emptyLabel := if blank then some (provided.getD noneLabel) else none\n"
    "    return emptyLabel",
)

# riv-caller-wins-ignores-optionality (ADDED BY AUDIT): the caller-value preference is
# hoisted OUTSIDE the optionality check, so a supplied placeholder wins even for a
# REQUIRED relation and the optionality test is consulted only when the caller supplied
# nothing. This is the one near-miss the ported rivals left unattacked: every existing
# rival varies a single arm's VALUE, and each is correct on the whole
# `provided = some s` × `¬blank` corner, so the battery never probed whether the
# spec forces the optionality decision to DOMINATE the caller's value. Correct on all
# three of K1/K3/K4 and on the required arm with no caller label; wrong exactly on
# radioBranch ∧ ¬blank ∧ provided = some s. Attacks K2 at a point the K2 rival misses
# (that rival is wrong for every `provided`, so it never isolates the precedence).
_RIV_PRECEDENCE = _swap(
    _BASE,
    _IMPL,
    "def implementation_emptyLabel\n"
    "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
    "  Id.run do\n"
    "    let mut emptyLabel := provided\n"
    "    if radioBranch then\n"
    "      emptyLabel := match provided with\n"
    "        | some s => some s\n"
    "        | none => if blank then some noneLabel else none\n"
    "    return emptyLabel",
)

# riv-resolution-never-runs (ADDED BY AUDIT): the resolution step never executes — the
# accumulator is initialized to the caller's value and returned untouched, so no
# placeholder decision is ever made. This is the behavioural shadow of the nagini
# E1/E2 lane (atk-no-write) that the port recorded as VACUOUS. On this carrier there is
# indeed no dict key to leave unset, but "the resolution never happened" IS observable
# as a value: the returned label stays the caller's input where the spec demands a
# decision. Wrong on the whole radioBranch = true region except where the caller's value
# already coincides with the decision. Attacks K2 and K4 jointly.
_RIV_NORESOLVE = _swap(
    _BASE,
    _IMPL,
    "def implementation_emptyLabel\n"
    "    (radioBranch blank : Bool) (provided : Option String) : Option String :=\n"
    "  Id.run do\n"
    "    let mut emptyLabel := provided\n"
    "    return emptyLabel",
)


def _wit(rb, bl, prov, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal (radioBranch, blank, provided). `decide` reduces the transparent
    `if`/`getD`/`Id.run` predicate and closes the disequality. Elaborates against a
    rival that diverges from the spec there, and FAILS on gold (which satisfies the
    spec at every input) — SEEN to discriminate both ways (checked in /tmp against
    each rival AND against the frozen solution)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_emptyLabel {rb} {bl} {prov}\n"
        f"    (implementation_emptyLabel {rb} {bl} {prov}) := by\n"
        f"  unfold problem_spec_emptyLabel implementation_emptyLabel\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the decision is expressed as "
            "nested `if`s with early `return`s (required and default sub-cases returned "
            "directly, carry-through as the fall-through) instead of one accumulator "
            "update, and the default fallback is written with `<|>` (`Option.orElse`) "
            "instead of `getD`. Output equals the frozen impl's on every input. The "
            "theorem STATEMENT is byte-identical; the proof needs the `cases provided` "
            "split — no new axiom/lemma/sorry. NOT definitionally the frozen impl, and "
            "measured so rather than asserted: this module FAILS under a bare `rfl` "
            "(exit 1) and FAILS under the frozen narrow body `cases radioBranch <;> "
            "rfl` (exit 1, `Tactic 'rfl' failed`), while the frozen solution itself "
            "closes under bare `rfl` (exit 0). The earlier `getD` spelling of this "
            "case did close under bare `rfl`, i.e. it was definitionally the frozen "
            "impl and tested nothing; that is repaired here. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape)."
        ),
    },
    {
        "id": "adm-ground-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_GROUND,
        "rationale": (
            "ADMISSIBILITY on a total carrier: the obligation must be SATISFIABLE at "
            "the inputs the real suite exercises, not merely provable as a `∀`. This "
            "case discharges `problem_spec_emptyLabel` BY EVALUATION (`decide`) at four "
            "concrete ground points — the F2P-shaped caller-wins point (true, true, "
            "some \"Custom empty label\"), the required arm (true, false, none), the "
            "default arm (true, true, none) and carry-through (false, true, some "
            "\"Custom empty label\") — each as a `have`, and only then closes the "
            "frozen obligation with the frozen tactic body left byte-identical "
            "underneath. Nothing is assumed: no new declaration, no axiom/lemma/sorry, "
            "statement byte-identical. The port dropped this lane as 'N/A, the "
            "obligation binds no precondition'; that reason does not apply on a total "
            "carrier, where an obligation unsatisfiable at an F2P-shaped input is the "
            "analogue of PRECOND-TOO-STRONG. If it FAILS => the spec is not "
            "satisfiable at a normal input."
        ),
    },
    {
        "id": "pos-pure-if-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure `if`-expression "
            "(no `Id.run do`, no `let mut`, no early return) AND with the "
            "default-fallback spelled out as an explicit `match` on `provided` instead "
            "of `getD`. Semantics identical on every input. The theorem STATEMENT is "
            "byte-identical; the proof must case-split on `provided` — no new "
            "axiom/lemma/sorry. Deliberately NOT definitionally equal to the spec "
            "predicate's own right-hand side: the same impl carrying the frozen "
            "`cases radioBranch <;> rfl` body was SEEN to fail with `Tactic 'rfl' "
            "failed`, so the case really does exercise the postcondition rather than "
            "restating it. If it FAILS => SPEC-TOO-STRONG (the postcondition is bound "
            "to one syntactic impl shape rather than the behaviour)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "riv-truthiness-or-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRUTHINESS,
        "refinement": (
            "the faithful real patch is the issue's proposed `or`-form (keep the "
            "caller's placeholder only when it is truthy, else fall back to the "
            "default). It passes the lone F2P test (a NON-EMPTY 'Custom empty label') "
            "and every P2P, so the suite does NOT distinguish it from gold — but it "
            "silently drops a falsy present caller value (an empty label) that the gold "
            "form preserves verbatim. A rival that verified here would admit a patch "
            "that fails the issue's real intent on the falsy sub-domain => a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause K3 (caller-wins). With radioBranch and blank true and "
            "provided = some \"\", the spec demands result = some \"\" (the caller's own "
            "label kept), but the rival returns some noneLabel. Witness probes the "
            "optional relation with a FALSY present caller label. If it VERIFIES => "
            "SPEC-TOO-WEAK (caller-wins unpinned on the falsy sub-domain)."
        ),
        # radioBranch=true, blank=true, provided=some "" : gold -> some ""; rival -> some "None".
        "witness": _wit("true", "true", '(some "")',
                        "optional relation, falsy present caller label: gold keeps it, "
                        "truthiness rival replaces it with the default"),
    },
    {
        "id": "riv-prepatch-ignore-caller",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "this IS the pre-patch behaviour: in the optional-relation arm it always "
            "emits the default placeholder and discards any caller-supplied label — "
            "exactly the assignment the fix replaces. Its faithful real patch is the "
            "unchanged repo, which overrides a caller-supplied placeholder and so FAILS "
            "the F2P test (which pins the caller's own label). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause K3. With radioBranch and blank true and provided = "
            "some \"X\", the spec demands result = some \"X\" but the rival returns "
            "some noneLabel unconditionally. Witness probes the optional relation with a "
            "NON-EMPTY present caller label (the exact F2P discriminator). If it "
            "VERIFIES => SPEC-TOO-WEAK (the caller-override is not enforced)."
        ),
        # radioBranch=true, blank=true, provided=some "X" : gold -> some "X"; rival -> some "None".
        "witness": _wit("true", "true", '(some "X")',
                        "optional relation, non-empty caller label: gold keeps it, "
                        "pre-patch rival overrides with the default"),
    },
    {
        "id": "riv-required-uses-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REQUIRED,
        "refinement": (
            "a patch emitting the default placeholder for a REQUIRED relation makes the "
            "control offer a placeholder entry where none should exist; the resolved "
            "value becomes a non-`none` label for a required relation, FAILING the P2P "
            "assertion that a required relation yields no placeholder. Does NOT resolve "
            "(regresses a P2P)."
        ),
        "rationale": (
            "REJECTED by clause K2 (required ⇒ none). With radioBranch true and blank "
            "false the spec demands result = none, but the rival returns some noneLabel. "
            "Witness probes the required-relation arm (blank = false). If it VERIFIES => "
            "SPEC-TOO-WEAK (the required arm is unpinned)."
        ),
        # radioBranch=true, blank=false, provided=none : gold -> none; rival -> some "None".
        "witness": _wit("true", "false", "none",
                        "required relation: gold offers no placeholder (none), rival "
                        "emits the default label"),
    },
    {
        "id": "riv-optional-absent-drops-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ABSENT,
        "refinement": (
            "a patch that yields no placeholder for an optional relation with no "
            "caller-supplied label drops the empty-selection entry such a relation must "
            "offer; the resolved value becomes `none` where the default placeholder is "
            "required. Its faithful real patch regresses a P2P: a suite test renders a "
            "single-choice control over an OPTIONAL relation with no caller-supplied "
            "placeholder and asserts the rendered choices lead with an empty entry "
            "labelled by the default placeholder text, which this rival removes "
            "entirely. Does NOT match gold behaviour."
        ),
        "rationale": (
            "REJECTED by clause K4 (default). With radioBranch and blank true and "
            "provided = none the spec demands result = some noneLabel, but the rival "
            "returns none. Witness probes the optional relation with NO caller-supplied "
            "label. If it VERIFIES => SPEC-TOO-WEAK (the default arm is unpinned)."
        ),
        # radioBranch=true, blank=true, provided=none : gold -> some "None"; rival -> none.
        "witness": _wit("true", "true", "none",
                        "optional relation, no caller label: gold supplies the default, "
                        "rival drops the placeholder"),
    },
    {
        "id": "riv-ignore-radiobranch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CARRY,
        "refinement": (
            "a patch that applies the placeholder decision unconditionally — without "
            "first checking that the single-choice control is the one being built — "
            "overwrites a caller's already-resolved value when the caller had chosen the "
            "widget themselves. The carried-through value is clobbered, changing the "
            "control the caller configured, which regresses the paths where the caller "
            "pre-set the widget. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause K1 (carry-through). With radioBranch false the spec "
            "demands result = provided (unchanged), but the rival applies the "
            "optional/required decision and returns none (for provided = none, blank "
            "true) instead. Witness probes radioBranch = false — the binder nagini's "
            "single `permits_empty` guard could not vary independently. If it VERIFIES "
            "=> SPEC-TOO-WEAK (carry-through unpinned)."
        ),
        # radioBranch=false: gold -> provided (none); rival -> if blank then some ... else none.
        # blank=true, provided=none : gold -> none, rival -> some "None" -> differ.
        "witness": _wit("false", "true", "none",
                        "control not being built (carry-through): gold returns the "
                        "caller value unchanged, rival applies the placeholder decision"),
    },
    {
        "id": "riv-caller-wins-ignores-optionality",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PRECEDENCE,
        "refinement": (
            "a patch that lets a caller-supplied placeholder win REGARDLESS of the "
            "relation's optionality offers an empty-selection entry on a REQUIRED "
            "relation whenever the caller happened to supply a label. It satisfies the "
            "issue's request (the caller's own label is honoured) and passes the lone "
            "F2P test, whose relation is optional, so neither the issue nor the F2P "
            "distinguishes it from gold — but it regresses the P2P assertion that a "
            "required relation yields no placeholder at all, for any caller who also "
            "supplied a label. Does NOT resolve (regresses a P2P)."
        ),
        "rationale": (
            "REJECTED by clause K2 (required ⇒ none), at the precedence corner the "
            "other K2 rival cannot isolate. With radioBranch true, blank false and "
            "provided = some \"X\" the spec demands result = none — the optionality "
            "decision DOMINATES the caller's value — but this rival returns some \"X\". "
            "Witness probes the required arm WITH a caller-supplied label; every other "
            "rival in this battery is correct at that point. If it VERIFIES => "
            "SPEC-TOO-WEAK (the spec would leave the precedence between the caller's "
            "value and the optionality decision unpinned)."
        ),
        # radioBranch=true, blank=false, provided=some "X" : gold -> none; rival -> some "X".
        "witness": _wit("true", "false", '(some "X")',
                        "required relation WITH a caller-supplied label: gold offers no "
                        "placeholder, rival lets the caller's label override optionality"),
    },
    {
        "id": "riv-resolution-never-runs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NORESOLVE,
        "refinement": (
            "a patch that computes nothing — the placeholder is never resolved and the "
            "caller's value (or its absence) is forwarded as-is. The single-choice "
            "control then offers whatever the caller happened to pass and no decision "
            "about the relation's optionality is made at all, so a required relation "
            "keeps a caller's placeholder and an optional relation with no caller value "
            "gets no default. FAILS the P2P that pins no placeholder for a required "
            "relation. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clauses K2/K4 jointly: with radioBranch true the spec demands "
            "a DECISION (none for a required relation, the default when an optional "
            "relation has no caller label), while this rival forwards `provided` "
            "untouched. Witness probes the required arm with a caller label, where the "
            "spec demands none and the rival yields some \"X\". This is the behavioural "
            "shadow of the nagini E1/E2 no-write lane, which this port recorded as "
            "inexpressible; the audit found it IS expressible on this carrier — not as "
            "an unset key, but as a returned value that skipped the resolution. If it "
            "VERIFIES => SPEC-TOO-WEAK (the spec would admit an impl that never acts)."
        ),
        # radioBranch=true, blank=false, provided=some "X" : gold -> none; rival -> some "X".
        "witness": _wit("true", "false", '(some "X")',
                        "required relation, resolution step never runs: gold decides "
                        "none, rival forwards the caller value unresolved"),
    },
]


# No @ContractOnly axioms and no opaque callees: the one changed operation
# (dict.get with a default) is modeled DEEPLY as `provided.getD noneLabel` over
# transparent carriers, so there is no consumed axiom here and the axiom lane
# belongs to G-AX regardless.
AXIOM_TESTS = []
