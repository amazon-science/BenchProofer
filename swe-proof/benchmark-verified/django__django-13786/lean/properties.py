# properties.py — G-PBT falsification battery for django__django-13786 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for the positive that reproves, the body of an existing proof
# lemma — is edited), checked by variant_scope + the Lean verifier. Every
# expect="reject" case carries a refutation `witness`: a self-contained snippet that
# ELABORATES against the rival and FAILS on the frozen solution, so the rejection is
# attributable to the spec and not to a tactic script that merely stopped matching a
# reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   combineOptions : (base override : List (String × V)) → (managedKeys : List String)
#                    → List (String × V)
#   Overlay the overriding mapping on the base mapping (overriding value wins for a
#   shared key; base-only keys survive), then clear every MANAGED key the overriding
#   mapping is silent about. The single postcondition has TWO independent top-level
#   clauses: (A) the result's keys are DISTINCT (it is a genuine dictionary); and
#   (B) for every key k, the result's lookup equals the desired
#   overlay-then-clear-managed value — overriding wins if present, else `none` for a
#   managed key, else the base value. Both clauses are grounded in the actual inputs
#   (base / override / managedKeys), so there is no oracle to echo.
#
# CARRIER NOTE (how the nagini rivals map here): nagini's carrier was a Dict[int,int]
# behind fractional permissions, with the managed family fixed to two concrete
# tokens {key_managed_a()=0, key_managed_b()=1} and a representative non-managed
# name key_other()=2. This backend models the general polymorphic assoc-list carrier
# with `managedKeys` an arbitrary list of names, so nagini's per-token clauses become
# statements over an arbitrary key that IS / IS NOT in `managedKeys`. Each nagini
# uniqueness rival re-expresses directly:
#   weak-bare-merge-no-clear  -> weak-bare-merge      (never clear any managed key)
#   weak-forget-managed-b     -> weak-forget-tail     (clear only the first managed key)
#   weak-overclear-provided-* -> weak-overclear       (clear every managed key uncond.)
#   weak-clear-nonmanaged-other -> weak-keep-override (return only the overriding map)
#   weak-empty-result         -> weak-empty           (return the empty mapping)
# The lean spec additionally carries the key-DISTINCTNESS clause (a Python dict has no
# duplicate keys); that clause has no nagini counterpart (nagini's dict carrier was
# distinct by construction) and is attacked by weak-dup-keys — see its refinement.
# Two further rivals have NO nagini counterpart and were added by the audit, which
# found the corresponding arms of clause (B) unprobed by the ported set:
#   weak-reverse-precedence               (which of two values wins a shared key)
#   weak-clear-only-if-silent-everywhere  (per-KEY granularity of the managed clear;
#                                          every ported rival diverges already at an
#                                          EMPTY override, so a rival wrong only for a
#                                          partially-populated override was unreached)
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's mandatory class: operation_options was held at
#     Acc(dict_pred,1/2), so writing it was an INSUFFICIENT-PERMISSION reject). Lean
#     is referentially transparent — no aliasing, no fractional permission — so a
#     "write-back into a read-only input" rival is not expressible; the lane is
#     VACUOUS here. See 'assessment'.
#   (ADMISSIBILITY DOES port — see admiss-ground-f2p-shaped below. An earlier
#   revision of this manifest recorded the lane as N/A on the grounds that "the
#   precondition is a pair of hypotheses in the theorem binder and there is no caller
#   construct on this carrier that a variant could use to exercise it". That reason was
#   wrong, and the audit landed the case: the analogue of PRECOND-TOO-STRONG on a total
#   carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped input, which
#   a positive that discharges it at that concrete input — by evaluation, as a `have`,
#   before closing the frozen obligation verbatim — tests directly. No caller construct
#   is needed.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. (This bundle
#     consumes no callee axiom anyway — the overlay-then-clear is modeled deeply.)
from pathlib import Path

