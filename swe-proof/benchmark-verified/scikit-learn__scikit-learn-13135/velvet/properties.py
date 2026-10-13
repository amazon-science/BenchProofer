"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13135 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct computeBoundaries`` header survives) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect="verify"`` passes iff
(in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: the witness must ELABORATE
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method, one obligation):

  computeBoundaries (centers : List Rat) (lo : Rat) (hi : Rat) return (out : List Rat)
    ensures out = boundaries centers lo hi                      -- the WHOLE pin (C1)

  where the pure region fixes, transparently:

    asc xs        = xs.mergeSort (· ≤ ·)          -- ascending reorder
    mids          — adjacent-pair averages, front-recursive:
                    mids (a :: b :: rest) = (a + b) / 2 :: mids (b :: rest)
    boundaries centers lo hi = [lo] ++ mids (asc centers) ++ [hi]

The method reports the bracketed boundary sequence of a spread of representatives
between two endpoints: the lower endpoint, then the average of each adjacent pair
of the representatives TAKEN IN ASCENDING ORDER, then the upper endpoint.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 is the sole ``ensures`` and the sole
obligation, and it is an exact equality to ``boundaries centers lo hi`` — a
closed, total, TRANSPARENT function of the method's own three arguments. The
``axioms`` region is empty: there is no opaque callee and no answer key an impl
could echo, so pinning ``out = boundaries centers lo hi`` is GROUNDED (spec_guide
directive 8) and the only way to meet it is to do the computation. Unrolling C1
gives the independent structural facts every rival must respect, and each is a
distinct attack surface:

  (S1) length   — one more entry than there are adjacent pairs, i.e. the
                  representative count (the sequence is not short or long);
  (S2) head     — the first entry is the LOWER endpoint ``lo``;
  (S3) tail     — the last entry is the UPPER endpoint ``hi``;
  (S4) order    — the interior entries appear in the order ``mids`` emits them
                  (ascending), not reversed;
  (S5) values   — each interior entry is the AVERAGE of its own ADJACENT pair
                  of ASCENDING representatives — not a representative itself, not
                  an endpoint, not an average of a non-adjacent pair, and not an
                  average taken over the representatives in their ORIGINAL order.

S5 is the load-bearing distinction and the one the reported failure is about: the
pre-change reading paired the representatives in the order they arrived, WITHOUT
the ascending reorder, so the interior entries were not the ascending-adjacent
averages and the bracketed sequence was non-monotone — which the issue reports as
fatal to the downstream binning step. C1's midpoints are taken over ``asc
centers``, so any impl pairing the raw order contradicts C1 at every input whose
representatives are not already ascending.

CARRIER NOTE (decisive for this port, and for the witness route). The carrier is
Mathlib ``Rat`` — exact, order-faithful, and computable (mapping.md §2: this is
an ORDER-ONLY change, so there is no IEEE rounding confound). Both ``mids`` and
``boundaries`` are transparent computable ``def``s, so a rival's disagreement with
C1 is DECIDABLE at a concrete literal input: no conditioning on an opaque term is
needed, no witness here binds a hypothesis, and the gate's consistency probe is a
no-op for every case. What is NOT decidable on this carrier is the FROZEN IMPL's
executable image (its ``while`` fold) and the two library recursions ``asc`` and
``Rat`` division — see WITNESS MECHANICS, where each is handled separately.

