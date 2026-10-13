"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7324 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant produced by region surgery that touches ONLY the
``-- impl-start`` / ``-- impl-end`` region and — for a case that legitimately
re-proves — the ``-- proof-start`` / ``-- proof-end`` region. So
``markers.same_spec`` holds by construction, the single
``theorem correct_resolveIdent`` STATEMENT stays byte-identical, and no case
introduces a new ``axiom`` / ``theorem`` / ``lemma`` or any of
``sorry`` / ``admit`` / ``native_decide``.

``expect:"verify"`` passes iff the variant is in scope AND elaborates with the
obligation closed. ``expect:"reject"`` passes iff the variant is in scope AND
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh
invention. The nagini bundle splits the behavior across TWO contracted
functions over a ``List[int]`` code-point carrier — one that builds the
name-node identifier from the match-expression identifier, one that recovers
the match-expression identifier from the name-node identifier and consults the
membership predicate — and pins each with its own whole-sequence postcondition.
This Lean bundle models the SAME behavior as ONE end-to-end obligation over a
``List Char`` / ``List Char → Bool`` carrier: resolving a single identifier
against a matcher. So the nagini per-site cases COMPOSE onto one obligation
here (carrier narrowing — see the accounting block at the bottom), and case
count is deliberately not matched.

DEFENDED SURFACE (one modeled behavior, one top-level clause).
``problem_spec_resolveIdent name matcher result`` pins EXACTLY

    result = some (matcher name)

which is a single equation carrying TWO independent demands, and every rival
below attacks one of them:

  * (D1 totality) the result is ``some _`` — never the abort outcome. For EVERY
    identifier, including ones spelled like the reserved constants. Attacked by
    ``weak-no-prefix``, ``weak-strip-no-attach``, ``weak-partial-none`` and
    ``weak-partial-false``.
  * (D2 verdict) the boolean is ``matcher`` applied to ``name`` VERBATIM — not
    to a transformed identifier and not to a constant. Attacked by
    ``weak-no-strip``, ``weak-over-strip``, ``weak-first-char-prefix`` and
    ``weak-const-verdict``.

BINDER STRUCTURE. The predicate has TWO input binders, ``name`` (the identifier)
and ``matcher`` (the verdict function), and both are load-bearing. Both are
varied by the reject witnesses: the eight witnesses probe eight DISTINCT
``(name, matcher)`` points (``pts=8``), with ``name`` ranging over each of the
three reserved spellings, a one-character identifier, two-, four- and
five-character ordinary identifiers, and ``matcher`` ranging over a constant
verdict function and four different identifier-specific verdict functions. No
binder is held at a single value, and in particular no witness leaves ``matcher`` constant while
attacking D2 — a rival that mishandled only the argument passed to ``matcher``
is invisible to a constant matcher, so pinning ``matcher`` there would have made
the four D2 rivals unrefutable in principle.

WHY THE SPEC IS NOT ECHO-VULNERABLE (the argument carried from the nagini
sibling). ``matcher`` is a universally-quantified FREE PARAMETER of the
obligation, not an axiomatized oracle, and its ARGUMENT is grounded: the spec
demands ``matcher name`` for the very ``name`` the caller supplied. So an
implementation cannot satisfy the clause by echoing an answer key — it has to
apply the caller's own verdict function to the caller's own identifier, after
whatever transformation it performs has been undone exactly. That is why the
whole wrong-ARGUMENT family (``weak-no-strip``, ``weak-over-strip``,
``weak-first-char-prefix``) is refutable at a concrete point: instantiate
``matcher`` at a function that distinguishes the two identifiers.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's two mandatory
    probes write to a read-only input to satisfy the pin vacuously, and are
    rejected by its fractional-permission system. Lean is referentially
    transparent: ``name`` and ``matcher`` are immutable values, there is no
    aliasing, no ``mut`` input binder and no read-only cell to overwrite, so
    the class cannot be expressed. No substitute probe is fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS HERE (and only here).
    ``implementation_resolveIdent`` is a total Lean ``def``, so a diverging
    implementation cannot be written at all; the obligation is a plain
    equation, not a partial-correctness triple, so there is no vacuous-exit
    hole to probe. (Note this disposition is specific to lean: on a velvet
    bundle under ``loom.semantics.termination "partial"`` the same class is a
    KNOWN SPEC HOLE rather than vacuous — ``the corpus-wide termination-semantics finding``. The
    nagini sibling carries no divergence case either.)

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the port's weight sits.
    Rivals correct on part of the domain and wrong where the fix bites: the
    pre-fix behavior itself; a residual abort on exactly one reserved
    spelling (twice, at two DIFFERENT spellings); a transformation applied on
    one side only; and off-by-one and constant-substitution errors in the
    recovered identifier.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet that states the NEGATION of the spec
