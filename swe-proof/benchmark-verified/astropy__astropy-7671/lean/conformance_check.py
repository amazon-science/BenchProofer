#!/usr/bin/env python
"""G-CONF: differential conformance for astropy__astropy-7671.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_versionAtLeast` skeleton and diffs its end-to-end result against
the REAL patched `astropy.utils.introspection.minversion` over a discrete
catalogue of version strings plus >=1e5 randomized version strings, for both
values of `inclusive`.

Modeled behavior: `minversion` reduces the required-version string to its leading
release-number prefix (the inline PEP440 regex the gold patch adds), then decides
`LooseVersion(have) >= / > LooseVersion(reduced)`.

Refinement legs exercised here:
  * `releasePrefix` / `normalizeVersion`  — the CHANGED op, modeled DEEPLY in Lean
    (A-reference): the shadow reimplements the regex reduction in pure Python and
    this must agree with the real inline regex inside the patched `minversion`.
  * `versionGe` / `versionGt` / `orderable` — UNCHANGED opaque callees
    (A-reference): the shadow leaves them as the REAL `LooseVersion` comparison
    (we compare the end-to-end `minversion` return, so the real callee is in both
    legs), and `orderable` — whether that comparison completes on the pair — is
    exercised as the raise/value distinction of that same return.

PARTIALITY BRIDGE. `LooseVersion.__ge__` is genuinely partial: it RAISES
`TypeError` on a pair whose release numbers run out against a residual non-numeric
qualifier (bpo-30272 — the subject of this issue). The Lean carrier therefore
states the ordering as an operation on its DOMAIN — `orderable a b : Bool` is the
total question of whether the comparison completes, and `versionGe a b h` takes the
answer as an argument — while the RESULT is `Option Bool`, since that partiality
reaches `minversion`'s own return. The bridge is `none` <-> the comparison raises
(equivalently `orderable = false`), `some b` <-> it returns `b`, and the
differential below enforces BOTH directions: a raise on one side and a value on the
other is a disagreement, so the gate validates where the modeled operation has no
value as well as what it computes where it does. This is what makes the spec's
definedness clause an observed property of the real callee rather than an
assumption about it.

Bridge (mapping.md): a Lean `List Char` version string <-> a Python `str`; the
available version is supplied as a `ModuleType.__version__` (exactly the F2P test
harness); `inclusive` Bool <-> Python bool; the Bool result <-> the bool return.

Exit 0 iff zero disagreements. stdlib only; pinned seed.
"""
import random
import re
import sys
import unicodedata
from types import ModuleType

SEED = 20240627
N_RANDOM = 150_000  # >= 1e5

# Reference regex (identical to the gold patch); used ONLY to cross-check that the
# pure-Python shadow normalizer reproduces it — the differential target itself is
# the real patched minversion, not this regex.
_EXPR = r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'


# ---- Python shadow of the Lean pure helpers (releasePrefix / normalizeVersion) --

def _is_decimal_digit(c):
    """A *decimal digit*: Unicode category Nd, exactly what `\\d` matches for a
    str pattern under re's default UNICODE flag. Mirrors the Lean
    `isDecimalDigit` / `decimalDigitRanges`. NOT `str.isdigit()`, which is wider
    (it also accepts e.g. the superscripts, which `\\d` rejects)."""
    return unicodedata.category(c) == 'Nd'


def _is_ascii_digit(c):
    """`'0'`-`'9'` only — the character class the regex spells as the literals
    `0` and `[1-9]`, which (unlike `\\d`) are NOT Unicode-aware."""
    return '0' <= c <= '9'


def _span_digits(s, i):
    """`\\d*` — the maximal run of Unicode decimal digits."""
    j = i
    while j < len(s) and _is_decimal_digit(s[j]):
        j += 1
    return j


def _consume_number(s, i):
    """(0 | [1-9]\\d*) at index i -> end index or None. The LEADING character is
    ASCII-only (regex literals `0` / `[1-9]`); the continuation is `\\d*`."""
    if i >= len(s):
        return None
    c = s[i]
    if c == '0':
        return i + 1
    if _is_ascii_digit(c):  # '1'..'9', ASCII only
        return _span_digits(s, i + 1)
    return None


def _consume_epoch(s, i):
    """[1-9]\\d* '!' followed by a release-number start -> end index (past '!')
    or None. Head and the post-'!' digit are ASCII (regex literals); the epoch
    body is `\\d*`."""
    if i >= len(s):
        return None
    c = s[i]
    if _is_ascii_digit(c) and c != '0':
        j = _span_digits(s, i + 1)
        if (j < len(s) and s[j] == '!'
                and j + 1 < len(s) and _is_ascii_digit(s[j + 1])):
            return j + 1
    return None


def _scan_dots(s, i):
    """(\\.(0|[1-9][0-9]*))* from index i -> end index."""
    while i < len(s) and s[i] == '.':
        r = _consume_number(s, i + 1)
        if r is None:
            break
        i = r
    return i


def release_prefix(version):
    """Longest leading release-number prefix, or None when absent."""
    e = _consume_epoch(version, 0)
    if e is not None:
        r = _consume_number(version, e)
        if r is not None:
            end = _scan_dots(version, r)
            return version[:end]
        # unreachable (epoch guarantees a following release digit); fall through
    r = _consume_number(version, 0)
    if r is not None:
        end = _scan_dots(version, r)
        return version[:end]
    return None


def normalize_version(version):
    p = release_prefix(version)
    return p if p is not None else version


