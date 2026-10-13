"""properties.py — G-PBT falsification battery for django__django-15128 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides — so ``markers.same_spec``
holds and the ``prove_correct buildRelabeling`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the subject impl).

DEFENDED SURFACE (one contracted method over an ordered sequence of input
strings, a fresh prefix, and a set of strings to leave out):

  buildRelabeling (aliases newPrefix preserved) return (out)
      ensures out = relabeling newPrefix preserved aliases

The method builds the relabeling sequence handed onward: every input string
paired with a fresh name formed from ``newPrefix`` and the string's ORIGINAL
position, EXCEPT the strings listed in ``preserved``, which contribute no pair.
The position counter advances for EVERY string — including the ones left out —
so omitting a preserved string never shifts the names assigned to the others.
The sole load-bearing postcondition clause is
``out = relabeling newPrefix preserved aliases``, a front-recursive fold
(``relabelFrom``) that is a total, fully-unfolded pure function of the method's
three arguments.

The three INPUT binders are all free (no ``require`` clause anywhere), so the
admitted domain is total:
  * ``aliases``   — the ordered input strings; only their LENGTH, ORDER and
                    membership-in-``preserved`` drive the emitted shape;
  * ``newPrefix`` — the fresh prefix each emitted name is formed from;
  * ``preserved`` — the strings to leave out (no pair emitted, but the position
                    counter still advances past them).
The post-image must hold for EVERY value of each, which is what makes the
partial-domain rivals below genuinely refutable at concrete points.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling class is
    MANDATORY there because ``aliases`` carries a fractional heap permission an
    impl can overwrite (the sibling's headline probe writes to the input list to
    trivialise the postcondition, and is rejected for INSUFFICIENT PERMISSION).
    Lean and Velvet are referentially transparent: every parameter is an
    immutable value, this bundle declares no ``mut`` PARAMETER, there is no heap
    and no aliasing — so there is no read-only input to mutate and no substitute
    probe to fabricate. Not faked (per the porting map, this class is
    legitimately dropped here rather than replaced).
  * DIVERGENCE / NON-TERMINATION - no sibling case to port, and CLOSED BY THE
    SEMANTICS rather than left open. Under this bundle's
    ``set_option loom.semantics.termination "total"`` a postcondition is claimed of
    ALL runs, not only terminating ones, and the verifier demands a decreasing
    measure on every loop; the frozen loop carries ``decreasing i``. That option and
    the file's ``open TotalCorrectness DemonicChoice`` cannot disagree, because the
    ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``).
    Measured on THIS bundle rather than inherited from a corpus table, proof reduced
    to a bare ``loom_solve``: a spliced spun loop with no ``decreasing`` clause is
    refused at elaboration (``Decreasing annotations are required in total
    correctness semantics``), and the sharper shape that CARRIES a measure which
    does not decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q`` with body ``q := q``) is REJECTED on the measure's own goal -
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. The second shape is the one
    that matters: it cannot be dismissed as merely missing an annotation.
    So a diverging rival does NOT satisfy this spec: no known hole to record, and no
    reject case is owed. (An earlier revision of this bullet reached the same
    disposition by citing an internal findings doc and a census of a ``partial``
    majority of velvet bundles against a ``total`` minority. That
    census is withdrawn: all 500 velvet bundles now set ``"total"`` and open
    ``TotalCorrectness``, so there is no split to be on a side of, and the
    conclusion here rests on the builds above instead.)
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``relabeling`` is a total,
    fully-unfolded function of the method's own arguments (a concrete ``def`` in
    the ``pure`` region; the ``axioms`` region is empty — no opaque answer key
    to echo). The unique satisfier IS the positional fold. The sibling reaches
    the same conclusion ("fresh_alias is grounded, no wrong echo to build") and
    ships a cheapest-impl positive control plus partial-domain rivals in its
    place; so do we (the ``pos-*`` reshapes).
  * PARTIAL-DOMAIN / VALUE — the real attacks, all against the single ensures:
      - the exclude filter dropped, so a preserved string is wrongly relabeled
        (attacks the ``preserved`` binder over the whole sequence);
      - the first position special-cased, so the leading string is relabeled
        even when preserved (attacks ``preserved`` at the head — the sub-domain
        the failing scenario lives in);
      - the position counter collapsed to a constant, so distinct strings
        collapse onto ONE emitted name (attacks the per-position value / the
        injectivity of the emitted names);
      - the position counter RENUMBERED over the emitted strings only, so an
        omission shifts every later name (attacks the one invariant mapping.md
        §2 calls load-bearing: emission is filtered, numbering is not);
      - the membership guard inverted, so ONLY preserved strings are emitted
        (attacks ``preserved`` with the opposite polarity).

WITNESS MECHANICS ON THIS BUNDLE — and the correction of an earlier port.
The spec is a ``method`` CONTRACT, not a bare predicate, so a witness reaches it
through Velvet's tester machinery: ``buildRelabelingTester args = false`` says
the extracted program's result violates the postcondition at that concrete
input. Every witness here states its refutation at LITERAL inputs (no
hypothesis binders), so no consistency probe is in play and none CAN be
inconsistent.

The frozen impl is a backward ``while`` loop. Under
``loom.semantics.choice "demonic"`` its extracted program elaborates through
``Classical.choice``, which the kernel cannot unfold, so ``decide`` against the
FROZEN tester is stuck for every claim, true or false. A previous revision of
this battery read that stuck build as the "fails on gold" half of the
discriminator and shipped four rivals on it. That was wrong, and the gate caught
it: all four recorded ``witness-undecided`` and the cell came back
MALFORMED-TESTS. The exit code carried no information, so a forged witness
asserting a rival CORRECT would have cleared both halves equally.

The repair is the documented one: every reject case names a ``witness_reference``
— ``_LOOPFREE`` below, a loop-free variant that computes the same value by
direct recursion. The gate independently checks it shares the frozen spec and
VERIFIES before refuting any witness against it, and an impl the verifier
accepts cannot violate its own spec, so a genuine witness must still fail there.
Measured out-of-band with ``scripts/lean_verify.sh``, all five rivals now
discriminate on BOTH halves for the right reason:
  * against the rival: exit 0 (the witness elaborates);
  * against ``_LOOPFREE``: exit 1 with ``Tactic `decide` proved that the
    proposition ... is false`` — a genuine REFUTATION, not the
    ``did not reduce to `isTrue` or `isFalse``` stuck reduction the frozen loop
    produced. That message difference is the whole substance of the fix.
``_LOOPFREE`` also ships as the ``pos-loopfree-direct`` positive, so the battery
itself records that loop-freeness is not what any rival is being rejected for.

AXIOM lane: EMPTY. ``meta.json`` declares no ``axiom`` and no A-reference deep
model (the modeled op is self-contained over its three inputs), so there is
nothing for the axiom lane to probe and the gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15128"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region, verbatim — everything between the method's
# `-- impl-start` / `-- impl-end`, INCLUDING the backward `while` loop and its
# invariants. Every rival and reshape edits ONLY this block (and, for the
# admissibility case, the elided `prove_correct` tactic body), so the spec view
# is untouched and same_spec holds by construction.
_IMPL = """\
    -- impl-start
    let mut result : List (String × String) := []
    let mut i := aliases.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ aliases.length
      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)
      done_with i = 0
      decreasing i
    do
      let a := aliases[i - 1]!
      result := (if preserved.contains a then []
                 else [(a, newPrefix ++ toString (i - 1))]) ++ result
      i := i - 1
    return result
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen impl OPENING line — a unique anchor for inserting an in-region
# assert (admissibility) without disturbing anything else.
_IMPL_OPEN = "    -- impl-start\n    let mut result : List (String × String) := []\n"
assert _BASE.count(_IMPL_OPEN) == 1, "impl opening drifted"

