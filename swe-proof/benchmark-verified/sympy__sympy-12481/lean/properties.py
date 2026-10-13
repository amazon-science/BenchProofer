# properties.py — G-PBT falsification battery for sympy__sympy-12481 (lean lane).
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Every SPEC case is a FULL
# Solution.lean variant sharing the FROZEN spec byte-for-byte — only the impl region
# (and, where a restructured impl needs an honest reproof, the proof body inside
# proof-start/proof-end) differs, so `markers.same_spec` holds by construction and the
# `theorem correct_permFromCycles` STATEMENT is byte-identical in every case. Every
# expect="reject" case carries a refutation `witness`: a snippet that ELABORATES
# against the rival and FAILS on the frozen solution, so the rejection is attributable
# to the postcondition and not to a tactic script that merely stopped matching a
# reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
#   implementation_permFromCycles (cycles : List (List Nat)) : Option (List Nat)
#   Builds the array form of the left-to-right composition of a list of cycles given
#   in cyclic notation. `applyCycle c` is the action of ONE cycle (each listed point
#   goes to the next entry, cyclically; every other point is fixed); `applyAll cycles`
#   folds those actions left-to-right; `permSize cycles` is one past the largest point
#   named anywhere in `cycles`. All three are TRANSPARENT `def`s over `List Nat` — the
#   bundle consumes no `opaque` callee and no axiom, so every rival here is refutable
#   by `decide` at a concrete literal input; no carrier conditioning is needed and no
#   witness in this battery binds anything (so the gate's consistency probe is
#   vacuously satisfied — there are no hypotheses to be jointly unsatisfiable).
#
#   `problem_spec_permFromCycles cycles result` is a CONJUNCTION OF TWO LEGS selected by
#   `sizeUndetermined cycles` (cycles were supplied, yet none names a point, so the
#   width of the array form is not determined by the input):
#     (C0) DEGENERATE: `sizeUndetermined cycles = true → result = none` — on that shape
#          nothing is returned. Pins the outcome there rather than merely permitting it,
#          so an impl that builds an empty listing instead is refuted.
#     and, on the complementary leg (`sizeUndetermined cycles = false`), the same three
#     obligations the success case always carried:
#     (C1) SUCCESS:  `result = some aform` — for an admissible input of determined width
#          the construction always produces a value; it never declines to build one.
#          This is the clause the change is observable through.
#     (C2) LENGTH:   `aform.length = permSize cycles` — one entry per point from 0 up
#          to the largest point named, no more and no fewer.
#     (C3) IMAGE:    `∀ i < permSize cycles, aform.getD i 0 = applyAll cycles i` — the
#          per-position pin: entry `i` is the image of `i` under the left-to-right
#          composition. This is the LOAD-BEARING clause and carries the composition
#          ORDER, the requirement that EVERY listed cycle participate, and that EVERY
#          in-range position be composed.
#   The two legs are EXHAUSTIVE and mutually exclusive (the selector is a `Bool`), so
#   nothing is left unconstrained by the split; and the selector itself is attacked from
#   BOTH sides (`rej-always-build`, `rej-degenerate-too-wide`), which is what stops a
#   two-leg postcondition from being satisfied by mis-placing the boundary. Note the
#   whole shared-point sub-domain the change is about has a DETERMINED width, so the
#   discriminating behaviour lives entirely on the success leg.
#
#   The theorem's only precondition is `∀ c ∈ cycles, c.Nodup` (each cycle lists
#   distinct points). Notably it does NOT require the cycles to be pairwise disjoint,
#   which is what makes the shared-point sub-domain admissible and attackable.
#
# WHAT PORTS FROM NAGINI, AND HOW THE CARRIER RESHAPES IT
#   nagini modeled the composition of exactly TWO two-element swaps over `n` points:
#   `compose_cycles(n, a, b, c, d) -> List[int]`, with the pin
#   `Result()[i] == swap_val(swap_val(i, a, b), c, d)` and the four points as separate
#   int binders. This backend models the GENERAL routine: an arbitrary list of
#   arbitrary-length cycles, with the number of cycles, their lengths, their contents
#   and the resulting size all folded into the ONE binder `cycles`. So each nagini
#   rival keyed off a named point (a/b/c/d) becomes a rival keyed off a position in
#   `cycles` or in the output, and each nagini rival keyed off `n` becomes a rival
#   keyed off `permSize cycles`:
#     * `rej-drop-second-swap`  -> `rej-first-cycle-only`   (composes only the head
#       cycle; the general form of "apply (a b) but never (c d)").
#     * `rej-wrong-order`       -> `rej-reverse-order`       (folds the cycles
#       right-to-left; the general form of "(c d) then (a b)").
#     * `rej-skip-first-pos`    -> `rej-skip-first-index`    (position 0 left at its
#       own value; unchanged in spirit).
#     * `rej-skip-last-pos`     -> `rej-skip-last-index`     (the final position left
#       uncomposed; unchanged in spirit).
#     * `rej-disjoint-only`     -> `rej-reject-shared-point` (nagini expressed the
#       pre-change behaviour as "leave the second swap unapplied on non-disjoint
#       input", because its carrier had no failure channel. Here the carrier IS
#       `Option (List Nat)`, so the same defect is expressed FAITHFULLY as declining
#       to build at all — a `none` return. That is a STRONGER port: it attacks C1,
#       an obligation nagini's `List[int]` carrier could not even state.)
#     * `rej-identity-range-fill` -> `rej-identity-fill`     (returns 0..size-1,
#       satisfying C1 and C2 but not C3; unchanged in spirit).
#     * `pos-single-loop` / `pos-fused-two-phase` -> `pos-direct-image` /
#       `pos-array-accumulator` / `pos-pure-map` (structurally different CORRECT
#       impls; see below — each reproves the byte-identical obligation honestly).
#     * `admiss-f2p-witness`    -> `admiss-in-domain`.
#
#   TWO CASES ARE NEW HERE, because this carrier exposes a clause nagini's did not.
#   nagini's result length was pinned by `len(Result()) == n` with `n` an explicit
#   input, so a length rival would have had to disobey an input it was handed. Here
#   the length is DERIVED (`permSize cycles`), which makes it a genuine degree of
#   freedom an impl can get wrong while composing every position it does emit
#   correctly: `rej-truncate-array-form` and `rej-pad-array-form` attack C2 from
#   below and from above respectively. Without them C2 is stated but never probed.
#
#   TWO FURTHER CASES WERE ADDED BY AUDIT, closing sub-domains of the sole input
#   binder that none of the ported witnesses reached:
#     * `rej-drop-singleton-cycles` — a cycle of length 1 NAMES a point without
#       MOVING it, so discarding it preserves C3 exactly and is observable only
#       through the derived size. No shipped witness named a singleton cycle, so
#       every one of them agreed with this rival.
#     * `rej-none-on-single-cycle` — declines to build unless at least two cycles
#       are supplied. C1 again, but at a point the C1 rival above cannot reach:
#       that one is correct on every input whose cycles are disjoint, and this one
#       is wrong on exactly the single-cycle inputs, where the shared-point notion
#       does not even apply. Five shipped witnesses use a single cycle, so the
#       clause is probed at a sub-domain the battery already occupies.
#   The audit also proved the spec TIGHT (any two results satisfying the postcondition
#   at the same input are equal), which is the structural reason attack D found no
#   SPEC-TOO-WEAK hole: no impl can satisfy the postcondition and still differ
#   from the frozen one. Tightness survives the two-leg split — C0 pins `none`
#   uniquely on its leg and C1+C2+C3 pin the list uniquely on the other, and the legs
#   are exhaustive — so there is no input at which two distinct results are admitted.
#
#   TWO FURTHER CASES WERE ADDED BY REPAIR, probing the degenerate leg from both sides:
#     * `rej-always-build` — drops the guard and builds the empty listing on the
#       degenerate shape. It is the frozen impl's composing body verbatim, so it agrees
#       everywhere the width is determined and ONLY C0 can refute it. This is the rival
#       a spec that DELETED the leg rather than stating it would admit.
#     * `rej-degenerate-too-wide` — satisfies C0 but over-applies it, declining also at
#       the narrowest determined width (an input naming only the point 0). Only the
#       success leg refutes it. Together the pair pins the leg SELECTOR, not just the
#       two leg bodies.
#
# LANES THAT DO NOT PORT
#   * FRAME / PERMISSION MUTATION. Nagini-specific (fractional permissions). Its
#     sibling records the class as N/A there too: every parameter was a plain int and
#     the only permission was on the freshly-built result. Lean is referentially
#     transparent — no aliasing, no fractional permission — so the class is VACUOUS
#     here and no substitute is fabricated. The frame-shaped worry that remains (an
#     output component left unconstrained) is covered by C2+C3 together: every
#     position below `permSize cycles` is pinned and the length is pinned exactly, so
#     there is no unconstrained slot for a rival to fill. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION. The nagini sibling carries no such case, and on
#     lean the class is genuinely VACUOUS — measured, not asserted. The frozen solution
#     sets no `loom.semantics.termination` option at all, so the total-carrier reading
#     applies. Two probes were built. (a) A rival whose impl is a plain `def` recursing
#     on itself with no decreasing measure does not compile: Lean refuses it with `fail
#     to show termination for implementation_permFromCycles / failed to infer structural
#     recursion`, i.e. the carrier will not ACCEPT a diverging impl, so there is nothing
#     to reject. (b) The `partial def` spelling does compile, but it makes the impl an
#     opaque constant that no witness can reduce — and, decisively, a
#     hypothesis-conditioned witness against it elaborates against the FROZEN solution
#     too (measured exit 0 on both sides), so it discriminates nothing and would be a
#     hollow case rather than a shippable one. Neither spelling yields a rival that is
#     both admissible and refutable, which is what makes the class vacuous here. This is
#     the LEAN total-carrier disposition, explicitly not the velvet-`partial`
#     known-spec-hole one (the corpus-wide termination-semantics finding).
#   * CONTROL-FLOW / SIDE-EFFECT channel. As on nagini, there is no raise or effect
#     channel distinct from the returned value; the `Option` IS the channel, and it is
#     attacked directly by `rej-reject-shared-point`.
#   * WRONG-ECHO of an oracle. `applyAll` / `applyCycle` / `permSize` are grounded
#     total functions of `cycles`, fully unfolded, so there is no ungrounded answer-key
#     for an impl to echo — the cheapest honest impl IS the spec's right-hand side,
#     shipped as `pos-pure-map`.
#   * AXIOM_TESTS (nagini's `ax-sound-deepmodel` / `ax-contain-caller-domain`). The
#     axiom lane is G-AX's job and this gate ignores it; the bundle consumes no
#     callee axiom (the composition is an A-reference deep model validated by G-CONF).
from pathlib import Path

