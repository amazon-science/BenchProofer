#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14365 (nagini).

SHADOW  — the impl regions of `model.py`'s three contracted functions
          (`masked_field`, `reserved_data_token`, `command_line`) copied
          VERBATIM below with the contract statement lines
          (Requires/Ensures/Invariant/Assert) stripped; the model IS Python,
          so no transliteration.  The @Pure helpers (`up`, `upseq`, the
          `kw_*` keyword constants and the recognition predicates) copy over
          as plain functions.  `PSeq` becomes a small immutable tuple shim
          (`drop`/`take`/`+`/`==`/len/index); `ToSeq(list)` materializes a
          list as that shim.  Carrier: a text field/word is a List[int] of
          code points (mapping.md §2).

ORACLE  — the REAL patched repo functions (PYTHONPATH=/testbed; the gate
          applies the gold patch before this script runs), per mapping.md §1:
            * `astropy.io.ascii.qdp._line_type` — its `command` verdict
              oracles `command_line`, and its `data`/`new` verdict on
              single-field lines oracles `reserved_data_token` on the
              letter-bearing field sub-domain;
            * `astropy.io.ascii.qdp._get_tables_from_qdp_file` — the
              per-field missing-value decision inside its data loop oracles
              `masked_field`: a field of a parsed one-row table is observed
              masked iff the real test recognises it.
          Because the missing-value test is an inline per-field expression
          (not a standalone callable), `masked_field` is ALSO diffed on the
          full field domain against that expression evaluated verbatim, and
          `reserved_data_token` is likewise diffed against the reserved-token
          alternative of the patched line grammar evaluated verbatim — the
          same verdict-level references G-AX validates (mapping.md §3).

BRIDGE  — mapping.md §2's type abstraction, applied in the generator:
          str field <-> [ord(ch)] code points.  The whole-pipeline oracles
          run on the declared executable sub-domain: whitespace-free,
          comment-marker-free tokens (the regex tokenization and the
          whitespace/number structure are unchanged, case-irrelevant
          machinery abstracted out of the model; the token alphabet of the
          format is ASCII, plus the long-s letterform probe, the one further
          code point case-insensitive matching identifies with a keyword
          letter).  For `masked_field`'s table observation the
          field must additionally be a token the patched line grammar accepts
          (an input-domain fact of the data loop, which only ever sees fields
          of recognised data lines) — guarded by the real classifier itself.
          For `reserved_data_token`'s `_line_type` observation the field must
          bear a non-exponent letter (a field with no letter other than e/E
          can be an ordinary decimal, which is out of the modeled decision's
          scope; the filter is an input property, not the predicate under
          test).  `command_line`'s line is built as the two words plus the
          column numbers, single-space separated, matching the grammar's
          fixed word structure.

