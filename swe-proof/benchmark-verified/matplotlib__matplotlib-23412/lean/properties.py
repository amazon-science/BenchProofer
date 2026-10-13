"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-23412 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_dashRender`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total relation over a boolean guard + a carried pair)
---------------------------------------------------------------------------
A single modeled function reports the stroke style produced while rendering a
shape's dashed outline, from three inputs — a visibility guard and the two
pieces of the configured dash style (a numeric offset and an optional on/off
sequence):

  dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int))
             : Option (Int × Option (List Int))

The postcondition has two independent top-level clauses:

  (C1) visible = false → result = none
       the short-circuit: an invisible shape produces no stroke style.
  (C2) visible = true  → result = some (offset, dashes)
       the visible path reproduces BOTH configured pieces verbatim — the offset
       carried through unchanged (NOT discarded / zeroed) AND the on/off
       sequence copied exactly.

C2 is the LOAD-BEARING clause the F2P exercises: it asserts a shape configured
with a nonzero offset renders with that offset applied, matching an
offset-shifted zero-offset reference. The historical defect zeroed the offset on
the render-time style, so a nonzero configured offset had no visible effect;
C2's ``offset`` component is exactly the discriminator (the analogue of the
nagini head clause ``Result()[0] == phase``).

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models a heap procedure ``render_dash_pattern(phase, onoff)``
that CONSTRUCTS a fresh ``[phase] + onoff`` list element-by-element under
fractional list permissions, and its battery attacks that construction: a
head-zero seed, a drop-last loop bound, a tail-constant append, plus a
frame/permission-mutation rival. This lean carrier is referentially transparent
and models the observable as a pure relation: the render-time style is the
configured ``(offset, dashes)`` pair reproduced verbatim, with an added
visibility short-circuit the nagini model did not carry. The porting map:

  * head-zero / pre-patch offset dropped  → ``reject-offset-zeroed`` (C2 offset).
    This is the actual bug: the offset forced to a constant 0.
  * drop-last on/off element              → ``reject-drop-last-dash`` (C2 dashes).
    The last on/off length is dropped from the reproduced sequence.
  * tail-constant on/off passthrough      → ``reject-dashes-filled-offset``
    (C2 dashes). The on/off entries are overwritten with the offset value
    rather than copied — a value-mask that coincides with the reference only on
    an on/off sequence that already equals a constant-offset run.
  * (no nagini counterpart; carrier-native)→ ``reject-dashes-reversed`` and
    ``reject-solid-produces-nothing``, added by audit to cover the two
    ``dashes`` coordinates the ported rivals left unattacked: sequence ORDER,
    and the ``none`` (solid style) constructor, which this carrier's
    ``Option (List Int)`` has and the nagini ``List[int]`` parameter did not.
  * FRAME / PERMISSION MUTATION rival      → VACUOUS. This backend is
    referentially transparent: no input carries a heap permission, there is no
    read-only half-permission list to overwrite and no aliasing. The nagini
    ``frame-mutation-write-onoff`` rival has no counterpart and NO substitute is
    fabricated (see the port report ``assessment``).
  * UNGROUNDED-ORACLE ECHO                 → VACUOUS. The postcondition is
    GROUNDED: C2 equates the result to ``some (offset, dashes)``, a term built
    only from the inputs; the bundle declares no ``opaque``/``axiom``, so there
    is no answer key to echo. In its place the battery carries honest positive
    controls (``pos-*``) and an admissibility control that MUST verify.

NEW clause this carrier models that nagini did not: the visibility short-circuit
(C1). The lean ``draw`` model has two branches — the early ``none`` return when
invisible, and the visible render path — so C1 is attacked by a dedicated rival
(``reject-ignore-visibility``) that nagini's ``render_dash_pattern`` model (which
had no visibility guard) could not express.

