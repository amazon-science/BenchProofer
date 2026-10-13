"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7757 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct distributePositionalDefaults`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  distributePositionalDefaults (p q : Nat) (defaults : List Int)
      return (out : List (Option Int))
    require defaults.length ≤ p + q
    ensures out = distributed (p + q) defaults

A sequence of positional slots splits into a leading group of size ``p`` and a
trailing group of size ``q``, for ``n = p + q`` slots in declaration order. A
list of ``d ≤ n`` supplied payloads is RIGHT-ALIGNED across the WHOLE ``n``-slot
sequence: the last ``d`` slots receive the ``d`` payloads in order, the leading
``n - d`` slots receive the empty marker (``none``). ``distributed`` is the
concrete, fully-unfolded ``def`` computing that canonical right-alignment
(``replicate (n - d) none ++ defaults.map some``). The single load-bearing
``ensures`` clause pins the result to that exact per-slot vector — width ``p + q``
(the leading group is NOT excluded), right-aligned (not left), full length (no
slot dropped), payloads verbatim (no substitution).

CARRIER NOTE (decisive for this port). ``distributed`` is a concrete decidable
``def`` over ``Nat``/``List``, and the post-image is a decidable equality of
concrete lists. So a rival's disagreement with the spec is a DECIDABLE
proposition at a concrete input: a refutation witness is built by ``decide`` and
genuinely discriminates. The uniqueness class is LIVE on this carrier — no
opaque callee, no conditioning needed (contrast a bundle whose observable is an
opaque identity, where every rival reduces to an undecidable disequality and the
class collapses). There is NO axiomatized oracle to echo (the ``axioms`` region
is empty): the cheapest correct impl simply produces the right-alignment, which
the positive control covers honestly (directive 8).

WITNESS MECHANICS (measured on this backend). The frozen impl builds the
right-alignment with a well-founded ``while`` loop that prepends one ``none`` per
missing leading slot. The extracted-program tester over that loop does NOT
kernel-reduce under ``decide`` (well-founded recursion stays stuck), so a witness
``distributePositionalDefaultsTester … = false`` FAILS to elaborate against the
frozen solution regardless of the concrete input — which is exactly the "fails
on gold" half a discriminating witness needs. Each reject rival below is written
LOOP-FREE (a closed-form list expression), so ITS extracted tester reduces and
the same witness ELABORATES against the rival. The two halves therefore come
apart cleanly: rival reduces to ``false`` (the postcondition is violated at that
input), gold stays stuck (its loop does not reduce). This is the established
pattern for backward-loop bundles on this backend.

