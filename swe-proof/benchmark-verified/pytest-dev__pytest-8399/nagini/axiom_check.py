#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-8399.

This bundle consumes NO @ContractOnly axiom. It does carry one A-reference: the
deep model `listed` (model.py pure region) of the framework's *unchanged*
fixture-listing visibility rule. G-AX validates that deep model against the real
rule, and validates the end-to-end property the fix relies on.

The real visibility rule lives in `src/_pytest/python.py` (at base_commit
6e7dc8bac831cd8cf7a53b08efa366bd84f0c0fe):

  - `_showfixtures_main` (line 1511, reached by `pytest --fixtures`):
        if verbose <= 0 and argname[0] == "_":
            continue                       # fixture omitted from the listing
  - `_show_fixtures_per_test` (line 1429, the per-test variant):
        if verbose <= 0 and argname.startswith("_"):
            return                         # fixture omitted

Both agree: a fixture is omitted at the default verbosity (verbose <= 0) exactly
when its name's first character is the privacy marker '_'; at a raised verbosity
(verbose > 0) it is always shown. The deep model:

    listed(name, verbose) == True              if verbose > 0
                          == not name.startswith('_')   otherwise

is asserted equal to BOTH real filter expressions over boundary + fuzz.

We also reproduce the gold fix's structural effect: the generated fixture name
is `label` with the privacy marker prepended (the gold patch changes the f-string
prefix from `"unittest_..."` to `"_unittest_..."`, and similarly for the four
xunit prefixes). Prepending '_' to any real descriptive label flips the real
filter from "shown" to "omitted" at default verbosity while leaving it shown at
verbose -- exactly what the F2P test observes (no "no docstring available" line
under `--fixtures`, but the line reappears under `--fixtures -v`).

Imports nothing repo-specific; pure standard library. Exit 0 iff every
obligation holds.
"""
import random
import string
import sys

PRIVACY_MARKER = ord("_")  # 95


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def model_begins_private(name):
    """begins_private(name): first code point is the privacy marker."""
    return len(name) > 0 and name[0] == PRIVACY_MARKER


def model_listed(name, verbose):
    """Deep model `listed` (model.py pure region), over a list of code points."""
    if verbose > 0:
        return True
    return not model_begins_private(name)


def model_generated_name(label):
    """Deep model `generated_fixture_name`: prepend the privacy marker."""
    return [PRIVACY_MARKER] + list(label)


# --- the REAL framework visibility rules (verbatim from python.py) -----------

def real_filter_showfixtures_main(argname, verbose):
    """Returns True iff the fixture is SHOWN, mirroring _showfixtures_main:
        if verbose <= 0 and argname[0] == "_": continue   # i.e. NOT shown
    """
    if verbose <= 0 and argname[0] == "_":
        return False
    return True


def real_filter_per_test(argname, verbose):
    """Returns True iff the fixture is SHOWN, mirroring _show_fixtures_per_test:
        if verbose <= 0 and argname.startswith("_"): return  # i.e. NOT shown
    """
    if verbose <= 0 and argname.startswith("_"):
        return False
    return True


# --- checks ------------------------------------------------------------------

def check_listed_reference(name_str, verbose):
    """Assert deep model `listed` == both real filter rules for a nonempty
    name (the filters index argname[0], so they require a nonempty name)."""
    codepoints = [ord(ch) for ch in name_str]
    model = model_listed(codepoints, verbose)
    real_main = real_filter_showfixtures_main(name_str, verbose)
    real_pt = real_filter_per_test(name_str, verbose)
    assert model == real_main == real_pt, (
        "listed deep model unsound on name=%r verbose=%d: "
        "model=%r real(_showfixtures_main)=%r real(_show_fixtures_per_test)=%r"
        % (name_str, verbose, model, real_main, real_pt))


def check_fix_effect(label_str):
    """Reproduce the gold fix: prepend '_' to a descriptive label. The real
    filter must OMIT the result at default verbosity and SHOW it at verbose;
    and the un-prefixed (pre-patch) label, beginning with an ordinary letter,
    must be SHOWN even at default verbosity (the bug)."""
    assert label_str and label_str[0] != "_", (
        "test label must be a genuine non-private label: %r" % (label_str,))

    fixed = "_" + label_str  # post-patch generated name

    # post-patch: omitted at default verbosity, shown at verbose
    assert not real_filter_showfixtures_main(fixed, 0), (
        "post-patch name %r should be omitted at default verbosity" % (fixed,))
    assert real_filter_showfixtures_main(fixed, 1), (
        "post-patch name %r should be shown at verbose" % (fixed,))

    # pre-patch (the bug): the un-prefixed label is shown at default verbosity
    assert real_filter_showfixtures_main(label_str, 0), (
        "pre-patch name %r should (buggily) be shown at default verbosity"
        % (label_str,))

    # the deep model agrees on the post-patch generated name
    gen = model_generated_name([ord(ch) for ch in label_str])
    assert gen[0] == PRIVACY_MARKER and gen[1:] == [ord(ch) for ch in label_str]
    assert not model_listed(gen, 0)
    assert model_listed(gen, 1)


def main():
    # The actual descriptive labels the framework builds (gold f-strings minus
    # the leading '_'): the five generated xunit/unittest fixtures, with sample
    # qualnames covering the issue's reported cases.
    real_labels = [
        "unittest_setUpClass_fixture_MyTestCase",
        "unittest_setUpModule_fixture_MyTestCase",
        "xunit_setup_module_fixture_test_mod",
        "xunit_setup_function_fixture_test_mod",
        "xunit_setup_class_fixture_Test",
        "xunit_setup_method_fixture_Test",
        "unittest_setUpClass_fixture_Outer.Inner",
        "xunit_setup_class_fixture_A.B.C",
    ]
    for label in real_labels:
        check_fix_effect(label)

    # boundary names for the listing visibility rule (deep model == real rule)
    boundary = [
        "_", "_x", "_unittest_setUpClass_fixture_X",
        "a", "Z", "0", "fixture", "xunit_setup_class_fixture_T",
        "__dunder__", "_leading", "trailing_", "a_b_c",
        " _", "x_", "9_lives", "_", "_0",
    ]
    for name in boundary:
        for verbose in (-1, 0, 1, 2):
            check_listed_reference(name, verbose)

    # randomized fuzz over the listing visibility rule
    rng = random.Random(8399)
    alphabet = string.ascii_letters + string.digits + "_." + " "
    for _ in range(20000):
        n = rng.randint(1, 40)  # nonempty: the real filter indexes argname[0]
        name = "".join(rng.choice(alphabet) for _ in range(n))
        for verbose in (-2, -1, 0, 1, 3):
            check_listed_reference(name, verbose)

    # fuzz the end-to-end fix effect on labels that start with a letter
    letters = string.ascii_letters
    body = string.ascii_letters + string.digits + "_."
    for _ in range(20000):
        first = rng.choice(letters)
        n = rng.randint(0, 40)
        label = first + "".join(rng.choice(body) for _ in range(n))
        check_fix_effect(label)

    print("G-AX OK: `listed` deep model == real fixture-listing visibility rule "
          "(_showfixtures_main + _show_fixtures_per_test) over %d boundary + "
          "20000 fuzz names; fix effect (prepend '_') verified on %d real "
          "labels + 20000 fuzz labels"
          % (len(boundary), len(real_labels)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
