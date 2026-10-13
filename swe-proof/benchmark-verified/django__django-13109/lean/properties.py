# properties.py — G-PBT falsification battery for django__django-13109 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for a soundness positive that reproves, the proof body — is
# edited), checked by variant_scope + the Lean verifier. Every expect="reject" case
# carries a refutation `witness`: a self-contained snippet that ELABORATES against
# the rival and FAILS on the frozen solution, so the rejection is attributable to
# the spec and not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   validateReference (parentLink : Bool) (value : Option Nat) (rows : List Row)
#                     : Bool
#   Soundness of a reference from one record to a stored target record. The SINGLE
#   postcondition `problem_spec_validateReference` pins the whole verdict to ONE
#   equation:
#     result = (if parentLink then true
#               else match value with
#                    | none  => true
#                    | some v => existsValid v rows)
#   which bundles several independent obligations over three input binders:
#     (G1) PARENT-LINK GATE: `parentLink = true` ⇒ sound outright (no existence
#          check). Binder: `parentLink`.
#     (G2) NULL GATE: `value = none` ⇒ sound outright. Binder: `value`.
#     (E)  EXISTENCE CHECK (`some v`): sound exactly when the UNDERLYING stored
#          collection (`rows` IN FULL, independent of each record's
#          `defaultVisible` presentation flag) contains an eligible record whose
#          `key` equals `v` and whose `limitOk` holds — `existsValid v rows`.
#          Sub-obligations, each a distinct binder the rivals below abuse:
#            (E-vis)  the verdict does NOT depend on `defaultVisible`: a genuinely
#                     stored record hidden by the default presentation still
#                     counts. THE ACTUAL FIX.
#            (E-key)  only records whose `key` equals `v` count.
#            (E-lim)  only records satisfying the choice constraint (`limitOk`)
#                     count.
#            (E-all)  EVERY stored record is inspected (no record skipped).
#
# The carrier is FULLY TRANSPARENT: `Row` is three concrete fields (`Nat` / `Bool`
# / `Bool`) and `existsValid` computes by `List.any`. So every reject witness is a
# `decide` at concrete literal rows — no opaque callee, no carrier conditioning,
# no hypothesis binders (the gate's inconsistency probe is trivially satisfied
# because there are no hypotheses to be inconsistent).
#
# THE ADMISSIBILITY LANE DOES PORT (nagini's `admiss-reads`). An earlier revision of
# this battery recorded it N/A on the ground that the lean obligation carries NO
# precondition hypothesis, so nothing could be PRECOND-TOO-STRONG. That reason is
# WRONG, and this audit removed it: on a total carrier the analogue of a too-strong
# precondition is the modeled obligation being UNSATISFIABLE at exactly an
# F2P-shaped input, which a positive that discharges the obligation AT that concrete
# input — by evaluation, as a `have`, before closing the frozen obligation verbatim —
# tests directly. That is case `admiss-ground-hidden` below, and it verifies
# (measured). The lane is therefore expressed, not omitted.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY pair: `complete_rows` / `curated_rows`
#     were Acc(...,1/2) read-only and two rivals wrote back into them). Lean is
#     referentially transparent — no aliasing, no fractional permission — so a
#     "store into a read-only input" rival is not expressible. The read-only frame
#     obligation instead lives in the postcondition equation itself: the result is
#     a pure function of the inputs, so no rival can smuggle an effect. VACUOUS
#     here; see 'assessment'. DEMONSTRATED, not asserted: the closest analogue —
#     an impl that binds a local `let mut scratch := rows` and reassigns it
#     (`.reverse`, then `[]`) before running the frozen decision — still VERIFIES
#     (measured, exit 0). A local rebinding is unobservable in the result, so there
#     is no frame obligation for a rival to violate and no reject case to author.
#   * DIVERGENCE / NON-TERMINATION (nagini's MustTerminate(2) obligation P3).
#     NOTHING TO SHIP here, but not because a diverging impl is unwritable: it is
#     writable (`partial def implementation_validateReference ... := implementation_
#     validateReference ...` passes the mechanical scope check). MEASURED: that
#     variant is REJECTED by the frozen obligation, because `partial def` compiles
#     to an opaque constant backed by an `Inhabited` witness rather than to
#     equations, so the obligation cannot be discharged — `error: Tactic `unfold`
#     failed to unfold `implementation_validateReference``. It is therefore a
#     rejected-for-the-wrong-reason case (the failure is an unfolding failure, not
#     a semantic refutation at a concrete input), and NO witness can discriminate
#     it: an opaque constant has no computable value, so a `decide` refutation at
#     literal inputs does not elaborate against the rival either. This lane also
#     does NOT reproduce the known velvet-`partial` spec hole (that needs
#     `set_option loom.semantics.termination "partial"`, which this bundle does not
#     set; see the corpus-wide termination-semantics finding — not re-reported here). Omitted as
#     INEXPRESSIBLE-AS-A-WITNESSED-CASE, on the measurement above.
#   * AXIOM_TESTS (nagini's `ax-ref-manager-subset` / `ax-cover-choice-permitted`).
#     The axiom lane is G-AX's job; this gate ignores them. This bundle has NO
#     opaque callee and NO consumed axiom (the manager-selection decision is
#     modeled DEEPLY as the choice of whether the scan honours `defaultVisible`),
#     so there is nothing for this spec lane to test there anyway.
#
# CARRIER NARROWING vs nagini: nagini modeled the check imperatively as a
# back-to-front membership scan over `complete_rows` guarded by MustTerminate, and
# spent much of its battery on the frame/termination machinery (four of nine spec
# cases were frame or admissibility). Those classes are vacuous or N/A above. What
# remains — the actual behavioural obligations — ports one-for-one and is here
# BROADENED, because this carrier exposes as transparent fields (`key`,
# `defaultVisible`, `limitOk`) three sub-obligations nagini could only attack
# through the single opaque `choice_permitted` predicate:
#   nagini `admiss-reads`         -> admiss-ground-hidden  (obligation satisfiable at
#                                                           an F2P-shaped input)
#   nagini `weak-curated-bug`     -> weak-prepatch-default (E-vis)
#   nagini `weak-ignore-choice`   -> weak-ignore-choice    (E-lim)
#   nagini `weak-skip-head`       -> weak-skip-head        (E-all)
#   nagini `weak-always-return`   -> weak-always-return    (G1/G2/E, absent case)
#   nagini `weak-always-raise`    -> weak-always-raise     (E, present case)
#   (new, this carrier)           -> weak-ignore-key       (E-key)
#   (new, this carrier)           -> weak-ignore-parentlink (G1)
#   (new, this carrier)           -> weak-ignore-null      (G2)
#   (new, audit)                  -> weak-zero-as-null     (E, falsy-value sub-domain)
#   (new, audit)                  -> weak-all-not-any      (E, existential force)
# Details per case below.
from pathlib import Path

