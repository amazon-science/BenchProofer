#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7985 (nagini).

SHADOW: the impl regions of model.py (`starts_with`, `scheme_present`,
`check`), copied verbatim below with the contract calls (Requires / Ensures /
Invariant / Assert) stripped.  The @Pure status-code helpers (`UNCHECKED`,
`WORKING`, `MISSING`, `IGNORED`) copy over as plain functions; the remaining
pure symbols (`prefix_eq`, `lower_run`, `has_uri_scheme`, `classify`, the
PSeq literals and the inductive lemmas) appear only inside contracts and
stripped Assert lines, so they carry no runtime content here.  There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
the nested `check()` of
`sphinx.builders.linkcheck.CheckExternalLinksBuilder.check_thread`.  The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched module importable.  The nested function's code object is
pulled out of `check_thread.__code__.co_consts` and materialized with the
module's own globals (so `uri_re` and `path` resolve exactly as in the repo)
and a per-case closure supplying its three free variables:

  * `uri`        — the target string under test;
  * `self`       — a builder stand-in carrying only the attributes the code
                   reads (`srcdir`, `to_ignore`, `good`, `broken`,
                   `redirected`, `app.config.linkcheck_retries`);
  * `check_uri`  — the network probe, stubbed to return a fixed sentinel
                   status (the probe is environment, outside the modeled
                   behavior; the model carries its outcome as the opaque
                   `remote` input).

Environment-fact bridging (mapping.md section 2): the model consumes two
booleans instead of the raw environment —

  * `file_exists`  <-> `path.exists(path.join(self.srcdir, uri))`: the
    module-level `path` name is swapped, in a COPY of the module globals used
    only for the materialized oracle, for a shim whose `exists` returns the
    case's boolean (and whose `join` is the real os.path.join).  Only the
    environment probe is replaced; every string decision in the oracle
    (including the patched regex object) is the real repo code.
  * `ignore_match` <-> "some pattern in `self.to_ignore` matches": realized
    as `to_ignore = [re.compile('')]` (matches every string) when True and
    `[]` when False, so the real matching loop runs for real.

Output bridge: statuses 'unchecked'/'working'/'broken'/'ignored' map to the
model's int codes 0/1/2/3.  A target the oracle handles on its web branch
resolves there to a cache/ignore/probe outcome; that outcome is encoded as
100 + code (a value disjoint from the four local codes) and fed to the shadow
as its opaque `remote` argument, so the comparison still catches any shadow
that misroutes a target between the local and web branches, while leaving the
web branch's own outcome unconstrained exactly as the spec does.

Input domain (the Requires): any code-point list `target` (bridged to str via
chr/ord per position), any booleans, any int `remote`.  Boundary cases cover
the empty target, each recognized literal prefix and near-misses, scheme
shapes (lowercase-run/colon/slash placements, uppercase and digit leads),
plain relative paths, and non-ASCII code points; fuzz draws from a mixed
alphabet rich in ':', '/', '#', lowercase runs and non-ASCII.

