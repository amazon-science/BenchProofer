# properties.py — G-PBT falsification battery for sympy__sympy-24443 (velvet lane).
#
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each case is a
# FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl
# region — and, where a positive reproves, the `prove_correct` body — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries
# a refutation `witness`: a self-contained snippet that ELABORATES against the
# rival and FAILS on the frozen solution, so the rejection is attributable to the
# spec and not to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#
#   method evalWord (assign : Nat → G) (syllables : List (Nat × Int)) return (out : G)
#     ensures out = wordProd assign syllables            <- the SOLE obligation
#
#   `G` is an ARBITRARY `[Group G] [Inhabited G]` — possibly non-abelian. A *word*
#   is a list of `(symbol, exponent)` syllables; `assign` sends each generator
#   symbol to a codomain element. `wordProd` is the ordered left-to-right product
#   of `assign sym ^ p` over the syllables, front-recursive, with `p : Int` a
#   SIGNED exponent (`zpow`): a negative exponent inverts.
#
#   The single `ensures` is an EQUALITY, so the spec admits exactly one output per
#   input — there is no independent conjunct to attack separately, and no weaker
#   arm a rival could satisfy while missing the other. What a rival can abuse is
#   therefore the STRUCTURE of `wordProd`, and each of its four load-bearing
#   features gets its own rival below:
#     (a) EVERY syllable contributes            -> drop-negative, drop-last
#     (b) the exponent is used, and is SIGNED   -> drop-negative, ignore-exponent
#     (c) the SYMBOL selects which element      -> ignore-symbol
#     (d) the product is ORDERED, and the empty
#         word is the identity                  -> order-flip, seed-nonidentity
#
#   `wordProd` is a total, transparent function of the arguments (no opaque
#   callee, no answer-key oracle), so `return wordProd assign syllables` is the
#   honest cheapest CORRECT impl rather than an ungrounded echo — it ships as a
#   positive control, exactly as the nagini sibling ships its `image_fold` echo.
#
# CARRIER NOTE (what the nagini rivals BECAME here). The nagini sibling abstracted
# the same per-syllable image to a fold `image_fold` over two PARALLEL integer
# arrays (a block's resolved element handle and its signed exponent) held behind
# fractional read permission, with the codomain an opaque non-commutative monoid.
# This backend models the identical behavior over a genuine Mathlib `Group G`,
# with the two parallel arrays fused into one `List (Nat × Int)` and the element
# lookup exposed as a first-class function input `assign`. Consequences:
#   * nagini's equal-length precondition (`len(block_elems) == len(block_pows)`)
#     has NO counterpart: pairing is structural in `List (Nat × Int)`, so an
#     unequal-length input is not expressible and the method has no `require` at
#     all. Nagini's `admiss-self-call`, which existed to show that precondition
#     admits a normal F2P-shaped word, therefore has nothing to defend here — see
#     the omissions list.
#   * `assign` is a binder nagini did NOT model (it pre-resolved each block to an
#     element handle). It is attacked directly by `ignore-symbol`.
#
# WITNESS MECHANICS (measured in this workspace; the port's main new work).
# The frozen impl is a Velvet `while` loop, which elaborates to a CCPO fixpoint
# (`forIn Lean.Loop.mk ...` under `invariantGadget`/`decreasingGadget`). That term
# does NOT reduce, so `decide` and `simp` both get STUCK on the frozen solution —
# which is precisely what makes half 2 of the discrimination check land. Two
# routes are used, and each was confirmed to discriminate by real builds:
#   1. Five rivals are loop-free (`foldr`/`foldl`/`take`), so their extracted
#      program COMPUTES. Their witnesses run the extractor, project the `DivM`
#      result out, and `decide` the disequality against `wordProd` at a concrete
#      point over `Multiplicative Int` (the type variable `G` is pinned purely by
#      the shape of the value arguments — there is no explicit instantiation).
#      `decide` cannot see the frozen `while` term, so the same witness fails on
#      gold. IMPORTANT: this asymmetry is not what makes the witness meaningful.
#      A CONTROL was run for every one of these five — the same witness against a
#      loop-free but CORRECT `foldr` rival — and each control fails with
#      "`decide` proved that the proposition ... is false". So the witness tracks
#      the VALUE, not the loop-free shape: a reshaped-but-correct impl does not
#      satisfy it.
#   2. `order-flip` needs a NON-ABELIAN carrier, and no non-abelian group is
#      reachable from the frozen `import Velvet.Std` (re-measured under audit:
#      `Group (Equiv.Perm (Fin 3))` fails to synthesize; `DihedralGroup`,
#      `Matrix`, `FreeGroup`, `Function.End` and `SemidirectProduct` are all
#      `Unknown identifier`; and a witness may not add imports). It therefore
#      CONDITIONS on the carrier instead: it quantifies over two elements and
#      assumes the single disequality `y * x ≠ x * y`. That is one hypothesis
#      about one pair, jointly satisfiable in any non-abelian group, so the gate's
#      consistency probe cannot derive `False` from it (re-confirmed by build).
#      This case is ALSO the one the audit had to REPAIR, and the correction
#      matters more than the mechanism: refuted against the FROZEN solution the
#      witness failed on the UN-REDUCED `forIn Lean.Loop.mk` term rather than on
#      the claim, and the forgery test proved that hollow — the FLIPPED claim
#      (asserting gold is CORRECT at this point) fails against gold with the
#      byte-identical error. The case now carries a `witness_reference`: the
#      loop-free `_REF_DIRECT`, against which the same script normalises and
#      leaves a semantic `⊢ False`, and against which the flipped claim
#      ELABORATES. See the case's own comment for the exit codes.
#
# LANES THAT DID NOT PORT (see `assessment` in the payload for the full list):
#   * FRAME-MUTATION (nagini's MANDATORY class: `block_elems` / `block_pows` were
#     held read-only at half permission and the rival WROTE one back — append /
#     index store — to satisfy the postcondition vacuously). This backend is
#     referentially transparent: there is no aliasing and no fractional
#     permission, the inputs are immutable values, and neither parameter is `mut`.
#     A "store into a read-only input" rival is not expressible, so the class is
#     genuinely VACUOUS here — not a spec hole, and no substitute is fabricated.
#   * DIVERGENCE / NON-TERMINATION. Not a hole in THIS bundle, and not vacuous for
#     the usual referential-transparency reason either — the reason is the solver
#     flag. This bundle runs under `loom.semantics.termination "total"`, as do all
#     500 velvet bundles (none sets `partial`, so the `partial`-cohort hole an
#     earlier version of this line pointed at does not exist).
#     RE-MEASURED UNDER AUDIT, and the port's reading holds: a
#     rival that removes the loop's `decreasing` clause is REJECTED at the
#     ELABORATOR — "Decreasing annotations are required in total correctness
#     semantics" — before any obligation is reached, and the loop's WP is then
#     discharged by an injected `sorry`. The rejection is therefore real and is
#     attributable to the termination semantics rather than to a tactic gap, but
#     it is NOT witness-refutable: the witness file is built from the same rival
#     source, so the SAME elaborator error fires there too (re-measured: exit 1,
#     "Decreasing annotations are required …", the witness never elaborated), and
#     a `sorry`-bearing loop term does not reduce for `decide` either way. The
#     other diverging shape — keeping `decreasing i` but never decrementing `i` —
#     is rejected on the MEASURE goal instead (re-measured: `unsolved goals` on
#     `decreasing_1: i`), and is likewise not witness-refutable. So the class is a
#     rival that is rejected but whose rejection no witness can attest, which is
#     exactly the shape this gate says must NOT ship; it is reported here instead.
#     This is a TOOLING limit of the witness harness on this backend (the witness
#     inherits the rival's uncompilable impl region), not a hole in the spec.
#   * ADMISSIBILITY — NOT a dropped lane; the port's "N/A" was wrong and the
#     audit landed the case (`admiss-f2p-shaped-word`). Nagini's
#     `admiss-self-call` defended its equal-length half-permission precondition,
#     and it is true that this method has NO `require` clause at all (the pairing
#     nagini had to state is structural in `List (Nat × Int)`). But "the frozen
#     obligation has no precondition" is not a reason for the lane to be vacuous:
#     on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the obligation
#     being UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
#     discharges the obligation at that concrete input — by evaluation, as a
#     `have`, before closing the frozen obligation verbatim — tests directly.
#     That is what the case now does, at a four-syllable two-symbol word carrying
#     an inverted generator, under an injective assignment.
#   * AXIOM_TESTS. This bundle declares no `axiom` and consumes no callee (the
#     word product is modeled DEEPLY over the transparent Mathlib group; meta.json
#     records G-AX as `skip`). The axiom lane is G-AX's job and this gate ignores
#     it regardless.
from pathlib import Path

