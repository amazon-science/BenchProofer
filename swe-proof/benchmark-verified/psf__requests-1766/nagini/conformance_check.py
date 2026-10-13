#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-1766 (nagini).

Refutes (never proves) the refinement leg: does the MODEL agree with the REAL
patched repository code it claims to model?

SHADOW
------
`append_qop_directive`'s impl region of `model.py`, copied VERBATIM below with
only the contract calls stripped (`Requires`/`Ensures`; the region contains no
`Invariant`/`Assert`/`Fold`/`Unfold`). Not a paraphrase: the seven `result = ...`
lines and their code-point literals are the model's bytes. The impl region calls
no `@Pure` helper and there are no `@ContractOnly` callees in this bundle
(mapping.md §3: the segment is assembled deeply, zero axioms), but the pure
region (`quoted_value_token` / `directive_head` / `directive_mid` /
`directive_tail` / `qop_segment`) is ALSO copied over — contracts stripped, on a
`PSeq` shim — and diffed against the same oracle, so the postcondition's
right-hand side is exercised against real code rather than only against the
impl.

ORACLE (called, not transliterated) — two independent legs, both running the
real patched `requests/auth.py` from /testbed (the gate git-applies the gold
patch before this script starts; `PYTHONPATH` makes the patched module
importable):

  * Leg A — `stmt`: the modeled statement itself, mapping.md §1's
    `requests/auth.py:146-147`, the `if qop:` branch of
    `HTTPDigestAuth.build_digest_header`. We do NOT retype it: we read
    `requests.auth.__file__` AT RUNTIME (after the patch is applied), locate
    that `If` node with `ast`, compile the node, and `exec` the real repo
    bytecode with `base`/`ncvalue`/`cnonce`/`qop` bound to our generated
    inputs. This is the only way to drive the modeled statement over an
    arbitrary `base`/`ncvalue`/`cnonce` domain — the enclosing method derives
    all three internally (hashes, `'%08x' % nonce_count`, `sha1(...)+urandom`)
    and accepts no injection point for them — while still executing repository
    code, so a change to that line (e.g. the pre-patch bare `qop=auth`) makes
    this check fail. Failing loudly if the node is absent is part of the check.
  * Leg B — `build_digest_header`: the whole real patched method, driven
    end-to-end with a synthetic Digest challenge. `sys.settrace` captures the
    interpreter's own `base`/`ncvalue`/`cnonce` immediately BEFORE the modeled
    line and `base` immediately after, so the shadow is fed the real pre-state
    and diffed against the real transition. Leg B also asserts that the line
    actually executed is the very line leg A extracted (ties the two legs
    together, so leg A cannot be reading dead code), and that the F2P
    discriminator `'"auth"'` occurs in the credential the method returns
    (`test_DIGESTAUTH_QUOTES_QOP_VALUE`).

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
Model carrier `List[int]` of Unicode code points  <->  repo `str`:
`to_str(cps) == ''.join(chr(c) for c in cps)`, `to_cps(s) == [ord(c) for c in
s]` (mutual inverses on non-surrogate code points, which is what we generate).
`%s` interpolation of a token <-> list `+` of that token's code points. Inputs
are generated as code-point lists (so every one satisfies the model's
`Requires`, which is pure `Acc(list_pred(·), 1/2)` permission and admits any
list) and bridged to `str` for the oracle; both sides are then compared in the
code-point domain.

INPUT DOMAIN
------------
Infinite (arbitrary `base`/`ncvalue`/`cnonce` strings), so: boundary cases first
— all-empty, singletons, the exact F2P shape (a real credential prefix with
`nc='00000001'` and a 16-hex-digit cnonce), tokens carrying `%s`/`%d`/`%%`
(format-injection: a `%`-template oracle and a concatenating shadow could only
diverge here), embedded `"`/`,`/`=`, non-ASCII and astral code points, long
tokens — then seeded fuzz to fill the count. The impl region is straight-line
(one path, no branches), so a single input covers it structurally; the fuzz
covers the interpolation domain. The repo-side `if qop:` guard is driven truthy
on both legs (leg B over `auth`, `auth,auth-int`, `auth-int,auth`), which is the
branch the model models.