predicate at one concrete ``(name, matcher)`` point and closes by ``decide``
after unfolding. Every input is a ground literal and every matcher a closed
lambda, so each witness binds NOTHING in its head and there are no hypotheses
whose joint satisfiability could be in question (no conditioning on an opaque
term is needed: this carrier computes). Each of the eight was checked with two
real ``lean_verify.sh`` builds — HOLDS of its rival, FAILS on the frozen
solution — so it discriminates rather than asserting a tautology. On the frozen
solution every one fails with ``decide`` PROVING the negated spec false, i.e. a
positive computation that gold satisfies the clause at that very point, which is
the strongest available form of gold-side failure (not an unknown identifier, a
stuck reduction, or a timeout).

REFINEMENT. Each reject case's ``refinement`` argues that its faithful real
counterpart would NOT resolve the F2P tests, which pass an identifier through
the whole resolve path and assert the matcher's verdict on that identifier
comes back — including for the three identifiers spelled like the reserved
constants. A rival that verified would therefore be a genuine
verify-does-not-imply-resolve break, not an artifact.

AXIOM lane: EMPTY. This bundle declares no ``opaque`` callee and consumes no
``axiom`` (the finite reserved-constant set and the two prefix operations are
modeled deeply as A-references). The nagini ``AXIOM_TESTS`` is also empty, and
the axiom lane belongs to G-AX regardless, so it is dropped.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7324"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Every one lies wholly inside `-- impl-start`/`-- impl-end`
# (the `_I_*` group) or wholly inside `-- proof-start`/`-- proof-end` (the
# `_P_*` group), and each is unique in the frozen file — asserted at load, so a
# future edit to Solution.lean breaks this manifest loudly instead of silently
# producing a variant that edits the wrong region.
# ---------------------------------------------------------------------------
_I_PREFIX = "def identPrefix : List Char := ['$']"
_I_KEY = "  let key := identPrefix ++ name"
_I_GUARD = "  if isReservedConst key then"
_I_RET = "  return some (matcher (key.drop identPrefix.length))"
_I_SIG = """    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
  -- build the name node's identifier from the match-expression identifier
  let key := identPrefix ++ name
  -- compiling the name node aborts if its identifier is a reserved constant
  if isReservedConst key then
    return none
  -- consult the matcher with the identifier recovered from the name node
  return some (matcher (key.drop identPrefix.length))"""

_P_INTRO = "  intro name matcher"
_P_TAIL = """  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
  rw [if_neg]
  · rfl
  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
      Bool.false_eq_true, not_false_eq_true]"""


