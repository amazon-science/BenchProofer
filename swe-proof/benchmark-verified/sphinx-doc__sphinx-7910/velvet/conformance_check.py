#!/usr/bin/env python3
"""G-CONF differential conformance for sphinx-doc__sphinx-7910 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `inclusionDecisionM` (the
member-inclusion branch decision modeled in Solution.lean). There are NO axioms
in this bundle: every op is a concrete structural decision over the recorded
fields of one documentable target, so the whole impl region is R/I-tagged
(conf_skip=false).

ORACLE CHOICE — why we transliterate the patched control flow instead of running
the real `_skip_member`:
  Driving the real `sphinx.ext.napoleon._skip_member` to the modeled ownership
  branch needs a configured Sphinx application object, real class/module objects
  with populated `__globals__`/`__qualname__`/`__dict__`, and (for the fixed
  case) a decorated method whose `__wrapped__` chain must be followed — i.e. the
  F2P test harness. Building that purely to read back the include-vs-default
  verdict would not isolate the modeled behavior. Per the worker prompt the
  ORACLE is the PATCHED ownership-decision control flow transliterated VERBATIM
  (sphinx/ext/napoleon/__init__.py:421-462, post-patch):

      has_doc = getattr(obj, '__doc__', False)
      is_member = (what == 'class' or what == 'exception' or what == 'module')
      if name != '__weakref__' and has_doc and is_member:
          cls_is_owner = False
          if what == 'class' or what == 'exception':
              qualname = getattr(obj, '__qualname__', '')
              cls_path, _, _ = qualname.rpartition('.')
              if cls_path:
                  try:
                      if '.' in cls_path:
                          mod = importlib.import_module(obj.__module__)
                          cls = functools.reduce(getattr, cls_path.split('.'), mod)
                      else:
                          cls = inspect.unwrap(obj).__globals__[cls_path]   # <- the fix
                  except Exception:
                      cls_is_owner = False
                  else:
                      cls_is_owner = (cls and hasattr(cls, name) and name in cls.__dict__)
              else:
                  cls_is_owner = False
          if what == 'module' or cls_is_owner:
              is_init = (name == '__init__')
              is_special = (not is_init and name.startswith('__') and name.endswith('__'))
              is_private = (not is_init and not is_special and name.startswith('_'))
              if ((is_special and inc_special) or (is_private and inc_private) or
                      (is_init and inc_init)):
                  return False
      return None

  The unchanged per-object machinery (`getattr`, `importlib.import_module`,
  `functools.reduce`, `inspect.unwrap`, `hasattr`, `__dict__` membership) is
  folded out: each target is reduced to the recorded fields the branch actually
  inspects — `has_doc`; the qualified name (`cls_path`); for a multi-segment path
  whether the attribute-chain walk yields an owner (`owner_via_path_walk`); and,
  for a single-segment path, whether the container name is owned when looked up in
  the DIRECT scope vs the RESOLVED (unwrapped) scope. The post-patch oracle reads
  ownership from the RESOLVED scope (`inspect.unwrap(obj).__globals__`); the
  modeled impl does the same (`resolvedScope`). mapping.md §2/§3.

  The SHADOW is the model from Solution.lean (`inclusionDecision` and its helpers
  `containerPath`/`isMultiSegment`/`scopeOwns`/`ownerIn`/`categoryEnabled`)
  transliterated to Python. SHADOW and ORACLE are differential-tested over
  randomly-generated targets and exhaustive small cases. Exit 0 iff zero
  disagreements. stdlib only.
"""
import random
import sys

SEED = 7910
N_FUZZ = 100_000

WEAKREF = list("__weakref__")
INIT = list("__init__")

# names drawn from the F2P/PASS_TO_PASS leaf-name space + boundaries
NAMES = [
    "__init__", "__decorated_func__", "__special_doc__", "__special_undoc__",
    "_private_doc", "_private_undoc", "__weakref__", "public", "__", "_",
    "_x", "__x__", "x__", "__x",
]
CONTEXTS = ["classBody", "exceptionBody", "wholeUnit", "freestanding"]
# qualified-name shapes: empty path, single-segment path, multi-segment path
QUALNAMES = ["leaf", "A.leaf", "pkg.A.leaf", "a.b.c.leaf", ".leaf"]


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def container_path(s):
    """`containerPath`: everything before the last '.', else empty."""
    idx = s.rfind('.')
    return s[:idx] if idx >= 0 else ""


def is_multi_segment(s):
    """`isMultiSegment`: the container path itself contains a '.'."""
    return '.' in s


def scope_owns(scope, key):
    """`scopeOwns`: lookup key in the scope (list of (name, owns)); False if
    absent."""
    for k, owns in scope:
        if k == key:
            return owns
    return False


def owner_in(t, scope):
    """`ownerIn`: ownership for a bodied context against a chosen scope."""
    cp = container_path(t["qualified_name"])
    if cp == "":
        return False
    if is_multi_segment(cp):
        return t["owner_via_path_walk"]
    return scope_owns(scope, cp)


def is_considered(ctx):
    return ctx in ("classBody", "exceptionBody", "wholeUnit")


def is_init(name):
    return name == "__init__"


def is_special(name):
    return (not is_init(name) and name.startswith("__") and name.endswith("__"))


def is_private(name):
    return (not is_init(name) and not is_special(name) and name.startswith("_"))


def category_enabled(name, inc_init, inc_special, inc_private):
    return ((is_special(name) and inc_special) or
            (is_private(name) and inc_private) or
            (is_init(name) and inc_init))


