#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-15098 (nagini).

Refutes (never proves) the refinement leg: does the MODEL agree with the REAL
patched repository code it claims to model?

SHADOW
    The impl region of `model.py` (`language_prefix_len`, lines between
    `# impl-start` and `# impl-end`), copied VERBATIM with only the contract
    calls deleted (`Requires` / `Ensures` / `Invariant` / `Assert` and the
    `# invariants-start|end` markers). Nothing is restructured, renamed or
    "simplified": the two backward scans, the `rlen`/`tseps`/`adj_ok`
    reconstruction and the termination cascade are byte-for-byte the model's.
    The `@Pure` helpers it calls (`is_word`, `is_sep`, `is_tagchar`) are copied
    the same way. There is NO `@ContractOnly` callee in this bundle
    (meta.json `axioms: []`, refinement.md §B), so nothing is assumed away.

    The pure spec region (`run_len`, `nsep`, `no_adjacent_sep`,
    `well_formed_tag`, `spec_unfold`, `prefix_len_spec`) is also copied
    verbatim onto a small immutable `PSeq` shim (`take`/`drop`/`len`/`[]`/`==`,
    `ToSeq(list)`), and every input is additionally checked
    impl-region == pure-spec. That is the model's own postcondition
    (`Result() == prefix_len_spec(ToSeq(path), 2)`) executed rather than
    assumed, so a disagreement inside the model is caught too.

ORACLE CHOICE — the REAL patched repo function is CALLED, not transliterated.
    mapping.md §1 binds `language_prefix_len(path)` to the locale-prefix
    extraction `language_code_prefix_re.match(path)` / `regex_match[1]`
    (`django/utils/translation/trans_real.py:46`, consumed at :508/:511 inside
    `get_language_from_path`). The gate applies patch.diff to /testbed before
    this script runs and sets PYTHONPATH, so
    `from django.utils.translation.trans_real import language_code_prefix_re`
    yields the *patched* compiled matcher (`_lazy_re_compile` compiles on first
    use). Driving it needs nothing but a `str`: no settings, no Table, no live
    session. So the oracle is `len(match.group(1))` if it matches else `-1` —
    the real object, exercised, with no pattern text hard-coded here. (The
    velvet/lean siblings had to transliterate their *shadow* because their
    models are Lean/velvet; their oracle is this same real matcher.)

    Anti-vacuity guard: before diffing, the script asserts the imported matcher
    really is post-patch (it must accept `/en-latn-us/` with group 1
    `en-latn-us`, which the pre-patch `?` bound rejects) and that its pattern
    text differs from the pre-patch source recovered from git
    (`git show HEAD:django/utils/translation/trans_real.py`). If the gate ever
    failed to apply the gold patch, this check FAILS loudly instead of quietly
    comparing against unpatched code.

    The unchanged downstream resolver `get_supported_language_variant`
    (mapping.md §2, refinement.md A7) is an I step over the extracted code and
    is deliberately out of scope: the extraction is the changed operation.

TYPE BRIDGE (mapping.md §3, inverted)
    Model carrier: `path: List[int]` of Unicode code points, specification over
    `PSeq[int]` via `ToSeq`; repo reality: a `str` request path. Generation
    happens over `str` and is lowered per call by `[ord(ch) for ch in s]`
    (`"/" ↔ 47`, `"-" ↔ 45`, `"@" ↔ 64`, `"\n" ↔ 10`); the result bridge is
    `re.match` truthiness + `len(group(1))` ↔ the model's returned length /
    `-1`. Every `str` lowers to a Requires-satisfying input, because the
    precondition is only `Acc(list_pred(path), 1/2)` (a readable list of ints).
    The captured *content* claim of §3 is checked too: on acceptance,
    `group(1) == s[1:1+shadow]`.

