#!/usr/bin/env python3
"""G-AX executable grounding check for sphinx-doc__sphinx-10673.

This bundle has NO consumed axioms and NO deep-model references: `autoTargets`
in Solution.lean is a FREE input (the reference targets the project provides
automatically), and the modeled decision is pure list/membership logic. There is
therefore no callee contract to soundness-check in the usual G-AX sense.

What this check pins instead is the single REAL-repo fact the refinement's
R-binding (refinement.md A1 / mapping.md §2, §3) rests on: the set the patched
code computes as `generated_docnames` — the value flowing into Solution.lean's
`autoTargets` carrier — is exactly the key set of the std domain's `labels`
initial data, namely {'genindex', 'modindex', 'search'}. If that real set were
something else, the conformance oracle (driven with this set) and the F2P
scenario would be mis-grounded. We confirm it against the real repo `sphinx`
(in-container, gold patch applied) so the bijection is falsifiable, not asserted.

Imports only the repo's own `sphinx` (no test-only or instance-specific code).
Exit 0 iff the grounding holds.
"""
import sys


def check_generated_docnames():
    """The patched directive/adapter both compute `generated_docnames` from
    `self.env.domains['std'].initial_data['labels'].keys()` (and `.copy()`).
    Confirm that key set is exactly the three auto-generated reference targets
    the issue is about — the value that flows into Solution.lean's autoTargets."""
    from sphinx.domains.std import StandardDomain

    labels = StandardDomain.initial_data["labels"]
    observed = set(labels.keys())
    expected = {"genindex", "modindex", "search"}
    assert observed == expected, (
        "generated-docname grounding unsound: std domain labels keys are %r, "
        "refinement assumes %r" % (sorted(observed), sorted(expected)))

    # Each label maps to (docname, labelid, sectionname); the directive only
    # uses the KEY as a valid docname, so confirm the keys are plain strings.
    for k, v in labels.items():
        assert isinstance(k, str), "label key %r is not a str" % (k,)
        assert isinstance(v, tuple) and len(v) == 3, (
            "label value for %r is not a 3-tuple: %r" % (k, v))
    return observed


def main():
    observed = check_generated_docnames()
    print("G-AX OK: generated-docname grounding sound — std domain labels keys "
          "== %r (the autoTargets carrier; refinement R-binding mapping.md §3)."
          % (sorted(observed),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
