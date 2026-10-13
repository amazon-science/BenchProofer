# properties.py — G-PBT spec-lane manifest for django__django-15916 (lean).
# NOT a Lean file: a record of adversarial cases the gate executes against the
# frozen Solution.lean and stamps a verdict onto. Each SPEC_TESTS case is a
# complete Solution.lean variant that shares the frozen spec byte-for-byte
# (only the impl region and, where a positive reproves, the proof BODY differ),
# so markers.same_spec holds by construction and every rejection is
# attributable to the postcondition rather than to a tampered spec.
#
# Ported from the nagini sibling's battery (benchmark-verified/
# django__django-15916/nagini/properties.py), which is the design document: the
# adversarial ARGUMENT of each case is carried over, the mechanics are
# re-expressed against this backend's carrier. See 'PORT MAP' below for the
# case-by-case correspondence and the omissions.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean; one obligation)
# ---------------------------------------------------------------------------
#   resolveModelFormCallback
#       (metaCallback      : Option Callback)
#       (directHasCallback : Bool)
#       (directCallback    : Option Callback)
#       (baseMetaCallback  : Option (Option Callback))
#     -> Option Callback
#
#   theorem correct_resolveModelFormCallback : the obligation is UNCONDITIONAL
#   (a bare `∀` over all four inputs; no hypothesis, hence no precondition).
#
#   Load-bearing postcondition — a single top-level clause:
#       result = metaCallback
#
#   That one equation carries two independent kinds of content, and a rival can
#   attack either:
#     (a) the SELECTION: the answer is the callback carried by the class's own
#         options block;
#     (b) the FRAME (SPEC_GUIDE §0.5): the answer is independent of every other
#         candidate carrier — of whether a direct class attribute is present
#         (`directHasCallback`), of that attribute's value (`directCallback`),
#         and of any base form's options block (`baseMetaCallback`). In
#         particular, when the own options block declares no callback the answer
#         is "no callback" even where another carrier would supply one.
#
#   The postcondition is GROUNDED in an input (it is a projection of
#   `metaCallback`), not pinned to an opaque answer-key oracle, so there is no
#   ungrounded-oracle-echo rival to build here. `Callback := Nat` and
#   `Option`/`Bool` are all fully decidable, so every witness below states the
#   refutation at CONCRETE literal inputs and closes by `decide` — no
#   conditioning on an opaque carrier is needed (that technique is not reached
#   for in this bundle, so no witness binds anything and none can be
#   `witness-inconsistent`).
#
# ---------------------------------------------------------------------------
# PORT MAP — nagini case -> this bundle
# ---------------------------------------------------------------------------
# The nagini sibling contracts TWO functions (a class-construction site and a
# factory site, each over `int` callback ids with 0 meaning "absent"). This
# bundle models ONE obligation whose four inputs carry BOTH sites' candidate
# carriers, so the nagini rivals land on a single carrier here. Case-count
# parity is not the target; coverage of the modeled surface is.
#
#   nagini case                        -> here
#   ---------------------------------------------------------------------
#   pos-declared-branch-reorder        -> pos-own-block-case-split
#   pos-factory-explicit-if            -> pos-carriers-then-own-block-wins
#   admiss-declared-f2p-shape          -> admiss-f2p-shaped-inputs (both nagini
#   admiss-factory-f2p-shape              admissibility cases land on it)
#   weak-declared-drop-own             -> weak-legacy-carrier-scan
#   weak-factory-passed-wins           -> weak-direct-attr-overrides-own
#   weak-declared-inverted-shadow      -> weak-base-block-shadows-own
#                                         (+ weak-base-block-shadows-own-near
#                                          as its near-miss, see below)
#   weak-factory-drop-base-inherited   -> weak-base-block-as-fallback
#   weak-factory-ignore-passed         -> weak-base-block-only
#   (no nagini counterpart)            -> weak-direct-attr-only
#   (no nagini counterpart)            -> weak-own-block-derived-id (the VALUE
#                                         half of the equation; see case 3c)
#   frame/permission-mutation class    -> VACUOUS (see below)
#   divergence / non-termination class -> VACUOUS on lean (see below)
#   AXIOM_TESTS (empty in nagini)      -> dropped; the axiom lane is G-AX's job
#
# ADMISSIBILITY — landed by the independent audit as `admiss-f2p-shaped-inputs`,
# carrying BOTH nagini admissibility cases. An earlier draft of this note omitted
# the lane as "vacuous" on the ground that `correct_resolveModelFormCallback`
# states no precondition, so PRECOND-TOO-STRONG is inexpressible. That reason is
# wrong, and the argument it rests on is the one the guide names explicitly: on a
# TOTAL carrier the analogue of an over-strong precondition is the obligation
# being UNSATISFIABLE at a concrete input the exported behavior actually has to
# handle. A bare `∀` makes the domain full; it does not make the postcondition
# satisfiable at any particular point in it, and nothing else in this battery
# checks that it is. The positive below tests it directly, at both F2P shapes, by
# EVALUATION rather than by re-asserting the binder — see the case's rationale for
# the control that shows the check is load-bearing.
#
# VACUOUS — frame/permission mutation. Nagini's frame class turns on fractional
# permissions over heap inputs. Lean is referentially transparent: the four
# inputs are immutable values and no impl can mutate a caller's view of them, so
# the class has no counterpart. (The FRAME sense that DOES apply here — an
# output component left unconstrained — is attacked directly, by the three
# rivals that consult a carrier the postcondition frames out.)
#
# NOTHING TO SHIP — divergence / non-termination. The disposition is that there
# is no rival to ship here, but NOT for the structural reason an earlier draft of
# this note gave. That draft claimed a non-terminating implementation "cannot be
# written at all" because the impl is a total Lean `def` elaborated by the
# kernel. That is false as stated, and was measured false: marking the impl
# `partial` is inside `variant_scope` (it is an impl-region edit, and `partial`
# is not among the banned tokens for a variant), and a self-looping
# `partial def implementation_resolveModelFormCallback ... :=
#   implementation_resolveModelFormCallback ...` ELABORATES on this carrier
# (exit 0 with the obligation removed). So a diverging impl is writable.
#
# What makes the class empty here is the OBLIGATION, not the elaborator. Lean's
# `correct_resolveModelFormCallback` is a total-correctness statement about the
# denotation of `implementation_resolveModelFormCallback` at every input; it
# carries no termination side-condition that a diverging impl could satisfy
# vacuously. A `partial def` is compiled against an `Inhabited` default and its
# equation lemma is withheld, so the diverging impl's own theorem is not provable
# rather than trivially provable — re-measured by the independent audit: the
# self-looping `partial def` variant fails its obligation (`rfl`, `simp`,
# `decide`, `simp_all` and `simp [implementation_…]` all fail; `simp made no
# progress` on an opaque `problem_spec … (implementation …)` goal), so it does
# not verify and is no SPEC-TOO-WEAK finding.
#
# It is nonetheless NOT shippable as a reject case, and the reason is the witness
# rather than the obligation — which is the part the earlier draft did not
# establish. Withholding the equation lemma is exactly what stops a witness from
# discriminating: the audit built the gate's own `witness_file` against that
# variant and `decide` cannot evaluate the claim at all —
#   Tactic `decide` failed ... its `Decidable` instance instDecidableNot did not
#   reduce to `isTrue` or `isFalse`
# which is the gate's `_STUCK_REDUCTION` screen, recorded `witness-undecided`
# (inconclusive => MALFORMED-TESTS), not `rejected`. The fourth independent audit
# re-ran both witness shapes against that variant and confirms the disposition
# while sharpening which screen fires: this battery's own `_witness` helper
# unfolds `implementation_resolveModelFormCallback` too, and against a `partial
# def` that unfold ITSELF fails first —
#   Tactic `unfold` failed to unfold `implementation_resolveModelFormCallback` in
#   ¬implementation_resolveModelFormCallback (some 1) false none none = some 1
# (exit 1) — so the shipped witness shape lands as `witness-unproven` rather than
# `witness-undecided`. Dropping that unfold reproduces the `_STUCK_REDUCTION`
# message quoted above verbatim (exit 1). Both are INCONCLUSIVE outcomes, so
# either way the case is unshippable and the withheld equation lemma is the cause;
# the disposition below is unchanged. A `witness_reference` cannot
# rescue it either: the blocked term is the RIVAL's own irreducible impl, and the
# reference only replaces the gold-side subject. So the disposition is a KNOWN
# HOLE in what this gate can attest for a diverging impl on this carrier, not a
# vacuous class — no rival to ship, and the reason is measured, not structural.
#
# The velvet sibling's `loom.semantics.termination "partial"` hole — where a
# diverging impl DOES satisfy every `ensures` vacuously and verifies while its
# faithful patch hangs the F2P — is a real and separate defect, already
# escalated for the 401 velvet bundles it applies to; see
# the corpus-wide termination-semantics finding, which records lean as unaffected. It is cited
# here, not re-derived, and is not a hole in THIS spec. The nagini sibling
# carries no `diverge-*`/`nonterm-*` case either.
from pathlib import Path

