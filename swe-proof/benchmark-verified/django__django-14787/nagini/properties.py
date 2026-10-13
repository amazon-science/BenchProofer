# properties.py — PBT falsification battery for django__django-14787.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py variant that shares the frozen spec exactly
# (same_spec) and swaps ONLY the executable text inside # impl-start/# impl-end;
# the runner checks it with Nagini verify. Each AXIOM_TESTS case is a
# self-contained probe run in the instance Docker image against the REAL callee.
#
# Defended surface (read from model.py / refinement.md / instance.json):
#   assemble_bound_callable(method: FuncIdentity) -> FuncIdentity
#   * method is READ-ONLY: Requires(Acc(method.has_name,1/2) and Acc(method.name,1/2))
#     and likewise for has_module/module — fractional permission. The frame-
#     mutation attack (write to method to satisfy the post vacuously) MUST be
#     rejected for insufficient permission. (#1 weakness class — MANDATORY.)
#   * Load-bearing post: Result().has_name, Result().has_module (presence — the
#     prepatch fails on has_name); Result().name == method.name,
#     Result().module == method.module (value equality, GROUNDED in the input
#     argument — there is no opaque @Pure oracle to echo, so the ungrounded-echo
#     class is N/A; a grounded cheapest-impl positive control is used instead).
#   * Read-only invariant: method.name == Old(method.name) (and module) — the
#     method is unchanged; Acc(Result().*) — the result is a fresh fully-owned obj.
#   The F2P test "@method_decorator preserves wrapper assignments" applies a user
#   decorator whose inner reads getattr(func,'__name__',None) and asserts it ==
#   'method' and that __module__ is not None; pre-patch the bare partial has no
#   __name__ so func_name is None != 'method'. The discriminating clause is the
#   NAME presence+equality (Result().has_name, Result().name == method.name).

from pathlib import Path

INSTANCE = "django__django-14787"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()

