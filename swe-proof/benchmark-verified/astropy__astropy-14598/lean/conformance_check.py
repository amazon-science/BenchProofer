#!/usr/bin/env python3
"""G-CONF — cross-language differential test for astropy__astropy-14598.

Oracle  : the REAL post-patch parsing pipeline of `Card._split`'s per-subcard
          value branch, reproduced verbatim from the patched source —
              m = _strg_comment_RE.match(vc)            # fixed (anchored) pattern
              if not m: <verbatim>                      # -> Lean `none`
              value = m.group("strg") or ""
              value = value.rstrip()                    # NO .replace("''","'")
              if value and value[-1] == "&": value = value[:-1]
Shadow  : the R/I transcription of `implementation_splitValue` in Solution.lean
          (matchQuotedFixed -> dropTrailingWs -> dropTrailingAmp), built here in
          pure Python and bridged via mapping.md (str <-> List Char).

We fuzz >=1e5 segment strings `vc` over the FITS-card printable alphabet and
assert the shadow agrees with the oracle on every input. Exit 0 iff zero
disagreements. stdlib-only.
"""
import re
import random
import sys

# ---- oracle: the real fixed regex + cleanup (post-patch card.py) -------------
_strg = r"\'(?P<strg>([ -~]+?|\'\'|) *?)\'(?=$|/| )"
_comm_field = r"(?P<comm_field>(?P<sepr>/ *)(?P<comm>(.|\n)*))"
_strg_comment_RE = re.compile(f"({_strg})? *{_comm_field}?$")   # the '$' is the fix


def oracle(vc):
    """Returns the recovered value (str), or None when the segment doesn't match
    (the patched code does `if not m: return kw, vc` -> caller keeps it verbatim).
    None corresponds to Lean `none`; a str corresponds to `some <chars>`."""
    m = _strg_comment_RE.match(vc)
    if not m:
        return None
    value = m.group("strg") or ""
    value = value.rstrip()
    if value and value[-1] == "&":
        value = value[:-1]
    return value


# ---- shadow: R/I transcription of implementation_splitValue ------------------
def is_printable(c):
    return 32 <= ord(c) <= 126


def is_ws(c):
    return ord(c) in (32, 9, 10, 13, 11, 12)


def drop_trailing_ws(s):
    i = len(s)
    while i > 0 and is_ws(s[i - 1]):
        i -= 1
    return s[:i]


def drop_trailing_amp(s):
    if s and s[-1] == "'":
        pass
    return s[:-1] if s and s[-1] == "&" else s


def remainder_ok(rest):
    j = 0
    while j < len(rest) and rest[j] == " ":
        j += 1
    return j == len(rest) or rest[j] == "/"


def scan_fixed(body):
    acc = []
    i = 0
    while i < len(body):
        c = body[i]
        rest = body[i + 1:]
        if c == "'" and acc and remainder_ok(rest):
            return "".join(acc)
        if is_printable(c):
            acc.append(c)
            i += 1
        else:
            return None
    return None


def match_quoted_fixed(vc):
    if vc[:1] == "'":
        body = vc[1:]
        s = scan_fixed(body)
        if s is not None:
            return s
        if body[:1] == "'" and remainder_ok(body[1:]):
            return ""
        return None
    # no leading quote
    return "" if remainder_ok(vc) else None


def shadow(vc):
    strg = match_quoted_fixed(vc)
    if strg is None:
        return None
    value = drop_trailing_ws(strg)
    value = drop_trailing_amp(value)
    return value


# ---- fuzz --------------------------------------------------------------------
ALPHABET = list("xyz'/ &~AB12-q")
SEED = 14598
N = 200_000


def rand_vc(rng):
    L = rng.randint(0, 14)
    pre = rng.choice(["'", "x", "/", " ", ""])
    return pre + "".join(rng.choice(ALPHABET) for _ in range(L))


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    # deterministic boundary seeds
    seeds = [
        "", "'", "''", "'x'", "'x&'", "'xx''&'", "'xx'' xxx'", "'xx''xxx'",
        "'xxxxxxxx&'", "'xxx' / a comment", "/ comment", "'xx", "'", "x",
        "''xxx'", "'' xxx", "'a''b''c'", "'a''&'",
    ]
    n = 0
    for vc in seeds:
        n += 1
        if shadow(vc) != oracle(vc):
            disagreements += 1
            if len(examples) < 20:
                examples.append((vc, shadow(vc), oracle(vc)))
    for _ in range(N):
        vc = rand_vc(rng)
        n += 1
        if shadow(vc) != oracle(vc):
            disagreements += 1
            if len(examples) < 20:
                examples.append((vc, shadow(vc), oracle(vc)))
    print(f"status={'ok' if disagreements == 0 else 'fail'} "
          f"tested={n} disagreements={disagreements} seed={SEED}")
    for vc, sh, oc in examples:
        print(f"  MISMATCH vc={vc!r} shadow={sh!r} oracle={oc!r}")
    sys.exit(0 if disagreements == 0 else 1)


if __name__ == "__main__":
    main()
