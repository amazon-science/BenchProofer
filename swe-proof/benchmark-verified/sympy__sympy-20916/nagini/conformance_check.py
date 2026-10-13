#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""G-CONF differential conformance check for sympy__sympy-20916 (nagini).

Refutes (never proves) the refinement leg no other gate covers: does the MODEL
in model.py agree with the REAL gold-patched repository code it claims to model?
G-VERIFY says the impl meets the spec; G-PBT says no wrong impl meets it; neither
one looks at the repository. This script does.

SHADOW
  The `# impl-start` / `# impl-end` region of model.py, copied VERBATIM below
  with only the contract calls deleted (`Requires`, `Ensures`, `Invariant`,
  `Assert`, `Acc`, `MustTerminate`) and the `# invariants-start/-end` markers
  removed. Nothing is renamed, reordered, restructured or "simplified": the
  three loops (leading-letter scan, all-digit tail scan, result-building copy)
  and the `k`/`j`/`bad`/`matched`/`upper`/`i` locals are exactly as written, so
  what is tested is model.py's code and not a paraphrase of it.

  The four `@Pure` helpers of the `# pure-start` region — `num_leading_letters`,
  `all_digits`, `splits`, `split_point` — are copied the same way, minus their
  contracts. After contract-stripping the impl region no longer *calls* them
  (every use sat inside an `Assert`/`Invariant`), so they are exercised
  deliberately instead: see STRIPPED ASSERTS below.

  Nagini carriers: `PSeq[int]` is realized by the immutable-tuple shim below
  (`len` / `[]` / `==` / `take` / `drop` / `+`, the operations these regions
  use) and `ToSeq(list)` materializes one — the same shape as the other nagini
  bundles in this corpus.

  `is_letter` / `is_digit` are `@Pure @ContractOnly`: they have no body to copy.
  Per mapping.md §1 and §3.1 they axiomatize the two per-code-point character
  classes of the patched module pattern — `[^\W\d_]` and `\d`, evaluated by the
  stdlib `re` engine under `re.U`. The shims below therefore CALL the real `re`
  engine, and the two class sources are not re-typed by hand: they are EXTRACTED
  at run time from the group bodies of the real patched module object's
  `_name_with_digits_p.pattern` (see `_derive_classes`). So the axioms are
  exercised against the shipped artifact rather than assumed, and a patch that
  changed the classes would change the shadow's classifiers too.

ORACLE — the real patched repo code, CALLED, never reimplemented
  Two levels of the same patched module, both imported from
  `sympy/printing/conventions.py` at base_commit 82298df6a51 with the gold patch
  applied by the gate (`apply_gold=True`, `PYTHONPATH=/testbed`):

  (1) `sympy.printing.conventions._name_with_digits_p` (`conventions.py:10`, the
      line the gold patch rewrites) driven as `.match(name)` / `.groups()`. This
      is the exact boundary the model models: mapping.md §2 binds
      `match is not None` ↔ `splits(ToSeq(name))`, `m.group(1)` ↔
      `take(split_point)`, `m.group(2)` ↔ `drop(split_point)`. The model's input
      IS the `name` local that the pattern is applied to, so feeding the pattern
      directly compares the two sides on precisely the modeled domain.
  (2) `sympy.printing.conventions.split_super_sub` (`conventions.py:13`, the
      consumer of the exception block at `conventions.py:63-68`) driven
      end-to-end on separator-free names, where mapping.md §1's unchanged
      parsing loop is the identity (`name = text`, `supers = []`) so the only
      observable is the trailing-digit decomposition this bundle models. This
      pins that the peeled run really does land at `subs[0]` (refinement A7),
      i.e. that the modeled block is consumed the way refinement.md claims.

  The script hard-errors (exit 2) if the import fails or if the loaded
  `_name_with_digits_p.pattern` is not the post-patch pattern, so a patch-apply
  failure can never be mistaken for agreement.

TYPE BRIDGE (mapping.md §2, inverted)
  Model side: `name: List[int]`, a list of Unicode code points, carried into the
  specification as `PSeq[int]` via `ToSeq`. Repo side: a `str`. The bijection is
  `[ord(ch) for ch in s]` / `"".join(chr(c) for c in cps)`, under which `len`,
  index, and the slices `s[:p]` / `s[p:]` correspond to `len`, `[]`, and
  `take(p)` / `drop(p)`. Generation happens on the `str` side and is mapped into
  the model carrier, so every generated input is a genuine code-point list and
  therefore satisfies the model's `Requires` (which is only
  `Acc(list_pred(name), 1/2)` + `MustTerminate`, i.e. any int list, read-only).

