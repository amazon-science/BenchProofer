"""properties.py — G-PBT falsification battery for django__django-14155 (lean lane).

PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
over, the mechanics re-expressed against this backend's carrier. NOT a Lean
module — a manifest the runner parses. Each SPEC case is a FULL Solution.lean
variant that shares the FROZEN spec byte-for-byte (only the impl region — and,
for a positive that reshapes the impl, the proof body — is edited), so
variant_scope.same_spec holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec. Every
expect="reject" case carries a refutation `witness`: a self-contained snippet
that ELABORATES against the rival and FAILS on the frozen solution, so the
rejection is attributable to the spec and not to a tactic script that merely
stopped matching a reshaped impl.

DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
----------------------------------------------------------------------
The modeled function assembles the single-line human-readable representation of
a resolved match:

    implementation_resolverMatchRepr
        (funcIsPartial : Bool) (funcPath funcRepr : String)
        (args kwargs urlName appNames namespaces route : Rendered) : String

pinned by the single load-bearing clause `problem_spec_resolverMatchRepr`, a
string equality:

    result = "ResolverMatch(func=" ++ (if funcIsPartial then funcRepr else funcPath)
             ++ ", args=" ++ args.r ++ ", kwargs=" ++ kwargs.r
             ++ ", url_name=" ++ urlName.r ++ ", app_names=" ++ appNames.r
             ++ ", namespaces=" ++ namespaces.r ++ ", route=" ++ route.r ++ ")"

Two independently-fixed behaviours the nagini sibling identified live in that
clause, and both port here:
  (A) THE VIEW SLOT: it shows `funcRepr` when the view is a partial application
      and `funcPath` otherwise. A rival that mishandles the flag-dependent
      selection is refuted on the appropriate `funcIsPartial` value.
  (B) THE REMAINING SIX SLOTS render their REPRESENTATION form (`.r`), not their
      plain form (`.s`); for a text value the two differ (repr adds delimiting
      quotes). A rival that renders a slot with `.s` is refuted at an input whose
      two renderings differ.
There is additionally a STRUCTURAL fact the clause pins: the FIXED ORDER of the
seven labelled slots. A rival that transposes two slots is refuted by the string
equality even though every piece is individually well-formed.

CARRIER NOTE — what the Lean model computes vs. what it is GIVEN
---------------------------------------------------------------
Crucially, on this carrier the representation-form of each value (nagini's
behaviour B "quoting") is supplied as an INPUT field (`Rendered.r`), not computed
by the function under spec. The function only SELECTS between the plain and
representation forms (`.s` vs `.r`) and CONCATENATES them in order. So the
adversarial content that ports is: which form each slot selects (B), the
flag-dependent view selection (A), and the slot order (structural). The
carrier is fully transparent (a `String` built by `++` over literal `Rendered`
fields), so witnesses need no conditioning — `decide` reduces the equality at any
literal input.

WHICH NAGINI CASES PORT, WHICH ARE OMITTED
------------------------------------------
  * `pos-reorder` (nagini branch reorder of the func selection) -> `pos-reorder`
    — a structurally different CORRECT impl (view slot defaulted to funcRepr,
    overridden to funcPath on the non-partial branch). The FROZEN proof body
    (`cases funcIsPartial <;> rfl`) still closes, so no reproof.
  * added `pos-pure-expression` — a second correct impl written as a pure
    `String` expression (no `Id.run do`, no `let mut`), directly the spec's
    right-hand side. The frozen proof body still closes (the `if`-expression is
    definitionally the spec's). Stands as a soundness positive of a different
    impl SHAPE. If either fails => SPEC-TOO-STRONG.
    CAVEAT (audit): its body is the spec's RHS token-for-token, so it is
    `rfl`-trivial and tests only that the spec is not bound to the MONADIC
    wrapper. It cannot detect a spec over-fitted to the concatenation's own
    right-nested `++` grouping, because it reproduces that grouping exactly.
    `pos-reassociated` (added below) is the positive that carries that weight.
  * added `pos-reassociated` — a correct impl that RE-ASSOCIATES the seven
    concatenations (a head/mid/tail split with the pieces grouped left, then
    joined) so the result is NOT syntactically the spec's RHS and the frozen
    `rfl` genuinely does not close it: with the frozen proof body the build
    fails `(deterministic) timeout at whnf, maximum number of heartbeats`. It
    is REPROVEN (`simp [String.append_assoc]`), which the variant scope
    permits — the theorem STATEMENT stays byte-identical and no
    axiom/lemma/sorry is added. This is the only positive here whose passing is
    not `rfl`-trivial: it shows the spec constrains the string VALUE and not the
    parenthesisation used to build it.
  * `sel-always-path` (nagini `SEL_ALWAYS_PATH`, the PRE-PATCH view slot) ->
    `sel-always-path`. Attacks behaviour A on the partial sub-domain.
  * `sel-inverted` (nagini `SEL_INVERTED`) -> `sel-inverted`. Attacks behaviour A
    on both flag values.
  * `bare-text-fields` (nagini `BARE_TEXT_FIELDS`, the PRE-PATCH `%s`) ->
    `bare-text-fields`. Attacks behaviour B on TWO slots (url_name + route).
  * `partial-route-bare` (nagini `PARTIAL_ROUTE_BARE`) -> `partial-route-bare`.
    PARTIAL-DOMAIN: renders url_name correctly (`.r`) but route with `.s`.
  * `field-order-swap` (nagini `FIELD_ORDER_SWAP`) -> `field-order-swap`. Attacks
    the structural slot ORDER (url_name / route slots transposed).
  * added `args-kwargs-swap` — transposes the args and kwargs slots. Exercises
    the `args`/`kwargs` binders that nagini's carrier folded into a single
    ordered rendering and that no other witness here varies distinctly.
  * added `appnames-ns-swap` — transposes the app_names and namespaces slots.
    These were the two binders NO shipped case moved: before this case every
    rival left both bound to `appNames.r` / `namespaces.r`, and every witness
    supplied them with `.s == .r`, so the spec's dependence on that pair was
    entirely unprobed and a spec that dropped either constraint would have been
    certified SOUND. Its witness gives all six slots distinct `.r` values.
  * added `wrong-quote-char` — see the omission note below; this is the ported
    nagini `WRONG_QUOTE_CHAR`, which an earlier revision of this file wrongly
    recorded as inexpressible.
  * added `args-bare` and `kwargs-bare` — the args and kwargs slots rendered in
    their PLAIN form (`.s`) instead of their representation form (`.r`). The
    swap rivals (`args-kwargs-swap`) move those two binders' POSITIONS but leave
    both reading `.r`, and every other `.s`-vs-`.r` rival attacks only
    url_name/route, so before these two cases the spec's FORM selection on the
    args and kwargs slots was unprobed on this carrier: a spec that read
    `args.s`/`kwargs.s` would still have been certified SOUND by the rest of
    this battery. Their witnesses supply args/kwargs with `.s != .r`.

  * `WRONG_QUOTE_CHAR` (nagini) is NOT inexpressible — an earlier revision of
    this file recorded it as such, and the audit disproved that by landing it.
    The claim was that "the delimiter lives in the supplied `.r` string, so no
    impl can choose the wrong one". That confuses *reading* the supplied
    representation form with *fabricating* one: an impl is free to ignore `.r`
    and BUILD a delimited rendering itself, and the faithful port of nagini's
    attack is exactly that — wrap the PLAIN form in the wrong delimiter,
    `", url_name=" ++ ("\"" ++ urlName.s ++ "\"")`. That is a strictly stronger
    rival than `bare-text-fields`: the slot IS delimited, so a proxy checking
    only "is the text field wrapped in some quote" passes it, and only the
    exact-string equality refutes it. Shipped as `wrong-quote-char`.
  * FRAME-MUTATION (nagini's MANDATORY `FRAME_MUTATE_URLNAME`: url_name held at
    Acc(list_pred,1/2) read-only, rival wrote back into it). Lean is
    referentially transparent — no aliasing, no fractional permission — so a
    "mutate the read-only input" rival is not expressible; the whole lane is
    VACUOUS here. See 'assessment'.
  * ADMISSIBILITY (nagini's `ADMISS`, defending the half-permission Requires) ->
    `admiss-shaped-points`. An EARLIER revision of this file recorded this lane
    as N/A, reasoning that the lean obligation carries NO precondition
    hypothesis so nothing can be PRECOND-TOO-STRONG. A later audit rejected that
    reasoning and landed the case. The analogue of PRECOND-TOO-STRONG on a total
    carrier is not a false `Requires`: it is the OBLIGATION being unsatisfiable
    at exactly an F2P-shaped input — a postcondition so shaped that no impl,
    including the frozen one, can meet it at a realistic point. That is tested
    directly by discharging `problem_spec_resolverMatchRepr` at concrete
    F2P-shaped arguments, by evaluation, as a `have`, before closing the frozen
    obligation verbatim. Measured: the two `have`s close with `unfold …; rfl`
    (exit 0) and the case verifies; perturbing ONE claimed output character
    (dropping the url_name slot's delimiters) makes the same `have` fail
    `Tactic 'rfl' failed: The left-hand side …` (exit 1), so the probe is
    load-bearing and not a tautology. NOTE: `decide` does NOT work here —
    it hits `maximum recursion depth has been reached` on strings this long;
    `rfl` / `decide +kernel` / `simp` all close it.
  * DIVERGENCE / NON-TERMINATION — nagini carries no such case for this instance;
    and on lean `implementation_resolverMatchRepr` is a total Lean `def`, so a
    diverging impl cannot be written at all: genuinely vacuous.
  * AXIOM_TESTS — the axiom lane is G-AX's job; this gate ignores them. The
    assembly is modeled DEEPLY over transparent carriers with no consumed axiom.

Every reject witness probes a DISTINCT input point and moves the binders it
attacks (the view flag/paths, the per-slot form selection, the slot order), so
the battery exercises the spec's dependence on each. All witnesses were built
BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit 1). The carrier is
transparent, so no witness binds a hypothesis (nothing to be inconsistent).

AUDIT RECORD (independent re-derivation)
----------------------------------------
Every reject witness was rebuilt from scratch, both ways, with
scripts/lean_verify.sh: rival exit 0, gold exit 1 for all of them. The gold-side
failure was read, not just counted, and in every case it is the SEMANTIC form
`Tactic 'decide' proved that the proposition ... is false` — a decided
refutation of the concrete claim, never a stuck reduction, unknown identifier,
type error or timeout. No witness binds a head hypothesis, so no consistency
probe applies.

FORGERY TEST (does gold's exit code actually track the CLAIM?). For every reject
case the witness was rebuilt with its claim FLIPPED — the leading `¬` dropped, so
the file asserts the frozen impl IS correct at that same input, everything else
byte-identical. Result on all of them: flipped-claim-on-GOLD exit 0 (gold
satisfies the spec there, as it must) and flipped-claim-on-RIVAL exit 1
(`Tactic 'decide' proved that the proposition ... is false`). So each gold-side
exit code inverts exactly when the claim inverts: it carries information about
the claim and not about the file's shape. Combined with the unflipped pair
(rival 0 / gold 1) that is a genuine 4-way discrimination per case.

Gaps the port left, all closed above: the `app_names`/`namespaces` binder pair
was completely unprobed (`appnames-ns-swap`); the `WRONG_QUOTE_CHAR` omission was
expressible after all (`wrong-quote-char`); both shipped positives were
`rfl`-trivial with respect to the concatenation's grouping (`pos-reassociated`);
the FORM selection on the `args`/`kwargs` slots was unprobed, since the swap
rival moves their positions but leaves both reading `.r` (`args-bare`,
`kwargs-bare`); and the whole ADMISSIBILITY lane was recorded N/A on reasoning
that does not hold on a total carrier (`admiss-shaped-points`).

Attack D (new wrong impls not in the battery, each checked to be REJECTED with a
discriminating witness — none verified, so no spec hole): app_names rendered
`.s`; namespaces rendered `.s`; app_names/namespaces transposed; the
`", app_names="` label misspelled `", appNames="`; the closing `")"` dropped;
and a tuned near-miss that takes the partial branch only when `funcRepr != ""`
(refuted at `funcIsPartial=true, funcRepr=""`, the one input where it differs).
A later pass added five more, all likewise rejected with a discriminating witness
(rival exit 0 / gold exit 1): args rendered `.s`; kwargs rendered `.s` (both
promoted into the battery as `args-bare` / `kwargs-bare`); the view slot ALWAYS
`funcRepr`; a near-miss taking the partial branch when `funcIsPartial ||
funcPath == ""`, refuted at the single point `funcIsPartial=false, funcPath=""`;
and the `", route="` label written without its space, `",route="`.
Attack E (new correct reshapes, all VERIFIED, so no soundness hole): `s!`-string
interpolation; `match funcIsPartial with` in place of the `if`; the
re-association now shipped as `pos-reassociated`; a `List String` of the seven
pieces joined by `foldl (· ++ ·) ""` (reproved `simp [List.foldl,
String.append_assoc]`); and a route slot written as the conditional identity
`if route.s == route.r then route.s else route.r` (reproved by case split), which
verifies — so the spec does not merely demand the LITERAL token `route.r`, it
constrains the value that slot denotes.
"""
from pathlib import Path