Inputs: boundary cases + exhaustive keyword-case grids + >=100000 fuzzed
Requires-satisfying inputs in total.  Pinned seed: 14365.
Exit 0 iff zero disagreements; on disagreement print the input and both
outputs and exit 1.  stdlib + numpy + the repo under test only.
"""
import random
import re
import sys
import warnings

warnings.simplefilter("ignore")

SEED = 14365


# ---------------------------------------------------------------------------
# PSeq / ToSeq shim: model.py's pure sequence carrier as a plain tuple wrapper.
# ---------------------------------------------------------------------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *elems):
        self._t = tuple(elems)

    @classmethod
    def _of(cls, iterable):
        s = cls()
        s._t = tuple(iterable)
        return s

    def drop(self, n):
        return PSeq._of(self._t[n:])

    def take(self, n):
        return PSeq._of(self._t[:n])

    def __add__(self, other):
        return PSeq._of(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._of(lst)


# ---------------------------------------------------------------------------
# model.py pure region, copied as plain functions (@Pure/Ensures stripped).
# ---------------------------------------------------------------------------

def up(c):
    if 97 <= c and c <= 122:
        return c - 32
    if c == 383:
        return 83
    return c


def upseq(s):
    if len(s) == 0:
        return s
    return PSeq(up(s[0])) + upseq(s.drop(1))


def kw_NO():
    # "NO"
    return PSeq(78, 79)


def kw_READ():
    # "READ"
    return PSeq(82, 69, 65, 68)


def kw_SERR():
    # "SERR"
    return PSeq(83, 69, 82, 82)


def kw_TERR():
    # "TERR"
    return PSeq(84, 69, 82, 82)


def kw_NAN():
    # "NAN"
    return PSeq(78, 65, 78)


def is_masked_field(field):
    return upseq(field) == kw_NO()


def is_reserved_data_token(field):
    return (upseq(field) == kw_NO()
            or upseq(field) == kw_NAN()
            or (len(field) >= 1
                and (field[0] == 43 or field[0] == 45)   # '+' or '-'
                and upseq(field.drop(1)) == kw_NAN()))


def is_command_tokens(tok0, tok1, ncols):
    return (upseq(tok0) == kw_READ()
            and (upseq(tok1) == kw_SERR() or upseq(tok1) == kw_TERR())
            and ncols >= 1)


# ---------------------------------------------------------------------------
# model.py impl regions, VERBATIM with contract statement lines
# (Requires/Ensures/Invariant/Assert) stripped.
# ---------------------------------------------------------------------------

def masked_field(field):
    folded = []  # type: list
    i = len(field)
    while i > 0:
        c = field[i - 1]
        if 97 <= c and c <= 122:
            folded = [c - 32] + folded
        elif c == 383:
            folded = [83] + folded
        else:
            folded = [c] + folded
        i = i - 1
    return ToSeq(folded) == kw_NO()


def reserved_data_token(field):
    folded = []  # type: list
    i = len(field)
    while i > 0:
        c = field[i - 1]
        if 97 <= c and c <= 122:
            folded = [c - 32] + folded
        elif c == 383:
            folded = [83] + folded
        else:
            folded = [c] + folded
        i = i - 1
    is_no = ToSeq(folded) == kw_NO()
    is_nan = ToSeq(folded) == kw_NAN()
    is_signed_nan = (len(field) >= 1
                     and (field[0] == 43 or field[0] == 45)
                     and ToSeq(folded).drop(1) == kw_NAN())
    return is_no or is_nan or is_signed_nan


def command_line(tok0, tok1, ncols):
    f0 = []  # type: list
    i = len(tok0)
    while i > 0:
        c = tok0[i - 1]
        if 97 <= c and c <= 122:
            f0 = [c - 32] + f0
        elif c == 383:
            f0 = [83] + f0
        else:
            f0 = [c] + f0
        i = i - 1

    f1 = []  # type: list
    j = len(tok1)
    while j > 0:
        d = tok1[j - 1]
        if 97 <= d and d <= 122:
            f1 = [d - 32] + f1
        elif d == 383:
            f1 = [83] + f1
        else:
            f1 = [d] + f1
        j = j - 1

    is_read = ToSeq(f0) == kw_READ()
    is_err = ToSeq(f1) == kw_SERR() or ToSeq(f1) == kw_TERR()
    return is_read and is_err and ncols >= 1


# ---------------------------------------------------------------------------
# Oracle plumbing: the real patched repo functions.
# ---------------------------------------------------------------------------

def cps(s):
    """Bridge: str field/word -> List[int] code points (mapping.md §2)."""
    return [ord(ch) for ch in s]


def _classify_or_none(line_type, line):
    try:
        return line_type(line)
    except ValueError:
        return None


def _require_post_patch(line_type):
    """The gate applies the gold patch before running this script; refuse to
    diff against a pre-patch classifier (every mixed-case keyword would then
    disagree for a reason that is an environment error, not a shadow bug)."""
    if _classify_or_none(line_type, "read serr 1") != "command" or \
            _classify_or_none(line_type, "no") != "data,1":
        print("G-CONF ERROR: imported classifier behaves pre-patch; the "
              "harness must apply patch.diff before this script runs")
        sys.exit(2)


# The reserved-token alternative and the missing-value expression of the
# patched sources, evaluated verbatim (the same verdict-level references
# mapping.md §3.2/§3.4 bind the model to); used for the full-field-domain
# diffs where the inline site has no standalone callable.
_reserved_token_re = re.compile(r"(NO|[-+]?nan)", re.IGNORECASE)


def real_masked_expr(field):
    return field.upper() == "NO"


def real_reserved_token_expr(field):
    return _reserved_token_re.fullmatch(field) is not None


class Differ:
    def __init__(self):
        self.checked = 0
        self.disagreements = []

    def diff(self, what, inp, shadow_v, real_v):
        self.checked += 1
        if shadow_v != real_v:
            self.disagreements.append((what, inp, shadow_v, real_v))
        return len(self.disagreements) < 10


def main():
    import numpy as np
    from astropy.io.ascii.qdp import _get_tables_from_qdp_file, _line_type

    _require_post_patch(_line_type)
    rng = random.Random(SEED)
    d = Differ()

    def real_is_command(line):
        return _classify_or_none(_line_type, line) == "command"

    def real_data_or_new(field):
        v = _classify_or_none(_line_type, field)
        return v is not None and (v.startswith("data") or v == "new")

    def real_masked_cell(field):
        """Whole-pipeline observation of the data loop's per-field
        missing-value decision: parse a one-row two-column table whose first
        field is the candidate and observe whether that cell is masked."""
        tables = _get_tables_from_qdp_file(field + " 1\n")
        cell = tables[0].columns[0][0]
        return bool(np.ma.is_masked(cell))

    ok = True

    # ------------------------------------------------------------------
    # 1. masked_field — full field domain vs the patched missing-value
    #    expression, evaluated verbatim (17 boundary + 30000 fuzz).
    # ------------------------------------------------------------------
    mask_boundary = ["NO", "no", "No", "nO", "N0", "NOO", "ON", "n", "o", "",
                     "0.5", "nan", "NaN", "1", "-1.4e-5", "+NO", "O",
                     "ſ", "ſO", "Nſ"]
    mask_alphabet = list("NOno0.5-+eEnaAN")
    mask_fields = list(mask_boundary)
    for _ in range(30000):
        n = rng.randint(0, 6)
        mask_fields.append("".join(rng.choice(mask_alphabet) for _ in range(n)))
    for f in mask_fields:
        ok = d.diff("masked_field(expr)", f, masked_field(cps(f)),
                    real_masked_expr(f))
        if not ok:
            break

    # ------------------------------------------------------------------
    # 2. masked_field — whole-pipeline table observation on the executable
    #    sub-domain (fields the patched line grammar accepts as one data
    #    token; guarded by the real classifier — an input-domain fact of the
    #    data loop, which only ever sees fields of recognised lines).
    # ------------------------------------------------------------------
    if ok:
        pipe_boundary = ["NO", "no", "No", "nO", "nan", "NaN", "nAn", "+nan",
                         "-nan", "+NAN", "1", "2", "0.5", "-1.4e-5", "1e3",
                         ".5", "+.5", "-7"]
        pipe_pool = []
        while len(pipe_pool) < 4000:
            n = rng.randint(1, 6)
            f = "".join(rng.choice(mask_alphabet) for _ in range(n))
            if any(ch.isspace() for ch in f):
                continue
            pipe_pool.append(f)
        for f in pipe_boundary + pipe_pool:
            if _classify_or_none(_line_type, f + " 1") != "data,2":
                continue  # not a single accepted data token: loop never sees it
            ok = d.diff("masked_field(pipeline)", f, masked_field(cps(f)),
                        real_masked_cell(f))
            if not ok:
                break

    # ------------------------------------------------------------------
    # 3. command_line — vs the real _line_type command verdict.  Boundary:
    #    the full keyword-case grid x column tails; then 35000 fuzz lines.
    #    Bridge sub-domain: non-empty whitespace/comment-marker-free words,
    #    single-space separated (the grammar's fixed word structure).
    # ------------------------------------------------------------------
    if ok:
        read_words = ["READ", "read", "Read", "rEaD", "READING", "REA",
                      "rad", "no", "R", "DAER"]
        err_words = ["SERR", "serr", "Serr", "sErR", "TERR", "terr", "Terr",
                     "tErR", "ERR", "XERR", "SER", "serrr", "no", "S",
                     "ſERR", "ſerr", "SEſR", "ſ"]
        num_lists = [[], [1], [1, 2], [3, 1, 4], [42], [1, 2, 3, 4, 5], [0]]
        cases = [(w0, w1, nums) for w0 in read_words for w1 in err_words
                 for nums in num_lists]
        word_alphabet = list("READSTErdstnoraX")
        for _ in range(35000):
            w0 = "".join(rng.choice(word_alphabet)
                         for _ in range(rng.randint(1, 6)))
            w1 = "".join(rng.choice(word_alphabet)
                         for _ in range(rng.randint(1, 6)))
            nums = [rng.randint(0, 99) for _ in range(rng.randint(0, 4))]
            cases.append((w0, w1, nums))
        for w0, w1, nums in cases:
            line = " ".join([w0, w1] + [str(n) for n in nums])
            ok = d.diff("command_line", line,
                        command_line(cps(w0), cps(w1), len(nums)),
                        real_is_command(line))
            if not ok:
                break

    # ------------------------------------------------------------------
    # 4. reserved_data_token — (a) full field domain vs the patched
    #    reserved-token alternative evaluated verbatim; (b) the real
    #    _line_type data/new verdict on single-field lines, restricted to
    #    letter-bearing fields (a field whose only letters are the exponent
    #    markers e/E can be an ordinary decimal token, which is outside the
    #    modeled decision — an input-domain filter, not the predicate).
    #    34 boundary + 30000 fuzz fields, both oracles per field.
    # ------------------------------------------------------------------
    if ok:
        token_boundary = ["NO", "no", "No", "nO", "NAN", "nan", "NaN", "nAn",
                          "+nan", "-nan", "+NAN", "-NAN", "+NaN", "-nAn",
                          "N0", "NOO", "ON", "nann", "na", "n", "o", "naan",
                          "+no", "-no", "++nan", "1", "0.5", "1e3", "1E3",
                          "-1.4e-5", ".5", "+.5", "", "a",
                          "ſ", "ſO", "naſ"]
        token_alphabet = list("NOnaANo+-01.eE")
        token_fields = list(token_boundary)
        for _ in range(30000):
            n = rng.randint(0, 6)
            token_fields.append("".join(rng.choice(token_alphabet)
                                        for _ in range(n)))
        for f in token_fields:
            ok = d.diff("reserved_data_token(expr)", f,
                        reserved_data_token(cps(f)),
                        real_reserved_token_expr(f))
            if not ok:
                break
            if not f or any(ch.isspace() for ch in f):
                continue
            if not any(("a" <= ch.lower() <= "z") and ch not in "eE"
                       for ch in f):
                continue  # no non-exponent letter: possibly a plain decimal
            ok = d.diff("reserved_data_token(_line_type)", f,
                        reserved_data_token(cps(f)),
                        real_data_or_new(f))
            if not ok:
                break

    # ------------------------------------------------------------------
    # Verdict.
    # ------------------------------------------------------------------
    if d.disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d comparisons (seed=%d):"
              % (len(d.disagreements), d.checked, SEED))
        for what, inp, shadow_v, real_v in d.disagreements:
            print("  [%s] input=%r shadow=%r real=%r"
                  % (what, inp, shadow_v, real_v))
        return 1
    print("G-CONF OK: model.py impl shadow (masked_field, "
          "reserved_data_token, command_line) agrees with the real patched "
          "recognition behaviour on %d comparisons (seed=%d), "
          "0 disagreements." % (d.checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