>= 1e5 Requires-satisfying inputs; pinned seed 1766 (recorded in mapping.md
§G-CONF). Exit 0 iff zero disagreements; on a disagreement the input and both
outputs are printed and the exit status is 1. stdlib only.
"""
import ast
import random
import sys
from typing import List  # so the impl region's `# type: List[int]` copies over verbatim

SEED = 1766
N_FUZZ = 100_000
N_DRIVE = 2000  # end-to-end leg-B drives of the real build_digest_header


# ---------------------------------------------------------------------------
# PSeq shim: Nagini's immutable sequence carrier (take/drop/+/len/[]/==),
# plus ToSeq to materialize one from a list.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# model.py pure region, copied over verbatim (@Pure and docstrings dropped).
# ---------------------------------------------------------------------------
def quoted_value_token():
    return PSeq(34, 97, 117, 116, 104, 34)  # '"auth"'


def directive_head():
    #   ','  ' '  'q'  'o'  'p'  '='  ('"auth"')          ','  ' '  'n'  'c'  '='
    return PSeq(44, 32, 113, 111, 112, 61) + quoted_value_token() + PSeq(44, 32, 110, 99, 61)


def directive_mid():
    #   ','  ' '  'c'  'n'  'o'  'n'  'c'  'e'  '='  '"'
    return PSeq(44, 32, 99, 110, 111, 110, 99, 101, 61, 34)


def directive_tail():
    return PSeq(34)


def qop_segment(ncvalue, cnonce):
    return directive_head() + ncvalue + directive_mid() + cnonce + directive_tail()


# ---------------------------------------------------------------------------
# SHADOW: model.py's impl region (# impl-start .. # impl-end), verbatim,
# contract calls stripped.
# ---------------------------------------------------------------------------
def append_qop_directive(base, ncvalue, cnonce):
    result = list(base)  # type: List[int]
    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
    result = result + [44, 32, 113, 111, 112, 61]
    result = result + [34, 97, 117, 116, 104, 34]
    result = result + [44, 32, 110, 99, 61]
    # the count value, bare
    result = result + ncvalue
    # ', cnonce="'
    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
    # the client-nonce value
    result = result + cnonce
    # closing double quote
    result = result + [34]
    return result


# ---------------------------------------------------------------------------
# Type bridge (mapping.md §2, inverted): List[int] code points <-> str.
# ---------------------------------------------------------------------------
def to_str(cps):
    return "".join(chr(c) for c in cps)


def to_cps(s):
    return [ord(c) for c in s]


# ---------------------------------------------------------------------------
# ORACLE leg A: the real patched `if qop:` statement of build_digest_header,
# located in the installed source at runtime and executed as repo bytecode.
# ---------------------------------------------------------------------------
class OracleStatement(object):
    def __init__(self):
        import requests.auth as repo_auth
        self.path = repo_auth.__file__
        if self.path.endswith(("c", "o")):  # never .pyc in these images, but be safe
            self.path = self.path[:-1]
        with open(self.path) as fh:
            src = fh.read()
        tree = ast.parse(src, filename=self.path)
        nodes = []
        for cls in tree.body:
            if isinstance(cls, ast.ClassDef) and cls.name == "HTTPDigestAuth":
                for fn in cls.body:
                    if (isinstance(fn, ast.FunctionDef)
                            and fn.name == "build_digest_header"):
                        for st in fn.body:
                            if (isinstance(st, ast.If)
                                    and isinstance(st.test, ast.Name)
                                    and st.test.id == "qop"):
                                nodes.append(st)
        if len(nodes) != 1:
            raise AssertionError(
                "expected exactly one `if qop:` statement in "
                "HTTPDigestAuth.build_digest_header of %s, found %d — the "
                "oracle could not be located, so this check would certify "
                "nothing" % (self.path, len(nodes)))
        self.node = nodes[0]
        self.lineno = self.node.lineno              # `if qop:`      (auth.py:146)
        self.body_lineno = self.node.body[0].lineno  # the append     (auth.py:147)
        self.source = ast.get_source_segment(src, self.node)
        mod = ast.Module(body=[self.node], type_ignores=[])
        ast.fix_missing_locations(mod)
        self.code = compile(mod, self.path, "exec")

    def append(self, base, ncvalue, cnonce):
        """Run the real repo statement on these values; return the new `base`."""
        ns = {"base": base, "ncvalue": ncvalue, "cnonce": cnonce, "qop": "auth"}
        exec(self.code, ns)
        return ns["base"]


# ---------------------------------------------------------------------------
# ORACLE leg B: the whole real patched build_digest_header, driven end-to-end,
# with sys.settrace recovering the interpreter's own base/ncvalue/cnonce around
# the modeled line.
# ---------------------------------------------------------------------------
def make_auth(qop_value, realm, nonce):
    from requests.auth import HTTPDigestAuth
    auth = HTTPDigestAuth("user", "pass")
    chal = {"realm": realm, "nonce": nonce, "qop": qop_value}
    # The challenge lives on the instance in this version; newer requests keeps
    # it on a per-thread state object.
    if hasattr(auth, "init_per_thread_state"):
        auth.init_per_thread_state()
        auth._thread_local.chal = chal
        auth._thread_local.last_nonce = ""
        auth._thread_local.nonce_count = 0
    else:
        auth.chal = chal
        auth.last_nonce = ""
        auth.nonce_count = 0
    return auth


def drive_real_function(stmt, qop_value, realm, nonce, method, url):
    """Call the real patched build_digest_header; return
    (base_before, ncvalue, cnonce, base_after, credential)."""
    auth = make_auth(qop_value, realm, nonce)
    target = stmt.body_lineno
    trace = []

    def tracer(frame, event, arg):
        if frame.f_code.co_name != "build_digest_header":
            return None
        if event == "call":
            return tracer
        if event == "line":
            loc = frame.f_locals
            trace.append((frame.f_lineno, loc.get("base"),
                          loc.get("ncvalue"), loc.get("cnonce")))
        return tracer

    sys.settrace(tracer)
    try:
        cred = auth.build_digest_header(method, url)
    finally:
        sys.settrace(None)
    if not isinstance(cred, str):
        # build_digest_header returns None when it declines the challenge
        # (unknown algorithm / auth-int-only qop). Our challenges never do, so
        # this means the generator left the modeled branch — fail, never skip.
        raise AssertionError(
            "build_digest_header returned %r (no credential) for qop=%r "
            "realm=%r nonce=%r — the modeled `if qop:` branch was not reached"
            % (cred, qop_value, realm, nonce))
    hits = [i for i, rec in enumerate(trace) if rec[0] == target]
    if not hits:
        raise AssertionError(
            "the real build_digest_header never executed auth.py:%d (the "
            "statement leg A extracted) — leg A would be checking dead code"
            % target)
    i = hits[0]
    before = trace[i]
    if i + 1 >= len(trace):
        raise AssertionError("no post-state trace record for auth.py:%d" % target)
    after = trace[i + 1]
    return before[1], before[2], before[3], after[1], cred


# ---------------------------------------------------------------------------
# Input generation. Every generated input is a List[int] of non-surrogate code
# points, so to_str/to_cps are mutual inverses and the model's Requires (pure
# permission over the three lists) holds for all of them.
# ---------------------------------------------------------------------------
HEX = "0123456789abcdef"


def rand_cps(rng, lo, hi):
    n = rng.randint(lo, hi)
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.55:                       # printable ASCII (the realistic domain)
            out.append(rng.randint(32, 126))
        elif r < 0.70:                     # the structural characters
            out.append(rng.choice([34, 37, 44, 61, 32, 115, 100]))  # " % , = sp s d
        elif r < 0.85:                     # control / latin-1 / BMP
            out.append(rng.randint(1, 0xD7FF))
        elif r < 0.95:                      # BMP above the surrogate block
            out.append(rng.randint(0xE000, 0xFFFF))
        else:                               # astral
            out.append(rng.randint(0x10000, 0x2FFFF))
    return out


def boundary_cases():
    """Empty, singleton, the exact F2P shape, format-injection, structural
    characters, non-ASCII, long tokens."""
    f2p_prefix = ('username="user", realm="testrealm@host.com", '
                  'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '
                  'uri="/dir/index.html", '
                  'response="6629fae49393a05397450978507c4ef1"')
    cases = [
        ([], [], []),
        ([65], [66], [67]),
        (to_cps(f2p_prefix), to_cps("00000001"), to_cps("0a4f113b" * 2)),
        (to_cps(f2p_prefix), to_cps("%08x" % 1), to_cps("f" * 16)),
        ([], to_cps("00000001"), []),
        (to_cps("base"), [], []),
        (to_cps("%s"), to_cps("%s"), to_cps("%s")),
        (to_cps("%d %r %%"), to_cps("%d"), to_cps("%%")),
        (to_cps("%(x)s"), to_cps("%(y)s"), to_cps("%*s")),
        (to_cps('a"b'), to_cps('n"c'), to_cps('c"n')),
        (to_cps(", qop=auth, nc="), to_cps(", qop="), to_cps('"auth"')),
        (to_cps("a=b, c=d"), to_cps("="), to_cps(",")),
        (to_cps("\x00\x01"), [0], [0]),
        (to_cps("ünïcödé — 中文 🎉"), to_cps("κ"), to_cps("🎉")),
        ([0xD7FF], [0xE000], [0x2FFFF]),
        (to_cps("x" * 300), to_cps("y" * 64), to_cps("z" * 64)),
        (to_cps("Digest "), to_cps("ffffffff"), to_cps("0" * 16)),
    ]
    return cases


def check_one(stmt, base_cps, nc_cps, cn_cps, failures):
    """Diff the shadow (impl region + pure region) against oracle leg A."""
    shadow_cps = append_qop_directive(base_cps, nc_cps, cn_cps)
    oracle_str = stmt.append(to_str(base_cps), to_str(nc_cps), to_str(cn_cps))
    oracle_cps = to_cps(oracle_str)
    if shadow_cps != oracle_cps:
        failures.append(("impl-region", base_cps, nc_cps, cn_cps,
                         shadow_cps, oracle_cps))
        return
    # The postcondition's right-hand side (pure region) must agree too.
    spec = ToSeq(base_cps) + qop_segment(ToSeq(nc_cps), ToSeq(cn_cps))
    if spec != ToSeq(oracle_cps):
        failures.append(("pure-region/qop_segment", base_cps, nc_cps, cn_cps,
                         list(spec._t), oracle_cps))
        return
    # The discriminating structural property: the segment opens with
    # directive_head, which carries the quoted token '"auth"' contiguously.
    head = ToSeq(oracle_cps).drop(len(base_cps)).take(len(directive_head()))
    if head != directive_head():
        failures.append(("directive_head", base_cps, nc_cps, cn_cps,
                         list(directive_head()._t), list(head._t)))


def report_failures(failures, count):
    print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
          % (len(failures), count, SEED))
    for kind, base_cps, nc_cps, cn_cps, shadow, oracle in failures[:5]:
        print("  [%s]" % kind)
        print("    base   = %r" % (to_str(base_cps),))
        print("    nc     = %r" % (to_str(nc_cps),))
        print("    cnonce = %r" % (to_str(cn_cps),))
        print("    shadow = %r" % (to_str(shadow),))
        print("    oracle = %r" % (to_str(oracle),))
        print("    shadow_cps = %r" % (shadow,))
        print("    oracle_cps = %r" % (oracle,))


def main():
    rng = random.Random(SEED)
    stmt = OracleStatement()
    failures = []
    count = 0

    # ---- leg A: boundary cases, then fuzz --------------------------------
    for base_cps, nc_cps, cn_cps in boundary_cases():
        count += 1
        check_one(stmt, base_cps, nc_cps, cn_cps, failures)
    for _ in range(N_FUZZ):
        count += 1
        check_one(stmt, rand_cps(rng, 0, 40), rand_cps(rng, 0, 10),
                  rand_cps(rng, 0, 20), failures)
        if len(failures) >= 5:
            break
    if failures:
        report_failures(failures, count)
        return 1

    # ---- leg B: drive the whole real patched method end-to-end ----------
    qop_values = ["auth", "auth,auth-int", "auth-int,auth"]
    methods = ["GET", "POST", "PUT", "HEAD", "DELETE"]
    drives = 0
    for i in range(N_DRIVE):
        qv = qop_values[i % len(qop_values)]
        realm = "".join(rng.choice(HEX) for _ in range(6)) + "@host.com"
        nonce = "".join(rng.choice(HEX) for _ in range(rng.randint(4, 34)))
        url = ("http://example.com/" + "".join(rng.choice(HEX) for _ in range(4))
               + ("?q=" + "".join(rng.choice(HEX) for _ in range(3))
                  if rng.random() < 0.4 else ""))
        base_before, ncvalue, cnonce, base_after, cred = drive_real_function(
            stmt, qv, realm, nonce, rng.choice(methods), url)
        drives += 1
        count += 1
        shadow_cps = append_qop_directive(to_cps(base_before), to_cps(ncvalue),
                                         to_cps(cnonce))
        if shadow_cps != to_cps(base_after):
            failures.append(("build_digest_header", to_cps(base_before),
                             to_cps(ncvalue), to_cps(cnonce),
                             shadow_cps, to_cps(base_after)))
        elif to_str(shadow_cps) not in cred:
            failures.append(("credential", to_cps(base_before),
                             to_cps(ncvalue), to_cps(cnonce),
                             shadow_cps, to_cps(cred)))
        elif '"auth"' not in cred:  # the F2P discriminator
            failures.append(("f2p-quoted-token", to_cps(base_before),
                             to_cps(ncvalue), to_cps(cnonce),
                             to_cps('"auth"'), to_cps(cred)))
        if len(failures) >= 5:
            break
    if failures:
        report_failures(failures, count)
        return 1

    print("G-CONF OK: model.py impl region (+ pure region) agrees with the real "
          "patched requests/auth.py:%d `if qop:` append on %d inputs "
          "(%d boundary + %d fuzz code-point triples driving the repo statement, "
          "%d end-to-end build_digest_header drives), seed=%d, 0 disagreements."
          % (stmt.body_lineno, count, len(boundary_cases()), N_FUZZ, drives, SEED))
    print('{"gate": "G-CONF", "instance": "psf__requests-1766", '
          '"backend": "nagini", "status": "pass", "inputs": %d, '
          '"boundary": %d, "fuzz": %d, "real_function_drives": %d, "seed": %d, '
          '"disagreements": 0, "oracle": '
          '"requests.auth.HTTPDigestAuth.build_digest_header (`if qop:` at '
          'auth.py:%d, executed as repo bytecode) + end-to-end calls", '
          '"shadow": "model.py impl region verbatim, contracts stripped"}'
          % (count, len(boundary_cases()), N_FUZZ, drives, SEED,
             stmt.body_lineno))
    return 0


if __name__ == "__main__":
    sys.exit(main())
