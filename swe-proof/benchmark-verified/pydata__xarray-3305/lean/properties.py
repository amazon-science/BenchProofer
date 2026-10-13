"""properties.py — G-PBT falsification battery for pydata__xarray-3305 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a positive control that legitimately reproves
its reshaped implementation, inside a ``-- proof-start`` / ``-- proof-end``
region — is changed, so ``markers.same_spec`` holds and both
``theorem correct_<name>`` STATEMENTS stay byte-identical).
``expect="verify"`` passes iff (in scope AND the file elaborates with every
obligation closed); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh
invention: the nagini manifest is the design document and each case below is
traced to it (or its principled omission recorded) in the module
``assessment``. The nagini bundle models the same two-site caller→callee chain,
but over a heap carrier with fractional permissions (a read-only source payload
held at half permission, a mutable result list); this bundle models the same two
sites as two total Lean functions over immutable inputs. The adversarial
ARGUMENTS carry over one-for-one; the mechanics are re-expressed, and the
permission-based case class collapses (see ``assessment``).

DEFENDED SURFACE (two modeled obligations, callee then caller).

  ``correct_arrayQuantile`` — the single-array reduction. Inputs: the surviving
  dimension labels ``newDims``, the computed value data ``qs``, the source
  metadata payload ``selfAttrs``, the three-valued keep request ``keepAttrs``
  (``none`` = unspecified), and the supplied fallback flag ``globalDefault``.
  ``problem_spec_arrayQuantile`` has THREE independent top-level conjuncts:

    (C0) ``result.dims = newDims``  — the metadata choice does not touch the
         dimension labels (the FRAME clause on the labels);
    (C1) ``result.data = qs``       — nor the value data (the FRAME clause on
         the data);
    (C2) ``result.attrs = if resolveKeepAttrs keepAttrs globalDefault then
         some selfAttrs else none``  — the LOAD-BEARING clause. Note it pins
         BOTH branches and pins them to distinct points of ``Option Attrs``:
         ``some selfAttrs`` (which payload, not merely that there is one) and
         ``none`` (no payload, which is NOT ``some []``). Both are attacked.
         It is grounded
         in the inputs: ``resolveKeepAttrs keepAttrs globalDefault`` is
         ``keepAttrs.getD globalDefault``, fully unfolded, so an explicit
         request decides directly and an unspecified one falls back to the
         supplied flag; and the kept payload must be the SOURCE payload
         ``selfAttrs`` itself, not merely some payload. There is no opaque
         answer key an implementation could echo, so the "ungrounded-oracle
         echo" attack class does not apply here (honest cheapest-implementation
         positive controls stand in its place — see ``assessment``).

  ``correct_collectionQuantile`` — the collection-level reduction. Inputs: the
  member arrays ``arrays``, the same three-valued request ``keepAttrs``, the
  same fallback flag ``globalDefault``. Its postcondition is ONE conjunct, but
  a compound one: the result is ``arrays.map`` of the per-member reduction, so
  it pins simultaneously (a) the LENGTH and ORDER of the output against the
  input list, (b) each member's own labels and data, and (c) that the ONE
  shared request is forwarded UNCHANGED to EVERY member. The discriminating
  content of this site is exactly the forwarding: the reported failure is that
  a collection-level call swallowed the request and each member then resolved
  from the fallback flag instead.

BINDER COVERAGE. Every input binder of both predicates is moved by some reject
witness, and each rival is refuted at its own input point:
  * ``keepAttrs`` — probed at ``some true`` / ``some false`` / ``none``;
  * ``globalDefault`` — probed at both ``false`` and ``true``, on BOTH
    obligations: at the single-array level by a matched pair of rivals that
    hardcode the unspecified branch each way, and at the collection level by a
    rival that forwards the request faithfully but substitutes a negative
    fallback, so neither obligation's dependence on the fallback flag is left
    unprobed in either direction;
  * ``selfAttrs`` — a rival that keeps an EMPTY payload instead of the source
    payload is refuted at a two-entry source payload, so the clause is shown to
    depend on the payload's contents and not merely on its presence;
  * ``newDims`` / ``qs`` — attacked by the two frame rivals (C0, C1), which
    mangle the labels / the data in one metadata branch and are refuted at a
    multi-label / multi-element input;
  * ``arrays`` — attacked by three traversal rivals refuted at TWO-member
    inputs, one per structural property the mapped postcondition pins:
    per-member content (leading-member-only forwarding), ORDER (reversed
    emission), and LENGTH (trailing member dropped). Order and length are
    separate attacks because a permutation preserves the length and a truncation
    preserves the order, so neither rival moves the other's property.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection ALONE attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate directly at one
concrete input and refutes it. Each was built against its rival (must elaborate)
and against the frozen solution (must fail), so it is a discriminator and not a
tautology. This carrier is fully transparent — the ``Attrs`` / ``QResult`` /
``SrcArray`` carriers all derive ``DecidableEq`` and no callee is ``opaque`` —
so every witness states its refutation at literal inputs and closes by
``decide``. No witness binds a hypothesis, so none can be inconsistent.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3305"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file, so the manifest breaks loudly if the frozen solution drifts.
# ---------------------------------------------------------------------------

# The whole single-array implementation BODY (inside the first `impl` region).
_ARRAY_BODY = """\
  -- default the keep request from the supplied default flag when unspecified
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  let attrs := if keep.getD globalDefault then some selfAttrs else none
  return { dims := newDims, data := qs, attrs := attrs }"""

# The whole collection-level implementation BODY (inside the second `impl`
# region).
_COLL_BODY = """\
  let mut out : Array QResult := #[]
  for a in arrays do
    -- forward the SAME keep request to each member array's reduction
    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
    out := out.push r
  return out.toList"""

# The tactic BODY of the single-array closed form (inside the first `proof`
# region). Only a positive control that reshapes the single-array
# implementation touches this; the theorem STATEMENT is never edited.
_ARRAY_PROOF = "  cases keepAttrs <;> rfl"

# The tactic BODY of the collection-level obligation (inside the second `proof`
# region).
_COLL_PROOF = """\
  intro arrays keepAttrs globalDefault
  unfold problem_spec_collectionQuantile implementation_collectionQuantile
  have h := collectionQuantile_forIn arrays keepAttrs globalDefault #[]
  simpa [Id.run] using h"""

for _anchor in (_ARRAY_BODY, _COLL_BODY, _ARRAY_PROOF, _COLL_PROOF):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"frozen solution drifted from anchor {_anchor[:50]!r}")


def _array(new_body, new_proof=None):
    """A variant that edits only the single-array implementation (and, for a
    reshaped positive control, only that function's closed-form tactic body)."""
    out = _swap(_BASE, _ARRAY_BODY, new_body)
    if new_proof is not None:
        out = _swap(out, _ARRAY_PROOF, new_proof)
    return out


def _coll(new_body, new_proof=None):
    """A variant that edits only the collection-level implementation (and, for a
    reshaped positive control, only that obligation's tactic body)."""
    out = _swap(_BASE, _COLL_BODY, new_body)
    if new_proof is not None:
        out = _swap(out, _COLL_PROOF, new_proof)
    return out


# ===========================================================================
# POSITIVE CONTROLS — must VERIFY, else SPEC-TOO-STRONG / PRECOND-TOO-STRONG.
# Each ships a proof that actually closes for its new implementation shape; no
# obligation statement is touched, no helper lemma is added, no `sorry`.
# ===========================================================================

# pos-array-dispatch-on-request: the port of nagini's `pos-site1-branch-reorder`.
# Instead of normalising the request into a local and then selecting, dispatch on
# the request FIRST (an explicit choice decides directly; an unspecified one
# falls back to the supplied flag) and early-return a fully-built result from
# each of the four leaves. No accumulator, no `let mut`, both metadata branches
# written out twice. Behaviourally identical at every (request, flag) pair, so it
# must verify. The reshape is definitional per leaf, so the closed form is
# reproved by splitting the request and then the relevant boolean.
_POS_ARRAY_DISPATCH = """\
  -- dispatch on the request itself: an explicit choice decides directly, an
  -- unspecified one falls back to the supplied default flag
  match keepAttrs with
  | some k =>
    if k then
      return { dims := newDims, data := qs, attrs := some selfAttrs }
    else
      return { dims := newDims, data := qs, attrs := none }
  | none =>
    if globalDefault then
      return { dims := newDims, data := qs, attrs := some selfAttrs }
    else
      return { dims := newDims, data := qs, attrs := none }"""

_POS_ARRAY_DISPATCH_PROOF = """\
  cases keepAttrs with
  | none => cases globalDefault <;> rfl
  | some k => cases k <;> rfl"""

# pos-collection-map: the port of nagini's `pos-site2-inline`. The accumulator
# loop is replaced by a single traversal expression that forwards the same
# request to every member — the shape the delegation actually has once the
# temporary is dropped. Behaviourally identical, so it must verify; reproved by
# induction on the member list against the mapped closed form (the same Route-B
# shape as the frozen loop lemma, applied directly to the new body).
_POS_COLL_MAP = """\
  -- map each member array through the single-array reduction, forwarding the
  -- SAME keep request to every member
  return arrays.map (fun a =>
    implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault)"""

_POS_COLL_MAP_PROOF = """\
  intro arrays keepAttrs globalDefault
  unfold problem_spec_collectionQuantile implementation_collectionQuantile
  simp only [Id.run, bind, pure]
  induction arrays with
  | nil => rfl
  | cons a as ih => simp [List.map_cons, arrayQuantile_eq, ih]"""

# admiss-normal-input: the port of nagini's `admiss-site2-precond`. Nagini
# asserted in-body that the callee's read permission was in hand at the
# forwarding call site; here neither obligation has a precondition to satisfy,
# so the admissibility question becomes whether the spec is SATISFIABLE at a
# normal, report-shaped input rather than only vacuously true. This variant keeps
# the frozen bodies and the frozen proofs verbatim and only adds two in-body
# `have`s discharged by `decide`: the single-array predicate and the
# collection-level predicate each hold at a concrete input carrying a non-empty
# source payload, an explicit keep request, and a false fallback flag — the exact
# shape of the reported failing scenario. If either predicate were unsatisfiable
# there (PRECOND-TOO-STRONG / an over-constrained spec), `decide` would fail.
_ADMISS_COLL = """\
  -- a normal, report-shaped input is admitted by BOTH predicates: one member
  -- array carrying a non-empty metadata payload, an explicit keep request, and
  -- a false fallback flag
  have _hMember :
      problem_spec_arrayQuantile ["x"] [1] [("k1", "v1")] (some true) false
        { dims := ["x"], data := [1], attrs := some [("k1", "v1")] } := by
    unfold problem_spec_arrayQuantile resolveKeepAttrs
    decide
  have _hCollection :
      problem_spec_collectionQuantile
        [{ dims := ["x"], qs := [1], attrs := [("k1", "v1")] }] (some true) false
        [{ dims := ["x"], data := [1], attrs := some [("k1", "v1")] }] := by
    unfold problem_spec_collectionQuantile resolveKeepAttrs
    decide
  let mut out : Array QResult := #[]
  for a in arrays do
    -- forward the SAME keep request to each member array's reduction
    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
    out := out.push r
  return out.toList"""


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Every one edits ONLY
# an implementation region and ships a `witness` refuting it at a concrete input.
# ===========================================================================

# --- C2, the load-bearing clause: the resolved request ----------------------

# weak-array-always-keep — ports nagini `partial-always-keep`.
_WEAK_ALWAYS_KEEP = """\
  -- keep the source payload regardless of the request
  return { dims := newDims, data := qs, attrs := some selfAttrs }"""

# weak-array-always-drop — ports nagini `partial-always-drop`; this IS the
# single-array behaviour before the change (the result never carries the source
# payload).
_WEAK_ALWAYS_DROP = """\
  -- never carry the source payload
  return { dims := newDims, data := qs, attrs := none }"""

# weak-array-empty-payload — the NEAR-MISS of the above: the keep/drop decision
# is honoured exactly, but what is kept is an EMPTY payload rather than the
# source payload. Agrees with the frozen spec everywhere the source payload
# happens to be empty; wrong wherever it is not.
_WEAK_EMPTY_PAYLOAD = """\
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  -- honour the decision but carry an empty payload instead of the source one
  let attrs := if keep.getD globalDefault then some ([] : Attrs) else none
  return { dims := newDims, data := qs, attrs := attrs }"""

# weak-array-drop-branch-empty-payload — the OPTION-COLLAPSE near-miss, and the
# mirror of weak-array-empty-payload on the other branch: the keep/drop decision
# is honoured and the kept payload is the SOURCE payload, but the no-payload
# branch carries an EMPTY payload rather than NO payload. C2 pins that branch to
# `none`, and `none` and `some []` are two distinct points of `Option Attrs`, so
# the rival contradicts C2 exactly where the request resolves negative. Nothing
# else in the battery attacks the drop branch's `none` — every other C2 rival
# either gets the decision wrong or mangles the KEPT payload — so without this
# case a rival that collapsed "no payload" into "an empty payload" would verify
# unnoticed.
_WEAK_DROP_SOME_EMPTY = """\
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  -- the no-payload branch carries an EMPTY payload instead of no payload
  let attrs := if keep.getD globalDefault then some selfAttrs else some ([] : Attrs)
  return { dims := newDims, data := qs, attrs := attrs }"""

# weak-array-inverted-request — ports nagini `partial-inverted-flag`.
_WEAK_INVERTED = """\
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  -- carry the payload exactly when the resolved request says not to
  let attrs := if keep.getD globalDefault then none else some selfAttrs
  return { dims := newDims, data := qs, attrs := attrs }"""

# weak-array-unspecified-keeps — ports nagini `partial-none-defaults-keep`: the
# explicit branches are right, only the UNSPECIFIED branch is wrong — it keeps
# instead of consulting the supplied fallback flag.
_WEAK_UNSPEC_KEEPS = """\
  -- an unspecified request keeps, instead of consulting the supplied flag
  let keep := keepAttrs.getD true
  let attrs := if keep then some selfAttrs else none
  return { dims := newDims, data := qs, attrs := attrs }"""

# weak-array-unspecified-drops — the MIRROR of the above and the second half of
# the pair that pins the fallback flag in BOTH directions: the unspecified branch
# hardcodes drop, so the rival is wrong exactly where the supplied flag is true.
_WEAK_UNSPEC_DROPS = """\
  -- an unspecified request drops, instead of consulting the supplied flag
  let keep := keepAttrs.getD false
  let attrs := if keep then some selfAttrs else none
  return { dims := newDims, data := qs, attrs := attrs }"""

# weak-array-explicit-false-ignored — the narrowest near-miss on C2: an explicit
# NEGATIVE request is conflated with an unspecified one, so it falls through to
# the supplied flag. Correct at every explicit-keep request, at every unspecified
# request, and at an explicit-negative request whenever the flag is false; wrong
# only when an explicit negative request meets a true flag.
_WEAK_EXPLICIT_FALSE = """\
  -- treat an explicit negative request as if it were unspecified
  let keep := if keepAttrs = some true then true else globalDefault
  let attrs := if keep then some selfAttrs else none
  return { dims := newDims, data := qs, attrs := attrs }"""

# --- C0 / C1, the frame clauses --------------------------------------------

# weak-array-drops-labels — the metadata decision is honoured, but the branch
# that carries no payload also loses the surviving dimension labels. This is the
# frame attack nagini expressed as a write through a read-only reference: there
# is no heap here, so the analogue is an output component the spec pins to an
# input being produced from something else instead.
_WEAK_DROPS_LABELS = """\
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  if keep.getD globalDefault then
    return { dims := newDims, data := qs, attrs := some selfAttrs }
  else
    -- the no-payload branch also loses the surviving labels
    return { dims := [], data := qs, attrs := none }"""

# weak-array-clears-data — the same frame attack on the other pinned component:
# the branch that carries the payload returns empty value data.
_WEAK_CLEARS_DATA = """\
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  if keep.getD globalDefault then
    -- the payload-carrying branch also loses the value data
    return { dims := newDims, data := [], attrs := some selfAttrs }
  else
    return { dims := newDims, data := qs, attrs := none }"""

# --- the collection-level obligation: forwarding and traversal -------------

# weak-collection-swallows-request — ports nagini `site2-drops-flag`; this IS the
# collection-level behaviour before the change (the shared request never reached
# the per-member reduction, which then resolved from the fallback flag).
_WEAK_COLL_SWALLOWS = """\
  let mut out : Array QResult := #[]
  for a in arrays do
    -- the shared request never reaches the member reduction
    let r := implementation_arrayQuantile a.dims a.qs a.attrs none globalDefault
    out := out.push r
  return out.toList"""

# weak-collection-forces-keep — the mirror of the above: the collection level
# forwards an explicit KEEP to every member regardless of what was asked.
_WEAK_COLL_FORCES = """\
  let mut out : Array QResult := #[]
  for a in arrays do
    -- force an explicit keep onto every member, whatever was asked
    let r := implementation_arrayQuantile a.dims a.qs a.attrs (some true) globalDefault
    out := out.push r
  return out.toList"""

# weak-collection-leading-member-only — the request reaches the LEADING member
# and every later member falls back to the flag. Indistinguishable from gold on
# every single-member collection; wrong from the second member onward.
_WEAK_COLL_LEADING = """\
  let mut out : Array QResult := #[]
  let mut leading := true
  for a in arrays do
    -- only the leading member receives the shared request
    let req := if leading then keepAttrs else none
    leading := false
    let r := implementation_arrayQuantile a.dims a.qs a.attrs req globalDefault
    out := out.push r
  return out.toList"""

# weak-collection-hardcodes-default — the shared request IS forwarded to every
# member, but the fallback flag is not: a negative fallback is substituted for
# the supplied one. Indistinguishable from gold at every explicit request and at
# every false fallback; wrong exactly where an unspecified request meets a true
# fallback. This is the case that moves the collection level's `globalDefault`
# binder off false.
_WEAK_COLL_HARDCODES_DEFAULT = """\
  let mut out : Array QResult := #[]
  for a in arrays do
    -- the request is forwarded, but the supplied fallback flag is not
    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs false
    out := out.push r
  return out.toList"""

# weak-collection-drops-trailing — the LENGTH attack. The request is forwarded
# faithfully to every member and every emitted result is per-member correct, but
# the trailing member's reduction never reaches the result. The mapped
# postcondition pins the result to `arrays.map f`, whose LENGTH is the input's;
# the reversal rival permutes a list of the right length and the
# leading-member rival changes a member's content, so neither one moves the
# length. Without this case a rival that silently shortened the collection would
# verify unnoticed.
_WEAK_COLL_DROPS_TRAILING = """\
  let mut out : Array QResult := #[]
  for a in arrays do
    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
    out := out.push r
  -- the trailing member's reduction never reaches the result
  return out.toList.dropLast"""

# weak-collection-reversed — the request is forwarded correctly to every member,
# but the members are emitted in the opposite order, so each reduced result is
# paired with the wrong member. Attacks the ORDER the mapped postcondition pins.
_WEAK_COLL_REVERSED = """\
  let mut out : Array QResult := #[]
  for a in arrays.reverse do
    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
    out := out.push r
  return out.toList"""


def _wit_array(newDims, qs, selfAttrs, keepAttrs, globalDefault):
    """A witness refuting the single-array predicate at one literal input."""
    args = f"{newDims} {qs} {selfAttrs} {keepAttrs} {globalDefault}"
    return (f"example : ¬ problem_spec_arrayQuantile {args}\n"
            f"    (implementation_arrayQuantile {args}) := by\n"
            "  unfold problem_spec_arrayQuantile implementation_arrayQuantile "
            "resolveKeepAttrs\n"
            "  decide\n")


def _wit_coll(arrays, keepAttrs, globalDefault):
    """A witness refuting the collection-level predicate at one literal input."""
    args = f"{arrays} {keepAttrs} {globalDefault}"
    return (f"example : ¬ problem_spec_collectionQuantile {args}\n"
            f"    (implementation_collectionQuantile {args}) := by\n"
            "  unfold problem_spec_collectionQuantile "
            "implementation_collectionQuantile resolveKeepAttrs\n"
            "  decide\n")


_A1 = '[("k1", "v1")]'
_A2 = '[("k1", "v1"), ("k2", "v2")]'
_M1 = '{ dims := ["x"], qs := [1], attrs := [("k1", "v1")] }'
_M2 = '{ dims := ["y"], qs := [2], attrs := [("k2", "v2")] }'
_M3 = '{ dims := ["x", "y"], qs := [3, 4], attrs := [("k3", "v3")] }'


SPEC_TESTS = [

    # ------------------------------------------------------------------ +
    {
        "id": "pos-array-dispatch-on-request",
        "kind": "soundness",
        "expect": "verify",
        "module": _array(_POS_ARRAY_DISPATCH, _POS_ARRAY_DISPATCH_PROOF),
        "rationale": "a structurally different but behaviourally identical "
                     "single-array implementation: dispatch on the request "
                     "first and early-return a fully-built result from each of "
                     "the four leaves, with no normalising local and both "
                     "metadata branches written out twice. It agrees with the "
                     "frozen implementation at every (request, flag) pair, so "
                     "C0/C1/C2 all hold and it MUST verify (else "
                     "SPEC-TOO-STRONG: the spec would be pinning the "
                     "particular encoding of the decision rather than the "
                     "decision). Reproved honestly for the new shape by "
                     "splitting the request and then the relevant boolean — "
                     "the obligation statement is byte-identical and no lemma "
                     "is added.",
    },
    {
        "id": "pos-collection-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _coll(_POS_COLL_MAP, _POS_COLL_MAP_PROOF),
        "rationale": "the collection-level accumulator loop replaced by a "
                     "single traversal expression that forwards the SAME "
                     "request to every member — behaviourally identical, so it "
                     "must verify (else SPEC-TOO-STRONG: the mapped "
                     "postcondition would be pinning the imperative "
                     "accumulation rather than the mapping). Reproved by "
                     "induction on the member list against the mapped closed "
                     "form; the obligation statement is untouched.",
    },
    {
        "id": "admiss-normal-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _coll(_ADMISS_COLL),
        "rationale": "neither obligation carries a precondition, so "
                     "admissibility here is satisfiability at a normal input "
                     "rather than only vacuous truth. Keeping both frozen "
                     "bodies and both frozen proofs verbatim, this variant adds "
                     "two in-body `have`s discharged by `decide`: the "
                     "single-array predicate and the collection-level predicate "
                     "each HOLD at a report-shaped input (one member array, a "
                     "non-empty source payload, an explicit keep request, a "
                     "false fallback flag). If the spec were over-constrained "
                     "at that point — the very input the reported failure is "
                     "about — `decide` would fail and the case would surface "
                     "PRECOND-TOO-STRONG.",
    },

    # ------------------------------------------------------------------ -
    {
        "id": "weak-array-always-keep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_ALWAYS_KEEP),
        "rationale": "attacks C2 (`result.attrs = if resolveKeepAttrs keepAttrs "
                     "globalDefault then some selfAttrs else none`) on the "
                     "resolved-negative subdomain: the rival carries the source "
                     "payload unconditionally, so it agrees with the spec "
                     "wherever the request resolves positive and contradicts it "
                     "wherever it resolves negative. Refuted at keepAttrs = "
                     "some false with a non-empty source payload, where the "
                     "spec pins `none`. If it verified, the negative branch of "
                     "C2 would be unpinned (SPEC-TOO-WEAK).",
        "refinement": "a faithful patch that carried the source metadata "
                      "regardless of the request would honour the positive "
                      "request the report demonstrates, but it would also "
                      "attach metadata where the caller explicitly asked for "
                      "none and where the unspecified request falls back to a "
                      "negative default. The documented default for this "
                      "reduction is to return no metadata, and the "
                      "already-passing metadata-preservation checks in the same "
                      "suite assert exactly that a default-request reduction "
                      "carries no metadata while an explicit positive request "
                      "carries all of it. Such a patch fails the negative half "
                      "and does NOT resolve.",
        "witness": _wit_array('["x"]', "[1]", _A1, "(some false)", "false"),
    },
    {
        "id": "weak-array-always-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_ALWAYS_DROP),
        "rationale": "attacks C2 on the resolved-positive subdomain, and is the "
                     "single-array behaviour the report describes: the result "
                     "never carries the source payload. Refuted at keepAttrs = "
                     "some true with a non-empty source payload, where the spec "
                     "pins `some selfAttrs` and the rival yields `none`. This "
                     "is the exact clause the bundle's prepatch variant fails "
                     "(G-DIFF), so if it verified the spec would not see the "
                     "reported defect at all (SPEC-TOO-WEAK).",
        "refinement": "this IS the pre-change behaviour: a reduction whose "
                      "result never carries the source metadata. The reported "
                      "scenario asks for the metadata explicitly and observes "
                      "an empty mapping instead of the source mapping, and the "
                      "failing test in the suite asserts the reduced object's "
                      "metadata equals the source object's. A patch with this "
                      "behaviour is precisely the unfixed code and does NOT "
                      "resolve.",
        "witness": _wit_array('["x"]', "[1]", _A1, "(some true)", "false"),
    },
    {
        "id": "weak-array-empty-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_EMPTY_PAYLOAD),
        "rationale": "the NEAR-MISS of weak-array-always-drop, and the case "
                     "that makes C2's dependence on the `selfAttrs` binder a "
                     "measured fact: the keep/drop decision is honoured "
                     "exactly, but the payload carried is empty rather than the "
                     "SOURCE payload. It agrees with the frozen spec at every "
                     "input whose source payload is empty — a strictly larger "
                     "agreement region than always-drop — so it is refuted at "
                     "its own distinguishing input: a TWO-entry source payload "
                     "with keepAttrs = some true, where the spec pins `some "
                     "selfAttrs`. If it verified, C2 would pin only whether a "
                     "payload is present, not which payload (SPEC-TOO-WEAK).",
        "refinement": "a patch that attached a fresh empty metadata mapping "
                      "instead of the source mapping would make the reduced "
                      "object report an empty mapping — which is exactly the "
                      "observed wrong output in the report, and exactly what "
                      "the failing assertion (reduced metadata equals source "
                      "metadata) rejects, for every source object that carries "
                      "any metadata at all. It does NOT resolve.",
        "witness": _wit_array('["x"]', "[1]", _A2, "(some true)", "false"),
    },
    {
        "id": "weak-array-drop-branch-empty-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_DROP_SOME_EMPTY),
        "rationale": "the OPTION-COLLAPSE near-miss on C2, and the mirror of "
                     "weak-array-empty-payload on the other branch: the "
                     "keep/drop decision is honoured exactly AND the kept "
                     "payload is the source payload, but the no-payload branch "
                     "carries an EMPTY payload (`some []`) where C2 pins NO "
                     "payload (`none`). Those are two distinct points of "
                     "`Option Attrs` on this carrier, so the rival contradicts "
                     "C2 wherever the request resolves negative; it is refuted "
                     "at an unspecified request with a false fallback flag and a "
                     "two-entry source payload. Every other C2 rival either gets "
                     "the decision wrong or mangles the KEPT payload, so the "
                     "drop branch's `none` was unattacked: a rival that "
                     "collapsed 'no payload' into 'an empty payload' would have "
                     "verified unnoticed (SPEC-TOO-WEAK).",
        "refinement": "a patch that attached an empty metadata mapping instead "
                      "of no mapping at all whenever the metadata is not kept "
                      "would make every default reduction report a present but "
                      "empty mapping rather than an absent one. The two are "
                      "distinguishable by callers that test for the mapping's "
                      "presence, so a patch of this shape changes the default "
                      "observable and does NOT faithfully implement the "
                      "documented drop behavior.",
        "witness": _wit_array('["z"]', "[9]", _A2, "none", "false"),
    },
    {
        "id": "weak-array-inverted-request",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_INVERTED),
        "rationale": "attacks C2 on BOTH subdomains at once: the resolved "
                     "request is computed correctly and then applied backwards, "
                     "so the payload is carried exactly when the spec says it "
                     "must not be and dropped exactly when it must be carried. "
                     "Refuted at an unspecified request with a TRUE fallback "
                     "flag (a point no other rival is refuted at), which pins "
                     "both the fallback path and the direction of the "
                     "selection: the spec resolves positive there and the rival "
                     "yields `none`.",
        "refinement": "inverting the selection drops the metadata precisely "
                      "when the caller asked to keep it and keeps it precisely "
                      "when the caller asked to drop it. The reported scenario "
                      "asks to keep and would still observe an empty mapping, "
                      "and the already-passing default-drop checks would start "
                      "observing metadata. It fails both halves and does NOT "
                      "resolve.",
        "witness": _wit_array('["x", "y"]', "[1, 2]", _A1, "none", "true"),
    },
    {
        "id": "weak-array-unspecified-keeps",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_UNSPEC_KEEPS),
        "rationale": "attacks C2 through `resolveKeepAttrs` on the UNSPECIFIED "
                     "subdomain only: both explicit branches are handled "
                     "correctly, but an unspecified request hardcodes keep "
                     "instead of consulting the supplied fallback flag. Refuted "
                     "at keepAttrs = none with globalDefault = false, where the "
                     "spec resolves negative and pins `none`. Together with its "
                     "mirror (weak-array-unspecified-drops) this pins the "
                     "spec's dependence on the `globalDefault` binder in both "
                     "directions; if it verified, the fallback would be "
                     "unpinned in the keeping direction (SPEC-TOO-WEAK).",
        "refinement": "a patch that defaulted an unspecified request to keep "
                      "would reverse the documented default for this reduction, "
                      "which is to return no metadata. The already-passing "
                      "metadata checks in the same suite assert that a "
                      "reduction with no explicit request carries no metadata; "
                      "such a patch makes them observe the source metadata "
                      "instead, so it does NOT resolve.",
        "witness": _wit_array('["x"]', "[1]", _A1, "none", "false"),
    },
    {
        "id": "weak-array-unspecified-drops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_UNSPEC_DROPS),
        "rationale": "the MIRROR of weak-array-unspecified-keeps and the other "
                     "half of the pair that pins `globalDefault`: the "
                     "unspecified branch hardcodes DROP rather than consulting "
                     "the supplied flag, so the rival is wrong exactly where "
                     "the flag is true. Refuted at keepAttrs = none with "
                     "globalDefault = true, where the spec resolves positive "
                     "and pins `some selfAttrs`. Without this case the battery "
                     "would only ever probe the fallback flag at false, and a "
                     "rival that ignored the flag in the negative direction "
                     "would verify unnoticed.",
        "refinement": "a patch that hardcoded an unspecified request to drop, "
                      "rather than consulting the ambient default, would ignore "
                      "an ambient configuration that asks for metadata to be "
                      "preserved. Callers that set that configuration globally "
                      "and then reduce without an explicit request would "
                      "silently lose their metadata, which is the same class of "
                      "defect the report is about, one level of indirection "
                      "away; it does NOT faithfully implement the resolution "
                      "rule.",
        "witness": _wit_array('["x"]', "[1]", _A1, "none", "true"),
    },
    {
        "id": "weak-array-explicit-false-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_EXPLICIT_FALSE),
        "rationale": "the narrowest near-miss on C2: an explicit NEGATIVE "
                     "request is conflated with an unspecified one and falls "
                     "through to the fallback flag. It agrees with the frozen "
                     "spec at every positive request, at every unspecified "
                     "request, and at a negative request whenever the flag is "
                     "false — so its whole wrong subdomain is the single "
                     "combination (explicit negative request, true flag), and "
                     "that is exactly where it is refuted. This is the case "
                     "that shows C2 distinguishes an explicit negative request "
                     "from an absent one; the two are `some false` and `none` "
                     "and `getD` treats them differently.",
        "refinement": "a patch that treated an explicit negative request as "
                      "absent would override a caller's explicit instruction "
                      "with an ambient setting: under a configuration asking "
                      "for metadata to be preserved, a caller explicitly "
                      "requesting NO metadata would get metadata anyway. "
                      "Explicitly requesting no metadata is the documented way "
                      "to opt out, so a patch that cannot honour it does NOT "
                      "faithfully implement the behavior the report asks for.",
        "witness": _wit_array('["y"]', "[3]", '[("k2", "v2")]',
                              "(some false)", "true"),
    },
    {
        "id": "weak-array-drops-labels",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_DROPS_LABELS),
        "rationale": "attacks C0 (`result.dims = newDims`) — the frame clause "
                     "pinning the surviving dimension labels to their input. "
                     "The metadata decision itself is honoured exactly; the "
                     "no-payload branch additionally returns empty labels. This "
                     "is the port of nagini's read-only-frame rival: there is "
                     "no heap here to write through, so the analogue of "
                     "corrupting a read-only input is producing a pinned output "
                     "component from something other than its input. Refuted at "
                     "a TWO-label input with keepAttrs = some false, which is "
                     "also the only reject witness that moves the `newDims` "
                     "binder off a single label. If it verified, the labels "
                     "would be unconstrained in one metadata branch — the frame "
                     "hole (SPEC-TOO-WEAK).",
        "refinement": "a patch that rebuilt the reduced object without its "
                      "surviving dimension labels whenever no metadata is "
                      "carried would change the SHAPE of every default "
                      "reduction, not just its metadata. The failing test in "
                      "the suite also compares the reduced values against a "
                      "reference array, and the many already-passing reduction "
                      "checks compare shapes and labels; a shape change breaks "
                      "them wholesale, so it does NOT resolve.",
        "witness": _wit_array('["x", "y"]', "[5]", _A1, "(some false)", "false"),
    },
    {
        "id": "weak-array-clears-data",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _array(_WEAK_CLEARS_DATA),
        "rationale": "attacks C1 (`result.data = qs`) — the other frame clause, "
                     "in the other metadata branch: the payload-carrying branch "
                     "returns empty value data. Refuted at a TWO-element data "
                     "input with keepAttrs = some true, the only reject witness "
                     "that moves the `qs` binder off a single element. Paired "
                     "with weak-array-drops-labels this shows both pinned "
                     "output components are attacked, and in DIFFERENT branches "
                     "of the metadata decision, so neither clause is defended "
                     "only where the other happens to bite.",
        "refinement": "a patch that returned an empty value array whenever the "
                      "metadata is carried would break the reported scenario "
                      "itself: it asks for the metadata explicitly and then "
                      "compares the reduced values against a reference array, "
                      "so the values would be empty where the reference is not. "
                      "It does NOT resolve.",
        "witness": _wit_array('["x"]', "[7, 8]", _A1, "(some true)", "false"),
    },
    {
        "id": "weak-collection-swallows-request",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _coll(_WEAK_COLL_SWALLOWS),
        "rationale": "attacks the collection-level postcondition's forwarding "
                     "content, and is the collection-level behaviour the report "
                     "describes: the shared request never reaches the "
                     "per-member reduction, which then resolves from the "
                     "fallback flag. The postcondition pins each member's "
                     "metadata to `if resolveKeepAttrs keepAttrs globalDefault "
                     "then some a.attrs else none` — the CALLER's request — so "
                     "substituting an unspecified request contradicts it "
                     "wherever the two resolve differently. Refuted at one "
                     "member with keepAttrs = some true and globalDefault = "
                     "false. This is the clause the bundle's second prepatch "
                     "variant fails (G-DIFF).",
        "refinement": "this IS the pre-change behaviour of the collection-level "
                      "path: the per-member reduction was invoked without the "
                      "request the caller supplied, so every member resolved "
                      "from the ambient default and dropped its metadata. The "
                      "reported call reaches the per-member reduction through "
                      "exactly this path, so with this behaviour the reported "
                      "scenario still observes an empty mapping and the failing "
                      "assertion still fails. It is the unfixed code and does "
                      "NOT resolve.",
        "witness": _wit_coll(f"[{_M1}]", "(some true)", "false"),
    },
    {
        "id": "weak-collection-forces-keep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _coll(_WEAK_COLL_FORCES),
        "rationale": "the mirror of weak-collection-swallows-request: the "
                     "collection level forwards an explicit POSITIVE request to "
                     "every member whatever the caller asked, so it is right "
                     "wherever the caller's request resolves positive and wrong "
                     "wherever it resolves negative. Refuted at one member with "
                     "keepAttrs = some false. Without this case the forwarding "
                     "would be attacked only in the swallowing direction, and a "
                     "rival that ignored the request by forcing it the other "
                     "way would verify unnoticed (SPEC-TOO-WEAK).",
        "refinement": "hardcoding a positive request at the collection level "
                      "would fix the reported scenario while making every "
                      "default collection-level reduction carry each member's "
                      "metadata. The documented default is to carry none, and "
                      "the already-passing metadata checks in the same suite "
                      "assert that; such a patch breaks them, so it does NOT "
                      "resolve.",
        "witness": _wit_coll(f"[{_M1}]", "(some false)", "false"),
    },
    {
        "id": "weak-collection-hardcodes-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _coll(_WEAK_COLL_HARDCODES_DEFAULT),
        "rationale": "the collection-level postcondition resolves each member's "
                     "metadata through `resolveKeepAttrs keepAttrs "
                     "globalDefault`, so it depends on TWO inputs and this "
                     "rival abuses the second one: the shared request is "
                     "forwarded faithfully to every member, but a negative "
                     "fallback is substituted for the supplied one. It agrees "
                     "with the frozen spec at every explicit request (where the "
                     "fallback is irrelevant) and at every false fallback, so it "
                     "is refuted where its wrong subdomain lies — an "
                     "unspecified request with globalDefault = true, where the "
                     "spec pins each member's metadata to `some a.attrs` and "
                     "the rival yields `none`. Every other collection-level "
                     "rival is refuted at a false fallback; without this one "
                     "the battery would say nothing about the collection "
                     "level's dependence on the fallback flag, and a rival that "
                     "hardcoded it would verify unnoticed (SPEC-TOO-WEAK).",
        "refinement": "the collection-level path must consult the same ambient "
                      "default the per-member reduction consults; a patch that "
                      "hardcoded a negative fallback there would ignore an "
                      "ambient configuration asking for metadata to be "
                      "preserved, so a caller who set that configuration "
                      "globally and then reduced a collection without an "
                      "explicit request would silently lose every member's "
                      "metadata. That is the same defect the report is about, "
                      "reached through the ambient setting rather than the "
                      "explicit argument, so the patch does NOT faithfully "
                      "implement the resolution rule.",
        "witness": _wit_coll(f"[{_M1}]", "none", "true"),
    },
    {
        "id": "weak-collection-leading-member-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _coll(_WEAK_COLL_LEADING),
        "rationale": "attacks the postcondition's claim that the ONE shared "
                     "request is forwarded to EVERY member, which is a claim "
                     "about the traversal and not just about the request. The "
                     "rival forwards it to the leading member only; it is "
                     "therefore indistinguishable from the frozen "
                     "implementation on every single-member collection, so it "
                     "is refuted at a TWO-member input with keepAttrs = some "
                     "true and globalDefault = false — the second member's "
                     "metadata is pinned to `some a.attrs` and the rival yields "
                     "`none`. This is the case that moves the `arrays` binder "
                     "off a one-element list; without it a rival that mishandled "
                     "any member but the first would verify.",
        "refinement": "a patch that threaded the request into only the first "
                      "member's reduction would leave every later member's "
                      "metadata dropped. The reported scenario happens to go "
                      "through a single-member collection and would pass, which "
                      "is exactly what makes this a verify-does-not-imply-"
                      "resolve hazard: any collection carrying more than one "
                      "member silently loses metadata on all but the first, so "
                      "the patch does NOT faithfully implement the "
                      "forwarding.",
        "witness": _wit_coll(f"[{_M1}, {_M2}]", "(some true)", "false"),
    },
    {
        "id": "weak-collection-drops-trailing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _coll(_WEAK_COLL_DROPS_TRAILING),
        "rationale": "attacks the LENGTH the mapped postcondition pins. "
                     "`result = arrays.map f` forces the result to have exactly "
                     "as many members as the input, and this rival forwards the "
                     "shared request faithfully and emits every member "
                     "correctly — it simply drops the trailing one, so it is "
                     "wrong on every collection with at least one member. "
                     "Refuted at a two-member input with an unspecified request "
                     "and a TRUE fallback flag. The reversal rival permutes a "
                     "list of the RIGHT length and the leading-member rival "
                     "changes a member's content, so neither moves the length; "
                     "without this case a rival that silently shortened the "
                     "collection would verify unnoticed (SPEC-TOO-WEAK).",
        "refinement": "a patch that left the last reduced member out of the "
                      "collection-level result would silently lose a whole "
                      "member, not merely its metadata: callers would see a "
                      "collection with fewer members than they reduced. The "
                      "reported scenario goes through a single-member "
                      "collection, so it would report no member at all rather "
                      "than the requested metadata; the patch does NOT resolve.",
        "witness": _wit_coll(f"[{_M2}, {_M3}]", "none", "true"),
    },
    {
        "id": "weak-collection-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _coll(_WEAK_COLL_REVERSED),
        "rationale": "attacks the structural half of the collection-level "
                     "postcondition: `result = arrays.map f` pins the ORDER and "
                     "the per-member pairing, not just the metadata decision. "
                     "This rival forwards the request correctly to every member "
                     "and still contradicts the spec, because it emits the "
                     "members in the opposite order, pairing each reduced "
                     "result with the wrong member's labels and data. Refuted "
                     "at a two-member input whose members differ in labels and "
                     "data (with keepAttrs = some true, globalDefault = false), "
                     "a distinct input point from the leading-member rival. If "
                     "it verified, the mapping would be pinned only as a "
                     "multiset of results (SPEC-TOO-WEAK).",
        "refinement": "the collection-level reduction associates each reduced "
                      "result with the member it came from; a patch that "
                      "reversed the traversal would attach each reduced result "
                      "to the wrong member, changing the labels and values "
                      "reported for every member of any collection with more "
                      "than one. The reported scenario's own value comparison "
                      "and the many already-passing reduction checks compare "
                      "per-member values and labels, so such a patch does NOT "
                      "resolve.",
        "witness": _wit_coll(f"[{_M2}, {_M3}]", "(some true)", "false"),
    },
]


