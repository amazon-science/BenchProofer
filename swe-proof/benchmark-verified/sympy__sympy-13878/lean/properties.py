"""properties.py — G-PBT falsification battery for sympy__sympy-13878 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start``/``-- impl-end`` and — for a case that
legitimately re-proves — inside ``-- proof-start``/``-- proof-end`` is changed, so
``markers.same_spec`` holds and the single ``theorem correct_arcsinCdf``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff the variant is in
scope AND elaborates with the obligation closed (no ``sorry``/``admit``/
``native_decide``, no new ``axiom``/``theorem``/``lemma``); ``expect:"reject"``
passes iff the variant is in scope AND does NOT verify AND its refutation
``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a translation of
its text. The two bundles model DIFFERENT slices of the same behavior:

  * the nagini sibling models the DISPATCH — a two-valued family tag crossed with
    a two-valued query flag, four reachable inputs, and a coarse
    "which branch was taken" answer code. Its rivals mis-route that dispatch.
  * this Lean bundle models the ANSWER the selected routine assembles: the
    ordered case analysis that the cumulative distribution of a continuous
    variable supported on a bounded interval is handed back as.

So the nagini arguments carry over as attacks on WHICH CASE OFFERS WHICH VALUE
UNDER WHICH GUARD, and — because this carrier is SYNTACTIC — also as attacks on
the case COUNT and the case ORDER, which the nagini branch-tag abstraction could
not express at all.

DEFENDED SURFACE (one modeled behavior, one obligation, five independent
top-level clauses). ``problem_spec_arcsinCdf a b x result`` pins EXACTLY:

  * (K kind)   ``result = CdfObject.caseSplit cs`` — the answer is an explicit
    case analysis, not a single unguarded value and not the unevaluated
    accumulation of the density;
  * (N count)  ``cs.length = 3`` — it carries exactly three cases;
  * (P0)       ``cs[0]? = some ⟨lit 0, lt x a⟩`` — position 0 offers zero under a
    STRICT cutoff at the lower endpoint;
  * (P1)       ``cs[1]? = some ⟨arcsinProfile a b x, le x b⟩`` — position 1
    offers the inverse-sine profile, spelled out over the operands, under a
    NON-STRICT cutoff at the upper endpoint. This is the load-bearing clause;
  * (P2)       ``cs[2]? = some ⟨lit 1, always⟩`` — position 2 offers one under
    the catch-all guard.

There is NO precondition: the modeled routine assembles the same analysis
whatever the operands denote, so the obligation is ``∀ a b x : T`` at EVERY
carrier ``T`` of the ``Term`` signature, with no hypothesis binder to admit.

WHY THE CARRIER RECORDS TERMS, and what that buys the reject lane. The scored
behavior is a single assertion comparing the returned object as a whole symbolic
expression tree. So the answer's SHAPE is part of the answer: the number of
cases, their ORDER, the STRICTNESS of each cutoff, and the term structure of each
value all distinguish one answer from another. Several distinct answers here are
the same function of a real evaluation point — the inverse-sine profile happens
to flatten to zero below the support and saturate at one above it — so a
value-level carrier over the reals would make them indistinguishable, and rivals
that merge cases, reorder them, drop one, or trade a non-strict cutoff for a
strict one would all be behaviourally identical to the frozen solution. They are
NOT identical answers, and this battery attacks exactly those, which is only
possible because the carrier records terms.

WHY THE CARRIER IS A SIGNATURE AND NOT A DATATYPE, and what that costs each
case. ``Term T`` is the signature of the term-builders the answer is assembled
from, over a carrier ``T`` the frozen file leaves ARBITRARY: the answer type, the
on-support value, the postcondition and the obligation are all stated under
``{T : Type} [Term T]``. An implementation therefore receives carrier elements it
can only ASSEMBLE WITH -- there is no way to take one apart, and the signature
carries no laws, so no question about the operands is settled. That is what makes
"which analysis is assembled" the whole of the modeled behavior, and it is why
the frozen file's own inhabiting carrier is declared LAST, after the obligation,
where nothing that assembles an answer can consult it.

Two consequences run through the cases below. Every impl-region variant carries
the same binders, so `List Case` reads `List (Case T)` and a local value binding
reads `: T`. And a reject witness cannot be stated at the abstract carrier: over
an arbitrary carrier a strict cutoff and a non-strict one are not provably
distinct elements (the one-element algebra satisfies the signature and identifies
them), so a refutation there is not available for the rivals that matter. Each
witness therefore DECLARES ITS OWN carrier -- the free algebra ``WTerm``, in
which distinct builders build distinct elements -- and instantiates the spec at
it. The declaration sits inside the witness, so it is appended to the rival's
file and to the frozen solution's file alike and both builds ask the same
question (``pbt_witness.witness_scope_problems`` is the rule this respects). It
is also a legitimate refutation of a universally quantified claim: the frozen
postcondition asserts the required analysis at EVERY carrier, so exhibiting one
carrier at which the rival's answer violates it refutes the rival.

GROUNDING (why the "ungrounded-oracle echo" class is N/A). ``arcsinProfile`` is
not an opaque answer key: it is a transparent ``def`` applying the signature's
own operations to ``a``, ``b`` and ``x``, and ``CdfObject.caseSplit`` is an
ordinary inductive constructor. There is no ``opaque`` callee and no consumed
``axiom`` anywhere in the bundle, so an implementation cannot "echo an oracle" —
assembling that list IS doing the modeled work, and the cheapest honest
implementation is a legitimate positive control, not a cheat.

BINDER STRUCTURE. Three input binders: ``a`` (lower support endpoint), ``b``
(upper support endpoint), ``x`` (the evaluation point). All three are
load-bearing — position 1's value normalizes ``x`` against BOTH endpoints, and
positions 0 and 1 draw their cutoffs at ``a`` and ``b`` respectively. Every
reject witness below is stated at FREE operands (``Term.sym``) of the witness's
own carrier, which is the operand kind on which the whole assembled analysis is
observable, and each names its own distinct operand triple so no two rivals are
refuted at the same point.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen script is tuned to the frozen form), so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that declares the free-algebra carrier described
above, evaluates the rival at one concrete operand triple of it (``simp``/``rfl``
reduce the ``Id.run do`` list-append chain, since that carrier has decidable
equality), instantiates the offending clause, and closes on a constructor
mismatch or a list-index mismatch that ``simp`` decides once the carrier's own
instance is in its rewrite set. Every witness binds
NOTHING in its head — all three operands are concrete ``Term.sym`` literals — so
there are no hypotheses whose joint satisfiability could be in question, and the
consistency probe is not applicable.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` — every term-builder is modeled deeply as a signature operation, and
the one unchanged operation
left outside the model (the algebra layer's case-split constructor) is validated
executably by ``conformance_check.py`` rather than axiomatized. So the nagini
``AXIOM_TESTS`` lane is dropped: that is G-AX's job and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13878"
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
# Frozen regions, verbatim. Every swap's anchor lies ENTIRELY inside the impl
# region or the proof region, so `same_spec` holds by construction and the
# `theorem correct_arcsinCdf` statement is never touched.
# ---------------------------------------------------------------------------

# The impl region's body (between `-- impl-start` and `-- impl-end`), minus the
# declaration head, which every variant keeps.
_IMPL_BODY = """  let mut cs : List (Case T) := []
  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
  return CdfObject.caseSplit cs"""

# Individual impl lines, for surgery that changes ONE case.
_I_CASE0 = "  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]"
_I_CASE1 = ("  cs := cs ++ [{ value := arcsinProfile a b x, "
            "guard := Term.le x b }]")
_I_CASE2 = "  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]"
_I_RETURN = "  return CdfObject.caseSplit cs"

# The proof region's tactic body (between `-- proof-start`'s theorem head and
# `-- proof-end`). Replaced wholesale by the soundness positives, which re-prove
# the SAME statement for a re-shaped impl.
_PROOF_BODY = """  intro a b x
  unfold problem_spec_arcsinCdf implementation_arcsinCdf
  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl"""

# The frozen proof's opening line — the anchor the admissibility positive
# prepends a ground instance to, leaving the rest of the frozen script untouched.
_P_INTRO = "  intro a b x"

assert _BASE.count(_IMPL_BODY) == 1
assert _BASE.count(_PROOF_BODY) == 1
# The carrier is a SIGNATURE, and every variant below is written under its
# binders. Asserted so that a re-presentation of the carrier fails this manifest
# loudly instead of silently shipping variants that no longer share the spec.
assert _BASE.count("class Term (T : Type) where") == 1
assert _BASE.count("{T : Type} [Term T]") == 4


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls that
# MUST verify, else SPEC-TOO-STRONG. Each keeps the obligation's statement
# byte-identical and re-proves it inside the proof region; no helper lemma, no
# new declaration, no assumption token.
# ===========================================================================

# pos-literal-list: assemble the SAME ordered analysis as a single literal list
# instead of by three accumulating appends. Identical answer on every operand
# triple, different control flow. This is the honest cheapest implementation on
# this carrier, and it must verify: the spec pins WHICH ordered analysis comes
# back, and is not permitted to also demand a particular way of building it.
_POS_LITERAL_IMPL = """  return CdfObject.caseSplit
    [{ value := Term.lit 0, guard := Term.lt x a },
     { value := arcsinProfile a b x, guard := Term.le x b },
     { value := Term.lit 1, guard := Term.always }]"""

_POS_LITERAL_PROOF = """  intro a b x
  unfold problem_spec_arcsinCdf implementation_arcsinCdf
  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl"""

# pos-build-by-cons: build the list from the BACK, consing each case onto the
# front in reverse order, instead of appending at the end. Same ordered answer,
# opposite traversal. Re-proved by reducing the cons chain.
_POS_CONS_IMPL = """  let mut cs : List (Case T) := []
  cs := { value := Term.lit 1, guard := Term.always } :: cs
  cs := { value := arcsinProfile a b x, guard := Term.le x b } :: cs
  cs := { value := Term.lit 0, guard := Term.lt x a } :: cs
  return CdfObject.caseSplit cs"""

_POS_CONS_PROOF = """  intro a b x
  unfold problem_spec_arcsinCdf implementation_arcsinCdf
  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl"""

# pos-profile-spelled-inline: do not call the pure helper — spell the case-1
# value out inline, node for node. Definitionally the same term, so it must
# verify; this is what stops the spec from demanding that a particular helper be
# CALLED rather than that a particular value be OFFERED.
_POS_INLINE_IMPL = """  let onSupport : T := Term.div
    (Term.mul (Term.lit 2)
      (Term.arcsin (Term.sqrt (Term.div (Term.sub x a) (Term.sub b a)))))
    Term.pi
  let mut cs : List (Case T) := []
  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
  cs := cs ++ [{ value := onSupport, guard := Term.le x b }]
  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
  return CdfObject.caseSplit cs"""

_POS_INLINE_PROOF = """  intro a b x
  unfold problem_spec_arcsinCdf implementation_arcsinCdf
  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl"""


# ===========================================================================
# ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
# concrete, scored-shaped operand triple. The obligation carries no precondition
# binder, so the nagini "does the callee's Requires hold for the scored input"
# check re-expresses as: discharge the spec predicate BY EVALUATION at the
# operand kind the scored behavior actually uses — three FREE operands — as a
# `have` prepended to the frozen script, then close the frozen obligation
# verbatim. If the modeled behavior were unsatisfiable at exactly such an input
# the `have` would not close (the analogue of PRECOND-TOO-STRONG).
# Nothing is assumed: no new declaration, statement byte-identical.
#
# The operands are drawn from the obligation's OWN carrier `T`, which is in scope
# in the tactic block because the binders `{T : Type} [Term T]` precede the
# theorem's colon. That is the only carrier available at this point in the file —
# the frozen solution's inhabiting carrier is declared after the obligation, on
# purpose — and it is also the stronger reading: satisfiable at a free operand
# triple of EVERY carrier of the signature, not of one chosen one.
# ===========================================================================
_ADMISS_GROUND = """  have _free : problem_spec_arcsinCdf
      (Term.sym "a" : T) (Term.sym "b") (Term.sym "x")
      (implementation_arcsinCdf (Term.sym "a" : T) (Term.sym "b")
        (Term.sym "x")) := by
    unfold problem_spec_arcsinCdf implementation_arcsinCdf
    refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
