"""PBT manifest for sympy__sympy-24443 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (region-surgery: only
the text strictly inside the `# impl-start` / `# impl-end` region is edited —
markers.same_spec elides exactly that region, so nested invariants/asserts are
editable while axioms/pure/pre/post-conditions and signatures stay frozen) and
swap the implementation; they are checked by Nagini verify + markers.same_spec.
Axiom cases are real-callee probes run in the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md / instance):

  ONE modeled function:
    relator_image(block_elems: List[int], block_pows: List[int]) -> int
      models the nested helper `_image(r)` of `_check_homomorphism` (gold patch:
      `w = identity; for symbol, power in r.array_form: w *= images[g]**power;
      return w`). A relator word is two parallel List[int]: block_elems[k] is the
      resolved codomain element handle for block k's generator, block_pows[k] its
      (possibly NEGATIVE) integer exponent. The codomain group is an opaque,
      NON-commutative monoid (gid/gmul/gpow). The image is the ordered
      left-to-right product of every block's factor gpow(elem, exponent).

      Pre : Acc(list_pred(block_elems), 1/2)          <- READ-ONLY input
            Acc(list_pred(block_pows), 1/2)            <- READ-ONLY input
            len(block_elems) == len(block_pows)
            len(ToSeq(block_elems)) == len(ToSeq(block_pows))
      Post: Acc(list_pred(block_elems), 1/2)           (returns the read perms)
            Acc(list_pred(block_pows), 1/2)
            len(ToSeq(block_elems)) == len(ToSeq(block_pows))
            Result() == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows))
                                                        <- LOAD-BEARING pin

  LOAD-BEARING clause: the last Ensures. image_fold(gid(), elems, pows) is a
  front-recursive @Pure fold, FULLY GROUNDED in the inputs
  (image_fold(acc,elems,pows) = image_fold(gmul(acc, gpow(elems[0],pows[0])),
  elems.drop(1), pows.drop(1)); empty -> acc). It is NOT an opaque @ContractOnly
  answer-key oracle: it is a pure function of the args, fully unfolded. So the
  directive-2 "ungrounded-oracle echo" attack does NOT apply — `return
  image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows))` is the CORRECT
  cheapest impl, not a wrong echo. Per directive 2 we therefore use that as an
  honest cheapest-impl POSITIVE CONTROL (expect=verify) rather than a reject
  case (see assessment).

  Read-only inputs: BOTH block_elems and block_pows are held at Acc(..., 1/2) in
  the pre- and post-condition => the FRAME-MUTATION probe is MANDATORY: a rival
  that WRITES either array (append / index-store) to satisfy the postcondition
  vacuously must be REJECTED for INSUFFICIENT PERMISSION (list mutation needs the
  full list_pred; only 1/2 is held). The gold fold value-logic is kept verbatim
  around the write so the rejection is attributable to the write.

  Discriminating content: the negative-exponent (inverted-generator) block. The
  pre-patch dropped its factor (model_prepatch.py: `if block_pows[i] >= 0: w =
  gmul(...)`), yielding a non-identity image and a spurious "do not define a
  homomorphism" error. The F2P test_homomorphism adds D3 -> D3 identity map
  (`homomorphism(D3, D3, D3.generators, D3.generators); T.is_isomorphism()`),
  whose relator `x_1*x_0*x_1**-1*x_0` contains exactly that inverted-generator
  block — so any impl that drops/perturbs a negative-exponent factor does NOT
  resolve.

Axiom lane: three @ContractOnly A-consumed axioms gid/gmul/gpow with the WEAKEST
  contract (Ensures(True)) — they cannot over-claim, so axiom-soundness for them
  is trivial. The discriminating content is the A-REFERENCE deep model image_fold
  validated == the real fixed `_image` by axiom_check.py (G-AX). The PBT axiom
  lane therefore re-runs that validation in the instance image:
    * axiom-soundness  — embed axiom_check.py's source (read on the HOST at load
      time; it is NOT mounted in-container) and execute its main() under the gold
      patch: the REAL fixed `_image`, on a battery of real PermutationGroups /
      FpGroups / FreeGroups (D3/D4/D5/C6/A4/S4 + FpGroups), must reproduce the
      deep image_fold over EVERY relator INCLUDING inverted-generator (negative-
      exponent) blocks — the discriminating case — plus the monoid laws
      (identity / associativity / g*g**-1==e / g**-2==(g**-1)**2). Any
      disagreement => the A-reference (or a monoid axiom) is UNSOUND.
    * axiom-containment — the opaque gid/gmul/gpow carry NO domain restriction
      (Ensures(True), gpow total over EVERY integer exponent incl. negative), so
      every caller-reachable callee input is trivially inside their domain. For
      the A-reference deep model, the model's only Requires on the carrier is
      equal-length int arrays with arbitrary (incl. negative) exponents; the
      G-AX battery validates image_fold == real _image on exactly that domain
      and explicitly asserts a negative-exponent relator is exercised, so no
      caller-reachable input lies outside the validated domain.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24443"
FLOAT_ENCODING = None  # meta.json float_encoding is null (group elements are opaque int tags)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchor: the WHOLE content strictly INSIDE the impl region (the gold
# forward per-block fold loop, with its nested invariants + head/tail-split
# Asserts). Every variant is built by _swap on exactly this block, so only impl
# text is edited and same_spec is guaranteed. Loop variants keep the gold
# invariants / asserts verbatim (pilot-bug-2/3: never drop a framing assert /
# lemma needed by the proof).
# ---------------------------------------------------------------------------

_GOLD_IMPL = (
    "    w = gid()\n"
    "    i = 0\n"
    "    while i < len(block_elems):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(block_elems), 1 / 2))\n"
    "        Invariant(Acc(list_pred(block_pows), 1 / 2))\n"
    "        Invariant(len(block_elems) == len(block_pows))\n"
    "        Invariant(0 <= i and i <= len(block_elems))\n"
    "        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))\n"
    "        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))\n"
    "        # `w` is the product of the first `i` blocks; the remaining suffix folds\n"
    "        # onto it to give the whole-word image.\n"
    "        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))\n"
    "                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))\n"
    "        # invariants-end\n"
    "        # The fold unfolds at the head of drop(i) (non-empty since i < len):\n"
    "        # supply the head/tail split so a single unfold relates step i to i+1.\n"
    "        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))\n"
    "        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))\n"
    "        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])\n"
    "        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])\n"
    "        w = gmul(w, gpow(block_elems[i], block_pows[i]))\n"
    "        i = i + 1\n"
    "    return w\n"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): structurally-different cheapest impl -----
    # The postcondition oracle image_fold(gid(), elems, pows) is FULLY GROUNDED in
    # the inputs (a @Pure front-recursive fold over the two block arrays), so the
    # cheapest CORRECT impl simply returns it. This is structurally different from
    # the gold forward loop (no loop / no invariants / no asserts) yet
    # behaviourally identical for every word. It must verify (else
    # SPEC-TOO-STRONG). It is also the honest replacement for the directive-2
    # ungrounded-oracle echo: because the oracle is grounded, echoing it is
    # CORRECT, not a wrong echo.
    {
        "id": "pos-cheapest-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    return image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows))\n"),
        "rationale": "Result() == image_fold(gid(), ToSeq(block_elems), "
                     "ToSeq(block_pows)) is immediate when the impl returns the "
                     "grounded fold directly; both arrays are only read, so the 1/2 "
                     "frame permissions and the equal-length Ensures are preserved "
                     "unchanged from the pre-state. A correct impl with a "
                     "structurally different (loop-free) shape must verify, else the "
                     "postcondition rejects a correct output (SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): forward loop, accumulator rename ----------
    # Keeps the gold forward control flow + EVERY gold invariant and the four
    # head/tail-split Asserts verbatim (only the accumulator is renamed w -> acc,
    # consistently EVERYWHERE inside the impl region, including the invariant
    # `image_fold(acc, ...)`). No proof obligation is dropped (pilot-bug-2); the
    # loop-invariant proof is byte-equivalent modulo the local name. MUST verify.
    {
        "id": "pos-loop-rename",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    acc = gid()\n"
            "    i = 0\n"
            "    while i < len(block_elems):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(block_elems), 1 / 2))\n"
            "        Invariant(Acc(list_pred(block_pows), 1 / 2))\n"
            "        Invariant(len(block_elems) == len(block_pows))\n"
            "        Invariant(0 <= i and i <= len(block_elems))\n"
            "        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))\n"
            "        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))\n"
            "        Invariant(image_fold(acc, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))\n"
            "                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))\n"
            "        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))\n"
            "        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])\n"
            "        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])\n"
            "        acc = gmul(acc, gpow(block_elems[i], block_pows[i]))\n"
            "        i = i + 1\n"
            "    return acc\n"),
        "rationale": "behaviourally identical forward per-block fold with the "
                     "accumulator renamed (w -> acc) consistently across the impl "
                     "region; every gold invariant (incl. image_fold(acc, ...)) and "
                     "all four head/tail-split Asserts are kept verbatim, so the "
                     "loop-invariant proof is unchanged. A reshape that keeps the "
                     "gold proof must verify (else SPEC-TOO-STRONG).",
    },

    # -- ADMISSIBILITY: the precondition admits a normal F2P-shaped relator ------
    # The impl self-calls relator_image on a freshly-built 2-block word that
    # mirrors the F2P discriminator: one positive block and one NEGATIVE-exponent
    # block (elems=[0,0], pows=[1,-1]) — exactly the inverted-generator shape of
    # D3's relator x_1*x_0*x_1**-1*x_0. The fresh lists are full-permission; the
    # 1/2 perms are threaded into the call and returned by the Ensures, equal
    # length 2. Then the gold loop runs on the real params. If the precondition
    # could not be established for this normal, negative-exponent input the
    # self-call would fail => PRECOND-TOO-STRONG. (The Result is left unconstrained
    # — image_fold over opaque ops is not pinned to a literal — so admissibility
    # is not confounded by a value-proof gap.)
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    we = [0, 0]  # type: List[int]\n"
            "    wp = [1, -1]  # type: List[int]\n"
            "    _img = relator_image(we, wp)  # type: int\n"
            "    w = gid()\n"
            "    i = 0\n"
            "    while i < len(block_elems):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(block_elems), 1 / 2))\n"
            "        Invariant(Acc(list_pred(block_pows), 1 / 2))\n"
            "        Invariant(len(block_elems) == len(block_pows))\n"
            "        Invariant(0 <= i and i <= len(block_elems))\n"
            "        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))\n"
            "        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))\n"
            "        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))\n"
            "                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))\n"
            "        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))\n"
            "        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])\n"
            "        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])\n"
            "        w = gmul(w, gpow(block_elems[i], block_pows[i]))\n"
            "        i = i + 1\n"
            "    return w\n"),
        "rationale": "a self-call on a freshly-built F2P-shaped relator (elems=[0,0], "
                     "pows=[1,-1]: equal length 2, one inverted-generator block) "
                     "establishes the Requires for a normal negative-exponent word "
                     "and returns the 1/2 permissions; the gold loop then runs on "
                     "the real params. Verifies => the precondition admits an "
                     "F2P-shaped input incl. the inverted-generator case (else "
                     "PRECOND-TOO-STRONG).",
    },

    # -- FRAME-MUTATION (uniqueness): append to the read-only block_pows ---------
    # MANDATORY: block_pows is Acc(list_pred(block_pows), 1/2) — READ-ONLY. This
    # rival appends to block_pows before running the gold fold (gold value-logic
    # verbatim). list.append needs the FULL list_pred, only 1/2 is held => rejected
    # for INSUFFICIENT PERMISSION. If it verified, the read-only frame is unguarded
    # (SPEC-TOO-WEAK on the frame).
    {
        "id": "frame-mutate-append-pows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    block_pows.append(0)\n" + _GOLD_IMPL),
        "refinement": "the faithful real patch corresponding to this write would "
                      "mutate the relator word's array_form (the (symbol, power) "
                      "block tuple) in place while computing its image. The gold "
                      "patch iterates `for symbol, power in r.array_form` and never "
                      "mutates r — sympy FreeGroupElement.array_form is a cached, "
                      "shared, immutable tuple, so a patch that appended to / rewrote "
                      "it would corrupt every other use of that relator (the same "
                      "relator object is iterated for every codomain check) and the "
                      "P2P test_isomorphisms invariants re-reading the relators would "
                      "observe the corruption — it would NOT resolve the suite.",
        "rationale": "rejected by the permission system: block_pows is held at "
                     "Acc(list_pred(block_pows), 1/2); list.append requires the FULL "
                     "list_pred, so the write is INSUFFICIENT-PERMISSION. The gold "
                     "fold value-logic is verbatim after the write, so the rejection "
                     "is attributable to the write. If it verified, the read-only "
                     "frame is unguarded (SPEC-TOO-WEAK).",
    },

    # -- FRAME-MUTATION supporting case (uniqueness): index store on block_elems -
    # A different write shape on the OTHER read-only input: block_elems[0] = 0
    # (guarded so it only fires on a non-empty word). Also needs the full
    # list_pred; the gold fold is verbatim. Rejected for INSUFFICIENT PERMISSION.
    {
        "id": "frame-mutate-index-elems",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    if len(block_elems) > 0:\n"
            "        block_elems[0] = 0\n" + _GOLD_IMPL),
        "refinement": "an in-place store into the relator's block carrier is not a "
                      "faithful _image fix: the gold patch reads each block via "
                      "`for symbol, power in r.array_form` and resolves `images[g]` "
                      "without mutating the relator. A patch that rewrote a block of "
                      "the cached, DAG-shared array_form / relator would change what "
                      "every other homomorphism check reports for that relator and "
                      "break the P2P test_isomorphisms relator-reuse invariants — it "
                      "would not resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: an in-place store to "
                     "block_elems[0] needs the full list_pred but only 1/2 is held. "
                     "Frame integrity of the read-only block carrier; gold value-"
                     "logic verbatim so the rejection attributes to the write.",
    },

    # -- PARTIAL-DOMAIN (uniqueness): the canonical bug — drop negative blocks ---
    # Correct for every NON-negative block; skips the factor of any
    # negative-exponent (inverted-generator) block. This IS the pre-patch
    # behaviour (model_prepatch.py, verbatim: `if block_pows[i] >= 0: w =
    # gmul(...)`). The gold invariants + asserts are kept verbatim; only the
    # multiply is guarded. It fails the loop invariant image_fold(w, drop(i)) ==
    # image_fold(gid(), full) on exactly the negative-exponent sub-domain (the
    # dropped factor makes the running product provably unequal to the full
    # per-block product, since gmul/gpow are opaque). Must be REJECTED.
    {
        "id": "partial-drop-negative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    w = gid()\n"
            "    i = 0\n"
            "    while i < len(block_elems):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(block_elems), 1 / 2))\n"
            "        Invariant(Acc(list_pred(block_pows), 1 / 2))\n"
            "        Invariant(len(block_elems) == len(block_pows))\n"
            "        Invariant(0 <= i and i <= len(block_elems))\n"
            "        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))\n"
            "        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))\n"
            "        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))\n"
            "                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))\n"
            "        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))\n"
            "        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])\n"
            "        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])\n"
            "        if block_pows[i] >= 0:\n"
            "            w = gmul(w, gpow(block_elems[i], block_pows[i]))\n"
            "        i = i + 1\n"
            "    return w\n"),
        "refinement": "this IS the pre-patch bug (model_prepatch.py): the old "
                      "two-index walk took the `else: s = r[i]` branch for an "
                      "inverted letter, matched neither `s in images` nor "
                      "`s**-1 in images`, and contributed NOTHING for a "
                      "negative-exponent block. The F2P test_homomorphism's added "
                      "D3 -> D3 identity map has relator x_1*x_0*x_1**-1*x_0 whose "
                      "x_1**-1 block is negative; dropping it yields a non-identity "
                      "image and a spurious ValueError('do not define a "
                      "homomorphism'), so T.is_isomorphism() is never reached — it "
                      "does NOT resolve (G-DIFF: model_prepatch fails here).",
        "rationale": "rejected by the loop invariant image_fold(w, drop(i), drop(i)) "
                     "== image_fold(gid(), full, full): skipping block i's gmul/gpow "
                     "leaves w one factor short while i advances, so the running "
                     "product is provably unequal to the full per-block product "
                     "(gmul/gpow are opaque, the missing factor cannot cancel). The "
                     "non-negative blocks fold correctly, so the rejection attributes "
                     "precisely to the negative-exponent sub-domain. If it verified, "
                     "per-block completeness on inverted generators is unpinned "
                     "(SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): drop the LAST block's factor ---------------
    # Correct for every block except the final one: the multiply is guarded by
    # `i < len - 1`, so the last factor is dropped. Diverges ONLY on words of
    # length >= 1, at exactly the final position. Catches a too-weak pin that an
    # interior-only attack would miss; gold invariants/asserts verbatim.
    {
        "id": "partial-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    w = gid()\n"
            "    i = 0\n"
            "    while i < len(block_elems):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(block_elems), 1 / 2))\n"
            "        Invariant(Acc(list_pred(block_pows), 1 / 2))\n"
            "        Invariant(len(block_elems) == len(block_pows))\n"
            "        Invariant(0 <= i and i <= len(block_elems))\n"
            "        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))\n"
            "        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))\n"
            "        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))\n"
            "                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))\n"
            "        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))\n"
            "        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])\n"
            "        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])\n"
            "        if i < len(block_elems) - 1:\n"
            "            w = gmul(w, gpow(block_elems[i], block_pows[i]))\n"
            "        i = i + 1\n"
            "    return w\n"),
        "refinement": "a patch that stops one block early (a `while i < len(r) - 1` "
                      "off-by-one, or forgetting the last `w *= images[g]**power`) "
                      "drops the final factor of every non-trivial relator. For the "
                      "F2P D3 relator the final x_0 factor would be missing, so the "
                      "computed image is not the identity and homomorphism() raises "
                      "the spurious 'do not define a homomorphism' error — "
                      "is_isomorphism() is never reached and it does NOT resolve.",
        "rationale": "rejected by the loop invariant: dropping the final block's "
                     "factor leaves w short by one opaque factor while i reaches "
                     "len, so at loop exit image_fold(w, empty) = w != "
                     "image_fold(gid(), full) (the missing factor cannot cancel "
                     "under opaque gmul/gpow). All interior blocks fold correctly, "
                     "so the rejection attributes precisely to the last-block "
                     "sub-domain. If it verified, the trailing factor is unpinned "
                     "(SPEC-TOO-WEAK).",
    },

    # -- VALUE / ORDER (uniqueness): commute the first factor (wrong order) ------
    # Multiplies the FIRST block on the LEFT of the accumulator (gmul(gpow,w))
    # instead of the right (gmul(w,gpow)); identical for every other block. Since
    # gmul is OPAQUE / NON-commutative, this produces a different product on words
    # of length >= 2 (for length 1, w=gid() so left/right agree — so it diverges
    # only on the multi-block sub-domain). Tests that the spec pins factor ORDER,
    # not just the multiset of factors. Gold invariants/asserts verbatim.
    {
        "id": "order-flip-first-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    w = gid()\n"
            "    i = 0\n"
            "    while i < len(block_elems):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(block_elems), 1 / 2))\n"
            "        Invariant(Acc(list_pred(block_pows), 1 / 2))\n"
            "        Invariant(len(block_elems) == len(block_pows))\n"
            "        Invariant(0 <= i and i <= len(block_elems))\n"
            "        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))\n"
            "        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))\n"
            "        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))\n"
            "                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))\n"
            "        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))\n"
            "        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])\n"
            "        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])\n"
            "        if i == 0:\n"
            "            w = gmul(gpow(block_elems[i], block_pows[i]), w)\n"
            "        else:\n"
            "            w = gmul(w, gpow(block_elems[i], block_pows[i]))\n"
            "        i = i + 1\n"
            "    return w\n"),
        "refinement": "a patch that multiplies factors in the wrong order (e.g. "
                      "`w = images[g]**power * w` instead of `w *= images[g]**power`) "
                      "computes the reversed/misordered product. The codomain "
                      "PermutationGroup is non-abelian, so for D3's relator the "
                      "misordered product is not the identity and homomorphism() "
                      "raises the spurious error — is_isomorphism() is never reached "
                      "and it does NOT resolve (the self-audit reversed-product "
                      "control in G-EQ likewise FAILS).",
        "rationale": "rejected by the load-bearing Ensures Result() == "
                     "image_fold(gid(), elems, pows): image_fold accumulates each "
                     "factor on the RIGHT (gmul(acc, gpow(...))), but this impl puts "
                     "the first factor on the LEFT. Because gmul is opaque / "
                     "non-commutative the verifier cannot prove gmul(x, gid()) == "
                     "gmul(gid(), x) for an opaque x, so the loop invariant fails for "
                     "the first block already, diverging on words of length >= 2. If "
                     "it verified, factor ORDER would be unpinned (SPEC-TOO-WEAK; the "
                     "non-commutative product would be admitted reversed).",
    },
]


# ===========================================================================
# AXIOM LANE
# Three @ContractOnly A-consumed axioms gid/gmul/gpow with the WEAKEST contract
# (Ensures(True)) — they cannot over-claim, so their soundness is trivial. The
# discriminating content is the A-REFERENCE deep model image_fold, validated
# == the real fixed `_image` by axiom_check.py (G-AX).
# ===========================================================================
#
# The runner mounts ONLY the probe script at /work; axiom_check.py / model.py are
# NOT in-container. The soundness probe therefore EMBEDS axiom_check.py's source
# (read on the HOST at manifest-load time) and EXECUTES the real callee (the
# fixed `_image` via the real sympy group machinery) under the gold patch. It
# never scrapes source (pilot-bug-4). The containment probe embeds model.py's +
# axiom_check.py's source (read on the HOST) and checks them statically + runs the
# real callee on a negative-exponent relator. Host file reads are decoded utf-8.

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")
_MODEL_SRC = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")

# axiom-soundness: run axiom_check.py's main() in-container under the gold patch.
# It exercises the monoid laws on a real DihedralGroup (identity / associativity /
# g*g**-1==e / g**-2==(g**-1)**2 — the negative/inverse-power law the bug dropped)
# and asserts the deep image_fold == the REAL fixed per-relator image on 9 group
# cases / 23 relators across PermutationGroups, FpGroups and FreeGroups, with at
# least one negative-exponent (inverted-generator) relator REQUIRED to be
# exercised. Exit 0 iff every obligation holds.
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# ---- PBT axiom-soundness driver (appended) --------------------------------
import sys as _sys
print("PBT axiom-soundness: running the REAL fixed _image (real sympy group "
      "machinery) on every relator of D3/D4/D5/C6/A4/S4 + FpGroups and asserting "
      "the deep image_fold reproduces it, INCLUDING inverted-generator "
      "(negative-exponent) relators, plus the monoid laws (identity / "
      "associativity / g*g**-1==e / negative powers).")
try:
    _rc = main()
except SystemExit as _e:
    _rc = _e.code if isinstance(_e.code, int) else 1
except AssertionError as _ae:
    print("PBT axiom-soundness FAIL: axiom UNSOUND / A-reference disagreement:", _ae)
    _sys.exit(1)
if _rc not in (0, None):
    print("PBT axiom-soundness FAIL: axiom_check.main() rc=%r" % (_rc,))
    _sys.exit(1)
_sys.exit(0)
"""

