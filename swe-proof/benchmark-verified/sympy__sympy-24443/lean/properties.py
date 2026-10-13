# properties.py — G-PBT falsification battery for sympy__sympy-24443 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   checkRelators (genOf : Sym → Gen) (imageOf : Gen → G)
#                 (rels : List (List (Sym × Int))) : Bool
#   Given a valuation of generators (`genOf` naming each relator symbol's
#   generator, `imageOf` assigning each generator a codomain element of a group
#   `G`), it returns `true` exactly when EVERY defining relator word evaluates to
#   the codomain identity. A relator word is a list of `(symbol, exponent)` blocks;
#   the word's value is the ORDERED left-to-right product of `imageOf (genOf s) ^ p`
#   over its blocks (`evalWord`, a front-recursive product). Crucially the exponent
#   is a signed `Int`: a NEGATIVE exponent is an inverted generator, and Mathlib's
#   `g ^ (p : Int)` gives the genuine integer group power (`g ^ (-1) = g⁻¹`).
#
#   The single postcondition is an IFF that pins the boolean result to the exact
#   membership fact:
#       (result = true) ↔ ∀ r ∈ rels, evalWord genOf imageOf r = 1
#   Both arms are load-bearing: `→` forbids accepting a valuation with a
#   non-vanishing relator; `←` forbids rejecting a valuation whose relators all
#   vanish. `evalWord` is a total, transparent product over the input (no opaque
#   callee, no answer-key), so at a CONCRETE group `decide` computes both the spec
#   and the impl — witnesses need no conditioning on the carrier.
#
# CARRIER NOTE. The nagini sibling abstracted the same per-relator image to a fold
# `image_fold` over two parallel `List[int]` (a block's resolved element handle and
# its signed exponent) behind fractional read permission, with the codomain an
# opaque non-commutative monoid (gid/gmul/gpow). This backend models the identical
# behavior over a genuine Mathlib `Group G`: `evalWord genOf imageOf r`. The
# discriminating content the nagini battery attacked — the NEGATIVE-exponent
# (inverted-generator) block, and the ORDER of a non-commutative product — has a
# direct counterpart here, and each is refutable at a concrete literal input in a
# small non-abelian group (`DihedralGroup 3`). The two lookups `genOf`/`imageOf`,
# which nagini did not model, are transparent function inputs here and are attacked
# directly (a rival that passes the wrong argument through them).
#
# LANES THAT DID NOT PORT (see 'assessment' in the payload):
#   * FRAME-MUTATION (nagini's mandatory class: block_elems / block_pows were held
#     read-only at Acc(list_pred,1/2) and the rival WROTE back — append / index
#     store — to satisfy the postcondition vacuously). Lean is referentially
#     transparent: there is no aliasing and no fractional permission, and the inputs
#     are immutable values, so a "store into a read-only input" rival is not
#     expressible. The whole class is VACUOUS here.
#   * ADMISSIBILITY — PORTED (see `admiss-ground-inverted-word`). An earlier pass
#     recorded this lane N/A because the lean obligation carries NO precondition
#     hypothesis, so nothing could be PRECOND-TOO-STRONG. That reasoning is wrong:
#     on a TOTAL carrier the analogue of an over-strong precondition is the
#     obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
#     positive that discharges the spec predicate at that concrete input — by
#     evaluation, before closing the frozen obligation verbatim — tests directly.
#     The case below does that at the F2P-shaped word carrying an inverted
#     generator, and it is measured load-bearing (the same `have` block FAILS
#     against the drop-negative rival).
#   * DIVERGENCE / NON-TERMINATION — vacuous, and MEASURED so rather than asserted.
#     Two routes exist and both were built. (1) Keeping the frozen `def` and making
#     the body a self-loop is rejected by Lean's own termination checker at
#     elaboration: `error: fail to show termination for
#     implementation_checkRelators`. So within the variant scope (impl region only,
#     signature frozen) a diverging impl is not WRITABLE — the obligation to
#     terminate is discharged by the carrier before the spec is ever consulted.
#     (2) The only way around that is to weaken the binder to `partial def`, which
#     makes the constant irreducible; that variant is also rejected, but with
#     `error: `simp` made no progress` — a tactic-shape failure, NOT attributable
#     to the spec, and no witness can discriminate it because an irreducible
#     constant cannot be evaluated at any concrete input. So this class yields no
#     SHIPPABLE reject case here (a reject case with no discriminating witness is
#     exactly the hollow shape the witness requirement exists to forbid). Recorded
#     vacuous on the strength of (1): divergence is unexpressible in the frozen
#     impl's shape, not merely hard to refute.
#   * AXIOM_TESTS. The word-evaluation is modeled DEEPLY over the Mathlib group (no
#     consumed axiom, no opaque callee); the axiom lane is G-AX's job and this gate
#     ignores it regardless.
from pathlib import Path