INSTANCE = "django__django-13109"

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
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    if parentLink then\n"
    "      return true\n"
    "    match value with\n"
    "    | none => return true\n"
    "    | some v =>\n"
    "      let mut qs := rows\n"
    "      qs := qs.filter (fun r => r.key == v)\n"
    "      qs := qs.filter (fun r => r.limitOk)\n"
    "      return !qs.isEmpty\n"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the positives whose different impl shape needs an (equally cheap, honest) reproof
# of the byte-identical theorem statement.
_PROOF = (
    "  have helper : ∀ (l : List Row) (p : Row → Bool),\n"
    "      (!(l.filter p).isEmpty) = l.any p := by\n"
    "    intro l p\n"
    "    induction l with\n"
    "    | nil => rfl\n"
    "    | cons a as ih =>\n"
    "      simp only [List.filter_cons, List.any_cons]\n"
    "      by_cases h : p a = true\n"
    "      · simp [h]\n"
    "      · simp only [Bool.not_eq_true] at h\n"
    "        simp [h, ih]\n"
    "  intro parentLink value rows\n"
    "  unfold problem_spec_validateReference implementation_validateReference existsValid\n"
    "  simp only [Id.run, bind, pure]\n"
    "  cases parentLink <;> simp only [Bool.false_eq_true, if_false, if_true]\n"
    "  cases value with\n"
    "  | none => rfl\n"
    "  | some v =>\n"
    "    show (!(List.filter (fun r => r.limitOk) (List.filter (fun r => r.key == v) rows)).isEmpty)\n"
    "        = rows.any (fun r => r.key == v && r.limitOk)\n"
    "    rw [List.filter_filter, helper]\n"
    "    have hp : (fun r : Row => r.limitOk && r.key == v)\n"
    "        = (fun r : Row => r.key == v && r.limitOk) := by\n"
    "      funext r; rw [Bool.and_comm]\n"
    "    rw [hp]\n"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-pure-map: a structurally different CORRECT impl written as a pure functional
# `if`/`match` returning `existsValid v rows` directly (no `Id.run do`, no `let mut`,
# no `Array`/`filter` pipeline). It is DEFINITIONALLY the spec's RHS, so the theorem
# statement is byte-identical and its proof is reproven honestly with `rfl` inside
# proof-start/proof-end — no new axiom/lemma/sorry, just the cheapest tactic for the
# new shape. If it FAILS => SPEC-TOO-STRONG (the postcondition bound to the monadic
# filter-pipeline impl shape rather than the behaviour).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_validateReference\n"
        "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
        "  if parentLink then true\n"
        "  else match value with\n"
        "       | none => true\n"
        "       | some v => existsValid v rows\n",
    ),
    _PROOF,
    "  intro parentLink value rows\n"
    "  rfl\n",
)

