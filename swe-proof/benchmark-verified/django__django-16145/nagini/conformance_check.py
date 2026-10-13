#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16145 (nagini).

SHADOW: the impl region of model.py's ``display_address``, copied VERBATIM
below with only the contract calls (Requires / Ensures / Invariant / Assert)
stripped. The @Pure helpers ``wildcard_short`` / ``wildcard_dotted`` /
``shown_address`` copy over as plain functions on top of a small immutable
PSeq shim (tuple-backed; supports ``+``, ``==``, ``take``, ``len``); the
shadow exercises the loops of the impl region, and ``shown_address`` is kept
as an internal cross-check of the executable shadow. There are no
@ContractOnly callees (mapping.md section 3: no consumed axioms, no
A-references).

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``django.core.management.commands.runserver.Command.inner_run``,
specifically the address string it renders into the
"Starting development server at ..." announcement. The gate applies
patch.diff to /testbed before this script runs. Each probe builds a Command,
sets the two instance attributes the derivation reads (the bound address and
the bracketed-IPv6 flag, normally assigned in ``handle``), stubs the
side-effecting steps that follow the announcement (migration check; the
handler getter raises KeyboardInterrupt so the socket server never starts),
runs ``inner_run``, and extracts the shown address from the captured
announcement text between the fixed URL prefix and the fixed
":<port>/ ... Quit the server with ..." suffix (the port is a pinned
sentinel string so the suffix anchor is unambiguous even for adversarial
address content).

