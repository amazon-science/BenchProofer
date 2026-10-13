# properties.py — G-PBT falsification battery for django__django-11734 (lean lane).
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
#   relocateFilterIntoSubquery : String → FilterRHS → String × FilterRHS
#   A filter condition `(lhs, rhs)` is relocated one query boundary deeper. `rhs`
#   is one of three shapes — `value v` (a direct literal), `colRef name` (a
#   same-query column reference), `outerRef level name` (an outer-query reference
#   carrying a nesting level). The single postcondition
#   `problem_spec_relocateFilterIntoSubquery lhs rhs result` pins TWO independent
#   top-level clauses:
#     (C1) FRAME: the left-hand side is carried through untouched — `result.1 = lhs`.
#     (C2) RE-ANCHOR: the right-hand side is re-anchored — `result.2 = reanchor rhs`
#          — which fully PINS the per-shape dispatch across all three arms:
#            * value v          -> value v            (literal unchanged, no hop)
#            * colRef name       -> outerRef 1 name    (same-query ref -> reach out one)
#            * outerRef lvl name -> outerRef (lvl+1) name (existing ref -> one FURTHER)
#          No slack on any arm: a rival that mishandles ANY shape fails C2.
#   `reanchor` is a total, transparent 3-way match over the input carrier (no
#   opaque callee, no answer-key), so witnesses need no conditioning: `decide`
#   reduces the dispatch at any concrete FilterRHS literal.
#
# CARRIER NOTE / relation to the nagini sibling: nagini split the modeled behaviour
# across TWO pure functions over an int shape tag rhs_kind in {value, local, outer}
# — `rebind_into_inner_subquery` (the outward hop count) and
# `normalize_only_concrete_value` (the value-normalisation guard). This backend
# models the observable DIRECTLY and MORE RICHLY: a single re-anchor over a typed
# 3-shape carrier `FilterRHS`, returning the actual rewritten reference (level and
# all), not just an int hop count. So:
#   * nagini's `rebind` rivals (weak-outer-zero-hops, weak-local-zero-hops,
#     weak-value-one-hop) port onto clause C2's three arms — here they are refuted
#     on the ACTUAL rewritten reference, a strictly stronger discrimination than
#     nagini's hop-count int (the level the outer-ref carries is observable).
#   * a prepatch discriminator not separately present in nagini's rebind lane is
#     ADDED (weak-value-payload, by the audit): the value arm's PAYLOAD, as distinct
#     from its shape — nagini's int hop count could not express "the literal itself is
#     carried through unchanged" at all, since a literal contributes no hops. On this
#     typed carrier it is a real sub-clause of C2 and it was unattacked.
#   * a prepatch discriminator not separately present in nagini's rebind lane is
#     ADDED (weak-prepatch): the base_commit bug is not "zero hops" but "collapse
#     the carried level to one" (an OuterRef is a subclass of an F, so the base
#     `OuterRef(filter_rhs.name)` rebuilds at level ONE, discarding the level the
#     original reference carried). The typed carrier senses this where an int hop
#     count could not distinguish it from the zero-hop rival at every point.
#   * a FRAME rival on C1 (weak-lhs-mangled) is ADDED: the typed carrier models the
#     left-hand side as a real output component, so the "lhs untouched" clause is
#     directly attackable — the referential-transparency analogue of the
#     read-only-input frame obligation.
#
# LANES THAT DO NOT PORT:
#   * NORMALISE-GUARD (nagini's normalize_only_concrete_value rivals:
#     weak-normalize-all, weak-normalize-local-true). This backend does NOT model
#     the value-normalisation guard function at all — it is one of the two
#     behaviour-preserving supporting hunks that keep an expression RHS from being
#     mangled by value normalisation, orthogonal to the re-anchoring observable the
#     F2P test exercises. The lean bundle models only the purely-functional
#     re-anchoring core (one `theorem correct_*`), so these rivals have NO
#     counterpart here — legitimate carrier narrowing, NOT an omission for
#     difficulty. See 'assessment'.
#   * FRAME-MUTATION (nagini's fractional-permission write-back class). Lean is
#     referentially transparent — no aliasing, no Acc(x,1/2) read-only input to
#     overwrite — so a "store into a read-only input" rival is not expressible and
#     the class is VACUOUS here. The nagini sibling itself records this as N/A
#     (both its modeled functions took an int by value); on this carrier the LHS
#     "untouched" property is instead an ordinary output-frame clause (C1), which
#     IS attacked by weak-lhs-mangled. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION. Nothing to ship, and the nagini sibling carries no
#     diverge case anyway. AUDIT NOTE (repair): the reason recorded here was that a
#     non-terminating impl "cannot be written at all". That is not quite right — it can
#     be written as a `partial def` self-call, which stays in variant scope. Measured:
#     such a variant FAILS (exit 1) because a `partial def` is opaque to reduction, so
#     the frozen proof's `simp` leaves the two spec conjuncts as unsolved goals rather
#     than discharging them vacuously. So the class is not INEXPRESSIBLE but merely
#     UNINFORMATIVE: it lands in the same bucket as any reshaped impl whose proof no
#     longer closes, and adds no discrimination the level/name/lhs rivals do not already
#     provide. This backend is NOT under the velvet `loom.semantics.termination
#     "partial"` regime where such an impl verifies vacuously; that is a separate,
#     already-recorded spec hole (the corpus-wide termination-semantics finding), not re-derived here.
#   * ADMISSIBILITY — LANE RESTORED BY AUDIT; the reason recorded here was WRONG.
#     The port dropped the lane because "the lean obligation binds NO precondition
#     hypothesis, so nothing could be PRECOND-TOO-STRONG". That is precisely the
#     reason the audit brief rules out: on a TOTAL carrier the analogue of a
#     too-strong precondition is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, which a positive that discharges the obligation at that
#     concrete input — by evaluation, as a `have`, before closing the frozen
#     obligation verbatim — tests directly. The lane is therefore NOT vacuous here
#     and `adm-f2p-outerref` now carries it (measured: verifies, exit 0; and with a
#     deliberately FALSE claim at the same point it fails AT the `have`, so the case
#     is load-bearing rather than decorative). Nagini's own admissibility case
#     defended its {0,1,2} tagged-domain precondition; the analogue here is not "no
#     precondition, nothing to test" but "the F2P-shaped point is in the spec's
#     satisfiable domain", which is a real and checkable claim.
#   * AXIOM_TESTS (nagini's ax-classify-query-expression / ax-outerref-resolution-
#     levels). The axiom lane is G-AX's job; this gate ignores them. The re-anchor
#     is modeled DEEPLY over a transparent carrier, so there is no consumed axiom
#     here anyway.
from pathlib import Path

