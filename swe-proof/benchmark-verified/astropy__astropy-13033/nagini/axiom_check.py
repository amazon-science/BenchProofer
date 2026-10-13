#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13033.

This bundle consumes NO axioms. The changed behaviour -- rendering a run of
column names for the disagreement report, and assembling the full report -- is
modelled DEEPLY in model.py (the pure folds `quoted` / `joined` / `render_run`
/ `report_seq` and the verified construction loop in `as_scalar_or_list_str`).
G-AX therefore validates those deep models as A-references: it executes the
REAL behaviour and asserts the deep model reproduces it exactly.

The deep model abstracts each column name as one token. The validation
substitutes a real name string for each token, so the token sequence the model
produces must, after substitution, equal:

  * the real helper `as_scalar_or_list_str(run)` -- the exact function added by
    the fix (a lone name -> "'name'"; any other length -> the ordinary textual
    list form str(run)); and

  * the full report -- the exact format string the fix emits.

The model's punctuation code points (apostrophe 39, comma 44, space 32,
brackets 91/93, and the literal class/connective text) must line up
character-for-character with the real output once the name tokens are expanded.
Imports only the standard library. Exit 0 iff every observation matches.
"""
import random
import sys

# --- the REAL behaviour (the exact code the gold patch ships) ---------------
# as_scalar_or_list_str is the helper introduced by the fix; reproduced here
# verbatim so G-AX checks the deep model against the real function, not a
# paraphrase.


def real_as_scalar_or_list_str(obj):
    if not hasattr(obj, "__len__"):
        return f"'{obj}'"
    elif len(obj) == 1:
        return f"'{obj[0]}'"
    else:
        return str(obj)


def real_report(cls_name, required_columns, found_columns):
    """The exact message the patched _check_required_columns emits in the
    leading-run-disagreement branch."""
    plural = 's' if len(required_columns) > 1 else ''
    return ("{} object is invalid - expected {} "
            "as the first column{} but found {}"
            .format(cls_name,
                    real_as_scalar_or_list_str(required_columns),
                    plural,
                    real_as_scalar_or_list_str(found_columns)))


# --- model.py deep-model encodings (kept in lock-step with model.py) --------

NAME_QUOTE = 39
COMMA = 44
SPACE = 32
LBRACK = 91
RBRACK = 93


def encode_name(t):
    return t + 256


def quoted(t):
    return [NAME_QUOTE, encode_name(t), NAME_QUOTE]


def joined(run):
    if len(run) == 0:
        return []
    if len(run) == 1:
        return quoted(run[0])
    return quoted(run[0]) + [COMMA, SPACE] + joined(run[1:])


def render_run(run):
    if len(run) == 1:
        return quoted(run[0])
    return [LBRACK] + joined(run) + [RBRACK]


def seg(s):
    return [ord(c) for c in s]


def report_seq(cls_name, demanded, found):
    seg1 = seg(" object is invalid - expected ")
    seg2 = seg(" as the first column")
    plural = [ord('s')] if len(demanded) > 1 else []
    seg3 = seg(" but found ")
    return (seg(cls_name) + seg1 + render_run(demanded) + seg2 + plural + seg3
            + render_run(found))


# --- substitution: expand a model token sequence to the real string ---------

def expand(model_seq, names):
    """Replace each encoded name token (>= 256) by that name's real string and
    each punctuation/literal code point by its character, yielding the real
    rendered string the model claims to produce."""
    out = []
    for code in model_seq:
        if code >= 256:
            out.append(names[code - 256])
        else:
            out.append(chr(code))
    return "".join(out)


# --- the checks --------------------------------------------------------------

def check_render(names):
    """names: list of real column-name strings (run). Tokens are their indices
    0..n-1. Assert the deep model render_run, expanded, == real helper."""
    run_tokens = list(range(len(names)))
    model = render_run(run_tokens)
    observed = expand(model, names)
    expected = real_as_scalar_or_list_str(names)
    assert observed == expected, (
        "render_run deep model unsound on %r: model->%r real->%r"
        % (names, observed, expected))


def check_report(cls_name, demanded_names, found_names):
    dem_tokens = list(range(len(demanded_names)))
    fnd_tokens = list(range(len(demanded_names),
                            len(demanded_names) + len(found_names)))
    all_names = demanded_names + found_names
    model = report_seq(cls_name, dem_tokens, fnd_tokens)
    observed = expand(model, all_names)
    expected = real_report(cls_name, demanded_names, found_names)
    assert observed == expected, (
        "report_seq deep model unsound on cls=%r demanded=%r found=%r: "
        "model->%r real->%r"
        % (cls_name, demanded_names, found_names, observed, expected))


def main():
    # --- boundary runs: length 0, 1, 2, 3 over realistic names -------------
    boundary_runs = [
        [],
        ["time"],
        ["a"],
        ["time", "a"],
        ["time", "flux"],
        ["time", "a", "b"],
        ["x", "y", "z", "w"],
        ["banana"],
        ["time", "b"],
    ]
    for run in boundary_runs:
        check_render(run)

    # The exact F2P scenario (issue #13009): demanded ['time','a'] vs found
    # ['time','b'] under TimeSeries, and the legacy single-column scenarios.
    check_report("TimeSeries", ["time", "a"], ["time", "b"])
    check_report("TimeSeries", ["time"], ["a"])
    check_report("TimeSeries", ["time"], ["banana"])
    check_report("TimeSeries", ["time"], ["c"])
    check_report("TimeSeries", ["time"], ["d"])
    check_report("TimeSeries", ["time", "a"], ["b", "c"])

    # --- randomized fuzz over name alphabets and run lengths ---------------
    rng = random.Random(13033)
    alphabet = ["time", "flux", "a", "b", "c", "abc", "col_1", "X", "name",
                "value", "t", "q"]
    for _ in range(20000):
        nd = rng.randint(0, 5)
        nf = rng.randint(0, 5)
        demanded_names = [rng.choice(alphabet) for _ in range(nd)]
        found_names = [rng.choice(alphabet) for _ in range(nf)]
        check_render(demanded_names)
        check_render(found_names)
        cls = rng.choice(["TimeSeries", "BinnedTimeSeries", "SampledTimeSeries"])
        check_report(cls, demanded_names, found_names)

    print("G-AX OK: render_run + report_seq deep models reproduce the real "
          "as_scalar_or_list_str helper and the real report format over "
          "%d boundary runs + 6 fixed reports + 20000 fuzz reports "
          "(0 mismatch)" % len(boundary_runs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
