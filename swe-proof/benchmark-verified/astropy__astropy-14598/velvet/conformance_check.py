#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14598 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `recoverSegmentText` impl
              region transliterated to Python over the real repo type (`str`),
              via the mapping.md bijection (`List Char` ↔ `str` per code point).
              The Lean defs are modeled FAITHFULLY: `recordContent` reads the
              record's content off the record grammar (`closesContent` /
              `onlyPaddingThenAnnotation` / `firstPrefix` / `isContentChar`) and
              yields `None` for a text in which no delimiter closes a content;
              `rstripSpaces` drops only the space code point
              (`dropWhile (· = ' ')` from the end); the `&`-trim uses
              `getLast?`/`dropLast`. No A-tagged content (this bundle has no
              axioms / no A-reference), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the post-patch per-segment recovery
              lines of `Card._split` (`card.py:861-865` after the gold patch),
              driven by the post-patch `_strg_comment_RE` (`card.py:69`, quoted
              verbatim), executed with Python's NATIVE `re` backtracking,
              `str.rstrip()` and `[-1]` slice semantics. A non-match — the real
              code's early `return kw, vc`, where no value is appended at all —
              is the oracle's `None`. This is a DISTINCT implementation from the
              shadow (regex backtracking vs an explicit grammar scan,
              rstrip-all-whitespace vs drop-only-space), so agreement is a
              genuine R-bijection witness, not a tautology.

They must agree on every input, on the WHOLE unrestricted `str` domain — the
modeled method carries no `require`. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

DOMAIN (load-bearing). The modeled op is asserted for EVERY `vc` the real
recovery can receive, and the corpus must therefore not be narrower than that.
Two ways an earlier corpus was:

  * it excluded `/` from the inner alphabet, so it never reached the
    comment-bearing segments `_itersubcards()` really produces — `Card("FOO",
    "x"*100 + "''", "comment")` yields a final segment `vc = "'' / comment"` fed
    to these exact lines. Fixed: `/`-bearing and unbookended segments are fuzzed.
  * it drew EVERY character from PRINTABLE (`[ -~]`), so it could not reach a
    single input outside the record content set — while the reader API
    (`Card.fromstring` / `Header.fromstring`) accepts arbitrary card text, so
    such a `vc` genuinely reaches the recovery (e.g. a non-content character
    sitting in the annotation region, `vc = "'tail' / com<TAB>ment"`). The
    modeled `isContentChar` guard and the line-break end-of-record case are the
    real callee's behaviour there, and a corpus that cannot generate the inputs
    they govern ENFORCES neither. Fixed: `NON_CONTENT` is in the alphabet and in
    the fixed cases, so the guard is checked rather than assumed.

Both sides are TOTAL — nothing is skipped, so no input can be silently excused.

A complementary check drives the REAL patched `astropy.io.fits` round-trip on
fuzzed long values (the actual F2P observable) when astropy is importable in the
container; this ties the verdict to patch.diff behaviour end-to-end (the gold
patch — both hunks — is applied before this runs, per the harness). Half of those
values are round-tripped WITH a comment, which is what actually drives a
comment-bearing segment through the modeled recovery.

Round-trip DOMAIN (load-bearing): astropy does NOT promise
`fromstring(image(v)).value == v` for every `v`. Two trailing tails are
non-round-trippable BY DESIGN and UNCHANGED by this patch — unrelated to the
`''` bug being fixed:
  * a trailing `&` is the FITS CONTINUE continuation marker, stripped
    unconditionally by the `&`-trim (`card.py:863-864`); and
  * trailing whitespace is removed by `value.rstrip()` (`card.py:862`).
