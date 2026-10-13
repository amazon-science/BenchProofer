#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15161 (nagini).

SHADOW: the impl region of model.py's `deconstruct_path`, copied VERBATIM
below with only the contract calls (Requires/Ensures/Invariant/Assert)
stripped. The @Pure helpers used by the impl/spec (`DOT`, `public_root`,
`qualified`, `no_dot`, `serialized_module_rooted`) copy over as plain
functions with PSeq replaced by a plain tuple and Forall replaced by `all`.
There are NO @ContractOnly callees (the bundle consumes no axioms), so the
shadow is self-contained.

ORACLE (mapping.md section 1): the path-selecting behaviour of the
`deconstruct(obj)` method that `django.utils.deconstruct.deconstructible`
generates. We build a class through the REAL decorator — with a configured
canonical path when `configured` is non-empty, without one otherwise — and
observe the first element of `instance.deconstruct()`:
  * `exact == True`  -> the instance is of the exact decorated class;
  * `exact == False` -> the instance is of a subclass (so the exact-type
    condition inside the real method is False and the fallback fires; the
    model's `module`/`name` are then the subclass's own module and name,
    per the mapping's `type(obj) is klass` <-> `exact` bridge).
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the (unchanged, but patched-tree) module is imported
from the patched repo.

TYPE BRIDGE (mapping.md section 2): model carrier List[int] of Unicode code
points <-> repo str, elementwise xs[k] == ord(s[k]). Encode: a candidate
List[int] becomes "".join(chr(c)); decode: an oracle str becomes
[ord(ch) for ch in s]. Empty str <-> []. `if path` truthiness <->
len(configured) > 0.

INPUT DOMAIN: the model's one Requires is that `name` carries no '.'
(a single leaf component). The real method additionally resolves the chosen
module and asserts the name is present on it (a serializability guard, not
part of the modeled path choice), so — exactly as the G-AX harness does —
each case registers throwaway modules in sys.modules carrying the class, and
the generated inputs keep to that executability envelope: `module` is a
non-empty dotted string with non-empty components, `name` is a non-empty
dot-free string, and `configured` is either empty or a dotted string (the
real method splits a configured path on its last dot to find the module to
resolve, so a configured path always carries a dot, as every real configured
value does). Code points are drawn from ASCII letters/digits/underscore plus
a few non-ASCII letters to exercise the code-point bridge.

BOUNDARY CASES: the six expression-node (configured, module, name) triples
the patch introduces, each with exact True and False; the same module/name
pairs with no configured path; single-character and long components; a
configured path with a multi-dot module part; non-ASCII components.

Fuzz: >= 1e5 Requires-satisfying inputs total, pinned seed 151610 (recorded
here per the G-CONF contract). Exit 0 iff zero disagreements; on a
disagreement print the input and both outputs and exit 1. stdlib only.
"""
import json
import random
import sys
import types

REPO = "/testbed"
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from django.utils.deconstruct import deconstructible  # noqa: E402

SEED = 151610
N_TOTAL_MIN = 100_000


# --- pure helpers from model.py (decorators stripped, PSeq -> tuple) ---------

def DOT():
    # ord('.')
    return 46


def public_root():
    """The public package prefix INCLUDING its trailing dot:
    'django.db.models.' as code points."""
    return (100, 106, 97, 110, 103, 111, 46, 100, 98, 46,
            109, 111, 100, 101, 108, 115, 46)


def qualified(module, name):
    """The dotted qualified-name fallback: `module "." name`."""
    return tuple(module) + (DOT(),) + tuple(name)


def no_dot(s):
    """True iff `s` contains no '.' code point (a single path component)."""
    return all(s[k] != DOT() for k in range(len(s)))


def serialized_module_rooted(p):
    """True iff `p` begins with the public prefix and the remaining leaf
    carries no further dot."""
    return (len(p) > len(public_root()) and
            tuple(p[:len(public_root())]) == public_root() and
            no_dot(p[len(public_root()):]))


# --- impl region of model.py, verbatim (contracts stripped) ------------------

def deconstruct_path(configured, exact, module, name):
    result = []  # type: list
    if len(configured) > 0 and exact:
        i = 0
        while i < len(configured):
            result = result + [configured[i]]
            i = i + 1
        return result
    else:
        i = 0
        while i < len(module):
            result = result + [module[i]]
            i = i + 1
        result = result + [DOT()]
        j = 0
        while j < len(name):
            result = result + [name[j]]
            j = j + 1
        return result


# --- type bridge --------------------------------------------------------------

def to_cp(s):
    return [ord(ch) for ch in s]


def to_str(cp):
    return "".join(chr(c) for c in cp)


# --- the real callee ------------------------------------------------------------

def real_reported_path(configured, exact, module, name):
    """Build a class through the REAL decorator and return the import path the
    generated deconstruct() reports for an instance.

    configured == "" -> decorated without a canonical path; non-empty ->
    decorated with it. exact False -> the instance is of a subclass carrying
    the given module/name (so the observing instance's own class location is
    what the fallback reads)."""
    # Save/restore ledger: a registered module name may collide with a module
    # that genuinely exists (e.g. a configured path rooted at a real package),
    # so cleanup must restore the prior sys.modules entry and the prior
    # attribute value rather than evict the real module.
    undo = []

    def register(mod_name, attr, cls):
        existed = mod_name in sys.modules
        holder = sys.modules.get(mod_name)
        if holder is None:
            holder = types.ModuleType(mod_name)
        had_attr = hasattr(holder, attr)
        prior = getattr(holder, attr, None)
        setattr(holder, attr, cls)
        sys.modules[mod_name] = holder
        undo.append((mod_name, existed, holder, attr, had_attr, prior))

    if configured:
        @deconstructible(path=configured)
        class K:
            def __init__(self):
                self._constructor_args = ((), {})
    else:
        @deconstructible
        class K:
            def __init__(self):
                self._constructor_args = ((), {})

    try:
        if exact:
            K.__module__ = module
            K.__qualname__ = name
            K.__name__ = name
            register(module, name, K)
            if configured:
                # the configured path's own module/leaf must resolve too
                c_mod, _, c_leaf = configured.rpartition(".")
                register(c_mod, c_leaf, K)
            obj = K()
        else:
            # a subclass instance: the exact-type condition is False, so the
            # real method reads the instance's own class module/name.
            K.__module__ = module + "._base"
            K.__name__ = name + "Base"
            K.__qualname__ = name + "Base"
            S = type(name, (K,), {})
            S.__module__ = module
            S.__qualname__ = name
            register(module, name, S)
            obj = S()
        return obj.deconstruct()[0]
    finally:
        for mod_name, existed, holder, attr, had_attr, prior in reversed(undo):
            if had_attr:
                setattr(holder, attr, prior)
            else:
                try:
                    delattr(holder, attr)
                except AttributeError:
                    pass
            if not existed:
                sys.modules.pop(mod_name, None)


# --- differential ---------------------------------------------------------------

def check_case(configured, exact, module, name):
    """Diff the shadow against the real callee on one Requires-satisfying
    input (str form). Returns an error string on disagreement, else None."""
    shadow_cp = deconstruct_path(to_cp(configured), exact,
                                 to_cp(module), to_cp(name))
    shadow = to_str(shadow_cp)
    real = real_reported_path(configured, exact, module, name)
    if shadow != real:
        return ("DISAGREEMENT: configured=%r exact=%r module=%r name=%r -> "
                "shadow=%r real=%r" % (configured, exact, module, name,
                                       shadow, real))
    # cross-check the rooting predicate tracks the chosen branch, at the
    # code-point level, as the postcondition states (pure-helper sanity).
    want = (serialized_module_rooted(to_cp(configured))
            if (len(configured) > 0 and exact)
            else serialized_module_rooted(qualified(to_cp(module), to_cp(name))))
    got = serialized_module_rooted(shadow_cp)
    if got != want:
        return ("ROOTING MISMATCH: configured=%r exact=%r module=%r name=%r -> "
                "result-rooted=%r branch-rooted=%r"
                % (configured, exact, module, name, got, want))
    return None


ALPHA = ("abcdefghijklmnopqrstuvwxyz"
         "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
         "éüα漢")


def rand_component(rng, lo=1, hi=12):
    return "".join(rng.choice(ALPHA) for _ in range(rng.randint(lo, hi)))


def rand_module(rng):
    return ".".join(rand_component(rng) for _ in range(rng.randint(1, 5)))


def main():
    checked = 0
    failures = 0

    def run(configured, exact, module, name):
        nonlocal checked, failures
        err = check_case(configured, exact, module, name)
        checked += 1
        if err is not None:
            failures += 1
            print(err)

    # ---- boundary cases -----------------------------------------------------
    six = ["Func", "Value", "ExpressionWrapper", "When", "Case", "OrderBy"]
    for leaf in six:
        cfg = "django.db.models." + leaf
        mod = "django.db.models.expressions_shadowtest"
        for exact in (True, False):
            run(cfg, exact, mod, leaf)   # configured, both exactness values
            run("", exact, mod, leaf)    # no configured path
    extra = [
        ("a.b", True, "a", "b"),                       # minimal dotted config
        ("a.b", False, "a", "b"),
        ("", True, "m", "N"),                          # single-char components
        ("x.y.z.w.Leaf", True, "other.mod", "Leaf"),   # multi-dot module part
        ("x.y.z.w.Leaf", False, "other.mod", "Leaf"),
        ("p." + "L" * 100, True, "m" * 80, "n" * 80),  # long components
        ("café.mod.αLeaf", True, "café.mod", "αLeaf"),
        ("", False, "漢.字", "üName"),    # non-ASCII fallback
    ]
    for configured, exact, module, name in extra:
        run(configured, exact, module, name)

    # ---- fuzz (pinned seed) ---------------------------------------------------
    rng = random.Random(SEED)
    while checked < N_TOTAL_MIN:
        module = rand_module(rng)
        name = rand_component(rng)
        exact = rng.random() < 0.5
        r = rng.random()
        if r < 0.25:
            configured = ""
        elif r < 0.55:
            # a configured path rooted at the public package
            configured = "django.db.models." + rand_component(rng)
        else:
            # an arbitrary dotted configured path
            configured = rand_module(rng) + "." + rand_component(rng)
        run(configured, exact, module, name)

    print(json.dumps({"checked": checked, "failures": failures,
                      "seed": SEED}))
    if failures:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs"
              % (failures, checked))
        return 1
    print("G-CONF OK: shadow == real reported path on %d inputs "
          "(boundary + fuzz, seed %d)" % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
