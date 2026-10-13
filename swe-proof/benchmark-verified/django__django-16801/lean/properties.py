# properties.py — G-PBT falsification battery for django__django-16801 (lean lane).
# NOT a Lean module; a manifest the gate parses. Every case is a full
# Solution.lean built by region surgery that edits ONLY the impl region (and,
# for a reshaped positive, the proof tactic body), so the frozen spec view is
# byte-identical (same_spec holds by construction) and the `theorem
# correct_connectPostInit` STATEMENT is preserved verbatim. Ported from the
# nagini sibling's properties.py, re-expressed against this backend's carrier.
#
# DEFENDED SURFACE (read off Solution.lean):
#   connectPostInit (isAbstract : Bool) (widthField heightField : Option String)
#     : Bool
#   The single output is whether the post-initialization dimension-sync handler
#   is installed for this (model, field) pair. ONE obligation, ONE top-level
#   postcondition clause, and it is an EQUALITY that pins the output on the whole
#   input domain (no arm is left unconstrained):
#     (C1) result = (!isAbstract && (truthy widthField || truthy heightField))
#   with the name test grounded, not oracular:
#     truthy none = false;  truthy (some s) = !s.isEmpty
#   So C1 decomposes into three sub-decisions any rival can get wrong
#   independently, and the battery attacks each:
#     (a) the concrete/abstract conjunct  — `!isAbstract`
#     (b) the DISJUNCTION over the two tracked attribute names — not a
#         conjunction, not an exclusive-or, and not either name alone
#     (c) the per-name non-empty test — absent and empty both configure nothing;
#         any non-empty name, however short, configures something
#
# Carrier narrowing vs the nagini sibling (case-count parity is NOT the target).
# The nagini model contracted a MUTATING procedure
# `attach_post_init_hook(receivers, owner_id, is_abstract, width_target,
# height_target)` over a heap-allocated notification list plus an identity
# token, and its load-bearing postcondition was a REGISTRATION BICONDITIONAL
# relating a decision predicate to the growth of that list. This bundle models
# the purely functional core the F2P test actually observes: the DECISION itself,
# as a Bool. Consequences for the port:
#   * Both halves of nagini's biconditional collapse into the single equality C1
#     (`result = <decision>` already says "installed iff the decision holds"),
#     so nagini's two-clause split has one clause here and every rival attacks it.
#   * nagini's `receivers` list and `owner_id` token are NOT modeled here — the
#     observable is whether the connection happens, not the container it is
#     recorded in. So nagini's `wrong-token` rival (append a different identity
#     token) has NO counterpart on this carrier: there is no token binder to
#     corrupt. Dropped, and recorded as such rather than fabricated over an
#     input this bundle does not have.
#   * The two attribute-name binders are `Option String` here rather than
#     nagini's `Optional[List[int]]` stand-in, so the empty-name boundary is
#     directly expressible and is attacked by two rivals nagini had no room for.
#
# Vacuous / dropped classes (stated, never silently omitted):
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean. nagini's
#     `frame-mutation-width` rival wrote to a read-only companion input held at a
#     fractional permission, and was rejected by the permission system plus an
#     unchanged-input pin. Lean is referentially transparent: the inputs are
#     immutable values, there is no aliasing and no fraction to exceed, so there
#     is no such rival to write. Nothing to port; no substitute fabricated.
#   * DIVERGENCE / NON-TERMINATION lane — NOT SHIPPABLE on this carrier, for a
#     reason MEASURED rather than asserted (audit 2026-08-13 corrected the
#     earlier wording here, which claimed a diverging impl "cannot be written at
#     all" — that is true only of a plain `def`). Two routes exist and both are
#     closed:
#       (1) A plain `def` whose recursion carries no decreasing measure is
#           rejected by Lean's own termination checker before the spec is ever
#           consulted: `implementation_connectPostInit ... := implementation_
#           connectPostInit ...` gives `fail to show termination for
#           implementation_connectPostInit / failed to infer structural
#           recursion`, and a helper `def spin (n : Nat) : Bool := spin (n + 1)`
#           gives the same. So on the total-`def` route divergence really is
#           inexpressible, and the frozen obligation is discharged over a total
#           function — this bundle is the `"total"` disposition, not `"partial"`.
#       (2) A `partial def` IS writable and passes `variant_problems` clean, and
#           the gate does record it as rejected — but the rejection is a
#           REDUCIBILITY artifact, not a semantic refutation: `partial def` is
#           compiled through an opaque `Inhabited`-backed constant, so the frozen
#           script fails with `Tactic 'unfold' failed to unfold
#           'implementation_connectPostInit'`, which says nothing about the
#           decision. Measured: no witness discriminates it. A literal
#           `decide` witness fails on BOTH sides (rival and gold alike, exit 1 /
#           1, the kernel cannot reduce the opaque constant — `witness-
#           undecided`), and a hypothesis-conditioned witness
#           `(h : implementation_connectPostInit false none none = true)`
#           ELABORATES on BOTH sides (exit 0 / 0) because on gold the hypothesis
#           is simply false and the goal follows from it — i.e. it fails the
#           must-fail-on-gold half, which is exactly the forgery the witness
#           requirement exists to reject.
#     So the class is recorded as a known hole in the WITNESS machinery for
#     `partial def`, not as a spec hole and not as a vacuous class. Distinct from
#     the velvet situation, where `loom.semantics.termination "partial"` lets a
#     non-terminating impl satisfy every clause vacuously and VERIFY while its
#     faithful patch hangs the F2P test — a genuine SPEC HOLE
#     (the corpus-wide termination-semantics finding). Here the diverging impl does NOT verify.
#   * AXIOM lane — DROPPED. `meta.axioms == []` and there is no `opaque` callee:
#     the decision reads three already-available facts and combines them with
#     boolean connectives plus a grounded non-empty-name test. The axiom lane is
#     G-AX's job (recorded skip there) and this gate ignores AXIOM_TESTS, so the
#     nagini file's two axiom probes are not carried over.
#
# WITNESSES. Every reject case ships a `witness`: the spec predicate stated
# directly at ONE concrete input, negated. It is checked in a file with the
# frozen obligation removed, so no tactic script can interfere, and it must
# ELABORATE against the rival and FAIL against the frozen solution. That
# two-sided check is what stops a reject case from passing merely because
# reshaping the impl broke the frozen tactic script. The whole carrier is
# closed and finite-per-point (`Bool`, `Option String`, `String.isEmpty`), so
# every witness here decides at a literal input — no `opaque` term forces the
# conditioning route, and therefore no witness binds a hypothesis and none can
# be `witness-inconsistent`.
#
# The ten witness points are pairwise DISTINCT and jointly move all three
# binders: `isAbstract` takes both values; `widthField` takes `none`,
# `some ""`, and non-empty names of length 1 and >1; `heightField` likewise.
# No binder is pinned at one value across the reject lane.

