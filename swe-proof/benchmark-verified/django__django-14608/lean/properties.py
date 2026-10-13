# properties.py — G-PBT falsification battery for django__django-14608 (lean lane).
# NOT a Lean module; a record of adversarial cases the gate elaborates against the
# frozen spec. Ported from the nagini sibling's properties.py, re-expressed
# against this backend's carrier.
#
# Defended surface (read from Solution.lean):
#   implementation_nonFormErrors
#     (isBound mgmtValid : Bool) (mgmtError : String)
#     (raised : Option (List String)) : ErrorList
#   The error collection a form-set produces for its non-form errors. The single
#   obligation `correct_nonFormErrors` is total (no precondition hypothesis: the
#   four binders range over their whole types), and `problem_spec_nonFormErrors`
#   has exactly TWO independent top-level conjuncts:
#     (C1) result.cssClass = "errorlist nonform"
#          — the rendered class carries the base class AND the non-form marker,
#            on EVERY production path. This is the load-bearing clause: it holds
#            unconditionally, so it constrains all three paths at once.
#     (C2) result.messages = expectedMessages isBound mgmtValid mgmtError raised
#          — the carried messages, pinned per path by the `pure`-region fold:
#            unbound => empty; cross-collection report present => exactly the
#            reported messages (regardless of the bookkeeping flag); otherwise
#            invalid bookkeeping => the single supplied message; else empty.
#
# Where the spec's strength comes from (the nagini argument, re-expressed):
#   * C1 is pinned to a fully GROUNDED literal — a `String` the spec spells out —
#     and `mkErrorList`'s class rule is modeled DEEPLY in the `pure` region, not
#     axiomatized (meta.axioms == [], opaque_callees == []). So there is no opaque
#     answer-key an impl could echo without doing the work: the cheapest impl that
#     satisfies C1 IS the honest one. That is why the nagini file shipped no
#     "wrong echo" rival and neither does this port; instead the soundness lane
#     carries honest positive controls, including one that builds the class string
#     compositionally and one that bypasses the deep-model constructor entirely.
#   * C1 also makes it impossible to fix ONE production path and pass: because
#     the clause is unconditional, a rival that carries the marker at the
#     construction site but not at the reconstruction site (or vice versa) is
#     refuted on the path it missed. Both single-site rivals are shipped, at
#     disjoint witness points.
#   * C2's four cases are disjoint and exhaustive, so each is separately
#     attackable: drop the bookkeeping message, drop the reconstruction, copy the
#     wrong elements, mis-order them, ignore the unbound early stop, or invert the
#     precedence between the bookkeeping message and the reported ones.
#
# AUDIT NOTE — spec strength vs upstream-check observability. An independent audit
# re-derived every case and confirmed the spec REJECTS all of them (13 witnesses
# rebuilt: rival elaborates, frozen solution refuted by `decide` on the concrete
# claim). It also found that several of the port's `refinement` notes overclaimed
# by asserting the shipped upstream checks FAIL for their rival. They do not
# always: only the reconstruction site and the reported-message list are observed
# by those checks, because every non-form message list asserted anywhere upstream
# has exactly ONE element, an empty collection renders as the empty string
# (emitting no class at all), the paths that keep the initially-constructed
# collection leave it empty, the bookkeeping-path checks compare the collection as
# a plain message list (which ignores the class), and no check reaches the
# both-sources-populated path. The affected notes now say which rivals are
# upstream-observable (weak-no-marker-report, weak-skip-report-rebuild,
# weak-report-drop-last, weak-wrong-marker, weak-marker-replaces-base,
# weak-no-separator, weak-drop-mgmt-message, weak-constant-mgmt-message) and which
# are genuine deviations from the MODELED production that the shipped checks
# happen not to distinguish (weak-no-marker-construct, weak-report-reversed,
# weak-mgmt-precedence, weak-ignore-unbound, weak-empty-report-conflate). All are
# retained: the spec is deliberately stronger than the shipped checks on the
# clauses C1 pins unconditionally, and each of those rivals is the sole probe of
# its binder or boundary. No case was dropped as vacuous.
#
# Carrier narrowing vs the nagini sibling. Nagini contracted a procedure over a
# MUTABLE collection object plus a read-only message list, with heap permissions;
# this bundle models the same production as a total function returning a value.
# Consequences for the port:
#   * nagini's css_class clause ports to C1 and its three `Implies` items clauses
#     port to C2's cases, so every nagini VALUE-level rival has a counterpart
#     here: uniq-no-marker-init, uniq-no-marker-rejected, uniq-wrong-marker,
#     uniq-drop-group-append, uniq-skip-rejected-rebuild, uniq-rejected-copy-prefix
#     are all ported (renamed to this carrier's vocabulary), and both nagini
#     positive controls plus its admissibility control are ported.
#   * this carrier has a binder nagini's did NOT model: `isBound`, the unbound
#     early stop. C2's first case is therefore an attack surface with no nagini
#     counterpart, and a rival for it is ADDED so no binder is held fixed by every
#     witness.
#   * nagini's rejection-list copy was an explicit indexed loop with fold
#     invariants; here the reported messages arrive as a `List String` the impl
#     installs wholesale, so the off-by-one attack is re-expressed as dropping the
#     final element rather than as a loop-bound error, and an order attack (which
#     nagini's forward-append loop could not express) is added alongside it.
#
# Vacuous / dropped classes (stated per directive, not silently omitted):
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean, so nagini's
#     frame-mutate-append and frame-mutate-store are NOT ported. They are rejected
#     by nagini's fractional-permission system for writing to an input held
#     read-only. Lean is referentially transparent: `raised : Option (List String)`
#     is an immutable value, there is no aliasable input to overwrite, and no
#     rival can express the write those two cases make. The class does not exist
#     on this carrier — nothing was dropped for difficulty. DEMONSTRATED by the
#     audit rather than asserted: the nearest expressible analogue of
#     frame-mutate-append (rebind a local `let mut` copy of `raised`, appending to
#     it, before running the frozen body) was built and VERIFIES, exit 0. The
#     "write" is unobservable because the rebind cannot escape, so there is no
#     permission lane for it to fail and no rejection to attribute to the spec —
#     which is exactly what makes the pair vacuous here rather than merely hard.
#   * DIVERGENCE / NON-TERMINATION lane — VACUOUS on lean. The nagini sibling
#     carries no `diverge-*`/`nonterm-*`/`weak-diverge` case here, and in any
#     event `implementation_nonFormErrors` is a total Lean `def`: a diverging
#     implementation cannot be written, so the class does not exist. (Contrast
#     velvet under `partial` termination semantics, where the frozen spec ADMITS a
#     non-terminating rival — a known spec hole, not vacuity; see
#     the corpus-wide termination-semantics finding. That disposition does not apply to lean.)
#   * AXIOM lane — DROPPED. `meta.axioms == []` and `opaque_callees == []`; the
#     error-collection constructor is an A-reference modeled deeply as
#     `mkErrorList` and validated == the real callee by G-AX (recorded pass:
#     120008 inputs, seed 14608). Nagini's ax-sound-class_attr / ax-cover-class_attr
#     probes are G-AX's job and this gate ignores them. AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-14608"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly on drift.
# The impl region body and the proof TACTIC body (everything after the theorem
# statement's `:= by`) are the only regions a variant may edit. The spec view,
# every signature, and the byte-identical `theorem correct_nonFormErrors`
# statement are never touched, so same_spec holds by construction.

