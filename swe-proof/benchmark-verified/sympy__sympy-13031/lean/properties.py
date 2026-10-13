"""properties.py — G-PBT falsification battery for sympy__sympy-13031 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves or discharges
a ground instance, inside a ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and every ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (two total joins over a two-operand domain, `self` and
`other`, each modeled as a ``Mat`` carrying row/column dimensions, a total value
accessor ``get i j``, and a ``kind`` tag for the concrete matrix class):

  hJoin self other = result           -- place `other` to the RIGHT of `self`
    result.kind = self.kind
    ∧ (self.cols = 0 → result has other's shape and entries)
    ∧ (self.cols ≠ 0 → result.rows = self.rows
                     ∧ result.cols = self.cols + other.cols       -- THE PIN
                     ∧ entries read from self on the left, other on the right)

  vJoin self other = result           -- place `other` BENEATH `self`
    result.kind = self.kind
    ∧ (self.rows = 0 → result has other's shape and entries)
    ∧ (self.rows ≠ 0 → result.rows = self.rows + other.rows       -- THE PIN
                     ∧ result.cols = self.cols
                     ∧ entries read from self on top, other below)

  The two obligations are exact transposes. Each has THREE independent top-level
  clauses — the kind conjunct, the null-operand arm, and the general-operand arm
  — and the load-bearing content is the general arm's ACCUMULATION PIN: the
  result dimension along the joined axis is the SUM of the two operands'
  dimensions, grounded structurally in the inputs (a plain integer sum), NOT
  pinned to any opaque oracle. The bug this surface defends against silently
  collapses the accumulated dimension to `other`'s alone whenever `self` is
  null-dimensioned, dropping `self`'s contribution.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because its operands are held at fractional
    (read-only) permission, so a rival that STORES into an operand to fabricate
    the accumulated count is rejected for insufficient permission rather than a
    wrong value. Lean is referentially transparent: the two operands are plain
    immutable values, there is no half-permission to violate and no aliasing to
    exploit, so this class has NO expressible instance here. No substitute is
    fabricated. The accumulation is instead attacked directly by the reset and
    forget rivals below, which is where the real bug lives.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The bundle declares NO ``opaque`` / no
    ``axiom`` (the joins are modeled deeply: every output entry is read off one
    of the two input accessors at an index computed from the inputs). There is
    no answer key an impl could echo without doing the work, so this class is
    N/A on this carrier; the honest analogue is the cheapest-correct POSITIVE
    CONTROL below.

  * PARTIAL-DOMAIN (pre-fix reset) — APPLIES, load-bearing. The pre-fix guard
    fires on ANY null-dimensioned operand and returns a result shaped like
    `other` alone, discarding `self`'s accumulated dimension. It coincides with
    gold exactly when `self` contributes nothing and diverges precisely on the
    F2P observable (a run of null-dimensioned operands whose OTHER dimension
    still accumulates), so it is refuted there — attacked on BOTH obligations
    (``partial-reset-hjoin`` / ``partial-reset-vjoin``) to confirm the symmetric
    spec is equally tight.

  * PARTIAL-DOMAIN (forget the other operand's dimension) and CLASS-DROP — APPLY.
    A join that omits `other`'s dimension from the sum on the general path, and
    a join that returns a result of `other`'s class instead of `self`'s, each
    violate a distinct clause on a distinct sub-domain and are refuted with
    witnesses at distinct input points.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
concrete input; each was built (against the rival) and rebuilt (against the
frozen solution) to confirm it HOLDS of its rival and FAILS on gold (so it
discriminates rather than asserting a tautology). Every witness uses only
concrete literal ``Mat`` values (no head binders), so the arithmetic clashes are
closed by ``decide`` after destructuring the relevant clause; nothing is assumed.

BINDER / CLAUSE COVERAGE. Both input binders (`self`, `other`) are varied across
the reject witnesses — the rivals are refuted at differing operand shapes and at
differing `kind` tags, so neither binder is pinned to a single value.

Each obligation has three top-level clauses, and the two implication arms each
carry three CONJUNCTS (rows, cols, entries) — SEVEN leaf positions per
obligation. Every one of the fourteen is attacked by its own rival at its own
input point:

  * KIND conjunct                  — class-drop rivals (h + v)
  * null-operand arm / joined axis — null-arm-drop rivals (h: cols, v: rows)
  * null-operand arm / off axis    — null-arm-keep-rows (h),
                                     null-arm-keep-cols (v)
  * null-operand arm / entries     — zero-entries rivals (h + v)
  * general arm / ACCUMULATION PIN — reset + forget rivals (h + v)
  * general arm / OFF-AXIS conjunct— gen-arm-offaxis rivals (h: rows, v: cols)
  * general arm / entries          — general-arm-entry rivals (h + v)

NB on the general arm's OFF-AXIS conjunct (`result.rows = self.rows` for hJoin,
`result.cols = self.cols` for vJoin). It is attacked by its own rival, NOT
delegated to the positive control. The tempting argument for delegating it —
that any impl which gets the joined-axis dimension and the entries right and
the off-axis one wrong is a reshape of the reset rival — is FALSE, and is
refuted by construction below: ``weak-gen-arm-offaxis-hjoin`` perturbs only the
off-axis row count on the general path, coincides with gold on the joined axis,
the entries, the kind tag AND the whole null-operand arm, and is nonetheless
refuted by its own witness at its own input point. Nothing about it collapses
into the reset rival, whose defect is on a different arm entirely.

``pts`` = 15 distinct input points across the two obligations (8 hJoin,
7 vJoin).

DOMAIN RESTRICTION (recorded, not defended — see assessment). Each obligation's
precondition binder (`self.cols = 0 ∨ self.rows = other.rows`, symmetric for
vJoin) EXCLUDES the shape-incompatible operand pairs. On that excluded region the
postcondition constrains nothing, so an impl may return an arbitrary result there
and still discharge the obligation; this was confirmed with a real build (a rival
returning a garbage shape and kind on exactly that region VERIFIES). The nagini
sibling pins that region instead of excluding it, so the behavior is defended
there and NOT here. No rival can close this on the frozen spec — the obligation
would have to carry the excluded region (e.g. an `Except`/`Option` result), which
is a change to the frozen artifact and outside this lane. Recorded as a spec
finding rather than papered over with a case that cannot exist.

DIVERGENCE / NON-TERMINATION CLASS — VACUOUS, demonstrated by build. The frozen
bundle sets no `loom.semantics.termination` option at all: both obligations are
plain total Lean `def`s, so a rival whose body recurses without a decreasing
measure is refused at DEFINITION time (`fail to show termination for
implementation_hJoin ... no parameters suitable for structural recursion`), not
at proof time. Confirmed with a real build of exactly such a rival: the module
fails, but so does its witness file, for the same definitional error rather than
for anything about the spec — the rival never becomes a well-formed impl, so
there is nothing for a witness to refute and no shippable reject case here. This
is a carrier property, not a spec gap: the class cannot be instantiated rather
than being left untested.

OMITTED nagini cases (see assessment):

  * the frame/permission-mutation rival — VACUOUS on a referentially-transparent
    carrier (immutable operand values, no fractional permission to violate);
  * the control-flow / no-raise rival — its subject matter is the excluded
    region described above. Expressible on this carrier IN PRINCIPLE (an
    `Except`/`Option` return would model the raise) but NOT against this frozen
    spec, which has no clause for it. Escalated, not silently dropped;
  * the AXIOM_TESTS lane — this bundle declares no axiom / deep-model reference
    (G-AX skips) and the axiom lane is not this gate's job.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13031"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body of each obligation, and the frozen proof bodies, so
# every replacement lands entirely inside the region it means to edit.
_IMPL_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "    return concatCols (zeroColsMat other.rows self.kind) other\n"
    "  return concatCols self other"
)
_IMPL_V = (
    "def implementation_vJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
    "    return concatRows (zeroRowsMat other.cols self.kind) other\n"
    "  return concatRows self other"
)

# The frozen hJoin proof body opening (used to splice the admissibility ground
# instance in). The `intro self other _hpre` line opens BOTH proofs; the longer
# anchor below is unique to hJoin.
_PROOF_H_OPEN = (
    "  intro self other _hpre\n"
    "  have himpl : implementation_hJoin self other =\n"
    "      if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "        concatCols (zeroColsMat other.rows self.kind) other\n"
    "      else concatCols self other := by"
)

assert _BASE.count(_IMPL_H) == 1, "hJoin impl region drifted; update _IMPL_H"
assert _BASE.count(_IMPL_V) == 1, "vJoin impl region drifted; update _IMPL_V"
assert _BASE.count(_PROOF_H_OPEN) == 1, "hJoin proof region drifted"


# ===========================================================================
# POSITIVE CONTROL (soundness) — a structurally different but CORRECT variant
# of BOTH joins that MUST verify. The degenerate-normalisation guard on each
# join is commuted (`self.rows ≠ other.rows ∧ self.cols = 0` in place of
# `self.cols = 0 ∧ self.rows ≠ other.rows`; symmetric for vJoin) — an equivalent
# boolean form, same value on every input. The frozen tactic body is retuned to
# the reshaped guard (the `if`-condition in the `himpl` rewrite and the `by_cases`
# predicate are commuted, and the two `h.1`/`h.2` projections and the `⟨_, _⟩`
# reassembly are swapped to match). Statement byte-identical; no new lemma,
# axiom, or assumption token.
# ===========================================================================
def _pos_control():
    src = _BASE
    # --- hJoin: commute the guard in impl + proof ---
    src = _swap(
        src,
        "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
        "    return concatCols (zeroColsMat other.rows self.kind) other\n"
        "  return concatCols self other",
        "  if self.rows ≠ other.rows ∧ self.cols = 0 then\n"
        "    return concatCols (zeroColsMat other.rows self.kind) other\n"
        "  return concatCols self other",
    )
    src = _swap(
        src,
        "  have himpl : implementation_hJoin self other =\n"
        "      if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
        "        concatCols (zeroColsMat other.rows self.kind) other\n"
        "      else concatCols self other := by\n"
        "    unfold implementation_hJoin; simp only [Id.run]; rfl\n"
        "  rw [himpl]\n"
        "  by_cases h : self.cols = 0 ∧ self.rows ≠ other.rows",
        "  have himpl : implementation_hJoin self other =\n"
        "      if self.rows ≠ other.rows ∧ self.cols = 0 then\n"
        "        concatCols (zeroColsMat other.rows self.kind) other\n"
        "      else concatCols self other := by\n"
        "    unfold implementation_hJoin; simp only [Id.run]; rfl\n"
        "  rw [himpl]\n"
        "  by_cases h : self.rows ≠ other.rows ∧ self.cols = 0",
    )
    src = _swap(src, "    · intro hc0; exact absurd h.1 hc0",
                "    · intro hc0; exact absurd h.2 hc0")
    src = _swap(src, "        by_contra hne; exact h ⟨hc0, hne⟩",
                "        by_contra hne; exact h ⟨hne, hc0⟩")
    # --- vJoin: commute the guard in impl + proof ---
    src = _swap(
        src,
        "  if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
        "    return concatRows (zeroRowsMat other.cols self.kind) other\n"
        "  return concatRows self other",
        "  if self.cols ≠ other.cols ∧ self.rows = 0 then\n"
        "    return concatRows (zeroRowsMat other.cols self.kind) other\n"
        "  return concatRows self other",
    )
    src = _swap(
        src,
        "  have himpl : implementation_vJoin self other =\n"
        "      if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
        "        concatRows (zeroRowsMat other.cols self.kind) other\n"
        "      else concatRows self other := by\n"
        "    unfold implementation_vJoin; simp only [Id.run]; rfl\n"
        "  rw [himpl]\n"
        "  by_cases h : self.rows = 0 ∧ self.cols ≠ other.cols",
        "  have himpl : implementation_vJoin self other =\n"
        "      if self.cols ≠ other.cols ∧ self.rows = 0 then\n"
        "        concatRows (zeroRowsMat other.cols self.kind) other\n"
        "      else concatRows self other := by\n"
        "    unfold implementation_vJoin; simp only [Id.run]; rfl\n"
        "  rw [himpl]\n"
        "  by_cases h : self.cols ≠ other.cols ∧ self.rows = 0",
    )
    src = _swap(src, "    · intro hr0; exact absurd h.1 hr0",
                "    · intro hr0; exact absurd h.2 hr0")
    src = _swap(src, "        by_contra hne; exact h ⟨hr0, hne⟩",
                "        by_contra hne; exact h ⟨hne, hr0⟩")
    return src


_POS_CONTROL = _pos_control()


# ===========================================================================
# ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
# (non-vacuous) at an F2P-shaped input rather than only in the abstract: a
# null-row pair whose column dimensions still accumulate (`self` = 0×1, `other`
# = 0×2, so the join's width must be 1 + 2 = 3 on the general-operand arm — the
# case the pre-fix reset breaks). The ground instance is discharged as a `have`
# inside the frozen hJoin tactic body, ahead of the frozen obligation which is
# then closed verbatim. Statement byte-identical; no new declaration/axiom/sorry.
# ===========================================================================
_ADMISS = _swap(
    _BASE,
    _PROOF_H_OPEN,
    "  intro self other _hpre\n"
    "  have _ground : problem_spec_hJoin ⟨0, 1, fun _ _ => 0, 0⟩ "
    "⟨0, 2, fun _ _ => 0, 0⟩\n"
    "      (implementation_hJoin ⟨0, 1, fun _ _ => 0, 0⟩ ⟨0, 2, fun _ _ => 0, 0⟩) "
    ":= by\n"
    "    refine ⟨rfl, ?_, ?_⟩\n"
    "    · intro h; exact absurd h (by decide)\n"
    "    · intro _; exact ⟨rfl, rfl, fun i j => rfl⟩\n"
    "  have himpl : implementation_hJoin self other =\n"
    "      if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "        concatCols (zeroColsMat other.rows self.kind) other\n"
    "      else concatCols self other := by",
)


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals (must reject). Each replaces exactly one
# impl region and carries (a) the refinement argument that its faithful real
# patch would NOT resolve the F2P, and (b) a refutation witness pinning the
# violation at one concrete input.
# ===========================================================================

# Rival impl bodies (each a FULL impl region body for one obligation).

# PRE-FIX RESET on hJoin: the guard fires on ANY null-dimensioned operand
# (`self.rows = 0 ∨ self.cols = 0`) and returns a result shaped like `other`
# (its own dimensions and entries, re-tagged to `self`'s kind), discarding
# `self`'s accumulated column count.
_RESET_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∨ self.cols = 0 then\n"
    "    return { other with kind := self.kind }\n"
    "  return concatCols self other"
)

# FORGET other.cols on hJoin: the normalisation branch is correct but the
# general path returns `self` unchanged, omitting `other`'s columns from the sum.
_FORGET_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "    return concatCols (zeroColsMat other.rows self.kind) other\n"
    "  return self"
)

# CLASS-DROP on hJoin: the shape is correct on the general path but the result
# is tagged with `other`'s kind instead of `self`'s.
_KIND_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "    return concatCols (zeroColsMat other.rows self.kind) other\n"
    "  return { concatCols self other with kind := other.kind }"
)

# PRE-FIX RESET on vJoin (the transpose): the guard fires on any null-dimensioned
# operand and returns a result shaped like `other`, discarding `self`'s
# accumulated row count.
_RESET_V = (
    "def implementation_vJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∨ self.cols = 0 then\n"
    "    return { other with kind := self.kind }\n"
    "  return concatRows self other"
)

# CLASS-DROP on vJoin: shape correct on the general path, result tagged with
# `other`'s kind.
_KIND_V = (
    "def implementation_vJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
    "    return concatRows (zeroRowsMat other.cols self.kind) other\n"
    "  return { concatRows self other with kind := other.kind }"
)

# ZERO-ENTRIES on hJoin's null-operand arm: the shape (dimensions + kind) is
# correct on the normalisation branch, but the entries are left identically 0
# instead of read from the surviving operand — so the null-dimensioned operand
# silently discards the OTHER operand's values while keeping its shape.
_ZERO_ENT_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "    return { zeroColsMat other.rows self.kind with cols := other.cols }\n"
    "  return concatCols self other"
)

# ZERO-ENTRIES on vJoin's null-operand arm (the transpose).
_ZERO_ENT_V = (
    "def implementation_vJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
    "    return { zeroRowsMat other.cols self.kind with rows := other.rows }\n"
    "  return concatRows self other"
)

# NULL-ARM WIDTH DROP on hJoin: the normalisation branch returns the rebuilt
# zero-width receiver WITHOUT joining `other` onto it, so the result keeps the
# receiver's height and kind but is zero-WIDTH — the surviving operand's column
# count is dropped on the very arm that is supposed to adopt its shape.
_NULL_COLS_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "    return zeroColsMat other.rows self.kind\n"
    "  return concatCols self other"
)

# NULL-ARM HEIGHT KEPT on hJoin: the normalisation branch rebuilds the receiver
# at `self`'s OWN height instead of `other`'s, so the result's row count is the
# null receiver's rather than the surviving operand's.
_NULL_ROWS_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "    return concatCols (zeroColsMat self.rows self.kind) other\n"
    "  return concatCols self other"
)

# NULL-ARM HEIGHT DROP on vJoin (the transpose of _NULL_COLS_H): the
# normalisation branch returns the rebuilt zero-height receiver without stacking
# `other` onto it, dropping the surviving operand's row count.
_NULL_ROWS_V = (
    "def implementation_vJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
    "    return zeroRowsMat other.cols self.kind\n"
    "  return concatRows self other"
)

# GENERAL-ARM ENTRY on hJoin: dimensions and kind are exactly right on the
# general path, but EVERY entry is read off the left operand — the right block
# never reads `other`, so the join has the correct shape and the wrong contents.
_GEN_ENT_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "    return concatCols (zeroColsMat other.rows self.kind) other\n"
    "  return ⟨self.rows, self.cols + other.cols, fun i j => self.get i j, "
    "self.kind⟩"
)

# GENERAL-ARM ENTRY on vJoin (the transpose): correct shape and kind, but every
# entry is read off the top operand and the bottom block never reads `other`.
_GEN_ENT_V = (
    "def implementation_vJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
    "    return concatRows (zeroRowsMat other.cols self.kind) other\n"
    "  return ⟨self.rows + other.rows, self.cols, fun i j => self.get i j, "
    "self.kind⟩"
)


# GENERAL-ARM OFF-AXIS on hJoin: the joined axis (width), the entries and the
# kind are all exactly right on the general path, and the null-operand arm is
# untouched, but the result's ROW count is one past the receiver's — the one
# conjunct of the general arm that neither the dimension-pin nor the entry rivals
# perturb.
_GEN_OFFAXIS_H = (
    "def implementation_hJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.cols = 0 ∧ self.rows ≠ other.rows then\n"
    "    return concatCols (zeroColsMat other.rows self.kind) other\n"
    "  return ⟨self.rows + 1, self.cols + other.cols,\n"
    "    fun i j => if j < self.cols then self.get i j "
    "else other.get i (j - self.cols),\n"
    "    self.kind⟩"
)

# GENERAL-ARM OFF-AXIS on vJoin (the transpose): height, entries and kind right
# on the general path, but the result's COLUMN count is one past the receiver's.
_GEN_OFFAXIS_V = (
    "def implementation_vJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
    "    return concatRows (zeroRowsMat other.cols self.kind) other\n"
    "  return ⟨self.rows + other.rows, self.cols + 1,\n"
    "    fun i j => if i < self.rows then self.get i j "
    "else other.get (i - self.rows) j,\n"
    "    self.kind⟩"
)

# NULL-ARM WIDTH KEPT on vJoin (the transpose of _NULL_ROWS_H): the
# normalisation branch rebuilds the receiver at the RECEIVER's own width instead
# of the surviving operand's, so the result's column count is the null
# receiver's rather than the operand whose shape it is adopting.
_NULL_COLS_V = (
    "def implementation_vJoin (self other : Mat) : Mat := Id.run do\n"
    "  if self.rows = 0 ∧ self.cols ≠ other.cols then\n"
    "    return concatRows (zeroRowsMat self.cols self.kind) other\n"
    "  return concatRows self other"
)


def _wit_hjoin_pin(s, o):
    """Refute a hJoin rival on the general arm's column PIN at concrete inputs."""
    return (
        f"example : ¬ problem_spec_hJoin {s} {o}\n"
        f"    (implementation_hJoin {s} {o}) := by\n"
        "  rintro ⟨-, -, hne⟩\n"
        "  obtain ⟨-, hc, -⟩ := hne (by decide)\n"
        "  exact absurd hc (by decide)"
    )