INSTANCE = "django__django-11734"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the reorder positive) swaps THIS block.
_IMPL = (
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name\n"
    "  | .colRef name       => newRhs := .outerRef 1 name\n"
    "  | .value _           => pure ()\n"
    "  return (lhs, newRhs)"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the pure-match positive, whose different impl shape needs an (equally cheap, honest)
# reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro lhs rhs\n"
    "  cases rhs <;>\n"
    "    simp [problem_spec_relocateFilterIntoSubquery,\n"
    "          implementation_relocateFilterIntoSubquery, reanchor]"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reorder-arms: structurally-DIFFERENT but behaviourally identical. The three
# match arms are written in a different order (value first, then colRef, then
# outerRef); each arm's rewrite is unchanged, so the output equals the frozen impl's
# on every input. The frozen `theorem correct_*` statement is kept byte-identical AND
# the frozen proof body still closes (`cases rhs <;> simp [...]` is insensitive to arm
# order). No reproof, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE,
    _IMPL,
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .value _           => pure ()\n"
    "  | .colRef name       => newRhs := .outerRef 1 name\n"
    "  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name\n"
    "  return (lhs, newRhs)",
)

# pos-pure-match: a structurally different CORRECT impl written as a pure `match`
# expression (no `Id.run do` monad, no `let mut`, no early return), directly returning
# the pair. Semantics identical on every input. The theorem STATEMENT is byte-
# identical; the proof body is GENUINELY reproven for the new shape —
# `cases rhs <;> exact ⟨rfl, rfl⟩`, which discharges the two spec conjuncts
# componentwise now that each arm returns the pair directly. No new axiom/lemma/sorry.
# If it FAILS => SPEC-TOO-STRONG (the postcondition is bound to the monadic impl shape
# rather than the behaviour).
#
# AUDIT NOTE (repair): this case previously swapped the frozen proof body for a
# byte-identical copy of ITSELF, so despite the prose it carried no reproof at all and
# the "different shape needs a new proof" claim was untested. Measured: with the frozen
# `simp [...]` body the pure-match impl verifies (exit 0), so the no-op swap passed
# honestly but attested nothing about reprovability; with the tactic the prose used to
# name (`cases rhs <;> rfl`) the file FAILS (exit 1, `Tactic 'rfl' failed`, the goal
# being a conjunction rather than an equation), so that claim was simply false. The
# swap below is a real one and was measured to verify (exit 0).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_relocateFilterIntoSubquery\n"
        "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS :=\n"
        "  match rhs with\n"
        "  | .value v           => (lhs, .value v)\n"
        "  | .colRef name       => (lhs, .outerRef 1 name)\n"
        "  | .outerRef lvl name => (lhs, .outerRef (lvl + 1) name)",
    ),
    _PROOF,
    "  intro lhs rhs\n"
    "  cases rhs <;> exact ⟨rfl, rfl⟩",
)

