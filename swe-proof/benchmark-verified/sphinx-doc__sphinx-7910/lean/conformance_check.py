#!/usr/bin/env python
"""G-CONF: differential conformance for sphinx-doc__sphinx-7910.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_memberInclusion` skeleton and diffs it against the REAL patched
callee `sphinx.ext.napoleon._skip_member` over a discrete catalogue plus
>=1e5 fuzzed inputs.

Modeled branch: the single-segment `cls_path` case (`'.' not in cls_path`) — the
branch the gold patch edits (`cls = obj.__globals__[cls_path]` ->
`cls = inspect.unwrap(obj).__globals__[cls_path]`). The decorated-member case
(wrapper whose `__globals__` lack the owning class) is the bug the issue reports.

Bridge (mapping.md):
  what/name (str)                         -> identity
  member object `obj`                     -> PyObj model:
      qualname  = getattr(obj,'__qualname__','')
      hasDoc    = bool(getattr(obj,'__doc__',False))
      coreObject= follow __wrapped__ to the innermost object (== inspect.unwrap)
      globalsMap= {classname: list(cls.__dict__)} of class-valued names in the
                  *coreObject's* __globals__
  app.config.napoleon_include_{init,special,private}_with_doc  -> cfg flags
  real return False -> "false";  None -> "none"   (True must never occur)

Exit 0 iff zero disagreements. stdlib only; pinned seed.
"""
import functools
import random
import sys

SEED = 7910
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_memberInclusion (post-patch R/I leg) ----

def cls_path_single(qualname):
    """clsPathSingle: a single dotless owner segment (`Owner.member`)."""
    parts = qualname.split(".")
    if len(parts) == 2:
        return parts[0]
    return None


def shadow_skip(cfg, what, name, qualname, has_doc, core_globals_classes):
    """Transliteration of problem_spec_memberInclusion / implementation_*.
    `cfg` = (inc_init, inc_special, inc_private); `core_globals_classes` maps
    class short-name -> list of that class's directly-declared attribute names
    (from the coreObject's __globals__). Returns "false" or "none"."""
    inc_init, inc_special, inc_private = cfg
    is_member = what in ("module", "class", "exception")
    if name != "__weakref__" and has_doc and is_member:
        cls_owner = False
        if what in ("class", "exception"):
            cp = cls_path_single(qualname)
            if cp is not None:
                attrs = core_globals_classes.get(cp)
                cls_owner = attrs is not None and (name in attrs)
        if what == "module" or cls_owner:
            is_init = (name == "__init__")
            is_special = (not is_init) and name.startswith("__") and name.endswith("__")
            is_private = (not is_init) and (not is_special) and name.startswith("_")
            if ((is_special and inc_special) or (is_private and inc_private) or
                    (is_init and inc_init)):
                return "false"
    return "none"


# ---- bridge: derive the PyObj model from a real member object ---------------

def model_of(obj):
    """Extract (qualname, has_doc, core_globals_classes) per mapping.md."""
    qualname = getattr(obj, "__qualname__", "") or ""
    has_doc = bool(getattr(obj, "__doc__", False))
    # coreObject: follow __wrapped__ to the innermost (mirrors inspect.unwrap).
    core = obj
    seen = set()
    while hasattr(core, "__wrapped__") and id(core) not in seen:
        seen.add(id(core))
        core = core.__wrapped__
    g = getattr(core, "__globals__", {}) or {}
    classes = {k: list(vars(v)) for k, v in g.items() if isinstance(v, type)}
    return qualname, has_doc, classes


# ---- builders: real member objects with controlled globals / decoration -----

