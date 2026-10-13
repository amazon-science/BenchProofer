"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-7454.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The bundle models the gold patch's single changed helper
`make_xref(text)` (sphinx/domains/python.py) as one contracted function
`make_cross_reference(text: List[int]) -> CrossReference` over `List[int]` of
Unicode code points. There are NO @ContractOnly axioms (meta.axioms == []) and
NO A-reference deep models (deep_model_references == []), so AXIOM_TESTS == [].
The deep classifier `kind_for` and the code-point tag constants are validated
== the gold rule by axiom_check.py (G-AX), out of band of this PBT.

THE DEFENDED SURFACE
--------------------
`make_cross_reference(text: List[int]) -> CrossReference`
    Builds the cross-reference node carrying the annotation name `text`. The
    input is READ-ONLY: `Requires(Acc(list_pred(text), 1 / 2))` (and the same
    half-permission is given back in the postcondition). The LOAD-BEARING
    postcondition pins both touched fields three redundant ways:

        # target carry-through (the reftarget):
        Ensures(ToSeq(Result().target) == ToSeq(text))
        # kind classification (the reftype), grounded via the @Pure kind_for:
        Ensures(ToSeq(Result().kind) == kind_for(ToSeq(text)))
        Ensures(Implies(ToSeq(text) == name_value(),
                        ToSeq(Result().kind) == tag_value()))   # 'None' -> 'obj'
        Ensures(Implies(ToSeq(text) != name_value(),
                        ToSeq(Result().kind) == tag_type()))    # else  -> 'class'

    `kind_for(text)` is a @Pure value/type split on `text == name_value()`,
    fully GROUNDED in the input (Viper unfolds it to the `if text==name_value()`
    branch). `name_value()`/`tag_value()`/`tag_type()` are spelled-out code-point
    constants (PSeq(78,111,110,101) / PSeq(111,98,106) / PSeq(99,108,97,115,115)
    = 'None'/'obj'/'class'). There is NO opaque answer-key oracle: the kind is a
    pure function of the arg, so there is no *wrong* echo an impl could return —
    the cheapest faithful impl must still test the input and copy it through
    (see UNGROUNDED-ORACLE note below).

