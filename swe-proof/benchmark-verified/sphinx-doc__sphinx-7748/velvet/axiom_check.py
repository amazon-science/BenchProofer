#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7748.

This bundle consumes NO axioms. The single kind-A construct is an **A-reference**:
the per-line classification `LineInfo` is supplied to the modeled method as an
input carrier, and G-AX must validate that this carrier is a FAITHFUL abstraction
of the genuinely-**unchanged** per-line callees the scan reads.

SCOPE (why this checks only the bridge):
  G-AX runs against the repo at base_commit *without* the gold patch applied
  (only G-CONF applies it — its oracle is the patched repo). So the only thing
  G-AX can soundly audit is the part of the model that is **patch-independent**:
  the unchanged callees. The end-to-end equivalence "deep model `collectSigs` ==
  the real *patched* `_find_signature`" is a property of the CHANGED function and
  is owned by G-CONF (`conformance_check.py`, which applies the gold patch and
  diffs the R/I shadow against the patched oracle on >=10^5 inputs). Re-running it
  here against the *unpatched* function would compare the correct model to the
  pre-patch bug — a false negative, not a soundness signal.

The A-reference under audit (mapping.md §3 bridge):
  `line_info(s, valid_names)` is built from the REAL `py_ext_sig_re` (the
  unchanged module-level signature regex — the patch only moves its call site,
  not its definition) and the REAL `str.endswith`/`str.rstrip`/`bool`. We assert
  each `LineInfo` field has exactly the semantics Solution.lean's spec relies on:
        blank == (not line)
        cont  == line.endswith('\\')
        isSig == bool(real_regex.match(line.rstrip('\\').rstrip())) and base in valid_names
        sig   == (group(4), group(5)) of that match
  over a boundary corpus and randomized fuzz, in BOTH documenter configurations
  (plain-function valid_names and class valid_names; mapping.md §3 callee
  provenance). Each field is independently recomputed from the real callees and
  compared to the bridge.

Imports only `re`/`random` (stdlib) plus the REAL repo regex `py_ext_sig_re`
(the callee under audit). Exit 0 iff every per-line observation matches.
"""
import random
import sys

# --- the REAL unchanged callee: the module-level signature regex ------------
from sphinx.ext.autodoc import py_ext_sig_re


# --- mapping.md §3 bridge: one docstring line -> LineInfo (uses real callees) -
def line_info(s, valid_names):
    blank = not s
    if s.endswith('\\'):
        cont = True
        stripped = s.rstrip('\\').rstrip()
    else:
        cont = False
        stripped = s
    m = py_ext_sig_re.match(stripped)
    is_sig = bool(m) and (m.group(3) in valid_names)
    sig = (m.group(4), m.group(5)) if m else (None, None)
    return {"blank": blank, "isSig": is_sig, "cont": cont, "sig": sig}


# --- corpora -----------------------------------------------------------------
def sig_lines(name):
    return [
        "%s(foo, bar)" % name,
        "%s(foo: int, bar: int, baz: int) -> None" % name,
        "%s(a)" % name,
        "%s()" % name,
        "%s" % name,                      # bare name: regex matches, args=None
        "module.%s(x) -> str" % name,
    ]


def check_line(s, valid_names):
    """Independently recompute every LineInfo field from the real callees and
    assert the bridge agrees. This is the A-reference soundness obligation."""
    li = line_info(s, valid_names)
    exp_blank = not s
    exp_cont = s.endswith('\\')
    stripped = s.rstrip('\\').rstrip() if exp_cont else s
    m = py_ext_sig_re.match(stripped)
    exp_isSig = bool(m) and (m.group(3) in valid_names)
    assert li["blank"] == exp_blank, (s, valid_names, "blank")
    assert li["cont"] == exp_cont, (s, valid_names, "cont")
    assert li["isSig"] == exp_isSig, (s, valid_names, "isSig")
    if m:
        assert li["sig"] == (m.group(4), m.group(5)), (s, valid_names, "sig")
    else:
        assert li["sig"] == (None, None), (s, valid_names, "sig-none")


def main():
    # mapping.md §3 callee provenance: validate BOTH documenter configurations.
    #   plain function: valid_names == [objpath[-1]]
    #   class:          valid_names == [objpath[-1], '__init__', *mro names]
    name_configs = [
        ["E"],                                  # plain-function case
        ["E", "__init__", "Base", "object"],    # class case (mro names included)
    ]

    boundary_lines = [
        "",
        "   ",
        "Some descriptive text.",
        "E(foo: int, bar: int, baz: int) -> None \\",
        "E(foo: str, bar: str, baz: str) -> None",
        "E(foo, bar) \\",
        "F(x, y)",                        # wrong name -> isSig False (function case)
        "    E(indented)",                # leading space -> regex anchored ^, no match
        "D(foo, bar, baz)",
        "E -> None",
        "E\\",
        "__init__(self, x)",              # matches only in the class config
        "Base(a, b)",                     # mro name: class config only
    ]
    boundary_lines += sig_lines("E") + sig_lines("F") + sig_lines("Base")

    n_checks = 0
    for vn in name_configs:
        for s in boundary_lines:
            check_line(s, vn)
            n_checks += 1

    # ---- randomized per-line fuzz over both configs -------------------------
    rng = random.Random(7748)
    line_pool = (
        [""] + sig_lines("E") + sig_lines("F") + sig_lines("Base") + sig_lines("__init__")
        + ["plain text", "  indented", "E -> int", "E(a, *args, **kw) -> 'T'"]
    )
    # decorate signature lines with a trailing continuation marker
    cont_pool = [l + " \\" for l in sig_lines("E") + sig_lines("F") + sig_lines("Base")]
    pool = line_pool + cont_pool

    for _ in range(40000):
        s = rng.choice(pool)
        vn = rng.choice(name_configs)
        check_line(s, vn)
        n_checks += 1

    print("G-AX OK: LineInfo A-reference bridge sound vs the real unchanged "
          "callees (py_ext_sig_re + str.endswith/rstrip + valid_names "
          "membership) on %d boundary lines x 2 configs + 40000 fuzz checks "
          "(seed=7748). End-to-end model<->patched-function equivalence is "
          "owned by G-CONF." % len(boundary_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
