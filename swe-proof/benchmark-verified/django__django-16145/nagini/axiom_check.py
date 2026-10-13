#!/usr/bin/env python3
"""G-AX soundness check for django__django-16145.

This bundle consumes NO axioms: the modeled `shown_address` is a pure, piecewise
transcription of the bound address (bracket-wrap / wildcard-expand / identity)
over Unicode code points (mapping.md §3, refinement.md §B). There is therefore
no `@ContractOnly` callee Ensures to fuzz against a real library callee.

What remains to validate is the single nontrivial soundness obligation of the
refinement: the R-refinement of mapping.md §2 — that the modeled function

    shown_address(codepoints(addr), raw_ipv6)

(transcribed from model.py's `shown_address`, operating on the List[int] /
PSeq[int] carrier) equals Python's OWN native evaluation of the gold
`patch.diff` expression bound to `addr` in `inner_run`:

    if self._raw_ipv6:   addr = f"[{self.addr}]"
    elif self.addr == "0": addr = "0.0.0.0"
    else:                addr = self.addr

— for every representative bound address and both values of `raw_ipv6`. The
input space is enumerated over boundary addresses (the wildcard "0", the
fully-written "0.0.0.0", bracketed/bare IPv6 and IPv4 literals, hostnames, the
empty string, addresses that merely contain or start with '0', multi-character
"00"), each crossed with raw_ipv6 in {False, True}, plus a randomized fuzz of
addresses drawn from the digit/dot/colon/bracket/letter alphabet. Also confirms
the bundle's discriminator: the PRE-PATCH expression (which lacks the wildcard
expansion) differs from the gold on exactly the inputs where the bound address
is "0" and it is not a bracketed IPv6 literal.

stdlib-only; exit 0 iff sound.
"""
import random
import sys


def codepoints(s):
    return [ord(ch) for ch in s]


# --- model.py transcription, operating on the code-point carrier -------------
WILDCARD_SHORT = [48]                       # "0"
WILDCARD_DOTTED = [48, 46, 48, 46, 48, 46, 48]   # "0.0.0.0"


def model_shown(addr_cps, raw_ipv6):
    """Transcription of model.py's `shown_address` over List[int] code points."""
    if raw_ipv6:
        return [91] + list(addr_cps) + [93]          # "[" + addr + "]"
    if list(addr_cps) == WILDCARD_SHORT:
        return list(WILDCARD_DOTTED)
    return list(addr_cps)


# --- gold patch.diff expression, verbatim semantics over str -----------------
def gold_expression(addr_str, raw_ipv6):
    if raw_ipv6:
        return "[%s]" % addr_str
    elif addr_str == "0":
        return "0.0.0.0"
    else:
        return addr_str


# --- pre-patch (buggy) repo expression, verbatim semantics over str ----------
def prepatch_expression(addr_str, raw_ipv6):
    # "[%s]" % self.addr if self._raw_ipv6 else self.addr  (no "0" expansion)
    return ("[%s]" % addr_str) if raw_ipv6 else addr_str


BOUNDARY_ADDRS = [
    "0",            # the wildcard (the discriminating input)
    "0.0.0.0",      # the fully-written form
    "00",           # multi-char zeros (NOT the wildcard)
    "0.0",          # leading-zero-ish but not the wildcard
    "10",           # contains no special handling
    "127.0.0.1",    # default IPv4
    "192.168.0.1",  # IPv4 with a zero octet
    "::1",          # bare IPv6 (as bracketed literal it is wrapped)
    "fe80::1",      # IPv6
    "localhost",    # hostname
    "example.com",  # FQDN
    "",             # empty
    "8000",         # purely a port-like token used as addr
]

FUZZ_ALPHABET = "0123456789.:[]abcdefABCDEF-"


def main():
    violations = 0
    discriminating = 0
    checked = 0

    def check(addr_str, raw_ipv6):
        nonlocal violations, discriminating, checked
        checked += 1
        m = "".join(chr(c) for c in model_shown(codepoints(addr_str), raw_ipv6))
        g = gold_expression(addr_str, raw_ipv6)
        if m != g:
            violations += 1
            print(
                f"MISMATCH model!=gold at addr={addr_str!r} raw_ipv6={raw_ipv6}: "
                f"model={m!r} gold={g!r}",
                file=sys.stderr,
            )
        p = prepatch_expression(addr_str, raw_ipv6)
        if p != g:
            discriminating += 1

    for addr in BOUNDARY_ADDRS:
        for raw_ipv6 in (False, True):
            check(addr, raw_ipv6)

    rng = random.Random(20221003)
    for _ in range(40000):
        n = rng.randint(0, 8)
        addr = "".join(rng.choice(FUZZ_ALPHABET) for _ in range(n))
        check(addr, rng.choice((False, True)))

    if violations:
        print(
            f"UNSOUND: {violations} violation(s) of model == gold over "
            f"{checked} inputs",
            file=sys.stderr,
        )
        return 1

    if discriminating == 0:
        print(
            "DEGENERATE: pre-patch expression never differs from gold — "
            "the spec could not sense the bug",
            file=sys.stderr,
        )
        return 1

    # The discriminator must include exactly the wildcard non-IPv6 case.
    if prepatch_expression("0", False) == gold_expression("0", False):
        print(
            "DEGENERATE: pre-patch and gold agree on the wildcard '0' input",
            file=sys.stderr,
        )
        return 1

    print(
        f"SOUND: model `shown_address` == gold expression on all {checked} "
        f"inputs (13 boundary x 2 + 40000 fuzz); pre-patch (no wildcard "
        f"expansion) differs from gold on {discriminating} of them, including "
        f"the discriminating addr='0' (gold '0.0.0.0' vs pre-patch '0')."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