def _wit_hjoin_kind(s, o):
    """Refute a hJoin rival on the kind conjunct at concrete inputs."""
    return (
        f"example : ¬ problem_spec_hJoin {s} {o}\n"
        f"    (implementation_hJoin {s} {o}) := by\n"
        "  rintro ⟨hk, -, -⟩\n"
        "  exact absurd hk (by decide)"
    )


def _wit_vjoin_pin(s, o):
    """Refute a vJoin rival on the general arm's row PIN at concrete inputs."""
    return (
        f"example : ¬ problem_spec_vJoin {s} {o}\n"
        f"    (implementation_vJoin {s} {o}) := by\n"
        "  rintro ⟨-, -, hne⟩\n"
        "  obtain ⟨hr, -, -⟩ := hne (by decide)\n"
        "  exact absurd hr (by decide)"
    )


def _wit_vjoin_kind(s, o):
    """Refute a vJoin rival on the kind conjunct at concrete inputs."""
    return (
        f"example : ¬ problem_spec_vJoin {s} {o}\n"
        f"    (implementation_vJoin {s} {o}) := by\n"
        "  rintro ⟨hk, -, -⟩\n"
        "  exact absurd hk (by decide)"
    )


def _wit_hjoin_nullentry(s, o):
    """Refute a hJoin rival on the null-operand arm's entry equality at (0,0)."""
    return (
        f"example : ¬ problem_spec_hJoin {s} {o}\n"
        f"    (implementation_hJoin {s} {o}) := by\n"
        "  rintro ⟨-, hz, -⟩\n"
        "  obtain ⟨-, -, he⟩ := hz (by decide)\n"
        "  exact absurd (he 0 0) (by decide)"
    )


