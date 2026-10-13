#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""G-CONF differential conformance check for psf__requests-1724 (nagini).

Refutes (never proves) the refinement leg: does the MODEL agree with the REAL
patched repository code it claims to model?  No other gate covers this leg.

RUNTIME
-------
The instance image for this bundle runs **Python 2.7.18** (conda env `testbed`
at /testbed) -- which is the whole point of the behaviour under specification:
the reported failure is a Python-2 one, and the native/non-native text split
this check compares is `str` vs `unicode`, a distinction that only *exists* on
Python 2.  This script is therefore written to the Python-2 language (no
`typing` import -- not in the 2.7 stdlib and the impl region's `List[int]` is a
type *comment*; no underscore numeric literals; explicit `coding:` declaration
for the prose below) so that the comparison actually executes on the
interpreter that hosts the real code.

SHADOW
------
The impl region of `model.py` `normalize_method`, copied VERBATIM below with
only the contract calls removed (`Requires` / `Ensures` / `Invariant` /
`Assert` and the `# invariants-start|end` markers).  The loop structure, the
backward index walk, the `out = [upper_cp(c)] + out` prepend and the
`TextToken(out, native_flavour)` construction are byte-for-byte the model's --
no restructuring, no renaming, no "simplification".  The two `@Pure` helpers
the model defines in its pure region (`upper_cp`, `upper_seq`) are copied over
with their contracts stripped; `upper_cp` is the one the impl region calls,
`upper_seq` (the front-recursive fold the postcondition is phrased over) is
copied too and checked against the same oracle as a second, loop-independent
path through the `PSeq` shim.

Nagini carriers are realized by shims: `PSeq` is an immutable sequence with
`take` / `drop` / `+` / `len` / `[]` / `==`, and `ToSeq(list)` materializes one
(same shape as the other nagini bundles in this corpus).

The one `@ContractOnly` callee, `to_native` (model.py axioms region), has no
body to copy, so it is NOT stubbed to its axiom `Ensures(native_form(Result()))`.
It calls the REAL callee mapping.md 3.1 names -- `requests.compat.builtin_str`
-- on the real supplied text value at its real supplied flavour, and returns
the flavour predicate the axiom asserts (`type(builtin_str(v)) is builtin_str`).
So the axiom is EXERCISED here rather than assumed: if `builtin_str` ever
failed to produce a native value the shadow's `native_flavour` would go False
and the flavour comparison below would fail.

ORACLE  (called, not transliterated)
------------------------------------
The REAL patched repo function, per mapping.md 1: the method-handling step of
`requests.sessions.Session.request` (`requests/sessions.py:278`, body at
312-314 pre-patch; the gold patch inserts `method = builtin_str(method)` right
before `Request(method = method.upper(), ...)`).  The gate applies patch.diff
to /testbed and sets PYTHONPATH before this script runs, so the patched module
is the one imported -- asserted at startup (`_assert_patched`), which makes an
unpatched container an error instead of a silent green.

The function is DRIVEN, not reimplemented: a real `Session` is built, the real
`Session.request` is invoked with the generated method, and the observable is
read out of the real `Request` object that the real code constructs.  Only two
things are intercepted, both strictly downstream of the modeled step:

  * `Session.prepare_request` is wrapped to capture the `Request.method` field
    the modeled step produced -- this IS the modeled observable (mapping.md 2:
    "projection onto the `method` field only") -- and then delegates to the
    real unchanged `prepare_request`, so nothing upstream is short-circuited.
  * `Session.send` is stubbed to a sentinel, because the modeled step is
    complete before `send` and a live socket is neither available nor relevant.

No line of the patched function is copied into this file.

TYPE BRIDGE  (mapping.md 2, inverted)
--------------------------------------
The model works over the abstract carrier `TextToken` = (`chars: List[int]` of
Unicode code points, `native: bool`); the repo wants a text value.  Inverting:
`chars` -> the text with those code points, and the flavour bit selects the
runtime flavour of that text.  On the Python-2 runtime this is exact and needs
no stand-in: `native=True` -> the native byte-`str` (what `builtin_str` is,
`requests/compat.py:95`), `native=False` -> `unicode`, which is precisely the
flavour mapping.md 2 pairs with `native == False` and precisely the flavour the
reported failure supplies (`method=u'POST'`).  Reading back, the real carried
method `m` maps to `TextToken([ord(ch) for ch in m], type(m) is builtin_str)`.
Generation runs in the abstract direction (code-point lists), so every
generated input satisfies the model's `Requires` (`Acc(list_pred(chars), 1/2)`
-- any list of ints) by construction.

