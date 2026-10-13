# properties.py — G-PBT falsification battery for django__django-11749 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over and the mechanics re-expressed against this backend's carrier. Each SPEC case
# is a FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive honestly reproves, the proof body — differs),
# checked by variant_scope before the verifier runs. Every expect="reject" case
# carries a refutation `witness`: a snippet that ELABORATES against the rival and
# FAILS on the frozen solution, so the rejection is attributable to the spec and not
# to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   requiredOptionArgs
#     (actions : List ParserAction) (groups : List ExclusiveGroup)
#     (optionKeys : List String) (argOptions : List (String × String))
#     (parseArgsPrefix : List String)
#     : Option (List String)
#   One obligation, `theorem correct_requiredOptionArgs`, with NO precondition
#   hypothesis: the postcondition must hold for every value of all five binders.
#   The single load-bearing clause is
#       result = (renderAll argOptions
#                   (actions.filter (keepAction groups optionKeys))).map
#                 (fun rendered => parseArgsPrefix ++ rendered)
#   which pins FOUR independent things at once, each attacked below:
#     (a) SELECTION — `keepAction groups optionKeys opt` =
#         `destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt)`:
#         an action is selected iff the caller NAMED its destination AND it is
#         required either individually or by virtue of belonging to a group that is
#         itself required. Three independent bits, hence three sub-domains. Note the
#         selection consults `optionKeys` and NOTHING else: the value table
#         `argOptions` has no say in which actions are selected.
#     (b) STRUCTURE — the selected actions appear in DECLARATION ORDER, all of them,
#         appended after the frame-pinned `parseArgsPrefix` which is reproduced
#         verbatim (directive 5: the unchanged component is pinned, not left free).
#     (c) RENDERING — each selected action renders from its LEXICOGRAPHICALLY LEAST
#         flag, not an arbitrary one, paired with the value `argOptions` carries at
#         that action's destination: `leastFlag? opt.optionStrings` and
#         `argOptions.lookup opt.dest` combined as `flag ++ "=" ++ value`.
#     (d) DEFINEDNESS — the carrier is `Option (List String)`, and the whole result
#         is `none` exactly when some SELECTED action fails to render, which happens
#         for EITHER of TWO independent reasons: the action has no least flag (it
#         declares no flag at all), or the value table carries nothing at its
#         destination. Both lookups in `renderArg?` are PARTIAL by construction and
#         `renderAll` propagates either failure across the selected run, so the
#         postcondition pins not only WHAT is forwarded but WHERE the computation is
#         defined. The two reasons are SEPARATELY attackable: a rival may agree
#         everywhere the result is defined and still TOTALIZE one of them, so
#         weak-totalize-missing-flag and weak-totalize-missing-value below refute
#         one each. The second one is load-bearing precisely because selection and
#         value lookup read DIFFERENT inputs: a named destination is not the same
#         thing as a carried key, so a selected action whose destination the value
#         table does not carry is an ordinary reachable input, not a corner case.
#         Notably the frame-pinned prefix is NOT reproduced when the result is
#         `none`: partiality dominates the append, so a rival that emitted the
#         prefix alone at such an input would also differ.
#
# WHAT THE NAGINI BATTERY ATTACKED, AND WHERE IT LANDS HERE. The nagini sibling
# abstracted the same decision to a fold over a `List[int]` in which each declared
# option was one integer whose low three bits encoded (supplied, individually
# required, in a mandated set), behind a fractional read permission. This backend
# models the same decision over a transparent record carrier, so every nagini
# sub-domain has a DIRECT counterpart, and the carrier is strictly RICHER: the three
# bits become three real inputs (`optionKeys`, `opt.req`, and `groups` + membership),
# and four components nagini's integer encoding could not express — the frame-pinned
# prefix, the rendering of each selected action, and the two independent ways the
# whole result can be undefined — become attackable too. Each of nagini's four
# partial-domain rivals plus both of its mechanical near-misses is ported; eight
# further rivals exist only because this carrier is richer (the audit added
# weak-group-membership-by-dest, weak-totalize-missing-flag and, after the
# faithfulness review, weak-select-on-value-table / weak-totalize-missing-value).
#
# The DISCRIMINATING content of the change (refinement.md, G-DIFF): an action that
# was SUPPLIED and belongs to a REQUIRED group but is NOT individually required MUST
# be selected. Dropping the group disjunct is the pre-change behaviour and is the
# headline rival (weak-drop-required-group) — its faithful real counterpart is the
# un-patched selection, which does not resolve the sole F2P.
#
# The carrier is transparent (no `opaque` callee, no answer-key) but PARTIAL in TWO
# places, so
# every witness states `¬ problem_spec_… … (implementation_… …)` at CONCRETE literal
# inputs and is closed by `decide` — no conditioning on the carrier is needed and no
# witness binds a hypothesis. Rendering forces a lexicographic `String` comparison
# whenever an action declares two or more flags, and kernel reduction of that
# comparison gets stuck at `String.decidableLT'`, so a witness whose PINNED side has
# to render such an action would fail by STUCK REDUCTION rather than by refutation
# and would discriminate nothing. Every witness therefore holds the RENDERED actions
# at a single flag; the one case that must vary the flag list into non-lexicographic
# order (weak-render-first-flag) supplies the comparison as a PROVED rewrite over the
# rendering's own `leastFlag?` projection and hands it to `simp`. See the TACTIC NOTE
# on that case for the measurement that fixed its shape: an earlier formulation
# supplied the comparison at the `String` level, which `simp` never reached because it
# had already unfolded the comparison to `List Char` — leaving the goal open on BOTH
# sides and making the gold-side exit code independent of what the witness claimed.
# Every witness here is a proved fact, not an assumption: none binds a hypothesis, so
# there is nothing that could be inconsistent.
#
# EVIDENCE THAT EACH GOLD-SIDE FAILURE TRACKS THE CLAIM (the property that makes a
# rejection attributable to the spec rather than to a tactic mismatch). Measured, per
# class, by building the witness and its exact OPPOSITE (the same input with the `¬`
# dropped, i.e. asserting the frozen impl is CORRECT there) against both subjects:
#   * the `decide` class (thirteen cases): the opposite claim BUILDS against the frozen
#     solution (exit 0) and FAILS against the rival (exit 1) — the exact mirror of the
#     witness itself. The kernel evaluates both sides, so the exit code is a verdict on
#     the claim, and the gold-side message is `decide` reporting the negation false.
#   * weak-render-first-flag (the one `simp` case): same mirror after the repair —
#     opposite claim builds on gold, fails on the rival; the witness fails on gold with
#     `simp` having reduced the goal to `False`, i.e. it PROVED the rendering equation
#     for the frozen impl and could not for the rival.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submission for the full list):
#   * FRAME-MUTATION (nagini's uniq-frame-mutate, its self-declared #1 class: the
#     declared-options list was held at half permission and the rival wrote into it).
#     Lean is referentially transparent — no aliasing, no fractional permission — so
#     "store into a read-only input" is not expressible and the lane is VACUOUS here.
#     Its ARGUMENT (the input must survive untouched) does have a counterpart, and it
#     is ported as weak-drop-prefix, which attacks the frame-pinned component the
#     spec states explicitly.
#   * ADMISSIBILITY. This lane DOES port, and the argument that it does not was wrong.
#     "The frozen obligation has no precondition hypothesis" is true and is not a
#     reason: on this carrier the analogue of PRECOND-TOO-STRONG is the obligation
#     being UNSATISFIABLE at exactly an F2P-shaped input — a postcondition no impl
#     could meet there would let every rival AND the frozen impl fail alike, and the
#     uniqueness lane cannot see it because it only ever asks whether two impls
#     DIFFER. `pos-admissible-f2p-input` below tests it directly, by discharging the
#     postcondition at the concrete F2P-shaped input by EVALUATION as a `have`, before
#     closing the frozen obligation verbatim. The lane matters MORE on a partial
#     carrier, not less: a postcondition that forced `none` at the F2P input would
#     look like a perfectly ordinary spec to every uniqueness case here.
#   * DIVERGENCE / NON-TERMINATION. The nagini sibling carries no such case, and on
#     this backend the class is genuinely vacuous: `implementation_requiredOptionArgs`
#     is a total Lean `def` into `Option` (partiality is in the VALUE, not in the
#     reduction), so a diverging implementation cannot be written at all. (Contrast
#     velvet under partial termination semantics, where it is a real
#     spec hole.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores it. There is no
#     consumed axiom anyway (the changed selection is modeled deeply).
from pathlib import Path