# pos-reorder-filters: structurally different but behaviourally identical — the two
# sequential filters (`key == v`, then `limitOk`) are applied in the OPPOSITE order.
# The result equals the frozen impl's on every input (filter composition commutes),
# and the theorem STATEMENT is byte-identical. Reproven with the same helper lemma,
# differing only in the final `show`/`rw` orientation (no `Bool.and_comm` needed
# because the surviving conjunction is already in the spec's order). No new
# axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit to the
# exact filter order).
_POS_REORDER = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_validateReference\n"
        "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
        "  Id.run do\n"
        "    if parentLink then\n"
        "      return true\n"
        "    match value with\n"
        "    | none => return true\n"
        "    | some v =>\n"
        "      let mut qs := rows\n"
        "      qs := qs.filter (fun r => r.limitOk)\n"
        "      qs := qs.filter (fun r => r.key == v)\n"
        "      return !qs.isEmpty\n",
    ),
    _PROOF,
    "  have helper : ∀ (l : List Row) (p : Row → Bool),\n"
    "      (!(l.filter p).isEmpty) = l.any p := by\n"
    "    intro l p\n"
    "    induction l with\n"
    "    | nil => rfl\n"
    "    | cons a as ih =>\n"
    "      simp only [List.filter_cons, List.any_cons]\n"
    "      by_cases h : p a = true\n"
    "      · simp [h]\n"
    "      · simp only [Bool.not_eq_true] at h\n"
    "        simp [h, ih]\n"
    "  intro parentLink value rows\n"
    "  unfold problem_spec_validateReference implementation_validateReference existsValid\n"
    "  simp only [Id.run, bind, pure]\n"
    "  cases parentLink <;> simp only [Bool.false_eq_true, if_false, if_true]\n"
    "  cases value with\n"
    "  | none => rfl\n"
    "  | some v =>\n"
    "    show (!(List.filter (fun r => r.key == v) (List.filter (fun r => r.limitOk) rows)).isEmpty)\n"
    "        = rows.any (fun r => r.key == v && r.limitOk)\n"
    "    rw [List.filter_filter, helper]\n",
)


# admiss-ground-hidden: the ADMISSIBILITY lane. The impl is the FROZEN one — this case
# defends the OBLIGATION, not an impl shape. Two `have`s are prepended to the frozen
# tactic body, inside proof-start/proof-end, before the frozen script closes the
# byte-identical theorem verbatim:
#   * `_ground` discharges the obligation AT a single concrete F2P-shaped input — a
#     reference to a target record that IS genuinely stored and eligible but that the
#     target kind's default presentation HIDES (`defaultVisible := false`) — by
#     evaluation (`decide`).
#   * `_verdict` then EVALUATES the modeled outcome at that same input to the concrete
#     literal `true`. This second `have` is what makes the case non-vacuous: the
#     `_ground` discharge alone would read identically if the input landed in a
#     short-circuit branch (`parentLink`/null), since the spec pins `result` to a term
#     over the same inputs either way. Pinning the verdict to `true` shows the ground
#     instance really lands in the EXISTENCE-CHECK branch and is satisfied there.
# If this FAILS => the modeled obligation is unsatisfiable at exactly the input class
# the real behaviour is about — the total-carrier analogue of PRECOND-TOO-STRONG.
# Nothing is assumed: no new declaration, no sorry/axiom, statement byte-identical.
_ADM_GROUND = _swap(
    _BASE,
    _PROOF,
    "  have _ground : problem_spec_validateReference false (some 3)\n"
    "      [{ key := 3, defaultVisible := false, limitOk := true }]\n"
    "      (implementation_validateReference false (some 3)\n"
    "        [{ key := 3, defaultVisible := false, limitOk := true }]) := by\n"
    "    unfold problem_spec_validateReference implementation_validateReference existsValid\n"
    "    decide\n"
    "  have _verdict : implementation_validateReference false (some 3)\n"
    "      [{ key := 3, defaultVisible := false, limitOk := true }] = true := by\n"
    "    unfold implementation_validateReference\n"
    "    decide\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

def _riv(impl_body):
    return _swap(_BASE, _IMPL, impl_body)


# weak-prepatch-default: THE ACTUAL PRE-PATCH BUG. Before checking key/eligibility it
# first restricts to records the DEFAULT presentation keeps (`defaultVisible`),
# instead of scanning the underlying stored collection in full. Correct on every
# reference whose target is default-visible, WRONG on a genuinely-stored target the
# default presentation hides. Attacks sub-obligation E-vis (the `defaultVisible`
# binder).
_RIV_PREPATCH = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    if parentLink then\n"
    "      return true\n"
    "    match value with\n"
    "    | none => return true\n"
    "    | some v =>\n"
    "      let mut qs := rows\n"
    "      qs := qs.filter (fun r => r.defaultVisible)\n"
    "      qs := qs.filter (fun r => r.key == v)\n"
    "      qs := qs.filter (fun r => r.limitOk)\n"
    "      return !qs.isEmpty\n"
)