INSTANCE = "sympy__sympy-24443"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). --------------------------------------------------------------
# The single per-block multiply — the line that folds block `sp` onto the running
# product. Every value/order/domain rival edits exactly this.
_C_MUL = "        acc := acc * imageOf g ^ sp.2\n"
# The per-relator verdict: fail the whole check the moment a relator does not vanish.
_C_RETFALSE = "      return false\n"
# The guard that decides whether a relator's value is the identity.
_C_IFNE = "    if w ≠ 1 then\n"
# The OUTER loop header — the relator-list walk (as opposed to the word walk).
_C_FORR = "  for r in rels do\n"
# The all-relators-vanished verdict at the very end of the routine.
_C_RETTRUE = "  return true"
for _a in (_C_MUL, _C_RETFALSE, _C_IFNE, _C_FORR, _C_RETTRUE):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"

# The whole frozen impl body (from `:= Id.run do` to the final `return true`) — used
# to swap in the direct-oracle and structural positives.
_IMPL_TAIL = (
    ":= Id.run do\n"
    "  for r in rels do\n"
    "    let w : G := Id.run do\n"
    "      let mut acc : G := 1\n"
    "      for sp in r do\n"
    "        let g := genOf sp.1\n"
    "        acc := acc * imageOf g ^ sp.2\n"
    "      return acc\n"
    "    if w ≠ 1 then\n"
    "      return false\n"
    "  return true"
)
assert _BASE.count(_IMPL_TAIL) == 1, "impl body anchor drifted"

# The frozen proof body (everything after the proof-introducing `:= by`, inside
# proof-start/proof-end). Positives that reshape the impl reprove honestly by
# swapping this for a body that closes the NEW impl — the `theorem correct_*`
# STATEMENT is kept byte-identical and no new axiom/lemma/sorry is introduced.
_PROOF = (
    "  have inner_loop : ∀ (r : List (Sym × Int)) (acc : G),\n"
    "      (forIn r acc (fun sp a => ForInStep.yield (a * imageOf (genOf sp.1) ^ sp.2)) : Id G)\n"
    "        = acc * evalWord genOf imageOf r := by\n"
    "    intro r\n"
    "    induction r with\n"
    "    | nil => intro acc; simp [evalWord]; rfl\n"
    "    | cons hd tl ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      show forIn tl (acc * imageOf (genOf hd.1) ^ hd.2) _ = _\n"
    "      rw [ih]\n"
    "      obtain ⟨s, p⟩ := hd\n"
    "      simp [evalWord, mul_assoc]\n"
    "  simp only [problem_spec_checkRelators, implementation_checkRelators, Id.run, bind, pure]\n"
    "  have key : ∀ r : List (Sym × Int),\n"
    "      (forIn r 1 (fun sp a => ForInStep.yield (a * imageOf (genOf sp.1) ^ sp.2)) : Id G)\n"
    "        = evalWord genOf imageOf r := by\n"
    "    intro r; rw [inner_loop]; simp\n"
    "  simp only [key]\n"
    "  induction rels with\n"
    "  | nil => simp\n"
    "  | cons hd tl ih =>\n"
    "    rw [List.forIn_cons]\n"
    "    by_cases hw : evalWord genOf imageOf hd = 1\n"
    "    · simp only [hw, ne_eq, not_true_eq_false, if_false]\n"
    "      simp only [List.forall_mem_cons, hw, true_and]; exact ih\n"
    "    · simp [hw]\n"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-direct: the cheapest HONEST impl. The postcondition oracle
# `∀ r ∈ rels, evalWord genOf imageOf r = 1` is GROUNDED in the arguments (a total
# transparent product over the input), so directly returning its decision is a
# fully-grounded correct implementation, not an ungrounded-oracle echo — there is no
# WRONG constant to build here (a wrong constant fails the IFF). The proof collapses
# after unfolding + `decide_eq_true_eq`. MUST verify; else SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _swap(_BASE, _IMPL_TAIL,
          ":=\n  decide (∀ r ∈ rels, evalWord genOf imageOf r = 1)"),
    _PROOF,
    "  unfold problem_spec_checkRelators implementation_checkRelators\n"
    "  simp [decide_eq_true_eq]\n",
)

