# properties.py — PBT falsification battery for sphinx-doc__sphinx-7910.
#
# NOT a Nagini module: a record of adversarial cases the runner (swebench_nagini.pbt)
# executes. Spec cases are full model.py variants that share the FROZEN spec
# byte-for-byte (only the # impl-start/# impl-end region is edited — region surgery
# GUARANTEES same_spec) and are checked by Nagini verify. Axiom cases are
# self-contained, stdlib-only probes run in the instance Docker image against the
# REAL callee (inspect.unwrap).
#
# Defended surface (read from model.py + refinement.md + the gold patch + the F2P
# test test_class_decorated_doc):
#
#   skip_decision(obj, is_special, is_init, is_private, inc_special, inc_init,
#                 inc_private) -> Optional[bool]
#
#   * obj: MemberObj is READ-ONLY — every touched field is held at Acc(.,1/2)
#     and its namespace at Acc(dict_pred(obj.ns),1/4). => FRAME-MUTATION is
#     MANDATORY (directive 5 / PBT_PLAN §4a).
#   * LOAD-BEARING postcondition clause (the biconditional):
#       (Result() is False) ==
#         (obj.has_doc and obj.is_class_member and
#          ((is_special and inc_special) or (is_init and inc_init) or
#           (is_private and inc_private)))
#     plus  Result() is False or Result() is None.
#     This is GROUNDED in the input (obj.is_class_member, the ground-truth
#     ownership), NOT pinned to an opaque @Pure answer-key. The `canonical`
#     axiom is CONSUMED in the impl (it bridges canon.ns lookup == is_class_member)
#     and never appears in an Ensures, so there is no "echo the oracle" attack —
#     see 'assessment'. We therefore use a structural positive control instead of
#     an ungrounded-oracle echo, plus a full set of uniqueness rivals each tied to
#     a slice of the biconditional.
#   * axiom `canonical` (@ContractOnly, A-consumed) models sphinx.util.inspect.unwrap
#     (-> CPython inspect.unwrap). Two axiom probes: soundness (real callee matches
#     the axiom Ensures, incl. the ValueError/cycle path) + caller-domain containment.

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7910"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r} ({src.count(old)}x)")
    return src.replace(old, new, 1)


# The frozen gold impl region (verbatim from model.py, between # impl-start /
# # impl-end). Every rival is built by editing ONLY text inside this block.
_GOLD_IMPL = """    doc = obj.has_doc
    member = obj.is_class_member
    if not doc:
        return None
    # Resolve the owning class through the ORIGINAL (unwrapped) object's
    # namespace -- the namespace that genuinely knows the class.
    canon = canonical(obj)
    Assert(canon.cls_name == obj.cls_name)
    Assert(canon.is_class_member == member)
    cls_is_owner = False
    if obj.cls_name in canon.ns:
        cls_is_owner = canon.ns[obj.cls_name]
    # The unwrapped namespace lookup recovers the ground-truth ownership.
    Assert(cls_is_owner == member)
    if cls_is_owner:
        if ((is_special and inc_special) or
                (is_init and inc_init) or
                (is_private and inc_private)):
            return False
    return None"""

assert _GOLD_IMPL in _BASE, "gold impl region drifted from model.py"


# =====================================================================
#  SPEC TESTS  (Nagini verify + same_spec against the frozen model.py)
# =====================================================================

SPEC_TESTS = []