# weak-ignore-choice: drops the eligibility (`limitOk`) filter — decides on
# key-membership alone. Accepts a stored record whose key matches but which fails the
# standing choice constraint. Attacks sub-obligation E-lim.
_RIV_IGNORE_CHOICE = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    if parentLink then\n"
    "      return true\n"
    "    match value with\n"
    "    | none => return true\n"
    "    | some v =>\n"
    "      let mut qs := rows\n"
    "      qs := qs.filter (fun r => r.key == v)\n"
    "      return !qs.isEmpty\n"
)

# weak-ignore-key: drops the key-match filter — decides on eligibility alone. Accepts
# a reference to `v` whenever ANY eligible record exists, even one carrying a
# DIFFERENT key. Attacks sub-obligation E-key (the `key` binder).
_RIV_IGNORE_KEY = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    if parentLink then\n"
    "      return true\n"
    "    match value with\n"
    "    | none => return true\n"
    "    | some v =>\n"
    "      let mut qs := rows\n"
    "      qs := qs.filter (fun r => r.limitOk)\n"
    "      return !qs.isEmpty\n"
)

# weak-skip-head: PARTIAL-DOMAIN / off-by-one. Scans `rows.tail`, never inspecting the
# first stored record. Correct for every reference not uniquely matched at the head,
# WRONG when the only eligible matching record sorts to that head position. Attacks
# sub-obligation E-all (every record inspected).
_RIV_SKIP_HEAD = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    if parentLink then\n"
    "      return true\n"
    "    match value with\n"
    "    | none => return true\n"
    "    | some v =>\n"
    "      let mut qs := rows.tail\n"
    "      qs := qs.filter (fun r => r.key == v)\n"
    "      qs := qs.filter (fun r => r.limitOk)\n"
    "      return !qs.isEmpty\n"
)

# weak-always-return: the cheapest "forgot to do the work" baseline that never
# rejects — every reference is declared sound. Accepts a reference with no matching
# stored record at all. Attacks clause E (absent case).
_RIV_ALWAYS_RETURN = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  true\n"
)

# weak-always-raise: the cheapest baseline that always rejects — no reference is ever
# sound. Rejects a reference with a genuine eligible matching record. Attacks clause E
# (present case).
_RIV_ALWAYS_RAISE = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  false\n"
)

# weak-ignore-parentlink: drops the parent-link early-exit gate and runs the existence
# check unconditionally. Correct whenever an existence check would have agreed, WRONG
# on a parent-link reference whose value has no matching stored record. Attacks
# gate G1 (the `parentLink` binder).
_RIV_IGNORE_PARENTLINK = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    match value with\n"
    "    | none => return true\n"
    "    | some v =>\n"
    "      let mut qs := rows\n"
    "      qs := qs.filter (fun r => r.key == v)\n"
    "      qs := qs.filter (fun r => r.limitOk)\n"
    "      return !qs.isEmpty\n"
)

# weak-ignore-null: mishandles the null gate — a null (absent) reference is declared
# UNSOUND instead of sound outright. Attacks gate G2 (the `value = none` binder).
_RIV_IGNORE_NULL = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    if parentLink then\n"
    "      return true\n"
    "    match value with\n"
    "    | none => return false\n"
    "    | some v =>\n"
    "      let mut qs := rows\n"
    "      qs := qs.filter (fun r => r.key == v)\n"
    "      qs := qs.filter (fun r => r.limitOk)\n"
    "      return !qs.isEmpty\n"
)


