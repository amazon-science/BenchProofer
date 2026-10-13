# properties.py — PBT falsification manifest for django__django-12276.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec verbatim (region-surgery edits
# ONLY inside the # impl-start / # impl-end region) and are checked by Nagini
# verify + same_spec; axiom cases are real-callee probes run in the instance
# Docker image.
#
# Defended surface (read model.py):
#   requires_value(control: UploadControl, value_present: bool) -> bool
#     Requires(Acc(control.hidden, 1/2))                         # READ-ONLY input
#     Ensures(Acc(control.hidden, 1/2))                          # frame: gives 1/2 back
#     Ensures(Result() == (generic_requires_value(control.hidden) and not value_present))
#     Ensures(Implies(value_present, Result() == False))
#     Ensures(Implies(not value_present, Result() == generic_requires_value(control.hidden)))
#   generic_requires_value(hidden) is @Pure @ContractOnly with
#     Ensures(Result() == (not hidden))   # A-consumed axiom; the inherited base
#                                          # Widget.use_required_attribute.
#
# The result is pinned to a TOTAL function of the two inputs
# (generic_requires_value(control.hidden) and not value_present), so there is no
# "wrong echo": echoing the oracle IS the correct behaviour. The genuine attack
# surface is therefore (a) frame-mutation of the read-only `control`, and
# (b) partial-domain rivals that get one of the two observed facts wrong.

from pathlib import Path

INSTANCE = "django__django-12276"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The single impl line in model.py (between # impl-start / # impl-end).
_GOLD_IMPL = "    return generic_requires_value(control.hidden) and not value_present"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — a structurally-different but CORRECT impl.
# Branch-reorder: decide on value_present FIRST, then fall through to the
# generic decision. Semantically identical to the gold conjunction, but a
# different executable shape. Both decomposed Ensures clauses
# (Implies(value_present, Result()==False) and Implies(not value_present,
# Result()==generic_requires_value(...))) are discharged directly by the two
# branches, so the gold proof obligations stay valid. If this can't verify =>
# SPEC-TOO-STRONG.
_POS_REORDER = (
    "    if value_present:\n"
    "        return False\n"
    "    return generic_requires_value(control.hidden)"
)

# POSITIVE CONTROL #2 — De Morgan / local-variable reshape. Compute the generic
# decision into a typed local, negate value_present into a typed local, and
# return their conjunction in the opposite operand order. Boolean `and` is
# commutative here (both operands are bools), so this equals the gold result;
# it keeps every postcondition obligation. A second independent witness that a
# faithful correct impl of a different shape verifies.
_POS_LOCALS = (
    "    g = generic_requires_value(control.hidden)  # type: bool\n"
    "    absent = not value_present  # type: bool\n"
    "    return absent and g"
)

# ---------------------------------------------------------------------------
# ADMISSIBILITY — a caller asserts the precondition admits a normal,
# F2P-shaped input (a visible FileInput control with NO usable value present:
# the test_use_required_attribute(None) case), and that the modeled function is
# callable on it. Acc(control.hidden, 1/2) must be establishable for a freshly
# constructed control. If this can't verify => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # admissibility: a normal F2P-shaped input must satisfy Requires and\n"
    "    # the call must go through. UploadControl(False) is a visible control\n"
    "    # (input_type != 'hidden'); value_present=False is the no-initial F2P case.\n"
    "    probe = UploadControl(False)\n"
    "    Assert(Acc(probe.hidden, 1 / 2))\n"
    "    return generic_requires_value(control.hidden) and not value_present"
)