# adm-f2p-outerref: ADDED BY AUDIT. The admissibility lane, which the port recorded
# as N/A on the ground that "the frozen obligation has no precondition hypothesis, so
# nothing could be PRECOND-TOO-STRONG". That reason is the one the audit brief names as
# insufficient: on a TOTAL carrier the analogue of a too-strong precondition is the
# obligation being UNSATISFIABLE at exactly an F2P-shaped input, and a positive that
# discharges the obligation at that concrete input — by evaluation, as a `have`, BEFORE
# closing the frozen obligation verbatim — tests that directly.
#
# The impl is the FROZEN one (untouched) and the frozen tactic body still closes the
# obligation; the only addition is a leading `have` that EVALUATES the spec at the
# F2P-shaped point (an outer-query reference at level 2 — the shape the F2P test pins,
# where the relocated reference must reach out two levels rather than one) and closes it
# by `decide`. If the spec were unsatisfiable there, `decide` would refute the `have`
# and the case would FAIL => PRECOND-TOO-STRONG (an obligation no F2P-shaped input can
# meet). `clear` drops the hypothesis afterwards so it cannot help the main proof: the
# `have` must stand on its own evaluation, not be laundered into the frozen tactic.
#
# NEGATIVE CONTROL (measured, so the `have` is demonstrably load-bearing rather than
# dead weight): replacing the claim with a FALSE one at the same point (asserting the
# relocated reference is `outerRef 9 "pk"`) FAILS, exit 1, with `Tactic decide proved
# that the proposition ... is false` reported AT the `have` line. So this case's exit
# code tracks the concrete claim; it is not a no-op that passes for free. The case as
# shipped was measured to verify (exit 0).
_ADM_F2P = _swap(
    _BASE,
    _PROOF,
    "  intro lhs rhs\n"
    "  have hAdmissible :\n"
    "      problem_spec_relocateFilterIntoSubquery \"id\" (FilterRHS.outerRef 2 \"pk\")\n"
    "        (implementation_relocateFilterIntoSubquery \"id\"\n"
    "          (FilterRHS.outerRef 2 \"pk\")) := by\n"
    "    unfold problem_spec_relocateFilterIntoSubquery\n"
    "      implementation_relocateFilterIntoSubquery reanchor\n"
    "    decide\n"
    "  clear hAdmissible\n"
    "  cases rhs <;>\n"
    "    simp [problem_spec_relocateFilterIntoSubquery,\n"
    "          implementation_relocateFilterIntoSubquery, reanchor]",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-outer-zero-hops: an existing outer-query reference is carried into the deeper
# subquery UNCHANGED — zero extra outward hops (the outerRef arm does nothing).
# PARTIAL-DOMAIN on clause C2's outerRef arm: correct on value/colRef, WRONG on every
# outer reference (which must reach out one FURTHER level).
_RIV_OUTER_ZERO = _swap(
    _BASE,
    _IMPL,
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .outerRef _ _      => pure ()\n"
    "  | .colRef name       => newRhs := .outerRef 1 name\n"
    "  | .value _           => pure ()\n"
    "  return (lhs, newRhs)",
)

# weak-local-zero-hops: a same-query column reference is left UNCHANGED instead of
# being re-anchored to a level-one outer reference (the colRef arm does nothing).
# PARTIAL-DOMAIN on C2's colRef arm: correct on value/outer, WRONG on every same-query
# column reference.
_RIV_LOCAL_ZERO = _swap(
    _BASE,
    _IMPL,
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name\n"
    "  | .colRef _          => pure ()\n"
    "  | .value _           => pure ()\n"
    "  return (lhs, newRhs)",
)

# weak-value-one-hop: a plain literal is spuriously wrapped as a level-one outer
# reference instead of being left untouched (the value arm rewrites when it must not).
# PARTIAL-DOMAIN on C2's value arm: correct on colRef/outer, WRONG on every literal
# (which has no reference to re-anchor).
_RIV_VALUE_HOP = _swap(
    _BASE,
    _IMPL,
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name\n"
    "  | .colRef name       => newRhs := .outerRef 1 name\n"
    "  | .value _           => newRhs := .outerRef 1 \"0\"\n"
    "  return (lhs, newRhs)",
)

# weak-prepatch: the EXACT base_commit behaviour. An existing outer reference is
# rebuilt at level ONE (the carried level is DISCARDED), because at base_commit the
# outer-reference case is handled by the same-query-column branch (an outer reference
# is a subclass of a column reference), so it is rebuilt from its name alone at a fresh
# single level. Near-miss to weak-outer-zero-hops: both mishandle the outerRef arm,
# but this one collapses the level to 1 rather than leaving it unchanged, so it
# DISAGREES with the zero-hop rival on any level >= 2 reference — probed there.
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .outerRef _ name   => newRhs := .outerRef 1 name\n"
    "  | .colRef name       => newRhs := .outerRef 1 name\n"
    "  | .value _           => pure ()\n"
    "  return (lhs, newRhs)",
)

