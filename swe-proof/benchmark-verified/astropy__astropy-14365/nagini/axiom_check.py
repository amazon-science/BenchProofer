#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14365.

This bundle consumes NO `@ContractOnly` axiom (the `axioms` region of model.py
is empty). The changed behaviour is modelled DEEPLY as an ASCII case fold
(`up`/`upseq`) plus recognition predicates over the folded text
(`is_masked_field`, `is_command_tokens`, `is_reserved_data_token`). They are
A-references: G-AX validates each deep model against the REAL callee the gold
patch makes the parser use.

  (A-reference 1) CASE FOLD.  The model's per-code-point `up` / sequence fold
      `upseq` must equal the real ASCII upper-casing the patch introduces in the
      missing-value test (the new `v.upper()`). We validate `upseq(s) ==
      str.upper(s)` on the ASCII-letter/keyword domain the recognition uses
      (the QDP token alphabet is ASCII), over boundary + fuzz.

  (A-reference 2) MISSING-VALUE RECOGNITION (masking loop).  The model claims a
      field is masked iff `upseq(field) == "NO"` (case-insensitive). The real
      patched test is `v.upper() == "NO"`. We assert the model verdict equals
      the real `v.upper() == "NO"` on every fuzzed field.

  (A-reference 3) COMMAND RECOGNITION (the `command` regex branch).  The model
      claims a line is a command iff (case folded) its first word is `READ`, its
      second is `SERR`/`TERR`, and a column number follows. The real callee is
      the patched `_line_type`, whose command regex `READ [TS]ERR(\\s+[0-9]+)+`
      is now compiled with `re.IGNORECASE`. We run the REAL `_line_type` on
      case-variant command lines (and on near-miss non-commands) and assert its
      `"command"`/non-command verdict equals the model's `is_command_tokens`.

  (A-reference 4) RESERVED-DATA-TOKEN RECOGNITION (the `data`/`new` regex
      branches).  The SAME `re.IGNORECASE` edit also changes the `data` and
      `new` branches: a reserved-word data token — the missing-value word `NO`
      or the not-a-number word `nan` (optionally signed) — must now be
      recognised case-insensitively (the regex sub-pattern `(NO|[-+]?nan)`). A
      lower-case `no` data field — which the actual F2P input contains — was
      UNRECOGNISED pre-patch, so its whole data line raised `ValueError` at the
      line-classification stage before any masking loop ran. We validate the
      model's `is_reserved_data_token` two ways: (i) against the patched regex's
      reserved-token sub-pattern compiled with `re.IGNORECASE` (a verbatim slice
      of the gold-patched `_data_re`); and (ii) against the REAL `_line_type`'s
      `data`/`new` verdict on single-field data lines and on `NO`-only `new`
      lines, over every case combination + fuzz. (Ordinary decimal numbers are
      case-irrelevant unchanged machinery and are NOT in scope of this token
      predicate; we cross-check that the predicate and the real callee agree on
      every fuzzed reserved-word-or-near-miss field.)

