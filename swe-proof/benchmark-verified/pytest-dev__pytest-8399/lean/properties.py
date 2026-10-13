"""properties.py — G-PBT falsification battery for pytest-dev__pytest-8399 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the name construction as a per-code-point ``List[int]`` fold guarded by
fractional-permission contracts and a termination obligation; this Lean bundle
models the SAME purely-functional core — one total function over the two string
inputs returning the assembled name as ``List Char``. The nagini spec is a
STRUCTURAL conjunction (a length pin, a first-element/marker pin, a carry
clause, plus the grounded listing consequences); the Lean spec collapses those
into the single grounded equality ``result = '_' :: descriptiveName setupName
qualname``, which pins every component at once (the leading marker, the constant
template head/tail, and both string inputs in order). Each nagini case therefore
carries over as an attack on one COMPONENT of that one equality, or is
principled-omitted; the per-case mapping (or its omission reason) is recorded
inline and summarised in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior). The generated fixture name is the
descriptive name made private: an underscore, then the constant template head,
then the first string input, then the constant template tail, then the second
string input — in that order and nothing else. The postcondition pins ``result``
to a single grounded computation over the two inputs, so its independent pinned
components are:

  * the leading private marker (the CHANGED component — the fix that prepends
    the underscore);
  * the constant template head and tail literals;
  * the first string input, carried verbatim in position;
  * the second string input, carried verbatim in position.

The BEHAVIOURAL DISCRIMINATOR (the fix): the assembled name BEGINS with an
underscore, so the consumer's listing rule (which hides only names whose first
character is an underscore) omits the synthesized fixture at the default
verbosity. The pre-fix behavior omitted that leading underscore; the
``weak-no-prepend`` rival below IS that pre-fix behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (a
    write into the read-only borrowed input list) has no expressible instance
    here; no substitute is fabricated. (nagini FRAME-MUTATION case.)

  * TERMINATION / DIVERGENCE — NOT LANDABLE AS A WITNESSED CASE (measured, and
    NOT because the rival is inexpressible). The nagini DIVERGE rival computes
    the correct name and then loops forever before returning it, defeating
    partial correctness; the frozen ``MustTerminate`` precondition is what
    rejects it. The honest state of this lane on THIS carrier, established by
    real builds rather than by argument:

      - the rival IS expressible and IS in scope. A self-recursive
        ``partial def implementation_generatedFixtureName … := implementation_…``
        replaces the impl region; ``partial`` is NOT among the tokens
        ``variant_scope`` bans (those are ``sorry``/``sorryAx``/``admit``/
        ``native_decide``/``Assume``/``Refute``), so the scope check returns no
        problems. It also does NOT verify (exit 1: the frozen ``rfl`` cannot
        equate an opaque ``partial`` constant with the pinned right-hand side).
        So it would be a well-formed ``expect="reject"`` candidate.
      - but no WITNESS can be built against it, so the case cannot be landed
        honestly. A ``partial def`` is compiled to an opaque constant with no
        kernel-reducible equations, so the refutation ``¬ problem_spec … (impl
        …)`` cannot be decided at any concrete input: the rival-side build fails
        with ``simp made no progress`` (exit 1) where the gate REQUIRES exit 0.
        Nor is the hypothesis-conditioning technique available: there is no
        opaque callee whose value the refutation could be stated relative to —
        the divergence is in the impl itself, not in a term the spec mentions.
        A case whose rival-side witness build fails is recorded
        ``witness-unproven`` (inconclusive ⇒ MALFORMED-TESTS), which is strictly
        worse for the artifact than an admitted gap.
      - and the underlying hole does not exist here anyway: this backend has no
        partial-correctness escape. ``lean`` carries no
        ``loom.semantics.termination "partial"`` option (the frozen solution sets
        no ``set_option`` at all), so unlike the velvet lane there is no
        semantics under which a non-terminating impl satisfies the obligation
        vacuously — the diverging rival is REJECTED, as measured above, rather
        than admitted. The known ``partial``-semantics spec hole is scoped to 401
        velvet bundles and explicitly records lean as unaffected.

    Disposition: nothing to ship, and the reason is the witness requirement plus
    the absence of the partial-correctness hole — NOT "inexpressible". Recorded
    this way so a later wave does not re-derive it. (nagini DIVERGE case.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the two inputs and constant
    literals (``descriptiveName`` is a transparent concatenation, NOT an opaque
    oracle). There is no answer key an implementation could echo, so the carrier
    is fully ``decide``-able and every reject witness is refuted by plain
    evaluation at a concrete input — no conditioning on an opaque term is needed.
    In its place the battery carries honest cheapest-implementation POSITIVE
    CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where a pinned component bites: the missing leading marker (the
    fix itself), the wrong marker code point, a corrupted constant template
    literal, a dropped first input, and a truncated second input.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it by ``decide`` (the carrier is transparent, so no
hypothesis-conditioning is required and every witness head binds nothing). Each
was checked with two real builds to HOLD of its rival and to FAIL on the frozen
solution, so it discriminates rather than asserting a tautology.

BINDER / POINT SPREAD. The spec predicate has two input binders — the first
string input (``setupName``) and the second (``qualname``). The five reject
witnesses move both rather than fixing them at one convenient point, and each
rival is refuted at its OWN input (five distinct points): ``weak-wrong-marker``
at the F2P scenario ``("setUpClass","MyTestCase")``; ``weak-no-prepend`` at
``("s","C")``; ``weak-corrupt-qualname`` at ``("a","XY")`` (attacks the SECOND
input — its truncation shows only there); ``weak-drop-setupname`` at
``("tearDown","Foo")`` (attacks the FIRST input — its omission shows only when
that input is non-empty); ``weak-wrong-template`` at ``("setUp","Bar")``. Both
input binders are thus both VARIED across witnesses and directly ATTACKED by a
dedicated rival.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the name is built entirely from constant literals and the two inputs
by concatenation). The nagini ``AXIOM_TESTS`` were also empty; dropped.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-8399"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# positive, the proof region) so same_spec stays byte-identical.

# The marker append (the CHANGED step, the fix that prepends the underscore).
_I_MARKER = '  name := name ++ "_".toList\n'

# The marker append followed by the template-head append (for the merge reshape).
_I_MARKER_HEAD = (
    '  name := name ++ "_".toList\n'
    '  name := name ++ "unittest_".toList\n'
)

# The full ordered body of appends (for the prepend-at-front reshape).
_I_BODY = (
    '  name := name ++ "_".toList\n'
    '  name := name ++ "unittest_".toList\n'
    '  name := name ++ setupName\n'
    '  name := name ++ "_fixture_".toList\n'
    '  name := name ++ qualname\n'
)

# The first-input append.
_I_SETUP = '  name := name ++ setupName\n'

# The second-input append.
_I_QUAL = '  name := name ++ qualname\n'

# The constant template-tail append.
_I_TAIL = '  name := name ++ "_fixture_".toList\n'

# The frozen proof body's opening `intro` (proof region anchor).
_P_INTRO = '  intro setupName qualname\n'

# The WHOLE frozen impl declaration (for a positive that replaces the assembly
# route outright rather than permuting the existing append steps).
_I_DECL = (
    'def implementation_generatedFixtureName\n'
    '    (setupName qualname : List Char) : List Char := Id.run do\n'
    '  let mut name : List Char := []\n'
    + _I_BODY +
    '  return name\n'
)

# The frozen proof's tactic body after the `intro` (for a positive that must
# RE-PROVE rather than reuse the frozen script). Replacing this is admissible:
# `variant_scope` pins the theorem STATEMENT byte-for-byte and lets the tactic
# body differ, precisely so a legitimately reshaped impl can be reproven.
_P_BODY = (
    '  simp only [problem_spec_generatedFixtureName, implementation_generatedFixtureName,\n'
    '    descriptiveName, Id.run, List.append_assoc, List.nil_append]\n'
    '  rfl\n'
)


def _witness(inp, note=""):
    """A reject witness: the spec predicate stated at concrete literal inputs,
    refuted by `decide` (transparent carrier). `inp` is the two `List Char`
    literals in argument order."""
    head = (f"-- {note}\n") if note else ""
    return (
        head +
        "example : ¬ problem_spec_generatedFixtureName\n"
        f"    {inp}\n"
        f"    (implementation_generatedFixtureName {inp}) := by\n"
        "  unfold problem_spec_generatedFixtureName implementation_generatedFixtureName"
        " descriptiveName\n"
        "  simp only [Id.run]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical; the reshapes below preserve
    # the definitional form so the frozen proof still closes (no helper lemma,
    # no axiom, no assumption token introduced).
    #
    # Ports nagini case (1) pos-control-local-reshape: the nagini positive
    # reshaped the append step (compute the element into a temp, build a
    # one-element tail, concatenate) while keeping every invariant, so the
    # prefix-preservation pins still discharged. Here the analogous structural
    # reshapes keep the same value flow into the assembled name.
    # =====================================================================
    {
        "id": "pos-merge-marker-and-head",
        "kind": "soundness",
        "expect": "verify",
        # Merge the leading-marker append and the constant template-head append
        # into a single append of the concatenated literal. Same assembled value
        # on every input, so `result = '_' :: descriptiveName …` still holds and
        # the frozen tactic body closes after the literal reduces.
        "module": _swap(
            _BASE, _I_MARKER_HEAD,
            '  name := name ++ "_unittest_".toList\n',
        ),
        "rationale": "reshapes the assembly by fusing the leading-marker append "
                     "and the constant template-head append into one append of "
                     "the concatenated literal; the assembled name is identical "
                     "on every input, so `result = '_' :: descriptiveName …` "
                     "still holds. Must verify, else the pinned equality is "
                     "SPEC-TOO-STRONG. Proof: the frozen tactic body is retained "
                     "(the fused literal reduces, the proof closes). Ports "
                     "nagini's append-step reshape positive.",
    },
    {
        "id": "pos-prepend-marker-last",
        "kind": "soundness",
        "expect": "verify",
        # Build the whole descriptive name FIRST (no leading marker), then
        # prepend the marker at the front as the last step. Different control
        # flow (marker added last, at the head, rather than first) but the same
        # assembled value; the frozen tactic body still closes.
        "module": _swap(
            _BASE, _I_BODY,
            '  name := name ++ "unittest_".toList\n'
            '  name := name ++ setupName\n'
            '  name := name ++ "_fixture_".toList\n'
            '  name := name ++ qualname\n'
            '  name := "_".toList ++ name\n',
        ),
        "rationale": "reshapes the CHANGED marker step: assemble the descriptive "
                     "name first, then prepend the private marker at the front as "
                     "the final step (rather than appending it first). The "
                     "assembled name is identical on every input, so `result = "
                     "'_' :: descriptiveName …` still holds. Must verify. Defends "
                     "the marker component with a correct reshape whose control "
                     "flow places the marker LAST — the opposite end of the "
                     "computation from the fix's site — a second independent "
                     "positive. NOTE (audit): this reshape, like the one above, "
                     "is DEFINITIONALLY EQUAL to the frozen impl as a function "
                     "(`example : pos = gold := by rfl` elaborates, exit 0), so "
                     "it exercises the pinned equality only up to the kernel's "
                     "own reduction. That is a weak positive on its own; the "
                     "`pos-reverse-assembly` case below is the non-defeq one "
                     "that carries the real SPEC-TOO-STRONG signal.",
    },
    {
        "id": "pos-reverse-assembly",
        "kind": "soundness",
        "expect": "verify",
        # Assemble the name BACKWARDS — every segment reversed and concatenated
        # in reverse order — then reverse the whole thing once at the end. Same
        # value on every input, but NOT definitionally equal to the frozen impl:
        # the frozen `rfl` cannot close it (measured: exit 1, `Tactic 'rfl'
        # failed`; and `example : e4 = gold := by rfl` fails too), so the case
        # must genuinely RE-PROVE the obligation via `List.reverse_append`. That
        # is what makes it a real soundness probe rather than a restatement: a
        # spec that pinned the assembly ROUTE rather than the assembled VALUE
        # would reject it.
        "module": _swap(
            _swap(
                _BASE, _I_DECL,
                'def implementation_generatedFixtureName\n'
                '    (setupName qualname : List Char) : List Char :=\n'
                '  (qualname.reverse ++ "_fixture_".toList.reverse ++ setupName.reverse\n'
                '    ++ "unittest_".toList.reverse ++ "_".toList.reverse).reverse\n',
            ),
            _P_BODY,
            '  simp [problem_spec_generatedFixtureName, implementation_generatedFixtureName,\n'
            '    descriptiveName, List.reverse_append, List.append_assoc]\n',
        ),
        "rationale": "a correct reshape that is NOT definitionally equal to the "
                     "frozen impl: the name is assembled from reversed segments "
                     "in reverse order and reversed once at the end, so the "
                     "frozen `rfl` does not close it and the obligation is "
                     "re-proven from `List.reverse_append`. Must verify, else the "
                     "pinned equality is SPEC-TOO-STRONG — it would be pinning "
                     "the assembly ROUTE rather than the assembled VALUE. This is "
                     "the battery's only positive whose correctness the kernel "
                     "does not get for free; the other two are defeq to the "
                     "frozen impl and so cannot detect that class of "
                     "over-strength.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis
    # (the modeled behavior is total, so `∀` is unguarded), so the nagini
    # precondition-admission probe has no binder to attack here; the honest
    # analogue is to discharge the spec predicate by evaluation at the ground
    # F2P input (the reported `setUpClass` / `MyTestCase` scenario) alongside the
    # frozen obligation. Ports nagini case (6) admissibility-fstring-label.
    # =====================================================================
    {
        "id": "admiss-ground-f2p-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P input by evaluation (a `have`),
        # then close the frozen obligation verbatim. Nothing is assumed: no new
        # declaration, statement byte-identical, the ground instance is a `have`
        # inside the existing tactic body.
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _ground : problem_spec_generatedFixtureName "setUpClass".toList '
            '"MyTestCase".toList\n'
            '      (implementation_generatedFixtureName "setUpClass".toList '
            '"MyTestCase".toList) := by\n'
            '    unfold problem_spec_generatedFixtureName '
            'implementation_generatedFixtureName descriptiveName\n'
            '    simp only [Id.run]; decide\n'
            + _P_INTRO,
        ),
        "rationale": "the obligation is discharged at the ground F2P input (the "
                     "reported `setUpClass` / `MyTestCase` scenario) by "
                     "evaluation, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior is unsatisfiable at "
                     "exactly the input the F2P exercises — the analogue of "
                     "PRECOND-TOO-STRONG / a vacuous precondition). Nothing is "
                     "assumed: no new declaration, the theorem statement is "
                     "byte-identical, and the ground instance is a `have` inside "
                     "the existing tactic body. Ports nagini's admissibility "
                     "probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, checked to hold of the rival and fail on gold.
    # =====================================================================

    # ---- the pre-patch behavior itself: no leading marker (nagini NO-PREPEND) --
    {
        "id": "weak-no-prepend",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the leading-marker append entirely: assemble the bare descriptive
        # name with no private marker. This IS the pre-patch (buggy) behavior.
        "module": _swap(_BASE, _I_MARKER, ""),
        "refinement": "this IS the pre-patch behavior — the generated name keeps "
                      "no leading underscore, so the consumer's listing rule "
                      "(which hides only names whose first character is an "
                      "underscore) SHOWS the synthesized fixture at the default "
                      "verbosity and it prints its no-documentation line. That is "
                      "exactly the reported bug; by construction it does NOT "
                      "resolve the F2P. A verifying no-marker impl is the most "
                      "basic SPEC-TOO-WEAK.",
        "rationale": "REJECT from the leading-marker component of the pinned "
                     "equality: the spec requires `result` to begin with `'_'` "
                     "and the rival omits it, so `result` differs on every input. "
                     "Refuted at the short input ('s','C'); moves both binders to "
                     "single-character values distinct from every other witness.",
        "witness": _witness(
            '"s".toList "C".toList',
            "Pre-patch behavior: the assembled name lacks the leading marker, so "
            "it differs from the spec's `'_' :: …` at the very first character. "
            "Fully concrete; decidable.",
        ),
    },

    # ---- wrong marker code point (nagini WRONG-MARKER) ----
    {
        "id": "weak-wrong-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # Prepend a DIFFERENT separator ('.') instead of the private marker '_'.
        "module": _swap(
            _BASE, _I_MARKER, '  name := name ++ ".".toList\n',
        ),
        "refinement": "a faithful real patch that prefixed the generated name "
                      "with any character other than the private marker (e.g. a "
                      "dot) would NOT be hidden by the consumer's listing rule — "
                      "which hides only names whose first character is the "
                      "underscore — so the synthesized fixture would still print "
                      "its no-documentation line at the default verbosity and the "
                      "F2P assertion (that line is absent) would FAIL. It would "
                      "NOT resolve.",
        "rationale": "REJECT from the leading-marker component: the spec pins the "
                     "first character to `'_'` and the rival emits `'.'`, so "
                     "`result` differs. Refuted at the F2P scenario "
                     "('setUpClass','MyTestCase') — the reported input — so the "
                     "load-bearing component is demonstrated live at the exact "
                     "case the test exercises.",
        "witness": _witness(
            '"setUpClass".toList "MyTestCase".toList',
            "At the reported F2P input the assembled name begins with '.' where "
            "the spec requires '_'. Fully concrete; decidable.",
        ),
    },

    # ---- corrupt the trailing input (nagini PARTIAL-DOMAIN corrupt-last) ----
    {
        "id": "weak-corrupt-qualname",
        "kind": "uniqueness",
        "expect": "reject",
        # Carry the SECOND input truncated (last code point dropped) instead of
        # verbatim. Correct on empty/one-char qualnames but wrong wherever the
        # second input has a real tail character.
        "module": _swap(
            _BASE, _I_QUAL, '  name := name ++ qualname.dropLast\n',
        ),
        "refinement": "a faithful real patch that carried the owning object's "
                      "qualified name with its final character dropped would "
                      "produce a fixture name that is NOT the intended `'_' + "
                      "descriptive` string; the framework's injected `name=` would "
                      "differ from the intended one, breaking the modeled "
                      "construction and the identity the tests assert. It carries "
                      "the marker but mangles the trailing input, so it is a "
                      "partial-domain miss that would NOT resolve.",
        "rationale": "REJECT from the second-input component: the spec carries "
                     "`qualname` verbatim while the rival drops its last code "
                     "point, so `result` differs whenever that input is non-empty. "
                     "Refuted at ('a','XY') — the ONLY rival attacking the second "
                     "input, and it moves that binder to a length-≥2 value where "
                     "the truncation is observable.",
        "witness": _witness(
            '"a".toList "XY".toList',
            "The second input 'XY' is carried as 'X' (last char dropped), so the "
            "assembled name differs from the spec's verbatim carry. Fully "
            "concrete; decidable.",
        ),
    },

    # ---- drop the leading input (attacks the FIRST binder) ----
    {
        "id": "weak-drop-setupname",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the first-input append entirely: the descriptive name loses the
        # setup-hook component. Correct only when the first input is empty.
        "module": _swap(_BASE, _I_SETUP, ""),
        "refinement": "a faithful real patch that omitted the setup-hook "
                      "component of the descriptive name would collapse the names "
                      "of the distinct setup/teardown fixtures onto one another "
                      "(they differ only in that component), defeating the "
                      "uniqueness the `name=` keyword exists to provide, and would "
                      "produce a name the tests do not expect. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the first-input component: the spec carries "
                     "`setupName` verbatim in position while the rival omits it, "
                     "so `result` differs whenever that input is non-empty. "
                     "Refuted at ('tearDown','Foo') — the ONLY rival attacking "
                     "the first input, moving that binder to a non-empty value "
                     "distinct from every other witness.",
        "witness": _witness(
            '"tearDown".toList "Foo".toList',
            "The first input 'tearDown' is dropped from the assembled name, so it "
            "differs from the spec's in-position carry. Fully concrete; "
            "decidable.",
        ),
    },

    # ---- corrupt a constant template literal ----
    {
        "id": "weak-wrong-template",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the constant infix template literal (the fixed component
        # between the two inputs) to a different constant.
        "module": _swap(
            _BASE, _I_TAIL, '  name := name ++ "_FIXTURE_".toList\n',
        ),
        "refinement": "a faithful real patch that altered the constant infix "
                      "template literal would produce a name that is NOT the "
                      "framework's descriptive template woven with the inputs; the "
                      "injected `name=` would differ from the intended one on "
                      "every input, breaking the modeled construction. It would "
                      "NOT resolve.",
        "rationale": "REJECT from the constant-template component: the spec pins "
                     "the fixed infix literal and the rival emits a different "
                     "constant, so `result` differs on every input. Refuted at "
                     "('setUp','Bar') — a fifth distinct point that varies both "
                     "binders again while isolating the constant component.",
        "witness": _witness(
            '"setUp".toList "Bar".toList',
            "The fixed infix template literal is corrupted, so the assembled name "
            "differs from the spec's pinned constant. Fully concrete; decidable.",
        ),
    },

    # ---- marker PRESENT but in the wrong POSITION (audit-added) --------------
    # The five rivals above attack the marker's PRESENCE (`weak-no-prepend`) and
    # its IDENTITY (`weak-wrong-marker`) but never its POSITION: every one of
    # them either omits the underscore or emits a different character at the
    # front. A rival that appends the correct '_' at the END therefore attacks a
    # component the battery left unprobed — and it is the sharpest wrong impl
    # here, because it contains the fix's exact character and differs from gold
    # only in where that character lands. The consumer's listing rule tests the
    # FIRST character, so a trailing underscore is not hidden and the modeled
    # behavior is not achieved.
    {
        "id": "weak-marker-at-end",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_BODY,
            '  name := name ++ "unittest_".toList\n'
            '  name := name ++ setupName\n'
            '  name := name ++ "_fixture_".toList\n'
            '  name := name ++ qualname\n'
            '  name := name ++ "_".toList\n',
        ),
        "refinement": "a faithful real patch that APPENDED the private marker "
                      "instead of prepending it would leave the generated name "
                      "beginning with its ordinary template letter, so the "
                      "consumer's listing rule — which tests the FIRST character "
                      "only — would still SHOW the synthesized fixture at the "
                      "default verbosity and it would print its no-documentation "
                      "line. The F2P assertion (that line is absent) would FAIL, "
                      "so it would NOT resolve, even though the name does contain "
                      "the marker character.",
        "rationale": "REJECT from the POSITION of the leading-marker component: "
                     "the spec pins `result` to `'_' :: …`, i.e. the marker at the "
                     "HEAD, and the rival puts the very same character at the "
                     "tail. Neither `weak-no-prepend` (presence) nor "
                     "`weak-wrong-marker` (identity) covers this: both differ from "
                     "gold in the marker's character or its absence, whereas this "
                     "rival's multiset of characters is exactly gold's. Refuted at "
                     "('setUpModule','Mod') — a sixth distinct point.",
        "witness": _witness(
            '"setUpModule".toList "Mod".toList',
            "The marker is appended at the tail rather than consed at the head, "
            "so the assembled name differs from the spec's `'_' :: …` at the "
            "first character (and at the last). Fully concrete; decidable.",
        ),
    },

    # ---- corrupt the template HEAD literal (audit-added) --------------------
    # `weak-wrong-template` corrupts only the INFIX literal (`_fixture_`). The
    # head literal (`unittest_`) — which sits between the marker and the first
    # input, and is the component the marker is prepended ONTO — was pinned by
    # the spec but never probed by a rival.
    {
        "id": "weak-corrupt-head-literal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, '  name := name ++ "unittest_".toList\n',
            '  name := name ++ "unittest".toList\n',
        ),
        "refinement": "a faithful real patch that dropped the separator from the "
                      "constant template HEAD would run the template word "
                      "straight into the setup-hook component, producing a name "
                      "that is not the framework's descriptive template woven with "
                      "the inputs. The injected `name=` would differ from the "
                      "intended one on every input, so it would NOT resolve.",
        "rationale": "REJECT from the constant template-HEAD component, which no "
                     "other rival attacks (`weak-wrong-template` corrupts the "
                     "INFIX literal only). The spec pins the head literal "
                     "immediately after the marker; the rival emits a different "
                     "constant there, so `result` differs on every input. Refuted "
                     "at ('setUp','Baz') — a seventh distinct point.",
        "witness": _witness(
            '"setUp".toList "Baz".toList',
            "The constant template head is corrupted, so the assembled name "
            "differs from the spec's pinned constant immediately after the "
            "marker. Fully concrete; decidable.",
        ),
    },
]

# No AXIOM lane here: the bundle declares no `opaque` callee and consumes no
# `axiom` (the name is built from constant literals and the two inputs by
# concatenation). The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