# weak-name-dropped: ADDED BY AUDIT. Gets the LEVEL arithmetic right on both reference
# arms (outerRef lvl -> lvl+1, colRef -> 1) but rebuilds the re-anchored reference with
# an EMPTY column name, discarding WHICH column the reference names. Every pre-existing
# rival attacks either the level payload or the lhs; none varies the `name` payload of
# the re-anchored reference, so "the spec pins the name too" was an unattacked
# sub-clause of C2. A real patch of this shape re-anchors to the correct query but
# points at no column, so the relocated condition compares the wrong thing entirely.
# Does NOT resolve.
_RIV_NAME_DROP = _swap(
    _BASE,
    _IMPL,
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .outerRef lvl _    => newRhs := .outerRef (lvl + 1) \"\"\n"
    "  | .colRef _          => newRhs := .outerRef 1 \"\"\n"
    "  | .value _           => pure ()\n"
    "  return (lhs, newRhs)",
)

# weak-value-payload: ADDED BY AUDIT. Keeps the value arm's SHAPE correct (a literal
# stays a literal — no spurious reference wrap, so weak-value-one-hop does not cover it)
# but perturbs the literal's own PAYLOAD, returning `value (v+1)` instead of `value v`.
# Every pre-existing rival varies a nesting level, a column name, or the lhs; none
# varies the carried literal, so "the spec pins the literal's value, not merely that it
# is still a literal" was an unattacked sub-clause of C2's value arm. A real patch of
# this shape passes the relocated literal through a coercion that does not round-trip,
# so the relocated condition compares against a different constant than the caller
# asked for. Measured: does NOT resolve (exit 1).
_RIV_VALUE_PAYLOAD = _swap(
    _BASE,
    _IMPL,
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name\n"
    "  | .colRef name       => newRhs := .outerRef 1 name\n"
    "  | .value v           => newRhs := .value (v + 1)\n"
    "  return (lhs, newRhs)",
)