>= 1e5 Requires-satisfying inputs: boundary grid (all four flag combinations
each) + 100000 fuzz cases.  Pinned fuzz seed: 7985.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib only (plus the repo under test).
"""
import os
import random
import re
import sys
import types
from types import SimpleNamespace

SEED = 7985
N_FUZZ = 100_000

# Status encoding (model.py's @Pure status helpers, contract-free copies).


def UNCHECKED():
    return 0


def WORKING():
    return 1


def MISSING():
    return 2


def IGNORED():
    return 3


# ---------------------------------------------------------------------------
# SHADOW: impl regions of model.py, verbatim, contract calls stripped.
# ---------------------------------------------------------------------------

def starts_with(target, lit):
    # impl-start (contracts + Assert lemma invocations stripped)
    n = len(lit)
    if n > len(target):
        return False
    ok = True
    i = n
    while i > 0:
        if target[i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    return ok
    # impl-end


def scheme_present(target):
    # impl-start (contracts + Assert lemma invocations stripped)
    n = len(target)
    k = 0
    while k < n and 97 <= target[k] and target[k] <= 122:
        k = k + 1
    # k is now the maximal leading lowercase run length.
    if k < 1:
        return False
    if k + 3 > n:
        return False
    res = (target[k] == 58 and target[k + 1] == 47 and target[k + 2] == 47)
    return res
    # impl-end


def check(target, file_exists, ignore_match, remote):
    # impl-start (contracts stripped)
    h = []   # type: list
    h = [35]
    m = [109, 97, 105, 108, 116, 111, 58]
    if len(target) == 0 or starts_with(target, h) or starts_with(target, m):
        return UNCHECKED()
    hp = [104, 116, 116, 112, 58]
    hsp = [104, 116, 116, 112, 115, 58]
    if not (starts_with(target, hp) or starts_with(target, hsp)):
        if scheme_present(target):
            # recognised non-verifiable leading shape: nothing to verify
            return UNCHECKED()
        else:
            if file_exists:
                return WORKING()
            else:
                if ignore_match:
                    return IGNORED()
                else:
                    return MISSING()
    return remote
    # impl-end


# ---------------------------------------------------------------------------
# ORACLE: the real nested check() from the patched module.
# ---------------------------------------------------------------------------

# Sentinel status the stubbed network probe reports; distinct from every
# locally produced status string.
PROBE_STATUS = "probe-outcome"

STATUS_CODE = {"unchecked": 0, "working": 1, "broken": 2, "ignored": 3}
# Web-branch outcomes, encoded disjointly from the local codes (opaque to the
# spec; the offset only serves to make branch misrouting observable).
WEB_CODE = {"working": 100, "broken": 101, "redirected": 102, "ignored": 103,
            "unchecked": 104, PROBE_STATUS: 105}

MATCH_ALL = re.compile("")


def _cell(value):
    # a real closure cell holding `value` (portable across CPython versions)
    return (lambda: value).__closure__[0]


def load_real_check_factory():
    """Extract the nested check() code object from the patched module and
    return a factory materializing it per test case."""
    import sphinx.builders.linkcheck as lc
    outer = lc.CheckExternalLinksBuilder.check_thread
    outer_code = getattr(outer, "__func__", outer).__code__
    codes = [c for c in outer_code.co_consts
             if isinstance(c, types.CodeType) and c.co_name == "check"]
    assert len(codes) == 1, "expected exactly one nested check() code object"
    code = codes[0]
    assert set(code.co_freevars) == {"check_uri", "self", "uri"}, (
        "unexpected free variables: %r" % (code.co_freevars,))

    # Copy of the module globals with only the filesystem probe swapped for a
    # shim; `uri_re` (the patched regex object) and everything else stay real.
    class _FS(object):
        exists_result = False

        @staticmethod
        def exists(p):
            return _FS.exists_result

        join = staticmethod(os.path.join)

    g = dict(lc.__dict__)
    assert "uri_re" in g, "patched module does not define its regex object"
    g["path"] = _FS

    def make(uri, file_exists, ignore_match):
        _FS.exists_result = bool(file_exists)
        fake_self = SimpleNamespace(
            srcdir="/tmp/sbu-conf-srcdir",
            to_ignore=[MATCH_ALL] if ignore_match else [],
            good=set(),
            broken={},
            redirected={},
            app=SimpleNamespace(config=SimpleNamespace(linkcheck_retries=1)),
        )

        def check_uri():
            return PROBE_STATUS, "", 0

        cells = []
        for name in code.co_freevars:
            cells.append(_cell({"check_uri": check_uri,
                                "self": fake_self,
                                "uri": uri}[name]))
        return types.FunctionType(code, g, "check", None, tuple(cells))

    return make


# ---------------------------------------------------------------------------
# Differential driver.
# ---------------------------------------------------------------------------

def run_case(make_real, uri, fe, im):
    """Run oracle and shadow on one target; return error string or None."""
    real_fn = make_real(uri, fe, im)
    status, _info, _code = real_fn()

    web = uri.startswith(("http:", "https:"))  # domain split for the harness
    if web:
        assert status in WEB_CODE, "unexpected web-branch status %r" % status
        expected = WEB_CODE[status]
        rem = expected           # the opaque outcome the environment supplies
    else:
        assert status in STATUS_CODE, (
            "unexpected local status %r for uri=%r" % (status, uri))
        expected = STATUS_CODE[status]
        rem = 999                # must be ignored by a correct local branch

    target = [ord(ch) for ch in uri]
    got = check(target, fe, im, rem)
    if got != expected:
        return ("DISAGREEMENT\n  uri=%r file_exists=%r ignore_match=%r "
                "remote=%r\n  shadow=%r\n  real status=%r (expected code %r)"
                % (uri, fe, im, rem, got, status, expected))
    return None


BOUNDARY = [
    "", "#", "#frag", "#top", "##",
    "mailto:a@b.com", "mailto:", "mai", "mailto", "mailtoX", "Mailto:x",
    "http:", "https:", "http://x", "https://y", "httpx", "http", "https",
    "http:/x", "https:/x", "HTTP://x",
    "ftp:", "ftp://server/f", "ftp:/x", "ftps://h",
    "conf.py", "path/to/notfound", "index.rst", "a/b/c", "doesntexist",
    "file:///etc/passwd", "data:text/plain,hi",
    "a://b", "a://", "ab://c", "abc://", "z://", "zz://zz",
    "A://b", "1://b", "://x", ":/x", "a:/b", "a//b", "a:b", "a:",
    "scheme://host", "Scheme://Host", "x-y://z", "aB://c", "a1://c",
    "relative/path", "./local", "../up", "with space", "/abs/path",
    "UPPER", "MiXeD", "\u00fcn\u00efc\u00f6d\u00e9/path", "\u00e9://x",
    "a\nb", "\n", " ", "  //", "a ://b",
]

ALPHABET = (list("abcdefghijklmz") + list("ABZ") + list("0139")
            + [":", "/", ".", "-", "#", " ", "_", "@", "\n"]
            + ["\u00e9", "\u017f", "\u4e2d"])


def main():
    make_real = load_real_check_factory()
    rng = random.Random(SEED)
    n = 0
    fails = 0

    for uri in BOUNDARY:
        for fe in (False, True):
            for im in (False, True):
                err = run_case(make_real, uri, fe, im)
                n += 1
                if err:
                    print(err)
                    fails += 1
                    if fails >= 5:
                        return 1

    for _ in range(N_FUZZ):
        ln = rng.randint(0, 18)
        if rng.random() < 0.35:
            # bias toward recognized-prefix / scheme-like shapes so both
            # sides of every branch are exercised heavily
            head = rng.choice(["#", "mailto:", "http:", "https:", "ftp:",
                               "http://", "https://", "a://", "ab://",
                               "gopher://", "a:/", "://", "a:", "A://"])
        else:
            head = ""
        s = head + "".join(rng.choice(ALPHABET) for _ in range(ln))
        fe = rng.random() < 0.5
        im = rng.random() < 0.5
        err = run_case(make_real, s, fe, im)
        n += 1
        if err:
            print(err)
            fails += 1
            if fails >= 5:
                return 1

    if fails:
        return 1
    print("G-CONF OK: shadow == real patched check() on %d inputs "
          "(%d boundary x 4 flag combos + %d fuzz, seed %d); 0 disagreements."
          % (n, len(BOUNDARY), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
