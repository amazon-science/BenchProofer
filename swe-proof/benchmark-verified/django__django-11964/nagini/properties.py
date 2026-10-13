"""PBT manifest for django__django-11964 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  render_to_text(self: Member) -> List[int]
    Requires (READ-ONLY self, both fields at 1/2 perm):
        Acc(self.value_text, 1/2)     and Acc(list_pred(self.value_text), 1/2)
        Acc(self.qualified_label,1/2) and Acc(list_pred(self.qualified_label),1/2)
    Ensures (frame, the 1/2 perms returned + contents preserved):
        Acc(self.value_text, 1/2) ... ; Acc(self.qualified_label, 1/2) ...
        len(self.value_text)     == Old(len(self.value_text))     + Forall preservation
        len(self.qualified_label)== Old(len(self.qualified_label)) + Forall preservation
    Ensures (fresh result):       Acc(list_pred(Result()))
    Ensures (DISCRIMINATOR, load-bearing):
        ToSeq(Result()) == ToSeq(self.value_text)

  Model the gold one-method change to django/db/models/enums.py:
    -    pass
    +    def __str__(self):
    +        return str(self.value)
  i.e. coerce a choice member to its VALUE text ("first" / "1"), NOT the default
  enum diagnostic "Owner.NAME" label (carried here as self.qualified_label).

GROUNDED-ORACLE NOTE: the load-bearing postcondition oracle is
ToSeq(self.value_text) -- a function of the INPUT (the member's own field), fully
materialized, NOT an opaque @Pure answer-key. So there is NO *wrong* echo a rival
can return: copying self.value_text element-for-element is the honest correct
impl (the gold impl itself), and any DIFFERENT returned content (the qualified
label, a truncation, the empty sequence) fails the postcondition. The uniqueness
lane therefore targets (a) the read-only frame (overwrite self to satisfy the
postcondition vacuously -> MANDATORY permission probe), and (b) returning a value
that diverges from the value text on a discriminating sub-domain (the pre-patch
"Owner.NAME" label; a truncation; the empty sequence) -- exactly the behaviours
the gold change replaces. We include the honest cheapest correct impl as a
positive control to confirm the spec is not echo-vulnerable.

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (meta.axioms == []).
The single A-reference is the standard string coercion str(value) producing
value_text (the changed rendering is modelled DEEPLY as an element-for-element
copy of value_text). We re-run axiom_check.py's real-callee equivalence (str of a
reconstructed patched Choices member == real Python str(value), and != the
default "Owner.NAME" label) as an axiom-soundness probe. axiom_check.py imports
ONLY stdlib `enum`/`random`/`sys`, so it runs in-container unchanged; its source
is read on the HOST at load time and embedded into the probe string (the runner
mounts only the probe at /work). A containment probe is N/A: no axiom Requires
domain exists to fall outside (no consumed axiom), and the A-reference's input
domain (any int/str enum value) strictly contains every value the caller reaches.

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end (the invariants are nested inside that region, so
editing them is still inside impl and preserves same_spec). The frozen spec
(axioms/pure/pre/post-conditions/signatures/Member class) is never touched.
"""
from pathlib import Path

INSTANCE = "django__django-11964"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
_HEAD = "    result = []  # type: List[int]\n    i = 0\n"
_WHILE = "    while i < len(self.value_text):\n"
_APPEND = "        result.append(self.value_text[i])\n"
_INV_TAKE = "        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))\n"
_INV_LEN = "        Invariant(len(result) == i)\n"
_INV_BOUND = "        Invariant(0 <= i and i <= len(self.value_text))\n"
_RETURN = "    return result\n"

for _a in (_HEAD, _WHILE, _APPEND, _INV_TAKE, _INV_LEN, _INV_BOUND, _RETURN):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5) POSITIVE CONTROL -- local-variable reshape. The gold `result.append(
# self.value_text[i])` is split into reading the code point into a temp `c`
# (== self.value_text[i]) then appending `c`. Semantically identical, so the
# take(i) loop invariant (ToSeq(result) == ToSeq(self.value_text).take(i)) and
# every other gold invariant stay valid VERBATIM -- the gold proof is preserved.
# A loop-direction flip / fold-rewrite is deliberately AVOIDED (it would need an
# f(a+b)==f(a)+f(b) lemma the verifier won't auto-discharge -- pilot bug #3).
# MUST verify; else the postcondition is over-fit to the exact append FORM
# => SPEC-TOO-STRONG.
_POS_RESHAPE = _swap(
    _BASE, _APPEND,
    "        c = self.value_text[i]\n"
    "        result.append(c)\n",
)