_IMPL_OLD = """\
def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : ErrorList := Id.run do
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonform")
  return nonForm"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro isBound mgmtValid mgmtError raised
  unfold problem_spec_nonFormErrors implementation_nonFormErrors expectedMessages
  cases isBound <;> cases mgmtValid <;> cases raised <;>
    exact ⟨rfl, rfl⟩"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"

# The impl header, shared by every variant below that keeps the imperative shape.
_HEAD = """\
def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : ErrorList := Id.run do
"""


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant. Replaces the impl body, and (for a
    positive whose reshaped impl needs a matching proof) the proof tactic body.
    The theorem STATEMENT and the whole spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


def _witness(args):
    """State the spec predicate directly at a concrete, `decide`-able input. The
    negation elaborates iff the rival's output contradicts the spec there.
    Checked in a file with the frozen obligations removed, so no tactic script
    can interfere. Every witness here is stated at LITERAL inputs and binds
    nothing, so there are no hypotheses that could be jointly unsatisfiable."""
    return f"""\
example : ¬ problem_spec_nonFormErrors {args}
    (implementation_nonFormErrors {args}) := by
  unfold problem_spec_nonFormErrors implementation_nonFormErrors expectedMessages
  decide"""


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY. Each is a structurally different
# but behaviourally identical correct impl. Each was built and confirmed to close
# the byte-identical `theorem correct_nonFormErrors` statement; no new lemma, no
# axiom, no sorry, no weakened obligation.
# ---------------------------------------------------------------------------

# pos-build-from-concat: the port of nagini's pos-control-build-from-concat.
# Nagini's control built the class as a concatenation of code-point lists instead
# of one spelled-out literal; here the equivalent move is to build the class
# string compositionally (base class, separator, marker) as a `let`-bound value
# and construct the collection record directly, so the deep-model constructor is
# never called at either site. If C1 were satisfiable only by a syntactic echo of
# the spec's own literal, or only via the modeled constructor, this would fail —
# so it is what makes "C1 is pinned to a VALUE" a measured claim.
_POS_CONCAT = _HEAD + """\
  let cls : String := "errorlist" ++ " " ++ "nonform"
  let mut nonForm : ErrorList := { messages := [], cssClass := cls }
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := { nonForm with messages := nonForm.messages ++ [mgmtError] }
  if let some errs := raised then
    nonForm := { messages := errs, cssClass := cls }
  return nonForm"""

# pos-reorder-report-first: the port of nagini's pos-control-reorder-rejected-first.
# Handle the cross-collection report FIRST and return early from each path, so
# the bookkeeping branch is only reached when no report is present — the same
# precedence the frozen impl reaches by overwriting, expressed as control flow
# instead. Every path returns a freshly constructed collection.
_POS_REORDER = _HEAD + """\
  if !isBound then
    return mkErrorList [] (some "nonform")
  if let some errs := raised then
    return mkErrorList errs (some "nonform")
  if !mgmtValid then
    return (mkErrorList [] (some "nonform")).append mgmtError
  return mkErrorList [] (some "nonform")"""

# pos-pure-functional: no nagini counterpart (nagini's carrier was an imperative
# procedure mutating a collection in place, so this shape could not be written
# there). The same production as a pure functional match — no `Id.run`, no
# `let mut`, no early `return`. Confirms the spec does not secretly depend on the
# imperative encoding.
#
# AUDIT CORRECTION (measured). The port's note here claimed this was "the one
# positive whose proof genuinely had to be reauthored", because the frozen
# `exact ⟨rfl, rfl⟩` supposedly no longer closes once the bookkeeping path goes
# through `.append`. That was built and MEASURED FALSE: this impl paired with the
# byte-identical FROZEN tactic body elaborates, exit 0. The `.append` on that path
# reduces to the spec's singleton definitionally, so `rfl` closes it. The
# reauthored `simp` body below is therefore a convenience, not a necessity, and the
# case is a weaker soundness probe than the port advertised — it does NOT
# demonstrate that a reshape can force a new proof. Kept as-is (it is still an
# honest structurally-different correct impl, and `simp` closing is not a defect),
# with the claim corrected rather than the impl changed; see the rationale.
_POS_PURE = """\
def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : ErrorList :=
  if !isBound then mkErrorList [] (some "nonform")
  else match raised with
       | some errs => mkErrorList errs (some "nonform")
       | none => if !mgmtValid then (mkErrorList [] (some "nonform")).append mgmtError
                 else mkErrorList [] (some "nonform")"""

_POS_PURE_PROOF = """\
  intro isBound mgmtValid mgmtError raised
  unfold problem_spec_nonFormErrors implementation_nonFormErrors expectedMessages
  cases isBound <;> cases mgmtValid <;> cases raised <;>
    simp [mkErrorList, ErrorList.append]"""

# admiss-path-shapes: the port of nagini's admiss-f2p-shaped-input. Nagini could
# not add a module-level caller without breaking same_spec, so it injected the
# admissibility witness INSIDE the impl region as leading `Assert`s; the lean
# analogue is the same claims as in-body `have`s, discharged against the spec
# predicate itself at three concrete inputs — one per reachable production path
# (a bound clean form-set, invalid bookkeeping, and a cross-collection report).
# The impl body and the frozen proof script are otherwise verbatim, so the only
# thing this can fail on is the spec being unsatisfiable at a legitimate input
# (PRECOND-TOO-STRONG / spec-shape regression). `correct_nonFormErrors` has no
# precondition hypothesis to over-strengthen, which is why this lane is a
# shape check rather than a domain check on this carrier.
_ADMISS = _HEAD + """\
  have _hRaised : problem_spec_nonFormErrors true true "mgmt"
      (some ["cross-collection message"])
      (mkErrorList ["cross-collection message"] (some "nonform")) := by
    constructor <;> rfl
  have _hMgmt : problem_spec_nonFormErrors true false "mgmt" none
      ((mkErrorList [] (some "nonform")).append "mgmt") := by
    constructor <;> rfl
  have _hClean : problem_spec_nonFormErrors true true "mgmt" none
      (mkErrorList [] (some "nonform")) := by
    constructor <;> rfl
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonform")
  return nonForm"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region and ships a witness that was BUILT and SEEN to discriminate:
# it elaborates against the rival and fails against the frozen solution.
# ---------------------------------------------------------------------------

# --- C1 (the rendered class) --------------------------------------------------

# weak-no-marker-construct: the pre-change behaviour at the CONSTRUCTION site —
# the collection is built with no extra class, so it renders under the base class
# alone. Ports nagini's uniq-no-marker-init.
_WEAK_NO_MARKER_CONSTRUCT = _HEAD + """\
  let mut nonForm := mkErrorList [] none
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonform")
  return nonForm"""

# weak-no-marker-report: the pre-change behaviour at the RECONSTRUCTION site —
# the marker is carried on the paths that keep the initial collection but lost
# when a cross-collection report replaces it. Ports nagini's
# uniq-no-marker-rejected; disjoint production path from the rival above, so the
# pair shows C1 must hold at BOTH sites, not just one.
_WEAK_NO_MARKER_REPORT = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs none
  return nonForm"""

# weak-wrong-marker: the marker for a form's non-field errors, used by analogy in
# place of the form-set's non-form marker. Correct in SHAPE (base class, space,
# marker) and wrong only in the marker token. Ports nagini's uniq-wrong-marker.
_WEAK_WRONG_MARKER = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonfield")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonfield")
  return nonForm"""

# weak-marker-replaces-base: no nagini counterpart. Every C1 rival above either
# omits the marker or misspells it; this one keeps the marker and drops the BASE
# class, so the collection renders under the marker alone. Without it, the "the
# base class survives" half of C1 is pinned at no value any rival changes.
_WEAK_MARKER_ONLY = _HEAD + """\
  let mut nonForm : ErrorList := { messages := [], cssClass := "nonform" }
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := { messages := errs, cssClass := "nonform" }
  return nonForm"""