# ---------------------------------------------------------------------
# (1) FRAME-MUTATION  (MANDATORY — obj is read-only). expect=reject.
#     A rival that WRITES to obj.has_doc (a 1/2-permission field) to make the
#     decision come out the gold way "for free". The spec must reject this for
#     INSUFFICIENT PERMISSION (Acc(obj.has_doc,1/2) is read-only; a write needs
#     full permission). All gold invariants/asserts kept verbatim so the rejection
#     is attributable solely to the write. The write is a no-op on the VALUE
#     (re-storing the same bool), so it could not change behaviour — it can only
#     fail on the permission system, which is exactly the point.
SPEC_TESTS.append({
    "id": "frame-mutate-has_doc",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        "    doc = obj.has_doc\n    member = obj.is_class_member",
        "    doc = obj.has_doc\n    obj.has_doc = doc  # WRITE to a read-only (1/2) field\n    member = obj.is_class_member",
    ),
    "refinement": (
        "A faithful real patch behaves like the gold here (re-storing the same "
        "value is a value no-op), so it WOULD still resolve test_class_decorated_doc. "
        "The point is the permission frame: the autodoc-skip-member hook's member "
        "object is an external library object the hook must not mutate; the spec "
        "encodes that as Acc(obj.has_doc,1/2) (read-only). A model that needs to "
        "WRITE the input to verify has escaped the frame the gold respects. If this "
        "verified, the frame condition would be vacuous."),
    "rationale": (
        "Rejected by the PERMISSION SYSTEM: obj.has_doc is held at Acc(.,1/2); a "
        "store requires full permission. Insufficient-permission, not a value "
        "mismatch."),
})

# Supporting frame-mutation: write to obj.cls_name (another 1/2 field).
SPEC_TESTS.append({
    "id": "frame-mutate-cls_name",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        "    cls_is_owner = False\n    if obj.cls_name in canon.ns:",
        "    cls_is_owner = False\n    obj.cls_name = obj.cls_name  # WRITE to a read-only (1/2) field\n    if obj.cls_name in canon.ns:",
    ),
    "refinement": (
        "Same value (self-assign) so a real patch's behaviour is unchanged and it "
        "would still resolve; the rejection is purely the read-only frame on "
        "obj.cls_name (Acc(.,1/2)). Supporting case for the mandatory frame probe."),
    "rationale": "Rejected by the permission system: Acc(obj.cls_name,1/2) is read-only.",
})

# ---------------------------------------------------------------------
# (2) PRE-PATCH OPERAND  (the model_prepatch.py defect). expect=reject.
#     Resolve ownership through obj.ns (the wrapper's OWN namespace) instead of
#     canon.ns (the unwrapped original's). This is the one operand the gold patch
#     changes. The Assert(cls_is_owner == member) then cannot be discharged: the
#     axiom only ties canon.ns (not obj.ns) to ground-truth ownership, so the
#     postcondition biconditional fails.
SPEC_TESTS.append({
    "id": "prepatch-obj-ns",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        "    cls_is_owner = False\n    if obj.cls_name in canon.ns:\n        cls_is_owner = canon.ns[obj.cls_name]",
        "    cls_is_owner = False\n    if obj.cls_name in obj.ns:\n        cls_is_owner = obj.ns[obj.cls_name]",
    ),
    "refinement": (
        "This IS the pre-patch repo line `cls = obj.__globals__[cls_path]`. On the "
        "F2P member SampleClass.__decorated_func__ (functools.wraps-decorated, "
        "decorator defined in sphinx/testing/util.py), the WRAPPER's __globals__ "
        "does NOT contain SampleClass, so cls_is_owner=False and _skip_member "
        "returns None (skip) — but test_class_decorated_doc expects False (include). "
        "The faithful real patch does NOT resolve. (Confirmed by G-AX: wrapper "
        "namespace misses the class; unwrapped namespace recovers it.)"),
    "rationale": (
        "Rejected by the postcondition biconditional: the canonical axiom ties "
        "canon.ns[cls_name] (NOT obj.ns[cls_name]) to is_class_member, so "
        "Assert(cls_is_owner == member) is unprovable through obj.ns."),
})

