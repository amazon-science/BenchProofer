"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8265 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a method's ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and BOTH ``prove_correct renderGroup`` / ``prove_correct renderIndex``
obligations survive with byte-identical statements) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (two contracted methods):

  renderGroup (elts : List Expr) return (out : List Char)
    ensures out = render (.group elts)                                     -- G

  renderIndex (value idx : Expr) return (out : List Char)
    ensures out = render (.index value idx)                               -- I

The two methods render, to source text, a parenthesised group of expressions and
an indexing expression. ``render`` is a TRANSPARENT ``def`` over the method's own
arguments (there is no opaque answer-key oracle — the ``axioms`` region is
empty), so pinning ``out = render (.group elts)`` / ``out = render (.index value
idx)`` is grounded, not an echo. ``render`` composes two independently-attackable
sub-domains PER method:

  * GROUP: an empty group renders as the literal ``()``; a non-empty group is its
    comma-joined members enclosed in the surrounding parentheses. Two arms — the
    empty arm and the non-empty (bracket-wrapped join) arm — each attackable
    alone.
  * INDEX: when the index is a non-empty group carrying no unpacking element, its
    members are placed DIRECTLY inside the brackets (no redundant grouping
    parentheses); in every other case the index is rendered as a whole expression
    inside the brackets. Two arms — the direct-members arm and the
    whole-expression arm — plus the rendered ``value`` prefix, each attackable
    alone.