from pathlib import Path

INSTANCE = "django__django-16801"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- The two editable regions, extracted verbatim so the manifest breaks loudly
# if the frozen solution ever changes. `_IMPL_OLD` is the whole impl-region body;
# `_PROOF_OLD` is the frozen tactic body (everything after the theorem
# STATEMENT's `:= by`). The spec view, the signatures and the theorem statement
# are never touched by any case.

_IMPL_OLD = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  if !isAbstract && (truthy widthField || truthy heightField) then
    return true
  return false"""

_PROOF_OLD = """\
  intro isAbstract widthField heightField
  unfold problem_spec_connectPostInit implementation_connectPostInit
  simp only [Id.run]
  by_cases h : !isAbstract && (truthy widthField || truthy heightField)
  · simp only [h, if_true]; rfl
  · simp only [h, if_false, Bool.false_eq_true]; rfl"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"
assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """A full Solution.lean variant: new impl body, optionally a new tactic body
    (needed by positives whose reshaped impl the frozen script no longer
    matches). No new lemma / axiom / sorry, and the obligation's statement is
    untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


def _guard(expr):
    """The frozen impl SHAPE with a different decision expression: the rivals
    below differ from the frozen impl only in the guard, so a rejection is
    attributable to the decision and not to the surrounding do-block."""
    return f"""\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  if {expr} then
    return true
  return false"""


# The proof shape that closes for every reshaped POSITIVE below: split the three
# binders exhaustively and reduce. Same obligation, same statement, honest proof.
_PROOF_SPLIT = """\
  intro isAbstract widthField heightField
  unfold problem_spec_connectPostInit implementation_connectPostInit
  simp only [Id.run]
  cases isAbstract <;>
    cases hw : truthy widthField <;>
      cases hh : truthy heightField <;> simp_all <;> rfl"""


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG. Each is a
# structurally different but behaviourally identical correct implementation,
# shipped WITH a proof that actually closes for the new shape.
# ---------------------------------------------------------------------------

# pos-pure-functional: drop the do-block entirely and return the decision as an
# expression, dispatching on the concrete/abstract flag first. This is the shape
# the real two-line guard has. Ports nagini's pos-control-helper (bind the
# decision, then act on it) to a carrier where the decision IS the output.
_POS_PURE = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool :=
  if isAbstract then false
  else (truthy widthField || truthy heightField)"""

