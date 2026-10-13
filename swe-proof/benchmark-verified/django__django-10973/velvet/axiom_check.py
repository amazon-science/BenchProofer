#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-10973.

This bundle has NO consumed axiom: the post-patch behaviour (the password is
exposed to the child VERBATIM, `str(passwd)`) is modeled deeply as the identity
copy in Solution.lean's impl loop, and consumes no callee contract.

The one kind-A object is an **A-reference**: the legacy per-code-point quoting
fold `pgpassQuoteSeq` (with `pgpassQuote`) that the *prepatch* skeleton applies,
which models the removed module-level helper `_escape_pgpass` at base_commit:

    def _escape_pgpass(txt):
        return txt.replace('\\', '\\\\').replace(':', '\\:')

G-AX validates that deep model against the real removed helper (reproduced
verbatim below — it is deleted by the patch, so it is not importable from the
patched repo) on boundary + fuzz inputs, AND witnesses that the post-patch
verbatim exposure DIVERGES from that legacy quoting exactly on the discriminators
the F2P tests pin (`:` and `\\`). Exit 0 iff every obligation holds. Imports only
the standard library.
"""
import random
import sys


# --- the removed helper, reproduced verbatim (deleted by patch.diff) ---------
def _escape_pgpass(txt):
    """Escape a fragment of a PostgreSQL .pgpass file. (client.py:9-13 @ base.)"""
    return txt.replace('\\', '\\\\').replace(':', '\\:')


# --- the deep model from Solution_prepatch.lean's impl region (A-reference) ---
def pgpass_quote(c):
    """pgpassQuote (Char -> List Char): the per-code-point quoting.
    '\\' -> '\\\\'  ;  ':' -> '\\:'  ;  else identity."""
    if c == '\\':
        return '\\\\'
    if c == ':':
        return '\\:'
    return c


def pgpass_quote_seq(s):
    """pgpassQuoteSeq: concatenate the per-code-point quoting (forward fold)."""
    return "".join(pgpass_quote(c) for c in s)


# --- the post-patch verbatim exposure (the spec core, A2/A3) ------------------
def verbatim(s):
    """The post-patch model: the value exposed for the password is `s` verbatim."""
    return s


def check_reference(s):
    """A-reference: the deep model pgpass_quote_seq(s) == the REAL removed
    _escape_pgpass(s)."""
    assert pgpass_quote_seq(s) == _escape_pgpass(s), (
        "pgpassQuoteSeq deep model unsound on %r: _escape_pgpass gave %r, "
        "deep model gives %r" % (s, _escape_pgpass(s), pgpass_quote_seq(s)))


def main():
    discriminators = [':', '\\']
    ordinary = list("aZ0 ;#@quotlgmp") + ['é', '•']

    # --- A-reference: boundary cases ----------------------------------------
    boundary = [""]
    boundary += discriminators
    boundary += [c + c for c in discriminators]
    boundary += [
        "some:password",            # F2P test_column password
        "sésame",                   # F2P test_accent password
        "somepassword",             # F2P test_basic password
        ":\\:", "\\:", ":\\",
        "a:b:c", "back\\slash",
        "host:444:db:user:pw",
        "::1",                      # the test_column host
    ]
    for s in boundary:
        check_reference(s)

    # --- A-reference: randomized fuzz ---------------------------------------
    rng = random.Random(10973)
    alphabet = discriminators + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_reference(s)

    # --- spec core (A2): post-patch value is the password verbatim ----------
    for s in boundary:
        assert verbatim(s) == s, "verbatim exposure altered %r" % (s,)

    # --- divergence witnesses: verbatim != legacy quoting on the F2P cases ---
    # The whole point of the change: a colon/backslash password is exposed raw,
    # NOT pgpass-quoted. These are exactly what test_column / the bug pin.
    assert verbatim("some:password") == "some:password"
    assert pgpass_quote_seq("some:password") == "some\\:password"
    assert verbatim("some:password") != pgpass_quote_seq("some:password"), (
        "verbatim exposure must differ from legacy quoting on a colon password")
    assert verbatim("back\\slash") != pgpass_quote_seq("back\\slash"), (
        "verbatim exposure must differ from legacy quoting on a backslash password")
    # and they AGREE on inputs with neither discriminator (no transformation)
    assert verbatim("somepassword") == pgpass_quote_seq("somepassword")
    assert verbatim("sésame") == pgpass_quote_seq("sésame")

    print("G-AX OK: pgpassQuoteSeq deep model (== removed _escape_pgpass) sound "
          "on %d boundary + 20000 fuzz inputs; post-patch verbatim exposure "
          "diverges from legacy quoting exactly on ':'/'\\\\' (F2P discriminators)."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