"""


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real counterpart would NOT resolve the scored behavior, and (b) a witness
# pinning the violation at one concrete operand triple.
# ===========================================================================

# weak-no-case-analysis: hand back the unevaluated accumulation of the density
# instead of any case analysis at all. This IS the modeled defect (the shape
# `Solution_prepatch.lean` carries). Attacks K.
_WEAK_ACCUM_RETURN = "  return CdfObject.accumulateUpTo x"

# weak-collapse-to-bare: hand back the on-support value as a SINGLE UNGUARDED
# term, with no case analysis. Denotationally this is the same function of a real
# evaluation point as the required answer (the profile flattens to zero below the
# support and saturates at one above it), so it is invisible to a value-level
# carrier — and it is a different symbolic object. Attacks K.
_WEAK_BARE_RETURN = "  return CdfObject.bare (arcsinProfile a b x)"

# weak-strict-upper-cutoff: the right three cases in the right order, but the
# upper cutoff traded from NON-STRICT to STRICT. At the upper endpoint the
# profile already reads one, so this rival is again denotationally identical to
# the required answer and structurally different. Attacks P1.
_WEAK_STRICT_CASE1 = ("  cs := cs ++ [{ value := arcsinProfile a b x, "
                      "guard := Term.lt x b }]")

# weak-nonstrict-lower-cutoff: the mirror of the above on the other cutoff —
# trade the STRICT lower cutoff for a non-strict one. At the lower endpoint the
# profile already reads zero, so denotationally identical, structurally
# different. Attacks P0.
_WEAK_NONSTRICT_CASE0 = ("  cs := cs ++ [{ value := Term.lit 0, "
                         "guard := Term.le x a }]")

# weak-reordered-cases: all three required cases, all three required guards, but
# assembled in the reverse order. Because the guards partition the line the same
# way, this is once more the same function and a different answer. Attacks P0/P2
# (position 0 and position 2 both hold the wrong case). This is the rival a model
# that pinned only "which region gets which value", without pinning ORDER, could
# not reject.
_WEAK_REORDER_IMPL = """  let mut cs : List (Case T) := []
  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
  return CdfObject.caseSplit cs"""

# weak-dropped-lower-case: two cases instead of three — omit the below-support
# case entirely and let the profile's own flattening cover that region. Attacks
# N (and P0/P1, which shift up a position). The rival a model that pinned only
# the SET of offered values could not reject.
_WEAK_DROP_IMPL = """  let mut cs : List (Case T) := []
  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
  return CdfObject.caseSplit cs"""

# weak-mirrored-profile: the right shape everywhere, but position 1's value
# normalizes the evaluation point against the endpoints in EXCHANGED positions,
# so the support is traversed backwards. Attacks P1 on the value rather than the
# guard. Unlike the cutoff rivals this one is not even denotationally right.
_WEAK_MIRROR_CASE1 = ("  cs := cs ++ [{ value := arcsinProfile b a x, "
                      "guard := Term.le x b }]")

# weak-profile-nosqrt: a NEAR-MISS on the case-1 value's INNER structure — the
# normalized position without its square root inside the inverse sine. The right
# endpoint values, the wrong profile between them, and a different expression
# tree. Attacks P1.
_WEAK_NOSQRT_IMPL = """  let noRoot : T := Term.div
    (Term.mul (Term.lit 2)
      (Term.arcsin (Term.div (Term.sub x a) (Term.sub b a))))
    Term.pi
  let mut cs : List (Case T) := []
  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
  cs := cs ++ [{ value := noRoot, guard := Term.le x b }]
  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
  return CdfObject.caseSplit cs"""

# weak-lower-case-one: below the support offer the full cumulative probability
# instead of zero. Attacks P0 on the value.
_WEAK_ONE_CASE0 = ("  cs := cs ++ [{ value := Term.lit 1, "
                   "guard := Term.lt x a }]")

# weak-tail-case-zero: beyond the support offer zero instead of one. Attacks P2.
_WEAK_ZERO_CASE2 = ("  cs := cs ++ [{ value := Term.lit 0, "
                    "guard := Term.always }]")


# ---------------------------------------------------------------------------
# Witness scaffolds. Each declares the witness's OWN carrier (below), evaluates
# the rival at one concrete triple of free operands of it (the kind on which the
# whole assembled analysis is observable), instantiates the offending clause, and
# closes by `simp` over that carrier's own instance, which decides its constructor
# and list-index equalities. `himpl` is what makes each witness FAIL on the frozen
# solution: it states the rival's answer, which the frozen impl does not have.
#
# WHY THE WITNESS BRINGS A CARRIER. The frozen postcondition is stated at an
# arbitrary carrier of the `Term` signature, and the signature has no laws, so at
# that carrier a strict cutoff and a non-strict one are not provably distinct
# elements: the one-element algebra satisfies the signature and identifies every
# term with every other. A refutation therefore has to be stated somewhere the
# builders are known to be distinct, and the free algebra is the canonical such
# place. Declaring it INSIDE the witness is what keeps the two builds comparable:
# the snippet is appended to the rival's file and to the frozen solution's file
# alike, so both sides have the carrier and gold's failure is a satisfied spec
# rather than an unknown name (`pbt_witness.witness_scope_problems`). And one
# carrier is enough: the postcondition claims the required analysis at EVERY
# carrier, so a single carrier at which the rival's answer violates it refutes
# the rival.
#
# The frozen solution's own inhabiting carrier cannot be used for this: it lives
# in the proof region, deliberately after the obligation, and `witness_file`
# strips that region before appending the witness.
_WPRELUDE = """/-- The witness's own carrier: the free algebra over the signature, in which
distinct builders build distinct elements, so a cutoff's strictness and a value's
term structure are both decidable here. Declared by the witness, hence present in
the rival's build and in the frozen solution's build alike.

