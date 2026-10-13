#!/usr/bin/env python3
r"""G-AX soundness check for django__django-15098.

model.py consumes ONE @ContractOnly axiom, `is_word(c)`: membership of a single
code point in the "word" character class a locale sub-tag's characters are drawn
from. Its real counterpart is the `\w` character class as Python's `re` evaluates
it on a `str` pattern -- i.e. with FULL UNICODE semantics.

This script discharges the two obligations that soundness needs, and it discharges
the second one over the WHOLE code-point space rather than over an ASCII slice:

  (1) AXIOM SOUNDNESS. The axiom's only Ensures is a conditional pinned strictly
      below code point 128:

          Ensures(Implies(c < 128, Result() == (0-9 | A-Z | a-z | _)))

      so the real class must agree with that ASCII enumeration on EVERY code
      point below 128, and the axiom must say NOTHING about code points at or
      above 128 (it is deliberately OPEN there, because the real class is
      Unicode and which further letters/digits it admits is the callee's
      business). Both halves are checked: the pinned half exhaustively over
      cp 0..127, and the open half by confirming the contract has no clause that
      constrains cp >= 128 -- witnessed by exhibiting real code points at/above
      128 on BOTH sides of the class (letters/digits that ARE members, and
      punctuation/symbols/spaces that are NOT), each of which the axiom must
      permit.

  (2) DEEP-MODEL SOUNDNESS (the A-reference). With `is_word` instantiated at its
      REAL counterpart -- the actual Unicode `\w` -- the structural parse
      `prefix_len_spec(path, 2)` must equal the real patched matcher

          language_code_prefix_re = re.compile(r'^/(\w+([@-]\w+){0,2})(/|$)')

      on every probed path (len(match.group(1)) when it matches, -1 when it does
      not), and `prefix_len_spec(path, 1)` must equal the real PRE-patch matcher
      r'^/(\w+([@-]\w+)?)(/|$)', so the model captures the exact behavioural
      delta. Because is_word is instantiated at the real class rather than at an
      ASCII approximation of it, there is NO out-of-domain region here: the probe
      corpus deliberately includes non-ASCII letters, non-ASCII digits, and
      non-ASCII NON-word characters, and any disagreement is a FAILURE, not a
      documented gap.

stdlib-only (`re`, `random`, `sys`, `unicodedata`). Exit 0 iff both obligations
hold on every probed input.
"""
import random
import re
import sys
import unicodedata

# The REAL matchers (verbatim from the repo): pre-patch (budget 1) and the
# gold-patched matcher (budget 2). The patch only changes `?` -> `{0,2}`.
REAL_OLD = re.compile(r'^/(\w+([@-]\w+)?)(/|$)')
REAL_NEW = re.compile(r'^/(\w+([@-]\w+){0,2})(/|$)')

# The REAL per-code-point class the axiom `is_word` models: `\w` exactly as the
# matchers above evaluate it (str pattern => full Unicode). Not an enumeration.
REAL_WORD_CLS = re.compile(r'\w')


def real_is_word(c):
    """The real `\\w` membership of one code point -- the axiom's counterpart."""
    return REAL_WORD_CLS.fullmatch(chr(c)) is not None


# ---------------------------------------------------------------------------
# (1) AXIOM SOUNDNESS: the pinned half, and the openness of the open half.
# ---------------------------------------------------------------------------
# The axiom's Ensures, transcribed from model.py's axioms region.
def axiom_pinned_value(c):
    """What the axiom REQUIRES of Result() -- defined only for c < 128."""
    return ((48 <= c <= 57) or (65 <= c <= 90) or (97 <= c <= 122) or c == 95)


def axiom_permits(c, result):
    """Does the axiom's contract permit `is_word(c) == result`?
    Below 128 it pins the value; at/above 128 it permits either."""
    if c < 128:
        return result == axiom_pinned_value(c)
    return True


def check_axiom_pinned_half():
    """Exhaustive over cp 0..127: the real class must equal the pinned value."""
    bad = []
    for c in range(128):
        got = real_is_word(c)
        want = axiom_pinned_value(c)
        if got != want:
            bad.append((c, chr(c), got, want))
    if bad:
        for c, ch, got, want in bad:
            print("UNSOUND is_word axiom at cp=%d (%r): real \\w membership %r, "
                  "axiom Ensures pins %r" % (c, ch, got, want), file=sys.stderr)
        return False
    print("axiom_check: is_word pinned half SOUND -- real \\w == the axiom's "
          "ASCII enumeration on all 128 code points below 128")
    return True


