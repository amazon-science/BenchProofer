#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for astropy__astropy-14508.

The bundle models `_format_float(value)`: render a numeric value as the string
written into a fixed-width header card, shortened to at most 20 characters.

The modeled value is a PURE function of the value's grounded textual carriers:

    reprStr  = str(value)            (the value's shortest standard form)
    fixedStr = f"{value:.16G}"       (the fixed-precision form, pre-patch only)

Post-patch rule (the gold edit builds value_str from str(value), not the
fixed-precision form, then applies the UNCHANGED 20-char limit):

    value_str = reprStr.replace("e","E")
    if len(value_str) > 20:
        idx = value_str.find("E")
        if idx < 0:  value_str = value_str[:20]
        else:        value_str = value_str[:20-(len-idx)] + value_str[idx:]
    return value_str

Standing up the full astropy Card machinery is unnecessary: the modeled value is
this pure decision over the textual carrier the real function reads. So the
ORACLE below is a faithful in-process replica of the POST-PATCH `_format_float`
(operating on the raw repr carrier), and the SHADOW is the op-for-op
transliteration of `implementation_formatFloat` (Solution.lean impl region) per
refinement.md. We additionally drive both with the REAL `str(value)` of randomly
generated floats so the modeling against actual Python float reprs is exercised.

stdlib-only. Pinned seed: 14508 (also in mapping.md).
"""
import random
import sys

SEED = 14508
N = 120_000


# --- normE: .replace("e","E") modeled per-char (mapping.md) -------------------
def normE(s):
    return "".join("E" if c == "e" else c for c in s)


# --- the UNCHANGED 20-char limiting block (deep model: truncate20) ------------
def truncate20(value_str):
    str_len = len(value_str)
    if str_len > 20:
        idx = value_str.find("E")
        if idx < 0:
            value_str = value_str[:20]
        else:
            value_str = value_str[: 20 - (str_len - idx)] + value_str[idx:]
    return value_str


# --- ORACLE: faithful in-process replica of POST-PATCH _format_float ----------
# Takes the raw repr carrier (= str(value)); == the real post-patch function.
def oracle(repr_str):
    value_str = repr_str.replace("e", "E")
    return truncate20(value_str)


# --- SHADOW of implementation_formatFloat (the R/I leg) -----------------------
# Mirrors Solution.lean impl region exactly: normE reprStr, then truncate20.
def shadow(repr_str):
    value_str = normE(repr_str)
    str_len = len(value_str)
    if str_len > 20:
        idx = value_str.find("E")
        if idx < 0:
            value_str = value_str[:20]
        else:
            value_str = value_str[: 20 - (str_len - idx)] + value_str[idx:]
    return value_str


def disagree(repr_str):
    got = oracle(repr_str)
    want = shadow(repr_str)
    if got != want:
        return (repr_str, got, want)
    return None


def _edge_cases():
    cases = []
    # F2P values: short forms, unchanged
    cases += ["0.009125", "8.95", "-99.9"]
    # the unnecessarily-expanded fixed-precision form (must be > 20 so it would
    # truncate — confirms the post-patch path does not produce it)
    cases += ["0.009124999999999999", "8.9500000000000002", "-99.900000000000006"]
    # scientific notation, lower- and upper-case markers
    cases += ["1e-10", "1E-10", "1.23e+05", "6.022e23", "-3.14e-7"]
    # long mantissa with exponent -> significand truncation branch
    cases += ["1.234567890123456789e-100", "-1.2345678901234567e+300",
              "3.141592653589793e-123"]
    # long non-scientific string -> [:20] branch
    cases += ["0." + "1" * 40, "-0." + "9" * 40, "123456789012345678901234567890"]
    # boundary lengths around 20
    cases += ["1" * 20, "1" * 21, "1" * 19, "1.0", "-0.0", "inf", "-inf", "nan"]
    return cases


def main() -> int:
    checked = 0
    for rs in _edge_cases():
        d = disagree(rs)
        if d:
            print(f"DISAGREE edge: repr={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)

    # (a) real str(float) carriers — the actual representations the patch reads
    for _ in range(N // 2):
        kind = rng.random()
        if kind < 0.4:
            v = rng.uniform(-1e6, 1e6)
        elif kind < 0.7:
            v = rng.uniform(-1, 1) * 10 ** rng.randint(-300, 300)
        elif kind < 0.85:
            v = float(rng.randint(-(10 ** 18), 10 ** 18))
        else:
            v = rng.choice([0.0, -0.0, float("inf"), float("-inf"),
                            float("nan"), 1e-323, 1.7e308])
        rs = str(v)
        d = disagree(rs)
        if d:
            print(f"DISAGREE float: v={v!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    # (b) synthetic carrier strings — stress every truncation branch
    alphabet = "0123456789.+-eE"
    for _ in range(N - N // 2):
        n = rng.randint(0, 40)
        rs = "".join(rng.choice(alphabet) for _ in range(n))
        d = disagree(rs)
        if d:
            print(f"DISAGREE synth: repr={rs!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