# The full executable block inside the impl region of the frozen model (the gold
# assembly). Every rival is built by _swap-ing ONLY this block, so the spec view
# (axioms/pure/pre/post + signatures) is byte-identical => same_spec holds.
_GOLD_IMPL = (
    "    has_name = method.has_name\n"
    "    name = method.name\n"
    "    has_module = method.has_module\n"
    "    module = method.module\n"
    "    bound = FuncIdentity(has_name, name, has_module, module)\n"
    "    return bound"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# Sanity: the gold impl block must appear exactly once in the frozen model.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block drifted; update _GOLD_IMPL"


# --------------------------------------------------------------------------- #
# SPEC LANE                                                                    #
# --------------------------------------------------------------------------- #

# (1) POSITIVE CONTROL — structurally-different CORRECT impl. Reorder which
#     facet is read first and inline the constructor call directly from the
#     method's attributes (no intermediate locals). Behaviourally identical to
#     gold: copies all four facets from the read-only method. MUST verify (else
#     SPEC-TOO-STRONG). Keeps every gold proof obligation: each result facet is
#     the method's own attribute, so Result().name == method.name etc. discharge
#     directly; the method is only read, so the read-only invariant holds.
_POS_REORDER = (
    "    # structurally-different but CORRECT: module facet read first, name\n"
    "    # second, constructed inline from the method's own attributes.\n"
    "    md_has = method.has_module\n"
    "    md_val = method.module\n"
    "    nm_has = method.has_name\n"
    "    nm_val = method.name\n"
    "    return FuncIdentity(nm_has, nm_val, md_has, md_val)"
)

# (2) POSITIVE CONTROL — cheapest honest impl (grounded-oracle positive control).
#     The postcondition value pins (Result().name == method.name,
#     Result().module == method.module) are GROUNDED in the input argument, so
#     there is no opaque answer-key to echo. The cheapest impl that does the real
#     work is a single inline construction from method's attributes; it must
#     verify. (Stands in for the ungrounded-echo case, which is N/A here.)
_POS_CHEAPEST = (
    "    return FuncIdentity(method.has_name, method.name,\n"
    "                        method.has_module, method.module)"
)

# (3) ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input
#     and that the gold assembly delivers the F2P observations for it. We keep
#     the gold assembly and add in-impl Assert()s pinning exactly the facts the
#     F2P test reads (name present & == method's; module present & not-None,
#     modelled as == method's). If the precondition were too strong for a normal
#     method these would be unreachable/unprovable. MUST verify (else
#     PRECOND-TOO-STRONG). Asserts are over the just-built result, no new spec.
_ADMISS = (
    "    has_name = method.has_name\n"
    "    name = method.name\n"
    "    has_module = method.has_module\n"
    "    module = method.module\n"
    "    bound = FuncIdentity(has_name, name, has_module, module)\n"
    "    # A normal (F2P-shaped) method has both attributes present (precond),\n"
    "    # so the assembled callable carries them with the method's values --\n"
    "    # exactly the F2P observations getattr(func,'__name__')=='method' and\n"
    "    # getattr(func,'__module__') is not None.\n"
    "    Assert(bound.has_name and bound.name == method.name)\n"
    "    Assert(bound.has_module and bound.module == method.module)\n"
    "    return bound"
)

# (4) FRAME-MUTATION (MANDATORY) — a rival that WRITES to the read-only method to
#     satisfy a postcondition vacuously. It tries to assign method.name (and
#     method.module) and then build the result from them. The method is held with
#     only Acc(method.name, 1/2): a write needs FULL permission, so this MUST be
#     REJECTED for INSUFFICIENT PERMISSION (the write, not a value mismatch). The
#     gold post (incl. the read-only invariant method.name == Old(method.name))
#     is kept verbatim so the rejection is attributable to the illegal write.
#     refinement: its faithful real patch would MUTATE the original method object
#     (e.g. method.__name__ = ...), corrupting the very method the decorator
#     chain re-binds and that other instances/decorations reuse — update_wrapper
#     copies ONTO the wrapper and leaves the wrapped method untouched, so a patch
#     that writes the method is not functools.wraps and would change observable
#     method identity elsewhere; it does not faithfully resolve the F2P (which
#     asserts the assembled callable, not the method, carries the name).
_FRAME_MUT = (
    "    # ILLEGAL: write to the read-only method (only Acc(method.*,1/2) held).\n"
    "    method.name = method.name\n"
    "    method.module = method.module\n"
    "    bound = FuncIdentity(method.has_name, method.name,\n"
    "                         method.has_module, method.module)\n"
    "    return bound"
)

# (5) PARTIAL-DOMAIN (value) — a rival correct on a sub-domain only. It copies
#     the method's MODULE token into the result's NAME facet (and keeps the rest
#     gold). It is correct exactly when method.name == method.module (the
#     coincidental sub-domain) and WRONG otherwise. The postcondition
#     Result().name == method.name pins it to the method's NAME, so it MUST be
#     REJECTED. A byte-fuzzer never picks 'use the sibling facet'.
#     refinement: its faithful real patch would set the assembled callable's
#     __name__ to method.__module__ (e.g. 'tests') instead of method.__name__
#     ('method'); the F2P asserts func_name == 'method', so it would FAIL the
#     F2P on the actual fixture (name 'method' != module 'tests'). Verifying =>
#     SPEC-TOO-WEAK (admits a callable carrying the wrong name).
_PARTIAL_VALUE = (
    "    has_name = method.has_name\n"
    "    name = method.module\n"  # WRONG: module token used as the name value
    "    has_module = method.has_module\n"
    "    module = method.module\n"
    "    bound = FuncIdentity(has_name, name, has_module, module)\n"
    "    return bound"
)

# (6) PARTIAL-DOMAIN (presence) — a rival that DROPS the name copy: the assembled
#     callable is left with has_name=False (the pre-patch behaviour) while the
#     module copy is kept. This is exactly what model_prepatch.py does. The
#     postcondition Result().has_name pins presence, so it MUST be REJECTED.
#     refinement: this IS the pre-patch assembly (bare partial, no __name__) —
#     G-DIFF/model_prepatch confirms it fails Ensures(Result().has_name) and the
#     F2P test fails because getattr(func,'__name__',None) is None != 'method'.
#     A verifying variant here would be SPEC-TOO-WEAK (admits the unresolved
#     pre-patch behaviour).
_PARTIAL_PRESENCE = (
    "    # Drop the name copy (pre-patch behaviour): name absent on the result.\n"
    "    has_module = method.has_module\n"
    "    module = method.module\n"
    "    bound = FuncIdentity(False, 0, has_module, module)\n"
    "    return bound"
)


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_REORDER),
        "rationale": "structurally-different but correct impl (facets read in a "
        "different order, inline construct) must verify; else SPEC-TOO-STRONG. "
        "Each result facet is still the method's own attribute, so the value "
        "pins discharge directly and the read-only invariant holds.",
    },
    {
        "id": "pos-control-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_CHEAPEST),
        "rationale": "the post value pins (Result().name==method.name, "
        "Result().module==method.module) are grounded in the input arg, so the "
        "cheapest honest impl (single inline construction from method's "
        "attributes) is correct and must verify. No opaque oracle to echo, so "
        "ungrounded-echo is N/A; this is the grounded positive control.",
    },
    {
        "id": "admissibility",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "the precondition (method.has_name and method.has_module) "
        "admits a normal method; in-impl Assert()s pin the exact F2P "
        "observations on the assembled callable and verify; else PRECOND-TOO-"
        "STRONG. Asserts are over the just-built result and add no spec.",
    },
    {
        "id": "frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUT),
        "refinement": "a faithful real patch behind this would WRITE the wrapped "
        "method (e.g. method.__name__ = ...) rather than copy onto the wrapper; "
        "functools.update_wrapper copies ONTO the wrapper and leaves the method "
        "untouched, so this is not the gold wrap. It would corrupt the original "
        "method's identity (reused across instances/decorations) and does not "
        "make the ASSEMBLED callable carry the name, so it would not faithfully "
        "resolve the F2P (which inspects the assembled callable, not the method).",
        "rationale": "the method is held with Acc(method.*,1/2) (read-only); the "
        "write `method.name = ...` needs full permission and must be REJECTED "
        "for INSUFFICIENT PERMISSION. Rejection comes from the permission "
        "system (the fractional-permission Requires), not a value mismatch. "
        "Gold post incl. the read-only invariant kept verbatim.",
    },
    {
        "id": "partial-domain-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_VALUE),
        "refinement": "the faithful patch sets the assembled callable's __name__ "
        "to method.__module__ ('tests') instead of method.__name__ ('method'); "
        "the F2P asserts func_name == 'method', so it FAILS on the actual "
        "fixture (name != module). It only happens to be right where a method's "
        "name token equals its module token. Verifying => SPEC-TOO-WEAK.",
        "rationale": "rejection comes from the postcondition clause "
        "Result().name == method.name — the rival pins the result name to "
        "method.module, which is not provably == method.name in general.",
    },
    {
        "id": "partial-domain-presence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_PRESENCE),
        "refinement": "this IS the pre-patch assembly (the bare partial with no "
        "__name__ copied); model_prepatch.py is exactly this and G-DIFF "
        "confirms it fails Ensures(Result().has_name). The F2P fails because "
        "getattr(func,'__name__',None) is None != 'method'. Verifying => SPEC-"
        "TOO-WEAK (admits the unresolved pre-patch behaviour).",
        "rationale": "rejection comes from the postcondition clause "
        "Result().has_name (and Result().name == method.name) — presence of the "
        "name on the result, which a False/0 name facet cannot satisfy.",
    },
]


