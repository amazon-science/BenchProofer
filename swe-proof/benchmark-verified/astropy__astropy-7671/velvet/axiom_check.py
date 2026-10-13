#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-7671.

Two kind-A obligations are checked against the REAL callees the changed
function invokes:

  (A-reference) the deep model `cleanLabel` (Solution.lean `pure` region) ==
      the REAL leading-portion extractor the patch introduces:
          re.match(PEP440_EXPR, version).group(0)   (falls back to the raw
          string when there is no match — exactly the `if m:` guard of the
          patch). `cleanLabel` is the spelled-out structural prefix parser; G-AX
          validates it against the real `re.match` over boundary + fuzz inputs.

  (A-consumed) the `labelGE` axiom models the UNCHANGED ordering callee
      `LooseVersion(have) >= / > LooseVersion(candidate)`. The Lean axiom is
      fully OPAQUE (no `ensures`), so there is no contract strength to refute;
      the only soundness obligation is that the real callee is a well-defined
      PARTIAL operation of the claimed signature — for every (have, candidate,
      inclusive) it either returns a Bool verdict or raises (the
      `incomparable` failure the `Except CmpErr Bool` carrier models). G-AX
      confirms this trichotomy holds (never anything but bool-or-raise) and, as
      a positive witness, that the partiality is REAL: there exist candidate
      labels on which the raw comparison raises but the cleaned one does not —
      which is the whole reason `cleanLabel` must precede the comparison.

Modeled domain: the required label is ASCII (`meetsRequirement`'s
precondition `∀ c ∈ version, c.toNat < 128`; mapping.md §2.1) — Python's
Unicode-aware `\d` and the model's ASCII digit test agree exactly there, and
all alphabets below are ASCII accordingly.