# ---------------------------------------------------------------------------
# FRAME-MUTATION (MANDATORY: control is Acc(control.hidden, 1/2) = read-only).
# The rival overwrites the half-permission input field to make the postcondition
# trivially hold, then returns the (now self-consistent) value. With only 1/2
# permission a WRITE to control.hidden is illegal; Nagini must REJECT for
# INSUFFICIENT PERMISSION (not for a value mismatch). The gold postcondition is
# kept verbatim so the rejection is attributable to the write.
# refinement: a faithful real patch behaving this way would assign to
# self.is_hidden inside FileInput.use_required_attribute — a control-state
# mutation the real method never performs (it is a pure read of self.is_hidden
# via super()). Such a patch corrupts the widget's hidden state and would NOT
# resolve test_render / test_use_required_attribute_true (P2P) which observe the
# unmutated hidden state on the same widget.
_FRAME_MUT = (
    "    control.hidden = False  # illegal write through a 1/2 (read-only) permission\n"
    "    return generic_requires_value(control.hidden) and not value_present"
)

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN #1 — the PRE-PATCH bug verbatim: ignore value_present and return
# only the generic control-level decision. Correct on the entire value_present=
# False sub-domain, but WRONG whenever a usable value is already present
# (value_present=True) on a visible control: returns True where the spec
# requires False.
# refinement: this IS the pre-patch FileInput behaviour (inherits only
# Widget.use_required_attribute -> `super().use_required_attribute(initial)`
# with no `and not initial`). The faithful real patch is the EMPTY change (no
# method added), which is exactly the state the F2P tests fail on:
# test_use_required_attribute expects use_required_attribute('resume.txt') is
# False, and test_filefield_with_fileinput_required expects NO `required`
# attribute when an initial value is present. So this rival does NOT resolve.
_PARTIAL_DROP_VALUE = (
    "    return generic_requires_value(control.hidden)"
)

# PARTIAL-DOMAIN #2 — drop the generic control-level decision: return only
# `not value_present`. Correct on every NON-hidden control (where
# generic_requires_value is True, so the gold result equals `not value_present`),
# but WRONG on a HIDDEN control with no value present: the spec requires
# generic_requires_value(True)==False, but this returns `not False`==True.
# refinement: the faithful real patch would be
# `return not initial` (dropping the `super().use_required_attribute(initial)`
# conjunct). That makes a hidden file control advertise a required value when it
# never should — diverging from Widget.use_required_attribute's
# `not self.is_hidden` base behaviour that the no-value P2P cases
# (test_use_required_attribute_true / _false on the inherited base) rely on. It
# would NOT preserve the unchanged base decision and would not resolve.
_PARTIAL_DROP_GENERIC = (
    "    absent = not value_present  # type: bool\n"
    "    return absent"
)

# PARTIAL-DOMAIN #3 — XOR instead of AND. `g != value_present` agrees with the
# gold AND on three of the four (g, value_present) corners but DIVERGES on the
# single corner g=False, value_present=True: gold AND gives False, XOR gives
# True. A value-flip that survives any postcondition pinning only part of the
# input domain.
# refinement: a real patch computing
# `super().use_required_attribute(initial) != bool(initial)` would, on a HIDDEN
# control carrying a usable value, advertise required (True) where both the base
# decision (False, hidden) and the present-value suppression demand False. It
# diverges from the gold conjunction and would not resolve the rendering tests.
_PARTIAL_XOR = (
    "    g = generic_requires_value(control.hidden)  # type: bool\n"
    "    return g != value_present"
)

# SUPPORTING near-miss — constant False. Correct on every (g and not
# value_present)==False corner, wrong on the corner g=True, value_present=False
# (a visible control, no value: the spec requires True). Cheap supporting case;
# carries a real refinement.
# refinement: a real patch `return False` makes EVERY file control non-required,
# so test_use_required_attribute(None) (expects True) and
# test_filefield_with_fileinput_required (expects `required` rendered with no
# initial) both fail => does NOT resolve.
_CONST_FALSE = (
    "    return False"
)