BINDER STRUCTURE (read this before judging binder coverage). The postcondition
depends on all three method inputs — ``p``, ``q`` and ``defaults`` — through
``distributed (p + q) defaults``. The DISCRIMINATING content of the modeled fix
is that the leading group ``p`` PARTICIPATES in the alignment (width ``p + q``,
not ``q``): a supplied payload that spills into the leading group must survive.
The reject witnesses vary ``p`` over {2, 0, 1, 1}, ``q`` over {1, 1, 0, 1} and
``defaults`` over {[0,1], [5], [], [7]} — moving the alignment across the
leading-group-spill case (``d > q``, the headline bug), the empty-leading-group
case (``p = 0``), the empty-defaults length boundary, and the single-leading-slot
case — so the manifest demonstrates the post-image's dependence on the ``p``/``q``
split and on ``defaults``, not merely its value at one pinned point.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive control — APPLIES. A structurally different but
    behaviourally identical assembly (produce the right-alignment directly with
    a closed-form expression instead of the backward prepend loop) must still
    verify, else SPEC-TOO-STRONG on the shape of the assembly. (``pos-*``.)
  * ADMISSIBILITY — RE-AIMED. The lone precondition (``defaults.length ≤ p + q``)
    is trivially satisfiable for an F2P-shaped input, so the "a normal input
    meets the precondition" probe is vacuous. Re-aimed at the residual risk that
    the post-image is degenerate / unsatisfiable at the interesting point: an
    in-region ``assert`` pins the post-image's concrete value at the headline
    input (leading-group split with a spilled payload). (``admiss-*``.)
  * UNIQUENESS / SPEC-TOO-WEAK rivals — APPLY, and carry the port's
    discriminating content. Four rivals attack the alignment clause across four
    sub-domains — align over the trailing group only (the modeled bug), drop
    every payload, drop the last slot (length), and align the wrong direction —
    each with a machine-checked refutation witness at a distinct concrete input.
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling carries this
    MANDATORY because its read-only input is held at a fractional heap permission
    (``Acc(.,1/2)``) an impl can illegally overwrite. Lean and Velvet are
    referentially transparent: every parameter here is an immutable value (this
    bundle declares no ``mut`` binder on an input), there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe to
    build. Not fabricated (porting map: this class is vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A. ``distributed`` is a concrete ``def`` in the
    ``pure`` region; the ``axioms`` region is empty (no opaque answer key).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the per-element
rendering of a payload is a type-refinement identity, not an oracle). The gate
ignores ``AXIOM_TESTS`` regardless. See the footer for the full nagini→velvet
accounting.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7757"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen backward-prepend loop, verbatim (the
# ---- executable lines strictly inside distributePositionalDefaults'
# ---- -- impl-start / -- impl-end). Lies wholly inside the single impl region
# ---- and is unique in Solution.lean (the prepatch skeleton lives in a separate
# ---- file); both facts asserted at load by _swap. Every variant _swap()s only
# ---- this block (and, where the reshape needs it, the proof body below), so the
# ---- edit never touches the spec regions (axioms/pure/pre/post + the method
# ---- signature and the `ensures`).
_IMPL = (
    "    let mut out : List (Option Int) := defaults.map (Option.some)\n"
    "    let mut k := (p + q) - defaults.length\n"
    "    while k > 0\n"
    "      invariant k ≤ (p + q) - defaults.length\n"
    "      invariant out = List.replicate (((p + q) - defaults.length) - k) none\n"
    "                        ++ defaults.map (Option.some)\n"
    "      done_with k = 0\n"
    "      decreasing k\n"
    "    do\n"
    "      out := none :: out\n"
    "      k := k - 1\n"
    "    return out"
)
assert _BASE.count(_IMPL) == 1, "distributePositionalDefaults impl region drifted"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a case that reshapes the impl (or adds an in-region
# ---- assert) may retune its script without touching the spec or dropping the
# ---- obligation.
_PROOF = (
    "prove_correct distributePositionalDefaults by\n"
    "  loom_solve\n"
    "  case _ =>  -- loop-body step: prepend one empty slot\n"
    "    rw [invariant_2]\n"
    "    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)\n"
    "  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition\n"
    "    simp_all [distributed]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof):
    """Reshape the impl region AND retune the tactic body."""
    src = _swap(_BASE, _IMPL, new_impl)
    return _swap(src, _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `distributePositionalDefaultsTester p q defaults = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. There is one `require`
# ---- (defaults.length ≤ p + q), satisfied by every witness input below.
def _tester(body):
    m = "distributePositionalDefaults"
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n" + body)


def _witness(p, q, defaults):
    return _tester(
        f"example : distributePositionalDefaultsTester {p} {q} {defaults} "
        "= false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Produce the right-alignment
    # DIRECTLY as a closed-form list expression instead of accumulating it with
    # the backward prepend loop. Same value on the whole domain; the reshaped
    # (loop-free) obligation closes with `simp_all [distributed]` (verified
    # out-of-band with a real build).
    # =====================================================================
    {
        "id": "pos-closed-form-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "    let out : List (Option Int) :=\n"
            "      List.replicate ((p + q) - defaults.length) none ++ defaults.map (Option.some)\n"
            "    return out",
            "prove_correct distributePositionalDefaults by\n"
            "  loom_solve\n"
            "  simp_all [distributed]"),
        "rationale": "structurally different CORRECT reshape: it produces the "
                     "right-alignment directly (empty prefix ++ the payloads) "
                     "instead of accumulating it with the backward prepend loop, "
                     "so `out = distributed (p + q) defaults` still discharges by "
                     "definitional unfolding. A faithful reshape MUST verify, else "
                     "SPEC-TOO-STRONG on the assembly's shape (the mutable loop is "
                     "not load-bearing).",
    },

    # =====================================================================
    # ADMISSIBILITY — the lone precondition (defaults.length ≤ p + q) is
    # trivially satisfiable for any F2P-shaped input, so the "a normal input
    # meets the precondition" probe is vacuous. Re-aimed at the residual risk on
    # this surface: that the post-image is UNSATISFIABLE / degenerate at the
    # interesting point (a spec no impl can meet reads exactly like one every
    # impl meets). The in-region assert pins the post-image's concrete value at
    # the headline input (a leading-group split p=2, q=1 with a payload spilling
    # into the leading group, defaults [0,1] ↦ [none, some 0, some 1]); the
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges. The assert is live: a false claim in its place leaves an
    # unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-alignment-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (distributed (2 + 1) [0, 1] = [none, some 0, some 1]))\n"
            + _IMPL,
            "prove_correct distributePositionalDefaults by\n"
            "  loom_solve\n"
            "  case _ =>  -- the in-region admissibility assert\n"
            "    decide\n"
            "  case _ =>  -- loop-body step: prepend one empty slot\n"
            "    rw [invariant_2]\n"
            "    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)\n"
            "  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition\n"
            "    simp_all [distributed]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "headline input: a leading group of size 2 and a trailing "
                     "group of size 1 with two supplied payloads (one spilling "
                     "into the leading group) must right-align to [none, some 0, "
                     "some 1] — the leading slot empty, the spilled payload kept. "
                     "The in-region assert must discharge (else the obligation is "
                     "unsatisfiable / PRECOND-TOO-STRONG); the impl is kept "
                     "verbatim so the method's own `ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # distinct concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is written
    # loop-free so its extracted tester reduces under `decide` (see WITNESS
    # MECHANICS in the module docstring).
    # =====================================================================
    {
        "id": "weak-trailing-group-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The modeled bug: align the payloads across the TRAILING group only
        # (width q), excluding the leading group. At most q payloads survive; any
        # payload that would belong to a leading slot is DROPPED. Coincides with
        # the correct alignment exactly when d ≤ q, which is why only a
        # leading-group-spill input exposes it.
        "module": _impl(
            "    let kept := defaults.drop (defaults.length - min q defaults.length)\n"
            "    let out : List (Option Int) :=\n"
            "      List.replicate ((p + q) - kept.length) none ++ kept.map (Option.some)\n"
            "    return out"),
        "refinement": "a counterpart that aligns the supplied payloads across the "
                      "trailing group ALONE (excluding the leading group from the "
                      "alignment width) drops any payload that belongs to a "
                      "leading slot — the exact vanished-default misbehaviour the "
                      "issue reports. On a leading-group split where a payload "
                      "spills into the leading group (e.g. p=2, q=1, two "
                      "payloads), the leading slot's payload is lost; the failing "
                      "test that reads it back would still observe the empty "
                      "marker and still FAIL. It would NOT resolve.",
        "rationale": "REJECT from `out = distributed (p + q) defaults`: aligning "
                     "over width q keeps only `min q d` payloads and empties the "
                     "leading group, which is not the right-alignment over width "
                     "p + q whenever d > q. Verifying would be SPEC-TOO-WEAK (it "
                     "would admit the leading-group-excluded alignment). Refuted "
                     "at p=2, q=1, defaults=[0,1] (d=2 > q=1: a payload spills "
                     "into the leading group), the headline bug sub-domain.",
        "witness": _witness(2, 1, "[0, 1]"),
    },
    {
        "id": "weak-drop-all-payloads",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the empty marker at EVERY slot, dropping every supplied payload.
        # Trivially satisfies the length clause (n slots) but pins the wrong value
        # wherever a payload should appear; correct only when d = 0.
        "module": _impl(
            "    let out : List (Option Int) := List.replicate (p + q) none\n"
            "    return out"),
        "refinement": "a counterpart that attaches NO payload to any slot (e.g. "
                      "omitted the distribution entirely) renders every positional "
                      "slot empty; the failing test that reads back a supplied "
                      "payload would observe the empty marker and FAIL. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = distributed (p + q) defaults`: an "
                     "all-empty vector equals the right-alignment only when d = 0; "
                     "with any payload it differs at the trailing slots. Verifying "
                     "would be SPEC-TOO-WEAK on the presence of payloads. Refuted "
                     "at p=0, q=1, defaults=[5] (a single trailing slot that must "
                     "carry the payload; the empty-leading-group case p=0).",
        "witness": _witness(0, 1, "[5]"),
    },
    {
        "id": "weak-short-result",
        "kind": "uniqueness",
        "expect": "reject",
        # Right-align correctly, then DROP the last slot. Correct on every slot it
        # does emit, but the result has p + q - 1 slots (for p + q > 0).
        "module": _impl(
            "    let full : List (Option Int) :=\n"
            "      List.replicate ((p + q) - defaults.length) none ++ defaults.map (Option.some)\n"
            "    let out := full.dropLast\n"
            "    return out"),
        "refinement": "a counterpart with an off-by-one that omits the final "
                      "positional slot entirely produces a vector one slot short; "
                      "the failing test that enumerates all slots would be missing "
                      "the last one and FAIL. It would NOT resolve.",
        "rationale": "REJECT from `out = distributed (p + q) defaults`: dropping "
                     "the last slot yields length p + q - 1 ≠ p + q (for p + q > "
                     "0), so the per-slot vector differs in length. Verifying "
                     "would be SPEC-TOO-WEAK on the slot count. Refuted at p=1, "
                     "q=0, defaults=[] (the single-leading-slot, empty-defaults "
                     "boundary: correct [none], rival []).",
        "witness": _witness(1, 0, "[]"),
    },
    {
        "id": "weak-left-align",
        "kind": "uniqueness",
        "expect": "reject",
        # Right SHAPE and count, wrong DIRECTION: place the payloads FIRST and the
        # empty markers last (left-aligned). Correct only when the empty prefix is
        # empty (d = n) or d = 0; wrong whenever a leading slot must be empty.
        "module": _impl(
            "    let out : List (Option Int) :=\n"
            "      defaults.map (Option.some) ++ List.replicate ((p + q) - defaults.length) none\n"
            "    return out"),
        "refinement": "a counterpart that lays the supplied payloads down from the "
                      "FIRST slot (left-aligned) rather than right-aligned assigns "
                      "each payload to the wrong slot whenever there is a leading "
                      "empty; the failing test that reads a specific slot's payload "
                      "by position would observe a different value (or an empty "
                      "marker) and FAIL. It would NOT resolve.",
        "rationale": "REJECT from `out = distributed (p + q) defaults`: the "
                     "right-alignment puts the empty markers FIRST; a left-aligned "
                     "vector differs whenever 0 < d < p + q. Verifying would be "
                     "SPEC-TOO-WEAK on the alignment direction — a near-miss "
                     "(correct length and payload multiset) the drop rivals do not "
                     "subsume. Refuted at p=1, q=1, defaults=[7] (one leading slot "
                     "must be empty: correct [none, some 7], rival [some 7, none]).",
        "witness": _witness(1, 1, "[7]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 1 MANDATORY frame-mutation rival, 4
# value/uniqueness rivals) plus a 2-case AXIOM lane. The sibling contracts a
# richer surface (`resolve_positional_defaults` over a heap `List[int]` held at a
# fractional permission, with a grounded @Pure `resolved_default` helper and a
# render/renderable axiom pair); this bundle models the SAME purely-functional
# core — the right-alignment of defaults across all p + q positional slots — as a
# single method over immutable `Nat`/`List` values with a concrete `distributed`
# def and NO axioms. The accounting below records every sibling case.
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-reorder (branch reorder)     -> pos-closed-form-direct       RE-EXPRESSED
#   admiss-f2p (precond admits F2P)  -> admiss-alignment-grounded    RE-AIMED
#   r1-posonly-exempt (pre-patch)    -> weak-trailing-group-only     PORTED
#   r2-offby-posonly (mis-align)     -> weak-left-align              RE-EXPRESSED
#   r3-all-empty                     -> weak-drop-all-payloads       PORTED
#   r4-frame-mutation (MANDATORY)    -> (none)                       VACUOUS (no heap)
#   r5-short-result                  -> weak-short-result            PORTED
#   AXIOM_TESTS (2)                  -> (none)                       DROPPED (G-AX)
#
# RE-EXPRESSED (positive control): the sibling reorders the two branches of the
#   per-iteration decision block. This bundle's impl is a backward prepend loop,
#   not an if/else over a per-index decision, so a branch reorder is not the
#   natural reshape. The ARGUMENT ("a structurally different but faithful impl
#   must verify, else SPEC-TOO-STRONG") is carried by a reshape that IS natural on
#   this carrier: produce the right-alignment directly as a closed-form list
#   expression, dropping the loop entirely. Verified to build.
# RE-AIMED (admissibility): the sibling asserts the precondition admits an
#   F2P-shaped supplied-defaults list. This bundle's lone precondition
#   (defaults.length ≤ p + q) is trivially satisfiable, so the probe is re-aimed
#   at the residual risk (post-image degeneracy) with an in-region assert pinning
#   the post-image's concrete value at the headline leading-group-spill input.
#   Verified to build (assert discharged by `decide`, method obligation kept).
# PORTED / RE-EXPRESSED (value rivals): r1-posonly-exempt (align over the trailing
#   group only, dropping leading-group payloads — the modeled bug) ports directly
#   as weak-trailing-group-only. r3-all-empty ports as weak-drop-all-payloads.
#   r5-short-result ports as weak-short-result (drop the last slot). r2's off-by-
#   one alignment (a mis-alignment of the payloads relative to the slots) is
#   RE-EXPRESSED as weak-left-align — the cleanest wrong-alignment on this carrier
#   (right shape and payload multiset, wrong direction), a near-miss the drop
#   rivals do not subsume. Each rival is loop-free so its extracted tester reduces
#   under `decide`, and each carries a machine-checked witness that ELABORATES
#   against the rival and FAILS against the frozen solution (two real builds per
#   case; confirmed out-of-band during authoring).
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because its input
#   `provided` is held at Acc(list_pred(provided), 1/2) an impl can illegally
#   write. This backend is referentially transparent and declares no `mut` binder
#   on an input — every parameter is an immutable value with no heap footprint —
#   so there is no read-only field to overwrite and no substitute probe to build.
#   Not fabricated (porting map: this class is vacuous here).
#
#   The four reject witnesses probe four DISTINCT input tuples; across them p
#   takes {2, 0, 1, 1}, q takes {1, 1, 0, 1}, defaults takes {[0,1], [5], [],
#   [7]}. The load-bearing p/q split is varied across the leading-group-spill case
#   (p=2, q=1, d=2 > q), the empty-leading-group case (p=0), the empty-defaults
#   length boundary (d=0), and the single-leading-slot case (p=1, q=1, d=1). No
#   two rivals are refuted at the same input tuple.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the per-element rendering of a payload is a type-refinement identity, not
# an oracle), so there is nothing to probe and the gate ignores AXIOM_TESTS
# regardless.
AXIOM_TESTS = []
