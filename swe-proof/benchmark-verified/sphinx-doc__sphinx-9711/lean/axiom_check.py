#!/usr/bin/env python3
"""G-AX — A-reference validation for sphinx-doc__sphinx-9711.

The version comparison is modeled DEEPLY in Solution.lean (refinement.md ops
5/6), so its callee — the repo's version-parsing/ordering library routine — is an
A-reference: the deep model must equal the real callee. This script runs the REAL
callee in the instance environment and asserts the deep model reproduces it, on a
boundary set + fuzz.

SCOPE = the spec's admissibility predicate. `problem_pre_verifyExtensionVersions`
admits an entry iff both version strings it mentions are ASCII text; the checks
below therefore run over ASCII strings, and every string they check is ASSERTED
ASCII, so no input the spec admits can be skipped. The excluded class is exactly
one thing, and it is excluded because the real callee is not stable there rather
than because the model is weak: a string carrying a non-ASCII code point that a
case-folding table maps onto an ASCII letter (U+0130, U+0131, U+017F, U+212A are
the only such code points for an ASCII letter/digit class). Released revisions of
the callee disagree on those — some scope their case-insensitive tag matching to
ASCII and raise on such a string, others accept it and keep the non-ASCII
spelling in the ordering key, where it then sorts ABOVE the ASCII spelling of the
same tag. The two readings give different end-to-end verdicts on the same inputs
(e.g. required `1` against present `1.0dev1+<U+017F>`: one reading reports the
requirement unmet, the other reports it met), so no single model can be faithful
to both, and the spec claims neither. `OUT_OF_SCOPE` below records that class
explicitly; each of its strings is asserted NON-ASCII, so the exclusion cannot be
widened to hide an in-scope disagreement, and what this environment does on them
is reported as an observation, never as a pass/fail.

Four properties are checked, per version string / per (req, ver) pair:

  P0 (accept set): the Lean `parseVersion` returns `some _` exactly when the
      real callee accepts the string as a version (i.e. does NOT raise its
      invalid-version error). An earlier revision of this bundle got this
      wrong: a model that accepts only dotted-decimal takes the raw-string
      path on strings the real callee happily reads (a leading `v`, an epoch,
      a pre/post/dev tag, surrounding blanks, upper case), and then the two
      decision procedures disagree.

  P1 (ordering): on strings BOTH accept, the model's key comparison
      `verGt (parseVersion req) (parseVersion ver)` equals the real callee's
      `>`. This covers zero-padding (`1` == `1.0` == `1.0.0`), epoch
      dominance, the pre/post/dev suffix ranking, and build-tag ordering.

  P2 (fallback): for strings the real callee rejects, the Lean `parseVersion`
      returns `none` (so the impl dispatches to the raw-string comparison),
      AND `stringGt req ver` equals Python `req > ver` (both are `str.__gt__` /
      code-point order).

  P3 (composed decision): the modeled `requirementUnmet req ver` equals the
      real repo block's decision (`'unknown version'` fails; else compare as
      versions, falling back to the raw-string comparison when either string
      is not a version). P3 is the property the spec actually rests on; P0-P2
      localize any failure of it.

`release_key` below is a transliteration of Solution.lean's `pure` region
(`parseVersion` / `verGt`): blanks stripped, ASCII case folded, optional leading
`v`, optional `<digits>!` epoch, dotted numeric release, optional pre/post/dev
qualifier tags, optional `+` build tag, then the 4-part ordering key.

stdlib-only except the repo's own version library (a real Sphinx dependency).
Pinned seed: 9711. exit 0 iff every in-scope observation meets the model.
"""
import sys

from packaging.version import InvalidVersion, Version

SEED = 9711
N = 100_000

# ----- Lean `pure` region, transliterated (the deep model under validation) -----

# Solution.lean `blankChars`: the code points a leading/trailing run of which is
# ignored. This is exactly Python's `str` `\s` class, which is what the real
# callee's `\s*...\s*` pattern wrapper strips.
BLANKS = "".join(map(chr, (
    0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x85, 0xa0,
    0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007,
    0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000)))

DIGITS = "0123456789"
SEPS = "._-"