# The frozen proof, verbatim. Rivals leave it as-is (the rejection is carried by
# the witness, not the tactic script). The admissibility reshape adds an assert
# VC, so it retunes THIS block (elided from the spec view) to a form that also
# discharges a `decide`-able assert.
_PROOF = """\
prove_correct buildRelabeling by
  loom_solve
  all_goals (
    try (rw [relabelFrom_drop_step aliases newPrefix preserved i (by omega) (by omega)])
    try (obtain ⟨hi0, hr⟩ := i_2)
    simp_all [relabeling])"""
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# A proof script robust to an added in-region assert VC: discharge the loop step
# where present, otherwise close the assert VC by computation.
_PROOF_RETUNED = """\
prove_correct buildRelabeling by
  loom_solve <;>
    (try (rw [relabelFrom_drop_step aliases newPrefix preserved i (by omega) (by omega)])) <;>
    (try (obtain ⟨hi0, hr⟩ := i_2)) <;>
    (first | decide | simp_all [relabeling])"""


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region replaced."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + new_body + "\n    -- impl-end")


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE. A loop-free, CORRECT impl of the frozen spec: the same
# value the backward loop accumulates, computed directly by the pure region's own
# front-recursion. It exists because the frozen `while` loop cannot serve as the
# second half of the discrimination check — under demonic choice its extracted
# program goes through `Classical.choice`, which the kernel cannot unfold, so
# `decide` against it is stuck for EVERY claim and its exit code discriminates
# nothing (the gate reports `witness-undecided`; see the module docstring).
#
# This one DOES reduce, so refuting a witness against it is real evidence. The
# gate checks it shares the frozen spec and VERIFIES before trusting it (an impl
# that failed everything would refute every witness, honest or forged); measured
# verifying out-of-band with scripts/lean_verify.sh, and it also ships below as
# the `pos-loopfree-direct` positive so the battery itself records that
# loop-freeness is not the grounds for any rejection.
# ---------------------------------------------------------------------------
_LOOPFREE = _impl(
    "    let out := relabelFrom newPrefix preserved 0 aliases\n"
    "    return out")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `buildRelabelingTester args = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
_TESTER = ("extract_program_for buildRelabeling\n"
           "prove_precondition_decidable_for buildRelabeling\n"
           "prove_postcondition_decidable_for buildRelabeling\n"
           "derive_tester_for buildRelabeling\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG. The first two keep the backward `while` loop and
    # the gold front-recursive invariant, so the reproof stays exactly the frozen
    # script (no retune needed); the third drops the loop entirely.
    # =====================================================================
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the omission guard and swap the two arms — emit the
        # pair when the string is NOT preserved, else nothing. Same set of pairs
        # on both arms; observationally `relabeling newPrefix preserved aliases`.
        "module": _impl(
            "    let mut result : List (String × String) := []\n"
            "    let mut i := aliases.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ aliases.length\n"
            "      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let a := aliases[i - 1]!\n"
            "      result := (if !(preserved.contains a) then [(a, newPrefix ++ toString (i - 1))]\n"
            "                 else []) ++ result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": "negating the omission guard and swapping the branches emits "
                     "the same pair set on both arms, so "
                     "`out = relabeling newPrefix preserved aliases` still holds; "
                     "a correct reshape must verify, else SPEC-TOO-STRONG on "
                     "branch order.",
    },
    {
        "id": "pos-entry-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-position emission to a typed local before
        # prepending, instead of the inline `if`. Same value flow; the invariant
        # is unchanged, so the frozen proof still closes.
        "module": _impl(
            "    let mut result : List (String × String) := []\n"
            "    let mut i := aliases.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ aliases.length\n"
            "      invariant result = relabelFrom newPrefix preserved i (aliases.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let a := aliases[i - 1]!\n"
            "      let entry : List (String × String) :=\n"
            "        if preserved.contains a then [] else [(a, newPrefix ++ toString (i - 1))]\n"
            "      result := entry ++ result\n"
            "      i := i - 1\n"
            "    return result"),
        "rationale": "binding the per-position emission to a typed local before "
                     "prepending computes the same pairs every iteration, so the "
                     "ensures is unchanged; must verify (else SPEC-TOO-STRONG on "
                     "the local-binding shape).",
    },
    {
        "id": "pos-loopfree-direct",
        "kind": "soundness",
        "expect": "verify",
        # The SAME source every reject case names as its `witness_reference`.
        # Shipped as a case in its own right so the battery records, on the
        # record, that this impl VERIFIES — i.e. that loop-freeness is not what
        # any rival is being rejected for, and that the subject the rivals are
        # refuted against is a genuine satisfier of the frozen spec rather than
        # just another wrong impl (which would refute every witness).
        "module": _LOOPFREE,
        "rationale": "the value the backward loop accumulates, computed directly "
                     "by the pure region's own front-recursion with no loop and "
                     "no invariant: a maximally different CONTROL FLOW that is "
                     "still observationally `relabeling newPrefix preserved "
                     "aliases`, so it must verify (else SPEC-TOO-STRONG on the "
                     "loop shape). Doubles as the reject lane's "
                     "`witness_reference`, and the gate re-checks it verifies "
                     "before refuting any witness against it.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause, so no F2P-shaped
    # input is excluded; the usual "a normal input satisfies the precondition"
    # probe is vacuously satisfied. The residual admissibility risk on a total
    # domain is that the post-image is DEGENERATE at the interesting point — a
    # spec no impl can meet reads exactly like one every impl meets. This case
    # discharges an in-region `assert` pinning the post-image at two F2P-shaped
    # points: a preserved leading string is left out AND the later string keeps
    # the position the preserved one still consumed (so the omission does not
    # shift it); and a lone non-preserved string is relabeled at position 0. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live (a false claim about the same points leaves
    # an unsolved goal — checked out-of-band).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_OPEN,
                  "    -- impl-start\n"
                  "    assert (with_name_prefix `assert\n"
                  "      (relabeling \"T\" [\"a\"] [\"a\", \"b\"] = [(\"b\", \"T1\")] ∧\n"
                  "       relabeling \"T\" [] [\"a\"] = [(\"a\", \"T0\")]))\n"
                  "    let mut result : List (String × String) := []\n"),
            _PROOF, _PROOF_RETUNED),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: for a preserved leading string it emits "
                     "NO pair for that string yet keeps the later string at the "
                     "position the omitted one still consumed (T1, not T0), and "
                     "for a lone non-preserved string it emits the pair at "
                     "position 0. The in-region assert must discharge (else the "
                     "obligation is unsatisfiable / PRECOND-TOO-STRONG); the impl "
                     "is kept verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a straight-line COMPUTABLE impl (so its
    # witness reduces under `decide`), refuted at a concrete input by a witness
    # checked against the loop-free `_LOOPFREE` reference — the frozen loop
    # cannot decide anything, so it is not a usable subject (see the module
    # docstring). Each carries the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-no-exclude",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour: relabel EVERY string, holding nothing back —
        # `preserved` is ignored entirely.
        "module": _impl(
            "    let out := aliases.mapIdx (fun pos a => (a, newPrefix ++ toString pos))\n"
            "    return out"),
        "refinement": "relabeling every string with none held back re-maps the "
                      "shared base string too, so combining the two sides "
                      "re-introduces the conflicting rename the issue reports "
                      "(a rename whose sources and targets overlap); the "
                      "consumer's disjointness assertion then fires and the "
                      "combined query raises, so the failing commutativity test "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = relabeling newPrefix preserved aliases`: "
                     "a preserved string must contribute NO pair, and this impl "
                     "emits one for it. Refuted with a preserved leading string "
                     "in a two-string sequence (`preserved = [\"a\"]`).",
        "witness": _witness('buildRelabelingTester ["a", "b"] "T" ["a"]'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-first-position-relabeled",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct for every position >= 1 but special-cases position 0 to ALWAYS
        # emit a pair, regardless of whether the leading string is preserved.
        # The leading string is exactly the one the failing scenario preserves.
        "module": _impl(
            "    let out := (aliases.mapIdx (fun pos a =>\n"
            "        if pos = 0 then [(a, newPrefix ++ toString pos)]\n"
            "        else if preserved.contains a then [] else [(a, newPrefix ++ toString pos)])).flatten\n"
            "    return out"),
        "refinement": "the string that must be held back is the leading one, so a "
                      "counterpart that always relabels the first position re-maps "
                      "exactly that shared string, re-creating the overlapping "
                      "rename the fix is meant to avoid; the combined query still "
                      "raises. It diverges on the very sub-domain the bug lives "
                      "in, so it would NOT resolve.",
        "rationale": "REJECT from `out = relabeling newPrefix preserved aliases`: "
                     "when the leading string is preserved the impl emits a pair "
                     "for it where the post-image demands none. Refuted at a "
                     "preserved LEADING string (`preserved = [\"p\"]`), the head "
                     "sub-domain no other rival probes, and with a distinct "
                     "prefix and length-3 sequence so those binders move too.",
        "witness": _witness('buildRelabelingTester ["p", "q", "r"] "U" ["p"]'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-collapsed-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Non-injective: the emitted name always uses position 0, so distinct
        # strings collapse onto ONE fresh name. Honours the omission filter, so
        # this is refuted purely on the per-position VALUE, not the exclusion.
        "module": _impl(
            "    let out := (aliases.mapIdx (fun pos a =>\n"
            "        if preserved.contains a then [] else [(a, newPrefix ++ toString 0)])).flatten\n"
            "    return out"),
        "refinement": "a counterpart whose fresh name ignores the position "
                      "counter maps every string to the SAME new name, silently "
                      "merging distinct joins; the two combine orders then no "
                      "longer yield the same rows — the failing test's exact "
                      "observation. It would NOT resolve.",
        "rationale": "REJECT from `out = relabeling newPrefix preserved aliases`: "
                     "each emitted name is `newPrefix ++ toString pos` and must "
                     "differ by position, but this impl pins them all to position "
                     "0. Refuted with an EMPTY `preserved` (nothing held back) so "
                     "the divergence is isolated to the per-position value, and "
                     "with a further distinct prefix.",
        "witness": _witness('buildRelabelingTester ["c", "d"] "N" []'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-renumbered-after-omission",
        "kind": "uniqueness",
        "expect": "reject",
        # The SHARPEST near-miss, and the one closest to a plausible real
        # counterpart: filter FIRST, then number the survivors 0,1,2,... So the
        # omission filter is honoured exactly (a preserved string contributes no
        # pair, the right polarity, at every position) and the emitted names are
        # all distinct — every other rival's failure mode is absent. It is wrong
        # only in that an omitted string no longer CONSUMES its position, so
        # every later name shifts down by one. Agrees with the post-image
        # whenever nothing is held back, which is why it needs its own witness
        # at an input where an omission is followed by a survivor.
        "module": _impl(
            "    let kept := aliases.filter (fun a => !preserved.contains a)\n"
            "    let out := kept.mapIdx (fun pos a => (a, newPrefix ++ toString pos))\n"
            "    return out"),
        "refinement": "numbering only the emitted strings makes the fresh name of "
                      "every string AFTER a held-back one differ from the name the "
                      "unfiltered numbering gives it. The rename is then computed "
                      "against names the other side never agreed on, so the two "
                      "combine orders again disagree on the rows they yield, and "
                      "the failing commutativity test still fails. Worse, shifting "
                      "the numbering down by one is exactly what re-opens the "
                      "possibility of a rename whose sources and targets overlap "
                      "— the condition the consumer's disjointness assertion "
                      "fires on. It would NOT resolve.",
        "rationale": "REJECT from `out = relabeling newPrefix preserved aliases`: "
                     "the position counter advances for EVERY input string, "
                     "including the ones left out, so a preserved string still "
                     "consumes its index. This impl renumbers the survivors "
                     "densely instead. It gets the omission FILTER and name "
                     "distinctness right, so it is refutable only where an "
                     "omission is followed by a survivor — refuted at a preserved "
                     "MIDDLE string (`[\"k\",\"l\",\"m\"]`, `preserved=[\"l\"]`, "
                     "prefix \"V\"), a third `preserved` shape (interior, not "
                     "head and not empty) and an input point no other rival "
                     "probes. It attacks the numbering/emission independence "
                     "mapping.md §2 calls the subtle load-bearing invariant, "
                     "which no other rival isolates.",
        "witness": _witness('buildRelabelingTester ["k", "l", "m"] "V" ["l"]'),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-inverted-membership",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: the membership guard is inverted, so ONLY the
        # preserved strings are emitted and every other string is dropped — wrong
        # with the opposite polarity to weak-no-exclude.
        "module": _impl(
            "    let out := (aliases.mapIdx (fun pos a =>\n"
            "        if preserved.contains a then [(a, newPrefix ++ toString pos)] else [])).flatten\n"
            "    return out"),
        "refinement": "a counterpart with an inverted membership guard relabels "
                      "ONLY the base string and leaves every conflicting string "
                      "unchanged, so the combine never disambiguates them and the "
                      "failing test still observes the mismatch. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = relabeling newPrefix preserved aliases`: "
                     "a non-preserved string must contribute a pair and a "
                     "preserved one must not — the inverted guard gets BOTH "
                     "polarities wrong. Refuted with a preserved leading string "
                     "in a two-string sequence and yet another distinct prefix, "
                     "so this rival's input differs from the others.",
        "witness": _witness('buildRelabelingTester ["m", "n"] "X" ["m"]'),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals — one of them the MANDATORY
# frame-mutation probe). Every one is accounted for below. The sibling contracts
# ONE function, build_relabel_map, over a permission-bearing read-only list; this
# bundle contracts the same construction as one purely-functional method,
# buildRelabeling. The value surface carries across intact; the permission
# surface does not exist here.
#
#   sibling case                          -> here                          disposition
#   -----------------------------------------------------------------------------
#   pos-control-branch-reorder            -> pos-negated-guard              PORTED
#                                            (+ pos-entry-local             ADDED)
#                                            (+ pos-loopfree-direct         ADDED)
#   admiss-read-input                     -> admiss-nondegenerate           RE-AIMED
#   frame-mutation-overwrite-input        -> (none)                         VACUOUS
#   partial-domain-prepatch-no-exclude    -> weak-no-exclude                PORTED
#   partial-domain-firstpos-flag          -> weak-first-position-relabeled  PORTED
#   partial-domain-noninjective-collapse  -> weak-collapsed-position        PORTED
#   support-inverted-flag                 -> weak-inverted-membership       PORTED
#   (no sibling counterpart)              -> weak-renumbered-after-omission ADDED
#
# 5 ported, 1 re-aimed, 1 vacuous; 2 positive controls + 1 rival added.
#
# PORTED (the four uniqueness rivals): each sibling rival attacks a postcondition
#   clause that survives on this carrier, so its ARGUMENT ports directly and only
#   the mechanics change. The sibling's A6 biconditional (a per-position source
#   FLAG) and A4b per-ordinal value pin are both folded here into the single
#   `out = relabeling …` ensures: A6's "a preserved string is left out" becomes
#   "a preserved string contributes no pair" (weak-no-exclude, weak-first-
#   position-relabeled, weak-inverted-membership), and A4b's per-ordinal value
#   becomes "the emitted name is `newPrefix ++ toString pos`" (weak-collapsed-
#   position). The sibling rewrites its loop INVARIANT to the rival's own shape
#   to keep Viper from stalling on a stale invariant; that concern is absent here
#   because each rival is a straight-line COMPUTABLE impl (no loop, no invariant)
#   whose rejection is carried by a machine-checked witness rather than by the
#   verifier's failure to re-prove a reshaped loop.
# ADDED (3): pos-entry-local — a second correct reshape (per-position emission
#   bound to a typed local). pos-loopfree-direct — a third, maximally different
#   control flow (no loop at all), which is ALSO the reject lane's
#   witness_reference, shipped as a case so the record shows it verifies.
#   weak-renumbered-after-omission — a rival with NO sibling counterpart, because
#   nagini's carrier cannot express it: there, emission is a separate is_source
#   FLAG list parallel to a target list numbered by its own index, so "the filter
#   shifts the numbering" is not a reachable corruption. Here emission and
#   numbering share one traversal, so a filter-then-number impl is both writable
#   and the sharpest near-miss in the battery — it is correct on the entire
#   sub-domain where nothing is held back, and mapping.md §2 names precisely this
#   independence ("the filter decides only *emission*, not *numbering*") as the
#   subtle invariant the bijection preserves. Carrier narrowing usually REMOVES
#   cases; this is the rarer converse, and it closes the clause that would
#   otherwise be attacked by no rival.
# RE-AIMED (admissibility): the sibling establishes that the read-only grant and
#   the well-formedness facts of the PRECONDITION are usable for an F2P-shaped
#   input. This bundle has NO precondition (no `require`), so that probe is
#   vacuous — nothing could exclude a normal input. It is re-aimed at the
#   residual total-domain risk — that the post-image is DEGENERATE at the
#   interesting point — via an in-region assert that the ensures leaves a
#   preserved leading string out while keeping the later string at the position
#   the omitted one still consumed (the subtle invariant the fix turns on), and
#   relabels a lone non-preserved string at position 0.
# VACUOUS (frame-mutation-overwrite-input): the sibling's MANDATORY frame probe
#   overwrites the read-only input list to trivialise the postcondition, and is
#   rejected for INSUFFICIENT PERMISSION (only a fractional grant is held). This
#   backend is referentially transparent: every parameter is an immutable value,
#   this bundle declares no `mut` parameter, there is no heap and no aliasing.
#   There is no read-only input to overwrite and no permission system to trip, so
#   the class is vacuous. No substitute is fabricated (per the porting map, this
#   class is legitimately dropped here rather than replaced).
# NOT OWED (divergence): the sibling carries no diverge-*/nonterm-* case, and the
#   class is CLOSED BY THE SEMANTICS here. This bundle sets termination "total" with
#   `decreasing i` on the frozen loop; under "total" a postcondition is claimed of
#   ALL runs and every loop must carry a decreasing measure. Measured on this bundle:
#   an unmeasured spun loop is refused at elaboration (`Decreasing annotations are
#   required in total correctness semantics`), and a loop carrying a NON-decreasing
#   measure (`while q > 0 ... decreasing q`, body `q := q`) is rejected on the
#   measure's own goal -- `case «decreasing_1: q»`, residual `q < q`. Nothing to port
#   and no hole to record. (The earlier version of this note reached the same
#   disposition by citing an internal findings doc and a corpus census splitting
#   the bundles between `partial` and `total`; both are withdrawn, since all 500
#   velvet bundles read "total".)
#
# WITNESS NOTE (backend-specific, no sibling counterpart) — and the record of a
#   corrected error. The frozen impl is a backward `while` loop; under demonic
#   choice its extracted program elaborates through `Classical.choice`, which the
#   kernel cannot unfold, so `decide` on the FROZEN tester is stuck for every
#   claim regardless of truth. A previous revision of this battery treated that
#   stuck build as the "fails on gold" half of the discriminator; the gate
#   correctly refused all four rivals as `witness-undecided` and recorded
#   MALFORMED-TESTS. It was right to: the frozen-side exit code carried no
#   information, so a witness asserting a rival CORRECT would have passed too.
#   Every reject case now names `witness_reference=_LOOPFREE`, a loop-free
#   variant that computes the same value by direct recursion, VERIFIES (checked
#   by the gate before use, and shipped as pos-loopfree-direct), and actually
#   REDUCES. Confirmed out-of-band with scripts/lean_verify.sh, ten builds: each
#   of the five witnesses elaborates against its rival (exit 0) and fails against
#   _LOOPFREE with "Tactic `decide` proved that the proposition ... is false" —
#   a real refutation, versus the "did not reduce to `isTrue` or `isFalse`" the
#   frozen loop produced. The message difference is the evidence.
#
# BINDER / DOMAIN COVERAGE of the reject witnesses over the three input binders
#   of the sole ensures (pts=5, five DISTINCT input points):
#     aliases    — length 2 (weak-no-exclude, weak-collapsed-position,
#                  weak-inverted-membership) and length 3 (weak-first-position-
#                  relabeled, weak-renumbered-after-omission); order and content
#                  vary across all five.
#     preserved  — a preserved LEADING string (weak-no-exclude ["a"],
#                  weak-first-position-relabeled ["p"], weak-inverted-membership
#                  ["m"]), a preserved INTERIOR string (weak-renumbered-after-
#                  omission ["l"], the only point where an omission is FOLLOWED
#                  by a survivor), and EMPTY (weak-collapsed-position []). So all
#                  three structurally distinct shapes are probed — nothing held
#                  back, held back at the head, held back mid-sequence.
#     newPrefix  — "T", "U", "N", "X", "V": moves across all five rivals, never
#                  held fixed.
#   The single ensures is attacked from five independent angles — omission of a
#   preserved string, omission at the load-bearing head position, the
#   per-position emitted VALUE (injectivity), the independence of NUMBERING from
#   emission, and the inverted membership polarity.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model, so there is nothing there to probe; the
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
