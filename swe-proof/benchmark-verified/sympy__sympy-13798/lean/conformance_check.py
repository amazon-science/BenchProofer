#!/usr/bin/env python3
r"""G-CONF — mechanical differential conformance for sympy__sympy-13798.

The bundle models how `LatexPrinter.__init__` derives the two multiplication-
separator strings from the `mul_symbol` selector:

    mul_symbol_latex          (separator between general factors)
    mul_symbol_latex_numbers  (separator between numeric coefficients)

This is a PURE function of the selector and the CONSTANT table

    mul_symbol_table = {None: " ", "ldot": r" \,.\, ",
                        "dot": r" \cdot ", "times": r" \times "}

POST-PATCH rule (the gold edit wraps each subscript in try/except KeyError):

    try:    latex      = mul_symbol_table[mul_symbol]
    except: latex      = mul_symbol
    try:    latexNum   = mul_symbol_table[mul_symbol or 'dot']
    except:
        if mul_symbol.strip() in ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']:
                latexNum = mul_symbol_table['dot']
        else:   latexNum = mul_symbol

The ORACLE below is a faithful in-process replica of the POST-PATCH derivation.
The SHADOW is the op-for-op transliteration of `implementation_initMulSymbol`
(Solution.lean impl region) per refinement.md, using the `KeyError ↔ none` and
result-type bijections from mapping.md. We additionally cross-check the oracle
against the REAL `sympy.printing.latex.LatexPrinter` when sympy is importable in
the container, so the modeling is exercised against the actual constructor.

stdlib-only (sympy optional). Pinned seed: 13798 (also in mapping.md).
"""
import random
import sys

SEED = 13798
N = 120_000

MUL_SYMBOL_TABLE = {
    None: r" ",
    "ldot": r" \,.\, ",
    "dot": r" \cdot ",
    "times": r" \times ",
}
SPACE_LIKE = ['', ' ', '\\', '\\,', '\\:', '\\;', '\\quad']


# --- ORACLE: faithful in-process replica of the POST-PATCH derivation ---------
def oracle(mul_symbol):
    try:
        latex = MUL_SYMBOL_TABLE[mul_symbol]
    except KeyError:
        latex = mul_symbol
    try:
        latex_num = MUL_SYMBOL_TABLE[mul_symbol or 'dot']
    except KeyError:
        if mul_symbol.strip() in SPACE_LIKE:
            latex_num = MUL_SYMBOL_TABLE['dot']
        else:
            latex_num = mul_symbol
    return ("ok", latex, latex_num)


# --- model pieces mirroring Solution.lean pure region -------------------------
def mul_symbol_table(ms):
    """`mulSymbolTable : Option String → Option String`; None key = None selector."""
    if ms is None:
        return ("some", " ")
    if ms == "ldot":
        return ("some", r" \,.\, ")
    if ms == "dot":
        return ("some", r" \cdot ")
    if ms == "times":
        return ("some", r" \times ")
    return ("none",)


def num_key(ms):
    """`numKey`: None or '' selector behaves as 'dot'."""
    if ms is None:
        return "dot"
    return "dot" if ms == "" else ms


def py_whitespace(c):
    """Transliteration of `pyWhitespace` (Solution.lean): the Unicode
    whitespace set used by str.strip()."""
    o = ord(c)
    return (0x09 <= o <= 0x0d or 0x1c <= o <= 0x20 or o == 0x85 or o == 0xa0
            or o == 0x1680 or 0x2000 <= o <= 0x200a or o == 0x2028
            or o == 0x2029 or o == 0x202f or o == 0x205f or o == 0x3000)


def py_strip(s):
    """Transliteration of `pyStrip` (Solution.lean): dropWhile from both ends."""
    chars = list(s)
    i = 0
    while i < len(chars) and py_whitespace(chars[i]):
        i += 1
    j = len(chars)
    while j > i and py_whitespace(chars[j - 1]):
        j -= 1
    return "".join(chars[i:j])


def is_space_like(s):
    return py_strip(s) in SPACE_LIKE


DOT_LATEX = r" \cdot "


# --- SHADOW of implementation_initMulSymbol (the R/I leg) ---------------------
def shadow(ms):
    t = mul_symbol_table(ms)
    if t[0] == "some":
        latex = t[1]
    else:
        latex = ms if ms is not None else ""
    tn = mul_symbol_table(num_key(ms))
    if tn[0] == "some":
        latex_num = tn[1]
    else:
        base = ms if ms is not None else ""
        latex_num = DOT_LATEX if is_space_like(base) else base
    return ("ok", latex, latex_num)