# ---------------------------------------------------------------------
# (3) UNIQUENESS — always abstain. expect=reject.
#     Cheapest impl satisfying the disjunctive half (Result is False or None) by
#     never returning False. Fails the biconditional whenever a documented, owned,
#     enabled-category member exists (Result must be False there).
SPEC_TESTS.append({
    "id": "always-none",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        _GOLD_IMPL,
        "    return None",
    ),
    "refinement": (
        "Always-skip: _skip_member would never include a documented owned member, "
        "so test_class_decorated_doc (expects include => False) FAILS, as do the "
        "P2P include cases. Does not resolve."),
    "rationale": (
        "Rejected by the biconditional: when has_doc and is_class_member and an "
        "enabled category hold, Result() must be False, but this returns None."),
})

# ---------------------------------------------------------------------
# (4) UNIQUENESS — always include when documented (drop ownership + category).
#     expect=reject. Over-includes: returns False whenever doc present, ignoring
#     is_class_member AND the category-enabled disjunction.
SPEC_TESTS.append({
    "id": "include-if-doc",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        _GOLD_IMPL,
        "    if not obj.has_doc:\n        return None\n    return False",
    ),
    "refinement": (
        "Returns False (include) for ANY documented member, including non-owned "
        "ones or members whose category is disabled. _skip_member would document "
        "members it must skip (e.g. a documented member with its category config "
        "False), failing the P2P assertSkip cases that re-disable the config and "
        "expect None. Does not resolve."),
    "rationale": (
        "Rejected by the biconditional: when is_class_member is False (or no "
        "category enabled) Result() must be None, but this returns False."),
})

# ---------------------------------------------------------------------
# (5) PARTIAL-DOMAIN — handle only the `is_special` category, drop init/private.
#     expect=reject. Correct on the special branch (the F2P category), wrong on
#     the is_init / is_private sub-domains.
SPEC_TESTS.append({
    "id": "partial-special-only",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        "    if cls_is_owner:\n        if ((is_special and inc_special) or\n                (is_init and inc_init) or\n                (is_private and inc_private)):\n            return False",
        "    if cls_is_owner:\n        if is_special and inc_special:\n            return False",
    ),
    "refinement": (
        "Correct for the F2P (a __special__ member) but a documented, owned "
        "__init__ with napoleon_include_init_with_doc=True (the original bug "
        "report's exact scenario — a decorated __init__) would be SKIPPED (None) "
        "instead of included (False). A faithful real patch with this body fails "
        "the init/private P2P include cases. Does not resolve."),
    "rationale": (
        "Rejected by the biconditional on the is_init / is_private sub-domain: "
        "Result() must be False there too, but this returns None."),
})

# ---------------------------------------------------------------------
# (6) PARTIAL-DOMAIN — invert the doc guard (abstain when documented).
#     expect=reject. Mirrors the boundary: handles the undocumented domain wrong.
SPEC_TESTS.append({
    "id": "partial-invert-doc",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        "    doc = obj.has_doc\n    member = obj.is_class_member\n    if not doc:\n        return None",
        "    doc = obj.has_doc\n    member = obj.is_class_member\n    if doc:\n        return None",
    ),
    "refinement": (
        "Abstains exactly on documented members — the only members that can ever be "
        "included — so the F2P documented __decorated_func__ yields None, not False. "
        "Does not resolve."),
    "rationale": (
        "Rejected by the biconditional: a documented owned enabled member must be "
        "False, but the inverted guard returns None for every documented member."),
})

