#!/usr/bin/env python3
"""G-CONF for django__django-15503.

Differential test: the R/I Python shadow of `implementation_keyLookupPath`
(Solution.lean) vs. the REAL patched RHS JSON-path assembly in
`django/db/models/fields/json.py`. The orchestrator applies the gold patch
before running this, so the imported callees are the post-patch versions.

The carrier takes THREE inputs — `byName`, the path prefix, and the non-empty
key list — because the assembly must be able to address the FINAL step in
either of two forms, selected by the enquiry rather than by the step text:

  * byName = True  — the enquiry asks whether the document carries a MEMBER OF
    A GIVEN NAME, so the final step is addressed by member name whatever its
    text reads as;
  * byName = False — the enquiry asks about whichever location the final step's
    text denotes, so it is addressed exactly like an intermediate step (a text
    reading as a base-10 integer becomes the bracketed positional step).

The repository has one real callee per form, reached through the same
dispatchable hook, and BOTH legs are checked here: a shadow that agreed with
only one of them would leave the other form unconstrained, which is exactly the
observable the spec now pins.

Oracle (post-patch per-key body of the membership-lookup SQL compiler):
    *rhs_key_transforms, final_key = rhs_key_transforms
    rhs_json_path  = compile_json_path(rhs_key_transforms, include_root=False)
    rhs_json_path += self.compile_json_path_final_key(final_key)
    rhs_params.append(lhs_json_path + rhs_json_path)
with `self` drawn from the by-name lookup class when byName is True and from
the denoted-location lookup class when it is False, so the oracle exercises the
hook's dispatch rather than one hardwired branch.

Type bridge (mapping.md): a key `str` <-> Lean `String`; `rhs_key_transforms`
(`list[str]`) <-> `List String`; the addressing-form selector `bool` <-> `Bool`;
the assembled path `str` <-> `String`. `encodeKey` <-> `json.dumps`, used
identically on both legs (it cancels) — we bind the shadow's `encode_key` to
`json.dumps` so the comparison isolates the positional-vs-named routing.

Digit budget. The real integer read is `int(text)`, which on this interpreter
refuses a text carrying more than `sys.get_int_max_str_digits()` decimal digits
and raises instead of returning a value — so such a text is NOT positional and
is addressed by member name like any other. `numeric_key` below carries that
bound (Lean `maxParseDigits`), and the fuzz alphabet straddles it (a text at the
bound, one just over, and one over with underscore separators) so the leg is
actually exercised rather than merely written down.

Digit alphabet. `int()` reads a decimal digit from ANY script — the Unicode
`Nd` general category — and nothing outside it, so a character is tested with
`unicodedata.category(c) == "Nd"` rather than with `str.isdigit()`, which is
also true of characters (superscripts, for instance) that `int()` rejects. The
alphabet includes both a non-ASCII `Nd` run and a digit-like non-`Nd`
character, so a shadow that used the looser test would be caught here.

Exit 0 iff zero disagreements over >=1e5 fuzzed cases. stdlib + real django
callee only.
"""
import json
import random
import sys
import unicodedata

SEED = 15503
N_CASES = 200_000

# The interpreter's own bound on how many decimal digits a base-10 read will
# accept. Queried rather than hardcoded: the modeled bound must be the real
# one, and an interpreter without the bound reads any length.
try:
    MAX_PARSE_DIGITS = sys.get_int_max_str_digits()
except AttributeError:  # no bound on this interpreter
    MAX_PARSE_DIGITS = None

_OVER = (MAX_PARSE_DIGITS + 1) if MAX_PARSE_DIGITS else 5000
_AT = MAX_PARSE_DIGITS if MAX_PARSE_DIGITS else 4300

# key alphabet: digit runs (array-index-looking), leading zeros, mixed alnum,
# empty, plain names, the tricky base-10-read cases (sign, surrounding
# whitespace, underscore separators, doubled/edge underscores), non-ASCII
# decimal digits, a digit-LOOKING character that is not a decimal digit, and the
# digit-budget cliff — the full domain over which positional-vs-named
# addressing must agree with the real read.
ALPHABET = ["foo", "bar", "1111", "123", "000", "0", "a1", "", "12a", "ipsum",
            "9", "007", "nested", "array", "d",
            "-1", "+2", " 3 ", "1_0", "1_", "_1", "1__0", "\t5\t", " 42",
            "-0", "+00", "1_000", "12_", "0x1f", "  ", "  7  ",
            "٣", "١٢", "１０",          # non-ASCII Nd
            "²", "½",                                 # digit-like, not Nd
            "1" * _AT, "1" * _OVER, "0" * _OVER,
            "_".join("1" * _AT), "+" + "1" * _OVER]
PREFIXES = ["$", "$.a", "$[0]", '$."foo"', "$.nested[2]"]


def encode_key(k):
    """The opaque `encodeKey` — bound to the real json serializer (cancels)."""
    return json.dumps(k)


# Lean `isParseSpace`: the whitespace a base-10 read tolerates around its text.
_WS = ({0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x20, 0x85, 0xa0, 0x1680,
        0x2028, 0x2029, 0x202f, 0x205f, 0x3000}
       | set(range(0x2000, 0x200b)))


def _is_parse_space(c):
    return ord(c) in _WS


def _is_decimal_digit(c):
    """Lean `isDecimalDigit`: a decimal digit in any script (Unicode Nd)."""
    return unicodedata.category(c) == "Nd"