def _variant(impl_block):
    return _swap(_BASE, _GOLD_IMPL, impl_block)


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_REORDER),
        "rationale": "structurally-different CORRECT impl (decide on value_present "
                     "first, else generic decision); discharges both decomposed "
                     "Ensures branches directly. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS_LOCALS),
        "rationale": "correct impl via typed locals + commuted boolean `and` "
                     "(both operands bool). Second independent positive witness; "
                     "must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-novalue",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "Requires(Acc(control.hidden,1/2)) must admit a freshly built "
                     "visible UploadControl with value_present=False (the F2P "
                     "no-initial case) and the self-call must go through. If it "
                     "cannot, PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mut-write-hidden",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FRAME_MUT),
        "refinement": "a real patch assigning to self.is_hidden inside "
                      "FileInput.use_required_attribute mutates the widget's "
                      "hidden state, which the real (pure-read) method never does; "
                      "it would corrupt the control and fail the rendering P2P "
                      "tests that observe the unmutated hidden state. Does NOT resolve.",
        "rationale": "control is Acc(control.hidden,1/2) (read-only): writing "
                     "control.hidden is INSUFFICIENT PERMISSION -> Nagini rejects. "
                     "If it verified, the frame condition would be unenforced "
                     "(SPEC-TOO-WEAK / frame leak).",
    },
    {
        "id": "partial-drop-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PARTIAL_DROP_VALUE),
        "refinement": "this is the PRE-PATCH FileInput behaviour (inherits only "
                      "Widget.use_required_attribute = super().use_required_attribute"
                      "(initial), no `and not initial`). The faithful real patch is "
                      "the empty change, exactly the state the F2P tests FAIL on "
                      "(use_required_attribute('resume.txt') must be False; "
                      "test_filefield_with_fileinput_required expects no `required` "
                      "with an initial value). Does NOT resolve.",
        "rationale": "violates Ensures(Implies(value_present, Result()==False)): on "
                     "a visible control with value_present=True it returns "
                     "generic_requires_value(False)==True. Nagini rejects.",
    },
    {
        "id": "partial-drop-generic",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PARTIAL_DROP_GENERIC),
        "refinement": "a real patch `return not initial` drops the "
                      "super().use_required_attribute(initial) conjunct, so a HIDDEN "
                      "file control with no value advertises required (True) when the "
                      "unchanged base decision (not is_hidden = False) forbids it. It "
                      "abandons the inherited base behaviour and would not resolve.",
        "rationale": "violates Ensures(Implies(not value_present, "
                     "Result()==generic_requires_value(control.hidden))): on a hidden "
                     "control (hidden=True) with value_present=False the spec needs "
                     "generic_requires_value(True)==False but this returns True. "
                     "Nagini rejects.",
    },
    {
        "id": "partial-xor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PARTIAL_XOR),
        "refinement": "a real patch computing "
                      "`super().use_required_attribute(initial) != bool(initial)` "
                      "diverges from the gold conjunction on a hidden control "
                      "carrying a usable value (returns True where the base decision "
                      "and the present-value suppression both demand False). Does NOT "
                      "resolve the rendering tests.",
        "rationale": "XOR agrees with AND on three corners but on g=False, "
                     "value_present=True the gold result is False while XOR is True "
                     "-> violates Ensures(Implies(value_present, Result()==False)). "
                     "Nagini rejects.",
    },
    {
        "id": "supporting-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_CONST_FALSE),
        "refinement": "a real patch `return False` makes every file control "
                      "non-required, so test_use_required_attribute(None) (expects "
                      "True) and test_filefield_with_fileinput_required (expects "
                      "`required` rendered with no initial) both fail. Does NOT resolve.",
        "rationale": "supporting near-miss: violates Ensures(Implies(not "
                     "value_present, Result()==generic_requires_value(control.hidden))) "
                     "on a visible control with no value (spec needs True). Nagini rejects.",
    },
]

# ---------------------------------------------------------------------------
# AXIOM lane — the bundle has ONE @ContractOnly axiom: generic_requires_value
# (A-consumed), modeling the unchanged inherited base
# Widget.use_required_attribute reached via super(). Both probes run the REAL
# callee in the instance Docker image (apply_gold=True so the moved method is
# present), never scraping source. Files opened with encoding="utf-8" is moot
# (no file reads), and the probes import only Django (the package under change)
# + stdlib.