INPUT DOMAIN
  The Requires-satisfying domain is infinite (any code-point list), so this is
  boundary cases first, then seeded fuzz. The domain is NOT narrowed to make the
  check pass: in particular names containing `\n` are generated, because the
  model's `Requires` admits them, `split_super_sub` really can be reached with
  them (`Symbol("w1\n")`), and `\n` is where Python's `$` anchor stops being a
  pure end-of-string test. Excluding it would produce a green G-CONF that
  certifies nothing about the very code point that discriminates the two sides.

  Boundary set (`_boundary_names`) covers: the empty name; singletons; every
  FAIL_TO_PASS name of `test_super_sub` (`w1`, `w𝟙`, `w11`, `w𝟙𝟙`, `w𝟙2𝟙`, `ω1`,
  `ω11`, and the pre-existing `alpha_11` bases); each branch of the impl region
  taken at least once — the letter scan exiting by `k == n` and by a non-letter;
  the digit scan exiting with `bad` true and false; `matched` true and false;
  `k >= 1 and k < m` false via `k == 0` and via `k == m`; the copy loop entered
  and not entered (`upper == 0`); the terminating line feed both set aside
  (`m < n`) and absent (`m == n`) — plus the `$`-anchor probes (`w1\n`,
  `w1\n\n`, `w1\r`, `w1\r\n`, `w\n1`) and non-word/underscore/caret separators.
  Branch coverage is not asserted by eye: the shadow records which branches it
  took and `main` fails if any of the ten tracked branches was never exercised.

  Fuzz: 100_000 names over an alphabet of multi-script letters (Latin, Greek,
  Cyrillic, Latin-1), multi-script decimal digits (ASCII, astral mathematical,
  Arabic-Indic, Devanagari), word-but-not-decimal code points (`²`, `Ⅰ`, `①` —
  letters to `[^\W\d_]` but not digits to `\d`), and non-word code points
  (`_`, `^`, ` `, `-`, `\n`, `\r`). Lengths 0..7. Pinned seed: 20916, recorded
  in mapping.md under `## G-CONF`.

STRIPPED ASSERTS become checked observations
  model.py's impl region ties itself to the deep pure model through `Assert`
  calls, which are contracts and are stripped here. Rather than let the copied
  `@Pure` folds go dead, every input additionally checks the two facts those
  asserts carried, as observations:
    * `matched == splits(ToSeq(name))` — checked in the equivalent observable
      form `result == take(split_point) if splits else name`, which is exactly
      the postcondition pair of the spec region, so the pure folds are diffed
      against the impl region on every input as well;
    * the peeled remainder `drop(split_point)` is non-empty and all digits
      whenever `splits`.
  A disagreement in either is reported like any other.

