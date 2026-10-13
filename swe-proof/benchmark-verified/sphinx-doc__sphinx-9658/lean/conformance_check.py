#!/usr/bin/env python
"""G-CONF: differential conformance for sphinx-doc__sphinx-9658.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_mockQualifiedName` skeleton and diffs it against the REAL patched
behavior: the `__qualname__` a mock stand-in object reports after construction.

  observable: for a mock stand-in created with short name `name` (via
  `_make_subclass(name, module)`), the `__qualname__` attribute of the resulting
  instance, AND the corresponding `restify(...)` rendering tail.
    - real:   instance.__qualname__   (and restify -> 'module.<qualname>')
    - shadow: name                    (problem_spec / implementation: result = name)

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import string
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_mockQualifiedName ---------------------

def shadow_qualified_name(name):
    # transliteration of problem_spec_mockQualifiedName / implementation_*:
    #   __qualname__ := __name__ (the short name the stand-in was created with)
    nameAttr = name
    qualname = nameAttr
    return qualname


# ---- real behavior observation ---------------------------------------------

def real_qualname(name, module):
    """Build a real mock stand-in with short name `name` under `module` via the
    patched `_make_subclass`, instantiate it (runs `_MockObject.__init__`), and
    return the resulting `__qualname__`."""
    from sphinx.ext.autodoc.mock import _make_subclass
    obj = _make_subclass(name, module)()
    return obj.__qualname__


def real_restify_tail(name, module):
    """The component `restify` appends after the module path for a stand-in:
    restify(o) == ':py:class:`%s.%s`' % (o.__module__, o.__qualname__).
    `restify` is applied to the stand-in INSTANCE (as in the F2P test, which
    passes `unknown.secret.Class`, an instance produced by mocked attribute
    access). We verify the rendered string is the expected complete reference."""
    from sphinx.ext.autodoc.mock import _make_subclass
    from sphinx.util.typing import restify
    obj = _make_subclass(name, module)()  # the stand-in instance
    return restify(obj)


def main():
    disagreements = 0
    checked = 0

    rng = random.Random(SEED)
    alphabet = string.ascii_letters + string.digits + "_"

    # discrete catalogue: realistic identifier-shaped short names + the empty
    # base-default name + names with separators that could expose truncation.
    names = ["Class", "secret", "Module", "A", "x", "", "Foo_Bar", "T123",
             "lowercase", "UPPER", "_private", "mixedCase42"]
    modules = ["unknown", "unknown.secret", "pkg.sub", "torch.nn", "a.b.c"]

    cases = [(n, m) for n in names for m in modules]

    for _ in range(N_RANDOM):
        ln = rng.randint(0, 16)
        nm = "".join(rng.choice(alphabet) for _ in range(ln))
        # ensure a non-digit lead is not required: stand-in names are arbitrary
        md = rng.choice(modules)
        cases.append((nm, md))

    for name, module in cases:
        got_qual = real_qualname(name, module)
        exp_qual = shadow_qualified_name(name)
        checked += 1
        if got_qual != exp_qual:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH qualname name={name!r} module={module!r}: "
                      f"real={got_qual!r} shadow={exp_qual!r}")
            continue

        # cross-check the downstream rendering uses the qualname tail (== name).
        rendered = real_restify_tail(name, module)
        expected = ':py:class:`%s.%s`' % (module, name)
        checked += 1
        if rendered != expected:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH restify name={name!r} module={module!r}: "
                      f"real={rendered!r} expected={expected!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