# weak-zero-as-null: conflates a FALSY referenced value with an ABSENT one — treats
# `some 0` as if the reference were null and declares it sound outright, skipping the
# existence check. Correct on every non-zero referenced value, WRONG on a reference to
# the key value 0 that no stored record carries. Attacks clause E on a sub-domain no
# other case reaches: every other rival/witness here is stated at a NON-ZERO referenced
# value, so without this the "which values get an existence check" boundary is pinned
# only away from zero.
_RIV_ZERO_AS_NULL = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    if parentLink then\n"
    "      return true\n"
    "    match value with\n"
    "    | none => return true\n"
    "    | some v =>\n"
    "      if v == 0 then\n"
    "        return true\n"
    "      let mut qs := rows\n"
    "      qs := qs.filter (fun r => r.key == v)\n"
    "      qs := qs.filter (fun r => r.limitOk)\n"
    "      return !qs.isEmpty\n"
)

# weak-all-not-any: swaps the QUANTIFIER — demands that EVERY stored record match the
# referenced value and be eligible, instead of that SOME record does. Agrees with the
# spec on collections of at most one record (which is what most other witnesses here
# use), and is WRONG as soon as a second, non-matching record is also stored: a genuine
# matching record no longer suffices. Attacks clause E's existential force directly.
_RIV_ALL_NOT_ANY = _riv(
    "def implementation_validateReference\n"
    "    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=\n"
    "  Id.run do\n"
    "    if parentLink then\n"
    "      return true\n"
    "    match value with\n"
    "    | none => return true\n"
    "    | some v =>\n"
    "      return rows.all (fun r => r.key == v && r.limitOk)\n"
)


# --- witnesses ---------------------------------------------------------------------
# Each witness states `¬ problem_spec_validateReference … (impl …)` at concrete
# literal inputs, unfolds spec + impl + existsValid, and closes by `decide` (the
# carrier is fully transparent — three `Nat`/`Bool` fields — so no opaque term, no
# hypothesis binder). It ELABORATES against the rival (which returns the wrong verdict
# there) and FAILS on gold (which satisfies the spec at every input). Verified by hand
# against both faces with scripts/lean_verify.sh before shipping.

def _wit(pl, val, rows):
    return (
        "example :\n"
        f"    ¬ problem_spec_validateReference {pl} {val} {rows}\n"
        f"      (implementation_validateReference {pl} {val} {rows}) := by\n"
        "  unfold problem_spec_validateReference implementation_validateReference existsValid\n"
        "  decide"
    )


_R_HIDDEN = "{ key := 3, defaultVisible := false, limitOk := true }"
_R_VISIBLE = "{ key := 3, defaultVisible := true, limitOk := true }"
_R_NOLIMIT = "{ key := 3, defaultVisible := true, limitOk := false }"
_R_OTHERKEY = "{ key := 5, defaultVisible := true, limitOk := true }"

# E-vis: a stored record matching `v=3` and eligible, but hidden by the default
# presentation. gold => sound (scans full collection); prepatch rival => unsound.
_WIT_PREPATCH = _wit("false", "(some 3)", f"[{_R_HIDDEN}]")

# E-lim: a stored record matching `v=3` but NOT eligible. gold => unsound;
# ignore-choice rival (drops eligibility) => sound.
_WIT_IGNORE_CHOICE = _wit("false", "(some 3)", f"[{_R_NOLIMIT}]")

# E-key: an eligible stored record carrying a DIFFERENT key (5, not the referenced 3).
# gold => unsound; ignore-key rival (drops key match) => sound.
_WIT_IGNORE_KEY = _wit("false", "(some 3)", f"[{_R_OTHERKEY}]")

# E-all: two records; the only eligible match sorts to the HEAD position, followed by
# a non-matching record. gold => sound; skip-head rival (scans the tail) => unsound.
# Distinct input point from every other witness (two-record collection, match at head).
_WIT_SKIP_HEAD = _wit(
    "false",
    "(some 3)",
    f"[{_R_VISIBLE}, {{ key := 1, defaultVisible := true, limitOk := true }}]",
)

# E (absent): empty stored collection. gold => unsound; always-return rival => sound.
_WIT_ALWAYS_RETURN = _wit("false", "(some 3)", "[]")

# E (present): a stored record matching `v=3` and eligible. gold => sound;
# always-raise rival => unsound.
_WIT_ALWAYS_RAISE = _wit("false", "(some 3)", f"[{_R_VISIBLE}]")

# G1: parent-link reference (parentLink=true) with an empty collection, so an
# existence check would fail. gold => sound outright (gate fires);
# ignore-parentlink rival => runs the check and returns unsound.
_WIT_IGNORE_PARENTLINK = _wit("true", "(some 3)", "[]")

# G2: null (absent) reference. gold => sound outright; ignore-null rival => unsound.
_WIT_IGNORE_NULL = _wit("false", "none", "[]")