def _wit_vjoin_nullentry(s, o):
    """Refute a vJoin rival on the null-operand arm's entry equality at (0,0)."""
    return (
        f"example : ¬ problem_spec_vJoin {s} {o}\n"
        f"    (implementation_vJoin {s} {o}) := by\n"
        "  rintro ⟨-, hz, -⟩\n"
        "  obtain ⟨-, -, he⟩ := hz (by decide)\n"
        "  exact absurd (he 0 0) (by decide)"
    )


def _wit_hjoin_nullcols(s, o):
    """Refute a hJoin rival on the null-operand arm's COLUMN conjunct."""
    return (
        f"example : ¬ problem_spec_hJoin {s} {o}\n"
        f"    (implementation_hJoin {s} {o}) := by\n"
        "  rintro ⟨-, hz, -⟩\n"
        "  obtain ⟨-, hc, -⟩ := hz (by decide)\n"
        "  exact absurd hc (by decide)"
    )


def _wit_hjoin_nullrows(s, o):
    """Refute a hJoin rival on the null-operand arm's ROW conjunct."""
    return (
        f"example : ¬ problem_spec_hJoin {s} {o}\n"
        f"    (implementation_hJoin {s} {o}) := by\n"
        "  rintro ⟨-, hz, -⟩\n"
        "  obtain ⟨hr, -, -⟩ := hz (by decide)\n"
        "  exact absurd hr (by decide)"
    )


