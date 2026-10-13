# properties.py — G-PBT falsification battery for django__django-10097 (lean lane).
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
#   urlUserinfoValid : List Char → Bool
#   The acceptance predicate for the credentials segment that precedes the `@` of a
#   URL authority. The single postcondition pins the result to the exact verdict of
#   a four-clause decision, each clause grounded in the input list of characters:
#     (1) the segment is NON-EMPTY;
#     (2) it does NOT begin with a colon (the leading user run is mandatory);
#     (3) it carries AT MOST ONE colon (the single user/password separator);
#     (4) every character is ADMISSIBLE — neither whitespace nor one of the reserved
#         delimiters `:` `@` `/` — with the single separator colon permitted.
#   The oracle is a total, transparent fold over the input (no opaque callee, no
#   answer-key), so `decide` computes it at any literal input — witnesses need no
#   conditioning on the carrier.
#
# CARRIER NOTE: the nagini sibling abstracted the same decision to a fold over a
# `List[int]` of code points behind fractional read permission. This backend models
# the identical decision over a transparent `List Char`, so every clause the nagini
# battery attacked has a direct counterpart here, and each is refutable at a concrete
# literal input.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's #1 class: the segment was Acc(list_pred(seg),1/2)
#     read-only, and the rival wrote back into it). Lean is referentially
#     transparent — no aliasing, no fractional permission — so a "store into a
#     read-only input" rival is not expressible and the whole lane is VACUOUS here.
#     See 'assessment'.
#   * ADMISSIBILITY — the port originally recorded this lane N/A because the lean
#     obligation `∀ (s : List Char), problem_spec … (implementation … s)` carries no
#     precondition hypothesis. That reason was WRONG (corrected in audit): the
#     analogue on a total carrier is not "is the precondition satisfiable" but "is
#     the obligation SATISFIABLE at an F2P-shaped input", which a positive that
#     discharges `problem_spec` at concrete points BY EVALUATION — as `have`s,
#     before closing the frozen obligation verbatim — tests directly. The lane is
#     expressible here and is now carried by `admiss-f2p-points` below.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them (the changed
#     matcher is modeled DEEPLY, so there is no consumed axiom anyway).
from pathlib import Path

INSTANCE = "django__django-10097"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). One per decision clause. ------------------------------------
_C_EMPTY = "  if s.isEmpty then return false\n"
_C_LEAD = "  if s.head? == some ':' then return false\n"
_C_COLON = "  if !Nat.ble (s.count ':') 1 then return false\n"
_C_ADMIS = "  if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false\n"
for _a in (_C_EMPTY, _C_LEAD, _C_COLON, _C_ADMIS):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"

# The frozen impl body (all four guards + the final `return true`) — used to swap in
# the direct-oracle positive.
_IMPL_BODY = (
    "  if s.isEmpty then return false\n"
    "  if s.head? == some ':' then return false\n"
    "  if !Nat.ble (s.count ':') 1 then return false\n"
    "  if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false\n"
    "  return true"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl body anchor drifted"

# The frozen proof body (only the tactic lines, inside proof-start/proof-end).
_PROOF = (
    "  intro s\n"
    "  unfold problem_spec_urlUserinfoValid implementation_urlUserinfoValid urlUserinfoValid\n"
    "  simp only [Id.run, bind, pure]"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reorder: structurally DIFFERENT but behaviourally identical. The at-most-one-
# colon guard and the all-admissible guard are COMMUTED. Both are independent
# rejections that fire before `return true`, so the result value is identical on
# every input; only the branch FORM changes — the shape a faithful patch could
# equally take. The frozen `rfl`-style `simp only` proof no longer closes the
# commuted branch tree, so the proof body is re-closed with `grind` (a genuine
# reproof, NOT a weakening: the theorem STATEMENT is byte-identical and no new
# axiom/lemma/sorry is introduced). If it FAILS => SPEC-TOO-STRONG (a faithful,
# structurally-different correct impl rejected because the postcondition is over-fit
# to one branch order).
_POS_REORDER = _swap(
    _swap(
        _BASE, _C_COLON + _C_ADMIS,
        _C_ADMIS + _C_COLON,
    ),
    _PROOF,
    "  intro s\n"
    "  unfold problem_spec_urlUserinfoValid implementation_urlUserinfoValid urlUserinfoValid\n"
    "  simp only [Id.run, bind, pure]\n"
    "  grind",
)

# pos-direct: the cheapest HONEST impl. The postcondition oracle `urlUserinfoValid`
# is GROUNDED in the argument (a total transparent fold), so directly returning it
# is a fully-grounded correct implementation, not an ungrounded-oracle echo — there
# is no WRONG constant/echo to build here (a wrong constant fails the postcondition).
# The proof collapses to `rfl` after unfolding. MUST verify (the postcondition is
# literally `result = urlUserinfoValid s`); else SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _swap(
        _BASE, _IMPL_BODY,
        "  urlUserinfoValid s",
    ),
    _PROOF,
    "  intro s\n"
    "  unfold problem_spec_urlUserinfoValid implementation_urlUserinfoValid\n"
    "  rfl",
)

