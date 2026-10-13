#!/usr/bin/env python3
"""G-CONF differential conformance check for psf__requests-2317 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The stripped Assert lines
were the only place the impl region touched PSeq/ToSeq, so no sequence shim is
needed: the executable content is a plain forward copy loop over List[int].
There are no @Pure helpers and no @ContractOnly callees in this bundle (the
axioms region is empty; the changed operation is modeled deeply).

ORACLE: the REAL patched repo callee the model models per mapping.md —
`requests.utils.to_native_string`, the coercion the patched
`requests.sessions.Session.request` applies to the `method` token. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched package importable. The import must succeed — no inline
fallback, so the diff is always against the real repo function.

Type bridge (mapping.md section 2): a method token that is either a native
text string or an ASCII byte string maps to `content: List[int]` of its
character / byte values plus `is_bytes: bool`. Both real carriers are
exercised for every generated `content`: the text form
``''.join(chr(v) for v in content)`` and the byte form ``bytes(content)``.
The oracle's native-text result is lifted back to code points via `ord` and
compared against the shadow's List[int] exactly.

Input domain: the model Requires admits every value 0 <= v < 128 with
v != 39 and v != 92. Generation draws only from that alphabet (boundary HTTP
method tokens, an exhaustive single-value sweep of the whole alphabet, and
randomized fuzz tokens of length 0..24), so every input is
Requires-satisfying by construction and is re-checked before use.

>= 1e5 Requires-satisfying inputs: 14 boundary + 126 sweep + 100000 fuzz
tokens, each diffed as BOTH the text and the byte carrier (2 oracle calls per
token). Pinned fuzz seed: 2317.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 2317
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def native_method(content, is_bytes):
    result = []  # type: list
    j = 0
    n = len(content)
    while j < n:
        result = result + [content[j]]
        j = j + 1
    return result


# --- the model Requires domain -------------------------------------------------
# model.py pre-conditions: every value 0 <= v < 128 and v != 39 and v != 92.

def in_requires_domain(values):
    return all(0 <= v < 128 and v != 39 and v != 92 for v in values)


DOMAIN = [v for v in range(0, 128) if v not in (39, 92)]


# --- differential check of one token --------------------------------------------

def check_token(to_native_string, content):
    """Diff the shadow against the real callee on both the text and the byte
    form of one token; return an error string on disagreement, else None."""
    assert in_requires_domain(content), (
        "generated token %r is outside the model Requires domain" % (content,))

    # text carrier
    method_str = "".join(chr(v) for v in content)
    real_text = [ord(ch) for ch in to_native_string(method_str)]
    shadow_text = native_method(content, False)
    if real_text != shadow_text:
        return ("DISAGREEMENT (text carrier)\n  content=%r\n  shadow=%r\n"
                "  real=%r" % (content, shadow_text, real_text))

    # byte carrier
    method_bytes = bytes(content)
    real_bytes = [ord(ch) for ch in to_native_string(method_bytes)]
    shadow_bytes = native_method(content, True)
    if real_bytes != shadow_bytes:
        return ("DISAGREEMENT (byte carrier)\n  content=%r\n  shadow=%r\n"
                "  real=%r" % (content, shadow_bytes, real_bytes))
    return None


def boundary_tokens():
    names = ["", "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH",
             "TRACE", "CONNECT", "get", "Post", "X", "GETGET"]
    return [[ord(ch) for ch in m] for m in names]


def main():
    from requests.utils import to_native_string  # REAL patched repo callee

    checked = 0
    boundary = boundary_tokens()
    for content in boundary:
        err = check_token(to_native_string, content)
        if err:
            print(err)
            return 1
        checked += 1

    # exhaustive single-value sweep of the whole Requires alphabet
    for v in DOMAIN:
        err = check_token(to_native_string, [v])
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 24)
        content = [rng.choice(DOMAIN) for _ in range(n)]
        err = check_token(to_native_string, content)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real coercion on %d tokens "
          "(%d boundary + %d sweep + %d fuzz, seed %d), each as both "
          "text and byte carriers." % (checked, len(boundary), len(DOMAIN),
                                       N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