# pos-structural: a structurally-DIFFERENT but behaviourally identical correct impl.
# The frozen impl is a `for`-loop with an early `return false`; this replaces the
# whole body with `rels.all (fun r => decide (evalWord … r = 1))` — a fold with no
# early exit and no mutable accumulator over the relator list, yet the same verdict
# on every input. The frozen inductive proof no longer matches, so the proof body is
# honestly re-closed (statement byte-identical, no new axiom/lemma/sorry). If it
# FAILS => SPEC-TOO-STRONG (postcondition over-fit to one control-flow shape).
_POS_STRUCT = _swap(
    _swap(_BASE, _IMPL_TAIL,
          ":=\n  rels.all (fun r => decide (evalWord genOf imageOf r = 1))"),
    _PROOF,
    "  unfold problem_spec_checkRelators implementation_checkRelators\n"
    "  simp [List.all_eq_true, decide_eq_true_eq]\n",
)


# ===========================================================================
# ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at exactly the
# F2P-shaped input, not merely in the abstract. On this total carrier the frozen
# obligation has no precondition hypothesis, so the analogue of PRECOND-TOO-STRONG
# is the spec predicate being unsatisfiable at the concrete input the suite
# exercises. The word below is the F2P shape: a four-block relator over a small
# non-abelian group in which one block is an INVERTED generator (negative
# exponent), under the identity valuation — the assignment the suite asserts IS a
# homomorphism. `_ground` discharges the spec predicate there by evaluation and
# `_accepts` pins the verdict to `true` (so the admission cannot be read as
# landing in a reject branch); then the frozen obligation is closed verbatim.
# ===========================================================================
_DW = "DihedralGroup 3"
_ID = f"(id : {_DW} → {_DW})"
# sr 0 * r 1 * (sr 0)⁻¹ * r 1 — a genuine D3 relator: it evaluates to the identity
# under the identity valuation ONLY because the inverted block contributes its
# true inverse, which is precisely the sub-domain the spec must pin.
_ADM_RELS = ("[[(DihedralGroup.sr 0, (1:Int)), (DihedralGroup.r 1, 1), "
             "(DihedralGroup.sr 0, -1), (DihedralGroup.r 1, 1)]]")
