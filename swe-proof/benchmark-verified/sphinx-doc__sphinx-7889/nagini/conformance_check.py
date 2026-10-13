#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7889 (nagini).

SHADOW
------
The `# impl-start` .. `# impl-end` region of `model.py`, copied VERBATIM (comments
included) with only the contract calls removed -- the two `Assert(...)` lines and
the `# invariants-start`/`-end` blocks of `Invariant(...)`.  Nothing is renamed,
reordered or "simplified": both `while` loops that materialise the display name
code point by code point are executed exactly as written, so the shadow tests the
model's algorithm and not a paraphrase of it.  The `@Pure` helper the region
calls (`render_text`) is copied over the same way, minus its `Ensures`.

`PSeq` is realised by a small immutable-sequence shim (`take`/`drop`/`+`/`len`/
`[]`/`==`) and `ToSeq(list)` materialises one, mirroring the Nagini carriers.

The region's one `@ContractOnly` callee, `display_name`, has no body to copy, so
this script does NOT assume its axiom: the shim CALLS THE REAL REPO FUNCTION it
abstracts -- `sphinx.ext.autodoc.mock._make_subclass` (mapping.md §1/§3.1,
`sphinx/ext/autodoc/mock.py:71-76`, unchanged by the patch) -- converts the
carrier arguments to `str`, and reads `__display_name__` back off the fabricated
class.  Consequently the axiom's Ensures is exercised against real code on every
input, and its display-name output (`produced`, dead in the model once `Assert`
is stripped) is captured through a trace slot and diffed against the oracle
alongside the loop-materialised `result`.  Two observables per input, both from
the shadow, both compared.

ORACLE
------
The REAL patched repo function, CALLED, not transliterated:

    sphinx.ext.autodoc.mock._MockObject.__getitem__   (mock.py:55, body 56)

which the gold patch rewrites to `_make_subclass(str(key), self.__display_name__,
self.__class__)()`.  The gate applies `patch.diff` to /testbed and sets
PYTHONPATH before this script runs, so `mock[key]` below IS the patched
subscript.  Driving it needs only a parent placeholder whose
`self.__display_name__` is the module under test, which is built in-container the
same way the repo builds one (`type(<name>, (_MockObject,), {...})`, i.e. exactly
what `_make_subclass` does), so there is no reason to transliterate anything.
The observable is `type(mock[key]).__display_name__`, the display name of the
placeholder the subscript returns.

TYPE BRIDGE  (mapping.md §2, inverted)
--------------------------------------
The real input is generated FIRST and the model input derived from it, so every
sample is by construction the bridge image of a real one:

    real  key: Any , parent display name: str
    model key_is_text = isinstance(key, str)
          key_text    = [ord(c) for c in str(key)]      # code points of str(key)
          module      = [ord(c) for c in display_name]  # code points of the module

and back on the output side `List[int]` code points -> `str` by `chr`/`ord`, with
`46 == ord('.')`.  A shadow raise or an oracle raise is captured as
`("err", <exception type name>)` so the two sides are compared on failure too,
never just on the happy path.

INPUT DOMAIN
------------
The model's `Requires` constrains only the index's textual rendering: no NUL code
point and no surrogate code point (55296..57343) in `key_text` -- exactly the
names CPython's `type()` rejects, per mapping.md §3.1.  Keys whose `str()` would
carry either are therefore OUTSIDE the specified domain and are excluded (G-AX
covers that the real callee raises there); the domain is NOT narrowed any
further.  In particular `module` is unconstrained by `Requires`, so NUL-bearing
and surrogate-bearing modules ARE generated -- the real callee only concatenates
`module`, so both sides must still agree, and they are checked to.

The input space is infinite (arbitrary-length indices), so: boundary cases first
-- empty module (outer loop runs zero times), empty index (inner loop runs zero
times), both empty, single code point, the exact F2P shape (`TypeVar('T')`, the
`mock.SomeClass[T]` index from the issue), covariant/contravariant TypeVars,
classes, ints, floats, None, bool, list/tuple/dict/bytes indices (`key_is_text ==
False`), non-ASCII and space/tab-bearing textual indices, NUL/surrogate-bearing
modules -- then seeded fuzz to fill the count.  Both branches of `key_is_text`
and both loop-taken/loop-skipped shapes are covered by the boundary block.