def _wit_vjoin_nullrows(s, o):
    """Refute a vJoin rival on the null-operand arm's ROW conjunct."""
    return (
        f"example : ¬ problem_spec_vJoin {s} {o}\n"
        f"    (implementation_vJoin {s} {o}) := by\n"
        "  rintro ⟨-, hz, -⟩\n"
        "  obtain ⟨hr, -, -⟩ := hz (by decide)\n"
        "  exact absurd hr (by decide)"
    )


def _wit_vjoin_nullcols(s, o):
    """Refute a vJoin rival on the null-operand arm's COLUMN conjunct."""
    return (
        f"example : ¬ problem_spec_vJoin {s} {o}\n"
        f"    (implementation_vJoin {s} {o}) := by\n"
        "  rintro ⟨-, hz, -⟩\n"
        "  obtain ⟨-, hc, -⟩ := hz (by decide)\n"
        "  exact absurd hc (by decide)"
    )


def _wit_hjoin_genrows(s, o):
    """Refute a hJoin rival on the GENERAL arm's OFF-AXIS row conjunct."""
    return (
        f"example : ¬ problem_spec_hJoin {s} {o}\n"
        f"    (implementation_hJoin {s} {o}) := by\n"
        "  rintro ⟨-, -, hne⟩\n"
        "  obtain ⟨hr, -, -⟩ := hne (by decide)\n"
        "  exact absurd hr (by decide)"
    )