`_format_long_image` cannot encode either tail distinguishably, so the reader
legitimately loses it. The F2P test and the problem-statement reproduction both
live strictly inside this domain (their values end in `x`/`'`, never in ` `/`&`).
Accordingly the complementary fuzz rstrips ` `/`&` from each generated value
before asserting the round-trip invariant — asserting it only where astropy
actually guarantees it. (A faithful local encode/decode simulation confirms
ZERO round-trip failures on this domain are caused by anything other than the
` `/`&` tail, and that the pre-patch code fails on this very domain — so the
restriction neither hides the bug nor weakens the contract.)

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md) for a deterministic verdict.
"""
import random
import re
import sys

SEED = 14598
N_FUZZ = 100_000

# Printable-ASCII card-content domain [ -~] = code points 0x20..0x7E (mapping.md).
PRINTABLE = [chr(c) for c in range(0x20, 0x7F)]

QUOTE, SPACE, ANNOT, AMP, BREAK = "'", " ", "/", "&", "\n"

# Characters OUTSIDE the record content set [ -~]. The reader API accepts
# arbitrary card text, so a `vc` carrying one of these really can reach the
# modeled recovery; an earlier corpus drew only from PRINTABLE and therefore
# could not reach a single such input. They are fuzzed here so the content
# character set is ENFORCED by this gate rather than assumed.
NON_CONTENT = ["\t", "\n", "\r", "\v", "\f", "\x00", "\x1f", "\x7f", "\x85", "é"]

# The post-patch `_strg_comment_RE` (the gold's anchored regex, card.py:69) is the
# ORACLE for the content-read step. Quoted verbatim from the post-patch source so
# the oracle is a DISTINCT implementation from the shadow's explicit scan.
_STRG = r"\'(?P<strg>([ -~]+?|\'\'|) *?)\'(?=$|/| )"
_COMM_FIELD = r"(?P<comm_field>(?P<sepr>/ *)(?P<comm>(.|\n)*))"
_STRG_COMMENT_RE_POST = re.compile(f"({_STRG})? *{_COMM_FIELD}?$")


# --- the R/I shadow: Solution.lean's pure region, transliterated -------------

def _is_content_char(c):
    """isContentChar: the record content character set, `' '`..`'~'` — i.e. the
    printable range 0x20..0x7E. Mirrors the regex body class `[ -~]`."""
    return SPACE <= c <= "~"


def _only_padding_then_annotation(rest):
    """onlyPaddingThenAnnotation: once the content is over a record holds only
    padding and then at most an annotation, which runs to the record's end — or
    else the single line break a record may be terminated by (the `$` anchor
    matches before a final newline as well as at the very end)."""
    t = rest.lstrip(SPACE)                      # rest.dropWhile (· = spaceCh)
    if t == "":
        return True
    return t[0] == ANNOT or (t[0] == BREAK and len(t) == 1)


def _closes_content(rest):
    """closesContent: `rest` opens with the delimiter that closes the content."""
    return bool(rest) and rest[0] == QUOTE and _only_padding_then_annotation(rest[1:])


def _first_prefix(p, l):
    """firstPrefix: shortest NON-EMPTY prefix of `l` made of content characters
    ONLY whose remainder satisfies p. The scan stops dead at the first character
    a record's content cannot hold (the `[ -~]+?` body class)."""
    if not l:
        return None
    c, rest = l[0], l[1:]
    if not _is_content_char(c):
        return None
    if p(rest):
        return c
    sub = _first_prefix(p, rest)
    return None if sub is None else c + sub


def _record_content(field):
    """recordContent: the content of one record, read off the record grammar.
    None when the text is not a record — no delimiter in it closes a content."""
    if field == "":
        return ""
    c, rest = field[0], field[1:]
    if c == QUOTE:
        body = _first_prefix(_closes_content, rest)
        if body is not None:
            return body
        return "" if _closes_content(rest) else None
    return "" if _only_padding_then_annotation(field) else None


def shadow_recover(field):
    """recoverSegmentText's `do` block transliterated:
        let out := (recordContent field).map (fun content =>
          let trimmed := (content.reverse.dropWhile (· = ' ')).reverse
          if trimmed.getLast? = some '&' then trimmed.dropLast else trimmed)
    rstripSpaces drops ONLY the space code point (faithful to the Lean defs)."""
    content = _record_content(field)
    if content is None:
        return None                           # Option.none — no literal text
    i = len(content)
    while i > 0 and content[i - 1] == SPACE:   # dropWhile (·=' ') from the end
        i -= 1
    trimmed = content[:i]
    if trimmed and trimmed[-1] == AMP:         # trimmed.getLast? = some '&'
        return trimmed[:-1]                    # trimmed.dropLast
    return trimmed


# --- the oracle: patch.diff behaviour (post-patch card.py:69 + 861-865) -------

def oracle_recover(field):
    """The post-patch per-segment recovery, with the real post-patch regex + native
    Python semantics:
        m = _strg_comment_RE.match(vc)         # ANCHORED regex (card.py:69)
        if not m:
            return kw, vc                      # no value appended at all
        value = m.group("strg") or ""
        value = value.rstrip()                 # the `.replace("''","'")` is gone
        if value and value[-1] == "&":
            value = value[:-1]
    It composes BOTH gold hunks: the capture (which span of `vc` becomes the
    content) and the recovery (rstrip + `&`-trim, no `''`-collapse). It is a
    DISTINCT implementation from the shadow (regex backtracking vs an explicit
    grammar scan, native rstrip-all-whitespace vs drop-only-space), so agreement
    is a genuine R-bijection witness over the modeled domain, not a tautology."""
    m = _STRG_COMMENT_RE_POST.match(field)
    if not m:
        return None                            # the real code's early return
    value = m.group("strg") or ""
    value = value.rstrip()
    if value and value[-1] == AMP:
        value = value[:-1]
    return value


