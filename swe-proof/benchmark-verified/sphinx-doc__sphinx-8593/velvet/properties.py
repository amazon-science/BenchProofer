"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8593 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps RESULT onto. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is edited — both of which the consumer spec view elides, so
``markers.same_spec`` holds by construction and the ``prove_correct
collectMemberDocs`` header survives). ``expect="verify"`` passes iff (in scope
AND verifies); ``expect="reject"`` passes iff (in scope AND does NOT verify AND
its refutation ``witness`` discriminates: elaborates against the rival, fails
against the witness's declared subject — here a ``witness_reference``, the correct
loop-free forward map, rather than the frozen solution; see THE THREE BUILDS).

DEFENDED SURFACE (one contracted method, one obligation):

  collectMemberDocs (attrDocs : List (Int × List (List Int))) (names : List Int)
      return (out : List MemberDoc)
    ensures out = buildMembers attrDocs names

ONE load-bearing clause, E1, pinning the WHOLE result to a deep, fully-unfolded
pure model over the method's own two inputs. The ``axioms`` region is empty:
there is no opaque answer key to echo, so an impl that satisfies E1 has done the
modeled work. E1 decomposes into four independently-attackable facts, and the
reject lane below attacks each:

  (a) LENGTH/PRESENCE — one entry per presented name, none dropped, none added;
  (b) ORDER — the entries appear in the order the names are presented;
  (c) ASSOCIATION — entry *i* carries the text recorded for ITS OWN name, not a
      neighbour's and not the table's first row;
  (d) ASSEMBLY — that text is the recorded lines joined by a single break each,
      and empty exactly when no lines are recorded.

TWO INPUT BINDERS: ``attrDocs`` (the per-name line table — which names have
recorded lines, and what those lines are) and ``names`` (the candidate roster,
its length and its order).

CARRIER NOTE — WHY THE WITNESSES GO THROUGH ``…Exec`` AND NOT THE TESTER. The
sibling velvet bundles reach the post-image via ``derive_tester_for`` and close
with ``decide``. THAT PATH IS DEAD HERE, and not for a decidability reason: the
postcondition IS decidable (``MemberDoc`` derives ``DecidableEq``) and
``derive_tester_for`` emits a computable ``collectMemberDocsTester`` — ``#eval``
returns ``true`` on it. But the frozen impl is a ``while`` loop, so the extracted
``collectMemberDocsExec`` is well-founded recursion that the KERNEL declines to
reduce, and ``decide`` gets stuck at the ``Decidable`` instance for BOTH gold and
any rival. Measured: ``decide``, ``decide +kernel``, ``rfl``,
``with_unfolding_all rfl/decide``, and ``simp [NonDetT.run, Lean.Loop.forIn]``
all fail on gold's tester; ``simp`` leaves the raw ``forIn Lean.Loop.mk`` term
with its ``invariantGadget``/``onDoneGadget`` gadgets intact.

A ``decide``-closed witness is therefore NOT usable here, and the gate says so
explicitly rather than accepting it: measured, a ``decide`` witness elaborates
against a loop-free rival and fails on gold with "reduction got stuck at
``.hasDecEq``", which the gate classifies as ``witness-undecided`` — the same
error would appear for a TRUE claim about the frozen impl, so it attests to a
refutation that was never performed. That is exactly the second failure mode this
battery is required to avoid, and the first authored draft of this file hit it on
all five rivals.

What replaces it is REDUCTION BY ``simp``, over a carrier that is fully
transparent (no opaque callee anywhere in E1; ``MemberDoc`` derives
``DecidableEq``). Each rival is written LOOP-FREE (a ``List.map`` / ``match`` /
``filter``), so ITS ``collectMemberDocsExec`` unfolds and computes under ``simp``
with the model's own defs. Each witness states, at one concrete input,

    extract_program_for collectMemberDocs

    example : collectMemberDocsExec <attrDocs> <names>
        ≠ DivM.res (buildMembers <attrDocs> <names>) := by
      unfold collectMemberDocsExec collectMemberDocs
      simp [NonDetT.run, pure, buildMembers, lookupDocs, joinNL, List.map]

i.e. the rival's own extracted result DIFFERS from the transparent post-image E1
demands — a direct E1 violation, reduced on both sides to concrete list literals
and closed by their literal disequality. No witness binds any hypothesis (every
input is a concrete literal), so no consistency probe applies and no assumption
can be inconsistent. No banned token (sorry/admit/native_decide/axiom/opaque).

THE THREE BUILDS BEHIND EVERY REJECT CASE, AND WHY THE THIRD IS THE GATE'S.
The gate runs two builds per reject case: the witness must elaborate against the
RIVAL and fail against a SUBJECT. Taking GOLD as that subject is not enough here,
and this was measured rather than argued. Gold's ``…Exec`` is the ``while`` loop's
well-founded fixpoint, and ``simp`` leaves it as a raw ``forIn Lean.Loop.mk`` term
with its ``invariantGadget``/``onDoneGadget``/``decreasingGadget`` intact (present
in all five gold logs), so the residual goal is an unreduced ``¬(NonDetT.run … =
DivM.res …)``. That build fails for EVERY claim about gold, true or false, so read
alone it discriminates LOOP-FREE from LOOPING, not WRONG from RIGHT.

The forgery this admits was built and run: take any witness below and replace
``≠`` by ``=`` — asserting the rival is CORRECT at an agreement point, the exact
OPPOSITE of a refutation — at ``attrDocs = []``, ``names = [1]``, where the
doc-dropping rival and the model agree. Measured RIVAL exit 0, GOLD exit 1 with
the same unreduced residual. Both gold-side halves cleared by a statement that
refutes nothing. The gate's own ``witness-undecided`` screen does not catch it
either: that screen matches stuck-``decide``/dependent-elimination messages, and
these logs say ``unsolved goals`` instead — checked directly against
``swebench_unified.gates.pbt._stuck``, which returns False on all five gold logs.

So every reject case carries a ``witness_reference``: the CORRECT loop-free forward
map, which the GATE (not this prose) refutes each witness against, having first
independently checked that the reference shares the frozen spec AND verifies. There
``simp`` reduces BOTH sides completely; measured, all five honest witnesses fail
with ``⊢ False`` — their claim refuted by a correct impl — while the ``=`` forgery
above ELABORATES against it (exit 0), which the gate records as ``witness-vacuous``
and refuses. That is the discrimination the gold build could not supply. The same
impl is also shipped as the ``pos-control-forward-map`` positive, from one shared
source (``_REF_FORWARD_MAP``) so the two cannot drift apart.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY, and carry the sibling's TWO reshape
    positives. The sibling's ``med-pos-reorder`` (invert the guard) and
    ``med-pos-locals`` (bind the chosen source to a local, copy once) are both
    per-element reshapes of a selection; here they become a direct return of the
    grounded model, a loop-preserving ``let``-naming, and a forward ``List.map``
    with a fresh inductive reproof. All three verify.
  * ADMISSIBILITY — the sibling asserts a tautology to show its
    fractional-permission precondition admits an F2P-shaped input. This method
    has NO ``require`` clause and no permission surface, so that probe is
    degenerate; RE-AIMED at the sharper residual risk, a DEGENERATE post-image.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend, per the porting map.
    The sibling's THREE MANDATORY frame rivals (``med-frame-mut-attr``,
    ``med-frame-mut-value``, ``kmm-frame-mut-attr``) write a half-permission
    read-only input and are rejected for INSUFFICIENT PERMISSION. Lean/Velvet are
    referentially transparent: ``attrDocs`` and ``names`` are immutable values
    declared read-only (not ``mut``), there is no heap, no aliasing, no
    fractional permission. There is no read-only input to overwrite and no
    permission clause to trip. NOT ported; fabricating a substitute would test
    nothing.
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, so not a hole, not
    vacuous, and not a battery gap. NB the footer's account of WHY has been
    rewritten twice: this bundle declares `termination "total"` (not `"partial"`,
    as one earlier revision asserted) AND opens `TotalCorrectness` and nothing
    else (contrary to a later revision, which read line 7 as opening
    `PartialCorrectness`). Under that scope a postcondition is claimed of ALL
    runs, the verifier demands a DECREASING measure on every loop, and a
    diverging rival is REJECTED: measure-less, at elaboration; measure-carrying,
    on the measure's own goal (measured on this cell, `⊢ q < q` under
    `case «decreasing_1: q»`). See the footer for both exhibits and the
    retraction.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records: E1 pins the
    result to ``buildMembers`` over the method's own arguments, a fully-unfolded
    ``def``. There is no opaque answer key a wrong impl could echo, and the
    cheapest correct impl computes the assembly honestly (the positives cover
    this).
  * VALUE / PARTIAL-DOMAIN — carries the whole reject lane, one rival per
    independently-attackable fact of E1.