def check_axiom_open_half():
    """At/above 128 the axiom must constrain nothing. Witness that by exhibiting
    real code points on BOTH sides of the class there, each of which the axiom
    must permit; and confirm the real class genuinely populates both sides (so
    the openness is load-bearing, not vacuous)."""
    members, nonmembers = [], []
    # Letters and digits (members) and marks/punctuation/symbols/spaces (not).
    probes = [0x00E9, 0x00F1, 0x00DF, 0x4E2D, 0x03B1, 0x0430, 0x0660, 0x00C7,
              0x00AA, 0x05D0, 0x3042, 0x0915, 0x1E9E, 0xFF21, 0x00B5,
              0x00D7, 0x2010, 0x00A0, 0x00AB, 0x2013, 0x00A9, 0x00B7,
              0x2026, 0x00F7, 0x2192, 0x3001, 0xFF0F, 0x20AC, 0x2603]
    for c in probes:
        got = real_is_word(c)
        if not axiom_permits(c, got):
            print("UNSOUND: axiom does not permit the real is_word(%d)=%r "
                  "(cp >= 128 must be unconstrained)" % (c, got), file=sys.stderr)
            return False
        (members if got else nonmembers).append(c)
    if not members or not nonmembers:
        print("VACUOUS open half: probes did not populate both sides of the "
              "real class above 128 (members=%d nonmembers=%d)"
              % (len(members), len(nonmembers)), file=sys.stderr)
        return False
    print("axiom_check: is_word open half SOUND and NON-VACUOUS -- above 128 the "
          "real \\w has %d member and %d non-member probes (e.g. %r member, %r "
          "non-member), and the axiom constrains neither; an implementation may "
          "therefore not decide that region for itself"
          % (len(members), len(nonmembers), chr(members[0]), chr(nonmembers[0])))
    return True


# ---------------------------------------------------------------------------
# (2) DEEP MODEL, transcribed verbatim from model.py's pure region, with the
#     axiom `is_word` instantiated at its REAL counterpart.
# ---------------------------------------------------------------------------
def is_word(c):
    return real_is_word(c)          # the axiom, at its real counterpart


def is_sep(c):
    return c == 45 or c == 64


def is_tagchar(c):
    return is_word(c) or is_sep(c)


def run_len(s):
    n = 0
    while n < len(s) and is_tagchar(s[n]):
        n += 1
    return n


def nsep(s):
    return sum(1 for c in s if is_sep(c))


def no_adjacent_sep(s):
    return all(not (is_sep(s[k]) and is_sep(s[k + 1])) for k in range(len(s) - 1))


def well_formed_tag(t):
    return (len(t) > 0 and is_word(t[0]) and is_word(t[-1])
            and no_adjacent_sep(t))


def prefix_len_spec(path, maxsep):
    if len(path) == 0 or path[0] != 47:   # 47 == '/'
        return -1
    body = path[1:]
    r = run_len(body)
    if r == 0:
        return -1
    tag = body[:r]
    if not well_formed_tag(tag):
        return -1
    if nsep(tag) > maxsep:
        return -1
    if r == len(body) or body[r] == 47:
        return r
    # Python-re `$` also matches immediately before a newline that is the
    # LAST character of the string.
    if body[r] == 10 and r == len(body) - 1:
        return r
    return -1


def real_group1_len(rx, path_str):
    m = rx.match(path_str)
    if not m:
        return -1
    return len(m.group(1))


def check(path_str):
    cps = [ord(ch) for ch in path_str]
    for rx, budget, name in ((REAL_OLD, 1, "old"), (REAL_NEW, 2, "new")):
        model = prefix_len_spec(cps, budget)
        real = real_group1_len(rx, path_str)
        if model != real:
            print("MISMATCH (%s budget=%d): path=%r model=%r real=%r"
                  % (name, budget, path_str, model, real), file=sys.stderr)
            return False
    return True