def _w(name, matcher):
    """A refutation witness: the spec predicate FAILS at this concrete point.

    Ground literals only, so the head binds nothing and the hypothesis-
    consistency question does not arise. `decide` closes it because both the
    identifier and the verdict function are closed computable terms.
    """
    return (f"example : ¬ problem_spec_resolveIdent {name} ({matcher})\n"
            f"    (implementation_resolveIdent {name} ({matcher})) := by\n"
            "  unfold problem_spec_resolveIdent\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_resolveIdent` STATEMENT byte-identical and adds no
    # declaration.
    # =====================================================================
    {
        "id": "pos-let-recovered",
        "kind": "soundness",
        "expect": "verify",
        # Bind the recovered identifier to a named local before consulting the
        # matcher, instead of consulting it on an inline expression. Same value
        # on every input, different data-flow shape. Definitionally identical to
        # the frozen body, so the frozen proof still closes with no authoring.
        # (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_I_KEY, _I_KEY + "\n  let recovered := key.drop identPrefix.length"),
            (_I_RET, "  return some (matcher recovered)"),
        ),
        "rationale": "correct reshape: the recovered identifier is bound to a named "
                     "local and the matcher is consulted on that local rather than on "
                     "an inline expression. It computes the same result on every "
                     "(name, matcher) pair, so the single clause `result = some "
                     "(matcher name)` still holds — if this failed, the spec would be "
                     "over-fit to the inline form => SPEC-TOO-STRONG. Definitionally "
                     "the frozen body, so the frozen proof closes unchanged; statement "
                     "byte-identical, no new axiom/lemma. Ports the nagini "
                     "pos-encode-local / pos-lookup-local pair (there: read the "
                     "element into a local `ch` before appending; both sibling cases "
                     "compose onto this bundle's single obligation).",
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        # Drop the monadic `Id.run do` / early-`return` shape entirely and write
        # the same behavior as a pure `let` + `if/then/else` expression. This is
        # the honest CHEAPEST-implementation control: the clause is grounded in
        # the two input binders, so even the cheapest shape that satisfies it
        # must apply the caller's own matcher to the caller's own identifier.
        # Re-proved: the same rewrite chain closes, minus the `rfl` step that
        # existed only to strip the `do`-block's unit bind. (Verified: real
        # build.)
        "module": _swaps(
            _BASE,
            (_I_SIG, """    (name : List Char) (matcher : List Char → Bool) : Option Bool :=
  -- build the name node's identifier from the match-expression identifier
  let key := identPrefix ++ name
  -- compiling the name node aborts if its identifier is a reserved constant
  if isReservedConst key then none
  -- consult the matcher with the identifier recovered from the name node
  else some (matcher (key.drop identPrefix.length))"""),
            (_P_TAIL, """  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
  rw [if_neg]
  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
      Bool.false_eq_true, not_false_eq_true]"""),
        ),
        "rationale": "correct reshape from the monadic early-return shape to a pure "
                     "`let` + if/then/else expression — same values, different "
                     "control-flow encoding. A faithful reshape MUST verify, else "
                     "SPEC-TOO-STRONG. Doubles as the honest cheapest-impl control "
                     "showing the clause is GROUNDED, not an oracle echo: `matcher` is "
                     "a free parameter and its argument is pinned to `name`, so even "
                     "the cheapest satisfying shape has to apply the caller's verdict "
                     "function to the caller's identifier. Re-proved by dropping the "
                     "`rfl` step that only stripped the do-block's unit bind; "
                     "statement byte-identical, no new axiom/lemma. Ports the nagini "
                     "pos-encode-assert-grounded control.",
    },
    {
        "id": "pos-alt-prefix",
        "kind": "soundness",
        "expect": "verify",
        # Use a DIFFERENT prefix character. Any prefix that cannot make the
        # name node collide with a reserved constant implements the modeled
        # behavior; the spec must not be over-fit to one particular character.
        # The frozen proof unfolds `identPrefix` and discharges the guard by
        # literal disequality, so it closes for the new character too.
        # (Verified: real build.)
        "module": _swap(_BASE, _I_PREFIX, "def identPrefix : List Char := ['#']"),
        "rationale": "correct variant using a DIFFERENT prefix character. The modeled "
                     "behavior is insensitive to which character is attached, as long "
                     "as it cannot produce a reserved-constant collision and is "
                     "removed again before the matcher is consulted — so this must "
                     "verify. If it failed, the spec would be pinning an "
                     "implementation detail (a specific character) rather than the "
                     "observable input->output relation => SPEC-TOO-STRONG. The frozen "
                     "proof unfolds the prefix and discharges the guard by literal "
                     "disequality, so it closes unchanged; statement byte-identical, "
                     "no new axiom/lemma. Nagini has no counterpart (its sibling pins "
                     "the leading code point to a specific constant in the "
                     "postcondition, so an alternate prefix is genuinely rejected "
                     "THERE); ADDED here because this carrier's clause is stated "
                     "purely as an input->output relation and therefore admits it.",
    },
    {
        "id": "pos-conditional-prefix",
        "kind": "soundness",
        "expect": "verify",
        # Genuinely different control shape: attach the prefix ONLY for an
        # identifier that would collide, and correspondingly remove it only in
        # that case. Observationally identical to the frozen implementation on
        # every input, but the proof needs a real case split rather than a
        # single rewrite, so it is re-proved inside the proof region.
        # (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_I_KEY,
             "  let key := if isReservedConst name then identPrefix ++ name else name"),
            (_I_RET,
             "  return some (matcher (if isReservedConst name then "
             "key.drop identPrefix.length else key))"),
            (_P_TAIL,
             "  simp only [identPrefix, isReservedConst, Id.run]\n"
             "  split <;> simp_all [List.cons.injEq, pure, Id.instMonad]"),
        ),
        "rationale": "correct variant with a genuinely different control shape: the "
                     "prefix is attached only when the identifier would otherwise "
                     "collide, and removed only in that same case. Observationally "
                     "identical to the frozen implementation at every (name, matcher) "
                     "pair — the guard never fires and the matcher always sees `name` "
                     "verbatim — so the clause `result = some (matcher name)` holds and "
                     "it must verify, else SPEC-TOO-STRONG (over-fit to the "
                     "unconditional-transform shape). Re-proved with a case split on "
                     "the collision test instead of a single rewrite; statement "
                     "byte-identical, no new axiom/lemma. Re-expresses the nagini "
                     "structural-reshape positives on the composed obligation.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at a normal, F2P-shaped
    # input, i.e. the modeled behavior is not vacuously or accidentally
    # unreachable exactly where the tests probe it.
    # =====================================================================
    {
        "id": "admiss-reserved-ident",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen obligation carries NO precondition, so the nagini
        # precondition-admission self-calls re-express as: discharge the spec
        # predicate by evaluation at an F2P-shaped input — one of the three
        # identifiers spelled like a reserved constant, the exact inputs the
        # F2P tests add — as a `have`, then close the frozen obligation
        # verbatim. Nothing is assumed: no new declaration, the ground instance
        # is a `have` prepended inside the existing tactic body, and the
        # statement is byte-identical. (Verified: real build.)
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _f2p : problem_spec_resolveIdent ['T', 'r', 'u', 'e'] (fun _ => true)\n"
            "      (implementation_resolveIdent ['T', 'r', 'u', 'e'] (fun _ => true)) := by\n"
            "    unfold problem_spec_resolveIdent\n"
            "    decide\n" + _P_INTRO),
        "rationale": "the obligation is discharged by evaluation at an F2P-shaped "
                     "input — an identifier spelled exactly like one of the reserved "
                     "constants, which is precisely the input class the F2P tests add "
                     "— as a `have`, and then the frozen obligation is closed "
                     "verbatim. If this failed, the modeled behavior would be "
                     "unsatisfiable at exactly a normal test input (the analogue of "
                     "PRECOND-TOO-STRONG on a carrier whose obligation has no "
                     "precondition). Nothing is assumed: no new declaration, "
                     "statement byte-identical. Ports the nagini admiss-encode-"
                     "reserved and admiss-lookup-prefixed pair, which compose here "
                     "because the two sibling sites are one obligation and its "
                     "precondition surface is empty.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P,
    # and (b) a witness pinning the violation at one concrete input, checked to
    # hold of the rival and to FAIL on the frozen solution.
    # =====================================================================

    # ---- D1: the pre-fix behavior — no transformation at all ----
    {
        "id": "weak-no-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix behavior: the identifier is used verbatim as the name
        # node's identifier and consulted verbatim, so an identifier spelled
        # like a reserved constant makes the name node fail to compile and
        # resolution aborts.
        "module": _swaps(_BASE,
                         (_I_KEY, "  let key := name"),
                         (_I_RET, "  return some (matcher key)")),
        "refinement": "this IS the pre-fix behavior: no transformation is applied on "
                      "either side, so the three identifiers spelled like the reserved "
                      "boolean/none constants reach the compilation step unprotected "
                      "and resolution aborts instead of returning a verdict. The F2P "
                      "tests resolve exactly those identifiers and assert a boolean "
                      "comes back, so the faithful real counterpart aborts the "
                      "interpreter on them and would NOT resolve.",
        "rationale": "REJECT from D1 (totality): the spec pins `result = some (matcher "
                     "name)`, and in particular `some _`, but the rival yields the "
                     "abort outcome for a reserved spelling. Refuted at "
                     "name=['T','r','u','e'] with a constant-true matcher — the "
                     "smallest F2P-shaped input, where the rival returns the abort "
                     "outcome and the spec demands `some true`.",
        "witness": _w("['T', 'r', 'u', 'e']", "fun _ => true"),
    },

    # ---- D1: residual abort on exactly one reserved spelling (NEAR-MISS) ----
    {
        "id": "weak-partial-none",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: applies the transformation correctly and is gold on
        # every identifier EXCEPT one reserved spelling, which it still refuses.
        # This is the near-miss to `weak-no-prefix` — it agrees with gold over
        # strictly more of the domain — so it is refuted at the one input that
        # distinguishes it, not at `weak-no-prefix`'s point.
        "module": _swap(_BASE, _I_GUARD,
                        "  if isReservedConst key || name == ['N', 'o', 'n', 'e'] then"),
        "refinement": "a faithful real counterpart of this shape protects the name "
                      "node in general but keeps a residual rejection for one reserved "
                      "spelling, so resolving that one identifier still aborts instead "
                      "of returning a verdict. The F2P set covers each reserved "
                      "spelling as its own case, so the case for that spelling would "
                      "still fail — it would NOT resolve. This is exactly the "
                      "partial-fix shape that passes the pre-existing cases and leaves "
                      "one of the newly added ones broken.",
        "rationale": "REJECT from D1 (totality) on a PROPER SUB-DOMAIN: the rival is "
                     "gold at every identifier except one reserved spelling, where it "
                     "yields the abort outcome while the spec demands `some _`. "
                     "Refuted at name=['N','o','n','e'] — the input that distinguishes "
                     "it from weak-no-prefix, which handles ordinary identifiers "
                     "identically but fails at ALL THREE reserved spellings. Giving it "
                     "its own point is what makes the claimed sub-domain demonstrated "
                     "rather than asserted.",
        "witness": _w("['N', 'o', 'n', 'e']", "fun _ => true"),
    },

    # ---- D1: residual abort on a DIFFERENT reserved spelling (near-miss) ----
    {
        "id": "weak-partial-false",
        "kind": "uniqueness",
        "expect": "reject",
        # The same residual-abort shape as `weak-partial-none`, but keyed on a
        # DIFFERENT reserved spelling. Added by audit: the battery's D1 lane
        # probed only two of the three reserved spellings, so the third was
        # asserted as covered by the accounting block and never demonstrated.
        # A partial fix that happens to leave THIS spelling broken was
        # unattacked by every other case.
        "module": _swap(_BASE, _I_GUARD,
                        "  if isReservedConst key || name == "
                        "['F', 'a', 'l', 's', 'e'] then"),
        "refinement": "a faithful real counterpart of this shape protects the name "
                      "node in general but keeps a residual rejection for one reserved "
                      "spelling — a different one from weak-partial-none's — so "
                      "resolving that identifier still aborts instead of returning a "
                      "verdict. The F2P set covers each reserved spelling as its own "
                      "case, so that case would still fail: it would NOT resolve.",
        "rationale": "REJECT from D1 (totality) on a PROPER SUB-DOMAIN: the rival is "
                     "gold at every identifier except one reserved spelling, where it "
                     "yields the abort outcome while the spec demands `some _`. "
                     "Refuted at name=['F','a','l','s','e'] with a constant-true "
                     "matcher — a point NO other witness in the battery visits, and "
                     "the only five-character identifier probed, so it also extends "
                     "the `name` binder's length range past four. Added by audit: "
                     "without it the third reserved spelling was claimed as covered "
                     "but never demonstrated at a witness point.",
        "witness": _w("['F', 'a', 'l', 's', 'e']", "fun _ => true"),
    },

    # ---- D1+D2: transformation removed but not applied (one-sided) ----
    {
        "id": "weak-strip-no-attach",
        "kind": "uniqueness",
        "expect": "reject",
        # Half the change: the identifier is NOT transformed on the way in, but
        # the recovery step still runs on the way out, so the matcher is asked
        # about the identifier minus its first character. Wrong on ordinary
        # identifiers too, which is where it is refuted.
        "module": _swap(_BASE, _I_KEY, "  let key := name"),
        "refinement": "applies only the second half of the change: nothing is attached "
                      "on the way in, but the recovery step still runs on the way out, "
                      "so the matcher is consulted about the identifier with its first "
                      "character removed. Every F2P identifier is asked about under "
                      "the wrong spelling, so the matcher does not recognise it and "
                      "the assertion fails; on top of that the reserved spellings "
                      "still abort. A faithful real counterpart would NOT resolve — "
                      "and would in fact break the previously passing cases too.",
        "rationale": "REJECT from D2 (verdict argument) AND D1: the spec pins `matcher "
                     "name`, but the rival consults the matcher on `name` minus its "
                     "first character. Refuted at name=['x','y'] with a matcher that "
                     "recognises only ['x','y'] — an ORDINARY identifier, chosen "
                     "because that is where this rival differs from weak-no-prefix "
                     "(which is gold on ordinary identifiers). Also the only witness "
                     "point where a wrong verdict is produced without the guard being "
                     "involved at all.",
        "witness": _w("['x', 'y']", "fun s => s == ['x', 'y']"),
    },

    # ---- D2: transformation applied but never removed ----
    {
        "id": "weak-no-strip",
        "kind": "uniqueness",
        "expect": "reject",
        # The other half: the identifier is transformed on the way in but the
        # transformation is never undone, so the matcher is asked about the
        # transformed spelling.
        "module": _swap(_BASE, _I_RET, "  return some (matcher key)"),
        "refinement": "applies only the first half of the change: the name node is "
                      "protected, but the transformation is never undone, so the "
                      "matcher is consulted about the transformed spelling instead of "
                      "the identifier the caller wrote. The F2P tests supply a matcher "
                      "keyed on the original identifier, so it is asked about a name "
                      "it does not know and the assertion fails for every identifier "
                      "— a faithful real counterpart would NOT resolve.",
        "rationale": "REJECT from D2 (verdict argument): the spec pins `matcher name` "
                     "verbatim, but the rival passes the transformed identifier. This "
                     "is the wrong-ARGUMENT probe — it is refutable precisely because "
                     "`matcher` is a free parameter with a GROUNDED argument, so it can "
                     "be instantiated at a function that separates the two spellings. "
                     "Refuted at the shortest possible identifier name=['a'] with a "
                     "matcher recognising only ['a'], the point that isolates the "
                     "missing recovery step from any length arithmetic.",
        "witness": _w("['a']", "fun s => s == ['a']"),
    },

    # ---- D2: recovery removes one character too many ----
    {
        "id": "weak-over-strip",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one in the recovery step: one character too many is removed,
        # so the matcher is asked about the identifier minus its first
        # character.
        "module": _swap(_BASE, _I_RET,
                        "  return some (matcher (key.drop (identPrefix.length + 1)))"),
        "refinement": "the recovery step removes one character too many, so the "
                      "matcher is consulted about the identifier with its first "
                      "character missing. A faithful real counterpart miscomputing the "
                      "width to remove asks the matcher about a truncated name, which "
                      "the F2P matcher does not recognise, so the assertion fails for "
                      "every multi-character identifier — it would NOT resolve.",
        "rationale": "REJECT from D2 (verdict argument): the spec pins `matcher name` "
                     "but the rival passes `name` with its first character dropped. "
                     "Refuted at name=['a','b'] with a matcher recognising only "
                     "['a','b'] — a two-character identifier, the shortest length at "
                     "which an off-by-one in the recovery width is observable and "
                     "distinct from weak-no-strip's one-character point.",
        "witness": _w("['a', 'b']", "fun s => s == ['a', 'b']"),
    },

    # ---- D2: first identifier character corrupted ----
    {
        "id": "weak-first-char-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain corruption: the name node is built by REPLACING the
        # identifier's first character rather than by prepending, so the
        # recovered identifier keeps the right length but a wrong first
        # character. Correct on the empty identifier and on any identifier
        # whose first character already equals the attached one.
        "module": _swap(_BASE, _I_KEY,
                        "  let key := identPrefix ++ identPrefix ++ name.drop 1"),
        "refinement": "builds the name node by REPLACING the identifier's first "
                      "character instead of prepending, so the recovered identifier "
                      "has the same length as the original except at the empty "
                      "identifier, where it is one character longer. A faithful "
                      "real counterpart that overwrote the first character while "
                      "attaching the guard character asks the matcher about a "
                      "misspelled name, so the F2P matcher does not recognise it and "
                      "the assertion fails — it would NOT resolve.",
        "rationale": "REJECT from D2 (verdict argument) on a PROPER SUB-DOMAIN: the "
                     "rival agrees with gold exactly on the identifiers whose first "
                     "character already equals the attached one (measured: at "
                     "name=['$','k'] both sides ask the matcher about ['$','k'], and "
                     "the refutation witness there FAILS against the rival), and "
                     "diverges on the rest — so a length-only or shape-only clause "
                     "would miss it and only the verbatim-argument pin catches it. "
                     "It does NOT agree on the empty identifier: there gold asks the "
                     "matcher about [] while the rival asks about ['$'] (measured by "
                     "evaluation), which is a divergence, not an agreement. "
                     "Refuted at name=['q','z'] with a matcher recognising only "
                     "['q','z'], a point in the divergent sub-domain and distinct from "
                     "every other witness. Ports the nagini "
                     "encode-partial-first-char rival.",
        "witness": _w("['q', 'z']", "fun s => s == ['q', 'z']"),
    },

    # ---- D2: constant verdict, ignoring the matcher entirely ----
    {
        "id": "weak-const-verdict",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns a constant verdict, never consulting the matcher. Attacks the
        # value half of D2 directly and is the case that makes the `matcher`
        # binder load-bearing: a spec that only demanded `some _` would admit
        # it.
        "module": _swap(_BASE, _I_RET, "  return some false"),
        "refinement": "returns a constant verdict without ever consulting the "
                      "matcher. A faithful real counterpart that resolved every "
                      "identifier to a fixed answer would report every identifier as "
                      "non-matching, so the F2P assertion that the supplied matcher's "
                      "verdict comes back fails for every identifier — it would NOT "
                      "resolve. It also breaks the previously passing cases, which is "
                      "why no faithful patch of this shape could be mistaken for the "
                      "fix.",
        "rationale": "REJECT from D2 (verdict value): the spec pins the boolean to "
                     "`matcher name`, but the rival ignores `matcher` completely. This "
                     "is the case that demonstrates the `matcher` binder is "
                     "load-bearing — a clause demanding only `some _` (D1 alone) would "
                     "admit it. Refuted at name=['1','2','3','4'] with a constant-true "
                     "matcher: an ordinary identifier that neither collides with a "
                     "reserved spelling nor is used by any other witness, so the "
                     "refutation is attributable to the ignored matcher alone and not "
                     "to the guard.",
        "witness": _w("['1', '2', '3', '4']", "fun _ => true"),
    },
]

# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. Every sibling case is recorded below, including the
# ones with no counterpart here.
#
# The sibling battery has 11 SPEC cases (3 soundness positives, 2 admissibility,
# 6 uniqueness rivals) plus an EMPTY axiom lane, spread over TWO contracted
# functions. This bundle models the SAME behavior as ONE end-to-end obligation,
# so the sibling's per-site cases COMPOSE rather than double. Case-count parity
# is not the target; per-clause and per-binder coverage is.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-encode-local             -> pos-let-recovered        RE-EXPRESSED (composed)
#   pos-lookup-local             -> pos-let-recovered        COMPOSED (same case)
#   pos-encode-assert-grounded   -> pos-pure-functional      RE-EXPRESSED
#   admiss-encode-reserved       -> admiss-reserved-ident    RE-EXPRESSED (composed)
#   admiss-lookup-prefixed       -> admiss-reserved-ident    COMPOSED (same case)
#   encode-no-sentinel           -> weak-no-prefix           PORTED
#   encode-partial-first-char    -> weak-first-char-prefix   PORTED
#   lookup-no-strip              -> weak-no-strip            PORTED
#   lookup-over-strip            -> weak-over-strip          PORTED
#   encode-frame-mutate          -> (none)                   VACUOUS
#   lookup-frame-mutate          -> (none)                   VACUOUS
#   (none)                       -> pos-alt-prefix           ADDED
#   (none)                       -> pos-conditional-prefix   ADDED
#   (none)                       -> weak-strip-no-attach     ADDED
#   (none)                       -> weak-partial-none        ADDED
#   (none)                       -> weak-partial-false       ADDED (audit)
#   (none)                       -> weak-const-verdict       ADDED
#   AXIOM_TESTS (0)              -> (none)                   DROPPED (G-AX's lane)
#
# COMPOSED (pos-lookup-local, admiss-lookup-prefixed): the sibling contracts the
#   build step and the lookup step separately and therefore needs one positive
#   and one admissibility probe per site. Here they are a single obligation over
#   a single input->output relation, so the corresponding case is one case. This
#   is carrier narrowing, not an omission: nothing the sibling case tested is
#   left untested — the composed case exercises the same reshape and the same
#   ground input across both steps at once.
#
# RE-EXPRESSED (pos-encode-assert-grounded): the sibling's control asserts the
#   built sequence equals the grounded pin just before returning, to show the pin
#   is a real deep model rather than an opaque answer key. This carrier has no
#   separate helper to re-assert — the clause is already a bare equation over the
#   two input binders — so the grounding argument is carried instead by
#   pos-pure-functional (the cheapest satisfying shape still has to apply the
#   caller's verdict function to the caller's identifier) together with the three
#   wrong-ARGUMENT rivals, which are refutable precisely BECAUSE the argument is
#   grounded.
#
# VACUOUS (encode-frame-mutate, lookup-frame-mutate): the sibling's two mandatory
#   probes write to a read-only input in order to satisfy the pin on a
#   self-mutated value, and are rejected by its fractional-permission system.
#   Lean is referentially transparent: the inputs are immutable values, there is
#   no aliasing, no `mut` input binder, and no read-only cell to overwrite, so
#   the class cannot be written down. No substitute probe is fabricated.
#
# DIVERGENCE: the sibling carries NO divergence / non-termination case, and on
#   this backend the class is genuinely vacuous anyway —
#   `implementation_resolveIdent` is a total Lean `def`, so a diverging
#   implementation cannot be expressed, and the obligation is a plain equation
#   with no vacuous exit. (This disposition is lean-specific; on a velvet bundle
#   under `partial` termination semantics the same class is a KNOWN SPEC HOLE, see
#   the corpus-wide termination-semantics finding. Nothing to record here.)
#
# ADDED, and why none of them is a fabrication for an unmodeled behavior:
#   * pos-alt-prefix — the sibling pins the leading code point to a specific
#     constant in its postcondition, so an alternate prefix is genuinely REJECTED
#     there. This carrier's clause is a pure input->output relation and so admits
#     it; the case checks that the spec is not silently over-fit to one character.
#   * pos-conditional-prefix — a second, deeper structural reshape (a real case
#     split rather than a rewrite), to defend the obligation against more than
#     one syntactic form.
#   * weak-strip-no-attach — the one-sided rival the sibling cannot express,
#     because its two sites are contracted separately: applying the recovery step
#     without the build step is a single-implementation rival only once the two
#     steps live in one obligation. It also supplies the only witness point where
#     a wrong verdict is produced with the guard uninvolved.
#   * weak-partial-none — the residual-abort near-miss (gold everywhere except
#     one reserved spelling), which is the realistic partial-fix shape and the
#     case that gives the D1 lane a second, strictly-harder point.
#   * weak-partial-false — the SAME residual-abort shape keyed on a different
#     reserved spelling. Added by the adversarial audit: the battery asserted in
#     prose that `name` ranged over all three reserved spellings, but no witness
#     point visited the third, so a partial fix leaving exactly that spelling
#     broken was unattacked. It also extends the probed `name` length range to
#     five characters.
#   * weak-const-verdict — the case that makes the `matcher` binder demonstrably
#     load-bearing: a clause demanding only a non-abort outcome would admit it.
#
# POINT SPREAD. The eight reject witnesses probe eight DISTINCT (name, matcher)
# points (pts=8):
#   name                    matcher                    case                     lane
#   ['T','r','u','e']       fun _ => true              weak-no-prefix           D1
#   ['N','o','n','e']       fun _ => true              weak-partial-none        D1
#   ['F','a','l','s','e']   fun _ => true              weak-partial-false       D1
#   ['x','y']               s == ['x','y']             weak-strip-no-attach     D1+D2
#   ['a']                   s == ['a']                 weak-no-strip            D2
#   ['a','b']               s == ['a','b']             weak-over-strip          D2
#   ['q','z']               s == ['q','z']             weak-first-char-prefix   D2
#   ['1','2','3','4']       fun _ => true              weak-const-verdict       D2
# `name` takes eight distinct values spanning ALL THREE reserved spellings and
# ordinary identifiers of length 1, 2 and 4; `matcher` takes five distinct
# values, and crucially it is NOT held constant across the D2 lane — the four
# argument/value rivals are refuted against matchers that actually discriminate
# between identifier spellings, which is what a rival mishandling only the
# argument requires. Neither binder is pinned by the battery.
#
# ADVERSARIAL AUDIT RECORD (independent re-derivation, not the port's own claim).
# All exit codes below are from real `scripts/lean_verify.sh` builds.
#
#   Statement integrity: all 13 cases' `theorem correct_resolveIdent` statements
#   are BYTE-identical to the frozen file (not merely logically equal), as are the
#   imports and the axioms / pure / post-conditions regions.
#
#   Witness re-derivation: every reject witness was rebuilt against its rival and
#   against the frozen solution. All held of the rival (exit 0) and failed on gold
#   (exit 1), and every gold-side failure is `decide` PROVING the negated spec
#   false — a positive computation that gold satisfies the clause there. None is a
#   missing identifier, a stuck reduction, or a timeout.
#
#   SPEC-TOO-WEAK probes (new wrong impls the battery did not contain; each was
#   REJECTED, and each rejection was confirmed SEMANTIC by its own two-build
#   witness, so none is a spec hole):
#     * guard tested on the unprefixed identifier (aborts on reserved spellings)
#     * verdict polarity inverted (uses both binders, so neither the constant-
#       verdict nor the wrong-argument family subsumes it)
#     * correct except on identifiers of length >= 5 (beyond every witness point
#       at the time; this is the gap `weak-partial-false` now also covers)
#     * correct except it aborts on the EMPTY identifier
#     * a `partial def` self-recursive impl: rejected, and NOT vacuous here —
#       `unfold` cannot reduce it, so it cannot discharge the equation. (The
#       velvet `partial`-semantics hole is a separate known finding.)
#
#   SPEC-TOO-STRONG probes (new CORRECT reshapes; the spec admits each, so it is
#   not over-fit): the cheapest direct `some (matcher name)`; a two-character
#   prefix; dropping the post-prefix-dead guard entirely; and a reverse/reverse
#   round-trip on the recovered identifier. All four verify (exit 0). The last two
#   needed a re-authored proof script — a proof-authoring cost, not a spec
#   rejection.
#
#   Prose defects found and FIXED: `weak-first-char-prefix` claimed agreement with
#   gold on the empty identifier. Measured false by evaluation — at name=[] gold
#   asks the matcher about [] while the rival asks about ['$'] — so the claimed
#   agreement sub-domain is exactly {identifiers already starting with the
#   attached character}, verified at name=['$','k'] (witness FAILS on the rival
#   there, exit 1). The length claim was corrected likewise.
#
# AXIOM_TESTS: dropped. The axiom lane belongs to G-AX; this bundle declares no
# `opaque` callee and consumes no `axiom` (the reserved-constant set and both
# transformation steps are modeled deeply as A-references), and the sibling's
# AXIOM_TESTS is empty too, so there is nothing to carry over.
AXIOM_TESTS = []
