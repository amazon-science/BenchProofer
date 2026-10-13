#!/usr/bin/env python3
"""G-CONF for sympy__sympy-16886.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_encodeMorse` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `encode_morse`, over
>=1e5 fuzzed messages. Zero disagreements => exit 0.

Modeled domain (mapping.md): a message whose characters are all printable ASCII
(32..126) or ASCII blanks (9..13), and a separator SEQUENCE of any length that is
not a single character the table already keys (the real encoder asserts
`sep not in mapping`, and its `mapping[" "] = 2*sep` mutation makes a lone space
separator fail too). On that domain the real `encode_morse(msg, sep)` is the
word-level assembly the Lean impl performs: split the message at ASCII blanks,
drop each character the table has no entry for, drop a word that retains nothing,
join a word's code words with ONE copy of `sep`, join the words with TWO copies,
and append one more doubled `sep` when the message ends in a blank.

  * Oracle  = the REAL patched `sympy.crypto.crypto.encode_morse(msg, sep=sep)`.
  * Shadow  = the op-for-op transliteration below (Lean: the two flat loops over
              `wordRuns msg` and `kept`), with codeOf = the A-reference REAL
              char_morse.

IMPORTANT — the oracle is called with a FRESH mapping each time. The real
`encode_morse` MUTATES the module-global `char_morse` (`mapping[" "] = 2*sep`),
so calls leak state into one another; passing a fresh copy is what makes each
fuzz case an independent measurement of the function rather than of call order.
The mutation itself is the reason a lone-space separator is excluded above.

Type bijection (mapping.md): msg:List Char <-> msg:str (per code point);
sep:List Char <-> sep:str (per code point, any length); result:List Char <->
returned str (per code point); codeOf c <-> char_morse[c].

stdlib-only; pinned seed 16886.
"""
import json
import random
import string
import sys

from sympy.crypto.crypto import char_morse, encode_morse

SEED = 16886
N = 100_000

# The ASCII blanks, which is exactly what `str.split()` breaks on inside the
# modeled domain and what `string.whitespace` tests for at the tail.
BLANKS = "".join(chr(c) for c in (32, 9, 10, 11, 12, 13))

# The characters the encoding is specified over.
MODELED = "".join(chr(c) for c in range(32, 127)) + "".join(
    chr(c) for c in range(9, 14))

# A snapshot of the REAL table's keys, taken BEFORE any call mutates it.
TABLE = dict(char_morse)
SUPPORTED = sorted(TABLE.keys())

# Characters usable inside a separator. A separator of length != 1 is
# unrestricted, so the only exclusions bite at length 1; we draw from characters
# that are safe either way.
SEP_CHARS = [c for c in string.printable
             if c not in TABLE and c not in BLANKS and c.isprintable()]


def fresh_mapping():
    """A private copy of the real table, so one call cannot perturb the next."""
    return dict(TABLE)


def oracle(msg, sep):
    """The REAL patched encoder, on a fresh mapping (see module docstring)."""
    return encode_morse(msg, sep=sep, mapping=fresh_mapping())


def shadow(msg, sep):
    """R/I transliteration of implementation_encodeMorse (Lean).

    Op 1 (`wordRuns msg`): split the message at every ASCII blank, keeping the
          empty words a run of blanks produces.
    Op 2 (the `kept` loop): within each word keep only the characters the
          A-reference table has an entry for; drop a word that retains nothing.
    Op 3 (the `encoded` loop): render each surviving word as its code words
          joined by ONE copy of the separator.
    Op 4 (the return): join the encoded words by TWO copies of the separator,
          then append one more doubled separator when the message ends in a
          blank (`endsInWordBreak msg`).
    """
    runs = [[]]
    for c in msg:
        if c in BLANKS:
            runs.append([])
        else:
            runs[-1].append(c)
    kept = []
    for w in runs:
        supported = [c for c in w if c in TABLE]
        if supported:
            kept.append(supported)
    encoded = [sep.join(TABLE[c] for c in w) for w in kept]
    tail = (sep + sep) if (msg and msg[-1] in BLANKS) else ""
    return (sep + sep).join(encoded) + tail


def rand_msg(rng):
    n = rng.randint(0, 14)
    # Bias toward supported characters and blanks so words, word breaks and
    # dropped characters all occur often, while still drawing from the whole
    # modeled range.
    pool = SUPPORTED * 6 + list(BLANKS) * 3 + list(MODELED)
    return "".join(rng.choice(pool) for _ in range(n))


def rand_sep(rng):
    n = rng.choice([0, 1, 1, 1, 2, 2, 3])
    return "".join(rng.choice(SEP_CHARS) for _ in range(n))


def main() -> int:
    rng = random.Random(SEED)
    disagreements = []

    # Boundary / graded-assertion-flavored cases: the digit words the change
    # pins, the multi-word and trailing-blank shapes, the all-unsupported
    # message, the empty message, and the empty / multi-character separators.
    fixed_msgs = ["12345", "67890", "0", "1", "9", "ABC", "HELLO",
                  "", " ", "  ", "SMS ", "SMS\n", "SMS\t", "A B", "A  B",
                  "!@#$%^&*()_+", "A%B", "%", "% %", " A ", "\tA\tB\t",
                  "".join(SUPPORTED)]
    fixed_seps = ["", "|", "`", "``", "|||", "#", "~", "^", "%", "#~", "\t"]
    cases = [(w, s) for w in fixed_msgs for s in fixed_seps]
    for _ in range(N):
        cases.append((rand_msg(rng), rand_sep(rng)))

    checked = 0
    for msg, sep in cases:
        try:
            o = oracle(msg, sep)
        except Exception as e:  # pragma: no cover - should not happen on domain
            disagreements.append({"msg": msg, "sep": sep, "error": repr(e)})
            if len(disagreements) >= 10:
                break
            continue
        s = shadow(msg, sep)
        checked += 1
        if o != s:
            disagreements.append({"msg": msg, "sep": sep,
                                  "oracle": o, "shadow": s})
            if len(disagreements) >= 10:
                break

    status = "pass" if not disagreements else "fail"
    print(json.dumps({
        "status": status,
        "instance": "sympy__sympy-16886",
        "checked": checked,
        "seed": SEED,
        "disagreements": disagreements[:10],
    }))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
