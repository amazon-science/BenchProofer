# properties.py — PBT manifest for matplotlib__matplotlib-20676.
#
# NOT a Nagini module; a record of adversarially-reasoned falsification cases.
# The runner (swebench_nagini.pbt) parses SPEC_TESTS / AXIOM_TESTS, writes each
# `module` to a temp file, runs Nagini verify + markers.same_spec against the
# frozen model.py, and stamps RESULT. Region-surgery (we replace ONLY text
# strictly inside # impl-start / # impl-end) guarantees same_spec stays True.
#
# DEFENDED SURFACE (reasoned, not corrupted):
#   selector_initial_coords(direction: int, x_bound: Tuple[int,int],
#                           y_bound: Tuple[int,int], other_coords: Tuple[int,int])
#                           -> List[int]
#   Models SpanSelector._setup_edge_handle: the gold fix selects the initial
#   edge-marker coordinates from the orientation's CURRENT axis bound
#   (get_xbound()/get_ybound()) instead of the selector's degenerate (0,0)
#   self.extents (= the prepatch bug, abstracted by the other_coords parameter).
#
#   PRECONDITION: Requires(direction == HORIZONTAL or direction == VERTICAL).
#   Only `direction` is constrained; the three coordinate inputs are unconstrained
#   value tuples.
#
#   INPUTS are all `int` / `Tuple[int,int]` value types. Tuples are IMMUTABLE in
#   Nagini and carry NO Acc(...)/predicate permission in the Requires — there is
#   NO Acc(x,1/2) read-only mutable input, hence NOTHING to frame-mutate. The
#   frame-mutation class is therefore N/A here (see assessment); the result list
#   permission Acc(list_pred(Result())) is a PRODUCED obligation, not an input
#   frame. has_readonly_input = False.
#
#   POSTCONDITION (the load-bearing clauses):
#     (P0) Acc(list_pred(Result()))                          fresh list produced
#     (P1) len(Result()) == 2                                exactly two values
#     (P2) Implies(direction==HORIZONTAL, Result()[0]==x_bound[0]
#                                         and Result()[1]==x_bound[1])  <-- discriminator
#     (P3) Implies(direction==VERTICAL,   Result()[0]==y_bound[0]
#                                         and Result()[1]==y_bound[1])  <-- discriminator
#     (P4) ToSeq(Result()) == reported_positions(
#              selected_bound(direction, x_bound[0], x_bound[1],
#                             y_bound[0], y_bound[1]))         fold/identity form
#   P2/P3 are GROUNDED in the bound inputs (a function of the args), and the fold
#   form P4 unfolds: selected_bound is @Pure (returns PSeq(x_lo,x_hi) /
#   PSeq(y_lo,y_hi), a grounded function of the args) and reported_positions is
#   the @Pure @ContractOnly IDENTITY (Ensures(Result()==positions)). So
#   reported_positions(selected_bound(...)) == selected_bound(...) == the same
#   grounded value P2/P3 pin. There is NO ungrounded answer-key to echo: an impl
#   that "echoes" the oracle is returning the CORRECT grounded value, so the
#   ungrounded-oracle-echo class is N/A; we instead ship a grounded positive
#   control (directive-2 fallback) and an honest cheapest impl.
#
#   THE REAL BUG (prepatch / model_prepatch.py): the markers came from the
#   unrelated (0,0) extents (the other_coords parameter), NOT the orientation's
#   current bound. That fails P2/P3 — exactly the discriminating clauses. So the
#   high-value attacks are: the prepatch other_coords echo, the x<->y direction
#   swap, a partial-domain rival correct on one orientation only, an order swap
#   (does P2/P3 pin lower-then-upper, not just set-equality?), and a length break.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20676"
FLOAT_ENCODING = None   # meta.json float_encoding is null (which-value bug, not precision)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact frozen impl-region BODY of model.py (strictly INSIDE the markers,
# marker comment lines excluded). We only ever replace this body, so the spec
# regions (axioms/pure/pre/post-conditions + signatures) are never touched and
# markers.same_spec stays True for every spec case.
_IMPL = """    # Select the two endpoints of THIS orientation's current range as the
    # reported coordinate values.
    if direction == HORIZONTAL:
        result = [x_bound[0], x_bound[1]]  # type: List[int]
    else:
        result = [y_bound[0], y_bound[1]]
    # The selected values equal the orientation's range, which the
    # position-reporting component then returns unchanged.
    Assert(ToSeq(result) == selected_bound(
        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))
    Assert(reported_positions(ToSeq(result)) == ToSeq(result))
    return result"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(body: str) -> str:
    """Build a full model.py variant by replacing ONLY the impl-region body."""
    return _swap(_BASE, _IMPL, body)


SPEC_TESTS = [
    # -------------------------------------------------------------------------
    # 5. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
    # Branch reordered (handle VERTICAL first), values written one index at a
    # time into a typed local instead of a list literal. Keeps the gold framing
    # asserts (no induction needed; pure PSeq selection). MUST verify — else
    # SPEC-TOO-STRONG.
    # -------------------------------------------------------------------------
    {
        "id": "pos-control-vertical-first-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if direction == VERTICAL:\n"
            "        result = [y_bound[0], y_bound[1]]  # type: List[int]\n"
            "    else:\n"
            "        result = [x_bound[0], x_bound[1]]\n"
            "    # Same gold framing obligations (P4 fold + identity); only the\n"
            "    # branch order and not the selected values changed.\n"
            "    Assert(ToSeq(result) == selected_bound(\n"
            "        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))\n"
            "    Assert(reported_positions(ToSeq(result)) == ToSeq(result))\n"
            "    return result"
        ),
        "rationale": "a structurally-different (vertical-branch-first) but CORRECT "
                     "impl selects the same orientation bound; it must satisfy "
                     "P1/P2/P3/P4. If it cannot verify the postcondition is too "
                     "strong (SPEC-TOO-STRONG). No induction lemma — pure PSeq "
                     "selection the gold proof already uses.",
    },
    # -------------------------------------------------------------------------
    # 2 (fallback). GROUNDED POSITIVE CONTROL (in place of an ungrounded-oracle
    # echo — the oracle reported_positions(selected_bound(...)) is fully grounded
    # in the args, so its echo is the CORRECT value). Build the result by
    # appending each endpoint to a fresh typed list, re-establishing the per-
    # element framing the gold proof needs around the appends. MUST verify.
    # -------------------------------------------------------------------------
    {
        "id": "pos-control-append-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    if direction == HORIZONTAL:\n"
            "        result.append(x_bound[0])\n"
            "        result.append(x_bound[1])\n"
            "        Assert(result[0] == x_bound[0] and result[1] == x_bound[1])\n"
            "    else:\n"
            "        result.append(y_bound[0])\n"
            "        result.append(y_bound[1])\n"
            "        Assert(result[0] == y_bound[0] and result[1] == y_bound[1])\n"
            "    Assert(len(result) == 2)\n"
            "    # Same gold framing obligations (P4 fold + identity).\n"
            "    Assert(ToSeq(result) == selected_bound(\n"
            "        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))\n"
            "    Assert(reported_positions(ToSeq(result)) == ToSeq(result))\n"
            "    return result"
        ),
        "rationale": "the oracle reported_positions(selected_bound(...)) is fully "
                     "grounded, so the honest cheapest impl that materialises it is "
                     "CORRECT and must verify (directive-2 fallback; no answer-key to "
                     "echo). Built via append with the per-element pins the gold proof "
                     "uses, so any failure would be SPEC-TOO-STRONG, not a proof gap.",
    },
    # -------------------------------------------------------------------------
    # 6. ADMISSIBILITY — the F2P-shaped input (horizontal selector on a plot whose
    # x bound is the integer pair (10, 20), the test's get_xbound()) lies inside
    # the precondition (10/20 immaterial; only direction is constrained) and the
    # returned pair is exactly that bound, lower then upper. MUST verify — else
    # PRECOND-TOO-STRONG.
    # -------------------------------------------------------------------------
    {
        "id": "admiss-f2p-horizontal",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    if direction == HORIZONTAL:\n"
            "        result = [x_bound[0], x_bound[1]]  # type: List[int]\n"
            "    else:\n"
            "        result = [y_bound[0], y_bound[1]]\n"
            "    Assert(ToSeq(result) == selected_bound(\n"
            "        direction, x_bound[0], x_bound[1], y_bound[0], y_bound[1]))\n"
            "    Assert(reported_positions(ToSeq(result)) == ToSeq(result))\n"
            "    # admissibility witness: the F2P horizontal case — the reported\n"
            "    # pair is the current x bound endpoints, lower then upper.\n"
            "    if direction == HORIZONTAL:\n"
            "        Assert(result[0] == x_bound[0])\n"
            "        Assert(result[1] == x_bound[1])\n"
            "        Assert(len(result) == 2)\n"
            "    return result"
        ),
        "rationale": "the precondition (direction in {0,1}) admits the exact F2P "
                     "shape (horizontal, bound (10,20)) and the postcondition pins "
                     "the result to the x-bound endpoints in order; if the call "
                     "cannot verify, PRECOND-TOO-STRONG. F2P asserts "
                     "tool._edge_handles.positions == list(get_xbound()).",
    },
    # -------------------------------------------------------------------------
    # 3. THE REAL BUG — prepatch echo: report the unrelated coordinate pair
    # (other_coords, abstracting self.extents == (0,0)) instead of the orientation
    # bound. This is literally model_prepatch.py. expect=reject (fails P2 and P3).
    # -------------------------------------------------------------------------
    {
        "id": "reject-prepatch-other-coords",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # PREPATCH BUG: reads the unrelated (0,0) extents, not the bound.\n"
            "    result = [other_coords[0], other_coords[1]]  # type: List[int]\n"
            "    return result"
        ),
        "refinement": "this IS the pre-patch op (positions = self.extents). On the "
                      "freshly-constructed selector self.extents == (0,0); feeding "
                      "(0,0) to ToolLineHandles' axvline/axhline sets "
                      "scalex/scaley = (0 < xmin) and expands the axes to include 0, "
                      "so ax.get_xbound() changes (10,20)->(-1,21) AND "
                      "tool._edge_handles.positions == [0,0] != list(bound). Both F2P "
                      "asserts FAIL. Does NOT resolve.",
        "rationale": "violates P2 (Implies(HORIZONTAL, Result()[0]==x_bound[0] and "
                     "Result()[1]==x_bound[1])) and P3: it pins the result to "
                     "other_coords, not the orientation bound. A verify here is "
                     "SPEC-TOO-WEAK (the discriminating clause unenforced).",
    },
    # -------------------------------------------------------------------------
    # 3'. DIRECTION SWAP — selects the OTHER orientation's bound (horizontal
    # returns y_bound, vertical returns x_bound). Right shape, right grounding in
    # *a* bound, but the WRONG bound for the orientation. expect=reject (fails
    # P2 on horizontal, P3 on vertical).
    # -------------------------------------------------------------------------
    {
        "id": "reject-direction-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG: horizontal selector reads the vertical bound and vice versa.\n"
            "    if direction == HORIZONTAL:\n"
            "        result = [y_bound[0], y_bound[1]]  # type: List[int]\n"
            "    else:\n"
            "        result = [x_bound[0], x_bound[1]]\n"
            "    return result"
        ),
        "refinement": "the real faithful patch (positions = get_ybound() in the "
                      "horizontal branch) supplies the y bound (10,30) to vertical "
                      "axvlines on the horizontal selector: those x positions "
                      "(10,30) lie partly outside the x bound (10,20) -> axvline(30) "
                      "sets scalex True and expands the x axis, and "
                      "tool._edge_handles.positions == [10,30] != list(get_xbound()) "
                      "== [10,20]. Both F2P[horizontal] asserts FAIL. Does NOT resolve.",
        "rationale": "violates P2 on the horizontal sub-domain (Result()==y_bound != "
                     "x_bound) and P3 on the vertical sub-domain; a verify here is "
                     "SPEC-TOO-WEAK (P2/P3 would not bind orientation to its own bound).",
    },
    # -------------------------------------------------------------------------
    # 3''. PARTIAL-DOMAIN — correct for HORIZONTAL, but on the VERTICAL sub-domain
    # falls back to the prepatch other_coords. Passes P2 (horizontal) and the
    # horizontal F2P, but diverges exactly on the vertical orientation. expect=
    # reject (fails P3). Probes that BOTH orientations are pinned, not just one.
    # -------------------------------------------------------------------------
    {
        "id": "reject-partial-vertical-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if direction == HORIZONTAL:\n"
            "        result = [x_bound[0], x_bound[1]]  # type: List[int]\n"
            "    else:\n"
            "        # WRONG on the vertical sub-domain only: prepatch (0,0) extents.\n"
            "        result = [other_coords[0], other_coords[1]]\n"
            "    return result"
        ),
        "refinement": "fixes only the horizontal orientation (positions = "
                      "get_xbound()) but leaves the vertical branch reading "
                      "self.extents == (0,0). For a vertical SpanSelector the (0,0) "
                      "y positions sit below the y bound (10,30) -> axhline(0) "
                      "expands the y axis and tool._edge_handles.positions == [0,0] "
                      "!= list(get_ybound()). The F2P[vertical] case FAILS even "
                      "though F2P[horizontal] passes. Does NOT resolve both.",
        "rationale": "violates P3 (Implies(VERTICAL, Result()[0]==y_bound[0] and "
                     "Result()[1]==y_bound[1])) on the vertical sub-domain; a verify "
                     "here is SPEC-TOO-WEAK (only one orientation pinned).",
    },
    # -------------------------------------------------------------------------
    # ORDER SWAP (value/position pin) — selects the right orientation's bound but
    # reports the endpoints REVERSED (upper then lower). Set-equal to the bound,
    # but P2/P3 demand Result()[0]==bound[0] AND Result()[1]==bound[1] (lower then
    # upper). expect=reject. Proves P2/P3 pin ORDER, not just membership.
    # -------------------------------------------------------------------------
    {
        "id": "reject-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG ORDER: upper endpoint reported first.\n"
            "    if direction == HORIZONTAL:\n"
            "        result = [x_bound[1], x_bound[0]]  # type: List[int]\n"
            "    else:\n"
            "        result = [y_bound[1], y_bound[0]]\n"
            "    return result"
        ),
        "refinement": "the gold patch passes positions = get_xbound() == (lower, "
                      "upper) in order to ToolLineHandles, so "
                      "._edge_handles.positions == [lower, upper] == list(bound). "
                      "Reversing to [upper, lower] makes "
                      "tool._edge_handles.positions == [20,10] != list(get_xbound()) "
                      "== [10,20] (list equality is order-sensitive), so the F2P "
                      "assert `== list(bound)` FAILS. Does NOT resolve.",
        "rationale": "violates the per-index conjuncts of P2/P3 (Result()[0]==bound[0] "
                     "AND Result()[1]==bound[1]); set-equality is not enough. A verify "
                     "here would mean P2/P3 do not pin order (SPEC-TOO-WEAK).",
    },
    # -------------------------------------------------------------------------
    # LENGTH BREAK (cheap supporting near-miss) — returns three values. Violates
    # P1 (len==2) and P4 (the fold form is a 2-element PSeq). expect=reject.
    # Confirms the length clause is load-bearing.
    # -------------------------------------------------------------------------
    {
        "id": "reject-wrong-length-three",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # WRONG LENGTH: a third value appended.\n"
            "    if direction == HORIZONTAL:\n"
            "        result = [x_bound[0], x_bound[1], x_bound[0]]  # type: List[int]\n"
            "    else:\n"
            "        result = [y_bound[0], y_bound[1], y_bound[0]]\n"
            "    return result"
        ),
        "refinement": "list(get_xbound()) is exactly two elements, so a 3-element "
                      "positions list makes tool._edge_handles.positions (3 lines) "
                      "!= list(bound) (2 elements) and also drops a spurious third "
                      "edge line — the F2P `== list(bound)` assert FAILS. Does NOT "
                      "resolve. (Cheap supporting near-miss with a real refinement.)",
        "rationale": "violates P1 (len(Result())==2) and P4 (the 2-element fold form). "
                     "A verify here would mean the length is unconstrained (SPEC-TOO-WEAK).",
    },
]


# axiom_check.py source, read on the HOST at load time and embedded into the
# soundness probe (the runner mounts ONLY the probe at /work, so model.py /
# axiom_check.py are NOT in-container — directive 6). The embedded oracle CALLS
# the real ToolLineHandles / SpanSelector, never scrapes source (directive 4),
# and runs headless Agg with utf-8 reads (directive 5).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


AXIOM_TESTS = [
    # -------------------------------------------------------------------------
    # reported_positions is the ONE @ContractOnly deep model (A-reference): the
    # IDENTITY reported_positions(P) == P, modeling that the real
    # matplotlib.widgets.ToolLineHandles reports the supplied positions back
    # unchanged (axvline(p)/axhline(p) -> get_xdata()/get_ydata()[0] == p).
    #
    # AXIOM-SOUNDNESS: run the REAL ToolLineHandles on boundary + 2000 fuzz
    # position pairs x2 directions and assert .positions == list(positions); plus
    # the end-to-end discriminator (interactive SpanSelector leaves the bound
    # unchanged with markers on the orientation bound, and the prepatch (0,0)
    # DOES expand it). This reuses axiom_check.py verbatim (the bundle's audited
    # G-AX oracle) — strongest available soundness witness. apply_gold=True (the
    # end-to-end / discriminator sub-checks require the gold fix; the identity
    # sub-check is patch-independent, per meta G-AX note).
    # -------------------------------------------------------------------------
    {
        "id": "ax-sound-reported-positions-identity",
        "axiom": "reported_positions",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the A-reference deep model reported_positions(P)==P must equal "
                     "the real ToolLineHandles report-back on every caller-reachable "
                     "position pair. axiom_check.py executes the real callee over 8 "
                     "boundary + 2000 fuzz pairs x2 directions and asserts "
                     ".positions == list(positions); a single mismatch is AXIOM-UNSOUND. "
                     "It also reproduces the bound-invariance discriminator and the "
                     "prepatch (0,0) expansion. Exit 0 iff sound.",
    },
    # -------------------------------------------------------------------------
    # AXIOM-CONTAINMENT: the model can only ever pass reported_positions a value
    # produced by selected_bound(direction, x_lo, x_hi, y_lo, y_hi) — i.e. a
    # 2-element PSeq of coordinate values (one orientation's [lo, hi]). The real
    # ToolLineHandles.positions Requires domain is "any finite sequence of numeric
    # positions" (it builds one axvline/axhline per element with no length or
    # value restriction). Every caller-reachable input (a length-2 numeric pair)
    # lies inside that domain; coverage is broader-than-reached (ToolLineHandles
    # accepts other lengths too), which is SOUND (float-vs-int rule). A reachable
    # input the callee rejects would be AXIOM-TOO-WEAK-FOR-CALLER — none exists.
    # The probe ENUMERATES the exact caller-reachable shapes (the F2P bound pairs
    # and fuzz length-2 pairs) and asserts the real callee accepts each and
    # returns them unchanged (containment witnessed by acceptance + identity).
    # -------------------------------------------------------------------------
    {
        "id": "ax-contain-reported-positions-domain",
        "axiom": "reported_positions",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys, random\n"
            "try:\n"
            "    import matplotlib\n"
            "    matplotlib.use('Agg')\n"
            "    import matplotlib.pyplot as plt\n"
            "    from matplotlib.widgets import ToolLineHandles\n"
            "except Exception as e:\n"
            "    print('cannot import matplotlib:', e); sys.exit(1)\n"
            "\n"
            "# The model passes reported_positions ONLY a value of selected_bound(): a\n"
            "# 2-element numeric pair = one orientation's [lo, hi]. Enumerate exactly\n"
            "# the caller-reachable 2-pairs (F2P integer bound + fuzz) and assert the\n"
            "# real ToolLineHandles accepts each (in its Requires domain) and reports\n"
            "# it back unchanged (containment witnessed by acceptance + identity).\n"
            "reached = [(10, 20), (10, 30), (0, 0), (-5, 5), (10, 10), (20, 10),\n"
            "           (10.5, 11.5), (-1.25, 3.75)]\n"
            "rng = random.Random(20676)\n"
            "for _ in range(200):\n"
            "    reached.append((rng.uniform(-1000, 1000), rng.uniform(-1000, 1000)))\n"
            "ok = True\n"
            "for direction in ('horizontal', 'vertical'):\n"
            "    for pair in reached:\n"
            "        assert len(pair) == 2, 'model only ever passes a 2-element pair'\n"
            "        fig, ax = plt.subplots(1, 1)\n"
            "        try:\n"
            "            try:\n"
            "                handles = ToolLineHandles(ax, pair, direction)\n"
            "            except Exception as e:\n"
            "                print('FAIL: caller-reachable pair %r (%s) OUTSIDE the '\n"
            "                      'callee domain: %s' % (pair, direction, e))\n"
            "                ok = False\n"
            "                continue\n"
            "            observed = handles.positions\n"
            "            if observed != list(pair):\n"
            "                print('FAIL: containment/identity mismatch %r -> %r '\n"
            "                      '(%s)' % (pair, observed, direction))\n"
            "                ok = False\n"
            "        finally:\n"
            "            plt.close(fig)\n"
            "if not ok:\n"
            "    sys.exit(1)\n"
            "print('AX-CONTAIN OK: every caller-reachable 2-element coordinate pair '\n"
            "      '(F2P bound + 200 fuzz x2 directions) lies in the ToolLineHandles '\n"
            "      'positions Requires domain and is reported back unchanged; coverage '\n"
            "      'is broader-than-reached (callee also accepts other lengths) - SOUND.')\n"
            "sys.exit(0)\n"
        ),
        "rationale": "containment, not whole-domain coverage: the model only ever "
                     "passes reported_positions a 2-element numeric pair (a value of "
                     "selected_bound). Every such caller-reachable input lies inside "
                     "the real ToolLineHandles.positions domain (it accepts any finite "
                     "numeric sequence). A reachable input the callee rejected would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists. Broader callee coverage "
                     "is sound (float-vs-int rule).",
    },
]
