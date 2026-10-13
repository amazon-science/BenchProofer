#!/usr/bin/env python3
"""G-CONF differential conformance for mwaskom__seaborn-3187 — SKIPPED.

WHY conf_skip=true (impl region is all-A-tagged):

Both modeled `do` blocks (`legendLabels`, `legendEntries`) build a brief numeric
legend's labels by handing a list of tick positions to matplotlib's tick
renderer. The patched code is, at both sites:

    seaborn/_core/scales.py (legend branch of Continuous._setup):
        if hasattr(axis.major.formatter, "set_useOffset"):
            axis.major.formatter.set_useOffset(False)
        if hasattr(axis.major.formatter, "set_scientific"):
            axis.major.formatter.set_scientific(False)
        labels = axis.major.formatter.format_ticks(locs)

    seaborn/utils.py (locator_to_legend_entries, the ScalarFormatter branch):
        formatter = mpl.ticker.ScalarFormatter()
        formatter.set_useOffset(False)
        formatter.set_scientific(False)
        ...
        formatted_levels = [formatter(x) for x in raw_levels]

The single observable the spec pins — each printed label, read back, denotes its
tick's true value — is produced ENTIRELY by the axiomatized callee `renderTicks`
(matplotlib's `ScalarFormatter.format_ticks`) / `renderLog` (`LogFormatter`).
The impl region's own R/I content is only:
  * the two configuration constants `offsetMode = scaleMode = false` (the patch's
    `set_useOffset(False)` / `set_scientific(False)`), and
  * the `isLog` renderer selection (the `LogLocator` branch of utils.py),
neither of which is an input-dependent transformation of the label CONTENTS that
this gate could differentially fuzz. The computed `labels` value is the callee's
output verbatim; there is no R/I shadow to transliterate.

The discriminating fact — that a `ScalarFormatter` with BOTH shared-term
abbreviation modes disabled renders labels that read back to their ticks, while
the default (either mode enabled) does NOT — is a property of the REAL matplotlib
renderer, not of a pure transliteration. It is exactly what axiom_check.py (G-AX)
validates against live matplotlib over boundary + 60k fuzzed integer tick sets
(including a non-vacuity witness that the default configuration misreads the
issue's ~1e8 ticks).

Per SPEC_GUIDE §4 / WORKER_PROMPT: when the impl region's observable is produced
wholly by an A-tagged callee with no DB-/library-free, input-dependent R/I
shadow, set meta.json conf_skip=true and ship this status=skip stub. Soundness is
carried instead by:
  * G-VERIFY — the spec provably forces every label to read back to its tick
    (the faithfulness `ensures`) only when both modes are off;
  * G-DIFF   — the prepatch (renderer left in its default mode) fails exactly the
    faithfulness `ensures` at both sites;
  * G-AX     — the real `ScalarFormatter` meets the `renderTicks`/`labelValue`
    axioms with both modes off (and breaks them otherwise); `LogFormatter` meets
    `renderLog_length`.
See mapping.md §3/§4 and refinement.md §C.
"""
import sys


def main():
    print("G-CONF status=skip: mwaskom__seaborn-3187 — both modeled do-blocks "
          "render legend labels via the axiomatized matplotlib tick renderer "
          "(ScalarFormatter.format_ticks / LogFormatter); the patch only flips "
          "the renderer's two shared-term abbreviation modes off "
          "(set_useOffset(False)/set_scientific(False)). The computed labels are "
          "the callee's output verbatim — the impl region is all-A-tagged with "
          "no input-dependent R/I shadow to fuzz. conf_skip=true. Soundness "
          "covered by G-VERIFY + G-DIFF + G-AX (axiom_check.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