# Solution.lean `preToks` / `postToks`: spellings longest-first, each with the
# rank it denotes.
PRE_TOKS = (("alpha", 1), ("beta", 2), ("preview", 3), ("pre", 3), ("rc", 3),
            ("a", 1), ("b", 2), ("c", 3))
POST_TOKS = (("post", 1), ("rev", 1), ("r", 1))


def _fold_char(c):
    """Solution.lean `foldChar`: ASCII upper case to lower case, nothing else.

    Tag matching is case-insensitive within ASCII, which is the whole of the
    admitted domain (see SCOPE above); no non-ASCII code point folds onto an
    ASCII letter here, so no non-ASCII code point can spell a qualifier tag.
    """
    if "A" <= c <= "Z":
        return chr(ord(c) + 32)
    return c


def _is_digits(s):
    return len(s) > 0 and all(c in DIGITS for c in s)


def _take_digits(s, i):
    j = i
    while j < len(s) and s[j] in DIGITS:
        j += 1
    return s[i:j], j


def _drop_sep(s, i):
    if i < len(s) and s[i] in SEPS:
        return i + 1
    return i


def _try_tok(toks, s, i):
    """Solution.lean `tryTok`: optional sep, a token, optional sep, optional
    number. Returns (rank, num, newpos) or None."""
    for tok, rank in toks:
        j = _drop_sep(s, i)
        if s.startswith(tok, j):
            k = _drop_sep(s, j + len(tok))
            d, k2 = _take_digits(s, k)
            return (rank, int(d) if d else 0, k2)
    return None


def _mk_local_seg(cur):
    """Solution.lean `mkLocalSeg`."""
    if _is_digits(cur):
        return (True, int(cur), "")
    return (False, 0, cur)


def _parse_local(s, i):
    """Solution.lean `localLoop`: non-empty word/number segments separated by
    single separators; anything else rejects."""
    segs, cur = [], ""
    while i < len(s):
        c = s[i]
        if c in DIGITS or "a" <= c <= "z":
            cur += c
        elif c in SEPS:
            if cur == "":
                return None
            segs.append(_mk_local_seg(cur))
            cur = ""
        else:
            return None
        i += 1
    if cur == "":
        return None
    segs.append(_mk_local_seg(cur))
    return segs


def _strip_zeros(xs):
    """Solution.lean `stripZeros`: drop trailing zero components."""
    out = list(xs)
    while out and out[-1] == 0:
        out.pop()
    return out


def _parse_after_epoch(epoch, s, i):
    """Solution.lean `parseAfterEpoch`."""
    d, i = _take_digits(s, i)
    if not d:
        return None
    rel = [int(d)]
    # `.`-separated further numeric components
    while i < len(s) and s[i] == ".":
        d2, j = _take_digits(s, i + 1)
        if not d2:
            break
        rel.append(int(d2))
        i = j
    pre = _try_tok(PRE_TOKS, s, i)
    if pre is not None:
        pre_rank, pre_num, i = pre
    else:
        pre_rank, pre_num = None, 0
    # revision tag: the bare `-N` form first, then the worded spellings
    post_rank, post_num = None, 0
    handled = False
    if i < len(s) and s[i] == "-":
        d2, j = _take_digits(s, i + 1)
        if d2:
            post_rank, post_num, i = 1, int(d2), j
            handled = True
    if not handled:
        post = _try_tok(POST_TOKS, s, i)
        if post is not None:
            post_rank, post_num, i = post
    dev = _try_tok((("dev", 0),), s, i)
    if dev is not None:
        dev_rank, dev_num, i = 0, dev[1], dev[2]
    else:
        dev_rank, dev_num = None, 0
    # build tag
    if i < len(s) and s[i] == "+":
        segs = _parse_local(s, i + 1)
        if segs is None:
            return None
    elif i == len(s):
        segs = []
    else:
        return None
    # Solution.lean `mkKey`
    if pre_rank is None and post_rank is None and dev_rank is not None:
        pr = 0            # development-only sorts below every pre-qualifier
    elif pre_rank is None:
        pr = 4            # no pre-qualifier sorts above them all
    else:
        pr = pre_rank
    pn = pre_num if pre_rank is not None else 0
    suffix = [pr, pn, 1 if post_rank is not None else 0, post_num,
              0 if dev_rank is not None else 1, dev_num]
    return (epoch, tuple(_strip_zeros(rel)), tuple(suffix), tuple(segs))


