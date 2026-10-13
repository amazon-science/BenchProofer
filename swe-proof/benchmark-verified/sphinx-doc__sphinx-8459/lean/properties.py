# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8459 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   aliasedLabels (render : String → String) (aliases : List (String × String))
#                 (params : List (String × Option String)) (ret : Option String)
#                 -> List (String × String)
#   Builds the displayed type-label table for a documented callable: one ordered
#   entry per parameter that carries a declared type name (keyed by the
#   parameter's own name), followed by a single return entry (reserved key
#   "return") when the return carries a declared type name. Each label is
#   ALIAS-AWARE: the configured replacement if the declared type name is a key of
#   the alias table, else the default renderer's label.
#
#   The single postcondition is a strict equality that pins the WHOLE result:
#     result = paramEntries render aliases params ++ returnEntry render aliases ret
#   Unpacking, it constrains four independent things simultaneously —
#     (C1) LABEL RESOLUTION: every emitted label is `renderName render aliases nm`
#          (alias replacement when `nm` is aliased, else `render nm`), for BOTH the
#          parameter entries and the return entry. A rival that drops the alias
#          lookup on ANY slot fails C1.
#     (C2) RETURN MEMBERSHIP: the return entry is present iff `ret` is `some`, under
#          the reserved key "return". A rival that omits it fails C2.
#     (C3) PARAMETER MEMBERSHIP: a parameter contributes an entry iff its declared
#          type name is `some`; a `none`-annotated parameter contributes NOTHING. A
#          rival that emits an entry for an untyped parameter fails C3.
#     (C4) ORDER: parameters in declaration order, THEN the return entry. Two
#          independent orderings, each needing its own rival: a rival that moves the
#          return entry to the front fails C4, and so does one that keeps the return
#          last but permutes the parameter entries among themselves.
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled the recorder as a
# freshly-built `Dict[int,int]` whose postcondition clauses were order-INDEPENDENT
# membership/value pins over int tokens; `resolve(tok, aliases)` was the alias-aware
# value and `expand(tok)=tok+1000` the default rendering. This backend models the
# recorded OrderedDict directly as an ordered `List (String × String)`, and the
# default renderer as a FREE INPUT `render : String → String` universally quantified
# in the theorem (nagini's concrete `expand`). Consequences for the port:
#   * nagini's alias-value rivals (`weak-prepatch-expand`, `weak-return-expand`)
#     port onto clause C1 as `weak-prepatch`, `weak-return-ignore-alias`,
#     `weak-params-ignore-alias`: each drops the alias lookup on a
#     different slot (all slots / the return only / the parameters only). Because
#     `render` is a free input, "drop the alias lookup" is faithfully modeled as
#     "use `render nm` where the spec demands `renderName render aliases nm`" — the
#     exact prepatch shape (`inspect.signature(obj)` with no `type_aliases`).
#   * nagini's `weak-slot1-expand` (clause (1) pins EACH parameter, not just the
#     first) ports as `weak-later-params-ignore-alias`. The fixed two-slot nagini
#     carrier spelled this as "slot1 specifically"; on an arbitrary-length `params`
#     list the faithful analogue is "the FIRST typed parameter resolves, every LATER
#     one falls back to the default rendering". This needs a witness with TWO typed
#     parameters, which is what makes it a distinct case rather than a respelling of
#     `weak-params-ignore-alias` (whose single-parameter witness cannot separate
#     "the parameters" from "the first parameter").
#   * nagini's `weak-drop-return` ports directly onto clause C2 as `weak-drop-return`.
#   * the ordered-List carrier EXPOSES structure the order-independent dict could not:
#     clause C4 (ORDER) and clause C3 (parameter membership under a `none` annotation)
#     have NO nagini counterpart. They are attacked additionally by `weak-reverse-
#     order`, `weak-reverse-params` and `weak-include-untyped`, exercising binders
#     (`params` element order, an untyped parameter) the nagini carrier could not
#     express. C4 is TWO independent orderings on this carrier — parameters-vs-return
#     and parameter-vs-parameter — so it takes two rivals: `weak-reverse-order` moves
#     the return entry to the front, `weak-reverse-params` keeps the return last and
#     reverses the parameter entries among themselves. A rival for only the first
#     leaves the ordered-List carrier's own added structure (the order WITHIN the
#     parameter block) unpinned by any witness.
# Every reject witness probes a distinct (render, aliases, params, ret) point so the
# spec's dependence on each input binder is demonstrated; the two multi-parameter
# witnesses additionally demonstrate that each clause pins EVERY parameter and their
# relative order, which no single-parameter point can show.
#
# All THREE directions this gate exists to test are covered: SPEC-TOO-STRONG (2
# soundness positives), PRECOND-TOO-STRONG (1 admissibility positive — satisfiability
# at a behaviour-shaped input, see below), and SPEC-TOO-WEAK (8 uniqueness rivals).
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `_FRAME_WRITE`: `aliases` was held at
#     Acc(dict_pred(aliases),1/2) read-only and the rival WROTE into it, rejected for
#     INSUFFICIENT PERMISSION). Lean is referentially transparent — no aliasing, no
#     fractional permission — so a "store into a read-only input" rival is not
#     expressible and the lane is VACUOUS here (no field of this manifest
#     claims otherwise).
#   * DIVERGENCE / NON-TERMINATION. `implementation_aliasedLabels` is a total Lean
#     `def`; a non-terminating implementation cannot be written at all, so the class
#     is genuinely VACUOUS on lean (NOT the velvet-partial known-hole disposition).
#     Measured, not assumed: a `partial def` rival whose body is a self-call (the
#     only way to write a non-total impl here) is still REJECTED by the frozen
#     obligation, because `partial def` yields an OPAQUE constant that the proof
#     cannot unfold rather than a diverging one (re-measured by audit a7: the frozen
#     `set_option loom.semantics.termination` line is absent, i.e. this bundle is not
#     under the velvet `partial` setting, and the rejection error is
#     `Tactic 'unfold' failed to unfold 'implementation_aliasedLabels'`).
#
# ADMISSIBILITY DOES PORT (see `admiss-behaviour-shaped-input`). An earlier revision
# of this manifest recorded the lane N/A on the ground that the lean obligation
# `∀ render aliases params ret, problem_spec … (implementation …)` carries no
# precondition hypothesis. That is the WRONG test on a total carrier: it is true that
# no hypothesis can be over-strong, but the analogue of PRECOND-TOO-STRONG here is the
# obligation being UNSATISFIABLE at exactly a behaviour-shaped input, which a positive
# that discharges it at that concrete input BY EVALUATION tests directly. nagini's
# `admiss-readonly-membership` therefore has a faithful counterpart and the lane is
# neither vacuous nor hard.
#   * AXIOM_TESTS (nagini's UNGROUNDED-ORACLE discussion). The alias-aware label rule
#     is modeled DEEPLY (`renderName`/`lookupAlias`) over a transparent carrier, and
#     `render` is a free quantified input, so there is no consumed axiom here; the
#     axiom lane is G-AX's job and this gate ignores it.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8459"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block.
_IMPL = (
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      annotation := annotation ++ [(name, renderName render aliases nm)]\n"
    "  if let some nm := ret then\n"
    "    annotation := annotation ++ [(\"return\", renderName render aliases nm)]\n"
    "  return annotation"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The full frozen proof body (tactic lines inside proof-start/proof-end). Swapped
# only by the pure-expression positive, whose different impl shape needs an (equally
# cheap, honest) reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro render aliases params ret\n"
    "  unfold problem_spec_aliasedLabels implementation_aliasedLabels\n"
    "  simp only [Id.run, bind, pure]\n"
    "  rw [loop_aliasedLabels render aliases params []]\n"
    "  simp only [List.nil_append]\n"
    "  cases ret with\n"
    "  | none => simp only [returnEntry, List.append_nil]\n"
    "  | some nm => simp only [returnEntry]"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-pure-expression: a structurally different CORRECT impl written as a pure
# expression (no `Id.run do`, no `let mut`, no `for`), directly returning the spec's
# own RHS shape `paramEntries ++ returnEntry`. Semantics identical on every input.
# The theorem STATEMENT is byte-identical; its proof collapses to `rfl` (the impl is
# now definitionally the spec RHS) — no new axiom/lemma/sorry, just the cheapest
# tactic for the new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition is
# bound to the monadic accumulator shape rather than the behaviour).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_aliasedLabels (render : String → String)\n"
        "    (aliases : List (String × String)) (params : List (String × Option String))\n"
        "    (ret : Option String) : List (String × String) :=\n"
        "  paramEntries render aliases params ++ returnEntry render aliases ret",
    ),
    _PROOF,
    "  intro render aliases params ret\n"
    "  rfl",
)

