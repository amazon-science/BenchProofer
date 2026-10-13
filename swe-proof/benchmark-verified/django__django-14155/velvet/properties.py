"""properties.py — G-PBT falsification battery for django__django-14155 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct resolverMatchRepr`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  resolverMatchRepr (m : MatchView) return (out : String)
    require asciiOpt m.urlName
    require asciiOpt m.route
    ensures out = matchRepr m

The method renders a resolved-URL match object as its single human-readable text
line. The match is abstracted to the nine observable facts the line reads
(``isPartialFunc`` / ``funcPartialText`` / ``funcPath`` / ``argsText`` /
``kwargsText`` / ``urlName`` / ``appNamesText`` / ``namespacesText`` / ``route``).
The sole ensures pins the whole rendered line as a total function of those facts:

  matchRepr m
    = "ResolverMatch(func=" ++ (if m.isPartialFunc then m.funcPartialText
                                                    else m.funcPath)
      ++ ", args=" ++ m.argsText ++ ", kwargs=" ++ m.kwargsText
      ++ ", url_name=" ++ quotedOpt m.urlName
      ++ ", app_names=" ++ m.appNamesText ++ ", namespaces=" ++ m.namespacesText
      ++ ", route=" ++ quotedOpt m.route ++ ")"

Two independently-fixed behaviours live in that clause (they are exactly the two
places the change is observable — mapping.md §2a):

  (A) the CALLABLE token: a callable carrying pre-bound arguments is shown by its
      full textual form (``funcPartialText``); an ordinary callable by its
      dotted path (``funcPath``). Selected by ``isPartialFunc``.
  (B) the two string-valued fields ``urlName`` / ``route`` render QUOTED
      (``quotedOpt`` = ``None`` when absent, else ``quoted``, which wraps in the
      apostrophe delimiter and escapes) — NOT as the bare underlying text.

The container-valued fields (args/kwargs/app_names/namespaces) are carried
verbatim as already-rendered text: on those types the host str/repr coincide, so
the change is observationally inert there and there is nothing to attack (only
(A) and (B) carry the fix; mapping.md §2a). ``built_repr`` is NOT an opaque
answer-key: ``matchRepr`` is a concrete concatenation of literal fragments with
the SELECTED func token and the QUOTED text fields, every piece a function of the
argument, so there is no wrong value an impl could "echo" — computing it
correctly IS the work. Hence no echo case; the soundness lane carries an honest
structurally-different positive control instead.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop), so
each reject rival carries a machine-checked refutation ``witness`` — a Velvet
tester statement ``resolverMatchReprTester <m> = false`` at ONE concrete
``MatchView``, checked in a file whose ``prove_correct`` block has been stripped
so no tactic script can mask the verdict. Two carrier regimes:

  * behaviour (A) rivals mis-select the func token, observable with BOTH string
    fields absent (``urlName := none`` / ``route := none``), so ``quotedOpt``
    reduces to the literal ``"None"`` and the whole tester settles under
    ``decide`` with no conditioning.
  * behaviour (B) and structural rivals need a present string field, which drives
    ``quoted`` — and ``quoted`` calls ``String.contains``, whose byte-position
    ``anyAux`` recursion the kernel's ``decide`` will NOT reduce (and the workspace
    exposes no ``String.contains``→``List`` rewrite through ``Velvet.Std`` alone;
    adding an import would break ``same_spec``). So those witnesses CONDITION ON
    THE CARRIER: they assume the concrete value of ``quoted`` at the probed string
    (e.g. ``hq : quoted "no" = "'no'"``) and rewrite by it, after which the tester
    is decidable. Each such hypothesis is individually TRUE (``#eval`` confirms
    ``quoted "no" = "'no'"``), so the binders are jointly satisfiable and the
    gate's inconsistency probe cannot derive ``False`` from them; each is at most
    two hypotheses (one per present string field). Both halves were checked
    out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES against
    its rival and FAILS on the frozen solution, and the gold-side failure is in
    every case the SEMANTIC message ``Tactic `decide` proved that the proposition
    ... is false`` — a refutation the kernel actually performed, never a stuck
    reduction, an unknown identifier or a type error. The conditioning really is
    forced: the same witnesses stated WITHOUT their hypothesis, and with
    ``quoted``/``escChar``/``hexDigit`` added to the unfolding chain instead, both
    fail on the RIVAL with ``Tactic `decide` failed`` on an unreduced
    ``String.contains`` — so the hypothesis is not a convenience.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` (mapping.md §3);
``quoted`` / the verbatim-carried renderings are deep-model references, and this
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14155"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl-region anchors. Each lies ENTIRELY inside the method's
# `-- impl-start` / `-- impl-end` block and is UNIQUE in the file (the pure
# `matchRepr` spec carries the same lines at a SHALLOWER indent — anchoring on
# the impl's indentation keeps every edit inside the impl region, so the spec
# view is untouched and same_spec holds by construction). `_swap` asserts
# uniqueness, so any drift breaks the manifest at load.
# ---------------------------------------------------------------------------

# (A) the func-token selection, impl copy (4-space indent).
_SEL = "    let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath"

# (B) the url_name field, impl copy (6-space indent).
_URL = '      ", url_name=" ++ quotedOpt m.urlName ++'

# (B) the route field, impl copy (6-space indent).
_ROUTE = '      ", route=" ++ quotedOpt m.route ++ ")"'

# The frozen proof, verbatim. A correct reshape may retune THIS block (elided
# from the spec view); rivals leave it as-is — their rejection is carried by the
# witness, not the tactic script.
_PROOF = "prove_correct resolverMatchRepr by\n  loom_solve <;> simp_all [matchRepr]"

assert _BASE.count(_SEL) == 1, "func-selection impl anchor drifted"
assert _BASE.count(_URL) == 1, "url_name impl anchor drifted"
assert _BASE.count(_ROUTE) == 1, "route impl anchor drifted"
assert _BASE.count(_PROOF) == 1, "proof region drifted"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `resolverMatchReprTester <m> = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. The precondition
# ---- `asciiOpt` is not auto-decidable (a `∀ … < 128` under an `Option` match),
# ---- so its decidability instance is discharged explicitly; the postcondition
# ---- side is left to inference. Checked in a file whose `prove_correct` block
# ---- has been stripped.
_TESTER = (
    "extract_program_for resolverMatchRepr\n"
    "prove_precondition_decidable_for resolverMatchRepr by\n"
    "  all_goals (unfold asciiOpt; split <;> infer_instance)\n"
    "prove_postcondition_decidable_for resolverMatchRepr\n"
    "derive_tester_for resolverMatchRepr\n\n"
)

# Unfolding chain that drives the tester to a ground proposition. `quoted` is NOT
# in the list: on the (A) witnesses both string fields are `none` so `quotedOpt`
# never reaches `quoted`; on the (B)/structural witnesses `quoted <s>` is
# supplied as a conditioning hypothesis and rewritten by name (appended below).
_SIMP = ("resolverMatchReprTester, resolverMatchReprExec, resolverMatchRepr, "
         "NonDetT.run, matchRepr, quotedOpt, asciiOpt")


def _view(isPartial, funcPartialText, funcPath, argsText, kwargsText,
          urlName, appNamesText, namespacesText, route):
    def opt(x):
        return "none" if x is None else f'some "{x}"'
    return ("{ isPartialFunc := %s, funcPartialText := \"%s\", funcPath := \"%s\", "
            "argsText := \"%s\", kwargsText := \"%s\", urlName := %s, "
            "appNamesText := \"%s\", namespacesText := \"%s\", route := %s }"
            % ("true" if isPartial else "false", funcPartialText, funcPath,
               argsText, kwargsText, opt(urlName), appNamesText,
               namespacesText, opt(route)))


def _witness(view, binders="", hyps=()):
    """Tester witness at `view`. `binders` is the example's head (conditioning
    hypotheses, e.g. `(hq : quoted "no" = "'no'")`); each name in `hyps` is
    added to the `simp only` set so `quoted <s>` is rewritten by it."""
    head = f"example {binders}: resolverMatchReprTester {view} = false := by"
    extra = "".join(f", {h}" for h in hyps)
    return _TESTER + head + f"\n  simp only [{_SIMP}{extra}]\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. (Sibling: pos-reorder.)
    # =====================================================================
    {
        "id": "pos-negate-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the func-token selection: negate the guard and take the
        # ordinary-callable case first, the partial case last. Same value on
        # every input (the guard picks `funcPath` exactly where the frozen guard
        # did not). Pure branch reorder; the reproof is `loom_solve` plus a case
        # split on the flag.
        "module": _swap(
            _swap(_BASE, _SEL,
                  "    let funcStr := if !m.isPartialFunc then m.funcPath "
                  "else m.funcPartialText"),
            _PROOF,
            "prove_correct resolverMatchRepr by\n"
            "  loom_solve <;> simp_all [matchRepr] <;> "
            "(cases m.isPartialFunc <;> simp_all)"),
        "rationale": "negating the `isPartialFunc` guard and taking the "
        "ordinary-callable branch first computes the SAME func token on both "
        "flag values (`!isPartialFunc` selects `funcPath` exactly where the "
        "frozen guard did), so `out = matchRepr m` still holds on the whole "
        "domain; a correct reshape must verify, else SPEC-TOO-STRONG on branch "
        "order.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method DOES carry a precondition (`asciiOpt` on both
    # string fields), so the sibling's "a normal F2P-shaped input satisfies the
    # precondition" probe is live. This in-region assert pins, at an F2P-shaped
    # point, that (a) both `require asciiOpt` clauses are satisfiable by a normal
    # input, and (b) the discriminating (A) arm is NON-DEGENERATE — a present
    # (partial) callable renders by its full textual form and NOT by its dotted
    # path, so the choice really does fork the two. The rest of the impl is kept
    # verbatim so the method's own obligation still discharges; the proof is
    # retuned only to also clear the assert. String fields are `none` in the
    # asserted point so the assert stays `decide`-able without conditioning.
    # =====================================================================
    {
        "id": "admiss-fields",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, "    -- impl-start\n" + _SEL,
                  "    -- impl-start\n"
                  "    assert (with_name_prefix `admiss\n"
                  "      (asciiOpt (some \"no\") ∧ asciiOpt (none : Option String) ∧\n"
                  "       matchRepr { isPartialFunc := true, funcPartialText := \"pt\", "
                  "funcPath := \"fp\", argsText := \"a\", kwargsText := \"k\", "
                  "urlName := none, appNamesText := \"an\", namespacesText := \"ns\", "
                  "route := none }\n"
                  "         = \"ResolverMatch(func=pt, args=a, kwargs=k, url_name=None, "
                  "app_names=an, namespaces=ns, route=None)\" ∧\n"
                  "       matchRepr { isPartialFunc := true, funcPartialText := \"pt\", "
                  "funcPath := \"fp\", argsText := \"a\", kwargsText := \"k\", "
                  "urlName := none, appNamesText := \"an\", namespacesText := \"ns\", "
                  "route := none }\n"
                  "         ≠ \"ResolverMatch(func=fp, args=a, kwargs=k, url_name=None, "
                  "app_names=an, namespaces=ns, route=None)\"))\n" + _SEL),
            _PROOF,
            "prove_correct resolverMatchRepr by\n"
            "  loom_solve <;> simp_all [matchRepr, asciiOpt, quotedOpt]"),
        "rationale": "an in-region assert establishes (a) both `require asciiOpt` "
        "clauses hold of a normal input (an ASCII name, an absent route), so the "
        "precondition is not vacuously unsatisfiable — else PRECOND-TOO-STRONG; "
        "and (b) the discriminating (A) arm is non-degenerate: at a partial "
        "callable the line surfaces the full textual form (`func=pt`) and NOT the "
        "dotted path (`func=fp`), so the choice genuinely forks. The impl is kept "
        "verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each refuted at a concrete `MatchView` by a witness
    # that FAILS on the frozen solution, with the refinement argument that its
    # faithful real counterpart would NOT resolve the F2P.
    # =====================================================================

    # --- (A) selection rivals: mis-select the func token. Both string fields are
    #     absent in the witness so `quotedOpt` reduces to the literal "None" and
    #     the tester settles under plain `decide`.
    {
        "id": "sel-always-path",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the flag, always name by the dotted path (the pre-change
        # behaviour). Correct for an ordinary callable, wrong for a partial one.
        "module": _swap(_BASE, _SEL, "    let funcStr := m.funcPath"),
        "refinement": "always naming by the dotted path is the pre-change "
        "behaviour: a callable carrying pre-bound arguments is shown by an "
        "unhelpful generic token instead of its full textual form. Its faithful "
        "counterpart is the unchanged repo, which the F2P subtest asserting the "
        "full textual form for such a callable fails — it would NOT resolve (it "
        "is the bug being fixed).",
        "rationale": "REJECT from `out = matchRepr m` on the (A) arm: when "
        "`isPartialFunc` the post-image demands `funcPartialText`, but the rival "
        "emits `funcPath`. Refuted at a PARTIAL callable (`isPartialFunc := "
        "true`) whose two func forms differ (`P` vs `Q`) — the sub-domain where "
        "this rival is wrong and the ordinary-callable inputs are correct.",
        "witness": _witness(
            _view(True, "P", "Q", "a", "k", None, "an", "ns", None)),
    },
    {
        "id": "sel-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Selection exactly backwards: dotted path when partial, full form when
        # ordinary. Wrong on BOTH flag values' token.
        "module": _swap(_BASE, _SEL,
                        "    let funcStr := if m.isPartialFunc then m.funcPath "
                        "else m.funcPartialText"),
        "refinement": "inverting the selection names an ordinary callable by the "
        "form reserved for a partial one and vice-versa; both F2P subtests assert "
        "the opposite tokens, so neither branch renders as the tests demand — it "
        "would NOT resolve.",
        "rationale": "REJECT from `out = matchRepr m` on the (A) arm, wrong on "
        "both flag values. Refuted at an ORDINARY callable (`isPartialFunc := "
        "false`) whose two func forms differ — VARIES the `isPartialFunc` binder "
        "against sel-always-path (true there, false here), so the pair "
        "demonstrates the spec's dependence on the flag in both directions.",
        "witness": _witness(
            _view(False, "P", "Q", "a", "k", None, "an", "ns", None)),
    },

    # --- (B) quoting rivals: mis-render the two string fields. A present string
    #     field drives `quoted`, which the kernel `decide` cannot reduce, so each
    #     witness conditions on the concrete value of `quoted` at its probed
    #     string (a single TRUE hypothesis per present field).
    {
        "id": "bare-text-fields",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit both string fields BARE (the pre-change `%s`, no quoting).
        "module": _swap(
            _swap(_BASE, _URL, '      ", url_name=" ++ (m.urlName.getD "None") ++'),
            _ROUTE, '      ", route=" ++ (m.route.getD "None") ++ ")"'),
        "refinement": "rendering the two string fields bare is the pre-change "
        "behaviour (the old `%s`, not `%r`). The F2P subtest asserts those fields "
        "QUOTED (wrapped in apostrophes); the bare rendering fails it — the "
        "unchanged repo, which would NOT resolve.",
        "rationale": "REJECT from `out = matchRepr m` on the (B) quoting arm: the "
        "post-image demands `quoted urlName` ([apostrophe]+name+[apostrophe]) but "
        "the rival emits the bare name. Refuted at a present url_name (`some "
        "\"no\"`) whose quoted form (`'no'`) differs from the bare form (`no`); "
        "conditions on `quoted \"no\" = \"'no'\"` (a true fact). Exercises the "
        "`urlName` binder at `some`, which the (A) rivals hold at `none`.",
        "witness": _witness(
            _view(False, "P", "Q", "a", "k", "no", "an", "ns", None),
            binders='(hq : quoted "no" = "\'no\'") ', hyps=("hq",)),
    },
    {
        "id": "partial-route-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # Quote url_name correctly but leave ROUTE bare. Correct on the url_name
        # field; wrong only on the route field — a value-proxy checking only
        # url_name would miss it.
        "module": _swap(_BASE, _ROUTE,
                        '      ", route=" ++ (m.route.getD "None") ++ ")"'),
        "refinement": "a real patch that quoted the name but forgot the route "
        "field renders the route bare. The F2P subtest asserts the route QUOTED; "
        "the bare route fails that assertion — it would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: correct on the url_name field, diverges only "
        "on the route field. REJECT from the `quoted route` sub-term of the "
        "post-image. Refuted at a present route (`some \"xy\"`) with url_name "
        "ABSENT — isolating the route arm — conditioning on `quoted \"xy\" = "
        "\"'xy'\"`. Exercises the `route` binder at `some`, VARIED against the (A) "
        "rivals (none) and against bare-text-fields (none).",
        "witness": _witness(
            _view(False, "P", "Q", "a", "k", None, "an", "ns", "xy"),
            binders='(hq : quoted "xy" = "\'xy\'") ', hyps=("hq",)),
    },
    {
        "id": "wrong-quote-char",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrap url_name in DOUBLE quotes instead of the apostrophe delimiter.
        # Structurally a delimited field, but the wrong delimiter — a mask that
        # only checked "wrapped in some quote" would pass; the spec pins the
        # exact apostrophe.
        "module": _swap(
            _BASE, _URL,
            '      ", url_name=" ++ (match m.urlName with '
            '| none => "None" | some s => "\\"" ++ s ++ "\\"") ++'),
        "refinement": "a real patch hand-writing a double-quoted field instead of "
        "the standard repr rendering wraps an apostrophe-free name in double "
        "quotes, where the standard rendering uses the apostrophe. The F2P subtest "
        "asserts the apostrophe-delimited form; the double-quoted form fails it — "
        "it would NOT resolve.",
        "rationale": "value-level double-mask: REJECT from `quoted urlName`, which "
        "pins the delimiter CHOICE RULE rather than one fixed mark — the "
        "apostrophe is selected for every value that does not itself contain an "
        "apostrophe, and this rival hard-codes the double quote there. Refuted at "
        "a present url_name (`some \"no\"`, apostrophe-free) whose quoted form is "
        "apostrophe-wrapped (`'no'`) while the rival emits double quotes "
        "(`\"no\"`); conditions on `quoted \"no\" = \"'no'\"`. A proxy checking only "
        "'wrapped in some quote' would pass this rival. NOTE (audit): the "
        "delimiter is NOT unconditionally the apostrophe — on a value containing "
        "an apostrophe and no double quote the spec itself switches to the double "
        "quote (`quoted \"a'b\" = \"a'b\"` in double quotes, #eval-confirmed), so "
        "this rival is wrong on the apostrophe-free sub-domain only, and the "
        "SWITCH clause is the separate obligation `delim-switch-dropped` attacks.",
        "witness": _witness(
            _view(False, "P", "Q", "a", "k", "no", "an", "ns", None),
            binders='(hq : quoted "no" = "\'no\'") ', hyps=("hq",)),
    },
    {
        "id": "field-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Assemble the route's value where the url_name's should go and
        # vice-versa. Each field is individually well-formed (both quoted); only
        # their ORDER in the concatenation is wrong.
        "module": _swap(
            _swap(_BASE, _URL, '      ", url_name=" ++ quotedOpt m.route ++'),
            _ROUTE, '      ", route=" ++ quotedOpt m.urlName ++ ")"'),
        "refinement": "a real patch with the two quoted placeholders transposed "
        "prints the route under the url_name label and vice-versa. The F2P subtest "
        "pins the exact field order (the name, then the route); the transposition "
        "fails it — it would NOT resolve.",
        "rationale": "REJECT from the post-image's fixed concatenation ORDER "
        "(`url_name=` quoted(urlName) … `route=` quoted(route)); each piece is "
        "well-formed but their order is wrong. Refuted at a point where the two "
        "string fields DIFFER (`urlName := some \"no\"`, `route := some \"xy\"`) so "
        "the swap is observable — conditioning on `quoted \"no\"` and `quoted "
        "\"xy\"`. Exercises BOTH string binders at distinct `some` values.",
        "witness": _witness(
            _view(False, "P", "Q", "a", "k", "no", "an", "ns", "xy"),
            binders='(hq1 : quoted "no" = "\'no\'") (hq2 : quoted "xy" = "\'xy\'") ',
            hyps=("hq1", "hq2")),
    },

    # --- (B') INTERNAL-STRUCTURE rivals of the quoted rendering. Added by the
    #     AUDIT: every rival above is wrong about WHETHER the string fields are
    #     delimited at all (or by which mark, on the apostrophe-free sub-domain).
    #     None of them is wrong about the two clauses INSIDE the rendering — the
    #     delimiter-SWITCH rule and the per-character ESCAPING — so each was
    #     attested only by the frozen impl's own shape. A rival that gets the
    #     delimiting right and one inner clause wrong distinguishes them.
    {
        "id": "delim-switch-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Delimit and escape correctly, but ALWAYS with the apostrophe: drop the
        # rule that a value containing an apostrophe (and no double quote) wraps
        # in double quotes instead. Correct on every apostrophe-free value — the
        # whole sub-domain the rivals above probe — and wrong only where the
        # switch fires, so nothing already in this battery discriminates it.
        "module": _swap(
            _BASE, _URL,
            '      ", url_name=" ++ (match m.urlName with\n'
            '        | none => "None"\n'
            '        | some s =>\n'
            '          "\'" ++ String.join (s.toList.map (escChar \'\\\'\')) ++ "\'") ++'),
        "refinement": "a real patch hand-rolling the quoted rendering with a fixed "
        "apostrophe delimiter — escaping each inner apostrophe rather than "
        "switching the wrapping mark — renders a name containing an apostrophe "
        "with the apostrophe backslash-escaped, where the host's standard text "
        "rendering re-wraps that value in double quotes and leaves it unescaped. "
        "The two forms are different text, so an assertion pinning the host form "
        "fails on such a value — it would NOT resolve.",
        "rationale": "REJECT from the delimiter-SWITCH clause of `quoted`: the "
        "post-image selects the double quote when the value contains an "
        "apostrophe and no double quote, and this rival always selects the "
        "apostrophe. PARTIAL-DOMAIN and strictly finer than wrong-quote-char, "
        "which is wrong exactly where this rival is RIGHT: refuted at `urlName := "
        "some \"a'b\"`, an apostrophe-BEARING value (a binder point no other case "
        "in this battery reaches — every other witness probes apostrophe-free "
        "text), conditioning on the true fact `quoted \"a'b\"` = that value wrapped "
        "in DOUBLE quotes.",
        "witness": _witness(
            _view(False, "P", "Q", "a", "k", "a\\'b", "an", "ns", None),
            binders='(hq : quoted "a\'b" = "\\"a\'b\\"") ', hyps=("hq",)),
    },
    {
        "id": "escaping-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrap the route in the apostrophe delimiter but insert the underlying
        # text VERBATIM: no per-character escaping at all. Correct on every value
        # with nothing to escape (every string the other witnesses probe), wrong
        # as soon as the value carries a backslash — which route patterns
        # routinely do (`\d{4}`; mapping.md §2).
        "module": _swap(
            _BASE, _ROUTE,
            '      ", route=" ++ (match m.route with | none => "None" '
            '| some s => "\'" ++ s ++ "\'") ++ ")"'),
        "refinement": "a real patch that wrapped the route in quote marks by hand "
        "instead of deferring to the host's standard text rendering emits a "
        "backslash-bearing route with its backslash unescaped, where the standard "
        "rendering doubles it. Route patterns are regexes and carry backslashes "
        "routinely, so the rendered line differs from the asserted one — it would "
        "NOT resolve.",
        "rationale": "REJECT from the per-character ESCAPING clause of `quoted` "
        "(`escChar`): the post-image doubles an inner backslash, and this rival "
        "carries it through verbatim. PARTIAL-DOMAIN: indistinguishable from the "
        "frozen impl on every escape-free value, so it is exactly the rival the "
        "other (B) cases cannot see. Refuted at `route := some \"\\d\"`, a "
        "backslash-bearing route (a sub-domain no other witness here reaches), "
        "conditioning on the true fact that its quoted form doubles the "
        "backslash.",
        "witness": _witness(
            _view(False, "P", "Q", "a", "k", None, "an", "ns", "\\\\d"),
            binders='(hq : quoted "\\\\d" = "\'\\\\\\\\d\'") ', hyps=("hq",)),
    },
    {
        "id": "absent-marker-quoted",
        "kind": "uniqueness",
        "expect": "reject",
        # Quote the ABSENT marker as well: render a missing route as the literal
        # `None` WRAPPED in the delimiter. Correct on every present value; wrong
        # only on the absent one — the `quotedOpt none` arm, which every rival
        # above renders correctly (they all agree with the frozen impl there).
        "module": _swap(_BASE, _ROUTE,
                        '      ", route=" ++ quoted (m.route.getD "None") ++ ")"'),
        "refinement": "a real patch that routed the absent case through the same "
        "quoting as a present one renders a match with no route pattern as a "
        "QUOTED `None` rather than the bare literal. An assertion pinning the bare "
        "absent marker fails on any match whose route is unset — it would NOT "
        "resolve.",
        "rationale": "REJECT from the ABSENT arm of `quotedOpt`, which fixes the "
        "bare literal `None` and not a delimited one. PARTIAL-DOMAIN, and the "
        "complement of every other (B) rival: those are wrong only where a string "
        "field is PRESENT and correct on `none`, this one is correct on every "
        "present value and wrong only on `none` — so the two directions of the "
        "`Option` binder are now each independently defended. Refuted at `route := "
        "none` (with url_name also absent), conditioning on the true fact `quoted "
        "\"None\" = \"'None'\"`.",
        # `Option.getD` joins the rewrite set here: the rival reaches `quoted`
        # through `m.route.getD "None"`, which `simp only` must collapse to the
        # literal before `hq` can fire (verified out-of-band — without it the
        # rival-side `decide` is stuck on the unreduced `getD`).
        "witness": _witness(
            _view(False, "P", "Q", "a", "k", None, "an", "ns", None),
            binders='(hq : quoted "None" = "\'None\'") ',
            hyps=("Option.getD", "hq")),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases: 1 soundness
# positive (pos-reorder), 1 admissibility (admiss-fields), 1 MANDATORY
# frame-mutation rival (frame-mutate-urlname), and 6 uniqueness rivals
# (sel-always-path, sel-inverted, bare-text-fields, partial-route-bare,
# wrong-quote-char, field-order-swap). Every one is accounted for.
#
#   sibling case            -> here                 disposition
#   ---------------------------------------------------------------------------
#   pos-reorder             -> pos-negate-guard     RE-AIMED (reshape of the
#                                                    func-token choice; the
#                                                    sibling reorders the same
#                                                    branch)
#   admiss-fields           -> admiss-fields        PORTED (re-aimed at the live
#                                                    `asciiOpt` precondition +
#                                                    (A)-arm non-degeneracy)
#   frame-mutate-urlname    -> (none)               VACUOUS
#   sel-always-path         -> sel-always-path      PORTED (A arm)
#   sel-inverted            -> sel-inverted         PORTED (A arm)
#   bare-text-fields        -> bare-text-fields     PORTED (B arm)
#   partial-route-bare      -> partial-route-bare   PORTED (B arm, partial domain)
#   wrong-quote-char        -> wrong-quote-char     PORTED (B arm, delimiter)
#   field-order-swap        -> field-order-swap     PORTED (structural)
#
# 6 uniqueness rivals ported 1:1 (behaviours A and B both defended), 1 positive
# re-aimed, 1 admissibility ported, 1 frame-mutation vacuous.
#
# ADDED BY AUDIT (no sibling counterpart — these attack clauses the carrier
# EXPOSES and nagini's byte-list model did not have):
#   delim-switch-dropped    the delimiter-SWITCH rule inside `quoted`
#   escaping-dropped        the per-character ESCAPING rule (`escChar`)
#   absent-marker-quoted    the ABSENT arm of `quotedOpt`
# The ported six are all wrong about WHETHER (or, on the apostrophe-free
# sub-domain, with WHICH mark) a string field is delimited; none is wrong about
# what happens INSIDE the rendering or on the `none` constructor. On the sibling
# carrier that gap did not exist — `quoted` there was literally
# `[39] + s + [39]`, with no switch rule and no escaping to get wrong. On THIS
# carrier `quoted` is a real function with three independent clauses, so three
# rivals that keep the delimiting and break one clause each were expressible and
# unattacked. Each was landed with a rebuilt discriminating witness (rival exit
# 0, gold exit 1 by a semantic `decide` refutation, consistency probe exit 1).
#
# VACUOUS (frame-mutate-urlname): the sibling's MANDATORY frame-mutation rival
#   keeps the gold body then WRITES into a read-only sequence input that carries
#   only a fractional heap permission, and is rejected for INSUFFICIENT
#   PERMISSION. Lean and Velvet are referentially transparent: every parameter is
#   an immutable value, this method declares no `mut` binder, there is no heap and
#   no aliasing. There is no read-only input to overwrite and no permission system
#   to trip, so the class is vacuous. No substitute is fabricated.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# UNGROUNDED-ORACLE ECHO — N/A. The post-image is `matchRepr m`, a concrete `def`
#   over the method's own argument; the `axioms` region is empty. There is no
#   answer-key to echo — computing the concatenation correctly IS the work — so
#   the honest positive is the cheapest faithful reshape (pos-negate-guard).
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the input binders the
#   post-image reads (9 reject cases, 9 distinct input points):
#     isPartialFunc — true  (sel-always-path),
#                     false (sel-inverted, and the (B)/structural rivals):
#                     VARIED true/false, not held fixed.
#     urlName       — none  (sel-always-path, sel-inverted, partial-route-bare,
#                     escaping-dropped, absent-marker-quoted),
#                     some "no" (bare-text-fields, wrong-quote-char,
#                     field-order-swap), some "a'b" (delim-switch-dropped):
#                     `none`, an escape-free value, AND an apostrophe-bearing
#                     value that flips the delimiter choice — three points that
#                     each land on a DIFFERENT branch of `quoted`, not three
#                     spellings of one.
#     route         — none  (both (A) rivals, bare-text-fields, wrong-quote-char,
#                     delim-switch-dropped, absent-marker-quoted),
#                     some "xy" (partial-route-bare, field-order-swap),
#                     some "\d" (escaping-dropped): both constructors, plus a
#                     backslash-bearing value that fires `escChar`'s escape arm.
#   Every independent behaviour of the post-image is attacked: the (A) func-token
#   selection (both flag values); the (B) quoting of BOTH string fields
#   (jointly and each in isolation); the delimiter CHOICE on the apostrophe-free
#   sub-domain (wrong-quote-char) AND the delimiter-SWITCH rule on the
#   apostrophe-bearing one (delim-switch-dropped); the per-character ESCAPING
#   (escaping-dropped); the ABSENT arm of `quotedOpt` (absent-marker-quoted);
#   and the field ORDER. The container-valued fields are carried verbatim
#   (str/repr coincide; mapping.md §2a), so they are inert and correctly not
#   attacked — audited: transposing argsText/kwargsText IS rejected by the spec
#   with a discriminating witness, so the frame is pinned; the case is not
#   shipped because its faithful counterpart is not a reachable patch (the two
#   containers are distinct attributes, not a format-string clause the change
#   touches).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (mapping.md §3), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