def disagree(ms):
    got = oracle(ms)
    want = shadow(ms)
    if got != want:
        return (ms, got, want)
    return None


def _edge_cases():
    cases = [None, "", " ", "dot", "ldot", "times"]
    # F2P: the thin space and other spacing macros
    cases += ["\\,", "\\:", "\\;", "\\quad", "\\"]
    # arbitrary unrecognized selectors (general-separator verbatim branch)
    cases += ["x", "*", r"\ast", r"\bullet", "  \\,  ", "DOT", "Times", "  "]
    # selectors that strip to a space-like macro (numeric falls back to dot)
    cases += ["  \\quad  ", "\t\\,\n", "   "]
    # selectors that are NOT space-like (numeric used verbatim)
    cases += ["\\,x", "x\\,", r"\cdot", "??"]
    # exotic whitespace: str.strip() removes these too, so the numeric
    # separator falls back to dot (G-PANEL-2 counterexample class: \x0c,
    # \x0b, \x1c-\x1f, NEL, NBSP, and other Unicode space code points)
    cases += ["\x0c", "\x0b", "\x1c", "\x1d", "\x1e", "\x1f",
              "\x85", "\xa0", "\u1680", "\u2003", "\u200a", "\u2028",
              "\u2029", "\u202f", "\u205f", "\u3000",
              "\xa0\\,\xa0", "\x0c\\quad\x0b", "\u2003 \u2003"]
    # exotic whitespace glued to non-space content (NOT space-like: verbatim)
    cases += ["\x0cx", "x\xa0y", "\u2003\\cdot\u2003"]
    return cases


def _try_real_sympy():
    """If sympy is importable, cross-check the oracle against the REAL
    post-patch LatexPrinter constructor for a handful of selectors."""
    try:
        from sympy.printing.latex import LatexPrinter
    except Exception:
        return 0
    checked = 0
    for ms in _edge_cases():
        try:
            p = LatexPrinter({'mul_symbol': ms})
        except Exception:
            # the real (post-patch) constructor should never raise here
            print(f"REAL constructor raised for mul_symbol={ms!r}")
            print("status=fail")
            sys.exit(1)
        real = ("ok", p._settings['mul_symbol_latex'],
                p._settings['mul_symbol_latex_numbers'])
        if real != oracle(ms):
            print(f"REAL vs oracle mismatch ms={ms!r} real={real!r} "
                  f"oracle={oracle(ms)!r}")
            print("status=fail")
            sys.exit(1)
        checked += 1
    return checked


def main() -> int:
    checked = 0
    for ms in _edge_cases():
        d = disagree(ms)
        if d:
            print(f"DISAGREE edge: ms={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    checked += _try_real_sympy()

    rng = random.Random(SEED)
    exotic_ws = ["\t", "\n", "\x0b", "\x0c", "\r", "\x1c", "\x1d", "\x1e",
                 "\x1f", "\x85", "\xa0", " ", " ", " ",
                 " ", " ", " ", " ", " ", "　"]
    alphabet = (list(" \\,:;.xX*0123456789{}qadt")
                + ["\\,", "\\quad", "\\:", "\\;"] + exotic_ws)
    pool = [None, "", " ", "dot", "ldot", "times", "\\,", "\\:", "\\;", "\\quad",
            "\\", "x", "*", "\\cdot"] + exotic_ws
    for _ in range(N):
        r = rng.random()
        if r < 0.3:
            ms = rng.choice(pool)
        elif r < 0.6:
            n = rng.randint(0, 8)
            ms = "".join(rng.choice(alphabet) for _ in range(n))
        else:
            # bias toward whitespace-wrapped space-like macros to exercise the
            # numeric fallback branch (padding drawn from the FULL Unicode
            # whitespace set, not just ASCII space)
            core = rng.choice(["", "\\,", "\\quad", "\\:", "\\;", "\\", " ", "x"])
            pad = "".join(rng.choice([" "] + exotic_ws)
                          for _ in range(rng.randint(0, 3)))
            ms = pad + core + pad
        d = disagree(ms)
        if d:
            print(f"DISAGREE fuzz: ms={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"status=pass checked={checked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