# ---------------------------------------------------------------------
# (7) POSITIVE CONTROL — structurally different but CORRECT. expect=verify.
#     Reordered/reshaped impl: compute the category-enabled flag into a local up
#     front, fold the doc guard into the final decision, and use a single return
#     site. KEEPS every gold proof obligation (the canon asserts and the
#     cls_is_owner==member bridge) so it is a SPEC test, not a proof-gap test.
#     If this cannot verify => SPEC-TOO-STRONG.
SPEC_TESTS.append({
    "id": "pos-control-reshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE,
        _GOLD_IMPL,
        "    member = obj.is_class_member\n"
        "    if not obj.has_doc:\n"
        "        return None\n"
        "    # category-enabled flag computed first (reshape, same value)\n"
        "    enabled = ((is_special and inc_special) or\n"
        "               (is_init and inc_init) or\n"
        "               (is_private and inc_private))\n"
        "    # Resolve ownership through the unwrapped namespace (gold bridge kept).\n"
        "    canon = canonical(obj)\n"
        "    Assert(canon.cls_name == obj.cls_name)\n"
        "    Assert(canon.is_class_member == member)\n"
        "    cls_is_owner = False\n"
        "    if obj.cls_name in canon.ns:\n"
        "        cls_is_owner = canon.ns[obj.cls_name]\n"
        "    Assert(cls_is_owner == member)\n"
        "    result = None  # type: Optional[bool]\n"
        "    if cls_is_owner and enabled:\n"
        "        result = False\n"
        "    return result",
    ),
    "rationale": (
        "A correct, structurally-different impl (enabled-flag hoisted, single "
        "return, doc guard reordered) must verify against the frozen spec. The "
        "gold canon/Assert bridges are kept verbatim so this exercises the SPEC, "
        "not an auto-discharge proof gap. If it fails => SPEC-TOO-STRONG."),
})

# ---------------------------------------------------------------------
# (8) ADMISSIBILITY — an F2P-shaped input establishes the precondition.
#     expect=verify. Inside the impl region we construct a fresh MemberObj that
#     mirrors the F2P member (documented, owned, special) and self-call
#     skip_decision on it with is_special & inc_special — the precondition must be
#     establishable (mutually-exclusive category flags hold) and the call must
#     verify. If the Requires cannot be met for this normal input =>
#     PRECOND-TOO-STRONG. The gold logic for the REAL `obj` is unchanged below.
SPEC_TESTS.append({
    "id": "admiss-f2p-shaped",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE,
        "    doc = obj.has_doc\n    member = obj.is_class_member\n    if not doc:\n        return None",
        "    # --- admissibility probe: build an F2P-shaped MemberObj and self-call ---\n"
        "    probe_ns = {}  # type: Dict[int, bool]\n"
        "    probe_ns[7] = True   # class-name token 7 owns the member\n"
        "    probe_obj = MemberObj(True, True, 7, probe_ns)\n"
        "    # is_special selected, inc_special enabled; init/private off — the\n"
        "    # category flags satisfy the mutual-exclusivity precondition.\n"
        "    _ = skip_decision(probe_obj, True, False, False, True, False, False)\n"
        "    # --- end admissibility probe (gold logic for the real obj follows) ---\n"
        "    doc = obj.has_doc\n    member = obj.is_class_member\n    if not doc:\n        return None",
    ),
    "rationale": (
        "A representative F2P-shaped input (documented, owned, special, special "
        "config enabled) must satisfy Requires so the self-call verifies. If it "
        "cannot, the precondition is too strong (PRECOND-TOO-STRONG)."),
})


# =====================================================================
#  AXIOM TESTS  (real callee inspect.unwrap, in the instance Docker image)
# =====================================================================

# The axiom probes embed the host-side axiom_check.py soundness logic (stdlib-only:
# functools / inspect / types) so they are self-contained — the runner mounts ONLY
# the probe script at /work (model.py / axiom_check.py are NOT in-container,
# directive 6). All file reads (none here) would use encoding="utf-8" (directive 5).

