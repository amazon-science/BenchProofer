#!/usr/bin/env python3
"""G-AX — A-reference soundness check for psf__requests-5414.

The bundle consumes NO `axiom <callee>_prop` (the only `opaque` callee,
`idnaEncode` ↔ `_get_idna_encoded_host`, governs the UNCHANGED non-ASCII branch
and the proof consumes none of its properties). But the ASCII branch selector is
modeled DEEPLY as an A-reference:

    isAscii host := host.all (fun c => c.toNat < 128)

mapped to the real unchanged callee `requests._internal_utils.unicode_is_ascii`
(mapping.md). SPEC_GUIDE §3 requires a deep A-reference be validated == the real
callee. This script drives the REAL `unicode_is_ascii` on boundary + fuzzed host
strings and asserts the Lean model agrees for every observation.

We additionally validate the changed-decision deep model
`startsWithInvalid host := host[0] in {'*','.'}` against the real post-patch
predicate `host.startswith((u'*', u'.'))` (an `str` builtin — exercised here for
completeness; G-CONF is the primary differential for it).

stdlib + the in-repo `requests` package only; no network. exit 0 iff sound.
"""
import sys

SEED = 5414
N = 60_000


def model_isAscii(host: str) -> bool:
    # Lean: host.all (fun c => c.toNat < 128)
    return all(ord(c) < 128 for c in host)


def model_startsWithInvalid(host: str) -> bool:
    # Lean: match host with [] => false | c :: _ => c == '*' || c == '.'
    return len(host) > 0 and (host[0] == '*' or host[0] == '.')


def real_startsWithInvalid(host: str) -> bool:
    # post-patch predicate on the ASCII branch
    return host.startswith((u'*', u'.'))


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


# A code-point alphabet spanning ASCII boundaries and a few non-ASCII points so
# the ascii/non-ascii decision is exercised in both directions.
_ALPHABET = (
    ['*', '.', '-', '_', '@', '/', ' ', ':', '0', '9', 'a', 'z', 'A', 'Z']
    + [chr(0), chr(127), chr(128), chr(255), '☃', 'ジ', 'ß']
)


def main() -> int:
    try:
        from requests._internal_utils import unicode_is_ascii
    except Exception as e:  # pragma: no cover
        print(f"status=fail could not import real callee unicode_is_ascii: {e!r}")
        return 1

    checked = 0
    mismatches = 0

    # --- boundary / hand-picked hosts ---
    edge = [
        "", "*", ".", "*.com", ".example.com", "example.com", "*example.com",
        "a.b.c", "host*", "ho.st", "☃.net", "xn--n3h.net",
        "ジェ.jp", "straße.de", chr(127), chr(128), chr(127) + ".x",
        "  ", "1.2.3.4", "[::1]",
    ]
    for host in edge:
        # A-reference: isAscii model == real unicode_is_ascii
        real_ascii = bool(unicode_is_ascii(host))
        if model_isAscii(host) != real_ascii:
            print(f"MISMATCH isAscii edge {host!r}: model={model_isAscii(host)} real={real_ascii}")
            mismatches += 1
        # only the ASCII branch reaches startsWithInvalid in prepare_url
        if real_ascii and model_startsWithInvalid(host) != real_startsWithInvalid(host):
            print(f"MISMATCH startsWithInvalid edge {host!r}")
            mismatches += 1
        checked += 1

    # --- fuzz ---
    rnd = _lcg(SEED)
    for _ in range(N):
        length = next(rnd) % 11          # hosts 0..10 code points
        chars = []
        for _ in range(length):
            chars.append(_ALPHABET[next(rnd) % len(_ALPHABET)])
        host = "".join(chars)
        real_ascii = bool(unicode_is_ascii(host))
        if model_isAscii(host) != real_ascii:
            print(f"MISMATCH isAscii fuzz {host!r}: model={model_isAscii(host)} real={real_ascii}")
            mismatches += 1
            break
        if real_ascii and model_startsWithInvalid(host) != real_startsWithInvalid(host):
            print(f"MISMATCH startsWithInvalid fuzz {host!r}")
            mismatches += 1
            break
        checked += 1

    if mismatches:
        print(f"checked={checked} mismatches={mismatches}")
        print("status=fail")
        return 1
    print(f"checked={checked} mismatches=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