# pos-match-return: a structurally different CORRECT impl that keeps the monadic
# accumulator loop but records the return entry via an explicit `match ret with`
# (both branches) instead of the `if let some` sugar. Same values, same order, on
# every input, so the FROZEN proof body still closes (the two return-branch forms are
# definitionally equal). No reproof, no new axiom/lemma/sorry. If it FAILS =>
# SPEC-TOO-STRONG (postcondition over-fit to one syntactic return-handling shape).
_POS_MATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      annotation := annotation ++ [(name, renderName render aliases nm)]\n"
    "  match ret with\n"
    "  | some nm => annotation := annotation ++ [(\"return\", renderName render aliases nm)]\n"
    "  | none => pure ()\n"
    "  return annotation",
)


# ===========================================================================
# ADMISSIBILITY (satisfiability at a behaviour-shaped input) — must VERIFY, else
# PRECOND-TOO-STRONG. The FROZEN impl and the FROZEN proof body are both kept
# VERBATIM; the case only PREFIXES `have`s that discharge the obligation at concrete
# inputs by evaluation, then `clear`s them so nothing downstream can lean on them.
# ===========================================================================

# The behaviour-shaped point: several parameters AND the return all declaring the SAME
# aliased type name, under a renderer whose default label for that name DIFFERS from
# the configured replacement — the only configuration in which the alias-aware rule is
# observable at all. At this point the spec demands [("x","myint"),("y","myint"),
# ("return","myint")] (checked by #eval), i.e. the configured replacement on all three
# slots, whereas the default rendering would give "int" on all three.
_ADM_RENDER = '(fun s => if s == "myint" then "int" else s)'
_ADM_ALIASES = '[("myint", "myint")]'
_ADM_PARAMS = '[("x", some "myint"), ("y", some "myint")]'
_ADM_RET = '(some "myint")'