_POS_PURE_PROOF = """\
  intro isAbstract widthField heightField
  unfold problem_spec_connectPostInit implementation_connectPostInit
  cases isAbstract <;> simp"""

# pos-demorgan: the De Morgan / early-skip reorder — bail out on
# "abstract, or no attribute tracked" and install otherwise. Ports nagini's
# pos-control-demorgan verbatim in argument.
_POS_DEMORGAN = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  if isAbstract || !(truthy widthField || truthy heightField) then
    return false
  return true"""

# pos-decision-local: accumulate the answer in a mutable local — decide on the
# tracked-attribute disjunction first, then let the concrete/abstract flag veto
# it. Same decision reached in the opposite order, with the two sub-decisions
# recombined by a different operator arrangement.
_POS_LOCAL = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  let mut decision := false
  if truthy widthField || truthy heightField then
    decision := !isAbstract
  return decision"""

# pos-name-test-inlined: the GROUNDED-PREDICATE control. The frozen impl reaches
# its decision by naming `truthy`, the very helper the spec's own clause names,
# so the shape that actually discriminates on this carrier is the one that never
# mentions it: split on the two names' presence and test emptiness inline. If C1
# were satisfiable only by a syntactic echo of the spec's own helper rather than
# by its VALUE, this would fail — so it is what makes "the name test is grounded,
# not an oracle echo" a measured claim instead of an assertion.
_POS_INLINE_NAME_TEST = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  match widthField, heightField with
  | none,   none   => return false
  | some w, none   => return (!isAbstract && !w.isEmpty)
  | none,   some h => return (!isAbstract && !h.isEmpty)
  | some w, some h => return (!isAbstract && (!w.isEmpty || !h.isEmpty))"""

_POS_INLINE_NAME_TEST_PROOF = """\
  intro isAbstract widthField heightField
  unfold problem_spec_connectPostInit implementation_connectPostInit truthy
  simp only [Id.run]
  cases widthField <;> cases heightField <;> cases isAbstract <;>
    simp_all <;> rfl"""

# ---------------------------------------------------------------------------
# ADMISSIBILITY — must VERIFY, else PRECOND-TOO-STRONG / spec-shape regression.
# ---------------------------------------------------------------------------

# admiss-obligation-at-f2p: the port of nagini's admiss-readperm.
#
# AUDIT REPAIR (2026-08-13). The shipped version of this case asserted three
# facts about the helper `truthy` ALONE — `truthy none = false`,
# `truthy (some "") = false`, `truthy (some "wAttr") = true` — and nothing about
# `problem_spec_connectPostInit`. That made the case hollow in a way the gate
# cannot see: `truthy` lives in the frozen `pure` region, which every variant
# reproduces byte-identically because `same_spec` requires it, so those three
# `have`s are theorems about frozen text that hold in EVERY admissible variant
# of this bundle. The case could therefore only ever have failed if the frozen
# `truthy` itself were changed — which is not a variant this manifest can build
# — so it verified honestly while testing nothing about the OBLIGATION, and its
# rationale's claim ("does the obligation admit the entire name domain") named a
# thing the case never mentioned. It passed for the wrong reason.
#
# The analogue of an admissibility positive on a total carrier is: the
# obligation must be SATISFIABLE at exactly an F2P-shaped input, and at the
# P2P-shaped inputs the real fixtures reach. So the repaired case discharges
# `problem_spec_connectPostInit` itself, by evaluation, at seven concrete
# points, as `have`s, BEFORE closing the frozen obligation verbatim:
#   * (false, none, none) ↦ false — the F2P-shaped input: a concrete model
#     tracking no attribute. If the spec's clause were unsatisfiable here (a
#     PRECOND-TOO-STRONG / over-constrained postcondition), this `have` is the
#     one that fails, and it is the exact point the shipped F2P assertion probes.
#   * (false, some "", some "") ↦ false — the same decision reached through the
#     empty-name route rather than the absent-name route.
#   * (false, some "wAttr", none) ↦ true, (false, none, some "hAttr") ↦ true,
#     (false, some "wAttr", some "hAttr") ↦ true — the width-only, height-only
#     and both-attribute P2P fixture shapes.
#   * (true, some "wAttr", some "hAttr") ↦ false — an abstract model.
#   * (false, some "w", none) ↦ true — a one-character name, the boundary the
#     tightest reject rivals part company at.
# Each is `unfold problem_spec_connectPostInit; decide`, so it is settled by
# EVALUATING the frozen clause, not by restating it. The frozen tactic script is
# otherwise verbatim, so the only thing this case can fail on is the obligation
# becoming unsatisfiable at one of those inputs.
_ADMISS_OBLIGATION_AT_F2P = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  have _hF2P : problem_spec_connectPostInit false none none false := by
    unfold problem_spec_connectPostInit; decide
  have _hF2PEmpty : problem_spec_connectPostInit false (some "") (some "") false := by
    unfold problem_spec_connectPostInit; decide
  have _hWidthOnly : problem_spec_connectPostInit false (some "wAttr") none true := by
    unfold problem_spec_connectPostInit; decide
  have _hHeightOnly : problem_spec_connectPostInit false none (some "hAttr") true := by
    unfold problem_spec_connectPostInit; decide
  have _hBoth : problem_spec_connectPostInit false (some "wAttr") (some "hAttr") true := by
    unfold problem_spec_connectPostInit; decide
  have _hAbstractBoth : problem_spec_connectPostInit true (some "wAttr") (some "hAttr") false := by
    unfold problem_spec_connectPostInit; decide
  have _hMinimalName : problem_spec_connectPostInit false (some "w") none true := by
    unfold problem_spec_connectPostInit; decide
  if !isAbstract && (truthy widthField || truthy heightField) then
    return true
  return false"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each edits ONLY the
# impl region and ships a witness SEEN to discriminate (elaborates against the
# rival, fails against the frozen solution).
# ---------------------------------------------------------------------------

# (a) the pre-change decision: install for every concrete model, ignoring the
# tracked attribute names entirely. Ports nagini always-register-prepatch-bug.
_ALWAYS_CONCRETE = _guard("!isAbstract")

# (b) conjunction instead of disjunction: install only when BOTH attributes are
# tracked. Ports nagini and-instead-of-or.
_AND_NOT_OR = _guard("!isAbstract && (truthy widthField && truthy heightField)")

# (c) width-only partial domain: drop the height attribute from the decision.
# Correct everywhere except a concrete model that tracks only a height attribute.
# Ports nagini partial-domain-width-only.
_WIDTH_ONLY = _guard("!isAbstract && truthy widthField")

# (d) drop the concrete/abstract conjunct: install whenever an attribute is
# tracked, abstract models included. Ports nagini ignore-abstract.
_IGNORE_ABSTRACT = _guard("truthy widthField || truthy heightField")

# (e) never install — the no-op decision. Ports nagini never-register.
_NEVER = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  return false"""