INSTANCE = "django__django-15916"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- exact frozen regions (edit ONLY these) ---------------------------------

# The whole body of the `-- impl-start` / `-- impl-end` region, below the
# signature. Anchored on the full three lines: each lies inside the impl region
# and the block occurs exactly once in the file.
_IMPL = (
    "  -- the constructed class draws its callback from its own options block\n"
    "  let mut selected := metaCallback\n"
    "  return selected\n"
)

# The tactic BODY of `theorem correct_resolveModelFormCallback` (inside
# `-- proof-start` / `-- proof-end`). The theorem STATEMENT is never touched, so
# every variant carries the identical obligation.
_PROOF = (
    "  intro metaCallback directHasCallback directCallback baseMetaCallback\n"
    "  rfl\n"
)


def _witness(args):
    """A refutation witness: the spec predicate is FALSE of what the rival
    returns at one concrete input. Checked in a file whose proof obligations
    have been stripped, so no tactic script can interfere; it must elaborate
    against the rival and FAIL against the frozen solution."""
    return (
        f"example : ¬ problem_spec_resolveModelFormCallback {args}\n"
        f"    (implementation_resolveModelFormCallback {args}) := by\n"
        "  unfold problem_spec_resolveModelFormCallback"
        " implementation_resolveModelFormCallback\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different CORRECT impls.
    # Must VERIFY; if either is rejected the spec is SPEC-TOO-STRONG. Both
    #
    # The independent audit probed SPEC-TOO-STRONG further (attack E) with three
    # NEW correct reshapes not shipped here — `metaCallback.map id`,
    # `metaCallback.elim none some`, and a bind-based answer that first folds every
    # framed-out carrier into a discarded accumulator. All three VERIFY (exit 0,
    # closed by `cases … <;> rfl` near the frozen proof), so the spec admits
    # faithful impls across the eliminator/map/bind spellings and is not over-fit
    # to the frozen projection's shape. Not shipped, to keep the lane from
    # duplicating what the two below already defend.
    #
    # The third independent audit re-ran that probe with FOUR further reshapes,
    # again not shipped: a DEPENDENT-`Option.get` split (`if h : metaCallback.isSome
    # then return some (metaCallback.get h) else return none`), `metaCallback.elim
    # none some`, `metaCallback.bind some` after reading and discarding every
    # framed-out carrier, and a `+ 0` round-trip through the declared identifier.
    # All four VERIFY (exit 0) under a proof near the frozen one, and `map id`
    # re-verifies too. So the spec admits faithful impls across the eliminator /
    # map / bind / dependent-get spellings, and it is NOT over-fit: the two
    # positives below also confirm the frozen `rfl` alone is genuinely insufficient
    # for a reshape (each fails with the frozen tactic body, `rfl failed: the
    # left-hand side baseMetaCallback is not definitionally equal to ...`, exit 1),
    # so both positives really do reprove rather than inheriting a script that
    # would have closed anything.
    # reprove inside the proof region (the frozen `rfl` is tuned to the frozen
    # impl's syntactic form, so a reshaped impl needs its own script) while
    # keeping the `theorem correct_resolveModelFormCallback` statement
    # byte-identical. Neither adds a lemma, an axiom, or `sorry`.
    # =====================================================================
    {
        "id": "pos-own-block-case-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "  -- Correct, structurally different: dispatch on whether the\n"
                "  -- class's own options block declares a callback at all, and\n"
                "  -- answer each case explicitly, instead of projecting the\n"
                "  -- input in one step. Same selection, spelled as a match.\n"
                "  match metaCallback with\n"
                "  | none => return none\n"
                "  | some cb => return some cb\n",
            ),
            _PROOF,
            "  intro metaCallback directHasCallback directCallback baseMetaCallback\n"
            "  unfold problem_spec_resolveModelFormCallback"
            " implementation_resolveModelFormCallback\n"
            "  cases metaCallback <;> rfl\n",
        ),
        "rationale": "an eta-expanded but observationally identical impl of the "
                     "same selection must verify, else SPEC-TOO-STRONG. The "
                     "`match` reassembles exactly its scrutinee in both arms, so "
                     "`result = metaCallback` holds in each; the two-way case "
                     "split needs no induction and closes by `cases … <;> rfl`. "
                     "Defends the sole obligation "
                     "`correct_resolveModelFormCallback`.",
    },
    {
        "id": "pos-carriers-then-own-block-wins",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "  -- Correct, structurally different: consult the other\n"
                "  -- candidate carriers first, then let the class's own options\n"
                "  -- block have the final say — whatever any other carrier\n"
                "  -- offered is overwritten before the answer is produced. The\n"
                "  -- extra reads are dead, so the selection is unchanged.\n"
                "  let mut selected := baseMetaCallback.getD none\n"
                "  if directHasCallback then\n"
                "    selected := directCallback\n"
                "  selected := metaCallback\n"
                "  return selected\n",
            ),
            _PROOF,
            "  intro metaCallback directHasCallback directCallback baseMetaCallback\n"
            "  unfold problem_spec_resolveModelFormCallback"
            " implementation_resolveModelFormCallback\n"
            "  cases directHasCallback <;> rfl\n",
        ),
        "rationale": "a correct impl that READS every framed-out carrier and "
                     "then discards what it read must still verify, else "
                     "SPEC-TOO-STRONG. This is the sharp positive control for "
                     "the frame half of `result = metaCallback`: the spec must "
                     "forbid other carriers from reaching the RESULT, not "
                     "forbid an impl from touching them. The branch on "
                     "`directHasCallback` makes the final assignment the only "
                     "live one, so `cases directHasCallback <;> rfl` closes both "
                     "arms. Defends `correct_resolveModelFormCallback`.",
    },

    # =====================================================================
    # ADMISSIBILITY — landed by the independent audit; see the note above for
    # why the lane is NOT vacuous on a total carrier. The impl region is kept
    # byte-for-byte FROZEN and the frozen tactic body still closes the frozen
    # obligation verbatim at the end, so this case weakens nothing and adds a
    # check: two `have`s that discharge the postcondition BY EVALUATION at the
    # two concrete input shapes the exported behavior must handle.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "  -- ADMISSIBILITY on a total carrier: the obligation must be\n"
            "  -- SATISFIABLE at the concrete inputs the exported behavior\n"
            "  -- actually has to handle. Each `have` discharges the\n"
            "  -- postcondition at one such input by EVALUATION (`decide` on the\n"
            "  -- reduced `Id.run` term), so it fails if the spec cannot be met\n"
            "  -- there. The frozen obligation is then closed verbatim below.\n"
            "  have f2p_own_block :\n"
            "      problem_spec_resolveModelFormCallback (some 7) false none none\n"
            "        (implementation_resolveModelFormCallback (some 7) false none"
            " none) := by\n"
            "    unfold problem_spec_resolveModelFormCallback"
            " implementation_resolveModelFormCallback\n"
            "    decide\n"
            "  have f2p_inherited_block :\n"
            "      problem_spec_resolveModelFormCallback (some 7) true none"
            " (some (some 7))\n"
            "        (implementation_resolveModelFormCallback (some 7) true none"
            " (some (some 7))) := by\n"
            "    unfold problem_spec_resolveModelFormCallback"
            " implementation_resolveModelFormCallback\n"
            "    decide\n"
            "  intro metaCallback directHasCallback directCallback baseMetaCallback\n"
            "  rfl\n",
        ),
        "rationale": "ADMISSIBILITY on a total carrier. The frozen obligation is "
                     "a bare `∀` with no hypothesis, and the port had dropped "
                     "this lane on the ground that nothing could be "
                     "PRECOND-TOO-STRONG. That reason is wrong: a full domain is "
                     "not a satisfiable postcondition, and the analogue here is "
                     "the obligation being UNSATISFIABLE at a concrete "
                     "F2P-shaped input. The two `have`s pin it at exactly the "
                     "two shapes the modeled behavior must handle — the callback "
                     "declared only in the class's own options block "
                     "(`metaCallback = some 7`, `directHasCallback = false`, "
                     "`baseMetaCallback = none`), and the options block carrying "
                     "the callback with a direct attribute also present and a "
                     "base form declaring the same one (`some 7`, `true`, "
                     "`none`, `some (some 7)`) — and each is closed by `decide` "
                     "past the `Id.run` residue, so the do-block is really "
                     "EVALUATED at that input rather than reasoned about "
                     "abstractly. The check is load-bearing, not a restatement "
                     "of the binder: the audit built the same case with the "
                     "claimed result changed to `some 8` at the first input and "
                     "it FAILS (`decide` proved `some 8 = some 7` is false, exit "
                     "1), so a spec unsatisfiable at these points would be "
                     "caught here. If this case is REJECTED => "
                     "PRECOND-TOO-STRONG. Defends "
                     "`correct_resolveModelFormCallback`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each MUST be rejected; if any
    # verifies, the spec admits an impl that is not the modeled behavior.
    # Every case carries a `witness` seen to discriminate by hand: it
    # elaborates against the rival and fails on the frozen solution (checked
    # with scripts/lean_verify.sh before shipping — see 'notes').
    #
    # The third audit's own attack-D sweep ran EIGHT further wrong impls not
    # shipped here, each built with a maximal `first | rfl | (cases <each binder>
    # <;> rfl) | simp | simp_all | decide | aesop` script so a rejection could not
    # be a tactic gap: own-block-then-direct-fallback, the constant "no callback",
    # direct-value-wins, base-block-when-the-direct-attribute-is-absent,
    # direct-wins-only-when-it-carries-a-real-callback, a value SHIFT
    # (`metaCallback.map (· + 1)`), collapse-every-declared-callback-to-one-id, and
    # base-`some none`-forces-the-answer-empty. All eight exited 1 on genuinely
    # OPEN goals over the residual claim (`⊢ none = metaCallback`,
    # `⊢ Option.map (fun cb => cb + 1) metaCallback = metaCallback`, `⊢ 0 = val`,
    # `⊢ (if directHasCallback = true ∧ directCallback.isSome = true then pure
    # directCallback else pure metaCallback).run = metaCallback`), never a tactic
    # mismatch — so the single clause is tight and there is no spec hole. Two of
    # those eight were the diagnostic ones: the value-shift rival is what showed
    # the VALUE half went unattacked (now shipped as case 3c), and the value-keyed
    # direct-wins rival is what re-measured case 3's discrimination claim.
    #
    # The independent audit also probed for an UNATTACKED hole (attack D) with
    # four NEW wrong impls the battery does not contain: own-block-then-DIRECT-
    # attribute fallback; the constant "no callback"; direct-attribute-wins-on-
    # VALUE (`match directCallback with | some cb => …`); and base-block-wins-when-
    # the-direct-attribute-is-ABSENT. Each was built twice — with the frozen proof
    # body, and with a maximal `first | rfl | (cases … <;> rfl) | simp_all | decide`
    # script so a rejection could not be a mere tactic gap. All eight builds exited
    # 1, and the failures are genuinely OPEN goals on the residual claim (e.g.
    # `⊢ (if metaCallback = none then pure directCallback else pure metaCallback).run
    # = metaCallback`, `⊢ none = metaCallback`), not tactic mismatches. So no
    # additional spec hole was found; the single clause is tight against every
    # carrier this surface exposes.
    #
    # The first four attack the SELECTION half and each one's faithful patch
    # loses an F2P outright. Case 3c attacks the VALUE half — the right carrier,
    # the wrong identifier — which the carrier-moving rivals structurally cannot
    # reach (see its rationale). The last three attack the FRAME half at inputs
    # the shipped test suite does not reach; their refinement notes say so plainly
    # rather than claiming an F2P failure they do not cause.
    #
    # A THIRD independent audit rebuilt all of the above from scratch and found
    # the reject lane sound but INCOMPLETE in one direction, and one rationale
    # false. Both are fixed here rather than reported:
    #   * Every shipped rival attacked WHICH CARRIER is read, so the equation's
    #     VALUE half was unprobed as a CLASS: no shipped rival distorted the value
    #     found in the correct carrier. Landed as case 3c (rival exit 1 under the
    #     frozen proof AND under a maximal
    #     `first | rfl | cases … | simp_all | decide | aesop` script, so its
    #     rejection is not a tactic gap; witness exit 0 on the rival, exit 1 on
    #     gold with `decide proved ¬(have selected := some 1; pure selected).run =
    #     some 1 is false`, forgery exit 0 on gold and exit 1 on the rival).
    #   * Case 3's rationale claimed its witness is "the only point in the battery
    #     where `directCallback` is a real callback rather than `none`". That is
    #     FALSE as written — case 3b's point also carries `directCallback = some 6`
    #     — and the claim it was reaching for is the true one now stated there:
    #     the only point where the direct carrier holds a callback DIFFERENT from
    #     the own block's. Re-measured with the value-keyed rival the claim exists
    #     to catch, which is refuted at case 3's point (exit 0) and NOT at case 2's
    #     or case 3b's (exit 1 each), so the point is load-bearing.
    #
    # A FIFTH independent audit rebuilt the whole reject lane from scratch and found