_ADM_HAVES = (
    "  -- ADMISSIBILITY. The frozen obligation is an unconditional universal, so no\n"
    "  -- hypothesis of it can be over-strong; the analogue of PRECOND-TOO-STRONG on\n"
    "  -- this total carrier is the obligation being UNSATISFIABLE at exactly a\n"
    "  -- behaviour-shaped input. These `have`s discharge it at such inputs BY\n"
    "  -- EVALUATION, ahead of the frozen tactic body which then follows verbatim.\n"
    "  -- Point 1: several parameters AND the return all declaring the SAME aliased\n"
    "  -- type name, under a renderer whose default label for that name differs from\n"
    "  -- the configured replacement — the only shape in which the rule is visible.\n"
    f"  have adm_behaviour_shaped : problem_spec_aliasedLabels {_ADM_RENDER} {_ADM_ALIASES}\n"
    f"      {_ADM_PARAMS} {_ADM_RET}\n"
    f"      (implementation_aliasedLabels {_ADM_RENDER} {_ADM_ALIASES}\n"
    f"        {_ADM_PARAMS} {_ADM_RET}) := by\n"
    "    unfold problem_spec_aliasedLabels implementation_aliasedLabels\n"
    "    simp [renderName, lookupAlias, paramEntries, returnEntry, Id.run, pure, bind]\n"
    "  -- Point 2: the same aliased name on the RETURN slot only (no parameters), so\n"
    "  -- the return half is shown satisfiable independently of the parameter half.\n"
    f"  have adm_return_only : problem_spec_aliasedLabels {_ADM_RENDER} {_ADM_ALIASES}\n"
    f"      ([] : List (String × Option String)) {_ADM_RET}\n"
    f"      (implementation_aliasedLabels {_ADM_RENDER} {_ADM_ALIASES}\n"
    f"        ([] : List (String × Option String)) {_ADM_RET}) := by\n"
    "    unfold problem_spec_aliasedLabels implementation_aliasedLabels\n"
    "    simp [renderName, lookupAlias, paramEntries, returnEntry, Id.run, pure, bind]\n"
    "  -- INFORMATIVENESS control: at the SAME point as `adm_behaviour_shaped` the\n"
    "  -- obligation evaluates to FALSE for the table the default rendering would\n"
    "  -- produce. So the two haves above are real evaluations of the postcondition,\n"
    "  -- not steps that would close for any output whatsoever.\n"
    f"  have adm_discriminates : ¬ problem_spec_aliasedLabels {_ADM_RENDER} {_ADM_ALIASES}\n"
    f"      {_ADM_PARAMS} {_ADM_RET}\n"
    '      [("x", "int"), ("y", "int"), ("return", "int")] := by\n'
    "    unfold problem_spec_aliasedLabels\n"
    "    simp [renderName, lookupAlias, paramEntries, returnEntry]\n"
    "  clear adm_behaviour_shaped adm_return_only adm_discriminates\n"
)