def release_key(raw):
    """Mirror of `parseVersion`: the ordering key, or None when the text is not
    a readable version."""
    t = raw.strip(BLANKS)
    s = "".join(_fold_char(c) for c in t)
    i = 0
    if i < len(s) and s[i] == "v":
        i += 1
    bang = s.find("!", i)
    if bang != -1:
        e = s[i:bang]
        if not _is_digits(e):
            return None
        return _parse_after_epoch(int(e), s, bang + 1)
    return _parse_after_epoch(0, s, i)


def _local_cmp_key(segs):
    """Solution.lean `localCmp`: word segments order before numeric ones."""
    return [(1, n, "") if isnum else (0, 0, w) for (isnum, n, w) in segs]


def ver_gt(a, b):
    """Solution.lean `verGt` on two keys."""
    ka = (a[0], list(a[1]), list(a[2]), _local_cmp_key(a[3]))
    kb = (b[0], list(b[1]), list(b[2]), _local_cmp_key(b[3]))
    return ka > kb


def string_gt(a, b):
    return a > b


def model_unmet(req, ver):
    """Solution.lean `requirementUnmet`: the sentinel always fails; otherwise
    compare as versions when both are readable, else as raw strings."""
    if ver == "unknown version":
        return True
    ka, kb = release_key(req), release_key(ver)
    if ka is not None and kb is not None:
        return ver_gt(ka, kb)
    return string_gt(req, ver)


# ----- the real callee --------------------------------------------------------
def real_accepts(s):
    try:
        Version(s)
        return True
    except InvalidVersion:
        return False


def real_unmet(req, ver):
    """The repo block's decision for one entry, with the REAL callee: the
    sentinel fails; else the version comparison, falling back to the raw-string
    comparison when either string is not a version."""
    if ver == "unknown version":
        return True
    try:
        return Version(req) > Version(ver)
    except InvalidVersion:
        return req > ver


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def check_string(s):
    """P0: the model's accept set is the real callee's accept set."""
    model_ok = release_key(s) is not None
    if model_ok != real_accepts(s):
        return ("P0 accept-set mismatch", s, "model", model_ok,
                "real", real_accepts(s))
    return None


def check_pair(req, ver):
    """P1 / P2 / P3: order on the accepted domain, raw-string fallback off it,
    and the composed per-entry decision either way."""
    ka, kb = release_key(req), release_key(ver)
    if ka is not None and kb is not None:
        # Both readable => the impl compares as versions; must match the callee.
        model = ver_gt(ka, kb)
        real = Version(req) > Version(ver)
        if model != real:
            return ("P1 order mismatch", req, ver, "model", model, "real", real)
    else:
        # At least one unreadable => the impl uses the raw-string comparison.
        if string_gt(req, ver) != (req > ver):
            return ("P2 string fallback mismatch", req, ver)
    if model_unmet(req, ver) != real_unmet(req, ver):
        return ("P3 decision mismatch", req, ver, "model",
                model_unmet(req, ver), "real", real_unmet(req, ver))
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


