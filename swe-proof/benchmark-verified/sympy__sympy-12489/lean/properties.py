"""properties.py — G-PBT falsification battery for sympy__sympy-12489 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_mul`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``). The nagini bundle contracts TWO functions over a
heap carrier with fractional permissions: ``make`` (an internal builder) and
``combine`` (a binary combination minted through the LEFT operand's family). This
Lean bundle is CARRIER-NARROWED: it models only the single purely-functional
core — the binary combination of two arrangements — as ``implementation_mul``
over an immutable ``Arr`` structure (``arr : List Int`` mapping, ``fam : Nat``
family tag). There is no separate builder function on this carrier, so every
nagini case attached to ``make`` alone has no standalone counterpart; its
adversarial ARGUMENT (family propagation, content identity) is re-expressed as an
attack on the corresponding clause of ``implementation_mul``. The nagini
frame/permission-mutation class is VACUOUS here (referential transparency — see
the accounting block at the bottom).

DEFENDED SURFACE (one modeled behavior; two independent top-level clauses).
``problem_spec_mul self other result`` pins EXACTLY:

  * (C0 mapping)  ``result.arr = composeArr self.arr other.arr`` — the composed
    mapping is exactly the composition of the two operands' mappings (content
    identity: the mapping is unchanged by the fix and fully pinned to the inputs);
  * (C1 family)   ``result.fam = self.fam`` — the produced arrangement belongs to
    the family of the LEFT operand.

THE BEHAVIOURAL DISCRIMINATOR (the fix). Pre-fix, a combination always minted
onto the BASE family (family ``0``) regardless of the left operand's family;
post-fix it carries the left operand's family. The ``weak-family-base`` rival
below IS that pre-fix behavior (``fam := 0``). The reported defect: a value of a
specialised family, when combined, silently became a base-family value, so a user
who subclassed the arrangement type could not compose instances and keep their
subclass. The FAIL_TO_PASS test pins exactly this: ``type(p * q)`` must be the
left operand's (specialised) class, while ``type(q * p)`` — base on the left —
stays base. C1 is the load-bearing clause for that test.

BINDER STRUCTURE. The spec predicate has THREE input binders: ``self`` (the left
operand — an ``Arr`` with its own ``arr`` and ``fam``), ``other`` (the right
operand), and, implicitly, the two field-projections ``self.fam`` and the
mappings ``self.arr`` / ``other.arr`` that feed ``composeArr``. All are
load-bearing:

  * ``self.fam`` is the sole determinant of C1 — attacked by every family rival,
    and varied across the witnesses (``self.fam ∈ {1,2,3}``);
  * ``other.fam`` must NOT influence the result family — the ``weak-right-family``
    rival abuses exactly this binder (varied ``other.fam ∈ {0,1,2}``);
  * ``self.arr`` / ``other.arr`` jointly determine C0 — attacked by the two
    content rivals over distinct, non-symmetric mappings.

The six reject witnesses probe six DISTINCT input points; no binder is held
constant across them.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini rivals overwrite a
    read-only ``Acc(...,1/2)`` input (``self.kind = 0``; ``array[0] = 0``) to
    satisfy the postcondition vacuously. On this referentially transparent
    carrier there is no heap, no aliasing, no fractional permission and no ``mut``
    INPUT binder: ``self`` / ``other`` are immutable values and a variant cannot
    even express an input write. The class is genuinely vacuous; no substitute
    probe is fabricated (porting map: Lean is referentially transparent).

  * DIVERGENCE / NON-TERMINATION — APPLIES, and is now SHIPPED
    (``diverge-nonterminating-mapping``). An earlier revision of this manifest
    recorded the class as vacuous on the ground that "a diverging implementation
    cannot be written at all on this carrier". That reason is FALSE and was
    corrected by real builds: ``partial def`` elaborates here, so a variant whose
    mapping is a non-terminating recursion IS writable. What actually holds is the
    opposite of vacuity — this bundle carries no
    ``loom.semantics.termination "partial"`` escape, so such an impl does not
    verify vacuously; it simply fails to close C0, which makes it a genuinely
    REFUTABLE wrong impl and therefore shippable in the reject lane rather than a
    known hole. See that case for the witness technique the class requires.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: C0 pins the
    mapping structurally to ``composeArr`` of the two input mappings and C1 pins
    the family to ``self.fam`` — no opaque answer key exists to echo. In its place
    the battery carries honest cheapest-implementation POSITIVE CONTROLS.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: the pre-fix constant base family (attacks C1
    everywhere self.fam≠0); the right operand's family (attacks C1 whenever the
    two families differ); a family that collapses ONLY the specialised family
    onto the base (attacks C1 on the exact F2P sub-domain); and two mapping rivals
    that mis-compose (attack C0).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof (``intro; unfold; by_cases; simp;
⟨rfl,rfl⟩``) is tuned to the frozen form — so a rejection alone attributes nothing
to the spec. Every ``expect="reject"`` case therefore carries a Lean snippet that
states the spec predicate directly at CONCRETE ground inputs and closes by
``decide`` (after unfolding ``composeArr``/``completeTo`` so the mapping computes).
The one exception is the divergence rival, whose mapping has no normal form for
``decide`` to evaluate: its refutation is stated as CONSTANCY over a PAIR of ground
inputs instead (see that case). Every witness binds NOTHING in its head (all
inputs are ground ``Arr`` literals), so there are no hypotheses whose consistency
could be in question. Each was checked with two real ``lake env lean`` builds — to
HOLD of its rival (the rival provably contradicts the spec there) and to FAIL on
the frozen solution (so it is a real discriminator, not a tautology) — and, in the
independent audit, with a third: a FORGERY differing only in dropping the ``¬``
builds CLEAN on the frozen solution and FAILS on the rival, so the frozen side's
exit code demonstrably tracks the claim rather than being a constant.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart mints
the combination onto the wrong family (or mis-composes the mapping), so on the
F2P's subclass-combination witnesses the produced object has the wrong class (or
the wrong array form), and ``test_Permutation_subclassing`` would mismatch, so
the faithful patch would NOT resolve.

Which HALF of that test carries a given rival is not uniform, and the audit
corrected one case that got it wrong. The test has two distinct lanes:

  * the TYPE lane — its ``type(p*q)`` / ``type(q*p)`` assertions. These are the
    family clause C1's business. But both operands there are built from the SAME
    mapping, so a mapping-ORDER rival agrees with the frozen impl at exactly
    those inputs (machine-checked: a witness at that operand tuple fails to
    refute ``weak-mapping-swapped``). The type lane therefore carries the family
    rivals, NOT every mapping rival.
  * the VALUE lane — the test re-runs the whole base ``test_Permutation`` body
    under the subclass, and that body asserts array forms of non-commuting
    products in BOTH operand orders. This is what carries the C0 mapping rivals,
    together with the PASS_TO_PASS product-value tests.

So a C0 refinement must cite the value lane; citing "p*q and q*p have distinct
array forms" is false on this test's own operands. See ``weak-mapping-swapped``.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the composed mapping is modeled deeply as ``composeArr``; the family
step is a direct field copy). The nagini ``AXIOM_TESTS`` re-run the real callee
via ``axiom_check.py`` and belong to G-AX; this gate ignores them, and they are
dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-12489"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The result constructor line: chooses BOTH observable components (the composed
# mapping `perm` and the family `self.fam`). Family rivals reshape only the
# `fam :=` half; the `arr_ident` content rival reshapes the `arr :=` half. Lands
# wholly inside `-- impl-start`/`-- impl-end`.
_I_RETURN = "return { arr := perm, fam := self.fam }"

# The single line that computes the composed mapping inside the non-empty branch.
# The mapping rival reshapes only this line (still inside the impl region).
_I_PERM = ("    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length")

# The whole frozen impl block and proof block, swapped together by the two
# positive controls (a structurally different impl needs its own closing proof;
# the `correct_mul` STATEMENT is preserved byte-identical in each replacement).
_IMPL_BLOCK = (
    "def implementation_mul (self other : Arr) : Arr := Id.run do\n"
    "  let a := self.arr\n"
    "  let b := other.arr\n"
    "  let mut perm : List Int := a\n"
    "  if b ≠ [] then\n"
    "    let bc := completeTo b a.length\n"
    "    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length\n"
    "  return { arr := perm, fam := self.fam }"
)
_PROOF_BLOCK = (
    "theorem correct_mul :\n"
    "    ∀ (self other : Arr),\n"
    "      problem_spec_mul self other (implementation_mul self other) := by\n"
    "  intro self other\n"
    "  unfold problem_spec_mul implementation_mul composeArr\n"
    "  by_cases h : other.arr = []\n"
    "  · simp only [Id.run, h, if_pos, ite_not]\n"
    "    exact ⟨rfl, rfl⟩\n"
    "  · simp only [Id.run, h, ite_not]\n"
    "    exact ⟨rfl, rfl⟩"
)

# The frozen proof's `intro` line — unique in the file — so the admissibility
# positive can prepend a ground `have` without touching the theorem STATEMENT or
# the spec view.
_P_INTRO = "  intro self other"


# ---------------------------------------------------------------------------
# witness scaffold. State the spec predicate at one ground input and close by
# `decide` after unfolding the mapping helpers so the composition computes. The
# input is fully concrete (no head binders), so its "hypotheses" are trivially
# consistent — nothing to be `witness-inconsistent` about.
# ---------------------------------------------------------------------------
def _w(sa, sf, oa, of):
    return (
        f"example : ¬ problem_spec_mul {{ arr := {sa}, fam := {sf} }} "
        f"{{ arr := {oa}, fam := {of} }}\n"
        f"    (implementation_mul {{ arr := {sa}, fam := {sf} }} "
        f"{{ arr := {oa}, fam := {of} }}) := by\n"
        "  unfold problem_spec_mul implementation_mul composeArr completeTo\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the `theorem correct_mul`
    # statement byte-identical and re-proves in-region (no new axiom/lemma).
    # =====================================================================
    {
        "id": "pos-direct-functional",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: drop the imperative `Id.run do`
        # / `let mut` / branch entirely and build the result with a single record
        # literal whose mapping is `composeArr self.arr other.arr` (the pure
        # helper the spec itself uses). Same value on every input; the proof
        # collapses to `⟨rfl, rfl⟩`. (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_IMPL_BLOCK,
             "def implementation_mul (self other : Arr) : Arr :=\n"
             "  { arr := composeArr self.arr other.arr, fam := self.fam }"),
            (_PROOF_BLOCK,
             "theorem correct_mul :\n"
             "    ∀ (self other : Arr),\n"
             "      problem_spec_mul self other (implementation_mul self other) "
             ":= by\n"
             "  intro self other\n"
             "  unfold problem_spec_mul implementation_mul\n"
             "  exact ⟨rfl, rfl⟩"),
        ),
        "rationale": "correct functional reshape: the imperative loop is replaced "
                     "by one record literal whose mapping is the pure `composeArr` "
                     "of the two inputs and whose family is `self.fam`; both C0 and "
                     "C1 hold definitionally, so it MUST verify — else "
                     "SPEC-TOO-STRONG. Re-proved by `⟨rfl, rfl⟩` after unfold; "
                     "statement byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-combine-inline (there: inline the builder call; here the "
                     "combination is expressed directly, no separate builder def "
                     "exists on this carrier).",
    },
    {
        "id": "pos-let-compose",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape that KEEPS the imperative
        # `Id.run do` shape but removes the `let mut` / branch: bind the composed
        # mapping with a single `let` (calling the pure `composeArr`) and return.
        # Same value on every input; proof collapses to `⟨rfl, rfl⟩`.
        # (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_IMPL_BLOCK,
             "def implementation_mul (self other : Arr) : Arr := Id.run do\n"
             "  let composed : List Int := composeArr self.arr other.arr\n"
             "  return { arr := composed, fam := self.fam }"),
            (_PROOF_BLOCK,
             "theorem correct_mul :\n"
             "    ∀ (self other : Arr),\n"
             "      problem_spec_mul self other (implementation_mul self other) "
             ":= by\n"
             "  intro self other\n"
             "  unfold problem_spec_mul implementation_mul\n"
             "  exact ⟨rfl, rfl⟩"),
        ),
        "rationale": "correct imperative reshape: keeps `Id.run do` but drops the "
                     "`let mut`/branch, binding the composed mapping with one `let` "
                     "and returning it with family `self.fam`; C0/C1 both hold, so "
                     "it MUST verify — else SPEC-TOO-STRONG. Re-proved by "
                     "`⟨rfl, rfl⟩`; statement byte-identical, no new axiom/lemma. "
                     "Ports nagini's pos-make-inline (drop the intermediate local).",
    },

    {
        "id": "pos-max-complete",
        "kind": "soundness",
        "expect": "verify",
        # The load-bearing positive of the three. Both shipped positives above
        # reshape only the CONTROL FLOW and then bind the mapping to the spec's own
        # `composeArr`, so C0 holds by `rfl` — they cannot distinguish a spec that
        # pins the mapping from one that merely pins it up to definitional
        # unfolding. This reshape instead recomputes the mapping by a DIFFERENT
        # route: it completes the shorter right mapping to the MAX of the two
        # lengths rather than to the left mapping's length. Observationally equal
        # (the extra identity entries are exactly the ones `drop` discards, and
        # `n - m = 0` when m ≥ n), but NOT definitionally so — the two terms differ
        # under the kernel, `rfl` alone does not close C0, and the proof has to
        # bridge them with a real arithmetic step (`omega` on the two subtractions)
        # before `⟨rfl, rfl⟩` applies. A spec that rejected this would be
        # SPEC-TOO-STRONG against a faithful impl. (Verified: real build, exit 0.)
        "module": _swaps(
            _BASE,
            (_IMPL_BLOCK,
             "def implementation_mul (self other : Arr) : Arr := Id.run do\n"
             "  let a := self.arr\n"
             "  let b := other.arr\n"
             "  let mut perm : List Int := a\n"
             "  if b ≠ [] then\n"
             "    let bc := completeTo b (max a.length b.length)\n"
             "    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length\n"
             "  return { arr := perm, fam := self.fam }"),
            (_PROOF_BLOCK,
             "theorem correct_mul :\n"
             "    ∀ (self other : Arr),\n"
             "      problem_spec_mul self other (implementation_mul self other) "
             ":= by\n"
             "  intro self other\n"
             "  unfold problem_spec_mul implementation_mul composeArr\n"
             "  by_cases h : other.arr = []\n"
             "  · simp only [Id.run, h, if_pos, ite_not]\n"
             "    exact ⟨rfl, rfl⟩\n"
             "  · have hlen : max self.arr.length other.arr.length "
             "- other.arr.length\n"
             "        = self.arr.length - other.arr.length := by omega\n"
             "    simp only [Id.run, h, ite_not, completeTo, hlen]\n"
             "    exact ⟨rfl, rfl⟩"),
        ),
        "rationale": "correct reshape that recomputes the mapping by a different "
                     "route: the shorter right mapping is completed to the MAX of "
                     "the two lengths instead of to the left mapping's length. "
                     "Observationally identical on every input but NOT "
                     "definitionally equal, so unlike the two positives above this "
                     "one does not hold by `rfl` — the proof must bridge the two "
                     "completion lengths with a real arithmetic step. This is what "
                     "makes it the load-bearing soundness probe: it tests that the "
                     "spec pins the mapping's VALUE rather than its syntactic form, "
                     "and rejection would be SPEC-TOO-STRONG. Statement "
                     "byte-identical, no new axiom/lemma (the bridge is a `have` "
                     "inside the existing tactic body).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition, so the
    # nagini precondition-admission self-call re-expresses as: discharge the spec
    # predicate by evaluation at the exact F2P combination shape (both operands
    # the mapping [1,2,3,0], the left of a specialised family 1, the right of the
    # base family 0 — mirroring `CustomPermutation([1,2,3,0]) * Permutation(...)`)
    # as a `have`, then close the frozen obligation verbatim. Nothing is assumed:
    # no new declaration, statement byte-identical, the ground instance is a `have`
    # prepended to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-combination",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_mul { arr := [1,2,3,0], fam := 1 } "
            "{ arr := [1,2,3,0], fam := 0 }\n"
            "      (implementation_mul { arr := [1,2,3,0], fam := 1 } "
            "{ arr := [1,2,3,0], fam := 0 }) := by\n"
            "    unfold problem_spec_mul implementation_mul composeArr completeTo\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the exact F2P combination "
                     "shape (a specialised-family left operand [1,2,3,0] combined "
                     "with a base-family right operand [1,2,3,0]) by evaluation as a "
                     "`have`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior would be unsatisfiable at "
                     "exactly a normal F2P input — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "statement byte-identical, the ground instance is a `have` in "
                     "the existing tactic body. Ports nagini's admiss-combine.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, and (b) a witness pinning the violation
    # at one concrete input, checked to hold of the rival and fail on gold.
    # =====================================================================

    # ---- the fix itself: mint onto the fixed BASE family (attacks C1) ----
    {
        "id": "weak-family-base",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: the combination always mints onto the base family 0
        # regardless of the left operand's family.
        "module": _swap(_BASE, _I_RETURN,
                        "return { arr := perm, fam := 0 }"),
        "refinement": "this IS the pre-fix behavior: the combination is minted onto "
                      "the fixed base family instead of the left operand's family. A "
                      "faithful real patch keeping the base-family construction "
                      "makes every combination produce a base-family value, so a "
                      "value of a specialised family, combined, is silently demoted "
                      "to the base class. The F2P asserts type(p*q) is the left "
                      "operand's specialised class (not the base), so the faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from C1 (family): the spec pins `result.fam = self.fam` "
                     "but the rival emits `0`, which differs whenever self.fam ≠ 0. "
                     "Refuted at self.fam=2 (a specialised family), other.fam=0.",
        "witness": _w("[0]", 2, "[0]", 0),
    },

    # ---- mint through the RIGHT operand's family (attacks C1) ----
    {
        "id": "weak-right-family",
        "kind": "uniqueness",
        "expect": "reject",
        # Reach the family from the WRONG (right) operand: result.fam = other.fam.
        # Correct only on the sub-domain self.fam == other.fam.
        "module": _swap(_BASE, _I_RETURN,
                        "return { arr := perm, fam := other.fam }"),
        "refinement": "reaches the family through the RIGHT operand instead of the "
                      "left. A faithful real patch minting through type(other) "
                      "yields, on the F2P p*q (p specialised, q base), a "
                      "base-family value where the specialised class is required; "
                      "the test asserts type(p*q) is p's class, so the faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from C1 (family): the spec pins `result.fam = self.fam` "
                     "but the rival emits `other.fam`, differing whenever the two "
                     "operands are of different families. Refuted at self.fam=3, "
                     "other.fam=0 (distinct families).",
        "witness": _w("[1,0]", 3, "[1,0]", 0),
    },

    # ---- collapse ONLY the specialised family onto the base (attacks C1) ----
    {
        "id": "weak-family-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: honour the family for every family EXCEPT the specific
        # specialised family 1 (the F2P's subclass), which is collapsed onto the
        # base family 0. Correct for every other self.fam.
        "module": _swap(
            _BASE, _I_RETURN,
            "return { arr := perm, fam := (if self.fam = 1 then 0 else self.fam) }"),
        "refinement": "honours the family for every family except the one mirroring "
                      "the F2P's subclass (family 1), which it still mints as the "
                      "base. A faithful real patch propagating every family except "
                      "that one specialised class would still produce a base value "
                      "for exactly the subclass the F2P constructs; the test asserts "
                      "type(p*q) is that subclass, so the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 (family): the spec pins `result.fam = self.fam` "
                     "but at self.fam=1 the rival returns 0 ≠ 1. Refuted at "
                     "self.fam=1 (the exact collapsed sub-domain), other.fam=0.",
        "witness": _w("[0]", 1, "[0]", 0),
    },

    # ---- ignore the composition: return the left mapping unchanged (attacks C0) ----
    {
        "id": "weak-mapping-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Content cheat: return the LEFT operand's mapping `a` verbatim instead of
        # the composition, dropping C0. Correct only when other is empty / the
        # composition is a no-op.
        "module": _swap(_BASE, _I_RETURN,
                        "return { arr := a, fam := self.fam }"),
        "refinement": "returns the left operand's mapping unchanged instead of the "
                      "composition. A faithful real patch that skipped the "
                      "composition would return the wrong array form for every "
                      "non-trivial combination; the F2P (and the PASS_TO_PASS "
                      "test_mul) compare the product's exact array form, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C0 (mapping): the spec pins "
                     "`result.arr = composeArr self.arr other.arr` but the rival "
                     "emits `self.arr`; these differ whenever the composition is "
                     "non-trivial. Refuted at self.arr=[1,0], other.arr=[1,0] where "
                     "the composition is [0,1] ≠ [1,0].",
        "witness": _w("[1,0]", 1, "[1,0]", 1),
    },

    # ---- compose in the WRONG order (attacks C0) ----
    {
        "id": "weak-mapping-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Content cheat: compose the mappings in the WRONG order (apply the right
        # operand's mapping through the left's). Equal to gold only when the two
        # mappings commute.
        "module": _swap(
            _BASE, _I_PERM,
            "    perm := (b.map (fun i => (completeTo a b.length).getD i.toNat 0)) "
            "++ (completeTo a b.length).drop b.length"),
        "refinement": "composes the two mappings in the reversed order, so for every "
                      "non-commuting pair it returns the array form of the OTHER "
                      "product. NOTE (corrected in audit): this is NOT carried by the "
                      "F2P's own `type(p*q)` / `type(q*p)` assertions. Those are "
                      "stated at two operands built from the SAME mapping, which "
                      "commutes with itself, so both orders agree there and those two "
                      "assertions separate the products by TYPE only — a distinction "
                      "this rival preserves. Measured, not argued: a witness at that "
                      "exact operand tuple (self.arr = other.arr = [1,2,3,0]) FAILS "
                      "to refute this rival (real build, exit 1), i.e. the rival "
                      "agrees with the frozen impl precisely there. What does carry "
                      "it is the product-VALUE lane: the F2P re-runs the whole "
                      "`test_Permutation` body under the subclass, and that body "
                      "(also PASS_TO_PASS in its own right, alongside `test_mul`) "
                      "asserts the array forms of genuinely non-commuting products in "
                      "BOTH operand orders against distinct expected values. A "
                      "faithful real patch that swapped the composition operands "
                      "returns the other order's array form for those pairs, so it "
                      "would NOT resolve. The rejection itself is sound and "
                      "non-vacuous — see this case's own witness, which discriminates "
                      "at a non-commuting pair.",
        "rationale": "REJECT from C0 (mapping): the spec pins "
                     "`composeArr self.arr other.arr` but the rival computes the "
                     "composition with the operands swapped; for non-commuting "
                     "mappings these disagree. Refuted at self.arr=[1,0,2], "
                     "other.arr=[2,1,0] where the two orders give [1,2,0] vs "
                     "[2,0,1].",
        "witness": _w("[1,0,2]", 1, "[2,1,0]", 2),
    },

    # ---- a mapping that never terminates (attacks C0; the DIVERGENCE lane) ----
    {
        "id": "diverge-nonterminating-mapping",
        "kind": "uniqueness",
        "expect": "reject",
        # The family half is kept honest; the MAPPING is produced by a recursion
        # with no decreasing measure, so no input ever yields a value for C0 to be
        # equal to. `partial def` is what makes this expressible: it elaborates on
        # this carrier (so the class is NOT vacuous here), while this bundle grants
        # no semantics option under which a non-terminating impl would discharge
        # the obligation vacuously — it simply cannot close C0.
        "module": _swaps(
            _BASE,
            (_IMPL_BLOCK,
             "partial def spin (n : Nat) : List Int := spin (n + 1)\n\n"
             "def implementation_mul (self other : Arr) : Arr :=\n"
             "  { arr := spin 0, fam := self.fam }"),
            (_PROOF_BLOCK,
             "theorem correct_mul :\n"
             "    ∀ (self other : Arr),\n"
             "      problem_spec_mul self other (implementation_mul self other) "
             ":= by\n"
             "  intro self other\n"
             "  unfold problem_spec_mul implementation_mul\n"
             "  exact ⟨rfl, rfl⟩"),
        ),
        "refinement": "the mapping is computed by a recursion that never bottoms "
                      "out, so no combination ever produces an array form at all. A "
                      "faithful real patch of this shape hangs on the very first "
                      "product, so every array-form assertion in the F2P's value "
                      "lane (and every PASS_TO_PASS product test) fails to complete "
                      "rather than compare — the faithful patch would NOT resolve.",
        "rationale": "REJECT from C0 (mapping): the spec pins "
                     "`result.arr = composeArr self.arr other.arr`, a value that "
                     "depends on both operands, but the rival's mapping is one "
                     "input-independent non-terminating term. The refutation is "
                     "stated as CONSTANCY rather than at a single input, because a "
                     "diverging term has no normal form for `decide` to evaluate: "
                     "the spec forces the mapping to differ between two operand "
                     "pairs whose compositions differ ([0]*[0] = [0] vs "
                     "[1,0]*[1,0] = [0,1]), while this rival returns the SAME term "
                     "for both, so the two spec instances cannot both hold. "
                     "Machine-checked, incl. the mandatory forgery pair: witness "
                     "holds of the rival (exit 0) and fails on the frozen solution "
                     "(exit 1); a type-revealing probe prints the frozen side's "
                     "hypothesis as `True` (i.e. `simp` PROVED the equation there) "
                     "against `spin 0 = [0]` on the rival; and the FLIPPED claim "
                     "(both instances DO hold) builds clean on the frozen solution "
                     "(exit 0) while failing on the rival (exit 1) — so the frozen "
                     "side's exit code tracks the claim.",
        # Constancy refutation: the negation of a CONJUNCTION of two spec
        # instances. Binds nothing in its head (both operand pairs are ground), so
        # there are no hypotheses whose consistency could be in question, and it
        # names only `problem_spec_mul` / `implementation_mul` — never the rival's
        # own helper — so its failure on the frozen solution is a satisfied spec
        # rather than an unknown identifier.
        "witness":
            "example : ¬ (problem_spec_mul { arr := [0], fam := 1 } "
            "{ arr := [0], fam := 0 }\n"
            "      (implementation_mul { arr := [0], fam := 1 } "
            "{ arr := [0], fam := 0 })\n"
            "    ∧ problem_spec_mul { arr := [1,0], fam := 1 } "
            "{ arr := [1,0], fam := 0 }\n"
            "      (implementation_mul { arr := [1,0], fam := 1 } "
            "{ arr := [1,0], fam := 0 })) := by\n"
            "  rintro ⟨⟨h1, -⟩, ⟨h2, -⟩⟩\n"
            "  unfold implementation_mul composeArr completeTo at h1 h2\n"
            "  simp at h1 h2\n"
            "  rw [h1] at h2\n"
            "  simp at h2\n",
    },
]


# ===================================================================== #
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals split across `make` and
# `combine`) plus an AXIOM lane (1 case). This bundle is CARRIER-NARROWED to the
# single purely-functional combination `implementation_mul`; nagini's separate
# builder `make` is not a modeled function here, so `make`-only cases have no
# standalone counterpart and their argument is re-expressed as an attack on the
# corresponding clause of `implementation_mul`. Every sibling case is recorded:
#
#   sibling case                      -> here
#   ---------------------------------------------------------------------------
#   pos-make-inline                   -> pos-let-compose        RE-EXPRESSED
#   pos-combine-inline                -> pos-direct-functional  RE-EXPRESSED
#   admiss-combine                    -> admiss-f2p-combination PORTED
#   frame-combine-self-kind-write     -> (none)                 VACUOUS (ref. transp.)
#   frame-make-array-write            -> (none)                 VACUOUS (ref. transp.)
#   partial-make-collapse-kind1       -> weak-family-collapse   RE-EXPRESSED (onto C1)
#   partial-combine-right-family      -> weak-right-family      PORTED
#   partial-combine-content-drop      -> weak-mapping-identity  RE-EXPRESSED (onto C0)
#   (none)                            -> weak-family-base       ADDED (the fix itself, C1)
#   (none)                            -> weak-mapping-swapped    ADDED (2nd C0 attack)
#   (none)                            -> pos-max-complete        ADDED (non-defeq positive)
#   (none)                            -> diverge-nonterminating-mapping
#                                                                ADDED (divergence lane)
#   AXIOM_TESTS (1)                   -> (none)                 DROPPED (G-AX)
#
# RE-EXPRESSED (positives): nagini's two positives inline the builder call /
#   drop the intermediate local across `make`/`combine`. This carrier has one
#   combination function and no separate builder, so the analogous
#   "structurally different but correct" reshapes are a pure functional record
#   literal (pos-direct-functional) and an imperative `let`-bound compose
#   (pos-let-compose). Both re-prove by `⟨rfl,rfl⟩` (verified with real builds).
# RE-EXPRESSED (partial-make-collapse-kind1): nagini collapses the BUILDER's
#   family at kind==1. There is no builder here, so the same "collapse only the
#   specialised family onto the base" idea is applied to the combination's family
#   clause C1 (weak-family-collapse) — the exact F2P sub-domain.
# RE-EXPRESSED (partial-combine-content-drop): nagini drops content by minting on
#   a fresh empty array (its `is product` identity clause). This carrier's content
#   clause is C0 (`result.arr = composeArr ...`); the analogue returns the left
#   mapping verbatim (weak-mapping-identity), and a second distinct C0 attack
#   composes in the wrong order (weak-mapping-swapped, ADDED) so C0 is probed at
#   two distinct points.
# ADDED (weak-family-base): the pre-fix bug itself — mint onto the fixed base
#   family. This is the headline discriminator of the whole instance (the F2P's
#   type(p*q) assertion); nagini expresses it via its pre-patch model, and it is
#   the strongest C1 attack, so it is carried explicitly.
# VACUOUS (frame/permission mutation): the two nagini frame rivals overwrite a
#   read-only Acc(...,1/2) input. On this referentially transparent carrier there
#   is no heap, no aliasing and no fractional permission, so a variant cannot
#   perform a caller-visible input write and the permission-based REJECT reason
#   has no analogue. AUDIT REFINEMENT of this reason: the closest expressible
#   analogue — shadow-REBINDING the input inside the impl (`let self := { self
#   with fam := 0 }`, or `{ self with arr := 0 :: self.arr.tail }`) and then
#   satisfying the postcondition from the shadowed copy — IS writable here, and
#   was measured: both variants fail to verify, and a ground witness holds of each
#   (build exit 0) while failing on the frozen solution (exit 1), so each is a
#   genuinely refutable wrong impl rather than a vacuity cheat. The reason it
#   cannot cheat is not inexpressibility but SCOPE: `problem_spec_mul` is applied
#   to the caller's `self`/`other`, so a local rebinding cannot reach the terms
#   the spec reads. No case is added because both analogues collapse onto points
#   the battery already probes — the `fam` one is observationally identical to
#   weak-family-base (constant base family) and the `arr` one to the C0 content
#   attacks — and two spellings of one point buy no coverage.
# SHIPPED (divergence) — was recorded VACUOUS, and that was WRONG twice over.
#   Not present in this sibling, so nothing forced the question; the port answered
#   it with "a diverging implementation cannot be written at all on this carrier",
#   which a real build refutes: `partial def spin (n : Nat) : List Int :=
#   spin (n + 1)` elaborates here. A later revision softened this to "writable but
#   nothing to port"; that is also wrong, and in the more consequential direction.
#   This bundle sets no `loom.semantics.termination` option at all (grepped: the
#   frozen file carries no `set_option`), so the `"partial"` semantics under which
#   a non-terminating impl verifies VACUOUSLY — the only setting that makes the
#   class a known hole rather than a shippable case — is not in force. Under the
#   semantics this bundle actually has, a diverging impl simply cannot close C0
#   (measured: exit 1), which makes it a genuinely refutable wrong impl and so
#   belongs in the reject lane. Landed as `diverge-nonterminating-mapping`.
#   The witness needed a different technique from the other five, and this is the
#   part worth recording: a diverging term has NO normal form, so the standard
#   `decide`-at-one-ground-input scaffold (`_w`) cannot be used — it fails on the
#   RIVAL (measured: `Tactic decide failed`, exit 1), which is the half that must
#   succeed. The refutation is instead stated as CONSTANCY: the spec forces the
#   mapping to take two DIFFERENT values at two operand pairs ([0]*[0] = [0] vs
#   [1,0]*[1,0] = [0,1]), while the rival returns one input-independent term for
#   both, so the conjunction of the two spec instances is contradictory. Measured
#   with the full forgery pair — rival exit 0, frozen exit 1; type-reveal prints
#   the frozen side's hypothesis as `True` (`simp` PROVED that equation) against
#   `spin 0 = [0]` on the rival; and the FLIPPED claim builds clean on the frozen
#   solution (exit 0) while failing on the rival (exit 1). None of the
#   `_STUCK_*` screens matches the frozen-side log (checked string by string).
# ADDED (pos-max-complete): an AUDIT-FOUND gap in the soundness lane, not a
#   sibling port. Both original positives reshape only the control flow and then
#   bind the mapping to the spec's own `composeArr`, so C0 holds by `rfl` in each
#   — neither can tell a spec that pins the mapping's VALUE from one that pins its
#   syntactic form, which is exactly what a soundness probe is for. This third
#   positive completes the shorter mapping to the MAX of the two lengths:
#   observationally equal on every input, but NOT definitionally equal, so `rfl`
#   alone does not close C0 and the proof carries a real arithmetic bridge. It
#   verifies (exit 0), so the spec admits a faithful impl whose mapping term
#   differs from the frozen one under the kernel.
#
# POINT SPREAD. The six reject witnesses probe six DISTINCT input tuples:
#   (self.arr, self.fam, other.arr, other.fam)              rival                clause
#     ([0],     2, [0],     0)   weak-family-base       C1
#     ([1,0],   3, [1,0],   0)   weak-right-family      C1
#     ([0],     1, [0],     0)   weak-family-collapse   C1
#     ([1,0],   1, [1,0],   1)   weak-mapping-identity  C0
#     ([1,0,2], 1, [2,1,0], 2)   weak-mapping-swapped   C0
#     ([0],1,[0],0) + ([1,0],1,[1,0],0)  diverge-nonterminating-mapping  C0
#       (a PAIR of tuples, jointly — the constancy refutation needs two points
#        whose compositions differ; see that case)
#   Across them self.fam ∈ {1,2,3}, other.fam ∈ {0,1,2}, and the mappings range
#   over singleton / 2-cycle / 3-element non-symmetric shapes, so no input binder
#   (self.fam, other.fam, self.arr, other.arr) is pinned to one value.
#
# INDEPENDENT AUDIT (adversarial re-derivation; every claim below is a real
# `lake env lean` build, exit codes as observed). Nothing in this block is part of
# the battery the gate executes; it records what was probed so the next reader does
# not have to re-measure it.
#
# Witnesses REBUILT (all 5 original reject cases, both halves, from the manifest
#   bytes): rival build exit 0 / frozen-solution build exit 1 for every case. The
#   gold-side failure is the STRONGEST available shape in all five: `decide` fully
#   reduced and reported the frozen impl's spec instance `is false` for the
#   witness's negation — a semantic refutation of the concrete claim, not a
#   missing identifier, type error, unfolding failure, stuck reduction or timeout.
#   None of the `_STUCK_*` screens in pbt_witness matched any gold log. Statement
#   integrity re-checked independently: the `theorem correct_mul` statement is
#   byte-identical to the frozen file in all cases (compared as raw bytes from the
#   declaration head to `:= by`, not merely whitespace-normalised), and every
#   case's diff is confined to the impl (and, for the positives/admissibility,
#   proof) regions.
#
# SECOND INDEPENDENT AUDIT (re-derived from scratch, not read off the block above).
#   Every one of the five original reject cases additionally passed the FORGERY
#   test, which the prior block did not record: a file differing from the witness
#   ONLY in dropping the `¬` — i.e. asserting the frozen impl is CORRECT at that
#   input — builds CLEAN on the frozen solution (exit 0) and FAILS on the rival
#   (exit 1), in all five. So the frozen side's exit code demonstrably tracks the
#   claim rather than being a constant, and the recorded rejections are real
#   refutations. Also re-confirmed independently: the admissibility case is not
#   trivially satisfiable prose — NEGATING its ground `have` (asserting the spec
#   FAILS at the F2P shape) makes the file fail (exit 1) with `decide` reporting
#   the negation `is false`, so the `have` carries information about that input.
#   The `weak-mapping-swapped` prose claim was re-measured too: a witness at the
#   F2P's own operand tuple (self.arr = other.arr = [1,2,3,0]) fails to refute
#   that rival (exit 1) while refuting weak-family-base at the same tuple (exit 0),
#   confirming the corrected refinement's account of the two test lanes.
#
# SPEC-TOO-WEAK probes (attack D — NEW wrong impls this battery does not contain,
# aimed at the mapping clause C0, the least-probed surface). All REJECTED, so no
# spec hole was found; each was additionally confirmed SEMANTICALLY wrong (its own
# ground witness holds of it and fails on the frozen solution) rather than merely
# tactic-broken:
#   D1 initialise the accumulator to [] instead of the left mapping   rejected
#   D2 skip the identity-completion of the shorter right mapping      rejected
#   D3 out-of-range default 1 instead of 0 in the index lookup        rejected
#   D4 index with `Int.natAbs` instead of `Int.toNat`                 rejected
#   D5 drop the carried-over trailing entries of the completed map    rejected
#   F1/F2 shadow-rebind an input, then answer from the copy           rejected
# SECOND AUDIT's attack-D probes, aimed at sub-domains the six shipped rivals
# leave unattacked (the empty-left-mapping edge, the empty-right guard, the
# out-of-range default, and a family wrong only above a threshold). All REJECTED,
# and each confirmed SEMANTICALLY wrong, not merely tactic-broken — its own ground
# witness holds of it (exit 0) and fails on the frozen solution (exit 1) with
# `decide` reporting the instance `is false`:
#   D6 family = base only when the LEFT mapping is empty              rejected
#   D7 drop the empty-right guard, always take the general branch     rejected
#   D8 out-of-range lookup defaults to the index itself, not 0        rejected
#   D9 family taken modulo 4 (correct below the threshold only)       rejected
#   D10 truncate the result to the left mapping's length              rejected
#   D11 reverse the composed mapping                                  rejected
# SPEC-TOO-STRONG probes (attack E — NEW correct reshapes that MUST verify). All
# VERIFIED, so the spec rejects no faithful impl that was tried:
#   E1 `match other.arr with [] / (x :: xs)` + record literals        verified
#   E2 pure `if other.arr = []` + record literals (no `Id.run`)       verified
#   E3 complete to `max` of the two lengths — observationally equal   verified
#      but NOT definitionally so; needs a real bridging lemma, which
#      is why it is the load-bearing soundness probe of the three.
#      NOW SHIPPED as `pos-max-complete` — see the ADDED note above. The
#      prior audit measured it and left it in prose; a positive that is
#      only described is not a case the gate runs, so it is now one.
#   E1 caveat, worth recording so the next reader does not misread a failed
#      build as a spec hole: the `match` reshape needs its proof to case on
#      `other.arr` in a way that keeps the impl's own `match` reducing. Two
#      closing scripts failed (`simp only [hm]` and an `rcases ... <;> exact
#      ⟨rfl, rfl⟩`, both exit 1 with `rfl ... expected to have type True` —
#      i.e. `simp` had ALREADY closed the goal and the trailing `exact` was
#      then ill-typed), and `cases hm : other.arr with | nil => simp [hm]
#      | cons x xs => simp [hm]` verifies (exit 0). The failures were in the
#      probe's tactic script, NOT in the spec; reporting E1 as
#      SPEC-TOO-STRONG on the strength of the first two would have been wrong.
#
# COVERAGE (advisory reporter): re-run after the two ADDED cases — obl=1 cases=10
# binders=2, ok, no findings. The reject points were checked by hand to be
# MEANINGFUL rather than spellings of one point: each lands on a different
# clause/sub-domain, the two C0 value points differ in whether the two mappings
# commute, and the divergence point differs in KIND (no value exists at all).
#
# SECOND AUDIT — TWO DEFECTS FOUND AND FIXED, both UNDERPORTING rather than
# hollowness. No shipped case was found to pass for a wrong reason: all five
# original rejections survived the forgery test, all three positives were
# confirmed to re-prove in-region with byte-identical statements, and no hole was
# found in the FROZEN spec (17 wrong impls across both audits all rejected).
#   (1) The DIVERGENCE lane was recorded VACUOUS on a reason that is false on this
#       carrier (`partial def` elaborates) and, after the first audit softened it,
#       on a reason that misreads the bundle's own semantics (this file sets no
#       `loom.semantics.termination`, so the `"partial"` vacuity that would make
#       the class a known hole is not in force). The case is shippable and is now
#       shipped: `diverge-nonterminating-mapping`.
#   (2) The SOUNDNESS lane's two positives were both definitional — each binds the
#       mapping to the spec's own `composeArr` and closes C0 by `rfl` — so neither
#       tested that the spec pins the mapping's value rather than its form. The
#       first audit measured a non-definitional reshape (E3) and recorded it only
#       as prose; it is now a case the gate runs: `pos-max-complete`.
# FIRST AUDIT's defect, retained for the record: `weak-mapping-swapped` carried a
# FALSE refinement
# (it claimed the F2P asserts p*q and q*p have distinct array forms; on that
# test's own operands both are built from the same mapping, which commutes with
# itself, so the two orders AGREE there and only the type assertions separate
# them — which this rival preserves). Machine-checked by building a witness at
# that exact operand tuple: it FAILED to refute the rival (exit 1). The rival
# itself is sound and non-vacuous; only the prose was wrong, and it now cites the
# product-VALUE lane that actually carries it. No frozen artifact was touched.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# opaque callee and consumes no axiom (the composed mapping is modeled deeply as
# `composeArr`, the family step is a field copy), so there is nothing to probe and
# the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