# (5b) POSITIVE CONTROL -- the cheapest HONEST impl. The load-bearing oracle
# ToSeq(self.value_text) is GROUNDED in the input (the member's own field), so a
# faithful element-for-element copy IS the correct implementation (this is the
# gold impl modulo the temp). We re-affirm it here as a distinct case using a
# pre-sized read into a typed local to show the spec is not echo-vulnerable: any
# DIFFERENT returned content fails the postcondition (there is no wrong constant
# echo to build). MUST verify; else SPEC-TOO-STRONG.
_POS_COPY = _swap(
    _BASE, _APPEND,
    "        nxt = self.value_text[i]  # type: int\n"
    "        result.append(nxt)\n",
)

# (6) ADMISSIBILITY -- a self-call on a fresh F2P-shaped member. Member() ensures
# FULL permission on both fields; render_to_text needs only 1/2, so the call site
# can establish the precondition for a normal member and gets back the result
# property. We then run the actual gold body on the real `self`. MUST verify; if
# the precondition cannot be established for a freshly constructed member =>
# PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE, _HEAD,
    "    probe = Member()\n"
    "    rendered = render_to_text(probe)\n"
    "    Assert(ToSeq(rendered) == ToSeq(probe.value_text))\n"
    "    result = []  # type: List[int]\n    i = 0\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). `self` is read-only: both
# fields are held at Acc(list_pred(.),1/2). This rival WRITES through the
# read-only reference -- `self.value_text[i] = 88` -- before reading it, the
# canonical "normalize the input to satisfy the postcondition vacuously" attack.
# A store into list_pred(self.value_text) needs FULL permission, but only 1/2 is
# held, so it MUST be rejected for INSUFFICIENT PERMISSION (not a value mismatch).
# Every gold invariant is kept verbatim, so the rejection is attributable solely
# to the write.
_RIVAL_FRAME = _swap(
    _BASE, _APPEND,
    "        self.value_text[i] = 88\n"
    "        result.append(self.value_text[i])\n",
)

# (2/3a) WRONG-VALUE rival -- return the QUALIFIED LABEL (the pre-patch
# "Owner.NAME" behaviour, == model_prepatch.py). The loop is retargeted to copy
# self.qualified_label, and the take(i) / len invariants are retargeted to
# qualified_label so the rival is internally consistent (all edits inside impl,
# so same_spec holds). The only remaining open obligation is the load-bearing
# postcondition ToSeq(Result()) == ToSeq(self.value_text): result now equals the
# qualified label, which differs from the value text for every member whose label
# != value (e.g. "YearInSchool.FRESHMAN" vs "FR", "Suit.DIAMOND" vs "1"). The
# verifier cannot close it.
_RIVAL_LABEL = _BASE
_RIVAL_LABEL = _swap(_RIVAL_LABEL, _WHILE,
                     "    while i < len(self.qualified_label):\n")
_RIVAL_LABEL = _swap(_RIVAL_LABEL, _INV_BOUND,
                     "        Invariant(0 <= i and i <= len(self.qualified_label))\n")
_RIVAL_LABEL = _swap(_RIVAL_LABEL, _INV_TAKE,
                     "        Invariant(ToSeq(result) == ToSeq(self.qualified_label).take(i))\n")
_RIVAL_LABEL = _swap(_RIVAL_LABEL, _APPEND,
                     "        result.append(self.qualified_label[i])\n")