# The frozen proof body must survive VERBATIM after the probes, so the obligation is
# reproven rather than replaced, and the FROZEN impl is untouched.
_ADMISS = _swap(_BASE, _PROOF, _ADM_HAVES + _PROOF)
assert _PROOF in _ADMISS, "frozen proof body must follow the admissibility probes"
assert _IMPL in _ADMISS, "admissibility case must keep the FROZEN impl verbatim"


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-prepatch: the EXACT pre-patch behaviour. Every label uses `render nm` — the
# default rendering — IGNORING the alias table entirely, on both parameters and the
# return. This is the recorder built from the signature with no alias resolution.
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      annotation := annotation ++ [(name, render nm)]\n"
    "  if let some nm := ret then\n"
    "    annotation := annotation ++ [(\"return\", render nm)]\n"
    "  return annotation",
)

# weak-return-ignore-alias: parameters resolved alias-aware (correct) but the RETURN
# entry drops the alias lookup and uses `render nm`. A partial-domain rival diverging
# on the return slot only.
_RIV_RETURN = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      annotation := annotation ++ [(name, renderName render aliases nm)]\n"
    "  if let some nm := ret then\n"
    "    annotation := annotation ++ [(\"return\", render nm)]\n"
    "  return annotation",
)

# weak-params-ignore-alias: the RETURN entry resolved alias-aware (correct) but the
# PARAMETER entries drop the alias lookup and use `render nm`. The dual partial-domain
# rival, diverging on the parameter slots only — tests clause C1 pins EACH parameter,
# not just the return.
_RIV_PARAMS = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      annotation := annotation ++ [(name, render nm)]\n"
    "  if let some nm := ret then\n"
    "    annotation := annotation ++ [(\"return\", renderName render aliases nm)]\n"
    "  return annotation",
)

# weak-later-params-ignore-alias: the FIRST typed parameter is resolved alias-aware
# (correct), but every LATER typed parameter drops the alias lookup and uses
# `render nm`. The return is correct too. This is nagini's `weak-slot1-expand`
# re-expressed for an arbitrary-length parameter list: it is REJECTED only if clause
# C1 pins every parameter rather than "the first one", and — unlike
# weak-params-ignore-alias — it can only be caught by a witness carrying TWO typed
# parameters, so it is what actually demonstrates the per-parameter quantification.
_RIV_LATER_PARAMS = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  let mut seen : Bool := false\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      if seen then\n"
    "        annotation := annotation ++ [(name, render nm)]\n"
    "      else\n"
    "        annotation := annotation ++ [(name, renderName render aliases nm)]\n"
    "      seen := true\n"
    "  if let some nm := ret then\n"
    "    annotation := annotation ++ [(\"return\", renderName render aliases nm)]\n"
    "  return annotation",
)

# weak-reverse-params: emits exactly the right entries with the right alias-aware
# labels and keeps the return entry LAST, but emits the PARAMETER entries in REVERSE
# declaration order (prepending instead of appending). The second half of clause C4:
# weak-reverse-order tests parameters-vs-return, this tests parameter-vs-parameter,
# which is order structure only the ordered-List carrier has. Needs a witness with
# TWO typed parameters — with one, this rival is observationally identical to gold.
_RIV_REVERSE_PARAMS = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      annotation := [(name, renderName render aliases nm)] ++ annotation\n"
    "  if let some nm := ret then\n"
    "    annotation := annotation ++ [(\"return\", renderName render aliases nm)]\n"
    "  return annotation",
)

# weak-drop-return: records both parameters correctly but DROPS the return entry
# entirely (never emits the "return" key). Violates clause C2.
_RIV_DROP = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      annotation := annotation ++ [(name, renderName render aliases nm)]\n"
    "  return annotation",
)

# weak-reverse-order: records the RIGHT entries with the RIGHT labels but emits the
# return entry FIRST, then the parameters. Violates clause C4 (declaration order,
# return last). No nagini counterpart — the order-independent dict carrier could not
# express order.
_RIV_ORDER = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  if let some nm := ret then\n"
    "    annotation := annotation ++ [(\"return\", renderName render aliases nm)]\n"
    "  for (name, ann) in params do\n"
    "    if let some nm := ann then\n"
    "      annotation := annotation ++ [(name, renderName render aliases nm)]\n"
    "  return annotation",
)