INSTANCE = "django__django-11749"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside impl-start/impl-end (or, for _PROOF,
# proof-start/proof-end) and is unique in the frozen file, so the manifest breaks
# loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------
_GUARD = ("    if destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt) then\n")
_LOOP = "  for opt in actions do\n"
_INIT = "  let mut parseArgs := parseArgsPrefix\n"
_APPEND = "      parseArgs := parseArgs ++ [← renderArg? argOptions opt]\n"
_SIG = "    Option (List String) := do\n"
_BODY = _INIT + _LOOP + _GUARD + _APPEND + "  return parseArgs"
# The frozen closing script of `correct_requiredOptionArgs`. The `show` re-states
# the desugared `forIn`/`Option.bind` skeleton the do-notation elaborates to, which
# is why it is load-bearing rather than cosmetic: `rw` cannot see the loop through
# the `do` block's `have`-bindings without it.
_PROOF = (
    "  intro actions groups optionKeys argOptions parseArgsPrefix\n"
    "  unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs\n"
    "  show Option.bind (forIn actions parseArgsPrefix (fun opt r =>\n"
    "      (if keepAction groups optionKeys opt then\n"
    "        Option.bind (renderArg? argOptions opt)\n"
    "          (fun s => some (ForInStep.yield (r ++ [s])))\n"
    "      else some (ForInStep.yield r) : Option (ForInStep (List String)))))\n"
    "      (fun r => some r) = _\n"
    "  rw [forIn_requiredOptionArgs actions groups optionKeys argOptions"
    " parseArgsPrefix]\n"
    "  cases renderAll argOptions (actions.filter (keepAction groups optionKeys))"
    " <;> rfl"
)
for _a in (_GUARD, _LOOP, _INIT, _APPEND, _SIG, _BODY, _PROOF):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted: {_a!r}")


# ---------------------------------------------------------------------------
# Witness vocabulary. Concrete carrier literals, chosen so that every INPUT
# BINDER of the spec predicate is VARIED across the reject witnesses:
#   * `actions` varies in length (0-element selection, 1, 2), in `req`, in `dest`,
#     in `optionStrings` (single flag vs two flags out of lexicographic order vs
#     NO flag at all, one of the two points where the rendering is undefined);
#   * `groups` varies over [] / one required group / one non-required group;
#   * `optionKeys` varies over a named matching destination vs a non-matching one;
#   * `argOptions` varies over carrying a value at the selected action's
#     destination vs carrying none there (the other point where the rendering is
#     undefined) vs carrying one at a destination no action was selected on — the
#     three configurations that matter once selection and value lookup are read
#     from two SEPARATE inputs;
#   * `parseArgsPrefix` varies over [] / ["app"] / ["app", "sub"].
# The default in the helpers below is the ALIGNED pair (the caller names exactly
# the destinations the value table carries), so a witness that does not care about
# the distinction reads exactly as it did before; the two cases that DO care state
# the two lists independently.
# ---------------------------------------------------------------------------
# a supplied group member that is NOT individually required — the configuration the
# sole F2P constructs (two flags in a group declared required, each member not).
_A_GROUP_MEMBER = ('{ id := 1, optionStrings := ["--foo-id"], req := false, '
                   'dest := "foo_id" }')
# an individually-required action carrying TWO flags, in no group. Only ever used
# at inputs where the PINNED result does NOT select it (so the pinned side never
# renders it); see _A_INDIVIDUAL_ONE_FLAG for why that matters.
_A_INDIVIDUAL = ('{ id := 2, optionStrings := ["--need-me", "-n"], req := true, '
                 'dest := "needme" }')
# an individually-required action carrying ONE flag, in no group. Needed wherever
# the PINNED result selects and therefore RENDERS the action: rendering forces the
# lexicographic minimum of the flags, and kernel reduction of `String` `<` gets
# stuck at `String.decidableLT'`, so a two-flag action makes `decide` report stuck
# reduction rather than a verdict on the side that has to render it. With a single
# flag the minimum is the head and no comparison is reached, so the claim decides.
_A_INDIVIDUAL_ONE_FLAG = ('{ id := 7, optionStrings := ["--need-me"], '
                          'req := true, dest := "needme" }')
# an individually-required action declaring NO flag at all — the point where the
# rendering, and hence the whole result, is UNDEFINED. Used only by
# weak-totalize-missing-flag, the case that attacks component (d).
_A_NO_FLAG = ('{ id := 8, optionStrings := [], req := true, dest := "reqpos" }')
# two individually-required actions, used to probe order and completeness.
_A_FIRST = '{ id := 3, optionStrings := ["--bar"], req := true, dest := "bar" }'
_A_SECOND = '{ id := 4, optionStrings := ["--zzz"], req := true, dest := "zzz" }'
# an action required neither individually nor by a group.
_A_OPTIONAL = '{ id := 5, optionStrings := ["--opt"], req := false, dest := "opt" }'
# an action whose flags are declared OUT of lexicographic order.
_A_FLIPPED = ('{ id := 6, optionStrings := ["--zeta", "--alpha"], req := true, '
              'dest := "flip" }')


def _group(required, members):
    return (f'{{ required := {str(required).lower()}, '
            f'groupActions := [{", ".join(members)}] }}')


def _lst(xs):
    return "[" + ", ".join(xs) + "]"


def _opts(pairs):
    return "[" + ", ".join(f'("{k}", "{v}")' for k, v in pairs) + "]"


def _strs(xs):
    return "[" + ", ".join(f'"{x}"' for x in xs) + "]"


def _aligned(pairs):
    """The (optionKeys, argOptions) pair for a caller who named exactly the
    destinations the value table carries — the ordinary configuration, in which the
    two inputs agree and the distinction between them is invisible."""
    return _strs([k for k, _ in pairs]), _opts(pairs)


_DECIDE = "  decide"


def _wit(actions, groups, option_keys, arg_options, prefix, note,
         tactic=_DECIDE):
    """A refutation witness: `¬ problem_spec_… args (implementation_… args)` at a
    concrete literal input. Elaborates against a rival whose result differs from the
    pinned one there; fails on the frozen solution, which satisfies the spec at every
    input. No binders, so nothing to be jointly satisfiable.

    `option_keys` and `arg_options` are the two SEPARATE inputs the predicate reads:
    the destinations the caller named, and the value table consulted at a selected
    action's destination. Most witnesses hold them ALIGNED (`_aligned` below builds
    both from one list of pairs) because they attack selection, order, the prefix or
    the flag choice, none of which depends on the alignment; the two that attack the
    value lookup itself state them independently."""
    args = (f"{actions}\n      {groups}\n      {option_keys} {arg_options}"
            f" {prefix}")
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_requiredOptionArgs\n"
        f"    {args}\n"
        f"    (implementation_requiredOptionArgs\n"
        f"      {args}) := by\n"
        f"  unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs\n"
        f"{tactic}"
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls that
# must VERIFY (else SPEC-TOO-STRONG). Each keeps `theorem correct_requiredOptionArgs`
# byte-identical in STATEMENT and, where the reshape breaks the frozen tactic script,
# reproves it honestly inside proof-start/proof-end — no new axiom, lemma, sorry or
# native_decide. Ports the nagini sibling's two soundness controls (pos-control-helper
# and pos-control-local), plus one this carrier makes available.
# ===========================================================================

# pos-consult-keep-predicate: the port of nagini's pos-control-helper. Replace the
# INLINED selection expression with the shared predicate `keepAction`, whose body is
# literally that same expression. Same loop, same accumulation; the frozen proof still
# closes because the spec's own filter is stated over `keepAction`.
_POS_KEEP = _swap(_BASE, _GUARD,
                  "    if keepAction groups optionKeys opt then\n")

# pos-commuted-conjunction: the port of nagini's pos-control-local — a reshape of the
# executable form that leaves the value identical on every input. The two conjuncts of
# the selection test are COMMUTED (`&&` on Bool is commutative, both sides total), a
# shape a faithful patch could equally take. The frozen script no longer closes the
# commuted test, so it is reproved by rewriting with `Bool.and_comm` back to
# `keepAction` and then invoking the frozen loop lemma. A genuine reproof of the same
# obligation, not a weakening.
_POS_COMMUTED = _swap(
    _swap(_BASE, _GUARD,
          "    if (opt.req || inRequiredGroup groups opt)\n"
          "        && destInOptions optionKeys opt then\n"),
    _PROOF,
    "  intro actions groups optionKeys argOptions parseArgsPrefix\n"
    "  unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs\n"
    "  have hc : ∀ opt : ParserAction,\n"
    "      ((opt.req || inRequiredGroup groups opt)\n"
    "        && destInOptions optionKeys opt)\n"
    "        = keepAction groups optionKeys opt := by\n"
    "    intro opt\n"
    "    unfold keepAction\n"
    "    exact Bool.and_comm _ _\n"
    "  simp only [hc]\n" + _PROOF.split("\n", 2)[2],
)

# pos-declarative: the cheapest HONEST impl — build the result declaratively instead
# of by accumulation, propagating partiality through `renderAll` rather than through
# the loop's `←`. This is NOT an ungrounded-oracle echo: the pinned expression is a
# transparent function of the five inputs (a filter, a partial render, and a map over
# the argument carrier), with no axiomatized answer-key to echo, so computing it IS
# doing the work and any WRONG value — or a value defined at a point the spec leaves
# undefined — fails the postcondition (the fifteen rivals below demonstrate that).
# The proof collapses to `rfl` after unfolding. Stands in for the grounded-oracle
# control nagini recorded as N/A for the same reason.
_POS_DECLARATIVE = _swap(
    _swap(_BASE, _SIG + _BODY,
          "    Option (List String) :=\n"
          "  (renderAll argOptions\n"
          "      (actions.filter (keepAction groups optionKeys))).map\n"
          "    (fun rendered => parseArgsPrefix ++ rendered)"),
    _PROOF,
    "  intro actions groups optionKeys argOptions parseArgsPrefix\n"
    "  unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs\n"
    "  rfl",
)


# pos-admissible-f2p-input: the ADMISSIBILITY case. Discharge the postcondition at a
# concrete F2P-shaped input — a group declared required whose TWO members are each not
# individually required, one destination supplied by keyword, over a non-empty pinned
# prefix — as an in-place `have` closed BY EVALUATION (`decide`), and only then close
# the frozen obligation verbatim. The obligation statement is byte-identical and the
# frozen proof script is retained unchanged after the `have`, so the case adds a
# demand and weakens nothing. If the postcondition were unsatisfiable at that input
# the `have` could not be evaluated closed => PRECOND-TOO-STRONG. On this PARTIAL
# carrier the case carries extra weight: it also pins that the F2P input is a DEFINED
# point (both members declare a flag, so `renderAll` succeeds and the result is
# `some`), ruling out a spec that had pushed the fixed behaviour into `none`. Port of
# nagini's admiss-f2p-shaped-input, whose self-call defended the same property against
# the half-permission precondition this carrier does not have.
# The F2P-shaped input, rendered at a given indent. Lean's whitespace sensitivity
# inside a `have` type makes the continuation indent load-bearing: the two occurrences
# below sit at different depths, so emitting one fixed-indent literal twice produces a
# structure-instance parse error rather than the intended claim. Built as a function of
# the indent for that reason (measured: the fixed-literal form failed to elaborate with
# `unexpected identifier; expected '}'`).
def _admiss_args(pad):
    return (
        '[{ id := 1, optionStrings := ["--foo-id"], req := false, dest := "foo_id" },\n'
        f'{pad}  {{ id := 2, optionStrings := ["--foo-name"], req := false, '
        'dest := "foo_name" }]\n'
        f'{pad}[{{ required := true,\n'
        f'{pad}    groupActions :=\n'
        f'{pad}      [{{ id := 1, optionStrings := ["--foo-id"], req := false, '
        'dest := "foo_id" },\n'
        f'{pad}        {{ id := 2, optionStrings := ["--foo-name"], req := false, '
        'dest := "foo_name" }] }]\n'
        f'{pad}["foo_id"] [("foo_id", "1")] ["testapp"]')


_POS_ADMISSIBLE = _swap(
    _BASE, _PROOF,
    "  -- ADMISSIBILITY: the postcondition is SATISFIABLE at a concrete\n"
    "  -- F2P-shaped input, discharged BY EVALUATION before the frozen\n"
    "  -- obligation is closed verbatim below.\n"
    "  have hAdmissible : problem_spec_requiredOptionArgs\n"
    f"      {_admiss_args(' ' * 6)}\n"
    "      (implementation_requiredOptionArgs\n"
    f"        {_admiss_args(' ' * 8)}) := by\n"
    "    unfold problem_spec_requiredOptionArgs implementation_requiredOptionArgs\n"
    "    decide\n" + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly, edits only the impl region, and carries a witness that has been SEEN
# to elaborate against the rival and fail on the frozen solution.
#
# Group (a): the SELECTION clause — one rival per bit of
# `destInOptions && (req || inRequiredGroup)`, in both directions.
# ===========================================================================

# THE BUG: drop the required-group disjunct. Pre-change selection.
_RIV_DROP_GROUP = _swap(_BASE, _GUARD,
                        "    if destInOptions optionKeys opt && opt.req then\n")

# drop the individually-required disjunct: select only via group membership.
_RIV_DROP_INDIVIDUAL = _swap(
    _BASE, _GUARD,
    "    if destInOptions optionKeys opt && inRequiredGroup groups opt then\n")

# ignore the group's own `required` flag: any group membership selects. This is the
# near-miss that agrees with the pinned result on every configuration EXCEPT a group
# declared non-required, so it gets its own witness at that configuration.
_RIV_IGNORE_FLAG = _swap(
    _BASE, _GUARD,
    "    if destInOptions optionKeys opt\n"
    "        && (opt.req || groups.any (fun g => g.groupActions.any (· == opt))) then\n")

# match group membership by DESTINATION rather than by action identity. Added by the
# audit: the manifest's group-related rivals all attack WHETHER the membership test is
# consulted, none attacks HOW the member is matched, and this carrier makes the
# distinction observable (mapping.md records membership as identity-based, carried by
# `id`). Diverges only when two distinct declared actions share a destination and just
# one of them is the group member.
_RIV_GROUP_BY_DEST = _swap(
    _BASE, _GUARD,
    "    if destInOptions optionKeys opt\n"
    "        && (opt.req || groups.any (fun g => g.required\n"
    "             && g.groupActions.any (fun a => a.dest == opt.dest))) then\n")

# drop the supplied-destination conjunct: select on the obligation alone.
_RIV_DROP_SUPPLIED = _swap(_BASE, _GUARD,
                           "    if opt.req || inRequiredGroup groups opt then\n")

# drop the obligation conjunct: select every action whose destination was supplied.
_RIV_ANY_SUPPLIED = _swap(_BASE, _GUARD,
                          "    if destInOptions optionKeys opt then\n")

# no selection at all: forward every declared action.
_RIV_FORWARD_ALL = _swap(_BASE, _GUARD + _APPEND,
                         "    parseArgs := parseArgs ++ [← renderArg? argOptions opt]\n")

# select nothing: return the pinned prefix alone.
_RIV_FORWARD_NONE = _swap(_BASE, _SIG + _BODY,
                          "    Option (List String) :=\n  some parseArgsPrefix")

# ---- Group (b): the STRUCTURE clause — the frame-pinned prefix, the order, and the
# completeness of the selected run. ----

# discard the frame-pinned prefix and start from the empty list.
_RIV_DROP_PREFIX = _swap(_BASE, _INIT, "  let mut parseArgs : List String := []\n")

# emit the selected actions in reverse declaration order.
_RIV_REVERSED = _swap(_BASE, _LOOP, "  for opt in actions.reverse do\n")

# never consider the FIRST declared action.
_RIV_SKIP_FIRST = _swap(_BASE, _LOOP, "  for opt in actions.tail do\n")

# ---- Group (c): the RENDERING clause. ----

# render with the FIRST-DECLARED flag instead of the lexicographically least one.
_RIV_FIRST_FLAG = _swap(
    _BASE, _APPEND,
    "      parseArgs := parseArgs ++ [← (argOptions.lookup opt.dest).map\n"
    "        (fun value => opt.optionStrings.headD \"\" ++ \"=\" ++ value)]\n")

# ---- Group (d): the DEFINEDNESS clause, which has TWO independent halves — a
# selected action may fail to render because it has no least flag, OR because the
# value table carries nothing at its destination. One rival per half. ----

# TOTALIZE the missing FLAG: where a selected action declares no flag and so has no
# least flag, substitute the empty flag and carry on. Added by the audit. This rival
# agrees with the pinned result on every input where every SELECTED action declares at
# least one flag — which is every input the selection/structure/rendering rivals use —
# and diverges only at that undefined point, so a rival that totalized it would
# otherwise verify unnoticed. Note it keeps the VALUE lookup partial, so it is
# refuted only by a missing-flag input and is genuinely distinct from the next rival.
_RIV_TOTALIZE = _swap(
    _BASE, _APPEND,
    "      parseArgs := parseArgs ++ [← (argOptions.lookup opt.dest).map\n"
    "        (fun value => (leastFlag? opt.optionStrings).getD \"\" ++ \"=\" ++ value)]\n")

# TOTALIZE the missing VALUE: keep the flag lookup partial but substitute the empty
# string where the value table carries nothing at the selected action's destination.
# Added after the faithfulness review, and it is the rival the OLD model could not
# express at all: with one input serving as both the membership test and the value
# table, "selected but not carried" was unreachable, and the missing value was
# silently totalized to "" by the model itself. It is reachable here because
# selection reads `optionKeys` while the value comes from `argOptions`, so a named
# destination need not be a carried key. Agrees with the pinned result on every input
# where the value table carries a value at every selected destination — every input
# the other fourteen rivals use — so nothing else in this battery constrains this
# half of the definedness clause.
_RIV_TOTALIZE_VALUE = _swap(
    _BASE, _APPEND,
    "      parseArgs := parseArgs ++ [← (leastFlag? opt.optionStrings).map\n"
    "        (fun flag => flag ++ \"=\" ++ (argOptions.lookup opt.dest).getD \"\")]\n")

# SELECT on the VALUE TABLE instead of on the keys the caller named. The rival keeps
# the whole obligation disjunction and the rendering intact; it only reads the
# membership test off the wrong one of the two inputs. Added after the faithfulness
# review: with selection and value lookup drawn from two separate inputs, WHICH input
# the membership test consults is an independent component of the postcondition, and
# every other rival here holds the two aligned and therefore cannot see it.
_RIV_SELECT_ON_VALUES = _swap(
    _BASE, _GUARD,
    "    if argOptions.any (fun kv => kv.1 = opt.dest)\n"
    "        && (opt.req || inRequiredGroup groups opt) then\n")


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {
        "id": "pos-consult-keep-predicate",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_KEEP,
        "rationale": (
            "structurally-different CORRECT impl: the inlined selection expression is "
            "replaced by the shared predicate whose body is literally that same "
            "expression, so the value is identical on every input and the frozen "
            "obligation still closes unchanged. Defends the single obligation "
            "`theorem correct_requiredOptionArgs` (statement byte-identical, no new "
            "axiom/lemma/sorry). If a faithful correct impl is REJECTED => "
            "SPEC-TOO-STRONG. Port of the nagini sibling's pos-control-helper."
        ),
    },
    {
        "id": "pos-commuted-conjunction",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_COMMUTED,
        "rationale": (
            "the two conjuncts of the selection test are COMMUTED. Both sides are "
            "total Bool tests, so the verdict — and hence the whole result, including "
            "where it is defined — is identical on every value of all four binders; "
            "only the executable form changes, a shape a faithful patch could equally "
            "take. The frozen tactic script no longer matches the commuted form, so "
            "the SAME obligation is honestly reproved by rewriting the commuted test "
            "back to the shared predicate with Bool.and_comm and then replaying the "
            "frozen closing script (statement byte-identical; no new axiom, lemma, "
            "sorry or native_decide). If it FAILS => SPEC-TOO-STRONG (the "
            "postcondition would be over-fit to one syntactic form of the test). "
            "Port of pos-control-local."
        ),
    },
    {
        "id": "pos-declarative",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DECLARATIVE,
        "rationale": (
            "the cheapest HONEST impl: build the result declaratively (filter, then "
            "render the whole run, then map the pinned prefix over the outcome) "
            "instead of accumulating in a loop and propagating partiality through "
            "`←` — a genuinely different algorithmic shape for the same partial "
            "function. The proof collapses to `rfl` after unfolding; the obligation "
            "statement is byte-identical. Must verify (else SPEC-TOO-STRONG). Note "
            "this is NOT an ungrounded-oracle echo: the pinned expression is a "
            "transparent function of the four inputs with no axiomatized answer-key, "
            "so computing it is doing the work, and any WRONG value — or a value "
            "defined where the spec leaves the computation undefined — fails the "
            "postcondition; the thirteen rivals below each demonstrate one such "
            "failure."
        ),
    },

    # ---------------- admissibility (must VERIFY) ----------------
    {
        "id": "pos-admissible-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISSIBLE,
        "rationale": (
            "the postcondition must be SATISFIABLE at an F2P-shaped input, not merely "
            "satisfiable somewhere. The impl is the frozen one and the frozen proof "
            "script is retained verbatim; what the case ADDS is an in-place `have` that "
            "discharges `problem_spec_requiredOptionArgs` at the concrete configuration "
            "the sole F2P constructs — a group declared required whose two members are "
            "each req := false, one destination supplied by keyword, over a non-empty "
            "pinned prefix — closed BY EVALUATION with `decide`, so the whole clause "
            "(selection, order, prefix, rendering, definedness) is computed at that "
            "point rather than argued about. If the postcondition were unsatisfiable "
            "there the `have` could not close and the case would FAIL => "
            "PRECOND-TOO-STRONG: on this carrier that is what an over-strong "
            "obligation looks like, and the uniqueness lane cannot detect it, because "
            "a postcondition no impl can meet at that input rejects every rival AND "
            "the frozen impl alike while every rival still LOOKS correctly rejected. "
            "The partial carrier gives the case a second job: it pins that the F2P "
            "input is a DEFINED point (both members declare a flag, so the run renders "
            "and the result is `some`), which rules out a spec that had quietly pushed "
            "the fixed behaviour into the undefined case. Adds a demand, weakens "
            "nothing: statement byte-identical, no new axiom/lemma/sorry. Port of "
            "nagini's admiss-f2p-shaped-input."
        ),
    },

    # ---------------- selection clause: rivals (must be REJECTED) ----------------
    {
        "id": "weak-drop-required-group",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_GROUP,
        "refinement": (
            "THE headline rival: selection keeps the supplied-destination test and the "
            "individually-required test but DROPS the required-group disjunct. Its "
            "faithful real counterpart is precisely the pre-change selection, which "
            "omits a supplied action that is not individually required but belongs to "
            "a group declared required. That is exactly the configuration the sole F2P "
            "constructs (a group declared required whose two members are each not "
            "individually required, one of whose destinations is supplied by keyword): "
            "the value is never forwarded to the parser, which then reports that one "
            "of those flags is required, and the F2P does NOT pass. So a rival "
            "verifying here would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the selection sub-clause `opt.req || inRequiredGroup groups "
            "opt` of the single postcondition: at the witness input the pinned filter "
            "keeps the action (its group is required) while the rival's test is false, "
            "so the results differ. Varies the `groups` binder (one required group) "
            "and `actions` (a member with req := false). If it VERIFIES => "
            "SPEC-TOO-WEAK. Port of nagini's uniq-prepatch-predicate."
        ),
        "witness": _wit(
            _lst([_A_GROUP_MEMBER]), _lst([_group(True, [_A_GROUP_MEMBER])]),
            *_aligned([("foo_id", "1")]), _strs([]),
            "supplied member of a required group, not individually required: the "
            "pinned result forwards it, the rival omits it"),
    },
    {
        "id": "weak-drop-individual-required",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_INDIVIDUAL,
        "refinement": (
            "the mirror error: selection keeps the required-group disjunct but drops "
            "the INDIVIDUALLY-required one, so only group members are ever forwarded. "
            "Its faithful patch would forward nothing for a plain required option "
            "declared outside any group, so a keyword-supplied value for such an "
            "option never reaches the parser and the parser reports it missing — the "
            "long-standing required-option behaviour breaks, failing the pre-existing "
            "P2P calls that pass a required option by keyword while doing nothing for "
            "the F2P. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the same selection sub-clause read the other way: at the "
            "witness input the action is individually required and in NO group, so the "
            "pinned filter keeps it and the rival drops it. Varies `groups` to the "
            "EMPTY list and `actions` to req := true — the complementary corner of the "
            "one weak-drop-required-group probes. If it VERIFIES => SPEC-TOO-WEAK. "
            "TACTIC NOTE: this is the one witness whose PINNED side must RENDER the "
            "action (the rival omits it, so the rival's two results differ in SHAPE and "
            "decide refutes by constructor clash without evaluating any string, while "
            "the pinned side must compare rendering to rendering). Rendering forces the "
            "lexicographic minimum of the flags, and kernel reduction of `String` `<` "
            "gets stuck at `String.decidableLT'` — with a two-flag action the pinned "
            "build fails by STUCK REDUCTION rather than by refutation, which "
            "discriminates nothing. The witness therefore uses a SINGLE-flag action, "
            "where the minimum is the head and no comparison is reached; the pinned "
            "build then reports `decide` proved the proposition false, a real verdict. "
            "The rival is unchanged — only the input moved to a point that reduces."
        ),
        "witness": _wit(
            _lst([_A_INDIVIDUAL_ONE_FLAG]), _lst([]), *_aligned([("needme", "2")]),
            _strs([]),
            "supplied individually-required action in no group: the pinned result "
            "forwards it, the rival omits it"),
    },
    {
        "id": "weak-ignore-group-required-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_FLAG,
        "refinement": (
            "the closest NEAR-MISS: selection consults group membership but IGNORES "
            "whether the group itself is required, so every group member gets "
            "forwarded. It agrees with the pinned result on every configuration except "
            "a group declared NOT required — including on the F2P configuration, which "
            "is why it needs its own witness at the distinguishing input. Its faithful "
            "patch would forward a keyword value for a member of an ordinary "
            "(non-required) group, pushing a value into the parser for an option the "
            "caller's declaration never required; that changes what the parser sees "
            "and what the resulting defaults are, regressing the pre-existing "
            "option-parsing P2P calls. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the selection sub-clause: the pinned membership test is "
            "guarded by the group's own required flag, so at the witness input (a "
            "supplied member of a NON-required group, not individually required) the "
            "pinned filter drops the action while the rival keeps it. This is the ONLY "
            "witness that varies the group's required flag to false — the flag "
            "mapping.md records the fix as depending on — so without this case a rival "
            "that ignored that flag entirely would go unnoticed. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit(
            _lst([_A_GROUP_MEMBER]), _lst([_group(False, [_A_GROUP_MEMBER])]),
            *_aligned([("foo_id", "1")]), _strs([]),
            "supplied member of a group that is NOT itself required: the pinned "
            "result omits it, the rival forwards it"),
    },
    {
        "id": "weak-group-membership-by-dest",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_GROUP_BY_DEST,
        "refinement": (
            "the membership-MATCHING attack, added by the audit: the rival consults the "
            "group's required flag correctly and consults membership correctly, but "
            "decides membership by comparing DESTINATIONS instead of by action "
            "identity. Its faithful patch would test the group's members by their "
            "destination key rather than by the action object, so a declared option "
            "that merely SHARES a destination with a required group's member — a "
            "second declared action writing the same destination, which a command is "
            "free to declare — is treated as if it were that member and its keyword "
            "value is forwarded. The parser then receives an argument for an option "
            "nothing required, changing what it sees and the resulting defaults, "
            "regressing the pre-existing option-parsing calls. Does NOT resolve: it is "
            "strictly over-forwarding relative to the pinned selection, and the F2P's "
            "configuration (one action per destination) is a point where it AGREES, "
            "so it neither fixes nor is needed for the F2P."
        ),
        "rationale": (
            "REJECTED by the membership content of `inRequiredGroup groups opt`, which "
            "the frozen definition states as `g.groupActions.any (· == opt)` — a "
            "comparison of the whole action, whose `id` field carries object identity "
            "(mapping.md). Distinct from every other group rival here: "
            "weak-drop-required-group drops the disjunct, weak-ignore-group-required-"
            "flag ignores the group's own flag, and BOTH agree with this rival on "
            "every input where destinations are unique — so none of them constrains "
            "HOW a member is matched, and a rival that matched on `dest` would "
            "otherwise verify unnoticed. The witness supplies the distinguishing "
            "input: two declared actions sharing dest \"shared\", only the second of "
            "which is the required group's member, with that destination supplied. The "
            "pinned filter keeps only the member; the rival keeps both. Also the only "
            "witness that varies `actions` to two entries with a COLLIDING dest. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit(
            _lst(['{ id := 11, optionStrings := ["--no-shared"], req := false, '
                  'dest := "shared" }',
                  '{ id := 10, optionStrings := ["--shared"], req := false, '
                  'dest := "shared" }']),
            _lst([_group(True, ['{ id := 10, optionStrings := ["--shared"], '
                                'req := false, dest := "shared" }'])]),
            *_aligned([("shared", "5")]), _strs([]),
            "two declared actions share a destination and only one is the required "
            "group's member: the pinned result forwards that member alone, the rival "
            "forwards both"),
    },
    {
        "id": "weak-drop-supplied-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_SUPPLIED,
        "refinement": (
            "selection drops the supplied-destination conjunct and forwards on the "
            "obligation alone. Its faithful patch would look up a value for a "
            "destination the caller never passed — the very lookup the retained guard "
            "exists to prevent — raising a key error inside the call for any command "
            "with a required option the caller did not supply, crashing legitimate "
            "calls covered by the pre-existing P2P set. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the `destInOptions options opt` conjunct: at the witness input "
            "the action is required but its destination is absent from the supplied "
            "mapping, so the pinned filter drops it and the rival keeps it. This is "
            "the only witness where `options` contains a NON-matching destination, and "
            "it also varies `parseArgsPrefix` to a one-element list. If it VERIFIES => "
            "SPEC-TOO-WEAK. Port of nagini's uniq-drop-supplied."
        ),
        "witness": _wit(
            _lst([_A_INDIVIDUAL]), _lst([]), *_aligned([("other", "7")]), _strs(["app"]),
            "required action whose destination was NOT supplied: the pinned result "
            "omits it, the rival forwards it"),
    },
    {
        "id": "weak-forward-any-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ANY_SUPPLIED,
        "refinement": (
            "selection drops the whole obligation disjunction and forwards every "
            "action whose destination was supplied. Its faithful patch would push "
            "values for ordinary optional options into the parser, changing what the "
            "parser sees and how the resulting defaults are computed for every "
            "keyword-passed optional argument — regressing the pre-existing "
            "option-parsing P2P calls while doing nothing that the F2P needs. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the `opt.req || inRequiredGroup groups opt` disjunction: at "
            "the witness input the action is supplied but required neither "
            "individually nor by a group, so the pinned filter drops it and the rival "
            "keeps it. Varies `actions` to req := false with `groups` empty — the "
            "over-forwarding direction. If it VERIFIES => SPEC-TOO-WEAK. Port of "
            "nagini's uniq-over-forward."
        ),
        "witness": _wit(
            _lst([_A_OPTIONAL]), _lst([]), *_aligned([("opt", "4")]), _strs([]),
            "supplied action required neither individually nor by a group: the pinned "
            "result omits it, the rival forwards it"),
    },
    {
        "id": "weak-forward-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FORWARD_ALL,
        "refinement": (
            "no selection whatsoever: every declared action is rendered and forwarded. "
            "Its faithful patch is the comprehension with its condition deleted, which "
            "renders a value for destinations the caller never supplied (key error) as "
            "well as for options nothing required — breaking essentially every "
            "command-invocation P2P test. Supporting mechanical near-miss for the "
            "selection weakness; it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the selection clause as a whole: the identity forwarding "
            "equals the pinned filter only if every declared action happens to be "
            "selectable, which the witness input violates (its single action is "
            "neither supplied nor required). Varies `options` to hold NO matching "
            "destination at all. If it VERIFIES => SPEC-TOO-WEAK. Port of nagini's "
            "uniq-identity."
        ),
        "witness": _wit(
            _lst([_A_OPTIONAL]), _lst([]), *_aligned([("other", "4")]), _strs([]),
            "action neither supplied nor required: the pinned result omits it, the "
            "rival forwards every declared action"),
    },
    {
        "id": "weak-forward-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FORWARD_NONE,
        "refinement": (
            "the trivial cheapest wrong impl: return the pinned prefix and forward "
            "nothing. Its faithful patch is deleting the accumulation entirely, so no "
            "required option's keyword value ever reaches the parser and the parser "
            "reports every required option missing — both the F2P and the pre-existing "
            "required-option P2P calls fail. Supporting near-miss; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition whenever the pinned filter is non-empty: at "
            "the witness input one action is selectable, so the pinned result carries "
            "one more element than the rival's. If it VERIFIES => SPEC-TOO-WEAK. Port "
            "of nagini's uniq-empty (adapted: the pinned prefix, which nagini's carrier "
            "had no counterpart for, is retained so the rejection is attributable to "
            "the selection and not to the frame)."
        ),
        "witness": _wit(
            _lst([_A_GROUP_MEMBER]), _lst([_group(True, [_A_GROUP_MEMBER])]),
            *_aligned([("foo_id", "1")]), _strs([]),
            "a selectable action exists: the pinned result forwards it, the rival "
            "forwards nothing"),
    },

    # ---------------- structure clause: rivals ----------------
    {
        "id": "weak-drop-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_PREFIX,
        "refinement": (
            "the frame attack, and the closest thing this carrier has to nagini's "
            "read-only-input rival: the rival discards the pinned prefix component and "
            "starts accumulating from the empty list. Its faithful patch would rebind "
            "the forwarded-argument list instead of extending it, dropping the "
            "positional arguments already collected before the changed region — every "
            "command invoked with positional arguments then loses them, breaking a "
            "large part of the pre-existing P2P set. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the frame-pinning half of the postcondition, the "
            "`fun rendered => parseArgsPrefix ++ rendered` mapped over the rendered "
            "run: at the witness input the prefix is non-empty, so the rival's result "
            "is missing its two leading elements. This is the ONLY case that varies "
            "`parseArgsPrefix` to a multi-element list — the binder the selection "
            "rivals all hold at [] — so without it a rival that mishandled only the "
            "pinned component would verify unnoticed. If it VERIFIES => SPEC-TOO-WEAK "
            "(the frame would be unconstrained, the referentially-transparent analogue "
            "of the permission hole nagini's uniq-frame-mutate attacked)."
        ),
        "witness": _wit(
            _lst([_A_FIRST]), _lst([]), *_aligned([("bar", "2")]), _strs(["app", "sub"]),
            "non-empty pinned prefix: the pinned result reproduces it verbatim, the "
            "rival discards it"),
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSED,
        "refinement": (
            "the ORDER attack: the same set is forwarded, but in reverse declaration "
            "order. Its faithful patch would iterate the declared actions backwards, "
            "so the forwarded arguments reach the parser in an order that does not "
            "follow the declaration — order-sensitive parsing (and the resulting "
            "reported values) diverges from what the command declared, breaking the "
            "pre-existing invocation P2P calls that pass several options at once, "
            "while contributing nothing to the F2P. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the ordering content of the postcondition: the pinned result "
            "renders a `filter` over `actions` in declaration order, and at the "
            "witness input two distinct actions are both selectable, so the reversed "
            "run is a different list. Requires a two-element `actions` binder and a "
            "two-entry `options` binder — the only witnesses (with skip-first) that "
            "move `actions` past length 1. If it VERIFIES => SPEC-TOO-WEAK (the spec "
            "would pin only the SET, and any permutation would pass)."
        ),
        "witness": _wit(
            _lst([_A_FIRST, _A_SECOND]), _lst([]),
            *_aligned([("bar", "2"), ("zzz", "9")]), _strs([]),
            "two selected actions: the pinned result keeps declaration order, the "
            "rival reverses it"),
    },
    {
        "id": "weak-skip-first-action",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIP_FIRST,
        "refinement": (
            "the COMPLETENESS attack: consider every declared action except the first "
            "one. Its faithful patch is a comprehension iterating the declared actions "
            "from the second onward; whenever the first-declared action is a supplied "
            "required option its value is never forwarded and the parser reports it "
            "missing — the F2P fails when the supplied group member happens to be "
            "declared first, and the pre-existing required-option calls fail likewise. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: the pinned filter runs over ALL of "
            "`actions`, so at the witness input (whose FIRST action is selectable) the "
            "rival's result is missing that action's rendering. A near-miss distinct "
            "from weak-reversed-order — it agrees with the pinned result whenever the "
            "first action is not selectable — so it is refuted at a two-action input "
            "whose first action IS selectable. If it VERIFIES => SPEC-TOO-WEAK. Port "
            "of nagini's uniq-drop-last."
        ),
        "witness": _wit(
            _lst([_A_FIRST, _A_SECOND]), _lst([]),
            *_aligned([("bar", "2"), ("zzz", "9")]), _strs([]),
            "the FIRST declared action is selectable: the pinned result includes it, "
            "the rival skips it"),
    },

    # ---------------- rendering clause: rival ----------------
    {
        "id": "weak-render-first-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRST_FLAG,
        "refinement": (
            "the RENDERING attack, which nagini's integer-encoded carrier could not "
            "express at all: the correct set is selected, in the correct order, after "
            "the correct prefix, but each entry is rendered with the FIRST-DECLARED "
            "flag rather than the lexicographically least one. Its faithful patch "
            "would render the wrong flag for any option declared with several flags "
            "in non-lexicographic order (a short form after a long one is the "
            "idiomatic declaration), so the parser receives an argument string it may "
            "not recognise or that binds to the wrong destination — breaking the "
            "pre-existing calls that pass such an option by keyword. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the rendering half of the postcondition, which pins each "
            "entry to the least flag of the action: at the witness input the action's "
            "flags are declared out of lexicographic order, so the two renderings "
            "differ. The ONLY case that varies the `optionStrings` component of the "
            "`actions` binder into non-lexicographic order — the selection rivals all "
            "hold it at a single flag, where the rendering agrees. If it VERIFIES => "
            "SPEC-TOO-WEAK (the flag choice would be unconstrained). "
            "TACTIC NOTE: `decide` cannot close this one — kernel reduction of the "
            "lexicographic String comparison gets stuck at `String.decidableLT'` "
            "(measured directly: `decide`, `decide +kernel` and `simp; decide` all "
            "report reduction stuck at `String.ltb … .iter`), so the comparison has to "
            "be supplied as a PROVED rewrite. It is supplied at the level of the "
            "rendering's own `leastFlag?` projection — `have hm : leastFlag? […] = "
            "some \"--alpha\"`, itself closed by `simp [leastFlag?, List.foldl]` then "
            "`decide +kernel` on the residue — and handed to `simp`, so `simp` rewrites "
            "the projection away before it can unfold the comparison. A proved fact, "
            "not an assumption: the witness head binds nothing, so there are no "
            "hypotheses that could be inconsistent. "
            "WHY THAT SHAPE AND NOT THE OBVIOUS ONE. Supplying the comparison as a "
            "String-level fact (`have h : (\"--alpha\" : String) < \"--zeta\"`, the "
            "first formulation of this case) does NOT work, and its failure is silent: "
            "`simp` unfolds the comparison inside `leastFlag?` to the `List Char` level "
            "(`['a','l','p','h','a'] < ['z','e','t','a']`) before `h` can fire, so `h` "
            "never applies and the goal is left OPEN. It was left open on both "
            "subjects — gold and rival alike — which made gold's exit code carry no "
            "information about the claim: the OPPOSITE claim (this input's rendering IS "
            "the first-declared flag, i.e. the frozen impl is wrong here) failed on "
            "gold with the same `unsolved goals`, so a witness asserting gold is "
            "CORRECT there would also have been recorded as a refutation. The "
            "`leastFlag?`-level rewrite restores the tracking, verified by the same "
            "pair: witness fails on gold (`simp` closes the rendering equation and "
            "leaves `⊢ False`) and builds on the rival; the opposite claim builds on "
            "gold and fails on the rival."
        ),
        "witness": _wit(
            _lst([_A_FLIPPED]), _lst([]), *_aligned([("flip", "3")]), _strs([]),
            "flags declared out of lexicographic order: the pinned result renders the "
            "least flag, the rival the first-declared one",
            tactic='  have hm : leastFlag? ["--zeta", "--alpha"] = some "--alpha" := by\n'
                   "    simp [leastFlag?, List.foldl]\n"
                   "    decide +kernel\n"
                   "  simp [renderArg?, renderAll, hm, keepAction, destInOptions,\n"
                   "    inRequiredGroup]"),
    },

    # ---------------- definedness clause: rival ----------------
    {
        "id": "weak-totalize-missing-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TOTALIZE,
        "refinement": (
            "the DEFINEDNESS attack, added by the audit. The rival selects exactly the "
            "right actions, in the right order, after the right prefix, and renders "
            "each of them from its least flag — but where a selected action declares NO "
            "flag, and therefore has no least flag, the rival SUBSTITUTES the empty "
            "flag and carries on, producing a defined result at a point the "
            "postcondition leaves undefined. Its faithful patch is the comprehension "
            "with the flag selection guarded — `min(opt.option_strings) if "
            "opt.option_strings else ''` — which is a real edit a solver could write "
            "and which SILENTLY CHANGES observable behaviour: an action declaring no "
            "flag is a positional argument, and a required positional (or one belonging "
            "to a required group) whose destination is supplied by keyword is a "
            "selected action, so the patched code hands the parser a bare `=value` "
            "string instead of failing. The un-guarded source raises on that input, "
            "before and after the change alike, so the guarded form is NOT the fix and "
            "does not resolve: it swallows an error the caller is entitled to see and "
            "feeds the parser an argument that binds to nothing."
        ),
        "rationale": (
            "REJECTED by the DEFINEDNESS content of the postcondition — the `Option` "
            "carrier together with `leastFlag?`, which is `none` on the empty flag list, "
            "and `renderAll`, which propagates that `none` across the whole selected "
            "run and thus through the pinned-prefix append. At the witness input a "
            "single individually-required action declaring NO flag has its destination "
            "supplied, so it is selected: the pinned result is `none`, while the rival "
            "returns `some [\"=hello\"]`. This is the ONLY case that varies "
            "`optionStrings` to the EMPTY list on a SELECTED action, and therefore the "
            "only one that constrains the FLAG half of where the computation is "
            "defined: all fourteen other rivals keep every selected action's flag list "
            "non-empty and agree with this rival on every input they use, so a rival "
            "that totalized that point would verify unnoticed without this case. If it "
            "VERIFIES => SPEC-TOO-WEAK (the spec would assert a defined output at an "
            "input where the modeled function has none, and any totalization would "
            "pass). No nagini counterpart: that carrier encoded each option as an "
            "integer and had no representation of a flag list, empty or otherwise."
        ),
        "witness": _wit(
            _lst([_A_NO_FLAG]), _lst([]), *_aligned([("reqpos", "hello")]), _strs([]),
            "a SELECTED action declares no flag, so it has no least flag: the pinned "
            "result is undefined there, the rival totalizes it to an empty flag"),
    },
    {
        "id": "weak-totalize-missing-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TOTALIZE_VALUE,
        "refinement": (
            "the OTHER half of the definedness attack, and the one only the repaired "
            "carrier can express. The rival selects exactly the right actions, in the "
            "right order, after the right prefix, and renders each from its least flag "
            "— but where the value table carries NOTHING at a selected action's "
            "destination it SUBSTITUTES the empty string and carries on, producing a "
            "defined result at a point the postcondition leaves undefined. Its faithful "
            "patch is the value lookup written as a defaulting read rather than a "
            "direct subscript, which is a real edit a solver could write and which "
            "SILENTLY CHANGES observable behaviour: instead of the call failing, the "
            "parser is handed a `<flag>=` argument with an empty value, which either "
            "binds the destination to the empty string or is rejected by the option's "
            "own type conversion — in both cases the caller sees a wrong result rather "
            "than the error the direct read produces. The direct read fails on that "
            "input, so the defaulting form is NOT the fix and does not resolve: it "
            "swallows an error the caller is entitled to see."
        ),
        "rationale": (
            "REJECTED by the VALUE-LOOKUP half of the definedness content of the "
            "postcondition — the `Option` carrier together with `argOptions.lookup "
            "opt.dest`, which is `none` at a destination the value table does not "
            "carry, and `renderAll`, which propagates that `none` across the whole "
            "selected run and thus through the pinned-prefix append. At the witness "
            "input a single individually-required action whose destination the caller "
            "NAMED is selected, while the value table carries a value only at a "
            "DIFFERENT destination: the pinned result is `none`, while the rival "
            "returns `some [\"--need-me=\"]`. This is the ONLY case whose "
            "`optionKeys` and `argOptions` binders are NOT aligned, and therefore the "
            "only one that constrains this half of the definedness clause at all: "
            "every other rival holds the two inputs in agreement and agrees with this "
            "rival on every input it uses. If it VERIFIES => SPEC-TOO-WEAK (the spec "
            "would assert a defined output where the modeled function has none, and "
            "any defaulting read would pass). No nagini counterpart, and no "
            "counterpart in the earlier revision of this battery either: that "
            "revision's carrier read the membership test and the value from ONE input, "
            "which made \"selected but not carried\" unreachable."
        ),
        "witness": _wit(
            _lst([_A_INDIVIDUAL_ONE_FLAG]), _lst([]), _strs(["needme"]),
            _opts([("other", "2")]), _strs([]),
            "a SELECTED action's destination is named but the value table carries "
            "nothing there: the pinned result is undefined, the rival totalizes the "
            "value to the empty string"),
    },
    {
        "id": "weak-select-on-value-table",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SELECT_ON_VALUES,
        "refinement": (
            "the WHICH-INPUT attack, also only expressible on the repaired carrier. "
            "The rival keeps the obligation disjunction and the rendering exactly "
            "right; it reads the membership half of the selection test off the value "
            "table instead of off the destinations the caller NAMED. Its faithful patch "
            "would test membership against the post-renaming value mapping rather than "
            "against the caller's own keyword keys, so an action is forwarded whenever "
            "the value table happens to carry its destination — which, when the two "
            "differ, selects a DIFFERENT action than the one the caller named and, "
            "symmetrically, drops the one they did. Does NOT resolve: it changes which "
            "actions reach the parser on exactly the configurations where the two "
            "inputs disagree, and the F2P's configuration — where they agree — is a "
            "point at which it merely coincides with the pinned selection."
        ),
        "rationale": (
            "REJECTED by the `destInOptions optionKeys opt` conjunct read as a claim "
            "about WHICH input the membership test consults: the postcondition states "
            "the selection over `optionKeys` and the rendered value over `argOptions`, "
            "two separate binders, so a rival that swaps the former for the latter is "
            "a different function. At the witness input the caller names \"needme\" "
            "while the value table carries \"other\": the pinned filter selects the "
            "action (named, individually required) and the result is `none` because no "
            "value is carried for it, whereas the rival does not select it at all and "
            "returns `some []`. Together with weak-totalize-missing-value this is one "
            "of only two cases whose two lookup binders are unaligned, and it is the "
            "only one that attacks the SELECTION side of the split rather than the "
            "value side. If it VERIFIES => SPEC-TOO-WEAK (the postcondition would not "
            "pin which of the two inputs governs selection, and either reading would "
            "pass)."
        ),
        "witness": _wit(
            _lst([_A_INDIVIDUAL_ONE_FLAG]), _lst([]), _strs(["needme"]),
            _opts([("other", "2")]), _strs([]),
            "the caller names one destination and the value table carries another: "
            "the pinned filter selects on what was NAMED, the rival on what is "
            "CARRIED"),
    },
]


# The axiom lane belongs to G-AX and is vacuous for this bundle regardless: the
# changed selection is modeled DEEPLY over a transparent carrier and the rendering
# operations are concrete, so meta.json records no consumed axiom and no
# deep-model reference (refinement.md: every row is R or I).
AXIOM_TESTS = []
