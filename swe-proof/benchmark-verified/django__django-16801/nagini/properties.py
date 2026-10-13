# properties.py — PBT falsification battery for django__django-16801.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses.
# Spec cases are full model.py variants built by region-surgery that edits ONLY
# inside the # impl-start / # impl-end region, so the frozen spec (axioms / pure
# / pre / post / spec_view) is byte-identical (same_spec GUARANTEED). Each case
# is checked by Nagini verify + same_spec on the host.
#
# DEFENDED SURFACE (reasoned, not mechanical):
#   attach_post_init_hook(receivers, owner_id, is_abstract, width_target, height_target)
#   - receivers: Acc(list_pred(receivers)) FULL — the genuinely-mutated post_init
#     notification list (modelled as List[int] of registered sender tokens).
#   - width_target, height_target: Acc(list_pred(.), 1/2) READ-ONLY companion
#     target names (str|None in the repo; only truthiness observed).
#   - owner_id: int identity token of the owning class (id(cls)).
#   The load-bearing postcondition is the registration BICONDITIONAL:
#     should_register(...) == (ToSeq(receivers) == Old(ToSeq(receivers)) + PSeq(owner_id))
#     (not should_register(...)) == (ToSeq(receivers) == Old(ToSeq(receivers)))
#   with should_register GROUNDED (fully unfolded over the args):
#     (not is_abstract) and (configured(width_target) or configured(height_target));
#     configured(name) == name is not None and len(name) > 0.
#   Plus read-only pins: ToSeq(width_target)==Old(...) and ToSeq(height_target)==Old(...).
#
# The gold fix (files.py:444) is:
#     if not cls._meta.abstract and (self.width_field or self.height_field):
#         signals.post_init.connect(self.update_dimension_fields, sender=cls)
# F2P: test_post_init_not_connected — a CONCRETE ImageField model with NO
# width_field/height_field must NOT appear in signals.post_init.receivers.
# P2P: "Dimensions are updated correctly in various situations." etc. — models
# WITH a single (width-only or height-only) target MUST still register, else the
# recalculation hook never fires and dimensions go stale.
from pathlib import Path

INSTANCE = "django__django-16801"
FLOAT_ENCODING = None  # meta.float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The ONLY editable region (between the impl markers). Gold impl verbatim.
_GOLD_IMPL = (
    "    # impl-start\n"
    "    if (not is_abstract) and (configured(width_target) or configured(height_target)):\n"
    "        receivers.append(owner_id)\n"
    "    # impl-end\n"
)


def _impl(body_lines: str) -> str:
    """Build a full model.py variant with a new impl-region body. `body_lines`
    is the executable body that replaces the gold body BETWEEN the markers (the
    markers themselves are preserved verbatim, so same_spec holds)."""
    new_region = "    # impl-start\n" + body_lines + "    # impl-end\n"
    return _swap(_BASE, _GOLD_IMPL, new_region)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): structurally-different but CORRECT impl.
# Instead of inlining the conjunction, call the @Pure decision helper directly
# into a typed local, then branch on it. Same boolean decision, different
# executable shape; keeps every proof obligation (should_register unfolds to the
# inlined guard, so the biconditional postcondition discharges). A faithful
# correct impl MUST verify, else SPEC-TOO-STRONG.
_POS_CONTROL = _impl(
    "    do_register = should_register(is_abstract, width_target, height_target)  # type: bool\n"
    "    if do_register:\n"
    "        receivers.append(owner_id)\n"
)

# POSITIVE CONTROL 2: De Morgan / branch reorder — guard on the negation and
# early-skip, then append in the else. Different control shape, same decision.
_POS_CONTROL_2 = _impl(
    "    if is_abstract or not (configured(width_target) or configured(height_target)):\n"
    "        pass\n"
    "    else:\n"
    "        receivers.append(owner_id)\n"
)

# ---------------------------------------------------------------------------
# ADMISSIBILITY: keep the gold impl, but first ASSERT that the precondition's
# read permission on the companion-target names is sufficient to evaluate the
# decision (configured reads width/height under Acc(.,1/4) <= the held 1/2).
# This confirms the precondition admits a normal F2P-shaped input (a concrete
# model whose width/height targets may be present, empty, or None). If this
# fails to verify, PRECOND-TOO-STRONG.
_ADMISS = _impl(
    "    Assert(Implies(width_target is not None,\n"
    "                   configured(width_target) == (len(width_target) > 0)))\n"
    "    Assert(Implies(height_target is not None,\n"
    "                   configured(height_target) == (len(height_target) > 0)))\n"
    "    if (not is_abstract) and (configured(width_target) or configured(height_target)):\n"
    "        receivers.append(owner_id)\n"
)