AXIOM_TESTS is empty. The bundle declares no axiom (mapping.md §3/§5: the
collection logic is modeled deeply and validated by G-CONF; ``meta.json
gates.G-AX.status = "skip"``), so the sibling's two ``meta_class`` probes have no
counterpart here. This gate ignores AXIOM_TESTS regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8593"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — each lies WHOLLY inside the impl region (or is the frozen proof
# body) and is unique in the file; both facts asserted at load so the manifest
# breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The whole impl block, markers included. Every reject rival and the direct /
# forward-map positives replace it with a loop-free body.
_IMPL = _BASE[_BASE.index("    -- impl-start"):
              _BASE.index("    -- impl-end") + len("    -- impl-end")]
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift"

# The impl-start marker line — the admissibility case inserts an in-region
# `assert` immediately after it, keeping the whole gold body verbatim.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# The frozen loop body. The loop-preserving positive names the assembled entry
# in a local `let`, leaving the loop, its invariants and the frozen proof intact.
_LOOP_BODY = """      let n := names[i - 1]!
      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop-body anchor drift"

# The frozen proof body (tactic script only; elided from the spec view).
_PROOF = _BASE[_BASE.index("prove_correct collectMemberDocs"):]
assert _BASE.count(_PROOF) == 1, "proof anchor drift"

# A flat proof for a loop-free impl: no loop invariant to peel, so the frozen
# script's backward-fold `rw` steps are not merely unnecessary but ill-typed
# (they name the loop counter `i`, which no longer exists). `loom_solve` alone
# discharges a body that IS the model, and leaves the goal unsolved for every
# reject rival — which is the point.
_PROOF_FLAT = "prove_correct collectMemberDocs by\n  loom_solve\n"


def _impl(body):
    """The frozen file with a loop-free `body` and the flat reproof."""
    return _swap(_swap(_BASE, _IMPL, "    -- impl-start\n" + body + "    -- impl-end"),
                 _PROOF, _PROOF_FLAT)


# The CORRECT loop-free forward map, with the inductive reproof that closes it.
# Shipped twice, deliberately and from one source: as the `pos-control-forward-map`
# positive (so the reader can re-run it from the manifest), and as the
# `witness_reference` of every reject case below — the subject the gate refutes
# each witness against, because the frozen `while` loop cannot serve as one. See
# the witness-builder note for the measured forgery this closes.
_REF_FORWARD_MAP = _swap(
    _swap(_BASE, _IMPL,
          "    -- impl-start\n"
          "    return names.map (fun n =>\n"
          "      { name := n, doc := joinNL (lookupDocs n attrDocs) })\n"
          "    -- impl-end"),
    _PROOF,
    "prove_correct collectMemberDocs by\n"
    "  loom_solve\n"
    "  induction names with\n"
    "  | nil => rfl\n"
    "  | cons hd tl ih => simp [buildMembers_cons, ih]\n")


# ---------------------------------------------------------------------------
# Witness builder. Both the tester path and any `decide`-closed witness are dead
# here — gold's `while` makes `collectMemberDocsExec` a well-founded fixpoint the
# kernel will not evaluate, so `decide` fails on gold by STUCK REDUCTION, which
# the gate rejects as `witness-undecided` (it would attest to a refutation never
# performed). See the CARRIER NOTE.
#
# Instead each witness extracts the executable program and refutes E1 by
# REDUCTION: `unfold` + `simp` over the model's own transparent defs computes the
# loop-free rival's result AND the post-image down to concrete list literals, and
# closes on their literal disequality. Checked in a file whose `prove_correct`
# block has been stripped, so no frozen tactic script can mask the verdict.
#
# Three builds per witness:
#   RIVAL -> exit 0, empty log            (the witness holds of the rival)
#   GOLD  -> exit 1, residual goal is the unreduced `forIn Lean.Loop.mk` term
#            with its invariantGadget/onDoneGadget/decreasingGadget intact
#   CTRL  -> exit 1, residual goal is `⊢ False` against a CORRECT loop-free impl
#            (both sides reduced) — the check that the witness is a real
#            discriminator and not merely true of an irreducible term.
#
# THE THIRD BUILD IS THE GATE'S, NOT A PROSE CLAIM (audit repair). An earlier
# revision of this file ran CTRL out-of-band and reported it here in prose, while
# the gate itself checked the witness against the FROZEN loop. That is not enough,
# and the gap was measured rather than argued:
#
#   * gold's `…Exec` is the `while` loop's well-founded fixpoint, so `simp` leaves
#     a raw `forIn Lean.Loop.mk` term and the gold-side goal is an UNREDUCED
#     `¬(NonDetT.run … = DivM.res …)`. That build fails for every claim about
#     gold, true or false — it discriminates LOOP-FREE from LOOPING, not WRONG
#     from RIGHT.
#   * measured forgery: the witness with `≠` replaced by `=` — i.e. asserting the
#     rival is CORRECT at an agreement point, the exact OPPOSITE of a refutation —
#     was built at `attrDocs = []`, `names = [1]`, where the doc-dropping rival
#     and the model agree. RIVAL exit 0, GOLD exit 1 (same unreduced residual).
#     Both halves the gate checks are cleared by a statement that refutes
#     nothing, and it would have been recorded as `rejected`.
#   * the gate's own `witness-undecided` screen does NOT catch this: it matches on
#     stuck-`decide`/dependent-elimination messages, and these logs say
#     `unsolved goals` instead. Checked directly against
#     `swebench_unified.gates.pbt._stuck`, which returns False on all five gold
#     logs. So nothing mechanical stood between this battery and a hollow SOUND.
#
# The repair is `witness_reference`: every reject case names the CORRECT loop-free
# forward map as the subject of the second build, so the gate re-derives CTRL
# itself (it independently checks the reference shares the frozen spec AND
# verifies, per `_reference_ok`). Against that reference `simp` reduces BOTH
# sides, so the second build carries information: measured, all five honest
# witnesses fail there with `⊢ False` (their claim refuted by a correct impl),
# while the `=` forgery above ELABORATES against it — exit 0, which the gate
# records as `witness-vacuous` and refuses. That is the discrimination the gold
# build could not supply.
# ---------------------------------------------------------------------------

def _witness(attr_docs, names):
    return ("extract_program_for collectMemberDocs\n\n"
            f"example : collectMemberDocsExec {attr_docs} {names}\n"
            f"    ≠ DivM.res (buildMembers {attr_docs} {names}) := by\n"
            "  unfold collectMemberDocsExec collectMemberDocs\n"
            "  simp [NonDetT.run, pure, buildMembers, lookupDocs, joinNL, List.map]\n")


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen impl's shape).
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: report the grounded model directly — no
        # loop, no branch, maximally different from the frozen backward fold.
        # `out` IS `buildMembers attrDocs names`, so E1 holds on the whole
        # domain and the residual goal closes under `loom_solve` alone.
        "module": _impl("    return buildMembers attrDocs names\n"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`buildMembers attrDocs names` directly (no loop, no branch, so the "
            "frozen backward-fold proof steps are dropped and `loom_solve` alone "
            "discharges it). `out` IS that model, so E1 holds at every "
            "(attrDocs, names). If this failed to verify the spec would be "
            "over-fit to the impl shape (SPEC-TOO-STRONG). Doubles as the "
            "no-ungrounded-echo control: `buildMembers` is a fully-unfolded def "
            "over the method's own inputs, not an opaque answer key, so "
            "returning it IS doing the modeled work rather than echoing a "
            "constant. (Sibling: med-pos-reorder / med-pos-locals — a "
            "structurally different correct impl that must verify.)"),
    },
    {
        "id": "pos-control-named-entry",
        "kind": "soundness",
        "expect": "verify",
        # Keeps the whole loop, its two invariants and the FROZEN proof script
        # byte-for-byte; only names the assembled entry in a local `let` before
        # prepending it. Observationally identical at every input, and the
        # minimal-edit counterpart to the direct-model positive above.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let n := names[i - 1]!\n"
            "      let entry : MemberDoc :=\n"
            "        { name := n, doc := joinNL (lookupDocs n attrDocs) }\n"
            "      result := entry :: result\n"
            "      i := i - 1"),
        "rationale": (
            "naming the assembled entry in a local `let entry` before prepending "
            "it folds the same stream with the same step, so E1 still holds on "
            "the whole domain; the loop, both invariants and the frozen proof "
            "script are untouched. A correct reshape INSIDE the frozen loop must "
            "verify, else the postcondition is SPEC-TOO-STRONG. This is the "
            "minimal-edit companion to pos-control-direct-model: together they "
            "defend the obligation from a completely different control shape AND "
            "from a local edit that keeps the frozen tactic script live. "
            "(Sibling: med-pos-locals — bind the chosen source to a typed local, "
            "then assemble once.)"),
    },
    {
        "id": "pos-control-forward-map",
        "kind": "soundness",
        "expect": "verify",
        # A forward per-name map (the frozen impl folds BACKWARD from the end).
        # Correct, and needs a genuinely NEW proof: the frozen drop-step lemma is
        # useless without the loop counter, so the tactic body reproves E1 by
        # induction on `names` using the frozen `buildMembers_cons`. No new
        # lemma, no `sorry` — the reproof closes honestly.
        #
        # This impl is ALSO the `witness_reference` of every reject case below —
        # the subject the GATE refutes each witness against, since the frozen
        # `while` loop cannot serve as one. Against this body `simp` reduces BOTH
        # sides and leaves `⊢ False`: the witness's own claim refuted by a correct
        # impl, which is what shows each witness asserts something true of a wrong
        # impl and FALSE of a right one, rather than merely true of a term the
        # kernel cannot reduce (which is all the gold build establishes). Same
        # source as `_REF_FORWARD_MAP`, so the two can never drift apart.
        "module": _REF_FORWARD_MAP,
        "rationale": (
            "a FORWARD per-name map, where the frozen impl folds BACKWARD from "
            "the end of the roster — the same association and the same order by "
            "a different traversal, so E1 holds at every input. The reproof is "
            "genuinely new (the frozen drop-step lemma is unusable once the loop "
            "counter is gone): induction on `names`, closed with the frozen "
            "`buildMembers_cons`, no added lemma and no `sorry`. Must verify, "
            "else the spec is over-fit to the traversal DIRECTION rather than to "
            "the modeled association. Also the `witness_reference` for the whole "
            "reject lane: every witness below is refuted BY THE GATE against this "
            "body, where both sides reduce and the residual is `⊢ False` — which "
            "is what distinguishes a real discriminator from a statement the "
            "kernel merely cannot reduce. Verifying here is therefore load-bearing "
            "twice over: `_reference_ok` requires it before the reference may be "
            "used at all."),
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling asserts a tautology on each modeled @Pure to
    # show its fractional-permission precondition admits a normal F2P-shaped
    # input. This method has NO `require` clause and no permission surface, so
    # that probe is degenerate here. RE-AIMED at the sharper residual risk: a
    # DEGENERATE post-image. The in-region `assert` pins the post-image at an
    # F2P-shaped input where all four facts of E1 are simultaneously live — a
    # multi-line entry (so the join separator is observable), a name recorded
    # with NO lines, and a name absent from the table — and the impl is kept
    # VERBATIM so the method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      buildMembers [(1, [[65], [66]]), (2, [])] [1, 2, 3] =\n"
                  "          [{ name := 1, doc := [65, 10, 66] },\n"
                  "           { name := 2, doc := [] },\n"
                  "           { name := 3, doc := [] }]))\n"),
            _PROOF,
            "prove_correct collectMemberDocs by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "      | decide\n"
            "      | (rw [buildMembers_drop_step attrDocs names i (by omega) (by omega)];\n"
            "         rw [‹result = buildMembers attrDocs (names.drop i)›])\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at an F2P-shaped "
            "input, with all four facts of E1 live at once: three presented "
            "names produce three entries in the presented order (length + "
            "order); the first carries its own two recorded lines joined by "
            "exactly ONE break code (association + assembly, and the separator "
            "is observable only because the entry is multi-line); the second is "
            "recorded with an EMPTY line list and the third is ABSENT from the "
            "table, both of which must yield empty text — the two ways a member "
            "legitimately carries no documentation. The in-region assert must "
            "discharge, else no input distinguishes the modeled outcomes and the "
            "obligation is degenerate. The impl is kept verbatim so E1 still "
            "verifies through the frozen loop. Checked live during authoring: "
            "perturbing the expected text to `[65, 66]` (dropping the break) "
            "makes the case FAIL, so the assert is load-bearing rather than a "
            "tautology. (Sibling: med-admiss / kmm-admiss, re-aimed from "
            "precondition admissibility to post-image non-degeneracy — this "
            "backend has no `require` clause and no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. One per independently-attackable fact of E1, each
    # with a machine-checked witness at a DISTINCT concrete input, and each with
    # the refinement argument that its faithful real patch would NOT resolve.
    #
    # F2P-OBSERVABILITY WAS CHECKED, NOT ASSUMED. The two F2P tests and the one
    # P2P test observe the collected documentation text through exactly one
    # channel: the downstream retention decision (a collected entry's text is
    # read for its `:meta public:` / `:meta private:` marker, which overrides the
    # leading-underscore default; the RENDERED body text is re-read from the
    # analyzer, not from the collected entry). Each rival below was driven
    # through a transcription of that retention logic on the real fixture — whose
    # real recorded lines are the TWO-line `[':meta public:', '']` and
    # `[':meta private:', '']` — and each changes the kept set on at least one of
    # the three tests. Three further rivals that were built and REJECTED for
    # failing this check are accounted for in the footer.
    # =====================================================================
    {
        "id": "weak-drop-doc",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported behaviour transcribed onto the carrier, and the literal
        # pre-image (Solution_prepatch.lean): each member is collected carrying
        # only its name, and the text recorded for it never travels with it.
        # Attacks fact (d) ASSEMBLY at its extreme — the text is empty for EVERY
        # name, whatever was recorded.
        "module": _impl(
            "    return names.map (fun n => { name := n, doc := [] })\n"),
        "refinement": (
            "this is the pre-change behaviour: a collected member arrives with no "
            "documentation text at all, so the marker recorded against its name "
            "is never available downstream and the retention decision falls back "
            "to the leading-underscore default. Checked on the real fixture: an "
            "underscore-named member marked public is then DROPPED and a "
            "plainly-named member marked private is KEPT — the kept set changes "
            "on BOTH F2P tests (the exact complaint in the issue: the member the "
            "reporter expects to be shown is not shown). Does NOT resolve."),
        "rationale": (
            "REJECT from E1: the spec pins each entry's `doc` to `joinNL "
            "(lookupDocs n attrDocs)`, but this rival returns `[]` for every "
            "name. Verifying would be SPEC-TOO-WEAK — the whole documentation-"
            "attachment behaviour unpinned, which is the one thing the "
            "obligation exists to state. Refuted at the minimal discriminating "
            "input: one name with one recorded line, `attrDocs = [(1, [[65]])]`, "
            "`names = [1]`. (Sibling: med-wrong-always-value / "
            "kmm-wrong-classify-value — the two prepatch reverts, both of which "
            "starve the classifier of the attribute documentation.)"),
        "witness": _witness("[(1, [[65]])]", "[1]"),
        # Refuted BY THE GATE against the CORRECT loop-free forward map, not
        # against the frozen loop: gold's `…Exec` never reduces, so its build
        # fails for every claim and the exit code carries no information (a
        # measured `=` forgery cleared both gold-side halves). See the
        # witness-builder note.
        "witness_reference": _REF_FORWARD_MAP,

    },
    {
        "id": "weak-ignore-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Every entry carries the FIRST table row's text regardless of its own
        # name — the lookup is skipped, not the join. Attacks fact (c)
        # ASSOCIATION: text is attached, and correctly assembled, but to the
        # wrong member. Correct whenever the table has one row whose name is the
        # only presented name, so it is wrong strictly inside the multi-name
        # sub-domain.
        "module": _impl(
            "    return names.map (fun n =>\n"
            "      { name := n, doc := match attrDocs with\n"
            "                          | []          => []\n"
            "                          | (_, v) :: _ => joinNL v })\n"),
        "refinement": (
            "a faithful counterpart that attached the first recorded entry's "
            "text to every collected member would broadcast one member's marker "
            "across all of them. Checked on the real fixture, where the first "
            "recorded name is the private-marked one: every member then reads as "
            "private and the kept set collapses to EMPTY, so the F2P that "
            "expects two members rendered fails outright. Does NOT resolve. "
            "Correct on a single-name roster whose one name heads the table, so "
            "this is a genuine partial-domain break rather than a total one."),
        "rationale": (
            "REJECT from E1 fact (c) ASSOCIATION: the spec pins entry `n`'s text "
            "to the lines recorded for `n` (`lookupDocs n attrDocs`), but this "
            "rival ignores `n` and reads the table's head row. Verifying would "
            "be SPEC-TOO-WEAK — the name-to-text association unpinned, so the "
            "spec would not say the documentation travels with the RIGHT member. "
            "Refuted at `attrDocs = [(1, [[65]]), (2, [[66]])]`, `names = "
            "[2, 1]`: a TWO-row table whose rows carry different text, with the "
            "roster ordered so the head row is not the head name — the point "
            "that makes the lookup KEY load-bearing and is distinct from every "
            "other witness here (it is the only one that moves the `attrDocs` "
            "binder to a multi-row table)."),
        "witness": _witness("[(1, [[65]]), (2, [[66]])]", "[2, 1]"),
        # Refuted BY THE GATE against the CORRECT loop-free forward map, not
        # against the frozen loop: gold's `…Exec` never reduces, so its build
        # fails for every claim and the exit code carries no information (a
        # measured `=` forgery cleared both gold-side halves). See the
        # witness-builder note.
        "witness_reference": _REF_FORWARD_MAP,

    },
    {
        "id": "weak-shift-doc-to-neighbour",
        "kind": "uniqueness",
        "expect": "reject",
        # OFF-BY-ONE in the association: each entry carries the text recorded for
        # the NEXT name in the roster, the last carrying none. The nearest miss
        # in the battery — every name is present, in order, and each text is
        # correctly assembled; only the pairing is shifted by one.
        "module": _impl(
            "    return (match names with\n"
            "            | []      => []\n"
            "            | _ :: ns =>\n"
            "                (List.zip names (ns ++ [0])).map\n"
            "                  (fun p => { name := p.1, doc := joinNL (lookupDocs p.2 attrDocs) }))\n"),
        "refinement": (
            "a faithful counterpart that paired each collected member with the "
            "NEXT candidate's recorded lines would hand every member its "
            "neighbour's marker. Checked on the real fixture: the private-marked "
            "member receives the public marker and is kept while the "
            "public-marked one loses it and is dropped — the kept set changes on "
            "BOTH F2P tests, and in the most damaging way (the wrong member is "
            "published). Does NOT resolve. Its agreement sub-domain is the "
            "SUCCESSOR-AGREEMENT set — the rosters on which every name's own "
            "recorded lines happen to equal its successor's (the last name's "
            "successor being the terminal sentinel `0`), which includes every "
            "roster where NEITHER any presented name NOR `0` is recorded in the "
            "table. Stated exactly rather than approximately: an earlier "
            "revision of this case claimed agreement on 'a single-name roster' "
            "and on 'any roster where no name has recorded lines', and BOTH are "
            "false — at `attrDocs = [(1, [[65]])]`, `names = [1]` the single "
            "entry wrongly loses its own text, and at `attrDocs = [(0, [[99]])]`, "
            "`names = [1, 2]` no PRESENTED name is recorded yet the last entry "
            "wrongly gains the sentinel row's text. Both counterexamples were "
            "enumerated, not argued."),
        "rationale": (
            "REJECT from E1 fact (c) ASSOCIATION, at the near-miss end: length, "
            "order and assembly are all correct and only the pairing is shifted "
            "by one. It gets its own witness rather than sharing "
            "weak-ignore-name's because the two agree with gold on INCOMPARABLE "
            "sub-domains, not because one is strictly nearer: enumerated over "
            "the 2560 points given by rosters of length ≤ 3 over three names "
            "and tables assigning each of those names either nothing, an empty "
            "line list, one line, or two lines, this rival agrees at 784 points "
            "and weak-ignore-name at 880, and NEITHER set contains the other "
            "(352 points where ignore-name agrees and this one does not, 256 "
            "the other way — e.g. `attrDocs = "
            "[(1, [[65]])]`, `names = [1]`, where ignore-name is right and the "
            "shift is wrong). TWO earlier revisions got this wrong and both are "
            "corrected here: the first claimed this rival agrees over strictly "
            "MORE of the domain, and the second reported the counts as "
            "924 / 172 / 216 against the same 2560-point domain. Re-enumerated "
            "independently by the audit (the 2560 total and ignore-name's 880 "
            "reproduce exactly; the shift's three numbers did not), so the "
            "INCOMPARABILITY conclusion stands and only the figures move. "
            "Refuted at `attrDocs = [(4, [[70], "
            "[71]])]`, `names = [3, 4]`: the recorded name sits SECOND in the "
            "roster and its text is multi-line, so the shift is observable in "
            "both entries at once (the first wrongly gains the text, the second "
            "wrongly loses it). Verifying would be SPEC-TOO-WEAK — the spec "
            "would permit a systematic off-by-one in which member owns which "
            "documentation."),
        "witness": _witness("[(4, [[70], [71]])]", "[3, 4]"),
        # Refuted BY THE GATE against the CORRECT loop-free forward map, not
        # against the frozen loop: gold's `…Exec` never reduces, so its build
        # fails for every claim and the exit code carries no information (a
        # measured `=` forgery cleared both gold-side halves). See the
        # witness-builder note.
        "witness_reference": _REF_FORWARD_MAP,

    },
    {
        "id": "weak-only-head-documented",
        "kind": "uniqueness",
        "expect": "reject",
        # Only the FIRST presented name gets its recorded text; every later
        # member is collected with empty text. Attacks fact (d) ASSEMBLY on a
        # POSITIONAL sub-domain: correct on a one-name roster and on any roster
        # where only the head has recorded lines, wrong as soon as a later member
        # is documented.
        "module": _impl(
            "    return (match names with\n"
            "            | []      => []\n"
            "            | n :: ns => { name := n, doc := joinNL (lookupDocs n attrDocs) }\n"
            "                           :: ns.map (fun m => { name := m, doc := [] }))\n"),
        "refinement": (
            "a faithful counterpart that attached documentation only to the "
            "FIRST candidate would starve every later member of its marker. "
            "Checked on the real fixture, where the members are enumerated in a "
            "fixed order and the public-marked one is not first: it loses its "
            "marker, falls back to the leading-underscore default and is "
            "dropped, so the F2P that expects it rendered fails. Does NOT "
            "resolve. Correct for the first member and for every undocumented "
            "member, i.e. a positional partial-domain break."),
        "rationale": (
            "REJECT from E1 fact (d) ASSEMBLY on a positional sub-domain: the "
            "spec pins EVERY entry's text, not just the head's, but this rival "
            "empties the tail. Verifying would be SPEC-TOO-WEAK — a member's "
            "documentation could be dropped purely for arriving later in the "
            "roster. Refuted at `attrDocs = [(2, [[66]])]`, `names = [1, 2]`: "
            "the recorded name is the SECOND presented one, so the head entry is "
            "correct and the divergence is isolated to the tail (a length-2 "
            "roster whose documented name is second — distinct from the "
            "shift rival's input, which pairs a multi-line text across both "
            "positions). (Sibling: med-wrong-len1 — a near-miss correct on most "
            "inputs and wrong on one distinguished sub-domain.)"),
        "witness": _witness("[(2, [[66]])]", "[1, 2]"),
        # Refuted BY THE GATE against the CORRECT loop-free forward map, not
        # against the frozen loop: gold's `…Exec` never reduces, so its build
        # fails for every claim and the exit code carries no information (a
        # measured `=` forgery cleared both gold-side halves). See the
        # witness-builder note.
        "witness_reference": _REF_FORWARD_MAP,

    },
    {
        "id": "weak-drop-undocumented",
        "kind": "uniqueness",
        "expect": "reject",
        # Names with no recorded lines are OMITTED from the result entirely.
        # Attacks fact (a) LENGTH/PRESENCE — the only rival that changes the
        # result's length, and the only one whose faithful patch is observable on
        # the PASS_TO_PASS test as well as both F2P tests.
        "module": _impl(
            "    return (names.filter (fun n => lookupDocs n attrDocs != [])).map\n"
            "      (fun n => { name := n, doc := joinNL (lookupDocs n attrDocs) })\n"),
        "refinement": (
            "a faithful counterpart that collected only the candidates having "
            "recorded documentation lines would drop every other member from the "
            "roster before the retention stage ever sees it. Checked on the real "
            "fixture: the two members documented by ordinary docstrings rather "
            "than by recorded lines vanish, changing the kept set on both F2P "
            "tests AND on the PASS_TO_PASS test (which expects all four members "
            "rendered) — the only rival here that breaks a currently-passing "
            "test as well. Does NOT resolve."),
        "rationale": (
            "REJECT from E1 fact (a) LENGTH/PRESENCE: the spec pins `out` to one "
            "entry per presented name, so `out.length = names.length` "
            "unconditionally, but this rival returns a shorter list whenever any "
            "name lacks recorded lines. Verifying would be SPEC-TOO-WEAK — the "
            "spec would not require the collected roster to be COMPLETE, only "
            "that whatever survives is well-assembled. Refuted at `attrDocs = "
            "[(1, [[65]])]`, `names = [1, 2, 3]`: a length-3 roster with a "
            "single documented name, so TWO entries go missing and the length "
            "divergence is unmistakable — the only witness here that varies the "
            "roster to length 3, and the only one whose refutation is about the "
            "result's SHAPE rather than its contents."),
        "witness": _witness("[(1, [[65]])]", "[1, 2, 3]"),
        # Refuted BY THE GATE against the CORRECT loop-free forward map, not
        # against the frozen loop: gold's `…Exec` never reduces, so its build
        # fails for every claim and the exit code carries no information (a
        # measured `=` forgery cleared both gold-side halves). See the
        # witness-builder note.
        "witness_reference": _REF_FORWARD_MAP,

    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The sibling battery ships 14 SPEC cases (3 soundness, 2 admissibility, 9
# uniqueness — 3 of them MANDATORY frame-mutation rivals) plus 2 AXIOM_TESTS. It
# contracts TWO functions over nagini's carrier — `member_effective_doc` (select
# the effective documentation of a member: the inline attribute doc when
# non-empty, else the value's intrinsic doc) and `keep_module_member` (the
# downstream retention formula, parametric in an axiomatized classifier) — each
# with half-permission read-only `List[int]` inputs.
#
# This bundle models a NARROWER surface, and the narrowing is the whole story of
# the case count. It contracts ONE method, `collectMemberDocs`, over the step
# that actually resolves the F2P: assembling, per candidate name, the
# documentation text recorded for that name and letting it travel with the
# member. The sibling's SECOND function (the retention formula and its `meta_class`
# classifier) is DOWNSTREAM of this one and is not modeled here at all — there is
# no `keep`/`want_all`/`private_mode`/`name_selected` binder anywhere in the
# frozen spec, and no axiom. So every sibling case attached to `keep_module_member`
# has no counterpart, exactly the carrier narrowing the porting map describes.
# Chasing case-count parity would mean fabricating rivals against behaviour this
# bundle does not contract.
#
#   sibling case                  kind          -> here                          disposition
#   -----------------------------------------------------------------------------------------------
#   med-pos-reorder               soundness     -> pos-control-direct-model      RE-SHAPED
#   med-pos-locals                soundness     -> pos-control-named-entry       PORTED (reshaped)
#                                                  (+ pos-control-forward-map      ADDED)
#   kmm-pos-bool                  soundness     -> (none)                        UNMODELED FUNCTION
#   med-admiss                    admissibility -> admiss-nondegenerate          RE-AIMED (merged)
#   kmm-admiss                    admissibility -> (none)                        UNMODELED FUNCTION
#   med-frame-mut-attr            uniqueness    -> (none)                        VACUOUS (carrier)
#   med-frame-mut-value           uniqueness    -> (none)                        VACUOUS (carrier)
#   kmm-frame-mut-attr            uniqueness    -> (none)                        VACUOUS (carrier)
#   med-wrong-always-value        uniqueness    -> weak-drop-doc                 PORTED
#   med-wrong-len1                uniqueness    -> weak-only-head-documented     PORTED (re-aimed)
#   med-wrong-swap                uniqueness    -> weak-ignore-name              PORTED (re-aimed)
#                                                  (+ weak-shift-doc-to-neighbour  ADDED)
#                                                  (+ weak-drop-undocumented       ADDED)
#   kmm-wrong-classify-value      uniqueness    -> weak-drop-doc (same argument) PORTED (merged)
#   kmm-wrong-drop-wantall        uniqueness    -> (none)                        UNMODELED FUNCTION
#   kmm-wrong-always-keep         uniqueness    -> (none)                        UNMODELED FUNCTION
#   ax-meta-class-sound           axiom         -> (none)                        N/A (no axioms; G-AX skip)
#   ax-meta-class-contain         axiom         -> (none)                        N/A (no axioms; G-AX skip)
#
# 5 uniqueness (3 ported + 2 added), 3 soundness (2 ported + 1 added),
# 1 admissibility (2 sibling cases merged and re-aimed);
# 3 uniqueness VACUOUS (frame); 4 cases dropped as UNMODELED FUNCTION;
# 2 AXIOM_TESTS dropped as out of this gate's lane.
#
# PORTED / RE-AIMED, case by case:
#   med-wrong-always-value -> weak-drop-doc. The sibling's rival always returns
#     the value's intrinsic doc, ignoring the attribute doc; here the inline
#     documentation never travels with the member at all. Same argument (the
#     member arrives WITHOUT its recorded documentation, so its marker is
#     unavailable downstream) and the same F2P consequence. kmm-wrong-classify-
#     value is the SAME defect one function later — classify on the doc that is
#     missing the marker — and on this carrier the two collapse into one rival,
#     so it is recorded as merged rather than as a separate case.
#   med-wrong-len1 -> weak-only-head-documented. The sibling's near-miss uses the
#     attribute doc only when it is LONGER than one code point. That exact
#     predicate is not wrong here (this spec's `joinNL` is defined on every line
#     count, and a length-1 line list is not a distinguished case of it), so the
#     near-miss is RE-AIMED onto the axis this carrier does distinguish: roster
#     POSITION. Same adversarial content — correct on most inputs, wrong on one
#     distinguished sub-domain.
#   med-wrong-swap -> weak-ignore-name. The sibling inverts the precedence
#     between two candidate documentation sources. This carrier has no two-source
#     precedence to invert (the model has ONE source, the per-name table), so the
#     rival is re-aimed onto the corresponding structural mistake: reading the
#     table WITHOUT its key, so text is attached to the wrong member.
#   ADDED weak-shift-doc-to-neighbour and weak-drop-undocumented. E1 pins four
#     independently-attackable facts (length, order, association, assembly) where
#     the sibling's `member_effective_doc` postcondition pins one selection, so
#     two facts have no sibling rival to port: the off-by-one association and the
#     result's LENGTH. Both are added rather than left uncovered, per the coverage
#     rule that every independent part of the postcondition be attacked.
#   med-admiss + kmm-admiss -> admiss-nondegenerate (merged, re-aimed). Both
#     sibling cases assert a tautology on a @Pure model to show the
#     fractional-permission precondition admits an F2P-shaped input. This method
#     has NO `require` clause and no permission surface, so that probe is
#     degenerate; the sharper residual risk is a DEGENERATE post-image, so one
#     re-aimed case discharges a live in-region assert pinning all four facts of
#     E1 at once.
#
# VACUOUS (med-frame-mut-attr, med-frame-mut-value, kmm-frame-mut-attr): the
#   sibling's three MANDATORY frame rivals write a half-permission read-only
#   input (clear the attribute-doc list, append to the intrinsic-doc list) and are
#   rejected for INSUFFICIENT PERMISSION — the permission system, not a value
#   clause. This backend is referentially transparent: `attrDocs` and `names` are
#   immutable values declared read-only (not `mut`), there is no heap, no
#   aliasing, no fractional permission, and no `Acc(...)` clause to trip. There is
#   nothing to overwrite and no rejection to attribute. Omitted as a genuine
#   carrier fact per the porting map, NOT fabricated.
#
# UNMODELED FUNCTION (kmm-pos-bool, kmm-admiss, kmm-wrong-drop-wantall,
#   kmm-wrong-always-keep): all four attach to the sibling's `keep_module_member`
#   — the downstream retention formula over `want_all` / `private_mode` /
#   `name_selected` and the `meta_class` classifier. This bundle does not contract
#   that function: the frozen spec has exactly one `method` and one
#   `prove_correct`, its only binders are `attrDocs` and `names`, and there is no
#   axiom (mapping.md §2.1 records the retention pipeline as downstream of the
#   modeled collection step). A rival for a behaviour the spec does not mention
#   cannot be written against this spec at all — it would have to invent binders,
#   which `same_spec` forbids. These are real GAPS RELATIVE TO THE SIBLING but not
#   relative to this obligation: the retention formula is defended by the
#   sibling's nagini battery, not by this one.
#
# NOT F2P-OBSERVABLE — three rivals BUILT, VALIDATED, AND THEN DROPPED. Each was
#   written, and each was confirmed to be a real E1 violation with a witness that
#   elaborated against it and failed on gold. All three were dropped anyway,
#   because their faithful real patch STILL resolves both F2P tests and the P2P
#   test, so shipping them would be an artifact rather than a
#   verify-does-not-imply-resolve break (the refinement rule forbids it):
#     * `join-no-break` — assemble the recorded lines with NO separator between
#       them. Refutable on the carrier (E1 pins the single break code, and the
#       witness discriminated at a two-line input). But the real recorded value
#       for each documented member on the fixture is a TWO-line list whose second
#       line is EMPTY, so joining with or without the separator yields text that
#       the downstream marker scan reads identically; the kept set is unchanged on
#       all three tests.
#     * `first-line-only` — carry only the first recorded line. Same story: the
#       marker lives on the first line and the second recorded line is empty, so
#       the retention decision does not move.
#     * `reversed-order` — emit the entries in reverse of the presented order.
#       Refutable on the carrier (E1 pins the order). But the members are re-sorted
#       downstream before rendering (the default member order is alphabetical), so
#       collection order is not observable to any of the three tests.
#   Recorded here rather than silently omitted: each is a genuine E1 violation, so
#   each is evidence the spec is TIGHTER than the tests require — the opposite of a
#   coverage gap — but none is a legitimate reject case for this gate.
#
# DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS: not a spec hole, not a
#   vacuous class, and not a battery gap. CORRECTED BY AUDIT THREE TIMES, and this
#   revision retracts the second AND third accounts, both of which called the
#   class a hole.
#
#   Account 1 said this bundle runs under `set_option
#   loom.semantics.termination "partial"`. It does not; the frozen solution's line
#   4 reads
#
#       set_option loom.semantics.termination "total"
#
#   Accounts 2 and 3 accepted that, but claimed the hole survived anyway because
#   line 7 opened `PartialCorrectness`, whose loop rule discards the measure. That
#   is also false, and it is the claim this text withdraws. Line 7 of the frozen
#   file reads
#
#       open TotalCorrectness DemonicChoice
#
#   and there is no `open PartialCorrectness` anywhere in the file. Moreover the
#   `set_option` on line 4 is not a plain option write: its elaborator BOTH
#   records the option AND runs `openScope `TotalCorrectness``
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`), and Velvet's `method` macro
#   opens the same namespace again (`Velvet/Velvet/Syntax.lean:386`). So line 7 is
#   REDUNDANT with line 4 rather than in conflict with it, and the total scope is
#   what resolves the loop rule. Under it a postcondition is claimed of ALL runs,
#   not only of terminating ones.
#
#   MEASURED (real builds, exit codes as recorded), both forms of the rival:
#     * The crude diverging rival, `while True do pure ()` spliced ahead of the
#       frozen body, is REJECTED (exit 1) with
#       `Decreasing annotations are required in total correctness semantics`,
#       raised by the `decreasing` elaborator, which reads the OPTION.
#     * The sharper rival, which supplies an annotation that never decreases and
#       so cannot be dismissed as merely missing one, is ALSO REJECTED, on the
#       measure's own goal. Spliced ahead of the frozen body with every
#       `prove_correct` tail reduced to a bare `loom_solve`:
#
#           let mut q : Nat := 1
#           while q > 0
#             invariant 0 ≤ q
#             done_with q = 0
#             decreasing q
#           do
#             q := q
#
#       exit 1, `unsolved goals`, `case «decreasing_1: q»`, residual goal
#       `⊢ q < q`. That is the descent obligation
#       `⌜with_name_prefix `decreasing (measure b' < measure b)⌝` emitted by
#       `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop` (Loom,
#       `MonadAlgebras/NonDetT/Basic.lean:544`), which takes `measure : β → Nat`.
#       The `PartialCorrectness` twin at :211 takes `measure : β → Option ℕ` and
#       never mentions it again in its `get`; that is the rule this bundle does
#       NOT use, so the `decreasing i` clause on the frozen loop is CHECKED rather
#       than inert.
#
#   THE EARLIER EXHIBIT IS WITHDRAWN. Accounts 2 and 3 recorded a rival of exactly
#   the shape above (a `while i > 0` loop with a contradictory `invariant` against
#   its `done_with`, a body that never changes `i`, and `decreasing i`, returning
#   `[{ name := 999, doc := [7] }]`) as VERIFYING at exit 0 "on two runs", and
#   concluded that the annotation was inert as shipped. Re-measured on the current
#   frozen bytes it is rejected on `⊢ q < q`. The two claimed "one-token
#   experiments" (swapping line 7's namespace to flip the verdict) cannot be
#   reproduced either, because line 7 already IS the total namespace: there is no
#   token to swap.
#
#   NO REJECT CASE IS SHIPPED even so, and the reason is the WITNESS CONTRACT, not
#   spec weakness. A reject case needs a witness that (1) ELABORATES against the
#   rival and (2) FAILS against gold. A diverging rival's module does not compile
#   at all, since the descent obligation fails at the `method` itself ahead of any
#   appended tester, so step (1) is unreachable for ANY witness and the gate
#   returns `witness-unproven`, which it maps to INCONCLUSIVE / MALFORMED-TESTS:
#   a FAILING gate, not a rejection. `witness_reference` cannot rescue it, since it
#   substitutes only the second subject. So the class is recorded as refuted by the
#   semantics and inexpressible as a case, which is distinct both from "vacuous on
#   this carrier" (nothing to attack) and from a spec hole (something the spec
#   misses). The nagini sibling carries no explicit `diverge-*` / `nonterm-*` /
#   `weak-diverge` case, so nothing was dropped in the port.
#
#   NOTHING IS ESCALATED, and the corpus note that used to sit here goes with the
#   retraction. It claimed a census in which only 105 of 500 velvet bundles had the
#   `set_option` and the `open` in agreement while 395 declared `total` and opened
#   `PartialCorrectness`, and it accused the total-correctness conversion of being
#   a no-op on those 395. Both halves rest on the same misreading of the `open`
#   line. As the corpus now stands, 496 of 500 velvet bundles carry
#   `open TotalCorrectness`; the two lines move together, and the conversion's own
#   docstring claim (that under `"total"` the verifier demands a decreasing
#   measure on every loop and a diverging rival is rejected) is what the builds
#   above show on this cell. No edit to the frozen `Solution.lean` and no change to
#   Loom is wanted: the total-correctness loop rule is in force and gold satisfies
#   it.
#
# BINDER / CLAUSE COVERAGE. E1 is the single obligation and has TWO input
#   binders. The five reject witnesses probe five DISTINCT input points (pts=5),
#   and BOTH binders are varied across them rather than held:
#     * weak-drop-doc                 [(1, [[65]])]              [1]
#     * weak-ignore-name              [(1, [[65]]), (2, [[66]])]  [2, 1]
#     * weak-shift-doc-to-neighbour   [(4, [[70], [71]])]        [3, 4]
#     * weak-only-head-documented     [(2, [[66]])]              [1, 2]
#     * weak-drop-undocumented        [(1, [[65]])]              [1, 2, 3]
#   `names` ranges over lengths {1, 2, 3}; over rosters whose documented name is
#   FIRST (shift), SECOND (only-head) and ABSENT-for-some-name (drop-undocumented);
#   and over a roster ORDERED AGAINST the table (ignore-name, `[2, 1]`), which is
#   what makes the lookup key rather than the position load-bearing. `attrDocs`
#   ranges over a one-row table, a TWO-row table with distinct texts
#   (ignore-name), and a row whose text is MULTI-LINE (shift), so the table's
#   keys, its row count and its per-row line count are each exercised; the
#   admissibility case additionally pins both ways a member carries empty text
#   (a row recorded with an EMPTY line list, and a name absent from the table).
#   Clause coverage: E1 is the only top-level clause and all five rivals attack
#   it, each on a different one of its four independent facts — (a) length by
#   weak-drop-undocumented, (b) order defended by the positives and by the
#   admissibility assert but deliberately NOT attacked (a reversal is not
#   F2P-observable; see NOT F2P-OBSERVABLE above), (c) association by
#   weak-ignore-name and weak-shift-doc-to-neighbour — two INCOMPARABLE
#   agreement sub-domains (enumerated: 784 vs 880 agreeing points of 2560, with
#   256 / 352 points exclusive to each), which is why each carries its own
#   witness rather than one standing in for the other; an earlier revision
#   called the shift a strictly nearer miss and that is false, see its own
#   rationale — (d) assembly by weak-drop-doc (total) and
#   weak-only-head-documented (positional).
#
# WITNESS-MECHANICS AUDIT TRAIL. The first authored draft of this file closed
#   every witness with `decide`. All five passed the rival half and all five
#   failed the gold half — but they failed by STUCK REDUCTION ("reduction got
#   stuck at `.hasDecEq`"), and the gate correctly recorded all five as
#   `witness-undecided` (MALFORMED-TESTS, gate ERROR): the same error appears for
#   a TRUE claim about the frozen impl, so the rejection would have attributed
#   nothing to the spec. That verdict is recorded here rather than quietly fixed,
#   because it is the exact failure mode a reject lane is supposed to be audited
#   for and the stuck-vs-refuted distinction is invisible in an exit code.
#   The lane was re-authored over a REDUCIBLE projection — `unfold` +
#   `simp` over the model's own transparent defs, which computes both sides to
#   concrete list literals — and re-measured at three builds per rival:
#     RIVAL exit 0 (clean log) / GOLD exit 1 (residual `forIn Lean.Loop.mk` term,
#     gadgets intact) / CTRL exit 1 with `⊢ False` against a correct loop-free
#     impl. 15 builds, all five rivals, all three halves as required.
#
#   FOURTH ROUND (independent audit). All 15 witness builds reproduced a third
#   time, plus the full forgery TRIPLE (rival / reference / gold) for all five
#   cases — 30 builds, every exit code as this file states:
#     honest   RIVAL 0 (clean) / REF 1 `⊢ False` / GOLD 1 unreduced `forIn` term
#     forged   RIVAL 1 `⊢ False` / REF 0 (clean) / GOLD 1 unreduced `forIn` term
#   The forged column is the attestation and it is exactly inverted from the
#   honest one on the two REDUCIBLE subjects, while GOLD's exit code is 1 in both
#   directions — confirming from the outside that gold carries no information
#   about the claim and the `witness_reference` repair is what makes these five
#   rejections attributable to E1. `pbt._stuck` / `_stuck_screen` were also run
#   directly on all ten gold-and-reference logs: False / '' on every one, so the
#   `unsolved goals` signature is genuinely outside the stuck-reduction screen,
#   as this file claims.
#     * ADMISSIBILITY, re-derived rather than trusted. The in-region assert was
#       perturbed three ways — dropping the break code from the multi-line entry,
#       transposing the first two entries, and giving the table-ABSENT name
#       non-empty text — and each perturbation FAILS the case. Isolated from the
#       tactic script (the same four claims stated as bare `example ... := by
#       decide` over the frozen pure region), the true one closes at exit 0 and
#       all three perturbations are ACTIVELY refuted with "Tactic `decide` proved
#       that the proposition ... is false". So the assert is decided on its
#       merits, not incidentally closed: it is load-bearing on the break code, on
#       the order, and on both ways a member carries empty text.
#     * SPEC-TOO-WEAK, re-probed with EIGHT new wrong impls (the six named below
#       plus a wrong separator code and an impl that empties the text exactly when
#       one line is recorded). All eight share the frozen spec and ALL EIGHT are
#       REJECTED. No value-level hole found in E1 from any direction tried.
#     * SPEC-TOO-STRONG, re-probed with FOUR fresh correct reshapes: a `foldr`,
#       a `match`-then-map split, reverse-map-reverse, and a FORWARD `while`
#       loop that appends at the tail under a `names.take i` invariant. All four
#       VERIFY (reverse-map-reverse needed the `map`-to-`buildMembers` bridge
#       lemma proven inline before `List.reverse_reverse` closes it; the naive
#       one-line `simp` script does NOT close, which is a proof-script gap and
#       not a spec fact — recorded so the next reader does not mistake it for
#       one).
#       The forward loop is the sharpest of the four, because its invariant is
#       the mirror image of the frozen one and its step lemma is therefore new
#       rather than reused, so it was measured in BOTH directions: with the
#       `bridge` and `take`-step lemmas in scope, `loom_solve` alone discharges
#       every goal (exit 0); with those two `have`s deleted and nothing else
#       changed, the same `loom_solve` stops at exit 1 on
#       `case «invariant_2: result = buildMembers attrDocs (names.take i)»`
#       with the residual goal
#         `result ++ [{ name := names[i]!, doc := ... }]
#            = buildMembers attrDocs (List.take (i + 1) names)`.
#       So the tail-append shape genuinely obliges a new argument and the frozen
#       `ensures` still admits it. That pair of exit codes is what earns the
#       SPEC-TOO-STRONG conclusion here: the postcondition is pinning the VALUE
#       of `out`, not the backward-fold shape of the loop that produces it.
#     * The ONE finding of this round was the divergence footer, which was wrong
#       on the facts. See DIVERGENCE / NON-TERMINATION above: this bundle is
#       `total`, not `partial`. A LATER round found that round's own replacement
#       text wrong as well (it read line 7 as opening `PartialCorrectness`) and
#       re-measured the class as CLOSED. Nothing is escalated.
#
#   THIRD ROUND (independent audit). The 15 witness builds were reproduced a
#   second time (rival 0 / reference 1 with `⊢ False` / gold 1 with the
#   unreduced `forIn Lean.Loop.mk` residual), and the FORGERY PAIR was rebuilt
#   for all five cases: the witness with `≠` replaced by `=` builds exit 0
#   against the reference and exit 1 against gold, with gold's error identical
#   to the honest witness's except for the leading `¬`. That is the measurement
#   that settles the `witness_reference` repair from the outside — gold's exit
#   code is confirmed to carry NO information about the claim (both directions
#   exit 1), while the reference's DOES (honest 1 / forged 0). The reference
#   half is the whole attestation, and it is the gate's, so all five rejections
#   are attributable to E1.
#
#   Also re-derived in that round, and both are recorded because they came out
#   STRONGER than this file previously claimed:
#     * SPEC-TOO-WEAK probe. Six NEW wrong impls outside the shipped five were
#       built against the frozen spec, aimed at what the reject lane leaves
#       unattacked: order reversal; joining with NO separator; carrying only the
#       first recorded line; a TRAILING break instead of a separating one;
#       `lookupDocs` taking the LAST matching row instead of the first (wrong
#       only on a table with DUPLICATE keys); and de-duplicating the roster
#       (wrong only on a REPEATED name). ALL SIX were rejected, each with an
#       `unsolved goals` residual naming its own divergent term. The two
#       duplicate-key / repeated-name sub-domains are the least-probed corners
#       of both binders and the spec pins them anyway, so E1 is not weak there.
#     * SPEC-TOO-STRONG probe. Three NEW correct reshapes were built and ALL
#       THREE verify: a `foldr` over the roster; a reverse-map-reverse round
#       trip; and — the sharpest of the three — a FORWARD `while` loop that
#       appends at the tail under a `names.take i` invariant, i.e. the frozen
#       backward fold's traversal direction inverted with its loop, its
#       invariants and its termination all rewritten. That last one needed a
#       genuinely new proof (a `buildMembers`-as-`map` bridge lemma plus
#       `List.take_succ`) and closes, which is the strongest available evidence
#       that E1 is pinned to the modeled association rather than to the frozen
#       impl's shape. No spec hole in either direction.
#
#   SECOND ROUND (independent audit). All 15 builds above were reproduced
#   (rival 0 / gold 1 / ctrl 1 with `⊢ False`), but the CTRL half was PROSE: the
#   gate was still checking the second half against GOLD, whose build fails for
#   every claim. The measured consequence is recorded in THE THREE BUILDS above —
#   a `≠`-to-`=` forgery at an agreement point clears both gold-side halves, and
#   `pbt.gates._stuck` returns False on all five gold logs, so no mechanical
#   screen stood behind the claim. Repaired by giving every reject case an
#   explicit `witness_reference` (the correct loop-free forward map), which moves
#   the third build inside the gate: the honest witnesses still fail there with
#   `⊢ False` and the forgery is caught as `witness-vacuous`. The rivals, the
#   witnesses and the recorded outcomes are unchanged; what changed is that the
#   discrimination is now re-derived by the gate on every run instead of asserted
#   in a comment.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3/§5: the
#   collection logic is modeled deeply and validated by G-CONF; `meta.json
#   gates.G-AX.status = "skip"`), so the sibling's two `meta_class` probes —
#   axiom-soundness and axiom-containment against the real classifier — have no
#   counterpart. That lane is G-AX's job and this gate ignores AXIOM_TESTS
#   regardless.
AXIOM_TESTS = []