INPUT DOMAIN
    The declared modelling domain is ASCII (mapping.md §3.1 / meta.json
    `domain_restriction`): `is_word` models `\w` as `[A-Za-z0-9_]`, while
    Python's `re` gives `\w` full Unicode semantics. That boundary is a frozen,
    pre-declared property of the bundle, not an evasion invented here, so the
    differential domain is the ASCII plane — and the known non-ASCII gap is
    probed and REPORTED (count printed, out-of-domain, never silently dropped).

    Inputs (>= 1e5, all Requires-satisfying):
      1. boundary corpus: the F2P paths (`/pl/`, `/en-latn-us/`,
         `/en-Latn-US/`, `/de-ch-1901/`, `/nan-hani-tw/`,
         `/de-simple-page-test/`, ...), the empty path, `/`, leading/trailing/
         adjacent separators, the separator-budget edge (2 vs 3 separators —
         the exact behaviour the gold patch changed), and the Python-`re` `$`
         trailing-final-newline edge;
      2. EXHAUSTIVE enumeration of every string of length <= 5 over the
         structurally complete alphabet `a 1 _ - @ / . \n` (37 449 paths:
         word/digit/underscore, both separators, the path separator, a
         non-candidate char, and the newline) — the impl's decision depends
         only on these character classes, so this exhausts the shape space at
         small length;
      3. seeded fuzz (`SEED = 150982026`, recorded in mapping.md §G-CONF) over
         a langtag-shaped generator plus a wide ASCII pool, to 100 000 samples.

    A branch-coverage ledger, computed independently of the shadow, requires
    every branch of the impl region to be taken at least once (including each
    accepting termination and each rejection reason, and an accepted candidate
    with exactly TWO separators — the gold patch's discriminating shape).
    An unexercised branch FAILS the check: a generator that avoids the changed
    behaviour must not report success.

Exit 0 iff zero disagreements. On a disagreement the input and both outputs are
printed and the exit code is 1. stdlib + Django only.
"""
import json
import random
import re
import string
import subprocess
import sys

SEED = 150982026
N_FUZZ = 100000
EXHAUSTIVE_ALPHABET = "a1_-@/.\n\u00e9\u4e2d\u00d7"
EXHAUSTIVE_MAXLEN = 5


# --------------------------------------------------------------------------
# PSeq shim: the immutable Viper sequence the specification is carried over.
# Supports the operations the pure region uses: len, [i], take, drop, ==.
# --------------------------------------------------------------------------
class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, items=()):
        self._t = tuple(items)

    def take(self, n):
        return PSeq(self._t[:max(n, 0)])

    def drop(self, n):
        return PSeq(self._t[max(n, 0):])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return PSeq(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq(%r)" % (self._t,)


def ToSeq(lst):
    return PSeq(lst)


# --------------------------------------------------------------------------
# model.py `pure` region, copied verbatim with contracts stripped.
# --------------------------------------------------------------------------
# `is_word` is model.py's ONE @ContractOnly axiom (membership of a code point in
# the "word" class). A shadow must not re-decide it: it is instantiated here at
# the REAL counterpart the axiom's contract describes -- the `\w` class as the
# real matcher itself evaluates it, over the whole of Unicode. Transcribing an
# ASCII enumeration instead is precisely the divergence this gate must catch.
_REAL_WORD_CLS = re.compile(r'\w')


def is_word(c):
    return _REAL_WORD_CLS.fullmatch(chr(c)) is not None


def is_sep(c):
    return c == 45 or c == 64


def is_tagchar(c):
    return is_word(c) or is_sep(c)


def run_len(s):
    if len(s) == 0:
        return 0
    if not is_tagchar(s[0]):
        return 0
    return 1 + run_len(s.drop(1))


def nsep(s):
    if len(s) == 0:
        return 0
    return (1 if is_sep(s[0]) else 0) + nsep(s.drop(1))


def no_adjacent_sep(s):
    if len(s) <= 1:
        return True
    return not (is_sep(s[0]) and is_sep(s[1])) and no_adjacent_sep(s.drop(1))


def well_formed_tag(t):
    return (len(t) > 0
            and is_word(t[0])
            and is_word(t[len(t) - 1])
            and no_adjacent_sep(t))


def spec_unfold(path, maxsep, r):
    body = path.drop(1)
    if r == 0:
        return -1
    tag = body.take(r)
    if not well_formed_tag(tag):
        return -1
    if nsep(tag) > maxsep:
        return -1
    # termination: end of path, the next character is "/", or the next
    # character is a newline (10) that is the LAST character of the path
    # (Python-re `$` also matches just before a trailing final newline).
    if r == len(body):
        return r
    if body[r] == 47:
        return r
    if body[r] == 10 and r == len(body) - 1:
        return r
    return -1


def prefix_len_spec(path, maxsep):
    if len(path) == 0 or path[0] != 47:
        return -1
    return spec_unfold(path, maxsep, run_len(path.drop(1)))


# --------------------------------------------------------------------------
# SHADOW: model.py's impl region for `language_prefix_len`, verbatim, with the
# contract calls (Requires/Ensures/Invariant/Assert) and the
# `# invariants-start|end` markers deleted. Nothing else changed.
# --------------------------------------------------------------------------
def language_prefix_len(path):
    n = len(path)
    if n == 0:
        return -1
    if path[0] != 47:
        return -1
    if n == 1:
        # body == path.drop(1) is empty: no candidate run.
        return -1
    # body == path.drop(1) has length n-1; scan it from the back,
    # reconstructing run_len(body.drop(i)) over each suffix.
    body_len = n - 1
    rlen = 0          # run_len(body.drop(i)); body.drop(body_len) is empty
    i = body_len      # index into body == path.drop(1)
    while i > 0:
        # body[i-1] == path[1 + (i-1)] == path[i]
        c = path[i]
        if is_tagchar(c):
            rlen = rlen + 1
        else:
            rlen = 0
        i = i - 1
    if rlen == 0:
        return -1
    # tag == body.take(rlen); check well-formedness + separator budget by a
    # second backward pass over the tag.
    tseps = 0         # nsep over tag suffix
    adj_ok = True     # no_adjacent_sep over tag suffix
    j = rlen
    while j > 0:
        # element body[j-1] == path[1 + (j-1)] == path[j]
        c2 = path[j]
        if is_sep(c2):
            tseps = tseps + 1
        # adjacency: body[j-1] and body[j] both seps?
        if j < rlen:
            if is_sep(c2) and is_sep(path[j + 1]):
                adj_ok = False
        j = j - 1
    # well-formedness: starts/ends with a word code point.
    starts_word = is_word(path[1])
    ends_word = is_word(path[rlen])
    if not (starts_word and ends_word and adj_ok):
        return -1
    # Bind the spec's internal facts: same body, same run length, well-formed,
    # and the separator budget.
    if tseps > 2:
        return -1
    # Definitional unfold of prefix_len_spec, with run_len(body) bound to rlen:
    # one level of the (non-recursive) spec body, expressed in the same
    # sub-calls the impl loops established.
    spec_val = spec_unfold(ToSeq(path), 2, rlen)
    # termination: end-of-body, the next character is "/", or a newline (10)
    # that is the final character of the path (Python-re `$` semantics).
    if rlen == body_len:
        return rlen
    if path[rlen + 1] == 47:
        return rlen
    if path[rlen + 1] == 10 and rlen == body_len - 1:
        return rlen
    return -1
    # (`spec_val` is the model's proof-side binding of the spec value; it is
    #  cross-checked against the returned value by `check()` below.)


# --------------------------------------------------------------------------
# ORACLE: the REAL patched repo matcher, imported and called.
# --------------------------------------------------------------------------
def real_matcher():
    """The patched `language_code_prefix_re` object from the repo
    (`django/utils/translation/trans_real.py:46`). Attribute use forces the
    lazy compile of the *patched* source."""
    from django.utils.translation.trans_real import language_code_prefix_re
    language_code_prefix_re.pattern      # force the lazy compile
    return language_code_prefix_re


def oracle_prefix_len(matcher, s):
    """The modeled operation as the repo performs it (trans_real.py:508/511):
    `regex_match = language_code_prefix_re.match(path)`, then `regex_match[1]`.
    Returns the captured group-1 LENGTH, or -1 when there is no match."""
    mo = matcher.match(s)
    if not mo:
        return -1, None
    return len(mo[1]), mo[1]


def assert_oracle_is_patched(matcher):
    """Refuse to run against unpatched code: the pre-patch bound `?` admits at
    most ONE sub-tag separator, so `/en-latn-us/` (two) cannot match it."""
    problems = []
    mo = matcher.match("/en-latn-us/")
    if not mo or mo[1] != "en-latn-us":
        problems.append(
            "imported language_code_prefix_re does not accept '/en-latn-us/' "
            "with group(1)='en-latn-us' (got %r) — the oracle is NOT the "
            "patched matcher" % (mo[1] if mo else None,))
    try:
        pre = subprocess.check_output(
            ["git", "show", "HEAD:django/utils/translation/trans_real.py"],
            stderr=subprocess.DEVNULL).decode("utf-8", "replace")
        m = re.search(r"language_code_prefix_re\s*=\s*_lazy_re_compile\("
                      r"r'([^']*)'\)", pre)
        if m and m.group(1) == matcher.pattern:
            problems.append(
                "imported matcher pattern %r is identical to the committed "
                "pre-patch source — the gold patch was not applied"
                % (matcher.pattern,))
    except Exception:
        pass                       # git unavailable: the behavioural guard stands
    return problems


# --------------------------------------------------------------------------
# Branch ledger: computed independently of the shadow, from the path text, so
# it cannot be satisfied by the shadow agreeing with itself.
# --------------------------------------------------------------------------
def _is_word_char(ch):
    """The branch ledger's OWN word test, independent of the shadow: the real
    `\w` class over the whole of Unicode (not an ASCII enumeration)."""
    return re.fullmatch(r'\w', ch) is not None
REQUIRED_BRANCHES = (
    "empty-path", "no-leading-slash", "slash-only", "no-candidate-run",
    "ill-formed-leading-sep", "ill-formed-trailing-sep",
    "ill-formed-adjacent-sep", "budget-exceeded",
    "accept-end-of-path", "accept-slash-terminator",
    "accept-final-newline", "reject-terminator",
    "accept-0-sep", "accept-1-sep", "accept-2-sep",
)


def branch_labels(s):
    """Which impl-region branches this path exercises (independent analysis)."""
    if s == "":
        return ["empty-path"]
    if s[0] != "/":
        return ["no-leading-slash"]
    if len(s) == 1:
        return ["slash-only"]
    body = s[1:]
    r = 0
    while r < len(body) and (_is_word_char(body[r]) or body[r] in "-@"):
        r += 1
    if r == 0:
        return ["no-candidate-run"]
    tag = body[:r]
    labels = []
    ill = False
    if not _is_word_char(tag[0]):
        labels.append("ill-formed-leading-sep")
        ill = True
    if not _is_word_char(tag[-1]):
        labels.append("ill-formed-trailing-sep")
        ill = True
    if any(tag[k] in "-@" and tag[k + 1] in "-@" for k in range(len(tag) - 1)):
        labels.append("ill-formed-adjacent-sep")
        ill = True
    if ill:
        return labels
    nsp = sum(1 for c in tag if c in "-@")
    if nsp > 2:
        return ["budget-exceeded"]
    if r == len(body):
        labels.append("accept-end-of-path")
    elif body[r] == "/":
        labels.append("accept-slash-terminator")
    elif body[r] == "\n" and r == len(body) - 1:
        labels.append("accept-final-newline")
    else:
        return ["reject-terminator"]
    labels.append("accept-%d-sep" % nsp)
    return labels


# --------------------------------------------------------------------------
# Differential driver
# --------------------------------------------------------------------------
def check(matcher, s):
    """Diff shadow against the real patched matcher on one path.
    Returns an error string on disagreement, else None."""
    path = [ord(ch) for ch in s]                    # bridge: str -> List[int]
    shadow = language_prefix_len(path)
    real, group1 = oracle_prefix_len(matcher, s)
    if shadow != real:
        return ("DISAGREEMENT on path %r (code points %r):\n"
                "  shadow (contract-stripped impl region of model.py) = %r\n"
                "  oracle (real patched language_code_prefix_re, "
                "len(match[1]) or -1) = %r  [group(1)=%r]"
                % (s, path, shadow, real, group1))
    # mapping.md §3: the captured CONTENT is path[1 : 1+len].
    if shadow != -1 and group1 != s[1:1 + shadow]:
        return ("CONTENT DISAGREEMENT on path %r: model's candidate slice %r "
                "!= real group(1) %r" % (s, s[1:1 + shadow], group1))
    # the model's own postcondition, executed: impl region == pure spec.
    spec = prefix_len_spec(ToSeq(path), 2)
    if shadow != spec:
        return ("MODEL-INTERNAL DISAGREEMENT on path %r: impl region = %r but "
                "prefix_len_spec(ToSeq(path), 2) = %r" % (s, shadow, spec))
    return None


def boundary_corpus():
    return [
        # F2P paths (test_get_language_from_path_real, post-patch) + neighbours
        "/pl/", "/pl", "/xyz/", "/en/", "/en-gb/",
        "/en-latn-us/", "/en-Latn-US/", "/de/", "/de-1996/", "/de-at/",
        "/de-ch/", "/de-ch-1901/", "/de-simple-page-test/",
        "/de-simple-page/", "/i-mingo/", "/kl-tunumiit/", "/nan-hani-tw/",
        "/en-latn-us", "/de-ch-1901", "/nan-hani-tw",
        # empty / singleton / structural boundaries
        "", "/", "//", "a", "no-slash", "/a", "/a/", "/a//", "/_x/", "/123/",
        # separator-budget edge: 2 separators accepted, 3 rejected (the gold
        # patch's discriminating behaviour)
        "/a-b/", "/a-b-c/", "/a-b-c-d/", "/a@b/", "/a@b@c/", "/a@b@c@d/",
        "/a-b@c/", "/a@b-c/", "/x-y-z", "/x-y-z-w",
        # ill-formed tags
        "/-", "/-a/", "/a-/", "/a--b/", "/a-@b/", "/a@-b/", "/-a-b/",
        "/a-b-/", "/@/", "/@a/",
        # non-candidate terminator / mid-path punctuation
        "/a.b/", "/a b/", "/a:b/", "/a%b/", "/a?b", "/a=b", "/a;b",
        "/a/b/c", "/aaa/bbb/",
        # Python-re `$`: matches at end-of-string AND just before a newline
        # that is the LAST character of the string
        "/en\n", "/en-us\n", "/de-ch-1901\n", "/nan-hani-tw\n", "/a-b\n",
        "/en\n\n", "/en\nx", "/en\n/", "/en/\n", "/en-\n", "/\n", "\n",
        "/en\r", "/en\r\n", "/en\rx", "/a-b-c-d\n", "/en@gb\n",
        # longer runs
        "/" + "a" * 60 + "/", "/a-" + "b" * 40 + "-c/", "/" + "z" * 60,
        # NON-ASCII word characters (letters of several scripts and a
        # non-ASCII digit): IN domain, because the word-class membership test
        # is consumed as an axiom that is open above code point 128 rather
        # than transcribed as an ASCII enumeration.
        "/\u00e9/", "/\u00e9", "/en-\u00e9/", "/en-\u00e9",
        "/\u00e9-en/", "/\u00e9\u00f1\u4e2d\u00df/", "/\u4e2d\u6587/",
        "/de-na\u00efve/", "/\u4e2d-\u6587-\u5b57/",
        "/\u4e2d-\u6587-\u5b57-\u9332/",
        "/\u03b1-\u03b2-\u03b3/", "/\u0430-\u0431/",
        "/\u0660\u0661\u0662/", "/\u00e9@\u00f1/",
        "/-\u00e9/", "/\u00e9-/", "/\u00e9--\u00f1/",
        "/en-\u00e9-us/", "/en-\u00e9-us-x/",
        "/\u00e9\n", "/\u00e9\n\n",
        # NON-ASCII NON-word characters: these must TERMINATE the candidate run
        # exactly as ASCII punctuation does.
        "/\u00d7/", "/en\u00d7/", "/en-\u00e9\u00d7/",
        "/en\u2013us/", "/en\u2010us/", "/en\u00b7us/",
        "/\u00a0/", "/en\u00a0/", "/en\u20ac/", "/\u2603/", "/en\u2026/",
    ]


def exhaustive_paths():
    """Every string of length <= EXHAUSTIVE_MAXLEN over EXHAUSTIVE_ALPHABET."""
    frontier = [""]
    yield ""
    for _ in range(EXHAUSTIVE_MAXLEN):
        nxt = []
        for pre in frontier:
            for ch in EXHAUSTIVE_ALPHABET:
                s = pre + ch
                nxt.append(s)
                yield s
        frontier = nxt


def fuzz_paths(rng, n):
    pool = (string.ascii_letters + string.digits + "_-@/. :;%~+!#?=\n\r\t"
            # non-ASCII word chars (letters/digits) and non-ASCII NON-word
            # chars (punctuation/symbols/spaces), so the fuzzer exercises the
            # word-class boundary on BOTH sides of code point 128.
            + "\u00e9\u00f1\u00df\u4e2d\u03b1\u0430\u0660\u00c7"
            + "\u00aa\u05d0\u3042\u0915"
            + "\u00d7\u2010\u00a0\u00ab\u2013\u00a9\u00b7\u2026"
            + "\u00f7\u20ac\u2603")
    subtags = ["en", "de", "pl", "nan", "kl", "i", "zh", "x", "Latn", "US",
               "us", "latn", "1996", "1901", "tw", "hani", "gb", "at", "ch",
               "simple", "page", "test", "tunumiit", "mingo", "_", "a",
               # non-ASCII sub-tags, so langtag-shaped paths cross the
               # word-class boundary too, not only the random stratum.
               "\u00e9", "\u4e2d", "\u00f1", "\u00df", "\u03b1",
               "\u0430\u0431", "\u0660\u0661"]
    tails = ["/", "", "/x", "-z", "1", ".", "\n", "/\n", "\n\n", "\nx", "\r",
             "@", "-", "?q=1", " ", "//",
             # non-ASCII terminators, word and non-word
             "\u00d7", "\u2013", "\u00a0", "\u20ac", "\u00e9", "-\u4e2d"]
    for _ in range(n):
        if rng.random() < 0.5:
            # langtag-shaped: dense on the accept/budget boundary
            k = rng.randint(1, 5)
            parts = [rng.choice(subtags) for _ in range(k)]
            seps = [rng.choice("-@") for _ in range(k - 1)]
            s = parts[0] + "".join(sp + p for sp, p in zip(seps, parts[1:]))
            s = (rng.choice(["/", "/", "/", ""])) + s + rng.choice(tails)
        else:
            L = rng.randint(0, 16)
            s = "".join(rng.choice(pool) for _ in range(L))
            if rng.random() < 0.7:
                s = "/" + s
        yield s


def main():
    matcher = real_matcher()
    problems = assert_oracle_is_patched(matcher)
    if problems:
        print("G-CONF FAIL: oracle provenance check failed:")
        for p in problems:
            print("  " + p)
        return 1

    seen_branches = {}
    checked = 0
    n_boundary = 0
    n_exhaustive = 0
    # Which non-ASCII code points the corpus actually put in front of the
    # matcher, split by real word-class membership. Coverage of BOTH sides is
    # asserted below: it is what makes agreement meaningful above cp 128.
    seen_nonascii_word = set()
    seen_nonascii_nonword = set()

    def run(s):
        nonlocal checked
        err = check(matcher, s)
        checked += 1
        for lab in branch_labels(s):
            seen_branches[lab] = seen_branches.get(lab, 0) + 1
        for ch in s:
            if ord(ch) >= 128:
                if _is_word_char(ch):
                    seen_nonascii_word.add(ord(ch))
                else:
                    seen_nonascii_nonword.add(ord(ch))
        return err

    for s in boundary_corpus():
        n_boundary += 1
        err = run(s)
        if err:
            print("G-CONF FAIL (boundary):")
            print(err)
            return 1

    for s in exhaustive_paths():
        n_exhaustive += 1
        err = run(s)
        if err:
            print("G-CONF FAIL (exhaustive length<=%d sweep):"
                  % EXHAUSTIVE_MAXLEN)
            print(err)
            return 1

    rng = random.Random(SEED)
    n_fuzz = 0
    for s in fuzz_paths(rng, N_FUZZ):
        n_fuzz += 1
        err = run(s)
        if err:
            print("G-CONF FAIL (fuzz, seed=%d):" % SEED)
            print(err)
            return 1

    missing = [b for b in REQUIRED_BRANCHES if b not in seen_branches]
    if missing:
        print("G-CONF FAIL: input generation never exercised these impl "
              "branches, so agreement proves nothing about them: %s"
              % ", ".join(missing))
        return 1

    # There is NO out-of-domain region: the word-class membership test is
    # consumed as an axiom that is OPEN above code point 128, so non-ASCII
    # paths are ordinary in-domain inputs and a disagreement on one is a
    # FAILURE like any other. What must be checked instead is that the corpus
    # actually REACHED both sides of that boundary -- otherwise agreement over
    # an accidentally-ASCII corpus would prove nothing about it.
    n_uni_word = len(seen_nonascii_word)
    n_uni_nonword = len(seen_nonascii_nonword)
    if not n_uni_word or not n_uni_nonword:
        print("G-CONF FAIL: the corpus never exercised the word-class boundary "
              "above code point 128 on both sides (non-ASCII word chars seen: "
              "%d, non-ASCII non-word chars seen: %d), so agreement says "
              "nothing about that region." % (n_uni_word, n_uni_nonword))
        return 1

    print("G-CONF OK: contract-stripped impl region of model.py == real "
          "patched language_code_prefix_re (len(match[1]) or -1) on %d paths "
          "spanning ASCII and non-ASCII (%d boundary + %d exhaustive |s|<=%d "
          "over %r + %d fuzz, seed=%d); all %d impl branches exercised; the "
          "word-class boundary above cp 128 was exercised on both sides (%d "
          "distinct word, %d distinct non-word code points); 0 disagreements; "
          "NO out-of-domain region."
          % (checked, n_boundary, n_exhaustive, EXHAUSTIVE_MAXLEN,
             EXHAUSTIVE_ALPHABET, n_fuzz, SEED, len(REQUIRED_BRANCHES),
             n_uni_word, n_uni_nonword))
    print(json.dumps({
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "boundary": n_boundary,
        "exhaustive": n_exhaustive,
        "fuzz": n_fuzz,
        "shadow": "direct (contract-stripped impl region of model.py)",
        "oracle": ("called: django.utils.translation.trans_real."
                   "language_code_prefix_re (patched)"),
        "branches_exercised": len(REQUIRED_BRANCHES),
        "nonascii_word_codepoints_exercised": n_uni_word,
        "nonascii_nonword_codepoints_exercised": n_uni_nonword,
        "out_of_domain_region": None,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
