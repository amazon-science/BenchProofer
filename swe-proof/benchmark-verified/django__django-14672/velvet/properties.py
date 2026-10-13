"""properties.py — G-PBT falsification battery for django__django-14672 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method assembling a comparison key over a
transparent carrier):

  comparisonKey (pre : List Comp) (slot : Slot) (post : List Comp)
      return (out : List Comp)
    require keyHashable pre = true
    require keyHashable post = true
    (Q1) ensures out = pre ++ [Comp.slot (canonicalize slot)] ++ post
    (Q2) ensures keyHashable out = true

The modeled behaviour: a comparison key is assembled from already-prepared
leading components ``pre``, the single component that carries a sequence value
``slot``, and already-prepared trailing components ``post``. The sequence slot
must be placed into the key in CANONICAL form, so the key hashes/compares by the
sequence's content and order regardless of whether the caller supplied an
order-only or already-canonical container, and the whole key must be usable as a
hash key. THE CARRIER IS TRANSPARENT: ``Slot`` / ``Comp`` derive ``DecidableEq``
and ``canonicalize`` / ``keyHashable`` are computable ``def``s, so every clause
reduces under ``decide`` at a concrete input — reject witnesses ARE buildable
here (contrast the opaque-oracle sibling bundles, where they are not).

  Load-bearing clauses:
    (Q1) pins the key structure AND the slot's canonical form (its content and
         order are preserved; the raw order-only container is never carried in).
         There is NO opaque answer key: ``canonicalize`` is a concrete ``def``,
         so pinning ``out = pre ++ [Comp.slot (canonicalize slot)] ++ post``
         grounds the result in the actual inputs (directive 8).
    (Q2) additionally pins that the assembled key is usable as a hash key — the
         property that separates a canonicalized slot from a raw order-only one.

  THREE input binders — ``pre``, ``slot``, ``post`` — all varied by the reject
  witnesses (see BINDER / POINT COVERAGE). ``slot`` is the load-bearing binder
  (the behaviour under change); ``pre`` / ``post`` are the read-only surrounding
  components the assembly must forward verbatim.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY read-only
    frame rival (append into the input held at ``Acc(list_pred(names), 1/2)``)
    because a Viper impl can illegally WRITE a fractional-permission input.
    Lean/Velvet are referentially transparent: every input here is an immutable
    value, this bundle declares no ``mut`` binder, there is no heap and no
    aliasing — so there is no read-only input to overwrite and no substitute
    probe to build. Not fabricated (per the porting map: this class is vacuous
    here).
  * UNGROUNDED-ORACLE ECHO — N/A. ``canonicalize`` is a concrete ``def`` in the
    ``pure`` region (validated equal to the real canonicalizing callee by G-AX as
    an A-reference), not an opaque answer key; the post-image is a total function
    of the inputs. There is no value an echo could carry that satisfies Q1/Q2
    yet does the wrong thing — the unique satisfier IS the canonical assembly of
    the inputs. The positives are honest cheapest-reshape controls.
  * PARTIAL-DOMAIN / VALUE rivals — APPLY to Q1 (slot content, none-boundary,
    off-by-one) and to the assembly structure (drop ``pre`` / drop ``post``).
  * HASHABILITY rival — APPLIES to Q2: the pre-patch behaviour (carry the raw
    order-only slot straight in) yields a key that is NOT usable as a hash key.

WITNESS PLACEMENT. Each reject rival is refuted at a concrete input via Velvet's
tester machinery (``comparisonKeyTester pre slot post = false`` says the
extracted program violates the postcondition there), checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. The six witnesses probe six DISTINCT input tuples that move ``slot``
across the absent (``Slot.none``), order-only single-element, order-only
two-element, and empty sub-domains, and move ``pre`` / ``post`` across empty and
non-empty. No two rivals are refuted at the same input; every clause and every
binder is attacked (see the accounting footer). Each witness was machine-checked
to ELABORATE against its rival and FAIL against the frozen solution (two builds
per case).

AXIOM lane: dropped (``AXIOM_TESTS = []``). The one A-reference
(``canonicalize`` == the real canonicalizing callee) is consumed by NO axiom —
it is a deep model in the ``pure`` region, validated out-of-band by
axiom_check.py under G-AX. The G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14672"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The two code lines lie wholly inside the single
# ---- -- impl-start .. -- impl-end region and are unique in Solution.lean (both
# ---- facts asserted at load by _swap), so each edit keeps same_spec by
# ---- construction and leaves the frozen `prove_correct` statement intact. ----
_IMPL = (
    "    let canon := canonicalize slot\n"
    "    return pre ++ [Comp.slot canon] ++ post"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so an
# ---- admissibility case adding an in-region assert may retune the tactic script
# ---- without touching the spec or dropping the obligation. Unique in the file.
_PROOF = (
    "prove_correct comparisonKey by\n"
    "  loom_solve\n"
    "  simp_all [keyHashable, Comp.isHashable]"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    """Reshape the impl body AND retune the frozen tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `comparisonKeyTester pre slot post = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped, so no tactic
# ---- script can mask the verdict. Every argument is a concrete literal over the
# ---- transparent carrier, so `decide` reduces without any opaque leaf. ----
_TESTER = (
    "extract_program_for comparisonKey\n"
    "prove_precondition_decidable_for comparisonKey\n"
    "prove_postcondition_decidable_for comparisonKey\n"
    "derive_tester_for comparisonKey\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the frozen proof
    # script (the post-image is a point-wise structural equality, so no reshape
    # here needs a new lemma). Confirmed EXIT 0 (bash scripts/lean_verify.sh).
    # =====================================================================
    {
        "id": "pos-inline-canon",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline the canonical-form conversion into the returned
        # expression instead of naming it in a `let`. Same value flow.
        "module": _with_impl(
            "    return pre ++ [Comp.slot (canonicalize slot)] ++ post"),
        "rationale": "REJECT/PASS SOURCE = Q1/Q2. Inlining `canonicalize slot` "
                     "into the returned expression instead of binding it to a "
                     "local leaves the assembled key unchanged, so Q1 "
                     "(out = pre ++ [Comp.slot (canonicalize slot)] ++ post) and "
                     "Q2 (keyHashable out = true) still discharge under the frozen "
                     "script. A structurally-different faithful reshape MUST "
                     "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-named-comp",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: name the whole slot component (not just the slot value) in a
        # typed local before assembling. Same returned value.
        "module": _with_impl(
            "    let comp : Comp := Comp.slot (canonicalize slot)\n"
            "    return pre ++ [comp] ++ post"),
        "rationale": "REJECT/PASS SOURCE = Q1/Q2. Binding the canonical slot "
                     "COMPONENT (`Comp.slot (canonicalize slot)`) to a typed local "
                     "before assembling the key leaves the returned value "
                     "unchanged, so Q1/Q2 still hold. A correct reshape must "
                     "verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method's `require` clauses constrain only pre/post
    # (already-hashable surrounding components); a normal input (an order-only
    # slot with empty/hashable pre and post, the F2P shape) trivially satisfies
    # them, so the usual "a normal input satisfies the precondition" probe is
    # vacuous. The residual admissibility risk on this domain is that the
    # post-image is DEGENERATE — that canonicalization does not actually change
    # hashability, in which case Q2 would be trivially true and pin nothing. This
    # case discharges an in-region `assert`, at a concrete order-only slot, that
    # the raw slot is genuinely NOT usable as a hash key while its canonical form
    # IS: the post-image really discriminates the case the fix cares about. The
    # surrounding impl is kept verbatim so the method's own obligations still
    # discharge; the proof body is retuned only to clear the extra assert goal by
    # `decide` (allowed — the tactic body is elided from the spec view). The
    # assert is LIVE, not decoration: a false claim at the same slot (verified
    # separately) leaves an unsolved goal. Confirmed EXIT 0.
    # =====================================================================
    {
        "id": "admiss-canon-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_and_proof(
            "    assert (with_name_prefix `admiss\n"
            "      (keyHashable [Comp.slot (Slot.seq [\"a\"] true)] = false ∧\n"
            "       keyHashable [Comp.slot (canonicalize (Slot.seq [\"a\"] true))]"
            " = true))\n"
            "    let canon := canonicalize slot\n"
            "    return pre ++ [Comp.slot canon] ++ post",
            "prove_correct comparisonKey by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [keyHashable, Comp.isHashable]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at a "
                     "concrete order-only slot: the RAW slot component is not "
                     "usable as a hash key (keyHashable = false) while its "
                     "CANONICAL form is (keyHashable = true), so Q2 genuinely "
                     "distinguishes the sub-domain the fix cares about (it is not "
                     "trivially true). The in-region assert must discharge (else a "
                     "degenerate obligation would read as trivially met); the impl "
                     "is kept verbatim so Q1/Q2 discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument for why its faithful
    # real counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-raw-slot",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behaviour: carry the raw order-only slot straight into
        # the key without canonicalizing it. Violates Q1 (wrong slot form) AND
        # Q2 (an order-only slot is not usable as a hash key).
        "module": _with_impl(
            "    return pre ++ [Comp.slot slot] ++ post"),
        "refinement": "carrying the raw sequence slot straight into the key is "
                      "exactly the unpatched behaviour: an order-only container "
                      "placed into the comparison key makes the whole key unusable "
                      "as a hash key, so deriving a hash from it raises at the "
                      "point the failing checks exercise (a relation whose key is "
                      "collected into a hashed container). A faithful patch that "
                      "omitted the canonical conversion is the pre-patch — it "
                      "would NOT resolve.",
        "rationale": "REJECT from Q2 (keyHashable out = true): a raw order-only "
                     "slot is not usable as a hash key, so the assembled key is "
                     "not either; and from Q1 (the slot must be in canonical "
                     "form). This is the single-token discriminator the spec "
                     "senses. Refuted at an order-only slot with non-empty pre and "
                     "post. If it verifies => SPEC-TOO-WEAK (the hashability fix "
                     "is not enforced).",
        "witness": _witness(
            'comparisonKeyTester [Comp.slot Slot.none] (Slot.seq ["a"] true) '
            '[Comp.slot Slot.none]'),
    },
    {
        "id": "weak-drop-items",
        "kind": "uniqueness",
        "expect": "reject",
        # Contribute a CONSTANT canonical-but-empty slot: hashable (Q2 holds) and
        # the right shape, but the sequence content is dropped for every input.
        "module": _with_impl(
            "    return pre ++ [Comp.slot (Slot.seq [] false)] ++ post"),
        "refinement": "a canonicaliser that produced a CONSTANT hashable value "
                      "(always the empty sequence) regardless of the slot would be "
                      "hashable but would collapse every distinct sequence to the "
                      "same key component, so two relations with different "
                      "sequences would compare/hash equal — the very distinction "
                      "the differing-sequence F2P test relies on. It would not "
                      "preserve the content and would NOT resolve.",
        "rationale": "REJECT from Q1 (out = pre ++ [Comp.slot (canonicalize "
                     "slot)] ++ post): the constant empty sequence differs from "
                     "`canonicalize slot` for any non-empty slot. Q2 still holds "
                     "(the empty canonical sequence IS hashable) — the divergence "
                     "is confined to the slot content, exactly where "
                     "content/order-preservation is pinned. Refuted at an "
                     "order-only single-element slot.",
        "witness": _witness(
            'comparisonKeyTester [] (Slot.seq ["a"] true) []'),
    },
    {
        "id": "weak-truncate-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one near-miss: canonical form but with the FIRST element
        # dropped. Correct kind/hashability (Q2 holds); correct content only for
        # the empty/degenerate slot; wrong on any sequence of length >= 1.
        "module": _with_impl(
            "    let canon := match slot with\n"
            "      | Slot.none => Slot.none\n"
            "      | Slot.seq xs _ => Slot.seq (xs.drop 1) false\n"
            "    return pre ++ [Comp.slot canon] ++ post"),
        "refinement": "an off-by-one canonicaliser that built the key component "
                      "from the sequence with its first element dropped would ship "
                      "a truncated slot — a distinct key component that breaks "
                      "hash/identity equality with the correctly-canonicalised "
                      "sibling relation in the failing equality test. Correct "
                      "only on degenerate slots; wrong for the F2P input — it "
                      "would NOT resolve.",
        "rationale": "REJECT from Q1: dropping the leading element differs from "
                     "`canonicalize slot` at the first element for any sequence of "
                     "length >= 1. Q2 holds (canonical, hashable) — a near-miss "
                     "that agrees with gold only on the empty/single-collapse "
                     "sub-domain. Refuted at an order-only TWO-element slot (where "
                     "it drops one element but the drop-items rival would drop "
                     "both), so it is not subsumed by weak-drop-items.",
        "witness": _witness(
            'comparisonKeyTester [] (Slot.seq ["x", "y"] true) []'),
    },
    {
        "id": "weak-absent-canonicalized",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the ABSENT sub-domain: an absent slot is turned into
        # an empty canonical sequence instead of staying absent. Hashable (Q2
        # holds), correct on every present slot; diverges only when slot = none.
        "module": _with_impl(
            "    let canon := match slot with\n"
            "      | Slot.none => Slot.seq [] false\n"
            "      | s => canonicalize s\n"
            "    return pre ++ [Comp.slot canon] ++ post"),
        "refinement": "a normaliser that turned an absent slot into an empty "
                      "canonical sequence (rather than leaving it absent) would "
                      "change the key of a relation declared WITHOUT a sequence "
                      "from carrying the absent value to carrying an empty "
                      "sequence — distinct from every other relation that "
                      "genuinely has the absent value there, breaking "
                      "identity/hash equality with the unchanged sibling. It "
                      "diverges from the canonicaliser on the absent sub-domain — "
                      "not the gold patch, would NOT resolve.",
        "rationale": "REJECT from Q1 on the absent sub-domain: `canonicalize "
                     "Slot.none = Slot.none`, but this returns "
                     "`Slot.seq [] false`. Q2 still holds (the empty canonical "
                     "sequence is hashable) — the divergence is invisible to the "
                     "hashability clause and caught only by the structural "
                     "equality on the none boundary. Refuted at an absent slot.",
        "witness": _witness("comparisonKeyTester [] Slot.none []"),
    },
    {
        "id": "weak-drop-pre",
        "kind": "uniqueness",
        "expect": "reject",
        # Structural: drop the leading components entirely. The slot is
        # canonicalized correctly (Q2 can still hold), but the surrounding
        # read-only components are not forwarded — the assembled key is wrong.
        "module": _with_impl(
            "    return [Comp.slot (canonicalize slot)] ++ post"),
        "refinement": "dropping the leading key components would build the "
                      "comparison key from only part of the relation descriptor, "
                      "so two relations differing ONLY in a leading component "
                      "would compare/hash equal — a corrupted identity. The patch "
                      "adds a call to the canonicaliser and leaves the rest of the "
                      "identity tuple intact; an impl that also dropped the "
                      "leading components would not be that patch and would NOT "
                      "resolve.",
        "rationale": "REJECT from Q1 (out = pre ++ [Comp.slot (canonicalize "
                     "slot)] ++ post): dropping `pre` differs from the pinned "
                     "assembly whenever `pre` is non-empty. Attacks the `pre` "
                     "binder specifically (a binder the slot-only rivals hold at "
                     "[]). Refuted with a non-empty `pre` and an absent slot.",
        "witness": _witness(
            'comparisonKeyTester [Comp.slot Slot.none] Slot.none []'),
    },
    {
        "id": "weak-drop-post",
        "kind": "uniqueness",
        "expect": "reject",
        # Structural: drop the trailing components entirely. Mirror of drop-pre,
        # attacking the `post` binder.
        "module": _with_impl(
            "    return pre ++ [Comp.slot (canonicalize slot)]"),
        "refinement": "dropping the trailing key components would build the "
                      "comparison key from only part of the relation descriptor, "
                      "so two relations differing ONLY in a trailing component "
                      "would compare/hash equal — a corrupted identity. Not the "
                      "gold patch (which leaves the rest of the identity tuple "
                      "intact) — would NOT resolve.",
        "rationale": "REJECT from Q1: dropping `post` differs from the pinned "
                     "assembly whenever `post` is non-empty. Attacks the `post` "
                     "binder specifically (held at [] by the slot-only rivals and "
                     "the drop-pre rival). Refuted with a non-empty `post` and an "
                     "absent slot.",
        "witness": _witness(
            'comparisonKeyTester [] Slot.none [Comp.slot Slot.none]'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The nagini sibling has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 MANDATORY frame-mutation, 4 value/uniqueness
# rivals). This velvet bundle models the SAME core behaviour (place the sequence
# slot into the comparison key in canonical form; keep the key hashable) but over
# a WIDER carrier: the velvet method assembles the WHOLE key `pre ++ [slot] ++
# post` (three input binders), where the nagini function takes only the slot
# collection `names` (one binder). So the value rivals port directly and two
# ADDED structural rivals cover the extra `pre` / `post` binders.
#
#   nagini case                 -> here
#   ---------------------------------------------------------------------
#   pos-reordered-branches      -> pos-inline-canon / pos-named-comp   PORTED (x2)
#   admiss-reads                -> admiss-canon-nondegenerate          RE-AIMED
#   frame-mut-append            -> (none)                              VACUOUS
#   weak-prepatch-mutable       -> weak-raw-slot                       PORTED
#   weak-absent-immutable       -> weak-absent-canonicalized           PORTED
#   weak-drop-items             -> weak-drop-items                     PORTED
#   weak-truncate-first         -> weak-truncate-first                 PORTED
#   (no nagini counterpart)     -> weak-drop-pre / weak-drop-post      ADDED (x2)
#   AXIOM_TESTS ([])            -> (none)                              N/A
#
# 5 ported (incl. 2 positives from 1 nagini positive), 1 re-aimed, 1 vacuous,
# 2 added = 9 velvet cases (2 soundness, 1 admissibility, 6 uniqueness).
#
# PORTED (positives): the nagini positive reorders the None-vs-present branches.
#   The velvet impl is a straight-line assembly with no branch to reorder, so the
#   ARGUMENT ("a structurally-different faithful impl must verify") is carried by
#   the two cheapest expressible reshapes — inline the canonical conversion, and
#   name the whole slot component in a typed local. Both build (EXIT 0).
# RE-AIMED (admissibility): the nagini case asserts a normal through-fields list
#   is in-domain under the half-permission. The velvet `require` constrains only
#   pre/post (an order-only slot with empty/hashable pre/post trivially satisfies
#   it), so that probe is vacuous. Re-aimed at the residual DEGENERACY risk on
#   this domain: Q2 could be trivially true if canonicalization did not change
#   hashability. The in-region assert (a raw order-only slot is NOT hashable while
#   its canonical form IS) establishes Q2 genuinely discriminates. Live (a false
#   claim at the same slot leaves an unsolved goal); the impl is kept verbatim so
#   Q1/Q2 discharge. Build EXIT 0.
# VACUOUS (frame-mutation): the nagini case is MANDATORY because `names` is held
#   at Acc(list_pred(names), 1/2) and a Viper impl can illegally append to it.
#   This backend is referentially transparent, declares no `mut` binder, and has
#   no heap/aliasing — every input is an immutable value, so there is no
#   read-only input to overwrite and no substitute probe to build. Not fabricated
#   (per the porting map: this class is vacuous on Lean/Velvet).
# PORTED (value rivals): weak-prepatch-mutable -> weak-raw-slot (carry the raw
#   order-only slot straight in; the exact missing-canonicalization bug, violates
#   Q1 AND Q2). weak-absent-immutable -> weak-absent-canonicalized (turn an absent
#   slot into an empty canonical sequence; partial-domain on the none boundary,
#   Q1 only). weak-drop-items ports directly (constant empty sequence; Q1 content,
#   Q2 still holds). weak-truncate-first ports directly (off-by-one on the leading
#   element; Q1 near-miss, Q2 still holds). Each carries a machine-checked witness
#   that ELABORATES against the rival and FAILS against the frozen solution.
# ADDED (structural rivals): the velvet carrier assembles the whole key, so it
#   exposes the `pre` and `post` binders the nagini function never had.
#   weak-drop-pre and weak-drop-post attack Q1's assembly structure on those two
#   binders (drop the leading / trailing components), a real divergence a
#   slot-only battery would never sense. Both carry discriminating witnesses.
#
# BINDER / POINT COVERAGE. Three input binders, all varied across the six reject
#   witnesses (six DISTINCT input tuples => pts=6):
#     pre  : {[], [Comp.slot Slot.none]}                    (drop-pre / raw)
#     slot : {Slot.none, Slot.seq ["a"] true,
#             Slot.seq ["x","y"] true}                       (absent / items / trunc)
#     post : {[], [Comp.slot Slot.none]}                    (drop-post / raw)
#   Clause coverage: Q1 (structure + slot canonical form) attacked by all six;
#   Q2 (whole-key hashability) attacked independently by weak-raw-slot (the only
#   rival producing a non-hashable key). Both positives and the admissibility
#   assert defend both clauses.
#
# AXIOM_TESTS: dropped. `canonicalize` is a deep model (A-reference) consumed by
#   NO axiom; its equivalence to the real canonicalizing callee is G-AX's job
#   (axiom_check.py). The G-PBT gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