def _wit_vjoin_gencols(s, o):
    """Refute a vJoin rival on the GENERAL arm's OFF-AXIS column conjunct."""
    return (
        f"example : ¬ problem_spec_vJoin {s} {o}\n"
        f"    (implementation_vJoin {s} {o}) := by\n"
        "  rintro ⟨-, -, hne⟩\n"
        "  obtain ⟨-, hc, -⟩ := hne (by decide)\n"
        "  exact absurd hc (by decide)"
    )


def _wit_hjoin_genentry(s, o, i, j):
    """Refute a hJoin rival on the GENERAL arm's entry clause at `(i, j)`.

    `j` must land in the right block (`j ≥ self.cols`), which is where the spec
    demands the entry be read off `other` shifted by `self.cols`.
    """
    return (
        f"example : ¬ problem_spec_hJoin {s} {o}\n"
        f"    (implementation_hJoin {s} {o}) := by\n"
        "  rintro ⟨-, -, hne⟩\n"
        "  obtain ⟨-, -, he⟩ := hne (by decide)\n"
        f"  exact absurd (he {i} {j}) (by decide)"
    )


def _wit_vjoin_genentry(s, o, i, j):
    """Refute a vJoin rival on the GENERAL arm's entry clause at `(i, j)`.

    `i` must land in the bottom block (`i ≥ self.rows`), where the spec demands
    the entry be read off `other` shifted by `self.rows`.
    """
    return (
        f"example : ¬ problem_spec_vJoin {s} {o}\n"
        f"    (implementation_vJoin {s} {o}) := by\n"
        "  rintro ⟨-, -, hne⟩\n"
        "  obtain ⟨-, -, he⟩ := hne (by decide)\n"
        f"  exact absurd (he {i} {j}) (by decide)"
    )


