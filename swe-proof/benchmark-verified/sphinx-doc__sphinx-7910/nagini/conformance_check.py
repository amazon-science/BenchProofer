#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7910 (nagini).

Runs INSIDE the instance image with the gold patch already applied by the gate
(apply_gold=True, PYTHONPATH=/testbed), so `sphinx.ext.napoleon` imports the
PATCHED module. Refutes (never proves) the R/I refinement leg: does the impl
region of model.py agree with the real patched repo function it claims to model?

SHADOW (provenance "direct").
  `MemberObj` and the `# impl-start`/`# impl-end` region of model.py, copied
  VERBATIM below with only the contract calls deleted (`Requires`, `Ensures`,
  `Assert`). Nothing is restructured, renamed or simplified — including the
  local `member = obj.is_class_member`, which the impl binds and then uses only
  inside the two stripped `Assert`s, and which is therefore dead in the shadow
  exactly as it is dead at runtime in the model. No `PSeq`/`ToSeq` shim is
  needed (this model carries no sequences), and the `# pure-start` region is
  empty ("No pure helpers required"), so there is no pure helper to copy.

  `canonical` is the bundle's one `@ContractOnly` callee, so it has no body to
  copy. Per the contract it is NOT re-implemented here: the shadow's
  `canonical()` calls the REAL repo callee it axiomatizes — mapping.md §1/§3.1
  binds it to `sphinx.util.inspect.unwrap` (sphinx/util/inspect.py:121), which
  is imported from the patched /testbed tree and applied to the REAL member
  object behind the abstract `MemberObj`, and the result is re-abstracted
  through the same bridge. So the axiom is exercised on real objects rather
  than assumed. The axiom's own obligations (identity preservation across the
  unwrap; the ownership clause) are additionally asserted on every input; a
  violation is reported as a failure, not swallowed.

ORACLE (called, NOT transliterated).
  The REAL patched `sphinx.ext.napoleon._skip_member(app, what, name, obj,
  skip, options)` — sphinx/ext/napoleon/__init__.py:381, changed body line 441
  (`cls = obj.__globals__[cls_path]` -> `cls = inspect.unwrap(obj).__globals__
  [cls_path]`), mapping.md §1. Driving it needs no Sphinx application: the
  modeled branch reads only `app.config.napoleon_include_{init,special,
  private}_with_doc` and never touches `options` or `skip`, so a two-attribute
  config stub plus a real function object is enough. (The velvet/lean sibling
  docstrings researched this oracle; velvet transliterated the control flow,
  lean called the real function. Calling it is strictly stronger, so this
  check calls it — the returned value is compared identity-sensitively, `False`
  vs `None` vs anything else.)

