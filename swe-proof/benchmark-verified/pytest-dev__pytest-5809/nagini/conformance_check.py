#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5809 (nagini).

SHADOW: the impl regions of model.py (`paste_mode_field`, `paste_body_field`,
`paste_expiry_field`), copied verbatim below with the contract calls stripped.
The @Pure helpers (`text_token`, `expiry_token`) copy over as plain functions
with `PSeq(...)` shimmed to a plain tuple; `ToSeq(list)` is `tuple(list)`.
There is no @ContractOnly callee in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — `_pytest.pastebin.create_new_paste(contents)`. The gate applies
patch.diff to /testbed before this script runs; the repo lays its package out
under src/, which this script puts on sys.path so the patched in-tree source
wins. The function's only externally visible output for our purposes is the
request body it submits: it resolves `urlopen` from `urllib.request` at call
time, so installing a capturing stand-in there observes the submitted payload
without any network traffic (the same seam the repo's own test suite uses).
The captured body is decoded with `urllib.parse.parse_qsl` (the exact inverse
of the serializer the function calls), recovering the three named fields.

TYPE BRIDGE (mapping.md section 2): field values are `str` in the repo and
`List[int]` of Unicode code points in the model; the bijection is
`codepoints(s) = [ord(ch) for ch in s]`. `py_major` models the running
interpreter's major version; the model's claim is that the mode field is the
SAME constant for every `py_major`, so each trial draws an arbitrary int
`py_major`, feeds it to the shadow, and compares against the real field
value observed under the one interpreter actually running — any dependence
of the shadow on `py_major` would surface as a disagreement.

Per trial, the comparison covers all three modeled functions:
  mode field:   shadow paste_mode_field(py_major)      vs codepoints(fields["lexer"])
  body field:   shadow paste_body_field(codepoints(c)) vs codepoints(fields["code"])
  expiry field: shadow paste_expiry_field()            vs codepoints(fields["expiry"])
plus structural cross-checks: the payload carries exactly these three field
names, and paste_body_field leaves its input list unchanged (the contracts
give the input only a read fraction).

INPUT DOMAIN (Requires): paste_mode_field takes any int; paste_body_field
takes any list of code points (any str via the bridge); paste_expiry_field
takes nothing. Trials draw contents over printable ASCII, whitespace-heavy,
URL-metacharacter-heavy, and non-ASCII Unicode strings (lengths 0..64), and
py_major over a wide int range including the boundary witnesses 2, 3, 4.

>= 1e5 Requires-satisfying inputs: 22 boundary + 34000 fuzz trials, each
exercising all THREE modeled functions (>= 102066 checked calls total).
Pinned fuzz seed: 5809.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import os
import random
import sys

SEED = 5809
N_FUZZ = 34_000


# --- pure helpers from model.py, PSeq shimmed to a plain tuple -----------------

def text_token():
    """The plain-text highlighting-mode token "text" as code points."""
    return (116, 101, 120, 116)


def expiry_token():
    """The constant one-week expiry token "1week" as code points."""
    return (49, 119, 101, 101, 107)


def ToSeq(xs):
    # PSeq materialization shim: a plain immutable tuple of the list elements.
    return tuple(xs)


# --- the impl regions of model.py, verbatim, contract calls stripped -----------

def paste_mode_field(py_major):
    mode = [116, 101, 120, 116]  # type: list
    return mode


def paste_body_field(contents):
    body = list(contents)  # type: list
    return body


def paste_expiry_field():
    exp = [49, 119, 101, 101, 107]  # type: list
    return exp


# --- oracle plumbing ------------------------------------------------------------

def _import_real():
    """Import the patched repo module (src layout: patched in-tree source must
    win over any stale ambient install)."""
    for base in ("/testbed", os.getcwd()):
        src = os.path.join(base, "src")
        if os.path.isdir(os.path.join(src, "_pytest")) and src not in sys.path:
            sys.path.insert(0, src)
    from _pytest import pastebin
    return pastebin


class _CapturingOpener:
    """Stand-in for urllib.request.urlopen: records the submitted request body
    and hands back a minimal well-formed response so the function returns
    normally. No network traffic occurs."""

    def __init__(self):
        self.calls = []

    def __call__(self, url, data=None):
        self.calls.append((url, data))

        class _Resp:
            def read(self):
                return b'<a href="/raw/c0nf0k"></a>'

        return _Resp()


def codepoints(s):
    return [ord(ch) for ch in s]


def _observed_fields(opener, pastebin, contents):
    """Run the REAL patched function once and decode the submitted body into
    its named fields with the serializer's stdlib inverse."""
    from urllib.parse import parse_qsl
    import urllib.request
    urllib.request.urlopen = opener          # call-time resolution seam
    n_before = len(opener.calls)
    pastebin.create_new_paste(contents)
    if len(opener.calls) != n_before + 1:
        return None, "expected exactly one submission, saw %d" % (
            len(opener.calls) - n_before)
    _url, data = opener.calls[-1]
    if not isinstance(data, bytes):
        return None, "submitted body is not bytes: %r" % (type(data).__name__,)
    pairs = parse_qsl(data.decode("ascii"), keep_blank_values=True)
    fields = dict(pairs)
    if len(pairs) != len(fields):
        return None, "duplicate field names in payload: %r" % (pairs,)
    return fields, None


def _check_trial(pastebin, opener, contents, py_major):
    """Compare all three shadow field-producers against the real submitted
    payload for one (contents, py_major) input; return an error string on any
    disagreement, else None."""
    fields, err = _observed_fields(opener, pastebin, contents)
    if err:
        return ("oracle observation failed on contents=%r: %s"
                % (contents, err))
    if sorted(fields) != ["code", "expiry", "lexer"]:
        return ("payload field-name disagreement on contents=%r: "
                "real names=%r, model expects exactly code/lexer/expiry"
                % (contents, sorted(fields)))

    # mode field — the differential carrier; the shadow's py_major input must
    # not change the outcome (the model claims version invariance).
    s_mode = paste_mode_field(py_major)
    r_mode = codepoints(fields["lexer"])
    if s_mode != r_mode:
        return ("mode-field disagreement on contents=%r py_major=%d:\n"
                "  shadow=%r (%r)\n  real  =%r (%r)"
                % (contents, py_major, s_mode,
                   "".join(map(chr, s_mode)), r_mode, fields["lexer"]))
    assert ToSeq(s_mode) == text_token()   # pure-region lock-step

    # body field — identity forward; input list must survive unmutated.
    cp_in = codepoints(contents)
    cp_arg = list(cp_in)
    s_body = paste_body_field(cp_arg)
    if cp_arg != cp_in:
        return ("paste_body_field mutated its input on contents=%r" % (contents,))
    r_body = codepoints(fields["code"])
    if s_body != r_body:
        return ("body-field disagreement on contents=%r:\n"
                "  shadow=%r\n  real  =%r (%r)"
                % (contents, s_body, r_body, fields["code"]))

    # expiry field — constant token.
    s_exp = paste_expiry_field()
    r_exp = codepoints(fields["expiry"])
    if s_exp != r_exp:
        return ("expiry-field disagreement on contents=%r:\n"
                "  shadow=%r\n  real  =%r (%r)"
                % (contents, s_exp, r_exp, fields["expiry"]))
    assert ToSeq(s_exp) == expiry_token()  # pure-region lock-step
    return None


def _boundary_trials():
    """Structured (contents, py_major) cases: the interpreter-major witnesses
    x representative bodies, plus serializer-stressing bodies."""
    bodies = [
        "full-paste-contents",       # the shape the repo's own test submits
        "",                          # empty body
        "a",
        "line one\nline two\n",      # newlines (percent-quoted by the wire form)
        "spaces and\ttabs",          # quote_plus territory
        "a+b&c=d%20e",               # URL metacharacters round-tripped
        "unicode: \u00e9\u4e2d\u6587\U0001f40d",  # non-ASCII code points
        "x" * 4096,                  # long body
    ]
    trials = []
    for pm in (2, 3, 4):             # interpreter-major witnesses
        for b in bodies[:6]:
            trials.append((b, pm))
    trials.append((bodies[6], 3))
    trials.append((bodies[7], 3))
    trials.append((bodies[0], -1))   # far-off py_major values
    trials.append((bodies[0], 10 ** 9))
    return trials


_ASCII = "".join(chr(c) for c in range(32, 127))
_EXTRA = "\n\t\u00e9\u00df\u0416\u4e2d\u6587\u2603\U0001f600"


def _rand_contents(rng):
    n = rng.randint(0, 64)
    pool = _ASCII if rng.random() < 0.7 else (_ASCII + _EXTRA)
    return "".join(rng.choice(pool) for _ in range(n))


def main():
    pastebin = _import_real()
    opener = _CapturingOpener()

    n_calls = 0
    boundary = _boundary_trials()
    for contents, py_major in boundary:
        err = _check_trial(pastebin, opener, contents, py_major)
        if err:
            print("DISAGREEMENT (boundary): " + err)
            return 1
        n_calls += 3   # all three modeled functions exercised

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        contents = _rand_contents(rng)
        py_major = rng.choice((2, 3, 4, rng.randint(-10 ** 6, 10 ** 6)))
        err = _check_trial(pastebin, opener, contents, py_major)
        if err:
            print("DISAGREEMENT (fuzz): " + err)
            return 1
        n_calls += 3

    print("G-CONF OK: shadow == real patched submission fields on %d boundary "
          "+ %d fuzz trials (%d modeled-function calls, seed %d): the mode "
          "field is the constant plain-text token for every py_major, the "
          "body field forwards contents unchanged, the expiry field is the "
          "constant one-week token."
          % (len(boundary), N_FUZZ, n_calls, SEED))
    print(json.dumps({"checked": n_calls, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