_AX_SOUNDNESS_PROBE = r'''
import functools, inspect, sys, types

# A decorator hosted in a SEPARATE module so the wrapper function's __globals__
# is that module's namespace, NOT the namespace where the owning classes live
# (the cross-module functools.wraps shape of the F2P test: decorator in
# sphinx/testing/util.py, classes in tests/test_ext_napoleon.py).
_deco_mod = types.ModuleType("axcheck_decorator_module")
exec(
    "import functools\n"
    "def simple_decorator(f):\n"
    "    @functools.wraps(f)\n"
    "    def wrapper(*args, **kwargs):\n"
    "        return f(*args, **kwargs)\n"
    "    return wrapper\n"
    "def double_decorator(f):\n"
    "    @functools.wraps(f)\n"
    "    def wrapper(*args, **kwargs):\n"
    "        return f(*args, **kwargs)\n"
    "    return wrapper\n",
    _deco_mod.__dict__,
)
simple_decorator = _deco_mod.simple_decorator
double_decorator = _deco_mod.double_decorator


class SampleClass:
    def __special_doc__(self):
        """SampleClass.__special_doc__.DOCSTRING"""
        pass

    @simple_decorator
    def __decorated_special__(self):
        """decorated special with doc"""
        pass

    @simple_decorator
    def __init__(self):
        """decorated init with doc"""
        pass

    @simple_decorator
    def _decorated_private(self):
        """decorated private with doc"""
        pass

    @double_decorator
    @simple_decorator
    def __twice_decorated__(self):
        """twice-decorated special with doc"""
        pass

    def __special_undoc__(self):
        pass


class SampleError(Exception):
    @simple_decorator
    def __decorated_special__(self):
        """decorated special on an Exception subclass"""
        pass

    def __special_doc__(self):
        """SampleError.__special_doc__.DOCSTRING"""
        pass


def cls_path_of(obj):
    qualname = getattr(obj, "__qualname__", "")
    cls_path, _, _ = qualname.rpartition(".")
    return cls_path


def real_cls_is_owner(globals_ns, cls_path, name):
    # The repo's `cls = globals[cls_path]; cls and hasattr(cls,name) and
    # name in cls.__dict__`, with KeyError -> cls_is_owner=False.
    if cls_path not in globals_ns:
        return False
    cls = globals_ns[cls_path]
    return bool(cls and hasattr(cls, name) and name in cls.__dict__)


def unwrap_under_repo_config(obj):
    # Prefer the actual callee the gold patch invokes (sphinx.util.inspect.unwrap),
    # which wraps stdlib inspect.unwrap with a ValueError guard returning obj.
    # Fall back to stdlib inspect.unwrap if the repo module is unavailable.
    try:
        from sphinx.util import inspect as sphinx_inspect
        return sphinx_inspect.unwrap(obj)
    except Exception:
        return inspect.unwrap(obj)


def check(owner_cls, name, expect_owned):
    obj = getattr(owner_cls, name)
    canon = unwrap_under_repo_config(obj)
    # (a) identity preserved across unwrap (functools.wraps copies metadata)
    assert canon is not None, "unwrap returned None for %s.%s" % (owner_cls.__name__, name)
    assert bool(getattr(canon, "__doc__", False)) == bool(getattr(obj, "__doc__", False)), \
        "AXIOM UNSOUND: has_doc not preserved for %s.%s" % (owner_cls.__name__, name)
    assert cls_path_of(canon) == cls_path_of(obj), \
        "AXIOM UNSOUND: cls_name not preserved for %s.%s" % (owner_cls.__name__, name)
    cls_path = cls_path_of(obj)
    truth = bool(owner_cls and hasattr(owner_cls, name) and name in owner_cls.__dict__)
    assert truth == expect_owned, \
        "fixture wrong: %s.%s owned=%r expected %r" % (owner_cls.__name__, name, truth, expect_owned)
    # (b) ground-truth ownership recovered through the UNWRAPPED namespace
    recovered = real_cls_is_owner(canon.__globals__, cls_path, name)
    assert recovered == truth, \
        "AXIOM UNSOUND: unwrapped-namespace ownership %r != ground truth %r for %s.%s" % (
            recovered, truth, owner_cls.__name__, name)
    return obj, canon, cls_path, truth


decorated = [
    (SampleClass, "__decorated_special__"),
    (SampleClass, "__init__"),
    (SampleClass, "_decorated_private"),
    (SampleClass, "__twice_decorated__"),
    (SampleError, "__decorated_special__"),
]
undecorated = [
    (SampleClass, "__special_doc__"),
    (SampleClass, "__special_undoc__"),
    (SampleError, "__special_doc__"),
]

discriminators = 0
for owner_cls, name in decorated:
    obj, canon, cls_path, truth = check(owner_cls, name, expect_owned=True)
    # The DISCRIMINATOR: wrapper's own __globals__ misses the class while the
    # unwrapped original's __globals__ recovers true ownership. (The bug fixed.)
    wrapper_sees = real_cls_is_owner(obj.__globals__, cls_path, name)
    unwrapped_sees = real_cls_is_owner(canon.__globals__, cls_path, name)
    assert wrapper_sees is False, \
        "expected wrapper namespace to miss the class for %s.%s" % (owner_cls.__name__, name)
    assert unwrapped_sees is True, \
        "expected unwrapped namespace to find the class for %s.%s" % (owner_cls.__name__, name)
    discriminators += 1

for owner_cls, name in undecorated:
    obj, canon, cls_path, truth = check(owner_cls, name, expect_owned=True)
    # undecorated: unwrap is the identity, both namespaces agree
    assert unwrap_under_repo_config(obj) is obj, \
        "unwrap not identity on undecorated %s.%s" % (owner_cls.__name__, name)
    assert real_cls_is_owner(obj.__globals__, cls_path, name) is True

# --- raise/sentinel path: the repo wrapper's ValueError guard returns obj ---
# A __wrapped__ cycle makes stdlib inspect.unwrap raise ValueError. The repo's
# sphinx.util.inspect.unwrap catches it and returns obj (still the identity),
# so the axiom's identity-on-unwrapped clause must STILL hold for the callee the
# patch actually invokes.
def _make_cycle():
    def a():
        pass
    def b():
        pass
    a.__wrapped__ = b
    b.__wrapped__ = a
    return a

cyc = _make_cycle()
try:
    from sphinx.util import inspect as sphinx_inspect
    got = sphinx_inspect.unwrap(cyc)
    assert got is cyc, "AXIOM UNSOUND: repo unwrap on a cycle must return obj (identity)"
    print("ValueError/cycle path: sphinx.util.inspect.unwrap returns obj (identity) -- OK")
except Exception as e:
    # If the repo module is not importable in this image, confirm stdlib raises
    # (so a real caller MUST guard it) -- the repo wrapper does exactly that.
    raised = False
    try:
        inspect.unwrap(cyc)
    except ValueError:
        raised = True
    assert raised, "expected stdlib inspect.unwrap to raise ValueError on a cycle"
    print("ValueError/cycle path: stdlib raises ValueError (repo wrapper guards it) -- OK (sphinx import: %s)" % e)

print("G-AX OK: canonical (== inspect.unwrap) sound on %d decorated (cross-module "
      "wraps) + %d undecorated members; %d discriminators; cycle/ValueError path OK"
      % (len(decorated), len(undecorated), discriminators))
sys.exit(0)
'''

