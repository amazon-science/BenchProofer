"""properties.py — G-PBT falsification battery for django__django-14315 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and both ``prove_correct`` obligations survive with byte-identical
statements) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (TWO contracted methods, both read-only inputs):

  effectiveProcessEnv (overrides : Option Overrides) (combined : Overrides)
      return (out : Option Overrides)
    ensures out = (if hasOverrides overrides then some combined else none)

  normalizedEnv (assembled : Overrides)
      return (out : Option Overrides)
    ensures out = (if assembled.isEmpty then none else some assembled)

Both ``ensures`` are grounded equalities over the method's own arguments (the
``axioms`` region is empty — no opaque answer key to echo). Each pins TWO
independent behaviours whose top-level branches are separately attackable:

  effectiveProcessEnv
    * (D1) the DECISION — the result is ``some combined`` exactly when the
      override set carries an entry (``hasOverrides overrides``), and ``none``
      otherwise. This forks in BOTH directions: an absent set (either genuinely
      absent, ``none``, OR present-but-empty, ``some []``) MUST yield ``none``;
      a present non-empty set MUST yield ``some combined``. The load-bearing
      half is that a present-but-EMPTY set is treated as absent (``none``), not
      as an empty-but-present set — the exact behaviour the fix pins.
    * (V1) the returned VALUE — on the present branch the result carries
      ``combined`` UNCHANGED. A rival that decides correctly but returns a
      different set (dropped / invented entries) violates the ensures on the
      value half. This makes the ``combined`` binder load-bearing.
  normalizedEnv
    * (D2) the DECISION — an empty assembled set is reported ``none``, a
      non-empty one ``some assembled``. Both directions are pinned.

INPUT BINDERS (all free — no ``require`` clause; the post-image must hold for
EVERY value of each):
  * ``overrides : Option Overrides`` — the (possibly-absent) override set;
    drives (D1).
  * ``combined : Overrides``          — the already-combined set; carried by
    (V1) on the present branch.
  * ``assembled : Overrides``         — the assembled set; drives (D2).

ADVERSARIAL READ of the sibling's classes on this carrier (see the footer for
the case-by-case accounting):
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling's #1
    class is three rivals that keep the value clauses verbatim then WRITE into a
    read-only input carrying only a fractional heap permission
    (``Acc(dict_pred(.),1/2)``), rejected for INSUFFICIENT PERMISSION. Lean and
    Velvet are referentially transparent: every parameter is an immutable value,
    neither method declares a ``mut`` binder, there is no heap and no aliasing.
    There is no read-only input to overwrite and no permission system to trip,
    so the class has no carrier analogue. No substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION — N/A. The sibling carries NO ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` case (it pins no ``MustTerminate``
    obligation), so there is nothing to port and no known-hole disposition to
    record for this instance.
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images are equalities to closed
    expressions over the methods' own arguments (``hasOverrides`` is a concrete
    ``def``; ``combined`` / ``assembled`` are the inputs); there is no opaque
    answer key a wrong impl could echo. The cheapest correct impl computes the
    decision honestly, which the positive controls cover.
  * MERGE-DIRECTION (sibling swapped-unpack rival) — the combine step is an
    UNCHANGED sub-computation the patch does not touch, abstracted to the free
    input ``combined`` (mapping.md §2/§3), so WHICH entry wins a collision is not
    observable in the result. Its nearest carrier analogue (permuting
    ``combined``) IS rejected here, because ``Overrides`` is a list and the spec
    therefore observes order — but its faithful real counterpart is a reordered
    dict, which mapping-equality does not observe, so that rival is not actually
    WRONG and is deliberately not shipped. See footer.
  * SPURIOUS-KEY (sibling key-injection rival) — genuinely expressible and
    shipped as ``weak-effective-augment-combined``. The value clause has TWO
    independent directions and one rival cannot cover both: at ``combined = []``
    a rival that DROPS entries agrees with gold while one that ADDS an entry
    still differs. Both directions are attacked (footer).
  * PARTIAL-DOMAIN / VALUE — the reject lane. Each rival is correct on most of
    the domain yet diverges on one sub-domain: the empty-not-absent break (the
    actual bug), the value-on-present break, the absent-input break, and the two
    normalizedEnv branch breaks.

WITNESS MECHANICS. Both frozen impls are STRAIGHT-LINE (a single ``let`` /
``if``), so their extracted programs reduce fully under ``decide``. Each reject
rival carries a machine-checked refutation ``witness`` — a Velvet tester
statement ``<method>Tester <args> = false`` at ONE concrete input, checked in a
file whose ``prove_correct`` blocks have been stripped so no tactic script can
mask the verdict. Every argument is a concrete literal so ``decide`` reduces the
extracted rival program without getting stuck. Both halves were checked
out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against
its rival and FAILS (``decide`` proves the proposition false) against the frozen
solution, so each rejection is a genuine spec refutation and not mechanical
tactic breakage. No ``sorry`` / ``admit`` / ``native_decide`` / ``axiom`` is
involved.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no
deep-model reference (mapping.md §3: both behaviours are closed
``Option``/emptiness decisions over free inputs; G-AX skipped). The sibling's
AXIOM_TESTS probe the PEP 448 merge, which is precisely the sub-computation this
carrier folds into the free input ``combined`` — not modeled here. This gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14315"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl bodies and proofs, verbatim — anchors lying wholly inside the
# impl regions / elided proof bodies, each unique in the file (asserted at
# load). Every variant edits ONLY these, so the spec view is untouched and
# same_spec holds by construction.
# ---------------------------------------------------------------------------
_EFF_IMPL = (
    "    let result := if hasOverrides overrides then some combined else none\n"
)
_NRM_IMPL = (
    "    let result := if assembled.isEmpty then none else some assembled\n"
)
_EFF_PROOF = "prove_correct effectiveProcessEnv by\n  loom_solve"
_NRM_PROOF = "prove_correct normalizedEnv by\n  loom_solve"

for _a in (_EFF_IMPL, _NRM_IMPL, _EFF_PROOF, _NRM_PROOF):
    assert _BASE.count(_a) == 1, f"anchor drift — re-sync {_a!r}"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's tester machinery:
# ---- `<method>Tester <args> = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` blocks have been stripped. Every argument is a
# ---- concrete literal so `decide` reduces the (straight-line) extracted rival.
def _tester(method, call):
    return (f"\nextract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. One per contracted method.
    # =====================================================================
    {
        "id": "pos-normalized-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape normalizedEnv: negate the emptiness guard and swap the two
        # arms (report the present set first). `!assembled.isEmpty` reports
        # exactly where the frozen guard reported, so `out = (if
        # assembled.isEmpty then none else some assembled)` still holds on the
        # whole domain; the reproof stays a bare `loom_solve`.
        "module": _swap(
            _BASE, _NRM_IMPL,
            "    let result := if !assembled.isEmpty then some assembled else none\n"),
        "rationale": (
            "negating the emptiness guard and swapping the arms reports the "
            "assembled set exactly where the frozen guard does and reports "
            "absent otherwise, so `out = (if assembled.isEmpty then none else "
            "some assembled)` holds on the whole domain; the reproof is "
            "`loom_solve`. A correct reshape must verify, else the spec is "
            "SPEC-TOO-STRONG on the branch order. (Sibling: "
            "pos-control-normalized-reordered.)"),
    },
    {
        "id": "pos-effective-match-restructure",
        "kind": "soundness",
        "expect": "verify",
        # Reshape effectiveProcessEnv: expand `hasOverrides overrides` into an
        # explicit match on `overrides` (absent -> none; present -> branch on
        # emptiness). Same decision and same returned value on every input; the
        # do-block changed shape, so the proof is retuned (still no new lemma).
        "module": _swap(
            _swap(
                _BASE, _EFF_IMPL,
                "    let result := match overrides with\n"
                "      | none     => none\n"
                "      | some kvs => if kvs.isEmpty then none else some combined\n"),
            _EFF_PROOF,
            "prove_correct effectiveProcessEnv by\n"
            "  loom_solve\n"
            "  cases overrides <;> simp_all [hasOverrides]"),
        "rationale": (
            "expanding `hasOverrides overrides` into an explicit match on "
            "`overrides` (absent -> none; present -> branch on emptiness) "
            "computes the same decision and returns the same `combined` on the "
            "present branch, so `out = (if hasOverrides overrides then some "
            "combined else none)` is unchanged; the proof is retuned with "
            "`cases overrides <;> simp_all [hasOverrides]` (no new lemma). A "
            "correct restructure must verify, else SPEC-TOO-STRONG on the guard "
            "shape. (Sibling: pos-control-effective-disjunctive-guard.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — both methods carry NO precondition (the pre-conditions
    # regions are empty), so the sibling's "a normal input satisfies the
    # (half-permission) precondition" probe is degenerate here (every input is
    # in-domain). The residual admissibility risk on a total-domain spec is that
    # the DECISION is DEGENERATE at the interesting point — a guard that never
    # separated present-non-empty from absent/empty would read like a live one.
    # This case discharges an in-region assert that the presence guard genuinely
    # forks: it is FALSE for a present-but-empty set and TRUE for a present
    # non-empty set — the exact boundary the fix pins. The rest of the impl is
    # kept verbatim so the method's own obligation still discharges; the proof
    # is retuned to also close the assert VC.
    # =====================================================================
    {
        "id": "admiss-effective-guard-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _EFF_IMPL,
                "    assert (with_name_prefix `admiss (\n"
                "      hasOverrides (some ([] : Overrides)) = false ∧\n"
                "      hasOverrides (some ([(\"P\", \"v\")] : Overrides)) = true))\n"
                + _EFF_IMPL),
            _EFF_PROOF,
            "prove_correct effectiveProcessEnv by\n  loom_solve <;> decide"),
        "rationale": (
            "the presence decision is satisfiable AND non-degenerate at the "
            "F2P-shaped points: a present-but-EMPTY set is NOT counted as "
            "carrying an override (`hasOverrides ... = false`, so the result is "
            "absent) while a present non-empty set IS (`hasOverrides ... = "
            "true`, so the result is `some combined`) — the guard really forks on "
            "that boundary, which is the whole behavioural content of the fix. "
            "The in-region assert must discharge (else the guard would be "
            "degenerate / the obligation vacuous); the impl is kept verbatim so "
            "`out = (if hasOverrides overrides then some combined else none)` "
            "still verifies. (Sibling: admiss-effective-normal-input, re-aimed "
            "from precondition admissibility to guard non-degeneracy since this "
            "backend has no precondition and no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing F2P test.
    # =====================================================================
    {
        "id": "weak-effective-empty-present",
        "kind": "uniqueness",
        "expect": "reject",
        # THE ACTUAL BUG (pre-patch shape): treat a present-but-EMPTY override
        # set as present rather than absent. Correct on absent (none) and on
        # present non-empty (some combined); diverges only on the
        # present-but-empty sub-domain.
        "module": _swap(
            _BASE, _EFF_IMPL,
            "    let result := match overrides with\n"
            "      | none     => none\n"
            "      | some _   => some combined\n"),
        "refinement": (
            "this is the pre-patch behaviour the change fixes: an empty (but "
            "present) override set was carried through as if it carried "
            "overrides, so the launched process received an explicit combined "
            "set instead of inheriting the ambient set wholesale (the absent "
            "signal). The F2P scenario that hands an empty override set and "
            "asserts the process is launched with the AMBIENT-inherit signal "
            "(absent) would instead see a present combined set, so the faithful "
            "patch does NOT resolve — the precise defect the spec must sense "
            "(G-DIFF)."),
        "rationale": (
            "REJECT from `out = (if hasOverrides overrides then some combined "
            "else none)` on the DECISION (D1): for a present-but-empty set "
            "`hasOverrides` is false so the post-image demands `none`, but this "
            "rival returns `some combined`. Verifying would be SPEC-TOO-WEAK (the "
            "empty-is-absent normalisation unpinned). Refuted at overrides = "
            "`some []` — the sub-domain no other rival abuses. (Sibling: "
            "partial-domain-effective-empty-not-normalised.)"),
        "witness": _tester(
            "effectiveProcessEnv",
            "effectiveProcessEnvTester (some ([] : List (String × String))) "
            "([] : List (String × String))"),
    },
    {
        "id": "weak-effective-ignore-combined",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE rival (V1): the presence DECISION is exactly right, but on the
        # present branch the result drops `combined` and returns the empty set.
        # Built to abuse `combined`, the free input the present branch carries:
        # every decision rival returns the right value where it reaches the
        # present branch, so none of them attests that the branch carries
        # `combined` through. This one is wrong exactly because it drops it.
        "module": _swap(
            _BASE, _EFF_IMPL,
            "    let result := if hasOverrides overrides then some [] else none\n"),
        "refinement": (
            "a counterpart that decided to launch with the combined set but "
            "handed over an EMPTY set instead would strip the applied overrides "
            "from the launched process's environment; the dbshell F2P scenarios "
            "assert the exact set passed to the launched process (the PG* values "
            "from the connection settings), which an emptied set breaks even "
            "though the present/absent decision is right — so the faithful patch "
            "does NOT resolve. A genuine value-on-present break."),
        "rationale": (
            "REJECT from `out = (if hasOverrides overrides then some combined "
            "else none)` on the VALUE (V1): the present branch is pinned to "
            "`some combined`, this rival returns `some []`. This is the "
            "sub-domain that proves `combined` is LOAD-BEARING — the witness "
            "fixes overrides at a present non-empty set and a NON-EMPTY combined "
            "set, so gold gives `some combined` and the rival `some []`; a rival "
            "mishandling only that binder is caught by no other witness. "
            "Verifying would be SPEC-TOO-WEAK (the returned set unpinned). "
            "(Sibling: the DROPPING half of the merge value rivals. The "
            "AUGMENTING half is a separate sub-domain and is shipped separately "
            "as weak-effective-augment-combined — it is NOT covered here: at "
            "`combined = []` this rival's `some []` AGREES with gold while an "
            "augmenting rival still differs.)"),
        "witness": _tester(
            "effectiveProcessEnv",
            "effectiveProcessEnvTester (some [(\"a\", \"b\")]) "
            "([(\"c\", \"d\")] : List (String × String))"),
    },
    {
        "id": "weak-effective-augment-combined",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE rival (V1), AUGMENTING direction — the sibling's spurious-key
        # class, which the earlier port folded into `weak-effective-ignore-
        # combined` on the claim that it had no additional discriminating
        # sub-domain. That claim is false and was refuted by build: the two
        # rivals are separated at `combined = []`, where the dropping rival
        # returns `some []` and AGREES with gold, while this one returns
        # `some [("X","x")]` and still differs. So the "returned set is
        # `combined` UNCHANGED" clause was only half defended: no shipped rival
        # ADDED an entry, and the witness that catches dropping does not catch
        # augmenting. The decision is exactly right; only the carried set is
        # polluted with an entry that came from neither input.
        "module": _swap(
            _BASE, _EFF_IMPL,
            "    let result := if hasOverrides overrides then "
            "some ((\"X\", \"x\") :: combined) else none\n"),
        "refinement": (
            "a counterpart that decided correctly but handed the launched "
            "process an EXTRA variable that came from neither the ambient set "
            "nor the applied overrides would pollute the launched environment; "
            "the dbshell F2P scenarios assert the EXACT set passed to the "
            "launched process, and an equality against the expected mapping "
            "fails as soon as a spurious entry is present (unlike a mere "
            "reordering, which mapping-equality does not observe). So the "
            "faithful patch does NOT resolve. A genuine value-on-present break "
            "in the augmenting direction."),
        "rationale": (
            "REJECT from `out = (if hasOverrides overrides then some combined "
            "else none)` on the VALUE (V1, augmenting direction): the present "
            "branch is pinned to `some combined` EXACTLY, and this rival returns "
            "a strictly larger set. Refuted at overrides = `some [(\"a\",\"b\")]` "
            "with combined = `[]` — the point chosen precisely because it is "
            "where `weak-effective-ignore-combined` AGREES with gold, so this "
            "witness attests to a sub-domain no other case in the battery "
            "reaches. Verifying would be SPEC-TOO-WEAK (the present branch would "
            "admit invented entries). (Sibling: "
            "uniqueness-effective-spurious-key, restored as a distinct case.)"),
        "witness": _tester(
            "effectiveProcessEnv",
            "effectiveProcessEnvTester (some [(\"a\", \"b\")]) "
            "([] : List (String × String))"),
    },
    {
        "id": "weak-effective-absent-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # ABSENT-input rival: ignore the presence guard entirely and always hand
        # over the combined set. Correct on the present non-empty sub-domain;
        # diverges on BOTH absent sub-domains (genuinely absent and empty). This
        # is the rival that drives the `overrides` binder to `none` and pins the
        # absent-input -> none clause.
        "module": _swap(
            _BASE, _EFF_IMPL,
            "    let result := some combined\n"),
        "refinement": (
            "a counterpart that always launched with the combined set — never "
            "signalling ambient-inherit — would hand the process an explicit set "
            "even when there is nothing to apply; the F2P scenario that hands an "
            "absent override set and asserts the process inherits the ambient set "
            "wholesale would instead see a present set, so the faithful patch "
            "does NOT resolve."),
        "rationale": (
            "REJECT from `out = (if hasOverrides overrides then some combined "
            "else none)` on the DECISION (D1, absent direction): for an absent "
            "set `hasOverrides` is false so the post-image demands `none`, but "
            "this rival returns `some combined`. Verifying would be SPEC-TOO-WEAK "
            "(the absent -> none clause unpinned). Refuted at overrides = `none` "
            "— the only reject witness that drives the `overrides` binder to its "
            "absent value, and the sub-domain the empty-present rival agrees with "
            "gold on (it also returns none for genuinely-absent), so the two do "
            "NOT share a witness. (Added: binder coverage of `overrides = none`, "
            "with no direct sibling — the sibling handled the None branch "
            "correctly in both pre- and post-patch.)"),
        "witness": _tester(
            "effectiveProcessEnv",
            "effectiveProcessEnvTester (none : Option (List (String × String))) "
            "([(\"z\", \"z\")] : List (String × String))"),
    },
    {
        "id": "weak-normalized-empty-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # THE ACTUAL BUG at the second site (pre-patch shape): report an empty
        # assembled set verbatim (`some []`) instead of normalising it to absent
        # (`none`). Correct on the non-empty sub-domain; diverges on the empty
        # sub-domain.
        "module": _swap(
            _BASE, _NRM_IMPL,
            "    let result := some assembled\n"),
        "refinement": (
            "this is the pre-patch behaviour at the second site: an assembled "
            "set that ended up empty was reported as an empty-but-PRESENT set "
            "rather than as absent. The F2P scenarios that build no entries and "
            "assert the reported value is absent (the ambient-inherit signal) "
            "would instead see an empty-but-present set, so the faithful patch "
            "does NOT resolve — the precise defect the spec must sense (G-DIFF)."),
        "rationale": (
            "REJECT from `out = (if assembled.isEmpty then none else some "
            "assembled)` on the DECISION (D2): for an empty assembled set the "
            "post-image demands `none`, but this rival returns `some assembled` "
            "(= `some []`). Verifying would be SPEC-TOO-WEAK (the empty -> absent "
            "normalisation unpinned). Refuted at assembled = `[]`. (Sibling: "
            "partial-domain-normalized-empty-not-none.)"),
        "witness": _tester(
            "normalizedEnv",
            "normalizedEnvTester ([] : List (String × String))"),
    },
    {
        "id": "weak-normalized-always-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual break at the second site: always report absent (`none`),
        # dropping the non-empty assembled set. Correct on the empty sub-domain
        # (where the spec also reports absent); diverges on the non-empty
        # sub-domain — the assembled set is silently dropped.
        "module": _swap(
            _BASE, _NRM_IMPL,
            "    let result := (none : Option Overrides)\n"),
        "refinement": (
            "a counterpart that always reported absent would drop a genuinely "
            "assembled non-empty override set, signalling ambient-inherit when "
            "there ARE entries to report; the dbshell F2P scenarios that build "
            "PG* entries and assert the reported value is exactly that non-empty "
            "set would instead see absent, so the faithful patch does NOT "
            "resolve."),
        "rationale": (
            "REJECT from `out = (if assembled.isEmpty then none else some "
            "assembled)` on the DECISION (D2, dual): for a non-empty assembled "
            "set the post-image demands `some assembled`, but this rival returns "
            "`none`. Verifying would be SPEC-TOO-WEAK (the non-empty -> present "
            "clause unpinned). Refuted at a non-empty assembled set — the "
            "sub-domain the empty-verbatim rival agrees with gold on, so the two "
            "do NOT share a witness. (Sibling: none directly; the dual "
            "half of the normalizedEnv decision, needed to defend both "
            "directions of (D2).)"),
        "witness": _tester(
            "normalizedEnv",
            "normalizedEnvTester ([(\"PGPASSWORD\", \"x\")] : List (String × String))"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 10 SPEC cases (2
# soundness positives, 1 admissibility, 7 uniqueness — three of which are the
# mandatory frame-mutation rivals) plus an AXIOM lane (2 AXIOM_TESTS over the
# PEP 448 merge). Every one is accounted for below.
#
# The sibling contracts the SAME two functions over full-permission mutable
# `Dict[int,int]` inputs held at half permission (READ-ONLY), and the non-empty
# effective path CALLS the `env_merge` @ContractOnly axiom whose value clauses
# (env-wins, base-carried, no-spurious) it pins. This backend models the SAME
# two behaviours DEEPLY but narrows the carrier per mapping.md: the merge itself
# is an UNCHANGED sub-computation folded into the free input `combined`, so its
# internal value clauses (which entry wins, which key is spurious) are NOT
# observable in the returned `Option Overrides` — only WHICH carrier (`some
# combined` vs `none`) is selected, and that the present branch returns
# `combined` unchanged. That refinement makes the merge-direction and
# spurious-key rivals vacuous-by-carrier and the axiom lane inapplicable.
#
#   sibling case                                    kind          -> here                                  disposition
#   -------------------------------------------------------------------------------------------------------------------
#   frame-mut-normalized-write-env                  uniqueness    -> (none)                                VACUOUS (frame)
#   frame-mut-effective-write-base                  uniqueness    -> (none)                                VACUOUS (frame)
#   frame-mut-effective-write-env                   uniqueness    -> (none)                                VACUOUS (frame)
#   partial-domain-effective-empty-not-normalised   uniqueness    -> weak-effective-empty-present          PORTED
#   partial-domain-normalized-empty-not-none        uniqueness    -> weak-normalized-empty-verbatim        PORTED
#   uniqueness-effective-swapped-merge              uniqueness    -> (none)                                VACUOUS-BY-CARRIER (order not observable in the merge)
#   uniqueness-effective-spurious-key               uniqueness    -> weak-effective-augment-combined       PORTED (audit repair; was wrongly folded)
#   pos-control-normalized-reordered                soundness     -> pos-normalized-negated-guard          PORTED
#   pos-control-effective-disjunctive-guard         soundness     -> pos-effective-match-restructure       PORTED (restructured)
#   admiss-effective-normal-input                   admissibility -> admiss-effective-guard-nondegenerate  RE-AIMED
#   AXIOM_TESTS (ax-sound / ax-cover env-merge)     axiom         -> (none)                                N/A (G-AX; merge not modeled)
#   (no sibling)                                                  -> weak-effective-absent-ignored         ADDED (overrides=none binder)
#   (no sibling)                                                  -> weak-normalized-always-absent         ADDED (D2 dual direction)
#
# 5 uniqueness ported, 2 positives ported, 1 admissibility re-aimed; 3 frame
# rivals vacuous; 1 merge-value rival (swapped-merge) vacuous-by-carrier; axiom
# lane N/A; 2 uniqueness ADDED for binder / clause coverage this carrier affords.
#
# VACUOUS (the three frame-mutation rivals): each keeps the value clauses
#   verbatim then writes into a read-only dict input granted only half
#   permission (`env[0]=0` / `base[0]=0`), rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: `overrides` / `combined` /
#   `assembled` are immutable values, neither method declares a `mut` binder,
#   there is no heap, no aliasing, no `Old`, and no permission system. There is
#   no read-only input to overwrite and no frame clause to violate, so the class
#   has no carrier analogue. Omitted as a genuine carrier fact, NOT fabricated
#   (per the porting map: this class is vacuous on a referentially-transparent
#   backend).
# VACUOUS-BY-CARRIER (swapped-merge ONLY): the sibling's swapped-unpack rival
#   makes os.environ override a command variable on a shared key. On this carrier
#   the combine step is an UNCHANGED sub-computation abstracted to the free input
#   `combined` (mapping.md §2/§3), so WHICH entry wins a collision is not
#   observable: there is no term recording the merge's internal structure. The
#   nearest carrier analogue is a PERMUTATION of `combined` (`some
#   combined.reverse`). That analogue is deliberately NOT shipped, and the reason
#   is a refinement fact rather than a carrier fact: `Overrides` is a LIST, so
#   the spec does observe order and the permuted rival IS rejected (measured:
#   rejected, with a witness that elaborates against it and fails on gold). But
#   its faithful real counterpart is a reordered dict, and dict equality does not
#   observe insertion order, so the F2P assertions still PASS and the faithful
#   patch DOES resolve. Shipping it would be a rival that is not actually wrong —
#   its rejection would attest to the list carrier's incidental order-sensitivity,
#   not to the spec. Recorded as a carrier over-approximation instead.
# PORTED, NOT VACUOUS (spurious-key): an earlier revision of this footer claimed
#   this rival too had "no ADDITIONAL discriminating sub-domain" and folded it
#   into `weak-effective-ignore-combined`. That claim was FALSE and is retracted:
#   the two are separated at `combined = []`, where the dropping rival returns
#   `some []` and AGREES with gold while an augmenting rival still differs, so
#   the dropping witness cannot catch augmenting. The augmenting direction of the
#   value clause was therefore undefended. Now shipped as
#   `weak-effective-augment-combined` (rival build exit 0, gold `decide` proves
#   the tester claim false, exit 1). Unlike the permutation analogue above, its
#   faithful counterpart DOES break the F2P assertions (a mapping equality fails
#   as soon as a spurious entry is present), so it is a genuine wrong rival.
# RE-AIMED (admissibility): the sibling asserts an F2P-shaped non-empty mapping
#   satisfies the half-permission Requires (readable through the merge). This
#   backend's methods have NO precondition and no permission surface, so that
#   probe is degenerate (every input is in-domain). It is re-aimed at the
#   residual total-domain risk — that the presence DECISION is DEGENERATE at the
#   interesting point — via an in-region assert that the guard genuinely forks:
#   false for a present-but-empty set, true for a present non-empty set (the
#   boundary the fix pins). The impl is kept verbatim so the ensures still
#   discharges too.
# ADDED (weak-effective-absent-ignored): drives the `overrides` binder to its
#   absent value `none` (which no ported reject case does — the sibling handled
#   the None branch correctly in both pre- and post-patch, so had no rival
#   there) and pins the absent -> none direction of (D1) independently of the
#   empty -> none direction.
# ADDED (weak-normalized-always-absent): the dual of the empty-verbatim rival —
#   pins the non-empty -> present direction of (D2), so both directions of the
#   normalizedEnv decision are attacked.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 6 distinct input
# points):
#   effectiveProcessEnv (D1 decision, V1 value):
#     * weak-effective-empty-present    overrides = some []            combined = []
#     * weak-effective-ignore-combined  overrides = some [("a","b")]   combined = [("c","d")]  (non-empty)
#     * weak-effective-augment-combined overrides = some [("a","b")]   combined = []  (the point where the DROPPING rival agrees with gold)
#     * weak-effective-absent-ignored   overrides = none               combined = [("z","z")]
#   normalizedEnv (D2 decision):
#     * weak-normalized-empty-verbatim  assembled = []
#     * weak-normalized-always-absent   assembled = [("PGPASSWORD","x")]  (non-empty)
#   So `overrides` ranges over {none, some [], some non-empty} — its absent /
#   empty-present / present-non-empty sub-domains all appear; `combined` is
#   varied and demonstrated LOAD-BEARING in BOTH directions (ignore-combined
#   DROPS entries, augment-combined ADDS one; each fixes the decision and abuses
#   only `combined`, and neither witness catches the other's rival);
#   `assembled` ranges over {[], non-empty}. Every independent top-level clause
#   is attacked: (D1) in BOTH directions (empty-present + absent-ignored vs
#   ignore-combined's correct decision), (V1) the returned value in BOTH
#   directions (ignore-combined + augment-combined), and (D2) in BOTH directions
#   (empty-verbatim + always-absent). No binder is pinned at a single value
#   across the reject set.
#
# AXIOM_TESTS: dropped. The sibling's two AXIOM_TESTS validate the PEP 448
#   `{**base, **overlay}` merge (soundness of its value clauses + caller-domain
#   containment). That merge is exactly the UNCHANGED sub-computation this
#   carrier folds into the free input `combined` (mapping.md §3: no axiom is
#   owed, `axiom_check.py` is a skip stub), so there is no axiom to probe here.
#   This gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