# weak-no-separator: no nagini counterpart, and the NEAREST possible miss on C1 —
# both tokens present, in the right order, with the separator between them
# dropped. If C1 pinned the class only loosely (to containing both tokens, say,
# rather than to the exact string) every rival above would still be caught and
# this one would slip through. This is what makes "the exact class string is
# pinned" a measured claim rather than an assumed one.
_WEAK_NO_SEPARATOR = _HEAD + """\
  let mut nonForm : ErrorList := { messages := [], cssClass := "errorlistnonform" }
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := { nonForm with messages := nonForm.messages ++ [mgmtError] }
  if let some errs := raised then
    nonForm := { messages := errs, cssClass := "errorlistnonform" }
  return nonForm"""

# --- C2 (the carried messages) -----------------------------------------------

# weak-drop-mgmt-message: omit the bookkeeping-error message entirely. Correct on
# the unbound, clean and report-present sub-domains; wrong only when the
# bookkeeping is invalid and no report is present. Ports nagini's
# uniq-drop-group-append.
_WEAK_DROP_MGMT = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonform")
  return nonForm"""

# weak-skip-report-rebuild: drop the cross-collection reconstruction. Correct
# whenever no report is present; on the report path the collection keeps whatever
# the earlier paths left. Ports nagini's uniq-skip-rejected-rebuild.
_WEAK_SKIP_REPORT = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  return nonForm"""

# weak-report-drop-last: install all but the FINAL reported message. Ports
# nagini's uniq-rejected-copy-prefix (whose loop bound stopped one short); on
# this carrier the reported messages arrive as a value, so the off-by-one is
# re-expressed as dropping the last element.
_WEAK_DROP_LAST = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs.dropLast (some "nonform")
  return nonForm"""

# weak-report-reversed: no nagini counterpart — its forward-append loop could not
# express an order error. Every reported message is present and the count is
# right; only the ORDER is wrong. The rendered list is order-sensitive, so this
# separates "the right messages" from "the right sequence".
_WEAK_REVERSED = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs.reverse (some "nonform")
  return nonForm"""

# weak-ignore-unbound: no nagini counterpart — nagini's carrier had no such
# binder. Omit the early stop for unbound data, so an unbound form-set is
# processed as if it had been submitted. Wrong on exactly the isBound = false
# sub-domain. Without this rival `isBound` would be held at the same value by
# every other witness, and a rival mishandling only that input would verify.
_WEAK_IGNORE_UNBOUND = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonform")
  return nonForm"""

# weak-constant-mgmt-message: no nagini counterpart. Carry a fixed message on the
# bookkeeping path instead of the one supplied. The message COUNT and every other
# path are right, so this isolates the `mgmtError` binder — the only rival that
# reads it wrongly rather than dropping it (weak-drop-mgmt-message drops it, which
# a spec pinning only the length would also catch).
_WEAK_CONSTANT_MSG = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append "bookkeeping error"
  if let some errs := raised then
    nonForm := mkErrorList errs (some "nonform")
  return nonForm"""