def inclusion_decision(ctx, name, t, inc_init, inc_special, inc_private):
    """`inclusionDecision` (Solution.lean): the modeled verdict."""
    if name != "__weakref__" and t["has_doc"] and is_considered(ctx):
        if ctx in ("classBody", "exceptionBody"):
            owner = owner_in(t, t["resolved_scope"])
        else:
            owner = False
        if ctx == "wholeUnit" or owner:
            if category_enabled(name, inc_init, inc_special, inc_private):
                return "forceInclude"
            return "noOverride"
        return "noOverride"
    return "noOverride"


# ---- ORACLE: patched _skip_member ownership flow transliterated -----------

def oracle_decision(ctx, name, t, inc_init, inc_special, inc_private):
    """Patched __init__.py:421-462 transliterated. `_skip_member` returns False
    to force inclusion and None otherwise; we tag False -> 'forceInclude',
    None -> 'noOverride'. Each target is reduced to the recorded fields the
    branch inspects; the ownership lookup reads the RESOLVED (unwrapped) scope,
    which is the single behavior the patch changes (mapping.md §2)."""
    what_is_member = ctx in ("classBody", "exceptionBody", "wholeUnit")
    if name != "__weakref__" and t["has_doc"] and what_is_member:
        cls_is_owner = False
        if ctx in ("classBody", "exceptionBody"):
            cls_path = container_path(t["qualified_name"])
            if cls_path:
                if '.' in cls_path:
                    cls_is_owner = t["owner_via_path_walk"]
                else:
                    # cls = inspect.unwrap(obj).__globals__[cls_path]  (the fix)
                    # KeyError -> except -> cls_is_owner=False, folded into the
                    # resolved-scope membership boolean.
                    cls_is_owner = scope_owns(t["resolved_scope"], cls_path)
            else:
                cls_is_owner = False
        if ctx == "wholeUnit" or cls_is_owner:
            o_init = (name == "__init__")
            o_special = (not o_init and name.startswith("__")
                         and name.endswith("__"))
            o_private = (not o_init and not o_special and name.startswith("_"))
            if ((o_special and inc_special) or (o_private and inc_private) or
                    (o_init and inc_init)):
                return "forceInclude"
        return "noOverride"
    return "noOverride"


# ---- target generator -----------------------------------------------------

def gen_scope(rng, key):
    """A scope (list of (name, owns)); sometimes contains `key`."""
    scope = []
    if rng.random() < 0.6 and key:
        scope.append((key, rng.random() < 0.7))
    # noise entries
    for _ in range(rng.randint(0, 3)):
        scope.append(("noise%d" % rng.randint(0, 9), rng.random() < 0.5))
    rng.shuffle(scope)
    return scope


def gen_target(rng):
    qn = rng.choice(QUALNAMES)
    cp = container_path(qn)
    return {
        "has_doc": rng.random() < 0.7,
        "qualified_name": qn,
        "owner_via_path_walk": rng.random() < 0.5,
        # direct and resolved scopes generated independently: a wrapped target
        # has a direct scope that may NOT contain the owner while the resolved
        # one does — the discriminating case the patch fixes. (Unused by the
        # shadow/oracle here since both read resolved_scope, but kept so the
        # record matches the Lean carrier exactly.)
        "direct_scope": gen_scope(rng, cp),
        "resolved_scope": gen_scope(rng, cp),
    }


def enumerate_small():
    """Boundary cases: every (context, name, has_doc, owner-bits) combination
    over the F2P/PASS_TO_PASS name space and the three qualified-name shapes."""
    out = []
    for ctx in CONTEXTS:
        for name in NAMES:
            for qn in QUALNAMES:
                cp = container_path(qn)
                for has_doc in (True, False):
                    for owns in (True, False):
                        for walk in (True, False):
                            for ii in (True, False):
                                for isp in (True, False):
                                    for ipr in (True, False):
                                        scope = [(cp, owns)] if cp else []
                                        t = {
                                            "has_doc": has_doc,
                                            "qualified_name": qn,
                                            "owner_via_path_walk": walk,
                                            "direct_scope": scope,
                                            "resolved_scope": scope,
                                        }
                                        out.append((ctx, name, t, ii, isp, ipr))
    return out


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for (ctx, name, t, ii, isp, ipr) in enumerate_small():
        count += 1
        sh = inclusion_decision(ctx, name, t, ii, isp, ipr)
        orc = oracle_decision(ctx, name, t, ii, isp, ipr)
        if sh != orc:
            disagreements.append((ctx, name, t, sh, orc))

    for _ in range(N_FUZZ):
        ctx = rng.choice(CONTEXTS)
        name = rng.choice(NAMES)
        t = gen_target(rng)
        ii, isp, ipr = (rng.random() < 0.5, rng.random() < 0.5, rng.random() < 0.5)
        count += 1
        sh = inclusion_decision(ctx, name, t, ii, isp, ipr)
        orc = oracle_decision(ctx, name, t, ii, isp, ipr)
        if sh != orc:
            disagreements.append((ctx, name, t, sh, orc))
        if len(disagreements) >= 8:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d cases:"
              % (len(disagreements), count))
        for ctx, name, t, sh, orc in disagreements[:8]:
            print("  ctx=%s name=%r t=%r shadow=%r oracle=%r"
                  % (ctx, name, t, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of inclusionDecisionM (inclusionDecision + "
          "helpers) agrees with the patched _skip_member ownership flow on "
          "%d cases (exhaustive + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