The instance is NAMED because the witnesses hand it to `simp` as a rewrite. A
signature operation at this carrier appears as a class projection, and plain
`simp` does not reduce one: measured, `example : ¬ ((Term.lit 1 : WTerm) =
Term.lit 0) := by simp` fails with "simp made no progress", while the same goal
closes under `simp [wTerm]`. Two of the ten rivals below differ from the required
answer only in one builder's ARGUMENT (a literal `1` where `0` is required, or one
node inside the on-support value), and those are exactly the refutations that need
the projections unfolded. -/
inductive WTerm where
  | lit (n : Nat)
  | sym (name : String)
  | pi
  | div (p q : WTerm)
  | mul (p q : WTerm)
  | sub (p q : WTerm)
  | arcsin (e : WTerm)
  | sqrt (e : WTerm)
  | lt (p q : WTerm)
  | le (p q : WTerm)
  | always
  deriving DecidableEq

instance wTerm : Term WTerm where
  lit := WTerm.lit
  sym := WTerm.sym
  pi := WTerm.pi
  div := WTerm.div
  mul := WTerm.mul
  sub := WTerm.sub
  arcsin := WTerm.arcsin
  sqrt := WTerm.sqrt
  lt := WTerm.lt
  le := WTerm.le
  always := WTerm.always