# weak-mgmt-precedence: no nagini counterpart at this precision (nagini's rival
# for this clause dropped the append outright). A near-miss that gets both C1 and
# every other C2 case exactly right and inverts ONLY the precedence between the
# two message sources: when the bookkeeping is invalid AND a report is present it
# keeps both, where the spec says the report replaces what came before. Wrong on
# exactly the one input where that precedence is load-bearing.
_WEAK_MGMT_PRECEDENCE = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList (nonForm.messages ++ errs) (some "nonform")
  return nonForm"""

# weak-empty-report-conflate: no nagini counterpart. Treat an EMPTY report as
# "nothing reported" and fall through to whatever the earlier paths left. Correct
# for every non-empty report, wrong only when a report is present but carries no
# messages — the boundary between "no report" and "an empty report", which every
# other rival holds at a non-empty value.
_WEAK_EMPTY_REPORT = _HEAD + """\
  let mut nonForm := mkErrorList [] (some "nonform")
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    if errs != [] then
      nonForm := mkErrorList errs (some "nonform")
  return nonForm"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-build-from-concat",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_CONCAT),
        "rationale": (
            "ports nagini's pos-control-build-from-concat. Structurally-different "
            "CORRECT impl: build the class string compositionally (base class, "
            "separator, marker) as a let-bound value and construct the collection "
            "record directly, so the deeply-modeled constructor is never called at "
            "either site. C1 holds because the concatenation's VALUE is the spec's "
            "literal, not because the impl echoes that literal or reuses the "
            "spec's own constructor; C2 is unchanged. Verifying is what makes the "
            "'C1 is grounded, not an echoable oracle' claim measured. If it fails "
            "=> SPEC-TOO-STRONG (C1 would demand a syntactic echo)."
        ),
    },
    {
        "id": "pos-reorder-report-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "ports nagini's pos-control-reorder-rejected-first. Handle the "
            "cross-collection report FIRST with an early return from every path, "
            "so the bookkeeping branch is reached only when no report is present — "
            "the same precedence the frozen impl gets by overwriting, expressed as "
            "control flow instead. Behaviourally identical on all four C2 cases and "
            "on C1. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE, _POS_PURE_PROOF),
        "rationale": (
            "no nagini counterpart (its carrier was an imperative procedure "
            "mutating a collection in place). The same production written as a "
            "pure functional match — no Id.run, no let mut, no early return — "
            "confirming the spec does not secretly depend on the imperative "
            "encoding. The theorem STATEMENT is byte-identical and no "
            "lemma/axiom/sorry was added. AUDIT CORRECTION: the port claimed this "
            "was the one positive whose proof HAD to be reauthored (that the "
            "frozen `exact ⟨rfl, rfl⟩` no longer closes once the bookkeeping path "
            "goes through append). Built and measured false — this impl with the "
            "byte-identical FROZEN tactic body elaborates (exit 0), because that "
            "append reduces to the spec's singleton definitionally. The `simp "
            "[mkErrorList, ErrorList.append]` body shipped below is a convenience, "
            "not a necessity, so this case does NOT demonstrate that a correct "
            "reshape can force a new proof; it demonstrates only that a "
            "non-imperative encoding is admitted. If it fails => SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-path-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "ports nagini's admiss-f2p-shaped-input. Nagini could not add a "
            "module-level caller without breaking same_spec, so it injected the "
            "witness inside the impl region as leading Asserts; the lean analogue "
            "is the same claims as in-body `have`s, discharged against the spec "
            "predicate at three concrete inputs — one per reachable production "
            "path (bound and clean, invalid bookkeeping, cross-collection report). "
            "The impl body and the frozen proof script are otherwise verbatim, so "
            "the only thing this can fail on is the spec being unsatisfiable at a "
            "legitimate input. Note the obligation carries NO precondition "
            "hypothesis on this carrier (all four binders range over their whole "
            "types), so there is no domain to over-restrict and this lane is a "
            "spec-shape check. If it fails => PRECOND-TOO-STRONG / shape "
            "regression."
        ),
    },

    # ---- C1: the rendered class (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "weak-no-marker-construct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_MARKER_CONSTRUCT),
        "witness": _witness('true true "mgmt" none'),
        "refinement": (
            "the pre-change behaviour at the construction site: the collection is "
            "built with no extra class, so it renders under the base class alone on "
            "every path that keeps it. AUDIT CORRECTION — the port claimed this "
            "rival's faithful patch IS the unpatched code and that the F2P string "
            "equalities fail for it. Both are false and the second was checked "
            "against the suite: (a) the unpatched code omits the marker at BOTH "
            "sites, which is the CONJUNCTION of this rival and "
            "weak-no-marker-report, not this rival alone; (b) all four F2P checks "
            "drive the form-set to report a cross-collection error, so each of them "
            "observes the RECONSTRUCTION site, which this rival marks correctly — "
            "they would pass. The class this rival gets wrong is not distinguished "
            "by any shipped check either: the paths that keep the initial "
            "collection leave it EMPTY (an empty collection renders as the empty "
            "string, carrying no class at all), and on the bookkeeping path the "
            "checks compare the collection as a plain message list, which ignores "
            "the class. So this rival is a genuine deviation from the modeled "
            "production (it differs from gold's collection VALUE, which C1 pins "
            "unconditionally) but NOT a resolution-breaking one. Retained on that "
            "ground: the spec is deliberately stronger here than the shipped "
            "checks, which is what makes C1 hold on all three paths."
        ),
        "rationale": (
            "rejected by C1 (result.cssClass must be the exact string with base "
            "class and marker; the rival yields the base class alone) on every "
            "path that keeps the initially-constructed collection. Witness at the "
            "bound/clean/no-report point (true, true, none), where C2 is satisfied "
            "so the refutation is attributable to C1 alone. If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-no-marker-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_MARKER_REPORT),
        "witness": _witness('true true "mgmt" (some ["a"])'),
        "refinement": (
            "the pre-change behaviour at the OTHER site: the marker is carried "
            "until a cross-collection report replaces the collection, and then "
            "lost. This is the half-finished patch that fixes one construction site "
            "and misses the other, and it IS the resolution-breaking half: all four "
            "F2P checks drive the form-set to report a cross-collection error and "
            "then observe the resulting collection's rendered class (three assert "
            "the exact markup string; the admin one compares against a collection "
            "constructed with the marker), so with the marker lost at this site "
            "every one of them fails. Does NOT resolve. (Verified against the "
            "suite: the port's original note said 'all three form-set F2P checks' — "
            "there are four F2P checks in total, three over the form-set and one "
            "over the admin change-list, and all four exercise this site.)"
        ),
        "rationale": (
            "rejected by C1 on the report path only. Because C1 is unconditional "
            "it constrains BOTH construction sites, which is what this rival and "
            "weak-no-marker-construct jointly demonstrate: each satisfies C1 on "
            "the other's path, so neither could be caught by a spec that pinned "
            "the class on one path. Witness at (true, true, some [\"a\"]) — a "
            "disjoint production path from that rival's witness. If it verifies => "
            "SPEC-TOO-WEAK on the report path."
        ),
    },
    {
        "id": "weak-wrong-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WRONG_MARKER),
        "witness": _witness('false true "mgmt" none'),
        "refinement": (
            "the marker a form uses for its non-field errors, applied by analogy "
            "where the form-set's own marker is required. The class SHAPE is right "
            "and only the token is wrong, which is exactly the plausible near-miss "
            "a developer writes from the neighbouring documented behaviour. The "
            "F2P checks assert the exact rendered class string and compare against "
            "a collection constructed with the form-set marker, so a different "
            "token fails them. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1: the marker token is pinned by the spec's literal, so "
            "a well-formed class carrying the wrong token is provably unequal. "
            "Witness at the UNBOUND point (false, true, none) — the cheapest path, "
            "and one no other C1 witness uses, so this case also varies the "
            "isBound binder while attacking C1. If it verifies => SPEC-TOO-WEAK on "
            "the marker token."
        ),
    },
    {
        "id": "weak-marker-replaces-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MARKER_ONLY),
        "witness": _witness('true false "m" none'),
        "refinement": (
            "carrying the marker but REPLACING the base class rather than adding "
            "to it. A real patch that overwrote the class instead of extending it "
            "would strip the base class every consumer of these lists already "
            "styles against; the F2P checks assert the rendered markup carries "
            "both, so it fails them, and it would regress the rendering of every "
            "other error list built the same way. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1's base-class half. Every other C1 rival omits or "
            "misspells the marker while keeping the base class, so without this "
            "case the requirement that the base class SURVIVES is pinned at no "
            "value any rival changes. Witness at the invalid-bookkeeping point "
            "(true, false, none), which also puts a C1 refutation on the third "
            "production path. If it verifies => SPEC-TOO-WEAK on the base class."
        ),
    },
    {
        "id": "weak-no-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_SEPARATOR),
        "witness": _witness('true false "m" (some ["a"])'),
        "refinement": (
            "both tokens present in the right order with the separator between "
            "them dropped, so the rendered attribute names a single unknown class "
            "rather than two. A real patch producing this would render markup that "
            "matches neither the base class nor the marker for any stylesheet or "
            "any consumer selecting on either, and it fails the F2P string "
            "equalities on the exact rendered attribute. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 at the NEAREST possible miss: same tokens, same order, "
            "one character absent. If C1 pinned the class loosely — to containing "
            "both tokens, or to a prefix — every other C1 rival would still be "
            "caught while this one slipped through, so this case is what makes "
            "'the exact class string is pinned' measured rather than assumed. "
            "Witness at (true, false, some [\"a\"]), the both-sources-populated "
            "point, which no other C1 witness probes. If it verifies => "
            "SPEC-TOO-WEAK on the exact class string."
        ),
    },

    # ---- C2: the carried messages (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "weak-drop-mgmt-message",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_MGMT),
        "witness": _witness('true false "mgmt problem" none'),
        "refinement": (
            "ports nagini's uniq-drop-group-append. Omitting the "
            "bookkeeping-error message models an impl that does not carry the "
            "message the unchanged bookkeeping path produces. That message is "
            "observable: two P2P checks (test_customize_management_form_error, "
            "test_management_form_invalid_data) drive a form-set with invalid "
            "bookkeeping data and assert the collection carries it. A patch "
            "dropping it changes a reachable path the change does not touch, so it "
            "is not faithful and regresses those checks."
        ),
        "rationale": (
            "rejected by C2's invalid-bookkeeping case (messages must be the single "
            "supplied message; the rival yields the empty list). PARTIAL-DOMAIN: "
            "correct on the unbound, clean and report-present sub-domains. Witness "
            "at (true, false, none). If it verifies => SPEC-TOO-WEAK on that "
            "sub-domain."
        ),
    },
    {
        "id": "weak-skip-report-rebuild",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SKIP_REPORT),
        "witness": _witness('true true "mgmt" (some ["x", "y", "z"])'),
        "refinement": (
            "ports nagini's uniq-skip-rejected-rebuild. Dropping the "
            "cross-collection reconstruction corresponds to a patch that never "
            "populates the collection from the reported errors. All FOUR F2P checks "
            "(three over the form-set, one over the admin change-list) drive a "
            "cross-collection report and assert the collection holds exactly the "
            "reported messages, three of them also asserting its rendered markup "
            "lists them; with no reconstruction the collection stays empty and those "
            "assertions fail. Does NOT resolve. Verified against the suite."
        ),
        "rationale": (
            "rejected by C2's report-present case (messages must be exactly the "
            "reported list). PARTIAL-DOMAIN attack on the report path. Witness at "
            "(true, true, some [\"x\",\"y\",\"z\"]) — a three-element report, so "
            "the failure is a whole missing list rather than an edge case. If it "
            "verifies => SPEC-TOO-WEAK on the report path."
        ),
    },
    {
        "id": "weak-report-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_LAST),
        "witness": _witness('true true "mgmt" (some ["a", "b"])'),
        "refinement": (
            "ports nagini's uniq-rejected-copy-prefix (whose loop bound stopped "
            "one element short; on this carrier the reported messages arrive as a "
            "value, so the off-by-one is dropping the final element). A real patch "
            "with this off-by-one loses the last reported message, so the collection "
            "compares unequal to the expected list of reported messages and its "
            "rendered markup is missing an entry. Does NOT resolve — and unlike the "
            "order and construct-site rivals this one IS test-observable: every "
            "non-form list asserted in the suite has exactly one element, and "
            "dropping the last element of a one-element report yields the EMPTY "
            "list, which fails both the list equality and the rendered-markup "
            "equality the F2P checks assert (an empty collection renders as the "
            "empty string, so no class attribute is emitted at all). Verified "
            "against the suite."
        ),
        "rationale": (
            "rejected by C2's report-present case: the messages equal the reported "
            "list minus its final element. Strictly tighter than "
            "weak-skip-report-rebuild, which loses the whole list and so would be "
            "caught by a spec pinning only 'non-empty when a report is present'. "
            "Witness at (true, true, some [\"a\",\"b\"]) — the shortest report "
            "where dropping the last element is not the same as dropping "
            "everything. If it verifies => SPEC-TOO-WEAK on the exact reported "
            "list."
        ),
    },
    {
        "id": "weak-report-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_REVERSED),
        "witness": _witness('true true "mgmt" (some ["first", "second", "third"])'),
        "refinement": (
            "no nagini counterpart: its forward-append loop with take-prefix "
            "invariants could not express an order error. Every reported message is "
            "present and the count is right; only the order is wrong. The rendered "
            "markup lists the messages in carried order, so a permutation changes "
            "what a reader sees while a multiset-level spec would not notice. AUDIT "
            "CORRECTION: the port claimed the F2P checks fail for this rival. "
            "Checked against the suite and that is FALSE — every non-form message "
            "list asserted anywhere in the suite has exactly ONE element, and a "
            "one-element list is its own reverse, so no shipped check distinguishes "
            "this rival. It is nonetheless genuinely wrong behaviour in the modeled "
            "production (the collection is built from the reported messages "
            "in order, and a caller reporting two or more messages would see them "
            "inverted), so it is a real deviation that happens to be untested "
            "upstream rather than a resolution-breaking one. Retained: it is the "
            "only rival separating 'the right messages' from 'the right sequence'."
        ),
        "rationale": (
            "rejected by C2's report-present case on ORDER alone — the rival's "
            "messages are a permutation of the required list, with the same length "
            "and the same elements. Separates 'the right messages' from 'the right "
            "sequence', which no other rival tests. Witness at (true, true, some "
            "[\"first\",\"second\",\"third\"]) — three distinct messages, so the "
            "reversal is not fixable by symmetry and is a distinct input point from "
            "the two-element off-by-one witness. If it verifies => SPEC-TOO-WEAK on "
            "message order."
        ),
    },
    {
        "id": "weak-ignore-unbound",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_UNBOUND),
        "witness": _witness('false false "mgmt" none'),
        "refinement": (
            "no nagini counterpart — nagini's carrier did not model this binder. "
            "Omitting the early stop for unbound data processes a form-set that "
            "was never submitted as though it had been, so the collection acquires "
            "messages about data that does not exist. A real patch dropping that "
            "guard would surface errors on a form-set that was never submitted, "
            "changing a reachable path the modeled change does not touch. AUDIT "
            "CORRECTION: the port cited a named P2P check as depending on the "
            "unbound collection staying empty. Checked against the suite and that "
            "citation is FALSE — the named check exercises the empty-form/unbound "
            "distinction and never reads the non-form collection at all, and no "
            "check in the suite asserts the unbound collection's contents (the "
            "public entry point returns False for unbound input before the "
            "collection is consulted). So this rival's wrongness is NOT "
            "test-observable; it is unfaithful to the MODELED production (the early "
            "stop is an unchanged operation the spec pins) rather than "
            "resolution-breaking. Retained on that ground: without it the isBound "
            "binder is varied by no other rival."
        ),
        "rationale": (
            "rejected by C2's unbound case (messages must be empty; the rival "
            "yields the bookkeeping message). Witness at (false, FALSE, none): the "
            "ONLY witness in this battery that sets isBound = false while another "
            "binder makes the difference observable, so without this case the "
            "unbound early stop would be exercised by no rival and an impl "
            "mishandling only unbound input would verify unnoticed. If it verifies "
            "=> SPEC-TOO-WEAK on the unbound path."
        ),
    },
    {
        "id": "weak-constant-mgmt-message",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CONSTANT_MSG),
        "witness": _witness('true false "a different message" none'),
        "refinement": (
            "no nagini counterpart at this precision. Carrying a hardcoded message "
            "on the bookkeeping path instead of the one produced there. A real "
            "patch doing this discards a caller-customized message: the P2P check "
            "test_customize_management_form_error installs its own message and "
            "asserts the collection carries exactly that text, which a fixed "
            "string fails while the message COUNT and every other path stay right. "
            "Does NOT resolve."
        ),
        "rationale": (
            "rejected by C2's invalid-bookkeeping case on the message VALUE. "
            "Isolates the mgmtError binder: weak-drop-mgmt-message drops the "
            "message, which a spec pinning only the list LENGTH would also catch, "
            "whereas this rival gets the length right and the content wrong, so it "
            "is the case that shows the supplied message is threaded through and "
            "not merely counted. Witness at (true, false, none) with a supplied "
            "message that differs from the hardcoded one. If it verifies => "
            "SPEC-TOO-WEAK on the message value."
        ),
    },
    {
        "id": "weak-mgmt-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MGMT_PRECEDENCE),
        "witness": _witness('true false "mgmt" (some ["reported"])'),
        "refinement": (
            "no nagini counterpart at this precision (nagini's rival for this "
            "clause dropped the bookkeeping append outright). Keeping the "
            "bookkeeping message ALONGSIDE the reported ones instead of letting the "
            "report replace what came before. A real patch that accumulated rather "
            "than replaced would, for a form-set whose bookkeeping is invalid and "
            "which also reports a cross-collection error, carry an extra entry and "
            "render it. AUDIT CORRECTION: the port claimed the F2P markup assertion "
            "fails for this rival. Checked against the suite and that is FALSE — no "
            "shipped check reaches the both-sources-populated path (the checks that "
            "supply invalid bookkeeping data never also drive a cross-collection "
            "report, and vice versa), so this rival is not distinguished by any of "
            "them. It is nonetheless a genuine deviation from the modeled "
            "production, which pins the reported messages as REPLACING what came "
            "before, matching the reassignment the unchanged code performs. "
            "Retained: it is the only rival isolating source precedence, and the "
            "spec pinning that path is deliberate strength beyond the shipped "
            "checks."
        ),
        "rationale": (
            "rejected by C2's report-present case, and ONLY there: this rival gets "
            "C1 and all three other C2 cases exactly right and inverts only the "
            "PRECEDENCE between the two message sources. Wrong on exactly the one "
            "input where that precedence is load-bearing — both sources populated "
            "— which a rival breaking several cases at once cannot isolate. Witness "
            "at (true, false, some [\"reported\"]). If it verifies => "
            "SPEC-TOO-WEAK on source precedence."
        ),
    },
    {
        "id": "weak-empty-report-conflate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY_REPORT),
        "witness": _witness('true false "mgmt" (some [])'),
        "refinement": (
            "no nagini counterpart. Treating an EMPTY report as 'nothing reported' "
            "and falling through to whatever the earlier paths left. A real patch "
            "testing the reported messages for truthiness rather than testing "
            "whether a report occurred would, when a cross-collection error is "
            "reported carrying no messages, leave the bookkeeping message in place "
            "where the report should have replaced it — reporting an error about "
            "the wrong thing while behaving correctly for every non-empty report. "
            "Does NOT faithfully implement the modeled production. No shipped "
            "upstream check reaches this boundary (each reports at least one "
            "message), so this rival's wrongness is a deviation from the modeled "
            "production rather than an upstream-check failure; it is retained "
            "because it is the only probe of the two Option constructors at their "
            "empty-list boundary, which C2's match on presence makes load-bearing."
        ),
        "rationale": (
            "rejected by C2's report-present case at the BOUNDARY between 'no "
            "report' and 'an empty report': the spec's match is on whether a report "
            "is present, so `some []` must yield the empty list, but the rival "
            "yields the bookkeeping message. Every other rival holds the report at "
            "a non-empty value, so without this case the distinction between the "
            "two `Option` constructors at their empty-list boundary is untested. "
            "Witness at (true, false, some []) — a distinct input point from every "
            "other witness. If it verifies => SPEC-TOO-WEAK on that boundary."
        ),
    },
]

# No consumed axioms and no opaque callee on this path (meta.axioms == [],
# opaque_callees == []); the collection constructor is an A-reference modeled
# deeply in the `pure` region and validated by G-AX. Nothing for the axiom lane
# to execute here.
AXIOM_TESTS = []