Every generated sample is asserted to satisfy `Requires` before use, and the
`@ContractOnly` shim re-asserts the axiom's own precondition, so a bridge bug
surfaces as exit 2 rather than as a silent pass or a bogus disagreement.

Pinned seed: 7889 (recorded in mapping.md §"G-CONF").  Exit 0 iff zero
disagreements over >= 1e5 Requires-satisfying inputs; on a disagreement the
input and both outputs are printed and the exit code is 1.  stdlib + the repo
module under test only.
"""
import json
import random
import sys
from typing import List, TypeVar  # List: used by the verbatim `# type:` comment

from sphinx.ext.autodoc.mock import _MockObject, _make_subclass

SEED = 7889
N_FUZZ = 100_000
MAX_REPORT = 5


class PreconditionViolation(Exception):
    """Raised when a generated input misses the model's Requires (script bug)."""


# --- PSeq shim: immutable sequence, the operations the model region uses ------

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

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- type bridge (mapping.md section 2) --------------------------------------

def cps(s):
    """str -> List[int] of Unicode code points."""
    return [ord(c) for c in s]


def text(codepoints):
    """List[int] / PSeq[int] of code points -> str."""
    return "".join(chr(c) for c in codepoints)


def seq_text(seq):
    return "".join(chr(seq[k]) for k in range(len(seq)))


def in_requires(key_text):
    """The model's Requires on the index's textual rendering: no NUL code point
    and no surrogate code point (55296..57343)."""
    return 0 not in key_text and not any(
        55296 <= c <= 57343 for c in key_text)


# --- @ContractOnly callee: call the REAL repo function it axiomatizes ---------
# model.py's `display_name(name_is_text, name, module)` abstracts
# sphinx.ext.autodoc.mock._make_subclass (mock.py:71-76, unchanged by the patch).
# It has no body to copy, so the axiom is EXERCISED here rather than assumed.

_TRACE = {}


def display_name(name_is_text, name, module):
    if not name_is_text:
        raise PreconditionViolation("display_name called with name_is_text=False")
    name_s = seq_text(name)
    if "\x00" in name_s:
        raise PreconditionViolation("axiom precondition: NUL in name %r" % (name_s,))
    if any(0xD800 <= ord(c) <= 0xDFFF for c in name_s):
        raise PreconditionViolation(
            "axiom precondition: surrogate in name %r" % (name_s,))
    module_s = seq_text(module)
    cls = _make_subclass(name_s, module_s)          # THE REAL REPO CALLEE
    produced = ToSeq(cps(cls.__display_name__))
    _TRACE["produced"] = produced
    return produced


# --- @Pure helper from model.py's pure region, contracts stripped -------------

def render_text(value_text):
    """Canonical textual rendering of a value, as the code-point sequence of
    its text.  Rendering is the identity on the text content (every value
    already carries its canonical textual form here); crucially its result is
    always textual, regardless of whether the value itself was textual."""
    return value_text


# --- SHADOW: model.py's impl region, verbatim, contract calls stripped -------

def subscript_placeholder(key_is_text, key_text, module):
    # Reduce the index to its textual rendering FIRST, so the string-only
    # fabricator receives an honest string for EVERY index.  The rendering is
    # always textual, so the fabricator's textual precondition (name_is_text)
    # is met unconditionally -- independent of key_is_text.
    name_is_text = True
    name = render_text(ToSeq(key_text))
    # Hand the (now textual) name to the fabricator; its textual precondition
    # name_is_text is discharged here.  This call is the operation that fails
    # for a non-textual name argument.
    produced = display_name(name_is_text, name, ToSeq(module))
    # Materialise the display name the fabricator describes.
    result = []  # type: List[int]
    i = 0
    while i < len(module):
        result = result + [module[i]]
        i = i + 1
    result = result + [46]
    j = 0
    while j < len(key_text):
        result = result + [key_text[j]]
        j = j + 1
    return result


