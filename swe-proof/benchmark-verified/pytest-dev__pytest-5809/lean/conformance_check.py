#!/usr/bin/env python3
"""G-CONF for pytest-dev__pytest-5809.

The gold patch is already applied to /testbed when this runs, so
`_pytest.pastebin.create_new_paste` builds `params = {"code": contents,
"lexer": "text", "expiry": "1week"}`. We compare the R/I Python shadow of
`implementation_buildPasteParams` (the Lean impl, transliterated op-for-op per
refinement.md) against the REAL patched parameter mapping, recovered by stubbing
`urllib.request.urlopen` to capture the encoded request body (exactly the way the
FAIL_TO_PASS test mocks the network), over >=1e5 fuzzed `contents` inputs.
Zero disagreements => exit 0.

Type bijection (mapping.md):
  contents : String                 <->  the `contents` argument carried to params["code"]
  result   : List (String × String) <->  the `params` dict as ordered (key,value) pairs

stdlib-only; no hypothesis required.
"""
import random
import sys
from urllib.parse import parse_qsl, urlencode


def oracle(contents):
    """Real patched behavior: call create_new_paste with urlopen stubbed to
    capture the encoded body, then decode it back into ordered (key,value)
    pairs. Returns the list of pairs in submission order."""
    import _pytest.pastebin as pastebin

    captured = {}

    class DummyResponse:
        def read(self):
            # a normal-looking response so the regex finds an id and the
            # function returns without error
            return b'View <a href="/raw/abc123def0">raw</a>.'

    def fake_urlopen(url, data=None):
        captured["url"] = url
        captured["data"] = data
        return DummyResponse()

    import urllib.request
    real = urllib.request.urlopen
    urllib.request.urlopen = fake_urlopen
    try:
        pastebin.create_new_paste(contents)
    finally:
        urllib.request.urlopen = real

    body = captured["data"].decode("ascii")
    # parse_qsl preserves order of the encoded body; the dict was encoded in
    # insertion order (Python >=3.7), so this recovers the ordered pairs.
    return parse_qsl(body, keep_blank_values=True)


def shadow(contents):
    """R/I transliteration of implementation_buildPasteParams (Lean)."""
    params = []
    params = params + [("code", contents)]
    params = params + [("lexer", "text")]
    params = params + [("expiry", "1week")]
    return params


def normalize_shadow(pairs):
    """The oracle recovers values through urlencode/parse_qsl, which is a
    faithful identity on the (key,value) text for our payloads. To compare on
    equal footing we round-trip the shadow's pairs through the same encoding."""
    return parse_qsl(urlencode(pairs), keep_blank_values=True)


def rand_contents(rng):
    r = rng.random()
    if r < 0.1:
        return ""
    if r < 0.2:
        return "full-paste-contents"  # the F2P payload
    n = rng.randint(1, 120)
    # printable ascii incl. spaces, plus a few unicode code points
    pool = [chr(c) for c in range(32, 127)] + ["é", "λ", "中", "\n", "\t", "&", "=", "%"]
    return "".join(rng.choice(pool) for _ in range(n))


def main():
    rng = random.Random(5809)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        contents = rand_contents(rng)
        o = oracle(contents)
        s = normalize_shadow(shadow(contents))
        if o != s:
            disagreements += 1
            if first is None:
                first = (contents, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