Both postconditions are compared, per input:
  (1) content -- the carried method's code points == the shadow's `out` list,
      and the length is preserved;
  (2) flavour -- the carried method's nativeness == the shadow's carried
      `native` bit, for BOTH supplied flavours.  This is the aspect the bug is
      about, so a shadow that only checked content would pass on the prepatch
      behaviour too.  The model's flavour clause is
      `Result().native == to_native(ToSeq(chars))` and the shadow's `to_native`
      calls the real `builtin_str`, so this comparison is against the real
      carried flavour, never against a constant.

INPUT DOMAIN
------------
Code points 0..127.  This is the domain over which mapping.md 3.2 states the
`upper_seq` deep model claims faithfulness to the unchanged `str.upper`
callee, and it is a strict superset of the RFC-7230 method-token alphabet the
behaviour under specification inhabits.  Not a convenience restriction, and
not a dodge around an unknown: the full-Unicode divergence is a KNOWN and
pre-recorded boundary of the frozen model (mapping.md 3.2, meta.json
`deep_model_references`, G-AX), and its witnesses are concrete -- U+00E9 ->
U+00C9, U+00DF -> 'SS', U+00B5 -> U+039C, U+0131 -> 'I' are real `str.upper`
results the per-code-point ASCII map does not produce.  Those code points are
not method tokens and are unreachable from the modeled call site's tested
behaviour; they are reported in the structured report below as a declared
domain boundary rather than silently avoided.

Over that domain the check is EXHAUSTIVE up to length 2 in both flavours --
every length-0 and length-1 input (2 + 256 cases) and every one of the 128x128
length-2 inputs in each flavour (32768 cases) -- which pins every branch of the
impl region: the `while` loop entered zero times (empty input), once, twice;
`upper_cp` on an ASCII lowercase letter and on a non-letter code point at
every position; and `to_native` on a native and on a non-native argument.
Seeded fuzz over the same domain (lengths 0..24) then fills the count past
1e5.  Exhaustive-then-fuzz on the same space is a stronger check than 1e5
samples alone, not a weaker one.

Exit 0 iff zero disagreements; on a disagreement the input and both outputs
are printed and the exit is 1.  stdlib only, seed pinned (mapping.md G-CONF).
"""
import json
import random
import sys

SEED = 17242026
N_FUZZ = 70000
MAX_FUZZ_LEN = 24
MAX_REPORTED = 5

# --- the real callees (mapping.md 1/3.1); patched module via PYTHONPATH ------

from requests.compat import builtin_str as REAL_BUILTIN_STR   # noqa: E402
import requests.sessions as REAL_SESSIONS                     # noqa: E402


# --- native / non-native text flavour on the running interpreter -------------
# On Python 2 (the runtime of this instance image, and of the reported failure)
# both flavours are primitive builtins: byte-`str` is native, `unicode` is not.
# The py3 branch keeps the script runnable off-image; there `builtin_str is
# str`, so the non-native flavour has no builtin inhabitant and UserString --
# a text value that is not `builtin_str` -- stands in for py2's `unicode`.
_PY2 = sys.version_info[0] == 2

if _PY2:
    _NONNATIVE_NAME = "unicode"

    def _mk_native(chars):
        return REAL_BUILTIN_STR("".join(chr(c) for c in chars))

    def _mk_nonnative(chars):
        return u"".join(unichr(c) for c in chars)     # noqa: F821  (py2 builtin)
else:
    from collections import UserString
    _NONNATIVE_NAME = "collections.UserString"

    def _mk_native(chars):
        return REAL_BUILTIN_STR("".join(chr(c) for c in chars))

    def _mk_nonnative(chars):
        return UserString("".join(chr(c) for c in chars))


# --- PSeq shim: immutable sequence, the operations the model region uses -----

class PSeq(object):
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

    def __ne__(self, other):          # py2 does not derive __ne__ from __eq__
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    """Materialize a list as a pure sequence (the Nagini `ToSeq` bridge)."""
    return PSeq._wrap(lst)


# --- TextToken, from model.py, contracts stripped ----------------------------

class TextToken(object):
    def __init__(self, chars, native):
        self.chars = chars
        self.native = native


# --- type bridge: mapping.md 2 inverted -------------------------------------

def to_repo_text(chars, native):
    """Abstract carrier -> the real text value the repo function wants.

    `chars` (code points) becomes the character content; `native` selects the
    runtime flavour: the native `builtin_str` value, or the non-native text
    flavour (py2 `unicode`; see the module docstring)."""
    if native:
        return _mk_native(chars)
    return _mk_nonnative(chars)


def from_repo_text(value):
    """The real carried method -> the abstract carrier (chars, native)."""
    return [ord(ch) for ch in value], type(value) is REAL_BUILTIN_STR


# --- the @ContractOnly callee, realized by its REAL callee (mapping.md 3.1) --

# The supplied flavour of the value currently being normalized. The model's
# `to_native(ToSeq(chars))` sees only the content (the flavour of its argument
# is deliberately not in the carrier), but the axiom's whole claim is that the
# result is native INDEPENDENT of the argument flavour -- so the shim below
# reconstitutes the real supplied value at its real supplied flavour and hands
# THAT to the real callee. Set by the driver, read only here.
_SUPPLIED_NATIVE = [True]


def to_native(chars):
    """`to_native` has no body in model.py (@Pure @ContractOnly). Rather than
    assume its axiom `Ensures(native_form(Result()))`, call the REAL callee it
    axiomatizes -- `requests.compat.builtin_str` -- on the real supplied value
    and return the flavour predicate the axiom asserts."""
    supplied = to_repo_text(list(chars), _SUPPLIED_NATIVE[0])
    produced = REAL_BUILTIN_STR(supplied)
    return type(produced) is REAL_BUILTIN_STR


# --- model.py pure region, verbatim, contracts stripped ----------------------

def upper_cp(c):
    """Case-normalisation of a single code point: an ASCII lowercase letter
    maps to its uppercase partner; every other code point is unchanged."""
    if 97 <= c and c <= 122:   # 'a'..'z'  ->  'A'..'Z'
        return c - 32
    return c


def upper_seq(s):
    """Case-normalisation of a whole sequence: the per-code-point upper map.
    Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(upper_cp(s[0])) + upper_seq(s.drop(1))


