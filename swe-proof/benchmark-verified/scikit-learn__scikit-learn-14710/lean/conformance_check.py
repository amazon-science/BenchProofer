#!/usr/bin/env python
"""G-CONF skip stub for scikit-learn__scikit-learn-14710.

The only value transformation in `implementation_scoreEarlyStop` is the
A-reference gather `relabelTargets ls codes` (modeling
`self.classes_[codes.astype(int)]`); every other op is control-flow / state-
threading glue (`Except EarlyStopError` do-block with mutable histories, the
`isClf` and `useVal` branches, the `Option` reads of the class-label table and of
the validation arguments, the `scorer`/`shouldStop` forwards) with no standalone
Python scalar to build an R/I differential shadow from. Every R-tagged op is the
same shape — an `Option`→value read whose failure mode models the `AttributeError`
the real method would raise off-guard (`'NoneType' object has no attribute
'astype'` for a validation argument, `'HistGradientBoostingRegressor' object has
no attribute 'classes_'` for the class-label table) — and that is a control-flow
disposition, not a scalar computation, so it has no differential shadow either.
`meta.json` records `conf_skip = true`.

The A-reference gather is `Except`-valued — a code the class-label table has no
entry for is numpy's `IndexError`, modeled as `.error codeOutOfRange`, not a
stand-in label — so its "shadow" would be a refusal rather than a scalar as well.
It is validated against the real numpy fancy-index by `axiom_check.py` (G-AX)
instead, in both directions and over all three parts of the domain (front-indexed,
end-indexed, out of range). Exit with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip impl region is all-A-tagged (sole value transform is the "
          "A-reference relabelTargets, validated by G-AX); no R/I leg to "
          "differential-test")
    sys.exit(0)