BINDER + CLAUSE COVERAGE. The three input binders are each varied by the reject
witnesses rather than pinned at one input point:

  * ``visible`` — attacked at BOTH polarities: ``reject-ignore-visibility`` is
    refuted at ``visible = false`` (the branch it drops), while the C2 rivals
    are all refuted at ``visible = true``.
  * ``offset``  — ``reject-offset-zeroed`` refuted at ``offset = 5``; the
    C2-dashes rivals vary it further (7, 6) so no rival can hard-code a single
    offset and survive.
  * ``dashes``  — attacked at BOTH constructors of the ``Option`` and in all
    three coordinates of the list. ``reject-drop-last-dash`` refuted on
    ``some [6, 6]`` (LENGTH: dropping the last entry gives ``[6]``),
    ``reject-dashes-filled-offset`` on ``some [1, 1]`` (ELEMENT VALUES; a
    sequence whose entries differ from the offset, so the fill is observable),
    ``reject-dashes-reversed`` on ``some [1, 2]`` (ORDER; asymmetric, since a
    reversal is invisible on the palindrome the F2P uses), and
    ``reject-solid-produces-nothing`` at ``none`` (the solid/unstyled carrier
    point — the other constructor).

Both top-level clauses are defended (POS + ADM verify) and attacked (C1 by
``reject-ignore-visibility``, C2 by the five value rivals). The frozen
postcondition is FUNCTIONAL — it pins a UNIQUE result at every input (both
clauses are equations on ``result`` and their guards are complementary), so any
impl satisfying it is pointwise equal to the frozen one and NO rival that
differs from gold at even one input can verify. That is why every rival here is
refuted by a single ground point: audit-confirmed by proving, against the frozen
file, that two results satisfying the spec at one input are equal and hence that
any verifying impl equals ``implementation_dashRender`` everywhere.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``refine … <;> subst … <;> simp`` is
tuned to the frozen form — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input, stated directly against the spec
predicate at ``decide``-able literals. Each was checked to hold of its rival AND
to FAIL on the frozen solution (so it discriminates rather than asserting a
tautology).

AXIOM lane: EMPTY. meta.json declares no axioms and no deep_model_references; the
modeled behavior is a total computation over the inputs, so there is no
axiom-soundness obligation to probe here (and that lane belongs to G-AX anyway).
The nagini bundle likewise shipped ``AXIOM_TESTS = []``.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23412"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the single impl region and the FULL tactic body of the single
# proof region, so every replacement lands entirely inside the region it edits.
_I_GOLD = (
    "Id.run do\n"
    "  if !visible then\n"
    "    return none\n"
    "  -- The stroke style applied while rendering carries the full configured\n"
    "  -- offset together with the on/off sequence (the offset is honored, not zeroed).\n"
    "  let used : Int × Option (List Int) := (offset, dashes)\n"
    "  return some used"
)
_P_GOLD = (
    "  intro visible offset dashes\n"
    "  refine ⟨fun h => ?_, fun h => ?_⟩ <;>\n"
    "    subst h <;>\n"
    "    simp [implementation_dashRender, Id.run, bind, pure]"
)

