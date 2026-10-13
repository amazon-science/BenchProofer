# properties.py — G-PBT falsification battery for django__django-10914 (lean lane).
# NOT a Lean module; a record of adversarial cases the gate elaborates against
# the frozen spec. Ported from the nagini sibling's properties.py, re-expressed
# against this backend's carrier.
#
# Defended surface (read from Solution.lean):
#   effectiveFilePermissionsMode
#     (storageOverride : Option Nat) (projectSetting : Option (Option Nat))
#     : Option Nat
#   The effective upload permission mode, resolved most-specific-first. Two
#   independent top-level postcondition clauses pin the whole output:
#     (C1) ∀ m, storageOverride = some m → result = some m
#          — a concrete per-instance override wins outright, whatever the setting.
#     (C2) storageOverride = none →
#            result = (match projectSetting with some v => v | none => default)
#          — with no per-instance override, the project-configured mode is used
#            when one is declared, and otherwise the built-in default (a definite
#            concrete mode). This is the layer the change makes definite.
#
# Carrier narrowing vs the nagini sibling. The nagini model contracted a single
# `resolve_storage_mode(override)` over ONE input; this bundle models the full
# most-specific-first cascade over TWO input binders (`storageOverride` and the
# nested `projectSetting`). Consequences for the port:
#   * The nagini C2/C3/C4 clauses (absent override => a DEFINITE default) collapse
#     into this bundle's C2 tail (`projectSetting = none => default`). The default
#     is `defaultUploadMode`, a `def` equal to a concrete mode, so the "grounded
#     oracle" distinction the nagini file drew (an echo of that constant is
#     CORRECT, not a wrong echo) still holds — there is no wrong echo to build,
#     so no such reject case is shipped. The grounded-oracle POSITIVE control is
#     shipped, MIRRORED: nagini's gold inlined the literal and its control
#     referenced the `@Pure` oracle, whereas this carrier's frozen impl already
#     references `defaultUploadMode`, so the discriminating shape is the reverse
#     — inline the concrete mode and never mention the oracle symbol at all
#     (pos-grounded-oracle below). That is what shows the C2 tail is pinned to a
#     VALUE and not to a syntactic echo of the spec's own constant.
#   * The new second binder is an attack surface nagini never had: rivals that
#     mishandle the project-setting layer (ignore it, or conflate its inner
#     `none` with an absent outer setting). These have NO nagini counterpart and
#     are added here so every input binder is exercised by some reject witness.
#     Note the binders must also be attacked JOINTLY, not just one at a time: a
#     rival can be correct at every single-binder point and still break the
#     cascade where both layers are populated (weak-precedence-inversion, and
#     weak-inner-none-preempts for the inner-`none` case).
#
# Vacuous / dropped classes (stated per directive, not silently omitted):
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean. The nagini file already
#     records this class as inapplicable (immutable scalar input, no heap
#     permissions). Lean is referentially transparent: there is no aliasable
#     read-only input to overwrite. Nothing to port.
#   * DIVERGENCE / NON-TERMINATION lane — VACUOUS on lean. The nagini sibling
#     carries no such case here, and in any event `implementation_*` is a total
#     Lean `def`: a diverging implementation cannot be written, so the class does
#     not exist on this carrier (contrast velvet's `partial` semantics, a known
#     spec hole — not relevant to lean; see the corpus-wide termination-semantics finding).
#   * AXIOM lane — DROPPED. `meta.axioms == []`, no opaque callee; the resolution
#     and the changed default are modeled directly. The axiom lane is G-AX's job
#     and this gate ignores it. AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-10914"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen regions, extracted verbatim so the manifest breaks loudly on drift.
# The impl region body (everything strictly between the impl markers) and the
# proof tactic body (everything after the theorem STATEMENT, up to the proof
# marker) are the ONLY regions a variant may edit. The spec, signatures, and the
# byte-identical `theorem correct_*` statement are never touched, so same_spec
# holds by construction.

_IMPL_OLD = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := defaultUploadMode
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some m => return some m
  | none   => return setting"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

