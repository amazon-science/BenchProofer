#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9658 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers ``dot``
and ``render_qualified`` copy over as plain functions on a PSeq realized as an
immutable tuple shim (the executable impl statements themselves never touch
PSeq — the Assert lines that did are contract calls and are stripped). There
are no @ContractOnly callees in this bundle (the axioms region is empty).

ORACLE: the REAL patched repo chain the model models per mapping.md — the
placeholder factory ``sphinx.ext.autodoc.mock._make_subclass`` (whose product's
``__init__`` is ``_MockObject.__init__``) and the renderer
``sphinx.util.typing.restify``. The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched package importable.
A real placeholder is built exactly the way the repo's attribute-access hook
builds one: ``_make_subclass(name, module)()``. Then:

  * ``subclass_short_name(name)``        vs the placeholder's real short
    identifier (its ``__name__`` attribute as seen from the instance);
  * ``placeholder_display_name(short)``  vs the placeholder's real display
    identifier (its ``__qualname__`` attribute, set by ``__init__``);
  * ``qualified_reference(name, module)`` vs the real rendered reference: the
    inner text of ``restify(placeholder)`` with its constant ``:py:class:`` /
    backtick decoration removed (mapping.md section 2 documents the wrapper as
    a constant the model omits), cross-checked against the placeholder's real
    ``__module__`` + '.' + ``__qualname__``.

Type bridge (mapping.md section 2): repo ``str`` values map to List[int] of
Unicode code points; ``s[k]`` <-> ``ord(s[k])``, concatenation <-> list ``+``,
'.' <-> [46], empty str <-> []. The shadow's output list is decoded back to a
str for the comparison (an exact bijection — no precision concern).

Input domain: the model's Requires only demand read access to the code-point
lists, so any list is admissible. The real factory operates on Python type
names / module-path strings, which excludes NUL (the type constructor rejects
names containing it) and unpaired surrogate code points (not representable as
real repo text); generation is restricted to that operating domain, mirroring
the callee's, and stays Requires-satisfying throughout.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs, each
pair exercising all three modeled functions. Pinned fuzz seed: 9658.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 9658
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure helpers from model.py, copied over as plain functions ---------------

def dot():
    return PSeq(46)


def render_qualified(module, display):
    return module + dot() + display


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def subclass_short_name(name):
    result = []  # type: list
    i = 0
    while i < len(name):
        result = result + [name[i]]
        i = i + 1
    return result


def placeholder_display_name(short_name):
    result = []  # type: list
    i = 0
    while i < len(short_name):
        result = result + [short_name[i]]
        i = i + 1
    return result


def qualified_reference(name, module):
    short = subclass_short_name(name)
    display = placeholder_display_name(short)
    result = []  # type: list
    i = 0
    while i < len(module):
        result = result + [module[i]]
        i = i + 1
    result = result + [46]
    result = result + display
    return result


# --- bridge: str <-> List[int] of code points ---------------------------------

def to_codes(s):
    return [ord(c) for c in s]


def to_str(codes):
    return "".join(chr(c) for c in codes)


REF_PREFIX = ":py:class:`"
REF_SUFFIX = "`"