# axiom-containment: the opaque gid/gmul/gpow carry NO domain restriction
# (Ensures(True); gpow is documented total over EVERY integer exponent incl.
# negative), so every caller-reachable callee input is trivially inside their
# domain — there is no containment defect possible for them. For the A-reference
# deep model image_fold, the model's only Requires on the carrier is equal-length
# int arrays (Requires(len(block_elems) == len(block_pows)) +
# Requires(len(ToSeq...) == len(ToSeq...))) with ARBITRARY (incl. negative)
# exponents; axiom_check.py validates image_fold == real _image on exactly that
# domain and ASSERTS a negative-exponent relator is exercised (any_negative). We
# confirm statically (AST over host-read sources): (1) the model's only carrier
# Requires are the two equal-length predicates (no exponent-sign restriction), and
# (2) axiom_check.py asserts a negative-exponent relator is covered; then we
# EXECUTE the real callee on a negative-exponent relator to show the discriminating
# input is inside the validated domain. A reachable input outside the validated
# domain would be A-reference-TOO-WEAK-FOR-CALLER.
_AX_COVER_PROBE = (
    "import sys, ast\n"
    "MODEL_SRC = " + repr(_MODEL_SRC) + "\n"
    "AXIOM_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "# 1) the model's only carrier Requires are the two equal-length predicates;\n"
    "#    there is NO exponent-sign / value restriction, so the reachable callee\n"
    "#    domain is 'equal-length int arrays with arbitrary (incl. negative) exps'.\n"
    "need = ['Requires(len(block_elems) == len(block_pows))',\n"
    "        'Requires(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))']\n"
    "missing = [s for s in need if s not in MODEL_SRC]\n"
    "if missing:\n"
    "    print('model.py missing expected carrier precondition(s):', missing); sys.exit(1)\n"
    "# there must be NO precondition restricting exponent sign/value (e.g. >= 0).\n"
    "forbidden = ['block_pows[', 'Requires(block_pows', 'Forall']\n"
    "# (scan only the Requires lines of relator_image for an exponent restriction)\n"
    "model_req_lines = [ln for ln in MODEL_SRC.splitlines() if 'Requires(' in ln]\n"
    "bad = [ln for ln in model_req_lines if ('>= 0' in ln and 'block' in ln) or ('> 0' in ln and 'block' in ln)]\n"
    "if bad:\n"
    "    print('unexpected exponent-restricting precondition:', bad); sys.exit(1)\n"
    "print('model precondition restricts the carrier only to equal-length int '\n"
    "      'arrays; exponents are unrestricted (incl. negative) -> the reachable '\n"
    "      'callee domain for the A-reference is exactly that.')\n"
    "# 2) axiom_check.py REQUIRES a negative-exponent relator be exercised\n"
    "#    (any_negative assertion). Parse the AST, not a docstring (pilot-bug-4).\n"
    "tree = ast.parse(AXIOM_SRC)\n"
    "has_neg_assert = False\n"
    "for node in ast.walk(tree):\n"
    "    if isinstance(node, ast.Assert):\n"
    "        d = ast.dump(node)\n"
    "        if 'any_negative' in d or 'saw_negative' in d:\n"
    "            has_neg_assert = True\n"
    "if not has_neg_assert:\n"
    "    print('axiom_check.py does not assert a negative-exponent relator is '\n"
    "          'exercised; the discriminating sub-domain may be uncovered'); sys.exit(1)\n"
    "print('axiom_check.py asserts a negative-exponent (inverted-generator) relator '\n"
    "      'is exercised -> the discriminating sub-domain is inside the validated '\n"
    "      'domain.')\n"
    "# 3) EXECUTE the real callee on a NEGATIVE-exponent relator to show the\n"
    "#    discriminating input is genuinely reachable and validated. D3's presentation\n"
    "#    relator contains an inverted generator (negative exponent).\n"
    "from sympy.combinatorics.named_groups import DihedralGroup\n"
    "D3 = DihedralGroup(3)\n"
    "gens = D3.presentation().generators\n"
    "symbols = [g.ext_rep[0] for g in gens]\n"
    "s2g = dict(zip(symbols, D3.generators))\n"
    "images = dict(zip(D3.generators, D3.generators))\n"
    "identity = list(images.values())[0] ** 0\n"
    "found_neg = False\n"
    "for r in D3.presentation().relators:\n"
    "    pows = [power for _, power in r.array_form]\n"
    "    if any(p < 0 for p in pows):\n"
    "        found_neg = True\n"
    "        # the fixed _image computes a well-defined product on this neg-exp word\n"
    "        w = identity\n"
    "        for symbol, power in r.array_form:\n"
    "            w *= images[s2g[symbol]] ** power\n"
    "        # the negative power is total (no exception); the input is in-domain.\n"
    "        assert w is not None\n"
    "if not found_neg:\n"
    "    print('expected a negative-exponent relator in D3 presentation'); sys.exit(1)\n"
    "print('AXIOM-CONTAINMENT OK: gid/gmul/gpow have no domain restriction "
    "(Ensures(True), gpow total over every integer exponent), and the A-reference "
    "image_fold is validated by axiom_check.py on exactly the model-reachable "
    "domain (equal-length int arrays, exponents unrestricted) with the "
    "negative-exponent sub-domain explicitly required and shown reachable -> no "
    "caller-reachable input lies outside the validated domain (no "
    "A-reference-TOO-WEAK-FOR-CALLER).')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-image_fold",
        "axiom": "image_fold",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the deep model image_fold is the A-reference for the CHANGED "
                     "operation (the per-relator image product). The REAL fixed "
                     "`_image`, under the gold patch, must reproduce it on every "
                     "relator of a battery of real groups (D3/D4/D5/C6/A4/S4 "
                     "PermutationGroups + FpGroups + FreeGroups), INCLUDING relators "
                     "with inverted-generator (negative-exponent) blocks — the "
                     "discriminating case — and the opaque gid/gmul/gpow monoid laws "
                     "(identity / associativity / g*g**-1==e / negative powers) must "
                     "hold. If the real callee disagreed anywhere, the A-reference (or "
                     "a monoid axiom) would be UNSOUND. Runs axiom_check.py's main() "
                     "in the instance image with the gold patch applied.",
    },
    {
        "id": "ax-cover-image_fold",
        "axiom": "image_fold",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "the opaque gid/gmul/gpow carry NO domain restriction "
                     "(Ensures(True); gpow total over every integer exponent), so no "
                     "containment defect is possible for them. For the A-reference "
                     "image_fold, the model's only carrier Requires are equal-length "
                     "int arrays with arbitrary (incl. negative) exponents; "
                     "axiom_check.py validates image_fold == real _image on exactly "
                     "that domain and ASSERTS a negative-exponent relator is "
                     "exercised. The probe confirms (AST) the model has no "
                     "exponent-sign precondition and axiom_check covers the negative "
                     "case, then runs the real callee on D3's negative-exponent "
                     "relator to show the discriminating input is reachable and "
                     "in-domain. A reachable input outside the validated domain would "
                     "be A-reference-TOO-WEAK-FOR-CALLER.",
    },
]
