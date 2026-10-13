#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12039.

This bundle consumes NO axioms: the changed operation (joining a column's base
token with its optional ordering suffix) is modelled DEEPLY in model.py as the
spelled-out conditional concatenation `joined(base, suffix)`. G-AX here
validates that deep model (an A-reference) against the REAL operation it stands
in for — the gold patch's `col_str` join, performed at BOTH change sites:

  Site 1 (Columns.__str__.col_str):
      col = self.quote_name(column)            # the base token
      suffix = self.col_suffixes[idx]
      if suffix:
          col = '{} {}'.format(col, suffix)
      return col

  Site 2 (IndexColumns.__str__.col_str):
      col = '{} {}'.format(self.quote_name(column), self.opclasses[idx])  # base
      suffix = self.col_suffixes[idx]
      if suffix:
          col = '{} {}'.format(col, suffix)
      return col

Both sites reduce to the same join on (base, suffix): a non-empty suffix is set
off from the base token by exactly one space; an empty suffix (the default,
ascending order — `col_suffixes` contains '' for it) contributes nothing, with
NO trailing space. `str.format`/`+` are the Python standard library; nothing
repo-specific is imported.

The check asserts, over boundary cases and randomized fuzz, that

    joined(base, suffix)  ==  real col_str join(base, suffix)

as code-point lists, for both sites, and additionally that model.py's
structural guarantees hold on the real rendering:
  * empty suffix  -> result == base exactly (no trailing separator);
  * non-empty suffix -> the code point right after the base token is the
    space separator (so the suffix keyword never fuses with the base).
Exit 0 iff every observation matches the model.
"""
import random
import sys

SEP = 32  # ' '  (model.py `sep`)


def joined(base_cp, suffix_cp):
    """model.py deep model `joined` as a list of code points."""
    if len(suffix_cp) == 0:
        return base_cp
    return base_cp + [SEP] + suffix_cp


def real_join(base_s, suffix_s):
    """The REAL gold-patch col_str join (identical logic at both sites):
    append a space-separated suffix only when the suffix is truthy."""
    col = base_s
    suffix = suffix_s
    if suffix:
        col = '{} {}'.format(col, suffix)
    return col


def check(base_s, suffix_s):
    observed = [ord(ch) for ch in real_join(base_s, suffix_s)]
    expected = joined([ord(ch) for ch in base_s], [ord(ch) for ch in suffix_s])
    assert observed == expected, (
        "deep model `joined` unsound on base=%r suffix=%r: real join gave %r, "
        "deep model gives %r" % (base_s, suffix_s, observed, expected))

    base_cp = [ord(ch) for ch in base_s]
    if suffix_s == "":
        # empty suffix: result is the base exactly (no trailing separator).
        assert observed == base_cp, (
            "empty suffix produced a trailing separator on base=%r: %r"
            % (base_s, observed))
    else:
        # non-empty suffix: base preserved as prefix, separator right after it.
        assert observed[:len(base_cp)] == base_cp, (
            "base token not preserved as prefix on base=%r suffix=%r"
            % (base_s, suffix_s))
        assert observed[len(base_cp)] == SEP, (
            "suffix keyword fuses with the base token on base=%r suffix=%r"
            % (base_s, suffix_s))
        assert observed[len(base_cp) + 1:] == [ord(ch) for ch in suffix_s], (
            "suffix not appended verbatim on base=%r suffix=%r"
            % (base_s, suffix_s))


def main():
    # Base tokens for each site:
    #  - site 1: the quoted column, e.g. "headline" (quote_name adds quotes).
    #  - site 2: quoted column + ' ' + opclass, e.g. "headline" text_pattern_ops.
    bases = [
        '"headline"',
        '"name"',
        '"headline" text_pattern_ops',          # site 2 base
        '"name" varchar_pattern_ops',
        '`schema_author`',
        "[col]",
        "",                                       # empty base (boundary)
        "x",
    ]
    # Ordering suffixes Django produces: '' (ascending) or 'DESC' (descending).
    suffixes = ["", "DESC", "ASC", "NULLS FIRST"]

    boundary = [(b, s) for b in bases for s in suffixes]
    for b, s in boundary:
        check(b, s)

    # The exact F2P / P2P scenarios:
    #  - test_descending_columns_list_sql (F2P): base '"headline"', suffix 'DESC'
    #    -> '"headline" DESC' (a space before DESC).
    obs = real_join('"headline"', "DESC")
    assert obs == '"headline" DESC', obs
    assert '"headline"DESC' not in obs, obs
    #  - test_columns_list_sql (P2P): base '"headline"', suffix '' -> '"headline"'.
    assert real_join('"headline"', "") == '"headline"'
    #  - test_ops_class_columns_lists_sql (P2P): base '"headline" text_pattern_ops',
    #    suffix '' -> no trailing space.
    obs = real_join('"headline" text_pattern_ops', "")
    assert obs == '"headline" text_pattern_ops', obs
    assert not obs.endswith(" "), obs
    #  - descending opclass: base '"headline" text_pattern_ops', suffix 'DESC'.
    obs = real_join('"headline" text_pattern_ops', "DESC")
    assert obs == '"headline" text_pattern_ops DESC', obs

    # randomized fuzz over arbitrary printable-ish base/suffix strings.
    rng = random.Random(12039)
    alphabet = [chr(c) for c in range(33, 127)] + [" "]
    for _ in range(20000):
        nb = rng.randint(0, 24)
        ns = rng.randint(0, 8)
        b = "".join(rng.choice(alphabet) for _ in range(nb))
        # half the time use an empty suffix (the ascending-order case) to
        # exercise the no-trailing-space branch heavily.
        s = "" if rng.random() < 0.4 else "".join(
            rng.choice(alphabet) for _ in range(ns))
        check(b, s)

    print("G-AX OK: deep model `joined` == real col_str join on %d boundary + "
          "20000 fuzz inputs (both sites); empty suffix leaves no trailing "
          "space and a non-empty suffix is space-separated (no fusion)."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