# (3b) PARTIAL-DOMAIN -- drop the LAST code point. The loop bound is narrowed to
# `i < len(self.value_text) - 1`, so the rendered result is value_text.take(n-1).
# The take(i) prefix invariant stays valid throughout (result is always a true
# prefix), and 0 <= i <= len, len(result)==i hold; only the final postcondition
# ToSeq(Result()) == ToSeq(self.value_text) is open -- false for every non-empty
# value (it renders "firs" for "first", "" for "1"). Correct only on empty values.
_RIVAL_DROPLAST = _swap(
    _BASE, _WHILE,
    "    while i < len(self.value_text) - 1:\n",
)

# (3c) VALUE-MASK supporting rival -- return the EMPTY sequence. The body is
# replaced by an immediate `return result` on the freshly-created empty list
# (no loop). result is empty; the postcondition ToSeq(Result()) ==
# ToSeq(self.value_text) then requires value_text to be empty -- false for every
# non-empty value. Cheapest wrong impl; correct only on empty values.
_RIVAL_EMPTY = _swap(
    _BASE,
    _BASE[_BASE.index(_HEAD):_BASE.index("    # impl-end")],
    "    result = []  # type: List[int]\n"
    "    return result\n",
)


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {"id": "pos-control-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_RESHAPE,
     "rationale": "structurally-different but CORRECT impl: the append is split into "
                  "reading the code point into a temp `c` (== self.value_text[i]) then "
                  "appending it. Every gold invariant -- esp. the take(i) prefix "
                  "invariant ToSeq(result)==ToSeq(self.value_text).take(i) -- stays valid "
                  "verbatim, so the gold proof is preserved (a loop-direction flip is "
                  "avoided to dodge an unprovable fold lemma). Must verify; else the "
                  "postcondition is over-fit to the exact append FORM => SPEC-TOO-STRONG."},
    {"id": "pos-control-copy", "kind": "soundness", "expect": "verify",
     "module": _POS_COPY,
     "rationale": "the load-bearing oracle ToSeq(self.value_text) is GROUNDED in the "
                  "input, so a faithful element-for-element copy IS the correct impl. This "
                  "case reads each code point into a typed local before appending -- a "
                  "second honest correct shape -- to confirm the spec is not "
                  "echo-vulnerable (any DIFFERENT returned content fails the postcondition; "
                  "there is no wrong constant echo). Must verify; else SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on a freshly constructed Member() (which ensures FULL "
                  "permission on both fields) must establish render_to_text's 1/2 "
                  "precondition and yield the result property ToSeq(rendered)=="
                  "ToSeq(probe.value_text). If the precondition cannot be established for a "
                  "normal member => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-value-text", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this. The gold __str__ "
                   "(`return str(self.value)`) only READS self.value to render it; an enum "
                   "member's .value is never mutated by stringifying it, and doing so would "
                   "corrupt the member (and is impossible for the immutable str/int values "
                   "the issue uses). The rival exists solely to test whether the read-only "
                   "(1/2) precondition can be subverted by overwriting self to make the "
                   "postcondition vacuously holdable. There is no resolving patch that "
                   "rewrites the member's value, so a verifying rival here would be a pure "
                   "verify-not-resolve artifact.",
     "rationale": "MANDATORY frame-mutation probe. `self.value_text[i] = 88` writes through "
                  "a 1/2 (read-only) reference and MUST fail for INSUFFICIENT PERMISSION (a "
                  "store into list_pred(self.value_text) needs full Acc), NOT a value "
                  "mismatch; the gold invariants are kept verbatim so the rejection is "
                  "attributable to the write. Rejection source: the PERMISSION SYSTEM. If "
                  "it verified => SPEC-TOO-WEAK (the read-only frame protection is hollow)."},
    {"id": "weak-qualified-label", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LABEL,
     "refinement": "this is EXACTLY the pre-patch behaviour (== model_prepatch.py): a "
                   "Choices member with the empty `pass` body inherits enum.Enum.__str__, "
                   "which returns the diagnostic 'Owner.NAME' qualified label. A faithful "
                   "patch that left __str__ returning that label still renders "
                   "'YearInSchool.FRESHMAN' / 'Suit.DIAMOND' instead of 'FR' / '1' and "
                   "FAILS the F2P test_str (assertEqual(str(test[member.name]), "
                   "str(member.value))) and test_textchoices -- it is the unfixed bug, the "
                   "definition of verify-not-resolve.",
     "rationale": "rejection source: the load-bearing postcondition ToSeq(Result()) == "
                  "ToSeq(self.value_text). The loop and its take(i)/len/bound invariants are "
                  "retargeted to self.qualified_label (all inside the impl region, so "
                  "same_spec holds), so the rival proves Result()==qualified_label; the "
                  "postcondition then requires qualified_label == value_text, which is false "
                  "for every member whose label differs from its value. The verifier cannot "
                  "close it. If it verified => SPEC-TOO-WEAK (the value-vs-label "
                  "discriminator -- the whole point of the fix -- would be hollow)."},
    {"id": "weak-drop-last", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROPLAST,
     "refinement": "a real __str__ that returned str(self.value)[:-1] would render 'firs' "
                   "for the value 'first' and '' for the value '1'. It diverges from the "
                   "value text on every non-empty value, so it FAILS the F2P test_str / "
                   "test_textchoices (str(test[member.name]) != str(member.value)) -- "
                   "verify-not-resolve on the entire non-empty sub-domain.",
     "rationale": "rejection source: the postcondition ToSeq(Result()) == "
                  "ToSeq(self.value_text). The loop bound is narrowed to "
                  "i < len(self.value_text) - 1, so result == value_text.take(n-1); the "
                  "prefix take(i) invariant stays valid (result is always a true prefix), "
                  "but at exit ToSeq(Result()) == value_text.take(n-1) != value_text for any "
                  "non-empty value. The verifier cannot close the postcondition. If it "
                  "verified => SPEC-TOO-WEAK (the spec would accept a truncating render)."},
    {"id": "weak-empty", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY,
     "refinement": "a real __str__ that returned '' for every member renders the empty "
                   "string instead of 'first' / '1', so str(test[member.name]) != "
                   "str(member.value) for every non-empty value and it FAILS the F2P "
                   "test_str / test_textchoices -- verify-not-resolve (this is the "
                   "cheapest wrong render).",
     "rationale": "rejection source: the postcondition ToSeq(Result()) == "
                  "ToSeq(self.value_text). The body immediately returns the empty result "
                  "(no loop), so Result() is empty; the postcondition then requires "
                  "value_text to be empty, false for every non-empty value. The verifier "
                  "cannot close it. Supporting value-mask case. If it verified => "
                  "SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed (meta.axioms == []). The single
# A-reference is the standard string coercion str(value) producing value_text; the
# changed rendering is modelled DEEPLY as an element-for-element copy of value_text.
# We re-run axiom_check.py's real-callee equivalence (str of a reconstructed
# patched Choices member == real Python str(value), and != the default
# "Owner.NAME" label, over boundary + 20000 fuzz int/str members) as an
# axiom-soundness check on that A-reference. axiom_check.py imports ONLY stdlib
# (enum/random/sys) -- the very enum machinery the patch builds on -- so it runs
# in-container unchanged; its source is read on the HOST at load time and embedded
# into the probe (the runner mounts only the probe at /work). A containment probe
# is N/A: there is no consumed-axiom Requires domain, and the A-reference's input
# domain (any int/str enum value) strictly contains every value the caller reaches.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-render-equals-str-value",
        "axiom": "value_text",  # the A-reference deep model (not a consumed axiom)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,  # axiom_check.py reconstructs the patched behaviour on
                              # stdlib enum; it does not need the Django source tree.
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model `value_text` is an A-reference: render_to_text must "
                     "return the member's value text == real Python str(member.value), "
                     "character for character, and NEVER the default 'Owner.NAME' label. "
                     "This probe (axiom_check.py verbatim, stdlib enum/random/sys only) "
                     "reconstructs the patched Choices.__str__ (`return str(self.value)`) "
                     "with the IntegerChoices/TextChoices int/str mix-ins the issue names, "
                     "and asserts over 31 boundary + 20000 fuzz int/str members that "
                     "str(member) == str(member.value) (the A-reference is sound) and that "
                     "str(member) != the 'Owner.NAME' label whenever they differ (the "
                     "discriminating behaviour the fix adds). Exit 0 iff every observation "
                     "agrees; any disagreement => the A-reference is UNSOUND.",
    },
]