SPEC_TESTS = [
    # ------------------------------------------------------------------ verify
    {
        "id": "pos-guard-commute-both",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "a correct reshape of BOTH joins that commutes the degenerate-"
            "normalisation guard to an equivalent boolean form "
            "(`self.rows ≠ other.rows ∧ self.cols = 0` for hJoin, symmetric for "
            "vJoin) must still satisfy `problem_spec_hJoin` / `problem_spec_vJoin` "
            "on every input; if it cannot, the postcondition is over-fit to the "
            "gold spelling (SPEC-TOO-STRONG). Proof: the `himpl` rewrite and the "
            "`by_cases` predicate are commuted to match, and the two guard "
            "projections are swapped; the branch arithmetic closes as in gold. No "
            "new declaration, axiom, or assumption token; the `correct_*` "
            "STATEMENTS are byte-identical."
        ),
    },
    {
        "id": "admiss-null-row-accumulate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the hJoin obligation is discharged at an F2P-shaped ground input "
            "(both operands null-row, widths 1 and 2, so the general-operand arm "
            "demands the accumulated width 1 + 2 = 3 — the case the pre-fix reset "
            "breaks) as a `have` ahead of the frozen obligation, which is then "
            "closed verbatim. Verifies (else the spec is unsatisfiable at a normal "
            "accumulation input, the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: the theorem STATEMENT is byte-identical, the ground instance "
            "is a `have` inside the existing tactic body, and no new "
            "declaration/axiom/sorry is introduced."
        ),
    },

    # ------------------------------------------------------------------ reject
    {
        "id": "weak-reset-hjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_H, _RESET_H),
        "refinement": (
            "this is the pre-fix behavior on the horizontal join: the guard fires "
            "on ANY null-dimensioned left operand and returns a result shaped like "
            "the right operand alone, discarding the left operand's accumulated "
            "width. On the F2P observable — a run of null-row operands of widths "
            "0,1,2,3 joined left to right — the accumulated width must reach 6, but "
            "the reset yields only the last operand's width. It does NOT resolve; "
            "this is the literal pre-patch."
        ),
        "rationale": (
            "REJECT from the general-operand arm's PIN `result.cols = self.cols + "
            "other.cols`: at `self = 0×3`, `other = 0×3` (both null-row, so "
            "`self.cols ≠ 0` selects the general arm) the spec demands width 6, but "
            "the rival returns the right operand's width 3. If it verifies, the "
            "spec does not force the accumulated width on the null-row sub-domain "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _wit_hjoin_pin("⟨0, 3, fun _ _ => 0, 0⟩", "⟨0, 3, fun _ _ => 0, 0⟩"),
    },
    {
        "id": "weak-forget-other-cols",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_H, _FORGET_H),
        "refinement": (
            "the normalisation branch is faithful but the general path returns the "
            "left operand unchanged, omitting the right operand's columns from the "
            "width sum. A real join that forgets to add the other operand's width "
            "on the non-empty merge under-counts on every operand with positive "
            "right width, so it fails the F2P width-accumulation observable. "
            "Faithful but non-resolving."
        ),
        "rationale": (
            "REJECT from the general-operand arm's PIN `result.cols = self.cols + "
            "other.cols`: at `self = 1×2`, `other = 1×3` the spec demands width "
            "2 + 3 = 5, but the rival returns the left operand's width 2. Refuted "
            "at a genuinely non-null operand shape distinct from the reset "
            "witness. If it verifies, the postcondition leaves the right operand's "
            "contribution unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_hjoin_pin("⟨1, 2, fun _ _ => 0, 0⟩", "⟨1, 3, fun _ _ => 0, 0⟩"),
    },
    {
        "id": "weak-class-drop-hjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_H, _KIND_H),
        "refinement": (
            "the width and entries are correct on the general path, but the result "
            "is tagged with the RIGHT operand's class instead of the receiver's. A "
            "join that returns a matrix of the wrong class fails the hidden "
            "type-preservation test (which asserts the join has the receiver's "
            "class), so a real patch of this shape does not resolve."
        ),
        "rationale": (
            "REJECT from the kind conjunct `result.kind = self.kind`: at "
            "`self.kind = 0`, `other.kind = 1` on the general path the spec demands "
            "the result carry kind 0, but the rival carries kind 1. Refuted with "
            "the two operands at DIFFERING `kind` tags — varying that facet of the "
            "binders off the value the other rivals hold it at. If it verifies, the "
            "spec does not pin the result class (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_hjoin_kind("⟨1, 2, fun _ _ => 0, 0⟩", "⟨1, 3, fun _ _ => 0, 1⟩"),
    },
    {
        "id": "weak-reset-vjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_V, _RESET_V),
        "refinement": (
            "the transpose pre-fix behavior on the vertical join: the guard fires "
            "on any null-dimensioned top operand and returns a result shaped like "
            "the bottom operand alone, discarding the top operand's accumulated "
            "height. On the transpose F2P observable — a run of null-column "
            "operands of heights 0,1,2,3 stacked top to bottom — the height must "
            "reach 6, but the reset yields only the last operand's height. It does "
            "NOT resolve; confirms the symmetric spec is equally tight."
        ),
        "rationale": (
            "REJECT from the general-operand arm's PIN `result.rows = self.rows + "
            "other.rows`: at `self = 3×0`, `other = 3×0` (both null-column, so "
            "`self.rows ≠ 0` selects the general arm) the spec demands height 6, "
            "but the rival returns the bottom operand's height 3. If it verifies, "
            "the spec does not force the accumulated height on the null-column "
            "sub-domain (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_vjoin_pin("⟨3, 0, fun _ _ => 0, 0⟩", "⟨3, 0, fun _ _ => 0, 0⟩"),
    },
    {
        "id": "weak-class-drop-vjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_V, _KIND_V),
        "refinement": (
            "the transpose of the class-drop rival: height and entries correct on "
            "the general path, but the result is tagged with the bottom operand's "
            "class instead of the receiver's. Fails the hidden type-preservation "
            "test for the vertical join, so a real patch of this shape does not "
            "resolve."
        ),
        "rationale": (
            "REJECT from the kind conjunct `result.kind = self.kind`: at "
            "`self.kind = 0`, `other.kind = 1` on the general path the spec demands "
            "kind 0, but the rival carries kind 1. Refuted with the two operands at "
            "differing `kind` tags and at a differing operand shape from the hJoin "
            "class-drop witness. If it verifies, the spec does not pin the result "
            "class on the vertical join (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_vjoin_kind("⟨2, 1, fun _ _ => 0, 0⟩", "⟨3, 1, fun _ _ => 0, 1⟩"),
    },
    {
        "id": "weak-null-arm-zero-entries-hjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_H, _ZERO_ENT_H),
        "refinement": (
            "on the null-left-operand arm the result keeps the correct shape and "
            "class but leaves its entries identically 0, silently discarding the "
            "surviving operand's VALUES. The hidden test joins a null receiver with "
            "a value-bearing operand and requires the result to carry that "
            "operand's entries (not merely its shape), so a real patch that zeroes "
            "them out does not resolve."
        ),
        "rationale": (
            "REJECT from the null-operand arm's entry clause "
            "`∀ i j, result.get i j = other.get i j`: at `self = 0×0`, "
            "`other = 2×1` with all entries 1 (so `self.cols = 0` and "
            "`self.rows ≠ other.rows` select this arm) the spec demands "
            "`result.get 0 0 = 1`, but the rival returns 0. Refuted at position "
            "(0,0); attacks the one clause the shape/kind rivals leave untouched. "
            "If it verifies, the null arm pins only shape and class, not entries "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _wit_hjoin_nullentry("⟨0, 0, fun _ _ => 0, 0⟩", "⟨2, 1, fun _ _ => 1, 0⟩"),
    },
    {
        "id": "weak-null-arm-zero-entries-vjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_V, _ZERO_ENT_V),
        "refinement": (
            "the transpose: on the null-top-operand arm the vertical join keeps the "
            "correct shape and class but zeroes its entries, discarding the "
            "surviving operand's values. Fails the hidden value-preservation test "
            "for the vertical join, so a real patch of this shape does not resolve."
        ),
        "rationale": (
            "REJECT from the null-operand arm's entry clause "
            "`∀ i j, result.get i j = other.get i j`: at `self = 0×0`, "
            "`other = 1×2` with all entries 1 the spec demands `result.get 0 0 = "
            "1`, but the rival returns 0. Refuted at position (0,0) on the vertical "
            "join, at an operand shape distinct from the hJoin entry witness. If it "
            "verifies, the null arm leaves entries unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_vjoin_nullentry("⟨0, 0, fun _ _ => 0, 0⟩", "⟨1, 2, fun _ _ => 1, 0⟩"),
    },
    {
        "id": "weak-null-arm-drop-cols-hjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_H, _NULL_COLS_H),
        "refinement": (
            "on the null-left-operand arm the rebuilt zero-width receiver is "
            "returned WITHOUT the right operand joined onto it, so the result is "
            "zero-width: the surviving operand's column count is dropped on the "
            "very arm meant to adopt its shape. A real join that rebuilds its "
            "receiver and then forgets to merge the other operand returns an "
            "empty matrix wherever the receiver is null, so the hidden "
            "null-receiver stacking observable fails. Non-resolving."
        ),
        "rationale": (
            "REJECT from the null-operand arm's COLUMN conjunct "
            "`result.cols = other.cols`: at `self = 1×0`, `other = 3×2` (so "
            "`self.cols = 0` and `self.rows ≠ other.rows` select this arm) the "
            "spec demands width 2, but the rival returns width 0. This is the one "
            "leaf of the null arm that the zero-entries rival leaves correct — it "
            "pins shape while breaking entries, this pins entries while breaking "
            "width. If it verifies, the null arm does not pin the width "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _wit_hjoin_nullcols("⟨1, 0, fun _ _ => 0, 0⟩", "⟨3, 2, fun _ _ => 4, 0⟩"),
    },
    {
        "id": "weak-null-arm-keep-rows-hjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_H, _NULL_ROWS_H),
        "refinement": (
            "the normalisation branch rebuilds the receiver at the RECEIVER's own "
            "height rather than the surviving operand's, so the result's row "
            "count is the null receiver's. A real join that rebuilds with its own "
            "row count produces a result whose height disagrees with the operand "
            "it is adopting, which the hidden null-receiver test catches. "
            "Non-resolving."
        ),
        "rationale": (
            "REJECT from the null-operand arm's ROW conjunct "
            "`result.rows = other.rows`: at `self = 2×0`, `other = 5×1` the spec "
            "demands height 5, but the rival returns the receiver's height 2. "
            "Refuted at a NON-zero receiver height, which distinguishes it from "
            "the zero-entries witnesses (whose receiver is 0×0 and whose height "
            "therefore coincides with a dropped one). If it verifies, the null arm "
            "does not pin the height (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_hjoin_nullrows("⟨2, 0, fun _ _ => 0, 0⟩", "⟨5, 1, fun _ _ => 3, 0⟩"),
    },
    {
        "id": "weak-null-arm-drop-rows-vjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_V, _NULL_ROWS_V),
        "refinement": (
            "the transpose of the width-drop rival: on the null-top-operand arm "
            "the rebuilt zero-height receiver is returned without the bottom "
            "operand stacked onto it, dropping the surviving operand's row count. "
            "Fails the hidden null-receiver stacking observable for the vertical "
            "join. Non-resolving."
        ),
        "rationale": (
            "REJECT from the null-operand arm's ROW conjunct "
            "`result.rows = other.rows`: at `self = 0×1`, `other = 3×2` (so "
            "`self.rows = 0` and `self.cols ≠ other.cols` select this arm) the "
            "spec demands height 3, but the rival returns height 0. Confirms the "
            "transpose spec pins the null arm's joined-axis dimension too. If it "
            "verifies, the null arm does not pin the height (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_vjoin_nullrows("⟨0, 1, fun _ _ => 0, 0⟩", "⟨3, 2, fun _ _ => 4, 0⟩"),
    },
    {
        "id": "weak-null-arm-keep-cols-vjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_V, _NULL_COLS_V),
        "refinement": (
            "the transpose of the null-arm height-kept rival: on the "
            "null-top-operand arm the receiver is rebuilt at the RECEIVER's own "
            "width instead of the surviving operand's, so the result's column "
            "count is the null receiver's. A real join that rebuilds with its "
            "own column count produces a result whose width disagrees with the "
            "operand it is adopting, which the hidden null-receiver test "
            "catches. Non-resolving."
        ),
        "rationale": (
            "REJECT from the null-operand arm's COLUMN conjunct "
            "`result.cols = other.cols`: at `self = 0×3`, `other = 2×5` (so "
            "`self.rows = 0` and `self.cols ≠ other.cols` select this arm) the "
            "spec demands width 5, but the rival returns the receiver's width "
            "3. Refuted at a NON-zero receiver width, so the discrimination "
            "cannot be an artifact of a receiver whose width coincides with a "
            "dropped one. This is the vJoin null arm's OFF-AXIS leaf, the "
            "transpose of the hJoin height leaf, and the last null-arm conjunct "
            "no other rival perturbs. If it verifies, the null arm does not pin "
            "the width on the vertical join (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_vjoin_nullcols(
            "⟨0, 3, fun _ _ => 0, 0⟩", "⟨2, 5, fun _ _ => 6, 0⟩"),
    },
    {
        "id": "weak-gen-arm-offaxis-hjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_H, _GEN_OFFAXIS_H),
        "refinement": (
            "on the general path the accumulated width, every entry and the "
            "result class are exactly right, and the null-operand arm is "
            "untouched, but the result carries one row more than the receiver. "
            "A real join that allocates its output one row too tall returns a "
            "matrix whose height disagrees with both operands, so every "
            "downstream shape assertion on the joined result fails. "
            "Non-resolving."
        ),
        "rationale": (
            "REJECT from the general arm's OFF-AXIS conjunct "
            "`result.rows = self.rows`: at `self = 3×1`, `other = 3×2` the spec "
            "demands height 3, but the rival returns 4. This leaf is attacked "
            "by its own rival rather than delegated to the positive control, "
            "and this case is the refutation of the delegating argument: the "
            "rival agrees with gold on the joined-axis pin, the entries, the "
            "kind tag and the entire null-operand arm, so it does NOT collapse "
            "into the reset rival (whose defect is on the other arm). If it "
            "verifies, the general arm leaves the off-axis dimension unpinned "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _wit_hjoin_genrows(
            "⟨3, 1, fun _ _ => 0, 0⟩", "⟨3, 2, fun _ _ => 0, 0⟩"),
    },
    {
        "id": "weak-gen-arm-offaxis-vjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_V, _GEN_OFFAXIS_V),
        "refinement": (
            "the transpose: accumulated height, entries and class right on the "
            "general path, null-operand arm untouched, but the result carries "
            "one column more than the receiver. Fails every downstream shape "
            "assertion on the stacked result. Non-resolving."
        ),
        "rationale": (
            "REJECT from the general arm's OFF-AXIS conjunct "
            "`result.cols = self.cols`: at `self = 1×4`, `other = 2×4` the spec "
            "demands width 4, but the rival returns 5. Refuted at an operand "
            "shape distinct from the hJoin off-axis witness, confirming the "
            "transpose obligation pins its off-axis dimension too. If it "
            "verifies, the general arm leaves it unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_vjoin_gencols(
            "⟨1, 4, fun _ _ => 0, 0⟩", "⟨2, 4, fun _ _ => 0, 0⟩"),
    },
    {
        "id": "weak-gen-arm-entry-hjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_H, _GEN_ENT_H),
        "refinement": (
            "on the general path the dimensions AND the result class are exactly "
            "right, but every entry is read off the left operand, so the right "
            "block never reads the operand being joined on. A real join that "
            "allocates the correct wider shape and then fails to copy the other "
            "operand's entries into the right block returns a matrix of the right "
            "shape holding the wrong values — the hidden value-equality assertion "
            "(the join is compared against an expected matrix, not just its "
            "shape) fails. Non-resolving."
        ),
        "rationale": (
            "REJECT from the general arm's ENTRY clause `∀ i j, result.get i j = "
            "if j < self.cols then self.get i j else other.get i (j - self.cols)`: "
            "at `self = 2×2` (all entries 5), `other = 2×3` (all entries 9), "
            "position (0,2) lies in the right block, so the spec demands 9 but the "
            "rival returns 5. This is the general arm's remaining leaf — the reset "
            "and forget rivals attack its dimension pin, this attacks its "
            "contents. If it verifies, the general arm pins shape and class but "
            "not the values read from the joined operand (SPEC-TOO-WEAK)."
        ),
        "witness": _wit_hjoin_genentry(
            "⟨2, 2, fun _ _ => 5, 0⟩", "⟨2, 3, fun _ _ => 9, 0⟩", 0, 2),
    },
    {
        "id": "weak-gen-arm-entry-vjoin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_V, _GEN_ENT_V),
        "refinement": (
            "the transpose: correct height, width and class on the general path, "
            "but every entry is read off the top operand so the bottom block "
            "never reads the operand being stacked on. Fails the hidden "
            "value-equality assertion for the vertical join. Non-resolving."
        ),
        "rationale": (
            "REJECT from the general arm's ENTRY clause `∀ i j, result.get i j = "
            "if i < self.rows then self.get i j else other.get (i - self.rows) j`: "
            "at `self = 2×2` (all entries 5), `other = 3×2` (all entries 9), "
            "position (2,0) lies in the bottom block, so the spec demands 9 but "
            "the rival returns 5. Refuted at an index distinct from the hJoin "
            "entry witness, on the transpose obligation. If it verifies, the "
            "general arm leaves the stacked operand's values unpinned "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _wit_vjoin_genentry(
            "⟨2, 2, fun _ _ => 5, 0⟩", "⟨3, 2, fun _ _ => 9, 0⟩", 2, 0),
    },
]


# No consumed axioms and no deep-model references: both joins are modeled
# directly over the input accessors and dimensions, so there is no in-model
# axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