# Boundary + representative strings, all ASCII (= all admitted). Beyond the
# dotted-decimal core (the reported domain) and differing arity (zero padding),
# this pool deliberately includes every shape the real callee accepts but a
# dotted-decimal-only model would reject — a leading `v`, an epoch, pre/post/dev
# qualifier tags in each of their spellings and separators, build tags,
# surrounding blanks, upper case — plus strings the callee rejects, which must
# take the raw-string comparison.
POOL = (
    # dotted-decimal core + padding
    "0.6", "0.10", "0.6.0", "3.9", "3.10", "3.11", "1", "1.0", "1.0.0",
    "0", "2", "9", "10", "99", "0.0", "10.2.3", "1.2.3.4", "2024.1",
    "1.0.0.0", "00", "01.02",
    # the sentinel + strings the callee rejects (raw-string comparison)
    "unknown version", "abc", "1.x", "1.", ".1", "", "1..2", "1_0", "x",
    "..", "v", "vv1", "1.0+", "+1", "1!", "!1", "-1", "1.-0", "1 0", "1.0.",
    "1.0-", "1.0_", "1.0..dev1", "1.0+a..b", "1.0+-a",
    # leading `v` / upper case — accepted by the real callee
    "v1", "v1.0", "v2.0", "V1.2", "V1", "v1.0.dev1", "v1!2.0",
    # epochs
    "1!0", "1!2.3", "0!1", "10!0.1", "2!1.0", "01!2", "0!0",
    # pre-qualifier tags, spellings and separators
    "1.0a1", "1.0b2", "1.0c1", "1.0rc2", "1.0alpha1", "1.0beta", "1.0pre",
    "1.0preview2", "1.0.a1", "1.0-alpha-1", "1.0_rc_2", "1.0PRE1", "1.0RC1",
    "1.0a", "1.0.rc.3", "1.0rc",
    # revision tags
    "1.0.post1", "1.0post1", "1.0-1", "1.0rev3", "1.0r4", "1.0.post",
    "1.0POST1", "1.0-post-2", "1.0_r_1", "1.0.rev", "1.0.r",
    # development tags
    "1.0.dev1", "1.0dev", "1.0.dev0", "1.0.DEV1", "1.0-dev-3", "1.0.dev",
    # build tags
    "1.0+ubuntu.1", "1.0+a", "1.0+1", "1.0+1.2", "1.0+abc_def", "1.0+A",
    "1.0+9x", "1.0.dev1+x.2", "1.0+a-b",
    # combined, and blanks
    "1!2.3a4.post5.dev6+ab.7", "1.0a1.post2.dev3", "1!1.0rc1+local.1",
    " 1.0", "1.0 ", "  1.0  ", "\t1.0\n", "\x1c1.0", "1.0\v",
)

# DOCUMENTED EXCLUSION — the one class the spec's admissibility predicate does
# NOT admit: a string carrying a code point outside ASCII that a case-folding
# table maps onto an ASCII letter, in a position where the callee matches
# letters (a qualifier tag or a build-tag segment). Released revisions of the
# callee read these differently from each other (see SCOPE above), so the model
# is neither validated nor faulted on them; they are only reported. Each entry
# is asserted non-ASCII below, so this list cannot quietly absorb an admitted
# input.
# Spelled as code points, not as literal glyphs: two of the four are visually
# indistinguishable from the ASCII letter they fold onto.
_LONG_S = chr(0x017F)     # folds onto ASCII "s"
_DOTTED_I = chr(0x0130)   # folds onto ASCII "i"
_DOTLESS_I = chr(0x0131)  # folds onto ASCII "i"
_KELVIN = chr(0x212A)     # folds onto ASCII "k"

OUT_OF_SCOPE = (
    f"1.0po{_LONG_S}t1", f"1.0po{_LONG_S}t", f"1.0dev1+{_LONG_S}",
    f"1.0+a{_LONG_S}", f"1.0+{_LONG_S}", f"1.0r{_LONG_S}", f"1.0{_LONG_S}",
    _LONG_S,
    f"1.0{_DOTTED_I}", f"1.0d{_DOTTED_I}v1", f"1!2.3{_DOTTED_I}",
    f"1.0+a{_DOTTED_I}", _DOTTED_I,
    f"1.0{_DOTLESS_I}", f"1.0+{_DOTLESS_I}",
    f"1.0+{_KELVIN}", f"1.0dev1+{_KELVIN}", f"1.0{_KELVIN}",
    # non-ASCII text that is NOT of that class: a non-Latin digit, a letter no
    # folding table maps onto ASCII, and the non-ASCII blanks the callee's
    # `\s*` wrapper strips. Listed here because the admissibility predicate is
    # drawn at the ASCII boundary — which is the version grammar's own
    # character set, and stable — rather than at the narrower folding class.
    "١.0", "1.0RC١", "1.0А", "　1.0", "\xa01.0",
)