"""


def _ops(a, b, x):
    """The witness's operand triple, at the witness's own carrier."""
    return (f'(Term.sym "{a}" : WTerm)', f'(Term.sym "{b}")',
            f'(Term.sym "{x}")')


def _w_kind(a, b, x, rival_answer):
    """Refute the KIND clause (K): the rival returns something that is not a
    case analysis at all, and the spec admits only `CdfObject.caseSplit`."""
    A, B, X = _ops(a, b, x)
    return (
        _WPRELUDE +
        f"example : ¬ problem_spec_arcsinCdf {A} {B} {X}\n"
        f"    (implementation_arcsinCdf {A} {B} {X}) := by\n"
        f"  have himpl : implementation_arcsinCdf {A} {B} {X}\n"
        f"      = {rival_answer} := by\n"
        f"    rfl\n"
        "  rw [himpl]\n"
        "  rintro ⟨cs, h, -⟩\n"
        "  simp at h\n")


def _w_list(a, b, x, rival_list):
    """Refute a COUNT/POSITION clause (N, P0, P1, P2): the rival returns a case
    analysis, but not the required ordered one. `simp` decides which conjunct of
    the spec fails from the rival's literal list."""
    A, B, X = _ops(a, b, x)
    return (
        _WPRELUDE +
        f"example : ¬ problem_spec_arcsinCdf {A} {B} {X}\n"
        f"    (implementation_arcsinCdf {A} {B} {X}) := by\n"
        f"  have himpl : implementation_arcsinCdf {A} {B} {X}\n"
        f"      = CdfObject.caseSplit\n"
        f"{rival_list} := by\n"
        f"    rfl\n"
        "  rw [himpl]\n"
        "  unfold problem_spec_arcsinCdf\n"
        "  rintro ⟨cs, h, hlen, h0, h1, h2⟩\n"
        "  simp only [CdfObject.caseSplit.injEq] at h\n"
        "  subst h\n"
        "  simp [arcsinProfile, wTerm] at hlen h0 h1 h2\n")


