"""properties.py — G-PBT falsification battery for sympy__sympy-22914 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct printApp`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method emitting the source text of a single
function-application node over a per-code-point string carrier, ``List Char``):

  printApp (head : List Char) (args : List (List Char)) (fallback : List Char)
      return (out : List Char)
    ensures head = "Min".toList → out = renderCall "min".toList args    -- C1
    ensures head = "Max".toList → out = renderCall "max".toList args    -- C2
    ensures head = "Abs".toList → out = renderCall "abs".toList args    -- C3
    ensures head ∉ {"Min","Max","Abs"} → out = fallback                 -- C4

where ``renderCall name args = name ++ "(".toList ++ joinComma args ++
")".toList`` and ``joinComma`` interleaves the rendered operands with ", ".
``renderCall``/``joinComma`` are TRANSPARENT ``def``s spelled out over the
inputs (directive 8), NOT an opaque answer-key: each supported clause reduces to
an ordered concatenation of a fixed builtin name, two literal parens, and the
comma-joined ``args``, so ``decide`` computes it and no rival can "echo an
oracle" — the only way to satisfy a supported clause is to build the exact
call string. There is no consumed axiom and no deep-model reference (the
``axioms`` region is empty; both the recursive operand rendering and the
unchanged surrounding machinery enter as the read-only inputs ``args`` and
``fallback``), so this gate's AXIOM lane is empty.

WHAT THE SPEC DEFENDS. The modeled behavior is the per-node DECISION: the two
newly-mapped heads emit a builtin call with the correct builtin name, the
pre-existing mapped head keeps its builtin call, and EVERY other head is emitted
verbatim as the unchanged machinery would (``fallback``) — nothing but the two
newly-mapped emissions may change. The attack surface is the four-way DOMAIN
PARTITION on ``head``: each of the three mapped heads is pinned by C1/C2/C3 and
every other head by C4. An impl correct on a subset but diverging on one head
class must be rejected.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on all THREE inputs — ``head``, ``args``, ``fallback``:

  * ``head`` selects the clause. Every reject rival is refuted at a specific
    head value; across the battery the witnesses probe "Min", "Max", "Abs" and
    two distinct non-mapped heads, so no head class is left unattacked and the
    ``head`` binder is varied across all four partition cells.
  * ``args`` is the rendered-operand text placed inside every supported call.
    Two rivals mishandle ``args`` specifically — one renders the operands in the
    wrong order, one drops the ", " separator between them — so this binder is
    ABUSED along two independent axes, not merely varied. (The separator rival is
    wrong even on a palindromic operand list, where the order rival is satisfied.)
  * ``fallback`` is the unchanged machinery's emission returned verbatim on the
    non-mapped arm. Two rivals ignore/replace it (emitting divergent text or a
    forged builtin call), so C4's dependence on ``fallback`` is pinned: a
    witness holds ``fallback`` at a value distinct from what the rival returns.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this
    MANDATORY because its list inputs are held at a fractional heap permission
    (``Acc(.,1/2)``) that an impl can illegally overwrite (``joined_args`` is
    read-only). Lean/Velvet are referentially transparent: every input here is
    an immutable value, there is no ``mut`` binder, no heap and no aliasing — so
    there is no read-only field to mutate and no substitute probe. Not
    fabricated (porting map: this class is vacuous here). The behavioural intent
    of the sibling's frame rival (corrupting the rendered operands) is instead
    carried by ``weak-args-reversed``, which mis-orders ``args`` in the emitted
    call — a value-level attack on the same sub-behaviour, refutable by the
    whole-string equality without any permission surface.
  * ADMISSIBILITY (nagini's F2P-shaped self-call proving the precondition) —
    PORTED as ``admiss-obligation-satisfiable-at-f2p``. An earlier revision of
    this battery recorded the lane VACUOUS because "this bundle declares NO
    ``require`` clause, so there is no precondition to admit". The SECOND
    INDEPENDENT AUDIT measured that reason and found it WRONG — not wrong that
    the pre-conditions region is empty (it is), but wrong that this makes the
    lane vacuous. On a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
    obligation being UNSATISFIABLE at exactly an F2P-shaped input: a post-image
    no computation can hit, or a clause set whose conjunction is contradictory
    at that point. That is a real, testable direction, and it is expressible
    here — the shipped case discharges the method's own Hoare ``triple`` at
    three concrete F2P-shaped inputs BY EVALUATION, as ``have``s, before closing
    the frozen obligation verbatim. Built: exit 0. Two FORGERIES of the same
    case (claiming the wrong concrete call string, and claiming the ``fallback``
    is returned at the minimum head) both FAIL to build (exit 1), so the
    ``have``s are load-bearing rather than decorative.
  * UNGROUNDED-ORACLE ECHO — N/A: each supported post-image is a transparent
    ``def`` over the method inputs, not an axiomatized oracle; the ``axioms``
    region is empty.
  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS, re-measured on this
    cell. The nagini sibling carries no divergence case, so there is nothing to
    PORT, and successive audits corrected the reason recorded here twice over.
    An earlier revision of this battery claimed this bundle
    sets ``loom.semantics.termination "partial"``. That is FALSE: the frozen
    solution's line 4 reads ``"total"``. Under ``"total"`` the naive diverging
    rival IS rejected — a loop with no measure fails with ``Decreasing
    annotations are required in total correctness semantics`` (built: exit 1) —
    so the disposition the false claim implied (a blanket vacuous-verification
    hole) does not describe this cell.

    Nor does the NARROWER form survive, and that is the second correction. A
    later revision of this bullet claimed the ``total`` obligation accepts ANY
    measure expression and never proves it strictly decreases, so that ``while
    True`` + ``done_with False`` + ``decreasing i`` with ``i := i + 1``,
    returning an unambiguously WRONG string, VERIFIES at exit 0. RETRACTED on
    measurement: that exact shape is REJECTED, exit 1, on the measure's own
    descent goal, ``case «decreasing_1: i» ... ⊢ i + 1 < i``. The obligation is
    genuinely emitted because both of the frozen header's lines select the total
    scope (line 4's ``set_option loom.semantics.termination "total"`` itself opens
    ``TotalCorrectness``, and the file opens it explicitly), and
    ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure`` and
    emits ``⌜measure b' < measure b⌝``; only the ``PartialCorrectness`` twin takes
    a measure and drops it. So no unreachable exit launders a wrong answer here.

    The class is therefore closed by the spec rather than a hole, and it is still
    not shippable as a reject case, for WITNESS mechanics alone: the no-measure
    form makes the rival's own file uncompilable, so a witness cannot elaborate
    against it, and a measure-carrying loop rival's un-normalised ``forIn
    Lean.Loop.mk`` term defeats a witness of this battery's shape (measured:
    ``decide`` on the loop rival's tester gets stuck, ``did not reduce to
    `isTrue` or `isFalse` ``, the exact ``witness-undecided`` class the gate
    screens for). Nothing is owed, and no ``spec_holes`` entry is filed.
  * AXIOM lane (nagini's 2 deep-model soundness/containment probes) — DROPPED.
    The axiom lane is G-AX's job; this bundle declares no axioms and no
    deep-model references, and this gate ignores ``AXIOM_TESTS`` regardless.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``printAppTester head args fallback = false`` says the extracted program's
result violates the postcondition at that concrete input. It is checked in a
file whose ``prove_correct`` block has been stripped (so no tactic script can
mask the verdict) and there are no ``require`` clauses, so every input reaches
the postcondition. ``List Char`` literals via ``"…".toList`` and ``List (List
Char)`` operand lists are fully concrete, so ``decide`` settles the whole
equality — no opaque term, no conditioning, no head binders (hence no
consistency obligation). Every witness below was confirmed with two real builds:
it ELABORATES against its rival (``printAppTester … = false`` decides to ``true``
there — the rival's output violates the clause) and FAILS against the frozen
solution (gold's tester decides to ``true``, so ``= false`` is refuted with
``Tactic `decide` proved that the proposition … is false``).

INDEPENDENT AUDIT (two, by different auditors, neither of whom wrote the port).
Every witness was rebuilt through the gate's own ``witness_file`` and built twice
(rival exit 0, gold exit 1, every one), and each gold-side failure read to
confirm it is a SEMANTIC refutation naming the concrete input rather than a
missing identifier or a type error. New wrong impls and new correct reshapes were
written and built to probe the spec from both sides.

The SECOND audit additionally ran the FORGERY test on all seven reject cases
(each witness rebuilt with its claim flipped, against both subjects): every pair
INVERTED, which is what proves these rejections attest to the spec rather than to
a tactic mismatch. It found no hole in either direction — 5 new wrong impls all
rejected, 5 new correct reshapes all verified — but it did find and repair TWO
FALSE PROSE CLAIMS, both of which had been used to retire a lane rather than test
it: this file claimed the bundle sets ``termination "partial"`` when the frozen
solution sets ``"total"``, and claimed the ADMISSIBILITY lane vacuous on a ground
that does not hold on a total carrier. The admissibility case now ships. The
full ledger, with every exit code observed and the one TOOLING limit found in
the Velvet WP generator, is in the accounting block at the foot of this file.

DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and CLOSED
BY THE SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``if`` over immutable values, no loop and no recursion), so
there is no control flow here to make diverge: a diverging rival cannot be
obtained by mutating this body, it has to bring a loop of its own. When it
does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-22914"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE impl body (comment lines + the nested
# ---- if/else ladder); lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean (both asserted at
# ---- load by _swap). Anchoring on the whole body keeps every surgery inside
# ---- the elided impl region — the frozen spec (the `method` header, the four
# ---- `ensures` clauses, and the `pure` region defining renderCall/joinComma)
# ---- is never touched, so same_spec holds by construction. ----
_IMPL = (
    "    -- Look up the head among the functions that have a direct Python builtin\n"
    "    -- equivalent and emit `<builtin>(rendered args)`. `Min`/`Max` map to the\n"
    "    -- builtins `min`/`max`; the absolute value `Abs` maps to `abs` (the\n"
    "    -- pre-existing entry). Anything without a builtin equivalent is emitted by\n"
    "    -- the unchanged surrounding machinery, whose output is `fallback`.\n"
    '    if head = "Min".toList then\n'
    '      return renderCall "min".toList args\n'
    "    else\n"
    '      if head = "Max".toList then\n'
    '        return renderCall "max".toList args\n'
    "      else\n"
    '        if head = "Abs".toList then\n'
    '          return renderCall "abs".toList args\n'
    "        else\n"
    "          return fallback"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- proof-body anchor. The frozen `prove_correct` tactic body, which the
# ---- consumer spec view ELIDES (only the `prove_correct printApp` header is
# ---- part of the obligation, and it survives byte-identical). The
# ---- admissibility case prepends `have`s to this body and then closes the
# ---- frozen obligation with the frozen script verbatim, so same_spec holds and
# ---- the obligation is reproven, not weakened. ----
_PROOF = "prove_correct printApp by\n  loom_solve\n  all_goals simp_all"


def _with_proof(new_proof: str) -> str:
    """Solution.lean with ONLY the elided prove_correct tactic body replaced."""
    return _swap(_BASE, _PROOF, new_proof)


# ---- ADMISSIBILITY body. Discharges printApp's OWN Hoare triple at three
# ---- concrete F2P-shaped inputs BY EVALUATION, as `have`s, BEFORE the frozen
# ---- `loom_solve; all_goals simp_all` closes the real obligation verbatim.
# ---- Each `have` names a literal head/args/fallback tuple and evaluates the
# ---- emitted text down to a concrete string, so it fails if the obligation is
# ---- unsatisfiable at that point.
_PROOF_ADMISS = (
    "prove_correct printApp by\n"
    "  -- The obligation is SATISFIABLE at the newly-mapped minimum head: the\n"
    "  -- method's own triple at that concrete input evaluates to the exact\n"
    "  -- builtin call text, for EVERY fallback (so the supported arm cannot be\n"
    "  -- reached only by accident of some particular fallback value).\n"
    "  have hadmMin : ∀ fb : List Char,\n"
    '      triple True (printApp "Min".toList ["a".toList, "b".toList] fb)\n'
    '        (fun out => out = renderCall "min".toList ["a".toList, "b".toList]\n'
    '                  ∧ out = "min(a, b)".toList) := by\n'
    "    intro fb\n"
    "    simp [printApp, triple, wp_pure, renderCall, joinComma]\n"
    "  -- ...and at the other newly-mapped head.\n"
    "  have hadmMax : ∀ fb : List Char,\n"
    '      triple True (printApp "Max".toList ["a".toList, "b".toList] fb)\n'
    '        (fun out => out = renderCall "max".toList ["a".toList, "b".toList]\n'
    '                  ∧ out = "max(a, b)".toList) := by\n'
    "    intro fb\n"
    "    simp [printApp, triple, wp_pure, renderCall, joinComma]\n"
    "  -- ...and on the verbatim arm, where the obligation demands the unchanged\n"
    "  -- machinery's own emission come back untouched.\n"
    "  have hadmOther :\n"
    '      triple True (printApp "f".toList ["x".toList] "f(x)".toList)\n'
    '        (fun out => out = "f(x)".toList) := by\n'
    "    simp [printApp, triple, wp_pure, renderCall, joinComma]\n"
    "  loom_solve\n"
    "  all_goals simp_all"
)


# ---- witness preamble: reach the contract through Velvet's tester machinery. ----
_TESTER = (
    "extract_program_for printApp\n"
    "prove_precondition_decidable_for printApp\n"
    "prove_postcondition_decidable_for printApp\n"
    "derive_tester_for printApp\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both verified out-of-band with a
    # real build against the frozen `prove_correct printApp by loom_solve;
    # all_goals simp_all` script.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # The dispatch order is permuted: the pre-existing mapped head is checked
        # FIRST, then the two others, then the verbatim emission. Same values,
        # different control flow. Ports the nagini branch-reorder positive.
        "module": _with_impl(
            "    -- Reordered dispatch: the pre-existing builtin head is checked first, then\n"
            "    -- the two other builtin-mapped heads; anything else keeps the unchanged\n"
            "    -- emission.\n"
            '    if head = "Abs".toList then\n'
            '      return renderCall "abs".toList args\n'
            "    else\n"
            '      if head = "Min".toList then\n'
            '        return renderCall "min".toList args\n'
            "      else\n"
            '        if head = "Max".toList then\n'
            '          return renderCall "max".toList args\n'
            "        else\n"
            "          return fallback"),
        "rationale": "structurally-different (dispatch branches permuted so the "
                     "pre-existing mapped head is tested first) but behaviourally "
                     "identical impl must verify against all four ensures clauses. "
                     "The branches are mutually exclusive so reordering preserves "
                     "every value; the frozen proof closes the byte-identical "
                     "obligation. If it fails to verify, the spec is over-fit to one "
                     "branch order => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-disjunction-guard",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different: one disjunctive guard gathers the three mapped
        # heads, a let-bound name-selection ladder picks the builtin name, and the
        # else arm keeps the verbatim emission. Same values, different shape.
        "module": _with_impl(
            "    -- Structurally different, behaviourally identical: gather the builtin-mapped\n"
            "    -- heads under one guard and select the builtin name, otherwise keep the\n"
            "    -- unchanged emission.\n"
            '    if head = "Min".toList ∨ head = "Max".toList ∨ head = "Abs".toList then\n'
            "      let nm : List Char :=\n"
            '        if head = "Min".toList then "min".toList\n'
            '        else if head = "Max".toList then "max".toList\n'
            '        else "abs".toList\n'
            "      return renderCall nm args\n"
            "    else\n"
            "      return fallback"),
        "rationale": "a structurally-different CORRECT impl: a single disjunctive "
                     "guard over the three mapped heads plus a let-bound name-selection "
                     "ladder, versus the frozen nested ladder. Observationally "
                     "identical on every input, so all four ensures clauses hold; the "
                     "frozen proof closes the byte-identical obligation. Must verify, "
                     "else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — ADDED BY THE SECOND AUDIT (attack F). The lane was recorded
    # VACUOUS on the ground that the bundle declares no `require` clause. That
    # ground is a measured MISTAKE: on a total carrier the PRECOND-TOO-STRONG
    # analogue is the obligation being UNSATISFIABLE at an F2P-shaped input, which
    # an empty pre-conditions region does not make vacuous. This case tests that
    # direction directly, at three concrete input points, by evaluation.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-f2p",
        "kind": "admissibility",
        "expect": "verify",
        # Only the ELIDED prove_correct tactic body changes; the impl is the frozen
        # one and the spec view (method header, four ensures clauses, pure region)
        # is untouched, so same_spec holds and the frozen obligation is closed
        # verbatim by the frozen script AFTER the admissibility haves.
        "module": _with_proof(_PROOF_ADMISS),
        "rationale": "PASS SOURCE = printApp's own Hoare triple is SATISFIABLE at "
                     "three concrete F2P-shaped inputs, each discharged BY "
                     "EVALUATION as an in-proof `have` before the frozen "
                     "`loom_solve; all_goals simp_all` closes the real obligation "
                     "verbatim. `hadmMin`/`hadmMax` evaluate the method at the two "
                     "newly-mapped heads over a UNIVERSALLY QUANTIFIED fallback and "
                     "close the post-image both as `renderCall` applied to the "
                     "operands AND as the fully-evaluated concrete call text, so the "
                     "clause is shown reachable by an actual computation rather than "
                     "restated; `hadmOther` does the same on the verbatim arm, where "
                     "the obligation demands the unchanged machinery's emission come "
                     "back untouched. If any of those post-images were unsatisfiable "
                     "at its input — a clause no computation can hit, or a clause set "
                     "contradictory at that point — the `have` could not be "
                     "discharged and this case would FAIL => PRECOND-TOO-STRONG / "
                     "SPEC-UNSATISFIABLE. NOT degenerate (the trap this lane falls "
                     "into): it is not `module = _BASE` re-running G-VERIFY, and the "
                     "`have`s are load-bearing — two FORGERIES of this same case, one "
                     "claiming the wrong concrete call text (`min(ab)`) and one "
                     "claiming the fallback is returned at the minimum head, both "
                     "FAIL to build, so the tactic is deciding the claim and not "
                     "waving it through.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (ELABORATES against the rival, FAILS against gold — both
    # halves confirmed out-of-band with real builds) and the refinement argument
    # for why its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-drop-max",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug (half of it): only the minimum and pre-existing
        # absolute-value heads are mapped; the maximum head falls through to the
        # verbatim emission. Correct on Min/Abs/other, wrong on Max.
        "module": _with_impl(
            "    -- ADVERSARIAL: only the minimum and absolute-value heads are mapped; the\n"
            "    -- maximum head falls through to the unchanged emission.\n"
            '    if head = "Min".toList then\n'
            '      return renderCall "min".toList args\n'
            "    else\n"
            '      if head = "Abs".toList then\n'
            '        return renderCall "abs".toList args\n'
            "      else\n"
            "        return fallback"),
        "refinement": "adds only ONE of the two new builtin mappings — the maximum "
                      "head is left unmapped, so its faithful real counterpart emits "
                      "the maximum node via the unchanged machinery (a non-call "
                      "rewrite form), NOT the builtin call the acceptance test demands. "
                      "The F2P test asserts the maximum node renders as its builtin "
                      "call, so this partial patch would NOT resolve.",
        "rationale": "REJECT from C2 (head = Max → out = renderCall \"max\" args): "
                     "the rival returns `fallback` for the maximum head, but the "
                     "post-image demands the builtin maximum call built from `args`. "
                     "Correct on the Min/Abs/other sub-domain, wrong on the Max cell "
                     "(partial-domain). Refuted at head = \"Max\" with a `fallback` "
                     "value distinct from the required call.",
        "witness": _witness('printAppTester "Max".toList ["x".toList] "Max(x)".toList'),
    },
    {
        "id": "weak-swap-min-max",
        "kind": "uniqueness",
        "expect": "reject",
        # Both new heads are mapped (the domain partition is honoured) but the two
        # builtin names are SWAPPED: minimum renders as the maximum builtin and
        # vice versa. Correct on Abs/other, wrong on both Min and Max.
        "module": _with_impl(
            "    -- ADVERSARIAL: the minimum and maximum builtin names are swapped.\n"
            '    if head = "Min".toList then\n'
            '      return renderCall "max".toList args\n'
            "    else\n"
            '      if head = "Max".toList then\n'
            '        return renderCall "min".toList args\n'
            "      else\n"
            '        if head = "Abs".toList then\n'
            '          return renderCall "abs".toList args\n'
            "        else\n"
            "          return fallback"),
        "refinement": "maps the minimum head to the maximum builtin and vice versa. "
                      "Its faithful real counterpart renders the minimum node as "
                      "`max(...)` — the WRONG builtin — so the acceptance test that "
                      "reads the minimum node back as its own builtin call fails; it "
                      "would NOT resolve.",
        "rationale": "REJECT from C1 (head = Min → out = renderCall \"min\" args): "
                     "the rival emits the maximum builtin name for the minimum head, "
                     "so the rendered call differs from the pinned one. Honours the "
                     "domain partition (both heads mapped) but fails the value clause. "
                     "Refuted at head = \"Min\" with a two-operand `args` (the builtin "
                     "name differs regardless of the operands).",
        "witness": _witness('printAppTester "Min".toList ["x".toList, "y".toList] "z".toList'),
    },
    {
        "id": "weak-abs-wrong-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the PRE-EXISTING mapped head (the clause the fix did not touch):
        # the absolute-value head renders with a wrong builtin name. Correct on
        # Min/Max/other, wrong on Abs.
        "module": _with_impl(
            "    -- ADVERSARIAL: the absolute-value head renders with a wrong builtin name.\n"
            '    if head = "Min".toList then\n'
            '      return renderCall "min".toList args\n'
            "    else\n"
            '      if head = "Max".toList then\n'
            '        return renderCall "max".toList args\n'
            "      else\n"
            '        if head = "Abs".toList then\n'
            '          return renderCall "ans".toList args\n'
            "        else\n"
            "          return fallback"),
        "refinement": "renders the absolute-value head with a corrupted builtin name. "
                      "It is NOT the modeled edit, which adds the two new mappings and "
                      "leaves the pre-existing absolute-value entry untouched; a "
                      "counterpart that rewrote that entry changes behaviour the "
                      "conformance differential confirms is unchanged, so it is not a "
                      "faithful counterpart of the modeled edit. "
                      "AUDIT NOTE (corrected): an earlier version of this refinement "
                      "claimed the corruption trips a PASS_TO_PASS test. That is FALSE "
                      "for this instance and is not what makes the case valid — the "
                      "recorded F2P and P2P sets contain no assertion on the "
                      "absolute-value rendering (checked at the base commit: 0 "
                      "occurrences across all 17 P2P functions and the F2P function). "
                      "This rival is therefore rejected on SPEC grounds only: it "
                      "violates C3, a clause the conformance differential independently "
                      "validates against real behaviour. Its rejection attests to the "
                      "spec pinning the pre-existing mapped head, NOT to a test "
                      "regression.",
        "rationale": "REJECT from C3 (head = Abs → out = renderCall \"abs\" args): "
                     "the post-image pins the builtin name exactly; emitting a "
                     "different name makes the rendered call differ. Attacks the "
                     "pre-existing supported clause the two new mappings did not "
                     "touch, so that clause is not left untested. Refuted at "
                     "head = \"Abs\".",
        "witness": _witness('printAppTester "Abs".toList ["x".toList] "z".toList'),
    },
    {
        "id": "weak-args-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level attack on `args`: the minimum head renders its operands in
        # REVERSED order. Correct shape (right builtin, right parens, right head
        # class) but the operand text is mis-ordered. Carries the behavioural
        # intent of the sibling's frame-mutation rival (corrupting the rendered
        # operands) on a referentially-transparent carrier.
        "module": _with_impl(
            "    -- ADVERSARIAL: the minimum head reverses the rendered operand order.\n"
            '    if head = "Min".toList then\n'
            '      return renderCall "min".toList args.reverse\n'
            "    else\n"
            '      if head = "Max".toList then\n'
            '        return renderCall "max".toList args\n'
            "      else\n"
            '        if head = "Abs".toList then\n'
            '          return renderCall "abs".toList args\n'
            "        else\n"
            "          return fallback"),
        "refinement": "reverses the rendered operand order inside the minimum call. "
                      "Its faithful real counterpart emits the operands in the wrong "
                      "order (`min(b, a)` for `min(a, b)`), a different expression, so "
                      "the acceptance test that reads back the exact call string fails; "
                      "it would NOT resolve. This is the value-level analogue of the "
                      "sibling's read-only-operand-corruption rival.",
        "rationale": "REJECT from C1 via the `args` binder: the post-image places the "
                     "operands in their given order inside the call, the rival reverses "
                     "them, so the rendered strings differ for any `args` that is not a "
                     "palindrome (≥2 distinct operands). This is the ONLY rival that "
                     "ABUSES `args` (the others thread it through unchanged), so the "
                     "operand binder is attacked. Refuted at head = \"Min\", "
                     'args = ["a", "b"] (a distinct input point from the swap '
                     "rival, which also attacks C1 but leaves `args` intact).",
        "witness": _witness('printAppTester "Min".toList ["a".toList, "b".toList] "z".toList'),
    },
    {
        "id": "weak-unsupported-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C4: a non-mapped head emits divergent text instead of the
        # unchanged machinery's verbatim `fallback`. Correct on all three mapped
        # heads, wrong on the verbatim arm.
        "module": _with_impl(
            "    -- ADVERSARIAL: a non-mapped head emits divergent text instead of the\n"
            "    -- unchanged machinery's emission.\n"
            '    if head = "Min".toList then\n'
            '      return renderCall "min".toList args\n'
            "    else\n"
            '      if head = "Max".toList then\n'
            '        return renderCall "max".toList args\n'
            "      else\n"
            '        if head = "Abs".toList then\n'
            '          return renderCall "abs".toList args\n'
            "        else\n"
            '          return "#".toList ++ joinComma args'),
        "refinement": "the modeled edit changes ONLY the two new builtin mappings; a "
                      "non-mapped head must keep the unchanged machinery's emission. "
                      "A counterpart that altered what an unknown head prints (here "
                      "prefixed, comma-joined text instead of the verbatim `fallback`) "
                      "would mis-print every unknown function while leaving the "
                      "acceptance test's mapped heads correct — a regression on the "
                      "no-change contract, so it would NOT resolve.",
        "rationale": "REJECT from C4 (head not mapped → out = fallback): the rival "
                     "returns fabricated text rather than the read-only `fallback`, so "
                     "the strings differ whenever `fallback` is not exactly that "
                     "fabricated text. Pins C4's dependence on the `fallback` binder. "
                     "Refuted at a non-mapped head with a `fallback` value distinct "
                     "from the rival's output.",
        "witness": _witness('printAppTester "f".toList ["x".toList] "f(x)".toList'),
    },
    {
        "id": "weak-unsupported-as-min",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C4 differently: a non-mapped head is rendered AS the minimum
        # call form (collapsing an unknown function onto a supported builtin call)
        # instead of the verbatim `fallback`. Near-miss to weak-unsupported-diverge
        # but forges a well-formed builtin call, refuted at a distinct input.
        "module": _with_impl(
            "    -- ADVERSARIAL: a non-mapped head is rendered as the minimum call form.\n"
            '    if head = "Min".toList then\n'
            '      return renderCall "min".toList args\n'
            "    else\n"
            '      if head = "Max".toList then\n'
            '        return renderCall "max".toList args\n'
            "      else\n"
            '        if head = "Abs".toList then\n'
            '          return renderCall "abs".toList args\n'
            "        else\n"
            '          return renderCall "min".toList args'),
        "refinement": "collapses every unknown head onto the minimum builtin call. "
                      "Its faithful real counterpart would mis-print every unsupported "
                      "function as `min(...)`, corrupting outputs the existing suite "
                      "renders via the unchanged machinery — a regression on the "
                      "no-change contract, so it would NOT resolve.",
        "rationale": "REJECT from C4 (head not mapped → out = fallback): the rival "
                     "forges a minimum builtin call from `args` rather than returning "
                     "the read-only `fallback`, so the strings differ whenever "
                     "`fallback` is not that forged call. A near-miss to "
                     "weak-unsupported-diverge (a well-formed call vs. arbitrary text), "
                     "refuted at a DISTINCT non-mapped head and operand list so it "
                     "probes its own input point.",
        "witness": _witness('printAppTester "g".toList ["x".toList, "y".toList] "g(x, y)".toList'),
    },
    {
        "id": "weak-args-no-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). A second, INDEPENDENT attack on the `args`
        # binder: the operands are concatenated with NO separator between them
        # rather than mis-ordered. This is a failure mode no other rival covers —
        # weak-args-reversed permutes the operand SEQUENCE (and is satisfied by any
        # palindromic args), whereas this one corrupts the JOIN itself and so is
        # wrong for every args with >= 2 operands regardless of their order. It
        # pins the ", " separator that joinComma contributes to each supported
        # clause, which no previously shipped witness discriminates.
        "module": _with_impl(
            "    -- ADVERSARIAL: the minimum call omits the argument separator,\n"
            "    -- concatenating the rendered operands with nothing between them.\n"
            '    if head = "Min".toList then\n'
            '      return "min".toList ++ "(".toList ++ args.foldr (fun a acc => a ++ acc) [] ++ ")".toList\n'
            "    else\n"
            '      if head = "Max".toList then\n'
            '        return renderCall "max".toList args\n'
            "      else\n"
            '        if head = "Abs".toList then\n'
            '          return renderCall "abs".toList args\n'
            "        else\n"
            "          return fallback"),
        "refinement": "emits the minimum call with its operands run together instead "
                      "of separated. Its faithful real counterpart renders a "
                      "two-operand minimum node as `min(xy)` rather than `min(x, y)` — "
                      "not the text the acceptance test reads back — so it would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 via the `args` binder and specifically via the "
                     "SEPARATOR that joinComma interleaves: the post-image places ', ' "
                     "between consecutive rendered operands, the rival places nothing, "
                     "so the strings differ for every args with two or more operands. "
                     "Distinct from weak-args-reversed, which permutes the operand "
                     "order and is refutable only when the operand list is not a "
                     "palindrome: this rival is wrong even on a palindromic args, so it "
                     "probes joinComma's separator rather than its order. Refuted at "
                     'head = "Min", args = ["p", "q"] — an input tuple no other case '
                     "uses.",
        "witness": _witness('printAppTester "Min".toList ["p".toList, "q".toList] "w".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness rivals) plus a 2-case AXIOM lane. This
# bundle models the SAME functional core — the per-node emission decision over
# the head/args/fallback inputs — over a `List Char` carrier instead of the
# sibling's `List[int]` code-point encoding with a name_code integer domain and
# @Pure is_supported/target_name/call_render helpers.
#
#   sibling case                 -> here                            disposition
#   --------------------------------------------------------------------------
#   pos-control-reorder          -> pos-branch-reorder              PORTED
#   (no sibling)                 -> pos-disjunction-guard           ADDED
#   admiss-min                   -> admiss-obligation-satisfiable-at-f2p
#                                                                   PORTED (audit 2)
#   weak-frame-mutate            -> weak-args-reversed              RE-EXPRESSED
#   weak-drop-max                -> weak-drop-max                   PORTED
#   weak-swap-minmax             -> weak-swap-min-max               PORTED
#   weak-abs-wrong-name          -> weak-abs-wrong-name             PORTED
#   weak-unsupported-diverge     -> weak-unsupported-diverge        PORTED
#   weak-unsupported-as-min      -> weak-unsupported-as-min         PORTED
#   (no sibling)                 -> weak-args-no-separator          ADDED (audit)
#   AXIOM_TESTS (2)              -> (none)                          DROPPED (G-AX lane)
#
# ---- INDEPENDENT AUDIT (attacks A-G, all re-run with real builds) ----------
# Attack A (statement integrity): every case's module diffed line-by-line against
#   Solution.lean — all 9 modules' hunks lie strictly inside the impl region; the
#   method header, all four `ensures` clauses, the `pure` region and the
#   prove_correct script are byte-identical. No reformatted statement.
# Attack B (witness re-derivation): all six shipped witnesses rebuilt from the
#   gate's own witness_file(); rival exit 0 / gold exit 1 for every one. Each
#   gold-side failure is a SEMANTIC refutation — "Tactic `decide` proved that the
#   proposition printAppTester <input> = false is false" — naming the concrete
#   input, not a missing identifier, type error or timeout. No witness binds a
#   head variable, so none needs a consistency probe (all are literal-input).
# Attack C (wrong vs merely different): each rival is OBSERVABLY distinct from
#   gold — the same witness input that elaborates against the rival is refuted by
#   gold, which is a machine-checked proof of divergence at that point. No rival
#   is definitionally equal to gold; none is vacuous.
# Attack D (SPEC-TOO-WEAK probe): five NEW wrong impls the battery did not
#   contain, all REJECTED by the frozen spec: wrong only on the empty operand
#   list; head matched on its first code point only (so "Mint" collapses onto the
#   min call); operands duplicated; separator dropped (two shapes). Each was given
#   a witness; every one elaborated against its rival and failed on gold. The last
#   is shipped above as weak-args-no-separator. NO spec hole found.
# Attack E (SPEC-TOO-STRONG probe): three NEW correct reshapes, all VERIFIED —
#   the non-mapped arm tested FIRST via the negated conjunction (exit 0 under the
#   frozen tactic); renderCall inlined at each call site (needs the in-scope proof
#   body to unfold the helper: `all_goals simp_all [renderCall]`, exit 0); and an
#   association-table lookup returning via Option.elim (exit 0). Note the
#   `match`-flavoured spelling of that table lookup is rejected by the Velvet WP
#   generator with "Failed to parse an assertion without names: WPGen" — a TOOLING
#   limit on `match` in an impl body, NOT a spec rejection, since the Option.elim
#   spelling of the same function verifies. No faithful correct impl is rejected.
# Attack G (coverage): scripts/pbt_coverage.py reports obl=1 binders=3 pts=6-6 ok
#   pre-repair; the added rival raises the reject lane to 7 distinct input points.
#
# ---- SECOND INDEPENDENT AUDIT (a fresh auditor; every claim below re-measured
# ---- with real builds, 45 in total; exit codes as observed) -----------------
# Attack A re-run MECHANICALLY rather than by eye: each case's module was diffed
#   against Solution.lean with difflib and every changed hunk's GOLD-side line
#   range checked against the parsed `impl` region span (lines 71-87). All 9
#   pre-existing modules: every hunk strictly inside. same_spec True for all;
#   variant_problems [] for all. No reformatted statement, no weakened hypothesis.
# Attack B re-run: all 7 shipped witnesses rebuilt through the gate's own
#   witness_file(). rival exit 0 / gold exit 1, every one. Every gold-side failure
#   is the plain-evaluation form `Tactic `decide` proved that the proposition
#   printAppTester <literal input> = false is false` — a SEMANTIC refutation naming
#   the concrete input. No witness binds a head variable (all_witness_head_binders
#   == [] for all 7), so none needs a consistency probe.
# Attack B' (FORGERY) run on all 7 even though the signatures are plain
#   evaluations and the rule does not require it. For each case a second file
#   differing ONLY in the claim (`= false` -> `= true`) was built against BOTH
#   subjects. Every pair INVERTED: forgery-on-gold exit 0, forgery-on-rival exit 1.
#   So gold's exit code carries full information about the claim — these witnesses
#   are discriminators, not tactic mismatches, and a forged witness asserting gold
#   is CORRECT at these points would NOT have been recorded as `rejected`.
# Attack C: each rival is OBSERVABLY distinct from gold at its witness input, which
#   the inverted forgery pair proves by machine rather than by argument. None is
#   definitionally equal to gold; none vacuous.
# Attack D (SPEC-TOO-WEAK), 5 NEW wrong impls this battery did not contain, aimed
#   at what the shipped rivals leave alone. ALL FIVE REJECTED (exit 1), each with a
#   witness that elaborates on its rival (exit 0) and fails on gold (exit 1):
#   (1) separator correct for 1-2 operands but dropped from the 3rd on (a
#   near-miss the shipped separator rival does not reach); (2) head matched by
#   PREFIX, so "Minimum" collapses onto the min call; (3) parens dropped on the
#   EMPTY operand list only ("min" for "min()"); (4) separator "," without the
#   space — a single-code-point corruption; (5) head matched case-insensitively, so
#   a lowercase "min" head is treated as mapped. NO spec hole found in this
#   direction. (Note on method: (5)'s first witness held `fallback` AT the forged
#   call text, which made it a non-discriminator — rival exit 1 — and re-aiming it
#   at a distinct fallback fixed it. Recorded because it is the same trap the C4
#   rationales warn about, met live.)
# Attack E (SPEC-TOO-STRONG), 5 NEW correct reshapes. ALL FIVE VERIFY (exit 0):
#   the verbatim arm tested FIRST via the negated conjunction; renderCall inlined
#   at all three call sites (needs `all_goals simp_all [renderCall]`); an
#   association-table `List.lookup` + `Option.elim` (a genuinely different
#   algorithm, needs `all_goals simp_all [List.lookup]`); a single-exit let-bound
#   ladder; and a hoisted name binding under one disjunctive guard. No faithful
#   correct impl is rejected — no soundness hole in the spec.
# Attack F (omissions): re-derived per case, see the per-case ledger above. One
#   verdict REVERSED — admissibility, recorded VACUOUS, is EXPRESSIBLE and now
#   ships. The frame/permission verdict is CONFIRMED vacuous (no heap, no `mut`
#   binder in the header; and a `mut` binder edit is not even available to a
#   variant since the header lives in the spec view). The 2-case AXIOM lane is
#   CONFIRMED out of scope (this gate ignores AXIOM_TESTS; the bundle declares no
#   axioms and G-AX is `skip`).
# Attack F' (divergence, judged against the semantics the bundle ACTUALLY sets):
#   the previous revision's `"partial"` claim is FALSE — line 4 reads `"total"`.
#   Corrected above, with the measured consequence: the measure-less diverging
#   rival is REJECTED here (exit 1, `Decreasing annotations are required...`), so
#   this is NOT the blanket vacuous-verification hole the false claim implied. The
#   narrower hole (any measure accepted, decrease never proven) does NOT reproduce
#   either, which RETRACTS what this entry used to record: the exact shape claimed,
#   `while True` + `done_with False` + `decreasing i` over `i := i + 1` with a
#   wrong return, is REJECTED (exit 1) on the measure's own goal,
#   `case «decreasing_1: i» ... |- i + 1 < i`. See the class note above.
# CORRECTED FALSE PROSE, audit 2 (two more, both in the ADVERSARIAL READ block):
#   (1) the `termination "partial"` claim, contradicted by the frozen file's own
#   line 4; (2) the admissibility-vacuous claim, contradicted by a case that
#   builds. Both were reasons recorded for OMITTING work, which is the category
#   where a false claim costs the most — it retires a lane instead of queueing it.
# CORRECTED FALSE PROSE (the one real defect found): weak-abs-wrong-name's
#   refinement claimed its corruption trips a PASS_TO_PASS test. Checked against
#   the base commit: the abs rendering is asserted in NO function of this
#   instance's recorded F2P or P2P sets (0 hits across all 17 P2P functions and
#   the F2P function; the assertions elsewhere in the printing suite belong to
#   other printers and other instances' test sets). Corrected in place; the case
#   now rests on C3 alone, which is where its validity actually came from. The
#   rival itself remains a correct, discriminating reject case.
# NOT A DEFECT, recorded for the reader: the frame/permission claim above is sound
#   on this carrier — pinning a frame with a `mut` binder is not even available to
#   a variant, since the binder lives in the method header and any such edit fails
#   same_spec (verified: variant_problems reports "spec view differs"). So the
#   sibling's permission MECHANISM genuinely has no expression here.
#
# PORTED (positive): pos-control-reorder inverts the dispatch and flattens the
#   name selection — here the reorder tests the pre-existing mapped head first
#   (branches are mutually exclusive, so values are preserved). Verified with a
#   real build against the frozen `loom_solve; all_goals simp_all`.
# ADDED (pos-disjunction-guard): a second CORRECT reshape (one disjunctive guard
#   over the three mapped heads + a let-bound name ladder) so the soundness
#   defence does not rest on a single reshape shape. Verified with a real build.
# PORTED, audit 2 (admissibility): the previous revision recorded this lane
#   VACUOUS because the bundle declares no `require` clause. The reason was
#   measured and is WRONG — an empty pre-conditions region does not make the lane
#   vacuous on a TOTAL carrier, where the PRECOND-TOO-STRONG analogue is the
#   obligation being UNSATISFIABLE at an F2P-shaped input. The sibling's admiss-min
#   witnessed 0<=name_min()<=3 and is_supported(name_min()); there is indeed no
#   integer name-code domain nor is_supported predicate on this carrier, so the
#   sibling's LITERAL assertions do not transfer — but its INTENT (the obligation
#   admits a normal F2P-shaped input) does, and is now carried by
#   admiss-obligation-satisfiable-at-f2p, which discharges printApp's own triple at
#   three concrete inputs by evaluation before closing the frozen obligation
#   verbatim. Built: exit 0. Load-bearing, not decorative: two forgeries of the
#   same case (wrong concrete call text `min(ab)`; fallback returned at the minimum
#   head) both FAIL, exit 1 each. Four earlier spellings were tried and recorded
#   for the next reader — `rw [wp_pure]` after `simp only [printApp, triple]` fails
#   (`Did not find an occurrence of the pattern`, because the reduced guard leaves
#   an un-collapsed `ite`), and a `refine le_trans ?_ (le_refl _)` framing fails
#   too; `simp [printApp, triple, wp_pure, renderCall, joinComma]` is what closes
#   it. That is a TACTIC-SHAPE note, not a carrier limit.
# RE-EXPRESSED (weak-frame-mutate -> weak-args-reversed): the sibling's frame
#   rival appended a code point to the read-only operand text, corrupting the
#   printed arguments (`min(x, y\x07)`) and failing the F2P. Velvet is
#   referentially transparent — no heap, no fractional permission, no `mut`
#   binder — so the permission MECHANISM is vacuous, but its BEHAVIOURAL intent
#   (corrupting the rendered operands so the call string is wrong) is carried by a
#   value-level rival that reverses the operand order inside the minimum call. It
#   is the only rival that abuses the `args` binder, machine-checked to
#   discriminate.
# PORTED (rivals): weak-drop-max (Max unmapped -> C2), weak-swap-minmax (min/max
#   names swapped -> C1/C2), weak-abs-wrong-name (pre-existing head, wrong name ->
#   C3), weak-unsupported-diverge (non-mapped head emits divergent text -> C4),
#   weak-unsupported-as-min (non-mapped head forged as a min call -> C4). Each
#   carries a machine-checked witness that ELABORATES against the rival and FAILS
#   against gold (two real builds per case; gold fails with
#   `decide` proved … is false).
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (the emission decision is spelled out in
#   full over the inputs), so there is nothing to probe and the gate ignores
#   AXIOM_TESTS regardless.
# VACUOUS (frame/permission-mutation MECHANISM): referentially transparent
#   carrier, no `mut` binder, no heap — no read-only field to overwrite. The
#   behavioural attack is preserved as weak-args-reversed (above), not fabricated
#   as a permission probe.
#
# CLAUSE / BINDER COVERAGE of the seven reject witnesses (pts = 7 distinct input
# points; no two rivals share an input tuple):
#   C1 (Min)   attacked by weak-swap-min-max, weak-args-reversed,
#              weak-args-no-separator.
#   C2 (Max)   attacked by weak-drop-max, weak-swap-min-max.
#   C3 (Abs)   attacked by weak-abs-wrong-name.
#   C4 (other) attacked by weak-unsupported-diverge, weak-unsupported-as-min.
#   head  — "Max","Min","Abs","f","g": all four partition cells (three mapped
#           heads + two distinct non-mapped heads) probed.
#   args  — ["x"], ["x","y"], ["x"], ["a","b"], ["x"], ["x","y"], ["p","q"]:
#           ABUSED along TWO independent axes — weak-args-reversed mis-orders the
#           operand sequence, weak-args-no-separator corrupts the ", " join that
#           holds the sequence together. The second is wrong even for a
#           palindromic operand list, where the first is satisfied, so the two
#           attack joinComma's order and its separator separately.
#   fallback — "Max(x)","z","z","z","f(x)","g(x, y)","w": each C4 witness holds it
#           at a value distinct from the rival's forged output, pinning C4's
#           dependence on it.
AXIOM_TESTS = []
