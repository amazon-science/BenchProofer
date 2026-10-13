"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14983 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct buildReprValues`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a subject known to satisfy the spec). Here that second subject is NOT the
frozen solution — ``decide`` cannot reduce the frozen ``while`` loop, so its
build fails without deciding anything — but the declared ``witness_reference``,
against which the failure is a real refutation. See the CARRIER NOTE.

DEFENDED SURFACE (one contracted method):

  buildReprValues (keys : List String) (attrs fallback : List (String × Int))
      (hasFallback : Bool) return (out : List (Option Int))
    ensures out = resolveAll attrs fallback hasFallback keys

The method resolves, in order, the value displayed for each named parameter in
``keys``. The value of ONE key is the pure, TRANSPARENT ``def resolveOne``:

    resolveOne attrs fallback hasFallback key
      = match attrs.lookup key with
        | some v => some v                                   -- primary wins
        | none   => if hasFallback then fallback.lookup key  -- secondary store
                    else none                                -- no store: absent

and the whole sweep is the front-recursive fold ``resolveAll`` (``resolveAll …
(k :: ks) = resolveOne … k :: resolveAll … ks``). Both are total ``def``s over
the method's own inputs — the ``axioms`` region is EMPTY, there is NO opaque
answer-key term — so pinning ``out = resolveAll attrs fallback hasFallback keys``
is GROUNDED, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. There is exactly ONE ``ensures`` clause (C1),
and it is the whole pin: a function of all four binders that fixes, at every
list position, WHICH source each key's value comes from and the ORDER the values
appear in. Every uniqueness rival therefore targets C1; each mishandles a
different sub-behaviour of ``resolveOne`` (or the outer order) so the rejections
are attributable to distinct facts C1 forces.

C1 folds FOUR independently-attackable behaviours, mirroring the nagini
sibling's load-bearing postcondition clauses:
  * PRIMARY-WINS — a key present in the primary attribute table takes that value,
    NOT the secondary store's (the ``value is None`` guard). [nagini P2]
  * THE FIX / SECONDARY-STORE — a key ABSENT from the primary table but present
    in the secondary store (when the store is present) takes the store's value,
    NOT ``none``. This is the discriminating behaviour the F2P exercises. [P3/P4]
  * NO-STORE-ABSENT — a key absent from the primary table on an object with NO
    secondary store stays ``none`` (absent). [nagini P5] This one breaks TWO
    ways and both are probed: fabricate some other value on that branch
    (rival-no-store-sentinel), or ignore the store-existence guard and read the
    secondary store anyway (rival-read-store-without-store).
  * ORDER / OUTER STRUCTURE — one resolved value per key, in key order.

