"""properties.py — G-PBT falsification battery for django__django-14855 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct getAdminUrl`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (``getAdminUrl (viewName pk appName objLabel) return (out)``).
The display for a related-object reference shown on a page carrying a named
application context: the target address is resolved WITHIN that context and, on
success, shown as a hyperlink captioned with the object's label; on failure the
bare label is shown. Four input binders — ``viewName``, ``pk``, ``appName``,
``objLabel`` — and a SINGLE load-bearing postcondition clause:

    (Q) out = render (resolveAddress viewName pk (some appName)) objLabel

The method has NO ``require`` clause; the admitted input domain is total.

CARRIER — ``resolveAddress`` is an OPAQUE axiom (``List Char → List Char →
Option (List Char) → Option (List Char)``) with NO constraining axiom: its value
at any concrete input is unknown to the kernel. That is what makes the surface
faithful (no concrete address is pinned), and it dictates HOW a witness is
stated here — not whether one exists.

  ATTACKING AN OPAQUE CALLEE (the technique this battery rests on, corrected by
  audit). An earlier pass recorded the whole context facet and the whole
  branch facet as "undiscriminable, no witness can be built". That was WRONG and
  is now measured wrong: nothing requires a witness to COMPUTE the opaque term.
  A witness states its refutation at a point described by HYPOTHESIS — e.g.
  ``(hDefault : resolveAddress ['v'] ['k'] none = some ['a'])`` paired with
  ``(hCtx : resolveAddress ['v'] ['k'] (some ['n']) = some ['b'])`` — and the
  gate's own consistency probe then confirms those hypotheses are jointly
  satisfiable, which an opaque term makes easy precisely BECAUSE no tactic can
  derive ``False`` from them. Under those hypotheses ``simp only [… , hDefault,
  hCtx]`` rewrites both sides to concrete constructors and the refutation
  closes by injection. Measured on the real verifier for every reject case
  below: rival exit 0, gold exit 1, probe exit 1 (probe FAILING is the pass —
  the hypotheses are consistent).

THREE facets of Q are therefore attacked, not one:

  * CONTEXT (the reported bug's own shape, and the load-bearing half of Q). Q
    pins the address to the resolution performed within ``some appName``. A rival
    resolving within any OTHER context — the ambient default ``none``, or another
    name — is refuted at a hypothesised point where the two contexts resolve to
    different addresses. This is the facet a previous pass omitted; it is now
    ported (``weak-context-default``, ``weak-context-route``).
  * BRANCH/STRUCTURE. A rival that always returns the ``plain`` shape (never a
    link) is refuted at a hypothesised point where the context resolves to
    ``some`` (``weak-always-plain``). Also previously and wrongly omitted.
  * CAPTION. ``render`` uses its label argument as the caption in BOTH arms, so
    whatever the address turns out to be, the display's label is ``objLabel``. A
    rival captioning with anything else contradicts Q for EVERY value of the
    address, and the contradiction closes by a case-split that never evaluates
    the resolver — so these two need no hypothesis at all.

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    carries mandatory framing rivals (write back into the read-only ``names`` /
    ``prefixes`` registry) because those inputs are held at a fractional heap
    permission ``Acc(list_pred(...),1/2)`` an impl can illegally overwrite. Lean
    and Velvet are referentially transparent: the four inputs are immutable
    values, this bundle declares NO ``mut`` binder, there is no heap and no
    aliasing — so there is no read-only input to mutate and no substitute probe
    to build. Not fabricated (per the porting map, this class is vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. Q pins ``out`` to
    ``render (resolveAddress …) objLabel``; the caption half is grounded in the
    input ``objLabel`` and the address half is the opaque resolver's own value
    (validated executably by G-AX, not an answer-key an impl could echo). The
    only value satisfying Q is the honest one, so the positive control is the
    cheapest faithful reshape, not a wrong echo.
  * PARTIAL-DOMAIN / WRONG-CONTEXT rivals (the heart of nagini's battery — the
    pre-patch missing context, the wrong-selector default) — PORTED, by
    hypothesis-placed witnesses (see above). Both nagini context rivals map onto
    ``weak-context-default`` (resolve within the ambient default) and
    ``weak-context-route`` (resolve within some other name).
  * CAPTION rivals — the resolver-independent slice. Two reject rivals attack
    Q's caption at two different input points, each refuted by a case-split on
    the opaque address that never evaluates it.

WITNESS PLACEMENT. ``extract_program_for`` is DEAD here: the method depends on
the opaque ``resolveAddress`` so it is ``noncomputable`` and the extracted
``…Exec`` fails the compiler IR check (verified empirically). Each witness
therefore reaches Q DIRECTLY, over the method's own ``.run`` (which reduces to
``match resolveAddress … with | some a => pure … | none => pure …``). The two
CAPTION witnesses case-split the opaque address and contradict the caption in
BOTH arms without touching the resolver's value; the three CONTEXT/BRANCH
witnesses instead pin the resolver at a hypothesised point (consistency-probed)
and close by injection on concrete constructors. Across the five reject
witnesses all four binders move (``['v','k','n','L']``, ``['p','q','r','x','y']``,
``['s','t','u','Z']``, ``['m','i','c','T']``), and the values are chosen so the
hypothesised resolutions DIFFER between the rival's context and Q's.
"""
from pathlib import Path