WITNESS MECHANICS (five measured facts, in the order they were hit; facts 4 and
5 are why the first cut of this battery was recorded MALFORMED-TESTS and what
repaired it).

  1. The tester+``decide`` route is DEAD. ``prove_postcondition_decidable_for`` /
     ``derive_tester_for`` yield a tester on which ``decide`` gets stuck at
     ``instDecidableEqRat`` — the spec_guide ``Rat`` trap. So each witness instead
     EXTRACTS the executable program (``extract_program_for computeBoundaries``)
     and refutes C1 directly against the transparent ``boundaries``:

         (match computeBoundariesExec <centers> <lo> <hi> with
            | DivM.res r => r | _ => []) ≠ boundaries <centers> <lo> <hi>

     Every rival is written LOOP-FREE, so its ``…Exec`` reduces.

  2. ``asc`` does not reduce: ``mergeSort`` is well-founded recursion, so no
     closer can compute ``asc [3, 1, 5]``. Each witness therefore discharges the
     reorder as its own lemma-free side goal first,
     ``rw [show asc <literal> = <ascending literal> by simp +decide
     [asc, List.mergeSort]]``.

  3. Bare ``decide`` does not compute ``Rat`` DIVISION: it gets stuck at
     ``((1 + 3).mul (Rat.inv 2)).num``. It DOES decide equality and disequality
     of ``Rat`` LITERAL lists (measured: ``[0,2,4,6] ≠ [0,2,3,6]`` closes by
     ``decide``, and the false form is reported as ``decide proved that the
     proposition … is false``). So the witness's job is to reach literals.

  4. ``decide +kernel`` does compute the division — and that is a TRAP, not the
     closer, because it reports a FALSE claim with the same ``did not reduce to
     `isTrue` or `isFalse` `` text a genuinely stuck claim produces. The gate
     reads that text as `witness-undecided` (it cannot distinguish "the kernel
     never evaluated this" from "the kernel evaluated it and the claim is
     false"), so a ``decide +kernel`` closer makes the REFUTED side of the check
     indistinguishable from a stuck one and the case attributes nothing. Fact 3's
     plain ``decide`` is the closer instead; ``decide +kernel`` appears ONLY
     inside ``show`` side goals for individual midpoint values, where the claim
     is true by construction and the kernel is being used as a calculator.

     So each witness normalizes to literals with one ``simp`` stage that carries
     the adjacent-pair average of every ordered pair of the probed
     representatives as a kernel-decided rewrite —
     ``show (((a:Rat) + b) / 2) = <literal> from by decide +kernel`` — and then
     closes with plain ``decide``. Full ``simp`` (not ``simp only``) because two
     rivals reach the interior through list operations (``head!``, ``tail``,
     ``dropLast``, ``drop``, ``map``) that need simp's own list lemmas before any
     midpoint appears; ``simp only [mids, …]`` left those stuck.

  5. GOLD CANNOT BE THE SECOND SUBJECT. The frozen impl keeps the backward
     ``while`` fold, and under ``loom.semantics.choice "demonic"`` its ``…Exec``
     elaborates through ``forIn``/``invariantGadget`` terms the kernel does not
     unfold. Measured: against gold every claim is stuck — the real refutation,
     and equally a trivially true one — so gold's exit code carries no
     information and a forged witness asserting a rival is CORRECT would clear
     both halves. That is exactly the ``witness-undecided`` shape the gate
     refuses, and it is what the first cut of this battery hit on all of the
     rivals then present.

     The repair is the documented one: every reject case names a
     ``witness_reference`` — ``_LOOPFREE``, a loop-free impl of the SAME frozen
     spec that the gate independently checks shares the spec and VERIFIES. An
     impl the verifier accepts cannot violate its own spec, so a genuine witness
     must still fail there, and being loop-free it REDUCES, so its failure is a
     decided refutation rather than a stuck one. ``pos-control-direct`` carries
     the identical source as an ``expect="verify"`` case, so the battery itself
     records that loop-freeness is not what any rival is rejected for.

No witness uses ``sorry``/``admit``/``native_decide``/``axiom``/``opaque``. All
NINE were checked out-of-band with ``scripts/lean_verify.sh``, two builds each:
every one ELABORATES against its rival (exit 0) and FAILS against ``_LOOPFREE``
with ``Tactic `decide` proved that the proposition … is false`` — a DECIDED
refutation, verified by grep on all eighteen logs to contain no ``did not reduce
to `isTrue` or `isFalse` `` text on either side.

INDEPENDENTLY RE-DERIVED BY THE AUDIT (attack B′, the FORGERY test), which is
what upgrades the paragraph above from a self-report to evidence. For each of the
nine rivals FOUR builds were re-run: the witness against the rival (exit 0), the
witness against ``_LOOPFREE`` (exit 1, ``decide`` proved the proposition FALSE),
the witness against GOLD (exit 1, but ``Tactic `decide` failed … did not reduce
to `isTrue` or `isFalse` `` on the ``forIn``/``invariantGadget`` term — which is
precisely fact 5, and precisely why gold is not the subject), and the FLIPPED
claim (``≠`` swapped for ``=``) against ``_LOOPFREE``. The flip is the decisive
one: it ELABORATES, exit 0, for all nine. So the reference's exit code TRACKS the
claim — asserting the correct value succeeds there and asserting the wrong one is
decided false — which is what makes the refutation real rather than a shape
artifact. Against GOLD the flipped claim fails with the byte-identical stuck
error as the true claim, confirming from the other side that gold carries no
information here and that the ``witness_reference`` is not a convenience.

ADVERSARIAL READ of the nagini classes on THIS carrier (full accounting in the
footer):
  * SOUNDNESS / positive controls — APPLY, and they are the real work here: a
    reshaped impl needs a proof that closes for the NEW shape. Three ported.
  * ADMISSIBILITY — RE-AIMED. The ``pre-conditions`` region is EMPTY (no
    ``require``), so the nagini "a normal input is admitted" probe is vacuous as
    stated; re-aimed at the residual risk that the domain is silently restricted
    to inputs on which the reorder is a NO-OP.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling records
    ``has_readonly_input == False`` outright (all six of its inputs are by-value
    scalars; there is no fractional-permission token anywhere in its contract), so
    there was nothing to port even there. Vacuous here for the stronger backend
    reason too: Velvet is referentially transparent, all three inputs are
    immutable values, and this bundle declares no ``mut`` parameter — there is no
    read-only input to overwrite and no heap, aliasing or permission system to
    subvert. No substitute probe is fabricated.
  * DIVERGENCE / NON-TERMINATION: CLOSED BY THE SEMANTICS, in both of its
    shapes, and re-measured on this bundle. The file sets
    ``set_option loom.semantics.termination "total"`` (in Loom that option is
    itself what opens ``TotalCorrectness`` scope), so a postcondition is claimed
    of ALL runs and every ``while`` owes a measure that STRICTLY DECREASES. With
    the ``decreasing`` clause omitted the elaborator refuses outright
    (``Decreasing annotations are required in total correctness semantics``);
    with the clause PRESENT but its measure constant, the descent goal ITSELF is
    what fails (``case «decreasing_1: q» ... q < q``), so the class is not
    reachable by supplying a fake measure either. What blocks a reject case here
    is the witness contract, not the spec: the full measurement and that
    argument are in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the nagini sibling
    reasoned it: C1 pins the result to a transparent function of the arguments,
    so "echoing the oracle IS doing the work". The nagini file's directive-2
    fallback (ship honest positives instead, and separately probe whether the
    VALUE clause is load-bearing beyond the weaker monotonicity clause) is ported
    faithfully — see reject-flat-interior.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13135"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the backward `while`
# ---- fold), everything strictly BETWEEN the method's `-- impl-start` and
# ---- `-- impl-end` marker lines. It lies wholly inside that single region and is
# ---- unique in the file (both facts asserted at load by _swap / the assert
# ---- below), so every edit keeps `same_spec` by construction and leaves the
# ---- `prove_correct computeBoundaries` header intact.
_IMPL = (
    "    let ys := asc centers\n"
    "    let mut result : List Rat := []\n"
    "    let mut i := ys.length\n"
    "    while i ≥ 2\n"
    "      invariant i ≤ ys.length\n"
    "      invariant result = mids (ys.drop (i - 1))\n"
    "      done_with i ≤ 1\n"
    "      decreasing i\n"
    "    do\n"
    "      let m := (ys[i - 2]! + ys[i - 1]!) / 2\n"
    "      result := m :: result\n"
    "      i := i - 1\n"
    "    return lo :: (result ++ [hi])"
)
assert _BASE.count(_IMPL) == 1, "computeBoundaries impl region drifted from expected text"

# ---- The first impl line alone: the insertion anchor for an in-region
# ---- admissibility `assert`, which is prepended to an OTHERWISE-GOLD impl.
_IMPL_HEAD = "    let ys := asc centers\n"
assert _BASE.count(_IMPL_HEAD) == 1, "impl head anchor drifted"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshaped positive may retune it without touching
# ---- the spec or dropping the obligation. Unique in the file.
_PROOF = (
    "prove_correct computeBoundaries by\n"
    "  loom_solve\n"
    "  · -- loop body: the backward fold peels one midpoint\n"
    "    have he : i - 1 - 1 = i - 2 := by omega\n"
    "    rw [he, mids_drop_step (asc centers) i (by omega) (by omega)]\n"
    "    simp_all\n"
    "  · -- exit (i ≤ 1): drop (i-1) is the whole sorted list, so result = mids (asc centers)\n"
    "    have hi0 : i - 1 = 0 := by omega\n"
    "    simp only [boundaries, hi0, List.drop_zero, List.singleton_append] at *\n"
    "    simp_all"
)
assert _BASE.count(_PROOF) == 1, "prove_correct computeBoundaries body drifted"

# The proof a LOOP-FREE reshape needs: with no loop there is no backward-fold
# goal, so the residual obligation is `boundaries`-definitional.
_PROOF_LOOPFREE = (
    "prove_correct computeBoundaries by\n"
    "  loom_solve\n"
    "  simp [boundaries]"
)


def _impl_reproved(new_body, new_proof=_PROOF_LOOPFREE):
    """Impl body replaced AND the (elided) tactic body retuned for the new shape."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- THE WITNESS REFERENCE (see WITNESS MECHANICS fact 5). The frozen impl's
# ---- `while` fold does not reduce under demonic choice, so `decide` against it
# ---- is stuck for EVERY claim and its exit code discriminates nothing. This is
# ---- a loop-free impl of the SAME frozen spec — byte-identical to the
# ---- `pos-control-direct` case's source, which the battery separately asserts
# ---- VERIFIES — for the gate to refute each witness against instead. The gate
# ---- re-checks both properties itself (shares the frozen spec, and verifies)
# ---- before using it, and being loop-free it reduces, so its failure on a
# ---- witness is a DECIDED refutation.
_LOOPFREE = _impl_reproved("    return lo :: (mids (asc centers) ++ [hi])")


def _rat(x):
    """A `Rat` literal for the Lean source: parenthesized when negative."""
    from fractions import Fraction
    x = Fraction(x)
    s = str(x.numerator) if x.denominator == 1 else f"({x.numerator}/{x.denominator})"
    return f"({s})" if x < 0 else s


# ---- witness builder. Extracts the executable program and refutes C1 directly
# ---- against the transparent `boundaries` at ONE concrete input. Three stages,
# ---- each forced by a measured fact (see WITNESS MECHANICS):
# ----   (a) unfold the executable image and the spec's own defs;
# ----   (b) resolve the reorder as a lemma-free `simp +decide` side goal, since
# ----       `mergeSort` is well-founded recursion no closer can compute;
# ----   (c) normalize to `Rat` LITERALS with one full `simp` stage carrying the
# ----       adjacent-pair average of every ordered pair of the probed
# ----       representatives as a kernel-decided rewrite, then close with plain
# ----       `decide` — which decides literal `Rat` list (dis)equality, whereas
# ----       `decide +kernel` as the CLOSER would report a false claim with the
# ----       same "did not reduce" text a stuck claim produces and so could not
# ----       be told apart from `witness-undecided`.
# ---- Only the representatives enter (c): no clause of C1 halves an endpoint.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict.
def _witness(centers, lo, hi):
    from fractions import Fraction
    cs = [Fraction(c) for c in centers]
    pool = list(dict.fromkeys(cs))
    facts = ",\n".join(
        f"    show ((({_rat(a)}:Rat) + {_rat(b)}) / 2) = {_rat((a + b) / 2)}"
        " from by decide +kernel"
        for a in pool for b in pool)
    clist = "[" + ", ".join([f"({_rat(cs[0])}:Rat)"]
                            + [_rat(c) for c in cs[1:]]) + "]"
    olist = "[" + ", ".join(_rat(c) for c in sorted(cs)) + "]"
    inp = f"{clist} {_rat(lo)} {_rat(hi)}"
    return (
        "extract_program_for computeBoundaries\n"
        "\n"
        "example :\n"
        f"    (match computeBoundariesExec {inp} with | DivM.res r => r | _ => [])\n"
        f"      ≠ boundaries {inp} := by\n"
        "  simp only [computeBoundariesExec, computeBoundaries, boundaries, pure]\n"
        f"  rw [show asc {clist} = {olist}"
        " by simp +decide [asc, List.mergeSort]]\n"
        f"  simp [mids,\n{facts}]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify, else the spec is SPEC-TOO-STRONG. On this backend each
    # needs a proof that actually closes for the NEW shape; the obligation
    # STATEMENT (the `method` header, which lives in the spec view) is untouched
    # and only the elided tactic body is retuned. All three verified EXIT 0
    # out-of-band with scripts/lean_verify.sh.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the boundary sequence DIRECTLY through the transparent
        # pure defs, with no per-pair loop at all. C1 is literally `out =
        # boundaries centers lo hi`, so this is the cheapest HONEST correct impl.
        # The loop is gone, so the frozen proof's backward-fold step lemma is
        # unneeded and the residual goal is `boundaries`-definitional.
        #
        # This is the SAME SOURCE every reject case names as its
        # `witness_reference`, deliberately: the gate refutes each witness
        # against `_LOOPFREE` because gold's `while` fold cannot decide anything,
        # and shipping that source here as a case makes the battery itself record
        # that it VERIFIES — so loop-freeness is demonstrably not the property any
        # rival is being rejected for.
        "module": _LOOPFREE,
        "rationale": (
            "PASS SOURCE = C1 (`out = boundaries centers lo hi`). The post-image "
            "is GROUNDED in the three arguments (transparent total defs, empty "
            "`axioms` region, no answer key), so building the sequence directly "
            "from those defs is the honest cheapest CORRECT impl and C1 is "
            "literally that equality — it MUST verify, else C1 over-constrains "
            "the executable staging (SPEC-TOO-STRONG). Ports the nagini "
            "directive-2 honest-echo control: because the pin is grounded, the "
            "cheapest impl satisfying it is doing the real work, which is why the "
            "'wrong echo' rival class has no member here (any wrong pairing or "
            "wrong order fails C1 — see the nine reject cases)."
        ),
    },
    {
        "id": "pos-control-loop-rename",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep gold's backward `while` fold, its invariant and its
        # `done_with` guard, but rename every local (ys→sorted, result→acc, i→k,
        # m→b). Same value flow, different surface. The frozen proof references
        # the loop counter by name, so the (elided) tactic body is retuned to the
        # new name; nothing else changes.
        "module": _impl_reproved(
            "    let sorted := asc centers\n"
            "    let mut acc : List Rat := []\n"
            "    let mut k := sorted.length\n"
            "    while k ≥ 2\n"
            "      invariant k ≤ sorted.length\n"
            "      invariant acc = mids (sorted.drop (k - 1))\n"
            "      done_with k ≤ 1\n"
            "      decreasing k\n"
            "    do\n"
            "      let b := (sorted[k - 2]! + sorted[k - 1]!) / 2\n"
            "      acc := b :: acc\n"
            "      k := k - 1\n"
            "    return lo :: (acc ++ [hi])",
            "prove_correct computeBoundaries by\n"
            "  loom_solve\n"
            "  · -- loop body: the backward fold peels one midpoint\n"
            "    have he : k - 1 - 1 = k - 2 := by omega\n"
            "    rw [he, mids_drop_step (asc centers) k (by omega) (by omega)]\n"
            "    simp_all\n"
            "  · -- exit: the whole reordered spread is consumed\n"
            "    have hi0 : k - 1 = 0 := by omega\n"
            "    simp only [boundaries, hi0, List.drop_zero,"
            " List.singleton_append] at *\n"
            "    simp_all"),
        "rationale": (
            "PASS SOURCE = C1. A correct impl with the SAME backward fold, "
            "invariant and guard as gold but every local renamed — same "
            "accumulation, different surface. It MUST verify, else the spec "
            "over-fits the exact local names of the frozen code form "
            "(SPEC-TOO-STRONG). Ports the nagini pos-reverse-midpoint-order "
            "argument (a structurally-different-but-correct impl over the same "
            "computation must not be rejected) onto the loop carrier: nagini's "
            "reshape reordered three straight-line midpoint assignments, which on "
            "this carrier is the loop's per-step body, so the renamed fold is the "
            "faithful counterpart."
        ),
    },
    {
        "id": "pos-control-staged-concat",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the reordered spread and its adjacent-pair averages to
        # named locals, then assemble the result by a DIFFERENT concatenation
        # split — `(lo :: ms) ++ [hi]` instead of `lo :: (ms ++ [hi])`. Same
        # value, different associativity/staging of the assembly.
        "module": _impl_reproved(
            "    let ys := asc centers\n"
            "    let ms := mids ys\n"
            "    return (lo :: ms) ++ [hi]"),
        "rationale": (
            "PASS SOURCE = C1. Stage the computation through named locals and "
            "assemble the sequence with a DIFFERENT concatenation split "
            "(`(lo :: ms) ++ [hi]` vs gold's `lo :: (ms ++ [hi])`) — the same "
            "value, a different bracketing of the assembly. It MUST verify, else "
            "C1 over-constrains how the endpoints are attached rather than WHAT "
            "sequence results (SPEC-TOO-STRONG). Ports the nagini pos-append-build "
            "argument (build the sequence by a different assembly route, not one "
            "literal) onto this carrier."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-f2p-shaped-input case. That
    # case established that the `Requires` admits an F2P-shaped input (an
    # unordered spread inside the endpoint range) and is non-vacuous. This method
    # has NO `require` at all (the `pre-conditions` region is EMPTY), so nothing
    # could exclude any input and the probe as stated is vacuous. Re-aimed at the
    # residual risk that IS live on a total domain: that the modeled domain is
    # silently restricted to inputs on which the reorder is a NO-OP (a spec whose
    # only satisfiable inputs are already-ascending spreads would read exactly
    # like one that pins the reorder). The in-region `assert` is a live decidable
    # claim about the reported failure shape — an UNORDERED spread — and a false
    # conjunct leaves an unsolved goal. Verified EXIT 0.
    # =====================================================================
    {
        "id": "admiss-unordered-spread",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_HEAD,
                "    -- Admissibility probe on the shape the reported failure "
                "drives: a spread of\n"
                "    -- representatives that is NOT already ascending is "
                "in-domain, the boundary\n"
                "    -- sequence it produces has one entry more than there are "
                "adjacent pairs, the\n"
                "    -- reorder genuinely CHANGES the answer (so the domain is "
                "not silently\n"
                "    -- restricted to inputs on which reordering is a no-op), and "
                "two spreads that\n"
                "    -- differ only in arrival order agree.\n"
                "    assert (with_name_prefix `adm\n"
                "      ((boundaries [(9:Rat), 1, 3] 0 10).length = 4 ∧\n"
                "       boundaries [(9:Rat), 1, 3] 0 10 ≠ [(0:Rat)] ++"
                " mids [(9:Rat), 1, 3] ++ [10] ∧\n"
                "       boundaries [(9:Rat), 1, 3] 0 10 ="
                " boundaries [(1:Rat), 3, 9] 0 10))\n" + _IMPL_HEAD),
            _PROOF,
            "prove_correct computeBoundaries by\n"
            "  loom_solve\n"
            "  · -- the admissibility claim, decided outright at the probed shape\n"
            "    refine ⟨?_, ?_, ?_⟩ <;>\n"
            "      simp only [boundaries,\n"
            "        show asc [(9:Rat), 1, 3] = [1, 3, 9]"
            " by simp +decide [asc, List.mergeSort],\n"
            "        show asc [(1:Rat), 3, 9] = [1, 3, 9]"
            " by simp +decide [asc, List.mergeSort]] <;>\n"
            "      decide +kernel\n"
            "  · -- loop body: the backward fold peels one midpoint\n"
            "    have he : i - 1 - 1 = i - 2 := by omega\n"
            "    rw [he, mids_drop_step (asc centers) i (by omega) (by omega)]\n"
            "    simp_all\n"
            "  · -- exit: the whole reordered spread is consumed\n"
            "    have hi0 : i - 1 = 0 := by omega\n"
            "    simp only [boundaries, hi0, List.drop_zero,"
            " List.singleton_append] at *\n"
            "    simp_all"),
        "rationale": (
            "the method carries NO `require`, so it is total and the nagini "
            "'a normal input is admitted' probe is vacuous as stated; re-aimed at "
            "the live total-domain risk that the modeled domain is silently "
            "restricted to inputs on which the reorder is a NO-OP. The in-region "
            "`assert` is a live decidable claim about the shape the reported "
            "failure drives — an UNORDERED spread — asserting three things at "
            "once: the boundary sequence is well-formed and one longer than the "
            "adjacent-pair count, the reorder genuinely CHANGES the answer there "
            "(so unordered inputs are not degenerate under the spec), and two "
            "spreads differing only in arrival order agree. A false conjunct "
            "leaves an unsolved goal. The impl is otherwise gold so C1 still "
            "discharges. If it cannot verify => PRECOND-TOO-STRONG / the domain "
            "excludes the very regime the change targets."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1; between them they hit
    # all five of its independent structural facts S1..S5 — S1 in BOTH
    # directions since the audit added reject-long-sequence — and the three input
    # binders are varied across eight distinct input points.
    # =====================================================================
    {
        "id": "reject-unordered-pairing",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour and the G-DIFF discriminator (this IS
        # Solution_prepatch.lean's impl region, written loop-free so its `…Exec`
        # reduces): pair the representatives in the order they ARRIVED, with no
        # ascending reorder. Correct on any already-ascending spread, WRONG on
        # every other. Refuted at the unordered `[3, 1, 5]`.
        "module": _impl_reproved(
            "    return lo :: (mids centers ++ [hi])"),
        "refinement": (
            "this IS the pre-change reading: the adjacent-pair averages are taken "
            "over the representatives in their ORIGINAL arrival order, with no "
            "ascending reorder first. Its faithful real counterpart is the "
            "unmodified pre-change source. On the failing test's column the "
            "upstream representatives come out NOT ascending, so the interior "
            "entries are out of order and the bracketed boundary sequence is "
            "non-monotone; the downstream binning step rejects a non-monotone "
            "boundary sequence outright (`ValueError: bins must be monotonically "
            "increasing or decreasing`, quoted in the problem statement) and the "
            "computation never reaches the expected assignment. So it does NOT "
            "resolve — and `Solution_prepatch.lean` carries exactly this skeleton "
            "and fails verification (G-DIFF)."
        ),
        "rationale": (
            "REJECT from C1, fact S5: `boundaries` takes its adjacent-pair "
            "averages over `asc centers`, so a rival pairing the raw arrival order "
            "diverges wherever the spread is not already ascending. Refuted at "
            "`centers = [3, 1, 5]`, `lo = 0`, `hi = 6`: the rival averages the "
            "arrival-adjacent pairs (3,1) and (1,5), C1 forces the "
            "ascending-adjacent (1,3) and (3,5). Correct on already-ascending "
            "spreads (a genuine partial-domain break, which is why the defect "
            "survived in the field). If it VERIFIED => SPEC-TOO-WEAK: the spec "
            "would admit the reported bug."
        ),
        "witness": _witness([3, 1, 5], 0, 6),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-partial-last-pair",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of the above, and given its OWN input: reorder the spread and
        # take every interior entry from the reordered spread EXCEPT the last,
        # which is taken from the raw last two representatives (the shape of a
        # stale slice read before the reorder settles). Agrees with gold on a
        # STRICTLY LARGER sub-domain than reject-unordered-pairing — every spread
        # whose last two arrivals are its two largest — so it needs its own,
        # more discriminating point.
        "module": _impl_reproved(
            "    let ys := asc centers\n"
            "    return lo :: ((mids ys).dropLast"
            " ++ mids (centers.drop (centers.length - 2)) ++ [hi])"),
        "refinement": (
            "partial-domain: its faithful counterpart reorders the "
            "representatives but computes the LAST interior entry from a slice of "
            "the ORIGINAL arrival order (a stale read of the last two arrivals "
            "taken before the reorder settles) instead of the last two of the "
            "reordered spread. On the failing test's column the last two arrivals "
            "are NOT the two largest representatives, so that final interior entry "
            "lands at the wrong value and can sit out of order — the downstream "
            "binning step then either rejects the non-monotone boundary sequence "
            "or assigns the wrong bin to values near it, and the expected "
            "assignment is not produced. Does NOT resolve on the sub-domain where "
            "the last two arrivals differ from the two largest."
        ),
        "rationale": (
            "REJECT from C1, fact S5, on a NARROWER sub-domain than "
            "reject-unordered-pairing: this rival is correct on every spread whose "
            "last two arrivals happen to be its two largest, so it agrees with gold "
            "over strictly more of the domain and needs a point that separates it "
            "specifically. Refuted at `centers = [9, 1, 3]`, `lo = 0`, `hi = 10`: "
            "the raw last two are (1,3) averaging 2, while C1's last "
            "ascending-adjacent pair is (3,9) averaging 6. Note this point is "
            "chosen deliberately — the mirror spread `[1, 9, 3]` does NOT "
            "discriminate (its raw last pair (9,3) averages 6, coinciding with "
            "gold), and a witness placed there was measured to FAIL against the "
            "rival. If it verified => SPEC-TOO-WEAK: C1 would not pin the last "
            "interior entry to the last ASCENDING-adjacent pair."
        ),
        "witness": _witness([9, 1, 3], 0, 10),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-mispaired-interior",
        "kind": "uniqueness",
        "expect": "reject",
        # Reorder correctly, then average the WRONG pairs: every interior entry
        # pairs the SMALLEST representative with each later one, instead of
        # pairing each ADJACENT pair. Gets the count right (S1) and stays inside
        # the endpoint range, but the pairing is non-adjacent. Refuted on an
        # already-ascending spread, so its rejection cannot be confused with the
        # reorder defect.
        "module": _impl_reproved(
            "    let ys := asc centers\n"
            "    return lo :: (ys.tail.map (fun x => (ys.head! + x) / 2) ++ [hi])"),
        "refinement": (
            "its faithful counterpart averages NON-ADJACENT representatives for "
            "the interior entries — pairing the smallest with each of the others "
            "rather than each neighbouring pair, the shape of an off-by-one slice "
            "in the pairing step. The interior boundaries land at the wrong "
            "values, so values sitting near a true boundary are assigned to the "
            "wrong bin and the failing test's expected assignment is not produced. "
            "Does NOT resolve whenever the two smallest representatives differ."
        ),
        "rationale": (
            "REJECT from C1, fact S5's ADJACENCY half specifically: `mids` averages "
            "each NEIGHBOURING pair, so pairing the smallest representative with a "
            "non-neighbour contradicts C1 whenever the two smallest differ. "
            "Refuted at `centers = [1, 3, 9]`, `lo = 0`, `hi = 10` — an ALREADY-"
            "ASCENDING spread, so the reorder is a no-op there and the rejection is "
            "attributable to the pairing alone, not to the reorder defect the other "
            "rivals attack. The rival's second interior entry is (1+9)/2 = 5; C1 "
            "forces (3+9)/2 = 6. If it verified => SPEC-TOO-WEAK: C1 would pin only "
            "that SOME pairs are averaged, not WHICH."
        ),
        "witness": _witness([1, 3, 9], 0, 10),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-flat-interior",
        "kind": "uniqueness",
        "expect": "reject",
        # The nagini reject-flat-monotone probe, ported: collapse every interior
        # entry to the LOWER endpoint. Trivially non-decreasing and correctly
        # bracketed and counted (S1/S2/S3/S4 all hold), but the interior values
        # are not the adjacent-pair averages. This is the case that proves the
        # VALUE content of C1 is load-bearing beyond mere monotonicity.
        "module": _impl_reproved(
            "    return lo :: ((mids (asc centers)).map (fun _ => lo) ++ [hi])"),
        "refinement": (
            "its faithful counterpart emits a degenerate boundary sequence whose "
            "interior entries all equal the lower endpoint. It is trivially "
            "non-decreasing, so the downstream binning step does NOT reject it — "
            "and that is exactly what makes it dangerous: it fails silently. Every "
            "value of the failing test's column then falls into a single extreme "
            "bin, so the produced assignment is constant and does not match the "
            "expected per-value assignment. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1, fact S5 — and this is the KEY case for spec strength, "
            "ported from the nagini reject-flat-monotone: the rival satisfies "
            "S1 (count), S2/S3 (both endpoints) and S4 (trivially non-decreasing) "
            "while getting every interior VALUE wrong. A spec that pinned only the "
            "monotonicity of the boundary sequence — the property the problem "
            "statement names — would WRONGLY ADMIT it. That C1 rejects it is the "
            "evidence that the exact-value content is load-bearing and not merely "
            "implied by monotonicity. Refuted at `centers = [1, 3, 5]`, `lo = 0`, "
            "`hi = 6`: the rival's interior is [0, 0], C1 forces [2, 4]. If it "
            "verified => SPEC-TOO-WEAK (monotone-only)."
        ),
        "witness": _witness([1, 3, 5], 0, 6),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-representatives-not-averages",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the reordered REPRESENTATIVES themselves (minus the last, to keep
        # the count right) as the interior entries, instead of their adjacent-pair
        # averages. Ascending, correctly bracketed, correctly counted — but the
        # values are the inputs, not the pairwise averages. Refuted at endpoints
        # that no other witness uses, and with a NEGATIVE lower endpoint, so the
        # `lo` binder is varied off 0.
        "module": _impl_reproved(
            "    return lo :: ((asc centers).dropLast ++ [hi])"),
        "refinement": (
            "its faithful counterpart brackets the reordered representatives "
            "themselves as the boundaries, skipping the pairwise-averaging step "
            "entirely (the shape of a patch that reordered but then dropped the "
            "averaging). The sequence is ascending, so the downstream binning step "
            "does not reject it, but every interior boundary sits ON a "
            "representative instead of BETWEEN two of them; values between "
            "representatives are then assigned to the neighbouring bin and the "
            "failing test's expected assignment is not produced. Does NOT resolve "
            "whenever any two adjacent representatives differ."
        ),
        "rationale": (
            "REJECT from C1, fact S5's AVERAGING half: the interior entries must be "
            "the pairwise AVERAGES, not the representatives themselves. The rival "
            "keeps S1 (count), S2/S3 (endpoints) and S4 (ascending) and still "
            "contradicts C1 wherever two adjacent representatives differ. Refuted "
            "at `centers = [1, 3, 5]`, `lo = -2`, `hi = 7`: the rival's interior is "
            "[1, 3], C1 forces [2, 4]. This witness is the only one placing `lo` "
            "off zero (and NEGATIVE) and `hi` at 7, so it varies both endpoint "
            "binders away from every other witness's values. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness([1, 3, 5], -2, 7),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-descending-orientation",
        "kind": "uniqueness",
        "expect": "reject",
        # Reorder and average correctly, then report the whole sequence REVERSED:
        # upper endpoint first, interior entries descending, lower endpoint last.
        # Attacks S2, S3 and S4 at once. Refuted at endpoints (1, 9) and a spread
        # no other witness uses.
        "module": _impl_reproved(
            "    return hi :: ((mids (asc centers)).reverse ++ [lo])"),
        "refinement": (
            "its faithful counterpart reorders the representatives DESCENDING and "
            "brackets with the endpoints swapped, so the boundary sequence is "
            "monotonically decreasing. The downstream binning step is fed the "
            "ascending-expected boundary slice; a decreasing sequence makes it "
            "assign every value to the mirrored bin, so the produced assignment is "
            "the reverse of the expected one and the failing test's expected "
            "per-value assignment is never produced. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 on THREE independent facts at once — S2 (the first "
            "entry must be the LOWER endpoint; here it is the upper), S3 (the last "
            "must be the UPPER; here it is the lower) and S4 (the interior order; "
            "here reversed). A verify would mean the spec does not pin the "
            "ORIENTATION of the boundary sequence. Refuted at `centers = "
            "[2, 6, 4]`, `lo = 1`, `hi = 9`: the rival returns [9, 5, 3, 1], C1 "
            "forces [1, 3, 5, 9]. A distinct spread AND distinct endpoints from "
            "every other witness. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness([2, 6, 4], 1, 9),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-endpoints-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of the above: reorder and average correctly AND keep the
        # interior order correct (S1/S4/S5 all hold), but swap only the two
        # bracketing endpoints. Isolates S2/S3 from S4, which the descending rival
        # violates jointly. Refuted at endpoints (2, 8).
        "module": _impl_reproved(
            "    return hi :: (mids (asc centers) ++ [lo])"),
        "refinement": (
            "its faithful counterpart brackets the correctly-ordered interior "
            "entries with the endpoints SWAPPED — the upper endpoint prepended and "
            "the lower appended. The sequence then starts above and ends below its "
            "own interior, so it is neither increasing nor decreasing; the "
            "downstream binning step rejects a non-monotone boundary sequence "
            "outright and the failing test's expected assignment is never reached. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1, facts S2 and S3 in ISOLATION: this rival keeps the "
            "count (S1), the interior order (S4) and every interior value (S5) "
            "correct and swaps ONLY the two bracketing endpoints — so unlike "
            "reject-descending-orientation, which violates S2/S3/S4 jointly, it "
            "attributes the rejection to the endpoint placement alone. Refuted at "
            "`centers = [1, 3, 5]`, `lo = 2`, `hi = 8`: the rival returns "
            "[8, 2, 4, 2], C1 forces [2, 2, 4, 8]. Endpoints (2, 8) are used by no "
            "other witness, so both endpoint binders take a third distinct pair of "
            "values here. If it verified => SPEC-TOO-WEAK: the endpoints would be "
            "unpinned."
        ),
        "witness": _witness([1, 3, 5], 2, 8),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-short-sequence",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the LAST interior entry, so the sequence is one short. Attacks S1
        # (and, at the tail, which value sits at each index). Cheap supporting
        # near-miss with a real refinement, ported from the nagini
        # reject-short-length-four.
        "module": _impl_reproved(
            "    return lo :: ((mids (asc centers)).dropLast ++ [hi])"),
        "refinement": (
            "its faithful counterpart emits one interior boundary fewer than there "
            "are adjacent pairs (an off-by-one in the pairing slice). The boundary "
            "sequence is then one entry short, so the configured number of bins is "
            "not realised and the produced per-value assignment does not match the "
            "failing test's expected assignment. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1, fact S1 (the LENGTH): the boundary sequence must carry "
            "one entry per adjacent pair plus the two endpoints, so dropping an "
            "interior entry contradicts C1 whenever there are at least two adjacent "
            "pairs. Refuted at `centers = [1, 3, 9]`, `lo = 0`, `hi = 10`: the rival "
            "returns the 3-entry [0, 2, 10], C1 forces the 4-entry [0, 2, 6, 10]. "
            "Ports the nagini reject-short-length-four. If it verified => "
            "SPEC-TOO-WEAK: the boundary COUNT would be unconstrained, which is the "
            "one fact no value clause implies."
        ),
        "witness": _witness([1, 3, 9], 0, 10),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "reject-long-sequence",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The UPPER side of the length fact. reject-short-sequence
        # attacks S1 from below only, so before this case a spec reading "at MOST
        # one entry per adjacent pair" (a `<=` where C1 has `=`) would have been
        # invisible to the whole battery: every other rival keeps the count exact.
        # Duplicate the FIRST interior entry so the sequence is one entry too
        # long, with every entry that gold emits still present, in order, at its
        # own index — so the divergence is the count alone and not a value or a
        # placement.
        "module": _impl_reproved(
            "    let ms := mids (asc centers)\n"
            "    return lo :: (ms ++ ms.take 1 ++ [hi])"),
        "refinement": (
            "its faithful counterpart emits one interior boundary MORE than there "
            "are adjacent pairs, re-emitting the first one before closing (the "
            "shape of a pairing slice whose upper bound is off by one the other "
            "way). The boundary sequence is then one entry long, so the "
            "configured number of bins is not realised — and because the extra "
            "entry repeats the SMALLEST interior boundary after the largest, the "
            "sequence is also no longer non-decreasing, so the downstream binning "
            "step rejects it outright. Either way the failing test's expected "
            "per-value assignment is not produced. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1, fact S1 (the LENGTH) from ABOVE — the direction "
            "reject-short-sequence does not test. C1 is an EQUALITY to "
            "`boundaries centers lo hi`, so the count is pinned in both "
            "directions; a spec that bounded the interior only from above (one "
            "entry per adjacent pair AT MOST) would admit the short rival's "
            "mirror, and no other rival in this battery emits a sequence that is "
            "too LONG. Refuted at `centers = [5, 1, 3]`, `lo = 0`, `hi = 8` — a "
            "spread and an endpoint pair no other witness uses: the rival returns "
            "the 5-entry [0, 2, 4, 2, 8], C1 forces the 4-entry [0, 2, 4, 8]. "
            "Every entry C1 demands is present, in order, at its own index, so "
            "the rejection is attributable to the COUNT alone. If it verified => "
            "SPEC-TOO-WEAK: the boundary count would be bounded on one side only."
        ),
        "witness": _witness([5, 1, 3], 0, 8),
        "witness_reference": _LOOPFREE,
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The sibling battery has 10 SPEC cases (2 soundness, 1 admissibility, 7
# uniqueness) plus 2 AXIOM_TESTS. It contracts ONE function over six by-value
# scalars — four representatives passed individually plus two endpoints — with an
# explicit `Requires` bounding each representative into the endpoint range, and
# an `@ContractOnly` reorder oracle (`order4`) consumed by its proof. This bundle
# widens the carrier to a LIST of representatives, has NO `require` at all, and
# models the reorder DEEPLY (`asc = mergeSort (· ≤ ·)`, an A-reference validated
# == the real routine by G-AX, per mapping.md §3.1) rather than consuming an
# oracle. So the value surface carries across essentially intact, while the
# axiom lane and the fixed-arity `Requires` become G-AX's and the empty
# pre-condition region's business respectively.
#
#   nagini case                      -> here                                 status
#   ------------------------------------------------------------------------------
#   pos-reverse-midpoint-order       -> pos-control-loop-rename              PORTED
#   pos-append-build                 -> pos-control-staged-concat            PORTED
#   (no sibling)                     -> pos-control-direct                   ADDED
#   admiss-f2p-shaped-input          -> admiss-unordered-spread              RE-AIMED
#   reject-prepatch-no-sort          -> reject-unordered-pairing             PORTED
#   reject-partial-last-midpoint     -> reject-partial-last-pair             PORTED
#   reject-mispaired-interior        -> reject-mispaired-interior            PORTED
#   reject-flat-monotone             -> reject-flat-interior                 PORTED
#   reject-descending-order          -> reject-descending-orientation        PORTED
#   reject-endpoint-swap             -> reject-endpoints-swapped             PORTED
#   reject-short-length-four         -> reject-short-sequence                PORTED
#   (no sibling)                     -> reject-representatives-not-averages  ADDED
#   (no sibling)                     -> reject-long-sequence            ADDED (AUDIT)
#   frame / permission-mutation      -> (none)                               VACUOUS
#   divergence / non-termination     -> (none)                               SPEC-CLOSED
#   AXIOM_TESTS (x2)                 -> (none)                               DROPPED
#
# 13 velvet SPEC cases: 3 soundness, 1 admissibility, 9 uniqueness. Every one of
# the sibling's 7 uniqueness rivals ported (none dropped), plus two added; both
# positives ported plus one added; the admissibility case re-aimed. NOTHING was
# omitted for being hard to prove.
#
# PORTED (positives). The sibling's two positives reshape a straight-line body:
#   pos-reverse-midpoint-order computes the three midpoint assignments in reverse
#   order, and pos-append-build assembles the sequence element-by-element instead
#   of as one literal. On this carrier the per-pair assignments ARE the loop body,
#   so the faithful counterparts are pos-control-loop-rename (gold's backward fold
#   with every local renamed — the same computation with a different surface, its
#   elided tactic body retuned to the new counter name) and
#   pos-control-staged-concat (stage through named locals and assemble with a
#   different concatenation split). Both keep the `method`/`ensures` header
#   byte-identical and verify EXIT 0.
# ADDED (pos-control-direct): the loop-free cheapest honest impl. It carries the
#   sibling's directive-2 honest-echo ARGUMENT: because C1's post-image is
#   grounded in the arguments (no opaque oracle), the cheapest impl meeting it IS
#   doing the work, so there is no "wrong echo" rival to write. Verifies EXIT 0
#   with its (elided) tactic body retuned to `loom_solve; simp [boundaries]` —
#   with no loop there is no backward-fold goal left.
# RE-AIMED (admiss-f2p-shaped-input -> admiss-unordered-spread): the sibling's
#   case establishes that its `Requires` (each representative inside the endpoint
#   range) admits an F2P-shaped input and that the reorder oracle is callable on
#   it. This bundle has an EMPTY `pre-conditions` region and no consumed oracle,
#   so both halves of that probe are vacuous as stated. Re-aimed at the risk that
#   IS live on a total domain: that the domain is silently restricted to inputs on
#   which the reorder is a no-op. The in-region `assert` is a live decidable claim
#   about an UNORDERED spread (well-formed and correctly-counted output, the
#   reorder genuinely changes the answer there, and arrival order is immaterial);
#   a false conjunct leaves an unsolved goal. Verifies EXIT 0.
# PORTED (all 7 rivals), each with its nagini refinement argument carried over and
#   re-grounded in the real failing-test behaviour, and each now backed by a
#   machine-checked witness:
#     reject-prepatch-no-sort      -> reject-unordered-pairing (THE bug and the
#         G-DIFF discriminator: pair the arrival order, no reorder).
#     reject-partial-last-midpoint -> reject-partial-last-pair (reorder, but take
#         the last interior entry from a stale slice of the arrival order).
#     reject-mispaired-interior    -> reject-mispaired-interior (reorder, then
#         average NON-ADJACENT pairs).
#     reject-flat-monotone         -> reject-flat-interior (the key spec-strength
#         case: trivially monotone, correctly bracketed and counted, every
#         interior VALUE wrong — a monotone-only spec would admit it).
#     reject-descending-order      -> reject-descending-orientation.
#     reject-endpoint-swap         -> reject-endpoints-swapped.
#     reject-short-length-four     -> reject-short-sequence.
# ADDED (reject-representatives-not-averages): bracket the reordered
#   representatives THEMSELVES as the boundaries, skipping the averaging. It
#   isolates the AVERAGING half of the value fact from the ADJACENCY half that
#   reject-mispaired-interior attacks, and it is the witness that drives the `lo`
#   binder NEGATIVE (see the binder table below).
# ADDED BY THE AUDIT (reject-long-sequence): the UPPER side of the length fact.
#   S1 was attacked from BELOW only — reject-short-sequence drops an interior
#   entry — while every other rival keeps the count exact, so a spec bounding the
#   interior from above alone (`≤` where C1 has `=`) was invisible to the whole
#   battery. This rival re-emits the first interior entry before closing, so the
#   sequence is one entry too LONG with every entry C1 demands still present, in
#   order, at its own index: the divergence is the count alone. Refuted at
#   `([5,1,3], 0, 8)`, a spread and endpoint pair no other witness uses, which
#   also lifts the point count from seven to eight.
#
# VACUOUS (frame / permission-mutation): the nagini sibling records
#   `has_readonly_input == False` in its own defended-surface docstring — all six
#   of its inputs are by-value scalars and there is no fractional-permission token
#   anywhere in its contract — so there was no frame rival to port even there.
#   Vacuous here for the stronger backend reason as well: Velvet is referentially
#   transparent, all three inputs are immutable values, this bundle declares no
#   `mut` parameter, and there is no heap, aliasing or permission system. No
#   read-only input to overwrite, no substitute probe fabricated.
#
# DIVERGENCE / NON-TERMINATION, CLOSED BY THE SEMANTICS. The earlier text in this
#   slot recorded the class as a KNOWN SPEC HOLE and is RETRACTED IN FULL: its
#   table claimed that a `decreasing` clause which is PRESENT but whose measure
#   does not shrink verifies at exit 0, and that does not reproduce. What does
#   hold was re-measured on this bundle with a BARE `loom_solve` tail, so that
#   nothing is scored rejected merely for `No goals to be solved`:
#
#     rival                                              outcome
#     ---------------------------------------------------------------------------
#     diverging loop with NO `decreasing` clause,        REJECTED (exit 1)
#       gold's return value                                `Decreasing annotations
#                                                           are required in total
#                                                           correctness semantics`
#     diverging loop WITH `decreasing q`, on a counter    REJECTED (exit 1), and on
#       the body does not shrink (`q := q`)                the MEASURE's own goal:
#                                                          `case «decreasing_1: q»
#                                                           ... q < q`
#     terminating `return []` (control)                  REJECTED (exit 1),
#                                                          `unsolved goals`
#     terminating `return [lo, hi]` (control)            REJECTED (exit 1), ditto
#
#   The second row is the one that matters, and it is the row the retracted table
#   had backwards. `total` does not merely require the clause to be PRESENT; the
#   measure is a real obligation. Loom's total-correctness loop generator
#   (`forWithInvariantLoop` under `TotalCorrectness.DemonicChoice.WPGen`) takes a
#   `measure : β -> Nat` and emits, per iteration, the side condition
#   `with_name_prefix `decreasing (measure b' < measure b)`, so a constant or
#   growing measure arrives as an unprovable `q < q`-shaped goal carrying the
#   clause's own name. The twin that accepts `measure : β -> Option ℕ` and
#   DISCARDS it belongs to `PartialCorrectness`, and nothing in this bundle
#   selects that scope: the file sets
#   `set_option loom.semantics.termination "total"`, and in Loom that option is
#   itself what opens the `TotalCorrectness` scope, so option and `open` cannot
#   disagree. Under `total` a postcondition is claimed of ALL runs, not only
#   terminating ones, so there is no vacuous satisfaction left to exploit: a
#   diverging impl does not verify here. The two terminating controls are what
#   show the `ensures` is independently live and does reject `[]` and `[lo, hi]`,
#   rather than the loop shape being rejected for some unrelated reason.
#
#   No reject case is shipped for the class all the same, and that is a limit of
#   the WITNESS contract rather than a spec hole or a dropped case. A reject case
#   must exhibit a witness that ELABORATES against the rival and FAILS against
#   gold. A diverging rival's module does not compile at all: the descent
#   obligation fails at the `method` itself, upstream of any appended tester, so
#   even a trivial witness comes back `witness-unproven`, and the case would be
#   scored MALFORMED instead of rejecting. The class is therefore carried as
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#   documentation and defended by the semantics, not by a case. The nagini
#   sibling ships no `diverge-*` / `nonterm-*` / `weak-diverge` case either, so
#   there is nothing to port.
#
# DROPPED (AXIOM_TESTS): the sibling's two probes (soundness + caller-domain
#   containment for its `order4` reorder oracle) are G-AX's job — here the reorder
#   is not a consumed axiom at all but the deep model `asc`, validated == the real
#   routine by axiom_check.py over 11 boundary + 20 000 fuzz arrays (mapping.md
#   §3.1, meta.json `deep_model_references`) — and this gate ignores AXIOM_TESTS
#   regardless.
#
# CLAUSE / BINDER / POINT COVERAGE (the part the gate does not check).
#   The single obligation (`prove_correct computeBoundaries`) is DEFENDED by four
#   `expect="verify"` cases (three soundness reshapes + admissibility) and
#   ATTACKED by nine rivals. C1 is the only clause; its five independent
#   structural facts are each attacked, and no fact rests on a single rival except
#   where noted:
#     S1 length      — reject-short-sequence (from BELOW: one entry too few),
#                      reject-long-sequence (from ABOVE: one too many, added by
#                      the audit — before it, S1 was tested in one direction
#                      only and a one-sided count bound would have gone unseen).
#     S2 head = lo   — reject-endpoints-swapped (isolated),
#                      reject-descending-orientation (jointly with S3/S4).
#     S3 tail = hi   — reject-endpoints-swapped (isolated),
#                      reject-descending-orientation.
#     S4 order       — reject-descending-orientation.
#     S5 values      — reject-unordered-pairing (raw vs ascending order),
#                      reject-partial-last-pair (one entry from the raw order),
#                      reject-mispaired-interior (non-adjacent pairing),
#                      reject-representatives-not-averages (no averaging),
#                      reject-flat-interior (interior collapsed to an endpoint).
#   All THREE input binders are varied across the reject witnesses:
#     centers at [3,1,5], [9,1,3], [1,3,9], [1,3,5], [2,6,4], [5,1,3] — six
#              spreads, two of them ALREADY ASCENDING (so a rejection there is
#              attributable to the pairing/assembly, not to the reorder) and four
#              not. [5,1,3] and [3,1,5] are DISTINCT points, not two spellings of
#              one: they are different arrival orders of the same multiset, and
#              arrival order is exactly what the reorder rivals turn on;
#     lo      at 0, -2, 1, 2                                  — including negative;
#     hi      at 6, 10, 7, 9, 8.
#   The nine witnesses sit at EIGHT distinct input points (pts=8):
#     ([3,1,5], 0, 6)   reject-unordered-pairing
#     ([9,1,3], 0, 10)  reject-partial-last-pair
#     ([1,3,9], 0, 10)  reject-mispaired-interior, reject-short-sequence
#     ([1,3,5], 0, 6)   reject-flat-interior
#     ([1,3,5], -2, 7)  reject-representatives-not-averages
#     ([2,6,4], 1, 9)   reject-descending-orientation
#     ([1,3,5], 2, 8)   reject-endpoints-swapped
#     ([5,1,3], 0, 8)   reject-long-sequence          (added by the audit)
#   (eight distinct (centers, lo, hi) triples; the two rivals SHARING
#   ([1,3,9], 0, 10) — mispaired-interior and short-sequence — genuinely fail
#   there for their own separate reasons, a wrong pairing and a missing entry, and
#   neither is a near-miss of the other.) No binder is held at one value by every
#   witness: `lo` moves off 0 and negative, `hi` takes five values, and `centers`
#   spans both already-ascending and unordered spreads. In particular the
#   near-miss pair is separated deliberately: reject-partial-last-pair agrees with
#   gold over strictly more of the domain than reject-unordered-pairing, so it is
#   refuted at its OWN point `([9,1,3], 0, 10)` rather than sharing the prepatch
#   rival's — and the mirror spread `[1,9,3]` was measured NOT to discriminate it
#   (there the raw last pair coincides with gold), which is recorded in its
#   rationale so the manifest never claims a sub-domain it has not demonstrated.
#
# WITNESS MECHANICS (all nine SEEN to discriminate, two real builds each; the
#   audit re-ran all of them plus the forgery pair — see the docstring).
#   The tester+`decide` route is dead: the `Rat` postcondition's Decidable
#   instance does not reduce (stuck at `instDecidableEqRat` — the spec_guide `Rat`
#   trap). Every witness instead extracts the executable program and refutes C1
#   directly against the transparent `boundaries`. Each rival is written LOOP-FREE
#   so its `…Exec` reduces, while gold's backward-`while` `…Exec` is well-founded
#   recursion the kernel leaves stuck on the `forIn`/`invariantGadget` term — so
#   the same statement elaborates against the rival and FAILS on gold. Two
#   measured tactic facts shape the closer: bare `decide` does not compute `Rat`
#   arithmetic (`decide +kernel` does), and `decide +kernel` still cannot reduce
#   `asc` (`mergeSort` is well-founded), so each witness first discharges the
#   reorder with `rw [show asc <literal> = <ascending literal> by simp +decide
#   [asc, List.mergeSort]]`. No witness binds a hypothesis (every input is a
#   concrete literal), so the gate's consistency probe is a no-op and there are no
#   assumptions that could be jointly unsatisfiable. No banned token
#   (sorry/admit/native_decide/axiom/opaque). Verified out-of-band with
#   scripts/lean_verify.sh, TWO builds per rival, all eighteen logs inspected
#   (plus the audit's forgery pair per rival — see the docstring):
#   every witness ELABORATES against its rival (exit 0) and FAILS against the
#   `_LOOPFREE` reference with `Tactic `decide` proved that the proposition … is
#   false` — a DECIDED refutation. Grepped: NO log on either side contains the
#   `did not reduce to `isTrue` or `isFalse`` text, so no half of any case rests
#   on a stuck reduction. The reference itself builds EXIT 0, as the gate
#   independently re-checks (it must share the frozen spec AND verify).
#
# TIMING NOTE. `decide +kernel` appears only inside the per-midpoint `show` side
#   goals (never as a closer — see WITNESS MECHANICS fact 4), which keeps the
#   kernel work small: measured per-case gate times are 20.9s–53.5s, so the
#   battery is comfortable at the 300s default cap. (An earlier cut of these
#   witnesses used `decide +kernel` as the CLOSER and did overrun 300s; that
#   shape was replaced because it also made a refuted claim textually
#   indistinguishable from a stuck one, not merely because it was slow.)
AXIOM_TESTS = []