def shadow_minversion(have_version, version, inclusive):
    """Transliteration of implementation_versionAtLeast: reduce `version` to its
    release prefix (deep model), then compare via the REAL LooseVersion.

    The comparison is applied to the REDUCED value and to nothing else — matching
    the Lean impl, which binds exactly one comparison. An extra comparison on the
    un-reduced string would be a `none` the spec does not permit (clause C5), and
    it would show up here as a raise the real patched `minversion` does not make.
    """
    from distutils.version import LooseVersion
    ver = normalize_version(version)
    if inclusive:
        return LooseVersion(have_version) >= LooseVersion(ver)
    else:
        return LooseVersion(have_version) > LooseVersion(ver)


# ---- real callee observation (patched minversion) ---------------------------

def real_minversion(have_version, version, inclusive):
    from astropy.utils.introspection import minversion
    mod = ModuleType(str("conf_test_module"))
    mod.__version__ = have_version
    return bool(minversion(mod, version, inclusive=inclusive))


def main():
    # First, cross-check the shadow normalizer vs the literal regex (group(0)).
    rng = random.Random(SEED)
    # The alphabet MUST reach past ASCII. `\d` in the pattern is Unicode-aware
    # while the `0` / `[1-9]` literals are not, so the ASCII-only region of the
    # input space cannot witness that asymmetry at all: a normalizer that gated
    # every digit on ASCII agrees with the regex on all of it. So include
    # non-ASCII decimal digits (Nd, which `\d` matches) from several scripts and
    # planes, plus numeric-but-NOT-Nd characters (superscripts, Roman numerals,
    # fractions) that `\d` must REJECT even though `str.isdigit()` /
    # `str.isnumeric()` accept them.
    nd_extra = '٥۳१৩๒１９' \
               '\U0001d7d0\U0001d7ff\U000104a2'   # Nd, non-ASCII, incl. astral
    non_nd_numeric = '²¹⁰Ⅶ½፩'  # numeric, not Nd
    alphabet = '0123456789.!abcdevrc-+ ' + nd_extra + non_nd_numeric

    norm_mismatch = 0
    for _ in range(50_000):
        s = ''.join(rng.choice(alphabet) for _ in range(rng.randint(0, 10)))
        m = re.match(_EXPR, s)
        ref = m.group(0) if m else s  # patch leaves version unchanged when no match
        got = normalize_version(s)
        if ref != got:
            norm_mismatch += 1
            if norm_mismatch <= 5:
                print(f"NORM MISMATCH {s!r}: regex={ref!r} shadow={got!r}")
    if norm_mismatch:
        print(f"status=fail {norm_mismatch} normalizer disagreement(s) vs regex")
        return 1

    # End-to-end differential vs real patched minversion.
    disagreements = 0
    checked = 0

    def rand_numeric_version():
        """A clean dotted release number (valid available-version string)."""
        n = rng.randint(1, 4)
        parts = [str(rng.randint(0, 30)) for _ in range(n)]
        return '.'.join(parts)

    def rand_required_version():
        """Required version: numeric core + optional qualifier/epoch, sometimes
        with a non-ASCII decimal digit or a numeric-but-not-Nd character spliced
        into the release region (the part `\\d` treats differently from the
        pattern's ASCII literals)."""
        core = rand_numeric_version()
        tail = rng.choice(['', 'dev', 'rc1', '.dev', 'a1', 'b2', '+local', '-1'])
        head = rng.choice(['', '', '', '1!', '2!', '0!'])
        s = head + core + tail
        if rng.random() < 0.35:
            # splice a non-ASCII char into the release region, including at the
            # very front (where the ASCII-only `[1-9]`/`0` literals must refuse).
            ch = rng.choice(nd_extra + non_nd_numeric)
            pos = rng.randint(0, min(len(s), 4))
            s = s[:pos] + ch + s[pos:]
        return s

    # discrete catalogue: the issue + F2P cases, both inclusive values
    discrete_haves = ['0.12.2', '1.14.3', '0.4.4', '2.0', '1.0', '3.6.0']
    discrete_reqs = ['0.12', '0.12.1', '0.12.0.dev', '0.12dev', '1', '1.2rc1',
                     '1.14dev', '1.14.3', '0.4.4', '2.0', '1.0rc1', '1!1.0',
                     '0!2.0', '0.12.2', '3.6',
                     # Unicode-digit region: `\d` matches these, the ASCII
                     # literals `0`/`[1-9]` do not. '1٥5' is the G-PANEL-2
                     # witness (kept whole by the real regex, so the comparison
                     # sees the FULL string); '٥1' has no match at all;
                     # '1²5' stops at '1' (numeric but not Nd).
                     '1٥5', '٥1', '1.2৩', '1٥!5',
                     '1!٥', '1²5', '12٥34']
    cases = []
    for hv in discrete_haves:
        for rv in discrete_reqs:
            for inc in (True, False):
                cases.append((hv, rv, inc))

    for _ in range(N_RANDOM):
        cases.append((rand_numeric_version(), rand_required_version(),
                      rng.random() < 0.5))

    for have, req, inc in cases:
        # The real comparison can still raise if even the REDUCED required string
        # is non-numeric (no leading release number at all, e.g. 'dev'); in that
        # case the real patched minversion raises and so would the shadow — both
        # legs share the identical reduced value, so we treat a shared raise as
        # agreement and a divergent raise as a disagreement.
        try:
            got = real_minversion(have, req, inc)
            real_err = None
        except Exception as e:  # noqa: BLE001
            got = None
            real_err = type(e).__name__
        try:
            exp = shadow_minversion(have, req, inc)
            shadow_err = None
        except Exception as e:  # noqa: BLE001
            exp = None
            shadow_err = type(e).__name__
        checked += 1
        agree = (real_err is None and shadow_err is None and got == exp) or \
                (real_err is not None and shadow_err is not None)
        if not agree:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH have={have!r} req={req!r} inc={inc}: "
                      f"real={got!r}/{real_err} shadow={exp!r}/{shadow_err}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