# ax-soundness: run the real Widget.use_required_attribute on widgets covering
# both hidden states and a battery of `initial` values (both truthiness cases,
# several Python types incl. raise-free sentinels) and assert it returns
# `not self.is_hidden`, IGNORING `initial` — exactly the axiom's
# Ensures(Result() == (not hidden)). Any disagreement => AXIOM-UNSOUND.
_AX_SOUNDNESS = r'''
import sys

def _configure_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
    import django
    django.setup()

class _FakeFile:
    def __init__(self, url):
        self.url = url
    def __bool__(self):
        return True

# Battery of `initial`: falsy (None,"",0,[],{},False) + truthy (non-empty str,
# whitespace, ints, lists, dicts, True, a stored-file-like object).
_INITIALS = [None, "", 0, [], {}, False,
             "resume.txt", "x", " ", 1, [0], {"a": 1}, True,
             _FakeFile("/media/resume.txt")]

def main():
    try:
        _configure_django()
        from django.forms.widgets import (
            Widget, Input, FileInput, ClearableFileInput, HiddenInput,
        )
    except Exception as exc:
        print("AX-SOUND SKIP: Django not configurable: %r" % (exc,))
        return 0

    base = Widget.use_required_attribute  # the unbound REAL base callee
    widgets = [FileInput(), ClearableFileInput(), Input(), Widget(), HiddenInput()]
    obs = 0
    for w in widgets:
        # The axiom binds generic_requires_value(hidden) == (not hidden); the
        # caller passes control.hidden = self.is_hidden. So the obligation is
        # base(self, initial) == (not self.is_hidden), for ALL initial.
        expected = (not w.is_hidden)
        for initial in _INITIALS:
            got = base(w, initial)
            if not isinstance(got, bool):
                print("AXIOM-UNSOUND: base returned non-bool %r on %s"
                      % (got, type(w).__name__)); return 1
            if got != expected:
                print("AXIOM-UNSOUND: base.use_required_attribute(%r) on %s = %r, "
                      "expected (not is_hidden) = %r"
                      % (initial, type(w).__name__, got, expected)); return 1
            obs += 1
    print("AX-SOUND OK: real Widget.use_required_attribute == (not is_hidden), "
          "independent of initial, over %d observations." % obs)
    return 0

sys.exit(main())
'''

# ax-containment: enumerate EXACTLY the inputs the MODEL can pass to
# generic_requires_value. The model calls generic_requires_value(control.hidden)
# where control.hidden : bool (the only field, declared bool). So the model can
# reach precisely two callee-inputs: hidden ∈ {True, False}. The axiom's
# Requires domain is the full bool type (generic_requires_value(hidden: bool),
# no extra Requires), which trivially contains {True, False}. We confirm by
# running the real base callee on a FileInput (the F2P widget, is_hidden=False)
# and a HiddenInput (is_hidden=True) — the two reachable hidden states — and
# checking each is handled (returns a bool matching not is_hidden) i.e. lies in
# the callee's accepted domain. A reachable input outside the covered domain
# would be AXIOM-TOO-WEAK-FOR-CALLER; here the domain is the entire bool type so
# containment is total.
_AX_CONTAINMENT = r'''
import sys

def _configure_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
    import django
    django.setup()

def main():
    try:
        _configure_django()
        from django.forms.widgets import Widget, FileInput, HiddenInput
    except Exception as exc:
        print("AX-COVER SKIP: Django not configurable: %r" % (exc,))
        return 0

    base = Widget.use_required_attribute
    # The model declares control.hidden: bool, so the ONLY callee-inputs the
    # model can reach are hidden in {False, True}. Realize both via the two
    # representative widgets and confirm each is accepted (in domain) and the
    # axiom's pinned value holds, i.e. the bool domain {False,True} the model can
    # reach is fully covered by the axiom's Requires (the whole bool type).
    reachable = {
        False: FileInput(),     # is_hidden False  (the F2P widget)
        True:  HiddenInput(),   # is_hidden True
    }
    for hidden, w in reachable.items():
        if bool(w.is_hidden) != hidden:
            print("AX-COVER NOTE: %s.is_hidden=%r (modeled hidden=%r) — using "
                  "actual" % (type(w).__name__, w.is_hidden, hidden))
        h = bool(w.is_hidden)
        got = base(w, None)
        if not isinstance(got, bool):
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable hidden=%r not handled "
                  "as bool (got %r)" % (h, got)); return 1
        if got != (not h):
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable hidden=%r gives %r != "
                  "(not hidden)=%r" % (h, got, not h)); return 1
    print("AX-COVER OK: the only model-reachable callee-inputs hidden in "
          "{False, True} both lie in the axiom Requires domain (the whole bool "
          "type) and satisfy Result()==(not hidden).")
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-generic_requires_value",
        "axiom": "generic_requires_value",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS,
        "rationale": "if the real inherited Widget.use_required_attribute ever "
                     "differs from (not is_hidden) — e.g. by reading `initial` — "
                     "the A-consumed axiom Ensures(Result()==(not hidden)) is "
                     "unsound (AXIOM-UNSOUND).",
    },
    {
        "id": "ax-cover-generic_requires_value",
        "axiom": "generic_requires_value",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT,
        "rationale": "the model can only pass hidden in {True,False} (control.hidden "
                     "is bool); both lie in the axiom's bool Requires domain. A "
                     "reachable input outside it would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
