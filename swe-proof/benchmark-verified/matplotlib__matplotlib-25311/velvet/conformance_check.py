#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-25311 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`initHandler`) is the constructor of the drag-interaction
base class `DraggableBase.__init__` (lib/matplotlib/offsetbox.py:1503). The gold
fix is purely STRUCTURAL:

    -        self.canvas = self.ref_artist.figure.canvas   # buggy: stores the
                                                           #   live GUI canvas in
                                                           #   the instance __dict__
    +    # A property, not an attribute, to maintain picklability.
    +    canvas = property(lambda self: self.ref_artist.figure.canvas)

i.e. stop persisting the (non-serializable) rendering surface as an instance
attribute, and expose it instead as a class-level derived property over the
already-stored `self.ref_artist`.

The changed op's only observable is whether a reference to the backend canvas
ends up in the object's *pickle stream*. That observable is NOT reproducible as a
pure, input-dependent R/I shadow this gate can fuzz over >=1e5 inputs:

  * It materializes only after a full matplotlib figure with a
    `legend(draggable=True)` has been built and pickled — exactly the F2P test
    `test_complete[png]`, whose assertion is
    `"FigureCanvasAgg" not in [arg for op,arg,pos in pickletools.genops(pkl)]`.
    Standing that up requires the Agg backend, a real Figure/Axes/Legend object
    graph, a draggable handler, and `pickle.dumps` + `pickletools.genops` — an
    integration scenario, not a transliteration fuzzable over a value domain.
  * The construction itself is constant with respect to any fuzzable repo input:
    `initHandler` builds a fixed-shape persisted state (reference handle + flags
    + registrations, NO surface) regardless of `use_blit`/`supports_blit` beyond
    which boolean flag bit is stored. There is no input-dependent computation to
    differential-test; diffing constants carries no information.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the impl region is a deep object-state
construction with no DB/GUI-free, input-dependent R/I shadow, set
meta.json conf_skip=true and ship this status=skip stub. Soundness of the modeled
construction is carried instead by:
  * G-VERIFY — the spec provably forces `persistable out` (no surface in the
    persisted state) AND `surfaceReachable out` (surface obtainable from the
    retained reference) on return;
  * G-DIFF — `Solution_prepatch.lean`, which stores the surface directly, fails
    exactly the `persistable out` clause (goal reduces to `False`);
  * G-RESOLVE — the gold patch (patch.diff) makes the harness `resolved`.
See mapping.md §5 and refinement.md §C. This mirrors the django__django-11179
state-construction precedent (conf_skip=true).
"""
import sys


def main():
    print("G-CONF status=skip: matplotlib__matplotlib-25311 — the modeled "
          "do-block constructs a drag-handler's persisted object state "
          "(DraggableBase.__init__); the structural fix (stop storing the live "
          "GUI canvas as an instance attribute, expose it via a derived "
          "property) has its sole observable in a real pickle stream built only "
          "inside the F2P integration test, with no input-dependent R/I shadow "
          "to fuzz. conf_skip=true. Soundness covered by G-VERIFY + G-DIFF + "
          "G-RESOLVE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