The script prefers the REAL repo module `astropy.io.ascii.qdp` (the very file the
patch edits) AND asserts the imported function is the POST-patch one (G-AX runs
it in the official container with the gold patch applied; this guards against an
accidentally pre-patch import — see the post-patch discriminator below). If the
import is unavailable it reconstructs `_line_type` from the patched source
verbatim (only stdlib `re`), which is byte-faithful to the gold hunk. Exit 0 iff
every obligation holds.
"""
import random
import re
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def up(c):
    """model.py `up`: case normalisation of one code point (ASCII a-z -> A-Z;
    the long-s letterform 383 -> 'S' (83), the one further code point that
    case-insensitive matching identifies with a reserved-word letter)."""
    if 97 <= c <= 122:
        return c - 32
    if c == 383:
        return 83
    return c


def upseq(codepoints):
    """model.py `upseq`: per-code-point ASCII upper-casing fold."""
    return [up(c) for c in codepoints]


_NO = [ord(ch) for ch in "NO"]
_NAN = [ord(ch) for ch in "NAN"]


def model_is_masked_field(field_str):
    """model.py `is_masked_field`: masked iff case fold == 'NO'."""
    return upseq([ord(ch) for ch in field_str]) == _NO


def model_is_reserved_data_token(field_str):
    """model.py `is_reserved_data_token`: case fold is 'NO' or 'NAN' or a signed
    'NAN'."""
    cp = [ord(ch) for ch in field_str]
    f = upseq(cp)
    return (f == _NO
            or f == _NAN
            or (len(cp) >= 1 and cp[0] in (ord("+"), ord("-")) and f[1:] == _NAN))


_READ = [ord(ch) for ch in "READ"]
_SERR = [ord(ch) for ch in "SERR"]
_TERR = [ord(ch) for ch in "TERR"]


def model_is_command_tokens(tok0, tok1, ncols):
    """model.py `is_command_tokens`: READ + SERR/TERR + >=1 column."""
    f0 = upseq([ord(ch) for ch in tok0])
    f1 = upseq([ord(ch) for ch in tok1])
    return f0 == _READ and (f1 == _SERR or f1 == _TERR) and ncols >= 1


# --- the REAL callee: the patched `_line_type` -------------------------------

def _line_type_from_patched_source():
    """Reconstruct the gold-PATCHED `_line_type` verbatim (stdlib `re` only)."""
    def _line_type(line, delimiter=None):
        _decimal_re = r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"
        _command_re = r"READ [TS]ERR(\s+[0-9]+)+"
        sep = delimiter
        if delimiter is None:
            sep = r"\s+"
        _new_re = rf"NO({sep}NO)+"
        _data_re = rf"({_decimal_re}|NO|[-+]?nan)({sep}({_decimal_re}|NO|[-+]?nan))*)"
        _type_re = (
            rf"^\s*((?P<command>{_command_re})|(?P<new>{_new_re})|"
            rf"(?P<data>{_data_re})?\s*(\!(?P<comment>.*))?\s*$"
        )
        _line_type_re = re.compile(_type_re, re.IGNORECASE)  # the gold change
        line = line.strip()
        if not line:
            return "comment"
        match = _line_type_re.match(line)
        if match is None:
            raise ValueError(f"Unrecognized QDP line: {line}")
        for type_, val in match.groupdict().items():
            if val is None:
                continue
            if type_ == "data":
                return f"data,{len(val.split(sep=delimiter))}"
            else:
                return type_
    return _line_type


def _classify_or_none(line_type, line):
    try:
        return line_type(line)
    except ValueError:
        return None


def _assert_post_patch(line_type):
    """DEFECT-3 guard: the official base image is at base_commit (PRE-patch);
    the harness applies the gold patch before importing. Refuse to validate a
    PRE-patch callee, which would spuriously disagree with the deep model on
    every lower-case keyword. The discriminator: post-patch, a lower-case
    `read serr 1` is a command and a lower-case `no` is a data line; pre-patch
    both RAISE."""
    if _classify_or_none(line_type, "read serr 1") != "command":
        raise SystemExit(
            "axiom_check: imported _line_type is PRE-patch (lower-case "
            "'read serr 1' is not a command). Apply patch.diff before importing "
            "the in-container repo callee (run with apply_gold=True).")
    if _classify_or_none(line_type, "no") != "data,1":
        raise SystemExit(
            "axiom_check: imported _line_type is PRE-patch (lower-case 'no' is "
            "not recognised as a data token). Apply patch.diff before importing "
            "the in-container repo callee (run with apply_gold=True).")


def _real_line_type_factory():
    """Return the real PATCHED `_line_type`, preferring the in-container repo
    module; fall back to the gold-patched source. Either way assert it is the
    post-patch function."""
    try:
        from astropy.io.ascii.qdp import _line_type as real
        line_type = real
    except Exception:
        line_type = _line_type_from_patched_source()
    _assert_post_patch(line_type)
    return line_type


def real_is_command(line, line_type):
    """Real verdict: the patched _line_type classifies `line` as a command."""
    return _classify_or_none(line_type, line) == "command"


def real_is_masked(field):
    """Real patched missing-value test: `v.upper() == "NO"`."""
    return field.upper() == "NO"


# The reserved-token sub-pattern is a VERBATIM slice of the gold-patched
# `_data_re` alternation `(NO|[-+]?nan)`, compiled with re.IGNORECASE (the gold
# change). `fullmatch` decides whether a single field is one reserved data token.
_reserved_token_re = re.compile(r"(NO|[-+]?nan)", re.IGNORECASE)


def real_is_reserved_data_token_regex(field):
    """Real verdict (i): the patched reserved-token sub-pattern matches `field`
    in full, case-insensitively."""
    return _reserved_token_re.fullmatch(field) is not None


def real_data_or_new(line_type, field):
    """Real verdict (ii): the patched _line_type classifies a single-field line
    `field` as a `data` line (and a 2-token `NO`-style line as `new`). A reserved
    word recognised as a data token makes a single-field line classify as
    `data,1`; an unrecognised token RAISES."""
    v = _classify_or_none(line_type, field)
    return v is not None and (v.startswith("data") or v == "new")


# --- the checks --------------------------------------------------------------

def check_case_fold(s):
    """A-reference 1: upseq(s) == str.upper(s) on the ASCII token domain."""
    observed = [ord(ch) for ch in s.upper()]          # real str.upper
    expected = upseq([ord(ch) for ch in s])           # deep model
    assert observed == expected, (
        "case fold deep model unsound on %r: str.upper gave %r, "
        "upseq gives %r" % (s, observed, expected))


def check_masking(field):
    """A-reference 2: model masking == real `v.upper() == "NO"`."""
    assert model_is_masked_field(field) == real_is_masked(field), (
        "masking deep model disagrees with real v.upper()=='NO' on %r" % field)


def check_command(tok0, tok1, nums, line_type):
    """A-reference 3: model command verdict == real _line_type command verdict.

    `nums` is the list of trailing column-number tokens; the line is the two
    keyword words plus those numbers, whitespace separated."""
    ncols = len(nums)
    line = " ".join([tok0, tok1] + [str(n) for n in nums])
    model_v = model_is_command_tokens(tok0, tok1, ncols)
    real_v = real_is_command(line, line_type)
    assert model_v == real_v, (
        "command deep model disagrees with real _line_type on %r: "
        "model=%s real=%s" % (line, model_v, real_v))


def check_reserved_token_regex(field):
    """A-reference 4(i): model reserved-data-token verdict == the patched regex
    reserved-token sub-pattern (verbatim slice of `_data_re`, re.IGNORECASE)."""
    model_v = model_is_reserved_data_token(field)
    real_v = real_is_reserved_data_token_regex(field)
    assert model_v == real_v, (
        "reserved-data-token deep model disagrees with patched (NO|[-+]?nan) "
        "sub-pattern on %r: model=%s real=%s" % (field, model_v, real_v))


def check_reserved_token_linetype(field, line_type):
    """A-reference 4(ii): on the LETTER-CONTAINING field sub-domain (which
    excludes every ordinary decimal number — a decimal `_decimal_re` token has
    no ASCII letters), the model reserved-data-token verdict == whether the REAL
    patched _line_type accepts the single-field line as `data` (vs RAISE).

    The sub-domain filter ("field contains an ASCII letter OTHER than the
    exponent markers e/E") is an INPUT property independent of the predicate
    under test, so this is NOT a double-mask. The QDP data grammar admits
    letters only in two places: the reserved words `NO`/`nan`, and the exponent
    `[eE]` of a decimal number. A field containing a NON-exponent letter
    (N/O/A/n/o/a, but not e/E) therefore cannot be a decimal number, so
    `_line_type` accepts it as data iff it is exactly the reserved-word
    alternative `(NO|[-+]?nan)`. Decimal numbers (no non-exponent letters) are
    case-irrelevant unchanged machinery and out of this predicate's scope. The
    check compares model bool == real-accepts bool WITHOUT filtering either side
    by the predicate the model decides."""
    if not field or any(ch.isspace() for ch in field):
        return
    if not any(("a" <= ch.lower() <= "z") and ch not in "eE" for ch in field):
        return  # pure number / sign / dot / exponent: out of the reserved-word sub-domain
    model_v = model_is_reserved_data_token(field)
    real_v = real_data_or_new(line_type, field)
    assert model_v == real_v, (
        "reserved-data-token deep model disagrees with real _line_type data "
        "verdict on single letter-containing field %r: model=%s real=%s"
        % (field, model_v, real_v))


def check_new_branch(tokens, line_type):
    """A-reference 4(ii, new branch): a line of >=2 fields each case-folding to
    `NO` classifies as `new`; the model says every token is a reserved `NO`
    token. Validate the whole-line `new` verdict against real _line_type."""
    line = " ".join(tokens)
    if any(ch.isspace() for ch in "".join(tokens)) or not tokens:
        return
    model_all_no = len(tokens) >= 2 and all(model_is_masked_field(t) for t in tokens)
    real_v = _classify_or_none(line_type, line) == "new"
    assert model_all_no == real_v, (
        "new-branch deep model disagrees with real _line_type on %r: "
        "model(all NO, >=2)=%s real(new)=%s" % (line, model_all_no, real_v))


def main():
    line_type = _real_line_type_factory()
    rng = random.Random(14365)

    # --- A-reference 1: case fold over the ASCII token domain --------------
    letters = [chr(c) for c in range(65, 91)] + [chr(c) for c in range(97, 123)]
    digits = [chr(c) for c in range(48, 58)]
    misc = list(" .-+_no")
    fold_alphabet = letters + digits + misc
    fold_boundary = ["", "NO", "no", "No", "nO", "READ", "read", "Read",
                     "SERR", "serr", "TERR", "terr", "nan", "NAN", "Z", "a", "9",
                     "ſ", "ſERR", "ſerr"]
    for s in fold_boundary:
        check_case_fold(s)
    for _ in range(20000):
        n = rng.randint(0, 8)
        s = "".join(rng.choice(fold_alphabet) for _ in range(n))
        check_case_fold(s)

    # --- A-reference 2: missing-value recognition --------------------------
    mask_boundary = ["NO", "no", "No", "nO", "N0", "NOO", "ON", "n", "o", "",
                     "0.5", "nan", "NaN", "1", "-1.4e-5", " no", "no "]
    for f in mask_boundary:
        check_masking(f)
    mask_alphabet = list("NOno0.5-+eEnaN ")
    for _ in range(20000):
        n = rng.randint(0, 5)
        f = "".join(rng.choice(mask_alphabet) for _ in range(n))
        check_masking(f)

    # --- A-reference 3: command recognition --------------------------------
    read_words = ["READ", "read", "Read", "rEaD", "READING", "REA", "rad", "no"]
    err_words = ["SERR", "serr", "Serr", "sErR", "TERR", "terr", "Terr",
                 "ERR", "XERR", "SER", "serrr", "no",
                 "ſERR", "ſerr", "SEſR", "ſ"]
    num_lists = [[1], [1, 2], [3, 1, 4], [42], [1, 2, 3, 4, 5]]
    empty_num = [[]]
    # boundary: every keyword-case combination, with and without column numbers
    for w0 in read_words:
        for w1 in err_words:
            for nums in num_lists + empty_num:
                check_command(w0, w1, nums, line_type)
    # the exact F2P discriminators (lower-case real-world QDP commands)
    check_command("read", "serr", [1, 2], line_type)
    check_command("read", "terr", [1], line_type)
    check_command("READ", "SERR", [2], line_type)
    # randomized fuzz over case + keyword + column count
    for _ in range(5000):
        w0 = rng.choice(read_words)
        w1 = rng.choice(err_words)
        nums = rng.choice(num_lists + empty_num)
        check_command(w0, w1, nums, line_type)

    # --- A-reference 4: reserved-data-token recognition (data/new branches) -
    # boundary: every case variant of the reserved words, signs, and near-misses
    token_boundary = ["NO", "no", "No", "nO", "NAN", "nan", "NaN", "nAn",
                      "+nan", "-nan", "+NAN", "-NAN", "+NaN", "-nAn",
                      "N0", "NOO", "ON", "nann", "na", "n", "o", "naan",
                      "+no", "-no", "++nan", "1", "0.5", "1e3", "1E3",
                      "-1.4e-5", ".5", "+.5", "nan ", " nan"]
    for f in token_boundary:
        check_reserved_token_regex(f)
        check_reserved_token_linetype(f, line_type)
    # the exact F2P discriminator: a lower-case `no` field is a reserved token
    assert model_is_reserved_data_token("no"), "F2P: lower-case 'no' must be a reserved data token"
    assert real_data_or_new(line_type, "no"), "F2P: real _line_type must accept single 'no' as data"
    # near-miss alphabet fuzz over the reserved-word domain (no whitespace)
    token_alphabet = list("NOnaANANO+-")
    for _ in range(20000):
        n = rng.randint(0, 5)
        f = "".join(rng.choice(token_alphabet) for _ in range(n))
        check_reserved_token_regex(f)
        check_reserved_token_linetype(f, line_type)

    # --- A-reference 4 (new branch): >=2 reserved `NO` tokens -> `new` ------
    no_variants = ["NO", "no", "No", "nO"]
    near_no = ["NO", "no", "nan", "1", "NOO", "N0"]
    for _ in range(4000):
        k = rng.randint(1, 5)
        toks = [rng.choice(no_variants) for _ in range(k)]
        check_new_branch(toks, line_type)
    for _ in range(4000):
        k = rng.randint(1, 5)
        toks = [rng.choice(near_no) for _ in range(k)]
        check_new_branch(toks, line_type)
    # exact discriminators
    check_new_branch(["no", "no", "no", "no", "no"], line_type)  # F2P-style lower-case `new`
    check_new_branch(["NO", "NO"], line_type)
    check_new_branch(["no"], line_type)  # single token -> data, not new

    print("G-AX OK: case fold (upseq == str.upper) + masking "
          "(== v.upper()=='NO') + command recognition (== patched _line_type) "
          "+ reserved-data-token recognition (== patched (NO|[-+]?nan) + real "
          "_line_type data/new verdict) sound on %d boundary + 73000 fuzz "
          "observations" % (len(fold_boundary) + len(mask_boundary)
                            + len(read_words) * len(err_words)
                            + len(token_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