# (f) always install, unconditionally: the opposite saturation to (e), and a
# STRICTLY weaker rival than (a) — it drops the concrete/abstract conjunct too.
# It is kept alongside (a) because the two fail at different points: (a) is
# already wrong at the F2P-shaped concrete dimension-less input, while this one
# is additionally wrong at the abstract dimension-less input, which no other
# witness in this battery probes as an OVER-installation.
_ALWAYS = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  return true"""

# (g) a present-but-empty width name counts as tracking something: use presence
# instead of non-emptiness for the width attribute. NO nagini counterpart at this
# precision (nagini's carrier stood the names in as lists). Wrong on exactly the
# sub-domain widthField = some "".
_EMPTY_WIDTH_COUNTS = _guard("!isAbstract && (widthField.isSome || truthy heightField)")

# (h) the same confusion on the HEIGHT name. Shipped separately from (g) because
# a rival that got the width test right and the height test wrong would otherwise
# be undetected by this battery, and because it moves a different binder to the
# empty-name point.
_EMPTY_HEIGHT_COUNTS = _guard("!isAbstract && (truthy widthField || heightField.isSome)")

# (i) exclusive-or instead of inclusive-or: install when EXACTLY ONE attribute is
# tracked. NO nagini counterpart. A genuine near-miss: it agrees with the frozen
# decision on the whole domain except when BOTH attributes are tracked — the one
# point at which "or" and "xor" part company, and the shape that a rival built
# from the single-attribute test cases alone would exhibit.
_XOR = _guard("!isAbstract && (truthy widthField != truthy heightField)")

# (j) require a name LONGER than one character rather than merely non-empty. NO
# nagini counterpart. The tightest near-miss in the battery: it agrees with the
# frozen decision at every absent name, every empty name, and every name of two
# or more characters, and parts company only at a one-character name. If C1's
# per-name test were pinned loosely — "long enough", "a plausible identifier" —
# rather than to non-emptiness exactly, this rival would verify.
_NAME_TOO_SHORT = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  let long (o : Option String) : Bool :=
    match o with
    | none   => false
    | some s => s.length > 1
  if !isAbstract && (long widthField || long heightField) then
    return true
  return false"""