INSTANCE = "django__django-14155"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmark — the full frozen impl body (Id.run do block, WITH its
# comments), lying ENTIRELY inside impl-start/impl-end and unique in the file
# (the spec region's concatenation is a distinct pure-`if` expression). Every
# rival and both positives swap THIS block wholesale; the proof body is left
# frozen (it still closes for both positives, and for the rivals the gate reads
# the witness, not the rival's own build).
# ---------------------------------------------------------------------------
_IMPL = (
    "def implementation_resolverMatchRepr\n"
    "    (funcIsPartial : Bool) (funcPath funcRepr : String)\n"
    "    (args kwargs urlName appNames namespaces route : Rendered)\n"
    "    : String := Id.run do\n"
    "  -- Choose the view slot: a partial application shows its own detailed\n"
    "  -- representation; any other view shows its dotted import path.\n"
    "  let mut func := funcPath\n"
    "  if funcIsPartial then\n"
    "    func := funcRepr\n"
    "  -- Assemble the line, rendering each remaining value in its representation form.\n"
    "  return \"ResolverMatch(func=\" ++ func ++\n"
    "    \", args=\" ++ args.r ++\n"
    "    \", kwargs=\" ++ kwargs.r ++\n"
    "    \", url_name=\" ++ urlName.r ++\n"
    "    \", app_names=\" ++ appNames.r ++\n"
    "    \", namespaces=\" ++ namespaces.r ++\n"
    "    \", route=\" ++ route.r ++ \")\""
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"


def _impl(sel: str, args="args.r", kwargs="kwargs.r", url="urlName.r",
          appn="appNames.r", ns="namespaces.r", route="route.r") -> str:
    """Build a full impl body: `sel` is the view-slot selection block (binds
    `func`), the six field slots select their form and order."""
    return (
        "def implementation_resolverMatchRepr\n"
        "    (funcIsPartial : Bool) (funcPath funcRepr : String)\n"
        "    (args kwargs urlName appNames namespaces route : Rendered)\n"
        "    : String := Id.run do\n"
        f"{sel}\n"
        "  return \"ResolverMatch(func=\" ++ func ++\n"
        f"    \", args=\" ++ {args} ++\n"
        f"    \", kwargs=\" ++ {kwargs} ++\n"
        f"    \", url_name=\" ++ {url} ++\n"
        f"    \", app_names=\" ++ {appn} ++\n"
        f"    \", namespaces=\" ++ {ns} ++\n"
        f"    \", route=\" ++ {route} ++ \")\""
    )


# The gold view-slot selection: default to the dotted path, override to the
# detailed representation for a partial application.
_SEL_GOLD = ("  let mut func := funcPath\n"
             "  if funcIsPartial then\n"
             "    func := funcRepr")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reorder: structurally-different but behaviourally identical view
# selection — DEFAULT to the detailed representation, override to the dotted path
# on the NON-partial branch. Output equals the frozen impl's on every input. The
# frozen `theorem correct_resolverMatchRepr` statement is kept byte-identical AND
# the frozen proof body (`cases funcIsPartial <;> rfl`) still closes (both branch
# orders reduce identically). No reproof, no new axiom/lemma/sorry.
_POS_REORDER = _swap(
    _BASE, _IMPL,
    _impl("  let mut func := funcRepr\n"
          "  if !funcIsPartial then\n"
          "    func := funcPath"))

# pos-pure-expression: a structurally different CORRECT impl written as a pure
# `String` expression (no `Id.run do`, no `let mut`, no early return), directly
# the spec's right-hand side. Semantics identical on every input. The theorem
# statement is byte-identical and the FROZEN proof body still closes (the
# `if`-expression is definitionally the spec's). No reproof needed.
_POS_PURE = _swap(
    _BASE, _IMPL,
    "def implementation_resolverMatchRepr\n"
    "    (funcIsPartial : Bool) (funcPath funcRepr : String)\n"
    "    (args kwargs urlName appNames namespaces route : Rendered)\n"
    "    : String :=\n"
    "  \"ResolverMatch(func=\" ++ (if funcIsPartial then funcRepr else funcPath) ++\n"
    "    \", args=\" ++ args.r ++\n"
    "    \", kwargs=\" ++ kwargs.r ++\n"
    "    \", url_name=\" ++ urlName.r ++\n"
    "    \", app_names=\" ++ appNames.r ++\n"
    "    \", namespaces=\" ++ namespaces.r ++\n"
    "    \", route=\" ++ route.r ++ \")\"")

# pos-reassociated: the positive that is NOT rfl-trivial. Both positives above
# reproduce the spec's right-nested `++` grouping verbatim, so `rfl` closes them
# and they cannot tell whether the spec constrains the string VALUE or merely the
# parenthesisation used to build it. This impl splits the assembly into head /
# mid / tail and RE-ASSOCIATES: `head ++ (mid ++ tail)` with the pieces grouped
# left. Same string on every input, but not the spec's RHS syntactically — with
# the frozen proof body the build fails `(deterministic) timeout at whnf,
# maximum number of heartbeats (200000)`, so this genuinely needs the reproof
# below. The theorem STATEMENT stays byte-identical and nothing is assumed (no
# axiom/lemma/sorry), which is exactly what the variant scope permits a
# soundness positive to do.
_POS_REASSOC = _swap(
    _BASE, _IMPL,
    "def implementation_resolverMatchRepr\n"
    "    (funcIsPartial : Bool) (funcPath funcRepr : String)\n"
    "    (args kwargs urlName appNames namespaces route : Rendered)\n"
    "    : String :=\n"
    "  let func := if funcIsPartial then funcRepr else funcPath\n"
    "  let head := \"ResolverMatch(func=\" ++ func\n"
    "  let mid := \", args=\" ++ args.r ++ (\", kwargs=\" ++ kwargs.r)\n"
    "  let tail := \", url_name=\" ++ urlName.r ++ (\", app_names=\" ++ appNames.r ++\n"
    "    (\", namespaces=\" ++ namespaces.r ++ (\", route=\" ++ route.r ++ \")\")))\n"
    "  head ++ (mid ++ tail)"
).replace("  cases funcIsPartial <;> rfl",
          "  cases funcIsPartial <;> simp [String.append_assoc]")
assert "String.append_assoc" in _POS_REASSOC, "reassoc reproof did not apply"


# ===========================================================================
# ADMISSIBILITY — must VERIFY (else PRECOND-TOO-STRONG / spec-shape regression).
#
# On this total carrier the frozen obligation carries no precondition
# hypothesis, so the nagini sibling's half-permission `Requires` has no direct
# analogue. The analogue of PRECOND-TOO-STRONG is instead the OBLIGATION being
# unsatisfiable at exactly an F2P-shaped input: a postcondition so shaped that
# no impl, the frozen one included, can meet it at a realistic point. This case
# tests that directly — it discharges `problem_spec_resolverMatchRepr` itself, by
# evaluation, at two concrete F2P-shaped argument tuples, as `have`s inside the
# impl region, and then closes the FROZEN obligation with the frozen impl body
# and frozen proof script verbatim. So the only thing it can fail on is the spec
# being unsatisfiable at those points.
#
# The two points span the flag: a plain view (funcIsPartial=false, so the view
# slot must show the dotted path) with positional arguments and a regex route,
# and a partial-application view (funcIsPartial=true, so the slot must show the
# callable's own detailed representation) with no positional arguments. Both
# supply text values whose plain and representation forms DIFFER (url_name and
# route are delimited in `.r`) and collection values whose forms coincide, which
# is the real shape of the inputs.
#
# TOOLING NOTE: `decide` fails here with `maximum recursion depth has been
# reached` — the `Decidable` instance for `String` equality reduces character by
# character and these strings are long. `rfl` closes both directly (kernel
# defeq); `decide +kernel` and `simp` also work. Measured load-bearing: dropping
# the url_name slot's delimiters from ONE claimed output makes that `have` fail
# `Tactic 'rfl' failed: The left-hand side …`, so this is not a tautology.
_ADMISS_HAVES = (
    '  have _h1 : problem_spec_resolverMatchRepr\n'
    '      false "pkg.views.plain_view" "<function plain_view at 0x7f0>"\n'
    '      { s := "(\'42\', \'37\')", r := "(\'42\', \'37\')" } { s := "{}", r := "{}" }'
    ' { s := "list-items", r := "\'list-items\'" } { s := "[]", r := "[]" }'
    ' { s := "[]", r := "[]" }'
    ' { s := "^items/([0-9]+)/([0-9]+)/$", r := "\'^items/([0-9]+)/([0-9]+)/$\'" }\n'
    '      "ResolverMatch(func=pkg.views.plain_view, args=(\'42\', \'37\'),'
    ' kwargs={}, url_name=\'list-items\', app_names=[], namespaces=[],'
    ' route=\'^items/([0-9]+)/([0-9]+)/$\')" := by\n'
    '    unfold problem_spec_resolverMatchRepr; rfl\n'
    '  have _h2 : problem_spec_resolverMatchRepr\n'
    '      true "pkg.views.plain_view"'
    ' "partial(<function plain_view at 0x7f0>, template_name=\'page.html\')"\n'
    '      { s := "()", r := "()" } { s := "{}", r := "{}" }'
    ' { s := "bound-view", r := "\'bound-view\'" } { s := "[]", r := "[]" }'
    ' { s := "[]", r := "[]" } { s := "bound-view/", r := "\'bound-view/\'" }\n'
    '      "ResolverMatch(func=partial(<function plain_view at 0x7f0>,'
    ' template_name=\'page.html\'), args=(), kwargs={}, url_name=\'bound-view\','
    ' app_names=[], namespaces=[], route=\'bound-view/\')" := by\n'
    '    unfold problem_spec_resolverMatchRepr; rfl'
)
_ADMISS = _swap(
    _BASE, "    : String := Id.run do\n",
    "    : String := Id.run do\n" + _ADMISS_HAVES + "\n")
assert "_h1" in _ADMISS and "cases funcIsPartial <;> rfl" in _ADMISS, \
    "admissibility probe did not apply / frozen proof body lost"


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is
# left in place (it will not close for the reshaped impl, but the gate reads the
# witness, checked in a file with the obligation removed).
# ===========================================================================

# sel-always-path: ignore funcIsPartial, ALWAYS name by the dotted path (the
# PRE-PATCH view slot: no partial handling). Attacks behaviour A on the partial
# sub-domain.
_RIV_ALWAYS_PATH = _swap(_BASE, _IMPL, _impl("  let func := funcPath"))

# sel-inverted: the view-slot choice exactly backwards — the detailed
# representation when NOT partial, the dotted path when partial. Wrong on both
# funcIsPartial values.
_RIV_INVERTED = _swap(
    _BASE, _IMPL,
    _impl("  let mut func := funcRepr\n"
          "  if funcIsPartial then\n"
          "    func := funcPath"))

# bare-text-fields: render url_name AND route in their PLAIN form (`.s`) — the
# PRE-PATCH `%s`. Attacks behaviour B on two slots.
_RIV_BARE = _swap(_BASE, _IMPL, _impl(_SEL_GOLD, url="urlName.s", route="route.s"))

# partial-route-bare: PARTIAL-DOMAIN. Render url_name correctly (`.r`) but route
# in its plain form (`.s`). Correct on the url_name slot, diverges only on route.
_RIV_ROUTE_BARE = _swap(_BASE, _IMPL, _impl(_SEL_GOLD, route="route.s"))

# field-order-swap: assemble route's rendering where url_name's should go and
# vice-versa. Each slot is individually well-formed; only their ORDER is wrong.
_RIV_ORDER = _swap(_BASE, _IMPL, _impl(_SEL_GOLD, url="route.r", route="urlName.r"))

# args-kwargs-swap: transpose the args and kwargs slots. Exercises the
# args/kwargs binders no other witness here distinguishes.
_RIV_ARGSKW = _swap(_BASE, _IMPL, _impl(_SEL_GOLD, args="kwargs.r", kwargs="args.r"))

# appnames-ns-swap: transpose the app_names and namespaces slots. These are the
# two binders NO other case moves — every other rival leaves both bound to
# appNames.r / namespaces.r, so without this case the spec's dependence on that
# pair is never exercised at all.
_RIV_APPNS = _swap(_BASE, _IMPL,
                   _impl(_SEL_GOLD, appn="namespaces.r", ns="appNames.r"))

# wrong-quote-char: the ported nagini WRONG_QUOTE_CHAR. Do not read the supplied
# representation form at all for the url_name slot — FABRICATE a delimited
# rendering from the plain form using the wrong delimiter (a double quote where
# the supplied representation form uses an apostrophe). Strictly stronger than
# `bare-text-fields`: the slot IS delimited, so a proxy asking only "is the text
# field wrapped in some quote" passes this rival; only the exact string equality
# refutes it.
_RIV_WRONGQ = _swap(_BASE, _IMPL,
                    _impl(_SEL_GOLD, url='("\\"" ++ urlName.s ++ "\\"")'))

# args-bare / kwargs-bare: render the args (resp. kwargs) slot in its PLAIN form
# (`.s`) where the spec pins its representation form (`.r`). These attack the FORM
# selection on the two binders that only the ORDER rivals touched: args-kwargs-swap
# moves their positions but leaves both reading `.r`, and every other .s-vs-.r
# rival attacks url_name/route only. Without these two the spec's form dependence
# on the args and kwargs slots is never exercised.
_RIV_ARGS_BARE = _swap(_BASE, _IMPL, _impl(_SEL_GOLD, args="args.s"))
_RIV_KWARGS_BARE = _swap(_BASE, _IMPL, _impl(_SEL_GOLD, kwargs="kwargs.s"))


# --- witnesses (checked with the obligation removed) -----------------------
# Each negates the spec predicate at one concrete literal input. The carrier is
# transparent (String `++` over literal Rendered fields), so `decide` closes the
# disequality and no witness binds a hypothesis. Each ELABORATES against its
# rival and FAILS against gold — SEEN to discriminate both ways.

def _wit(partial, fpath, frepr, args, kwargs, url, appn, ns, route) -> str:
    a = (f"{partial} \"{fpath}\" \"{frepr}\"\n"
         f"    {args} {kwargs} {url} {appn} {ns} {route}")
    return (
        "example : ¬ problem_spec_resolverMatchRepr\n"
        f"    {a}\n"
        "    (implementation_resolverMatchRepr\n"
        f"      {a}) := by\n"
        "  unfold problem_spec_resolverMatchRepr implementation_resolverMatchRepr\n"
        "  decide"
    )


def _r(s, r):
    return f'{{ s := "{s}", r := "{r}" }}'


# Distinct binder values per witness so each moves the positions it attacks and
# the battery probes six distinct input points.
_WIT_ALWAYS_PATH = _wit(  # partial view: gold => funcRepr "R1", rival => funcPath "P1"
    "true", "P1", "R1",
    _r("a1", "a1"), _r("k1", "k1"), _r("u1", "'u1'"),
    _r("an1", "an1"), _r("ns1", "ns1"), _r("ro1", "'ro1'"))
_WIT_INVERTED = _wit(  # non-partial: gold => funcPath "P2", rival => funcRepr "R2"
    "false", "P2", "R2",
    _r("a2", "a2"), _r("k2", "k2"), _r("u2", "'u2'"),
    _r("an2", "an2"), _r("ns2", "ns2"), _r("ro2", "'ro2'"))
_WIT_BARE = _wit(  # url_name/route .s ("u3","ro3") differ from .r: gold quotes, rival bare
    "false", "P3", "P3",
    _r("a3", "a3"), _r("k3", "k3"), _r("u3", "'u3'"),
    _r("an3", "an3"), _r("ns3", "ns3"), _r("ro3", "'ro3'"))
_WIT_ROUTE_BARE = _wit(  # route .s ("ro4") differs from .r ("'ro4'"); url_name correct
    "true", "P4", "P4",
    _r("a4", "a4"), _r("k4", "k4"), _r("u4", "'u4'"),
    _r("an4", "an4"), _r("ns4", "ns4"), _r("ro4", "'ro4'"))
_WIT_ORDER = _wit(  # url .r ("'u5'") != route .r ("'ro5'"), so the transposition shows
    "false", "P5", "P5",
    _r("a5", "a5"), _r("k5", "k5"), _r("u5", "'u5'"),
    _r("an5", "an5"), _r("ns5", "ns5"), _r("ro5", "'ro5'"))
_WIT_ARGSKW = _wit(  # args .r ("'a6'") != kwargs .r ("'k6'"), so the transposition shows
    "true", "P6", "R6",
    _r("a6", "'a6'"), _r("k6", "'k6'"), _r("u6", "'u6'"),
    _r("an6", "an6"), _r("ns6", "ns6"), _r("ro6", "'ro6'"))
_WIT_APPNS = _wit(  # appNames .r ("'an7'") != namespaces .r ("'ns7'"): the swap shows.
    # Every slot is given a DISTINCT representation form so the transposition
    # cannot be masked by two slots that happen to render alike.
    "false", "P7", "R7",
    _r("a7", "'a7'"), _r("k7", "'k7'"), _r("u7", "'u7'"),
    _r("an7", "'an7'"), _r("ns7", "'ns7'"), _r("ro7", "'ro7'"))
_WIT_ARGS_BARE = _wit(  # args .s ("a9") differs from .r ("'a9'"): the plain-form
    # read shows. kwargs is given .s == .r so the two new cases are not two
    # spellings of one point — this one moves ONLY the args binder's two forms.
    "true", "P9", "R9",
    _r("a9", "'a9'"), _r("k9", "k9"), _r("u9", "'u9'"),
    _r("an9", "an9"), _r("ns9", "ns9"), _r("ro9", "'ro9'"))
_WIT_KWARGS_BARE = _wit(  # kwargs .s ("k10") differs from .r ("'k10'"); args is
    # given .s == .r, the complement of the previous witness.
    "false", "P10", "R10",
    _r("a10", "a10"), _r("k10", "'k10'"), _r("u10", "'u10'"),
    _r("an10", "an10"), _r("ns10", "ns10"), _r("ro10", "'ro10'"))
_WIT_WRONGQ = _wit(  # url_name .s ("u8") delimited by the rival as "u8" (double
    # quote) where the spec pins the supplied .r ("'u8'", apostrophe): both are
    # delimited, so only the exact string equality separates them.
    "false", "P8", "R8",
    _r("a8", "a8"), _r("k8", "k8"), _r("u8", "'u8'"),
    _r("an8", "an8"), _r("ns8", "ns8"), _r("ro8", "'ro8'"))


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the view slot DEFAULTS to the "
            "detailed representation and is overridden to the dotted path on the "
            "non-partial branch (the frozen impl does the reverse). Output equals the "
            "frozen impl's on every input. The theorem statement is byte-identical and "
            "the FROZEN proof body (`cases funcIsPartial <;> rfl`) still closes — a "
            "faithful branch-order restructure with no reproof and no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to one syntactic branch order)."
        ),
    },
    {
        "id": "pos-pure-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure `String` "
            "expression (no `Id.run do`, no `let mut`, no early return), directly the "
            "spec's right-hand side. Semantics identical on every input. The theorem "
            "STATEMENT is byte-identical and the FROZEN proof body still closes (the "
            "`if`-expression is definitionally the spec's) — no reproof, no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (the postcondition is "
            "bound to the monadic impl shape rather than the behaviour). NOTE (audit): "
            "its body IS the spec's right-hand side token-for-token, so it is "
            "`rfl`-trivial — it isolates the monadic wrapper and nothing more. "
            "`pos-reassociated` is the positive that carries real weight."
        ),
    },
    {
        "id": "pos-reassociated",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REASSOC,
        "rationale": (
            "the one positive here that is NOT `rfl`-trivial. Both other positives "
            "reproduce the spec's right-nested `++` grouping verbatim, so they cannot "
            "distinguish a spec that constrains the string VALUE from one over-fitted "
            "to the parenthesisation used to build it. This impl splits the assembly "
            "into head/mid/tail and RE-ASSOCIATES (`head ++ (mid ++ tail)`, pieces "
            "grouped left): the same string on every input, but not the spec's "
            "right-hand side syntactically. Measured: with the FROZEN proof body the "
            "build fails `(deterministic) timeout at whnf, maximum number of heartbeats "
            "(200000)`, so the reproof is genuinely needed rather than cosmetic. It "
            "reproves with `simp [String.append_assoc]` — the theorem STATEMENT stays "
            "byte-identical and nothing is assumed (no axiom/lemma/sorry), which is "
            "what the variant scope permits a soundness positive to do. If it FAILS => "
            "SPEC-TOO-STRONG (the postcondition pins the concatenation's grouping, not "
            "the string it denotes)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-shaped-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "ports nagini's `ADMISS` lane, which an earlier revision of this file "
            "recorded as N/A on the ground that the lean obligation carries no "
            "precondition hypothesis. That ground was wrong: on a TOTAL carrier the "
            "analogue of PRECOND-TOO-STRONG is not a false `Requires` but the "
            "OBLIGATION being unsatisfiable at exactly an F2P-shaped input — a "
            "postcondition so shaped that no impl, the frozen one included, can meet "
            "it at a realistic point. This case tests that directly: it discharges "
            "`problem_spec_resolverMatchRepr` ITSELF, by evaluation, at two concrete "
            "F2P-shaped argument tuples, as `have`s inside the impl region, and then "
            "closes the FROZEN obligation with the frozen impl body and frozen proof "
            "script verbatim — so the only thing it can fail on is the spec being "
            "unsatisfiable at those points. The two points span the flag: a plain view "
            "(the slot must show the dotted path, positional args present, regex "
            "route) and a partial-application view (the slot must show the callable's "
            "own detailed representation, no positional args). Both supply text values "
            "whose plain and representation forms DIFFER and collection values whose "
            "forms coincide, which is the real input shape. Measured LOAD-BEARING, not "
            "a tautology: the `have`s close with `unfold …; rfl` (exit 0), and "
            "dropping the url_name slot's delimiters from ONE claimed output makes "
            "that same `have` fail `Tactic 'rfl' failed: The left-hand side …` "
            "(exit 1). TOOLING: `decide` is unusable here — `maximum recursion depth "
            "has been reached`, since String `DecidableEq` reduces character by "
            "character and these strings are long; `rfl`, `decide +kernel` and `simp` "
            "all close it. If it FAILS => PRECOND-TOO-STRONG / spec-shape regression "
            "(the postcondition is unsatisfiable at a realistic input)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "sel-always-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_PATH,
        "refinement": (
            "this is the PRE-PATCH view slot: name the view by its dotted path "
            "unconditionally, with no branch for a partial application. A partial-wrapped "
            "view then renders as the unhelpful plain 'functools.partial' form instead of "
            "its detailed representation. F2P test_repr_functools_partial asserts the "
            "partial shows its detailed representation; the old code fails it — does NOT "
            "resolve (it is the bug being fixed), so a verifying rival is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by behaviour A (the view slot). When funcIsPartial the spec "
            "demands funcRepr but the rival emits funcPath. Witness probes the "
            "partial sub-domain (funcIsPartial=true, funcPath != funcRepr). If it "
            "VERIFIES => SPEC-TOO-WEAK (the partial branch is unpinned)."
        ),
        "witness": _WIT_ALWAYS_PATH,
    },
    {
        "id": "sel-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INVERTED,
        "refinement": (
            "a real patch with the partial-application test inverted names a plain view "
            "by its detailed representation and a partial by its dotted path — the view "
            "slot backwards on BOTH flag values. Both F2P test_repr (plain view) and "
            "test_repr_functools_partial (partial view) assert the opposite tokens and "
            "would fail — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by behaviour A on BOTH funcIsPartial values (the selection is "
            "exactly backwards). Witness probes the NON-partial sub-domain "
            "(funcIsPartial=false, funcPath != funcRepr), the branch the previous rival "
            "leaves fixed. If it VERIFIES => SPEC-TOO-WEAK (the view selection is "
            "unpinned)."
        ),
        "witness": _WIT_INVERTED,
    },
    {
        "id": "bare-text-fields",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BARE,
        "refinement": (
            "this is the PRE-PATCH slot rendering: the url_name and route slots render "
            "their PLAIN display form instead of their representation form (the OLD `%s`, "
            "not the patched `%r`). F2P test_repr asserts url_name and route appear in "
            "their representation (quote-delimited) form; the old code emits them plain "
            "and fails — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by behaviour B on TWO slots: the spec pins urlName.r and route.r "
            "but the rival emits urlName.s and route.s. Witness uses a text input whose "
            "plain and representation forms differ (`.s`='u3'/'ro3', `.r`=\"'u3'\"/\"'ro3'\"), "
            "so the two renderings disagree. If it VERIFIES => SPEC-TOO-WEAK (the "
            "representation-form requirement is unpinned)."
        ),
        "witness": _WIT_BARE,
    },
    {
        "id": "partial-route-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ROUTE_BARE,
        "refinement": (
            "a real patch that switched ONLY the url_name slot to the representation form "
            "and forgot the route slot renders the route plain. F2P test_repr asserts the "
            "route in its representation (quote-delimited) form; an unquoted route fails "
            "that assertion — does NOT resolve."
        ),
        "rationale": (
            "PARTIAL-DOMAIN: correct on the url_name slot (urlName.r), diverges only on "
            "the route slot (emits route.s where the spec pins route.r). A value-proxy "
            "checking only url_name would miss it. Witness varies the `route` binder at a "
            "text input whose two forms differ. If it VERIFIES => SPEC-TOO-WEAK on the "
            "route slot."
        ),
        "witness": _WIT_ROUTE_BARE,
    },
    {
        "id": "field-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ORDER,
        "refinement": (
            "a real patch with the url_name and route placeholders/arguments transposed "
            "prints the route under the url_name label and vice-versa. F2P test_repr pins "
            "the exact slot order (url_name then route); the transposition fails — does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the fixed slot ORDER of the string equality (url_name slot then "
            "route slot). Each slot is individually well-formed but their order is wrong. "
            "Witness uses distinct url_name.r vs route.r so the transposition is "
            "observable. If it VERIFIES => SPEC-TOO-WEAK (the slot order is unpinned)."
        ),
        "witness": _WIT_ORDER,
    },
    {
        "id": "args-kwargs-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ARGSKW,
        "refinement": (
            "a real patch with the args and kwargs arguments transposed prints the "
            "positional arguments under the kwargs label and vice-versa. F2P test_repr "
            "pins the args slot then the kwargs slot with distinct values; the "
            "transposition fails — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the fixed slot ORDER: the spec pins args.r then kwargs.r, the "
            "rival emits kwargs.r then args.r. Varies the `args` and `kwargs` binders "
            "distinctly (args.r='a6' != kwargs.r='k6') — binders no other witness here "
            "distinguishes. If it VERIFIES => SPEC-TOO-WEAK on the args/kwargs slots."
        ),
        "witness": _WIT_ARGSKW,
    },
    {
        "id": "appnames-ns-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_APPNS,
        "refinement": (
            "a real patch with the app_names and namespaces arguments transposed prints "
            "the namespace chain under the app_names label and vice-versa. F2P test_repr "
            "pins the app_names slot then the namespaces slot; the transposition fails "
            "that assertion — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the fixed slot ORDER: the spec pins appNames.r then "
            "namespaces.r, the rival emits namespaces.r then appNames.r. Added by audit "
            "to close a real coverage gap — app_names and namespaces are the two binders "
            "NO other case in this battery moves (every other rival leaves both bound "
            "correctly, and every other witness supplies them with `.s == .r`), so "
            "without this case a spec that dropped either constraint would still be "
            "certified SOUND. Its witness gives all six slots DISTINCT representation "
            "forms so the swap cannot be masked by two slots rendering alike. If it "
            "VERIFIES => SPEC-TOO-WEAK on the app_names/namespaces slots."
        ),
        "witness": _WIT_APPNS,
    },
    {
        "id": "args-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ARGS_BARE,
        "refinement": (
            "a real patch that switched the text slots to the representation form but "
            "left the args slot on the old plain form renders the positional arguments "
            "in their plain display form. F2P test_repr pins the args slot's "
            "representation form; a plain-form args slot fails that assertion — does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by behaviour B on the args slot: the spec pins args.r, the rival "
            "emits args.s. Added by audit to close a real coverage gap — before this "
            "case the FORM selection on the args and kwargs slots was unprobed. "
            "`args-kwargs-swap` moves those two binders' POSITIONS but leaves both "
            "reading `.r`, and every other .s-vs-.r rival attacks url_name/route only, "
            "so a spec that read args.s would still have been certified SOUND. Witness "
            "supplies args with .s='a9' != .r=\"'a9'\" while kwargs has .s == .r, so "
            "this probes the args binder alone. If it VERIFIES => SPEC-TOO-WEAK on the "
            "args slot's form."
        ),
        "witness": _WIT_ARGS_BARE,
    },
    {
        "id": "kwargs-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KWARGS_BARE,
        "refinement": (
            "a real patch that switched the text slots to the representation form but "
            "left the kwargs slot on the old plain form renders the keyword arguments "
            "in their plain display form. F2P test_repr pins the kwargs slot's "
            "representation form; a plain-form kwargs slot fails that assertion — does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by behaviour B on the kwargs slot: the spec pins kwargs.r, the "
            "rival emits kwargs.s. The complement of `args-bare` — its witness "
            "supplies kwargs with .s='k10' != .r=\"'k10'\" while args has .s == .r, so "
            "the two cases probe DISTINCT binders and are not two spellings of one "
            "point. If it VERIFIES => SPEC-TOO-WEAK on the kwargs slot's form."
        ),
        "witness": _WIT_KWARGS_BARE,
    },
    {
        "id": "wrong-quote-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONGQ,
        "refinement": (
            "a real patch that hand-wrote a delimited rendering for the text slot "
            "instead of taking the value's representation form would emit the wrong "
            "delimiter (a double quote where the representation form of these "
            "apostrophe-free values uses an apostrophe). F2P test_repr asserts the "
            "url_name slot apostrophe-delimited; a double-quoted one fails that "
            "assertion — does NOT resolve."
        ),
        "rationale": (
            "the ported nagini WRONG_QUOTE_CHAR, which an earlier revision of this file "
            "recorded as inexpressible on this carrier; the audit disproved that by "
            "landing it. The rival ignores the supplied representation form for the "
            "url_name slot and FABRICATES a delimited rendering from the plain form with "
            "the wrong delimiter. Strictly stronger than `bare-text-fields`: that rival "
            "emits an UNdelimited slot, while this one emits a delimited slot with the "
            "wrong delimiter, so a proxy asking only 'is the text field wrapped in some "
            "quote' passes it and only the exact string equality refutes it. Witness "
            "probes an input whose plain and representation forms differ. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the slot's exact delimiter is unpinned)."
        ),
        "witness": _WIT_WRONGQ,
    },
]


# No consumed axioms and no opaque callees: the representation forms are supplied
# as inputs (Rendered.r) and the assembly is a transparent String concatenation,
# so the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