def check_pair(make_subclass, restify, name, module):
    """Run shadow and oracle on one (name, module) string pair; return an
    error string on disagreement, else None."""
    name_l = to_codes(name)
    module_l = to_codes(module)

    # Build the REAL placeholder the way the repo's attribute-access hook
    # does: subclass the placeholder base under `module`, then instantiate.
    placeholder = make_subclass(name, module)()
    real_short = getattr(placeholder, "__name__")
    real_display = getattr(placeholder, "__qualname__")
    real_module = getattr(placeholder, "__module__")

    shadow_short = to_str(subclass_short_name(name_l))
    if shadow_short != real_short:
        return ("DISAGREEMENT (short identifier)\n  name=%r module=%r\n"
                "  shadow=%r\n  real=%r"
                % (name, module, shadow_short, real_short))

    shadow_display = to_str(placeholder_display_name(to_codes(real_short)))
    if shadow_display != real_display:
        return ("DISAGREEMENT (display identifier)\n  name=%r module=%r\n"
                "  shadow=%r\n  real=%r"
                % (name, module, shadow_display, real_display))

    shadow_ref = to_str(qualified_reference(name_l, module_l))
    restified = restify(placeholder)
    if not (restified.startswith(REF_PREFIX) and restified.endswith(REF_SUFFIX)):
        return ("DISAGREEMENT (renderer wrapper shape)\n  name=%r module=%r\n"
                "  shadow=%r\n  real=%r" % (name, module, shadow_ref, restified))
    real_ref = restified[len(REF_PREFIX):-len(REF_SUFFIX)]
    if shadow_ref != real_ref:
        return ("DISAGREEMENT (qualified reference)\n  name=%r module=%r\n"
                "  shadow=%r\n  real=%r" % (name, module, shadow_ref, real_ref))
    # Cross-check: the rendered inner text is the placeholder's real module
    # path joined with its real display identifier by a dot.
    joined = real_module + "." + real_display
    if shadow_ref != joined:
        return ("DISAGREEMENT (attribute join)\n  name=%r module=%r\n"
                "  shadow=%r\n  real=%r" % (name, module, shadow_ref, joined))
    # PSeq pure-helper self-consistency on the same input (the spec's join).
    pure_ref = render_qualified(PSeq(*module_l), PSeq(*name_l))
    if list(pure_ref._t) != qualified_reference(name_l, module_l):
        return ("DISAGREEMENT (pure helper vs impl)\n  name=%r module=%r"
                % (name, module))
    return None


def boundary_pairs():
    return [
        ("Class", "unknown.secret"),   # the F2P shape: leaf under a dotted path
        ("Class", "unknown"),
        ("Module", "torch.nn"),        # the issue's reported shape
        ("", "unknown"),               # empty attribute name
        ("Class", ""),                 # empty module path
        ("", ""),
        ("A", "b"),                    # single-char extremes
        ("_", "_"),
        ("Leaf", "a.b.c.d.e.f"),       # deep dotted module path
        ("name.with.dots", "pkg"),     # dots inside the attribute name
        ("X" * 200, "m" * 200),        # long identifiers
        ("snake_case_name", "CamelCase.Module"),
        ("N0mbers123", "p4th.v2"),
        ("éüñ", "unicöde.mød"),  # non-ASCII BMP
        ("\U0001F600emoji", "astral.plane"),              # astral code points
        (" spaced name ", "odd module"),
        ("tab\tname", "new\nline"),
    ]


_ALPHA = ("abcdefghijklmnopqrstuvwxyz"
          "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def rand_str(rng, maxlen=12):
    n = rng.randint(0, maxlen)
    out = []
    for _ in range(n):
        p = rng.random()
        if p < 0.85:
            out.append(rng.choice(_ALPHA))
        elif p < 0.93:
            out.append(rng.choice(".-+ !\"#$%&'()*,/:;<=>?@[]^`{|}~"))
        else:
            # arbitrary BMP/astral code point, excluding NUL and surrogates
            # (outside the type constructor's / real repo text's domain)
            while True:
                cp = rng.randint(1, 0x10FFFF)
                if not (0xD800 <= cp <= 0xDFFF):
                    break
            out.append(chr(cp))
    return "".join(out)


def main():
    # REAL patched callees (PYTHONPATH=/testbed; the gate applied the patch).
    from sphinx.ext.autodoc.mock import _make_subclass
    from sphinx.util.typing import restify

    checked = 0
    for name, module in boundary_pairs():
        err = check_pair(_make_subclass, restify, name, module)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_pair(_make_subclass, restify, rand_str(rng), rand_str(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real placeholder factory + renderer on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_pairs()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