# (k) the same length>1 confusion applied to the HEIGHT name ONLY, leaving the
# width name's test correct. ADDED BY AUDIT (2026-08-13): (j) applies `long` to
# BOTH names at once, so its witness at (false, some "w", none) is discharged by
# the width disjunct alone and the case never exercises the height name's test at
# the one-character boundary. The battery already ships that width/height pairing
# for the empty-name boundary — (g) and (h) exist precisely because the spec
# applies the name test to each attribute INDEPENDENTLY — but the length boundary
# had only the width side, so a rival with a correct width test and a
# length-confused height test was unattacked. This closes that asymmetry.
_HEIGHT_NAME_TOO_SHORT = """\
def implementation_connectPostInit
    (isAbstract : Bool) (widthField heightField : Option String) : Bool := Id.run do
  let longH (o : Option String) : Bool :=
    match o with
    | none   => false
    | some s => s.length > 1
  if !isAbstract && (truthy widthField || longH heightField) then
    return true
  return false"""


def _witness(args):
    """The spec clause stated at one concrete input and negated. `decide`
    settles it: the carrier is closed at a literal point (`Bool`,
    `Option String`, `String.isEmpty`), so nothing here is conditioned on an
    opaque term and the witness binds no hypothesis."""
    return f"""\
example : ¬ problem_spec_connectPostInit {args}
    (implementation_connectPostInit {args}) := by
  unfold problem_spec_connectPostInit implementation_connectPostInit
  decide"""


# Shared prose for the four rivals whose faithful patch would still satisfy the
# ONE shipped F2P assertion. Stated openly rather than dressed up as a
# resolve-break: the assertion probes a single point (a concrete model tracking
# no attribute), so a rival wrong only OUTSIDE that point is a spec-fidelity
# rival, not a demonstrated verify-does-not-imply-resolve break.
_SUBDOMAIN_NOTE = (
    "Disclosure on this rival's break class: the shipped F2P assertion probes "
    "exactly one point — a concrete model tracking neither attribute — and this "
    "rival agrees with the required decision there, so its faithful patch would "
    "still satisfy that assertion and the shipped P2P set does not exercise the "
    "sub-domain where it differs. It is therefore shipped as a SPEC-FIDELITY "
    "rival, not as a demonstrated verify-does-not-imply-resolve break: the "
    "sub-domain it corrupts is real behavior a legal configuration reaches, but "
    "the harness does not probe it, so if the spec ADMITTED this rival the "
    "weakness would be invisible to every other gate and only G-PBT could "
    "surface it. Recorded this way deliberately — claiming a non-resolution "
    "argument this rival does not support would attest to a break we have not "
    "shown."
)