FOUR INPUT BINDERS: ``keys`` (the ordered parameter names), ``attrs`` (the
primary table), ``fallback`` (the secondary store), ``hasFallback`` (whether the
store is present). All four are load-bearing and the reject witnesses drive them
to FIVE distinct input points (pts=5): ``hasFallback`` ranges over {true,false},
``keys`` over length {1,2}, ``attrs`` over {empty, populated}, ``fallback`` over
{empty, populated} — and the two ``hasFallback`` values are each combined with
BOTH a populated and an empty ``fallback``, so ``hasFallback`` is discriminated
independently of the store's contents rather than confounded with them. No
binder is held at one value across the reject set.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY THE SECOND SUBJECT IS NOT GOLD.
A witness reaches the post-image through Velvet's tester machinery
(``buildReprValuesTester keys attrs fallback hasFallback = false`` says the
extracted program's result violates the postcondition at that concrete input) and
closes by ``decide``, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict. This carrier is FULLY
TRANSPARENT — ``resolveOne`` / ``resolveAll`` are computable ``def``s over
``List``/``Option``/``Int``/``Bool``, and the ``axioms`` region is empty — so
``decide`` reduces the extracted program to ``isTrue``/``isFalse`` for every
concrete literal tuple, PROVIDED the program itself reduces. Each reject rival is
written as a LOOP-FREE closed form (a ``keys.map`` / ``.reverse`` over the pure
helpers) so its extracted ``…Exec`` reduces under the kernel and the rival build
elaborates.

The FROZEN program, however, is the backward ``while`` loop, which under
``loom.semantics.choice "demonic"`` elaborates through ``Classical.choice``: the
kernel cannot unfold it, so ``decide`` on the FROZEN tester is STUCK for every
claim regardless of truth. That is NOT a refutation, and it must not be read as
one — a stuck build fails identically for a TRUE claim about gold, so its exit
code carries no information (see swebench_unified/gates/pbt.py _STUCK_REDUCTION,
which screens exactly this and would record ``witness-undecided``). Measured for
all five reject cases here, gold side:

    error: Tactic `decide` failed for proposition
      buildReprValuesTester … = false
    because its `Decidable` instance … did not reduce to `isTrue` or `isFalse`.

So each reject case names an explicit ``witness_reference``: the LOOP-FREE
verifying impl ``return resolveAll attrs fallback hasFallback keys``
(``pos-control-direct-fold``'s module, the battery's own positive). It shares the
frozen spec and VERIFIES, so it cannot violate its own spec, and it DOES reduce
— so the second half of the discrimination check is a genuine semantic
refutation, which the gate re-derives and the build log states in those words:

    error: Tactic `decide` proved that the proposition
      buildReprValuesTester … = false
    is false

i.e. the correct impl SATISFIES the postcondition at precisely the input where
the rival violates it. Naming the reference explicitly rather than leaning on the
gate's implicit positives fallback is what makes the attestation legible from the
artifact: ``meta.json`` then records which impl earned each rejection instead of
"gold cannot decide". No witness binds a hypothesis (every input is a concrete
literal that decides C1), so no consistency probe is needed; no banned token
(sorry/admit/native_decide/axiom/opaque). Every witness was re-checked with
``scripts/lean_verify.sh`` on THREE subjects: ELABORATES against its rival
(exit 0), STUCK against gold (exit 1, no verdict — hence the reference), and
REFUTED against the reference (exit 1, "decide proved … is false").

ADVERSARIAL READ of the nagini classes on this carrier (full accounting in the
footer):
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (return the grounded fold directly, no loop; or
    keep the loop but stage each key's value in a typed local) must verify, else
    the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method declares NO ``require`` clause (the pre-conditions
    region is empty), so the nagini probe's fractional-permission half has no
    counterpart. Its IN-DOMAIN half DOES: on a total carrier the analogue of
    PRECOND-TOO-STRONG is the obligation being unsatisfiable or degenerate at an
    F2P-shaped input. REPAIRED BY THE AUDIT — the case previously shipped the
    frozen file byte-for-byte, which re-runs the bundle's own build and could
    detect nothing. It now discharges C1's post-image at three concrete points
    (an F2P-shaped store-only key, the same input with the store absent, and the
    key also in the primary table) as a LIVE in-region ``assert``, ahead of the
    frozen loop, so a degenerate or unsatisfiable post-image fails the case.
    Liveness machine-checked in both directions; see the case comment.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    carries TWO MANDATORY frame-mutation rivals (write / delete an entry of the
    read-only secondary store held at ``Acc(dict_pred,1/2)``), rejected for
    INSUFFICIENT PERMISSION. Lean/Velvet are referentially transparent: ``attrs``
    and ``fallback`` are immutable ``List (String × Int)`` values declared
    read-only (none ``mut``), there is no heap, no aliasing, and no permission
    system. There is no read-only input to overwrite. The class has no carrier
    analogue; NOT ported (a fabricated substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION — CLOSED BY THE SPEC, UNWITNESSABLE BY
    CONSTRUCTION. Corrected by the audit: the previous text here claimed this
    bundle runs under ``"partial"`` semantics and that a diverging impl therefore
    VERIFIES, making the class a known spec hole. That is FALSE for this bundle —
    ``Solution.lean:4`` reads ``set_option loom.semantics.termination "total"``,
    and the audit measured the diverging rival REJECTED, four different ways:

        ``decreasing (0 : Nat)``                  exit 1, ``⊢ 0 < 0``
        ``decreasing (1 : Nat)``                  exit 1, ``⊢ 1 < 1``
        ``decreasing spin``, ``spin := spin + 1`` exit 1, ``⊢ spin + 1 < spin``
        no ``decreasing`` clause                  exit 1, refused at the ``while``

    Each rejection lands on the measure's own strict-decrease side-condition, so
    on THIS toolchain the ``total`` obligation really is checked and the
    residual hole an earlier internal finding claimed corpus-wide ("the obligation
    accepts any measure expression") does NOT reproduce here.
    So the class is neither a hole nor vacuous — the spec closes it.
    It is nonetheless NOT shippable as a reject case, for a WITNESS reason rather
    than a spec reason: a diverging rival necessarily carries a loop, and the
    loop blocks kernel reduction of the rival's OWN tester, which is the half a
    witness must SUCCEED on. Three shapes measured against the rival, all exit 1:
    ``decide`` and ``decide +kernel`` on the tester (``did not reduce to
    `isTrue` or `isFalse` ``), ``simp`` on the tester (goal left on an
    un-normalised ``NonDetT.run``), and an ``Exec``-conditioned witness
    (``Dependent elimination failed … forIn Lean.Loop.mk``). A trivial
    ``1 + 1 = 2`` appended to the same rival builds (exit 0), so the file is
    sound and it is specifically the claim's reduction that is blocked. Shipping
    it would record ``witness-unproven`` and force MALFORMED-TESTS on a battery
    that is otherwise honest. Same disposition sibling cells reached under
    ``total`` (see django__django-16901). No witness fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. C1 pins ``out`` to ``resolveAll …``, a
    transparent fold over the method's own arguments; there is no answer-key term
    a wrong impl could echo. The cheapest correct impl materializes the fold
    honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — the whole reject lane, all against C1: the prepatch
    (secondary store ignored), the primary-wins violation, the no-store sentinel,
    and the reversed order.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14983"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Reject rivals and the loop-free positive swap on
# ---- this block, so every edit is confined to the impl region and same_spec
# ---- holds by construction.
_IMPL = """    -- impl-start
    let mut result : List (Option Int) := []
    let mut i := keys.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ keys.length
      invariant result = resolveAll attrs fallback hasFallback (keys.drop i)
      done_with i = 0
      decreasing i
    do
      let k := keys[i - 1]!
      result := resolveOne attrs fallback hasFallback k :: result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the single loop-body line that prepends each resolved value, wholly inside
# ---- the impl region and unique. The loop-preserving positive reshapes only
# ---- this (stage the value in a typed local first), leaving the loop, the
# ---- invariants and the frozen proof intact.
_LOOP_PREPEND = "      result := resolveOne attrs fallback hasFallback k :: result\n"
assert _BASE.count(_LOOP_PREPEND) == 1, "loop-prepend anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival or the loop-free positive that reshapes the impl into a single
# ---- expression retunes it to the flat `loom_solve` (there is no loop invariant
# ---- to peel), without touching the spec or dropping the `prove_correct
# ---- buildReprValues` obligation.
_PROOF_GOLD = """prove_correct buildReprValues by
  loom_solve
  rw [resolveAll_drop_step keys attrs fallback hasFallback i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- the flat proof body: with a single-expression impl there is no loop
# ---- invariant to peel, so `loom_solve` alone discharges C1 (for a correct
# ---- reshape) or leaves it unsolved (for the reject rivals, which is the point —
# ---- the rejection is attributed to the spec by the witness, not by a stale
# ---- tactic script tuned to a loop that no longer exists).
_PROOF_FLAT = "prove_correct buildReprValues by\n  loom_solve"

# ---- the first declaration of the impl region, wholly inside it and unique: the
# ---- anchor the admissibility case prefixes its `assert` onto, so the whole
# ---- frozen loop (and the frozen proof's loop steps) survive underneath.
_PREPEND_DECL = "    let mut result : List (Option Int) := []\n"
assert _BASE.count(_PREPEND_DECL) == 1, "impl-first-decl anchor drift"

# ---- the admissibility probe: a LIVE in-region assert discharging C1's
# ---- post-image at three concrete points. Row 1 is the F2P shape (a key held
# ---- only in the secondary store, store present); rows 2-3 vary the guard and
# ---- the primary table so the demanded values DIFFER across neighbouring
# ---- points, which is what makes the satisfiability claim non-degenerate.
# ---- Generic key/value literals (no repository identifiers).
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `assert\n"
    "      (resolveAll [] [(\"p\", 2)] true [\"p\"] = [some 2] ∧\n"
    "       resolveAll [] [(\"p\", 2)] false [\"p\"] = [none] ∧\n"
    "       resolveAll [(\"p\", 5)] [(\"p\", 2)] true [\"p\"] = [some 5]))\n")

# ---- the admissibility proof: the frozen loop steps, plus a `decide` arm for
# ---- the new `assert_1` goal. `try` per goal rather than a bare sequence
# ---- because `loom_solve` now leaves TWO goals (the assert and the loop step)
# ---- and the frozen `rw` names loop-local binders that do not exist in the
# ---- assert's goal (measured: `Unknown identifier 'i'` when sequenced flatly).
_PROOF_ADMISS = (
    "prove_correct buildReprValues by\n"
    "  loom_solve\n"
    "  all_goals (try decide)\n"
    "  all_goals (try (rw [resolveAll_drop_step keys attrs fallback hasFallback i"
    " (by omega) (by omega)]\n"
    "                  simp_all))")


def _expr_rival(return_body):
    """A full Solution.lean whose impl is a single straight-line expression and
    whose proof is the flat `loom_solve`. Edits ONLY the impl and proof regions,
    so `same_spec` holds and the obligation statement is unchanged."""
    return _swap(_swap(_BASE, _IMPL,
                       "    -- impl-start\n" + return_body + "    -- impl-end"),
                 _PROOF_GOLD, _PROOF_FLAT)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `buildReprValuesTester keys attrs fallback hasFallback = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped.
# ---- Every argument is a concrete literal, so `decide` reduces the (loop-free)
# ---- extracted rival program without getting stuck; against gold's `while` loop
# ---- it stays stuck at the `Decidable` instance and FAILS (the discriminator).
def _witness(keys_lit, attrs_lit, fallback_lit, has_fallback):
    hf = "true" if has_fallback else "false"
    return (
        "\n"
        "extract_program_for buildReprValues\n"
        "prove_precondition_decidable_for buildReprValues\n"
        "prove_postcondition_decidable_for buildReprValues\n"
        "derive_tester_for buildReprValues\n\n"
        f"example : buildReprValuesTester {keys_lit} {attrs_lit} {fallback_lit} "
        f"{hf} = false := by\n  decide\n")


# ---- the second subject every reject witness is refuted against. NOT gold: the
# ---- frozen `while` loop elaborates through `Classical.choice` under
# ---- `loom.semantics.choice "demonic"`, so `decide` on the frozen tester is
# ---- STUCK for every claim — true or false — and its exit code discriminates
# ---- nothing (measured: "did not reduce to `isTrue` or `isFalse`" on all five).
# ---- This reference is the loop-free `return resolveAll …` impl, which SHARES
# ---- the frozen spec and VERIFIES (it is `pos-control-direct-fold`'s module, so
# ---- the battery independently asserts and the gate independently re-checks
# ---- that it verifies). An impl the verifier accepts cannot violate its own
# ---- spec, so a genuine witness must FAIL against it — and here it fails by
# ---- REFUTATION ("decide proved … is false"), a real verdict rather than a
# ---- stuck reduction. See the CARRIER NOTE.
_WITNESS_REF = _expr_rival(
    "    return (resolveAll attrs fallback hasFallback keys)\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Neither introduces a helper lemma, an axiom, or an
    # assumption token; both keep the `prove_correct buildReprValues` obligation
    # byte-identical.
    # =====================================================================
    {
        "id": "pos-control-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded fold directly, no loop
        # at all — maximally structurally different from the gold backward scan.
        # `out` IS `resolveAll attrs fallback hasFallback keys`, so C1 holds
        # trivially; the reproof is a bare `loom_solve` (no loop invariant to
        # peel). Because the post-image is GROUNDED in the arguments (not an opaque
        # answer key), this doubles as proof the spec is not echo-vulnerable: any
        # wrong per-key resolution fails `out = resolveAll …`. (Verified during
        # authoring: exit 0.)
        "module": _WITNESS_REF,
        "rationale": (
            "the post-image `resolveAll attrs fallback hasFallback keys` is "
            "GROUNDED in the inputs (a total front-recursive fold, no opaque answer "
            "key), so returning it directly (no loop) is the honest cheapest CORRECT "
            "impl; C1 is literally that equality, so it MUST verify and the flat "
            "`loom_solve` closes the definitional equality. Ports the nagini "
            "pos-control-grounded-oracle-cheapest: the cheapest impl satisfying the "
            "grounded pin, showing the spec is not echo-vulnerable. Else "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-staged-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold but bind each key's resolved
        # value to a typed local `v` before prepending it. Same value flow
        # (`v = resolveOne …`), different control shape; the frozen proof still
        # closes unchanged (the loop invariant and step lemma are untouched).
        # (Verified during authoring: exit 0.)
        "module": _swap(
            _BASE, _LOOP_PREPEND,
            "      let v := resolveOne attrs fallback hasFallback k\n"
            "      result := v :: result\n"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind each key's resolved "
            "value to a typed local before prepending it) must verify; the value "
            "flow is unchanged (`v = resolveOne …`) so C1 still discharges and the "
            "frozen loop proof closes as-is. Ports the nagini "
            "pos-control-reorder-early-return (a structurally-different but "
            "behaviourally identical correct impl of the modeled resolution). If it "
            "fails => SPEC-TOO-STRONG (over-fit to the inline-prepend code form)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares NO `require` clause (the pre-conditions
    # region is empty), so the nagini admiss-empty-store-in-domain (which
    # established the read-only fractional-permission precondition on an
    # F2P-shaped input) has no LITERAL counterpart: there is no precondition to
    # satisfy and no permission surface.
    #
    # REPAIRED BY THE AUDIT. The previous form of this case was `module = _BASE`
    # — the frozen file byte-for-byte. That verifies for exactly the reason the
    # frozen bundle verifies, i.e. it re-runs a build the gate already performs
    # elsewhere and adds no obligation of its own. It could not have detected
    # PRECOND-TOO-STRONG in any form, so the admissibility lane was present in
    # name and vacuous in substance.
    #
    # The analogue of PRECOND-TOO-STRONG on a TOTAL carrier is the obligation
    # being UNSATISFIABLE (or degenerate) at exactly an F2P-shaped input. So this
    # case now DISCHARGES C1's post-image at three concrete points, as a live
    # in-region `assert`, before closing the frozen obligation:
    #   * a key present ONLY in the secondary store, store present    -> [some 2]
    #   * the SAME key and store contents, store ABSENT               -> [none]
    #   * the same key also present in the primary table              -> [some 5]
    # Row 1 is the F2P shape (the discriminating input); rows 2-3 make the
    # demand non-degenerate — the post-image must ACCEPT one value here and a
    # DIFFERENT value there, so a spec satisfiable only by a constant answer
    # fails. The impl is otherwise the frozen loop verbatim, so the frozen C1
    # obligation still discharges alongside.
    #
    # The assert is LIVE, machine-checked in both directions by the audit:
    #   * this case, as written                                exit 0
    #   * one row's claim negated (`= [none]` on row 1)         exit 1,
    #       `unsolved goals  case «assert_1: …»
    #        ⊢ resolveAll [] [("p", 2)] true ["p"] = [none]`
    #     i.e. the assert generates its own goal, on its own concrete claim
    #   * this case with the FROZEN proof script verbatim       exit 1,
    #     same `assert_1` unsolved goal — so the extra `decide` arm below is
    #     discharging a real obligation and not decoration.
    # Else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE at the F2P-shaped input.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-point",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen loop verbatim, prefixed by the live `assert`; the proof gains a
        # `decide` arm for the new goal and keeps the frozen loop steps.
        "module": _swap(
            _swap(_BASE, _PREPEND_DECL, _ADMISS_ASSERT + _PREPEND_DECL),
            _PROOF_GOLD, _PROOF_ADMISS),
        "rationale": (
            "the obligation must be SATISFIABLE and non-degenerate at an "
            "F2P-shaped input, which on a total carrier with no `require` is what "
            "PRECOND-TOO-STRONG becomes. The in-region `assert` discharges C1's "
            "post-image `resolveAll` at three concrete points: a key held ONLY in "
            "the secondary store with the store present (`[some 2]` — the "
            "discriminating shape the failing test exercises), the SAME key and "
            "store contents with the store ABSENT (`[none]`), and that key also "
            "present in the primary table (`[some 5]`). Rows 2-3 make the demand "
            "non-degenerate: the post-image must accept DIFFERENT values at "
            "neighbouring points, so a spec satisfiable only by a constant fails. "
            "The frozen loop is kept verbatim so C1 still discharges. Re-aimed "
            "from the nagini admiss-empty-store-in-domain, whose "
            "fractional-permission half has no counterpart on this "
            "referentially-transparent carrier, but whose IN-DOMAIN half does. "
            "Verified live in both directions (negating a row leaves the "
            "`assert_1` goal unsolved). Else PRECOND-TOO-STRONG."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Each rival is a LOOP-FREE closed form
    # (single expression over the pure helpers) so its extracted tester `decide`s
    # (see the CARRIER NOTE); the frozen spec is untouched.
    # =====================================================================
    {
        "id": "rival-ignore-fallback-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG ITSELF (pre-patch): resolve each key from the PRIMARY attribute
        # table ONLY, never consulting the secondary store. Correct on every key
        # that is a direct attribute or has no store; WRONG on the discriminating
        # case (key absent from the primary table but present in the store):
        # returns `none` where C1 requires the store's value.
        "module": _expr_rival("    return (keys.map (fun k => attrs.lookup k))\n"),
        "refinement": (
            "this is the pre-change resolution: each parameter's value is read from "
            "the object's own attribute table only, with no consultation of the "
            "secondary keyword store. The failing scenario constructs an object that "
            "stows a parameter in its secondary store rather than as a direct "
            "attribute, so the primary lookup yields nothing and the parameter is "
            "reported ABSENT; the demanded textual representation lists that "
            "parameter with its stored value, so the representation MISMATCHES and "
            "it would NOT resolve. This is exactly the defect the fix corrects. "
            "(Also subsumes the nagini weak-store-branch-returns-none, which on "
            "this carrier is observationally identical: entering the store path but "
            "reporting `none` is the same as never reading the store.)"),
        "rationale": (
            "REJECT from C1 (`out = resolveAll …`): `resolveOne` resolves a key "
            "absent from the primary table, when the store is present, to "
            "`fallback.lookup key`, but this rival returns `attrs.lookup key` "
            "(=`none` there). Refuted at `keys=[\"a\"]`, `attrs=[]`, "
            "`fallback=[(\"a\",7)]`, `hasFallback=true` — the store-only key. If it "
            "verified => SPEC-TOO-WEAK (admits the very bug — the secondary-store "
            "fallback unpinned)."),
        "witness": _witness('["a"]', "[]", '[("a", 7)]', True),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "rival-store-overrides-primary",
        "kind": "uniqueness",
        "expect": "reject",
        # PRIMARY-WINS violated: consult the secondary store UNCONDITIONALLY when
        # it is present, so a key that IS a direct attribute is overwritten by the
        # store's value. Correct whenever the primary table lacks the key, or the
        # store lacks it, or the two agree; WRONG when the key is in both and the
        # values differ (the spec says the PRIMARY value wins).
        "module": _expr_rival(
            "    return (keys.map (fun k =>\n"
            "      if hasFallback then\n"
            "        match fallback.lookup k with\n"
            "        | some v => some v\n"
            "        | none => attrs.lookup k\n"
            "      else attrs.lookup k))\n"),
        "refinement": (
            "this consults the secondary store first and only falls back to the "
            "primary attribute table, dropping the guard that keeps the primary "
            "value authoritative. A parameter that is a direct attribute would then "
            "be reported with a stale value from the construction-time keyword "
            "store instead of its current attribute value; the representation the "
            "tests pin reflects the direct attribute, so a differing stored value "
            "would print the wrong parameter value and it would NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = resolveAll …`): `resolveOne` returns the primary "
            "value `some v` whenever `attrs.lookup key = some v`, regardless of the "
            "store; this rival returns the store's value there. Refuted at "
            "`keys=[\"a\"]`, `attrs=[(\"a\",1)]`, `fallback=[(\"a\",2)]`, "
            "`hasFallback=true` — a key present in BOTH with differing values (a "
            "point no other rival probes: populated `attrs`), so the witness varies "
            "the `attrs` binder. If it verified => SPEC-TOO-WEAK (the primary-wins "
            "precedence unpinned)."),
        "witness": _witness('["a"]', '[("a", 1)]', '[("a", 2)]', True),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "rival-no-store-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        # NO-STORE-ABSENT violated: for a key absent from the primary table on an
        # object with NO secondary store, fabricate a sentinel `some 0` instead of
        # `none`. Correct on every object that HAS a store, and on every present
        # key; WRONG on the no-store absent case (the spec requires `none`).
        "module": _expr_rival(
            "    return (keys.map (fun k =>\n"
            "      match attrs.lookup k with\n"
            "      | some v => some v\n"
            "      | none => if hasFallback then fallback.lookup k else some 0))\n"),
        "refinement": (
            "this fabricates a value for a parameter that is genuinely absent on an "
            "object with no secondary store — where a missing parameter must be "
            "reported as absent. A plain object (no secondary store) whose parameter "
            "is unset would then have its representation show a spurious value; the "
            "representation tests over such objects pin the absent rendering, so a "
            "fabricated value would MISMATCH and it would NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = resolveAll …`): `resolveOne` returns `none` when "
            "`attrs.lookup key = none` and `hasFallback = false`, but this rival "
            "returns `some 0`. Refuted at `keys=[\"a\"]`, `attrs=[]`, "
            "`fallback=[]`, `hasFallback=false` — the no-store absent point, where "
            "the rival FABRICATES a value the spec requires to be absent. If it "
            "verified => SPEC-TOO-WEAK (the no-store-stays-absent behaviour "
            "unpinned)."),
        "witness": _witness('["a"]', "[]", "[]", False),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "rival-read-store-without-store",
        "kind": "uniqueness",
        "expect": "reject",
        # NO-STORE-ABSENT violated the OTHER way: resolve correctly from the
        # primary table, and on a miss read the secondary store UNCONDITIONALLY,
        # dropping the store-existence guard entirely. Correct on every key the
        # primary table has, and on every object that HAS a store; WRONG when the
        # object has NO store yet the store list happens to be non-empty — the
        # spec says a key unresolved by the primary table on a storeless object
        # is `none`, whatever `fallback` holds.
        #
        # Added by the audit: the existing sentinel rival breaks the no-store
        # branch by fabricating a CONSTANT, which a spec pinning only "some
        # value from one of the two tables" would also reject. This rival breaks
        # it by reading the RIGHT table at the WRONG time, so it isolates
        # `hasFallback` as a GUARD rather than as a source selector — and it is
        # refuted at `hasFallback=false` with a POPULATED `fallback`, the
        # (hasFallback, fallback) combination no other witness reaches (the
        # sentinel holds `fallback` empty there, so on its point this rival and
        # gold AGREE).
        "module": _expr_rival(
            "    return (keys.map (fun k =>\n"
            "      match attrs.lookup k with\n"
            "      | some v => some v\n"
            "      | none => fallback.lookup k))\n"),
        "refinement": (
            "this reads the secondary keyword store without first checking that "
            "the object exposes one, so the store-existence guard is gone. On a "
            "plain object that carries no such store the lookup is not merely "
            "redundant — any residual store contents would be reported as though "
            "they were the object's own parameters, and a parameter that must "
            "render as absent would print a value instead. The representation "
            "tests over storeless objects pin the absent rendering, so the "
            "representation MISMATCHES and it would NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = resolveAll …`): `resolveOne` consults "
            "`fallback` only under `hasFallback`, returning `none` when "
            "`attrs.lookup key = none` and `hasFallback = false`; this rival "
            "returns `fallback.lookup key` there. Refuted at `keys=[\"a\"]`, "
            "`attrs=[]`, `fallback=[(\"a\",7)]`, `hasFallback=false` — the ONLY "
            "witness combining `hasFallback=false` with a POPULATED `fallback`, "
            "which is what makes `hasFallback` load-bearing as a GUARD "
            "independently of the store's contents. If it verified => "
            "SPEC-TOO-WEAK (the store-existence guard unpinned — the spec would "
            "then be indifferent to whether the store may be consulted at all)."),
        "witness": _witness('["a"]', "[]", '[("a", 7)]', False),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "rival-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # OUTER STRUCTURE violated: resolve each key correctly but emit the values
        # in REVERSED key order. Every per-key value is right; the OUTER ordering
        # is wrong. Correct on any single-key input; WRONG on any input with two
        # distinct values.
        "module": _expr_rival(
            "    return ((keys.map (fun k => resolveOne attrs fallback hasFallback k)).reverse)\n"),
        "refinement": (
            "this resolves every parameter's value correctly but lists them in the "
            "reverse of the requested order. The parameter names are supplied in a "
            "fixed (sorted) order and the demanded textual representation lists them "
            "in exactly that order; a reversed sequence prints the parameters in the "
            "wrong order, so the representation MISMATCHES and it would NOT resolve. "
            "A genuine outer-structure break — correct on every per-key value."),
        "rationale": (
            "REJECT from C1 (`out = resolveAll …`): `resolveAll` pins the i-th "
            "output to `keys[i]`'s resolution IN ORDER, but this rival reverses the "
            "list. Refuted at `keys=[\"a\",\"b\"]`, `attrs=[(\"a\",1),(\"b\",2)]`, "
            "`fallback=[]`, `hasFallback=false` — the ONLY witness with a two-key "
            "input (so it varies the `keys` length binder and the output ordering); "
            "at ANY single-key input this rival agrees with gold (`[x].reverse = "
            "[x]`), so no other case's witness could refute it and none of its "
            "own is shared. If it verified => SPEC-TOO-WEAK (the output order "
            "unpinned)."),
        "witness": _witness('["a", "b"]', '[("a", 1), ("b", 2)]', "[]", False),
        "witness_reference": _WITNESS_REF,
    },

]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling ships 12 SPEC cases (2 soundness positives, 1 admissibility,
# 7 uniqueness rivals — 2 mandatory frame-mutation + 1 divergence + 4 value) plus
# 1 AXIOM_TESTS entry. Both bundles model the SAME purely-functional core — the
# per-parameter value resolution of the textual-representation builder — but this
# bundle models the WHOLE-sequence sweep (`buildReprValues` over `keys`) with a single grounded
# `ensures out = resolveAll …` and four binders, where nagini contracts the
# single-key `reported_param_value` with five decomposed postcondition clauses
# (P1–P5) plus a termination clause (P6). The clauses map onto the sub-behaviours
# C1 folds; the frame and termination classes are carrier-specific.
#
#   nagini case                        -> here                          disposition
#   -------------------------------------------------------------------------------
#   pos-control-reorder-early-return   -> pos-control-staged-local       RE-SHAPED
#   pos-control-grounded-oracle-cheapest -> pos-control-direct-fold      RE-EXPRESSED
#   admiss-empty-store-in-domain       -> admiss-f2p-shaped-point        RE-AIMED
#   frame-mutate-store-insert          -> (none)                         VACUOUS
#   frame-mutate-store-del             -> (none)                         VACUOUS
#   weak-diverge-before-return         -> (none)                         SPEC-CLOSED,
#                                                                       UNWITNESSABLE
#   weak-prepatch-no-fallback          -> rival-ignore-fallback-prepatch PORTED (P1/P3/P4)
#   weak-store-branch-returns-none     -> (merged into prepatch)         COLLAPSES (carrier)
#   weak-store-overrides-attr          -> rival-store-overrides-primary  PORTED (P2)
#   weak-no-store-returns-sentinel     -> rival-no-store-sentinel        PORTED (P5)
#   (no sibling)                       -> rival-reversed-order           ADDED (outer order)
#   (no sibling)                       -> rival-read-store-without-store ADDED (P5 guard)
#   AXIOM_TESTS (1)                    -> (none)                         DROPPED (G-AX lane)
#
# 8 velvet SPEC cases: 2 soundness, 1 admissibility (repaired by the audit from
# a no-op frozen-file case into a live F2P-shaped satisfiability probe), 5
# uniqueness. Every nagini
# uniqueness rival that attacks a modeled clause is ported (or collapses onto a
# ported one); the one added rival covers the outer ordering that nagini's
# single-key contract cannot express.
#
# RE-SHAPED (pos-control-reorder-early-return -> pos-control-staged-local): the
#   nagini positive is an early-return case dispatch (attr-present first). Velvet
#   bans early return inside a loop, and the per-key resolution here is the pure
#   `resolveOne` (not an inline if/elif chain in the impl), so there is no branch
#   order in the impl region to reorder. The ANALOGUE structurally-different-but-
#   correct reshape is a let-staged prepend inside the frozen loop; it carries the
#   same argument (a faithful correct impl must verify, else SPEC-TOO-STRONG) and
#   keeps the frozen proof intact.
# RE-EXPRESSED (pos-control-grounded-oracle-cheapest -> pos-control-direct-fold):
#   the nagini honest control returns the transparent `resolved_value(...)`
#   directly. On this carrier the grounded oracle IS `resolveAll` and C1 already
#   IS `out = resolveAll …`, so the cheapest honest impl is `return resolveAll …`
#   (loop-free) — the same argument (the grounded pin is satisfiable only by the
#   real per-key work; no wrong echo verifies) expressed as a correct impl.
# RE-AIMED (admiss-empty-store-in-domain -> admiss-f2p-shaped-point): the nagini
#   case established the read-only fractional-permission precondition on an
#   F2P-shaped input. This method has NO `require` and no heap permission, so the
#   PERMISSION half is vacuous — but the IN-DOMAIN half is not, and it is what the
#   lane exists to test. REPAIRED BY THE AUDIT: the case previously shipped
#   `module = _BASE`, the frozen file byte-for-byte, which verifies for exactly
#   the reason the bundle verifies and adds no obligation — the lane was present
#   in name and vacuous in substance, unable to detect PRECOND-TOO-STRONG in any
#   form. It now prefixes the frozen loop with a LIVE in-region `assert`
#   discharging C1's post-image at three concrete points: the F2P shape (a key
#   held only in the secondary store, store present -> `[some 2]`), the same
#   input with the store ABSENT (-> `[none]`), and that key also present in the
#   primary table (-> `[some 5]`). The last two make the demand non-degenerate:
#   neighbouring points must accept DIFFERENT values, so a post-image satisfiable
#   only by a constant fails. Liveness measured in both directions — negating one
#   row leaves `unsolved goals case «assert_1: …»` (exit 1), and the case with
#   the FROZEN proof script verbatim also fails on that same `assert_1` goal, so
#   the added `decide` arm discharges a real obligation rather than decorating.
# PORTED (3 value rivals): weak-prepatch-no-fallback -> rival-ignore-fallback-
#   prepatch (the literal pre-patch: primary table only, refuted at the store-only
#   key — the F2P discriminator). weak-store-overrides-attr ->
#   rival-store-overrides-primary (drop the primary-wins guard, refuted where a
#   key is in both tables with differing values). weak-no-store-returns-sentinel
#   -> rival-no-store-sentinel (fabricate a value on the no-store absent branch,
#   refuted at hasFallback=false). Each carries its nagini refinement argument,
#   now backed by a machine-checked witness.
# COLLAPSES (weak-store-branch-returns-none): the nagini rival enters the store
#   path but reports `none` instead of `store[key]`. On this carrier that is
#   observationally IDENTICAL to weak-prepatch-no-fallback: resolving a key to
#   `attrs.lookup k` and then, on `none`, to `(if hasFallback then none else none)`
#   is just `attrs.lookup k`. There is no impl a rival could write that separates
#   the two on the returned value, so no distinct witnessable divergence exists;
#   subsumed by rival-ignore-fallback-prepatch (noted in its refinement), NOT
#   dropped for difficulty. DEMONSTRATED, not asserted — the audit built the
#   store-branch-returns-none impl as its own variant (it is rejected, exit 1,
#   with the same C1 `unsolved goals`) and PROVED the two impls extensionally
#   equal on this carrier (exit 0):
#       example (attrs fallback : List (String × Int)) (hf : Bool)
#           (keys : List String) :
#           (keys.map (fun k => match attrs.lookup k with
#                               | some v => some v
#                               | none => if hf then none else none))
#             = (keys.map (fun k => attrs.lookup k)) := by
#         apply List.map_congr_left; intro k _; cases h : attrs.lookup k <;> simp [h]
#   Equal impls cannot be discriminated by any witness, so shipping it as a
#   separate case would add a second rejection attributable to the same fact.
# ADDED (rival-reversed-order): nagini contracts a SINGLE key
#   (`reported_param_value`), so it has no notion of output ORDER to attack. This
#   bundle contracts the whole ordered sweep (`resolveAll` over `keys`), so the
#   outer structure — one value per key, in key order — is part of the defended
#   surface; a rival that resolves every value correctly but reverses the order is
#   a real, witnessable C1 divergence, and completes coverage of the outer
#   structure. A real divergence with a machine-checked witness, not fabricated
#   wrongness.
# FRAME-MUTATION (frame-mutate-store-insert / frame-mutate-store-del): VACUOUS.
#   The nagini rivals write / delete an entry of the read-only secondary store
#   held at `Acc(dict_pred,1/2)` and are rejected for insufficient permission.
#   Velvet is referentially transparent: `attrs` and `fallback` are immutable
#   values, none `mut`, no heap, no aliasing, no permission system. There is no
#   read-only input to overwrite. No substitute fabricated. DEMONSTRATED by the
#   audit rather than asserted, in both directions:
#     * writing the input binder is not even a well-formed program here — an impl
#       whose body is `fallback := []` is refused at ELABORATION:
#         error: `fallback` cannot be mutated, only variables declared using
#         `let mut` can be mutated
#       That is a TRANSLATION-level refusal, not a spec verdict, so shipping it
#       as a reject case would attribute a rejection to the spec that the spec
#       had no part in — precisely the vacuous-rejection defect the witness
#       requirement exists to catch. It also admits no witness: there is no
#       program whose tester could be evaluated at any input.
#     * mutating a LOCAL COPY (`let mut fb := fallback; fb := []`) IS expressible
#       and IS rejected (exit 1) — but on a pure VALUE mismatch
#       (`⊢ resolveAll attrs [] hasFallback keys = resolveAll attrs fallback
#       hasFallback keys`), i.e. it is just a wrong impl that discards the store,
#       already covered by rival-ignore-fallback-prepatch. The mutation is
#       invisible to the caller, which is exactly the sense in which the nagini
#       class has no analogue: there is no observable frame to violate.
# CLOSED BY THE SPEC, UNWITNESSABLE (weak-diverge-before-return) — CORRECTED BY
#   THE AUDIT. The previous text recorded this as a KNOWN SPEC HOLE on the ground
#   that "this bundle runs under `loom.semantics.termination \"partial\"`, under
#   which a non-terminating impl satisfies C1 VACUOUSLY and VERIFIES". That claim
#   was false about this bundle: `Solution.lean:4` reads `"total"`. The audit
#   built the diverging rival and it is REJECTED (exit 1) under every measure
#   tried — `decreasing (0 : Nat)` -> `⊢ 0 < 0`, `decreasing (1 : Nat)` ->
#   `⊢ 1 < 1`, `decreasing spin` with `spin := spin + 1` -> `⊢ spin + 1 < spin`,
#   and no `decreasing` clause at all -> refused at the `while`. Every rejection
#   is on the measure's own strict-decrease side-condition, so the `total`
#   obligation is genuinely enforced on this toolchain and the corpus-wide
#   residual hole an earlier internal finding claimed (any measure expression
#   accepted) does NOT reproduce on this cell. So: not a hole, and not
#   vacuous — the SPEC closes the class.
#   It still cannot ship as a reject case, for a WITNESS reason. A diverging
#   rival must carry a loop, and that loop blocks kernel reduction of the RIVAL's
#   own tester — the half a witness must SUCCEED on. Measured against the rival,
#   all exit 1: `decide` and `decide +kernel` on `buildReprValuesTester …`
#   (`did not reduce to `isTrue` or `isFalse``), `simp` on the tester (goal left
#   on an un-normalised `NonDetT.run (buildReprValues …)`), and an
#   `Exec`-conditioned witness (`Dependent elimination failed … forIn
#   Lean.Loop.mk`). Control: a trivial `example : 1 + 1 = 2 := by decide`
#   appended to that same rival builds at exit 0, so the variant file is sound
#   and it is specifically the claim's reduction that is blocked — the rival is
#   unwitnessable by construction, not by authoring difficulty. Shipping it would
#   record `witness-unproven` and force MALFORMED-TESTS. This is the disposition
#   sibling cells reached under `total` (django__django-16901). No witness
#   fabricated, and nothing here needs the frozen file changed.
# DROPPED (AXIOM_TESTS): the nagini axiom-lane entry probes the A-reference deep
#   model (`resolved_value` == the real per-key resolution) against
#   the real callee. Here the resolution is modeled deeply and transparently by
#   `resolveOne`/`resolveAll` (mapping.md §3: no consumed axiom), validated by
#   axiom_check.py (G-AX); the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole `ensures` clause C1 (`out =
#   resolveAll attrs fallback hasFallback keys`) folds four sub-behaviours, each
#   attacked by some rival: THE FIX / secondary-store (rival-ignore-fallback-
#   prepatch), PRIMARY-WINS (rival-store-overrides-primary), NO-STORE-ABSENT
#   (rival-no-store-sentinel for the fabricated-value break, rival-read-store-
#   without-store for the dropped-guard break), and OUTER ORDER
#   (rival-reversed-order). The four input binders are varied across FIVE distinct
#   points (pts=5):
#     * rival-ignore-fallback-prepatch  ["a"]      [] [("a",7)]         true
#     * rival-store-overrides-primary   ["a"]      [("a",1)] [("a",2)]  true
#     * rival-no-store-sentinel         ["a"]      [] []                false
#     * rival-read-store-without-store  ["a"]      [] [("a",7)]         false
#     * rival-reversed-order            ["a","b"]  [("a",1),("b",2)] [] false
#   So `hasFallback` ranges over {true,false}, `keys` over length {1,2}, `attrs`
#   over {empty, populated}, `fallback` over {empty, populated}. Crucially the
#   variation is MEANINGFUL rather than two spellings of one point: rows 1 and 4
#   are the SAME (keys, attrs, fallback) triple differing ONLY in `hasFallback`,
#   and gold's verdict differs across them (`[some 7]` vs `[none]`), so
#   `hasFallback` is demonstrated load-bearing as a GUARD in its own right rather
#   than confounded with whether the store happens to be populated. No binder is
#   held at one value across the reject set. C1 is defended by both positive
#   controls and the admissibility case (all discharge on gold).
#
# WITNESS MECHANICS: the carrier's PURE layer is fully transparent
#   (`resolveOne`/`resolveAll` are computable `def`s; the `axioms` region is
#   empty), but the frozen PROGRAM is not: its `while` loop elaborates through
#   `Classical.choice` under `loom.semantics.choice "demonic"`. Each witness
#   reaches the post-image via `buildReprValuesTester <args> = false` and closes by
#   `decide`, checked in a file whose `prove_correct` block is stripped. Every
#   argument is a concrete literal, so the extracted LOOP-FREE rival program
#   reduces and the tester is `false` for the rival (postcondition violated at that
#   input) — but against GOLD `decide` is STUCK for every claim regardless of
#   truth, so gold cannot serve as the discriminating second subject. Each case
#   therefore names an explicit `witness_reference`: the verifying loop-free
#   `return resolveAll …` impl, against which the witness fails by genuine
#   REFUTATION. No witness binds a hypothesis, so no consistency probe is needed.
#   All five re-checked with scripts/lean_verify.sh on THREE subjects each:
#     rival     exit 0 — elaborates;
#     gold      exit 1 — "did not reduce to `isTrue` or `isFalse`" (STUCK: no
#               verdict at all, which is why the reference exists; reading this
#               exit code as a refutation is exactly the hollow-SOUND defect);
#     reference exit 1 — "Tactic `decide` proved that the proposition … is false"
#               (a real semantic refutation: the correct impl SATISFIES C1 at
#               precisely the input where the rival violates it).
#
# AUDIT PROBES (attacks D and E; run out-of-band, not shipped as cases — a
#   rejected wrong impl and a verifying correct impl are evidence, not tests):
#     D (SPEC-TOO-WEAK probes; every one REJECTED, so no spec hole was found):
#       `return []`                                     exit 1 (C1 unsolved)
#       `… ++ [none]`            (one value too many)   exit 1
#       `.take (keys.length - 1)` (one value too few)   exit 1
#       drop the `hasFallback` guard                    exit 1 -> PROMOTED to
#         rival-read-store-without-store, because it was the one unattacked
#         sub-behaviour rather than merely one more rejection.
#     E (SPEC-TOO-STRONG probes; every one VERIFIES, so the spec is not over-fit
#       to the frozen impl's shape — none of these shapes is the frozen loop):
#       `keys.map (resolveOne …)` closed by list induction    exit 0
#       `keys.map` with `resolveOne` INLINED (the pure helper
#         never mentioned in the impl at all)                 exit 0
#       `keys.reverse.map (…) |>.reverse`                     exit 0
#       `keys.foldr (fun k acc => resolveOne … k :: acc) []`  exit 0  [audit]
#   AUDIT RE-DERIVATION (independent adversarial audit; every build below was
#   re-run rather than taken from this text). All 5 reject witnesses rebuilt on
#   all three subjects, reproducing the rival-0 / gold-STUCK / reference-REFUTED
#   pattern above exactly. The FORGERY test (flip `= false` to `= true`, i.e.
#   claim the subject is CORRECT at that input) was run on every reject case and
#   on every subject, which is what establishes the reference's exit code carries
#   information about the CLAIM rather than about the carrier:
#     forged claim vs REFERENCE  exit 0 — elaborates, because gold's answer at
#       that input IS what the forgery asserts. Real claim exit 1, forged claim
#       exit 0, same file otherwise: the reference DISCRIMINATES.
#     forged claim vs GOLD       exit 1 with the BYTE-IDENTICAL stuck-reduction
#       error as the real claim — which is the positive demonstration that gold
#       could not have served as the second subject here, and that this battery's
#       `witness_reference` is load-bearing rather than decorative.
#     forged claim vs RIVAL      exit 1 ("decide proved … is false") — the rival
#       really does compute the wrong value there, not merely fail to reduce.
#   Five further wrong impls (attack D) were built beyond the shipped set, all
#   REJECTED, so no spec hole was found: read the store but coerce its miss to a
#   fabricated value (`some ((fallback.lookup k).getD 0)`), resolve against
#   `attrs.reverse`/`fallback.reverse` (last-match instead of first-match lookup),
#   `keys.eraseDups` (drop duplicate keys), invert the guard
#   (`resolveOne … (!hasFallback)`), and drop the first resolved value (`.tail`).
#   The COLLAPSES claim above was re-derived too: the store-branch-returns-none
#   impl builds and is rejected (exit 1) and the extensional-equality `example`
#   quoted there elaborates (exit 0), so the two impls really are indiscriminable
#   on this carrier. Both frame-mutation claims re-derived as quoted: the
#   input-binder write is refused at elaboration ("`fallback` cannot be mutated")
#   and the local-copy version is rejected on a pure value goal
#   (`⊢ resolveAll attrs [] hasFallback keys = resolveAll attrs fallback
#   hasFallback keys`). The five witness INPUT POINTS were confirmed MEANINGFUL
#   rather than two spellings of one point by deciding gold's own answer at each
#   (exit 0): `[some 7]`, `[none]`, `[none]`, `[some 1]`, `[some 1, some 2]` —
#   in particular rows 1 and 4 share (keys, attrs, fallback) and differ only in
#   `hasFallback`, and gold's verdict differs across them, so the guard is
#   demonstrated load-bearing on its own.
#   The E results are what keep the positive lane honest: C1 admits impls that are
#   neither the frozen loop nor a bare echo of `resolveAll`, so
#   pos-control-direct-fold's near-definitional discharge is not the only way to
#   satisfy the spec.
AXIOM_TESTS = []