assert _I_GOLD in _BASE, "impl anchor drift: implementation_dashRender body not verbatim"
assert _P_GOLD in _BASE, "proof anchor drift: correct_dashRender tactic body not verbatim"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. The
    # `theorem correct_dashRender` STATEMENT is kept byte-identical; the impl is
    # reshaped from the accumulator-style `let used := …; return some used` into
    # an explicit two-branch match, and the proof is closed with core tactics
    # only (no helper lemma, no axiom, no assumption token).
    # =====================================================================
    {
        "id": "pos-match-branches",
        "kind": "soundness",
        "expect": "verify",
        # Spell the two paths as an explicit match on the visibility guard,
        # returning `none` / `some (offset, dashes)` directly, instead of the
        # guarded early-return + local binding. Same value on every input.
        "module": _swap(
            _BASE, _I_GOLD,
            "Id.run do\n"
            "  match visible with\n"
            "  | false => return none\n"
            "  | true => return some (offset, dashes)",
        ),
        "rationale": "a correct reshape that writes the two render paths as an "
                     "explicit match on the visibility guard (none when invisible, "
                     "some (offset, dashes) when visible) must satisfy BOTH clauses "
                     "of the postcondition; if it cannot, the spec is "
                     "SPEC-TOO-STRONG. The frozen tactic body closes the new shape: "
                     "after `subst h` on each polarity, `simp` reduces the match to "
                     "the required `none` / `some (offset, dashes)`.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, so the `∀` is unguarded), so the
    # nagini precondition-admission probe has no binder to attack here; the honest
    # analogue is to discharge the spec predicate at a ground F2P-shaped input (a
    # visible shape with a nonzero offset and a nonempty on/off sequence) by
    # evaluation, inside the proof region, alongside the frozen obligation. If
    # that ground instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the input the F2P exercises. Nothing is assumed: no
    # new declaration, the theorem statement is byte-identical, the ground
    # instance is a `have` inside the existing tactic body.
    # =====================================================================
    {
        "id": "admiss-ground-f2p-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_GOLD,
            "  have _ground : problem_spec_dashRender true 6 (some [6, 6])\n"
            "      (implementation_dashRender true 6 (some [6, 6])) := by\n"
            "    unfold problem_spec_dashRender implementation_dashRender\n"
            "    decide\n"
            + _P_GOLD,
        ),
        "rationale": "the postcondition is discharged at a ground F2P-shaped input "
                     "(a visible shape with a nonzero offset 6 and a nonempty on/off "
                     "sequence [6, 6]) by `decide`, then the frozen obligation is "
                     "closed verbatim. Verifies (else the spec is unsatisfiable at "
                     "the normal input, the analogue of PRECOND-TOO-STRONG). The "
                     "`decide` here is load-bearing, not decoration: audit-checked "
                     "by restating the same `have` with a MISMATCHED result "
                     "(spec at offset 6 against the impl run at offset 7), where "
                     "`decide` refuses and the file fails to elaborate — so this "
                     "control genuinely evaluates the postcondition at the ground "
                     "input rather than closing any goal put in front of it.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break rather than an artifact,
    # and (b) a refutation witness pinning the violation at one concrete input
    # (checked to hold of the rival and to FAIL on the frozen solution).
    # =====================================================================
    {
        "id": "reject-offset-zeroed",
        "kind": "uniqueness",
        "expect": "reject",
        # THE historical defect: the render-time style is built with the offset
        # forced to a constant 0 rather than the configured offset. Agrees with
        # gold when offset == 0, but drops any nonzero configured offset.
        "module": _swap(
            _BASE, _I_GOLD,
            "Id.run do\n"
            "  if !visible then\n"
            "    return none\n"
            "  let used : Int × Option (List Int) := (0, dashes)\n"
            "  return some used",
        ),
        "refinement": "this is the pre-fix behavior: build the render-time style "
                      "with a constant zero offset. A shape configured with a "
                      "nonzero offset then renders identically to a zero-offset "
                      "shape — NOT like the offset-shifted reference the F2P "
                      "compares against — so the image comparison differs and the "
                      "F2P FAILS. The faithful (pre-fix) code does not resolve.",
        "rationale": "REJECT from clause C2 (visible = true → result = "
                     "some (offset, dashes)): at visible = true with offset = 5 the "
                     "spec requires some (5, dashes) and the rival returns "
                     "some (0, dashes). Wrong on the whole nonzero-offset "
                     "sub-domain; the F2P uses a nonzero offset.",
        "witness": (
            "example : ¬ problem_spec_dashRender true 5 (some [6, 6])\n"
            "    (implementation_dashRender true 5 (some [6, 6])) := by\n"
            "  unfold problem_spec_dashRender implementation_dashRender\n"
            "  decide\n"
        ),
    },
    {
        "id": "reject-ignore-visibility",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the visibility short-circuit: produces a stroke style even for an
        # invisible shape. Attacks clause C1, which nagini's model (no visibility
        # guard) could not express. Correct on the visible sub-domain, wrong on
        # every invisible input.
        "module": _swap(
            _BASE, _I_GOLD,
            "Id.run do\n"
            "  let used : Int × Option (List Int) := (offset, dashes)\n"
            "  return some used",
        ),
        "refinement": "a faithful patch that dropped the `if not self.get_visible(): "
                      "return` short-circuit would apply the stroke style — and "
                      "render an outline — for a shape that should produce nothing. "
                      "Any test rendering an invisible shape (expecting an empty "
                      "result) would see a drawn outline and FAIL, so it does not "
                      "resolve. It agrees with gold on every visible shape, so it is "
                      "a true partial-domain miss on the invisible sub-domain.",
        "rationale": "REJECT from clause C1 (visible = false → result = none): at "
                     "visible = false the spec requires none and the rival returns "
                     "some (offset, dashes). This rival is the only one refuted at "
                     "visible = false, so it is what makes the visibility binder "
                     "load-bearing.",
        "witness": (
            "example : ¬ problem_spec_dashRender false 3 (some [2, 4])\n"
            "    (implementation_dashRender false 3 (some [2, 4])) := by\n"
            "  unfold problem_spec_dashRender implementation_dashRender\n"
            "  decide\n"
        ),
    },
    {
        "id": "reject-drop-last-dash",
        "kind": "uniqueness",
        "expect": "reject",
        # Reproduces all but the LAST on/off length (drops the final entry).
        # Correct ONLY where there is no last entry to drop: the solid style
        # (dashes = none, where the map does not fire) and the empty sequence
        # (dropLast [] = []). It is wrong on EVERY nonempty sequence, a singleton
        # included — audit-checked: the witness below, restated at
        # `some [6]`, also elaborates against this rival (dropLast [6] = []), so
        # the sub-domain this agrees with gold on is the empty/solid one only,
        # NOT "empty/solid plus singletons".
        "module": _swap(
            _BASE, _I_GOLD,
            "Id.run do\n"
            "  if !visible then\n"
            "    return none\n"
            "  let used : Int × Option (List Int) := (offset, dashes.map List.dropLast)\n"
            "  return some used",
        ),
        "refinement": "a faithful patch that installed the on/off sequence one "
                      "entry short would hand the renderer a different dash pattern "
                      "for every multi-entry sequence — a (6, [6, 6]) shape would "
                      "render with on/off [6] instead of [6, 6], producing visibly "
                      "different dashing from the reference — so the image "
                      "comparison FAILS and the patch does not resolve.",
        "rationale": "REJECT from clause C2 (visible = true → result = "
                     "some (offset, dashes)): the on/off component is "
                     "dashes.map List.dropLast, not dashes, so at visible = true "
                     "with dashes = some [6, 6] the spec requires some (7, [6, 6]) "
                     "and the rival returns some (7, [6]).",
        "witness": (
            "example : ¬ problem_spec_dashRender true 7 (some [6, 6])\n"
            "    (implementation_dashRender true 7 (some [6, 6])) := by\n"
            "  unfold problem_spec_dashRender implementation_dashRender\n"
            "  decide\n"
        ),
    },
    {
        # AUDIT ADDITION. Gap this closes: every pre-existing reject case pins
        # `dashes` at `some [...]`, so the `none` carrier point — the solid /
        # unstyled outline, one of the two shapes the `Option (List Int)` binder
        # exists to distinguish — was never a refutation point. A rival that is
        # correct on every dashed input and only mishandles the solid one
        # therefore had nothing attacking it. It also probes C1 vs C2
        # INTERACTION: it produces `none` (the invisible-branch answer) on a
        # VISIBLE input, so it is caught only because C2 fixes the visible
        # result independently of the guard.
        "id": "reject-solid-produces-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "Id.run do\n"
            "  if !visible then\n"
            "    return none\n"
            "  if dashes.isNone then\n"
            "    return none\n"
            "  let used : Int × Option (List Int) := (offset, dashes)\n"
            "  return some used",
        ),
        "refinement": "a faithful patch that took the absence of an on/off "
                      "sequence as licence to skip producing a stroke style at "
                      "all would stop rendering the outline of every solidly "
                      "stroked visible shape — the shape would lose its border "
                      "entirely. Any test rendering a solid-styled shape and "
                      "comparing against a reference with a drawn outline sees a "
                      "missing outline and FAILS, so it does not resolve. It "
                      "agrees with gold on every dashed shape, so it is a true "
                      "partial-domain miss on the solid sub-domain.",
        "rationale": "REJECT from clause C2 (visible = true → result = "
                     "some (offset, dashes)): C2 requires a style to be produced "
                     "for EVERY visible shape, so at visible = true with "
                     "dashes = none the spec requires some (5, none) and the "
                     "rival returns none. Refuted at the `none` carrier point, "
                     "which no other case in this battery visits.",
        "witness": (
            "example : ¬ problem_spec_dashRender true 5 none\n"
            "    (implementation_dashRender true 5 none) := by\n"
            "  unfold problem_spec_dashRender implementation_dashRender\n"
            "  decide\n"
        ),
    },
    {
        # AUDIT ADDITION. Gap this closes: the two pre-existing on/off rivals
        # attack LENGTH (drop-last) and ELEMENT VALUES (fill-with-offset), so a
        # rival preserving both — same multiset of ink lengths, same length, only
        # the ORDER permuted — was unattacked. Order is observable here (an
        # on/off sequence is read as alternating ink/gap runs, so permuting it
        # renders a different pattern), and it must be pinned at an ASYMMETRIC
        # sequence: on a palindrome such as the F2P's [6, 6] the reversal is
        # invisible, so this rival would survive a witness stated there — the
        # same blind spot the fill rival documents, in a new coordinate.
        "id": "reject-dashes-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_GOLD,
            "Id.run do\n"
            "  if !visible then\n"
            "    return none\n"
            "  let used : Int × Option (List Int) := (offset, dashes.map List.reverse)\n"
            "  return some used",
        ),
        "refinement": "a faithful patch that installed the on/off sequence in "
                      "reverse would swap which runs are ink and which are gaps "
                      "for any asymmetric sequence — a shape configured on/off "
                      "[1, 2] would render [2, 1], a visibly different dash "
                      "pattern — so the reference image comparison FAILS and the "
                      "patch does not resolve. On a palindromic sequence (the "
                      "F2P's [6, 6]) the reversal is a no-op and the test is "
                      "BLIND to it; only the spec's verbatim passthrough clause, "
                      "read at an asymmetric sequence, catches it.",
        "rationale": "REJECT from clause C2 (visible = true → result = "
                     "some (offset, dashes)): the on/off component is "
                     "dashes.map List.reverse, not dashes, so at visible = true "
                     "with offset = 4 and dashes = some [1, 2] the spec requires "
                     "some (4, [1, 2]) and the rival returns some (4, [2, 1]). "
                     "Length and element multiset are both preserved, so this is "
                     "refuted by the ORDER component of C2 alone.",
        "witness": (
            "example : ¬ problem_spec_dashRender true 4 (some [1, 2])\n"
            "    (implementation_dashRender true 4 (some [1, 2])) := by\n"
            "  unfold problem_spec_dashRender implementation_dashRender\n"
            "  decide\n"
        ),
    },
    {
        "id": "reject-dashes-filled-offset",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-mask: overwrite every on/off entry with the offset value instead
        # of copying the configured sequence. Head (offset) and length are kept
        # correct, so only the on/off-passthrough part of C2 catches it. On a
        # sequence that already equals a constant-offset run the corruption is
        # invisible — the analogue of the nagini tail-constant rival's F2P blind
        # spot — so it must be pinned at a sequence whose entries differ from the
        # offset.
        "module": _swap(
            _BASE, _I_GOLD,
            "Id.run do\n"
            "  if !visible then\n"
            "    return none\n"
            "  let used : Int × Option (List Int) := (offset, dashes.map (fun l => l.map (fun _ => offset)))\n"
            "  return some used",
        ),
        "refinement": "a faithful patch that built the render-time on/off sequence "
                      "from the offset value (filling every entry with the offset "
                      "rather than copying the configured sequence) would corrupt "
                      "the dash pattern of any shape whose on/off sequence differs "
                      "from a constant-offset run, so the reference equivalence the "
                      "F2P asserts breaks and the patch does not resolve. On a "
                      "sequence that already equals a constant-offset run the fill "
                      "coincides with the real sequence and would be BLIND to the "
                      "corruption — only the spec's verbatim passthrough clause "
                      "catches it, which is exactly the value this lane adds over "
                      "the test.",
        "rationale": "REJECT from clause C2 (visible = true → result = "
                     "some (offset, dashes)): the on/off component is every entry "
                     "replaced by the offset, not the configured sequence, so at "
                     "visible = true with offset = 6 and dashes = some [1, 1] the "
                     "spec requires some (6, [1, 1]) and the rival returns "
                     "some (6, [6, 6]).",
        "witness": (
            "example : ¬ problem_spec_dashRender true 6 (some [1, 1])\n"
            "    (implementation_dashRender true 6 (some [1, 1])) := by\n"
            "  unfold problem_spec_dashRender implementation_dashRender\n"
            "  decide\n"
        ),
    },
]

# No AXIOM_TESTS: the modeled behavior is a total relation over the inputs with
# no opaque callee or axiom, so there is nothing for the axiom lane to run
# (the nagini sibling likewise shipped AXIOM_TESTS = []).
AXIOM_TESTS = []