# weak-include-untyped: emits an entry for EVERY parameter, including those with NO
# declared type name (a `none` annotation), labelling the untyped one with the empty
# string. Violates clause C3 (an untyped parameter must contribute NOTHING). No
# nagini counterpart — the fixed-slot dict carrier had no "untyped parameter" input.
_RIV_INCLUDE = _swap(
    _BASE,
    _IMPL,
    "def implementation_aliasedLabels (render : String → String)\n"
    "    (aliases : List (String × String)) (params : List (String × Option String))\n"
    "    (ret : Option String) : List (String × String) := Id.run do\n"
    "  let mut annotation : List (String × String) := []\n"
    "  for (name, ann) in params do\n"
    "    match ann with\n"
    "    | some nm => annotation := annotation ++ [(name, renderName render aliases nm)]\n"
    "    | none => annotation := annotation ++ [(name, \"\")]\n"
    "  if let some nm := ret then\n"
    "    annotation := annotation ++ [(\"return\", renderName render aliases nm)]\n"
    "  return annotation",
)


def _wit(render, aliases, params, ret, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal (render, aliases, params, ret). `simp` reduces renderName/lookupAlias/
    paramEntries/returnEntry/Id.run and closes the disequality. Elaborates against a
    rival that diverges from the spec at this point, and FAILS on gold (which
    satisfies the spec at every input) — SEEN to discriminate both ways."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_aliasedLabels ({render}) {aliases} {params} {ret}\n"
        f"    (implementation_aliasedLabels ({render}) {aliases} {params} {ret}) := by\n"
        f"  unfold problem_spec_aliasedLabels implementation_aliasedLabels\n"
        f"  simp [renderName, lookupAlias, paramEntries, returnEntry, Id.run, pure, bind]"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-pure-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure expression (no "
            "`Id.run do`, no `let mut`, no `for`), directly returning the composed table "
            "`paramEntries ++ returnEntry`. Semantics identical on every input. The theorem "
            "STATEMENT is byte-identical; its proof collapses honestly to `rfl` (the impl is "
            "now definitionally the postcondition's RHS) — no new axiom/lemma/sorry, just the "
            "cheapest tactic for the new shape. If it FAILS => SPEC-TOO-STRONG (the "
            "postcondition is bound to the monadic accumulator shape rather than the "
            "behaviour)."
        ),
    },
    {
        "id": "pos-match-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH,
        "rationale": (
            "structurally-different but CORRECT impl: keeps the accumulator loop but handles "
            "the return entry via an explicit `match ret with` (both branches) instead of "
            "`if let some` sugar. Same entries, same labels, same order on every input, so "
            "the FROZEN proof body still closes (the two return-branch forms are "
            "definitionally equal) — a faithful restructure with no reproof and no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to one "
            "syntactic return-handling shape)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-behaviour-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation must be SATISFIABLE at the concrete input shapes the modeled "
            "behaviour exists for. This carrier is total and the frozen obligation is an "
            "unconditional universal over (render, aliases, params, ret), so nothing here "
            "can be PRECOND-TOO-STRONG in nagini's hypothesis-weakening sense — but that "
            "is NOT a reason to drop the lane, and an earlier revision of this manifest "
            "dropped it on exactly that ground. The analogue on a total carrier is the "
            "obligation being UNSATISFIABLE at a behaviour-shaped input, and this case "
            "tests it directly: two `have`s discharge the frozen postcondition BY "
            "EVALUATION at concrete points — several parameters AND the return all "
            "declaring the SAME aliased type name under a renderer whose default label "
            "for that name DIFFERS from its configured replacement, and the return slot "
            "alone — before the FROZEN tactic body runs verbatim. A third `have` is the "
            "informativeness control: at that same input the postcondition evaluates to "
            "FALSE for the table the default rendering would give, so the positive halves "
            "are genuine evaluations rather than steps that close for any output. Scope: "
            "the FROZEN impl is kept verbatim, the theorem STATEMENT is byte-identical, "
            "the probes are `clear`ed before the frozen body, and no "
            "declaration/axiom/sorry is added. MEASURED load-bearing, not decorative: "
            "carried onto the pre-change impl shape the first `have` fails at its OWN "
            "line (`unsolved goals ⊢ False`), independently of the frozen proof. Ports "
            "nagini's `admiss-readonly-membership`."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "this IS the pre-patch behaviour: every label uses the default rendering, "
            "IGNORING the configured alias table on both parameters and the return (the "
            "recorder built from the signature with no alias resolution threaded in). Its "
            "faithful real patch is the UNCHANGED repo, which under the description path "
            "renders each label by its default form; the F2P test configures an alias and "
            "asserts the alias-aware label is shown for the parameters AND the return, so it "
            "does NOT resolve. A verifying rival is a true verify-does-not-imply-resolve "
            "break."
        ),
        "rationale": (
            "REJECTED by clause C1 (label resolution). When a declared type name is a key of "
            "the alias table the spec demands the configured replacement, but the rival emits "
            "the default rendering of that name. Witness sits at an ALIASED parameter whose "
            "default rendering differs from its configured replacement. If it VERIFIES => "
            "SPEC-TOO-WEAK (the alias resolution is unpinned)."
        ),
        # aliased name "myint" -> replacement "MY"; render=identity gives default "myint".
        "witness": _wit('fun s => s', '[("myint", "MY")]', '[("x", some "myint")]', 'none',
                        "aliased parameter: gold shows the configured replacement, "
                        "prepatch shows the default rendering"),
    },
    {
        "id": "weak-return-ignore-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RETURN,
        "refinement": (
            "a partial-domain rival correct on the PARAMETERS but dropping the alias lookup "
            "for the RETURN entry only. A faithful real patch that threaded the alias table "
            "into the parameter loop but left the return label on the default rendering would "
            "show the alias for the parameters yet the default form for the return; the F2P "
            "asserts the return type label is the alias-aware form, so it does NOT resolve. "
            "verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 on the RETURN slot: the return label must be "
            "`renderName render aliases nm`, but the rival stores `render nm`, which differs "
            "whenever the return's declared type name is aliased. The return label is pinned "
            "independently of the parameter labels, so a single-slot divergence is caught. "
            "Witness probes an aliased RETURN (ret = some aliased-name). If it VERIFIES => "
            "SPEC-TOO-WEAK (the return label is unpinned)."
        ),
        # non-identity render on a name that IS aliased, in a MULTI-entry table where the
        # match is not first: alias wins for gold ("RET"), rival emits render "myint" =
        # "myint!" -> differ. Varies the render AND aliases binders.
        "witness": _wit('fun s => s ++ "!"', '[("other", "OO"), ("myint", "RET")]',
                        '([] : List (String × Option String))', '(some "myint")',
                        "aliased return, non-identity renderer, multi-entry alias table: gold "
                        "shows the configured replacement, rival shows the default rendering"),
    },
    {
        "id": "weak-params-ignore-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PARAMS,
        "refinement": (
            "the dual partial-domain rival: correct on the RETURN but dropping the alias "
            "lookup for the PARAMETER entries only. A faithful real patch that resolved the "
            "return against the alias table but rendered parameters by their default form "
            "would show the alias for the return yet the default form for each parameter; the "
            "F2P asserts each parameter type label is the alias-aware form, so it does NOT "
            "resolve. verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 on a PARAMETER slot: each parameter label must be "
            "`renderName render aliases nm`, but the rival stores `render nm`. Clause C1 pins "
            "EVERY parameter, not just the return. Witness probes an aliased PARAMETER with a "
            "distinct parameter name ('y') and an aliased return present, isolating the "
            "parameter divergence. If it VERIFIES => SPEC-TOO-WEAK (parameter labels "
            "unpinned)."
        ),
        # param "y":aliased "jsonobj" -> gold "JS", rival render "jsonobj"="jsonobj". return
        # aliased+rendered correctly by the rival, so only the param slot diverges. Distinct
        # alias key/replacement from the other witnesses varies the aliases binder.
        "witness": _wit('fun s => s', '[("jsonobj", "JS")]', '[("y", some "jsonobj")]',
                        '(some "jsonobj")',
                        "aliased parameter (return correct): gold shows the configured "
                        "replacement for the parameter, rival shows the default rendering"),
    },
    {
        "id": "weak-later-params-ignore-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LATER_PARAMS,
        "refinement": (
            "resolves the FIRST typed parameter alias-aware but lets every LATER typed "
            "parameter fall back to the default rendering (the return stays correct). A "
            "faithful real patch that threaded the alias table into only the first iteration "
            "of the parameter walk — an off-by-one in the loop — would show the alias for the "
            "leading parameter and the default form for the rest; the F2P documents a callable "
            "with SEVERAL alias-annotated parameters and asserts the alias-aware label for "
            "each of them, so it does NOT resolve. verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 quantified over EVERY parameter: the label of each "
            "parameter entry must be `renderName render aliases nm`, so a rival correct on the "
            "first parameter and wrong on the second still contradicts the postcondition. "
            "This is the case that DEMONSTRATES the per-parameter quantification: its witness "
            "carries TWO typed parameters, and at a one-parameter point this rival agrees with "
            "the frozen impl exactly, so no single-parameter witness could catch it. (That is "
            "what distinguishes it from weak-params-ignore-alias, which drops the lookup on "
            "all parameters.) If it VERIFIES => SPEC-TOO-WEAK (C1 pins only the leading "
            "parameter)."
        ),
        # TWO typed params, both aliased, distinct declared type names: gold
        # [("a","T1"),("b","T2")], rival [("a","T1"),("b","t2")] -> differ on the SECOND
        # parameter only. A one-parameter point cannot separate these two impls.
        "witness": _wit('fun s => s', '[("t1", "T1"), ("t2", "T2")]',
                        '[("a", some "t1"), ("b", some "t2")]', '(none : Option String)',
                        "two typed aliased parameters: gold resolves BOTH, the rival "
                        "resolves only the first and defaults the second"),
    },
    {
        "id": "weak-reverse-params",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE_PARAMS,
        "refinement": (
            "emits the right entries with the right alias-aware labels and keeps the return "
            "entry last, but lists the PARAMETER entries in reverse declaration order. A "
            "faithful real patch that accumulated each parameter row by prepending would "
            "render the parameter rows bottom-up; the F2P pins the documented parameters in "
            "declaration order, so it does NOT resolve. verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by clause C4 on the PARAMETER block: the spec fixes the result as the "
            "parameter entries IN DECLARATION ORDER followed by the return entry, so reversing "
            "the parameters among themselves contradicts it even though membership, every "
            "label, and the return's final position are all correct. Distinct from "
            "weak-reverse-order, which moves the return entry to the front: that one tests "
            "parameters-vs-return, this one tests parameter-vs-parameter, the order structure "
            "the ordered-List carrier adds over the nagini dict. Witness carries TWO typed "
            "parameters — at a one-parameter point this rival is observationally identical to "
            "the frozen impl. If it VERIFIES => SPEC-TOO-WEAK (only the return's position is "
            "pinned, not the parameter order)."
        ),
        # TWO typed params + a return, three distinct declared type names: gold
        # [("a","T1"),("b","T2"),("return","T3")], rival [("b","T2"),("a","T1"),("return","T3")]
        # -> same multiset, same return position, differing ONLY in parameter order.
        "witness": _wit('fun s => s', '[("t1", "T1"), ("t2", "T2"), ("t3", "T3")]',
                        '[("a", some "t1"), ("b", some "t2")]', '(some "t3")',
                        "two typed parameters and a return: gold keeps declaration order, "
                        "the rival reverses the parameter entries"),
    },
    {
        "id": "weak-drop-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP,
        "refinement": (
            "records the parameters correctly but DROPS the return entry entirely (never "
            "emits the reserved 'return' key). A faithful real patch omitting the "
            "return-recording line renders no return type label at all; the F2P asserts the "
            "output carries a 'Return type:' line with the alias-aware label, so it does NOT "
            "resolve. verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (return membership): when `ret` is `some` the result must "
            "contain the return entry, but the rival never emits it. Witness has an EMPTY "
            "parameter list and `ret = some`, so the only demanded entry is the return one "
            "the rival drops (the rival yields [], the spec demands a one-entry table). "
            "(Distinct from weak-return-ignore-alias, which emits a WRONG return LABEL; this "
            "one emits NO return entry.) If it VERIFIES => SPEC-TOO-WEAK (return presence "
            "unpinned)."
        ),
        # no params, UNALIASED return name (empty alias table): gold -> [("return","int")]
        # (the default rendering, since the name is not aliased), rival -> []. Membership,
        # not label value, is what diverges, so an empty alias table is the cleanest probe.
        "witness": _wit('fun s => s', '([] : List (String × String))',
                        '([] : List (String × Option String))', '(some "int")',
                        "return present (empty alias table), no parameters: gold emits the "
                        "return entry, rival emits an empty table"),
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ORDER,
        "refinement": (
            "records the RIGHT entries with the RIGHT alias-aware labels but emits the return "
            "entry FIRST, before the parameters. A faithful real patch that recorded the "
            "return ahead of iterating the parameters would place the reserved row first in "
            "the recorded table. HONEST SCOPE (narrowed by audit a7 — the earlier text "
            "claimed the F2P pins this, and it does not): the downstream consumer of this "
            "table SKIPS the reserved key while emitting the parameter rows and appends the "
            "return row afterwards, so the reserved key's own position in the recorded table "
            "is not observable in the rendered output, and no F2P or P2P test in this "
            "instance distinguishes it. This case is therefore justified as a MODEL-level "
            "uniqueness rival — the spec pins the recorded table as an ordered structure and "
            "a rival contradicting that pin must be rejected for the spec to mean what it "
            "says — and NOT as a verify-does-not-imply-resolve claim. Its sibling "
            "weak-reverse-params carries the resolve-grounded half of clause C4."
        ),
        "rationale": (
            "REJECTED by clause C4 (order): the spec fixes the result as the parameter "
            "entries in declaration order FOLLOWED BY the return entry, but the rival emits "
            "the return entry first. Witness has BOTH a typed parameter and a return present "
            "so the two orderings differ (`[return, x]` vs `[x, return]`). This clause has no "
            "nagini counterpart (order-independent dict). If it VERIFIES => SPEC-TOO-WEAK "
            "(order unpinned)."
        ),
        # one typed param + return, distinct declared type names, two-entry alias table so
        # the two labels differ ("PP" vs "RR"): gold [("x","PP"),("return","RR")],
        # rival [("return","RR"),("x","PP")] -> differ by order only.
        "witness": _wit('fun s => s', '[("ptype", "PP"), ("rtype", "RR")]',
                        '[("x", some "ptype")]', '(some "rtype")',
                        "typed parameter and return both present: gold orders parameter "
                        "before return, rival orders return first"),
    },
    {
        "id": "weak-include-untyped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INCLUDE,
        "refinement": (
            "emits an entry for EVERY parameter, including one with no declared type name, "
            "labelling the untyped one with the empty string. A faithful real patch that "
            "recorded a row for a parameter whose annotation is absent would add a spurious "
            "blank type label for a parameter the docs must leave unlabelled. HONEST SCOPE "
            "(narrowed by audit a7 — the earlier text claimed 'the F2P output has no such "
            "row', which does not discriminate): every parameter of the F2P's documented "
            "callable IS annotated, so that instance has no untyped parameter and cannot "
            "exhibit the spurious row. The claim is instead grounded in the description-path "
            "P2P tests, which document callables carrying unannotated parameters and pin the "
            "rendered field list exactly, so a spurious blank row for such a parameter is a "
            "P2P regression. That makes this a REGRESSION-grounded rival (breaking a test "
            "the fix must keep passing) rather than an F2P-grounded one, which is a real "
            "verify-does-not-imply-resolve claim but not the one the earlier text asserted."
        ),
        "rationale": (
            "REJECTED by clause C3 (parameter membership): a parameter with a `none` declared "
            "type name must contribute NO entry, but the rival emits one. Witness is a single "
            "UNTYPED parameter (annotation `none`) and no return: the spec demands the empty "
            "table, the rival emits a one-entry table. This clause has no nagini counterpart "
            "(fixed-slot dict, no 'untyped parameter' input). If it VERIFIES => SPEC-TOO-WEAK "
            "(the untyped-parameter exclusion is unpinned)."
        ),
        # single untyped param, no return: gold -> [], rival -> [("z","")]. The label value
        # is irrelevant to C3 (membership), so a distinct alias table just varies the binder.
        "witness": _wit('fun s => s', '[("a", "A"), ("b", "B")]', '[("z", none)]',
                        '(none : Option String)',
                        "untyped parameter, no return: gold emits an empty table, "
                        "rival emits a spurious entry"),
    },
]


# No consumed axioms and no opaque callees: the alias-aware label rule
# (renderName/lookupAlias) is modeled DEEPLY over transparent carriers and the
# default renderer is a FREE quantified input, so the axiom lane is vacuous here and
# belongs to G-AX regardless.
AXIOM_TESTS = []