INSTANCE = "sympy__sympy-24443"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. `_GOLD_IMPL` is the WHOLE content strictly inside impl-start/impl-end;
# `_PROOF` is the frozen `prove_correct` block. Both are unique in the file, so
# every variant edits only the impl region (plus, for a positive that genuinely
# needs to reprove, the proof body) and same_spec holds by construction. If the
# frozen solution ever changes, `_swap` raises at import and the manifest breaks
# loudly rather than silently testing a stale shape.
# ---------------------------------------------------------------------------

_GOLD_IMPL = (
    "    let mut result : G := 1\n"
    "    let mut i := syllables.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ syllables.length\n"
    "      invariant result = wordProd assign (syllables.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let s := syllables[i - 1]!\n"
    "      result := assign s.1 ^ s.2 * result\n"
    "      i := i - 1\n"
    "    return result\n"
)

_PROOF = (
    "prove_correct evalWord by\n"
    "  loom_solve\n"
    "  rw [wordProd_drop_step assign syllables i (by omega) (by omega)]\n"
    "  simp_all\n"
)

for _a in (_GOLD_IMPL, _PROOF):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted: {_a[:60]!r}")


def _impl(body):
    """A variant differing from the frozen solution ONLY in the impl region."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_reproved(body, proof):
    """A variant that reshapes the impl AND re-closes the obligation honestly.

    The `prove_correct evalWord` header is preserved (variant_scope rule 2) and
    nothing is assumed — no `sorry`, no new lemma, no `native_decide`.
    """
    return _swap(_impl(body), _PROOF, proof)


# `loom_solve` alone. Every rival below is LOOP-FREE (a `foldr`/`foldl`, so that
# its extracted program computes and its witness can be decided), which means the
# frozen script's trailing `rw [wordProd_drop_step assign syllables i ...]` refers
# to a loop index `i` that no longer exists in the reshaped impl.
#
# This matters for ATTRIBUTION, and it is the single correction the port needed.
# Measured: leaving the frozen script in place makes a rival fail with BOTH the
# genuine unsolved postcondition goal AND `Unknown identifier 'i'` — so the case
# would "reject" partly because the tactic script stopped matching the reshaped
# impl, which is exactly the wrong reason. Every reject case therefore ships with
# the proof body reduced to bare `loom_solve`, which is the WEAKEST honest script
# available: it discharges nothing but the WP plumbing and leaves the frozen
# `ensures` as the residual goal. Re-measured with that in place, all six rivals
# fail with ZERO stale-tactic diagnostics and a residual goal that is literally
# the frozen postcondition, e.g.
#     ⊢ List.foldl (fun acc s => assign s.1 ^ s.2 * acc) 1 syllables
#         = wordProd assign syllables
# so each rejection is attributable to the postcondition alone. Note the
# direction: this makes the rival's job HARDER, not easier — no obligation is
# weakened, the `prove_correct` header is intact, and nothing is assumed.
_PROOF_LOOPFREE = "prove_correct evalWord by\n  loom_solve\n"


# The cheapest CORRECT impl, reused in two roles: it ships as the `pos-direct`
# positive AND serves as the `witness_reference` for the one reject case whose
# refutation cannot be checked against the frozen solution (see `order-flip`).
# Loop-free, so it REDUCES where the frozen `while` term does not.
_REF_DIRECT = _impl_reproved("    return wordProd assign syllables\n", _PROOF_LOOPFREE)


# ===========================================================================
# WITNESS BUILDERS
# ===========================================================================

# Route 1 — a loop-free rival's extracted program COMPUTES, so the refutation is
# stated at a CONCRETE input and closed by `decide`. `Multiplicative Int` is the
# carrier: it is in scope from the frozen `import Velvet.Std` (no import is
# added), it is a genuine `Group` with `DecidableEq`, and negative exponents are
# non-trivial there (`ofAdd 1 ^ (-1) = ofAdd (-1) ≠ 1`). The type variable `G` is
# pinned implicitly, by the shape of the value arguments alone.
#
# The `match ... with | DivM.res r => r | _ => 1` projection is needed because
# `DivM` carries no `DecidableEq` instance in this workspace; projecting into `G`
# reaches an instance that `decide` can actually reduce.
def _wit(assign, syllables, note):
    return (
        f"-- {note}\n"
        "extract_program_for evalWord\n\n"
        f"example : (match evalWordExec {assign} {syllables} with\n"
        "           | DivM.res r => r | _ => 1)\n"
        f"    ≠ wordProd {assign} {syllables} := by\n"
        "  decide\n"
    )


# Two assignments, so the `assign` binder is genuinely VARIED across witnesses:
#   _A_CONST sends every symbol to the same element (symbol-blind);
#   _A_INJ   sends symbol `n` to `ofAdd n`, so DIFFERENT symbols get DIFFERENT
#            elements — the only shape that can catch a rival ignoring `.1`.
_A_CONST = "(fun _ => (Multiplicative.ofAdd (1:Int)))"
_A_INJ = "(fun n => (Multiplicative.ofAdd (n:Int)))"


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): the grounded cheapest impl --------------
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _REF_DIRECT,
        "rationale":
            "the sole `ensures out = wordProd assign syllables` is GROUNDED in "
            "the arguments — `wordProd` is a total, transparent function of "
            "`assign` and `syllables`, not an opaque answer-key — so returning "
            "it directly is the honest cheapest CORRECT implementation rather "
            "than an ungrounded-oracle echo. This is the counterpart of the "
            "nagini sibling's `pos-cheapest-fold`, and carries the same "
            "argument: because the postcondition oracle is fully unfolded in "
            "the inputs, echoing it is correct behavior, not a wrong echo. "
            "Structurally it is maximally different from the frozen backward "
            "`while` loop (no loop, no invariant, no index), so the frozen "
            "trailing `rw [wordProd_drop_step ...]` no longer applies and the "
            "proof is honestly re-closed by `loom_solve` alone — the "
            "`prove_correct evalWord` header is preserved and nothing is "
            "assumed. MUST verify; if it FAILS the postcondition rejects a "
            "correct output (SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): the frozen loop, consistently renamed ---
    {
        "id": "pos-loop-rename",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let mut acc : G := 1\n"
            "    let mut k := syllables.length\n"
            "    while k > 0\n"
            "      invariant 0 ≤ k ∧ k ≤ syllables.length\n"
            "      invariant acc = wordProd assign (syllables.drop k)\n"
            "      done_with k = 0\n"
            "      decreasing k\n"
            "    do\n"
            "      let s := syllables[k - 1]!\n"
            "      acc := assign s.1 ^ s.2 * acc\n"
            "      k := k - 1\n"
            "    return acc\n"
        ).replace("wordProd_drop_step assign syllables i",
                  "wordProd_drop_step assign syllables k"),
        "rationale":
            "the port of the nagini sibling's `pos-loop-rename`: the same "
            "backward per-syllable fold with the accumulator and the index "
            "renamed (`result`/`i` -> `acc`/`k`) consistently EVERYWHERE inside "
            "the impl region, including both loop invariants, the `done_with` "
            "and the `decreasing` clause. No proof obligation is dropped and no "
            "invariant is weakened, so the loop-invariant argument is "
            "byte-equivalent modulo the local names; the proof body's reference "
            "to the drop-step lemma is renamed to match the new index (still "
            "the frozen lemma, no new lemma introduced). A reshape that keeps "
            "the frozen proof structure must verify, else SPEC-TOO-STRONG.",
    },

    # -- ADMISSIBILITY: the obligation is SATISFIABLE at an F2P-shaped word -----
    # LANDED UNDER AUDIT. The port dropped this lane, arguing it is N/A because
    # the method has no `require` at all. That reason is the wrong one: on a total
    # carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    # UNSATISFIABLE at exactly an F2P-shaped input, and a spec no impl can meet at
    # the discriminating input reads exactly like a spec every impl meets. So the
    # lane is tested directly, by discharging the obligation at that concrete
    # input — by evaluation, as a `have`, BEFORE closing the frozen obligation
    # verbatim.
    {
        "id": "admiss-f2p-shaped-word",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_GOLD_IMPL).replace(
            _PROOF,
            "prove_correct evalWord by\n"
            "  have hAdmiss :\n"
            "      wordProd (fun n => (Multiplicative.ofAdd (n:Int)))\n"
            "        [(1,(1:Int)),(0,(1:Int)),(1,(-1:Int)),(0,(1:Int))]\n"
            "        = (1 : Multiplicative Int) := by decide\n"
            "  have hLive :\n"
            "      wordProd (fun n => (Multiplicative.ofAdd (n:Int)))\n"
            "        [(1,(1:Int)),(0,(1:Int)),(1,(1:Int)),(0,(1:Int))]\n"
            "        ≠ (1 : Multiplicative Int) := by decide\n"
            "  loom_solve\n"
            "  rw [wordProd_drop_step assign syllables i (by omega) (by omega)]\n"
            "  simp_all\n", 1),
        "rationale":
            "PASS SOURCE = the sole `ensures out = wordProd assign syllables` is "
            "SATISFIABLE at a concrete F2P-SHAPED word, and satisfiable with the "
            "value the F2P scenario needs. The scenario maps a group's generators "
            "to THEMSELVES — the identity map, a structure-preserving map by "
            "construction — and asks whether each defining relation's word "
            "evaluates to the IDENTITY; the discriminating relation contains an "
            "INVERTED generator. `hAdmiss` evaluates `wordProd` at exactly that "
            "shape — a four-syllable word over TWO distinct symbols, one syllable "
            "carrying a negative exponent — under an INJECTIVE assignment, and "
            "shows the value is `1`. So the spec's post-image at the "
            "inverted-generator input is not merely well-formed but attainable "
            "with the identity value the caller requires. If `wordProd` were "
            "unsatisfiable there — if the signed exponent made the equality "
            "unmeetable at the very input that discriminates — this `have` could "
            "not be discharged and the case would FAIL => PRECOND-TOO-STRONG / "
            "SPEC-UNSATISFIABLE at the F2P input. Both `have`s are LIVE, not "
            "decoration: measured out-of-band, claiming any other value for the "
            "first word FAILS (`decide` proved the proposition false), and "
            "flipping `hLive`'s `≠` to `=` FAILS too — so the pair pins the "
            "value rather than merely mentioning it, and `hLive` additionally "
            "shows the equality is DISCRIMINATING at the neighbouring word that "
            "differs only in that one exponent's sign. The frozen obligation is "
            "then closed verbatim by the frozen script (nothing is weakened, the "
            "`prove_correct evalWord` header is preserved, nothing is assumed), "
            "and the impl region is the frozen one byte-for-byte — this case "
            "varies only the elided proof body, which is where the extra "
            "obligation is discharged.",
    },

    # -- UNIQUENESS: the canonical bug — a negative exponent contributes nothing
    {
        "id": "drop-negative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_reproved(
            "    return syllables.foldr\n"
            "      (fun s acc => (if s.2 ≥ 0 then assign s.1 ^ s.2 else 1) * acc) 1\n", _PROOF_LOOPFREE),
        "refinement":
            "this IS the pre-change behavior, and the reason it does not "
            "resolve is behavioral, not incidental. The routine under change "
            "decides whether a set of generator images defines a structure-"
            "preserving map by evaluating each defining relation word and "
            "checking the value is the identity. The old walk recovered a "
            "generator from a relation letter through a membership test that "
            "only matched NON-inverted letters, so a syllable with a negative "
            "exponent contributed nothing to the product. Guarding the "
            "per-syllable factor on a non-negative exponent reproduces exactly "
            "that. The added F2P scenario maps a group's generators to "
            "THEMSELVES — the identity map, which is a structure-preserving map "
            "by construction — but that group's defining relation contains an "
            "inverted generator. Dropping its factor leaves the relation's "
            "value non-identity, so the routine reports the images do not "
            "define such a map and raises instead of returning, and the "
            "downstream assertion is never reached. So it does NOT resolve, and "
            "a rival that VERIFIED here would be a true "
            "verify-does-not-imply-resolve break.",
        "rationale":
            "REJECTED by the sole `ensures out = wordProd assign syllables`: "
            "`wordProd` contributes `assign sym ^ p` for EVERY syllable and `p` "
            "is a signed `Int` (`zpow`, so a negative `p` inverts), while this "
            "impl substitutes `1` whenever `p < 0`. Attacks features (a) and "
            "(b) of the postcondition — total syllable coverage and the SIGNED "
            "reading of the exponent — on the negative-exponent sub-domain, and "
            "varies the `syllables` binder. Every non-negative syllable is "
            "folded correctly, so the refutation attributes precisely to the "
            "inverted-generator case. If it VERIFIED, negative exponents would "
            "be unpinned (SPEC-TOO-WEAK).",
        # syllables = [(0,-1)]: gold = ofAdd 1 ^ (-1) = ofAdd (-1); the rival
        # substitutes 1. Control (same witness vs a CORRECT loop-free foldr):
        # `decide` proves the proposition FALSE, so this tracks the value.
        "witness": _wit(_A_CONST, "[(0,(-1:Int))]",
                        "a lone inverted syllable: the rival contributes "
                        "nothing where the spec contributes an inverse"),
    },

    # -- UNIQUENESS: the trailing syllable is dropped -------------------------
    {
        "id": "drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_reproved(
            "    return (syllables.take (syllables.length - 1)).foldr\n"
            "      (fun s acc => assign s.1 ^ s.2 * acc) 1\n", _PROOF_LOOPFREE),
        "refinement":
            "the port of the nagini sibling's `partial-drop-last`: an off-by-one "
            "that stops one syllable early, or a forgotten final "
            "multiplication, drops the trailing factor of every non-trivial "
            "relation word. For the F2P scenario's relation the last factor "
            "would be missing, so the word's value is not the identity, the "
            "routine reports the images do not define a structure-preserving "
            "map and raises, and the downstream assertion is never reached — it "
            "does NOT resolve.",
        "rationale":
            "REJECTED by the `ensures`: `wordProd` folds EVERY syllable, but "
            "this impl folds only the first `length - 1`. Attacks feature (a) "
            "at the END of the word — a sub-domain that `drop-negative` (which "
            "is correct on every non-negative syllable, and so correct on this "
            "witness's all-positive word) cannot reach, which is why the two do "
            "NOT share a witness. Varies the `syllables` binder to a "
            "length-2 all-positive word. If it VERIFIED, the trailing factor "
            "would be unpinned (SPEC-TOO-WEAK).",
        # syllables = [(0,1),(0,1)]: gold = ofAdd 2; the rival keeps one factor
        # and returns ofAdd 1. All exponents POSITIVE, so this input separates
        # `drop-last` from `drop-negative` (which is correct here).
        "witness": _wit(_A_CONST, "[(0,(1:Int)),(0,(1:Int))]",
                        "an all-positive two-syllable word: the rival is short "
                        "by the trailing factor"),
    },

    # -- UNIQUENESS: the exponent's magnitude is ignored ----------------------
    {
        "id": "ignore-exponent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_reproved(
            "    return syllables.foldr (fun s acc => assign s.1 ^ (1:Int) * acc) 1\n", _PROOF_LOOPFREE),
        "refinement":
            "a patch that includes each syllable's element but raises it to a "
            "fixed power of one — reading the syllable's generator while "
            "discarding its exponent — computes the wrong value for any "
            "relation word carrying a repeated generator, which is the normal "
            "shape of a defining relation (a rotation of finite order appears "
            "as that generator raised to its order). The word's value is then "
            "not the identity, so the routine reports the images do not define "
            "a structure-preserving map and the F2P does NOT resolve.",
        "rationale":
            "REJECTED by the `ensures`: `wordProd` raises each element to that "
            "syllable's exponent `p`, but this impl always uses `1`. Attacks "
            "feature (b) — that the exponent is READ at all — on the "
            "|exponent| > 1 sub-domain, which neither `drop-negative` nor "
            "`drop-last` reaches (both are exact on a single positive "
            "syllable). Varies the `syllables` binder to a one-syllable word "
            "with exponent 2. If it VERIFIED, the exponent's magnitude would be "
            "unpinned (SPEC-TOO-WEAK).",
        # syllables = [(0,2)]: gold = ofAdd 2; the rival returns ofAdd 1.
        "witness": _wit(_A_CONST, "[(0,(2:Int))]",
                        "a single syllable of exponent 2: the rival collapses "
                        "it to exponent 1"),
    },

    # -- UNIQUENESS: the wrong argument is passed to the element lookup -------
    {
        "id": "ignore-symbol",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_reproved(
            "    return syllables.foldr (fun s acc => assign 0 ^ s.2 * acc) 1\n", _PROOF_LOOPFREE),
        "refinement":
            "a patch that resolves every syllable through a FIXED generator "
            "instead of the one the syllable names — the failure mode of "
            "mis-threading the symbol-to-generator lookup while rewriting the "
            "walk — evaluates every relation word as if it were written over a "
            "single generator. On any group with more than one generator that "
            "is the wrong element, so a genuine structure-preserving map is "
            "reported as not being one and the F2P does NOT resolve. This rival "
            "has NO nagini counterpart: nagini pre-resolved each block to an "
            "element handle before the modeled function ran, so the lookup was "
            "outside its carrier. Here `assign` is a first-class input, so the "
            "argument passed to it is attackable — see the CARRIER NOTE.",
        "rationale":
            "REJECTED by the `ensures`: `wordProd` applies `assign` to THIS "
            "syllable's symbol `s.1`, while this impl always applies it to the "
            "constant `0`. Attacks feature (c) — that the symbol selects the "
            "element — and is the only rival that varies the `assign` binder, "
            "which it must be probed at an INJECTIVE assignment to catch (under "
            "the symbol-blind `assign` the other witnesses use, this rival "
            "agrees with gold everywhere). If it VERIFIED, the element lookup's "
            "argument would be unpinned (SPEC-TOO-WEAK) — a rival could resolve "
            "every syllable to the wrong generator and still verify.",
        # assign = ofAdd ∘ id (INJECTIVE: symbol n ↦ ofAdd n), syllables =
        # [(1,1)]: gold = ofAdd 1; the rival looks up symbol 0 and returns
        # ofAdd 0 = 1. Both the `assign` and `syllables` binders move here.
        "witness": _wit(_A_INJ, "[(1,(1:Int))]",
                        "an injective assignment and a non-zero symbol: the "
                        "rival reads the wrong generator"),
    },

    # -- UNIQUENESS: the product is accumulated in the wrong order ------------
    {
        "id": "order-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_reproved(
            "    return syllables.foldl (fun acc s => assign s.1 ^ s.2 * acc) 1\n", _PROOF_LOOPFREE),
        "refinement":
            "the port of the nagini sibling's `order-flip-first-factor`: a patch "
            "that accumulates each factor on the wrong side computes the "
            "REVERSED product. The codomain in the F2P scenario is a "
            "non-abelian group, so a relation word whose forward value is the "
            "identity need not have identity reverse value; the routine then "
            "reports a genuine structure-preserving map as not being one and "
            "the F2P does NOT resolve. The nagini sibling's self-audit "
            "reversed-product control fails for the same reason.",
        "rationale":
            "REJECTED by the `ensures`: `wordProd` is the ORDERED left-to-right "
            "product (`assign sym ^ p * wordProd assign rest`), but this impl "
            "folds from the left onto the accumulator's LEFT, reversing the "
            "word. Attacks feature (d) — factor ORDER — which no other rival "
            "touches: all five others compute a correctly-ordered product and "
            "are refuted by the VALUE of some factor, so this is the only case "
            "that would notice a spec pinning the multiset of factors rather "
            "than their sequence. `G` is an arbitrary, possibly non-abelian "
            "group, so the two differ on a two-syllable word over "
            "non-commuting elements. If it VERIFIED, order would be unpinned "
            "(SPEC-TOO-WEAK; the non-commutative product admitted reversed).",
        # CONDITIONED on the carrier, because no non-abelian group is reachable
        # from the frozen `import Velvet.Std` (re-measured under audit: `Group
        # (Equiv.Perm (Fin 3))` fails to synthesize, and `DihedralGroup`,
        # `Matrix`, `FreeGroup`, `Function.End`, `SemidirectProduct` are all
        # `Unknown identifier`; a witness may not add an import). `Multiplicative
        # Int` is abelian, where this rival AGREES with gold, so the refutation is
        # stated where the rival is actually wrong: over two elements assumed not
        # to commute. ONE hypothesis about ONE pair — jointly satisfiable in any
        # non-abelian group, so the gate's consistency probe cannot derive False
        # from it (re-confirmed by build: the probe leaves `⊢ False` unsolved).
        #
        # WITNESS_REFERENCE — the repair this case needed, and the one defect the
        # audit found. Refuted against the FROZEN solution this witness fails
        # with a bare `Type mismatch: hxy has type y * x ≠ x * y but is expected
        # to have type ¬(NonDetT.run do let r ← forIn Lean.Loop.mk ...)`: the
        # `simp` never reduced the frozen `while` term, so `hxy` was compared
        # against the un-normalised loop expression itself. That error is HOLLOW,
        # and the forgery test proves it rather than arguing it: building the
        # claim FLIPPED (`= DivM.res ...` — asserting gold is CORRECT at this
        # point, the opposite of a refutation) against the frozen solution gives
        # the byte-identical error modulo the dropped `¬`, and the type-revealing
        # variant (`exact (0 : Nat)`) prints the same un-normalised `forIn
        # Lean.Loop.mk` term on gold. So gold's exit code carried NO information
        # about the claim, and the gate would have recorded `rejected` for a
        # witness asserting gold is correct here. The frozen-solution signature
        # slipped `_STUCK_UNIFICATION` (which pairs "Application type mismatch"
        # with the loop term) because Lean printed a plain "Type mismatch".
        #
        # The fix is the repair the gate itself documents: name a
        # `witness_reference` — a VERIFYING impl of the SAME spec that DOES
        # reduce. Against `_REF_DIRECT` the same script normalises the program to
        # the ordered product and leaves `⊢ False` with `hxy` in context, i.e.
        # `Type mismatch: hxy has type y * x ≠ x * y but is expected to have type
        # False` — a SEMANTIC refutation: the reference's value already equals the
        # spec's, so nothing but `False` would close the goal. And the exit code
        # now TRACKS the claim: the flipped claim (`= DivM.res`, tactic dropped)
        # ELABORATES against the reference at exit 0, while against the rival it
        # is left needing `⊢ y * x = x * y`. That pair is what makes the
        # rejection attributable to the spec rather than to an unreduced loop.
        "witness_reference": _REF_DIRECT,
        "witness":
            "-- two non-commuting elements: the reversed product differs from "
            "the ordered one\n"
            "extract_program_for evalWord\n\n"
            "example (x y : G) (hxy : y * x ≠ x * y) :\n"
            "    evalWordExec (fun n => if n = 0 then x else y) "
            "[(0,(1:Int)),(1,(1:Int))]\n"
            "      ≠ DivM.res (wordProd (fun n => if n = 0 then x else y) "
            "[(0,(1:Int)),(1,(1:Int))]) := by\n"
            "  unfold evalWordExec evalWord\n"
            "  simp [NonDetT.run, pure, wordProd]\n"
            "  exact hxy\n",
    },

    # -- UNIQUENESS: the empty word is not the identity -----------------------
    {
        "id": "seed-nonidentity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_reproved(
            "    return syllables.foldr\n"
            "      (fun s acc => assign s.1 ^ s.2 * acc) (assign 0)\n", _PROOF_LOOPFREE),
        "refinement":
            "a patch that seeds the running product with some group element "
            "instead of the identity multiplies a spurious factor into EVERY "
            "relation word's value, including the empty word. A relation that "
            "genuinely holds then evaluates to that spurious element rather "
            "than the identity, so the routine reports a genuine "
            "structure-preserving map as not being one and the F2P does NOT "
            "resolve. It is also the one rival that is wrong on a word with no "
            "syllables at all, where every other rival here is exact.",
        "rationale":
            "REJECTED by the `ensures`: `wordProd assign [] = 1` by "
            "definition, but this impl returns `assign 0` on the empty word. "
            "Attacks the base case of feature (d) — that the product starts "
            "from the identity — and is the only case whose witness probes the "
            "EMPTY `syllables` list, the boundary of the recursion the other "
            "five never reach (all of them agree with gold there). If it "
            "VERIFIED, the fold's seed would be unpinned (SPEC-TOO-WEAK).",
        # syllables = [] (the recursion's boundary): gold = 1; the rival returns
        # assign 0 = ofAdd 1 ≠ 1. Control (same witness vs a CORRECT loop-free
        # foldr): `decide` proves the proposition FALSE.
        "witness": _wit(_A_CONST, "([] : List (Nat × Int))",
                        "the empty word: the spec's value is the identity, the "
                        "rival's is a group element"),
    },
]


# The axiom lane is empty by construction: this bundle declares no `axiom` and
# consumes no callee contract — the word product is modeled DEEPLY over the
# transparent Mathlib group carrier (meta.json records G-AX as `skip`). The
# nagini sibling's AXIOM_TESTS are dropped: that lane is G-AX's job and this gate
# ignores them regardless.
AXIOM_TESTS = []
