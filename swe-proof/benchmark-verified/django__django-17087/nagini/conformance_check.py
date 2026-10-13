#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-17087 (nagini).

SHADOW: the impl region of model.py's `render_class_member_reference`, copied
verbatim below with the contract calls (Requires/Ensures) stripped. The impl
region uses only plain `List[int]` concatenation — no PSeq operations — so no
PSeq shim is needed; the @Pure helpers (`member_path`, `import_line`) appear
only in contracts and are not part of the executable impl. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.migrations.serializer.FunctionTypeSerializer.serialize()`, taken on
the branch for a callable bound to a class object. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable. For each generated input we synthesise a real class-bound
method (a function bound to a freshly created class object via
types.MethodType) whose owning class carries the generated
__module__/__name__/__qualname__ texts, hand it to the real serializer, and
diff its (rendered string, import set) output against the shadow.

Type bridge (mapping.md section 2): repo `str` values map to `List[int]` of
Unicode code points (`cps(s) == [ord(ch) for ch in s]`); the real return is a
2-tuple `(string, imports)` whose import set is a singleton — the shadow's
second component compares against that single member's code points, and the
set wrapper is checked to be exactly one element.

Input domain: the model's Requires demands only readable lists of code points,
so any four texts are Requires-satisfying. The oracle-side realization needs
the texts to be settable as class/function identity attributes (always true
for str) and the branch guard needs the owning class object to be truthy (true
for any freshly created class). Generation spans: top-level shapes
(qualified == simple name), nested shapes (qualified = dotted chain + leaf,
including a nested Enum owner), empty texts, dotted modules of depth 1-4,
ASCII identifier shapes, and raw unicode/punctuation texts.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz methods.
Pinned fuzz seed: 170870.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random fuzzer; hypothesis not required).
"""
import enum
import json
import random
import string
import sys
import types

SEED = 170870
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def render_class_member_reference(module, class_simple_name,
                                  class_qualified_name, method_name):
    # frag = module + "." + class_qualified_name + "." + method_name
    frag = []                                # type: list
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_qualified_name
    frag = frag + [46]                       # '.'
    frag = frag + method_name
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    return (frag, imp)


# --- bridge: str <-> List[int] of code points ----------------------------------

def cps(s):
    return [ord(ch) for ch in s]


def make_bound_method(module, class_name, class_qualname, method_name):
    """A real callable bound to a class object whose identity texts are the
    given four strings — exactly the data the real serializer branch reads."""
    cls = types.new_class(class_name or "C")
    cls.__module__ = module
    cls.__name__ = class_name
    cls.__qualname__ = class_qualname

    def _fn(c):
        return c
    _fn.__name__ = method_name
    return types.MethodType(_fn, cls)   # __self__ is the class object


def check_one(serializer_cls, module, class_name, class_qualname, method_name):
    """Run shadow and oracle on one text quadruple; return an error string on
    disagreement, else None."""
    value = make_bound_method(module, class_name, class_qualname, method_name)
    # the branch guard the real code checks before the modeled hunk runs
    assert getattr(value, "__self__", None) is not None and isinstance(
        value.__self__, type)

    real_string, real_imports = serializer_cls(value).serialize()

    shadow_frag, shadow_imp = render_class_member_reference(
        cps(module), cps(class_name), cps(class_qualname), cps(method_name))

    if len(real_imports) != 1:
        return ("DISAGREEMENT (import-set arity)\n"
                "  input=(module=%r, class_name=%r, class_qualname=%r, "
                "method_name=%r)\n  real imports=%r (expected a singleton)"
                % (module, class_name, class_qualname, method_name,
                   real_imports))
    real_import = next(iter(real_imports))

    if cps(real_string) != shadow_frag or cps(real_import) != shadow_imp:
        return ("DISAGREEMENT\n"
                "  input=(module=%r, class_name=%r, class_qualname=%r, "
                "method_name=%r)\n"
                "  shadow frag=%r  (as text: %r)\n  real  frag=%r  (%r)\n"
                "  shadow import=%r  (as text: %r)\n  real  import=%r  (%r)"
                % (module, class_name, class_qualname, method_name,
                   shadow_frag, "".join(map(chr, shadow_frag)),
                   cps(real_string), real_string,
                   shadow_imp, "".join(map(chr, shadow_imp)),
                   cps(real_import), real_import))
    return None


# --- boundary inputs ------------------------------------------------------------

class Outer:
    class Inner:
        @classmethod
        def method(cls):
            return cls

    class Middle:
        class Deep:
            @classmethod
            def go(cls):
                return cls


class Host:
    class NestedMembers(enum.Enum):
        X = "X"

        @classmethod
        def method(cls):
            return cls.X


class TopLevelCls:
    @classmethod
    def cm(cls):
        return cls


def boundary_quads():
    """(module, class __name__, class __qualname__, method __name__) texts."""
    quads = [
        # top-level shape: qualified name == simple name
        ("m", "C", "C", "f"),
        ("pkg.sub.mod", "Widget", "Widget", "build"),
        # nested shapes: qualified name carries the enclosing dotted chain
        ("m", "Inner", "Outer.Inner", "method"),
        ("a.b.c.d", "Leaf", "E1.E2.E3.Leaf", "run"),
        # empty texts (Requires allows any code-point lists)
        ("", "C", "C", "f"),
        ("m", "", "", "f"),
        ("m", "C", "C", ""),
        ("", "", "", ""),
        # single-char and dot-heavy texts
        ("x", "y", "y", "z"),
        ("m", "C", "A.B.C", "."),
        # unicode texts
        ("möd", "Kläss", "Hülle.Kläss", "metodé"),
        ("模块", "类", "外.类", "方法"),
    ]
    # real class shapes (identity texts read straight off real classes)
    for owner, mname in [(Outer.Inner, "method"), (Outer.Middle.Deep, "go"),
                         (Host.NestedMembers, "method"), (TopLevelCls, "cm")]:
        quads.append((owner.__module__, owner.__name__,
                      owner.__qualname__, mname))
    return quads


# --- fuzz generation --------------------------------------------------------------

IDENT_HEAD = string.ascii_letters + "_"
IDENT_TAIL = string.ascii_letters + string.digits + "_"


def rand_ident(rng):
    n = rng.randint(1, 10)
    return rng.choice(IDENT_HEAD) + "".join(
        rng.choice(IDENT_TAIL) for _ in range(n - 1))


def rand_text(rng):
    """Occasionally arbitrary unicode/punctuation instead of identifier shape
    (Requires permits any code points; the real formatting is text-agnostic)."""
    n = rng.randint(0, 12)
    return "".join(chr(rng.choice((rng.randint(32, 126),
                                   rng.randint(0xA0, 0x2FFF))))
                   for _ in range(n))


def rand_quad(rng):
    module = ".".join(rand_ident(rng) for _ in range(rng.randint(1, 4)))
    leaf = rand_ident(rng)
    if rng.random() < 0.5:
        # nested: qualified name = enclosing dotted chain + '.' + leaf
        prefix = ".".join(rand_ident(rng)
                          for _ in range(rng.randint(1, 3)))
        qualname = prefix + "." + leaf
    else:
        qualname = leaf
    method = rand_ident(rng)
    if rng.random() < 0.05:
        # raw-text slice: exercise the pure-concatenation claim beyond
        # identifier-shaped inputs
        module, leaf, qualname, method = (rand_text(rng), rand_text(rng),
                                          rand_text(rng), rand_text(rng))
    return module, leaf, qualname, method


def main():
    # Oracle import: the REAL patched serializer class (PYTHONPATH=/testbed,
    # gold patch applied by the gate). Settings are configured defensively;
    # the serializer under test reads only object attributes.
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    from django.db.migrations.serializer import FunctionTypeSerializer

    checked = 0
    n_boundary = 0
    for quad in boundary_quads():
        err = check_one(FunctionTypeSerializer, *quad)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_one(FunctionTypeSerializer, *rand_quad(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched serializer on %d "
          "class-bound-method inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
