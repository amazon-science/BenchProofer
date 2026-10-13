"""properties.py — G-PBT falsification battery for sympy__sympy-13877 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds by construction and the single
``theorem correct_firstNonzero`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the same single behavior over a ``List[int]`` carrier where an entry is
abstracted to an integer *status code* and "mathematically zero" is the
arithmetic predicate ``e <= 0``; the answer is pinned against a grounded pure
front-recursive fold (nagini's ``first_usable``) returning a ``len(col)``
sentinel, with the result an ``int`` index and ``-1`` for "no pivot". This Lean
bundle models the SAME purely functional core — selecting, from a column of
symbolic expressions, the first entry that is not mathematically zero — but over
a RICHER carrier: an entry is a real expression tree (``PExpr``), the zero test
is spelled out deeply as evaluation to the zero polynomial (``eval`` /
``isMathZero``), and the result is an ``Option (Nat × PExpr)`` carrying BOTH the
position and the value. So the carrier is wider in two ways that matter for the
port, and narrower in none:

  * the "pseudo-zero" that the whole behavior turns on is no longer an opaque
    negative status code but a CONSTRUCTIBLE expression — a difference of two
    products that cancels completely — so the central rival can be refuted at a
    literal input rather than argued about;
  * the result carries a VALUE component the nagini carrier does not have, which
    is a second independent thing a rival can get wrong (see
    ``weak-placeholder-value``), and the ``none``/``some`` split replaces
    nagini's in-band ``-1`` sentinel.

Every nagini uniqueness rival carries over. The nagini frame/permission-mutation
rival is VACUOUS here and the nagini AXIOM lane is dropped; see ``assessment``
at the bottom for the full accounting.

AUDIT ADDENDUM (independent re-derivation; machine-checked). One prose claim in
the original port was measured FALSE and is corrected in place:

  * ``pos-branch-invert`` claimed the frozen loop bridge "inspects the branch
    shape" and therefore had to be re-proved for the inverted branch order. It
    does not: the inverted impl elaborates against the byte-frozen proof region
    with the obligation closed, because the two branch orders are definitionally
    equal after ``Bool`` case analysis. The needless proof-region swap is dropped
    and the case is now advertised only as the cheap branch-order reshape it is.

The WITNESSES block's claim that every gold-side failure is at the ``himpl`` step
was independently re-derived and CONFIRMED for all six (see that block).

Also added by the audit: ``pos-distinct-zero-test``, the positive the battery was
missing — a correct impl that decides mathematical-zero by a DIFFERENT, only
extensionally equal predicate, which the frozen ``rfl`` bridge does not close and
which therefore exercises the spec against a genuinely different reduction shape.

SPEC STRENGTH IS SETTLED, NOT ARGUED. The frozen postcondition is FUNCTIONAL: for
any column, any two results satisfying ``problem_spec_firstNonzero`` are equal.
This was proved against the frozen file as a standalone theorem (C2 rules out a
``some`` coexisting with a ``none``; mutual application of C3 to the two candidate
positions forces the positions equal; C1 then forces the values equal). A
functional postcondition admits exactly ONE result per input, so no wrong
implementation can satisfy it and SPEC-TOO-WEAK is impossible here by
construction — which is why the audit's tuned-wrong-impl probes (a constant-term-
only zero test, a scan that gives up after position 1, a re-derived
double-negated value, a ``Nat``-truncated position, a singleton-column ``none``)
were all rejected, as they must be.

DEFENDED SURFACE (one modeled behavior, one obligation).
``problem_spec_firstNonzero col result`` pins EXACTLY, with FIVE independent
top-level clauses across the two arms of the result:

  * (C0 range)   ``some (pos, val) -> pos < col.length`` — the reported position
    is a legal index of the column;
  * (C1 value)   ``some (pos, val) -> col[pos]? = some val`` — the reported value
    is exactly the entry sitting at that position, not a re-derived or
    canonicalized stand-in;
  * (C2 live)    ``some (pos, val) -> isMathZero val = false`` — the selected
    entry is GENUINELY not zero. This is the load-bearing clause: the whole
    modeled behavior exists because an entry can be written in a structurally
    non-trivial form and still be mathematically zero, and such an entry must
    not be selected;
  * (C3 first)   ``some (pos, val) -> ∀ k e, k < pos → col[k]? = some e →
    isMathZero e = true`` — every strictly-earlier entry is mathematically zero,
    i.e. ``pos`` is the FIRST live position and not merely some live position;
  * (C4 empty)   ``none -> ∀ e ∈ col, isMathZero e = true`` — reporting "no
    entry qualifies" is only permitted when every entry really is mathematically
    zero.

C2 and C3 together are what nagini's P3 (``Result == first_usable``) says in one
equation against its grounded fold; C0 is nagini's P1 range clause; C4 is
nagini's P2 (no-pivot iff all-zero) in the ``Option`` idiom; C1 has no nagini
counterpart at all, because nagini's result is a bare index with no value
component to corrupt.

GROUNDEDNESS / UNGROUNDED-ORACLE ECHO — VACUOUS, as in the sibling. The
postcondition is grounded in the input: ``result`` is pinned by structural
relations over ``col`` itself (an index bound, an indexing equation, and the
deeply-spelled ``isMathZero`` applied to the column's own entries). There is no
opaque answer key an implementation could echo — locating the first live entry IS
doing the work. The sibling makes the same observation about its ``first_usable``
fold and substitutes honest cheapest-correct positive controls; this port does
the same (``pos-branch-invert``, ``pos-pure-recursive``).

BINDER STRUCTURE. The spec predicate has exactly ONE input binder, ``col``
(``result`` is the output). It is therefore not possible for a witness to hold an
input binder fixed while moving others, and the coverage question reduces to
whether the reject witnesses probe ENOUGH DISTINCT columns to exercise every
clause. They probe SIX distinct columns (``pts=6``) spanning: a length-1 column
whose only entry is a non-trivially-mathematically-zero expression; a length-1
column whose only entry is live; a length-2 column with two live entries; a
length-2 column with a leading literal zero then a live entry; and two more (see
the point-spread block at the bottom). Length varies (1 and 2), the position of
the first live entry varies (0, 1, and absent), and the KIND of zero varies
(literal zero constant vs. a structurally non-trivial expression that cancels) —
that last axis being exactly the distinction the modeled behavior exists to draw.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet that computes the
rival's concrete output at one literal column with ``have himpl := by decide``,
rewrites the spec by it, destructures the postcondition, and closes by refuting
the single offending clause. The carrier is fully COMPUTABLE (``PExpr`` derives
``DecidableEq``; ``eval`` / ``isMathZero`` / the scanning loop all reduce), so
every witness is stated at literal inputs and each ``example`` head binds
NOTHING — there are no hypotheses whose joint satisfiability could be in
question, and no conditioning on an opaque term is needed anywhere in this
battery. Each witness was checked with two real ``lake env lean`` builds: it
HOLDS of its rival and FAILS on the frozen solution.

WHERE, EXACTLY, THE GOLD-SIDE FAILURE LANDS (audit-verified, all six rebuilt).
The original claim is CORRECT and is restated here with the evidence: in ALL SIX
cases the gold-side build fails at the ``himpl`` step, with the single error
``Tactic `decide` proved that the proposition implementation_firstNonzero <col> =
<rival output> is false``. That is a PLAIN EVALUATION refutation — the strongest
available signature on this carrier, and the one class for which the forgery
probe is not even required: ``decide`` reduced both sides to normal form and
reported the concrete inequality, so the exit code is a function of the claimed
output and nothing else. No case fails on gold for a missing identifier, a type
error, an unfolding failure, or a timeout.

The audit additionally confirmed, by type-revealing builds on the pseudo-zero
column, that the CLAUSE hypotheses these witnesses destructure are concrete
equations on both sides rather than ``True`` (i.e. no clause is silently proved
away by ``simp`` for either impl): on gold ``isMathZero <pseudo-zero> = true``,
on the structural-test rival ``isMathZero <pseudo-zero> = false``. And each
witness was checked to bind the clause its ``rationale`` NAMES, by revealing the
bound hypothesis's type: ``1 < [PExpr.const 4].length`` for the C0 case,
``[PExpr.const 0, sym*sym][1]? = some (PExpr.const 1)`` for the C1 case,
``isMathZero (PExpr.const 2) = true`` for the C3 case.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
The modeled behavior is consumed by a fraction-free elimination that DIVIDES by
the selected entry and recurses. Each reject case's ``refinement`` argues from
that consumer: selecting a mathematically-zero entry introduces a division whose
numerator and denominator both vanish, so the running quantity degenerates to an
undefined value and the downstream comparison on it raises rather than returning
a determinant — precisely the reported failure. Selecting the wrong LIVE entry
(or none at all, or the right entry under a wrong position/value) changes which
row is eliminated against, so the recursion computes a different quantity than
the one the F2P determinant assertions pin. In every case the faithful real
counterpart would NOT resolve.

AXIOM lane: EMPTY here. This bundle declares no ``opaque`` callee and consumes no
``axiom`` — the zero test the behavior turns on is modeled DEEPLY (``eval`` /
``isMathZero``, an A-reference validated against the real routine by G-CONF /
G-AX), never axiomatized. The sibling's two ``AXIOM_TESTS`` are dropped: the
axiom lane belongs to G-AX and this gate ignores them.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13877"
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
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# Solution.lean (checked by _swap at import time, so the manifest breaks loudly
# if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# The whole scanning loop body, inside `-- impl-start` / `-- impl-end`.
_I_LOOP = (
    "  let mut i := 0\n"
    "  for x in col do\n"
    "    if isMathZero x = false then\n"
    "      return some (i, x)\n"
    "    i := i + 1\n"
    "  return none"
)

# The impl's signature line + its `Id.run do` opener, so a pure-recursive
# positive can drop the monadic wrapper without touching anything else.
_I_HEAD = "    (col : List PExpr) : Option (Nat × PExpr) := Id.run do\n" + _I_LOOP

# The `by_cases` block inside `loop_eq_go` (proof region) — the only place the
# frozen proof inspects the loop's branch shape, so a branch-reshaping positive
# re-proves exactly here.
_P_BYCASES = (
    "      by_cases hx : isMathZero x = false\n"
    "      · simp only [hx, if_true]\n"
    "        rfl\n"
    "      · simp only [hx]\n"
    "        exact ih (i + 1)"
)

# The whole body of `loop_eq_go` (proof region), for the positive that replaces
# the monadic loop with a pure recursion and so must bridge a different shape.
_P_LOOPEQ = (
    "  intro col\n"
    "  simp only [implementation_firstNonzero, Id.run]\n"
    "  generalize (0 : Nat) = i\n"
    "  induction col generalizing i with\n"
    "  | nil => rfl\n"
    "  | cons x xs ih =>\n"
    "      simp only [List.forIn_cons, go]\n" + _P_BYCASES
)

# The opening of the frozen obligation's tactic body (proof region), so the
# admissibility case can prepend a ground `have` while leaving the
# `theorem correct_firstNonzero` STATEMENT byte-identical.
_P_CORRECT_OPEN = (
    "      problem_spec_firstNonzero col (implementation_firstNonzero col) := by\n"
    "  intro col\n"
    "  rw [loop_eq_go col]"
)


# ---------------------------------------------------------------------------
# Carrier vocabulary used by the rivals + witnesses.
#
# `_PSEUDO_ZERO` is the crux of the modeled behavior made CONSTRUCTIBLE: an
# expression tree that is structurally non-trivial (a sum of a product and a
# negated sum) yet evaluates to the zero polynomial, because the two products
# cancel completely. On the nagini carrier this class could only be named by an
# opaque negative status code; here it is a literal the verifier can compute
# with, which is what lets every rival be refuted at a ground input.
# ---------------------------------------------------------------------------
_PSEUDO_ZERO = (
    "(PExpr.add (PExpr.mul PExpr.sym (PExpr.add PExpr.sym (PExpr.const 1))) "
    "(PExpr.neg (PExpr.add (PExpr.mul PExpr.sym PExpr.sym) PExpr.sym)))"
)


# ---------------------------------------------------------------------------
# Witness scaffolds. Each computes the rival's concrete output at a literal
# column (`himpl`, closed by `decide` — the carrier is fully computable), rewrites
# the spec by it, then refutes ONE named clause. No head binders anywhere, so no
# consistency question arises.
# ---------------------------------------------------------------------------

_CLAUSE_PAT = {
    "C0": "⟨h, _, _, _⟩",   # pos < col.length
    "C1": "⟨_, h, _, _⟩",   # col[pos]? = some val
    "C2": "⟨_, _, h, _⟩",   # isMathZero val = false
    "C3": "⟨_, _, _, hk⟩",  # ∀ k e, k < pos → col[k]? = some e → isMathZero e
}


def _w_some(col, pos, val, clause, earlier=None):
    """Refute one clause of the `some` arm at the literal column `col`.

    `clause` is C0/C1/C2/C3. For C3 the ∀-quantified clause is instantiated at
    index 0 with `earlier`, the entry the rival wrongly scanned past.
    """
    if clause == "C3":
        tail = (f"  have h := hk 0 {earlier} (by decide) (by decide)\n"
                "  exact absurd h (by decide)\n")
    else:
        tail = "  exact absurd h (by decide)\n"
    return (
        f"example : ¬ problem_spec_firstNonzero {col}\n"
        f"    (implementation_firstNonzero {col}) := by\n"
        f"  have himpl : implementation_firstNonzero {col} "
        f"= some ({pos}, {val}) := by\n"
        "    decide\n"
        "  rw [himpl]\n"
        "  unfold problem_spec_firstNonzero\n"
        f"  rintro {_CLAUSE_PAT[clause]}\n" + tail
    )


def _w_none(col, live):
    """Refute C4 (the `none` arm) at `col`, whose member `live` is NOT math-zero."""
    return (
        f"example : ¬ problem_spec_firstNonzero {col}\n"
        f"    (implementation_firstNonzero {col}) := by\n"
        f"  have himpl : implementation_firstNonzero {col} = none := by\n"
        "    decide\n"
        "  rw [himpl]\n"
        "  unfold problem_spec_firstNonzero\n"
        "  intro hall\n"
        f"  have h := hall {live} (by decide)\n"
        "  exact absurd h (by decide)\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_firstNonzero` statement byte-identical, re-proves inside
    # the proof region only, and adds no axiom/theorem/lemma.
    # =====================================================================
    {
        "id": "pos-branch-invert",
        "kind": "soundness",
        "expect": "verify",
        # Branch INVERSION: test the positive form of the zero predicate and
        # advance in that branch, reporting the entry in an explicit `else`.
        # Identical values on every input, different control flow.
        #
        # AUDIT NOTE (measured, and the reason this case's proof region is now
        # UNTOUCHED). An earlier revision of this case also re-stated the frozen
        # `loop_eq_go` `by_cases` block, and claimed in its rationale that the
        # frozen bridge "inspects the branch shape" and so had to be re-proved
        # for the inverted form. That claim was FALSE. Building this exact
        # inverted impl against the byte-frozen proof region elaborates with the
        # obligation closed (exit 0): `if isMathZero x then i := i+1 else return`
        # and `if isMathZero x = false then return; i := i+1` are DEFINITIONALLY
        # equal after `Bool` case analysis, so `simp only [hx, if_true]; rfl`
        # closes both and the re-proof was doing no work. The swap is dropped and
        # the rationale corrected: this case is an honest but CHEAP reshape — it
        # confirms the spec does not over-fit the frozen branch ORDER, and it is
        # deliberately no longer advertised as more than that. The positive that
        # does require real proof work is `pos-distinct-zero-test`, added below.
        # (Verified: real build, obligation closed, frozen proof region.)
        "module": _swap(
            _BASE, _I_LOOP,
            "  let mut i := 0\n"
            "  for x in col do\n"
            "    if isMathZero x then\n"
            "      i := i + 1\n"
            "    else\n"
            "      return some (i, x)\n"
            "  return none"),
        "rationale": "correct reshape: the zero predicate is tested in its "
                     "positive form and the scan advances in THAT branch, "
                     "reporting the entry from an explicit `else`. It selects the "
                     "same position and the same value on every column, so C0/C1/"
                     "C2/C3/C4 all still hold — a faithful reshape MUST verify, "
                     "else SPEC-TOO-STRONG. Scope of what this case earns, stated "
                     "honestly: the two branch orders are DEFINITIONALLY equal on "
                     "this carrier (measured — the frozen proof region closes the "
                     "inverted impl verbatim, so no re-proof is needed and none is "
                     "performed), hence it tests only that the spec does not "
                     "over-fit the frozen branch order, and it does NOT exercise "
                     "the loop bridge against a genuinely different reduction "
                     "shape. Ports the sibling's pos-reorder, whose branch "
                     "inversion is likewise value-preserving; the sibling's "
                     "'keep every framing invariant verbatim' requirement maps "
                     "here to keeping the proof-region bridge verbatim, which is "
                     "now literally what happens.",
    },
    {
        "id": "pos-pure-recursive",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT shape: drop the monadic accumulator loop
        # entirely and scan with a pure front-recursive helper (an impl-region
        # `where` def — a `def`, not a new theorem/lemma, so it is an admissible
        # variant addition), threading the running index as an argument. Front-
        # recursive, matching the direction the spec's "first" clause reads in.
        # The frozen loop-bridge is re-proved against the recursive shape.
        # (Verified: real build, obligation closed.)
        "module": _swaps(
            _BASE,
            (_I_HEAD,
             "    (col : List PExpr) : Option (Nat × PExpr) :=\n"
             "  scanCol col 0\n"
             "where\n"
             "  scanCol : List PExpr → Nat → Option (Nat × PExpr)\n"
             "  | [], _ => none\n"
             "  | x :: xs, i =>\n"
             "    if isMathZero x = false then some (i, x) "
             "else scanCol xs (i + 1)"),
            (_P_LOOPEQ,
             "  intro col\n"
             "  simp only [implementation_firstNonzero]\n"
             "  generalize (0 : Nat) = i\n"
             "  induction col generalizing i with\n"
             "  | nil => rfl\n"
             "  | cons x xs ih =>\n"
             "      simp only [implementation_firstNonzero.scanCol, go]\n"
             "      by_cases hx : isMathZero x = false\n"
             "      · simp only [hx, if_true]\n"
             "      · simp only [hx]\n"
             "        exact ih (i + 1)"),
        ),
        "rationale": "the cheapest correct impl on this carrier: a pure "
                     "front-recursive scan carrying the running index, with no "
                     "mutable accumulator and no monadic loop at all. A correct "
                     "loop-free shape must verify (else SPEC-TOO-STRONG). Ports "
                     "the sibling's pos-cheapest, which materializes the grounded "
                     "front-recursive fold directly; this carrier has no separate "
                     "fold def to call (the spec pins the answer structurally, not "
                     "against a named fold), so the analogue is to WRITE that "
                     "front recursion as the impl. It also demonstrates the same "
                     "point the sibling case makes — the postcondition is grounded "
                     "in the input, so computing the first live position IS the "
                     "right answer and there is no wrong echo. Re-proved by "
                     "re-stating the loop bridge against the recursive shape; "
                     "statement byte-identical, no new axiom/theorem/lemma (the "
                     "helper is an impl-region `def`).",
    },

    {
        "id": "pos-distinct-zero-test",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT. The reshape the two original positives do not perform:
        # neither of them changes the ZERO TEST, which is the load-bearing notion
        # of the whole modeled behavior — `pos-branch-invert` only reorders the
        # branches around `isMathZero` (definitionally, see its note) and
        # `pos-pure-recursive` calls `isMathZero` verbatim. So the spec was never
        # shown to accept an impl that decides "mathematically zero" a DIFFERENT
        # WAY. This case does: liveness is decided by `(eval x).any (· ≠ 0)` —
        # "some coefficient is nonzero" — rather than by negating
        # `(eval x).all (· == 0)`. The two are extensionally equal but NOT
        # definitionally so: `List.any`/`List.all` recurse into different
        # `Bool` combinators, so the frozen `rfl`-based bridge does not close it
        # and the equality has to be PROVED by an induction on the coefficient
        # list (the `key` lemma below, a `have` inside the existing tactic body —
        # not a new top-level theorem/lemma). This is the positive that actually
        # exercises the loop bridge against a different reduction shape.
        # (Verified: real build, obligation closed.)
        "module": _swaps(
            _BASE,
            (_I_LOOP,
             "  let mut i := 0\n"
             "  for x in col do\n"
             "    if (eval x).any (fun c => !(c == 0)) then\n"
             "      return some (i, x)\n"
             "    i := i + 1\n"
             "  return none"),
            ("      simp only [List.forIn_cons, go]\n" + _P_BYCASES,
             "      simp only [List.forIn_cons, go]\n"
             "      have key : ((eval x).any (fun c => !(c == 0)))"
             " = !isMathZero x := by\n"
             "        unfold isMathZero\n"
             "        induction (eval x) with\n"
             "        | nil => rfl\n"
             "        | cons a t iht => simp only [List.any_cons, List.all_cons,"
             " Bool.not_and,\n"
             "            iht, Bool.not_eq_true']\n"
             "      rw [key]\n"
             "      by_cases hx : isMathZero x = false\n"
             "      · simp only [hx, Bool.not_false, if_true]\n"
             "        rfl\n"
             "      · simp only [Bool.not_eq_false] at hx\n"
             "        simp only [hx, Bool.not_true, Bool.false_eq_true,"
             " if_false]\n"
             "        exact ih (i + 1)"),
        ),
        "rationale": "correct reshape of the LOAD-BEARING notion itself: the "
                     "entry's liveness is decided as 'some coefficient of its "
                     "evaluation is nonzero' (`(eval x).any (· ≠ 0)`) instead of "
                     "as the negation of 'every coefficient is zero' "
                     "(`isMathZero`, i.e. `(eval x).all (· == 0)`). Same verdict "
                     "on every expression, so the same position and value are "
                     "selected on every column and C0–C4 all still hold — a "
                     "faithful reshape MUST verify, else SPEC-TOO-STRONG. Unlike "
                     "the other two positives this one is NOT definitionally the "
                     "frozen impl: `List.any` and `List.all` reduce through "
                     "different `Bool` combinators, so the frozen `rfl` bridge "
                     "fails on it and the extensional equality must be proved by "
                     "induction on the coefficient list. That makes this the "
                     "positive that genuinely exercises the loop bridge against a "
                     "different reduction shape, and it is the direction the "
                     "battery was missing: it shows the spec pins the MEANING of "
                     "mathematical zero and not the frozen predicate's syntax. "
                     "Statement byte-identical; the bridging equality is a `have` "
                     "in the existing tactic body, no new axiom/theorem/lemma.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at a normal,
    # F2P-shaped column. The frozen obligation carries NO precondition
    # hypothesis at all (it is `∀ col, problem_spec ... `), so the sibling's
    # "does the precondition admit a normal input" probe re-expresses as: is the
    # postcondition actually dischargeable at a normal input, or is the modeled
    # behavior unsatisfiable exactly where it matters?
    # =====================================================================
    {
        "id": "admiss-pseudo-zero-column",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the spec by evaluation at the smallest F2P-shaped column: a
        # leading structurally-non-trivial-but-mathematically-zero entry followed
        # by a genuinely live one — i.e. exactly the configuration the modeled
        # behavior exists to handle. Prepended as a ground `have` to the existing
        # tactic body; the frozen obligation is then closed verbatim. Nothing is
        # assumed: no new declaration, statement byte-identical.
        # (Verified: real build, obligation closed.)
        "module": _swap(
            _BASE, _P_CORRECT_OPEN,
            "      problem_spec_firstNonzero col "
            "(implementation_firstNonzero col) := by\n"
            f"  have _ground : problem_spec_firstNonzero "
            f"[{_PSEUDO_ZERO}, PExpr.const 5]\n"
            f"      (implementation_firstNonzero "
            f"[{_PSEUDO_ZERO}, PExpr.const 5]) := by\n"
            f"    have himpl : implementation_firstNonzero "
            f"[{_PSEUDO_ZERO}, PExpr.const 5] = some (1, PExpr.const 5) := by "
            "decide\n"
            "    rw [himpl]\n"
            "    unfold problem_spec_firstNonzero\n"
            "    refine ⟨by decide, by decide, by decide, ?_⟩\n"
            "    intro k e hk he\n"
            "    interval_cases k\n"
            "    · simp only [List.getElem?_cons_zero, Option.some.injEq] at he\n"
            "      subst he; decide\n"
            "  intro col\n"
            "  rw [loop_eq_go col]"),
        "rationale": "the obligation is discharged by evaluation at the smallest "
                     "F2P-shaped column — a leading entry that is written in a "
                     "structurally non-trivial form yet is mathematically zero, "
                     "followed by a genuinely live entry — proving all five "
                     "clauses hold simultaneously there (position 1 is in range, "
                     "the value is the entry at 1, that entry is not math-zero, "
                     "and the single earlier entry IS math-zero). Then the frozen "
                     "obligation is closed verbatim. If this failed, the modeled "
                     "behavior would be unsatisfiable at exactly a normal input "
                     "(the analogue of PRECOND-TOO-STRONG, which is what the "
                     "sibling's admiss-1 probes on its half-permission "
                     "precondition). Nothing is assumed: no new declaration, the "
                     "ground instance is a `have` in the existing tactic body, and "
                     "the statement is byte-identical.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve the F2P, and (b) a witness
    # pinning the violation at one literal column.
    # =====================================================================

    # ---- THE bug class: structural rather than mathematical zero test ----
    {
        "id": "weak-structural-zero-test",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behavior: an entry is treated as usable unless it is
        # LITERALLY the zero constant. An entry written in a structurally
        # non-trivial form that nonetheless cancels to zero is accepted.
        "module": _swap(
            _BASE, _I_LOOP,
            "  let mut i := 0\n"
            "  for x in col do\n"
            "    if x ≠ PExpr.const 0 then\n"
            "      return some (i, x)\n"
            "    i := i + 1\n"
            "  return none"),
        "refinement": "this IS the pre-fix behavior, and it is the reason the "
                      "modeled behavior exists: the qualifying test is structural "
                      "(is this entry the literal zero object?) rather than "
                      "mathematical (does this entry evaluate to zero?). The "
                      "consumer DIVIDES by the selected entry and recurses, so a "
                      "faithful real counterpart keeping the structural test "
                      "divides by an entry that is mathematically zero: numerator "
                      "and denominator both vanish, the running quantity "
                      "degenerates to an undefined value, and the downstream "
                      "comparison on it raises instead of returning a "
                      "determinant — exactly the reported failure on the "
                      "larger instances of the reported family. So the faithful "
                      "patch does NOT resolve the F2P, and a rival verifying here "
                      "would be a true verify-without-resolve break.",
        "rationale": "REJECT from C2 (`isMathZero val = false`): on a column whose "
                     "first entry is not the literal zero constant but evaluates "
                     "to the zero polynomial, the rival reports that entry while "
                     "the spec demands the selected value be mathematically "
                     "nonzero. Refuted at the length-1 column holding exactly such "
                     "an entry (a product-difference that cancels completely), the "
                     "minimal column on which the structural and mathematical "
                     "tests disagree. Ports the sibling's weak-structtruthy — the "
                     "same attack, but where the sibling had to speak of an opaque "
                     "negative status code, this carrier lets the pseudo-zero be a "
                     "literal the verifier computes with.",
        "witness": _w_some(f"[{_PSEUDO_ZERO}]", 0, _PSEUDO_ZERO, "C2"),
    },

    # ---- never selects the leading entry ----
    {
        "id": "weak-skip-leading",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain rival: correct on every column whose first live entry is
        # at position >= 1, but the scan starts one position in, so a leading live
        # entry is never selected.
        "module": _swap(
            _BASE, _I_LOOP,
            "  let mut i := 1\n"
            "  for x in col.tail do\n"
            "    if isMathZero x = false then\n"
            "      return some (i, x)\n"
            "    i := i + 1\n"
            "  return none"),
        "refinement": "correct wherever the first live entry sits at position >= 1, "
                      "but it never selects position 0. A faithful real counterpart "
                      "that began the search one row in either eliminates against "
                      "the wrong row (a different quantity than the one the F2P "
                      "determinant assertions pin) or wrongly reports that no entry "
                      "qualifies, collapsing a minor to zero that is not zero. "
                      "Either way the computed determinants differ from the "
                      "asserted ones, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from C4 (the `none` arm: `∀ e ∈ col, isMathZero e = "
                     "true`): on a length-1 column whose single entry is live, the "
                     "rival scans nothing and reports `none`, but that entry is not "
                     "mathematically zero. Equivalently C0/C1 would be violated on "
                     "a longer column where it skips to a later live entry. "
                     "Partial-domain (leading position). Refuted at the length-1 "
                     "live column — a point where every other rival here behaves "
                     "differently. Ports the sibling's weak-skipfirst.",
        "witness": _w_none("[PExpr.const 3]", "(PExpr.const 3)"),
    },

    # ---- selects the LAST live entry instead of the first ----
    {
        "id": "weak-last-live",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps overwriting the candidate as the scan proceeds, so it reports the
        # HIGHEST live position rather than the lowest. Agrees with gold on every
        # column with at most one live entry.
        "module": _swap(
            _BASE, _I_LOOP,
            "  let mut i := 0\n"
            "  let mut best : Option (Nat × PExpr) := none\n"
            "  for x in col do\n"
            "    if isMathZero x = false then\n"
            "      best := some (i, x)\n"
            "    i := i + 1\n"
            "  return best"),
        "refinement": "reports the highest qualifying position instead of the "
                      "lowest. A faithful real counterpart selecting the last "
                      "rather than the first qualifying entry eliminates against a "
                      "different row, and the fraction-free recursion is specified "
                      "for the leading choice — the sign and the accumulated "
                      "divisor both change, so the recursion computes a different "
                      "quantity than the determinants the F2P assertions pin. The "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from C3 (`∀ k e, k < pos → col[k]? = some e → "
                     "isMathZero e = true`): on a column with two live entries the "
                     "rival reports position 1 while position 0 is live, so an "
                     "earlier entry is NOT mathematically zero; the same point also "
                     "breaks the 'first' reading of C0/C1. This is the ONLY rival "
                     "attacking C3 — every other one keeps the earlier-entries "
                     "clause vacuous or true. Partial-domain (columns with two or "
                     "more live entries). Ports the sibling's weak-lastlive.",
        "witness": _w_some("[PExpr.const 2, PExpr.const 5]", 1, "(PExpr.const 5)",
                           "C3", earlier="(PExpr.const 2)"),
    },

    # ---- never reports any pivot ----
    {
        "id": "weak-never-qualifies",
        "kind": "uniqueness",
        "expect": "reject",
        # Degenerate rival: consumes the column and always reports that no entry
        # qualifies. Correct exactly on the all-mathematically-zero columns.
        "module": _swap(
            _BASE, _I_LOOP,
            "  let mut i := 0\n"
            "  for _x in col do\n"
            "    i := i + 1\n"
            "  return none"),
        "refinement": "always reports that no entry qualifies. A faithful real "
                      "counterpart would collapse EVERY minor to zero, so every "
                      "determinant it computes is zero — including the ones the "
                      "surrounding assertions pin to genuinely nonzero symbolic "
                      "values. The suite therefore fails on those, so the faithful "
                      "patch does NOT resolve even though it happens to give the "
                      "right answer on the singular instances of the reported "
                      "family.",
        "rationale": "REJECT from C4 (the `none` arm): reporting `none` obliges "
                     "every entry of the column to be mathematically zero, but "
                     "the probed column has a live entry. Refuted at a length-2 "
                     "column whose LEADING entry is the literal zero constant and "
                     "whose second entry is live — a distinct point from "
                     "weak-skip-leading's, and deliberately one where "
                     "weak-skip-leading is CORRECT, so the two near-miss rivals do "
                     "not share a witness. Supporting degenerate case with a real "
                     "refinement. Ports the sibling's weak-alwaysminusone.",
        "witness": _w_none("[PExpr.const 0, PExpr.const 7]", "(PExpr.const 7)"),
    },

    # ---- reports the position under the wrong origin (out of range) ----
    {
        "id": "weak-out-of-range-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Reports the correct ENTRY but counts its position from the wrong origin,
        # so the reported position can fall outside the column's index range.
        "module": _swap(
            _BASE, _I_LOOP,
            "  let mut i := 0\n"
            "  for x in col do\n"
            "    if isMathZero x = false then\n"
            "      return some (col.length - i, x)\n"
            "    i := i + 1\n"
            "  return none"),
        "refinement": "selects the right entry but reports its position under the "
                      "wrong origin, so the reported position is not a legal index "
                      "of the column. A faithful real counterpart handing the "
                      "consumer an out-of-range row offset either indexes outside "
                      "the sub-matrix or swaps the wrong pair of rows before "
                      "eliminating, so the recursion proceeds from a different "
                      "matrix than the one the F2P determinant assertions pin. The "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from C0 (`pos < col.length`): on a length-1 column "
                     "with a live leading entry the rival reports position 1, "
                     "which is not a legal index. This is the ONLY rival attacking "
                     "the range clause C0. Refuted at that length-1 live column "
                     "with a distinct entry value, a boundary point no other "
                     "witness probes. Ports the sibling's weak-len-sentinel — the "
                     "same out-of-range-answer attack, re-expressed for the "
                     "`Option` result idiom, where the wrongness lands in the "
                     "POSITION component rather than in an in-band sentinel "
                     "(this carrier has no in-band sentinel to corrupt).",
        "witness": _w_some("[PExpr.const 4]", 1, "(PExpr.const 4)", "C0"),
    },

    # ---- reports a canonical stand-in instead of the entry itself ----
    {
        "id": "weak-placeholder-value",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED rival (no sibling counterpart — see assessment): reports the
        # correct POSITION but pairs it with a canonical nonzero stand-in instead
        # of the entry actually sitting there. The nagini result is a bare index,
        # so this component does not exist on that carrier and no sibling rival
        # can attack it.
        "module": _swap(
            _BASE, _I_LOOP,
            "  let mut i := 0\n"
            "  for x in col do\n"
            "    if isMathZero x = false then\n"
            "      return some (i, PExpr.const 1)\n"
            "    i := i + 1\n"
            "  return none"),
        "refinement": "reports the right position but a canonical nonzero stand-in "
                      "as the value. The consumer DIVIDES by the reported value, so "
                      "a faithful real counterpart substituting a stand-in divides "
                      "by the wrong quantity: the fraction-free recursion's "
                      "accumulated divisor no longer matches the entries it is "
                      "cancelling against, and the computed determinant differs "
                      "from the asserted one on every instance of the reported "
                      "family whose leading live entry is not that constant. The "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from C1 (`col[pos]? = some val`): the spec pins the "
                     "reported value to be exactly the entry at the reported "
                     "position, and the rival reports a constant instead. This is "
                     "the ONLY rival attacking C1, and C1 is the clause with no "
                     "sibling counterpart at all (the nagini result carries no "
                     "value component). Note the rival still satisfies C2 — its "
                     "stand-in IS mathematically nonzero — so C1 is genuinely "
                     "load-bearing and not implied by C2. Refuted at a length-2 "
                     "column whose leading entry is the literal zero constant and "
                     "whose live entry is a square, a fifth distinct point.",
        "witness": _w_some("[PExpr.const 0, PExpr.mul PExpr.sym PExpr.sym]", 1,
                           "(PExpr.const 1)", "C1"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals of which 1 is the mandatory
# frame-mutation probe) plus 2 AXIOM_TESTS. This bundle models the SAME single
# purely-functional core, so every sibling SPEC case has a counterpart except the
# frame-mutation one, which is vacuous on this carrier. Full accounting:
#
#   sibling case              -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-cheapest              -> pos-pure-recursive            RE-EXPRESSED
#   pos-reorder               -> pos-branch-invert             PORTED (re-proved)
#   admiss-1                  -> admiss-pseudo-zero-column     RE-EXPRESSED
#   weak-structtruthy         -> weak-structural-zero-test     PORTED
#   weak-skipfirst            -> weak-skip-leading             PORTED
#   weak-lastlive             -> weak-last-live                PORTED
#   weak-alwaysminusone       -> weak-never-qualifies          PORTED
#   weak-len-sentinel         -> weak-out-of-range-position    RE-EXPRESSED
#   frame-mutate              -> (none)                        VACUOUS
#   (none)                    -> weak-placeholder-value        ADDED (attacks C1)
#   (none)                    -> pos-distinct-zero-test        ADDED BY AUDIT
#   AXIOM_TESTS (2)           -> (none)                        DROPPED (G-AX)
#
# ADDED BY AUDIT (pos-distinct-zero-test): the two original positives both keep
#   the zero TEST verbatim (pos-pure-recursive calls `isMathZero` unchanged;
#   pos-branch-invert only reorders the branches around it, definitionally), so
#   nothing in the battery showed the spec accepts an impl that decides
#   "mathematically zero" a different way — the one notion the whole modeled
#   behavior turns on. The added positive decides liveness as `(eval x).any
#   (· ≠ 0)`, extensionally equal but not definitionally so (`List.any` and
#   `List.all` reduce through different `Bool` combinators), so the frozen `rfl`
#   bridge fails and the equality is proved by induction on the coefficient list.
#   It is the only positive here that exercises the loop bridge against a
#   genuinely different reduction shape.
#
# FRAME LANE, re-derived by the audit and CONFIRMED vacuous — with the build to
#   show it rather than the argument alone. Attempting the closest analogue of the
#   sibling's frame-mutate (assign into the input inside the loop:
#   `col := col.set i (PExpr.const 0)`) does not fail for any spec reason; Lean
#   refuses it at ELABORATION: "`col` cannot be mutated, only variables declared
#   using `let mut` can be mutated". A function parameter is not assignable, so
#   the mutation cannot even be SPELLED, let alone observed. The variant that
#   Lean does accept — copy the input to a local `let mut c := col` and mutate the
#   copy — is a no-op the spec cannot see, and it is not a frame probe: nothing is
#   aliased. Confirms the port's VACUOUS disposition on machine evidence.
#
# RE-EXPRESSED (pos-pure-recursive): the sibling's cheapest-correct positive
#   materializes its grounded pure fold `first_usable(ToSeq(col), 0)` directly and
#   maps the fold's `len(col)` sentinel to the `-1` result. This carrier has no
#   such named fold to call — the postcondition pins the answer with structural
#   relations over `col` rather than against a fold def — so the faithful analogue
#   is to WRITE the front recursion as the implementation (a pure `where` helper,
#   no mutable state, no monadic loop). It makes the same point the sibling case
#   is there to make: the postcondition is grounded in the input, so computing the
#   first live position IS the correct answer and there is no wrong echo. The
#   sibling's framing-bridge `Assert` has no counterpart: it exists to transfer a
#   property between two nagini trigger phrasings (`ToSeq(col)[t]` vs `col[t]`),
#   which is machinery this carrier does not have.
# RE-EXPRESSED (admiss-pseudo-zero-column): the sibling's admissibility case
#   probes whether its half-permission precondition ADMITS a normal column (may we
#   read the length and an entry?). The frozen obligation here carries NO
#   precondition hypothesis at all — it is `∀ col, problem_spec ...`, total over
#   the carrier — so "is the precondition too strong" is not a question this
#   backend can ask. The honest analogue is the other half of the same worry: is
#   the POSTCONDITION dischargeable at a normal, F2P-shaped input, or is the
#   modeled behavior unsatisfiable exactly where it matters? That is what this
#   case proves, at the smallest column exhibiting the configuration the behavior
#   exists for (a non-trivially-math-zero entry followed by a live one).
# RE-EXPRESSED (weak-out-of-range-position): the sibling returns `len(col)` where
#   the spec demands the `-1` no-pivot sentinel, violating its range clause P1.
#   This carrier has no in-band sentinel — "no entry qualifies" is `none`, a
#   separate arm — so an out-of-range ANSWER cannot be spelled that way. The same
#   attack lands on the position component instead: report the correct entry at a
#   position counted from the wrong origin, which falls outside the index range
#   and so violates C0, the range clause the sibling's P1 corresponds to.
# ADDED (weak-placeholder-value): this backend's result carries a VALUE component
#   the nagini result does not (nagini returns a bare `int` index), so C1
#   (`col[pos]? = some val`) is a load-bearing clause with no sibling counterpart
#   and no sibling rival could attack it. Coverage requires every independent
#   top-level clause be attacked, so the rival is added: it reports the correct
#   position paired with a canonical nonzero stand-in. It is not fabricated for an
#   unmodeled behavior — it attacks a real clause of the SAME modeled spec, and it
#   still satisfies C2, which is what shows C1 is not implied by C2.
# VACUOUS (frame-mutate): the sibling's MANDATORY frame-mutation probe writes
#   `col[i] = 0` into an input carrying only `Acc(..., 1/2)`, so the rejection
#   comes from the permission system rather than from any value mismatch — a
#   property, as the sibling itself argues, that no value-only spec could enforce.
#   Lean is referentially transparent: `col : List PExpr` is an immutable value,
#   there is no `mut` input binder, no aliasing, no fractional permission and no
#   read-only cell to overwrite, so the class collapses entirely. Per the porting
#   map, NO substitute probe is fabricated.
# DIVERGENCE / NON-TERMINATION: the sibling carries no `diverge-*` / `nonterm-*` /
#   `weak-diverge` case, so there is nothing to port. Had it carried one, the class
#   would be VACUOUS on this backend rather than a known hole: `implementation_*`
#   is a total Lean `def` (and this one is a bounded `for` over the input list), so
#   a diverging implementation cannot be written at all. That is specifically a
#   lean fact — on velvet under partial termination semantics it would be a real
#   spec hole (the corpus-wide termination-semantics finding).
# AXIOM_TESTS (2, dropped): the sibling probes its deep-model zero predicate
#   against the real routine (soundness) and its caller-domain containment. Both
#   belong to the axiom lane, which is G-AX's job and which this gate ignores. This
#   bundle declares no `opaque` callee and consumes no `axiom` — the zero test is
#   modeled deeply as `eval` / `isMathZero`, an A-reference validated against the
#   real routine by the differential conformance check — so there is nothing for a
#   spec-lane case to probe here regardless.
#
# POINT SPREAD. The spec has exactly ONE input binder, `col`, so no binder can be
# held fixed while others move; what matters is how many distinct columns the
# rejections probe, and along which axes. The six reject witnesses probe SIX
# DISTINCT columns (pts=6):
#
#   col                                      case                          clause
#   -------------------------------------------------------------------------
#   [pseudo-zero]                            weak-structural-zero-test     C2
#   [const 3]                                weak-skip-leading             C4
#   [const 2, const 5]                       weak-last-live                C3
#   [const 0, const 7]                       weak-never-qualifies          C4
#   [const 4]                                weak-out-of-range-position    C0
#   [const 0, sym*sym]                       weak-placeholder-value        C1
#
# All five independent top-level clauses are attacked, each by at least one rival
# (C4 by two, at deliberately different points). Across the six columns: length
# varies (1, 2); the position of the first live entry varies (0, 1, and none); the
# KIND of mathematically-zero entry varies (the literal zero constant vs. a
# structurally non-trivial product-difference that cancels completely) — that last
# axis being exactly the distinction the modeled behavior exists to draw, and the
# one a rival could otherwise mishandle unnoticed; and the live entry's shape
# varies (integer constant, a square in the indeterminate). The two NEAR-MISS
# rivals are separated on purpose: weak-skip-leading and weak-never-qualifies both
# refute C4, but weak-skip-leading is refuted on the length-1 live column where
# weak-never-qualifies is also wrong, while weak-never-qualifies is refuted on a
# column where weak-skip-leading is CORRECT — so neither witness stands in for the
# other and each rival's claimed sub-domain is demonstrated.
AXIOM_TESTS = []