# E (falsy value): a reference to the key value 0 that NO stored record carries.
# gold => unsound (empty collection, nothing matches); zero-as-null rival => sound
# (it mistook the falsy value for an absent one). The only witness stated at the
# referenced value 0.
_WIT_ZERO_AS_NULL = _wit("false", "(some 0)", "[]")

# E (existential force): two stored records — a NON-matching record first, then the
# eligible match for `v=3`. gold => sound (SOME record matches); all-not-any rival =>
# unsound (not EVERY record matches). Discriminates `any` from `all`, which a
# single-record collection cannot.
#
# The match sits at index 1, NOT at the head, and that ordering is deliberate: the
# mirror-image collection (match first, non-match second) is also refuted by the
# skip-head rival, so a witness stated there would not attribute the rejection to the
# quantifier as opposed to the head-skip axis. MEASURED: this witness does NOT
# elaborate against the skip-head rival (its tail scan still finds the index-1 match),
# so this input point isolates clause E's existential force alone and is distinct from
# every other witness point in the battery.
_WIT_ALL_NOT_ANY = _wit(
    "false",
    "(some 3)",
    f"[{{ key := 1, defaultVisible := true, limitOk := true }}, {_R_VISIBLE}]",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-pure-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure functional "
            "`if`/`match` returning the existence-check helper directly (no `Id.run "
            "do`, no `let mut`, no filter pipeline). It is definitionally the spec's "
            "RHS on every input; the theorem STATEMENT is byte-identical and its "
            "proof is reproven honestly with `rfl` — no new axiom/lemma/sorry, just "
            "the cheapest tactic for the new shape. If it FAILS => SPEC-TOO-STRONG "
            "(the postcondition bound to the monadic filter-pipeline impl shape "
            "rather than the behaviour)."
        ),
    },
    {
        "id": "pos-reorder-filters",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally different but behaviourally identical: the two sequential "
            "filters (key-match, then eligibility) are applied in the OPPOSITE order, "
            "which composes to the same surviving set on every input. The theorem "
            "STATEMENT is byte-identical; reproven with the same helper lemma, "
            "differing only in the final `show`/`rw` orientation (no `Bool.and_comm` "
            "needed as the surviving conjunction is already in the spec's order). No "
            "new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to the exact filter order)."
        ),
    },

    {
        "id": "admiss-ground-hidden",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_GROUND,
        "rationale": (
            "the ADMISSIBILITY lane: the obligation is discharged at a single ground "
            "F2P-shaped input — a reference to a target record that IS genuinely stored "
            "and eligible but that the target kind's default presentation HIDES "
            "(`defaultVisible := false`) — by evaluation, as a `have`, and then the "
            "frozen obligation is closed verbatim by the frozen script. A second `have` "
            "EVALUATES the modeled outcome at that same input to the concrete literal "
            "`true`, which is what makes the case non-vacuous: the ground discharge "
            "alone would read identically if the input landed in a short-circuit branch "
            "(parent-link or null), since the spec pins `result` to a term over the same "
            "inputs either way, so pinning the verdict shows the instance really lands "
            "in the existence-check branch and is SATISFIED there. If it FAILS => the "
            "modeled obligation is unsatisfiable at exactly the input class the real "
            "behaviour is about — the total-carrier analogue of PRECOND-TOO-STRONG, "
            "which is the third direction this gate exists to test and which no "
            "soundness or uniqueness case reaches. Nothing is assumed: no new "
            "declaration, no sorry/axiom, the theorem statement is byte-identical, and "
            "the impl region is the FROZEN one (this case defends the obligation, not an "
            "impl shape). Ports nagini's admiss-reads."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-prepatch-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "restricts to the records the default presentation keeps before checking "
            "key/eligibility, instead of scanning the underlying stored collection in "
            "full — this IS the pre-patch behaviour. Its faithful real patch is the "
            "UNCHANGED code, under which a reference to a genuinely-stored target that "
            "the default presentation hides is rejected as invalid. That is exactly "
            "what the F2P tests (test_FK_validates_using_base_manager, "
            "test_validate_foreign_key_to_model_with_overridden_manager) assert must "
            "be VALID, so they FAIL. It would NOT resolve — this is the very bug the "
            "patch fixes (G-DIFF: the spec's whole purpose is sensing this "
            "presentation-independence)."
        ),
        "rationale": (
            "REJECTED by sub-obligation E-vis. For a stored record matching the "
            "referenced value and eligible but with `defaultVisible = false`, the "
            "spec's `existsValid v rows` is true (it scans the full collection) while "
            "the rival returns false (it dropped the hidden record first). Witness is "
            "the discriminating archived-but-stored record; `decide` closes it. This "
            "varies the `defaultVisible` binder (false), which every other witness "
            "holds at true. If it VERIFIES => SPEC-TOO-WEAK (presentation-independence "
            "unpinned)."
        ),
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "weak-ignore-choice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_CHOICE,
        "refinement": (
            "decides on key-membership alone, dropping the standing choice-constraint "
            "filter. Its faithful real patch is a fix that consults the full stored "
            "collection but omits the eligibility narrowing; it would accept a stored "
            "record whose key matches yet violates the field's choice constraint — a "
            "reference the gold rejects. The regression/P2P behaviour exercising the "
            "choice constraint would break, so it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by sub-obligation E-lim. For a stored record matching the "
            "referenced value but with `limitOk = false`, the spec is false (no "
            "eligible match) while the rival returns true (it dropped the eligibility "
            "filter). Witness varies the `limitOk` binder (false), which every other "
            "witness holds at true; `decide` closes it. If it VERIFIES => "
            "SPEC-TOO-WEAK (the eligibility conjunct unpinned)."
        ),
        "witness": _WIT_IGNORE_CHOICE,
    },
    {
        "id": "weak-ignore-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_KEY,
        "refinement": (
            "decides on eligibility alone, dropping the key-match filter, so a "
            "reference to `v` is accepted whenever ANY eligible stored record exists, "
            "even one carrying a different key value. Its faithful real patch is a fix "
            "that fails to filter by the referenced value; it would accept a dangling "
            "reference whose value matches no stored record while some unrelated "
            "record happens to be eligible. The accept/reject contract the validation "
            "tests pin (an absent key must be rejected) breaks, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by sub-obligation E-key. For an eligible stored record carrying "
            "key 5 while the reference is to 3, the spec is false (no record with the "
            "referenced key) while the rival returns true (it dropped the key match). "
            "Witness varies the `key` binder (a non-matching key), which the other "
            "value-domain witnesses hold at the matching value; `decide` closes it. If "
            "it VERIFIES => SPEC-TOO-WEAK (the key-match conjunct unpinned)."
        ),
        "witness": _WIT_IGNORE_KEY,
    },
    {
        "id": "weak-skip-head",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIP_HEAD,
        "refinement": (
            "an off-by-one that never inspects the first stored record. Its faithful "
            "real patch is an existence test whose scan skips the head of the "
            "collection; it would reject a reference whose only eligible matching "
            "record sorts to that head position while passing on every other input — a "
            "true PARTIAL-DOMAIN break (the stored record inspected first), not a "
            "blanket wrong impl. It would NOT resolve on that input class."
        ),
        "rationale": (
            "REJECTED by sub-obligation E-all (every stored record inspected). Witness "
            "uses a two-record collection whose only eligible match is at the HEAD, "
            "followed by a non-matching record: the spec is true (the head matches) "
            "while the rival returns false (it scans only the tail). Distinct input "
            "point from every other witness — the only one with the match at index 0, "
            "varying the `rows` length/order binder (weak-all-not-any deliberately "
            "states the MIRROR ordering, match at index 1, so the two do not share a "
            "point). `decide` closes it. "
            "If it VERIFIES => SPEC-TOO-WEAK on the head sub-domain."
        ),
        "witness": _WIT_SKIP_HEAD,
    },
    {
        "id": "weak-always-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_RETURN,
        "refinement": (
            "the cheapest 'forgot to do the work' baseline that declares every "
            "reference sound. Its faithful real patch is a validate that never "
            "rejects; it would accept a dangling reference to a value stored by no "
            "record at all, failing every reject-expecting validation test. It would "
            "NOT resolve. Cheap supporting baseline with a genuine refinement."
        ),
        "rationale": (
            "REJECTED by clause E (absent case). On a reference whose value matches no "
            "stored record (empty collection), the spec is false but the rival returns "
            "true. Witness uses the empty collection; `decide` closes it. If it "
            "VERIFIES => SPEC-TOO-WEAK (the reject condition unpinned)."
        ),
        "witness": _WIT_ALWAYS_RETURN,
    },
    {
        "id": "weak-always-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_RAISE,
        "refinement": (
            "the cheapest baseline that declares every reference unsound. Its faithful "
            "real patch is a validate that always rejects; it would reject a reference "
            "with a genuine eligible matching stored record, failing every "
            "accept-expecting test (including the F2P archived-record validation). It "
            "would NOT resolve. Cheap supporting baseline with a genuine refinement."
        ),
        "rationale": (
            "REJECTED by clause E (present case). On a reference with an eligible "
            "matching stored record the spec is true but the rival returns false. "
            "Witness uses a single matching, eligible, visible record; `decide` closes "
            "it. If it VERIFIES => SPEC-TOO-WEAK (the accept condition unpinned)."
        ),
        "witness": _WIT_ALWAYS_RAISE,
    },
    {
        "id": "weak-ignore-parentlink",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_PARENTLINK,
        "refinement": (
            "drops the parent-link early-exit gate and runs the existence check "
            "unconditionally. Its faithful real patch is a validate that lost the "
            "parent-link short-circuit; a parent-linking reference whose value has no "
            "matching stored record would be rejected, whereas such references must "
            "always be sound. The parent-link regression behaviour breaks, so it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by gate G1. With `parentLink = true` the spec is true outright "
            "regardless of the collection, but the rival runs the check and returns "
            "false on an empty collection. Witness is the only one varying the "
            "`parentLink` binder to true; `decide` closes it. If it VERIFIES => "
            "SPEC-TOO-WEAK (the parent-link gate unpinned)."
        ),
        "witness": _WIT_IGNORE_PARENTLINK,
    },
    {
        "id": "weak-ignore-null",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IGNORE_NULL,
        "refinement": (
            "mishandles the null gate: a null (absent) reference is declared unsound "
            "instead of sound outright. Its faithful real patch is a validate that "
            "rejects null references; a record with no reference value set would fail "
            "validation, whereas a null reference must be sound. The null-handling "
            "regression behaviour breaks, so it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by gate G2. With `value = none` the spec is true outright, but "
            "the rival returns false. Witness is the only one varying the `value` "
            "binder to `none`; `decide` closes it. If it VERIFIES => SPEC-TOO-WEAK "
            "(the null gate unpinned)."
        ),
        "witness": _WIT_IGNORE_NULL,
    },
    {
        "id": "weak-zero-as-null",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ZERO_AS_NULL,
        "refinement": (
            "conflates a FALSY referenced value with an ABSENT one: a reference "
            "carrying the key value 0 takes the null short-circuit and is declared "
            "sound without any existence check. Its faithful real patch is a fix that "
            "tests the referenced value for truthiness rather than for being unset "
            "before deciding whether to query at all — a classic conflation on this "
            "surface. It would accept a dangling reference to a key value 0 that no "
            "stored record carries, so the reject-expecting validation behaviour "
            "breaks on that sub-domain and it would NOT resolve. A true PARTIAL-DOMAIN "
            "near-miss: it agrees with gold on every other referenced value."
        ),
        "rationale": (
            "REJECTED by clause E on the falsy-value sub-domain. For a reference to 0 "
            "against an empty stored collection the spec is false (nothing matches) "
            "while the rival returns true (it skipped the check). This is the ONLY "
            "case varying the referenced value to 0 — every other rival and witness "
            "here is stated at a non-zero value, so without it the boundary between "
            "'takes the null gate' and 'runs the existence check' is pinned only away "
            "from zero. `decide` closes it. If it VERIFIES => SPEC-TOO-WEAK (the null "
            "gate would be unpinned against value-truthiness conflation)."
        ),
        "witness": _WIT_ZERO_AS_NULL,
    },
    {
        "id": "weak-all-not-any",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALL_NOT_ANY,
        "refinement": (
            "swaps the QUANTIFIER: it demands that EVERY stored record of the target "
            "kind match the referenced value and be eligible, rather than that SOME "
            "record does. Its faithful real patch is an existence test written as a "
            "universal rather than an existential over the candidate collection. It "
            "would reject a perfectly sound reference whenever the target kind also "
            "stores any unrelated record — i.e. on essentially every realistic table — "
            "so the accept-expecting behaviour (including the F2P references) breaks "
            "and it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause E's existential force. Witness stores a NON-matching "
            "record first and the eligible match for the referenced value SECOND: the "
            "spec is true (some record matches) while the rival returns false (not "
            "every record does). A one-record collection cannot tell `any` from `all` "
            "at a true point, which is why this needs its own two-record witness; it "
            "pins the quantifier itself rather than any single conjunct. Stating it "
            "with the match at index 1 rather than index 0 is what keeps it a distinct "
            "input point from weak-skip-head: MEASURED, this witness does NOT "
            "elaborate against the skip-head rival, so its rejection is attributable "
            "to the quantifier and not to the head-skip axis. `decide` closes "
            "it. If it VERIFIES => SPEC-TOO-WEAK (the existence check could be read "
            "universally)."
        ),
        "witness": _WIT_ALL_NOT_ANY,
    },
]


# No @ContractOnly axioms are consumed by this spec: there is NO opaque callee. The
# presentation-selection decision is modeled DEEPLY as whether the scan honours each
# record's `defaultVisible` flag, over a fully transparent carrier. The axiom lane is
# therefore empty here and belongs to G-AX regardless.
AXIOM_TESTS = []