def fuzz_fields(n, rng):
    """Yield record contents `vc` of every shape the real per-segment recovery can
    receive — bookended `'<inner>'`, ANNOTATED `'<inner>' / <comment>` (what
    `_itersubcards()` hands over whenever a continued string value carries a
    comment), and malformed/unbookended text (which the real code answers with its
    early `return kw, vc`). The annotation introducer `/` is IN the alphabet: the
    earlier corpus excluded it and thereby fuzzed a domain the real callee does not
    stay within — the G-PANEL-2 defect."""
    fixed = [
        # bookended, comment-free
        "''", "'''", "''''", "'''''", "' '", "'   '", "'&'", "'&  '",
        "'x'''", "'x'' '", "'x''&'", "'x''&  '", "'''x'''",
        "'" + "x" * 60 + "''", "'" + "x" * 60 + "'' '",
        "'" + "x" * 60 + "''" + "x" * 10 + "'",
        "'" + "x" * 31 + "'''' xxx'", "'" + "x" * 31 + "''''xxx'",
        "'aa'' bb'", "'aa'''' bb'", "'aa''' bb'", "'abc def'",
        "'ab'", "'ab  '", "'ab&'", "'ab& '", "'a' x'", "'a' bc'", "'a'  '",
        # ANNOTATED — the shape the G-PANEL-2 witness lives in
        "'' / comment", "'' / the trailing comment zz", "'val' / comment",
        "'a&' / cmt", "'' /", "'' / ", "'' /c", "'a' / b", "'a'/c",
        "'a''b' / c", "'x'' y' / c", "'' / don't", "'' / c / d",
        "'" + "x" * 33 + "'''' aaa&' / comment",
        "'" + "x" * 67 + "&' / comment",
        # malformed / unbookended — the real code's early-return path
        "", "abc", "'abc", "   ", "/", " / c", "x' y", "'a",
        # OUTSIDE the record content set [ -~] — reachable through the reader
        # API, which accepts arbitrary card text. Both sides must agree here
        # too; the earlier corpus could not generate any of these.
        "'\t'", "'a\tb'", "'ab'\t", "'ab' \t", "'ab' /\tc", "'a\nb'",
        "'a'\n", "'a'  \n", "'a' \n ", "'a'\n\n", "'a'\n/", "'a'/\n",
        "''/\n'", "\n", "\t", "'\x00'", "'\x7f'", "'é'", "'a'\r",
        "'tail' / com\tment", "'' / c\nd", "'x\x1fy'", "'a&'\n",
    ]
    for f in fixed:
        yield f
    # Two alphabets, deliberately. `alpha` is the record-content alphabet (the
    # domain the real encoder stays inside, where the recovery does its real
    # work); `alpha_nc` additionally carries characters OUTSIDE the record
    # content set, which the reader API can still deliver. Sampling both keeps
    # the well-formed-record domain densely covered while ALSO enforcing the
    # content-character guard and the end-of-record line break (the G-PANEL-2
    # domain gap) instead of assuming them. A single heavily
    # non-content-weighted alphabet would swamp the corpus with non-records and
    # thin out exactly the `some`-answering inputs that carry the behaviour.
    alpha = list("'' '' ''  ///&&& xy~") + PRINTABLE
    alpha_nc = alpha + NON_CONTENT * 4
    for i in range(n):
        # 1 input in 4 is drawn from the non-content alphabet.
        a = alpha_nc if i % 4 == 0 else alpha
        k = rng.randint(0, 40)
        inner = "".join(rng.choice(a) for _ in range(k))
        # a third bare, a third bookended, a third bookended + annotation
        r = i % 3
        if r == 0:
            yield inner
        elif r == 1:
            yield QUOTE + inner + QUOTE
        else:
            tail = "".join(rng.choice(a) for _ in range(rng.randint(0, 12)))
            yield QUOTE + inner + QUOTE + " / " + tail
        # every 7th input is an otherwise WELL-FORMED record with a single
        # trailing non-content character — the shape the end-of-record boundary
        # turns on (a final line break, which the record may be terminated by,
        # versus any other such character, which it may not).
        if i % 7 == 0:
            body = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 12)))
            yield QUOTE + body + QUOTE + rng.choice(NON_CONTENT)


