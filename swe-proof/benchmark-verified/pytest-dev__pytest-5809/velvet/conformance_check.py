#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5809 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`buildUploadParams` / the `UploadParams` construction)
              transliterated to Python over the *real* repo types, via the
              mapping.md bijection (`List Char` ↔ str/bytes; the three submitted
              fields code/lexer/expiry).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `_pytest.pastebin.create_new_paste(contents)` applied at
              base_commit (the real correctness oracle, G-RESOLVE). The network
              call is mocked exactly as the F2P test mocks it; the parameters
              the function actually submits (urlencoded POST body) are parsed
              back and compared field-by-field.

The impl region has NO A-tagged content (no axiomatized callees — the submitted
mapping is built entirely from `contents` plus fixed labels), so the shadow is
pure R/I. They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image); stdlib + the pytest
source under test (already installed). The fuzz seed is pinned (mapping.md §4)
for a deterministic verdict.
"""
import random
import sys
from urllib.parse import parse_qs

SEED = 5809
N_FUZZ = 100_000


def shadow_params(contents):
    """buildUploadParams transliterated: the per-input parameter mapping the
    UploadParams construction encodes (mapping.md §2). `contents` is the uploaded
    payload (bytes). The three submitted fields:
        code   = contents (carried verbatim)
        lexer  = "text"   (generic plain-text label)
        expiry = "1week"  (fixed retention label)
    """
    return {"code": contents, "lexer": "text", "expiry": "1week"}


def _make_oracle():
    """Build the ORACLE callable around the patched create_new_paste.

    Importing the module exercises the *patched* repo source (the harness has
    applied patch.diff at base_commit before this runs). The function performs a
    network POST; we monkeypatch urlopen (exactly as testing/test_pastebin.py
    does) to capture the urlencoded body and return a well-formed dummy response
    so the function completes. We then parse the captured body back into a params
    mapping — the observable the F2P test inspects."""
    import _pytest.pastebin  # noqa: F401  (ensure the patched module imports)

    captured = {}

    class _DummyResp(object):
        def read(self):
            # A minimal well-formed response so create_new_paste returns a URL.
            return b'View <a href="/raw/3c0c6750bd">raw</a>.'

    def _mock_urlopen(url, data):
        captured["url"] = url
        captured["data"] = data
        return _DummyResp()

    # create_new_paste does a *local* `from urllib.request import urlopen`, so we
    # patch the attribute on urllib.request (Python 3 in this image; the F2P test
    # does the same).
    import urllib.request

    def oracle(contents):
        captured.clear()
        orig = urllib.request.urlopen
        urllib.request.urlopen = _mock_urlopen
        try:
            from _pytest.pastebin import create_new_paste
            create_new_paste(contents)
        finally:
            urllib.request.urlopen = orig
        # Parse the urlencoded POST body back into a {field: value} mapping.
        body = captured["data"].decode("ascii")
        qs = parse_qs(body, keep_blank_values=True)
        # parse_qs yields lists; the params are single-valued.
        return {k: v[0] for k, v in qs.items()}

    return oracle


def fuzz_inputs(n, rng):
    # Boundary cases first (plan §4.1 step 4): the F2P payload, empty, and
    # payloads whose characters stress urlencoding (spaces, '+', '%', '&', '=',
    # newlines, non-ascii via utf-8 — mirroring captured console output).
    yield b"full-paste-contents"
    yield b""
    yield b"def test_fail():\n    assert 0\n"
    yield b"a=b&c=d lexer=python3 code=x%20+y"
    yield "non-ascii ☺ é".encode("utf-8")
    alphabet = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        " \t\n\r+%&=?#/\\\"'<>:;.,_-"
    )
    for _ in range(n):
        kind = rng.random()
        if kind < 0.7:
            length = rng.randint(0, 60)
            s = "".join(rng.choice(alphabet) for _ in range(length))
            yield s.encode("utf-8")
        else:
            # arbitrary utf-8 (incl. non-ascii code points like console output)
            length = rng.randint(0, 30)
            s = "".join(chr(rng.randint(0, 0x2FFF)) for _ in range(length))
            yield s.encode("utf-8")


def _expected_qs(contents):
    """The shadow params re-encoded the way the real function would observe them
    after urlencode→parse_qs, so the comparison is on the *parsed* body the test
    inspects. urlencode percent-encodes; parse_qs decodes back to the original
    string. `contents` (bytes) round-trips to its latin/utf-8 text form exactly
    as urlencode(bytes) → parse_qs does."""
    sp = shadow_params(contents)
    # urlencode encodes bytes by treating each byte; parse_qs returns the decoded
    # str. To mirror that for `code`, decode the bytes the same way parse_qs will
    # (it decodes percent-escapes to bytes then utf-8). We compute the expected
    # by running the same urlencode/parse_qs round trip on the shadow mapping.
    from urllib.parse import urlencode
    body = urlencode(sp).encode("ascii").decode("ascii")
    qs = parse_qs(body, keep_blank_values=True)
    return {k: v[0] for k, v in qs.items()}


def main():
    rng = random.Random(SEED)
    oracle = _make_oracle()
    disagreements = []
    count = 0
    for contents in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = _expected_qs(contents)
        try:
            orc = oracle(contents)
        except Exception as e:  # pragma: no cover
            disagreements.append((contents, "ERROR: %r" % e, None))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != orc:
            disagreements.append((contents, shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for contents, sh, orc in disagreements:
            print("  contents=%r shadow=%r oracle=%r" % (contents[:40], sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildUploadParams agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