# The frozen proof tactic body (after the theorem statement's `:= by`).
_PROOF_OLD = """\
  intro storageOverride projectSetting
  constructor
  · intro m hm
    cases projectSetting with
    | none => simp [implementation_effectiveFilePermissionsMode, hm]
    | some v => simp [implementation_effectiveFilePermissionsMode, hm]
  · intro hnone
    cases projectSetting with
    | none => simp [implementation_effectiveFilePermissionsMode, hnone]
    | some v => simp [implementation_effectiveFilePermissionsMode, hnone]"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """Build a full Solution.lean variant. Replaces the impl body, and (for
    soundness positives whose reshaped impl needs a matching proof) the proof
    tactic body. The theorem STATEMENT and the whole spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY. Each is a structurally different
# but behaviourally identical correct impl, shipped WITH a proof that closes for
# the new shape (the theorem statement is byte-identical; only the tactic body
# changes). No new lemma / axiom / sorry.
# ---------------------------------------------------------------------------

# pos-branch-reorder: dispatch on the per-instance override FIRST (mirrors the
# nagini pos-branch-reorder — guard inverted, present branch handled first),
# then fall through the project-setting cascade. Same Id.run do idiom; the frozen
# `cases … simp` proof still closes because both branches reduce definitionally.
_POS_REORDER = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  match storageOverride with
  | some m => return some m
  | none   =>
    match projectSetting with
    | some v => return v
    | none   => return defaultUploadMode"""

_POS_REORDER_PROOF = """\
  intro storageOverride projectSetting
  constructor
  · intro m hm
    cases projectSetting with
    | none => simp [implementation_effectiveFilePermissionsMode, hm]
    | some v => simp [implementation_effectiveFilePermissionsMode, hm]
  · intro hnone
    cases projectSetting with
    | none => simp [implementation_effectiveFilePermissionsMode, hnone]
    | some v => simp [implementation_effectiveFilePermissionsMode, hnone]"""

# pos-pure-functional: the same resolution written as a pure functional match
# (no Id.run / no `let mut`), the shape the real selector actually has. The proof
# collapses to `subst; rfl` on each clause because the result is definitionally
# the spec's RHS. Confirms the spec does not secretly depend on the imperative
# encoding.
_POS_PURE = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat :=
  match storageOverride with
  | some m => some m
  | none   =>
    match projectSetting with
    | some v => v
    | none   => defaultUploadMode"""

_POS_PURE_PROOF = """\
  intro storageOverride projectSetting
  constructor
  · intro m hm
    subst hm
    rfl
  · intro hnone
    subst hnone
    rfl"""