# --- ORACLE: the REAL patched _MockObject.__getitem__ ------------------------

def parent_placeholder(module):
    """A placeholder whose self.__display_name__ is `module`, built the way the
    repo builds one (_make_subclass's own `type(name, (superclass,), attrs)`)."""
    cls = type("_ConfParent", (_MockObject,),
               {"__module__": module, "__display_name__": module})
    return cls()


def oracle(module, key):
    """Drive the patched subscript (mock.py:56 post-patch) and observe the
    display name of the placeholder it returns."""
    inst = parent_placeholder(module)[key]      # patched __getitem__
    return cps(type(inst).__display_name__)


# --- differential -------------------------------------------------------------

def run_shadow(module_cp, key_is_text, key_text):
    _TRACE.pop("produced", None)
    try:
        result = subscript_placeholder(key_is_text, list(key_text),
                                       list(module_cp))
    except PreconditionViolation:
        raise
    except Exception as exc:                    # mirror the oracle's failure mode
        return ("err", type(exc).__name__), ("err", type(exc).__name__)
    produced = _TRACE.get("produced")
    axiom = ("ok", list(produced._t)) if produced is not None else ("missing", None)
    return ("ok", result), axiom


def run_oracle(module, key):
    try:
        return ("ok", oracle(module, key))
    except Exception as exc:                    # noqa: BLE001 - compared, not swallowed
        return ("err", type(exc).__name__)


def check(module, key, failures):
    """One differential sample.  Returns False if the input misses Requires."""
    key_s = str(key)
    key_text = cps(key_s)
    module_cp = cps(module)
    if not in_requires(key_text):
        return False
    key_is_text = isinstance(key, str)
    shadow, axiom = run_shadow(module_cp, key_is_text, key_text)
    got = run_oracle(module, key)
    if shadow != got or (axiom[0] == "ok" and axiom != got):
        failures.append({
            "module": repr(module),
            "key": repr(key),
            "key_is_text": key_is_text,
            "model_key_text": key_text,
            "shadow_result": shadow if shadow[0] == "err" else text(shadow[1]),
            "shadow_axiom_produced": (axiom if axiom[0] != "ok"
                                      else text(axiom[1])),
            "oracle": got if got[0] == "err" else text(got[1]),
        })
    return True


# --- inputs -------------------------------------------------------------------

T = TypeVar("T")
S_CO = TypeVar("S_CO", covariant=True)
S_CONTRA = TypeVar("S_CONTRA", contravariant=True)

# `module` is unconstrained by Requires, so NUL/surrogate-bearing modules are
# deliberately included: the real callee only concatenates `module`, so both
# sides must still agree.
BOUNDARY_MODULES = [
    "",                       # outer while loop runs zero times
    "m",                      # single code point
    "mod",
    "pkg.sub.mod",
    "_MockObject",
    "☃",                 # non-ASCII
    "a" * 32,
    "mo\x00d",                # NUL in module: legal here (name is what type() checks)
    "mod\ud800",              # lone surrogate in module: likewise legal
]

BOUNDARY_KEYS = [
    "",                       # inner while loop runs zero times
    "x",                      # single code point
    "T",
    "SomeClass",
    "a.b.c",
    "name with spaces",
    "tab\there",
    "~T",
    "9",
    "list",
    "café",
    "已",
    "•",
    "x" * 32,
    T,                        # the F2P shape: mock.SomeClass[T]
    S_CO,
    S_CONTRA,
    int,
    str,
    object,
    type,
    0,
    -1,
    2 ** 70,
    3.14,
    float("inf"),
    None,
    True,
    False,
    ["a", "b"],
    ("a",),
    (),
    {"k": "v"},
    frozenset({1}),
    b"bytes",
    1 + 2j,
]

_MOD_ALPHABET = list("abcDEF0123_.- TZ~*/:") + [
    "é", "•", "☃", "\x01", "\x1f", "\x00", "\ud800", "\udfff"]