# --- model.py impl region, VERBATIM, contract calls stripped -----------------

def normalize_method(chars, native):
    # impl-start
    native_flavour = to_native(ToSeq(chars))
    out = []  # type: List[int]
    i = len(chars)
    while i > 0:
        c = chars[i - 1]
        out = [upper_cp(c)] + out
        i = i - 1
    return TextToken(out, native_flavour)
    # impl-end


# --- oracle: drive the REAL patched Session.request -------------------------

_CAPTURED = {}


def _install_oracle():
    """Wrap the two members strictly downstream of the modeled step: capture
    the `Request.method` the real patched code constructs, and stub the wire.
    The modeled step itself (`method = builtin_str(method)` then
    `Request(method = method.upper(), ...)`) runs untouched."""
    real_prepare_request = REAL_SESSIONS.Session.prepare_request

    def capturing_prepare_request(self, request):
        _CAPTURED["method"] = request.method       # the modeled observable
        return real_prepare_request(self, request)

    REAL_SESSIONS.Session.prepare_request = capturing_prepare_request
    REAL_SESSIONS.Session.send = lambda self, prep, **kw: _SENT
    session = REAL_SESSIONS.Session()
    session.trust_env = False                     # no environment proxies/netrc
    return session


_SENT = object()
_ORACLE_URL = "http://conf.invalid/p"


def oracle(session, method_value):
    """Call the REAL patched repo function and read back the carried method."""
    _CAPTURED.pop("method", None)
    got = session.request(method_value, _ORACLE_URL)
    if got is not _SENT or "method" not in _CAPTURED:
        raise RuntimeError("oracle did not reach the capture point")
    return _CAPTURED["method"]


def _assert_patched():
    """The oracle is the PATCHED function; refuse to certify anything if the
    gate's patch did not land (a silent unpatched run would be a green that
    checks the wrong program)."""
    import inspect
    src = inspect.getsource(REAL_SESSIONS.Session.request)
    if "builtin_str(method)" not in src:
        print("G-CONF ERROR: requests.sessions.Session.request is NOT patched "
              "(no `builtin_str(method)` coercion in its source); the oracle "
              "would be the prepatch function.")
        sys.exit(2)