# pos-grounded-oracle: the MIRRORED port of the nagini grounded-oracle control
# (see the carrier note at the top). The frozen impl reaches the C2 tail by
# naming `defaultUploadMode`, the same symbol the spec's own tail names; this
# impl instead inlines the concrete mode and never mentions that symbol. If the
# C2 tail were satisfiable only by a syntactic echo of the spec's constant
# rather than by its VALUE, this would fail — so it is the control that makes
# the "grounded oracle" claim about `defaultUploadMode` a measured one.
_POS_ORACLE_INLINE = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  match storageOverride with
  | some m => return some m
  | none   =>
    match projectSetting with
    | some v => return v
    | none   => return (some 0o644)"""

_POS_ORACLE_INLINE_PROOF = """\
  intro storageOverride projectSetting
  constructor
  · intro m hm
    subst hm
    rfl
  · intro hnone
    subst hnone
    cases projectSetting <;> rfl"""

# admiss-shape: the port of the nagini admiss-roundtrip control. Nagini asserted
# the postcondition SHAPE at the F2P/P2P-shaped inputs with in-body
# `Assert(...)`; the lean analogue is the same claims as in-body `have`s.
#
# AUDIT REPAIR. The claims were originally written as `defaultUploadMode = some
# 0o644` and `(some 511 : Option Nat) = some 511`. Neither mentioned
# `problem_spec_effectiveFilePermissionsMode`, so neither asserted the
# postcondition shape at anything: the first is a definitional unfold of the
# constant and the second is a pure `rfl` tautology that elaborates in ANY file,
# against every rival in this battery included. The case therefore verified
# because the frozen impl and frozen proof were kept verbatim, not because the
# claimed points hold — an honest pass that measured nothing. Restated as the
# actual spec predicate applied at each point, so a spec/shape regression at
# those inputs really does break this case. A third point (the explicit
# "no special mode" declaration) is included because it is the shape claim the
# nagini sibling's single-binder model could not state at all.
_ADMISS_SHAPE = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  have _hDefault : problem_spec_effectiveFilePermissionsMode none none
      (some 0o644) := by unfold problem_spec_effectiveFilePermissionsMode; decide
  have _hPass : problem_spec_effectiveFilePermissionsMode (some 511) (some (some 7))
      (some 511) := by unfold problem_spec_effectiveFilePermissionsMode; decide
  have _hInnerNone : problem_spec_effectiveFilePermissionsMode none (some none)
      none := by unfold problem_spec_effectiveFilePermissionsMode; decide
  let mut setting : Option Nat := defaultUploadMode
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some m => return some m
  | none   => return setting"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region; every one ships a `witness` proving it violates the spec at a
# concrete input (elaborates against the rival, fails against the frozen sol).
# ---------------------------------------------------------------------------

# weak-default-none: the pre-change behaviour — the built-in default stays absent
# (none) instead of the concrete mode. Violates C2 on the (none, none) input.
# (Ports nagini weak-default-none.)
_WEAK_NONE = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := none
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some m => return some m
  | none   => return setting"""

# weak-always-default: collapse the whole cascade to the built-in default,
# ignoring BOTH the override and the project setting. Violates C1. (Ports nagini
# weak-always-default.)
_WEAK_ALWAYS = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  return defaultUploadMode"""

# weak-wrong-default: use a different concrete built-in default (0o600, the value
# the issue thread floated and the community rejected in favour of 0o644).
# Satisfies C1 and the C2 project-declared sub-case, violates the C2 tail. (Ports
# nagini weak-wrong-default.)
_WEAK_WRONG = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := some 0o600
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some m => return some m
  | none   => return setting"""

# weak-swap-branches: the inverted resolver — a present override returns the
# project cascade, an absent override returns none. Violates C1 (override no
# longer wins) AND the C2 tail. (Ports nagini weak-swap-branches.)
_WEAK_SWAP = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := defaultUploadMode
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some _ => return setting
  | none   => return none"""

# weak-partial-zero: correct on almost the whole domain, but special-cases the
# valid override mode 0 (0o000, all permissions cleared — a real chmod value) to
# fall back to the default instead of passing it through. Violates C1 on exactly
# the single sub-domain storageOverride = some 0. A byte-fuzzer never targets
# this boundary. (Ports nagini weak-partial-zero.)
_WEAK_ZERO = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := defaultUploadMode
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some 0 => return setting
  | some m => return some m
  | none   => return setting"""

# weak-ignore-setting: NO nagini counterpart — attacks the second binder. With no
# per-instance override it ignores the project-declared setting entirely and
# returns the built-in default. Violates the C2 project-declared sub-case
# (projectSetting = some v must yield v). Without this rival the `projectSetting`
# binder would be handled the same by gold and rival on every reject witness — a
# binder no rival abuses.
_WEAK_IGNORE_SETTING = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  match storageOverride with
  | some m => return some m
  | none   => return defaultUploadMode"""

# weak-setting-inner-none: NO nagini counterpart — attacks the INNER Option of the
# second binder. When the project explicitly declares the setting as the "no
# special mode" choice (projectSetting = some none), the spec's C2 requires the
# result to be that explicit `none`; this rival conflates it with "not declared"
# and substitutes the built-in default. Violates the C2 project-declared sub-case
# at the inner-none point only.
_WEAK_SETTING_INNER_NONE = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  match storageOverride with
  | some m => return some m
  | none   =>
    match projectSetting with
    | some (some k) => return some k
    | some none     => return defaultUploadMode
    | none          => return defaultUploadMode"""