# The key alphabet omits NUL and surrogates: those renderings are outside the
# model's Requires (see the docstring), not routed around for convenience.
_KEY_ALPHABET = list("abcDEF0123_.- TZ~*/:") + [
    "é", "•", "☃", "\x01", "\x1f", "\t", "\n", "\x7f"]

_NONTEXT_POOL = [
    T, S_CO, S_CONTRA, int, str, object, type, dict,
    0, 1, -7, 12345, 2 ** 65, 3.5, -0.0, float("inf"),
    None, True, False, (1, 2), (), ["a"], {"k": 1}, frozenset(), b"b", 1j,
    Ellipsis, NotImplemented, range(3), slice(1, 2),
]


def boundary_inputs():
    for module in BOUNDARY_MODULES:
        for key in BOUNDARY_KEYS:
            yield module, key


def fuzz_inputs(n, rng):
    for _ in range(n):
        ml = rng.randint(0, 12)
        module = "".join(rng.choice(_MOD_ALPHABET) for _ in range(ml))
        if rng.random() < 0.5:
            kl = rng.randint(0, 14)
            key = "".join(rng.choice(_KEY_ALPHABET) for _ in range(kl))
        elif rng.random() < 0.4:
            key = TypeVar("V%d" % rng.randint(0, 99999))
        else:
            key = rng.choice(_NONTEXT_POOL)
        yield module, key


def main():
    rng = random.Random(SEED)
    failures = []
    checked = 0
    skipped = 0
    text_keys = 0

    try:
        for module, key in boundary_inputs():
            if check(module, key, failures):
                checked += 1
                text_keys += isinstance(key, str)
            else:
                skipped += 1
            if len(failures) >= MAX_REPORT:
                break
        if len(failures) < MAX_REPORT:
            for module, key in fuzz_inputs(N_FUZZ, rng):
                if check(module, key, failures):
                    checked += 1
                    text_keys += isinstance(key, str)
                else:
                    skipped += 1
                if len(failures) >= MAX_REPORT:
                    break
    except PreconditionViolation as exc:
        print("G-CONF SCRIPT BUG: generated input misses the model Requires: %s"
              % (exc,))
        print(json.dumps({"status": "error", "reason": "precondition-violation",
                          "detail": str(exc)}))
        return 2

    if failures:
        print("G-CONF FAIL: %d disagreement(s) between the model shadow and the "
              "real patched _MockObject.__getitem__ over %d inputs (seed=%d):"
              % (len(failures), checked, SEED))
        for f in failures:
            print("  module=%s key=%s key_is_text=%s" %
                  (f["module"], f["key"], f["key_is_text"]))
            print("    shadow (impl region)      = %r" % (f["shadow_result"],))
            print("    shadow (axiom produced)   = %r" %
                  (f["shadow_axiom_produced"],))
            print("    oracle (patched __getitem__) = %r" % (f["oracle"],))
        print(json.dumps({"status": "fail", "checked": checked,
                          "disagreements": len(failures), "seed": SEED}))
        return 1

    print("G-CONF OK: model.py impl region (verbatim, contracts stripped; "
          "@ContractOnly display_name -> real _make_subclass) agrees with the "
          "real patched sphinx.ext.autodoc.mock._MockObject.__getitem__ on "
          "%d Requires-satisfying inputs (%d boundary + fuzz, seed=%d): "
          "0 disagreements on both the loop-materialised display name and the "
          "axiom's own output. %d out-of-domain samples skipped."
          % (checked, len(BOUNDARY_MODULES) * len(BOUNDARY_KEYS), SEED, skipped))
    print(json.dumps({
        "status": "pass",
        "checked": checked,
        "disagreements": 0,
        "skipped_out_of_domain": skipped,
        "textual_keys": text_keys,
        "nontextual_keys": checked - text_keys,
        "seed": SEED,
        "shadow": "model.py impl-start..impl-end verbatim, contracts stripped",
        "oracle": "sphinx.ext.autodoc.mock._MockObject.__getitem__ (called, patched)",
        "unsupported": [],
        "summary": ("impl region vs real patched __getitem__: %d inputs, "
                    "0 disagreements (seed=%d)" % (checked, SEED)),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