Imports only the Python standard library (`re`, `distutils.version`) — the same
modules the gold patch and the unchanged callee use. Exit 0 iff every
obligation holds.
"""
import re
import random
import sys
import warnings

warnings.filterwarnings("ignore")  # silence distutils deprecation noise
from distutils.version import LooseVersion

# The regex the patch introduces (PEP440 Appendix B leading numeric portion).
PEP440_EXPR = r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'


# --- the REAL leading-portion extractor (patch behaviour) --------------------
def real_clean(version):
    """patch.diff behaviour: re.match(EXPR, version); if it matches, the matched
    prefix, else the string unchanged (the patch's `if m:` guard)."""
    m = re.match(PEP440_EXPR, version)
    return m.group(0) if m else version


# --- the deep model `cleanLabel`, transliterated from Solution.lean ----------
def is_digit(c):
    return '0' <= c <= '9'


def digit_run(s, i):
    j = i
    while j < len(s) and is_digit(s[j]):
        j += 1
    return j - i


def seg_len(s, i):
    if i >= len(s):
        return 0
    c = s[i]
    if c == '0':
        return 1
    if is_digit(c):
        return 1 + digit_run(s, i + 1)
    return 0


def dotted_tail(s, i):
    total = 0
    while i < len(s) and s[i] == '.':
        sl = seg_len(s, i + 1)
        if sl == 0:
            break
        total += 1 + sl
        i += 1 + sl
    return total


def epoch_len(s):
    if not s:
        return 0
    c = s[0]
    if is_digit(c) and c != '0':
        r = 1 + digit_run(s, 1)
        if r < len(s) and s[r] == '!':
            if seg_len(s, r + 1) == 0:
                return 0
            return r + 1
        return 0
    return 0


def clean_label(version):
    e = epoch_len(version)
    r = seg_len(version, e)
    if r == 0:
        return version
    d = dotted_tail(version, e + r)
    return version[:e + r + d]


# --- the UNCHANGED ordering callee, raw + cleaned ----------------------------
def real_compare(have, candidate, inclusive):
    """The real LooseVersion ordering; returns ('ok', bool) or ('raise',)."""
    try:
        if inclusive:
            return ('ok', LooseVersion(have) >= LooseVersion(candidate))
        return ('ok', LooseVersion(have) > LooseVersion(candidate))
    except Exception:
        return ('raise',)


def main():
    rng = random.Random(7671)

    # ---- (A-reference) cleanLabel == real re.match extractor --------------
    boundary = [
        "", "0", "1", "00", "08", "10", "100", "9", "99999",
        "0.0", "0.12", "0.12.1", "0.12.0.dev", "0.12dev", "1.14dev",
        "1.14.3", "1.2rc1", "1", "12.3", "1.2.3.4.5", "1.", ".5",
        "a", "dev1.0", "0008.9", "007", "1!", "1!0.1", "1!2.3", "01.2",
        "1.2.3rc4.dev5", "1!2.3rc4", "9!9.9.9", "1.2.3.", "1!!2", "1..2",
    ]
    for s in boundary:
        assert clean_label(s) == real_clean(s), (
            "cleanLabel deep model unsound on %r: re.match gave %r, "
            "deep model gives %r" % (s, real_clean(s), clean_label(s)))

    alphabet = list("0123456789.!abrcdev-+ XY")
    n_ref = 200000
    for _ in range(n_ref):
        k = rng.randint(0, 14)
        s = "".join(rng.choice(alphabet) for _ in range(k))
        assert clean_label(s) == real_clean(s), (
            "cleanLabel deep model unsound on %r: re.match gave %r, "
            "deep model gives %r" % (s, real_clean(s), clean_label(s)))

    # ---- (A-consumed) labelGE: real callee is bool-or-raise, partial ------
    label_alpha = list("0123456789.abrcdevXY!-+ ")
    raises_seen = 0
    cleaned_fixes = 0  # raw raises, cleaned does not -> partiality is real
    n_ax = 200000
    for _ in range(n_ax):
        ka = rng.randint(0, 8)
        kb = rng.randint(0, 8)
        have = "".join(rng.choice(label_alpha) for _ in range(ka))
        cand = "".join(rng.choice(label_alpha) for _ in range(kb))
        inc = rng.random() < 0.5
        res = real_compare(have, cand, inc)
        # trichotomy: nothing but a Bool verdict or a raise (the Except carrier)
        assert res[0] in ("ok", "raise"), "unexpected callee outcome %r" % (res,)
        if res[0] == "ok":
            assert isinstance(res[1], bool), (
                "ordering callee returned non-Bool %r on (%r,%r,%s)"
                % (res[1], have, cand, inc))
        else:
            raises_seen += 1
            cleaned = real_compare(have, clean_label(cand), inc)
            if cleaned[0] == "ok":
                cleaned_fixes += 1

    # positive witness for the F2P case: the dirtied required label raises raw
    # but the cleaned label compares cleanly.
    fixed = real_compare("0.12.2", "0.12dev", True)
    cleaned_fixed = real_compare("0.12.2", clean_label("0.12dev"), True)
    assert fixed[0] == "raise", (
        "expected raw '0.12dev' comparison to raise (the bug), got %r" % (fixed,))
    assert cleaned_fixed == ("ok", True), (
        "expected cleaned '0.12dev' comparison to succeed True, got %r"
        % (cleaned_fixed,))

    assert raises_seen > 0, (
        "fuzzing never exercised the partial (raising) branch of the ordering "
        "callee — the labelGE partiality model is unwitnessed")
    assert cleaned_fixes > 0, (
        "cleaning never converted a raising comparison into a verdict — the "
        "reason cleanLabel must precede the comparison is unwitnessed")

    print("G-AX OK: cleanLabel deep model (== re.match PEP440 extractor) sound "
          "on %d boundary + %d fuzz inputs; ordering callee bool-or-raise on "
          "%d fuzz triples (%d raised raw, %d of those fixed by cleaning)."
          % (len(boundary), n_ref, n_ax, raises_seen, cleaned_fixes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