# admiss-f2p-points: the ADMISSIBILITY lane, landed in audit (the port had recorded
# it N/A for the wrong reason — see the header note). On a total carrier with no
# precondition, the analogue of PRECOND-TOO-STRONG is the obligation being
# UNSATISFIABLE at an F2P-shaped input: a spec that no admissible segment can
# satisfy positively, or that cannot refuse a genuinely inadmissible one, is
# unusable no matter how many rivals it rejects. So the impl discharges
# `problem_spec_urlUserinfoValid` at two concrete F2P-shaped points BY EVALUATION,
# as `have`s, before running the frozen body and closing the frozen obligation
# verbatim:
#   * a normal `user:password` credentials segment, which must be ADMITTED (true);
#   * a segment carrying a reserved delimiter, which must be REFUSED (false).
# These are the postcondition itself applied at those points, not a definitional
# identity — the tautology trap that has bitten sibling cells (`some 511 = some
# 511`). Verified as discriminating: flipping EITHER expected verdict makes the
# `have` fail with `decide` reporting the flipped equation false, so each one
# measures the spec's verdict at that input rather than restating it. Proof body
# and every clause of the impl are otherwise byte-identical to the frozen file, so
# the only thing this case can fail on is the obligation being unsatisfiable at a
# shape the fix must handle => PRECOND-TOO-STRONG / spec-shape regression.
_POS_ADMISS = _swap(
    _BASE, _C_EMPTY,
    "  have _hAdmit : problem_spec_urlUserinfoValid"
    " ['f', 'o', 'o', ':', 'b', 'a', 'r'] true := by\n"
    "    unfold problem_spec_urlUserinfoValid; decide\n"
    "  have _hRefuse : problem_spec_urlUserinfoValid"
    " ['f', 'o', 'o', '/', 'b', 'a', 'r'] false := by\n"
    "    unfold problem_spec_urlUserinfoValid; decide\n"
    + _C_EMPTY,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness that
# elaborates against the rival and FAILS on the frozen solution.
# ===========================================================================

# Each rival drops (or widens) exactly ONE decision clause, leaving the frozen proof
# body in place — that proof will not close for the reshaped impl, but the gate does
# not read the rival's own build for a reject case; it reads the witness, which is
# checked in a file with the obligation removed.
_RIV_EMPTY = _swap(_BASE, _C_EMPTY, "")
_RIV_LEAD = _swap(_BASE, _C_LEAD, "")
_RIV_COLON = _swap(_BASE, _C_COLON, "")
# whitespace-only admissibility: the EXACT pre-change character class (only
# whitespace excluded, `@`/`/`/second-`:` admitted). `s.all (fun c => c == ':' ||
# ...)`-shaped guard is replaced by one that rejects ONLY whitespace.
_RIV_WS = _swap(
    _BASE, _C_ADMIS,
    "  if !(s.all (fun c => !isUserinfoWhitespace c)) then return false\n",
)
# narrow-whitespace admissibility: keeps all four clauses and the full delimiter
# exclusion, but spells the whitespace side with Lean's own `Char.isWhitespace`,
# which covers only 4 of the 29 code points the admissible-character clause
# excludes. Added in audit: the four rivals above all attack the STRUCTURAL
# clauses (1)-(4) or the delimiter half of clause (4); none touched the
# whitespace half, so the 29-code-point enumeration was the least-probed part of
# the spec. Diverges from the frozen verdict at every one of the 25 code points
# Lean's predicate misses (NBSP U+00A0 below).
_RIV_NARROW_WS = _swap(
    _BASE, _C_ADMIS,
    "  if !(s.all (fun c => (!c.isWhitespace && c != ':' && c != '@' && c != '/')"
    " || c == ':')) then return false\n",
)


def _wit(chars, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal input, closed by `decide`. `chars` is the Lean List Char literal.
    Elaborates against a rival that diverges from the frozen verdict there, and fails
    on gold (which satisfies the spec at every input)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_urlUserinfoValid {chars}\n"
        f"    (implementation_urlUserinfoValid {chars}) := by\n"
        f"  unfold problem_spec_urlUserinfoValid implementation_urlUserinfoValid\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the at-most-one-colon guard "
            "and the all-admissible guard are COMMUTED. Both are independent early "
            "rejections firing before the accept, so the verdict is identical on "
            "every input; only the branch order changes. The frozen `theorem "
            "correct_urlUserinfoValid` statement is kept byte-identical and the proof "
            "body is honestly re-closed with `grind` (no new axiom/lemma/sorry). If "
            "it FAILS => SPEC-TOO-STRONG (postcondition over-fit to one branch order)."
        ),
    },
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition oracle urlUserinfoValid is GROUNDED in the argument (a "
            "total transparent fold), so `implementation := urlUserinfoValid s` is the "
            "honest cheapest CORRECT impl, not an ungrounded echo; the proof collapses "
            "to `rfl`. Must verify (postcondition is literally result = "
            "urlUserinfoValid s); else SPEC-TOO-STRONG. Also shows the spec is not "
            "echo-vulnerable: any WRONG constant fails the postcondition."
        ),
    },
    {
        "id": "admiss-f2p-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "the ADMISSIBILITY lane. With no precondition hypothesis on this total "
            "carrier, PRECOND-TOO-STRONG appears as the obligation being "
            "UNSATISFIABLE at an F2P-shaped input, so the impl discharges "
            "problem_spec_urlUserinfoValid at two concrete points by EVALUATION, as "
            "`have`s, before closing the frozen obligation verbatim: a normal "
            "user:password segment that must be ADMITTED, and a segment carrying a "
            "reserved delimiter that must be REFUSED. Both apply the postcondition "
            "itself at that input, so neither is a definitional tautology — flipping "
            "either expected verdict makes its `have` fail. If it FAILS => "
            "PRECOND-TOO-STRONG (the spec cannot be satisfied at a shape the change "
            "must handle) or a spec-shape regression."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-drop-empty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTY,
        "refinement": (
            "dropping the non-empty clause accepts the EMPTY segment. Its faithful "
            "real counterpart is a credentials matcher whose leading user run is `*` "
            "rather than `+`, which would accept an authority with an empty userinfo "
            "before the `@`. The narrowed group makes the leading run mandatory "
            "(`+`), so a matcher that accepts the empty run diverges from the "
            "post-change validator on exactly that sub-domain. SCOPE OF THE CLAIM "
            "(measured in audit against the real fixture lists, correcting an "
            "earlier overclaim): this divergence is NOT exercised by any shipped "
            "fixture — no fixture carries an empty userinfo — so a patch of this "
            "shape still passes the test suite and this case does NOT establish "
            "verify-does-not-imply-resolve. What it does establish is that the "
            "SPEC pins the clause the change's `+` quantifier states, over its whole "
            "domain rather than only where the fixtures happen to look. That is the "
            "spec-strength property this gate exists to test; a verifying rival here "
            "would mean the non-empty clause is unpinned."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins the result of the empty segment "
            "to false (non-empty clause). Attacks the non-empty clause / the s.isEmpty "
            "sub-domain of the single binder s. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # []: gold => false, rival (empty guard dropped) => true.
        "witness": _wit("[]", "empty segment: gold rejects, rival accepts"),
    },
    {
        "id": "weak-drop-leading-colon-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LEAD,
        "refinement": (
            "dropping the leading-colon clause accepts a segment with an EMPTY user "
            "run, e.g. \":pass\" or \":\". The narrowed credentials group requires a "
            "non-empty user run before the optional `:` separator, so it rejects a "
            "leading colon; a matcher that accepts it would admit URLs like "
            "http://:pass@example.com that the post-change validator must reject. "
            "SCOPE OF THE CLAIM (measured in audit against the real fixture lists, "
            "correcting an earlier overclaim): no shipped fixture carries a "
            "leading-colon userinfo, so a patch of this shape still passes the test "
            "suite and this case does NOT establish verify-does-not-imply-resolve. "
            "What it establishes is that the SPEC pins the mandatory-user-run clause "
            "over its whole domain and not merely where the fixtures probe — the "
            "spec-strength property this gate tests. Contrast "
            "weak-drop-colon-count-guard and weak-whitespace-only-class below, whose "
            "divergences ARE fixture-visible and which therefore do carry a genuine "
            "verify-does-not-imply-resolve claim."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins a segment beginning with ':' to "
            "false (leading-colon clause). Attacks the no-leading-colon clause / the "
            "s.head? == some ':' sub-domain. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # [':']: gold => false (leading colon), rival (leading guard dropped) => true.
        "witness": _wit("[':']", "leading colon: gold rejects, rival accepts"),
    },
    {
        "id": "weak-drop-colon-count-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_COLON,
        "refinement": (
            "dropping the at-most-one-colon clause accepts a segment with TWO OR MORE "
            "colons, e.g. \"a:b:c\". This is the pre-change behaviour for multiple "
            "colons: the narrowed group permits only one optional `:` separator, so it "
            "rejects a second colon. A matcher without this restriction still accepts "
            "http://a:b:c@example.com and does NOT resolve — verify-does-not-imply-"
            "resolve. CONFIRMED in audit by running both matchers embedded in the full "
            "authority pattern over the actual post-change fixture lists: the "
            "two-colon credentials URL is newly listed as invalid and this rival "
            "accepts it, so a patch of this shape fails the suite. One "
            "fixture-visible divergence."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins a segment with >=2 colons to "
            "false (at-most-one-colon clause). Attacks the s.count ':' <= 1 clause / "
            "the multi-colon sub-domain. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # ['a',':','b',':','c']: two colons; gold => false, rival => true.
        "witness": _wit("['a', ':', 'b', ':', 'c']",
                        "two colons: gold rejects, rival accepts"),
    },
    {
        "id": "weak-whitespace-only-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WS,
        "refinement": (
            "widening the admissible-character clause to exclude ONLY whitespace is "
            "the EXACT pre-change character class: `@` and `/` are treated as "
            "acceptable inside the segment. The narrowed class additionally excludes "
            "the reserved delimiters `:` `@` `/`, so it rejects a segment containing "
            "`/` or `@`. A matcher keeping the whitespace-only class still accepts "
            "http://a/b@example.com and http://a@b@example.com and does NOT resolve — "
            "verify-does-not-imply-resolve. CONFIRMED in audit by running both "
            "matchers embedded in the full authority pattern over the actual "
            "post-change fixture lists: this rival diverges from the frozen verdict on "
            "SIX fixtures, every one of them a URL newly listed as invalid that the "
            "rival accepts. The strongest resolve-linked rival in this battery."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins a segment containing '/' (or "
            "'@') to false (admissible-character clause: every non-separator character "
            "must be admissible, and '/'/'@' are not). Attacks the "
            "s.all isUserinfoChar clause / the delimiter-inside-segment sub-domain. If "
            "it VERIFIES => SPEC-TOO-WEAK (the narrowing to [^\\s:@/] would be hollow)."
        ),
        # ['a','/','b']: contains '/'; gold => false, rival (whitespace-only) => true.
        "witness": _wit("['a', '/', 'b']",
                        "embedded '/': gold rejects, rival accepts"),
    },
    {
        "id": "weak-narrow-whitespace-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NARROW_WS,
        "refinement": (
            "the admissible-character clause excludes whitespace as the real engine "
            "understands it — 29 code points over Unicode text — and the frozen spec "
            "enumerates them. This rival keeps all four structural clauses AND the "
            "full `:`/`@`/`/` exclusion, and weakens only the WHITESPACE side, to the "
            "4 code points Lean's own `Char.isWhitespace` recognises. It therefore "
            "accepts a credentials segment containing any of the other 25 — NBSP, the "
            "fixed-width spaces, IDEOGRAPHIC SPACE — which the character class must "
            "reject. SCOPE OF THE CLAIM, measured in audit rather than asserted: no "
            "shipped fixture carries a non-ASCII-whitespace credentials segment, so "
            "this rival passes the test suite and the case does NOT claim "
            "verify-does-not-imply-resolve. It is a pure SPEC-STRENGTH probe, and the "
            "reason it is here is that the other four rivals attack only the "
            "structural clauses and the delimiter half of the character class: the "
            "29-code-point enumeration was the single least-probed part of the frozen "
            "spec, and an unpinned whitespace class is exactly how a matcher that "
            "looks narrowed silently keeps admitting Unicode-space credentials."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins a segment containing NBSP "
            "(U+00A0) to false: NBSP is in the spec's whitespace class, so it is not "
            "an admissible character, while `Char.isWhitespace` does not recognise it "
            "and the rival accepts. Attacks the whitespace half of the "
            "admissible-character clause — the sub-domain no other rival reaches. If "
            "it VERIFIES => SPEC-TOO-WEAK (the whitespace enumeration would be "
            "decorative, and the class would collapse to ASCII)."
        ),
        # ['a', NBSP, 'b']: gold => false (NBSP is whitespace), rival => true.
        "witness": _wit("['a', ' ', 'b']",
                        "NBSP inside the segment: gold rejects, rival accepts"),
    },
]


# No @ContractOnly axioms and no opaque callees: the character-admissibility test
# and the single-separator structure are modeled DEEPLY over the transparent
# List Char carrier, so the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