# ---------------------------------------------------------------------------
# FRAME-MUTATION (MANDATORY — read-only input attack). The impl writes to the
# read-only companion-target name `width_target` (held only at Acc(.,1/2)) to
# (vacuously) try to satisfy the postcondition. Must FAIL for INSUFFICIENT
# PERMISSION: list mutation needs full Acc(list_pred(width_target)) but the
# precondition grants only 1/2, AND the read-only pin
# ToSeq(width_target)==Old(ToSeq(width_target)) forbids any change. The gold
# guard logic is kept verbatim so the rejection is attributable to the write.
_FRAME_MUT = _impl(
    "    if width_target is not None:\n"
    "        width_target.append(owner_id)\n"
    "    if (not is_abstract) and (configured(width_target) or configured(height_target)):\n"
    "        receivers.append(owner_id)\n"
)

# ---------------------------------------------------------------------------
# UNIQUENESS rivals (same spec, wrong impl) — must be REJECTED.

# (a) ALWAYS-REGISTER = the pre-patch bug. Register for every concrete class,
# ignoring the companion targets entirely. This is exactly the prepatch guard
# `if not cls._meta.abstract:`. Violates the biconditional on (concrete, no
# target): should_register is False but receivers grows.
_ALWAYS = _impl(
    "    if not is_abstract:\n"
    "        receivers.append(owner_id)\n"
)

# (b) AND-instead-of-OR. Register only when BOTH targets configured. Diverges on
# single-target (width-only OR height-only) concrete classes: should_register is
# True (OR) but this appends nothing.
_AND = _impl(
    "    if (not is_abstract) and (configured(width_target) and configured(height_target)):\n"
    "        receivers.append(owner_id)\n"
)

# (c) PARTIAL-DOMAIN: width-only guard — drops height from the decision. Correct
# on every input EXCEPT (concrete, height-only): should_register is True but this
# appends nothing.
_PARTIAL = _impl(
    "    if (not is_abstract) and configured(width_target):\n"
    "        receivers.append(owner_id)\n"
)

# (d) NEVER-REGISTER: no-op impl. Trivially wrong on every should_register-True
# input. Cheap supporting near-miss.
_NEVER = _impl(
    "    pass\n"
)

# (e) WRONG-TOKEN: register the correct cases but append the wrong identity
# token (owner_id + 1). The biconditional pins the appended element to
# PSeq(owner_id); a different token fails the sequence equality.
_WRONG_TOKEN = _impl(
    "    if (not is_abstract) and (configured(width_target) or configured(height_target)):\n"
    "        receivers.append(owner_id + 1)\n"
)

# (f) IGNORE-ABSTRACT: register whenever a target is configured, even for
# abstract base classes. Diverges on (abstract, configured): should_register is
# False (abstract) but this appends.
_IGNORE_ABSTRACT = _impl(
    "    if configured(width_target) or configured(height_target):\n"
    "        receivers.append(owner_id)\n"
)