INSTANCE = "django__django-14855"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the three comment lines
# ---- and the `match`). It lies wholly inside the single
# ---- -- impl-start / -- impl-end region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so each edit keeps same_spec by
# ---- construction and leaves the frozen `prove_correct getAdminUrl` statement
# ---- intact.
_IMPL = (
    "    -- Resolve the route within the page's own application context, then display\n"
    "    -- the resolved address as a captioned hyperlink, or the bare label if the\n"
    "    -- route does not resolve.\n"
    "    match resolveAddress viewName pk (some appName) with\n"
    "    | some a => return Rendered.link a objLabel\n"
    "    | none   => return Rendered.plain objLabel"
)
assert _BASE.count(_IMPL) == 1, "getAdminUrl impl region drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header survives), so a positive control that
# ---- reshapes the impl may retune its tactic script without touching the spec
# ---- or dropping the obligation.
_PROOF = (
    "prove_correct getAdminUrl by\n"
    "  loom_solve\n"
    "  all_goals simp_all [render]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY getAdminUrl's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_and_proof(new_impl, new_proof):
    """Reshape the impl AND retune the (elided) tactic body for the new shape."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Ports the nagini
    # `pos-inline-selector` ARGUMENT ("a faithful, structurally-different
    # correct impl is not rejected") onto this carrier: instead of matching on
    # the resolver result and returning the two display shapes inline, bind the
    # resolved address to a local and hand it to `render` directly — the pure
    # spec function itself. Observationally identical to the frozen impl on both
    # legs, so Q discharges; the reproof collapses to `loom_solve` (the trailing
    # `simp_all [render]` is then a no-op and dropped). Verified EXIT 0.
    # =====================================================================
    {
        "id": "pos-render-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_and_proof(
            "    -- Resolve within the page's own context and hand the outcome to\n"
            "    -- the display function directly.\n"
            "    let addr := resolveAddress viewName pk (some appName)\n"
            "    return render addr objLabel",
            "prove_correct getAdminUrl by\n"
            "  loom_solve"),
        "rationale": "PASS SOURCE = Q. Binding the resolved address to a local "
                     "and returning `render addr objLabel` (the pure spec "
                     "function) instead of matching-and-returning the two shapes "
                     "inline is observationally identical to gold on both legs, "
                     "so `out = render (resolveAddress viewName pk (some "
                     "appName)) objLabel` still discharges. A structurally "
                     "different faithful reshape MUST verify; if it cannot, the "
                     "postcondition over-constrains the display shape "
                     "(SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG) — landed by audit; the earlier pass
    # dropped this lane as "vacuous because the method has no `require`". That
    # reason is wrong on a total carrier: the analogue is the obligation being
    # UNSATISFIABLE at exactly an F2P-shaped input. Q's post-image demands a
    # display whose address half is the resolution WITHIN the page's own context;
    # at the F2P-shaped point (a page carrying a named context, a route that
    # resolves there) the demanded value must actually EXIST, on both legs of the
    # resolution outcome. This case discharges that at the concrete input as two
    # `have`s BEFORE closing the frozen obligation verbatim — impl region byte
    # -identical to gold, only the (elided) tactic body extended, so the
    # obligation statement is untouched. Verified EXIT 0.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct getAdminUrl by\n"
            "  have hResolves : ∀ a : List Char,\n"
            "      resolveAddress ['v'] ['k'] (some ['n']) = some a →\n"
            "      render (resolveAddress ['v'] ['k'] (some ['n'])) ['L']"
            " = Rendered.link a ['L'] := by\n"
            "    intro a h; simp [render, h]\n"
            "  have hFallback :\n"
            "      resolveAddress ['v'] ['k'] (some ['n']) = none →\n"
            "      render (resolveAddress ['v'] ['k'] (some ['n'])) ['L']"
            " = Rendered.plain ['L'] := by\n"
            "    intro h; simp [render, h]\n"
            "  clear hResolves hFallback\n"
            "  loom_solve\n"
            "  all_goals simp_all [render]"),
        "rationale": "the post-image of Q must be SATISFIABLE at an F2P-shaped "
                     "point — a page carrying a named application context "
                     "(appName=['n']), a route+key identifying the target "
                     "(['v'],['k']), and an object label (['L']). Both `have`s "
                     "exhibit the demanded display at that concrete input, one "
                     "per leg of the resolution outcome: when the route resolves "
                     "within that context the demanded value is the captioned "
                     "hyperlink to THAT address, and when it does not the "
                     "demanded value is the bare label. Neither is vacuous and "
                     "neither is `False`-derived, so Q is jointly satisfiable "
                     "exactly where the failing example lives, and the frozen "
                     "obligation then closes verbatim. If this FAILED, Q would "
                     "be unsatisfiable at the very input the fix is about "
                     "(PRECOND-TOO-STRONG on a total carrier).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input. THREE facets of Q are attacked: the CONTEXT the address is
    # resolved within (the load-bearing half), the BRANCH the outcome selects,
    # and the CAPTION. The context/branch witnesses pin the opaque resolver by
    # HYPOTHESIS (consistency-probed by the gate); the caption witnesses need no
    # hypothesis at all. See the module docstring.
    # =====================================================================

    # ---- caption must be `objLabel`, not another input ----
    {
        "id": "weak-caption-viewname",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolves within the correct context (the resolver call is byte-for-byte
        # gold), and dispatches the correct display SHAPE on each leg, but
        # captions with `viewName` instead of `objLabel`. Right on the resolution
        # and the branch, wrong on the caption — a pure attack on Q's label half
        # and on the `objLabel` binder.
        "module": _impl(
            "    match resolveAddress viewName pk (some appName) with\n"
            "    | some a => return Rendered.link a viewName\n"
            "    | none   => return Rendered.plain viewName"),
        "refinement": "a faithful counterpart that captions the produced display "
                      "with the route identifier rather than the object's label "
                      "renders text no failing assertion expects: the failing "
                      "example pins the visible caption to the object's own "
                      "label, so with the route identifier substituted the "
                      "rendered fragment no longer matches and the test stays "
                      "RED. It would NOT resolve.",
        "rationale": "REJECT from Q (out = render (resolveAddress …) objLabel): "
                     "`render` captions with `objLabel` in BOTH arms, so the "
                     "returned display's label must be `objLabel`; the rival's "
                     "label is `viewName`. Refuted at viewName=['v'], objLabel="
                     "['L'] (v ≠ L) by a case-split on the opaque address whose "
                     "both arms contradict the caption without evaluating the "
                     "resolver.",
        "witness":
            "example :\n"
            "    (getAdminUrl ['v'] ['k'] ['n'] ['L']).run\n"
            "      ≠ DivM.res (render (resolveAddress ['v'] ['k'] (some ['n'])) ['L']) := by\n"
            "  simp only [getAdminUrl, render]\n"
            "  cases hr : resolveAddress ['v'] ['k'] (some ['n']) with\n"
            "  | some x => intro heq; injection heq with h1; injection h1 with _ h2; simp at h2\n"
            "  | none => intro heq; injection heq with h1; injection h1 with h2; simp at h2\n",
    },

    # ---- caption must be the ACTUAL objLabel, not a fixed constant ----
    {
        "id": "weak-caption-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolver call and display shape are gold, but the caption is a fixed
        # empty label, ignoring `objLabel` entirely. A wrong-CONTENT attack on Q
        # distinct from the viewName rival (which mis-routes to another input):
        # here the label is a constant, so it is wrong for every non-empty
        # `objLabel`. Refuted at a two-character label so `objLabel` moves to a
        # value the other witness does not use.
        "module": _impl(
            "    match resolveAddress viewName pk (some appName) with\n"
            "    | some a => return Rendered.link a []\n"
            "    | none   => return Rendered.plain []"),
        "refinement": "a faithful counterpart that hardcodes an empty caption "
                      "drops the object's label from the rendered display "
                      "entirely, so every failing assertion pinning the visible "
                      "caption to the object's label observes an empty caption "
                      "instead and stays RED. It would NOT resolve.",
        "rationale": "REJECT from Q (out = render (resolveAddress …) objLabel): "
                     "the display's caption must equal the input `objLabel` in "
                     "both arms; the rival hardcodes the empty label. Refuted at "
                     "objLabel=['x','y'] (≠ []) by a case-split on the opaque "
                     "address whose both arms contradict the caption without "
                     "evaluating the resolver.",
        "witness":
            "example :\n"
            "    (getAdminUrl ['p'] ['q'] ['r'] ['x','y']).run\n"
            "      ≠ DivM.res (render (resolveAddress ['p'] ['q'] (some ['r'])) ['x','y']) := by\n"
            "  simp only [getAdminUrl, render]\n"
            "  cases hr : resolveAddress ['p'] ['q'] (some ['r']) with\n"
            "  | some x => intro heq; injection heq with h1; injection h1 with _ h2; simp at h2\n"
            "  | none => intro heq; injection heq with h1; injection h1 with h2; simp at h2\n",
    },

    # ---- the address must be resolved WITHIN the page's own context ----
    # The central rival of the sibling battery, and the one an earlier pass wrongly
    # recorded as impossible to witness here. Resolves within the ambient default
    # (context `none`) instead of the page's own named context: byte-for-byte gold
    # on the caption AND on the display shape, wrong only on the context. Refuted
    # at a hypothesised point where the two contexts resolve to DIFFERENT
    # addresses — which is a satisfiable hypothesis precisely because the resolver
    # is opaque (the gate's consistency probe confirms it; measured exit 1 = no
    # `False` derivable). Audited: rival 0, gold 1, probe 1; the type-revealing
    # variant prints `['a'] = ['b']` on the rival and `['b'] = ['b']` on gold, so
    # gold's exit code tracks the claim.
    {
        "id": "weak-context-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    match resolveAddress viewName pk none with\n"
            "    | some a => return Rendered.link a objLabel\n"
            "    | none   => return Rendered.plain objLabel"),
        "refinement": "a faithful counterpart that resolves the target address "
                      "without the page's own application context resolves it "
                      "within the ambient default instead, so a page served under "
                      "a NON-default context emits an address belonging to the "
                      "default one. The failing example renders under exactly such "
                      "a non-default context and pins the emitted address to that "
                      "context's own; with the default's address substituted the "
                      "assertion does not match and the test stays RED. It would "
                      "NOT resolve.",
        "rationale": "REJECT from Q (out = render (resolveAddress viewName pk "
                     "(some appName)) objLabel): Q pins the address to the "
                     "resolution performed within `some appName`, and the rival "
                     "performs it within `none`. Refuted at viewName=['v'], "
                     "pk=['k'], appName=['n'], objLabel=['L'] under the "
                     "satisfiable hypotheses that the default context resolves to "
                     "['a'] and the page's own context resolves to ['b']: the "
                     "rival's display then carries address ['a'] where Q demands "
                     "['b']. If it VERIFIED, Q would not enforce WHICH context the "
                     "address is resolved within — SPEC-TOO-WEAK on the sole "
                     "load-bearing clause.",
        "witness":
            "example (hDefault : resolveAddress ['v'] ['k'] none = some ['a'])\n"
            "    (hCtx : resolveAddress ['v'] ['k'] (some ['n']) = some ['b']) :\n"
            "    (getAdminUrl ['v'] ['k'] ['n'] ['L']).run\n"
            "      ≠ DivM.res (render (resolveAddress ['v'] ['k'] (some ['n'])) ['L']) := by\n"
            "  simp only [getAdminUrl, render, hDefault, hCtx]\n"
            "  intro heq\n"
            "  injection heq with e1\n"
            "  injection e1 with ea _\n"
            "  simp at ea\n",
    },

    # ---- ...and within THAT context, not merely within SOME named one ----
    # The dual of the sibling's wrong-selector rival: the rival does pass a named
    # context, so `some`-vs-`none` is not what is wrong; it passes the WRONG name
    # (the route identifier). This probes that Q checks WHICH name the context
    # carries, not merely that a name is supplied. Audited: rival 0, gold 1,
    # probe 1.
    {
        "id": "weak-context-route",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    match resolveAddress viewName pk (some viewName) with\n"
            "    | some a => return Rendered.link a objLabel\n"
            "    | none   => return Rendered.plain objLabel"),
        "refinement": "a faithful counterpart that resolves within a context "
                      "named by the route identifier rather than by the page's own "
                      "application context emits, on any page whose context name "
                      "differs from that identifier, an address belonging to some "
                      "other context. The failing example's page carries its own "
                      "context name and pins the emitted address to it, so the "
                      "assertion does not match and the test stays RED. It would "
                      "NOT resolve.",
        "rationale": "REJECT from Q: the context argument must be `some appName`, "
                     "the page's own; the rival passes `some viewName`. Refuted at "
                     "viewName=['m'], pk=['i'], appName=['c'], objLabel=['T'] "
                     "under the satisfiable hypotheses that context ['m'] resolves "
                     "to ['1'] while context ['c'] resolves to ['2']. Distinct "
                     "from weak-context-default: this rival DOES supply a named "
                     "context, so passing it would mean Q constrains only that "
                     "SOME name is supplied, not which — SPEC-TOO-WEAK.",
        "witness":
            "example (hOther : resolveAddress ['m'] ['i'] (some ['m']) = some ['1'])\n"
            "    (hCtx : resolveAddress ['m'] ['i'] (some ['c']) = some ['2']) :\n"
            "    (getAdminUrl ['m'] ['i'] ['c'] ['T']).run\n"
            "      ≠ DivM.res (render (resolveAddress ['m'] ['i'] (some ['c'])) ['T']) := by\n"
            "  simp only [getAdminUrl, render, hOther, hCtx]\n"
            "  intro heq\n"
            "  injection heq with e1\n"
            "  injection e1 with ea _\n"
            "  simp at ea\n",
    },

    # ---- the display SHAPE must follow the resolution outcome ----
    # The BRANCH facet, also wrongly recorded as undiscriminable by an earlier
    # pass. The rival never links: it returns the bare-label shape unconditionally,
    # which is correct on the leg where nothing resolves and wrong on the leg where
    # something does. Refuted at a hypothesised point on the resolving leg.
    # Audited: rival 0, gold 1, probe 1; the type-revealing variant prints
    # `Rendered.plain ['Z'] = Rendered.link ['w'] ['Z']` on the rival against
    # `Rendered.link ['w'] ['Z'] = Rendered.link ['w'] ['Z']` on gold.
    {
        "id": "weak-always-plain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return Rendered.plain objLabel"),
        "refinement": "a faithful counterpart that always shows the bare label "
                      "never emits a hyperlink at all, so a related-object "
                      "reference whose target does resolve is displayed as plain "
                      "text. The failing example asserts a hyperlink is present "
                      "and carries a particular address, so with no hyperlink "
                      "emitted it stays RED. It would NOT resolve.",
        "rationale": "REJECT from Q (out = render (resolveAddress …) objLabel): "
                     "`render` returns the `link` shape on the resolving leg, so "
                     "an impl that always returns `plain` contradicts Q wherever "
                     "the address resolves. Refuted at viewName=['s'], pk=['t'], "
                     "appName=['u'], objLabel=['Z'] under the satisfiable "
                     "hypothesis that the resolution within ['u'] yields ['w']: Q "
                     "then demands the captioned hyperlink and the rival returns "
                     "the bare label. Attacks the branch/shape facet no caption "
                     "rival touches (both of those keep gold's shape dispatch). If "
                     "it VERIFIED, Q would not force the display shape to follow "
                     "the resolution outcome — SPEC-TOO-WEAK.",
        "witness":
            "example (hRes : resolveAddress ['s'] ['t'] (some ['u']) = some ['w']) :\n"
            "    (getAdminUrl ['s'] ['t'] ['u'] ['Z']).run\n"
            "      ≠ DivM.res (render (resolveAddress ['s'] ['t'] (some ['u'])) ['Z']) := by\n"
            "  simp only [getAdminUrl, render, hRes]\n"
            "  intro heq\n"
            "  injection heq with e1\n"
            "  simp at e1\n",
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 7 SPEC cases (1
# soundness positive, 1 admissibility, 2 frame-mutation, 3 uniqueness rivals)
# plus 2 AXIOM_TESTS. This bundle models the SAME single operation (render the
# related-object link, resolving within the page's application context) over an
# OPAQUE resolver carrier. An earlier pass concluded the context and branch
# attacks "collapse" on that carrier and shipped 3 cases; an AUDIT re-derived
# them with real builds and found they do NOT collapse — a witness may pin the
# opaque resolver by HYPOTHESIS rather than compute it. Four cases were added.
# Every sibling case is accounted for below.
#
#   sibling case (nagini)        -> here
#   -----------------------------------------------------------------------
#   pos-inline-selector          -> pos-render-direct              PORTED
#   admiss-reads                 -> admiss-f2p-shaped-point        RE-AIMED
#   frame-mut-names              -> (none)                         VACUOUS
#   frame-mut-prefixes           -> (none)                         VACUOUS
#   weak-no-selector             -> weak-context-default           PORTED
#   weak-default-selector        -> weak-context-route             PORTED
#   weak-return-default          -> weak-context-default (merged)  PORTED
#   AXIOM_TESTS (x2)             -> (none)                         DROPPED
#
# ADDED (3, no direct sibling counterpart). The sibling has NO caption and no
# link/plain shape in its model (its result is the URL prefix, a scalar), so
# these have no exact counterpart; they attack the two facets of Q the sibling's
# scalar carrier cannot express:
#   weak-caption-viewname  — captions with `viewName` (a wrong INPUT); attacks
#       Q's label half and the `objLabel` binder at objLabel=['L'].
#   weak-caption-constant  — captions with a fixed empty label (a wrong
#       CONSTANT, ignoring `objLabel`); wrong-content dual, at objLabel=['x','y'].
#   weak-always-plain      — never emits the hyperlink shape; attacks the BRANCH
#       facet (which display shape the resolution outcome selects).
#
# CORRECTED (audit). Three claims the earlier pass recorded as carrier collapse
# were re-derived with the real verifier and are FALSE; the cases they excused
# are now shipped:
#   * "the wrong-context rivals are undiscriminable because
#     `resolveAddress vn pk (some an) ≠ resolveAddress vn pk <other>` is not a
#     theorem at any concrete input." The disequality does not need to be a
#     THEOREM — it is a HYPOTHESIS of the witness, and the gate's consistency
#     probe then confirms it is satisfiable, which the opacity makes easy for
#     exactly the reason the earlier pass mistook for a wall: no tactic can
#     derive `False` from it either. Measured: probe exit 1 (consistent),
#     rival exit 0, gold exit 1, for both weak-context-default and
#     weak-context-route.
#   * "the branch facet is undiscriminable; the residual goal after case-
#     splitting the opaque term is unsolved for that leg." True of a witness that
#     case-splits, which is why weak-always-plain does not case-split: it pins the
#     resolving leg by hypothesis instead. Measured: rival 0, gold 1, probe 1.
#   * "no admissibility case remains, because the method has no `require` and the
#     frozen `prove_correct` already verifies." The second half is the analogue
#     that matters on a total carrier and it is not vacuous: it asks whether Q's
#     post-image is satisfiable AT AN F2P-SHAPED INPUT, which a positive
#     discharging the demanded value at that concrete point by `have` tests
#     directly (admiss-f2p-shaped-point). "The gold impl verifies" attests to
#     satisfiability universally-quantified over the binders; it does not exhibit
#     the demanded display at the failing example's own shape, on each leg of the
#     resolution outcome, which is what the sibling lane checks.
#
# VACUOUS (frame / permission-mutation): nagini's frame-mut-names /
#   frame-mut-prefixes rely on a fractional heap permission an impl can
#   overwrite (`Acc(list_pred(names),1/2)` / `Acc(list_pred(prefixes),1/2)`).
#   This backend is referentially transparent and this bundle declares no `mut`
#   PARAMETER — all four inputs are immutable values with no heap footprint — so
#   there is no read-only input to overwrite and no substitute probe to build.
#   No permission probe fabricated.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   `resolveAddress` == the real `reverse`, incl. that the context genuinely
#   changes the result) and this gate ignores AXIOM_TESTS regardless.
#
# COVERAGE. The sole obligation (`prove_correct getAdminUrl`) is defended
# (pos-render-direct), shown satisfiable at an F2P-shaped point
# (admiss-f2p-shaped-point), and attacked on all three facets of Q: the CONTEXT
# the address is resolved within (weak-context-default, weak-context-route), the
# display SHAPE the outcome selects (weak-always-plain), and the CAPTION
# (weak-caption-viewname, weak-caption-constant). All four binders move across
# the five reject witnesses — ['v','k','n','L'] / ['p','q','r','x','y'] /
# ['s','t','u','Z'] / ['m','i','c','T'] — and the movement is MEANINGFUL rather
# than two spellings of one point: `appName` in particular changes the spec's
# verdict, since the context rivals are refuted precisely by the hypothesised
# resolutions under two DIFFERENT context values differing. `viewName` is
# load-bearing in two directions (as Q's route argument in weak-context-route, as
# a wrong caption in weak-caption-viewname).
#
# NOT PORTED: the divergence lane. Under
# `set_option loom.semantics.termination "total"`, which this bundle carries, a
# non-terminating impl is REJECTED rather than verifying vacuously: a postcondition
# is claimed of ALL runs and every loop owes a measure that STRICTLY DECREASES. An
# earlier version of this note had it backwards, calling vacuous verification a
# KNOWN spec hole of the backend measured across a `partial` cohort; that is
# withdrawn, all 500 velvet bundles set `"total"`. There is nothing for this
# battery to ship in the lane, because a reject case needs a witness that
# elaborates against the rival and a diverging rival's module does not compile.
AXIOM_TESTS = []