INSTANCE = "django__django-13786"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchor: the entire gold impl BODY (lies inside impl-start/impl-end
# and is unique in the file). Editing only this keeps same_spec. ---------------------
_IMPL_BODY = (
    "Id.run do\n"
    "  let mut options := mergeOpts base override\n"
    "  for key in managedKeys do\n"
    "    if ! keyPresent override key then\n"
    "      options := dropKey options key\n"
    "  return options"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drifted"

# The frozen `loop_is_foldl` proof body (in the proof region). Only the positive
# control edits this — to reprove the same lemma statement for the reshaped impl. ----
_LIF_BODY = (
    "  simp only [implementation_combineOptions, Id.run]\n"
    "  generalize mergeOpts base override = init\n"
    "  induction managedKeys generalizing init with\n"
    "  | nil => rfl\n"
    "  | cons k ks ih =>\n"
    "    simp only [List.forIn_cons, List.foldl_cons, stepFn]\n"
    "    split <;> exact ih _"
)
assert _BASE.count(_LIF_BODY) == 1, "loop_is_foldl body anchor drifted"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------
# The gold impl is an imperative `Id.run do … for … mut …` loop. This control is a
# structurally-DIFFERENT but observationally-identical functional shape: the same
# overlay-then-clear expressed as a single `List.foldl` over `managedKeys`. It is the
# exact right-hand side the frozen `loop_is_foldl` lemma equates the loop to, so the
# two impls are definitionally equal and the reshaped `loop_is_foldl` closes by `rfl`
# (every other proof lemma, and the `correct_combineOptions` statement, is unchanged).
# If it FAILS => SPEC-TOO-STRONG (a faithful, structurally-different correct impl
# rejected).
_POS_IMPL = (
    "\n"
    "  managedKeys.foldl\n"
    "    (fun options key => if ! keyPresent override key then dropKey options key "
    "else options)\n"
    "    (mergeOpts base override)"
)
_POS = _swap(_swap(_BASE, _IMPL_BODY, _POS_IMPL), _LIF_BODY, "  rfl")


# ---------------------------------------------------------------------------
# ADMISSIBILITY (soundness, second direction) — must VERIFY.
# ---------------------------------------------------------------------------
# On a total carrier the analogue of PRECOND-TOO-STRONG is not an unmeetable
# `Requires` but the obligation being UNSATISFIABLE at exactly the shape the
# FAIL_TO_PASS scenario has: an initial step carrying one MANAGED key and one
# non-managed key, and an overriding step with an EMPTY option set. This case
# discharges `problem_spec_combineOptions` at that concrete input FIRST — by
# evaluation (`decide` on the impl's value, then the lookup clause at each of the
# three key positions) — and only then closes the frozen obligation verbatim. The
# frozen `theorem correct_combineOptions` STATEMENT is byte-identical and every
# proof lemma is untouched; the ground instance is a `have` inside the existing
# tactic body, so nothing is assumed and no declaration is added.
# If it FAILS => the modeled behavior is unsatisfiable at a normal F2P-shaped
# input (PRECOND-TOO-STRONG's analogue here).
_CORRECT_BODY = (
    "  intro V base override managedKeys hbase hoverride\n"
    "  refine ⟨result_Nodup base override managedKeys hbase hoverride, ?_⟩\n"
    "  exact lookup_eq_expected base override managedKeys hbase hoverride"
)
assert _BASE.count(_CORRECT_BODY) == 1, "correct_ body anchor drifted"

_ADMISS_GROUND = (
    '  have _ground : problem_spec_combineOptions\n'
    '      ([("m", "A"), ("x", "C")] : List (String × String)) [] ["m"]\n'
    '      (implementation_combineOptions\n'
    '        ([("m", "A"), ("x", "C")] : List (String × String)) [] ["m"]) := by\n'
    '    have himpl : implementation_combineOptions\n'
    '        ([("m", "A"), ("x", "C")] : List (String × String)) [] ["m"]\n'
    '        = [("x", "C")] := by decide\n'
    '    rw [himpl]\n'
    '    refine ⟨by decide, ?_⟩\n'
    '    intro k\n'
    '    by_cases h1 : k = "m"\n'
    '    · subst h1; decide\n'
    '    · by_cases h2 : k = "x"\n'
    '      · subst h2; decide\n'
    '      · have b1 : ("m" == k) = false := by simp [Ne.symm h1]\n'
    '        have b2 : ("x" == k) = false := by simp [Ne.symm h2]\n'
    '        simp [optLookup, expectedLookup, dropKey, List.find?_cons, b1, b2]\n'
) + _CORRECT_BODY
_ADMISS = _swap(_BASE, _CORRECT_BODY, _ADMISS_GROUND)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly, edits only the impl BODY, and carries a discriminating witness.
# The frozen proof is left intact: against a reshaped/wrong impl it no longer closes,
# so the variant does not verify, and the witness is what attributes the rejection to
# the spec (not to the tactic gap).
# ---------------------------------------------------------------------------

# weak-bare-merge: overlay only, never clear an omitted managed key (the PRE-PATCH
# behaviour). Fails clause (B) at a managed key that is on base and silent in override.
_BARE = "\n  mergeOpts base override"

# weak-forget-tail: clear only the FIRST managed key; any later managed key silent in
# override survives. Correct except on that tail sub-domain — the analogue of nagini's
# weak-forget-managed-b. Fails clause (B) at a later managed key.
_FORGET = (
    "Id.run do\n"
    "  let mut options := mergeOpts base override\n"
    "  for key in managedKeys.take 1 do\n"
    "    if ! keyPresent override key then\n"
    "      options := dropKey options key\n"
    "  return options"
)

# weak-overclear: clear every managed key UNCONDITIONALLY, even when override provides
# it. Fails clause (B) at a managed key the override DOES supply (its value must win).
_OVERCLEAR = (
    "Id.run do\n"
    "  let mut options := mergeOpts base override\n"
    "  for key in managedKeys do\n"
    "    options := dropKey options key\n"
    "  return options"
)

# weak-keep-override: return ONLY the overriding mapping — every base-only key is
# dropped, managed or not. Satisfies clause (B) for overridden and managed keys and
# keeps keys distinct, but fails clause (B) at a NON-managed base-only key, which must
# survive. The analogue of nagini's weak-clear-nonmanaged-other.
_KEEP_OVERRIDE = "\n  override"

# weak-empty: return the empty mapping regardless of input. Vacuously distinct and
# clears every managed key, but fails clause (B) at any provided/kept key.
_EMPTY = "\n  []"

# weak-dup-keys: overlay by BARE CONCATENATION (override ++ base) with no filtering of
# base keys the override already carries. First-match lookup still agrees with the
# overlay, so clause (B) holds — but a shared key now appears TWICE, so the result's
# keys are NOT distinct and clause (A) fails.
_DUP = (
    "Id.run do\n"
    "  let mut options := override ++ base\n"
    "  for key in managedKeys do\n"
    "    if ! keyPresent override key then\n"
    "      options := dropKey options key\n"
    "  return options"
)


# weak-reverse-precedence: overlays the two mappings the WRONG WAY ROUND, so the
# INITIAL step's value wins a key both mention (the clearing loop is otherwise intact,
# and still keys off the overriding mapping, so every managed-clear arm is correct).
# Added by the audit: no existing rival attacks the overlay's PRECEDENCE — the
# shared-key arm was probed only for key-distinctness (weak-dup-keys), never for WHICH
# value survives. Fails clause (B) at a key both mappings carry.
_REVERSE_PRECEDENCE = (
    "Id.run do\n"
    "  let mut options := mergeOpts override base\n"
    "  for key in managedKeys do\n"
    "    if ! keyPresent override key then\n"
    "      options := dropKey options key\n"
    "  return options"
)

# weak-clear-only-if-silent-everywhere: clears the managed family only when the
# overriding mapping is ENTIRELY empty, instead of per-key. Correct on the whole
# empty-override sub-domain (so weak-bare-merge's witness input does NOT catch it) and
# correct wherever the override mentions every managed key; wrong exactly where the
# override is NON-EMPTY yet silent about some managed key. Added by the audit: the
# existing rivals all diverge at an empty or single-key override, leaving the
# partially-populated override — which is F2P case 2's shape — unprobed.
_CLEAR_ONLY_IF_EMPTY = (
    "Id.run do\n"
    "  let mut options := mergeOpts base override\n"
    "  if override.isEmpty then\n"
    "    for key in managedKeys do\n"
    "      options := dropKey options key\n"
    "  return options"
)


def _wit(base, override, managed, key, clause="B"):
    """A refutation witness: `¬ problem_spec_combineOptions …` at a concrete input.
    For clause (B) rivals it refutes the lookup-agreement conjunct at `key`; for the
    (A) rival it refutes the key-distinctness conjunct. It elaborates against the
    rival (which diverges from the frozen result there) and FAILS on gold (which
    satisfies the spec everywhere)."""
    args = (f"({base} : List (String × String)) {override} {managed} "
            f"(implementation_combineOptions ({base} : List (String × String)) "
            f"{override} {managed})")
    if clause == "A":
        body = f"  intro h; exact absurd h.1 (by decide)"
    else:
        body = f'  intro h; have hk := h.2 "{key}"; revert hk; decide'
    return (f"example : ¬ problem_spec_combineOptions {args} := by\n{body}")


SPEC_TESTS = [
    {
        "id": "pos-foldl-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "structurally-different but CORRECT impl: the imperative "
            "`Id.run do … for … mut` loop is re-expressed as the equivalent "
            "`List.foldl` over the managed-key family (the exact right-hand side the "
            "frozen `loop_is_foldl` lemma already equates the loop to). It produces "
            "the identical result on every input; the frozen "
            "`theorem correct_combineOptions` statement is kept byte-identical and its "
            "proof still closes (the reshaped `loop_is_foldl` is now `rfl`, every "
            "other lemma unchanged). If it FAILS => SPEC-TOO-STRONG (a faithful "
            "correct impl rejected)."
        ),
    },
    {
        "id": "admiss-ground-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is discharged at an F2P-SHAPED ground input before being "
            "closed verbatim: an initial mapping carrying one MANAGED key and one "
            "non-managed key, with an EMPTY overriding mapping — the combination the "
            "FAIL_TO_PASS scenario has. The `have` EVALUATES the combined result "
            "(`decide` pins it to the single surviving non-managed entry) and then "
            "checks the lookup clause at each of the three key positions (the managed "
            "key, the surviving key, and every other key), so it exercises the spec at "
            "that input rather than restating the obligation at a literal. Nothing is "
            "assumed: the ground instance is a `have` inside the existing tactic body, "
            "the frozen `theorem correct_combineOptions` statement is byte-identical, "
            "every proof lemma is unchanged, and no declaration is added. If it FAILS "
            "=> the modeled behavior is UNSATISFIABLE at exactly a normal F2P-shaped "
            "input, which is what PRECOND-TOO-STRONG amounts to on a total carrier. "
            "Ports nagini's admiss-f2p-shaped, whose half-permission self-call has no "
            "counterpart here but whose QUESTION does."
        ),
    },
    {
        "id": "weak-bare-merge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _BARE),
        "refinement": (
            "this IS the pre-change behaviour: the combined mapping is the bare "
            "overlay with no clearing of managed keys the overriding step omits. Its "
            "faithful real counterpart is the unchanged repo, where a managed option "
            "set on the original step but dropped by a later empty overriding step "
            "SURVIVES into the squashed result — exactly the FAIL_TO_PASS scenario "
            "(an overriding step with an empty option set must leave the squashed "
            "result with NO options). It does NOT resolve, so a verifying rival here "
            "would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (B): at a managed key present on `base` and silent in "
            "`override`, the spec pins the result lookup to `none` (cleared), but the "
            "bare overlay keeps the base value. Attacks the managed-clear behaviour "
            "the fix introduces. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # managed key "k" on base, override empty: gold clears -> none, rival keeps.
        "witness": _wit('[("k","A")]', "[]", '["k"]', "k"),
    },
    {
        "id": "weak-forget-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _FORGET),
        "refinement": (
            "clears only the FIRST managed key and forgets the rest — the analogue of "
            "a real patch that iterated over a truncated managed-key family. It is "
            "correct except on the sub-domain where a LATER managed key is set on the "
            "original step and omitted by the overriding step; there it leaves that "
            "option in the squashed result, matching the FAIL_TO_PASS scenario where "
            "an original step carries two managed options and the overriding step "
            "supplies only the first (the second must be cleared). Does NOT resolve."
        ),
        "rationale": (
            "partial-domain: REJECTED by clause (B) at a LATER managed key silent in "
            "`override` — the spec pins its lookup to `none`, the rival keeps the "
            "base value. Attacks the same managed-clear clause as weak-bare-merge but "
            "on the tail of the managed family, so a rival that mishandled only "
            "non-first managed keys is caught. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # managed=["a","b"], base has "b" (the tail), override empty: gold clears "b".
        "witness": _wit('[("b","X")]', "[]", '["a","b"]', "b"),
    },
    {
        "id": "weak-overclear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _OVERCLEAR),
        "refinement": (
            "drops every managed key UNCONDITIONALLY — even one the overriding step "
            "explicitly PROVIDES. A real patch that cleared the managed family "
            "without first checking the overriding step's own keys would, for an "
            "overriding step that sets a managed option, produce a squashed result "
            "MISSING that provided option instead of carrying the overriding value. "
            "It loses a provided option, diverging from the optimizer's expected "
            "reduced operation. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (B) at a managed key the override DOES supply: the "
            "spec pins the lookup to the overriding value (`some v`), the rival "
            "returns `none`. Attacks the overriding-wins arm of the managed clause. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # managed key "k" provided by override: gold keeps some "V", rival drops.
        "witness": _wit("[]", '[("k","V")]', '["k"]', "k"),
    },
    {
        "id": "weak-keep-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _KEEP_OVERRIDE),
        "refinement": (
            "returns ONLY the overriding step's mapping — every option the original "
            "step alone carried is dropped, INCLUDING non-managed ones outside the "
            "managed family. A real patch that replaced the merged options with the "
            "overriding step's dict alone would lose a non-managed original-only "
            "option that must survive (the managed-clear is scoped to the managed "
            "family only). The reduced operation differs. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (B) at a NON-managed base-only key: the spec pins the "
            "lookup to the base value, the rival returns `none`. Attacks the "
            "survive-non-managed-base-only arm (managedKeys empty here, so no key may "
            "be cleared). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # non-managed base-only key "o", managed empty: gold keeps, rival drops.
        "witness": _wit('[("o","X")]', "[]", "[]", "o"),
    },
    {
        "id": "weak-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _EMPTY),
        "refinement": (
            "returns the empty mapping regardless of input — every option, provided "
            "or kept, is lost. A real patch producing an empty option set would make "
            "every squashed-with-options reduction drop all its options, so no "
            "expected reduced operation carrying a surviving option could match. Does "
            "NOT resolve. (A cheap supporting near-miss: it clears every managed key "
            "vacuously and keeps keys distinct, so ONLY the positive lookup clause "
            "rejects it.)"
        ),
        "rationale": (
            "REJECTED by clause (B) at a provided key: the spec pins the lookup to the "
            "overriding value, the empty result returns `none`. Attacks the "
            "overriding-wins arm from the drop-everything side. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # provided key "k", managed empty: gold keeps some "V", rival empty.
        "witness": _wit("[]", '[("k","V")]', "[]", "k"),
    },
    {
        "id": "weak-dup-keys",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _DUP),
        "refinement": (
            "overlays by bare concatenation with no de-duplication of a base key the "
            "overriding step already carries, so a shared key appears TWICE. The "
            "assoc-list carrier models a genuine dictionary (keys distinct); a real "
            "patch that built the combined options as a LIST of items rather than a "
            "dict — e.g. concatenating both steps' items without the dict merge that "
            "collapses shared keys — would not produce a `CreateModel.options` dict "
            "the optimizer compares equal, so it does NOT resolve. This defends the "
            "carrier-shape clause the nagini dict carrier got for free."
        ),
        "rationale": (
            "REJECTED by clause (A): with a key shared between `base` and `override` "
            "the concatenation has a duplicated key, so `(result.map Prod.fst).Nodup` "
            "is false — even though first-match lookup (clause (B)) still agrees. This "
            "is the ONLY rival attacking the key-distinctness conjunct. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the spec would not pin the result to a genuine "
            "dictionary)."
        ),
        # key "k" on both base and override: result [("k","1"),("k","2")] has dup keys.
        "witness": _wit('[("k","2")]', '[("k","1")]', "[]", "k", clause="A"),
    },
    {
        "id": "weak-reverse-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _REVERSE_PRECEDENCE),
        "refinement": (
            "overlays the two option mappings the wrong way round, so for a key BOTH "
            "steps set, the ORIGINAL step's value survives instead of the overriding "
            "step's. The managed-clearing is untouched and still keys off the "
            "overriding step, so every clear arm behaves correctly. A real patch that "
            "combined the two option mappings in the reverse order would, for an "
            "overriding step that RE-SETS an option the original step already had, "
            "produce a squashed result carrying the STALE value — the optimizer's "
            "expected reduced operation carries the overriding one, so it does NOT "
            "resolve. (F2P case 2 has exactly this shape: the overriding step re-sets "
            "an option the original step also carries.)"
        ),
        "rationale": (
            "REJECTED by clause (B) at a key both mappings carry: the spec pins the "
            "lookup to the OVERRIDING value, this rival returns the base value. "
            "Attacks the overlay's PRECEDENCE, which no other rival probes — "
            "weak-dup-keys puts a key in both mappings but attacks only clause (A) "
            "(key-distinctness), never WHICH of the two values wins, and every other "
            "rival diverges at a key just one side mentions. If it VERIFIES => "
            "SPEC-TOO-WEAK (the spec would not pin the precedence)."
        ),
        # "k" on both, distinct values: gold keeps the override's, rival keeps base's.
        "witness": _wit('[("k","BASE")]', '[("k","OVR")]', "[]", "k"),
    },
    {
        "id": "weak-clear-only-if-silent-everywhere",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_BODY, _CLEAR_ONLY_IF_EMPTY),
        "refinement": (
            "clears the managed family only when the overriding step supplies NO "
            "options at all, instead of deciding key-by-key. A real patch that guarded "
            "the whole clearing step on the overriding step's option set being empty "
            "would handle the drop-everything case correctly and still leave a managed "
            "option stranded whenever the overriding step supplies SOME options but not "
            "that one — the squashed result then carries an option the overriding step "
            "does not own. That is FAIL_TO_PASS case 2's shape (the overriding step "
            "supplies one managed option while the original step carries two), so it "
            "does NOT resolve."
        ),
        "rationale": (
            "partial-domain: REJECTED by clause (B) at a managed key silent in a "
            "NON-EMPTY `override`. Correct on the entire empty-override sub-domain — so "
            "weak-bare-merge's and weak-forget-tail's witness inputs (both use an empty "
            "override) do NOT catch it — and correct when the override mentions every "
            "managed key. Attacks the per-key granularity of the managed-clear, which "
            "no existing rival probes: the partially-populated override was unreached. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # managed "m" on base, override NON-empty but silent about "m": gold clears "m".
        "witness": _wit('[("m","A")]', '[("other","Z")]', '["m"]', "m"),
    },
]


# No @ContractOnly axioms and no opaque callees: the overlay-then-clear is modeled
# DEEPLY over the transparent assoc-list carrier, so the axiom lane is vacuous here
# and belongs to G-AX regardless.
AXIOM_TESTS = []