def main():
    if not check_axiom_pinned_half():
        return 1
    if not check_axiom_open_half():
        return 1

    failures = 0
    checked = 0

    # 1. The F2P / issue boundary corpus (exact tested paths + neighbours),
    #    plus NON-ASCII paths -- which are IN domain now, not documented gaps.
    corpus = [
        "/pl/", "/pl", "/xyz/", "/en/", "/en-gb/", "/en-latn-us/",
        "/en-Latn-US/", "/de/", "/de-1996/", "/de-at/", "/de-ch/",
        "/de-ch-1901/", "/de-simple-page/", "/de-simple-page-test/",
        "/i-mingo/", "/kl-tunumiit/", "/nan-hani-tw/",
        # structural boundaries
        "", "/", "//", "/-", "/-/", "/-a/", "/a-/", "/a--b/", "/a@b/",
        "/a@b@c/", "/a@b@c@d/", "/a-b-c-d/", "/a.b/", "/a b/", "/123/",
        "/a_b/", "/a/b/c", "/A-B-C/", "/aaa/bbb/", "/x@y-z/", "/x-y@z/",
        "/" + "a" * 50 + "/", "/a-" + "b" * 30 + "-c/",
        "/en-latn-us", "/de-ch-1901", "/nan-hani-tw",
        # `$`-before-final-newline boundary (Python re semantics: `$` matches
        # at end-of-string AND just before a newline at the very end).
        "/en\n", "/en-us\n", "/de-ch-1901\n", "/nan-hani-tw\n",
        "/en\n\n", "/en\nx", "/en\r\n", "/en-\n", "/\n", "/en/\n",
        "/en\n/", "/a-b-c-d\n", "\n", "/en@gb\n", "/en\rx", "/en\r",
        # NON-ASCII: word characters above 128 (letters of several scripts,
        # a non-ASCII digit, a fullwidth form), each in accepting and
        # rejecting positions.
        "/é/", "/é", "/en-é/", "/en-é",
        "/é-en/", "/éñ中ß/", "/中文/",
        "/de-naïve/", "/中-文-字/",
        "/中-文-字-録/",
        "/α-β-γ/", "/а-б/",
        "/٠١٢/", "/é@ñ/", "/-é/",
        "/é-/", "/é--ñ/", "/en-é-us/",
        "/en-é-us-x/", "/é\n", "/é\n\n",
        # NON-ASCII NON-word characters above 128: these must TERMINATE the run
        # exactly as ASCII punctuation does.
        "/×/", "/en×/", "/en-é×/", "/en–us/",
        "/en‐us/", "/en·us/", "/ /", "/en /",
        "/en€/", "/☃/", "/en…/",
    ]
    for p in corpus:
        checked += 1
        if not check(p):
            failures += 1

    # 2. Exhaustive small structured paths over a CLASS-COMPLETE alphabet: an
    #    ASCII word char, an ASCII digit, the low line, both separators, the
    #    path separator, an ASCII non-candidate char, the newline, a non-ASCII
    #    letter, a non-ASCII ideograph, and a non-ASCII NON-word symbol. The
    #    matcher's decision depends only on these character classes, so this
    #    sweeps the decision space densely -- across the 128 boundary, not
    #    below it.
    alpha = "a1_-@/.\né中×"
    def gen(prefix, depth):
        nonlocal checked, failures
        checked += 1
        if not check(prefix):
            failures += 1
        if depth == 0:
            return
        for ch in alpha:
            gen(prefix + ch, depth - 1)
    gen("", 4)   # all paths of length <= 4 over the class-complete alphabet

    # 3. Heavy fuzz over a WIDE pool spanning both sides of the 128 boundary.
    rng = random.Random(150982024)
    pool = list("abzAZ09_-@/. :;%~+!#\n\r\t") + [
        "é", "ñ", "ß", "中", "α", "а",
        "٠", "Ç", "ª", "א", "あ", "क",
        "×", "‐", " ", "«", "–", "©",
        "·", "…", "÷", "€", "☃"]
    subtags = ["en", "de", "nan", "kl", "i", "zh", "x", "Latn", "US", "1996",
               "us", "é", "中", "ñ", "ß", "α",
               "аб", "٠١"]
    tails = ["/", "", "/x", "-z", "1", ".", "\n", "/\n", "\n\n", "\nx",
             "×", "–", " ", "€"]
    for _ in range(150000):
        if rng.random() < 0.5:
            parts = [rng.choice(subtags) for _ in range(rng.randint(1, 5))]
            seps = [rng.choice("-@") for _ in range(len(parts) - 1)]
            s = "/" + parts[0] + "".join(sp + p
                                         for sp, p in zip(seps, parts[1:]))
            s += rng.choice(tails)
        else:
            L = rng.randint(0, 16)
            s = "".join(rng.choice(pool) for _ in range(L))
            if rng.random() < 0.7:
                s = "/" + s
        checked += 1
        if not check(s):
            failures += 1

    # 4. A systematic sweep of the class boundary itself: for a spread of code
    #    points across the whole BMP, put each one inside a locale-shaped path
    #    and require agreement. This is the check that would catch the model
    #    approximating `\w` by any enumeration instead of consuming the axiom.
    n_word = n_nonword = 0
    for c in (list(range(0, 0x300)) + list(range(0x370, 0x400))
              + list(range(0x4E00, 0x4E80)) + list(range(0x2000, 0x2070))
              + list(range(0xFF00, 0xFF40)) + list(range(0x0600, 0x0680))):
        ch = chr(c)
        if unicodedata.category(ch) in ("Cs", "Cc") and c != 10:
            continue
        if real_is_word(c):
            n_word += 1
        else:
            n_nonword += 1
        for tmpl in ("/%s/", "/en-%s/", "/%s-en/", "/en-%s-us/", "/%s",
                     "/en-%s", "/e%sn/"):
            checked += 1
            if not check(tmpl % ch):
                failures += 1

    print("axiom_check: checked=%d paths (ASCII and non-ASCII) failures=%d; "
          "class-boundary sweep saw %d word and %d non-word code points above "
          "and below 128" % (checked, failures, n_word, n_nonword))
    if failures:
        print("UNSOUND: deep model disagrees with the real matcher.",
              file=sys.stderr)
        return 1
    if not n_word or not n_nonword:
        print("VACUOUS: the class-boundary sweep did not see both word and "
              "non-word code points.", file=sys.stderr)
        return 1

    print("SOUND: is_word's contract is exactly what the real \\w class "
          "satisfies (pinned below 128, open above it), and with is_word at "
          "that real class prefix_len_spec(.,2) == the real new matcher and "
          "prefix_len_spec(.,1) == the real old matcher on every probed input, "
          "with NO out-of-domain region.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