# The literal answer each list-shaped rival returns, at the witness's operands.
def _L(*entries):
    body = ",\n".join("           " + e for e in entries)
    return "        [" + body.lstrip() + "]"


def _c_zero_lt(x, a):
    return (f'{{ value := Term.lit 0, guard := Term.lt (Term.sym "{x}") '
            f'(Term.sym "{a}") }}')


def _c_zero_le(x, a):
    return (f'{{ value := Term.lit 0, guard := Term.le (Term.sym "{x}") '
            f'(Term.sym "{a}") }}')


def _c_one_lt(x, a):
    return (f'{{ value := Term.lit 1, guard := Term.lt (Term.sym "{x}") '
            f'(Term.sym "{a}") }}')


def _c_prof_le(a, b, x, first=None, second=None):
    fa = first if first is not None else a
    sb = second if second is not None else b
    return (f'{{ value := arcsinProfile (Term.sym "{fa}") (Term.sym "{sb}") '
            f'(Term.sym "{x}"),\n             '
            f'guard := Term.le (Term.sym "{x}") (Term.sym "{b}") }}')


def _c_prof_lt(a, b, x):
    return (f'{{ value := arcsinProfile (Term.sym "{a}") (Term.sym "{b}") '
            f'(Term.sym "{x}"),\n             '
            f'guard := Term.lt (Term.sym "{x}") (Term.sym "{b}") }}')


def _c_one_always():
    return "{ value := Term.lit 1, guard := Term.always }"


def _c_zero_always():
    return "{ value := Term.lit 0, guard := Term.always }"