assessment = """\
PORTED (nagini -> lean), case by case.

  * nagini `pos-site1-branch-reorder` (soundness, site 1) ->
    `pos-array-dispatch-on-request`. Same argument (a branch-reordered,
    early-returning, behaviourally identical implementation of the same
    decision must verify); re-expressed as a match on the three-valued request
    with four fully-built early returns, and REPROVED for the new shape (split
    the request, then the relevant boolean). The obligation statement is
    byte-identical.
  * nagini `pos-site2-inline` (soundness, site 2) -> `pos-collection-map`. Same
    argument (inline the delegation, drop the temporary); here the accumulator
    loop becomes a single traversal expression, reproved by induction on the
    member list.
  * nagini `admiss-site2-precond` (admissibility) -> `admiss-normal-input`.
    Nagini's version asserted in-body that the callee's read permission was in
    hand at the forwarding call site. Neither obligation here has a
    precondition, so the ported claim is the other half of the same question:
    both predicates are SATISFIABLE at a normal, report-shaped input rather
    than only vacuously true. Both frozen bodies and both frozen proofs are
    kept verbatim; only two `decide`-discharged `have`s are added. Those `have`s
    were confirmed by build during the audit to carry information rather than
    being inert decoration: restating either of them at a point where the
    predicate is FALSE (the same input, but with the metadata dropped though the
    request is an explicit positive) makes the variant FAIL to elaborate
    (`decide` reports the proposition "is false", exit 1, both sites). So the
    positive genuinely witnesses satisfiability at that input rather than
    passing because `decide` closes anything put in front of it.
  * nagini `partial-always-keep` -> `weak-array-always-keep`.
  * nagini `partial-always-drop` (the site-1 pre-change behaviour) ->
    `weak-array-always-drop`.
  * nagini `partial-inverted-flag` -> `weak-array-inverted-request`.
  * nagini `partial-none-defaults-keep` -> `weak-array-unspecified-keeps`.
  * nagini `site2-drops-flag` (the site-2 pre-change behaviour) ->
    `weak-collection-swallows-request`.
  * nagini `frame-mutate-self_meta` and `frame-mutate-self_meta-index`
    (uniqueness, permission mutation) -> re-expressed as
    `weak-array-drops-labels` and `weak-array-clears-data`. See the note below:
    the permission MECHANISM is vacuous here, but the OBLIGATION those two
    cases defend is not, and this carrier states it explicitly.

ADDED BEYOND NAGINI (rivals this carrier makes expressible, each closing a
coverage gap the ported set left open):

  * `weak-array-empty-payload` — nagini's oracle is `selected_meta(ToSeq(
    self_meta), ...)`, so its always-drop rival already exercised the payload's
    CONTENTS. Here C2's kept branch is `some selfAttrs`, and every ported rival
    was refuted with a single-entry payload, which would not have distinguished
    "carries the source payload" from "carries some payload". This near-miss
    honours the decision exactly and carries an EMPTY payload; it is refuted at
    a two-entry payload, making the `selfAttrs` dependence measured.
  * `weak-array-unspecified-drops` — the mirror of the ported
    `partial-none-defaults-keep`. Nagini's ambient default is a nullary axiom
    pinned to a single value, so only one direction was attackable there; here
    the default is an INPUT BINDER (`globalDefault`), and the ported case alone
    would have probed it at `false` only. The pair now pins it both ways.
  * `weak-array-explicit-false-ignored` — the three-valued request is
    `Option Bool` here, so `some false` and `none` are two distinct carrier
    points and a rival can conflate exactly those two and nothing else. Its
    whole wrong subdomain is one combination, and it is refuted there.
  * `weak-collection-forces-keep` — the mirror of the ported `site2-drops-flag`.
  * `weak-collection-hardcodes-default` — the collection-level postcondition
    resolves through BOTH `keepAttrs` and `globalDefault`, and nagini's site-2
    case attacks only the forwarded request (its ambient default is a nullary
    axiom, not an input, so there is no second input to abuse there). Without
    this rival every collection-level witness held the fallback flag at false —
    the exact shape the porting rules warn about — and a rival hardcoding it
    would have verified unnoticed. It was added in response to a real
    `pbt_coverage.py` finding, not authored speculatively.
  * `weak-array-drop-branch-empty-payload` — ADDED BY AUDIT. C2 pins the drop
    branch to `none`, and on this carrier `none` and `some []` are two distinct
    points of `Option Attrs`; the nagini oracle's drop branch is the EMPTY LIST,
    so that distinction does not exist there and no ported rival could carry it.
    Every other C2 rival here either gets the decision wrong or mangles the KEPT
    payload, leaving the drop branch's `none` unattacked — an option-collapsing
    rival would have verified unnoticed. Refuted at an unspecified request with
    a false fallback and a two-entry payload.
  * `weak-collection-drops-trailing` — ADDED BY AUDIT. `result = arrays.map f`
    pins the LENGTH as well as the order and the per-member content, and the two
    traversal rivals below move neither: a reversal permutes a list of the right
    length and the leading-member rival changes a member's content. This rival
    forwards the request faithfully, emits every member correctly, and drops the
    trailing one; refuted at a two-member input with an unspecified request and a
    TRUE fallback flag.
  * `weak-collection-leading-member-only` and `weak-collection-reversed` — the
    collection-level postcondition is `result = arrays.map f`, which pins the
    length, the order and the per-member pairing as well as the forwarding.
    Nagini models this site as a single scalar delegation, so it has no
    traversal to attack; these two attack it, and are the only reject cases
    that move the `arrays` binder off a one-element list.

OMITTED, and why:

  * The nagini FRAME / PERMISSION-MUTATION mechanism (`frame-mutate-*`
    rejected for INSUFFICIENT PERMISSION on a half-permission input) is
    VACUOUS on this backend. Lean is referentially transparent: an input
    carries no heap permission, there is no aliasing, and an implementation
    cannot write through an argument at all — the rival is not expressible, so
    no substitute is fabricated for the MECHANISM. What those two cases
    actually defend, though — that a component the spec pins to an input is not
    left free for the implementation to fill in — is live here and is defended
    explicitly by `weak-array-drops-labels` (C0) and `weak-array-clears-data`
    (C1), which is why they appear above as re-expressions rather than as
    omissions. Confirmed by build during the audit rather than argued: an impl
    that "mutates" the source payload (`let mut sa := selfAttrs; sa := sa ++
    [...]`) and then returns the frozen answer VERIFIES (exit 0), because the
    rebinding is invisible to the result. There is no permission to violate, so
    the MECHANISM is genuinely inexpressible — a rival of that shape would be a
    vacuous positive, not a reject case.
  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. The
    nagini sibling carries no `diverge-*` / `nonterm-*` case, so nothing was
    dropped in the port, but the class is NOT vacuous here and an earlier
    revision of this file claimed it was ("a diverging implementation cannot be
    written at all"). That claim is measurably false and is corrected here.
    Measured with real builds on this bundle:

      - A `while n < 1 do n := n` loop with no decreasing measure IS writable
        inside an `impl` region: `Lean.Loop.mk`'s `ForIn` instance is what the
        `while` sugar elaborates to, so no termination obligation is raised and
        the file is admissible under `variant_scope` (scope_problems == []).
        Only an explicit `let rec` without a measure is refused, and that is
        refused by the equation compiler ("fail to show termination"), i.e. the
        file does not compile rather than the SPEC rejecting it.
      - A variant carrying the frozen body PLUS such a loop whose value is
        DISCARDED VERIFIES against the frozen spec and the frozen proof, both
        at the single-array site and at the collection site (exit 0, both).
        The reason is definitional, not a spec weakness: in `Id`, a bound whose
        value is never used is erased by `rfl` — a standalone
        `(Id.run do let mut n := 0; while n < 1 do n := n; return 7) = 7`
        closes by `rfl`. So the loop is not observable in the result and the
        spec, which constrains only the result, cannot see it.
      - A variant whose ANSWER depends on the loop's value does NOT verify, and
        no witness can be landed against it: the refutation's `decide` fails
        ("Tactic `decide` failed") on the unreduced `forIn Lean.Loop.mk` term,
        while a trivial `1 + 1 = 2` claim in the same file builds fine — so the
        exit code carries no information about the claim, which is exactly the
        `witness-undecided` shape the gate screens for.

    So there is nothing shippable in this lane: a discarded divergence is
    invisible to any result-level spec (and to the real behavior it models), and
    a load-bearing one cannot be refuted by a witness on this carrier. That is a
    KNOWN HOLE in what a result-level postcondition can express, recorded as
    such rather than as "the class does not exist".
  * nagini AXIOM_TESTS (`ax-sound-ambient_keep_default`,
    `ax-cover-ambient_keep_default`) — dropped, per the porting rules: the axiom
    lane is G-AX's job and this gate ignores it. There is nothing to port in any
    case: this bundle declares NO callee axiom (meta.json `axioms: []`, G-AX
    skips). Nagini axiomatises the ambient default resolver as a nullary
    `@ContractOnly` pinned to False; here the resolved default is a modeled
    INPUT BINDER (`globalDefault`), validated end-to-end by G-CONF, which is
    also what makes the two `unspecified-*` rivals above able to attack it in
    both directions.
  * The nagini "ungrounded-oracle echo" class is recorded there as NOT
    APPLICABLE because its oracle is a fully-unfolded pure function of the
    inputs. The same holds here and for the same reason: C2's right-hand side is
    `if keepAttrs.getD globalDefault then some selfAttrs else none`, built only
    from the binders, with no `opaque` callee anywhere in the file. There is no
    answer key to echo, so no rival of that class is fabricated; the honest
    cheapest-implementation positive controls stand in its place.

No soundness positive was dropped for a proof that would not close: both
reshapes above were chosen so their proofs stay close to the frozen ones (a
case split for the first, the frozen Route-B induction applied directly to the
mapped body for the second), and both close with no new lemma, no weakened
statement and no `sorry`.

Every witness states its refutation at literal inputs and closes by `decide`:
this carrier is fully transparent (`Attrs`, `QResult`, `SrcArray` all derive
`DecidableEq`; no `opaque` term appears in the file), so no witness needed to
condition on a hypothesis, and none can therefore be inconsistent.
"""