# weak-lhs-mangled: re-anchors the right-hand side CORRECTLY on every shape (clause C2
# holds) but drops the left-hand side, returning the empty string instead of carrying
# `lhs` through. Attacks clause C1 (the FRAME) — the analogue of a read-only-input
# frame violation on this referentially-transparent carrier.
_RIV_LHS = _swap(
    _BASE,
    _IMPL,
    "def implementation_relocateFilterIntoSubquery\n"
    "    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do\n"
    "  let mut newRhs : FilterRHS := rhs\n"
    "  match rhs with\n"
    "  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name\n"
    "  | .colRef name       => newRhs := .outerRef 1 name\n"
    "  | .value _           => pure ()\n"
    "  return (\"\", newRhs)",
)


def _wit(lhs, rhs, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal (lhs, rhs). `unfold` exposes the spec conjunction and the impl's `Id.run`
    match; `decide` reduces the total 3-way dispatch and closes the disequality.
    Elaborates against a rival that diverges from the spec at that point, and FAILS on
    gold (which satisfies the spec at every input) — SEEN to discriminate both ways."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_relocateFilterIntoSubquery {lhs} {rhs}\n"
        f"    (implementation_relocateFilterIntoSubquery {lhs} {rhs}) := by\n"
        f"  unfold problem_spec_relocateFilterIntoSubquery "
        f"implementation_relocateFilterIntoSubquery reanchor\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder-arms",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the three match arms are written "
            "in a different order (value/colRef/outerRef), each arm's rewrite unchanged, "
            "so the output equals the frozen impl's on every input. The theorem statement "
            "is byte-identical and the FROZEN proof body still closes (`cases rhs <;> "
            "simp [...]` is insensitive to arm order) — a faithful restructure with no "
            "reproof and no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG "
            "(postcondition over-fit to one syntactic arm order)."
        ),
    },
    {
        "id": "pos-pure-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure `match` expression "
            "(no `Id.run do`, no `let mut`, no early return), directly returning the pair. "
            "Semantics identical on every input. The theorem STATEMENT is byte-identical; "
            "its proof is reproven honestly with `cases rhs <;> exact ⟨rfl, rfl⟩` — no new "
            "axiom/lemma/sorry, just the cheapest tactic for the new shape (AUDIT: this "
            "rationale previously named `cases rhs <;> simp [...]`, which is the FROZEN "
            "proof body and not what this case swaps in; corrected to the tactic actually "
            "shipped, which was measured to close, exit 0). If it FAILS "
            "=> SPEC-TOO-STRONG (the postcondition is bound to the monadic impl shape "
            "rather than the behaviour)."
        ),
    },

    {
        "id": "adm-f2p-outerref",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_F2P,
        "rationale": (
            "ADMISSIBILITY on a total carrier. The frozen obligation binds no precondition "
            "hypothesis, so the PRECOND-TOO-STRONG analogue here is the obligation being "
            "UNSATISFIABLE at an F2P-shaped input. This case discharges the spec at exactly "
            "that concrete point — an outer-query reference carrying level 2, the shape the "
            "F2P observable pins, where the relocated reference must reach out two levels — "
            "by EVALUATION as a leading `have`, then `clear`s it and closes the frozen "
            "obligation with the frozen tactic body verbatim. The impl is the frozen one. "
            "If the spec admitted no such input the `have`'s `decide` would refute it and "
            "this case would FAIL => PRECOND-TOO-STRONG. Demonstrated load-bearing: the "
            "same case with a FALSE claim at that point (relocated reference asserted to be "
            "at level 9) fails at the `have` line, so the outcome tracks the claim."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-outer-zero-hops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OUTER_ZERO,
        "refinement": (
            "carrying an existing outer-query reference into the deeper subquery "
            "UNCHANGED (zero extra outward hops) is what a real patch that omitted the "
            "new outer-reference re-anchor branch would do — the reference then resolves "
            "one level too shallow, onto the freshly generated inner subquery instead of "
            "the query the condition came from. The F2P test pins exactly an outer-"
            "reference right-hand side and asserts it still resolves against the intended "
            "outer query; this rival returns the wrong rows and the test FAILS. A faithful "
            "patch of this shape does NOT resolve; a verifying rival is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause C2 (re-anchor), outerRef arm. The spec demands "
            "`reanchor (outerRef lvl name) = outerRef (lvl+1) name`, but the rival returns "
            "the reference unchanged. Witness probes the outerRef sub-domain. If it "
            "VERIFIES => SPEC-TOO-WEAK (the one-further-level hop on an existing outer "
            "reference is unpinned)."
        ),
        # outerRef 2 "pk": gold -> outerRef 3 "pk"; rival -> outerRef 2 "pk" (unchanged).
        "witness": _wit('"c"', '(FilterRHS.outerRef 2 "pk")',
                        "outer-query reference: gold reaches out one further level, "
                        "rival leaves it unchanged"),
    },
    {
        "id": "weak-local-zero-hops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LOCAL_ZERO,
        "refinement": (
            "leaving a same-query column reference UNCHANGED is what a real patch that "
            "dropped the column-reference re-anchor branch would do — the bare reference, "
            "once pushed one boundary deeper, denotes a column of the inner subquery "
            "instead of the query the condition came from, so a negated filter with a "
            "local field right-hand side over a one-to-many relation matches the wrong "
            "rows. This regresses the pre-existing column-reference re-anchoring "
            "behaviour. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (re-anchor), colRef arm. The spec demands "
            "`reanchor (colRef name) = outerRef 1 name`, but the rival returns the "
            "column reference unchanged. Witness probes the colRef sub-domain. If it "
            "VERIFIES => SPEC-TOO-WEAK (the level-one re-anchor of a same-query reference "
            "is unpinned)."
        ),
        # colRef "name": gold -> outerRef 1 "name"; rival -> colRef "name" (unchanged).
        "witness": _wit('"c"', '(FilterRHS.colRef "name")',
                        "same-query column reference: gold re-anchors to a level-one "
                        "outer reference, rival leaves it unchanged"),
    },
    {
        "id": "weak-value-one-hop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_VALUE_HOP,
        "refinement": (
            "wrapping a plain literal as an outer-query reference is what a real patch "
            "that let a rewrite branch fire on a direct value would do — a literal has no "
            "query reference to re-anchor, so turning it into a (broken) outer reference "
            "makes a negated filter with a literal right-hand side over a one-to-many "
            "relation crash or return wrong rows. The desired behaviour leaves a literal "
            "untouched (no rewrite branch fires); this regresses the common literal path. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (re-anchor), value arm. The spec demands "
            "`reanchor (value v) = value v` (literal unchanged), but the rival returns an "
            "outer reference. Witness probes the value sub-domain. If it VERIFIES => "
            "SPEC-TOO-WEAK (the no-op on a literal is unpinned)."
        ),
        # value 7: gold -> value 7; rival -> outerRef 1 "0" (spurious wrap).
        "witness": _wit('"c"', '(FilterRHS.value 7)',
                        "direct literal: gold leaves it unchanged, rival wraps it as a "
                        "spurious outer reference"),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "this IS the base_commit behaviour: an existing outer-query reference is "
            "rebuilt at level ONE, DISCARDING the level it already carried, because at "
            "base_commit the outer-reference case falls through the same-query-column "
            "branch (an outer reference is a subclass of a column reference) and is "
            "rebuilt from its name alone. Its faithful real patch is the UNCHANGED repo, "
            "where the relocated reference reaches out only one level when it must reach "
            "out two (a new boundary now sits between it and its target) — exactly the "
            "failure the issue reports (the reference resolves against the wrong query). "
            "Does NOT resolve. Near-miss to weak-outer-zero-hops (both mishandle the "
            "outerRef arm) but distinguished on any level>=2 reference: this rival "
            "collapses to level one, the zero-hop rival leaves the level untouched."
        ),
        "rationale": (
            "REJECTED by clause C2 (re-anchor), outerRef arm. The spec demands "
            "`reanchor (outerRef lvl name) = outerRef (lvl+1) name`, but the rival returns "
            "`outerRef 1 name`, dropping the carried level. Witness sits at a level>=2 "
            "reference, where it and the zero-hop rival DISAGREE, so the two near-miss "
            "rivals are demonstrated distinct. If it VERIFIES => SPEC-TOO-WEAK (the "
            "level-preserving increment on an existing outer reference is unpinned)."
        ),
        # outerRef 3 "job": gold -> outerRef 4 "job"; rival -> outerRef 1 "job".
        "witness": _wit('"d"', '(FilterRHS.outerRef 3 "job")',
                        "deep outer-query reference (level 3): gold increments to level 4, "
                        "pre-patch rival collapses to level 1"),
    },
    {
        "id": "weak-name-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NAME_DROP,
        "refinement": (
            "gets the outward-hop arithmetic right on BOTH reference arms but rebuilds "
            "the re-anchored reference with an empty column name, so it reaches the "
            "correct query and then names no column there. A real patch of this shape "
            "carries the nesting level across the new boundary while losing the "
            "identifier the reference was built from, so the relocated condition "
            "compares against nothing and the negated filter over the one-to-many "
            "relation matches wrong rows (or errors on an unknown column). Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (re-anchor) on the NAME payload rather than the level. "
            "The spec demands `reanchor (colRef name) = outerRef 1 name` and "
            "`reanchor (outerRef lvl name) = outerRef (lvl+1) name` — the name is pinned "
            "in both, not just the level. Every other rival here varies a level, a "
            "literal, or the lhs, so this is the only case that probes the name "
            "component; without it, a spec that pinned only the levels would pass the "
            "battery. If it VERIFIES => SPEC-TOO-WEAK (the column identity carried by a "
            "re-anchored reference is unpinned)."
        ),
        # colRef "pk": gold -> outerRef 1 "pk"; rival -> outerRef 1 "" (name dropped).
        "witness": _wit('"c"', '(FilterRHS.colRef "pk")',
                        "named column reference: gold preserves the column name across "
                        "the re-anchor, rival empties it"),
    },
    {
        "id": "weak-value-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_VALUE_PAYLOAD,
        "refinement": (
            "keeps a literal right-hand side a LITERAL (the shape is right, so this is not "
            "the spurious-reference-wrap failure) but hands the deeper query a DIFFERENT "
            "constant than the caller supplied. Its faithful real patch routes the relocated "
            "literal through a value coercion that does not round-trip on the way into the "
            "nested subquery, so the relocated condition compares against the wrong "
            "constant: a negated filter with a literal right-hand side over a one-to-many "
            "relation matches the wrong rows. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (re-anchor), value arm, on the PAYLOAD rather than the "
            "shape. The spec demands `reanchor (value v) = value v` — the literal itself is "
            "pinned, not merely its shape. Every other rival varies a nesting level, a "
            "column name, or the lhs, so without this case a spec that pinned only "
            "\"a literal stays some literal\" would pass the battery. If it VERIFIES => "
            "SPEC-TOO-WEAK (the carried constant is unpinned)."
        ),
        # value 42: gold -> value 42; rival -> value 43 (payload perturbed).
        "witness": _wit('"c"', '(FilterRHS.value 42)',
                        "direct literal: gold carries the constant through unchanged, "
                        "rival hands the inner query a different constant"),
    },
    {
        "id": "weak-lhs-mangled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LHS,
        "refinement": (
            "re-anchors the right-hand side correctly on every shape (clause C2 holds) "
            "but drops the left-hand side of the relocated condition, returning an empty "
            "name instead of carrying it through. Its faithful real patch mutates or "
            "discards `filter_lhs` while relocating the condition, so the rebuilt filter "
            "targets the wrong column and the negated filter matches wrong rows. The "
            "desired behaviour leaves the left-hand side untouched by the relocation. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (the FRAME). The spec demands `result.1 = lhs` — the "
            "left-hand side carried through untouched — but the rival returns the empty "
            "string. Witness varies the `lhs` BINDER at a non-empty name so the two "
            "left-hand sides differ; this is the referentially-transparent analogue of a "
            "read-only-input frame violation. If it VERIFIES => SPEC-TOO-WEAK (the "
            "left-hand side is unconstrained — an output-frame hole)."
        ),
        # lhs "q": gold -> ("q", value 0); rival -> ("", value 0) — C1 differs.
        "witness": _wit('"q"', '(FilterRHS.value 0)',
                        "non-empty left-hand side: gold carries it through, rival drops "
                        "it to the empty string"),
    },
]


# No @ContractOnly axioms and no opaque callees: the re-anchoring (the 3-way shape
# dispatch and the level adjustment) is modeled DEEPLY over a transparent carrier, so
# the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