def _assert_flavours_distinct():
    """The non-native flavour must really be non-native on this interpreter,
    else the flavour comparison is vacuous (it would pass on the prepatch
    behaviour too) -- an error, never a silent green."""
    probe = [ord("p"), ord("o")]
    if type(to_repo_text(probe, False)) is REAL_BUILTIN_STR:
        print("G-CONF ERROR: the non-native flavour carrier (%s) IS "
              "builtin_str on this interpreter; the flavour observable would "
              "be vacuous." % _NONNATIVE_NAME)
        sys.exit(2)


# --- inputs: >= 1e5 satisfying the model's Requires -------------------------

ASCII = range(0, 128)
TOKENY = [ord(c) for c in
          "getpostGETPOSTputPUTdeleteheadoptionspatchtraceconnect0123456789-_."]


def inputs(rng):
    """(chars, native) pairs. Exhaustive to length 2 over the ASCII domain in
    both flavours, then seeded fuzz over the same domain."""
    for native in (True, False):
        yield [], native                                  # loop entered 0x
        for c in ASCII:
            yield [c], native                             # loop entered 1x
        for a in ASCII:
            for b in ASCII:
                yield [a, b], native                      # loop entered 2x
    for _ in range(N_FUZZ):
        n = rng.randint(0, MAX_FUZZ_LEN)
        if rng.random() < 0.5:
            chars = [rng.choice(TOKENY) for _ in range(n)]
        else:
            chars = [rng.randrange(0, 128) for _ in range(n)]
        yield chars, rng.random() < 0.5


def main():
    _assert_patched()
    _assert_flavours_distinct()
    session = _install_oracle()
    rng = random.Random(SEED)

    checked = 0
    disagreements = 0
    n_native = 0

    for chars, native in inputs(rng):
        # --- shadow: the model's impl region over the abstract carrier
        _SUPPLIED_NATIVE[0] = native
        shadow = normalize_method(list(chars), native)

        # --- oracle: the real patched repo function over the real value
        real = oracle(session, to_repo_text(chars, native))
        real_chars, real_native = from_repo_text(real)

        checked += 1
        n_native += 1 if native else 0
        bad = []
        # (1) content + length preservation
        if shadow.chars != real_chars:
            bad.append("content")
        if len(shadow.chars) != len(chars):
            bad.append("length")
        # (2) flavour -- the aspect the behaviour under specification is about
        if shadow.native != real_native:
            bad.append("flavour")
        # the loop-independent pure fold must agree with the same oracle
        if upper_seq(ToSeq(list(chars))) != ToSeq(real_chars):
            bad.append("upper_seq")

        if bad:
            disagreements += 1
            if disagreements <= MAX_REPORTED:
                print("DISAGREEMENT (%s): input chars=%r native=%r "
                      "supplied=%r\n  shadow: chars=%r native=%r\n"
                      "  oracle: chars=%r native=%r (value=%r type=%s)"
                      % (",".join(bad), chars, native,
                         to_repo_text(chars, native),
                         shadow.chars, shadow.native,
                         real_chars, real_native, real, type(real).__name__))

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d)."
              % (disagreements, checked, SEED))
        print(json.dumps({"checked": checked, "disagreements": disagreements,
                          "seed": SEED, "status": "fail"}))
        return 1

    print("G-CONF OK: shadow of model.py normalize_method (impl region "
          "verbatim; to_native -> real requests.compat.builtin_str) agrees "
          "with the real patched requests.sessions.Session.request method "
          "step on %d inputs (%d native / %d non-native supplied flavour; "
          "exhaustive over ASCII code points 0-127 up to length 2 in both "
          "flavours + %d seeded fuzz, seed=%d) in content, length and "
          "flavour; 0 disagreements."
          % (checked, n_native, checked - n_native, N_FUZZ, SEED))
    print(json.dumps({
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "runtime": "python%d.%d" % sys.version_info[:2],
        "oracle": "requests.sessions.Session.request (patched, called)",
        "shadow": "model.py impl region verbatim; @ContractOnly to_native -> "
                  "real requests.compat.builtin_str",
        "observables": ["content", "length", "flavour"],
        "nonnative_flavour": _NONNATIVE_NAME,
        "domain": "ASCII code points 0-127 x {native, non-native} flavour; "
                  "exhaustive to length 2, fuzz to length 24",
        "declared_domain_boundary": "non-ASCII code points: the frozen "
                                    "upper_seq deep model claims faithfulness "
                                    "only on ASCII (mapping.md 3.2 / G-AX); "
                                    "real str.upper diverges there "
                                    "(U+00DF -> 'SS'), and such code points "
                                    "are not RFC-7230 method tokens",
        "status": "pass",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