# weak-mask-high-bits: NO nagini counterpart. Every rival above either passes an
# override through untouched or reroutes it wholesale; none returns a MODIFIED
# override value. This one masks the mode down to its low nine bits, so it is
# correct for every ordinary permission mode and wrong only for modes that carry
# a bit above 0o777 (setuid/setgid/sticky, e.g. 0o10755 = 4589). Violates C1 on
# exactly that sub-domain. Closes the "the override is echoed verbatim" clause,
# which no other witness pins at a value the mask would change.
_WEAK_MASK = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  match storageOverride with
  | some m => return some (m % 512)
  | none   =>
    match projectSetting with
    | some v => return v
    | none   => return defaultUploadMode"""

# weak-precedence-inversion: NO nagini counterpart. A strictly TIGHTER near-miss
# than weak-swap-branches, which also breaks the C2 tail and so could be rejected
# on the tail alone. This one gets the C2 clause entirely right (both the
# declared and the undeclared sub-cases) and inverts ONLY the layer precedence:
# when the project declares a mode AND a per-instance override is present, the
# project setting wins instead of the override. Violates C1 only when both layers
# are populated — the one point where "most specific first" is actually load-
# bearing, and the point a rival that breaks several clauses at once cannot
# isolate.
_WEAK_PRECEDENCE = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  match projectSetting with
  | some v => return v
  | none   =>
    match storageOverride with
    | some m => return some m
    | none   => return defaultUploadMode"""

# weak-off-by-one-default: NO nagini counterpart. weak-wrong-default probes the
# changed constant with a far-away value (0o600); this probes it with the nearest
# possible one (0o645, a single bit away from 0o644). If the C2 tail pinned the
# default only loosely — to a range, a parity, or "some concrete mode" rather
# than to the exact value — the far miss would still be caught and this one would
# not. Violates the C2 tail at (none, none).
_WEAK_OFF_BY_ONE = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  let mut setting : Option Nat := some 0o645
  match projectSetting with
  | some v => setting := v
  | none   => pure ()
  match storageOverride with
  | some m => return some m
  | none   => return setting"""


# weak-inner-none-preempts: ADDED IN AUDIT. Every existing rival treats the
# explicit "no special mode" declaration (projectSetting = some none) only on the
# absent-override path (weak-setting-inner-none), so no case pinned what happens
# when that declaration is present AND a per-instance override is also set. This
# rival lets the explicit no-mode declaration PREEMPT the whole cascade, so a
# store carrying its own concrete mode silently performs no permission adjustment
# at all. Correct everywhere else — including at every input the other twelve
# cases witness at. Violates C1 on exactly the sub-domain
# (storageOverride = some m, projectSetting = some none).
_WEAK_INNER_NONE_PREEMPTS = """\
def implementation_effectiveFilePermissionsMode
    (storageOverride : Option Nat) (projectSetting : Option (Option Nat)) :
    Option Nat := Id.run do
  match projectSetting with
  | some none => return none
  | _ =>
    match storageOverride with
    | some m => return some m
    | none   =>
      match projectSetting with
      | some v => return v
      | none   => return defaultUploadMode"""


# --- Witness helper. Each reject case states the spec predicate directly at a
# concrete, `decide`-able input; the negation elaborates iff the rival's output
# contradicts the spec there. Checked in a file with the frozen obligations
# removed, so no tactic script can interfere.
def _witness(args):
    return f"""\