def _c_nosqrt_le(a, b, x):
    return ("{ value := Term.div\n"
            "               (Term.mul (Term.lit 2)\n"
            "                 (Term.arcsin (Term.div "
            f'(Term.sub (Term.sym "{x}") (Term.sym "{a}"))\n'
            f'                   (Term.sub (Term.sym "{b}") '
            f'(Term.sym "{a}")))))\n'
            "               Term.pi,\n"
            f'             guard := Term.le (Term.sym "{x}") '
            f'(Term.sym "{b}") }}')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (must verify; else SPEC-TOO-STRONG)
    # =====================================================================
    {
        "id": "pos-literal-list",
        "kind": "soundness",
        "expect": "verify",
        "module": _swaps(
            _BASE,
            (_IMPL_BODY, _POS_LITERAL_IMPL),
            (_PROOF_BODY, _POS_LITERAL_PROOF),
        ),
        "rationale": "structurally-different CORRECT impl: assemble the SAME "
                     "ordered case analysis as one literal list instead of by "
                     "three accumulating appends. Identical answer on every "
                     "operand triple, different control flow, so K/N/P0/P1/P2 all "
                     "still hold and it MUST verify, else SPEC-TOO-STRONG. This is "
                     "the honest cheapest implementation on this carrier: the spec "
                     "pins WHICH ordered analysis comes back and is not permitted "
                     "to also demand a particular way of building it. Ports the "
                     "nagini guard-reorder positive (there: invert the nested "
                     "dispatch into early-return guards).",
    },
    {
        "id": "pos-build-by-cons",
        "kind": "soundness",
        "expect": "verify",
        "module": _swaps(
            _BASE,
            (_IMPL_BODY, _POS_CONS_IMPL),
            (_PROOF_BODY, _POS_CONS_PROOF),
        ),
        "rationale": "a second structurally-different CORRECT impl, traversing the "
                     "cases in the OPPOSITE direction: cons each case onto the "
                     "front of the accumulator in reverse order rather than "
                     "appending at the end. The assembled list is the same ordered "
                     "analysis, so it must verify. Distinct from "
                     "`pos-literal-list` in that it still builds incrementally — "
                     "what changes is the direction — so between them they show "
                     "the spec constrains the RESULT and neither the number of "
                     "build steps nor their order.",
    },
    {
        "id": "pos-profile-spelled-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swaps(
            _BASE,
            (_IMPL_BODY, _POS_INLINE_IMPL),
            (_PROOF_BODY, _POS_INLINE_PROOF),
        ),
        "rationale": "CORRECT impl that does not call the pure helper at all: it "
                     "spells position 1's value out inline, node for node. "
                     "Definitionally the same term, so it must verify. This is what "
                     "stops the spec from demanding that a particular helper be "
                     "CALLED rather than that a particular value be OFFERED — an "
                     "over-strong spec that pinned the helper's syntactic use would "
                     "reject an otherwise identical implementation, and this case "
                     "is the control for that.",
    },

    # =====================================================================
    # ADMISSIBILITY (must verify; else the obligation is vacuous at the operand
    # kind the scored behavior uses — the PRECOND-TOO-STRONG analogue)
    # =====================================================================
    {
        "id": "admiss-free-operands",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _ADMISS_GROUND + _P_INTRO),
        "rationale": "prepends a CONCRETE instance of the spec predicate to the "
                     "frozen tactic script, at the operand kind the scored behavior "
                     "actually uses — three FREE operands, on which the whole "
                     "assembled analysis is observable — drawn from the "
                     "obligation's own arbitrary carrier and discharged by "
                     "evaluation, after which the frozen obligation is closed "
                     "verbatim. "
                     "Confirms the modeled behavior is SATISFIABLE at exactly such "
                     "an input rather than only universally asserted. If it could "
                     "not be established the obligation would be vacuous at a "
                     "normal input (PRECOND-TOO-STRONG analogue). Nothing is "
                     "assumed: no new declaration, no assumption token, statement "
                     "byte-identical. Ports nagini's admiss-<scored-input> case, "
                     "whose Assert-based witness has no counterpart here — this "
                     "obligation carries no precondition binder at all, since the "
                     "modeled routine assembles the same analysis whatever the "
                     "operands denote.",
    },

    # =====================================================================
    # UNIQUENESS rivals (must reject; else SPEC-TOO-WEAK)
    # =====================================================================
    {
        "id": "weak-no-case-analysis",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _WEAK_ACCUM_RETURN),
        "refinement": "this IS the modeled defect: no case analysis is produced for "
                      "this family at all. A faithful real counterpart supplies no "
                      "precomputed answer, which is precisely the state in which the "
                      "scored behavior is computed by symbolic integration instead — "
                      "yielding, for this family, the unevaluated non-convergent "
                      "integral the issue reports rather than the case analysis the "
                      "scored assertion demands. It therefore does NOT resolve; a "
                      "verifying variant here would be a genuine "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from K: the spec admits only `CdfObject.caseSplit`, and "
                      "the rival returns the unevaluated accumulation of the "
                      "density. Refuted at free operands (a, b, x), the operand kind "
                      "the scored behavior uses; the refutation is a constructor "
                      "mismatch, which `simp` decides.",
        "witness": _w_kind("a", "b", "x", 'CdfObject.accumulateUpTo (Term.sym "x")'),
    },
    {
        "id": "weak-collapse-to-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _WEAK_BARE_RETURN),
        "refinement": "a faithful real counterpart returns the on-support expression "
                      "as a bare unguarded value, with no case analysis around it. "
                      "The scored assertion compares the returned object as a whole "
                      "expression tree against a three-case analysis, and a bare "
                      "product of an inverse sine is not that tree, so it does NOT "
                      "resolve. Note this rival is DENOTATIONALLY IDENTICAL to the "
                      "required answer as a function of a real evaluation point — "
                      "the profile flattens to zero below the support and saturates "
                      "at one above it — which is exactly why a value-level carrier "
                      "could not reject it and this syntactic one can.",
        "rationale": "REJECT from K, and the most important rival in the battery: it "
                      "is the total collapse of the case analysis into a single "
                      "unguarded value. Refuted at free operands (p, q, t) — a "
                      "triple distinct from every other witness's — by constructor "
                      "mismatch.",
        "witness": _w_kind("p", "q", "t",
                           'CdfObject.bare (arcsinProfile (Term.sym "p") '
                           '(Term.sym "q") (Term.sym "t"))'),
    },
    {
        "id": "weak-strict-upper-cutoff",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_CASE1, _WEAK_STRICT_CASE1),
        "refinement": "a faithful real counterpart guards the on-support case with a "
                      "STRICT cutoff at the upper endpoint instead of a non-strict "
                      "one, so the upper endpoint itself falls through to the "
                      "catch-all. The scored assertion compares the returned object "
                      "structurally, and a strict relational is a different object "
                      "from a non-strict one — a different class with a different "
                      "printed form — so it does NOT resolve. Like the bare "
                      "collapse, this rival is DENOTATIONALLY IDENTICAL to the "
                      "required answer (at the upper endpoint the profile already "
                      "reads one, which is what the catch-all offers there), so only "
                      "a carrier that records the relation itself can reject it.",
        "rationale": "REJECT from P1: the spec pins position 1's guard as the "
                      "NON-STRICT cutoff `Term.le x b` and the rival offers the "
                      "strict `Term.lt x b`. Refuted at free operands (lo, hi, pt), "
                      "its own distinct triple; `simp` decides the guard "
                      "constructor mismatch at that list position.",
        "witness": _w_list("lo", "hi", "pt",
                           _L(_c_zero_lt("pt", "lo"),
                              _c_prof_lt("lo", "hi", "pt"),
                              _c_one_always())),
    },
    {
        "id": "weak-nonstrict-lower-cutoff",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_CASE0, _WEAK_NONSTRICT_CASE0),
        "refinement": "the mirror of the strict-upper rival, on the other cutoff: a "
                      "faithful real counterpart guards the below-support case with "
                      "a NON-STRICT cutoff at the lower endpoint, so the lower "
                      "endpoint itself is answered by that case rather than by the "
                      "on-support one. Structurally a different object, so the "
                      "scored assertion fails and it does NOT resolve — and again "
                      "denotationally identical to the required answer, since the "
                      "profile already reads zero at the lower endpoint.",
        "rationale": "REJECT from P0: the spec pins position 0's guard as the STRICT "
                      "cutoff `Term.lt x a` and the rival offers the non-strict "
                      "`Term.le x a`. Attacks the OTHER cutoff from "
                      "`weak-strict-upper-cutoff`, so between them both of the "
                      "spec's strictness choices are shown to be load-bearing "
                      "rather than just one. Refuted at free operands (u, v, w).",
        "witness": _w_list("u", "v", "w",
                           _L(_c_zero_le("w", "u"),
                              _c_prof_le("u", "v", "w"),
                              _c_one_always())),
    },
    {
        "id": "weak-reordered-cases",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _WEAK_REORDER_IMPL),
        "refinement": "a faithful real counterpart submits all three required cases "
                      "with all three required guards, but in REVERSE order — the "
                      "catch-all first. Since the guards partition the line the same "
                      "way this is once more the same function of a real evaluation "
                      "point, and it is a different object: the scored assertion "
                      "compares an ORDERED case list, and a catch-all in position 0 "
                      "makes the rest unreachable. So it does NOT resolve.",
        "rationale": "REJECT from P0 and P2 jointly: the spec pins position 0 as "
                      "zero-under-a-strict-lower-cutoff and position 2 as "
                      "one-under-the-catch-all, and the rival has them exchanged. "
                      "This is the rival a model pinning only WHICH REGION GETS "
                      "WHICH VALUE — a branch index or a region-to-value map — could "
                      "not reject, because every region does get its correct value; "
                      "only the ordered-list shape sees it. Refuted at free operands "
                      "(m, n, s).",
        "witness": _w_list("m", "n", "s",
                           _L(_c_one_always(),
                              _c_prof_le("m", "n", "s"),
                              _c_zero_lt("s", "m"))),
    },
    {
        "id": "weak-dropped-lower-case",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _WEAK_DROP_IMPL),
        "refinement": "a faithful real counterpart submits only TWO cases, omitting "
                      "the below-support one and letting the profile's own flattening "
                      "cover that region. The scored assertion compares against a "
                      "three-case object, so a two-case one is a different tree and "
                      "it does NOT resolve. Denotationally identical again, for the "
                      "same flattening reason.",
        "rationale": "REJECT from N (and from P0/P1, which shift up a position): the "
                      "spec pins the case count at exactly three and the rival "
                      "offers two. This is the rival a model pinning only the SET of "
                      "offered values, or only that each region is answered "
                      "correctly, could not reject. Refuted at free operands "
                      "(d, e, f), and it is the only witness in the battery that "
                      "fires on the count clause.",
        "witness": _w_list("d", "e", "f",
                           _L(_c_prof_le("d", "e", "f"),
                              _c_one_always())),
    },
    {
        "id": "weak-mirrored-profile",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_CASE1, _WEAK_MIRROR_CASE1),
        "refinement": "a faithful real counterpart normalizes the evaluation point "
                      "against the support's endpoints in EXCHANGED positions, so "
                      "the on-support expression traverses the support backwards — "
                      "reporting near-certainty just above the lower endpoint and "
                      "near-impossibility at the upper one. The endpoint difference "
                      "appears with the opposite sign in both numerator and "
                      "denominator, so it is a different expression from the one the "
                      "scored assertion compares against and it does NOT resolve. "
                      "Unlike the cutoff and ordering rivals this one is not even "
                      "denotationally right, so it is the rival a value-level "
                      "carrier COULD also have caught — it is here to show the "
                      "syntactic carrier did not lose that reach.",
        "rationale": "REJECT from P1 on the VALUE rather than the guard: the spec "
                      "pins position 1's value as the profile normalized against the "
                      "lower endpoint first, and the rival passes the two endpoints "
                      "in exchanged positions. Refuted at free operands (g, h, k).",
        "witness": _w_list("g", "h", "k",
                           _L(_c_zero_lt("k", "g"),
                              _c_prof_le("g", "h", "k",
                                         first="h", second="g"),
                              _c_one_always())),
    },
    {
        "id": "weak-profile-nosqrt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _WEAK_NOSQRT_IMPL),
        "refinement": "a faithful real counterpart emits the normalized position "
                      "WITHOUT its square root inside the inverse sine, so the "
                      "on-support expression has the right endpoint values but the "
                      "wrong profile between them — it rises linearly-in-arcsine "
                      "instead of with the square-root profile this family requires, "
                      "and its derivative is not the family's density. Different "
                      "expression tree, so the scored assertion fails and it does "
                      "NOT resolve.",
        "rationale": "REJECT from P1 on the value's INNER structure: this rival gets "
                      "the case count, the case order, both cutoffs and both "
                      "constants exactly right, and differs only in one node deep "
                      "inside position 1's value. It is what stops an "
                      "implementation that has the whole analysis right except the "
                      "profile's shape from slipping through — the deepest near-miss "
                      "in the battery. Refuted at free operands (r, s2, y).",
        "witness": _w_list("r", "s2", "y",
                           _L(_c_zero_lt("y", "r"),
                              _c_nosqrt_le("r", "s2", "y"),
                              _c_one_always())),
    },
    {
        "id": "weak-lower-case-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_CASE0, _WEAK_ONE_CASE0),
        "refinement": "a faithful real counterpart offers ONE below the support, so "
                      "the cumulative probability starts at certainty before any "
                      "mass has accumulated. The scored assertion's first case is "
                      "the constant zero, so the emitted object mismatches and it "
                      "does NOT resolve (and the result is not a cumulative "
                      "distribution function at all: it would fall from one to the "
                      "profile's zero at the lower endpoint).",
        "rationale": "REJECT from P0 on the VALUE: the spec pins position 0's value "
                      "as zero and the rival offers one. Distinct from "
                      "`weak-nonstrict-lower-cutoff`, which attacks the same "
                      "position's GUARD — between them both components of position 0 "
                      "are shown load-bearing. Refuted at free operands (c, d2, z).",
        "witness": _w_list("c", "d2", "z",
                           _L(_c_one_lt("z", "c"),
                              _c_prof_le("c", "d2", "z"),
                              _c_one_always())),
    },
    {
        "id": "weak-tail-case-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_CASE2, _WEAK_ZERO_CASE2),
        "refinement": "a faithful real counterpart offers zero as the catch-all "
                      "value, so beyond the support the cumulative probability "
                      "collapses back to zero instead of remaining at one. The "
                      "scored assertion's final case is the constant one, so the "
                      "emitted object mismatches and it does NOT resolve. (It is "
                      "also non-monotone and its total mass is lost above the "
                      "support.)",
        "rationale": "REJECT from P2 — the clause no other rival attacks on its "
                      "value: the spec pins position 2's value as one and the rival "
                      "offers zero. With this case every one of the five top-level "
                      "clauses (K, N, P0, P1, P2) has at least one rival refuting it, "
                      "and P0/P1 have one for the value and one for the guard "
                      "separately. Refuted at free operands (j, l, o).",
        "witness": _w_list("j", "l", "o",
                           _L(_c_zero_lt("o", "j"),
                              _c_prof_le("j", "l", "o"),
                              _c_zero_always())),
    },
]