# no substantive defect, only the one prose overclaim fixed in case 2's refinement
# above. What it ran, all with scripts/lean_verify.sh at 900s:
#   * All EIGHT witnesses, four builds each (rival / frozen solution / forgery on
#     the frozen solution / forgery on the rival): rival exit 0 and gold exit 1 for
#     all eight, and the forgery pair INVERTS on both subjects (forgery-on-gold
#     exit 0, forgery-on-rival exit 1). Every gold-side failure is the plain
#     evaluation `Tactic decide proved that the proposition ¬(...) is false`, so
#     attack B' needs no type-revealing build: the signature class here is a plain
#     evaluation, and gold's exit code demonstrably tracks the CLAIM.
#   * A full 8x9 witness-by-subject MATRIX (72 builds), the eight rivals plus the
#     value-keyed direct-wins rival as a ninth subject. It reproduces every
#     cross-rival claim these rationales make in prose: case 3b's witness does not
#     refute case 1's rival (exit 1); case 5's witness does not refute case 6's
#     (exit 1); case 6's witness DOES refute case 5's (exit 0), so 6 is a strict
#     near-miss; the value-keyed rival is refuted at case 3's point (exit 0) and at
#     neither case 2's nor case 3b's (exit 1 each); and case 3c is refuted
#     incidentally by six of the seven other witnesses, the sole exception being
#     case 4's `metaCallback = none` point, exactly as its rationale now states.
#   * FIVE NEW wrong impls under a maximal
#     `first | rfl | cases ... | simp | simp_all | decide | omega | aesop` script,
#     aimed at the traps the brief names: a `Nat`-truncation round-trip
#     (`cb - 1 + 1`, wrong only at `cb = 0`), an `Option`-collapsing
#     `some (metaCallback.getD 0)`, `Option.filter (· != 0)`, a frame rival keyed
#     on `metaCallback = none ∧ directHasCallback`, and a swap-when-the-direct-
#     carrier-differs rival. All five exited 1 on genuinely OPEN residual goals
#     (e.g. `⊢ Option.map (fun cb => cb - 1 + 1) metaCallback = metaCallback`,
#     `⊢ some (metaCallback.getD 0) = metaCallback`), never a tactic mismatch — so
#     none of those collapses is definitional on this carrier and the clause is
#     tight. No spec hole.
#   * FOUR NEW correct reshapes (attack E): a `2 * cb / 2` round-trip, a DEPENDENT
#     `if h : metaCallback = none` split, a three-way `match` on the pair
#     `metaCallback, directHasCallback`, and a `for`-loop that folds both framed-out
#     carriers into a discarded accumulator. All four VERIFY (exit 0), so the spec
#     is not over-fit. No soundness hole.
#   * Both positives rebuilt with the FROZEN tactic body: each exits 1
#     (`rfl failed ... baseMetaCallback is not definitionally equal`), so neither
#     positive is definitionally the frozen impl and each genuinely reproves.
#   * The admissibility control: the same case with the first `have`'s claimed
#     result changed to `some 8` exits 1 (`decide proved (have selected := some 7;
#     pure selected).run = some 8 is false`), so those `have`s really evaluate.
#   * The divergence lane (F'), re-derived: this bundle's Solution.lean carries NO
#     `set_option loom.semantics.termination` line at all — it is a plain
#     Lean+Mathlib carrier, not velvet — so neither the "total" nor the "partial"
#     disposition applies verbatim. Measured directly instead, and it reproduces
#     the KNOWN-HOLE disposition recorded above byte-for-byte: the self-looping
#     `partial def` does NOT verify (exit 1, `unfold failed to unfold
#     implementation_resolveModelFormCallback`), so no SPEC-TOO-WEAK; the shipped
#     witness shape against it exits 1 on that same failed unfold
#     (`witness-unproven`), and the bare-`decide` shape reproduces
#     `instDecidableNot did not reduce to isTrue or isFalse` (`_STUCK_REDUCTION`,
#     `witness-undecided`). Both INCONCLUSIVE, so still nothing shippable.
#   * Attack A: the `theorem correct_resolveModelFormCallback` statement is
#     byte-identical across all ELEVEN modules (sha d18916de527c), and the diff of
#     each module against the frozen file touches only the impl body and the proof
#     BODY — no lemma, axiom, sorry, or restated hypothesis.
#   * Case 1's rival impl is byte-identical (code lines) to Solution_prepatch.lean's
#     impl region, so it is the modeled legacy behavior rather than a reshape.
#
# INDEPENDENT AUDIT (attack B) re-derived all seven witnesses from scratch,
    # rebuilding each one with the gate's own `witness_file` construction against
    # the rival and against the frozen solution. Every rival build exited 0 and
    # every frozen-solution build exited 1, and — the part the exit code alone
    # does not show — each frozen-side failure is a POSITIVE semantic refutation,
    # `Tactic decide proved that the proposition ¬(...) is false`, never a stuck
    # reduction, an unknown identifier, a type error, or a timeout. So no case
    # here is `witness-undecided` in substance, and none is a tautology. No
    # witness binds anything (`consistency_probe` is None for all seven), so the
    # witness-inconsistent class is unreachable rather than merely unchecked.
    #
    # A SECOND independent audit added the FORGERY pair (attack B'), which is the
    # check that "the error looks semantic" cannot make: for each of the seven it
    # built a file differing from the witness ONLY in dropping the `¬`, i.e.
    # claiming the frozen solution is CORRECT at that same point, against the
    # frozen solution. All seven forgeries exited 0 — the exact OPPOSITE of the
    # witness's own exit 1 on the same subject. So gold's exit code is a function
    # of the CLAIM here, not of the file, and no case rests on an error that would
    # have been printed for a true claim too. The gold-side signature per case is
    # `decide proved ¬(have selected := <v>; pure selected).run = <v> is false`,
    # i.e. the kernel evaluated the frozen impl to a literal and found the spec
    # SATISFIED — the strongest gold-side evidence available.
    #
    # That audit also re-derived the three cross-rival claims the rationales below
    # make in prose, which no gate checks: case 3b's witness FAILS against case 1's
    # rival (exit 1 — case 1 really is correct at that point, so 3b cannot share
    # case 1's witness); case 5's witness FAILS against case 6's rival (exit 1 —
    # case 6 really is correct wherever a base declares "no callback"); and case
    # 6's witness HOLDS against case 5's rival (exit 0 — so 6 is a strict near-miss
    # of 5, not a duplicate of it). Each shipped near-miss therefore earns its own
    # witness point.
    # =====================================================================

    # (1) The legacy resolution in full: scan the base forms' options blocks and
    # let a direct class attribute override that, never reading the class's own
    # options block. This is the pre-existing behavior the bundle's
    # Solution_prepatch.lean models.
    {
        "id": "weak-legacy-carrier-scan",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "  -- Draw the callback from a base form's options block, letting a\n"
            "  -- direct class attribute override it when one is present. The\n"
            "  -- class's OWN options block is never consulted.\n"
            "  let mut selected := baseMetaCallback.getD none\n"
            "  if directHasCallback then\n"
            "    selected := directCallback\n"
            "  return selected\n",
        ),
        "witness": _witness("(some 1) false none (some (some 7))"),
        "refinement": "a faithful patch with this resolution fails "
                      "test_custom_callback_in_meta: that test declares the "
                      "callback ONLY in the constructed class's own options "
                      "block, with no direct class attribute and no base form "
                      "declaring one — the F2P shape `metaCallback = some cb`, "
                      "`directHasCallback = false`, `baseMetaCallback = none`. "
                      "This resolution answers `none` there, so the fields are "
                      "built with the model's default widgets instead of the "
                      "callback's. It does NOT resolve the F2P, so a verifying "
                      "rival here would be a true verify-does-not-imply-resolve "
                      "break.",
        "rationale": "violates the sole clause `result = metaCallback` — the "
                     "SELECTION half. The witness holds `directHasCallback = "
                     "false` and moves `baseMetaCallback` to `some (some 7)` "
                     "while `metaCallback = some 1`: the spec demands `some 1` "
                     "and this impl answers `some 7`. Probing the base-form "
                     "carrier rather than the F2P's `none` also varies the "
                     "`baseMetaCallback` binder away from the value the next two "
                     "witnesses hold it at.",
    },

    # (2) The class's own options block is read, but a direct class attribute
    # overrides it whenever the attribute is PRESENT — including when its value
    # is "no callback".
    {
        "id": "weak-direct-attr-overrides-own",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "  -- Read the class's own options block, but let a direct class\n"
            "  -- attribute override it whenever one is present — even when the\n"
            "  -- attribute's own value is \"no callback\".\n"
            "  let mut selected := metaCallback\n"
            "  if directHasCallback then\n"
            "    selected := directCallback\n"
            "  return selected\n",
        ),
        "witness": _witness("(some 5) true none none"),
        "refinement": "a faithful patch with this resolution fails "
                      "test_custom_callback_from_base_form_meta. There the "
                      "constructed class's options block inherits the callback "
                      "from the base form it is built from, while a direct "
                      "class attribute is present carrying \"no callback\" — the "
                      "F2P shape `metaCallback = some cb`, `directHasCallback = "
                      "true`, `directCallback = none`. The present-but-empty "
                      "attribute masks the options block, the answer is `none`, "
                      "and the produced form's fields get the model's default "
                      "widgets. It does NOT resolve the F2P. PRECISION (fifth "
                      "audit): this case's witness holds those three components "
                      "at the F2P's values but pins the FOURTH, "
                      "`baseMetaCallback`, at `none`, whereas at that F2P a base "
                      "form does declare the callback, so the witness point is "
                      "the F2P shape in three components and not, as an earlier "
                      "draft of this note said, \"exactly\" it. The F2P-loss "
                      "claim is unaffected and was measured rather than argued: "
                      "the audit built this same witness at the FULL F2P shape "
                      "`(some 5) true none (some (some 5))` and it still refutes "
                      "this rival (exit 0) while failing on the frozen solution "
                      "(exit 1, `decide proved ¬(have selected := some 5; pure "
                      "selected).run = some 5 is false`). The shipped point is "
                      "kept because it is the battery's only "
                      "`directHasCallback = true` / `directCallback = none` "
                      "point AND holds `baseMetaCallback = none`, which is what "
                      "shows the masking needs no base carrier at all.",
        "rationale": "violates `result = metaCallback` — the SELECTION half, at "
                     "the sub-domain where the framed-out `directHasCallback` "
                     "binder is `true`. This is the ONLY witness in the battery "
                     "that both sets `directHasCallback = true` and leaves "
                     "`directCallback = none`, so it is what discriminates "
                     "attribute PRESENCE from attribute VALUE: a rival keyed on "
                     "presence alone is caught here and nowhere else.",
    },

    # (3) Read only the direct class attribute; ignore both options blocks.
    {
        "id": "weak-direct-attr-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "  -- Draw the callback from a direct class attribute alone, ignoring\n"
            "  -- both the class's own options block and every base form's.\n"
            "  let mut selected := directCallback\n"
            "  return selected\n",
        ),
        "witness": _witness("(some 5) true (some 9) none"),
        "refinement": "a faithful patch reading only a direct class attribute "
                      "fails BOTH F2P tests. test_custom_callback_in_meta sets "
                      "no direct attribute at all, so the answer is \"no "
                      "callback\"; test_custom_callback_from_base_form_meta has "
                      "a direct attribute present but carrying \"no callback\", "
                      "so the answer is again \"no callback\". Both then build "
                      "fields with the model's default widgets. It does NOT "
                      "resolve either F2P.",
        "rationale": "violates `result = metaCallback` — the SELECTION half. "
                     "The witness is the only point in the battery where the "
                     "direct carrier holds a callback DIFFERENT from the own "
                     "options block's (`some 9` against `some 5`), which is what "
                     "moves the `directCallback` binder off the own block's "
                     "value: a rival that mishandled the attribute's VALUE (as "
                     "opposed to its mere presence, covered by case 2) would "
                     "otherwise go uncaught. Measured by the third independent "
                     "audit rather than argued: the value-keyed rival "
                     "`if directHasCallback && directCallback.isSome then "
                     "selected := directCallback` is NOT refuted at case 2's "
                     "point (exit 1 — it answers `some 5` there, correctly) and "
                     "IS refuted at this one (exit 0), and it is not refuted at "
                     "case 3b's point either, where the direct carrier AGREES "
                     "with the own block. So this point is load-bearing and no "
                     "other shipped point substitutes for it. Spec demands "
                     "`some 5`; this impl answers `some 9`.",
    },

    # (3b) Nagini's weak-factory-ignore-passed, re-expressed: ignore the
    # DIRECT carrier entirely and always take the base forms' options block.
    # Added by the independent audit — the port map named every other nagini case
    # but silently dropped this one, and no shipped case refutes this impl at a
    # point where the direct carrier and the base carrier are BOTH populated and
    # the own options block agrees with the direct one. Distinct from (1): (1)
    # lets a present direct attribute override the base scan, so (1)'s impl is
    # CORRECT at this witness point (verified by hand: the witness fails to
    # refute (1)'s rival there) and cannot stand in for this one.
    {
        "id": "weak-base-block-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "  -- Draw the callback from a base form's options block alone: the\n"
            "  -- class's own options block is never consulted, and a direct class\n"
            "  -- attribute is passed over even when one is present.\n"
            "  let mut selected := baseMetaCallback.getD none\n"
            "  return selected\n",
        ),
        "witness": _witness("(some 6) true (some 6) (some (some 2))"),
        "refinement": "a faithful patch reading only a base form's options block "
                      "fails test_custom_callback_in_meta: that test declares the "
                      "callback ONLY in the constructed class's own options block "
                      "and no base form declares one, so this resolution answers "
                      "\"no callback\" and the fields are built with the model's "
                      "default widgets. It does NOT resolve that F2P.",
        "rationale": "violates `result = metaCallback` — the SELECTION half, at "
                     "the sub-domain no other case reaches: the witness is the "
                     "only point in the battery where the direct carrier is "
                     "PRESENT and AGREES with the own options block (`some 6` "
                     "both) while a base form carries a DIFFERENT callback "
                     "(`some (some 2)`). That combination is what separates this "
                     "rival from case 1 — case 1 lets the present direct "
                     "attribute win and so answers `some 6` here, correctly, "
                     "which is why this case needs its own witness rather than "
                     "sharing case 1's. Spec demands `some 6`; this impl answers "
                     "`some 2`.",
    },

    # (3c) IDENTITY, not carrier. Added by the third independent audit: every
    # other rival in the battery attacks WHICH CARRIER is read, so all seven were
    # refuted by moving a carrier's value around, and nothing checked that the
    # answer is the callback the own options block actually declares rather than
    # some other callback DERIVED from it. `result = metaCallback` is an equation
    # on the value, not merely on the provenance, and that half went unprobed:
    # this rival reads exactly the right carrier — it consults no other carrier at
    # all, so every carrier-moving witness in the battery leaves it untouched —
    # and still answers wrongly, because it hands back a neighbouring identifier.
    {
        "id": "weak-own-block-derived-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "  -- Read the class's own options block — the right carrier, and the\n"
            "  -- only one consulted — but hand back a callback identifier DERIVED\n"
            "  -- from the declared one instead of the declared one itself.\n"
            "  let mut selected := metaCallback\n"
            "  selected := selected.map (fun cb => cb + 1)\n"
            "  return selected\n",
        ),
        "witness": _witness("(some 1) false none none"),
        "refinement": "a faithful patch that resolved the callback from the "
                      "constructed class's own options block and then used a "
                      "DIFFERENT callable than the one declared there fails "
                      "test_custom_callback_in_meta: that test asserts each built "
                      "field's widget is the one the declared callback produces, "
                      "so building the fields with any other callable leaves the "
                      "widget wrong even though the right carrier was consulted. "
                      "It does NOT resolve that F2P. The witness point is exactly "
                      "that F2P's shape (`metaCallback = some cb`, "
                      "`directHasCallback = false`, `baseMetaCallback = none`).",
        "rationale": "violates `result = metaCallback` as an EQUATION ON THE "
                     "VALUE, a wrong-impl CLASS no other rival in the battery "
                     "exhibits: cases 1-3b and 4-6 all attack which carrier is "
                     "read, so before this case nothing in the reject lane "
                     "distorted the value found in the CORRECT carrier. The "
                     "fourth independent audit measured what that does and does "
                     "NOT buy, because an earlier draft of this rationale "
                     "overclaimed it as \"survives all seven\" witnesses: it does "
                     "not. Built as an 8x10 witness-by-subject matrix, six of the "
                     "seven other witnesses DO refute this rival incidentally "
                     "(exit 0), because each states its point at `metaCallback = "
                     "some n` and this impl answers `some (n+1)` there. The one "
                     "that does not is case 4's, the battery's only "
                     "`metaCallback = none` point, where `Option.map` leaves "
                     "`none` fixed (exit 1). So the case earns its place as a "
                     "distinct RIVAL rather than as a uniquely-needed witness "
                     "POINT, and its own witness discriminates on its own terms "
                     "(exit 0 on the rival, exit 1 on gold). This impl consults "
                     "no carrier "
                     "but the own options block, so it agrees with the modeled "
                     "behavior about provenance and disagrees about identity. "
                     "Refuted at the plainest possible point — the F2P shape "
                     "itself, `metaCallback = some 1` with every framed-out "
                     "carrier empty — which is also why the witness needs no "
                     "carrier to vary. Spec demands `some 1`; this impl answers "
                     "`some 2`. Defends `correct_resolveModelFormCallback`.",
    },

    # (4) The class's own options block, with a base form's options block used
    # as a FALLBACK when the own block declares nothing. Nagini's
    # weak-factory-drop-base-inherited argument, re-expressed: the two-level
    # resolution is kept where the spec frames the second level out entirely.
    {
        "id": "weak-base-block-as-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "  -- Read the class's own options block, and when it declares no\n"
            "  -- callback fall back to a base form's options block instead of\n"
            "  -- answering \"no callback\".\n"
            "  let mut selected := metaCallback\n"
            "  if !metaCallback.isSome then\n"
            "    selected := baseMetaCallback.getD none\n"
            "  return selected\n",
        ),
        "witness": _witness("none false none (some (some 3))"),
        "refinement": "HONEST SCOPE — unlike cases 1-3 this rival's faithful "
                      "patch WOULD resolve both F2P tests: each declares the "
                      "callback in the constructed class's own options block "
                      "(`metaCallback = some cb`), so the fallback arm never "
                      "fires and the answer agrees with the modeled behavior at "
                      "both F2P points, and at the P2P callback shapes too "
                      "(none of them subclasses with a FRESH options block that "
                      "omits a callback its base declares — the only shape that "
                      "separates the two). So a verifying rival here would not "
                      "be a demonstrated F2P break; it would be a FRAME hole in "
                      "the spec (SPEC_GUIDE §0.5), the sub-domain where the "
                      "modeled behavior answers \"no callback\" and this impl "
                      "supplies one. That divergence is real and mechanically "
                      "detectable — the modeled behavior projects the own "
                      "options block unconditionally, so G-CONF's differential "
                      "fuzz over the R/I legs separates them even though the "
                      "shipped suite does not reach the point. Recorded as a "
                      "frame rival, not as an F2P-resolving one.",
        "rationale": "violates `result = metaCallback` — the FRAME half, on the "
                     "sub-domain the spec docstring calls out explicitly (\"when "
                     "the options block declares no callback the result is 'no "
                     "callback', even if a direct attribute or a base form would "
                     "otherwise supply one\"). This is the battery's ONLY "
                     "witness with `metaCallback = none`, so it is what varies "
                     "that binder off `some _`: a rival correct on every "
                     "declared callback but wrong on the absent case is caught "
                     "here alone. Spec demands `none`; this impl answers "
                     "`some 3`.",
    },

    # (5) Inverted shadowing: a base form that declares the attribute AT ALL
    # shadows the class's own options block. Nagini's
    # weak-declared-inverted-shadow, re-expressed on the `Option (Option _)`
    # carrier — which distinguishes "no base declares one" from "a base declares
    # it as empty", a distinction nagini's `int`/0 encoding collapses.
    {
        "id": "weak-base-block-shadows-own",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "  -- Inverted precedence: whenever a base form's options block\n"
            "  -- declares the callback at all, it shadows the class's own\n"
            "  -- options block — even if what it declares is \"no callback\".\n"
            "  let mut selected := metaCallback\n"
            "  if baseMetaCallback.isSome then\n"
            "    selected := baseMetaCallback.getD none\n"
            "  return selected\n",
        ),
        "witness": _witness("(some 4) false none (some none)"),
        "refinement": "HONEST SCOPE — as in case 4, this rival's faithful patch "
                      "would resolve both F2P tests: at test_custom_callback_in_"
                      "meta no base form declares the attribute "
                      "(`baseMetaCallback = none`), so the shadowing arm never "
                      "fires; at test_custom_callback_from_base_form_meta the "
                      "base form declares the SAME callback the constructed "
                      "class's options block inherits, so shadowing is "
                      "unobservable there. It is a FRAME rival: it inverts the "
                      "precedence the modeled behavior fixes, and diverges only "
                      "where the two levels disagree — a shape the shipped F2P "
                      "and P2P callback tests never build. Mechanically it is "
                      "still a real divergence from the modeled behavior "
                      "(caught by G-CONF's differential fuzz), so it is recorded "
                      "as a frame rival rather than an F2P-resolving one.",
        "rationale": "violates `result = metaCallback` — the FRAME half. The "
                     "witness point is what the `Option (Option Callback)` "
                     "carrier buys over nagini's flat encoding: "
                     "`baseMetaCallback = some none` is a base form that "
                     "declares the attribute with value \"no callback\", the "
                     "OUTER-`some`/inner-`none` case, and it moves the "
                     "`baseMetaCallback` binder to a third distinct value "
                     "(alongside `none` and `some (some _)` elsewhere in the "
                     "battery). Spec demands `some 4`; this impl answers `none`.",
    },

    # (6) NEAR-MISS of (5): shadow only when the base form's options block
    # carries an actual callback. Agrees with (5) over more of the domain, so it
    # gets its own witness at the input that separates them.
    {
        "id": "weak-base-block-shadows-own-near",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "  -- Inverted precedence, narrowed: a base form's options block\n"
            "  -- shadows the class's own only when it carries an actual\n"
            "  -- callback; a base declaring \"no callback\" is passed over.\n"
            "  let mut selected := metaCallback\n"
            "  match baseMetaCallback with\n"
            "  | some (some cb) => selected := some cb\n"
            "  | _ => pure ()\n"
            "  return selected\n",
        ),
        "witness": _witness("(some 4) false none (some (some 3))"),
        "refinement": "HONEST SCOPE — same standing as cases 4 and 5: the "
                      "faithful patch resolves both F2P tests (at "
                      "test_custom_callback_in_meta no base form declares the "
                      "callback; at test_custom_callback_from_base_form_meta the "
                      "base form's callback is the very one the constructed "
                      "class's options block inherits, so shadowing it changes "
                      "nothing). Recorded as a FRAME rival: it diverges from the "
                      "modeled behavior only where the two levels carry "
                      "DIFFERENT callbacks, which the shipped suite does not "
                      "build, and that divergence is caught by G-CONF's "
                      "differential fuzz rather than by an F2P.",
        "rationale": "violates `result = metaCallback` — the FRAME half. This is "
                     "a NEAR-MISS of case 5, agreeing with the modeled behavior "
                     "over strictly more of the domain (it is correct wherever a "
                     "base form declares \"no callback\", which is exactly case "
                     "5's witness point). So it does NOT share case 5's witness: "
                     "it is refuted at `baseMetaCallback = some (some 3)`, where "
                     "a base form carries a callback DIFFERENT from the own "
                     "options block's. Spec demands `some 4`; this impl answers "
                     "`some 3`. Shipping the two at one point would let case 6's "
                     "rationale claim a sub-domain the manifest never shows.",
    },
]

# The axiom lane is G-AX's job and this gate ignores AXIOM_TESTS. Recorded empty
# for parity with the nagini sibling's manifest shape: this bundle consumes no
# unchanged callee contract (no `opaque` declaration, no `axiom`), so there is no
# callee to probe in the first place.
AXIOM_TESTS = []