ATTACKS THIS SPEC MUST SURVIVE
------------------------------
  * FRAME-MUTATION (MANDATORY — `text` is read-only at `Acc(list_pred(text),
    1/2)`): `frame-mutate-text` writes a code point through `text` inside the
    build loop before reading it. A store through a 1/2 list_pred is INSUFFICIENT
    PERMISSION, so it must reject. The gold invariants/asserts are kept verbatim
    so the rejection is attributable to the write, not a proof gap. A
    byte-fuzzer never thinks to mutate the input — this is the #1 weakness class.
  * PARTIAL-DOMAIN:
      - `kind-always-type` is the literal pre-patch behaviour (every name ->
        'class', the old unconditional reftype='class'). Correct on every name
        EXCEPT 'None'; it must reject on the value clause for text == name_value().
        This is exactly the G-DIFF discriminator and the F2P delta.
      - `target-prefix-drop` carries text through but drops the LAST code point
        (target == text.take(len-1)). Correct only for the empty name; diverges
        on every non-empty name (incl. the F2P 'int'/'None'). Must reject.
  * UNIQUENESS / wrong-classifier:
      - `kind-swapped` swaps the two tags ('None'->'class', else->'obj'). It
        fails BOTH Implies directions and the kind_for equality. Must reject.
      - `target-echo-name` pins target to the constant value name 'None' for
        every input. Correct only for text == 'None'; must reject (and is the
        closest thing to an "oracle echo" here — but the target oracle is
        ToSeq(text), grounded in the arg, so a constant cannot satisfy it).
  * POSITIVE CONTROL (soundness): two structurally-DIFFERENT but CORRECT impls
    (a branch-order flip on the kind test; a pre-bound kind local) MUST verify,
    else SPEC-TOO-STRONG. Both keep the gold target loop, its invariants, and the
    `Assert(ToSeq(text).take(len(text)) == ToSeq(text))` prefix-completion pin
    (pilot bug #2: never drop a framing assert a positive control still needs).
  * ADMISSIBILITY: `admiss-self-call` appends an in-region caller that builds an
    F2P-shaped name and calls make_cross_reference, asserting the precondition
    (Acc(list_pred(text),1/2)) is establishable for a normal input.

  CONTROL-FLOW-EFFECT is N/A: the modeled function has no raise/return/side-
  effect difference invisible to the value abstraction — there is exactly one
  return, no exception path, and the only observable is the returned
  CrossReference whose two fields are fully value-pinned. VALUE-DOUBLE-MASK is
  N/A: the target clause pins the WHOLE sequence (ToSeq(target)==ToSeq(text), not
  an index-via-value proxy that could drop disagreeing indices) and the kind
  clause pins a whole constant sequence. UNGROUNDED-ORACLE ECHO has no *wrong*
  variant: kind_for and the target are functions of the arg (fully unfolded), so
  the positive controls are the honest cheapest-impl controls for this class.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end` (the whole impl region,
including the nested invariants, is elided by `markers.spec_view`, so
`markers.same_spec` is GUARANTEED). A rejection therefore comes from the
POSTCONDITION (or the permission system), never from a tampered spec. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P (`tests/test_domain_py.py::test_parse_annotation`,
which asserts reftype="class"/reftarget="int" for 'int' AND reftype="obj"/
reftarget="None" for 'None').
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7454"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError("drift: %r not in model.py" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r (%d)" % (old, src.count(old)))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Surgery anchors — verbatim substrings of the gold impl region.
# ---------------------------------------------------------------------------

# The kind-classification + return tail (the changed operation).
_GOLD_KIND = (
    "    if ToSeq(text) == name_value():\n"
    "        ref.kind = [111, 98, 106]\n"
    "    else:\n"
    "        ref.kind = [99, 108, 97, 115, 115]\n"
    "    return ref\n"
)

# The target-build loop body line (writes target, never text).
_GOLD_LOOPBODY = "        target = target + [text[i]]\n"

# The target assignment from the built copy.
_GOLD_TARGET_ASSIGN = "    ref.target = target\n"


# ===========================================================================
# SPEC CASES
# ===========================================================================
SPEC_TESTS = [

    # -- POSITIVE CONTROLS (soundness): structurally-different CORRECT impls ----

    # (1) Branch-order flip: test the COMPLEMENT (text != name_value()) first,
    # assigning the TYPE tag in the taken branch and the VALUE tag in the else.
    # Same classification, different control shape. kind_for + both Implies still
    # hold; the gold target loop/invariants/assert are untouched. MUST verify.
    {"id": "pos-kind-reorder", "kind": "soundness", "expect": "verify",
     "module": _swap(_BASE, _GOLD_KIND,
         "    if ToSeq(text) != name_value():\n"
         "        ref.kind = [99, 108, 97, 115, 115]\n"
         "    else:\n"
         "        ref.kind = [111, 98, 106]\n"
         "    return ref\n"),
     "rationale": "a correct but branch-reordered classifier must verify; "
                  "kind_for(ToSeq(text)) and both Implies directions are "
                  "unchanged. If it fails => SPEC-TOO-STRONG."},

    # (2) Pre-bound kind local: initialise to the TYPE tag, overwrite to the
    # VALUE tag only when text == name_value(), then assign to ref.kind. A
    # different data shape (one assignment path) that is provably equal. MUST
    # verify. (Each list literal gets a fresh list_pred, so ref.kind = kindloc
    # has the permission it needs.)
    {"id": "pos-kind-prebound", "kind": "soundness", "expect": "verify",
     "module": _swap(_BASE, _GOLD_KIND,
         "    kindloc = [99, 108, 97, 115, 115]  # type: List[int]\n"
         "    if ToSeq(text) == name_value():\n"
         "        kindloc = [111, 98, 106]\n"
         "    ref.kind = kindloc\n"
         "    return ref\n"),
     "rationale": "a correct impl that pre-binds the kind to a local before "
                  "assigning must verify (structurally different data shape, "
                  "same value). If it fails => SPEC-TOO-STRONG."},

    # -- ADMISSIBILITY: the precondition must admit a normal F2P-shaped input ---

    # Append an in-region caller that builds a concrete name ('None' = the value
    # name, an F2P input) and calls make_cross_reference. The list literal grants
    # full list_pred, so Acc(list_pred(text), 1/2) is trivially establishable. If
    # this caller cannot satisfy the Requires => PRECOND-TOO-STRONG.
    {"id": "admiss-self-call", "kind": "admissibility", "expect": "verify",
     # Keep the gold tail verbatim and append an in-region caller AFTER `return
     # ref` but BEFORE the closing `# impl-end` (the caller therefore lives inside
     # the impl span and is elided by markers.spec_view, so same_spec is intact).
     # A list literal grants full list_pred, so Acc(list_pred(text),1/2) is
     # trivially establishable for the F2P value name 'None'.
     "module": _swap(_BASE, _GOLD_KIND,
         "    if ToSeq(text) == name_value():\n"
         "        ref.kind = [111, 98, 106]\n"
         "    else:\n"
         "        ref.kind = [99, 108, 97, 115, 115]\n"
         "    return ref\n"
         "\n"
         "\n"
         "def _admiss_caller() -> None:\n"
         "    name = [78, 111, 110, 101]  # type: List[int]\n"
         "    r = make_cross_reference(name)\n"
         "    Assert(ToSeq(r.kind) == tag_value())\n"),
     "rationale": "a positive caller establishing Requires on a real F2P name "
                  "('None') must verify; if not => PRECOND-TOO-STRONG."},

    # -- FRAME-MUTATION (MANDATORY: text is read-only at Acc(list_pred(text),1/2))

    # Write a code point THROUGH the read-only `text` inside the build loop,
    # before continuing. The gold invariants/assert are kept verbatim so the only
    # change is the illegal store. A write through a 1/2 list_pred is INSUFFICIENT
    # PERMISSION => Nagini must REJECT. (If it verified, a mutating real patch
    # would scribble on the annotation name buffer it does not own.)
    {"id": "frame-mutate-text", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _GOLD_LOOPBODY,
         "        text[i] = 0\n"                       # <-- write through 1/2 perm
         "        target = target + [text[i]]\n"),
     "refinement": "the faithful real patch corresponding to a make_xref that "
                   "overwrites its own `text` argument buffer would corrupt the "
                   "annotation name (reftarget/display text), so reftarget would "
                   "no longer equal 'int'/'None' and test_parse_annotation's "
                   "assert_node(..., reftarget='int'/'None') would FAIL — it "
                   "would not resolve.",
     "rationale": "REJECT comes from the permission system: `text` is held at "
                  "Acc(list_pred(text),1/2); a store `text[i]=...` needs full "
                  "permission. Insufficient permission, not a postcondition miss."},

    # -- PARTIAL-DOMAIN: the literal pre-patch classifier (always 'class') -------

    # Every name classified as the TYPE tag — the old unconditional reftype=
    # 'class'. Correct on every name except 'None'. Fails the VALUE clause
    # Ensures(Implies(text == name_value(), kind == tag_value())) and the kind_for
    # equality for text == name_value(). MUST reject. (== model_prepatch.py.)
    {"id": "kind-always-type", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _GOLD_KIND,
         "    ref.kind = [99, 108, 97, 115, 115]\n"
         "    return ref\n"),
     "refinement": "this is the pre-patch make_xref (unconditional "
                   "reftype='class'); the F2P assert_node(doctree[0], "
                   "pending_xref, reftype='obj', reftarget='None') FAILS for "
                   "'None' (it stays 'class'), so the real patch would NOT "
                   "resolve test_parse_annotation.",
     "rationale": "REJECT from the value clause: for text == name_value() the "
                  "postcondition requires kind == tag_value() ('obj'), but this "
                  "impl gives tag_type() ('class')."},

    # -- PARTIAL-DOMAIN: target drops the last code point ------------------------

    # Carry text through but build only the (len-1)-prefix as the target (stop the
    # copy one element early). Correct only for the empty name; diverges on every
    # non-empty name (incl. F2P 'int'/'None'). Fails
    # Ensures(ToSeq(Result().target) == ToSeq(text)). MUST reject.
    # Implemented by stopping the loop at len(text)-1 via a guard on i.
    {"id": "target-prefix-drop", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _GOLD_LOOPBODY,
         "        if i + 1 < len(text):\n"
         "            target = target + [text[i]]\n"
         "        else:\n"
         "            target = target\n"),
     "refinement": "a make_xref that passes reftarget=text[:-1] (dropping the "
                   "last character) gives reftarget='in' for 'int' and 'Non' for "
                   "'None'; assert_node(..., reftarget='int'/'None') FAILS, so it "
                   "would NOT resolve test_parse_annotation.",
     "rationale": "REJECT attributable to the target clause "
                  "ToSeq(Result().target)==ToSeq(text): an impl that stops the "
                  "copy one element short cannot carry text through for any "
                  "non-empty name (the (len-1)-prefix differs), so it cannot "
                  "establish the target postcondition (it breaks first at the "
                  "loop invariant ToSeq(target)==ToSeq(text).take(i), the same "
                  "impossibility)."},

    # -- UNIQUENESS: tags swapped (value/type inverted) --------------------------

    # 'None' -> TYPE tag, every other name -> VALUE tag: the classifier inverted.
    # Fails BOTH Implies directions and the kind_for equality everywhere. MUST
    # reject.
    {"id": "kind-swapped", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _GOLD_KIND,
         "    if ToSeq(text) == name_value():\n"
         "        ref.kind = [99, 108, 97, 115, 115]\n"
         "    else:\n"
         "        ref.kind = [111, 98, 106]\n"
         "    return ref\n"),
     "refinement": "this make_xref reverses the rule (reftype='class' for "
                   "'None', reftype='obj' for everything else). For 'None' the "
                   "F2P wants reftype='obj' (gets 'class') AND for 'int' it wants "
                   "reftype='class' (gets 'obj'); BOTH assert_node checks FAIL, "
                   "so it would NOT resolve.",
     "rationale": "REJECT from both Implies: text==name_value() requires "
                  "tag_value() but gets tag_type(); text!=name_value() requires "
                  "tag_type() but gets tag_value()."},

    # -- UNIQUENESS: target pinned to the constant value name --------------------

    # Set the target to the constant 'None' code points for EVERY input, ignoring
    # `text`. Correct only when text == 'None'; the closest analogue of an "oracle
    # echo" — but the target oracle is ToSeq(text) (grounded in the arg), so a
    # constant cannot satisfy it for any other name. Fails
    # Ensures(ToSeq(Result().target) == ToSeq(text)). MUST reject.
    {"id": "target-echo-name", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _GOLD_TARGET_ASSIGN,
         "    ref.target = [78, 111, 110, 101]\n"),
     "refinement": "a make_xref that hard-codes reftarget='None' regardless of "
                   "the input gives reftarget='None' for the name 'int'; "
                   "assert_node(..., reftarget='int') FAILS, so it would NOT "
                   "resolve test_parse_annotation.",
     "rationale": "REJECT from the target clause: ToSeq(Result().target) must "
                  "equal ToSeq(text); the constant name_value() differs from "
                  "ToSeq(text) for every text != 'None'."},
]

# ===========================================================================
# AXIOM CASES — none. meta.axioms == [] and deep_model_references == []: the
# changed behaviour is a pure in-function value/type split over the input text,
# modeled deeply (kind_for + verbatim code-point tag constants). No @ContractOnly
# axiom and no A-reference external callee exist to discharge in Docker. (The
# deep-model fidelity G-AX would otherwise audit is covered host-side by
# axiom_check.py.)
# ===========================================================================
AXIOM_TESTS = []  # type: list