SPEC_TESTS = [
    # -------------------- positives --------------------
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE, _POS_PURE_PROOF),
        "rationale": (
            "structurally-different CORRECT impl: no do-block at all, the "
            "decision returned as an expression after dispatching on the "
            "concrete/abstract flag first. Ports nagini pos-control-helper (bind "
            "the decision, then act on it) to a carrier where the decision IS "
            "the output. C1 is an equality on the whole domain, so it must hold "
            "of any impl computing the same Bool; the proof closes by splitting "
            "the flag. If this fails => SPEC-TOO-STRONG (C1 would be pinned to "
            "the frozen impl's syntactic form rather than to its value)."
        ),
    },
    {
        "id": "pos-demorgan",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DEMORGAN, _PROOF_SPLIT),
        "rationale": (
            "ports nagini pos-control-demorgan: De Morgan of the decision, "
            "early-skipping on 'abstract, or no attribute tracked' and installing "
            "in the fall-through. Same decision, inverted control shape, and the "
            "obligation reproved honestly by exhaustive case split (statement "
            "byte-identical, no new lemma). If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-decision-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LOCAL, _PROOF_SPLIT),
        "rationale": (
            "the two sub-decisions recombined in the opposite order: settle the "
            "tracked-attribute disjunction first into a mutable local, then let "
            "the concrete/abstract flag veto it. Confirms C1 constrains the VALUE "
            "and not the order in which the conjunction is evaluated. If it fails "
            "=> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-name-test-inlined",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_INLINE_NAME_TEST, _POS_INLINE_NAME_TEST_PROOF),
        "rationale": (
            "the GROUNDED-PREDICATE control, and the mirror of nagini's "
            "@Pure-helper positive. The frozen impl names `truthy` — the same "
            "helper C1 names — so the discriminating shape here is the reverse: "
            "match on the two names' presence and test emptiness inline, never "
            "mentioning that helper. Verifying shows C1's per-name test is "
            "satisfiable by its VALUE and not only by a syntactic echo of the "
            "spec's own helper. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-obligation-at-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS_OBLIGATION_AT_F2P),
        "rationale": (
            "ports nagini admiss-readperm. There is no permission to check on "
            "this carrier, so the surviving question is SATISFIABILITY of the "
            "obligation at the concrete inputs real configurations reach: this "
            "case discharges `problem_spec_connectPostInit` ITSELF, by "
            "evaluation, at seven points before closing the frozen obligation "
            "verbatim — the F2P-shaped input (concrete model tracking no "
            "attribute, required decision false), the same decision via the "
            "empty-name route, the width-only / height-only / both-attribute "
            "P2P fixture shapes, an abstract model, and a one-character name. "
            "Each `have` is `unfold; decide`, i.e. settled by evaluating the "
            "frozen clause rather than restating it, so the only way this case "
            "fails is the clause being unsatisfiable at one of those inputs. "
            "If it fails => PRECOND-TOO-STRONG / over-constrained postcondition. "
            "NOTE (audit repair): this replaces a prior version that asserted "
            "only `truthy none = false` / `truthy (some \"\") = false` / "
            "`truthy (some \"wAttr\") = true`. Those are facts about the frozen "
            "`pure` region, which same_spec forces every variant to reproduce "
            "byte-identically, so they held in every buildable variant and the "
            "case verified without ever mentioning the obligation."
        ),
    },

    # -------------------- uniqueness rivals --------------------
    {
        "id": "always-install-concrete-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_CONCRETE),
        "witness": _witness("false none none"),
        "refinement": (
            "this IS the pre-change decision: install for every concrete model, "
            "whether or not the field tracks a dimension. Its faithful patch is "
            "the unpatched repo, and the F2P test test_post_init_not_connected "
            "asserts precisely that a concrete model whose field tracks NEITHER "
            "attribute must not appear among the post-initialization handler's "
            "registered senders. It appears. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 at (isAbstract=false, widthField=none, "
            "heightField=none): the required decision is false (nothing tracked) "
            "but the rival returns true. Attacks sub-decision (b) — the tracked-"
            "attribute disjunction — by deleting it outright."
        ),
    },
    {
        "id": "and-instead-of-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_AND_NOT_OR),
        "witness": _witness('false (some "wAttr") none'),
        "refinement": (
            "requiring BOTH attributes leaves a concrete model that tracks only "
            "one of them without the post-initialization handler, so that "
            "model's tracked dimension attribute is never refreshed after "
            "instance initialization and stays cleared: the P2P cases 'Tests "
            "assigning an image field through the model's constructor.' and "
            "'Dimensions are updated correctly in various situations.' fail for "
            "the one-attribute model class (whose own fixture documents that the "
            "dimension update must run on concrete-subclass instance "
            "post-initialization). Does NOT resolve. Audit note on the witness "
            "point: this rival is wrong at EVERY single-attribute input, and the "
            "shipped one-attribute fixture tracks a HEIGHT attribute only, so "
            "the break the harness would actually observe is at the height-only "
            "input; the witness is stated at the width-only input (false, "
            "some \"wAttr\", none), which is an equally real point of the same "
            "break class but not the one the fixture occupies. The height-only "
            "point is witnessed separately by width-only-partial-domain."
        ),
        "rationale": (
            "rejected by C1 at (false, some \"wAttr\", none): the disjunction "
            "requires true (a width attribute is tracked) but the rival's "
            "conjunction returns false. Attacks sub-decision (b) with the "
            "operator swap that a test set containing only both-attribute models "
            "would never distinguish."
        ),
    },
    {
        "id": "width-only-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WIDTH_ONLY),
        "witness": _witness('false none (some "hAttr")'),
        "refinement": (
            "deciding on the width attribute alone drops height-only models from "
            "installation, so their post-initialization refresh never runs and the "
            "height attribute stays cleared after construction. That is exactly "
            "the shape of the height-only fixture in the P2P set, whose "
            "'constructor' and 'Dimensions are updated correctly' cases then fail. "
            "Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 at (false, none, some \"hAttr\"): the required "
            "decision is true (a height attribute is tracked) but the rival "
            "returns false. Attacks sub-decision (b) from the other side than "
            "and-instead-of-or, and is the near-miss that isolates the height "
            "disjunct specifically."
        ),
    },
    {
        "id": "never-install",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NEVER),
        "witness": _witness('false (some "a") (some "")'),
        "refinement": (
            "ports nagini never-register. A no-op decision installs the handler "
            "for NO model, so no image-valued field ever refreshes its tracked "
            "dimension attributes after instance initialization and every P2P "
            "constructor/dimension case regresses. Cheap supporting saturation "
            "rival. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 at (false, some \"a\", some \"\"): the required "
            "decision is true (the width name is non-empty; the empty height name "
            "tracks nothing but the disjunction already holds) and the rival "
            "returns false. The witness point deliberately mixes a MINIMAL "
            "non-empty name with an empty one, so it also pins that a one-"
            "character name suffices and an empty one does not contribute."
        ),
    },
    {
        "id": "always-install-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS),
        "witness": _witness("true none none"),
        "refinement": (
            "the opposite saturation to never-install: install for every model. "
            "Its faithful patch removes the guard entirely, so a concrete model "
            "tracking no attribute is registered and the F2P assertion "
            "test_post_init_not_connected fails on the very point it probes. Does "
            "NOT resolve."
        ),
        "rationale": (
            "rejected by C1 at (true, none, none) — an ABSTRACT model tracking "
            "nothing: the required decision is false on both counts and the rival "
            "returns true. Kept alongside always-install-concrete-prepatch "
            "because the two fail at different points: this witness is the only "
            "one in the battery that probes OVER-installation at an abstract "
            "input, which is what varies the isAbstract binder in the "
            "over-install direction."
        ),
    },
    {
        "id": "ignore-abstract-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IGNORE_ABSTRACT),
        "witness": _witness('true (some "wAttr") none'),
        "refinement": (
            "ports nagini ignore-abstract: drop the concrete/abstract conjunct and "
            "install whenever an attribute is tracked. Abstract models never "
            "receive initialized instances, so a handler installed against one can "
            "never do work — which is the same 'installed but cannot do anything' "
            "cost the public problem statement is about, reintroduced on a "
            "different axis. " + _SUBDOMAIN_NOTE
        ),
        "rationale": (
            "rejected by C1 at (true, some \"wAttr\", none): the required decision "
            "is false because the model is abstract, but the rival returns true. "
            "The ONLY rival in the battery whose error is confined to the abstract "
            "sub-domain, so it is what demonstrates the spec pins sub-decision "
            "(a) — the concrete/abstract conjunct — rather than inheriting it "
            "incidentally from another clause."
        ),
    },
    {
        "id": "exclusive-or-of-attributes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_XOR),
        "witness": _witness('false (some "wAttr") (some "hAttr")'),
        "refinement": (
            "an exclusive-or decision withholds the handler from a model that "
            "tracks BOTH attributes — the commonest real configuration and the "
            "default fixture behind most of the P2P image-field cases. Those "
            "models declare their tracked attributes after the image-valued "
            "field, so without the post-initialization refresh both attributes "
            "stay cleared after construction and the P2P 'constructor' and "
            "'Dimensions are updated correctly' cases fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1 at (false, some \"wAttr\", some \"hAttr\"): inclusive-"
            "or requires true, exclusive-or returns false. Attacks sub-decision "
            "(b) at the single point where 'or' and 'xor' part company, which is "
            "the point neither and-instead-of-or nor width-only-partial-domain "
            "reaches — both of those are already wrong at a single-attribute "
            "input, where this rival is CORRECT."
        ),
    },
    {
        "id": "empty-width-name-counts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY_WIDTH_COUNTS),
        "witness": _witness('false (some "") none'),
        "refinement": (
            "testing the width attribute for PRESENCE rather than for a non-empty "
            "name treats a declared-but-empty attribute name as tracking a "
            "dimension, installing a handler that can only ever look up the empty "
            "name. " + _SUBDOMAIN_NOTE
        ),
        "rationale": (
            "rejected by C1 at (false, some \"\", none): the grounded name test "
            "makes an empty name configure nothing, so the required decision is "
            "false, but the rival's presence test returns true. Attacks sub-"
            "decision (c) on the WIDTH name, and is the only witness holding "
            "widthField at the empty-name point."
        ),
    },
    {
        "id": "empty-height-name-counts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY_HEIGHT_COUNTS),
        "witness": _witness('false none (some "")'),
        "refinement": (
            "the same presence-for-non-emptiness confusion on the HEIGHT "
            "attribute name. " + _SUBDOMAIN_NOTE
        ),
        "rationale": (
            "rejected by C1 at (false, none, some \"\"): required false, rival "
            "true. Shipped separately from empty-width-name-counts because the "
            "spec applies the name test to each attribute INDEPENDENTLY: a rival "
            "that got the width test right and the height test wrong would "
            "otherwise pass unattacked, and this witness is the only one holding "
            "heightField alone at the empty-name point."
        ),
    },
    {
        "id": "name-must-exceed-one-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NAME_TOO_SHORT),
        "witness": _witness('false (some "w") none'),
        "refinement": (
            "demanding a name longer than one character withholds the handler "
            "from a model whose tracked attribute is named with a single "
            "character — a legal attribute name — so that model's dimension stays "
            "cleared after construction. " + _SUBDOMAIN_NOTE + " The shipped "
            "fixtures all use multi-character attribute names, which is precisely "
            "why this near-miss has to be tested here rather than left to the "
            "harness."
        ),
        "rationale": (
            "rejected by C1 at (false, some \"w\", none): a one-character name is "
            "non-empty, so the required decision is true, but the rival's "
            "length>1 test returns false. The TIGHTEST rival in the battery — it "
            "agrees with the frozen decision at every absent name, every empty "
            "name, and every name of two or more characters. It is what shows "
            "sub-decision (c) is pinned to non-emptiness EXACTLY and not to a "
            "loose 'long enough' reading, which no other witness distinguishes. "
            "Note it applies the length test to BOTH names, so this witness is "
            "discharged by the WIDTH disjunct; the height side of the same "
            "boundary is attacked separately by height-name-must-exceed-one-char."
        ),
    },
    {
        "id": "height-name-must-exceed-one-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEIGHT_NAME_TOO_SHORT),
        "witness": _witness('false none (some "h")'),
        "refinement": (
            "the length>1 confusion on the HEIGHT attribute name alone, with the "
            "width name's test left correct: a model whose only tracked "
            "attribute is a single-character height name is withheld from "
            "installation, so its dimension stays cleared after construction. "
            + _SUBDOMAIN_NOTE
        ),
        "rationale": (
            "ADDED BY AUDIT (2026-08-13). Rejected by C1 at "
            "(false, none, some \"h\"): a one-character name is non-empty so the "
            "required decision is true, but the rival's height-side length>1 "
            "test returns false. Shipped because name-must-exceed-one-char "
            "applies `long` to BOTH names, so its witness at "
            "(false, some \"w\", none) is settled by the width disjunct and "
            "leaves the HEIGHT name's one-character boundary unprobed — the same "
            "per-name independence the empty-name pair (g)/(h) exists to cover. "
            "This is the only witness in the battery holding heightField alone "
            "at a one-character name."
        ),
    },
]