TYPE BRIDGE (mapping.md section 2): the repo value is a ``str``; the model
carrier is ``List[int]`` of Unicode code points via ``ord`` (a bijection on
surrogate-free strings). Generation happens over ``str`` and is lowered per
call; the shadow's result is raised back to ``str`` via ``chr`` for the
comparison. The precondition demands only a readable list, so every
surrogate-free ``str`` lowers to a Requires-satisfying input.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary addresses (the
one-character wildcard, its dotted expansion, near-miss zero forms, IPv4 /
IPv6 literals, hostnames, the empty string, percent signs, whitespace and
newline content, non-ASCII code points, long strings) each crossed with both
flag values, plus 60000 random fuzz addresses over a mixed
digit/dot/colon/bracket/letter/percent/space/non-ASCII alphabet, each
crossed with both flag values (>= 120000 checks total). Pinned fuzz seed:
16145. Exit 0 iff zero disagreements; on disagreement prints the input and
both outputs and exits 1. stdlib only.
"""
import io
import random
import sys

SEED = 16145
N_FUZZ = 60000
PORT_SENTINEL = "54321"


# --- PSeq shim: immutable sequence with the operations the model uses --------

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

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, copied as plain functions ----------------------

def wildcard_short():
    # "0"  (the single-character wildcard form)
    return PSeq(48)


def wildcard_dotted():
    # "0.0.0.0"  (the fully-written unspecified-IPv4 form)
    return PSeq(48, 46, 48, 46, 48, 46, 48)


def shown_address(addr, raw_ipv6):
    """The address shown to the operator, derived from the bound address.

    Priority order: bracketed-IPv6 first, then the "0" -> "0.0.0.0" wildcard
    expansion, then the bound address unchanged.
    """
    if raw_ipv6:
        return PSeq(91) + addr + PSeq(93)        # "[" + addr + "]"
    if addr == wildcard_short():
        return wildcard_dotted()
    return addr


# --- impl region of model.py, verbatim with contract calls stripped ----------

def display_address(addr, raw_ipv6):
    result = []  # type: List[int]
    c = 0
    if raw_ipv6:
        result = [91]
        i = 0
        while i < len(addr):
            c = addr[i]
            result = result + [c]
            i = i + 1
        result = result + [93]
    elif ToSeq(addr) == wildcard_short():
        result = [48, 46, 48, 46, 48, 46, 48]
    else:
        i = 0
        while i < len(addr):
            c = addr[i]
            result = result + [c]
            i = i + 1
    return result


# --- oracle: the real patched repo derivation, observed via inner_run --------

_PREFIX = "Starting development server at http://"


def _make_oracle():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True)
    django.setup()


def _build_command():
    from django.core.management.base import OutputWrapper
    from django.core.management.commands.runserver import Command

    cmd = Command()
    cmd.check_migrations = lambda: None

    def _no_handler(*a, **k):
        # abort inner_run right after the announcement, before any socket use
        raise KeyboardInterrupt

    cmd.get_handler = _no_handler
    return cmd, OutputWrapper


def real_shown(cmd, OutputWrapper, addr_str, raw_ipv6):
    """Run the real (patched) inner_run and extract the announced address."""
    buf = io.StringIO()
    cmd.stdout = OutputWrapper(buf)
    cmd.stderr = OutputWrapper(io.StringIO())
    cmd.addr = addr_str
    cmd._raw_ipv6 = raw_ipv6
    cmd.use_ipv6 = raw_ipv6
    cmd.port = PORT_SENTINEL
    options = {
        "use_threading": False,
        "skip_checks": True,
        "shutdown_message": "",
    }
    try:
        cmd.inner_run(None, **options)
    except SystemExit:
        pass
    text = buf.getvalue()
    i = text.index(_PREFIX)
    suffix = ":%s/\nQuit the server with " % PORT_SENTINEL
    j = text.rindex(suffix)
    return text[i + len(_PREFIX):j]


# --- input generation ---------------------------------------------------------

BOUNDARY_ADDRS = [
    "0",             # the one-character wildcard (the discriminating input)
    "0.0.0.0",       # the fully-written form
    "00",            # multi-char zeros (NOT the wildcard)
    "0.0",           # zero-ish but not the wildcard
    "0 ",            # wildcard plus trailing space (NOT the wildcard)
    " 0",            # leading space
    "10",
    "127.0.0.1",
    "192.168.0.1",
    "::",            # unspecified IPv6
    "::1",
    "fe80::1",
    "2001:db8::0",
    "localhost",
    "example.com",
    "",              # empty
    "8000",          # port-like token used as addr
    "%s",            # percent placeholder content must pass through as value
    "%",             # bare percent
    "a\nb",          # embedded newline
    "\t0\t",         # tabs around the wildcard char
    "[0]",           # already-bracketed content
    "\u00e9\u4e16",  # non-ASCII code points (bridge stress)
    "0" * 200,       # long run of the wildcard char
]

FUZZ_ALPHABET = "0123456789.:[]abcdefABCDEF-%\u00e9 \n"


def main():
    _make_oracle()
    cmd, OutputWrapper = _build_command()

    checked = 0
    disagreements = 0

    def check(addr_str, raw_ipv6):
        nonlocal checked, disagreements
        checked += 1
        cps = [ord(ch) for ch in addr_str]
        shadow_cps = display_address(cps, raw_ipv6)
        shadow = "".join(chr(c) for c in shadow_cps)
        # internal cross-check: the impl region agrees with the pure spec fn
        assert ToSeq(shadow_cps) == shown_address(ToSeq(cps), raw_ipv6), (
            "internal shadow inconsistency at %r/%r" % (addr_str, raw_ipv6))
        real = real_shown(cmd, OutputWrapper, addr_str, raw_ipv6)
        if shadow != real:
            disagreements += 1
            print(
                "DISAGREEMENT at addr=%r raw_ipv6=%r:\n  shadow=%r\n  real=%r"
                % (addr_str, raw_ipv6, shadow, real))

    for addr in BOUNDARY_ADDRS:
        for flag in (False, True):
            check(addr, flag)

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 12)
        addr = "".join(rng.choice(FUZZ_ALPHABET) for _ in range(n))
        for flag in (False, True):
            check(addr, flag)

    if disagreements:
        print("FAIL: %d disagreement(s) over %d inputs"
              % (disagreements, checked))
        return 1
    print("PASS: shadow == real patched repo derivation on all %d inputs "
          "(%d boundary x 2 + %d fuzz x 2); pinned seed %d"
          % (checked, len(BOUNDARY_ADDRS), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