TYPE BRIDGE (mapping.md §2, inverted).
  Inputs are generated as REAL member objects (a function with a controlled
  `__qualname__`/`__doc__`, defined in a controlled module-globals dict,
  optionally wrapped by `functools.wraps` decorators whose own globals live in
  a DIFFERENT dict) and abstracted to the model carrier:
    `has_doc`        <- bool(getattr(obj, '__doc__', False))
    `cls_name`       <- interned int token of `obj.__qualname__.rpartition('.')`
    `ns`             <- {token(k): bool(v and hasattr(v, name) and
                         name in v.__dict__) for k, v in obj.__globals__}
                        (absent key == the repo's KeyError -> cls_is_owner False)
    `is_class_member`<- the same expression evaluated on the CANONICAL
                        (unwrapped) object's globals, i.e. mapping.md §1's
                        "ground truth ... for the canonical (unwrapped) object"
  and the `is_special`/`is_init`/`is_private` flags are derived from the member
  name by the repository's own classification (`is_init = name == '__init__'`,
  etc., mapping.md §2 row 6), which is what makes the model's mutual-exclusion
  precondition hold by construction. Result bridge: model `False` <-> real
  `False` (include), model `None` <-> real `None` (abstain).
  A generated globals binding for which the repo's ownership expression would
  RAISE (e.g. `cls_path` bound to an `int`, where `name in cls.__dict__` throws
  outside the repo's try/except) has no `Dict[int, bool]` preimage under this
  bridge; the generators never build one, and if one ever appeared the harness
  reports it loudly (`bridge-undefined`) instead of silently dropping the input.

INPUT DOMAIN (the model's Requires + mapping.md §2's declared scope).
  The permission conjuncts are vacuous at runtime; the only real Requires is
  the mutual exclusion of is_init/is_special/is_private, satisfied by the
  bridge above. mapping.md §2 additionally declares the modeled scope: a
  documented-or-not class/exception member with a SINGLE-COMPONENT class path.
  The impl region has no `name != '__weakref__'` guard, no `what` test and no
  dotted-`cls_path` branch, so generation is confined to
  `what in {'class', 'exception'}`, `name != '__weakref__'`, and
  `__qualname__ == '<Cls>.<member>'` with a dotless `<Cls>`. These are the
  scope restrictions the mapping already declares (and G-PANEL-2 records), not
  a domain weakened to route around a disagreement; everything inside that
  scope is generated, including undocumented members, unresolvable classes and
  inherited-not-owned members.

BRANCH + PATCH COVERAGE (the check is built to be capable of failing).
  Boundary enumeration takes every impl branch at least once: `not doc` ->
  None; `cls_name not in canon.ns` (class never bound in the defining module's
  globals -> the repo's KeyError path); `canon.ns[cls_name] is False`
  (inherited-only member, member absent from the class, a falsy class via a
  `__len__` metaclass exercising the repo's `cls and` conjunct, and a non-class
  binding); `cls_is_owner` true with the category disabled -> None; and
  `cls_is_owner` true with the category enabled -> False. Decoration depth 0/1/2
  crosses all of them. The run also COUNTS the discriminating inputs — those on
  which resolving ownership through the member object's OWN namespace
  (`obj.ns`, the pre-patch source) would disagree with the patched result — and
  FAILS if that count is zero, so a generator that drifted away from the branch
  the gold patch changed cannot report a green vacuous pass.

INPUTS / SEED: 28224-case exhaustive boundary catalogue (every combination of
  2 class names x 14 member names x 3 doc values x 3 decoration depths x 7
  ownership shapes x 2 `what` values x 8 config settings) followed by seeded
  fuzz over the same space with randomly generated member/class names, to
  >= 1e5 total comparisons. Pinned seed 79100 (recorded in mapping.md §G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit code is 1. stdlib only (functools, random, json, sys).
"""
import functools
import json
import random
import sys

SEED = 79100
N_MIN_TOTAL = 100_000

# member names: the F2P/P2P leaf names + category boundaries. '__weakref__' is
# excluded by the declared modeled scope (the impl has no weakref guard).
NAMES = [
    "__init__",            # is_init
    "__decorated_func__",  # the F2P shape
    "__special_doc__", "__special_undoc__", "__dunder__", "__x__", "__",
    "_private_doc", "_private_undoc", "_x", "_",
    "public", "x__", "",
    # intrinsics: names every class body carries in its own __dict__, so the
    # repo's `name in cls.__dict__` is True even on an empty class
    "__doc__", "__module__",
]
CLSNAMES = ["SampleClass", "SampleError"]
DOCS = ["doc", None, ""]
DECORATIONS = [0, 1, 2]
SHAPES = ["owned", "inherited", "absent", "unbound", "nonclass", "falsy",
          "shadowed"]
WHATS = ["class", "exception"]
CFGS = [(i, s, p) for i in (False, True) for s in (False, True)
        for p in (False, True)]


# --------------------------------------------------------------------------
# SHADOW: model.py, contracts stripped, copied verbatim.
# --------------------------------------------------------------------------

class MemberObj:
    """Minimal view of the member object handed to the hook. ``ns`` maps a
    class-name token to whether the class resolved there owns this member."""

    def __init__(self, has_doc, is_class_member, cls_name, ns):
        self.has_doc = has_doc
        self.is_class_member = is_class_member
        self.cls_name = cls_name
        self.ns = ns


# `canonical` is @ContractOnly in model.py (no body to copy): it axiomatizes
# the real repo callee `sphinx.util.inspect.unwrap`. The shadow CALLS that real
# callee on the real member object behind `obj` and re-abstracts the result, so
# the axiom is exercised, not re-implemented. mapping.md §1 / §3.1.
_REAL = {}    # id(MemberObj) -> (real member object, member name)
_ALIVE = []   # strong refs so ids are not recycled inside a case


def canonical(obj):
    real, name = _REAL[id(obj)]
    core = _real_unwrap(real)
    return abstract(core, name)


def skip_decision(obj, is_special, is_init, is_private, inc_special, inc_init,
                  inc_private):
    # impl-start (model.py, verbatim; Assert() calls deleted)
    doc = obj.has_doc
    member = obj.is_class_member
    if not doc:
        return None
    # Resolve the owning class through the ORIGINAL (unwrapped) object's
    # namespace -- the namespace that genuinely knows the class.
    canon = canonical(obj)
    cls_is_owner = False
    if obj.cls_name in canon.ns:
        cls_is_owner = canon.ns[obj.cls_name]
    # The unwrapped namespace lookup recovers the ground-truth ownership.
    if cls_is_owner:
        if ((is_special and inc_special) or
                (is_init and inc_init) or
                (is_private and inc_private)):
            return False
    return None
    # impl-end


def prepatch_decision(obj, is_special, is_init, is_private, inc_special,
                      inc_init, inc_private):
    """model_prepatch.py's impl region (same stripping). NOT part of the
    shadow: used only to COUNT discriminating inputs, i.e. inputs on which the
    pre-patch namespace choice (`obj.ns`) disagrees with the patched result. A
    run with zero such inputs would not be exercising the changed behaviour and
    is failed below."""
    doc = obj.has_doc
    if not doc:
        return None
    cls_is_owner = False
    if obj.cls_name in obj.ns:
        cls_is_owner = obj.ns[obj.cls_name]
    if cls_is_owner:
        if ((is_special and inc_special) or
                (is_init and inc_init) or
                (is_private and inc_private)):
            return False
    return None


# --------------------------------------------------------------------------
# real callees, loaded from the PATCHED /testbed tree
# --------------------------------------------------------------------------

def _load_real():
    """Bind the two real repo callees: the oracle `_skip_member` (patched) and
    `sphinx.util.inspect.unwrap` (the axiomatized `canonical`)."""
    from sphinx.ext.napoleon import _skip_member
    from sphinx.util.inspect import unwrap
    return _skip_member, unwrap


_real_skip_member = None
_real_unwrap = None


# --------------------------------------------------------------------------
# TYPE BRIDGE (mapping.md §2)
# --------------------------------------------------------------------------

_TOKENS = {}


def token(s):
    """Intern a class-name string as the model's opaque int identity."""
    t = _TOKENS.get(s)
    if t is None:
        t = len(_TOKENS) + 1
        _TOKENS[s] = t
    return t


class BridgeUndefined(Exception):
    """The repo's ownership expression raises on this binding, so the input has
    no Dict[int, bool] preimage. Never silently dropped."""


def _owns(v, name):
    """The repository's ownership expression `cls and hasattr(cls, name) and
    name in cls.__dict__` (__init__.py:445-446), as a bool. Returns None when
    it would raise (the repo's `else:` clause is outside its try/except)."""
    try:
        return bool(v and hasattr(v, name) and name in v.__dict__)
    except Exception:
        return None


def abstract(real_obj, name):
    """real member object -> MemberObj (mapping.md §2)."""
    qual = getattr(real_obj, "__qualname__", "") or ""
    cls_path, _, _ = qual.rpartition(".")
    has_doc = bool(getattr(real_obj, "__doc__", False))
    g = getattr(real_obj, "__globals__", {}) or {}
    ns = {}
    for k, v in g.items():
        owned = _owns(v, name)
        if owned is None:
            if k == cls_path:
                raise BridgeUndefined(
                    "ownership expression raises for cls_path=%r" % (cls_path,))
            continue    # a key the repo never looks up on this input
        ns[token(k)] = owned
    # is_class_member: mapping.md §1 -- the ground truth taken on the CANONICAL
    # (unwrapped) object, via the real unwrap.
    core = _real_unwrap(real_obj)
    gc = getattr(core, "__globals__", {}) or {}
    if cls_path in gc:
        owned = _owns(gc[cls_path], name)
        if owned is None:
            raise BridgeUndefined(
                "ownership expression raises for canonical cls_path=%r"
                % (cls_path,))
        is_cm = owned
    else:
        is_cm = False
    m = MemberObj(has_doc, is_cm, token(cls_path), ns)
    _REAL[id(m)] = (real_obj, name)
    _ALIVE.append(m)
    return m


def classify(name):
    """mapping.md §2 row 6: the repository's own kind classification
    (__init__.py:451-455), which makes the model's mutual-exclusion Requires
    hold by construction."""
    is_init = (name == "__init__")
    is_special = (not is_init and name.startswith("__") and name.endswith("__"))
    is_private = (not is_init and not is_special and name.startswith("_"))
    return is_special, is_init, is_private


def tag(r):
    """Identity-sensitive result bridge: only False and None are in the modeled
    codomain (mapping.md §2, last paragraph)."""
    if r is False:
        return "False"
    if r is None:
        return "None"
    return "OTHER:%r" % (r,)


# --------------------------------------------------------------------------
# input generation: REAL member objects
# --------------------------------------------------------------------------

_DECO_CODE = compile(
    "import functools\n"
    "def deco(f):\n"
    "    @functools.wraps(f)\n"
    "    def wrapper(*a, **k):\n"
    "        return f(*a, **k)\n"
    "    return wrapper\n", "<deco_module>", "exec")
_FUNC_CODE = compile("def _f(self):\n    pass\n", "<member_module>", "exec")


def _wrap_once(f):
    """functools.wraps decorator whose OWN globals live in a separate module
    dict, so the wrapper's __globals__ cannot contain the owning class -- the
    exact shape of the reported bug / the F2P test's simple_decorator."""
    dg = {}
    exec(_DECO_CODE, dg)
    return dg["deco"](f)


def build_case(clsname, membername, doc, decorate, shape):
    """Build a real member object. Returns (obj, intent_owned) where
    intent_owned is the builder's ground truth for the repo's ownership
    relation: the value bound at the class-name key in the DEFINING module
    globals is truthy and carries `membername` in its own __dict__."""
    g = {}
    exec(_FUNC_CODE, g)
    func = g.pop("_f")
    func.__name__ = membername if membername.isidentifier() else "_f"
    func.__qualname__ = "%s.%s" % (clsname, membername)
    func.__doc__ = doc
    if shape == "owned":
        g[clsname] = type(clsname, (), {membername: func})
        intent = True
    elif shape == "inherited":
        base = type("Base", (), {membername: func})
        g[clsname] = type(clsname, (base,), {})
        # hasattr yes, own __dict__ no -- unless the name is one every class
        # body carries intrinsically ('__doc__', '__module__', ...).
        intent = membername in vars(g[clsname])
    elif shape == "absent":
        g[clsname] = type(clsname, (), {})
        intent = membername in vars(g[clsname])      # intrinsics only
    elif shape == "unbound":
        # the class exists but is never bound in the defining globals: the
        # repo's `obj.__globals__[cls_path]` raises KeyError.
        type(clsname, (), {membername: func})
        intent = False
    elif shape == "nonclass":
        # a non-class binding that still has a __dict__, so the repo's
        # expression evaluates to False instead of raising.
        def _noise():
            pass
        g[clsname] = _noise
        intent = False
    elif shape == "falsy":
        meta = type("Meta", (type,), {"__len__": lambda self: 0})
        g[clsname] = meta(clsname, (), {membername: func})
        intent = False                      # the repo's `cls and` conjunct
    elif shape == "shadowed":
        # a DIFFERENT class object, bound under the same name, owns the member
        type(clsname, (), {membername: func})           # the lexical owner
        g[clsname] = type(clsname, (), {membername: func})
        intent = True
    else:
        raise AssertionError("unknown shape %r" % (shape,))
    # namespace noise: other classes and non-class values under other keys
    g["_OtherCls"] = type("_OtherCls", (), {membername: func})
    g["_EmptyCls"] = type("_EmptyCls", (), {})
    g["_num"] = 17
    obj = func
    for _ in range(decorate):
        obj = _wrap_once(obj)
    return obj, intent


class ConfigStub:
    def __init__(self, inc_init, inc_special, inc_private):
        self.napoleon_include_init_with_doc = inc_init
        self.napoleon_include_special_with_doc = inc_special
        self.napoleon_include_private_with_doc = inc_private


class AppStub:
    def __init__(self, cfg):
        self.config = cfg


def rand_name(rng):
    """Random member name over the same category space (never __weakref__)."""
    core = rng.choice(["init", "doc", "x", "value", "calc", "a", "spec",
                       "func", "weakref2", "AB", ""])
    style = rng.randrange(7)
    if style == 0:
        name = "__%s__" % core
    elif style == 1:
        name = "_%s" % core
    elif style == 2:
        name = core
    elif style == 3:
        name = "__%s" % core
    elif style == 4:
        name = "%s__" % core
    elif style == 5:
        name = "__init__"
    else:
        name = "_%s_%s" % (core, rng.choice(["doc", "undoc"]))
    return "_x" if name == "__weakref__" else name


def rand_clsname(rng):
    return rng.choice(["SampleClass", "SampleError", "C", "Owner", "A_b",
                       "DistributedTrainerReplicated", "Z"])


# --------------------------------------------------------------------------
# one comparison
# --------------------------------------------------------------------------

def check_one(case):
    """Run shadow and oracle on one input. Returns (err_or_None,
    discriminating: bool)."""
    clsname, membername, doc, decorate, shape, what, cfg, skip = case
    _REAL.clear()
    del _ALIVE[:]
    obj, intent = build_case(clsname, membername, doc, decorate, shape)
    inc_init, inc_special, inc_private = cfg

    # ORACLE: the real patched repo function.
    app = AppStub(ConfigStub(inc_init, inc_special, inc_private))
    real = tag(_real_skip_member(app, what, membername, obj, skip, object()))

    # bridge into the model carrier
    try:
        m = abstract(obj, membername)
    except BridgeUndefined as e:
        return ("BRIDGE-UNDEFINED (input outside the abstraction, reported "
                "rather than dropped): case=%r: %s" % (case, e)), False

    # the bridge must agree with the builder's ground truth for ownership
    if m.is_class_member != intent and decorate == 0:
        return ("BRIDGE ERROR: is_class_member=%r but the builder built "
                "intent_owned=%r for case=%r" % (m.is_class_member, intent,
                                                 case)), False

    is_special, is_init, is_private = classify(membername)
    # the model's only non-vacuous Requires
    assert not (is_init and (is_special or is_private))
    assert not (is_special and (is_init or is_private))
    assert not (is_private and (is_init or is_special))

    # the axiom's own obligations, on the real callee (exercised, not assumed)
    canon = canonical(m)
    if canon is None:
        return "AXIOM VIOLATION: canonical() returned None for %r" % (case,), False
    if canon.has_doc != m.has_doc or canon.cls_name != m.cls_name:
        return ("AXIOM VIOLATION: real unwrap does not preserve has_doc/"
                "cls_name for case=%r (%r/%r vs %r/%r)"
                % (case, canon.has_doc, canon.cls_name, m.has_doc,
                   m.cls_name)), False
    if m.is_class_member != (m.cls_name in canon.ns and canon.ns[m.cls_name]):
        return ("AXIOM VIOLATION: canonical namespace does not record ground-"
                "truth ownership for case=%r" % (case,)), False

    # SHADOW
    shadow = tag(skip_decision(m, is_special, is_init, is_private, inc_special,
                               inc_init, inc_private))
    if shadow != real:
        return ("DISAGREEMENT\n  input: clsname=%r name=%r doc=%r decorate=%d "
                "shape=%s what=%s cfg(inc_init,inc_special,inc_private)=%r "
                "skip=%r\n  bridged: has_doc=%r cls_name=%r is_class_member=%r "
                "ns=%r\n  shadow (impl region) = %s\n  oracle (real patched "
                "_skip_member) = %s"
                % (clsname, membername, doc, decorate, shape, what, cfg, skip,
                   m.has_doc, m.cls_name, m.is_class_member, m.ns, shadow,
                   real)), False

    pre = tag(prepatch_decision(m, is_special, is_init, is_private, inc_special,
                                inc_init, inc_private))
    return None, (pre != real)


def boundary_cases():
    out = []
    for clsname in CLSNAMES:
        for membername in NAMES:
            for doc in DOCS:
                for decorate in DECORATIONS:
                    for shape in SHAPES:
                        for what in WHATS:
                            for cfg in CFGS:
                                out.append((clsname, membername, doc, decorate,
                                            shape, what, cfg, True))
    return out


def rand_case(rng):
    return (rand_clsname(rng), rand_name(rng), rng.choice(DOCS),
            rng.choice(DECORATIONS), rng.choice(SHAPES), rng.choice(WHATS),
            rng.choice(CFGS), rng.random() < 0.5)


def main():
    global _real_skip_member, _real_unwrap
    try:
        _real_skip_member, _real_unwrap = _load_real()
    except Exception as e:      # import failure is an error, not a pass
        print("status=error cannot import the real patched callees: %r" % (e,))
        return 1

    checked = 0
    discriminating = 0
    boundary = boundary_cases()
    for case in boundary:
        err, disc = check_one(case)
        if err:
            print(err)
            print("status=fail after %d checks" % (checked,))
            return 1
        checked += 1
        discriminating += int(disc)

    rng = random.Random(SEED)
    n_fuzz = max(0, N_MIN_TOTAL - len(boundary))
    for _ in range(n_fuzz):
        err, disc = check_one(rand_case(rng))
        if err:
            print(err)
            print("status=fail after %d checks" % (checked,))
            return 1
        checked += 1
        discriminating += int(disc)

    if discriminating == 0:
        # a green run that never exercised the patched behaviour certifies
        # nothing; fail loudly instead.
        print("status=fail vacuous run: 0 of %d inputs discriminate the "
              "patched namespace choice from the pre-patch one" % (checked,))
        return 1

    print("G-CONF OK: shadow (verbatim impl region of model.py, canonical() "
          "calling the real sphinx.util.inspect.unwrap) agrees with the real "
          "patched sphinx.ext.napoleon._skip_member on %d inputs "
          "(%d exhaustive boundary + %d fuzz, seed %d); %d of them "
          "discriminate the patched namespace choice from the pre-patch one; "
          "0 disagreements." % (checked, len(boundary), n_fuzz, SEED,
                                discriminating))
    print(json.dumps({"checked": checked, "boundary": len(boundary),
                      "fuzz": n_fuzz, "disagreements": 0,
                      "discriminating": discriminating, "seed": SEED,
                      "oracle": "sphinx.ext.napoleon._skip_member (called, "
                                "gold-patched)",
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