_POS_ADMISS = _swap(
    _BASE, _PROOF,
    f"  have _ground : problem_spec_checkRelators {_ID} {_ID}\n"
    f"      {_ADM_RELS}\n"
    f"      (implementation_checkRelators {_ID} {_ID}\n"
    f"        {_ADM_RELS}) := by\n"
    f"    unfold problem_spec_checkRelators implementation_checkRelators\n"
    f"    decide\n"
    f"  have _accepts : implementation_checkRelators {_ID} {_ID}\n"
    f"      {_ADM_RELS} = true := by\n"
    f"    unfold implementation_checkRelators\n"
    f"    decide\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly, edits only the impl region, and carries a witness that elaborates
# against the rival and FAILS on the frozen solution. Every witness is stated at a
# CONCRETE input in `DihedralGroup 3` (a small non-abelian group), so `decide`
# computes both the spec and the impl and no conditioning on the carrier is needed.
# ===========================================================================

# drop-negative: the canonical pre-patch bug. Guards the per-block multiply on a
# NON-NEGATIVE exponent, so an inverted-generator block (negative exponent) never
# contributes its factor — exactly the old membership test that silently skipped an
# inverted letter.
_RIV_DROPNEG = _swap(
    _BASE, _C_MUL,
    "        if sp.2 ≥ 0 then\n"
    "          acc := acc * imageOf g ^ sp.2\n",
)

# order-flip: multiplies each block's factor on the LEFT of the running product
# instead of the right, reversing the word. Since the codomain need not be abelian
# this changes the value on multi-block words.
_RIV_FLIP = _swap(
    _BASE, _C_MUL,
    "        acc := imageOf g ^ sp.2 * acc\n",
)

# accept-any: returns `true` even when a relator does NOT vanish — the `←` arm of the
# IFF is abandoned entirely (never rejects). Accepts a valuation that is not a
# homomorphism.
_RIV_ACCEPT = _swap(_BASE, _C_RETFALSE, "      return true\n")

# flip-guard: reverses the identity test (`w = 1` where gold has `w ≠ 1`), so it
# fails exactly the relators that DO vanish and accepts exactly those that do not —
# the postcondition's boolean is inverted.
_RIV_INVERT = _swap(_BASE, _C_IFNE, "    if w = 1 then\n")

# first-only: checks ONLY the first relator word and accepts on the strength of it.
# Added by audit: every pre-existing witness stated its refutation at a SINGLETON
# `rels`, so the OUTER (relator-list) loop was entirely unprobed — a rival that
# walks just one word was admitted by the whole battery.
_RIV_FIRSTONLY = _swap(_BASE, _C_FORR, "  for r in rels.take 1 do\n")

# empty-false: the vacuous boundary. With no relator words at all the ∀ holds
# vacuously, so the spec forces `true`; this returns `false` there. Added by audit:
# the `rels = []` boundary was unprobed.
_RIV_EMPTYFALSE = _swap(
    _BASE, _C_RETTRUE, "  if rels.isEmpty then return false\n  return true")

# natabs: mishandles an inverted generator by taking its exponent's ABSOLUTE value
# (g ^ -p becomes g ^ p) instead of dropping the factor. Added by audit: a distinct
# negative-exponent failure mode from drop-negative, and one that is invisible at
# |p| = 1 in any group of exponent 2, so it needs |p| > 1 to discriminate.
_RIV_NATABS = _swap(_BASE, _C_MUL, "        acc := acc * imageOf g ^ sp.2.natAbs\n")


# Every witness states its refutation over a concrete non-abelian carrier.
#   wa = r 1  (a rotation, order 3),  wb = sr 0,  wc = sr 2  (reflections, order 2).
# Reflections make the group non-abelian, so factor order matters; `r 1` has a
# genuine inverse `r (-1) = r 2`, so negative exponents are non-trivial.
_WIT_PRE = (
    "abbrev Dw := DihedralGroup 3\n"
    "def wa : Dw := DihedralGroup.r 1\n"
    "def wb : Dw := DihedralGroup.sr 0\n"
    "def wc : Dw := DihedralGroup.sr 2\n"
)


def _wit(gen_of, image_of, rels, note):
    """A refutation witness: `¬ problem_spec_checkRelators genOf imageOf rels
    (implementation_checkRelators genOf imageOf rels)` at a CONCRETE input over
    `DihedralGroup 3`, closed by `decide`. Elaborates against a rival whose verdict
    at that input diverges from the frozen one, and fails on gold (which satisfies
    the spec at every input)."""
    return (
        _WIT_PRE +
        f"-- {note}\n"
        f"example : ¬ problem_spec_checkRelators {gen_of} {image_of} {rels}\n"
        f"    (implementation_checkRelators {gen_of} {image_of} {rels}) := by\n"
        f"  unfold problem_spec_checkRelators implementation_checkRelators\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition oracle `∀ r ∈ rels, evalWord genOf imageOf r = 1` is "
            "GROUNDED in the arguments (a total transparent product over the input), "
            "so `implementation := decide (…)` is the honest cheapest CORRECT impl, "
            "not an ungrounded echo; the proof collapses after unfolding + "
            "`decide_eq_true_eq`. The frozen `theorem correct_checkRelators` statement "
            "is kept byte-identical and the proof body is honestly re-closed (no new "
            "axiom/lemma/sorry). Must verify (the postcondition is literally the "
            "decision of the oracle); else SPEC-TOO-STRONG. Also shows the spec is not "
            "echo-vulnerable: a wrong constant result fails the IFF."
        ),
    },
    {
        "id": "pos-structural",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_STRUCT,
        "rationale": (
            "structurally-different but CORRECT impl: the frozen `for`-loop with an "
            "early `return false` and a mutable accumulator is replaced by "
            "`rels.all (fun r => decide (evalWord … r = 1))` — a fold with no early "
            "exit, yet the same verdict on every input (the shape a faithful patch "
            "could equally take). The frozen inductive proof no longer matches, so the "
            "proof body is honestly re-closed with `simp [List.all_eq_true, "
            "decide_eq_true_eq]` (statement byte-identical, no new axiom/lemma/sorry). "
            "If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to one control-flow "
            "shape)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-ground-inverted-word",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "the obligation is SATISFIABLE at exactly the F2P-shaped input, not only "
            "in the abstract. This carrier is total and the frozen obligation carries "
            "no precondition hypothesis, so the analogue of PRECOND-TOO-STRONG is the "
            "spec predicate being unsatisfiable at the concrete input the suite "
            "exercises: a four-block relator word over a small non-abelian group in "
            "which one block is an INVERTED generator, under the identity valuation "
            "(the assignment the suite asserts IS a homomorphism). `_ground` "
            "discharges `problem_spec_checkRelators` there BY EVALUATION (`decide`, "
            "not `rfl` on a restatement) and `_accepts` separately pins the verdict to "
            "`true`, so the admission cannot be satisfied by an input that lands in a "
            "reject branch. Then the frozen obligation is closed verbatim: statement "
            "byte-identical, no new declaration/axiom/lemma/sorry. Measured "
            "load-bearing — the identical `have` block FAILS (`decide` proves the "
            "negation) against the drop-negative rival, so it is not a tautology. If "
            "it FAILS => the modeled behavior is unsatisfiable at the input the F2P "
            "exercises."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "drop-negative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPNEG,
        "refinement": (
            "this IS the pre-change bug. The old word-evaluation walked a relator with "
            "two indices and, for a permutation-group domain, recovered the generator "
            "from the relator letter via a membership test that only succeeded for "
            "NON-inverted letters; an inverted generator (a negative exponent) failed "
            "the test and its factor was handled wrongly, so a valid assignment was "
            "spuriously rejected. Guarding the per-block multiply on a non-negative "
            "exponent reproduces exactly that: the inverted-generator factor is "
            "dropped. The F2P adds the identity map on a group whose presentation "
            "relator contains an inverted generator; dropping its factor makes the "
            "relator's image non-identity, so the routine raises the spurious "
            "'do not define a homomorphism' and the F2P does NOT resolve — a verifying "
            "rival here is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition IFF: on a word with an inverted-generator "
            "block whose factor cancels a preceding block, the true product is the "
            "identity but the guarded impl leaves it non-identity, so the impl returns "
            "false while the oracle's ∀ holds — the `←` arm is violated. Attacks the "
            "signed-exponent handling of `evalWord` (the negative-exponent sub-domain) "
            "and varies the `rels` binder. If it VERIFIES => SPEC-TOO-WEAK (inverted "
            "generators unpinned)."
        ),
        # rels = [[(r1, +1), (r1, -1)]]: true product r1 * r1⁻¹ = 1, so gold => true;
        # the rival drops the -1 block, leaving product r1 ≠ 1, so it => false.
        "witness": _wit("(id : Dw → Dw)", "(id : Dw → Dw)",
                        "[[(wa,(1:Int)),(wa,-1)]]",
                        "inverted-generator block cancels: gold true, rival false"),
    },
    {
        "id": "order-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLIP,
        "refinement": (
            "a patch that accumulates each factor on the wrong side "
            "(`w = images[g]**power * w` instead of `w *= images[g]**power`) computes "
            "the REVERSED product. The codomain is a non-abelian permutation group, so "
            "for a relator whose forward product is the identity the reversed product "
            "need not be; the routine then reports a spurious non-homomorphism and the "
            "F2P does NOT resolve — verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition IFF: `evalWord` pins the ORDERED "
            "left-to-right product, but this impl reverses the order. On a multi-block "
            "word in a non-abelian group the reversed product differs from the forward "
            "one, so the impl's verdict diverges from the oracle's. Attacks factor "
            "ORDER (the multiplication-order structure of `evalWord`) and varies the "
            "`rels` binder (a length-3 word). If it VERIFIES => SPEC-TOO-WEAK (order "
            "unpinned; the non-commutative product admitted reversed)."
        ),
        # rels = [[(a,1),(b,1),(c,1)]] with a*b*c = 1 (c = (a*b)⁻¹ = sr 2): forward
        # product = 1 so gold => true; reversed product c*b*a ≠ 1 so rival => false.
        "witness": _wit("(id : Dw → Dw)", "(id : Dw → Dw)",
                        "[[(wa,(1:Int)),(wb,1),(wc,1)]]",
                        "non-abelian word: forward = 1, reversed ≠ 1"),
    },
    {
        "id": "accept-any",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ACCEPT,
        "refinement": (
            "a patch that never rejects (drops the per-relator failure, always "
            "concluding the mapping is a homomorphism) would declare EVERY assignment "
            "of generators to images a homomorphism. The suite exercises assignments "
            "that are genuinely NOT homomorphisms (a relator's image is non-identity) "
            "and expects them rejected, so this does NOT resolve — "
            "verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the `→` arm of the postcondition IFF: it pins result=true to "
            "'every relator vanishes', but this impl returns true even when a relator's "
            "image is non-identity. Attacks the accept-side of the decision; the "
            "witness varies `imageOf` (a constant non-identity assignment) and `rels`. "
            "If it VERIFIES => SPEC-TOO-WEAK (a non-homomorphism admitted)."
        ),
        # imageOf ≡ wa (r 1, order 3), rels = [[(wa,1)]]: image = r 1 ≠ 1, so the ∀
        # is FALSE and gold => false; the rival returns true regardless.
        "witness": _wit("(id : Dw → Dw)", "(fun _ => wa)", "[[(wa,(1:Int))]]",
                        "non-vanishing relator: gold false, rival accepts"),
    },
    {
        "id": "flip-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INVERT,
        "refinement": (
            "inverting the identity test (fail when the relator image IS the identity, "
            "accept when it is not) is the polar opposite of the intended check; it "
            "rejects genuine homomorphisms and accepts non-homomorphisms alike. Every "
            "relator check in the suite would land on the wrong verdict, so it does NOT "
            "resolve — verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition IFF (both arms): the boolean is inverted "
            "relative to 'every relator vanishes'. On a word whose image is the "
            "identity the impl returns false while the oracle's ∀ holds — the `←` arm "
            "fails. Attacks the polarity of the identity test; the witness varies "
            "`genOf` (a constant lookup) and `rels`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # genOf ≡ wa: both blocks resolve to imageOf wa = wa; rels = [[(wb,1),(wb,-1)]]
        # so the word evaluates to wa^1 * wa^-1 = 1. Gold => true (relator vanishes);
        # the flipped guard fails on w = 1, so rival => false.
        "witness": _wit("(fun _ => wa)", "(id : Dw → Dw)",
                        "[[(wb,(1:Int)),(wb,-1)]]",
                        "vanishing relator: gold true, flipped-guard rival false"),
    },
    {
        "id": "first-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRSTONLY,
        "refinement": (
            "a patch whose relator walk consumes only the first defining relator and "
            "concludes from it alone would accept any assignment that happens to "
            "satisfy the presentation's first relator while violating a later one. The "
            "suite exercises presentations with several defining relators and expects "
            "an assignment failing ANY of them rejected, so this does NOT resolve — "
            "verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the `→` arm of the postcondition IFF: the spec quantifies over "
            "EVERY `r ∈ rels`, but this impl inspects only the first. Added by audit — "
            "the four pre-existing witnesses all state their refutation at a SINGLETON "
            "`rels`, so the OUTER relator-list loop was unprobed and this rival would "
            "have been admitted by the whole battery. The witness varies the `rels` "
            "binder in the dimension none of the others did: LENGTH (two words). If it "
            "VERIFIES => SPEC-TOO-WEAK (the ∀ over relators is not pinned)."
        ),
        # rels = [[(wa,1),(wa,-1)], [(wa,1)]]: the FIRST word vanishes, the SECOND does
        # not, so the ∀ is false and gold => false; the rival never looks past the
        # first word, so it => true.
        "witness": _wit("(id : Dw → Dw)", "(id : Dw → Dw)",
                        "[[(wa,(1:Int)),(wa,-1)],[(wa,(1:Int))]]",
                        "second relator non-vanishing: gold false, take-1 rival true"),
    },
    {
        "id": "empty-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTYFALSE,
        "refinement": (
            "a patch that special-cases 'no defining relators' to a rejection would "
            "refuse every assignment out of a presentation with an empty relator set "
            "(a free domain), where every assignment IS a homomorphism. Such an "
            "assignment is expected accepted, so this does NOT resolve — "
            "verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the `←` arm of the postcondition IFF: over an empty `rels` the "
            "`∀ r ∈ rels` holds VACUOUSLY, so the spec forces `true`, but this impl "
            "returns `false`. Added by audit — no pre-existing witness touched the "
            "`rels = []` boundary, so the vacuous case was unprobed. Varies the `rels` "
            "binder to its empty extreme. If it VERIFIES => SPEC-TOO-WEAK (the vacuous "
            "case is unpinned)."
        ),
        # rels = []: the ∀ is vacuously true so gold => true; the rival short-circuits
        # to false on the empty list.
        "witness": _wit("(id : Dw → Dw)", "(id : Dw → Dw)",
                        "([] : List (List (Dw × Int)))",
                        "no relators: gold true (vacuous), rival false"),
    },
    {
        "id": "exp-natabs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NATABS,
        "refinement": (
            "a patch that resolves an inverted generator by raising its image to the "
            "MAGNITUDE of the exponent rather than the signed exponent handles the "
            "inverted letter wrongly in a second, distinct way: the factor is present "
            "but is the generator's image instead of that image's inverse. On a "
            "relator whose inverted block cancels a preceding one the product comes "
            "out non-identity, so the routine raises the spurious 'do not define a "
            "homomorphism' and the F2P does NOT resolve — "
            "verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the `←` arm of the postcondition IFF: `evalWord` pins the "
            "factor to the SIGNED integer power `imageOf (genOf s) ^ p`, and for p < 0 "
            "that is a genuine inverse, not the |p|-th power. Added by audit as a "
            "second, independent negative-exponent failure mode alongside "
            "drop-negative (which deletes the factor; this one keeps it with the wrong "
            "sign). Note the witness needs |p| > 1 — at |p| = 1 the two spellings "
            "coincide on any involution, so this rival is invisible to a word built "
            "only from reflections, which is why the exponent MAGNITUDE is varied here "
            "and nowhere else in the battery. If it VERIFIES => SPEC-TOO-WEAK (the "
            "exponent's sign is unpinned)."
        ),
        # rels = [[(wa,-2),(wa,2)]] on wa = r 1 (order 3): true product r1⁻² * r1² = 1
        # so gold => true; natAbs makes both blocks r1², product r1⁴ = r1 ≠ 1 => false.
        "witness": _wit("(id : Dw → Dw)", "(id : Dw → Dw)",
                        "[[(wa,(-2:Int)),(wa,2)]]",
                        "|p|>1 inverted block cancels: gold true, natAbs rival false"),
    },
]


# No @ContractOnly axioms and no opaque callees: the word evaluation and the
# per-relator identity check are modeled DEEPLY over the transparent Mathlib
# `Group G` carrier, so the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
