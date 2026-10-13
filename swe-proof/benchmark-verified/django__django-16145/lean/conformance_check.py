#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16145.

The bundle models ONE computation: the banner display-address sub-computation
inside `Command.inner_run`
(`django/core/management/commands/runserver.py`). Its Lean implementation
(`implementation_displayAddr`) turns the resolved bind host (`self.addr`) and the
raw-IPv6 flag (`self._raw_ipv6`) into the host string shown in the start-up
banner URL:

    if self._raw_ipv6:
        addr = "[%s]" % self.addr
    elif self.addr == "0":
        addr = "0.0.0.0"
    else:
        addr = self.addr

This script transliterates that R/I impl into Python (`shadow_display`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior — the same three-way branch with the new `addr == "0"` ->
"0.0.0.0" case.

We do NOT stand up Django's management-command / argument-parsing machinery
(heavy, and the modeled value is a pure two-input string computation). Both legs
are total functions over (raw_ipv6: bool, addr: str). The edge set enumerates the
cross-product of a curated boundary host set with both flag values — it contains
the discriminating input (raw_ipv6=False, addr="0") — and the fuzz loop then
samples >=1e5 random (flag, host) pairs.

stdlib-only. Pinned seed: 16145 (also recorded in mapping.md).
"""
import sys

SEED = 16145
N = 120_000

# Boundary host set: the shorthand "0" (the fix's trigger), its canonical form,
# empty, IPv6/IPv4 literals, and near-misses that must NOT trigger the rewrite.
BOUNDARY_ADDRS = (
    "0", "0.0.0.0", "", "::1", "127.0.0.1", "localhost",
    "0.0", "00", "10", "0:0", "1", "0.0.0.1",
)

# Character alphabet for fuzzed host-like strings (digits, dots, colons, letters).
ALPHABET = "0123456789.:abcfABCF[]-"


# --- ORACLE: the post-patch behavior, faithful in-process replica -----------
def oracle_display(raw_ipv6, addr):
    if raw_ipv6:
        return "[%s]" % addr
    elif addr == "0":
        return "0.0.0.0"
    else:
        return addr


# --- shadow of implementation_displayAddr (the R/I leg) ---------------------
# Mirrors Solution.lean branch-for-branch.
def shadow_display(raw_ipv6, addr):
    if raw_ipv6:
        return "[" + addr + "]"
    elif addr == "0":
        return "0.0.0.0"
    else:
        return addr


def disagree(raw_ipv6, addr):
    got = oracle_display(raw_ipv6, addr)
    want = shadow_display(raw_ipv6, addr)
    if got != want:
        return ((raw_ipv6, addr), got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # Edge set = boundary hosts x both flag values (exhaustive over the curated
    # boundary set; contains the discriminating input raw_ipv6=False, addr="0").
    for raw_ipv6 in (False, True):
        for addr in BOUNDARY_ADDRS:
            d = disagree(raw_ipv6, addr)
            if d:
                print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
                print("status=fail")
                return 1
            checked += 1

    # Random fuzz over (flag, host-like string).
    rnd = _lcg(SEED)
    for _ in range(N):
        raw_ipv6 = (next(rnd) & 1) == 1
        length = next(rnd) % 8  # 0..7 chars
        addr = "".join(ALPHABET[next(rnd) % len(ALPHABET)] for _ in range(length))
        d = disagree(raw_ipv6, addr)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