def check_shadow_vs_oracle(rng):
    disagreements = []
    count = n_annot = n_nomatch = n_noncontent = 0
    for field in fuzz_fields(N_FUZZ, rng):
        count += 1
        sh = shadow_recover(field)
        orc = oracle_recover(field)
        if ANNOT in field:
            n_annot += 1
        if orc is None:
            n_nomatch += 1
        if any(not _is_content_char(c) for c in field):
            n_noncontent += 1
        # Both sides are TOTAL: a non-match is `None` on both, so NOTHING is
        # skipped. Every generated input is compared.
        if sh != orc:
            disagreements.append((field, sh, orc))
            if len(disagreements) >= 5:
                break
    return count, disagreements, n_annot, n_nomatch, n_noncontent


def check_real_roundtrip(rng):
    """Complementary: the actual F2P observable via the patched astropy.
    For a long value, Card(...).image then Card.fromstring(...).value must
    round-trip. Returns (n, failures) or (0, []) if astropy isn't importable."""
    try:
        from astropy.io import fits
    except Exception:
        return 0, []
    failures = []
    n = 0
    # the three F2P seed values plus fuzzed long values containing ''
    seeds = ["x" * 100 + "''", "x" * 100 + "''xxx", "x" * 100 + "'' xxx"]
    for n_pad in range(50, 75):
        seeds.append("x" * n_pad + "''")
        seeds.append("x" * n_pad + "''" + "x" * 10)
        seeds.append("y" * n_pad + "'' z")
    # Random long values that stress a doubled quote `''` at/around the 67-char
    # CONTINUE segment boundary (the actual bug). We restrict to the genuine
    # round-trip domain: astropy does NOT promise `fromstring(image(v)).value==v`
    # for every `v`. Two tails are non-round-trippable BY DESIGN, unchanged by
    # this patch and unrelated to the `''` bug:
    #   * a trailing `&` is the FITS CONTINUE continuation marker, stripped
    #     unconditionally by the `&`-trim (`card.py:863-864`); and
    #   * trailing whitespace is removed by `value.rstrip()` (`card.py:862`).
    # `_format_long_image`'s encoder cannot represent either tail distinguishably,
    # so the reader legitimately loses it. The F2P test and the problem-statement
    # reproduction both live in this domain (their values end in `x`/`'`, never
    # in space or `&`). We therefore strip trailing spaces and `&` from each
    # generated value (interior `&`/space and all `''` stressing are preserved),
    # asserting the round-trip invariant only where astropy actually guarantees it.
    for _ in range(2000):
        k = rng.randint(60, 140)
        body = "".join(rng.choice(list("xy ") + ["''", "'", "&"]) for _ in range(k))
        body = body.rstrip(" &")
        if body:
            seeds.append(body)
    # Half the long values are ALSO round-tripped WITH a comment, which is what
    # drives a comment-bearing segment (`vc = "'' / comment"`) through the modeled
    # recovery — the reachability the G-PANEL-2 witness turned on.
    for idx, val in enumerate(seeds):
        comments = (None,) if idx % 2 else (None, "a trailing comment zz")
        for comment in comments:
            try:
                c1 = fits.Card("CONFIG", val) if comment is None else \
                    fits.Card("CONFIG", val, comment)
                c2 = fits.Card.fromstring(str(c1))
                n += 1
                if c1.value != c2.value:
                    failures.append((val, c1.value, c2.value))
            except Exception as e:
                failures.append((val, "EXC", repr(e)))
            if len(failures) >= 5:
                return n, failures
    return n, failures


def main():
    rng = random.Random(SEED)
    count, disagreements, n_annot, n_nomatch, n_noncontent = \
        check_shadow_vs_oracle(rng)
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for field, sh, orc in disagreements:
            print("  field=%r shadow=%r oracle=%r" % (field, sh, orc))
        return 1

    rt_n, rt_fail = check_real_roundtrip(rng)
    if rt_fail:
        print("G-CONF FAIL: %d real astropy round-trip mismatch(es) over %d values:"
              % (len(rt_fail), rt_n))
        for val, a, b in rt_fail:
            print("  value=%r card1=%r card2=%r" % (val[:40] + "…", a, b))
        return 1

    rt_msg = ("; real astropy round-trip OK on %d long values (half of them with "
              "a comment, driving comment-bearing segments through the modeled "
              "recovery)" % rt_n) if rt_n else \
             "; astropy not importable, round-trip check skipped"
    print("G-CONF OK: R/I shadow of recoverSegmentText agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements — of which %d carry "
          "an annotation (`/`), %d carry a character outside the record content "
          "set [ -~] (so the content-character guard is enforced, not assumed), "
          "and %d are texts the real code answers with its early return (modeled "
          "as `none`)%s."
          % (count, SEED, n_annot, n_noncontent, n_nomatch, rt_msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