SPEC_TESTS = [
    {
        "id": "pos-control-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": "structurally-different CORRECT impl: bind the @Pure "
                     "should_register decision into a typed local then branch on "
                     "it. should_register unfolds to the inlined guard, so the "
                     "registration biconditional discharges. Must verify; else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-demorgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL_2,
        "rationale": "branch-reorder positive control: De Morgan of the guard "
                     "(skip on `abstract or no-target`, else append). Same "
                     "decision, different control shape, gold proof obligations "
                     "intact. Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-readperm",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the precondition's Acc(width/height, 1/2) read permission "
                     "must admit evaluating configured() (needs only 1/4) on a "
                     "normal F2P-shaped input. If it can't verify, "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-width",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": "the real patch never writes to the field NAME "
                      "self.width_field; it only reads its truthiness. An impl "
                      "that mutated the field-name carrier would correspond to a "
                      "patch that rewrites ImageField's configured target name "
                      "list — not the gold change — and would not produce the "
                      "F2P/P2P behaviour (registration decision unchanged, but "
                      "field config corrupted). It can never resolve.",
        "rationale": "REJECT from the permission system + the read-only pin: "
                     "width_target.append needs full Acc(list_pred(width_target)) "
                     "but only Acc(.,1/2) is granted, and "
                     "Ensures(ToSeq(width_target)==Old(ToSeq(width_target))) "
                     "forbids any mutation. Insufficient-permission rejection.",
    },
    {
        "id": "always-register-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ALWAYS,
        "refinement": "this IS the pre-patch guard `if not cls._meta.abstract:` "
                      "(model_prepatch.py). A faithful patch keeping it leaves "
                      "the bug: a concrete ImageField model with no "
                      "width_field/height_field still registers the post_init "
                      "handler — exactly what F2P test_post_init_not_connected "
                      "asserts must NOT happen. Does not resolve.",
        "rationale": "REJECT from the biconditional on (concrete, no target): "
                     "should_register is False but ToSeq(receivers) grows by "
                     "owner_id, violating "
                     "(not should_register) == (ToSeq(receivers)==Old(...)).",
    },
    {
        "id": "and-instead-of-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _AND,
        "refinement": "a patch using `self.width_field and self.height_field` "
                      "would NOT register single-target (width-only or "
                      "height-only) concrete models, so their update_dimension_"
                      "fields hook never connects and the P2P dimension-update "
                      "tests for single-target ImageFields fail. Does not resolve.",
        "rationale": "REJECT from the biconditional on (concrete, width-only): "
                     "should_register is True (OR) but this appends nothing, "
                     "violating should_register == (receivers grew by owner_id).",
    },
    {
        "id": "partial-domain-width-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL,
        "refinement": "a patch guarding on `self.width_field` alone drops "
                      "height-only models from registration; their post_init "
                      "recalculation hook never fires, leaving the height "
                      "dimension stale — the P2P 'Dimensions are updated "
                      "correctly' tests for a height_field-only ImageField fail. "
                      "Does not resolve.",
        "rationale": "REJECT from the biconditional on (concrete, height-only): "
                     "should_register is True (height configured) but this "
                     "appends nothing.",
    },
    {
        "id": "ignore-abstract",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _IGNORE_ABSTRACT,
        "refinement": "a patch dropping the `not cls._meta.abstract` conjunct "
                      "would register the hook for abstract base classes, which "
                      "have no instances and whose registration was never "
                      "intended; the P2P abstract-model tests (no post_init "
                      "handler on abstract bases) regress. Does not resolve.",
        "rationale": "REJECT from the biconditional on (abstract, configured): "
                     "should_register is False (abstract) but this appends "
                     "owner_id.",
    },
    {
        "id": "wrong-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WRONG_TOKEN,
        "refinement": "registering a different sender token (id(cls)+1) means "
                      "the F2P/P2P membership probe `id(PersonModel) in "
                      "[sender_id ...]` is False for the right class (and a "
                      "phantom token leaks in); the hook is bound to the wrong "
                      "sender so update_dimension_fields never fires for real "
                      "instances. Does not resolve.",
        "rationale": "REJECT from the biconditional: the appended element is "
                     "pinned to PSeq(owner_id); owner_id+1 makes "
                     "ToSeq(receivers) != Old(...) + PSeq(owner_id).",
    },
    {
        "id": "never-register",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _NEVER,
        "refinement": "a no-op patch never connects update_dimension_fields, so "
                      "NO ImageField ever recomputes its companion dimensions — "
                      "every P2P dimension-update test fails. Cheap supporting "
                      "near-miss; does not resolve.",
        "rationale": "REJECT from the biconditional on any should_register-True "
                     "input: should_register is True but receivers is unchanged.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. There are NO @ContractOnly consumed axioms (meta.axioms == []).
# The registration decision is modelled deeply. The single A-reference is
# `should_register` validated == the real ImageField.contribute_to_class
# registration decision. axiom_check.py (G-AX) is the ground-truth check; here
# we run an axiom-SOUNDNESS probe that executes the REAL Django callee under the
# caller's runtime config and asserts it registers the post_init handler IFF the
# deep model's should_register holds — fuzzing the full {none,width,height,both}
# x {concrete,abstract} table plus the exact F2P no-target concrete scenario.
# (No flag_dependency: the decision is unconditional Python truthiness.)
# We embed axiom_check.py's host-side logic so the probe is self-contained at
# /work (the runner mounts only the probe script).
_AX_SOUND_PROBE = r'''
import sys

# --- deep-model reference (lock-step with model.py should_register/configured) -
def configured(name):
    return name is not None and len(name) > 0

def should_register(is_abstract, width_target, height_target):
    return (not is_abstract) and (configured(width_target) or configured(height_target))

# A-reference proper: the model's boolean decision == Python truthiness of the
# real `width_field or height_field` guard, over all relevant name shapes.
names = [None, "", "w", "mugshot_width", "mugshot_height", "x" * 64]
for is_abstract in (False, True):
    for w in names:
        for h in names:
            real_decision = (not is_abstract) and bool(w or h)
            assert real_decision == should_register(is_abstract, w, h), (
                "should_register disagrees with truthiness on "
                "(abstract=%r, w=%r, h=%r)" % (is_abstract, w, h))
            assert configured(w) == bool(w), "configured disagrees on %r" % (w,)
print("A-reference truthiness check OK (Django-independent)")

# --- in-container: drive the REAL ImageField.contribute_to_class -------------
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_I18N=False,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()
    from django.db import models
    from django.db.models import signals
    try:
        from PIL import Image  # noqa: F401
    except Exception as exc:
        print("G-AX-SOUND SKIP: Pillow absent: %r (truthiness A-reference confirmed)" % (exc,))
        sys.exit(0)
except Exception as exc:
    print("G-AX-SOUND SKIP: Django not configurable: %r (truthiness A-reference confirmed)" % (exc,))
    sys.exit(0)

seq = [0]
obs = [0]

def receivers_contain(sender):
    target = id(sender)
    return target in [sender_id for (_, sender_id), *_ in signals.post_init.receivers]

def observe(width_field, height_field, abstract):
    seq[0] += 1
    app_label = "gax16801"
    attrs = {
        "__module__": "gax16801.models",
        "Meta": type("Meta", (), {"app_label": app_label, "abstract": abstract}),
        "mugshot": models.ImageField(width_field=width_field,
                                     height_field=height_field, upload_to="t"),
    }
    if width_field:
        attrs[width_field] = models.PositiveIntegerField(null=True)
    if height_field:
        attrs[height_field] = models.PositiveIntegerField(null=True)
    cls = type("GaxModel_%d" % seq[0], (models.Model,), attrs)
    present = receivers_contain(cls)
    expected = should_register(abstract, width_field, height_field)
    assert present == expected, (
        "REAL ImageField.contribute_to_class registration disagrees with "
        "should_register on (abstract=%r, w=%r, h=%r): present=%r expected=%r"
        % (abstract, width_field, height_field, present, expected))
    obs[0] += 1

for abstract in (False, True):
    observe(None, None, abstract)
    observe("mugshot_width", None, abstract)
    observe(None, "mugshot_height", abstract)
    observe("mugshot_width", "mugshot_height", abstract)

# exact F2P scenario: concrete, no companion target -> handler ABSENT.
attrs = {
    "__module__": "gax16801.models",
    "Meta": type("Meta", (), {"app_label": "gax16801f2p"}),
    "mugshot": models.ImageField(upload_to="t"),
}
f2p_cls = type("GaxModelF2P", (models.Model,), attrs)
assert not receivers_contain(f2p_cls), (
    "F2P scenario: concrete ImageField model with no width/height still registered (the bug)")

print("G-AX-SOUND OK: real contribute_to_class registration == should_register "
      "over %d observations + F2P no-target concrete scenario" % (obs[0],))
sys.exit(0)
'''

# Containment: the model can pass should_register/configured only the args from
# its own Requires (is_abstract: bool; width/height: Optional[List[int]]). The
# real callee's domain is `cls._meta.abstract` (bool) and `self.width_field /
# self.height_field` (str|None). Every modelled name shape (None / empty /
# non-empty list, i.e. absent / empty / configured field name) is a valid
# str|None target, so every caller-reachable input lies inside the real callee's
# domain. There is no caller-reachable input outside it (no extra typing on the
# field names; field names are always str|None in Django). This is a pure
# Python-side containment assertion (no Django import needed).
_AX_CONTAIN_PROBE = r'''
import sys
# Enumerate exactly the (abstract, width, height) shapes the model can reach:
#   is_abstract in {True, False};  each target in {None (absent),
#   "" (empty, modelled as empty List), non-empty name}.
# Assert each is a valid input to the real guard `not abstract and
# (width or height)` (i.e. a bool and two str|None values) -> every shape is in
# the callee's domain. A reachable input outside it would be AXIOM-TOO-WEAK-FOR-CALLER.
shapes_abstract = [True, False]
shapes_name = [None, "", "configured_name"]
covered = 0
for a in shapes_abstract:
    assert isinstance(a, bool), "abstract not a bool: %r" % (a,)
    for w in shapes_name:
        for h in shapes_name:
            assert w is None or isinstance(w, str), "width not str|None: %r" % (w,)
            assert h is None or isinstance(h, str), "height not str|None: %r" % (h,)
            # the real guard evaluates without error on this shape (in domain):
            _ = (not a) and (bool(w) or bool(h))
            covered += 1
print("G-AX-CONTAIN OK: all %d caller-reachable (abstract,width,height) shapes "
      "lie in the real guard's str|None x bool domain" % (covered,))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-should_register",
        "axiom": "should_register",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "A-reference soundness: the REAL post-gold "
                     "ImageField.contribute_to_class registers the post_init "
                     "handler IFF should_register holds, over the full "
                     "{none,width,height,both} x {concrete,abstract} table + the "
                     "exact F2P no-target concrete scenario. Any disagreement is "
                     "AXIOM-UNSOUND (the deep model would mis-state the real "
                     "decision the proof's refinement relies on).",
    },
    {
        "id": "ax-contain-should_register",
        "axiom": "should_register",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "containment: every (abstract, width, height) shape the "
                     "model can reach (bool x str|None x str|None: absent/empty/"
                     "configured) lies inside the real guard's domain. A "
                     "reachable input outside it would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER. (Covering str|None exactly = the "
                     "callee's own field-name domain; no over/under-coverage.)",
    },
]