INPUT BINDERS. ``renderGroup`` binds ``elts : List Expr``; ``renderIndex`` binds
``value : Expr`` and ``idx : Expr``. All are load-bearing: ``elts`` selects the
group arm and supplies the joined members; ``idx`` selects the index arm and
supplies the members/whole rendering; ``value`` is the rendered prefix. The
reject witnesses move every one of them (see the footer's binder accounting).

WITNESS MECHANICS ON THIS BUNDLE. ``render`` / ``joinComma`` / ``isUnpack`` are
TRANSPARENT ``def``s and both impls are LOOP-FREE (a single ``let``/``match``),
so a witness reaches the post-image through Velvet's ``extract_program_for``
machinery: at one concrete input it states that the rival's own extracted output
DIFFERS from the transparent post-image the ``ensures`` demands,

    (match <method>Exec <args> with | DivM.res r => r | _ => default)
        ≠ render (.<shape> <args>)

a direct violation of the load-bearing ``ensures``. ``render`` is defined by
well-founded recursion (the nested ``elts.map render``), so it does NOT reduce
under bare ``decide``; the witness is discharged by ``simp`` handed the extracted
program's unfolding (``<method>Exec`` / ``NonDetT.run``) together with the
frozen file's own one-step unfold lemmas (``render_group`` / ``render_index``)
and ``render`` / ``joinComma``. Against the FROZEN solution the SAME statement
fails: gold's extracted program computes exactly ``render (.<shape> <args>)``, so
``simp`` reduces the ``≠`` to ``False`` and the witness FAILS on gold — exactly
the discrimination the gate requires. Every input is a concrete decidable literal
(no opaque term, no hypothesis), so no consistency probe is needed and no binder
is left unsatisfiable. No banned token (sorry/admit/native_decide/axiom). Each
witness was checked out-of-band with ``scripts/lean_verify.sh``: every one
ELABORATES against its rival (exit 0) and FAILS against gold (an unsolved
``False``).

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS / positive controls — APPLY. Structurally different but
    behaviourally identical impls (reorder the group arms; return the grounded
    ``render`` directly; hoist the common ``value ++ "["`` prefix on the index)
    MUST verify, else the spec is SPEC-TOO-STRONG on the shape of the impl. The
    direct-return control also covers the (N/A) ungrounded-oracle lane: the
    post-image is grounded in the inputs, so the cheapest faithful impl is
    correct and MUST verify.
  * ADMISSIBILITY — RE-AIMED. The nagini sibling establishes ``subscript_render``'s
    precondition ``Implies(index_is_member_group, len(elts) > 0)`` from a legal
    call site. Neither method here carries ANY ``require`` (both pre-conditions
    regions are empty), so the LITERAL "a normal input satisfies the precondition"
    probe has no precondition to satisfy. That does NOT make the lane vacuous: on
    a TOTAL carrier the PRECOND-TOO-STRONG analogue is the obligation being
    UNSATISFIABLE or DEGENERATE at exactly the F2P-shaped input, because a
    post-image no impl can meet reads exactly like one every impl meets, and no
    uniqueness rival would notice. The two ``kind="admissibility"`` cases below
    discharge that by EVALUATION at the concrete round-trip points, as in-region
    ``assert``s, before closing the frozen obligation. (AUDIT-CORRECTED: the port
    shipped a single admissibility case whose ``module`` was the frozen file
    VERBATIM, which is a restatement of G-GOLD and tests nothing this gate does
    not already know; see the accounting footer.)
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini surface already declared this
    N/A: every input is an immutable Nagini value sequence carried by SHARE with
    no write permission (has_readonly_input = False). Lean/Velvet are
    referentially transparent too: ``elts`` / ``value`` / ``idx`` are immutable
    values, no method declares a ``mut`` parameter, and there is no heap,
    aliasing, or permission system. No read-only input to overwrite, no frame
    clause to violate — the class has no carrier analogue. Not ported (a
    fabricated substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE on this bundle, for a reason
    the audit MEASURED rather than argued. The bundle sets
    ``loom.semantics.termination "total"``, so a rival whose loop carries no
    decreasing measure IS genuinely rejected, and "the frozen impls are loop-free"
    is NOT a reason (a rival may introduce a loop; the impl region is what a
    variant may rewrite). The audit built such a rival — a ``while n > 0`` with
    ``n := n + 1`` prepended to the frozen group body, leaving the returned value
    unchanged — confirmed it is IN SCOPE (``variant_problems`` clean) and confirmed
    the verifier rejects it: ``Decreasing annotations are required in total
    correctness semantics`` (exit 1). What blocks the case is the WITNESS half, not
    the rejection: the rival's extracted program is an unreduced
    ``forIn Lean.Loop.mk`` term, so the refutation witness fails against the RIVAL
    (exit 1, ``unsolved goals ⊢ ¬(match NonDetT.run ((fun a => ['(', ')']) <$>
    forIn Lean.Loop.mk 1 …)``) — the gate's ``witness-unproven`` outcome, which is
    an inconclusive MALFORMED result, not a pass. The rejection is also not
    attributable to the SPEC in the first place: it is the termination linter, one
    layer above the ``ensures``, and the same error fires for a diverging impl that
    returns the CORRECT value. So this class is recorded as a KNOWN GAP with the
    measured error text, not as "vacuous" and not as a shippable case. (The nagini
    sibling also carries no ``diverge-*`` / ``nonterm-*`` case, so nothing was
    dropped in the port.)
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, as the nagini surface already
    noted: the only oracle is ``render`` itself, a transparent function of the
    input, so echoing it IS doing the work. Covered by the honest cheapest-impl
    positive control (pos-group-direct).
  * PARTIAL-DOMAIN / VALUE / UNIQUENESS — the whole reject surface. The two gold
    prepatch bugs (a non-empty group rendered as the BARE join, and a simple
    index KEEPING its inner grouping parentheses) are reproduced as the
    load-bearing F2P / P2P discriminators, alongside three partial-domain
    near-misses.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8265"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors: the WHOLE frozen impl body of each method, everything
# ---- strictly BETWEEN that method's `-- impl-start` / `-- impl-end` (the marker
# ---- comment lines themselves are OUTSIDE these anchors, so they are preserved).
# ---- Every variant replaces exactly one of these blocks, so each edit lies
# ---- wholly inside one impl region and same_spec holds by construction (both
# ---- facts — present and unique — asserted at load).
_GROUP_IMPL = (
    "    let out : List Char :=\n"
    "      if elts.isEmpty then \"()\".toList\n"
    "      else \"(\".toList ++ joinComma (elts.map render) ++ \")\".toList\n"
    "    return out"
)
assert _BASE.count(_GROUP_IMPL) == 1, "renderGroup impl region drifted"

_INDEX_IMPL = (
    "    let out : List Char :=\n"
    "      match idx with\n"
    "      | .group elts =>\n"
    "          if (!elts.isEmpty) && (!elts.any isUnpack) then\n"
    "            render value ++ \"[\".toList ++ joinComma (elts.map render) ++ \"]\".toList\n"
    "          else\n"
    "            render value ++ \"[\".toList ++ render (.group elts) ++ \"]\".toList\n"
    "      | s => render value ++ \"[\".toList ++ render s ++ \"]\".toList\n"
    "    return out"
)
assert _BASE.count(_INDEX_IMPL) == 1, "renderIndex impl region drifted"


def _group(new_body):
    """Full Solution.lean variant with ONLY the renderGroup impl body replaced."""
    return _swap(_BASE, _GROUP_IMPL, new_body)


def _index(new_body):
    """Full Solution.lean variant with ONLY the renderIndex impl body replaced."""
    return _swap(_BASE, _INDEX_IMPL, new_body)


# ---- the two frozen proof bodies, verbatim. Only the ADMISSIBILITY cases touch
# ---- these, and only to APPEND a discharge step for the extra `assert` goal the
# ---- spliced probe raises: `loom_solve` closes the method's own obligation
# ---- exactly as frozen, then the appended `all_goals simp [...]` evaluates the
# ---- ground `render` facts. The tactic body is elided from the spec view, so
# ---- same_spec is untouched (asserted at load, and re-checked by the gate).
_GROUP_PROOF = "prove_correct renderGroup by\n  loom_solve"
assert _BASE.count(_GROUP_PROOF) == 1, "renderGroup proof region drifted"

_INDEX_PROOF = "prove_correct renderIndex by\n  loom_solve"
assert _BASE.count(_INDEX_PROOF) == 1, "renderIndex proof region drifted"

# The one appended step. It introduces no lemma, no axiom and no `sorry`; it only
# evaluates the transparent `render` / `joinComma` / `isUnpack` defs on ground
# data. Audit-measured LIVE: with a single conjunct negated the same script
# leaves `unsolved goals` (exit 1).
_ADMISS_RETUNE = "\n  all_goals simp [render, joinComma, isUnpack]"


def _group_admiss(assert_body):
    """Frozen renderGroup, with `assert_body` spliced at the head of its impl.

    The impl AFTER the assert is byte-identical to the frozen one, so the case's
    outcome is attributable to the obligation's SATISFIABILITY at the probed
    input and to nothing about a candidate impl.
    """
    return _swap(_swap(_BASE, _GROUP_IMPL, assert_body + _GROUP_IMPL),
                 _GROUP_PROOF, _GROUP_PROOF + _ADMISS_RETUNE)


def _index_admiss(assert_body):
    """Frozen renderIndex, with `assert_body` spliced at the head of its impl."""
    return _swap(_swap(_BASE, _INDEX_IMPL, assert_body + _INDEX_IMPL),
                 _INDEX_PROOF, _INDEX_PROOF + _ADMISS_RETUNE)


# ---- witness builders. `render` is well-founded-recursive so it does not reduce
# ---- under bare `decide`; each witness is closed by `simp` handed the extracted
# ---- program's unfolding and the frozen file's own one-step unfold lemmas
# ---- (`render_group` / `render_index`) plus `render` / `joinComma`. Checked in a
# ---- file whose `prove_correct` blocks are stripped, so no tactic script can
# ---- mask the verdict.
def _group_witness(elts):
    return (
        "\nextract_program_for renderGroup\n\n"
        "example :\n"
        f"    (match renderGroupExec {elts} with | DivM.res r => r | _ => default)\n"
        f"        ≠ render (.group {elts}) := by\n"
        "  simp [renderGroupExec, renderGroup, NonDetT.run, render_group,\n"
        "        joinComma, render, List.map, List.isEmpty]\n"
    )


def _index_witness(value, idx):
    return (
        "\nextract_program_for renderIndex\n\n"
        "example :\n"
        f"    (match renderIndexExec ({value}) ({idx}) with"
        " | DivM.res r => r | _ => default)\n"
        f"        ≠ render (.index ({value}) ({idx})) := by\n"
        "  simp [renderIndexExec, renderIndex, NonDetT.run, render_index,\n"
        "        render, joinComma, List.map, List.isEmpty, List.any, isUnpack]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-group-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the two arms: handle the non-empty group FIRST, the empty group
        # in the else. Same value, different executable shape; the frozen proof
        # (`loom_solve`) still closes because `render` is used exactly as the
        # ensures uses it.
        "module": _group(
            "    let out : List Char :=\n"
            "      if !elts.isEmpty then \"(\".toList ++ joinComma (elts.map render) ++ \")\".toList\n"
            "      else \"()\".toList\n"
            "    return out"),
        "rationale": (
            "renderGroup with the two arms reordered (non-empty first) must verify "
            "against ensures G (`out = render (.group elts)`); the value is "
            "unchanged so `loom_solve` still discharges the equality. If it cannot "
            "verify => SPEC-TOO-STRONG (over-fit to the empty-first code shape). "
            "(Sibling: pos-tuple-reorder.)"),
    },
    {
        "id": "pos-group-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl: return the grounded `render (.group elts)`
        # directly, no inline branch. `out` IS the post-image, so ensures G holds
        # on the whole domain.
        "module": _group(
            "    let out : List Char := render (.group elts)\n"
            "    return out"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded post-image "
            "`render (.group elts)` directly (no inline branch). Ensures G is "
            "literally that equation, so it MUST verify, else G is SPEC-TOO-STRONG. "
            "Also the honest no-ungrounded-echo control: `render …` is grounded in "
            "the input (not an opaque answer key), so a direct return is correct, "
            "not a cheat, and any WRONG rendering fails G. (Sibling: "
            "pos-tuple-cheapest.)"),
    },
    {
        "id": "pos-index-prefix",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the common `render value ++ "["` prefix into a local, then branch.
        # Same value flow, different shape; the frozen proof still closes.
        "module": _index(
            "    let pre := render value ++ \"[\".toList\n"
            "    let out : List Char :=\n"
            "      match idx with\n"
            "      | .group elts =>\n"
            "          if (!elts.isEmpty) && (!elts.any isUnpack) then\n"
            "            pre ++ joinComma (elts.map render) ++ \"]\".toList\n"
            "          else\n"
            "            pre ++ render (.group elts) ++ \"]\".toList\n"
            "      | s => pre ++ render s ++ \"]\".toList\n"
            "    return out"),
        "rationale": (
            "renderIndex with the common `render value ++ \"[\"` prefix precomputed "
            "into a local `pre` (same value, different shape) must verify against "
            "ensures I (`out = render (.index value idx)`); the frozen proof closes "
            "unchanged. Else SPEC-TOO-STRONG. (Sibling: pos-subscript-prefix.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-subscript-precond, and
    # REWRITTEN BY AUDIT. Neither method here carries ANY `require` (both
    # pre-conditions regions are empty), so the literal "a normal input
    # satisfies the precondition" probe has no precondition to satisfy. That
    # does NOT make the lane vacuous: on a TOTAL carrier the PRECOND-TOO-STRONG
    # analogue is the obligation being UNSATISFIABLE or DEGENERATE at exactly
    # the F2P-shaped input, since a post-image no impl can meet reads exactly
    # like one every impl meets and no uniqueness rival below would notice.
    #
    # The port discharged this with `module = _BASE` — the frozen file VERBATIM.
    # That case is honest but hollow: "the frozen impl verifies" is precisely
    # what G-GOLD already records, it moves no binder, states no claim about any
    # concrete input, and would pass unchanged no matter how degenerate the two
    # post-images were. Replaced by the two cases below, which each splice a
    # LIVE `assert` at the head of the frozen impl, discharge it BY EVALUATION at
    # the concrete round-trip points, and then close the frozen obligation with
    # the impl after the assert byte-identical to gold's.
    # =====================================================================
    {
        "id": "admiss-group-roundtrip-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The F2P-shaped group point: a three-member group. Asserts the
        # post-image there (a) round-trips to the parenthesised form, (b) still
        # renders the EMPTY group as the bare literal (so the two arms are not
        # collapsed by an unsatisfiable clause), and (c) is NOT the bare join —
        # so G is discriminating AT this point, not merely somewhere.
        "module": _group_admiss(
            '    assert (with_name_prefix `admiss\n'
            '      (render (.group [Expr.atom "1".toList, Expr.atom "2".toList,\n'
            '            Expr.atom "3".toList])\n'
            '          = "(1, 2, 3)".toList\n'
            '        ∧ render (.group ([] : List Expr)) = "()".toList\n'
            '        ∧ render (.group [Expr.atom "1".toList, Expr.atom "2".toList,\n'
            '            Expr.atom "3".toList])\n'
            '            ≠ "1, 2, 3".toList))\n'),
        "rationale": (
            "ensures G is SATISFIABLE and NON-DEGENERATE at the F2P-shaped group "
            "point — a three-member group, the round trip the failing test pins. "
            "Three conjuncts, all discharged by evaluation on ground data: the "
            "post-image at that point is the parenthesised form; the EMPTY group "
            "still renders as the bare literal (so the two arms are not collapsed "
            "by a clause no impl can meet); and the post-image is NOT the bare "
            "join, so G is orientation-sensitive AT this input rather than merely "
            "somewhere. If any conjunct failed, G would be unsatisfiable or "
            "degenerate exactly where the behaviour exists => PRECOND-TOO-STRONG, "
            "and every group rival below would be rejecting against an obligation "
            "no impl can meet. The impl after the assert and the frozen proof's "
            "`loom_solve` are byte-identical, so `out = render (.group elts)` "
            "still discharges as frozen; only a `simp` over the transparent defs "
            "is appended for the assert's own goal. Observed: verifies (exit 0); "
            "negating the first conjunct (the bare join wins) leaves `unsolved "
            "goals` (exit 1), so the assert is LIVE. (Lands the sibling's "
            "admiss-subscript-precond lane, which the port had discharged with "
            "the frozen file verbatim — see the accounting footer.)"),
    },
    {
        "id": "admiss-index-roundtrip-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The P2P-shaped index point: a two-member group index. Asserts the
        # post-image (a) places the members directly inside the brackets, (b)
        # routes the EMPTY group index to the whole-expression rendering (the
        # other arm — so BOTH arms of I are jointly satisfiable), and (c) is NOT
        # the redundantly-parenthesised form.
        "module": _index_admiss(
            '    assert (with_name_prefix `admiss\n'
            '      (render (.index (Expr.atom "T".toList)\n'
            '            (Expr.group [Expr.atom "int".toList, Expr.atom "int".toList]))\n'
            '          = "T[int, int]".toList\n'
            '        ∧ render (.index (Expr.atom "x".toList) (Expr.group ([] : List Expr)))\n'
            '            = "x[()]".toList\n'
            '        ∧ render (.index (Expr.atom "T".toList)\n'
            '            (Expr.group [Expr.atom "int".toList, Expr.atom "int".toList]))\n'
            '            ≠ "T[(int, int)]".toList))\n'),
        "rationale": (
            "ensures I is SATISFIABLE and NON-DEGENERATE at the P2P-shaped index "
            "point — a two-member group index, the round trip the regression rows "
            "pin. Three conjuncts by evaluation: the members are placed DIRECTLY "
            "inside the brackets; the EMPTY group index routes to the OTHER arm "
            "(the whole-expression rendering, the bare group literal inside the "
            "brackets), so both arms of I are jointly satisfiable and the "
            "two-clause guard selects a reachable arm on each side; and the "
            "post-image is NOT the redundantly-parenthesised form, so I bites AT "
            "this input. If any failed, I would be unsatisfiable or degenerate at "
            "exactly the point the behaviour exists for => PRECOND-TOO-STRONG. "
            "Impl after the assert and the frozen `loom_solve` byte-identical. "
            "Observed: verifies (exit 0); asserting instead that the members keep "
            "their grouping parentheses leaves `unsolved goals` (exit 1), so the "
            "assert is LIVE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Between them they attack
    # every arm of both post-images and move every input binder.
    # =====================================================================
    {
        "id": "rival-group-bare-join",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-patch bug: a non-empty group renders as the BARE
        # comma-join with NO surrounding parentheses. Correct on the empty
        # sub-domain, wrong on the non-empty one.
        "module": _group(
            "    let out : List Char :=\n"
            "      if elts.isEmpty then \"()\".toList\n"
            "      else joinComma (elts.map render)\n"
            "    return out"),
        "refinement": (
            "this is the literal pre-patch behaviour: a non-empty group renders as "
            "the bare join `1, 2, 3` with no surrounding parentheses. Its faithful "
            "real patch is the unchanged pre-patch renderer, which FAILS the F2P "
            "test pinning `(1, 2, 3)` back to `(1, 2, 3)` (it produces `1, 2, 3`). "
            "So a verifying rival would be verify-without-resolve."),
        "rationale": (
            "REJECT from ensures G via the NON-EMPTY arm: the spec pins a non-empty "
            "group to `\"(\" ++ joinComma … ++ \")\"`, but this returns the bare "
            "join. Verifying would be SPEC-TOO-WEAK (the surrounding parentheses "
            "unpinned). Refuted at a non-empty group `[atom \"1\", atom \"2\"]` — "
            "the sub-domain the empty-open rival agrees with gold on, so the two do "
            "NOT share a witness. (Sibling: rival-tuple-bare-join.)"),
        "witness": _group_witness('[Expr.atom "1".toList, Expr.atom "2".toList]'),
    },
    {
        "id": "rival-group-empty-open",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every non-empty group, but the EMPTY group renders as a single
        # "(" instead of "()". Pins only the non-empty half of the domain.
        "module": _group(
            "    let out : List Char :=\n"
            "      if elts.isEmpty then \"(\".toList\n"
            "      else \"(\".toList ++ joinComma (elts.map render) ++ \")\".toList\n"
            "    return out"),
        "refinement": (
            "correct on every non-empty group but renders the empty group as `(` "
            "instead of `()`. Its faithful real patch (an else-branch returning "
            "`(`) would FAIL the P2P test pinning the empty group `()` back to "
            "`()`. A partial-domain rival pinning only the non-empty half."),
        "rationale": (
            "REJECT from ensures G via the EMPTY arm: the spec pins an empty group "
            "to the literal `()`, but this returns `(`. Verifying would be "
            "SPEC-TOO-WEAK (the empty-group literal unpinned). Refuted at the EMPTY "
            "group `[]` — the ONLY witness that moves `elts` to the empty list, so "
            "the battery discriminates the empty sub-domain. (Sibling: "
            "rival-tuple-empty-open.)"),
        "witness": _group_witness("([] : List Expr)"),
    },
    {
        "id": "rival-group-extra-paren",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: a non-empty group gains a redundant trailing ")".
        # Confirms ensures G is an EXACT equality, not a prefix/containment check.
        "module": _group(
            "    let out : List Char :=\n"
            "      if elts.isEmpty then \"()\".toList\n"
            "      else \"(\".toList ++ joinComma (elts.map render) ++ \"))\".toList\n"
            "    return out"),
        "refinement": (
            "a near-miss: a non-empty group gains a redundant trailing `)`, "
            "rendering `(1))`. Its faithful real patch would emit the doubled "
            "bracket and FAIL the F2P test (which pins the exact `(1, 2, 3)` with "
            "one closing paren) — it would NOT resolve. Confirms the postcondition "
            "is an EXACT equality, not a prefix/containment check."),
        "rationale": (
            "REJECT from ensures G via the NON-EMPTY arm: the exact structural "
            "equality has ONE closing `)`, not two. Verifying would be "
            "SPEC-TOO-WEAK (G would be satisfiable by a prefix rather than an exact "
            "match). Refuted at a singleton group `[atom \"1\"]` — a distinct input "
            "point from the two-element bare-join witness. (Sibling: "
            "rival-tuple-extra-paren.)"),
        "witness": _group_witness('[Expr.atom "1".toList]'),
    },
    {
        "id": "rival-index-inner-parens",
        "kind": "uniqueness",
        "expect": "reject",
        # The coupling pre-patch bug: a simple-group index KEEPS an inner pair of
        # parentheses, so an index renders as base[(a, b)] not base[a, b]. Correct
        # on the whole-expression (non-group) arm, wrong on the direct-members arm.
        "module": _index(
            "    let out : List Char :=\n"
            "      match idx with\n"
            "      | .group elts =>\n"
            "          if (!elts.isEmpty) && (!elts.any isUnpack) then\n"
            "            render value ++ \"[\".toList ++ render (.group elts) ++ \"]\".toList\n"
            "          else\n"
            "            render value ++ \"[\".toList ++ render (.group elts) ++ \"]\".toList\n"
            "      | s => render value ++ \"[\".toList ++ render s ++ \"]\".toList\n"
            "    return out"),
        "refinement": (
            "this is the coupling pre-patch bug: a simple-group index renders with "
            "the group's own surrounding parentheses kept — `base[(a, b)]` instead "
            "of `base[a, b]`. Its faithful real patch would render the simple-tuple "
            "subscript with redundant parentheses and FAIL the P2P test that pins "
            "`Tuple[int, int]` back to `Tuple[int, int]` — it would NOT resolve. "
            "Correct on every non-group index."),
        "rationale": (
            "REJECT from ensures I via the DIRECT-MEMBERS arm: the spec pins a "
            "non-empty unpack-free group index to the members placed directly "
            "inside the brackets (no grouping parentheses), but this keeps them. "
            "Verifying would be SPEC-TOO-WEAK (the redundant-parenthesis removal "
            "unpinned). Refuted at value `atom \"T\"`, idx a two-member group "
            "`[atom \"a\", atom \"b\"]` — the group-arm sub-domain. (Sibling: "
            "rival-subscript-inner-parens.)"),
        "witness": _index_witness(
            'Expr.atom "T".toList',
            'Expr.group [Expr.atom "a".toList, Expr.atom "b".toList]'),
    },
    {
        "id": "rival-index-drop-body",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the direct-members (group) arm, but a non-group index DROPS
        # its body, rendering base[] instead of base[idx]. Pins only the group
        # half; and moves `value` to a distinct literal from the group rival so the
        # `value` binder is varied.
        "module": _index(
            "    let out : List Char :=\n"
            "      match idx with\n"
            "      | .group elts =>\n"
            "          if (!elts.isEmpty) && (!elts.any isUnpack) then\n"
            "            render value ++ \"[\".toList ++ joinComma (elts.map render) ++ \"]\".toList\n"
            "          else\n"
            "            render value ++ \"[\".toList ++ render (.group elts) ++ \"]\".toList\n"
            "      | _ => render value ++ \"[\".toList ++ \"]\".toList\n"
            "    return out"),
        "refinement": (
            "correct on the simple-group index arm but a non-group index drops its "
            "body, rendering `base[]` instead of `base[idx]`. Its faithful real "
            "patch would emit an empty index for every subscript whose index is not "
            "a simple group (a single-element / generic subscript) and FAIL those "
            "P2P unparse rows — it would NOT resolve. A partial-domain rival "
            "pinning only the group half."),
        "rationale": (
            "REJECT from ensures I via the WHOLE-EXPRESSION arm: the spec pins a "
            "non-group index to `render value ++ \"[\" ++ render idx ++ \"]\"`, but "
            "this drops `render idx`. Verifying would be SPEC-TOO-WEAK (the "
            "non-group index body unenforced). Refuted at value `atom \"x\"` "
            "(distinct from the group rival's `atom \"T\"`, so the `value` binder "
            "is varied), idx a non-group `atom \"a\"` (moving the `idx` binder off "
            "the group shape). (Sibling: rival-subscript-drop-body.)"),
        "witness": _index_witness('Expr.atom "x".toList', 'Expr.atom "a".toList'),
    },
    {
        "id": "rival-index-empty-group",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The index guard is a TWO-clause conjunction
        # `(!elts.isEmpty) && (!elts.any isUnpack)`; every rival above either
        # collapses both arms to one body or attacks the non-group arm, so NO case
        # isolated a single conjunct and no case ever moved `idx` to an EMPTY
        # group. This rival drops the `!elts.isEmpty` conjunct only: an empty
        # group index takes the direct-members arm and renders `T[]` where the
        # spec pins `T[()]`. Correct on every non-empty unpack-free group and on
        # every non-group index; wrong exactly on the empty-group index point.
        "module": _index(
            "    let out : List Char :=\n"
            "      match idx with\n"
            "      | .group elts =>\n"
            "          if !elts.any isUnpack then\n"
            "            render value ++ \"[\".toList ++ joinComma (elts.map render) ++ \"]\".toList\n"
            "          else\n"
            "            render value ++ \"[\".toList ++ render (.group elts) ++ \"]\".toList\n"
            "      | s => render value ++ \"[\".toList ++ render s ++ \"]\".toList\n"
            "    return out"),
        "refinement": (
            "an index whose index is an EMPTY group renders as `T[]` instead of "
            "`T[()]`, because the emptiness half of the arm guard is dropped and "
            "the empty group is comma-joined to nothing rather than rendered as a "
            "whole expression. Its faithful real counterpart would emit an empty "
            "pair of brackets for that expression shape and FAIL the unparse row "
            "pinning `x[()]` back to `x[()]` — it would NOT resolve. A "
            "partial-domain rival correct everywhere except the empty-group index."),
        "rationale": (
            "REJECT from ensures I via the EMPTINESS conjunct of the "
            "direct-members arm guard: the spec routes an empty group index to the "
            "WHOLE-EXPRESSION rendering (`render (.group [])` = the literal `()`), "
            "not to the direct-members join. Verifying would be SPEC-TOO-WEAK (the "
            "`!elts.isEmpty` half of the conjunction unpinned, leaving the arm "
            "selection decided by the unpack clause alone). Refuted at value "
            "`atom \"T\"`, idx the EMPTY group — the ONLY witness in the battery "
            "that moves `idx` to an empty group, so the emptiness conjunct is "
            "discriminated on its own. (No sibling: this conjunct is not separable "
            "in the nagini surface, whose group branch is selected by a single "
            "BOOLEAN parameter `index_is_member_group` rather than by inspecting "
            "the element list, so the two clauses are fused there.)"),
        "witness": _index_witness(
            'Expr.atom "T".toList', 'Expr.group ([] : List Expr)'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (3
# soundness positives, 1 admissibility, 5 uniqueness rivals) plus an EMPTY AXIOM
# lane (AXIOM_TESTS = []). This velvet bundle models the SAME two changed
# renderers DEEPLY and CONCRETELY (`render` / `joinComma` / `isUnpack` over the
# `Expr` carrier), so every nagini case has a direct counterpart — the surface is
# not narrowed here.
#
#   sibling case                  kind          -> here                       disposition
#   -----------------------------------------------------------------------------------------
#   pos-tuple-reorder             soundness     -> pos-group-reorder          PORTED
#   pos-tuple-cheapest            soundness     -> pos-group-direct           PORTED
#   pos-subscript-prefix          soundness     -> pos-index-prefix           PORTED
#   admiss-subscript-precond      admissibility -> admiss-group-roundtrip-…   RE-AIMED
#                                               +  admiss-index-roundtrip-…   (audit)
#   rival-tuple-bare-join         uniqueness    -> rival-group-bare-join      PORTED
#   rival-tuple-empty-open        uniqueness    -> rival-group-empty-open     PORTED
#   rival-tuple-extra-paren       uniqueness    -> rival-group-extra-paren    PORTED
#   rival-subscript-inner-parens  uniqueness    -> rival-index-inner-parens   PORTED
#   rival-subscript-drop-body     uniqueness    -> rival-index-drop-body      PORTED
#   AXIOM_TESTS (none)            axiom         -> (none)                     N/A (G-AX)
#   (no sibling)                  uniqueness    -> rival-index-empty-group    ADDED (audit)
#
# 5 uniqueness ported, 3 soundness ported, and the admissibility lane RE-AIMED
# into TWO cases by the audit (the port's single case was `module = _BASE`, the
# frozen file verbatim — a restatement of G-GOLD that moves no binder and would
# have passed unchanged however degenerate the post-images were; the replacements
# each carry a live, audit-measured `assert` at a concrete round-trip point).
# The FRAME class is vacuous (no case in the sibling, no carrier analogue: no
# `mut` parameter, no heap, no permission system). The DIVERGENCE class is a
# recorded KNOWN GAP, not vacuous and not shippable — measured, see the header:
# under `termination "total"` the diverging rival IS rejected (exit 1,
# `Decreasing annotations are required in total correctness semantics`) but its
# witness cannot be proven against the rival (the extracted program is an
# unreduced `forIn Lean.Loop.mk` term), so the case could only ever record the
# gate's inconclusive `witness-unproven`; and the rejection comes from the
# termination linter rather than from either `ensures`, so it would attribute
# nothing to the spec even if it built. Axiom lane empty (nothing to port).
# PLUS 1 uniqueness rival ADDED BY AUDIT
# (rival-index-empty-group) with no sibling counterpart: the index arm guard is a
# two-clause conjunction on THIS carrier (`(!elts.isEmpty) && (!elts.any
# isUnpack)`) but is a single boolean PARAMETER in the sibling, so the emptiness
# conjunct only becomes separately attackable here. 11 SPEC cases total.
#
# AUDIT PROBES that produced no case, recorded so the next reader need not
# re-measure them. SPEC-TOO-WEAK direction (attack D — six NEW wrong impls the
# battery does not contain, each built and judged by the real verifier): group
# rendered with square brackets instead of parentheses; group correct except at
# length 3 (the F2P point itself); group with a spurious suffix at length 2;
# index dropping the rendered `value` prefix; index dropping ONLY the unpack
# conjunct; index always rendering the whole index expression. ALL SIX were
# REJECTED (exit 1) — no spec hole found. SPEC-TOO-STRONG direction (attack E —
# four NEW correct reshapes): group by `match elts with | [] | es` instead of
# `isEmpty`; index returning the grounded post-image `render (.index value idx)`
# directly; index with the two guard conjuncts COMMUTED; group with the joined
# body hoisted into a local. ALL FOUR VERIFIED (exit 0) with the frozen proof
# script untouched — no soundness hole, and the obligations are not over-fit to
# the frozen syntactic form.
#
# AUDIT NOTE — the OTHER conjunct (`!elts.any isUnpack`) is deliberately NOT
# given a rival. A rival dropping it is rejected by the spec (built and measured:
# the variant fails to verify), so it is not a spec hole; but its only refutation
# point is an index over a group CONTAINING an unpacking element, and mapping.md
# records that shape as OUTSIDE the renderable domain — rendering an unpacking
# element is not implemented at the base commit, so it raises in BOTH arms and the
# distinction `T[(*a)]` vs `T[*a]` is UNOBSERVABLE upstream. Such a rival could
# carry no honest refinement argument (its faithful counterpart would resolve
# every real test), so it is omitted as vacuous-on-refinement rather than shipped
# as a case whose refinement prose would be false. The clause is modeled only to
# mirror the guard faithfully (refinement.md, directive 3).
#
# RE-AIMED (admiss-subscript-precond -> admiss-group-roundtrip-nondegenerate +
#   admiss-index-roundtrip-nondegenerate): the sibling asserts an F2P-shaped input
#   satisfies `subscript_render`'s fractional-permission Requires. Neither method
#   here carries a `require` (both pre-conditions regions are empty), so that
#   probe has no precondition to establish; the sharper residual risk on a total
#   carrier is an UNSATISFIABLE or DEGENERATE post-image at exactly the
#   F2P/P2P-shaped input. Each case now discharges that BY EVALUATION, as a live
#   in-region `assert` at the concrete round-trip point, before closing the frozen
#   obligation with the impl after the assert byte-identical to gold's. Both
#   asserts were audit-measured LIVE: negating one conjunct leaves `unsolved
#   goals` (exit 1) under the identical script.
#
# BINDER / CLAUSE COVERAGE (checked with scripts/pbt_coverage.py).
#   renderGroup — ensures G (`out = render (.group elts)`), ONE binder `elts`,
#   TWO arms (empty / non-empty). Three reject witnesses at THREE distinct
#   `elts`: `[atom "1", atom "2"]` (bare-join, non-empty arm),
#   `[]` (empty-open, empty arm — the ONLY empty-list point), `[atom "1"]`
#   (extra-paren, non-empty exact-equality). Both arms attacked; `elts` ranges
#   over {[], singleton, pair} and `elts.length` over {0, 1, 2}. pts (group) = 3.
#   renderIndex — ensures I (`out = render (.index value idx)`), TWO binders
#   `value`, `idx`, TWO arms (direct-members / whole-expression) whose selection
#   is a TWO-CLAUSE conjunction. THREE reject witnesses: inner-parens at
#   (value=`atom "T"`, idx=group `[atom "a", atom "b"]`) attacks the
#   direct-members arm; drop-body at (value=`atom "x"`, idx=`atom "a"`) attacks
#   the whole-expression arm; empty-group at (value=`atom "T"`, idx=group `[]`)
#   attacks the EMPTINESS CONJUNCT of the arm guard on its own (added by audit).
#   `value` ranges over {atom "T", atom "x"} (moved), `idx` over {non-empty group,
#   atom, EMPTY group} — all three shapes the guard distinguishes, and it is the
#   binder that selects the arm. Both arms attacked, both conjuncts of the guard
#   separated (the unpack conjunct being unobservable upstream — see the audit
#   note below). No binder pinned across the reject set. pts (index) = 3. Both
#   obligations are DEFENDED (renderGroup: pos-group-reorder + pos-group-direct +
#   admiss-group-roundtrip-nondegenerate; renderIndex: pos-index-prefix +
#   admiss-index-roundtrip-nondegenerate) and
#   ATTACKED (renderGroup 3 reject, renderIndex 3 reject).
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: both changed
#   renderers are modeled deeply and concretely, validated by G-CONF, so G-AX is
#   vacuous); the sibling's AXIOM_TESTS is likewise empty. This gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
