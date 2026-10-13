#!/usr/bin/env python3
"""G-AX for astropy__astropy-14539 — skip stub.

The bundle consumes NO unchanged-callee axiom. The modeled routine computes the
list of differing-row indices for one table column, and what the patch changes —
which of the two comparisons a column's declared format routes to — is modeled
exactly. What the enabled branch builds ON TOP of the per-row test (the row
domain `range(len(arra))`, the increasing order, the accumulation) is modeled
DEEPLY and structurally as a total function on lists of integer sequences
(`rowDiffIndices` / the `Id.run do … for … mut …` loop).

There are TWO `opaque` declarations, both standing for routines this patch does
not modify, and NEITHER carries a stated or consumed property (no
`axiom rowsAgree_prop`, no `axiom elementwiseDiff_prop`, no `sorry`):

  * `rowsAgree` — the per-row numeric closeness test
    (`np.allclose(arra[idx], arrb[idx], rtol=self.rtol, atol=self.atol)`,
    diff.py:1457 @ base_commit). The row-wise report is REQUIRED to be the set of
    rows this test does not accept, whatever it accepts, so the spec states no
    tolerance, broadcasting or magnitude property of it. The one thing named
    about it is not a property but its DOMAIN — `rowsComparable`, the pair of row
    lengths on which it answers at all — and the domain is an ARGUMENT of the
    declaration rather than an assumption about it: a caller supplies the fact,
    the test does not promise it. So there is nothing here that could be a false
    assumption smuggled into the proof; asking the test about a pair outside its
    domain is not expressible instead. The domain is measured empirically by the
    G-CONF `domain` leg all the same.
  * `elementwiseDiff` — the UNCHANGED flat element-by-element comparison used for
    ordinary fixed-shape columns, named only on the branch a variable-length
    format never takes. Its domain is an ARGUMENT in the same way
    (`rowsAreFixedShape`, the shape of column pair it has a report for: each column
    a rectangular block — the same number of stored values in every one of its rows
    — the two of the same number of rows, and the two block widths ones the flat
    comparison relates), so no property of it is stated either, and the branch that
    reaches it is entitled to consult it by the format that routed it there.
    Measured by the G-CONF `flat-domain` leg, on every non-VLA column pair its
    grammar generates and with no shape excluded.

SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed operation, and an
opaque signature with no axiom carries no contract to validate. There is
therefore no callee property to check against the real repo: where a falsification
witness needs one of these callees' values it states it as a LOCAL hypothesis of
that witness and pays for it with G-PBT's consistency probe. The R legs — the
report's shape and the comparability domain — are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "astropy__astropy-14539",
    "reason": "no consumed callee axiom: the routing decision the patch changes "
              "and the report built around the per-row test are modeled deeply, "
              "and the two opaque callees (rowsAgree, elementwiseDiff) carry no "
              "stated or consumed property — each names only the domain it "
              "answers on, as an argument the caller supplies rather than a "
              "promise, and both domains are measured by G-CONF (legs 'domain' "
              "and 'flat-domain')",
}))
sys.exit(0)