Exit 0 iff zero disagreements. On a disagreement the input and both sides'
outputs are printed and the exit code is 1. The final stdout line is a JSON
object (the gate reads it as a structured report). stdlib + the repo package
under change only.
"""
from typing import List
import json
import random
import re
import sys

SEED = 20916
N_FUZZ = 100_000

MAX_REPORTED = 8


# --- oracle: the REAL patched repo module ------------------------------------

POST_PATCH_PATTERN = r'^([^\W\d_]+)(\d+)$'


def _load_oracle():
    """Import the real patched callees. mapping.md §1: the module pattern
    `_name_with_digits_p` (`sympy/printing/conventions.py:10`, the gold-patched
    line) and its consumer `split_super_sub` (`conventions.py:13`)."""
    from sympy.printing import conventions
    pat = conventions._name_with_digits_p
    if pat.pattern != POST_PATCH_PATTERN:
        raise RuntimeError(
            "loaded _name_with_digits_p is not the post-patch pattern: %r "
            "(expected %r) -- gold patch not applied?"
            % (pat.pattern, POST_PATCH_PATTERN))
    return pat, conventions.split_super_sub


def _derive_classes(pattern_src):
    r"""Extract the two per-code-point character classes the `@ContractOnly`
    axioms `is_letter` / `is_digit` stand for (mapping.md §3.1) OUT OF the real
    patched pattern's source, so the shadow's classifiers are the shipped
    artifact's own classes rather than a hand-typed copy of them.

    `^([^\W\d_]+)(\d+)$` -> group bodies `[^\W\d_]` and `\d`."""
    m = re.match(r'^\^\((.+)\+\)\((.+)\+\)\$$', pattern_src)
    if m is None:
        raise RuntimeError("cannot extract the two group classes from the real "
                           "pattern %r" % pattern_src)
    letter_cls, digit_cls = m.group(1), m.group(2)
    return re.compile(letter_cls, re.U), re.compile(digit_cls, re.U)


# --- Nagini carrier shim: PSeq[int] / ToSeq ----------------------------------

class PSeq(tuple):
    """Immutable Viper sequence: `len` / `[]` / `==` / `take` / `drop` / `+`."""

    def take(self, n):
        return PSeq(tuple.__getitem__(self, slice(None, n)))

    def drop(self, n):
        return PSeq(tuple.__getitem__(self, slice(n, None)))

    def __add__(self, other):
        return PSeq(tuple.__add__(self, tuple(other)))


def ToSeq(lst):
    return PSeq(lst)


# --- @Pure @ContractOnly axioms: the REAL `re` classes, called ---------------

_LETTER_RE = None   # set by main() from the real patched pattern
_DIGIT_RE = None
_LETTER_CACHE = {}
_DIGIT_CACHE = {}


def is_letter(c: int) -> bool:
    r"""`@ContractOnly` in model.py; here the real callee it axiomatizes: the
    class `[^\W\d_]` of the patched pattern, evaluated by the stdlib `re`
    engine under `re.U` (mapping.md §3.1)."""
    v = _LETTER_CACHE.get(c)
    if v is None:
        v = _LETTER_RE.match(chr(c)) is not None
        _LETTER_CACHE[c] = v
    return v


def is_digit(c: int) -> bool:
    r"""`@ContractOnly` in model.py; here the real callee it axiomatizes: the
    class `\d` of the patched pattern, under `re.U` (mapping.md §3.1)."""
    v = _DIGIT_CACHE.get(c)
    if v is None:
        v = _DIGIT_RE.match(chr(c)) is not None
        _DIGIT_CACHE[c] = v
    return v


# --- model.py `# pure-start` region, verbatim, contracts stripped ------------

def core_len(s: PSeq) -> int:
    """Length of the name PROPER of `s`: `s` with a single terminating line-feed
    code point (10) set aside."""
    if len(s) >= 1 and s[len(s) - 1] == 10:
        return len(s) - 1
    return len(s)


def num_leading_letters(s: PSeq) -> int:
    """Length of the maximal prefix of `s` whose every code point is a letter.
    Front-recursive so a single unfold is available per proof step."""
    if len(s) == 0:
        return 0
    if not is_letter(s[0]):
        return 0
    return 1 + num_leading_letters(s.drop(1))


def all_digits(s: PSeq) -> bool:
    """True iff every code point of `s` is a decimal digit. Front-recursive."""
    if len(s) == 0:
        return True
    if not is_digit(s[0]):
        # s[0] is a non-digit at index 0: witnesses the Forall failing.
        return False
    return all_digits(s.drop(1))


def splits(s: PSeq) -> bool:
    """The trailing-digit exception applies to `s` iff the name proper
    `s.take(core_len(s))` is a non-empty run of letters immediately followed by
    a non-empty run of decimal digits, with nothing else."""
    return (num_leading_letters(s) >= 1
            and num_leading_letters(s) < core_len(s)
            and all_digits(s.take(core_len(s))
                           .drop(num_leading_letters(s))))


def split_point(s: PSeq) -> int:
    """The code-point index at which `s` is split when the exception applies."""
    return num_leading_letters(s)


def digit_run(s: PSeq) -> PSeq:
    """The peeled trailing digit run — the part of the name PROPER from the
    split point onward, so the set-aside terminating line feed is not in it."""
    return s.take(core_len(s)).drop(split_point(s))


# --- model.py `# impl-start` .. `# impl-end` region, verbatim ----------------
# Contract calls (Requires / Ensures / Invariant / Assert / Acc / MustTerminate)
# and the invariants-start/-end markers are the only deletions. BRANCHES records
# which arms were taken so main() can prove the fuzz reached all of them.

BRANCHES = {
    "letter_scan_exit_end": 0,      # leading-letter loop exited by k == n
    "letter_scan_exit_nonletter": 0,  # ... exited on a non-letter
    "digit_scan_bad": 0,            # tail scan hit a non-digit (bad = True)
    "digit_scan_clean": 0,          # tail scan ran to m (bad = False)
    "matched_true": 0,              # matched -> upper = k
    "matched_false": 0,             # not matched -> upper = n
    "copy_loop_entered": 0,         # result-building loop body ran
    "copy_loop_skipped": 0,         # ... upper == 0, body never ran
    "lf_set_aside": 0,              # one terminating line feed set aside (m < n)
    "lf_absent": 0,                 # ... no terminating line feed (m == n)
}


def split_trailing_digits(name: List[int]) -> List[int]:
    n = len(name)
    # The name PROPER ends at `m`: a single terminating line-feed code point
    # (10) is set aside, so m == core_len(name).
    m = n
    if n >= 1 and name[n - 1] == 10:
        m = n - 1
    BRANCHES["lf_set_aside" if m < n else "lf_absent"] += 1
    # Count the leading run of letters.
    k = 0
    while k < n and is_letter(name[k]):
        k = k + 1
    BRANCHES["letter_scan_exit_end" if k == n
             else "letter_scan_exit_nonletter"] += 1
    # Decide whether the name proper's remainder [k, m) is a non-empty
    # all-digit run.
    matched = False
    if k >= 1 and k < m:
        j = k
        bad = False
        while j < m and not bad:
            if not is_digit(name[j]):
                bad = True
            else:
                j = j + 1
        BRANCHES["digit_scan_bad" if bad else "digit_scan_clean"] += 1
        matched = not bad
    # Build the result list: the leading letter run when matched, else the
    # whole name unchanged.
    if matched:
        upper = k
    else:
        upper = n
    BRANCHES["matched_true" if matched else "matched_false"] += 1
    BRANCHES["copy_loop_entered" if upper > 0 else "copy_loop_skipped"] += 1
    result = []  # type: List[int]
    i = 0
    while i < upper:
        result = result + [name[i]]
        i = i + 1
    return result


# --- type bridge (mapping.md §2, inverted) ----------------------------------

def to_cps(s):
    """repo `str` -> model carrier `List[int]` of Unicode code points."""
    return [ord(ch) for ch in s]


def from_cps(cps):
    """model carrier `List[int]` -> repo `str`."""
    return "".join(chr(c) for c in cps)


# --- the differential step ---------------------------------------------------

def check_one(text, pattern, split_super_sub):
    """Return a disagreement tuple, or None. Compares:
      (a) the shadow's bare name vs the real patched pattern's group 1 / the
          unchanged name, per mapping.md §2;
      (b) the stripped Asserts, as observations, against the copied @Pure folds;
      (c) on separator-free names, the real `split_super_sub` end-to-end."""
    cps = to_cps(text)
    shadow_bare = from_cps(split_trailing_digits(cps))

    m = pattern.match(text)
    if m is None:
        oracle_bare, oracle_sub = text, None
    else:
        oracle_bare, oracle_sub = m.group(1), m.group(2)
    if shadow_bare != oracle_bare:
        return ("bare-name", text, shadow_bare, (oracle_bare, oracle_sub))

    # (b) stripped Asserts of the impl region, as checked observations: the
    # deep pure model must give the impl region's own result.
    s = ToSeq(cps)
    if splits(s):
        want = from_cps(list(s.take(split_point(s))))
        rest = digit_run(s)
        if not (len(rest) >= 1 and all_digits(rest)):
            return ("pure-peeled-run", text, shadow_bare,
                    (oracle_bare, oracle_sub))
        # the peeled run IS the real pattern's group 2 (mapping.md §2)
        if from_cps(list(rest)) != oracle_sub:
            return ("pure-peeled-run-value", text, from_cps(list(rest)),
                    oracle_sub)
    else:
        want = text
    if shadow_bare != want:
        return ("pure-vs-impl", text, shadow_bare, want)
    # the pure model's own match decision vs the real pattern
    if splits(s) != (m is not None):
        return ("pure-match-decision", text, splits(s), m is not None)

    # (c) end-to-end: on separator-free names the unchanged parsing loop is the
    # identity, so split_super_sub's observable is exactly this split.
    if "_" not in text and "^" not in text and text != "":
        o_name, o_supers, o_subs = split_super_sub(text)
        want_subs = [] if oracle_sub is None else [oracle_sub]
        if o_supers != [] or o_name != shadow_bare or o_subs != want_subs:
            return ("split_super_sub", text, (shadow_bare, want_subs),
                    (o_name, o_supers, o_subs))
    return None


# --- inputs ------------------------------------------------------------------

def _boundary_names():
    """Boundary cases: empty, singletons, every FAIL_TO_PASS name, each impl
    branch, and the `$`-anchor probes. Nothing here is filtered out."""
    return [
        # empty / singletons
        "", "w", "1", "ω", "\U0001D7D9", "_", "^", "\n",
        # FAIL_TO_PASS names of test_super_sub (the bases feeding the block)
        "w1", "w\U0001D7D9", "w11", "w\U0001D7D9\U0001D7D9",
        "w\U0001D7D92\U0001D7D9", "ω1", "ω11", "ω\U0001D7D9",
        "ω\U0001D7D92", "alpha", "alpha11", "x",
        # letter scan exits by k == n (all letters) / on a non-letter
        "abc", "abc_", "abc1", "1abc", "_abc",
        # digit scan clean / bad
        "w12", "w1a", "w1_", "w1 ", "a1b2",
        # k == 0 and k == n make the k>=1 and k<n guard false
        "12", "\U0001D7D9\U0001D7D9", "abcd",
        # multi-script letters and digits
        "аб123", "г1", "é1", "Βητα01", "x١", "x२", "ω\U0001D7D9\U0001D7D9",
        # word-but-not-decimal code points (letters to [^\W\d_], not \d)
        "x²", "x²1", "Ⅰ1", "①1", "x①",
        # `$` anchor: Python's non-MULTILINE `$` also matches just before ONE
        # final newline. These are Requires-satisfying names, so they are IN.
        "w1\n", "ω1\n", "abc123\n", "w\U0001D7D9\n",
        "w1\n\n", "w1\r", "w1\r\n", "w\n1", "w\n", "1\n",
        # separators (pattern-level only; the end-to-end leg skips these)
        "w_1", "_1", "w^1", "x_1^a",
    ]


def _fuzz_alphabet():
    return (list("abcXYZw")                       # ASCII letters
            + list("019")                         # ASCII digits
            + ["ω", "α", "Β", "а", "б", "é"]       # Greek/Cyrillic/Latin-1
            + ["\U0001D7D9", "\U0001D7DA", "١", "٢", "२"]   # non-ASCII digits
            + ["²", "Ⅰ", "①"]                     # word but not \d
            + ["_", "^", " ", "-", "\n", "\r"])   # non-word, incl. the `$` probe


def main():
    global _LETTER_RE, _DIGIT_RE
    try:
        pattern, split_super_sub = _load_oracle()
        _LETTER_RE, _DIGIT_RE = _derive_classes(pattern.pattern)
    except Exception as exc:                      # pragma: no cover
        print("G-CONF ERROR: %r" % (exc,))
        print(json.dumps({"status": "error", "reason": repr(exc)}))
        return 2

    disagreements = []
    checked = 0

    for text in _boundary_names():
        checked += 1
        d = check_one(text, pattern, split_super_sub)
        if d is not None and len(disagreements) < MAX_REPORTED:
            disagreements.append(("boundary",) + d)

    rng = random.Random(SEED)
    alphabet = _fuzz_alphabet()
    for _ in range(N_FUZZ):
        checked += 1
        text = "".join(rng.choice(alphabet)
                       for _ in range(rng.randint(0, 7)))
        d = check_one(text, pattern, split_super_sub)
        if d is not None and len(disagreements) < MAX_REPORTED:
            disagreements.append(("fuzz",) + d)

    unexercised = sorted(b for b, c in BRANCHES.items() if c == 0)

    if disagreements:
        print("G-CONF FAIL: model.py's impl region disagrees with the real "
              "patched %s on %d input(s) (of %d checked, seed=%d):"
              % ("sympy.printing.conventions._name_with_digits_p",
                 len(disagreements), checked, SEED))
        for kind, why, text, shadow_out, oracle_out in disagreements:
            print("  [%s/%s] input=%r shadow=%r oracle=%r"
                  % (kind, why, text, shadow_out, oracle_out))
        print(json.dumps({
            "status": "fail",
            "checked": checked,
            "seed": SEED,
            "disagreements": len(disagreements),
            "first": {"input": disagreements[0][2],
                      "why": disagreements[0][1],
                      "shadow": repr(disagreements[0][3]),
                      "oracle": repr(disagreements[0][4])},
            "branches": BRANCHES,
        }))
        return 1

    if unexercised:
        print("G-CONF FAIL: %d impl branch(es) never exercised: %s"
              % (len(unexercised), ", ".join(unexercised)))
        print(json.dumps({"status": "fail", "checked": checked, "seed": SEED,
                          "unexercised_branches": unexercised}))
        return 1

    print("G-CONF OK: model.py impl region (verbatim, contracts stripped) == "
          "the real patched _name_with_digits_p / split_super_sub on %d "
          "Requires-satisfying names (%d boundary + %d fuzz, seed=%d); all %d "
          "impl branches exercised; 0 disagreements."
          % (checked, len(_boundary_names()), N_FUZZ, SEED, len(BRANCHES)))
    print(json.dumps({"status": "pass", "checked": checked, "seed": SEED,
                      "disagreements": 0, "branches": BRANCHES}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