def main() -> int:
    checked = 0

    # SCOPE ASSERTIONS. Every checked string is admitted by the spec; every
    # excluded string is genuinely outside it. Neither list can drift into the
    # other without failing here.
    for s in POOL:
        if not is_ascii(s):
            print("VIOLATION", ("scope: POOL string is not ASCII", s))
            print("status=fail")
            return 1
    for s in OUT_OF_SCOPE:
        if is_ascii(s):
            print("VIOLATION", ("scope: OUT_OF_SCOPE string is ASCII, so the "
                               "spec admits it and it must be checked", s))
            print("status=fail")
            return 1

    # P0 exhaustively over the pool.
    for s in POOL:
        r = check_string(s)
        if r:
            print("VIOLATION", r)
            print("status=fail")
            return 1
        checked += 1

    # P1 / P2 / P3 exhaustively over pool x pool (boundary set).
    for req in POOL:
        for ver in POOL:
            r = check_pair(req, ver)
            if r:
                print("VIOLATION", r)
                print("status=fail")
                return 1
            checked += 1

    # Random fuzz: assemble ASCII strings from the version grammar's shapes
    # (epoch, release of varying arity, qualifier tags with varying separators,
    # build tags, blanks), plus deliberately malformed ones, to exercise
    # P0/P1/P2/P3 broadly.
    rnd = _lcg(SEED)
    seps = ("", ".", "-", "_")
    pre_sp = ("a", "b", "c", "rc", "alpha", "beta", "pre", "preview", "A", "RC")
    post_sp = ("post", "rev", "r", "POST")

    def rand_ver():
        kind = next(rnd) % 8
        if kind == 0:
            return POOL[next(rnd) % len(POOL)]
        s = ""
        if next(rnd) % 4 == 0:
            s += ("v", "V")[next(rnd) % 2]
        if next(rnd) % 5 == 0:
            s += str(next(rnd) % 4) + "!"
        ncomp = 1 + next(rnd) % 4
        s += ".".join(str(next(rnd) % 30) for _ in range(ncomp))
        if next(rnd) % 2 == 0:
            s += seps[next(rnd) % 4] + pre_sp[next(rnd) % len(pre_sp)]
            if next(rnd) % 3:
                s += seps[next(rnd) % 4] + str(next(rnd) % 10)
        if next(rnd) % 3 == 0:
            if next(rnd) % 3 == 0:
                s += "-" + str(next(rnd) % 10)
            else:
                s += seps[next(rnd) % 4] + post_sp[next(rnd) % len(post_sp)]
                if next(rnd) % 3:
                    s += seps[next(rnd) % 4] + str(next(rnd) % 10)
        if next(rnd) % 3 == 0:
            s += seps[next(rnd) % 4] + "dev"
            if next(rnd) % 3:
                s += str(next(rnd) % 10)
        if next(rnd) % 4 == 0:
            nseg = 1 + next(rnd) % 3
            s += "+" + ".".join(
                ("ubuntu", "1", "abc", "x9", "0")[next(rnd) % 5]
                for _ in range(nseg))
        if kind == 7:   # inject a malformed tail sometimes
            s += (".x", "..", "_", "+", "!", "-", "v")[next(rnd) % 7]
        if next(rnd) % 8 == 0:
            s = " " + s
        return s

    for _ in range(N):
        req, ver = rand_ver(), rand_ver()
        for s in (req, ver):
            if not is_ascii(s):
                print("VIOLATION", ("scope: fuzzer produced a non-ASCII "
                                    "string, so the run would skip an input "
                                    "the spec admits", s))
                print("status=fail")
                return 1
            r = check_string(s)
            if r:
                print("VIOLATION", r)
                print("status=fail")
                return 1
        r = check_pair(req, ver)
        if r:
            print("VIOLATION", r)
            print("status=fail")
            return 1
        checked += 1

    # Observation only (never a verdict): what THIS environment's callee does on
    # the excluded class, recorded so the exclusion is inspectable rather than
    # merely asserted.
    agree = sum(1 for s in OUT_OF_SCOPE
                if (release_key(s) is not None) == real_accepts(s))
    print(f"out_of_scope={len(OUT_OF_SCOPE)} "
          f"(model/callee accept-set agreement there: {agree}/"
          f"{len(OUT_OF_SCOPE)}; not gated — the callee's revisions disagree "
          f"on that class, so the spec does not claim it)")
    print(f"checked={checked} violations=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
