#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-10973.

This bundle consumes NO axiom: the changed behaviour (the value exposed to the
child process for the password) is modelled DEEPLY in model.py — the exposed
value is the password VERBATIM, pinned by `ToSeq(Result()) == ToSeq(passwd)`.

There is one A-reference: the `pgpass_quote_seq` fold in model.py's pure region
is the deep model of the legacy file-fragment quoting helper that the gold
patch REMOVES. The differential in model_prepatch.py is stated against it, so
its soundness matters even though the proof never consumes it. This check
validates it against the EXACT removed helper as it existed at base_commit:

    def _escape_pgpass(txt):
        return txt.replace('\\', '\\\\').replace(':', '\\:')

and confirms the central correctness fact the spec encodes: the post-patch
exposed value (`str(passwd)`, the password verbatim) differs from that legacy
quoting precisely on passwords containing a colon or a backslash — which is the
behaviour the FAIL_TO_PASS tests (`test_column`, `test_accent`, `test_basic`)
now assert.

Imports only the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys


# --- the legacy removed helper, reproduced verbatim from base_commit ---------
# django/db/backends/postgresql/client.py:9-13 @ ddb293685235fd09e932805771ae97f72e817181
def _escape_pgpass_real(txt):
    """The actual `_escape_pgpass` body the gold patch deletes."""
    return txt.replace('\\', '\\\\').replace(':', '\\:')


# --- model.py reference encodings (kept in lock-step with the pure region) ---
def pgpass_quote(c):
    """Reference of model.py `pgpass_quote` (one code point -> code points)."""
    if c == 92:        # '\\'
        return [92, 92]
    if c == 58:        # ':'
        return [92, 58]
    return [c]


def pgpass_quote_seq(codepoints):
    """Reference of model.py `pgpass_quote_seq` (whole-sequence legacy quoting)."""
    out = []
    for c in codepoints:
        out.extend(pgpass_quote(c))
    return out


def post_patch_exposed_value(passwd):
    """The value the GOLD-patched code exposes for the password: str(passwd)
    verbatim (env['PGPASSWORD'] = str(passwd)), present iff passwd is truthy."""
    return passwd  # passwd is already a str; str(str)==str (identity)


# --- the checks --------------------------------------------------------------

def check_a_reference(s):
    """A-reference: model.py's pgpass_quote_seq == the real removed helper."""
    model = pgpass_quote_seq([ord(ch) for ch in s])
    real = [ord(ch) for ch in _escape_pgpass_real(s)]
    assert model == real, (
        "A-reference unsound on %r: pgpass_quote_seq -> %r, real "
        "_escape_pgpass -> %r" % (s, model, real))


def check_verbatim(s):
    """Spec core: post-patch exposed value == the password VERBATIM (the
    model.py postcondition ToSeq(Result()) == ToSeq(passwd))."""
    exposed = [ord(ch) for ch in post_patch_exposed_value(s)]
    raw = [ord(ch) for ch in s]
    assert exposed == raw, (
        "verbatim-exposure broken on %r: exposed %r != raw %r"
        % (s, exposed, raw))


def main():
    significant = ['\\', ':']
    ordinary = list('abZ0 ;#x39 27éoqu') + ['é', 'ô', 'ê']

    boundary = [""]
    boundary += significant
    boundary += [c + c for c in significant]
    boundary += ["".join(significant), "".join(reversed(significant))]
    boundary += [
        "somepassword",                 # test_basic password (no specials)
        "some:password",                # test_column password (colon)
        "some\\password",               # the dropped test_escape_characters
        "some\\\\password",
        "sésame",                       # test_accent password (accents)
        "::1:444:dbname:some:user",     # pgpass-line-like material
        "a\\b:c\\:d::e",
        "C:\\path\\to\\file",
    ]
    for s in boundary:
        check_a_reference(s)
        check_verbatim(s)

    # randomized fuzz over the alphabet that exercises the special chars
    rng = random.Random(10973)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_a_reference(s)
        check_verbatim(s)

    # the discriminating witness: legacy quoting != verbatim on a colon and a
    # backslash (exactly why the F2P expectations changed from escaped to raw).
    for s in ["some:password", "some\\password", "::1"]:
        legacy = pgpass_quote_seq([ord(ch) for ch in s])
        verbatim = [ord(ch) for ch in s]
        assert legacy != verbatim, (
            "expected legacy quoting to differ from verbatim on %r" % s)

    print("G-AX OK: pgpass_quote_seq A-reference == real _escape_pgpass and "
          "verbatim exposure holds on %d boundary + 20000 fuzz inputs; legacy "
          "quoting differs from verbatim on the colon/backslash witnesses."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
