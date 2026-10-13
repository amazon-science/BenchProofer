"""properties.py — G-PBT falsification battery for sympy__sympy-19346 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
both ``prove_correct`` obligations survive with byte-identical headers) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness ELABORATES against the rival and FAILS against the
frozen solution).

DEFENDED SURFACE (two contracted methods over one read-only sequence input each):

  printDict (items : List (Obj × Obj)) return (out : List Char)
      ensures out = dictRender items
  printSet  (elems : List Obj)         return (out : List Char)
      ensures out = setRender elems

Each ``Obj`` carries two textual forms: ``reprText`` (the text the RECURSIVE
element renderer produces — the faithful choice) and ``strText`` (the shallow
textual form — the pre-change fallback). The two methods assemble the supported
rendering of a mapping / a collection of already-rendered elements. The two
load-bearing ``ensures`` pin each result to a fully-unfolded pure model of the
inputs:

  ``dictRender items = "{" ++ joinComma (items.map kvText) ++ "}"``
  ``kvText p = doprint p.1 ++ ": " ++ doprint p.2``   (``doprint o = o.reprText``)
  ``setRender elems = if elems = [] then "set()"``
  ``                  else "{" ++ joinComma (elems.map doprint) ++ "}"``
  ``joinComma [] = []`` ; ``joinComma [x] = x`` ;
  ``joinComma (x :: y :: rest) = x ++ ", " ++ joinComma (y :: rest)``

There is NO opaque answer-key to echo: the ``axioms`` region is empty and
``dictRender`` / ``setRender`` / ``kvText`` / ``joinComma`` / ``doprint`` are
fully-unfolded ``def``s over each method's own argument, so the unique satisfier
IS the honestly-assembled rendering. Each top-level clause combines several
independently-attackable sub-obligations:

  * RECURSIVE ELEMENT TEXT: every element/key/value is rendered by ``doprint``
    (its ``reprText``), NEVER the shallow ``strText`` — this is the whole point
    of the change.
  * BRACES: the join is wrapped in ``{`` / ``}`` specifically.
  * ENTRY / ELEMENT SEPARATOR: consecutive fragments are joined by the
    two-character ", " (comma-space), no leading or trailing separator.
  * KEY↦VALUE SEPARATOR (dict): within an entry the key and value are joined by
    the two-character ": " (colon-space).
  * KEY/VALUE ORDER (dict): each entry renders key first, then value.
  * EMPTY-COLLECTION TOKEN (set): the empty collection renders to "set()", not
    "{}" or "{...}".
  * ORDER / ELEMENT-WISE: fragments appear in their given order, all of them,
    none special-cased by position, over the WHOLE input domain.

Both input binders are load-bearing through the ``Obj`` fields: a rival keying
on ``strText`` instead of ``reprText`` is the pre-change bug; a rival abusing the
list structure (order, separators, pairing) attacks the assembly.

CARRIER NOTE — THE DECIDABLE BOUNDARY. The gold impls are backward ``while``
loops (the front-recursive-fold pattern), so the extracted ``printSetExec`` /
``printDictExec`` do NOT reduce under ``decide`` — a witness stated against a
gold impl gets stuck (measured: ``decide`` reports the tester instance "did not
reduce to isTrue or isFalse"). Every rival below is instead a loop-free
straight-line closed form whose extracted program reduces by kernel computation,
so the tester (from ``derive_tester_for``) evaluates to a literal ``Bool`` and
each witness closes by ``decide`` at fully-concrete literal inputs. Every
witness carrier is a concrete ``Obj`` literal (``reprText`` and ``strText`` are
single-``Char`` ``List``s), so no hypothesis is assumed and there is no
joint-satisfiability obligation. Where a rival keys on ``strText`` the witness
sets that field DIFFERENT from ``reprText`` so the two renderings actually
diverge; where the rival ignores the element text entirely (braces / separator /
order / empty token) the two fields may coincide. Every half was confirmed with
real ``scripts/lean_verify.sh`` builds per reject case (each witness elaborates
green against its rival and errors on the frozen solution).

Because the frozen impls are those loops, the frozen solution can only SEMANTICALLY
refute one of the thirteen witnesses (``wrong-empty-literal-set``, at the empty
COLLECTION, where the loop is never entered). For the other twelve gold's build
fails by stuck reduction, which decides nothing by itself, and the discrimination
is carried by a verifying loop-free positive from this battery instead — see
WITNESS DISCRIMINATION in the footer for the measured failure text, the per-case
subject, and the forgery control. Note the empty-MAPPING witness
(``wrong-empty-literal-dict``) is in the second group, not the first: gold's
``printDict`` has no empty-input early return, so its loop is entered even at
``[]`` and ``decide`` is stuck there too (measured, both claim directions).

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical correct impls (return the grounded models
    ``setRender elems`` / ``dictRender items`` directly, no loop) must verify,
    else the spec is SPEC-TOO-STRONG on the impl shape. Each reproves with a bare
    ``loom_solve`` (the frozen loop-specific rewrite is dropped — the tactic body
    is elided from the spec view, so same_spec and the obligation header are
    untouched).
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY frame rivals that WRITE through read-only inputs held at fractional
    heap permissions (``Acc(list_pred(elems), 1/2)`` and
    ``Acc(list_pred(flat), 1/2)``). Lean and Velvet are referentially
    transparent: ``elems`` and ``items`` are immutable values, no ``mut`` binder
    is declared for them, and there is no heap and no aliasing — so there is no
    read-only input to overwrite and no permission system to trip. Not
    fabricated (per the porting map, this class is vacuous on a
    referentially-transparent backend).
  * DIVERGENCE / NON-TERMINATION — the nagini sibling carries NO ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` case, so there is nothing to port. The
    semantics is ``loom.semantics.termination "total"``, so the class is NOT a
    ``partial`` hole: the verifier really does discharge a termination
    obligation, and a diverging rival really is rejected. It is nonetheless
    UNSHIPPABLE as a witnessed reject case, and the reason is a carrier fact
    about WITNESSES, not about termination — measured, not asserted:
      - a loop with no ``decreasing`` clause is refused by the ELABORATOR before
        any spec reasoning: ``error: Decreasing annotations are required in total
        correctness semantics``, then ``Failed to prove assertion without names:
        WPGen``. That is the termination obligation biting, i.e. the rejection is
        real and attributable — but the same error also fires in the
        proof-stripped WITNESS file, so the witness half cannot be built.
      - a loop with a ``decreasing i`` whose body never decreases ``i`` DOES
        elaborate and IS rejected (``unsolved goals`` on the loop's decreasing
        side-goal), but its witness cannot discriminate: a rival that keeps a
        ``while`` is exactly the shape whose extracted program does not reduce in
        the kernel, so ``decide`` on its tester is STUCK — measured, the witness
        against that rival fails with ``did not reduce to `isTrue` or `isFalse```
        (the gate's own ``_STUCK_REDUCTION`` screen), which is the rival half the
        gate requires to SUCCEED.
    So every diverging rival on this carrier necessarily keeps a loop, and a
    looping rival is un-witnessable here for the same reason the frozen impl is
    un-witnessable (see the CARRIER NOTE). Recorded as a KNOWN GAP in the
    divergence lane rather than as a vacuous class: the class is non-empty, the
    obligation does reject it, and what blocks shipping it is the witness
    carrier. Both builds are reported in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A. Each post-image is a fully-unfolded pure
    function of its input binder; there is no answer-key term a wrong impl could
    echo. The cheapest correct impl assembles the rendering honestly, which the
    positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-obligation (shallow vs recursive element
    text; braces vs parentheses; a dropped or wrong separator; swapped
    key/value; the wrong empty-collection token; the leading element mis-rendered
    while the tail is correct).

ADMISSIBILITY — PORTED (``adm-f2p-shaped-points``). AUDIT-ADDED; the original
port recorded this lane as "degenerate, no separate case" on the grounds that
neither method has a ``require`` clause, and that reasoning is the one the
porting map explicitly rejects. A precondition-free obligation on a TOTAL
carrier still has an admissibility surface: the analogue of PRECOND-TOO-STRONG
is the OBLIGATION being unsatisfiable at exactly an F2P-shaped input. Were
``out = dictRender items`` unmeetable at, say, the empty mapping, every
uniqueness rival would be rejected there for the contradiction rather than for
being wrong, and the whole reject lane would attest to nothing. The case
discharges the obligation at seven F2P-shaped points by EVALUATION, as ``have``s,
before closing the frozen obligation verbatim — including the two DIFFERENT
empty tokens (``{}`` for the mapping, ``set()`` for the collection). Verified
non-vacuous: flipping any one ``have`` to a false rendering makes the case fail.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` — the per-element
rendered text is the output of an UNCHANGED helper, modeled as the free input
carrier (``Obj.reprText``), and the assembly itself is modeled DEEPLY as
``dictRender`` / ``setRender`` / ``kvText`` / ``joinComma``. The nagini file's
AXIOM_TESTS drive the real post-patch printer in Docker (G-AX's job); this gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19346"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors: the ENTIRE frozen loop body of each method (between
# ---- and INCLUDING the markers). Each lies wholly inside one
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load).
_SET_IMPL = """    -- impl-start
    if elems = [] then
      return "set()".toList
    else
      let mut joined : List Char := []
      let mut i := elems.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ elems.length
        invariant joined = joinComma ((elems.map doprint).drop i)
        done_with i = 0
        decreasing i
      do
        let piece := doprint elems[i - 1]!
        joined := if i = elems.length then piece else piece ++ ", ".toList ++ joined
        i := i - 1
      return "{".toList ++ joined ++ "}".toList
    -- impl-end"""
assert _BASE.count(_SET_IMPL) == 1, "set impl-block anchor drift — re-sync _SET_IMPL"

_DICT_IMPL = """    -- impl-start
    let mut joined : List Char := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant joined = joinComma ((items.map kvText).drop i)
      done_with i = 0
      decreasing i
    do
      let piece := kvText items[i - 1]!
      joined := if i = items.length then piece else piece ++ ", ".toList ++ joined
      i := i - 1
    return "{".toList ++ joined ++ "}".toList
    -- impl-end"""
assert _BASE.count(_DICT_IMPL) == 1, "dict impl-block anchor drift — re-sync _DICT_IMPL"

# ---- proof-body anchors. Each frozen tactic script is tuned to its frozen loop
# ---- body. A positive control that drops the loop retunes it to a bare
# ---- `loom_solve`; both the impl region and the `prove_correct` body are elided
# ---- from the spec view, so same_spec still holds and each `prove_correct`
# ---- obligation survives with an identical header. Unique.
_SET_PROOF = """prove_correct printSet by
  loom_solve
  all_goals
    first
      | (rw [joinComma_drop_step_elem elems i (by omega) (by omega)]; simp_all)
      | (rw [show elems.length = (elems.map doprint).length from (List.length_map ..).symm,
             List.drop_length]; rfl)
      | simp_all [setRender]"""
assert _BASE.count(_SET_PROOF) == 1, "set proof region drifted from expected text"

_DICT_PROOF = """prove_correct printDict by
  loom_solve
  all_goals
    first
      | (rw [joinComma_drop_step_kv items i (by omega) (by omega)]; simp_all)
      | (rw [show items.length = (items.map kvText).length from (List.length_map ..).symm,
             List.drop_length]; rfl)
      | simp_all [dictRender]"""
assert _BASE.count(_DICT_PROOF) == 1, "dict proof region drifted from expected text"


def _set_impl(body):
    return _swap(_BASE, _SET_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _dict_impl(body):
    return _swap(_BASE, _DICT_IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


# ---- admissibility helper. Prefixes each frozen `prove_correct` tactic body
# ---- with extra `have`s and keeps the frozen script that follows VERBATIM, so
# ---- the obligation is still closed by exactly the frozen proof. The tactic
# ---- body is elided from the spec view, so same_spec holds and both
# ---- `prove_correct` headers survive byte-identically.
_SET_PROOF_HEAD = "prove_correct printSet by\n"
_DICT_PROOF_HEAD = "prove_correct printDict by\n"
assert _SET_PROOF.startswith(_SET_PROOF_HEAD)
assert _DICT_PROOF.startswith(_DICT_PROOF_HEAD)


def _prefix_proofs(set_pre, dict_pre):
    src = _swap(_BASE, _SET_PROOF,
                _SET_PROOF_HEAD + set_pre + _SET_PROOF[len(_SET_PROOF_HEAD):])
    return _swap(src, _DICT_PROOF,
                 _DICT_PROOF_HEAD + dict_pre + _DICT_PROOF[len(_DICT_PROOF_HEAD):])


# ---- witness preamble. Each spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `<method>Tester <input> = false` says the extracted program's result
# ---- violates that method's postcondition at the concrete input. Checked in a
# ---- file whose `prove_correct` blocks have been stripped, so no tactic script
# ---- can mask the verdict.
def _tester(method, body):
    return (f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-model-set",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the loop entirely and return the
        # grounded pure model `setRender elems` directly. `setRender` is a total
        # function of the input (no opaque answer-key — it spells out the empty
        # token, braces, `doprint` per element and the `joinComma` separator), so
        # this is a correct impl, not an echo. The residual goal is definitional,
        # closed by a bare `loom_solve`.
        "module": _swap(_set_impl("    return setRender elems"),
                        _SET_PROOF, "prove_correct printSet by\n  loom_solve"),
        "rationale": (
            "the cheapest honest correct collection renderer returns the grounded "
            "pure model `setRender elems` directly (no loop — maximally different "
            "from the gold backward `while`). The ensures is literally "
            "`out = setRender elems`, so it holds on the whole domain and a bare "
            "`loom_solve` discharges the definitional residual. If this failed the "
            "spec would be over-fit to the loop shape (SPEC-TOO-STRONG). Doubles "
            "as the no-ungrounded-echo control: the model IS the real assembly "
            "work. (Sibling: pos-control-set.)"),
    },
    {
        "id": "pos-return-model-dict",
        "kind": "soundness",
        "expect": "verify",
        # Same for the mapping renderer: return the grounded model `dictRender
        # items` and retune the proof to a bare `loom_solve`.
        "module": _swap(_dict_impl("    return dictRender items"),
                        _DICT_PROOF, "prove_correct printDict by\n  loom_solve"),
        "rationale": (
            "the cheapest honest correct mapping renderer returns the grounded "
            "pure model `dictRender items` directly (no loop). The ensures is "
            "literally `out = dictRender items`, so a bare `loom_solve` closes the "
            "definitional residual. Must verify, else the spec is over-fit to the "
            "loop shape (SPEC-TOO-STRONG). No ungrounded echo: `dictRender` spells "
            "out the braces, `kvText` per entry and the `joinComma` separator over "
            "the input. (Sibling: pos-control-dict.)"),
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). AUDIT-ADDED. Neither method has a
    # `require` clause, but on a TOTAL carrier the analogue of an over-strong
    # precondition is the OBLIGATION being unsatisfiable at exactly an F2P-shaped
    # input: `out = dictRender items` / `out = setRender elems` would then be a
    # postcondition no impl can meet there, and every uniqueness rival would be
    # rejected for that reason rather than for being wrong — the reject lane
    # would attest to a contradiction instead of to the spec. This case
    # discharges the obligation at each F2P-shaped point BY EVALUATION, as a
    # `have`, BEFORE closing the frozen obligation with the frozen script
    # VERBATIM. Each `have` names a concrete input and the exact rendering the
    # spec demands of it, so `decide` computing it to `True` IS the
    # satisfiability demonstration at that point.
    {
        "id": "adm-f2p-shaped-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _prefix_proofs(
            # collection side: the empty collection, a singleton, a pair.
            '  have adm_empty : setRender [] = "set()".toList := by decide\n'
            '  have adm_one :\n'
            '      setRender [{ reprText := "X".toList, strText := "x".toList }]\n'
            '        = "{X}".toList := by decide\n'
            '  have adm_two :\n'
            '      setRender [{ reprText := "X".toList, strText := "x".toList },\n'
            '                 { reprText := "Y".toList, strText := "y".toList }]\n'
            '        = "{X, Y}".toList := by decide\n',
            # mapping side: the empty mapping (which must render "{}", NOT the
            # collection's "set()" token), one entry, two entries, and an entry
            # whose value is itself an already-rendered container.
            '  have adm_empty : dictRender [] = "{}".toList := by decide\n'
            '  have adm_one :\n'
            '      dictRender [({ reprText := "K".toList, strText := "k".toList },\n'
            '                  { reprText := "V".toList, strText := "v".toList })]\n'
            '        = "{K: V}".toList := by decide\n'
            '  have adm_two :\n'
            '      dictRender [({ reprText := "K".toList, strText := "k".toList },\n'
            '                  { reprText := "V".toList, strText := "v".toList }),\n'
            '                 ({ reprText := "V".toList, strText := "v".toList },\n'
            '                  { reprText := "W".toList, strText := "w".toList })]\n'
            '        = "{K: V, V: W}".toList := by decide\n'
            '  have adm_nested :\n'
            '      dictRender [({ reprText := "K".toList, strText := "k".toList },\n'
            '                  { reprText := "{V: W}".toList,\n'
            '                    strText := "{v: w}".toList })]\n'
            '        = "{K: {V: W}}".toList := by decide\n'),
        "rationale": (
            "ADMISSIBILITY / PRECOND-TOO-STRONG. The sibling's admissibility "
            "control asserts an F2P-shaped input satisfies a `Requires`. Here "
            "the `pre-conditions` regions are empty, so the analogue on this "
            "TOTAL carrier is the POSTCONDITION being satisfiable at the "
            "F2P-shaped points: seven `have`s discharge `dictRender` / "
            "`setRender` by `decide` at the empty mapping (`{}`), the empty "
            "collection (`set()`), a singleton, a two-entry / two-element "
            "input, and an entry whose value is itself a rendered container — "
            "then the frozen obligation is closed by the frozen script "
            "VERBATIM. If any `have` failed, the obligation would be "
            "unsatisfiable at that input and the whole reject lane would be "
            "attesting to a contradiction rather than to the spec. Note the "
            "two empty tokens DIFFER (`{}` for the mapping, `set()` for the "
            "collection) and both are pinned here. NOT vacuous by construction: "
            "measured, flipping one `have` to a false rendering "
            "(`{K: V, V: W}` -> `{V: W, K: V}`, or `{X, Y}` -> `{XY}`) makes "
            "the case FAIL with \"`decide` proved ... is false\", so each "
            "`have` is deciding the real equation. (Sibling: the "
            "`len(flat) % 2 == 0` admissibility control, re-derived for a "
            "precondition-free total carrier.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free straight-line closed form with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test. Each rival's extracted program reduces by kernel
    # computation, so its witness discriminates by value (see the CARRIER NOTE).
    # =====================================================================

    # --- the prepatch discriminator (THE bug): shallow element text ---------
    {
        "id": "wrong-str-elem-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Render each element by the SHALLOW textual form (`o.strText`) instead of
        # the recursive `doprint o = o.reprText`. This IS the pre-change behaviour.
        "module": _set_impl(
            '    if elems = [] then\n'
            '      return "set()".toList\n'
            '    else\n'
            '      return "{".toList ++ joinComma (elems.map (fun o => o.strText)) ++ "}".toList'),
        "refinement": (
            "this is the pre-change behaviour: each element rendered by the "
            "shallow textual form instead of the recursive element renderer. The "
            "collection would print its elements by their shallow form (e.g. "
            "`{x, y}`) rather than their fully recursive rendering (e.g. "
            "`{Symbol('x'), Symbol('y')}`), which is exactly the wrong output the "
            "failing test rejects — so it would NOT resolve. Correct on the empty "
            "token, braces, separator and order; the divergence is exactly the "
            "shallow-vs-recursive element text. (Sibling: wrong-str-elem-set.)"),
        "rationale": (
            "REJECT from the RECURSIVE ELEMENT TEXT sub-obligation: `setRender` "
            "maps `doprint` (= `reprText`) over the elements, and this impl maps "
            "`strText`, so `out` ≠ the model whenever some element's two forms "
            "differ. If it verified => SPEC-TOO-WEAK (admits the prepatch). Refuted "
            "at a single element whose reprText=['x'] ≠ strText=['a']: gold builds "
            "`{x}`, the rival `{a}`."),
        "witness": _tester(
            "printSet",
            "example : printSetTester [{ reprText := ['x'], strText := ['a'] }] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "wrong-str-elem-dict",
        "kind": "uniqueness",
        "expect": "reject",
        # Render each key and value by the shallow form instead of the recursive
        # renderer — the pre-change mapping behaviour.
        "module": _dict_impl(
            '    return "{".toList ++ joinComma (items.map (fun p => p.1.strText ++ ": ".toList ++ p.2.strText)) ++ "}".toList'),
        "refinement": (
            "the pre-change mapping behaviour: each key/value via the shallow "
            "textual form instead of the recursive renderer. The mapping would "
            "print `{x: y}` rather than the fully recursive `{Symbol('x'): "
            "Symbol('y')}` the failing test asserts — so it would NOT resolve; this "
            "is precisely the state the fix repairs. Correct on the braces, "
            "separators and pairing; the divergence is the shallow-vs-recursive "
            "text. (Sibling: wrong-str-elem-dict.)"),
        "rationale": (
            "REJECT from the RECURSIVE ELEMENT TEXT sub-obligation: `kvText` uses "
            "`doprint` (= `reprText`) for both components, and this impl uses "
            "`strText`, so `out` ≠ the model whenever a component's two forms "
            "differ. If it verified => SPEC-TOO-WEAK (admits the prepatch). Refuted "
            "at one entry whose key/value reprText ≠ strText: gold builds "
            "`{x: y}`, the rival `{a: b}`."),
        "witness": _tester(
            "printDict",
            "example : printDictTester [({ reprText := ['x'], strText := ['a'] }, "
            "{ reprText := ['y'], strText := ['b'] })] = false := by\n  decide\n"),
    },

    # --- partial-domain: first element only mis-rendered -------------------
    {
        "id": "partial-domain-first-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Render the FIRST element by the shallow form and the rest recursively.
        # Correct on the whole tail; diverges only on the leading element.
        "module": _set_impl(
            '    if elems = [] then\n'
            '      return "set()".toList\n'
            '    else\n'
            '      return "{".toList ++ joinComma (elems[0]!.strText :: (elems.drop 1).map doprint) ++ "}".toList'),
        "refinement": (
            "renders the FIRST element by the shallow form and the rest "
            "recursively (correct on the whole tail, wrong only on the leading "
            "element). A faithful counterpart would print the first element by its "
            "shallow form (e.g. `{x, Symbol('y')}`) and fail the exact-string "
            "assertion — so it would NOT resolve. Agrees with gold on every "
            "input whose first element has coincident forms; refuted at the "
            "distinguishing leading-element input. (Sibling: "
            "partial-domain-first-set.)"),
        "rationale": (
            "REJECT from the RECURSIVE ELEMENT TEXT sub-obligation over the WHOLE "
            "domain: `setRender` pins EVERY element (including the first) to "
            "`doprint`, and this impl special-cases index 0 to `strText`. If it "
            "verified => SPEC-TOO-WEAK on the first-element sub-domain. Refuted at "
            "two elements where the first has reprText=['A'] ≠ strText=['p'] and "
            "the second coincides: gold builds `{A, B}`, the rival `{p, B}`."),
        "witness": _tester(
            "printSet",
            "example : printSetTester [{ reprText := ['A'], strText := ['p'] }, "
            "{ reprText := ['B'], strText := ['B'] }] = false := by\n  decide\n"),
    },

    # --- key/value ordering (dict) -----------------------------------------
    {
        "id": "swap-key-value-dict",
        "kind": "uniqueness",
        "expect": "reject",
        # Render each entry as value: key instead of key: value.
        "module": _dict_impl(
            '    return "{".toList ++ joinComma (items.map (fun p => doprint p.2 ++ ": ".toList ++ doprint p.1)) ++ "}".toList'),
        "refinement": (
            "renders each entry as value: key instead of key: value. A faithful "
            "counterpart emitting `value: key` prints `{Symbol('y'): Symbol('x')}` "
            "for the entry the fix renders `{Symbol('x'): Symbol('y')}` and fails "
            "the exact-string assertion — so it would NOT resolve. Correct on the "
            "recursive text, braces and separators; the divergence is the "
            "key/value order. (Sibling: swap-key-value-dict.)"),
        "rationale": (
            "REJECT from the KEY/VALUE ORDER sub-obligation: `kvText p` places "
            "`doprint p.1` (key) before `doprint p.2` (value), and this impl swaps "
            "them, so `out` ≠ the model whenever a key and value render "
            "differently. If it verified => SPEC-TOO-WEAK on entry ordering. "
            "Refuted at one entry key reprText=['K'] ≠ value reprText=['W']: gold "
            "builds `{K: W}`, the rival `{W: K}`."),
        "witness": _tester(
            "printDict",
            "example : printDictTester [({ reprText := ['K'], strText := ['k'] }, "
            "{ reprText := ['W'], strText := ['w'] })] = false := by\n  decide\n"),
    },

    # --- entry / element separator -----------------------------------------
    {
        "id": "no-separator-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Concatenate element renderings with NO separator (flatten) instead of
        # joining by ", ".
        "module": _set_impl(
            '    if elems = [] then\n'
            '      return "set()".toList\n'
            '    else\n'
            '      return "{".toList ++ (elems.map doprint).flatten ++ "}".toList'),
        "refinement": (
            "assembles the element renderings with no ', ' separator. A faithful "
            "counterpart using a no-separator concatenation prints "
            "`{Symbol('x')Symbol('y')}` and fails the exact-string assertion — so "
            "it would NOT resolve. Correct on the empty token, braces, recursive "
            "text and order, and on any single-element collection; the divergence "
            "is exactly the separator. (Sibling: no-separator-set.)"),
        "rationale": (
            "REJECT from the ELEMENT SEPARATOR sub-obligation: `joinComma` places "
            "', ' between consecutive fragments, and this impl places nothing, so "
            "`out` ≠ the model whenever ≥ 2 elements are joined. If it verified => "
            "SPEC-TOO-WEAK on the separator. Refuted at two elements: gold builds "
            "`{C, D}`, the rival `{CD}`."),
        "witness": _tester(
            "printSet",
            "example : printSetTester [{ reprText := ['C'], strText := ['c'] }, "
            "{ reprText := ['D'], strText := ['d'] }] = false := by\n  decide\n"),
    },
    {
        "id": "no-separator-dict",
        "kind": "uniqueness",
        "expect": "reject",
        # Concatenate entry renderings with NO ", " separator.
        "module": _dict_impl(
            '    return "{".toList ++ (items.map kvText).flatten ++ "}".toList'),
        "refinement": (
            "assembles the entry renderings with no ', ' separator. A faithful "
            "counterpart joining entries with an empty separator runs consecutive "
            "`key: value` entries together and fails the exact-string assertion — "
            "so it would NOT resolve. Correct on the braces, recursive text, "
            "pairing and order, and on any single-entry mapping; the divergence is "
            "exactly the entry separator. (Sibling: no-separator-set, applied to "
            "the mapping renderer.)"),
        "rationale": (
            "REJECT from the ENTRY SEPARATOR sub-obligation: `joinComma` places "
            "', ' between consecutive entries, and this impl places nothing, so "
            "`out` ≠ the model whenever ≥ 2 entries are joined. If it verified => "
            "SPEC-TOO-WEAK on the entry separator. Refuted at two entries with "
            "coincident forms (keys e/g, values f/h): gold builds "
            "`{e: f, g: h}`, the rival `{e: fg: h}`."),
        "witness": _tester(
            "printDict",
            "example : printDictTester [({ reprText := ['e'], strText := ['e'] }, "
            "{ reprText := ['f'], strText := ['f'] }), "
            "({ reprText := ['g'], strText := ['g'] }, "
            "{ reprText := ['h'], strText := ['h'] })] = false := by\n  decide\n"),
    },

    # --- key/value separator (dict) ----------------------------------------
    {
        "id": "kv-separator-dict",
        "kind": "uniqueness",
        "expect": "reject",
        # Join key and value within an entry by a bare "=" instead of ": ".
        "module": _dict_impl(
            '    return "{".toList ++ joinComma (items.map (fun p => doprint p.1 ++ "=".toList ++ doprint p.2)) ++ "}".toList'),
        "refinement": (
            "joins key and value within an entry by a bare '=' instead of the "
            "two-character ': '. A faithful counterpart emitting `key=value` "
            "renders the entry with the wrong intra-entry separator and fails the "
            "exact-string assertion — so it would NOT resolve. Correct on the "
            "recursive text, braces, entry separator, pairing and order; the "
            "divergence is exactly the key↦value separator. (Added: the sibling's "
            "dict rivals attack the pairing and the shallow text but not the "
            "intra-entry ': ' separator, which is an independent clause of "
            "`kvText`.)"),
        "rationale": (
            "REJECT from the KEY↦VALUE SEPARATOR sub-obligation: `kvText p` places "
            "the two-character ': ' between key and value, and this impl places a "
            "bare '=', so `out` ≠ the model for every non-empty mapping. If it "
            "verified => SPEC-TOO-WEAK on the intra-entry separator. Refuted at one "
            "entry with coincident forms: gold builds `{m: n}`, the rival `{m=n}`."),
        "witness": _tester(
            "printDict",
            "example : printDictTester [({ reprText := ['m'], strText := ['m'] }, "
            "{ reprText := ['n'], strText := ['n'] })] = false := by\n  decide\n"),
    },

    # --- braces / delimiters -----------------------------------------------
    {
        "id": "paren-not-brace-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrap in parentheses instead of braces.
        "module": _set_impl(
            '    if elems = [] then\n'
            '      return "set()".toList\n'
            '    else\n'
            '      return "(".toList ++ joinComma (elems.map doprint) ++ ")".toList'),
        "refinement": (
            "wraps the joined elements in parentheses instead of braces. A "
            "faithful counterpart using `(` / `)` renders the collection with the "
            "wrong delimiters and fails the exact-string assertion — so it would "
            "NOT resolve. Correct on the recursive text, separator and order; the "
            "divergence is exactly the delimiter choice. (Added: the sibling's set "
            "near-misses attack the separator and the empty token but not the "
            "outer brace delimiters, an independent clause.)"),
        "rationale": (
            "REJECT from the BRACES sub-obligation: `setRender` wraps the join in "
            "`{` / `}`, and this impl wraps it in `(` / `)`, so `out` ≠ the model "
            "whenever the collection is non-empty. If it verified => SPEC-TOO-WEAK "
            "on the delimiters. Refuted at one element: gold builds `{q}`, the "
            "rival `(q)`."),
        "witness": _tester(
            "printSet",
            "example : printSetTester [{ reprText := ['q'], strText := ['z'] }] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "paren-not-brace-dict",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrap the mapping in parentheses instead of braces.
        "module": _dict_impl(
            '    return "(".toList ++ joinComma (items.map kvText) ++ ")".toList'),
        "refinement": (
            "wraps the joined entries in parentheses instead of braces. A faithful "
            "counterpart using `(` / `)` renders the mapping with the wrong "
            "delimiters and fails the exact-string assertion — so it would NOT "
            "resolve. Correct on the recursive text, separators, pairing and "
            "order; the divergence is exactly the delimiter choice. (Added: the "
            "outer brace delimiters are an independent clause of `dictRender` no "
            "other rival attacks.)"),
        "rationale": (
            "REJECT from the BRACES sub-obligation: `dictRender` wraps the join in "
            "`{` / `}`, and this impl wraps it in `(` / `)`, so `out` ≠ the model "
            "for every mapping. If it verified => SPEC-TOO-WEAK on the delimiters. "
            "Refuted at one entry: gold builds `{u: v}`, the rival `(u: v)`."),
        "witness": _tester(
            "printDict",
            "example : printDictTester [({ reprText := ['u'], strText := ['u'] }, "
            "{ reprText := ['v'], strText := ['v'] })] = false := by\n  decide\n"),
    },

    # --- empty-collection token (set) --------------------------------------
    {
        "id": "wrong-empty-literal-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Return "{}" for the empty collection instead of "set()".
        "module": _set_impl(
            '    if elems = [] then\n'
            '      return "{}".toList\n'
            '    else\n'
            '      return "{".toList ++ joinComma (elems.map doprint) ++ "}".toList'),
        "refinement": (
            "returns '{}' for the empty collection instead of 'set()'. A faithful "
            "counterpart returning '{}' for an empty set renders it as an empty "
            "mapping and fails the assertion that the empty collection renders to "
            "'set()' — so it would NOT resolve. Correct on every non-empty "
            "collection; the divergence is exactly the empty-collection token. "
            "(Sibling: wrong-empty-literal-set.)"),
        "rationale": (
            "REJECT from the EMPTY-COLLECTION TOKEN sub-obligation: `setRender` "
            "pins the empty case to 'set()', and this impl returns '{}', so `out` "
            "≠ the model at the empty input. If it verified => SPEC-TOO-WEAK on the "
            "empty token. Refuted at `[]`: gold builds `set()`, the rival `{}`."),
        "witness": _tester(
            "printSet",
            "example : printSetTester [] = false := by\n  decide\n"),
    },

    # --- empty-collection token, MAPPING side ------------------------------
    # AUDIT-ADDED. `wrong-empty-literal-set` pins the COLLECTION's empty token
    # ("set()"), but nothing pinned the MAPPING's, and the two are DIFFERENT
    # literals — the empty mapping must render "{}". A rival that carried the
    # collection's empty-token special case over to the mapping renderer was
    # therefore unattacked, even though it is the more tempting mistake (one
    # renderer's empty case copied into the other). Every shipped dict rival
    # renders the empty mapping correctly, because each is a single unconditional
    # `return` whose join of `[]` is empty — so the empty-mapping sub-domain had
    # no rival at all. Built and refuted during the audit before being added.
    {
        "id": "wrong-empty-literal-dict",
        "kind": "uniqueness",
        "expect": "reject",
        # Return "set()" for the empty mapping instead of "{}" — the collection
        # renderer's empty token misapplied to the mapping renderer. Every
        # non-empty mapping is rendered exactly right.
        "module": _dict_impl(
            '    if items = [] then\n'
            '      return "set()".toList\n'
            '    else\n'
            '      return "{".toList ++ joinComma (items.map kvText) ++ "}".toList'),
        "refinement": (
            "returns the collection's empty token for the empty MAPPING instead "
            "of the empty-brace pair. A faithful counterpart that special-cased "
            "the empty mapping to the collection's token would render an empty "
            "mapping as though it were an empty collection, failing the "
            "exact-string assertion the graded failing test makes about the "
            "empty mapping — so it would NOT resolve. Correct on EVERY non-empty "
            "mapping (recursive text, braces, both separators, pairing, order); "
            "the divergence is exactly the empty-mapping token, which is a "
            "DIFFERENT literal from the empty-collection one. (Added by audit: "
            "the collection's empty token was pinned, the mapping's was not.)"),
        "rationale": (
            "REJECT from the EMPTY-MAPPING TOKEN sub-obligation: `dictRender []` "
            "unfolds to `\"{\" ++ joinComma [] ++ \"}\"` = the two-character "
            "empty-brace pair, and this impl returns the five-character "
            "collection token instead, so `out` ≠ the model at the empty input "
            "and ONLY there. If it verified => SPEC-TOO-WEAK on the "
            "empty-mapping token — note this is the one clause where the two "
            "renderers legitimately DISAGREE, so a rival copying one into the "
            "other is exactly the mistake the spec must exclude. Refuted at "
            "`[]`: gold builds the empty-brace pair, the rival the collection "
            "token."),
        "witness": _tester(
            "printDict",
            "example : printDictTester [] = false := by\n  decide\n"),
    },

    # --- fragment ORDER (both renderers) -----------------------------------
    # AUDIT-ADDED. The manifest's clause list names an ORDER / ELEMENT-WISE
    # sub-obligation ("fragments appear in their given order, all of them") and
    # claimed every clause was attacked, but no shipped rival moved a fragment's
    # POSITION: every one of them alters a fragment's TEXT, the delimiters, a
    # separator or the empty token, each of which is order-agnostic. A rival that
    # emits exactly the right multiset of fragments with exactly the right
    # separators, in the wrong order, was therefore unattacked. Both rivals below
    # were built and refuted during the audit before being added.
    {
        "id": "reverse-order-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the elements in REVERSE order. Every fragment is rendered by the
        # recursive renderer, the braces and the ", " separator are all correct,
        # and the empty case is untouched — only the positions move.
        "module": _set_impl(
            '    if elems = [] then\n'
            '      return "set()".toList\n'
            '    else\n'
            '      return "{".toList ++ joinComma (elems.reverse.map doprint) ++ "}".toList'),
        "refinement": (
            "emits the elements in reverse order. A faithful counterpart that "
            "walked the collection backwards would render the right elements with "
            "the right delimiters and separator but in the wrong positions (e.g. "
            "`{S, R}` where the fix builds `{R, S}`), failing the exact-string "
            "assertion — so it would NOT resolve. Agrees with gold on every input "
            "of length 0 or 1 and on every palindromic rendering; the divergence "
            "is exactly the element ORDER. (Added by audit: no other rival moves "
            "a fragment's position — each alters a fragment's text, the "
            "delimiters, a separator or the empty token, all order-agnostic.)"),
        "rationale": (
            "REJECT from the ORDER / ELEMENT-WISE sub-obligation: `setRender` maps "
            "`doprint` over `elems` IN ITS GIVEN ORDER, and this impl maps over "
            "`elems.reverse`, so `out` ≠ the model whenever two elements render "
            "differently. If it verified => SPEC-TOO-WEAK on fragment order — a "
            "rival emitting the right fragment multiset with the right separators "
            "in the wrong positions would go uncaught. Refuted at two elements "
            "reprText=['R'] and ['S'] (forms coincident, so the element-text "
            "clause is not what is being probed): gold builds `{R, S}`, the rival "
            "`{S, R}`."),
        "witness": _tester(
            "printSet",
            "example : printSetTester [{ reprText := ['R'], strText := ['R'] }, "
            "{ reprText := ['S'], strText := ['S'] }] = false := by\n  decide\n"),
    },
    {
        "id": "reverse-order-dict",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the entries in REVERSE order. Each entry is rendered correctly
        # (recursive key and value, ": " between them), the braces and the ", "
        # entry separator are correct — only the entry positions move.
        "module": _dict_impl(
            '    return "{".toList ++ joinComma (items.reverse.map kvText) ++ "}".toList'),
        "refinement": (
            "emits the entries in reverse order. A faithful counterpart iterating "
            "the mapping backwards renders each `key: value` entry correctly but "
            "places them in the wrong positions (e.g. `{c: d, a: b}` where the fix "
            "builds `{a: b, c: d}`), failing the exact-string assertion — so it "
            "would NOT resolve. Agrees with gold on every mapping of 0 or 1 "
            "entries; the divergence is exactly the entry ORDER. (Added by audit: "
            "the entry-position clause was unattacked.)"),
        "rationale": (
            "REJECT from the ORDER / ELEMENT-WISE sub-obligation: `dictRender` maps "
            "`kvText` over `items` IN ITS GIVEN ORDER, and this impl maps over "
            "`items.reverse`, so `out` ≠ the model whenever two entries render "
            "differently. If it verified => SPEC-TOO-WEAK on entry order. Refuted "
            "at two entries (a↦b, c↦d) whose forms coincide, so neither the "
            "element-text nor the separator clause is what is being probed: gold "
            "builds `{a: b, c: d}`, the rival `{c: d, a: b}`."),
        "witness": _tester(
            "printDict",
            "example : printDictTester [({ reprText := ['a'], strText := ['a'] }, "
            "{ reprText := ['b'], strText := ['b'] }), "
            "({ reprText := ['c'], strText := ['c'] }, "
            "{ reprText := ['d'], strText := ['d'] })] = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 10 SPEC cases (2
# soundness positives, 2 MANDATORY frame-mutation rivals, 6 uniqueness value/
# near-miss rivals; AXIOM_TESTS is a separate lane). It contracts
# `render_collection_codepoints(elems)` and `render_mapping_codepoints(flat)`
# over `List`/`PSeq` inputs held at fractional read-only permissions, modeling
# the codepoint stream as `List[int]`. This backend models the SAME brace-
# delimited, comma-separated renderings DEEPLY and CONCRETELY (`setRender` /
# `dictRender` / `kvText` / `joinComma` over `List Char`, with each element's
# recursive text supplied as the free carrier `Obj.reprText` and its shallow
# form as `Obj.strText`), pins each with a single `ensures`, and has NO
# precondition and NO permission surface. Those carrier facts make two sibling
# classes vacuous/degenerate here.
#
#   nagini case               kind          -> here                      disposition
#   ------------------------------------------------------------------------------------
#   pos-control-set           soundness     -> pos-return-model-set       PORTED
#   pos-control-dict          soundness     -> pos-return-model-dict      PORTED
#   frame-mut-set             uniqueness    -> (none)                     VACUOUS
#   frame-mut-dict            uniqueness    -> (none)                     VACUOUS
#   wrong-str-elem-set        uniqueness    -> wrong-str-elem-set         PORTED
#   wrong-str-elem-dict       uniqueness    -> wrong-str-elem-dict        PORTED
#   partial-domain-first-set  uniqueness    -> partial-domain-first-set   PORTED
#   swap-key-value-dict       uniqueness    -> swap-key-value-dict        PORTED
#   no-separator-set          uniqueness    -> no-separator-set           PORTED
#   wrong-empty-literal-set   uniqueness    -> wrong-empty-literal-set    PORTED
#   (no sibling)              uniqueness    -> no-separator-dict          ADDED
#   (no sibling)              uniqueness    -> kv-separator-dict          ADDED
#   (no sibling)              uniqueness    -> paren-not-brace-set        ADDED
#   (no sibling)              uniqueness    -> paren-not-brace-dict       ADDED
#   (no sibling)              uniqueness    -> reverse-order-set          ADDED (audit)
#   (no sibling)              uniqueness    -> reverse-order-dict         ADDED (audit)
#   (no sibling)              uniqueness    -> wrong-empty-literal-dict   ADDED (audit 2)
#   (dict Requires)           admissibility -> adm-f2p-shaped-points      ADDED (audit 2)
#   AXIOM_TESTS               axiom         -> (none)                     N/A (G-AX)
#
# 6 uniqueness ported + 7 added; 2 soundness ported; 1 admissibility re-derived;
# 2 frame-mutation vacuous; axiom lane dropped. 16 SPEC cases (2 soundness,
# 13 uniqueness, 1 admissibility).
#
# PORTED (pos-control-set/dict): the sibling's positive controls read the element
#   through a renamed-local indirection (a different SSA shape) while keeping the
#   loop. On this carrier the maximally-different correct impl drops the loop
#   entirely and returns the grounded model (`setRender elems` / `dictRender
#   items`); proof retuned to a bare `loom_solve` (verified to build). Doubles as
#   the no-ungrounded-echo control.
# PORTED (the six value/near-miss rivals): wrong-str-elem-set/dict (the prepatch
#   discriminator — shallow element text instead of the recursive renderer);
#   partial-domain-first-set (leading element shallow, tail recursive);
#   swap-key-value-dict (value: key instead of key: value); no-separator-set (no
#   ', ' between elements); wrong-empty-literal-set ('{}' for the empty set
#   instead of 'set()'). The sibling's 3d/3e near-misses map directly.
# ADDED (no-separator-dict): the sibling attacks the set separator but not the
#   dict ENTRY separator; the dict renderer's `joinComma` over entries is an
#   independent clause, so a rival dropping it is added.
# ADDED (kv-separator-dict): the sibling's dict rivals attack the pairing and the
#   shallow text but not the intra-entry KEY↦VALUE separator (': '), which is an
#   independent clause of `kvText`. Without it a rival mishandling only that
#   separator would go uncaught.
# ADDED (paren-not-brace-set, paren-not-brace-dict): the sibling attacks the
#   EMPTY token and separators but not the outer brace DELIMITERS, an independent
#   clause of both `setRender` and `dictRender`. Added one per renderer.
# ADDED BY AUDIT (reverse-order-set, reverse-order-dict): the fragment-POSITION
#   clause. Neither the sibling nor the original port carried a rival that moves a
#   fragment's position, though the clause list named ORDER / ELEMENT-WISE and
#   claimed it attacked. Both rivals emit exactly the right fragment multiset with
#   exactly the right delimiters and separators, in reversed positions, so they
#   isolate order alone (witness forms held coincident, reprText = strText).
#   Measured: rival exit 0, gold exit 1 (stuck), refuted semantically against the
#   verifying positive for its own method.
#
# SPEC PROBES RE-RUN BY THE SECOND AUDIT (no hole in the frozen spec; recorded
#   with the tactic that actually closed each, so the next reader does not
#   re-derive them). SPEC-TOO-WEAK direction — five NEW wrong impls beyond the
#   shipped rivals, ALL REJECTED by the frozen spec (exit 1, real builds):
#     * "set()" as the EMPTY-MAPPING token — rejected with the residual
#       `items = [] ⊢ False`, i.e. the spec pins the empty mapping to the
#       empty-brace pair. This one was a real COVERAGE GAP, not just a probe:
#       it is now shipped as `wrong-empty-literal-dict` above.
#     * a trailing ", " before the closing brace (collection);
#     * dropping the LAST element (collection);
#     * rendering the key only, dropping ": value" (mapping);
#     * treating a SINGLETON collection as empty.
#   SPEC-TOO-STRONG direction — correct impls that assemble the rendering INLINE
#   without ever naming `setRender`/`dictRender`/`kvText` DO verify, so the spec
#   is not over-fit to naming the pure model. CORRECTION: the earlier footer said
#   the set side needed `have hfun : (fun o : Obj => o.reprText) = doprint := rfl`
#   before `loom_solve` and the dict side "an `rfl` alternative". Re-measured,
#   BOTH of those specific scripts FAIL (exit 1, `unsolved goals` — and with the
#   `hfun` rewrite applied the goal is still `... = dictRender items`, because the
#   residual is the outer model unfold, not the inner congruence). What actually
#   closes them, measured exit 0:
#     * set inline:  `loom_solve` then `all_goals simp_all [setRender, hfun]`
#       (with the `hfun` have), or `all_goals simp_all [setRender, doprint]`;
#     * dict inline: `loom_solve` then `all_goals rfl`, or
#       `all_goals simp_all [dictRender, kvText, doprint]`.
#   Also verified as correct reshapes the spec ACCEPTS: an eta-expanded
#   `items.map (fun p => kvText p)` (needs `all_goals rfl`; bare `loom_solve`
#   alone fails), a `elems.length = 0` empty test in place of `elems = []`
#   (needs `simp_all [setRender, List.length_eq_zero_iff]`), and a
#   `elems.reverse.reverse` round trip (needs `simp_all [setRender,
#   List.reverse_reverse]`). In every case the failure of the WEAKER script is a
#   proof-engineering fact, not a spec rejection: a stronger script on the same
#   impl verifies. No faithful correct reshape was found that the spec rejects.
# ADMISSIBILITY — now PORTED as `adm-f2p-shaped-points` (see the case). The
#   original port recorded this lane as DEGENERATE because neither method has a
#   `require` clause. That is precisely the reason the porting map rules out: on a
#   TOTAL carrier the analogue of PRECOND-TOO-STRONG is the OBLIGATION being
#   unsatisfiable at an F2P-shaped input, which a positive that discharges it at
#   that concrete input — by evaluation, as a `have`, before closing the frozen
#   obligation verbatim — tests directly. The old note also mis-stated the
#   fallback argument: "twelve rivals FAIL a postcondition" shows the post-image
#   is not degenerate (not met by EVERY impl), which is a different claim from
#   "the post-image is MEETABLE at the F2P points" and does not imply it. Both are
#   now demonstrated: the reject lane for the first, this case for the second.
# VACUOUS (frame-mut-set, frame-mut-dict): the sibling's TWO MANDATORY frame
#   rivals write into read-only inputs held at `Acc(list_pred(elems), 1/2)` /
#   `Acc(list_pred(flat), 1/2)`, tripping the insufficient-permission check. This
#   backend is referentially transparent: `elems` and `items` are immutable
#   values, no `mut` binder is declared for them, and there is no heap, no
#   aliasing, and no permission system. There is no read-only input to overwrite
#   and no frame clause to violate, so the class has no carrier analogue. Omitted
#   as a genuine carrier fact, NOT fabricated (porting map: vacuous on a
#   referentially-transparent backend).
#     DEMONSTRATED by the audit rather than asserted, since "vacuous on this
#     carrier" is the reason that has most often been measured wrong. RE-CONFIRMED
#     INDEPENDENTLY by the second audit: a fresh build assigning to the input
#     binder (`elems := []` as the first impl statement) reproduces the error text
#     below verbatim, exit 1, and the file does not compile. Two real
#     builds attempting the sibling's write: assigning to the input binder
#     (`elems := []`) and element-assigning through it (`elems := elems.set 0 …`)
#     BOTH fail to elaborate at the impl line with
#       error: `elems` cannot be mutated, only variables declared using `let mut`
#              can be mutated
#     followed by `Failed to parse an assertion without names: WPGen sorry` — the
#     file does not compile at all, so there is no rival to state a witness
#     against and the case is inexpressible rather than merely hard. This is a
#     TOOLING-clean refusal by the elaborator (the error names the binder and the
#     mutability rule, not the spec), which is the right kind of evidence here.
#     A third build confirms the carrier fact positively: mutating a LOCAL copy
#     (`let mut work : List Obj := elems`, then reading `work`) elaborates AND
#     VERIFIES, because a "mutation" on this carrier rebinds a local and cannot be
#     observed through the caller's immutable value. So the class is empty for the
#     stated reason.
# DIVERGENCE / NON-TERMINATION: the sibling carries NO diverge-*/nonterm-*/
#   weak-diverge case, so there is nothing to port. The semantics IS
#   `loom.semantics.termination "total"`, so this is NOT a `partial` hole. But the
#   earlier note called the class VACUOUS ("a diverging impl cannot be written in
#   the modeled core"), and the second audit measured that as WRONG in the
#   direction that matters: a diverging impl CAN be written, and IS rejected. The
#   class is therefore non-empty and the honest disposition is a KNOWN GAP in the
#   witness lane, not a vacuous class. Two real builds:
#     (a) loop with the `decreasing` clause REMOVED — exit 1 at the impl line:
#           error: Decreasing annotations are required in total correctness
#                  semantics
#         then `Failed to prove assertion without names: WPGen`. The termination
#         obligation is real and the rejection is attributable to it. But the same
#         elaborator error fires in the proof-STRIPPED witness file too, so the
#         rival half of the witness check (which must SUCCEED) cannot be built.
#     (b) loop KEEPING `decreasing i` whose body never decreases `i`
#         (`joined := joined`) — exit 1 with `unsolved goals` on the loop's
#         decreasing side-goal, so again a real, attributable rejection. Its
#         witness, however, is STUCK: `decide` on `printSetTester [{ reprText :=
#         ['C'], strText := ['c'] }] = false` against that rival fails with
#           did not reduce to `isTrue` or `isFalse`
#         which is the gate's own `_STUCK_REDUCTION` screen — on the RIVAL side,
#         the half required to succeed.
#   The two exhaust the shapes: a diverging impl must keep a loop, and a looping
#   rival is un-witnessable on this carrier for exactly the reason the frozen impl
#   is (CARRIER NOTE). So the lane is UNDERPORTED-BY-CARRIER: the obligation
#   rejects the class, and no witnessed case for it can be shipped here.
#
# BINDER / CLAUSE COVERAGE. The two `ensures` (`out = setRender elems`,
#   `out = dictRender items`) bind `out`, `elems`, and `items`. The models combine
#   a RECURSIVE-ELEMENT-TEXT sub-obligation (reprText vs strText), a BRACES
#   sub-obligation, an ENTRY/ELEMENT SEPARATOR sub-obligation, a KEY↦VALUE
#   SEPARATOR sub-obligation (dict), a KEY/VALUE ORDER sub-obligation (dict), an
#   EMPTY-COLLECTION TOKEN sub-obligation (set), and an ORDER/ELEMENT-WISE
#   sub-obligation. All are attacked:
#     * RECURSIVE ELEMENT TEXT: wrong-str-elem-set, wrong-str-elem-dict, and
#       partial-domain-first-set (the length-restricted first-element sub-domain).
#     * BRACES: paren-not-brace-set, paren-not-brace-dict.
#     * ENTRY/ELEMENT SEPARATOR: no-separator-set, no-separator-dict.
#     * KEY↦VALUE SEPARATOR: kv-separator-dict.
#     * KEY/VALUE ORDER: swap-key-value-dict.
#     * EMPTY-COLLECTION TOKEN: wrong-empty-literal-set (collection, "set()") and
#       wrong-empty-literal-dict (mapping, "{}"). AUDIT-2-ADDED — the two empty
#       tokens are DIFFERENT literals and only the collection's was pinned; every
#       shipped dict rival is a single unconditional `return` that renders the
#       empty mapping correctly, so the empty-mapping sub-domain had no rival at
#       all. Built and refuted before being added.
#     * ORDER / ELEMENT-WISE (fragment POSITION): reverse-order-set,
#       reverse-order-dict. AUDIT-ADDED — the original port listed this clause
#       and asserted "all are attacked", but shipped no rival that moved a
#       fragment's position; every original rival changes a fragment's TEXT, a
#       delimiter, a separator or the empty token, all of which are
#       order-agnostic. Both order rivals were built and refuted before being
#       added, so the claim is now demonstrated rather than asserted.
#   The Obj fields are load-bearing and varied: witnesses that key on the element
#   text set reprText ≠ strText (['x']≠['a'], ['A']≠['p'], ['K']≠['W'], ['x']≠['a']/
#   ['y']≠['b']); witnesses that ignore the element text (braces, separators, empty
#   token, order) hold reprText = strText, isolating the attacked clause. The
#   reject witnesses probe DISTINCT input points over list lengths {0, 1, 2} and
#   both element types (Obj / Obj×Obj).
#     NOTE on `pts`: the earlier draft of this footer claimed "pts=10". That is
#     not what scripts/pbt_coverage.py reports and was never measured — the
#     reporter counts distinct input points PER OBLIGATION, not per case, so the
#     reject cases split across the two methods (`printSet`, `printDict`) and
#     it reported pts=5-5. Do not restate a coverage number this file does not
#     compute; run the reporter.
# WITNESS DISCRIMINATION — INDEPENDENTLY RE-DERIVED by the second audit with real
#   `scripts/lean_verify.sh` builds: for each of the 12 then-shipped reject cases,
#   SEVEN builds (witness vs rival / gold / the set positive / the dict positive,
#   plus the flipped-claim forgery vs the positive / the rival / gold) = 84 builds,
#   and 6 more for the newly added `wrong-empty-literal-dict`. Every case behaved
#   as declared: rival exit 0, gold exit 1, own-method positive exit 1,
#   other-method positive exit 1. Each witness ELABORATES against its loop-free
#   rival (the extracted program's result provably violates the ensures at the
#   probed input, `<method>Tester … = false` closing by `decide`). The carrier is
#   fully concrete at every witness, so each closes by `decide` with no hypothesis;
#   `consistency_probe` returns nothing for all 13, so the gate's joint-
#   satisfiability probe is not reached. No `sorry`/`admit`/`native_decide`/`axiom`.
#
#   WHICH SUBJECT ACTUALLY REFUTES, precisely. The gold-side exit code is NOT by
#   itself the discrimination for 12 of the 13 reject cases. Measured gold-side text:
#     * wrong-empty-literal-set — gold refutes SEMANTICALLY: "Tactic `decide`
#       proved that the proposition `printSetTester [] = false` is false", i.e.
#       gold's tester IS true at `[]`. A real refutation against the frozen impl.
#       (Only here because `printSet` early-returns on `elems = []`, so no loop.)
#     * the other 12 — gold fails by STUCK REDUCTION: "`decide` failed … its
#       `Decidable` instance … did not reduce to `isTrue` or `isFalse`. After
#       unfolding the instances … reduction got stuck". The frozen impl's backward
#       `while` does not reduce in the kernel, so that exit code decides nothing on
#       its own (the gate screens exactly this as `witness-undecided`; see
#       gates/pbt.py _STUCK_REDUCTION, which this text matches).
#   For those 12 the gate falls back — as designed — to one of THIS battery's own
#   expect="verify" positives as the refutation subject: a loop-free impl of the
#   same spec that the gate independently re-verifies first. Measured, each of the
#   12 is refuted SEMANTICALLY ("`decide` proved … is false") against the positive
#   for its OWN method, and is STUCK against the positive for the other method (the
#   other positive still contains the frozen loop for this method). meta.json
#   records this per case as `witness_subject: "a verifying positive from this
#   battery (gold cannot decide)"`, with `wrong-empty-literal-set` alone recording
#   "the frozen solution". That is a sound attestation — an impl the verifier
#   ACCEPTS cannot violate its own spec — but it is a different claim from "fails
#   on gold", and the artifact says which it is.
#   FORGERY CONTROL (attack B′, 39 real builds across all 13 cases — the earlier
#   footer claimed 6 and covered only 2). The subject's exit code CARRIES
#   INFORMATION rather than failing for every claim. For each case the exact
#   OPPOSITE claim (`… = true`: "the impl is CORRECT at this input"):
#     * ELABORATES (exit 0) against the verifying positive for its own method —
#       so that subject decides the tester in BOTH directions, and its exit-1 on
#       the real witness is a verdict about the CLAIM, not a blanket failure;
#     * FAILS (exit 1) against the rival, with "`decide` proved … `= true` is
#       false" — the rival's tester really is `false` at the probed input;
#     * against GOLD, fails with the byte-identical stuck-reduction error as the
#       un-flipped witness for 12 of 13 (confirming gold's exit code carries NO
#       information there, which is exactly why the fallback subject is required
#       and why reading gold's exit 1 as the refutation would be hollow), and
#       ELABORATES (exit 0) for `wrong-empty-literal-set` — the one case where
#       gold does decide, and it decides the opposite way, as a real refutation
#       must. That asymmetry is the machine-checked proof that this case's gold
#       signature is semantic and the other twelve's are not.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   `axiom` (the per-element recursive text is a free input carrier and the
#   assembly is modeled deeply), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