example : ¬ problem_spec_effectiveFilePermissionsMode {args}
    (implementation_effectiveFilePermissionsMode {args}) := by
  unfold problem_spec_effectiveFilePermissionsMode implementation_effectiveFilePermissionsMode
  decide"""


SPEC_TESTS = [
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER, _POS_REORDER_PROOF),
        "rationale": (
            "structurally-different but behaviourally-identical impl (dispatch on "
            "the per-instance override first, then the project-setting cascade). "
            "The frozen `cases projectSetting … simp` proof still closes for both "
            "C1 and C2 because each branch reduces definitionally. If it fails => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE, _POS_PURE_PROOF),
        "rationale": (
            "the same resolution as a pure functional match (no Id.run / let mut) "
            "— the shape the real two-line selector actually has. Result is "
            "definitionally the spec RHS, so the proof is `subst; rfl` per clause. "
            "Confirms the spec does not secretly depend on the imperative "
            "encoding. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_ORACLE_INLINE, _POS_ORACLE_INLINE_PROOF),
        "rationale": (
            "the MIRRORED grounded-oracle control. The frozen impl reaches the "
            "C2 tail by naming `defaultUploadMode` — the very symbol the spec's "
            "tail names — so the shape that actually discriminates on this "
            "carrier is the reverse of nagini's: inline the concrete mode and "
            "never mention that symbol. Verifying shows the C2 tail is pinned to "
            "the oracle's VALUE and not satisfiable only by a syntactic echo of "
            "the spec's own constant. If it fails => SPEC-TOO-STRONG (the tail "
            "would demand the echo)."
        ),
    },
    {
        "id": "admiss-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS_SHAPE),
        "rationale": (
            "ports the nagini admiss-roundtrip control: the F2P/P2P-shaped "
            "points asserted in-body (nagini `Assert(...)` -> lean `have ... := "
            "by unfold …; decide`) — the absent-everything input resolving to "
            "the definite default, a concrete override winning over a declared "
            "project mode, and the explicit no-mode declaration passing through. "
            "Each `have` applies `problem_spec_effectiveFilePermissionsMode` "
            "itself at that point, so it is the postcondition that is checked "
            "there and not a definitional identity: the earlier form of this "
            "case asserted `(some 511 : Option Nat) = some 511`, a tautology "
            "true in any file, and so verified without measuring anything (fixed "
            "in audit). Impl body and frozen proof script are otherwise verbatim, "
            "so the only thing this can fail on is a spec/shape regression at "
            "those points. If it fails => PRECOND-TOO-STRONG / spec-shape "
            "regression."
        ),
    },
    {
        "id": "weak-default-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NONE),
        "witness": _witness("none none"),
        "refinement": (
            "this IS the pre-change behaviour (the built-in default left absent). "
            "Its faithful real patch is the unpatched repo, whose F2P test "
            "test_override_file_upload_permissions asserts the default-storage "
            "mode equals the concrete 0o644 but finds the absent value. Does NOT "
            "resolve."
        ),
        "rationale": (
            "rejected by C2 tail (storageOverride = none, projectSetting = none => "
            "result = defaultUploadMode = some 0o644, but rival returns none). "
            "Witness at (none, none). If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-always-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS),
        "witness": _witness("(some 511) none"),
        "refinement": (
            "collapsing the cascade to the built-in default ignores a configured "
            "per-instance override. A faithful patch dropping the override layer "
            "would resolve the F2P override sub-check (a concrete override must "
            "still win) to the default instead of the override value. Does NOT "
            "resolve."
        ),
        "rationale": (
            "rejected by C1 (storageOverride = some 511 must give some 511, rival "
            "returns the default some 0o644). Witness at (some 511, none). If it "
            "verifies => SPEC-TOO-WEAK (override branch unconstrained)."
        ),
    },
    {
        "id": "weak-wrong-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_WRONG),
        "witness": _witness("none none"),
        "refinement": (
            "0o600 is the default the issue thread first proposed and the "
            "community explicitly rejected in favour of 0o644. A real patch "
            "pinning the built-in default to 0o600 fails the F2P assertion, which "
            "demands the concrete 0o644. Does NOT resolve."
        ),
        "rationale": (
            "satisfies C1 and the C2 project-declared sub-case, rejected by the C2 "
            "tail (result must equal defaultUploadMode = some 0o644 on "
            "(none, none), rival returns some 0o600). Witness at (none, none). If "
            "it verifies => the exact default value would be unpinned "
            "(SPEC-TOO-WEAK)."
        ),
    },
    {
        "id": "weak-swap-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP),
        "witness": _witness("(some 511) (some (some 7))"),
        "refinement": (
            "the inverted resolver (a present override returns the fallback, an "
            "absent override returns the absent value). Its real patch returns the "
            "project cascade when an override IS set and none when it is not — "
            "failing both the F2P default-storage case and the override sub-check. "
            "Does NOT resolve."
        ),
        "rationale": (
            "rejected by C1: storageOverride = some 511 must give some 511, but "
            "with projectSetting = some (some 7) the rival returns some 7. Witness "
            "at (some 511, some (some 7)) — a C1 violation distinct from "
            "weak-always-default's default value, so it probes a fresh point. If "
            "it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-partial-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ZERO),
        "witness": _witness("(some 0) none"),
        "refinement": (
            "mode 0 (0o000, all permissions cleared) is a legitimate chmod value a "
            "store could configure. A real patch special-casing it would resolve a "
            "store whose override is 0 to the default instead of 0, diverging from "
            "the unchanged most-specific-wins rule (which passes 0 through). Does "
            "NOT faithfully implement the resolver. PARTIAL-DOMAIN attack."
        ),
        "rationale": (
            "rejected by C1 on the single sub-domain storageOverride = some 0: it "
            "must pass through as some 0, but the rival returns the default some "
            "0o644. Witness at (some 0, none) — a boundary a byte-fuzzer never "
            "targets. If it verifies => SPEC-TOO-WEAK on that boundary."
        ),
    },
    {
        "id": "weak-ignore-setting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_IGNORE_SETTING),
        "witness": _witness("none (some (some 511))"),
        "refinement": (
            "ignoring a project-declared setting when no per-instance override is "
            "present. A real patch that reads only the built-in default and never "
            "the project setting would, under a project that declares the setting "
            "as a concrete mode, resolve to the default rather than the declared "
            "mode — the F2P test's project-override branch (a declared setting must "
            "win) then fails. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the C2 project-declared sub-case (storageOverride = none, "
            "projectSetting = some (some 511) => result must be some 511, rival "
            "returns the default some 0o644). Exercises the OUTER Option of the "
            "second binder, which no other rival varies. Witness at "
            "(none, some (some 511)). If it verifies => SPEC-TOO-WEAK on the "
            "project-setting layer."
        ),
    },
    {
        "id": "weak-setting-inner-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SETTING_INNER_NONE),
        "witness": _witness("none (some none)"),
        "refinement": (
            "conflating an explicitly-declared 'no special mode' project setting "
            "with 'not declared'. A real patch that treats an explicit no-mode "
            "declaration as if the setting were unset would substitute the "
            "built-in default where the project asked for the explicit absent "
            "mode, changing the observable resolved mode away from what the "
            "project declared. Does NOT faithfully implement the cascade."
        ),
        "rationale": (
            "rejected by the C2 project-declared sub-case at the INNER-none point "
            "(storageOverride = none, projectSetting = some none => result must be "
            "none, rival returns the default some 0o644). Exercises the INNER "
            "Option of the second binder — distinct from weak-ignore-setting's "
            "inner-some point. Witness at (none, some none). If it verifies => "
            "SPEC-TOO-WEAK on the explicit-no-mode declaration."
        ),
    },
    {
        "id": "weak-mask-high-bits",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MASK),
        "witness": _witness("(some 4589) none"),
        "refinement": (
            "masking the configured mode down to its low nine bits. A store may "
            "legitimately be configured with a mode carrying a bit above 0o777 "
            "(setuid/setgid/sticky are exactly the modes an operator sets "
            "deliberately); a real patch that masked them off would hand such a "
            "store a silently different mode from the one it configured, while "
            "behaving correctly for every ordinary mode. Does NOT faithfully "
            "implement the resolver. PARTIAL-DOMAIN attack."
        ),
        "rationale": (
            "rejected by C1 on the sub-domain of modes with a bit above 0o777: "
            "storageOverride = some 4589 (0o10755) must pass through as some "
            "4589, but the rival returns some 493 (0o755). This is the only rival "
            "that returns a MODIFIED override value — every other one passes the "
            "override through untouched or reroutes it wholesale, so without this "
            "case the 'echoed verbatim' half of C1 is pinned at no value a mask "
            "would change. If it verifies => SPEC-TOO-WEAK on that sub-domain."
        ),
    },
    {
        "id": "weak-precedence-inversion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PRECEDENCE),
        "witness": _witness("(some 511) (some (some 7))"),
        "refinement": (
            "inverting the precedence of the two configuration layers. A real "
            "patch consulting the project-wide setting before the per-instance "
            "one would, for a store constructed with its own explicit mode under "
            "a project that also declares one, apply the project's mode and "
            "discard the store's — the most-specific-wins rule, which this change "
            "does not touch, reversed. Does NOT faithfully implement the cascade."
        ),
        "rationale": (
            "rejected by C1, and ONLY by C1 at the both-layers-populated point: "
            "storageOverride = some 511 must give some 511, but the rival returns "
            "the declared some 7. Strictly tighter than weak-swap-branches, which "
            "also breaks the C2 tail and so could be rejected on the tail alone — "
            "this rival satisfies C2 in full (both the declared and undeclared "
            "sub-cases) and misses only the layer ORDER, which is load-bearing at "
            "exactly this one point. Witness at (some 511, some (some 7)). If it "
            "verifies => SPEC-TOO-WEAK on layer precedence."
        ),
    },
    {
        "id": "weak-inner-none-preempts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_INNER_NONE_PREEMPTS),
        "witness": _witness("(some 511) (some none)"),
        "refinement": (
            "letting an explicit project-wide 'no special mode' declaration "
            "preempt a per-instance override. A real patch that checked the "
            "project-wide no-mode choice before consulting the per-instance layer "
            "would leave a store that was constructed with its own concrete mode "
            "performing no permission adjustment at all — the most-specific-wins "
            "rule, which this change does not touch, silently overridden by the "
            "less specific layer. Does NOT faithfully implement the cascade."
        ),
        "rationale": (
            "rejected by C1 on the sub-domain (storageOverride = some m, "
            "projectSetting = some none): the override must give some 511, but "
            "the rival returns none. This is the one corner of the two-binder "
            "input space no other case pins — weak-setting-inner-none exercises "
            "the explicit no-mode declaration only with the override ABSENT, and "
            "weak-precedence-inversion inverts precedence only against a declared "
            "CONCRETE mode — so the rival agrees with gold at every point the "
            "other twelve cases witness at. Added during audit for that reason. "
            "Witness at (some 511, some none). If it verifies => SPEC-TOO-WEAK on "
            "the interaction of the two binders."
        ),
    },
    {
        "id": "weak-off-by-one-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_OFF_BY_ONE),
        "witness": _witness("none none"),
        "refinement": (
            "a built-in default one bit away from the intended one (0o645 rather "
            "than 0o644 — world-executable where the intended mode is not). A "
            "real patch pinning the default to 0o645 fails the same F2P assertion "
            "that demands the exact concrete mode. Does NOT resolve."
        ),
        "rationale": (
            "rejected by the C2 tail on (none, none), like weak-wrong-default but "
            "at the NEAREST possible miss (0o645 vs 0o644, one bit) rather than a "
            "far-away value. If the tail pinned the default only loosely — to a "
            "range, or merely to 'some concrete mode' — the far miss would still "
            "be caught while this one slipped through, so this case is what makes "
            "'the exact value is pinned' a measured claim. If it verifies => "
            "SPEC-TOO-WEAK on the exact default value."
        ),
    },
]

# No @ContractOnly axioms and no opaque callee on this path (meta.axioms == [],
# no deep-model references); the resolution and changed default are modeled
# directly. Nothing for the axiom lane to execute.
AXIOM_TESTS = []