_AX_CONTAINMENT_PROBE = r'''
import functools, inspect, sys, types

# CONTAINMENT (axiom-too-weak-for-caller check). The model calls canonical(obj)
# with the ONLY object it has: the MemberObj parameter `obj` (guarded by
# `if not obj.has_doc: return None`, so canonical is reached only for documented
# members). The axiom's Requires is purely permission to read three fields
# (Acc(obj.has_doc,1/4) & Acc(obj.is_class_member,1/4) & Acc(obj.cls_name,1/4)) —
# every MemberObj satisfies it. The faithful real callee is inspect.unwrap, whose
# domain is "any object". The containment obligation in repo terms: every member
# object the F2P/P2P test path can hand the patched line
# `inspect.unwrap(obj).__globals__[cls_path]` must be accepted by inspect.unwrap
# (no domain error) AND expose a __globals__ on the unwrapped result. We enumerate
# EXACTLY the kinds of object the caller reaches on the modeled single-component
# class/exception documented-member branch and assert each is in-domain.

_deco_mod = types.ModuleType("axcheck_decorator_module")
exec(
    "import functools\n"
    "def simple_decorator(f):\n"
    "    @functools.wraps(f)\n"
    "    def wrapper(*args, **kwargs):\n"
    "        return f(*args, **kwargs)\n"
    "    return wrapper\n",
    _deco_mod.__dict__,
)
simple_decorator = _deco_mod.simple_decorator


class SampleClass:
    @simple_decorator
    def __decorated_func__(self):
        """doc"""
        pass

    def __special_doc__(self):
        """doc"""
        pass

    @simple_decorator
    def __init__(self):
        """doc"""
        pass

    @simple_decorator
    def _decorated_private(self):
        """doc"""
        pass


class SampleError(Exception):
    @simple_decorator
    def __decorated_special__(self):
        """doc"""
        pass


def unwrap_under_repo_config(obj):
    try:
        from sphinx.util import inspect as sphinx_inspect
        return sphinx_inspect.unwrap(obj)
    except Exception:
        return inspect.unwrap(obj)


# Every caller-reachable member object on the modeled branch: documented members
# accessed as `OwnerClass.<name>` (a plain function in py3), decorated and
# undecorated, on a class and an Exception subclass, single + (composed) decorators.
reachable = [
    SampleClass.__decorated_func__,
    SampleClass.__special_doc__,
    SampleClass.__init__,
    SampleClass._decorated_private,
    SampleError.__decorated_special__,
]

for obj in reachable:
    # in-domain for inspect.unwrap: accepted without raising
    canon = unwrap_under_repo_config(obj)
    assert canon is not None, "unwrap returned None (out of axiom codomain) for %r" % (obj,)
    # the unwrapped object must expose the __globals__ the patched line indexes
    assert hasattr(canon, "__globals__"), \
        "CONTAINMENT GAP: unwrapped %r has no __globals__ (caller-reachable input " \
        "outside the axiom's usable domain)" % (obj,)
    # qualname must be present for cls_path resolution (the caller computes
    # obj.__qualname__.rpartition('.')); functools.wraps preserves it
    assert getattr(canon, "__qualname__", None) is not None, \
        "CONTAINMENT GAP: unwrapped %r has no __qualname__" % (obj,)

print("CONTAINMENT OK: all %d caller-reachable member objects are in inspect.unwrap's "
      "domain (accepted, unwrapped result exposes __globals__ + __qualname__). The "
      "axiom Requires (read-permission on 3 fields) is satisfied by every MemberObj "
      "the model constructs; nothing the caller reaches lies outside it." % len(reachable))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-canonical",
        "axiom": "canonical",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": (
            "The real callee (sphinx.util.inspect.unwrap -> stdlib inspect.unwrap) "
            "must, on every cross-module functools.wraps-decorated member AND every "
            "undecorated control, preserve has_doc/cls_name and recover ground-truth "
            "ownership through the UNWRAPPED namespace (the canonical axiom's "
            "Ensures), plus return the identity on the ValueError/cycle path the repo "
            "wrapper guards. Any disagreement => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-cover-canonical",
        "axiom": "canonical",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": (
            "Every member object the modeled single-component documented class/"
            "exception branch can hand `inspect.unwrap(obj)` (decorated/undecorated, "
            "class & Exception, __init__/special/private) is in inspect.unwrap's "
            "domain and the unwrapped result exposes __globals__/__qualname__. The "
            "axiom Requires is just read-permission on three fields, satisfied by "
            "every MemberObj. No caller-reachable input lies outside the axiom "
            "domain => not AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
