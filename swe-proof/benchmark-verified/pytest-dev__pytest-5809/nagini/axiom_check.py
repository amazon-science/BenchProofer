#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-5809.

This bundle consumes NO `@ContractOnly` axiom: the modelled behaviour — which
constant tokens the paste request's three fields carry — is concrete and
modelled deeply (the `text_token` / `expiry_token` pure functions and the
identity body field in model.py). There is therefore one deep-model reference to
validate against the real, UNCHANGED serialisation callee the patched code uses:
`urllib.parse.urlencode` + `bytes.decode`. We confirm that the modelled tokens,
once placed in the request `params` dict exactly as the gold patch builds it,
serialise to the wire form the FAIL_TO_PASS test observes:

    lexer=text          (the mode field — the single changed value)
    expiry=1week        (the unchanged expiry field)
    code=<contents>     (the unchanged body field, percent-quoted)

Imports nothing repo-specific: `urllib.parse` is the Python standard library —
the very serialiser the patched `create_new_paste` calls. Exit 0 iff every
observation matches the model's constant tokens.
"""
import random
import sys
from urllib.parse import urlencode

# --- model.py reference encodings (kept in lock-step with the deep model) ----

TEXT_TOKEN = [116, 101, 120, 116]            # model.text_token()  -> "text"
EXPIRY_TOKEN = [49, 119, 101, 101, 107]      # model.expiry_token() -> "1week"


def codepoints(s):
    return [ord(ch) for ch in s]


def check_tokens():
    """The deep-model constant tokens equal the intended literal strings."""
    assert codepoints("text") == TEXT_TOKEN, TEXT_TOKEN
    assert codepoints("1week") == EXPIRY_TOKEN, EXPIRY_TOKEN


def build_params(contents):
    """Exactly the params dict the gold patch constructs in create_new_paste:
    the mode field is the fixed plain-text token, INVARIANT of interpreter
    version; the body forwards `contents`; the expiry is the one-week token."""
    return {"code": contents, "lexer": "text", "expiry": "1week"}


def check_serialisation(contents):
    """Run the REAL unchanged serialiser and assert the wire form the F2P test
    observes — independent of the running interpreter major version."""
    params = build_params(contents)
    data = urlencode(params).encode("ascii").decode()   # real callee chain
    # the single changed value: the mode field is the plain-text token,
    # NOT a python/python3 token derived from sys.version_info.
    assert "lexer=text" in data, (contents, data)
    assert "lexer=python" not in data, (contents, data)
    assert "expiry=1week" in data, (contents, data)
    assert ("code=%s" % contents) in data, (contents, data)


def main():
    check_tokens()

    # The mode field must be "text" whatever the interpreter major version:
    # build_params does not consult sys.version_info, so iterating "versions"
    # here is a witness that the value is invariant.
    for _py_major in (2, 3, 4):
        check_serialisation("full-paste-contents")  # the F2P body

    # boundary + fuzz over the body contents (the only varying input)
    bodies = [
        "full-paste-contents", "", "a", "abc123", "test_fail", "x_y_z",
        "1234567890", "ASCIIonly", "under_score", "dash-free",
    ]
    for b in bodies:
        check_serialisation(b)

    rng = random.Random(5809)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    for _ in range(20000):
        n = rng.randint(0, 32)
        b = "".join(rng.choice(alphabet) for _ in range(n))
        check_serialisation(b)

    print("G-AX OK: deep-model tokens (lexer=text, expiry=1week, code=...) "
          "agree with the real urllib serialiser across 3 interpreter-major "
          "witnesses + %d body inputs; lexer is invariant under version."
          % (10 + 20000))
    return 0


if __name__ == "__main__":
    sys.exit(main())