INSTANCE = "sympy__sympy-12481"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The whole frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every case swaps THIS block (and nothing outside it, except the proof
# bodies noted below).
_IMPL = (
    "def implementation_permFromCycles\n"
    "    (cycles : List (List Nat)) : Option (List Nat) := Id.run do\n"
    "  if sizeUndetermined cycles then\n"
    "    return none\n"
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof's opening lines, and its whole tactic body. Both lie entirely
# inside proof-start/proof-end. Only the soundness positives touch these, and each
# reproves the byte-identical `theorem correct_permFromCycles` statement.
_INTRO = "  intro cycles hnd\n  clear hnd\n"
assert _BASE.count(_INTRO) == 1, "proof intro anchor drifted from expected text"

_PROOF_FULL = _BASE[_BASE.index(_INTRO):_BASE.index("\n-- proof-end")]

# The frozen proof's closing steps (discharging C1/C2/C3 from `key`), reused verbatim
# by the two positives that still route through a `key` equation.
_PROOF_TAIL = (
    "    rw [key]\n"
    "    refine ⟨_, rfl, ?_, ?_⟩\n"
    "    · simp\n"
    "    · intro i hi\n"
    "      rw [List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hi]\n"
    "      simp\n"
)
assert _BASE.count(_PROOF_TAIL) == 1, "proof tail anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# Each is a structurally DIFFERENT but behaviourally IDENTICAL impl, with the
# obligation REPROVEN honestly for the new shape: no `sorry`/`admit`/`native_decide`,
# no new `axiom`, no new `theorem`/`lemma`, and the theorem statement untouched.
# ===========================================================================

# pos-pure-map: the cheapest honest impl — a pure `List.range … |>.map (applyAll …)`
# with no `Id.run do`, no `let mut`, no accumulator and no loop at all. Since the
# result is now definitionally the spec's own right-hand side, the entire `key`
# derivation in the frozen proof becomes dead and the reproof is just the frozen
# CLOSING steps applied directly. Ports nagini's "cheapest honest impl" positive.
_POS_PURE = _swap(
    _swap(_BASE, _IMPL,
          "def implementation_permFromCycles\n"
          "    (cycles : List (List Nat)) : Option (List Nat) :=\n"
          "  if sizeUndetermined cycles then none\n"
          "  else some ((List.range (permSize cycles)).map (applyAll cycles))"),
    _PROOF_FULL,
    "  intro cycles hnd\n"
    "  clear hnd\n"
    "  unfold implementation_permFromCycles problem_spec_permFromCycles\n"
    "  constructor\n"
    "  · intro hdeg\n"
    "    simp [hdeg]\n"
    "  · intro hnon\n"
    "    simp only [hnon, Bool.false_eq_true, if_false]\n"
    "    refine ⟨_, rfl, ?_, ?_⟩\n"
    "    · simp\n"
    "    · intro i hi\n"
    "      rw [List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hi]\n"
    "      simp\n",
)

# pos-direct-image: keeps the imperative `Id.run do` / `let mut` / `for i in [0:sz]`
# accumulator shape, but FUSES the inner per-cycle fold into a single application of
# the composed action, so the nested `for c in cycles do` loop disappears. This is the
# direct counterpart of nagini's `pos-single-loop` (one forward pass appending the
# fully-composed image of each point). The reproof is the frozen one with the inner
# loop's `inner` lemma and its `hfun` congruence step dropped, since there is no
# nested loop left to normalize.
_POS_DIRECT = _swap(
    _swap(_BASE, _IMPL,
          "def implementation_permFromCycles\n"
          "    (cycles : List (List Nat)) : Option (List Nat) := Id.run do\n"
          "  if sizeUndetermined cycles then\n"
          "    return none\n"
          "  let sz := permSize cycles\n"
          "  let mut aform : List Nat := []\n"
          "  for i in [0:sz] do\n"
          "    aform := aform ++ [applyAll cycles i]\n"
          "  return some aform"),
    _PROOF_FULL,
    "  intro cycles hnd\n"
    "  clear hnd\n"
    "  constructor\n"
    "  · intro hdeg\n"
    "    unfold implementation_permFromCycles\n"
    "    simp [hdeg]\n"
    "  · intro hnon\n"
    "    have key : implementation_permFromCycles cycles\n"
    "        = some ((List.range (permSize cycles)).map (applyAll cycles)) := by\n"
    "      unfold implementation_permFromCycles\n"
    "      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',\n"
    "        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]\n"
    "      simp only [pure]\n"
    "      rw [List.forIn_yield_eq_foldl]\n"
    "      rw [List.range_eq_range']\n"
    "      generalize (permSize cycles) = sz\n"
    "      have foldl_app : ∀ (len start : Nat) (acc : List Nat),\n"
    "          (List.range' start len).foldl (fun r i => r ++ [applyAll cycles i]) acc\n"
    "          = acc ++ (List.range' start len).map (applyAll cycles) := by\n"
    "        intro len\n"
    "        induction len with\n"
    "        | zero => intro start acc; simp\n"
    "        | succ n ih => intro start acc; rw [List.range'_succ]; simp only [List.foldl_cons, List.map_cons, ih]; simp\n"
    "      rw [foldl_app]; simp; rfl\n"
    + _PROOF_TAIL,
)

# pos-array-accumulator: keeps BOTH loops but changes the accumulator's data
# structure from `List Nat` (append at the end) to `Array Nat` (`push`), converting
# once at the return. A different executable shape over a different carrier that
# computes the same array form. Ports nagini's `pos-fused-two-phase` role: a second,
# independent correct shape, so a spec over-fitted to one accumulator idiom is caught.
# The reproof mirrors the frozen one with the accumulator lemma restated over `Array`.
_POS_ARRAY = _swap(
    _swap(_BASE, _IMPL,
          "def implementation_permFromCycles\n"
          "    (cycles : List (List Nat)) : Option (List Nat) := Id.run do\n"
          "  if sizeUndetermined cycles then\n"
          "    return none\n"
          "  let sz := permSize cycles\n"
          "  let mut aform : Array Nat := #[]\n"
          "  for i in [0:sz] do\n"
          "    let mut v := i\n"
          "    for c in cycles do\n"
          "      v := applyCycle c v\n"
          "    aform := aform.push v\n"
          "  return some aform.toList"),
    _PROOF_FULL,
    "  intro cycles hnd\n"
    "  clear hnd\n"
    "  have inner : ∀ i, (forIn cycles i fun c r => (pure (ForInStep.yield (applyCycle c r)) : Id _))\n"
    "      = applyAll cycles i := by\n"
    "    intro i\n"
    "    unfold applyAll\n"
    "    induction cycles generalizing i with\n"
    "    | nil => rfl\n"
    "    | cons c cs ih => simp only [List.forIn_cons, ih]; rfl\n"
    "  constructor\n"
    "  · intro hdeg\n"
    "    unfold implementation_permFromCycles\n"
    "    simp [hdeg]\n"
    "  · intro hnon\n"
    "    have key : implementation_permFromCycles cycles\n"
    "        = some ((List.range (permSize cycles)).map (applyAll cycles)) := by\n"
    "      unfold implementation_permFromCycles\n"
    "      simp only [hnon, Bool.false_eq_true, if_false, Id.run, Std.Range.forIn_eq_forIn_range',\n"
    "        bind_pure_comp, map_pure, Std.Range.size, Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]\n"
    "      simp only [inner]\n"
    "      have hfun : (fun (i : Nat) (r : Array Nat) =>\n"
    "          ((fun a => ForInStep.yield (r.push a)) <$> applyAll cycles i : Id _))\n"
    "          = (fun (i : Nat) (r : Array Nat) => (ForInStep.yield (r.push (applyAll cycles i)) : Id _)) := rfl\n"
    "      rw [hfun, List.forIn_yield_eq_foldl]\n"
    "      rw [List.range_eq_range']\n"
    "      generalize (permSize cycles) = sz\n"
    "      have foldl_app : ∀ (len start : Nat) (acc : Array Nat),\n"
    "          ((List.range' start len).foldl (fun r i => r.push (applyAll cycles i)) acc).toList\n"
    "          = acc.toList ++ (List.range' start len).map (applyAll cycles) := by\n"
    "        intro len\n"
    "        induction len with\n"
    "        | zero => intro start acc; simp\n"
    "        | succ n ih => intro start acc; rw [List.range'_succ]; simp only [List.foldl_cons, List.map_cons, ih]; simp\n"
    "      show some (List.foldl (fun r i => Array.push r (applyAll cycles i)) #[] (List.range' 0 sz)).toList = _\n"
    "      rw [foldl_app]; simp\n"
    + _PROOF_TAIL,
)


# ===========================================================================
# ADMISSIBILITY — must VERIFY, else PRECOND-TOO-STRONG / spec vacuous.
# Ports nagini's `admiss-f2p-witness`. A top-level caller would leave the impl+proof
# regions and break same_spec, so this is done IN-REGION: extra `have`s at the head of
# the frozen proof body (a) CONSUME the precondition hypothesis, showing it is usable
# rather than a dead binder; (b) exhibit a normal F2P-shaped input — two cycles that
# SHARE a point — as satisfying that precondition; (c) reduce the impl at that input
# to a concrete array form; and (d) discharge `problem_spec_permFromCycles` at it with
# explicit witnesses, so all three clauses are shown non-vacuously satisfiable at a
# real point. The frozen tactic body then follows verbatim, so the obligation is still
# proven in full. If a hypothesis were unusable or the spec unsatisfiable at an
# in-domain input, this file would not elaborate.
# ===========================================================================
_ADMISS = _swap(
    _BASE, _INTRO,
    "  intro cycles hnd\n"
    "  have hused : ∀ c ∈ cycles, c.Nodup := hnd\n"
    "  have hdom : ∀ c ∈ ([[0, 1], [0, 2]] : List (List Nat)), c.Nodup := by decide\n"
    "  have hreach : implementation_permFromCycles [[0, 1], [0, 2]] = some [1, 2, 0] := by\n"
    "    simp [implementation_permFromCycles, Id.run, permSize, sizeUndetermined]\n"
    "    decide\n"
    "  have hwidth : sizeUndetermined [[0, 1], [0, 2]] = false := by decide\n"
    "  have hspec : problem_spec_permFromCycles [[0, 1], [0, 2]]\n"
    "      (implementation_permFromCycles [[0, 1], [0, 2]]) := by\n"
    "    rw [hreach]\n"
    "    refine ⟨fun hc => absurd (hwidth.symm.trans hc) (by simp), fun _ => ?_⟩\n"
    "    refine ⟨[1, 2, 0], rfl, by decide, ?_⟩\n"
    "    decide\n"
    "  clear hused hdom hreach hwidth hspec\n"
    "  clear hnd\n",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for a reshaped impl, which is exactly why the gate reads the
# `witness` — checked in a file with the obligation removed — rather than the rival's
# own build).
# ===========================================================================

def _rival(body):
    return _swap(_BASE, _IMPL,
                 "def implementation_permFromCycles\n"
                 "    (cycles : List (List Nat)) : Option (List Nat) := Id.run do\n" + body)


# rej-reject-shared-point: declines to build whenever some point is named by more
# than one cycle (the combined list of named points has a repeat), returning nothing;
# otherwise composes correctly. This is the PRE-CHANGE behaviour, and the faithful
# expression on this carrier of nagini's `rej-disjoint-only`. Attacks C1.
_R_PREPATCH = _rival(
    "  if ¬ cycles.flatten.Nodup then\n"
    "    return none\n"
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-first-cycle-only: applies only the HEAD cycle's action and ignores every later
# cycle. Correct whenever the remaining cycles move nothing reachable (in particular
# on any single-cycle input), wrong as soon as a second cycle acts. General form of
# nagini's `rej-drop-second-swap`. Attacks C3 (every listed cycle must participate).
_R_FIRST_ONLY = _rival(
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles.take 1 do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-reverse-order: folds the cycles' actions RIGHT-to-left instead of left-to-right.
# Applies every cycle and produces a genuine permutation of the right length, so it
# satisfies C1 and C2 and agrees with the spec on every input whose cycles commute
# (including every single-cycle input) — it is wrong only where the order matters.
# General form of nagini's `rej-wrong-order`. Attacks C3 (composition ORDER).
_R_REVERSE = _rival(
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles.reverse do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-skip-first-index: leaves output position 0 at its own value and composes every
# later position. PARTIAL-DOMAIN in the output index: correct everywhere except the
# first entry. Ports nagini's `rej-skip-first-pos`. Attacks C3 at i = 0.
_R_SKIP_FIRST = _rival(
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    if i ≠ 0 then\n"
    "      for c in cycles do\n"
    "        v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-skip-last-index: leaves the FINAL output position at its own value and composes
# every earlier one. The mirror partial-domain rival, distinguished from the one above
# because a witness pinned at index 0 cannot see it and vice versa. Ports nagini's
# `rej-skip-last-pos`. Attacks C3 at i = permSize cycles - 1.
_R_SKIP_LAST = _rival(
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    if i + 1 ≠ sz then\n"
    "      for c in cycles do\n"
    "        v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-truncate-array-form: composes EVERY position correctly, then drops the final
# entry, so the result is one shorter than the number of points named. NEW on this
# carrier (nagini received its length as an input binder and so had no room for this).
# Attacks C2 from below.
_R_TRUNCATE = _rival(
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform.dropLast")

# rej-pad-array-form: composes every position correctly and then appends one extra
# entry, so the result is one LONGER than the number of points named. The mirror of
# the truncation rival: it satisfies C3 at every index the spec quantifies over (the
# extra entry sits beyond `permSize cycles`, where C3 says nothing), so ONLY C2 can
# refute it. That makes it the sharpest probe that C2 pins the length exactly rather
# than as a lower bound. Also NEW on this carrier. Attacks C2 from above.
_R_PAD = _rival(
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some (aform ++ [0])")

# rej-drop-singleton-cycles: discards every LENGTH-1 cycle before composing — both its
# action (correct: a singleton moves nothing) and its contribution to the derived size
# (wrong: a singleton still NAMES a point, so it can raise `permSize`). ADDED BY AUDIT.
# It is a subtle rival precisely because dropping a singleton is behaviour-preserving for
# clause C3 and only observable through C2, and because none of the eight witnesses the
# port shipped names a singleton cycle at all — every one of them agrees with this rival,
# so before this case the singleton sub-domain was entirely unprobed. Attacks C2 through
# the derived size.
_R_DROP_SINGLETON = _rival(
    "  let moving := cycles.filter (fun c => c.length ≠ 1)\n"
    "  let sz := permSize moving\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in moving do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-none-on-single-cycle: composes correctly whenever at least two cycles are supplied
# but declines to build when handed a single one. ADDED BY AUDIT, and deliberately NOT
# keyed on the empty input: `cycles = []` is a point the modeled routine never reaches
# (the cyclic-form path is selected by the argument's first element BEING a sequence, so
# an empty argument list takes the array-form path instead, a different input shape that
# mapping.md puts out of scope), which makes a rival keyed on it a claim about behaviour
# outside the modeled domain. A single-cycle input is squarely inside it — five of this
# battery's other witnesses use one — so this reaches C1 at a sub-domain the C1 rival
# above cannot: that one is correct on every disjoint input, and "shares a point" does
# not even apply to a lone cycle. Attacks C1 on the cycle-count axis.
_R_NONE_SINGLE = _rival(
    "  if cycles.length < 2 then\n"
    "    return none\n"
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-always-build: drops the degenerate guard and always builds, so on a supplied-but-
# pointless cycle list it emits the empty array form instead of declining. ADDED BY THIS
# REPAIR alongside the leg it probes. It is byte-for-byte the composing body of the frozen
# impl and therefore agrees with it on EVERY input whose width is determined — the entire
# region clauses C2/C3 quantify over — so no length or per-position witness can see it.
# Only the degenerate leg can refute it, which makes it the sharpest available probe that
# the leg pins `none` rather than merely permitting it.
_R_ALWAYS_BUILD = _rival(
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-degenerate-too-wide: declines on a pointless cycle list (so the degenerate leg is
# satisfied) but ALSO declines whenever the cycles between them name no point beyond 0,
# i.e. it over-applies the degenerate treatment to a genuinely determined width of 1.
# ADDED BY THIS REPAIR. It is correct on the degenerate leg and wrong on the success leg
# at a sub-domain no other rival occupies: an input naming only the point 0.
_R_DEGEN_WIDE = _rival(
    "  if permSize cycles ≤ 1 then\n"
    "    return none\n"
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    let mut v := i\n"
    "    for c in cycles do\n"
    "      v := applyCycle c v\n"
    "    aform := aform ++ [v]\n"
    "  return some aform")

# rej-identity-fill: returns 0, 1, …, permSize cycles - 1, ignoring the cycles'
# actions entirely. Satisfies C1 and C2 and returns a genuine permutation of exactly
# the right length; only C3 forbids it. Ports nagini's `rej-identity-range-fill` and
# serves the same purpose: proving the per-position pin, not merely the shape and
# range clauses, is what carries the spec. Attacks C3.
_R_IDENTITY = _rival(
    "  let sz := permSize cycles\n"
    "  let mut aform : List Nat := []\n"
    "  for i in [0:sz] do\n"
    "    aform := aform ++ [i]\n"
    "  return some aform")


# --- witnesses ---------------------------------------------------------------------
# Each states `¬ problem_spec_permFromCycles cycles (implementation_permFromCycles
# cycles)` at a CONCRETE literal input, reduces the impl there, and derives the
# contradiction from whichever clause the rival violates. Every carrier involved is a
# transparent `def` over `List Nat`, so `decide` closes each one and no witness needs
# a hypothesis — there is nothing here to be jointly unsatisfiable. Each ELABORATES
# against its rival and FAILS on the frozen solution (verified by hand with
# scripts/lean_verify.sh before shipping).
#
# The ten reject witnesses deliberately probe TEN DISTINCT input points, varying the
# sole input binder `cycles` along every axis it has: number of cycles (one, two), cycle
# length (1 vs 2 vs 3), whether two cycles share a point (`[[0,1],[0,2]]` shares one,
# `[[0,1],[2,3]]` shares none), whether the two cycles commute, which point is named
# first, whether a cycle NAMES a point without MOVING it (a singleton), whether a point
# below the derived size is named by nothing at all (leading in `[[1,2]]`, interior in
# `[[0,2]]`, two of them in `[[1,3]]`), and the derived `permSize cycles` (2, 3, 4). A
# rival wrong only on one of those axes cannot hide behind the others. The refutation
# indices likewise span the range's first entry, its last entry, and an interior one
# (index 2 of 4), so no boundary-only pin is mistaken for the whole per-position clause.
#
# No witness names the EMPTY cycle list. That is deliberate, not a gap: the modeled
# routine selects this input shape by its argument's first element being itself a
# sequence, so an empty argument list never reaches the modeled path at all (it takes the
# other, out-of-scope shape). A rival keyed on `cycles = []` would therefore be attesting
# to behaviour outside the domain mapping.md declares, which is why the C1 probe on the
# cycle-count axis is stated at a SINGLE cycle instead — a point squarely inside the
# modeled domain and one five other witnesses already occupy.
#
# The two degenerate-leg witnesses added by repair extend that spread along a NEW axis:
# whether the supplied cycles name any point at all. `[[]]` supplies a cycle that names
# nothing (the C0 side) and `[[0]]` names exactly one point, the narrowest DETERMINED
# width (the success side at the leg boundary). Both are squarely in the modeled domain —
# each cycle vacuously or actually lists distinct points — and neither is the empty cycle
# LIST, so the out-of-scope shape is still untouched.

def _wit_index(cyc, produced, idx):
    """Refute via C3: the impl's entry at `idx` is not the composed image of `idx`."""
    return (
        f"example : ¬ problem_spec_permFromCycles {cyc}\n"
        f"    (implementation_permFromCycles {cyc}) := by\n"
        f"  have himpl : implementation_permFromCycles {cyc} = some {produced} := by\n"
        "    simp [implementation_permFromCycles, Id.run, permSize]\n"
        "    decide\n"
        "  rw [himpl]\n"
        "  rintro ⟨-, hsucc⟩\n"
        "  obtain ⟨aform, heq, hlen, hidx⟩ := hsucc (by decide)\n"
        "  injection heq with h\n"
        "  subst h\n"
        f"  exact absurd (hidx {idx} (by decide)) (by decide)"
    )


def _wit_len(cyc, produced):
    """Refute via C2: the impl's entry count is not `permSize cycles`."""
    return (
        f"example : ¬ problem_spec_permFromCycles {cyc}\n"
        f"    (implementation_permFromCycles {cyc}) := by\n"
        f"  have himpl : implementation_permFromCycles {cyc} = some {produced} := by\n"
        "    simp [implementation_permFromCycles, Id.run, permSize]\n"
        "    decide\n"
        "  rw [himpl]\n"
        "  rintro ⟨-, hsucc⟩\n"
        "  obtain ⟨aform, heq, hlen, hidx⟩ := hsucc (by decide)\n"
        "  injection heq with h\n"
        "  subst h\n"
        "  exact absurd hlen (by decide)"
    )


# C1 at two cycles sharing the point 0 — the sub-domain the change opens up. The
# rival produces nothing at all, so `result = some aform` is unsatisfiable there.
_WIT_PREPATCH = (
    "example : ¬ problem_spec_permFromCycles [[0, 1], [0, 2]]\n"
    "    (implementation_permFromCycles [[0, 1], [0, 2]]) := by\n"
    "  have himpl : implementation_permFromCycles [[0, 1], [0, 2]] = none := by\n"
    "    simp [implementation_permFromCycles, Id.run, sizeUndetermined]\n"
    "    rfl\n"
    "  rw [himpl]\n"
    "  rintro ⟨-, hsucc⟩\n"
    "  obtain ⟨aform, heq, -, -⟩ := hsucc (by decide)\n"
    "  exact absurd heq (by simp)"
)

# C3, two genuinely DISJOINT cycles (so the shared-point axis is varied away from the
# witness above — `[[0,1],[2,3]]` flattens to four distinct points): the second cycle
# moves points 2 and 3, which the head-only rival never applies, so the refutation is
# pinned at index 2. Also the only witness here with permSize 4, and the only one
# refuting at an index that is neither the first nor the last.
_WIT_FIRST_ONLY = _wit_index("[[0, 1], [2, 3]]", "[1, 0, 2, 3]", 2)
# C3, two cycles sharing point 0 but listed in the opposite order from the C1 witness:
# they do not commute, so folding right-to-left disagrees at index 0.
_WIT_REVERSE = _wit_index("[[0, 2], [0, 1]]", "[1, 2, 0]", 0)
# C3 at index 0, a SINGLE two-element cycle (varies the cycle-count and permSize axes
# to 1 and 2): the rival leaves entry 0 unmoved where the cycle moves it.
_WIT_SKIP_FIRST = _wit_index("[[0, 1]]", "[0, 0]", 0)
# C3 at the LAST index, a single cycle that fixes point 0 and moves the top point:
# the rival leaves the final entry unmoved. A different index AND a different input
# from the skip-first witness, so neither rival can borrow the other's refutation.
_WIT_SKIP_LAST = _wit_index("[[1, 2]]", "[0, 2, 2]", 2)
# C3 with a single THREE-element cycle (varies cycle length): the rival returns the
# identity where the cycle moves every point.
_WIT_IDENTITY = _wit_index("[[0, 2]]", "[0, 1, 2]", 0)
# C2 from below, single three-element cycle: 2 entries where 3 points are named.
_WIT_TRUNCATE = _wit_len("[[0, 1, 2]]", "[1, 2]")
# C2 from above, the same three points listed in a different rotation (a distinct
# input point): 4 entries where 3 points are named. Every index C3 quantifies over is
# correct here, so only the length clause can refute it.
_WIT_PAD = _wit_len("[[2, 0, 1]]", "[1, 2, 0, 0]")
# C2, an input containing a SINGLETON cycle: `[[0,1],[2]]` names three points, so the
# array form has 3 entries, but the rival that discards singletons emits only 2. The
# singleton's ACTION is nothing, which is why only the length clause sees this.
_WIT_DROP_SINGLETON = _wit_len("[[0, 1], [2]]", "[1, 0]")
# C1 at a SINGLE cycle. `[[1, 3]]` names the points 1 and 3, so `permSize` is 4 and the
# spec demands `some [0, 3, 2, 1]`; the rival that declines below two cycles yields
# nothing there. A sixth distinct single-cycle input, and the only witness in the battery
# whose cycle skips TWO points below the derived size (0 and 2). `decide` is not needed to
# reduce the impl here — the guard fires immediately — so the reduction closes by `rfl`,
# as in the pre-change witness above.
_WIT_NONE_SINGLE = (
    "example : ¬ problem_spec_permFromCycles [[1, 3]]\n"
    "    (implementation_permFromCycles [[1, 3]]) := by\n"
    "  have himpl : implementation_permFromCycles [[1, 3]] = none := by\n"
    "    simp [implementation_permFromCycles, Id.run]\n"
    "    rfl\n"
    "  rw [himpl]\n"
    "  rintro ⟨-, hsucc⟩\n"
    "  obtain ⟨aform, heq, -, -⟩ := hsucc (by decide)\n"
    "  exact absurd heq (by simp)"
)


# The degenerate leg, at a supplied-but-pointless cycle list. The rival that dropped the
# guard emits `some []` there; the leg demands nothing be returned. This is the ONLY
# witness in the battery that refutes through the degenerate leg rather than the success
# leg, and the only one whose input names no point at all.
_WIT_ALWAYS_BUILD = (
    "example : ¬ problem_spec_permFromCycles [[]]\n"
    "    (implementation_permFromCycles [[]]) := by\n"
    "  have himpl : implementation_permFromCycles [([] : List Nat)] = some [] := by\n"
    "    simp [implementation_permFromCycles, Id.run, permSize]\n"
    "    rfl\n"
    "  rw [himpl]\n"
    "  rintro ⟨hdeg, -⟩\n"
    "  exact absurd (hdeg (by decide)) (by simp)"
)

# The success leg at the narrowest determined width: `[[0]]` names exactly the point 0,
# so the width IS determined (it is 1) and the array form is `[0]`. The rival that treats
# every width below 2 as degenerate returns nothing there. A distinct input point from
# every other witness, and the only one probing the boundary between the two legs.
_WIT_DEGEN_WIDE = (
    "example : ¬ problem_spec_permFromCycles [[0]]\n"
    "    (implementation_permFromCycles [[0]]) := by\n"
    "  have himpl : implementation_permFromCycles [[0]] = none := by\n"
    "    simp [implementation_permFromCycles, Id.run, permSize]\n"
    "    rfl\n"
    "  rw [himpl]\n"
    "  rintro ⟨-, hsucc⟩\n"
    "  obtain ⟨aform, heq, -, -⟩ := hsucc (by decide)\n"
    "  exact absurd heq (by simp)"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-pure-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "The cheapest honest impl: a pure map of the composed action over the range of "
            "named points — no `Id.run do`, no `let mut`, no accumulator, no loop. Ports "
            "nagini's cheapest-honest-impl positive; because `applyAll` is a grounded total "
            "function of `cycles` (not an ungrounded oracle) this shape IS correct, so there "
            "is no wrong echo to worry about. The `theorem correct_permFromCycles` STATEMENT "
            "is byte-identical and the proof is reproven honestly: the result is now "
            "definitionally the spec's right-hand side, so the frozen loop-normalisation "
            "derivation is dead and only the frozen CLOSING steps (discharging C1 by `rfl`, "
            "C2 by `simp`, C3 by index lookup) remain. No new axiom, lemma, sorry or "
            "native_decide. If it FAILS => SPEC-TOO-STRONG (the postcondition would be "
            "over-fitted to an imperative accumulator shape rather than to the behaviour)."
        ),
    },
    {
        "id": "pos-direct-image",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "A structurally different CORRECT impl that keeps the imperative accumulator "
            "shape but FUSES the inner per-cycle fold into one application of the composed "
            "action, so the nested loop disappears entirely: a single forward pass appending "
            "the fully-composed image of each point. This is the direct counterpart of "
            "nagini's `pos-single-loop`. Same output on every input; the theorem statement is "
            "byte-identical and the reproof is the frozen one with the inner-loop lemma and "
            "its congruence step removed (nothing left to normalise there) — no new axiom, "
            "lemma, sorry or native_decide. If it FAILS => SPEC-TOO-STRONG (the spec would be "
            "pinned to the two-level loop nesting rather than to the composed image)."
        ),
    },
    {
        "id": "pos-array-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ARRAY,
        "rationale": (
            "A second independent correct shape, in the role of nagini's "
            "`pos-fused-two-phase`: both loops are kept, but the accumulator's DATA STRUCTURE "
            "changes from a list appended at the end to an array pushed onto, converted once "
            "at the return. A spec over-fitted to one accumulator idiom would reject this "
            "while accepting `pos-direct-image`, which is why two positives with different "
            "failure modes are shipped rather than one. Theorem statement byte-identical; the "
            "reproof mirrors the frozen argument with the accumulator lemma restated over the "
            "array carrier. No new axiom, lemma, sorry or native_decide. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-in-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "Ports nagini's `admiss-f2p-witness`. A top-level caller would leave the impl and "
            "proof regions and break same_spec, so the probe is done IN-REGION at the head of "
            "the proof body: it (a) CONSUMES the precondition hypothesis, showing it is a "
            "usable fact and not a dead binder; (b) shows a normal F2P-shaped input — two "
            "cycles that SHARE a point, the very configuration the modeled behaviour must "
            "accept — satisfies that precondition; (c) reduces the impl at that input to a "
            "concrete array form; and (d) discharges all three clauses of "
            "`problem_spec_permFromCycles` there with explicit witnesses (`result = some "
            "aform` with a named `aform`, `aform.length = permSize cycles`, and the per-index "
            "`applyAll` pin) — so the postcondition is shown SATISFIABLE and non-vacuous at a "
            "real in-domain point. The frozen tactic body then follows verbatim, so the full "
            "obligation is still proven and the statement is untouched. If this fails to "
            "verify, the precondition rules out an input the modeled behaviour must accept "
            "(PRECOND-TOO-STRONG) or the postcondition is unsatisfiable there."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "rej-reject-shared-point",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_PREPATCH,
        "refinement": (
            "Declines to build anything when some point is named by more than one cycle, and "
            "composes correctly otherwise. This is the PRE-CHANGE behaviour, so its faithful "
            "real patch is the unchanged routine — the exact code the change replaces. Under "
            "it the newly added F2P assertion, which requires that a two-cycle input sharing "
            "a point construct the permutation obtained by chaining the two rules (equal to "
            "the single cycle through those three points), still errors out instead of "
            "constructing anything, so the assertion FAILS. It would NOT resolve; this is "
            "precisely the behaviour the change enables (the G-DIFF discriminator)."
        ),
        "rationale": (
            "REJECTED by clause C1 (`result = some aform`): the spec demands a value for "
            "every admissible input, and the precondition requires only that each cycle list "
            "distinct points — it does NOT require the cycles to be pairwise disjoint, so an "
            "input whose cycles share a point is in-domain. The witness reduces the rival at "
            "such an input, where it yields nothing, and the existential is then "
            "unsatisfiable. This is the FAITHFUL port of nagini's `rej-disjoint-only`: nagini "
            "had to express the same defect as 'leave the second swap unapplied' because its "
            "`List[int]` carrier had no failure channel, whereas the `Option` carrier here "
            "states it directly — a strictly stronger attack, reaching a clause nagini could "
            "not state. If it VERIFIES => SPEC-TOO-WEAK (the spec would not sense the change "
            "at all)."
        ),
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "rej-first-cycle-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_FIRST_ONLY,
        "refinement": (
            "Applies only the FIRST listed cycle's rule and ignores every later one. Its "
            "faithful real patch composes just the leading cycle, so a two-cycle input builds "
            "the permutation of the first cycle alone rather than the chained result — for "
            "the F2P input that is the single transposition instead of the three-cycle, and "
            "the assertion FAILS. Every multi-cycle case in the existing regression suite "
            "breaks likewise. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 (`aform.getD i 0 = applyAll cycles i`): `applyAll` folds "
            "EVERY cycle, so dropping the tail is wrong as soon as a later cycle moves a "
            "reachable point. General form of nagini's `rej-drop-second-swap` on this carrier "
            "— nagini had exactly two named swaps, here the tail is arbitrary. The witness "
            "uses `[[0,1],[2,3]]`, two cycles that share NO point, deliberately moving off "
            "the shared-point sub-domain that the C1 rival's witness occupies, so this "
            "rival's refutation cannot be confused with that one's: it is wrong even where "
            "every cycle is disjoint. It is pinned at index 2 — neither end of the range — "
            "so it is also the one witness here that neither boundary-index rival could "
            "borrow. If it VERIFIES => SPEC-TOO-WEAK (the spec would not require every "
            "listed cycle to participate)."
        ),
        "witness": _WIT_FIRST_ONLY,
    },
    {
        "id": "rej-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_REVERSE,
        "refinement": (
            "Chains the cycles' rules in the opposite order — last listed applied first. Its "
            "faithful real patch composes the cycles right-to-left, which for the F2P input "
            "yields the OTHER three-cycle on the same points, so the equality assertion "
            "FAILS. Multi-cycle cases throughout the existing suite (any two listed cycles "
            "that do not commute) break the same way. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3, specifically its ORDER content: `applyAll` folds "
            "left-to-right, first-listed-first. Note this rival applies every cycle and "
            "returns a genuine permutation of exactly the right length, so C1 and C2 both "
            "hold and only the per-position pin can refute it — and it agrees with the spec "
            "on every input whose cycles commute, including every single-cycle input, so a "
            "witness at any one-cycle point would miss it entirely. The witness therefore "
            "uses two non-commuting cycles, listed in the opposite order from the C1 "
            "witness's input so the two probe distinct points. General form of nagini's "
            "`rej-wrong-order`. If it VERIFIES => SPEC-TOO-WEAK (the composition order would "
            "be unpinned)."
        ),
        "witness": _WIT_REVERSE,
    },
    {
        "id": "rej-skip-first-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_SKIP_FIRST,
        "refinement": (
            "Leaves the FIRST entry of the array form at its own index and composes every "
            "later position. Its faithful real patch is an off-by-one that mishandles the "
            "leading point, so the built permutation disagrees with the intended one at point "
            "0 whenever the cycles move it — as they do for the F2P input, whose first entry "
            "must be the image of 0 under the chained rules. The assertion FAILS and it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 at i = 0. PARTIAL-DOMAIN in the output index: correct at "
            "every position except the first, so a rival-by-rival uniform-wrongness argument "
            "does not reach it and only a witness pinned at index 0 does. Ports nagini's "
            "`rej-skip-first-pos`. The witness uses a SINGLE two-element cycle, moving the "
            "cycle-count and derived-length axes (1 cycle, 2 entries) away from every other "
            "witness in this battery, so the refutation is attributable to the index and not "
            "to the input's shape. If it VERIFIES => SPEC-TOO-WEAK (the pin would not hold at "
            "the first position)."
        ),
        "witness": _WIT_SKIP_FIRST,
    },
    {
        "id": "rej-skip-last-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_SKIP_LAST,
        "refinement": (
            "Leaves the FINAL entry of the array form at its own index and composes every "
            "earlier position. Its faithful real patch truncates the fill loop one short, so "
            "the built permutation disagrees at the largest named point whenever the cycles "
            "move it. For the F2P input the last entry must be the image of the top point "
            "under the chained rules, so the assertion FAILS and it would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 at i = permSize cycles - 1. The mirror of "
            "`rej-skip-first-index` and a genuinely separate sub-domain: this rival is CORRECT "
            "at index 0, so that rival's witness does not refute it, and vice versa — "
            "together they pin that the per-position claim holds at BOTH ends of the range "
            "rather than merely somewhere. Ports nagini's `rej-skip-last-pos`. The witness "
            "uses a single cycle that FIXES point 0 and moves the top point, a third distinct "
            "input, so the disagreement is isolated to the final index. If it VERIFIES => "
            "SPEC-TOO-WEAK (the pin would not hold at the last position)."
        ),
        "witness": _WIT_SKIP_LAST,
    },
    {
        "id": "rej-truncate-array-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TRUNCATE,
        "refinement": (
            "Composes every position correctly and then drops the final entry, so the array "
            "form is one shorter than the number of points named. Its faithful real patch "
            "builds the listing one element short, so the constructed object is a permutation "
            "on fewer points than the input names and does not equal the intended one — the "
            "F2P assertion, and every existing regression assertion that compares a "
            "constructed permutation to an explicit array form, FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (`aform.length = permSize cycles`). NEW on this carrier "
            "and not a nagini port: nagini received its length as an explicit input binder, "
            "so an impl could not disobey it without disobeying an argument it was handed, "
            "whereas here `permSize cycles` is DERIVED from the input and is therefore a real "
            "degree of freedom. Without this case C2 is stated but never probed. Note the "
            "rival composes every entry it does emit correctly, so C3 holds at every index it "
            "covers and only the length clause refutes it. Witness uses a single "
            "three-element cycle, a fourth distinct input. If it VERIFIES => SPEC-TOO-WEAK "
            "(the entry count would be unpinned from below)."
        ),
        "witness": _WIT_TRUNCATE,
    },
    {
        "id": "rej-pad-array-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_PAD,
        "refinement": (
            "Composes every position correctly and then appends one extra entry, so the array "
            "form is one longer than the number of points named. Its faithful real patch "
            "extends the listing past the largest named point, so the constructed object acts "
            "on a larger point set than the input names and does not equal the intended one. "
            "The F2P assertion compares against a permutation on exactly the named points, so "
            "it FAILS; existing regression assertions that pin the constructed size break "
            "likewise. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2, and by C2 ALONE — this is the point of shipping it "
            "alongside `rej-truncate-array-form`. The extra entry sits at an index BEYOND "
            "`permSize cycles`, which C3 does not quantify over, so every index the per-"
            "position pin mentions is satisfied and no C3-based witness can see this rival. "
            "It is therefore the sharpest available probe that C2 fixes the length EXACTLY "
            "rather than as a lower bound: a spec saying only `permSize cycles ≤ "
            "aform.length` would admit it. NEW on this carrier for the same reason as the "
            "truncation rival (the length is derived, not supplied). Witness lists the same "
            "three points in a different rotation, a fifth distinct input point. If it "
            "VERIFIES => SPEC-TOO-WEAK (the entry count would be unpinned from above)."
        ),
        "witness": _WIT_PAD,
    },
    {
        "id": "rej-drop-singleton-cycles",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_SINGLETON,
        "refinement": (
            "Discards every one-element cycle before composing. Its faithful real patch "
            "filters the listed cycles down to those that actually move a point, which is "
            "harmless for the composition itself but shrinks the constructed permutation "
            "whenever a discarded singleton named the largest point: the constructed object "
            "then acts on fewer points than the input names. Measured against the real suite "
            "by patching this behaviour into the routine and running the F2P and P2P tests: "
            "three existing assertions that list a singleton alongside a longer cycle and "
            "compare against an explicit array form on all the named points FAIL, across two "
            "P2P tests. It would NOT resolve. Note the F2P assertion's own input names no "
            "singleton, so this rival AGREES with the fix there and the F2P test passes — the "
            "regression it breaks is a P2P one. That is exactly why the case is needed: the "
            "clause it violates is real but invisible to the discriminating input alone."
        ),
        "rationale": (
            "REJECTED by clause C2 (`aform.length = permSize cycles`), and reached through a "
            "sub-domain no other case in this battery touches: an input containing a cycle "
            "that NAMES a point without MOVING it. Dropping such a cycle is invisible to C3 "
            "— a singleton's action is the identity, so every entry this rival does emit is "
            "the correct composed image — but `permSize` counts named points, not moved ones, "
            "so the entry COUNT is wrong. That makes it a sharper C2 probe than the "
            "truncate/pad pair: those two disobey the length by a literal ±1 after computing "
            "it correctly, whereas this one computes the wrong length from the input and is "
            "self-consistent about it, so it would survive a spec that merely required the "
            "length to agree with the emitted entries. Witness `[[0,1],[2]]`: 3 points named, "
            "2 entries emitted. If it VERIFIES => SPEC-TOO-WEAK (the derived size would be "
            "pinned to the MOVED points rather than the NAMED ones)."
        ),
        "witness": _WIT_DROP_SINGLETON,
    },
    {
        "id": "rej-none-on-single-cycle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_NONE_SINGLE,
        "refinement": (
            "Composes correctly whenever at least two cycles are supplied but declines to "
            "build when handed a single one. Its faithful real patch guards the composition on "
            "there being more than one cycle to chain and errors out otherwise, so a "
            "one-cycle construction raises instead of building that cycle's permutation. "
            "Measured against the real suite by patching this behaviour into the routine and "
            "running the F2P and P2P tests: two of the suite's one-cycle constructions raise, "
            "so the F2P test FAILS. It would NOT resolve. (Note the F2P assertion itself "
            "supplies TWO cycles and so agrees with this rival — the failure comes from the "
            "one-cycle assertions inside the same F2P test, which is why the case is stated "
            "here rather than left to the F2P input alone.)"
        ),
        "rationale": (
            "REJECTED by clause C1 (`result = some aform`) on the CYCLE-COUNT axis of the "
            "input binder. The precondition `∀ c ∈ cycles, c.Nodup` says nothing about how "
            "many cycles there are, so a one-cycle input is in-domain and the spec demands a "
            "value there — `permSize [[1,3]] = 4`, so C2 and C3 are both satisfied by `some "
            "[0, 3, 2, 1]` and C1 is the only clause that can refute. `rej-reject-shared-point` "
            "already establishes C1 is attackable, but that rival is CORRECT on every input "
            "whose cycles are disjoint, and the shared-point notion does not even apply to a "
            "lone cycle — so its witness cannot reach this rival and vice versa. Together the "
            "two pin C1 across the cycle-count axis rather than at one configuration. If it "
            "VERIFIES => SPEC-TOO-WEAK (success would be unpinned for single-cycle input)."
        ),
        "witness": _WIT_NONE_SINGLE,
    },
    {
        "id": "rej-always-build",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_ALWAYS_BUILD,
        "refinement": (
            "Builds unconditionally, so a cycle list that supplies cycles yet names no point "
            "between them yields the empty listing instead of being declined. Its faithful "
            "real patch removes the guard the routine's listing step applies when it has no "
            "point to size itself from, so that call returns an empty listing rather than "
            "reporting the error the routine actually reports. Measured against the real "
            "suite: the F2P assertion's inputs all name points, so the F2P test still passes "
            "— the regression is a P2P one, in the existing test that asserts the error IS "
            "reported for that shape. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the DEGENERATE leg, and by that leg alone. This rival is the frozen "
            "impl's composing body verbatim, so it agrees with the spec on every input whose "
            "width is determined — precisely the region the length and per-position clauses "
            "quantify over — and therefore NO witness pinned on a length or an index can see "
            "it. That makes it the sharpest available probe that the degenerate leg PINS the "
            "outcome to nothing-returned rather than merely permitting it, and it is the "
            "rival that would verify against a spec which simply dropped the leg instead of "
            "stating it. If it VERIFIES => SPEC-TOO-WEAK (the degenerate shape would be "
            "unpinned, which is exactly the over-strong/under-specified pair this leg fixes)."
        ),
        "witness": _WIT_ALWAYS_BUILD,
    },
    {
        "id": "rej-degenerate-too-wide",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DEGEN_WIDE,
        "refinement": (
            "Declines whenever the cycles name no point beyond the first, so it is right "
            "about the pointless shape but ALSO declines the legitimate one-point input, "
            "where the routine builds a one-entry listing. Its faithful real patch widens the "
            "listing step's guard from 'no point at all' to 'no point above the first', so a "
            "construction naming only that point raises instead of building. Measured against "
            "the real suite: existing assertions that construct from a cycle on the first "
            "point alone raise, so the F2P test FAILS. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the SUCCESS leg, at the boundary between the two legs — the "
            "narrowest input whose width IS determined. It satisfies the degenerate leg "
            "exactly, so `rej-always-build`'s witness cannot reach it and vice versa: "
            "together the two pin the leg SELECTOR itself, forbidding both a leg that is too "
            "narrow and one that is too wide. This is the case that stops the degenerate leg "
            "from being over-applied, which is the way a two-leg postcondition most easily "
            "goes wrong. If it VERIFIES => SPEC-TOO-WEAK (the boundary between the legs would "
            "be unpinned and success could be declined for a determined width)."
        ),
        "witness": _WIT_DEGEN_WIDE,
    },
    {
        "id": "rej-identity-fill",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_IDENTITY,
        "refinement": (
            "Returns the points in their original order, ignoring the cycles' rules entirely. "
            "Its faithful real patch builds the do-nothing permutation for any input, so no "
            "constructed permutation ever moves anything: the F2P assertion, which requires "
            "the two chained cycles to produce a three-cycle, FAILS, as does essentially "
            "every existing assertion in the suite. It would NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C3 only. This rival satisfies C1 (it always returns `some "
            "aform`) and C2 exactly (`aform.length = permSize cycles`), and what it returns "
            "is a genuine permutation of precisely the named points — so it probes whether "
            "the shape and range clauses alone could be mistaken for the spec, exactly the "
            "role nagini's `rej-identity-range-fill` played. The per-position `applyAll` pin "
            "is what forbids it, which is the strongest available evidence that C3 rather "
            "than C1/C2 is the load-bearing clause. Witness uses the single two-element cycle "
            "`[[0,2]]` over a three-point range (a distinct input point from every other "
            "witness here, and the only one whose cycle skips an INTERIOR point — point 1 is "
            "named by nothing yet sits below the derived size, so the derived size exceeds the "
            "cycle's own length for a reason no other witness exercises) — the composed image "
            "therefore differs from the identity at index 0. If it VERIFIES => SPEC-TOO-WEAK (the "
            "composition would be unpinned altogether and only the shape would be tested)."
        ),
        "witness": _WIT_IDENTITY,
    },
]


# The bundle consumes no callee axiom: the action of a single cycle, the left-to-right
# composition and the derived size are all modeled DEEPLY over transparent carriers
# (an A-reference validated by G-CONF against the real routine), so there is nothing
# for this spec lane to probe there. The axiom lane belongs to G-AX regardless.
AXIOM_TESTS = []