def build_member(clsname, membername, doc, decorate):
    """Build a real function `obj` that is a member `membername` of a class
    `clsname` defined in `obj`'s module globals. If `decorate`, wrap it with a
    functools.wraps decorator defined in a SEPARATE module globals (so the
    wrapper's __globals__ lack `clsname` — the bug condition)."""
    g = {}
    exec("def {m}(self):\n    pass\n".format(m=membername), g)
    func = g[membername]
    func.__qualname__ = "{c}.{m}".format(c=clsname, m=membername)
    func.__doc__ = doc
    cls = type(clsname, (), {membername: func})
    g[clsname] = cls
    obj = func
    if decorate:
        dg = {}
        exec(
            "import functools\n"
            "def deco(f):\n"
            "    @functools.wraps(f)\n"
            "    def wrapper(*a, **k):\n"
            "        return f(*a, **k)\n"
            "    return wrapper\n",
            dg,
        )
        obj = dg["deco"](func)
    return obj


def build_module_member(membername, doc):
    """A module-level member: qualname has no dot (no owning class)."""
    g = {}
    exec("def {m}():\n    pass\n".format(m=membername), g)
    func = g[membername]
    func.__qualname__ = membername
    func.__doc__ = doc
    return func


def fake_app(inc_init, inc_special, inc_private):
    cfg = type("Cfg", (), {})()
    cfg.napoleon_include_init_with_doc = inc_init
    cfg.napoleon_include_special_with_doc = inc_special
    cfg.napoleon_include_private_with_doc = inc_private
    app = type("App", (), {})()
    app.config = cfg
    return app


def real_skip(app, what, name, obj):
    from sphinx.ext.napoleon import _skip_member
    r = _skip_member(app, what, name, obj, True, object())
    if r is False:
        return "false"
    if r is None:
        return "none"
    return "other:{!r}".format(r)  # True/anything -> forces a mismatch


def main():
    rng = random.Random(SEED)

    clsnames = ["SampleClass", "SampleError"]
    members = ["__init__", "__special_doc__", "__decorated_func__",
               "_private", "__weakref__", "regular", "__dunder__"]
    whats_cls = ["class", "exception"]
    docs = ["doc text", None]
    decorates = [False, True]
    cfgs = [(i, s, p) for i in (False, True)
            for s in (False, True) for p in (False, True)]

    cases = []  # (app_cfg, what, name, obj)
    # discrete catalogue: every class/exception combination
    for clsname in clsnames:
        for membername in members:
            for doc in docs:
                for decorate in decorates:
                    obj = build_member(clsname, membername, doc, decorate)
                    for what in whats_cls:
                        for cfg in cfgs:
                            cases.append((cfg, what, membername, obj))
    # module members (no owning class)
    for membername in ["__special_doc__", "_private", "__weakref__",
                       "regular", "__init__"]:
        for doc in docs:
            obj = build_module_member(membername, doc)
            for cfg in cfgs:
                cases.append((cfg, "module", membername, obj))
    # non-documentable kinds always defer
    for what in ["method", "function", "attribute"]:
        obj = build_member("SampleClass", "regular", "doc", False)
        for cfg in cfgs:
            cases.append((cfg, what, "regular", obj))

    base = list(cases)
    # pad with randomized resampling to reach >= 1e5 comparisons
    while len(cases) < N_RANDOM:
        cases.append(rng.choice(base))

    disagreements = 0
    checked = 0
    for cfg, what, name, obj in cases:
        # cfg = (inc_init, inc_special, inc_private)
        app = fake_app(cfg[0], cfg[1], cfg[2])
        got = real_skip(app, what, name, obj)
        qualname, has_doc, classes = model_of(obj)
        exp = shadow_skip(cfg, what, name, qualname, has_doc, classes)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print("MISMATCH what={} name={} cfg={} qualname={}: "
                      "real={} shadow={}".format(what, name, cfg, qualname, got, exp))

    print("checked={} disagreements={}".format(checked, disagreements))
    if disagreements == 0:
        print("status=pass conformance OK ({} checks, 0 disagreements)".format(checked))
        return 0
    print("status=fail {} disagreement(s)".format(disagreements))
    return 1


if __name__ == "__main__":
    sys.exit(main())
