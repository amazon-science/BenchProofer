#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for psf__requests-5414.

The bundle models ONE fragment: the host-validation block of `prepare_url`. Its
Lean implementation (`implementation_validateHost`) decides, for a parsed host:

    if not isAscii(host):                       # non-ASCII branch (A-reference)
        result = idnaEncode(host)               # unchanged real callee — NOT in diff
    elif startsWithInvalid(host):               # the CHANGED decision (R/I)
        result = error                          # raise InvalidURL
    else:
        result = ok(host)                       # accept

This script transliterates the R/I leg (the ASCII validation decision) into
Python (`shadow_validate`) and differential-tests it against the ORACLE: a
faithful in-process replica of the POST-PATCH behavior of the changed lines
(`requests/models.py:401-405`):

    elif host.startswith((u'*', u'.')):
        raise InvalidURL('URL has an invalid label.')

The non-ASCII branch delegates to the UNCHANGED callee `_get_idna_encoded_host`
(modeled `opaque` as `idnaEncode`, an A-reference). It is IDENTICAL in both the
spec and the impl by construction, so it is excluded from the differential; only
the ASCII validation decision — the leg the patch edits — is compared. The
`isAscii` A-reference itself is validated against the real `unicode_is_ascii`
callee by `axiom_check.py` (G-AX).

Outcomes are encoded as the strings "error" (raise InvalidURL) and
("ok", host) (host carried forward), matching the Lean `Except Unit (List Char)`.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 5414 (also in mapping.md).
"""
import sys

SEED = 5414
N = 120_000


def _is_ascii(host: str) -> bool:
    return all(ord(c) < 128 for c in host)


# --- ORACLE: the post-patch validation outcome (ASCII leg) -------------------
# Faithful replica of requests/models.py:401-405 post-patch, restricted to the
# ASCII branch (the only leg the patch changes). Returns "error" for a rejected
# host, or ("ok", host) for an accepted one.
def oracle_validate(host: str):
    # caller guarantees this is the ASCII branch (unicode_is_ascii(host) is True)
    if host.startswith((u'*', u'.')):          # post-patch reserved leading chars
        return "error"                          # raise InvalidURL('URL has an invalid label.')
    return ("ok", host)                         # accepted as-is


# --- shadow of implementation_validateHost (the R/I ASCII leg) ---------------
# Mirrors Solution.lean: startsWithInvalid host := host[0] in {'*','.'}.
def shadow_validate(host: str):
    def starts_with_invalid(h):
        return len(h) > 0 and (h[0] == '*' or h[0] == '.')
    if starts_with_invalid(host):
        return "error"
    return ("ok", host)


def disagree(host: str):
    got = oracle_validate(host)
    want = shadow_validate(host)
    if got != want:
        return (host, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


# ASCII alphabet emphasizing the reserved leading characters and a spread of
# ordinary host characters, so the decision is exercised in every position.
_ALPHABET = ['*', '.', '-', '_', '@', '/', ' ', ':',
             '0', '9', 'a', 'b', 'z', 'A', 'Z', 'x', 'y', '~', '%', '+']


def _enumerate_edge():
    return [
        "", "*", ".", "..", "**", "*.com", ".example.com", "example.com",
        "*example.com", ".", "a.b.c", "host*", "ho.st", "a", "1.2.3.4",
        "x.", "x*", "*.", ".*", "  ", "-leading", "_leading",
    ]


def main() -> int:
    checked = 0

    for host in _enumerate_edge():
        # all edge hosts are ASCII by construction
        assert _is_ascii(host)
        d = disagree(host)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        length = next(rnd) % 11           # 0..10 code points
        host = "".join(_ALPHABET[next(rnd) % len(_ALPHABET)] for _ in range(length))
        # ASCII by construction (alphabet is ASCII) — the R/I leg under test
        d = disagree(host)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