# ---------------------------------------------------------------------------
# CLAUSE + POINT SPREAD of the reject witnesses (what `pbt_coverage.py` reports
# as `pts`). Nine rivals, nine DISTINCT operand triples, all five clauses
# attacked, and both components (value / guard) attacked separately where a
# clause has two:
#
#   rival                        operands      clause      what it changes
#   weak-no-case-analysis        (a, b, x)     K           no analysis at all
#   weak-collapse-to-bare        (p, q, t)     K           analysis -> bare value
#   weak-strict-upper-cutoff     (lo, hi, pt)  P1 guard    le -> lt at upper
#   weak-nonstrict-lower-cutoff  (u, v, w)     P0 guard    lt -> le at lower
#   weak-reordered-cases         (m, n, s)     P0 + P2     order reversed
#   weak-dropped-lower-case      (d, e, f)     N           three cases -> two
#   weak-mirrored-profile        (g, h, k)     P1 value    endpoints exchanged
#   weak-profile-nosqrt          (r, s2, y)    P1 value    square root dropped
#   weak-lower-case-one          (c, d2, z)    P0 value    0 -> 1
#   weak-tail-case-zero          (j, l, o)     P2 value    1 -> 0
#
# No rival is refuted at a point another rival already covers, and no two rivals
# attack the same clause the same way. All ten are refuted at the witness's own
# free-algebra carrier, for the reason given with `_WPRELUDE`: the frozen
# postcondition holds at every carrier of the signature, so one carrier at which
# a rival's answer violates it is a refutation of that rival, and the signature
# alone settles no comparison a refutation could rest on.
#
# WHY FOUR OF THESE ARE UNREACHABLE ON A VALUE-LEVEL CARRIER, and so are the
# point of the syntactic one. `weak-collapse-to-bare`,
# `weak-strict-upper-cutoff`, `weak-nonstrict-lower-cutoff`,
# `weak-reordered-cases` and `weak-dropped-lower-case` are all DENOTATIONALLY
# IDENTICAL to the required answer as functions of a real evaluation point: the
# inverse-sine profile flattens to zero below the support and saturates at one
# above it, so merging cases, dropping one, reordering them, or trading a cutoff's
# strictness changes nothing about the value at any point. A carrier over the
# reals cannot distinguish them from the frozen solution by ANY predicate, so a
# battery on such a carrier would have to ship them as positive controls. They
# are nonetheless different ANSWERS, and the scored assertion — a structural
# comparison of whole expression trees — rejects every one of them. That gap is
# the reason this carrier records terms.
#
# The remaining four (`weak-no-case-analysis`, `weak-mirrored-profile`,
# `weak-profile-nosqrt`, `weak-lower-case-one`, `weak-tail-case-zero`) are wrong
# denotationally too, and are kept so the syntactic carrier is shown not to have
# LOST the value-level reach while gaining the structural reach.
# ---------------------------------------------------------------------------
