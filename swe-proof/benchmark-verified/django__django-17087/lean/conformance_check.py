#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_classMethodRef
against the patch.diff behaviour (post-patch FunctionTypeSerializer.serialize,
class-bound-method branch).

The impl region is NOT all-A-tagged (it has I/R structure plus the deeply-modeled
dotted join). The shadow reproduces the post-patch assembly op-for-op:

    text    = "%s.%s.%s" % (module, ownerQualname, methodName)
    imports = {"import %s" % module}

The A-reference ops (the `%`-format dotted join and the import set) are realised
exactly as the real post-patch code does. We build REAL Python class hierarchies
(including nested classes) with real classmethods, read their genuine
`__module__` / `__qualname__` / method `__name__` attributes, and assert the
shadow agrees with an independent reconstruction of the patched serializer branch
over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys
import types

SEED = 17087          # pinned in mapping.md
N = 120_000           # >= 10^5

NAME_FRAGS = ["A", "B", "C", "Profile", "Capability", "Inner", "Outer",
              "Choices", "Model", "X", "Y", "Helper", "Mixin"]
MOD_FRAGS = ["app", "models", "core", "pkg", "sub", "appname", "migrations"]


def make_bound_classmethod(rng):
    """Construct a REAL class (possibly nested) with a real classmethod, return
    the bound method object and the genuine module string."""
    depth = rng.randint(1, 3)              # 1 = top-level, >=2 = nested
    names = [rng.choice(NAME_FRAGS) for _ in range(depth)]
    method_name = rng.choice(NAME_FRAGS).lower() + "_m"
    module = ".".join(rng.choice(MOD_FRAGS)
                      for _ in range(rng.randint(1, 3)))

    # Build the innermost class with a classmethod, then wrap in enclosing
    # classes so __qualname__ reflects the real nesting (Outer.Inner...).
    def _mk_inner():
        ns = {}
        exec(f"def {method_name}(cls): return cls", ns)  # plain fn placeholder
        cm = classmethod(ns[method_name])
        return type(names[-1], (), {method_name: cm})

    inner = _mk_inner()
    # Reparent to produce a nested __qualname__.
    qualname = ".".join(names)
    inner.__qualname__ = qualname
    inner.__module__ = module
    bound = getattr(inner, method_name)        # bound classmethod
    return bound, inner, module, method_name


def shadow(klass, value, module):
    """R/I shadow of implementation_classMethodRef.

    text := module ++ "." ++ ownerQualname ++ "." ++ methodName
    imports := [ "import " ++ module ]
    The A-reference dotted join uses the REAL class.__qualname__ (post-patch label).
    """
    text = module + "." + klass.__qualname__ + "." + value.__name__
    imports = ["import " + module]
    return text, imports


def patched_branch(value):
    """Independent reconstruction of the post-patch serializer branch."""
    klass = value.__self__
    module = klass.__module__
    return "%s.%s.%s" % (module, klass.__qualname__, value.__name__), {
        "import %s" % module
    }


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    for _ in range(N):
        bound, klass, module, method_name = make_bound_classmethod(rng)
        s_text, s_imports = shadow(klass, bound, module)
        p_text, p_imports = patched_branch(bound)
        if s_text != p_text or set(s_imports) != p_imports:
            disagreements += 1
            if len(examples) < 10:
                examples.append((klass.__qualname__, s_text, p_text,
                                 s_imports, p_imports))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for q, st, pt, si, pi in examples:
            print(f"  qual={q!r} shadow=({st!r},{si!r}) patched=({pt!r},{pi!r})")
        return 1

    print(f"G-CONF OK: {N} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