# --------------------------------------------------------------------------- #
# AXIOM LANE                                                                   #
# --------------------------------------------------------------------------- #
# No consumed @ContractOnly axiom (meta.axioms == []). The only kind-A construct
# is the A-reference DEEP MODEL of the unchanged stdlib primitive
# functools.update_wrapper / functools.wraps (the call the gold patch
# introduces). G-AX already validates the deep model == the real callee
# out-of-band (axiom_check.py). Below, the axiom lane re-runs the REAL callee in
# the instance Docker image (where functools lives) to (a) AXIOM-SOUNDNESS: the
# wrapped partial carries the method's __name__/__module__ and the method is
# unmodified — the exact Ensures the deep model encodes; (b) AXIOM-CONTAINMENT:
# every method the MODEL can reach (precondition: __name__ and __module__ both
# PRESENT) lies in the callee's effective domain (update_wrapper copies present
# WRAPPER_ASSIGNMENTS attributes verbatim). Imports stdlib only; encoding="utf-8"
# is irrelevant (no file reads) but the probes are ASCII-clean regardless.

_AX_SOUND_PROBE = r'''
import sys, random
from functools import partial, wraps, update_wrapper
import functools

def check(method):
    assert hasattr(method, "__name__") and hasattr(method, "__module__")
    m_name, m_module = method.__name__, method.__module__
    # Pre-patch fact: a bare partial has no __name__ of its own.
    bare = partial(method)
    if getattr(bare, "__name__", None) is not None:
        print("FAIL: bare partial unexpectedly has __name__=%r" %
              (getattr(bare, "__name__", None),))
        sys.exit(1)
    # The patched assembly == the deep model: copy __name__/__module__ ONTO it.
    bound = wraps(method)(partial(method))
    if getattr(bound, "__name__", None) != m_name:
        print("FAIL: __name__ not copied: method=%r bound=%r" %
              (m_name, getattr(bound, "__name__", None)))
        sys.exit(1)
    if getattr(bound, "__module__", None) != m_module:
        print("FAIL: __module__ not copied: method=%r bound=%r" %
              (m_module, getattr(bound, "__module__", None)))
        sys.exit(1)
    if not (hasattr(bound, "__name__") and hasattr(bound, "__module__")):
        print("FAIL: assembled callable missing presence flags")
        sys.exit(1)
    # The method is read-only: update_wrapper must NOT mutate the wrapped fn.
    if method.__name__ != m_name or method.__module__ != m_module:
        print("FAIL: update_wrapper mutated the method")
        sys.exit(1)
    # update_wrapper returns the same (updated) object that flows onward.
    again = update_wrapper(partial(method), method)
    if getattr(again, "__name__", None) != m_name or getattr(again, "__module__", None) != m_module:
        print("FAIL: update_wrapper return-value identity copy failed")
        sys.exit(1)

# Boundary fixtures: realistic shapes of the wrapped "method".
def method(self): return "tests"
class Host:
    def bound_method(self): return "tests"
fixtures = [method, Host.bound_method, Host().bound_method.__func__, (lambda self: None)]
def helper(self): return None
helper.__name__ = "weird name with spaces"; helper.__module__ = "some.dotted.module"
fixtures.append(helper)
def helper2(self): return None
helper2.__name__ = ""  # empty name still present
fixtures.append(helper2)
for m in fixtures:
    check(m)

# Randomized fuzz over name/module tokens (boundaries + sentinels).
rng = random.Random(14787)
alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._ "
for _ in range(20000):
    def fz(self): return None
    fz.__name__ = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 30)))
    fz.__module__ = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 20)))
    check(fz)

if "__name__" not in functools.WRAPPER_ASSIGNMENTS or "__module__" not in functools.WRAPPER_ASSIGNMENTS:
    print("FAIL: WRAPPER_ASSIGNMENTS missing __name__/__module__: %r" %
          (functools.WRAPPER_ASSIGNMENTS,))
    sys.exit(1)

print("AXIOM-SOUNDNESS OK: real functools.wraps/update_wrapper copies the "
      "method's __name__/__module__ onto the wrapped partial, leaves the method "
      "unmodified, and a bare partial has no __name__ -- over 6 boundary + 20000 "
      "fuzz methods. Matches the model's Ensures (Result().name==method.name, "
      "Result().module==method.module, method unchanged).")
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import sys
from functools import partial, wraps
import functools

# CONTAINMENT: the MODEL reaches the callee only with a "method" whose __name__
# AND __module__ are both PRESENT (model precondition: method.has_name and
# method.has_module). The callee's effective domain for the two modelled
# WRAPPER_ASSIGNMENTS attributes is exactly "the attribute is present on the
# wrapped object" (update_wrapper getattr/except-AttributeError/setattr). So we
# assert: for every caller-reachable shape (both attributes present), the real
# wraps copies BOTH verbatim -- i.e. the reachable inputs all lie in the domain
# where the deep model's Ensures (present + value-equal) holds. (Covering MORE
# -- e.g. partials with a missing attribute -- would be SOUND, not a defect; the
# caller never reaches those because the precondition pins both present.)

def reachable_method(name, module):
    def f(self): return None
    f.__name__ = name
    f.__module__ = module
    return f

# Enumerate the caller-reachable shapes the model's Requires admits: both
# attributes present, value tokens arbitrary (incl. boundary tokens).
cases = [
    ("method", "tests"),     # the actual F2P fixture
    ("", ""),                # empty tokens (still present)
    ("a.b.c", "x.y"),        # dotted
    ("weird name", "mod 1"), # spaces
]
for name, module in cases:
    m = reachable_method(name, module)
    # Both present => in the callee's copy domain.
    if not (hasattr(m, "__name__") and hasattr(m, "__module__")):
        print("FAIL: reachable method missing a modelled attribute (should be present)")
        sys.exit(1)
    bound = wraps(m)(partial(m))
    if getattr(bound, "__name__", None) != name or getattr(bound, "__module__", None) != module:
        print("FAIL: reachable input %r not covered by the callee copy domain" % ((name, module),))
        sys.exit(1)

# The model never reaches a method with a MISSING __name__/__module__ (precond),
# so we do NOT require the callee to define behaviour there. (Documenting the
# containment direction: a present attribute is always in-domain for the copy.)
print("AXIOM-CONTAINMENT OK: every caller-reachable method (both __name__ and "
      "__module__ present, per the model precondition) lies in the callee's "
      "copy domain; the real wraps copies both verbatim. No caller-reachable "
      "input falls outside functools.update_wrapper's effective domain.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-update-wrapper",
        "axiom": "wrapper-identity copy (functools.update_wrapper / wraps, A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the deep model in the impl region (copy __name__/__module__ "
        "onto the assembled callable, method unchanged) must == the real "
        "functools.wraps/update_wrapper. If the real callee disagrees on any "
        "fuzzed/boundary method => AXIOM-UNSOUND. Mirrors axiom_check.py / G-AX.",
    },
    {
        "id": "ax-contain-update-wrapper",
        "axiom": "wrapper-identity copy (functools.update_wrapper / wraps, A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "every method the MODEL can pass to the callee has both "
        "__name__ and __module__ present (precondition method.has_name and "
        "method.has_module); each lies in update_wrapper's copy domain (a "
        "present WRAPPER_ASSIGNMENTS attribute is copied verbatim). A reachable "
        "input outside that domain would be AXIOM-TOO-WEAK-FOR-CALLER; none "
        "exist here.",
    },
]