def _strip_space(cs):
    i, j = 0, len(cs)
    while i < j and _is_parse_space(cs[i]):
        i += 1
    while j > i and _is_parse_space(cs[j - 1]):
        j -= 1
    return cs[i:j]


def _valid_num_body(cs):
    """Lean `validNumBody`: a non-empty digit run with single underscores used
    strictly as separators, whose digits stay inside the read's digit budget."""
    if not cs:
        return False
    if not all(_is_decimal_digit(c) or c == "_" for c in cs):
        return False
    if not _is_decimal_digit(cs[0]) or not _is_decimal_digit(cs[-1]):
        return False
    if any(a == "_" and b == "_" for a, b in zip(cs, cs[1:])):
        return False
    if MAX_PARSE_DIGITS is None:
        return True
    return sum(1 for c in cs if _is_decimal_digit(c)) <= MAX_PARSE_DIGITS


def numeric_key(s):
    """R/I transliteration of Lean `numericKey` (Solution.lean): trim
    parse-whitespace and an optional sign, accept a digit run with single
    underscore separators inside the digit budget, and read its base-10 value.
    Modeled to match the real `int(s)` over the fuzz domain; G-CONF checks that
    against the real callee's read."""
    cs = _strip_space(list(s))
    if not cs:
        return None
    c = cs[0]
    if c == "-":
        sign, body = -1, cs[1:]
    elif c == "+":
        sign, body = 1, cs[1:]
    else:
        sign, body = 1, cs
    if not _valid_num_body(body):
        return None
    return sign * int("".join(ch for ch in body if ch != "_"))


def member_segment(k):
    """Lean `memberSegment`: address the step as a NAMED MEMBER."""
    return "." + encode_key(k)


def render_segment(k):
    """Lean `renderSegment`: address the step by WHAT ITS TEXT DENOTES."""
    n = numeric_key(k)
    if n is not None:
        return "[%s]" % n
    return member_segment(k)


def path_of_keys(keys):
    """Lean `pathOfKeys`."""
    return "".join(render_segment(k) for k in keys)


def final_segment(by_name, k):
    """Lean `finalSegment`: the final step in the form the enquiry selects."""
    return member_segment(k) if by_name else render_segment(k)


def shadow(by_name, lhs_json_path, keys):
    """R/I transliteration of implementation_keyLookupPath (Solution.lean)."""
    intermediate = keys[:-1]
    final_key = keys[-1] if keys else ""
    rhs_json_path = path_of_keys(intermediate)
    rhs_json_path = rhs_json_path + final_segment(by_name, final_key)
    return lhs_json_path + rhs_json_path


def main():
    # REAL patched callees (gold patch applied by the orchestrator). The two
    # classes are the two ends of the dispatchable final-step hook: the first
    # addresses the final step by member name, the second by what its text
    # denotes.
    from django.db.models.fields.json import (compile_json_path, HasKeyLookup,
                                              HasKeyOrArrayIndex)

    def oracle(by_name, lhs_json_path, keys):
        # exact post-patch per-key body of the membership-lookup compiler
        rhs_key_transforms = list(keys)
        *rhs_key_transforms, final_key = rhs_key_transforms
        rhs_json_path = compile_json_path(rhs_key_transforms, include_root=False)
        cls = HasKeyLookup if by_name else HasKeyOrArrayIndex
        rhs_json_path += cls.compile_json_path_final_key(None, final_key)
        return lhs_json_path + rhs_json_path

    rng = random.Random(SEED)
    mismatches = 0
    checked = 0
    by_name_seen = {True: 0, False: 0}
    for _ in range(N_CASES):
        by_name = rng.random() < 0.5
        lhs = rng.choice(PREFIXES)
        n = rng.randint(1, 4)  # precondition keys != []
        keys = [rng.choice(ALPHABET) for _ in range(n)]
        try:
            want = oracle(by_name, lhs, keys)
        except Exception as exc:
            # The real code does not raise here on str keys. If it ever does,
            # that is a modeling disagreement, not a case to skip: a silent
            # `continue` would let the shadow diverge exactly where the real
            # read refuses its input, which is the digit-budget boundary.
            mismatches += 1
            if mismatches <= 5:
                print("ORACLE RAISED byName=%s lhs=%r keys=%r -> %s: %s"
                      % (by_name, lhs, [k[:20] for k in keys],
                         type(exc).__name__, str(exc)[:100]))
            continue
        got = shadow(by_name, lhs, keys)
        if want != got:
            mismatches += 1
            if mismatches <= 5:
                print("MISMATCH byName=%s lhs=%r keys=%r"
                      % (by_name, lhs,
                         [k[:20] + ("..." if len(k) > 20 else "") for k in keys]))
                print("  oracle:", want[:160])
                print("  shadow:", got[:160])
        checked += 1
        by_name_seen[by_name] += 1

    # Both legs of the dispatch must actually have been exercised, else a
    # zero-mismatch run would attest to only one addressing form.
    if min(by_name_seen.values()) == 0:
        print("status=fail checked=%d one addressing form never exercised: %r"
              % (checked, by_name_seen))
        sys.exit(1)

    if mismatches == 0:
        print("status=pass checked=%d mismatches=0 byName=%d denoted=%d "
              "max_parse_digits=%s"
              % (checked, by_name_seen[True], by_name_seen[False],
                 MAX_PARSE_DIGITS))
        sys.exit(0)
    print("status=fail checked=%d mismatches=%d" % (checked, mismatches))
    sys.exit(1)


if __name__ == "__main__":
    main()
