# properties.py — G-PBT falsification battery for django__django-15569 (lean lane).
#
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. NOT a Lean
# module — a manifest the G-PBT gate parses. Each SPEC case is a FULL
# Solution.lean variant that shares the FROZEN spec byte-for-byte (region
# surgery: only text inside `-- impl-start`/`-- impl-end`, and for a positive
# that honestly reproves, inside `-- proof-start`/`-- proof-end` — both regions
# the consumer spec view elides, so `markers.same_spec` holds by construction and
# both frozen `theorem` STATEMENTS survive byte-identical). Every
# expect="reject" case additionally carries a refutation `witness`: a snippet
# that ELABORATES against the rival and FAILS on the frozen solution, so the
# rejection is attributable to the postcondition and not to a tactic script that
# merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#
#   implementation_unregisterLookup (s : LookupState) (lookupName : String)
#       : LookupState
#
#   `LookupState` carries an underlying table of named entries (`classLookups :
#   List (String × Nat)`) plus a memoized snapshot consulted by readers (`cache :
#   Option (List (String × Nat))`, `none` meaning "no snapshot — recompute from
#   the table"). Removing a name must leave the registry correct. The single
#   postcondition `problem_spec_unregisterLookup` pins that with FOUR conjuncts:
#
#     (1) result.classLookups = eraseKey s.classLookups lookupName
#         — the table is EXACTLY the input with every entry of that name dropped:
#           this one equation carries both halves, the removal AND the table
#           frame (all other entries preserved, in order, nothing added).
#     (2) result.cache = none
#         — the reader snapshot is INVALIDATED (cleared, not re-primed with a
#           precomputed value), so later table changes stay visible. THE
#           discriminating clause: it is the re-sync the change adds, and the
#           snapshot-blind removal fails exactly here.
#     (3) getLookups result = result.classLookups
#         — readers see the current table, not a stale snapshot.
#     (4) lookupName ∉ keys (getLookups result)
#         — and in particular no longer report the removed name.
#
#   CLAUSE DEPENDENCE (which is why the rival set is shaped the way it is): (3)
#   and (4) follow from (1) ∧ (2), since a cleared snapshot makes `getLookups`
#   recompute. So the INDEPENDENT top-level clauses are (1) and (2), and any rival
#   that violates (3) or (4) must route through (2). The battery therefore pins
#   (1) in isolation (`weak-frame-table-other-clobber`, correct snapshot handling,
#   wrong table), pins (2) in isolation (`weak-reprime-current`, correct table,
#   snapshot re-primed instead of cleared — the sharpest near-miss in the set),
#   and attacks (3)/(4) through the snapshot with three further rivals.
#
# CARRIER NOTE. The nagini sibling modeled the SAME operation as an in-place
# mutation of two full-permission dicts — the backing store and the memoised
# reader view — and pinned FOUR clauses: store[name] removed, view[name] removed,
# and two per-key `Old()` frame clauses. This backend is referentially
# transparent and returns a single record, so the sibling's per-key clauses fold
# into whole-post-state EQUATIONS: its store-deletion clause and its store frame
# clause both become (1), and its view clauses become (2)/(3)/(4). Equating the
# whole post-state to a function of the input pins the removed key AND every
# untouched key at once, so the sibling's frame attacks port intact — as direct
# clause violations rather than as anything about permissions.
#
# The carrier is fully TRANSPARENT: `LookupState` derives `DecidableEq`, and
# `eraseKey`/`keys`/`getLookups` are total `def`s over `List (String × Nat)` with
# no opaque callee and an EMPTY axioms region. So every witness states the
# refutation at a concrete literal input and closes by `decide` — no conditioning
# on the carrier is needed, and no witness binds anything, so no consistency
# probe applies.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submission for the full
# accounting):
#   * FRAME / PERMISSION-MUTATION. The sibling has NO `Acc(.,1/2)` read-only
#     input (both dicts are full-permission because the operation legitimately
#     writes them), so it ships no permission-mutation rival either; it attacks
#     the per-key `Old()` frame directly. Those attacks DO port, as clause (1)
#     and clause (2)/(3) violations. There is no fractional-permission wall on
#     this carrier to subvert, and none is fabricated.
#   * ADMISSIBILITY. PORTED (see `admiss-ground-registry`). An earlier revision of
#     this manifest recorded the lane as N/A because the frozen obligation binds
#     no precondition hypothesis. That reason was WRONG and a later audit
#     retracted it: on a total carrier the analogue of PRECOND-TOO-STRONG is the
#     obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
#     positive that discharges the spec predicate at that concrete input — by
#     evaluation, as a `have`, before closing the frozen obligation verbatim —
#     tests directly. That case is expressible here and builds (exit 0), so the
#     lane is shipped rather than declared inapplicable.
#   * DIVERGENCE / NON-TERMINATION. The sibling carries no diverge-*/nonterm-*/
#     weak-diverge case, so there is nothing to port. Recorded as a KNOWN SPEC
#     HOLE rather than as a vacuous class, correcting an earlier revision of this
#     manifest which claimed a diverging body "cannot be written at all (it would
#     not elaborate)". That claim is FALSE and was measured so: an impl whose
#     table component is `spin s.classLookups lookupName` for a
#     `partial def spin xs k := spin xs k` ELABORATES fine (Lean admits `partial
#     def` via an `Inhabited` default, no termination obligation is discharged),
#     and only its PROOF fails. The class is nevertheless unshippable here for the
#     reason attack F′ gives for `"partial"` semantics: a witness cannot refute
#     it. Measured — `decide` on the spec predicate at a literal input against
#     that rival fails with `Tactic 'decide' failed for proposition` (the opaque
#     `spin` application never reduces), which is a STUCK REDUCTION and not a
#     refutation, so no witness of the battery's shape discriminates. Hole, not
#     vacuous class.
#   * AXIOM_TESTS. Dropped — the axiom lane is G-AX's job and this gate ignores
#     it. There is no consumed axiom here regardless: the axioms region is empty
#     and the snapshot-invalidation effect is modeled DEEPLY.
from pathlib import Path

INSTANCE = "django__django-15569"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Every anchor lies ENTIRELY inside the region it is meant to
# edit and is unique in the file (both asserted by _swap at load, so the
# manifest breaks loudly if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# --- inside `-- impl-start` / `-- impl-end` ---
# the impl's own docstring (elided from the spec view along with the rest of the
# impl region); retuned only by the case that changes the impl's SHAPE.
_IMPL_DOC = (
    "/-- Remove the entry named `lookupName` from the registry. Mirrors the fixed\n"
    "procedure: drop the entry from the underlying table, then invalidate the reader\n"
    "snapshot so subsequent reads reflect the current table. -/\n"
)
# the impl's signature + `Id.run do` opener.
_IMPL_HEAD = (
    "def implementation_unregisterLookup\n"
    "    (s : LookupState) (lookupName : String) : LookupState := Id.run do\n"
)
# the WHOLE frozen impl body: the two writes and the return. Every rival and the
# reshaping positives replace exactly this text.
_IMPL_BODY = (
    "  let mut st := s\n"
    "  -- remove the named entry from the underlying table\n"
    "  st := { st with classLookups := eraseKey st.classLookups lookupName }\n"
    "  -- invalidate the reader snapshot\n"
    "  st := { st with cache := none }\n"
    "  return st\n"
)

# --- inside `-- proof-start` / `-- proof-end` (tactic bodies only; both
# --- `theorem` STATEMENTS stay byte-identical in every case) ---
_PROOF_CORRECT = (
    "  intro s lookupName\n"
    "  unfold problem_spec_unregisterLookup implementation_unregisterLookup\n"
    "  simp only [Id.run, getLookups, Option.getD_none, pure]\n"
    "  refine ⟨trivial, trivial, trivial, ?_⟩\n"
    "  simp only [eraseKey, keys, List.mem_map, List.mem_filter, bne_iff_ne, ne_eq,\n"
    "    not_exists, not_and]\n"
    "  rintro p ⟨_, hne⟩ rfl\n"
    "  exact hne rfl\n"
)
_PROOF_INTRO = (
    "  intro s lookupName\n"
    "  unfold problem_spec_unregisterLookup implementation_unregisterLookup\n"
)
_PROOF_DET = (
    "  intro s lookupName r h\n"
    "  obtain ⟨h1, h2, -, -⟩ := h\n"
    "  unfold implementation_unregisterLookup\n"
    "  simp only [Id.run, pure]\n"
    "  cases r\n"
    "  simp_all\n"
)

for _a in (_IMPL_DOC, _IMPL_HEAD, _IMPL_BODY, _PROOF_CORRECT, _PROOF_DET,
           _PROOF_INTRO):
    assert _BASE.count(_a) == 1, f"frozen region anchor drifted: {_a[:60]!r}"


def _impl(body):
    """A full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL_BODY, body)


def _wit(state, name, note):
    """A refutation witness: the spec predicate is provably FALSE of the rival's
    output at one concrete literal input, closed by `decide`.

    The whole carrier is transparent and `LookupState` derives `DecidableEq`, so
    `decide` computes both the impl and all four conjuncts at a literal. The
    statement ELABORATES against a rival whose output diverges from the pinned
    post-state there, and FAILS on the frozen solution — where `decide` instead
    proves the proposition TRUE, the required discrimination. The head binds
    nothing, so there are no hypotheses that could be inconsistent.
    """
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_unregisterLookup\n"
        f"    {state} \"{name}\"\n"
        f"    (implementation_unregisterLookup\n"
        f"      {state} \"{name}\") := by\n"
        f"  unfold problem_spec_unregisterLookup implementation_unregisterLookup\n"
        f"  decide"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT
    # impls that MUST verify. If a faithful correct impl is rejected the
    # postcondition is over-fit to the frozen impl's form => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-reorder-writes",
        "kind": "soundness",
        "expect": "verify",
        # Invalidate the reader snapshot FIRST, then drop the entry from the
        # table. The two writes touch INDEPENDENT fields of the record and
        # neither reads the other's result (the table write reads
        # `st.classLookups`, the snapshot write stores a constant), so they
        # commute and the final state is identical on every input. Ports the
        # sibling's pos-reorder-writes directly: there too the two writes were
        # independent and commuted.
        "module": _impl(
            "  let mut st := s\n"
            "  -- invalidate the reader snapshot\n"
            "  st := { st with cache := none }\n"
            "  -- remove the named entry from the underlying table\n"
            "  st := { st with classLookups := eraseKey st.classLookups lookupName }\n"
            "  return st\n"),
        "rationale": (
            "structurally-different CORRECT impl: the two writes are COMMUTED. "
            "They touch independent fields and neither consumes the other's "
            "result, so the final state — and hence all four conjuncts (1) "
            "result.classLookups = eraseKey s.classLookups lookupName, (2) "
            "result.cache = none, (3) getLookups result = result.classLookups, "
            "(4) lookupName ∉ keys (getLookups result) — is identical on every "
            "(s, lookupName). Defends all four clauses over both input binders. "
            "The frozen tactic bodies close it unchanged, so both `theorem` "
            "statements AND bodies are byte-identical to the frozen file. If it "
            "FAILS => SPEC-TOO-STRONG (postcondition over-fit to one write order)."
        ),
    },
    {
        "id": "pos-local-temp",
        "kind": "soundness",
        "expect": "verify",
        # Compute the erased table ONCE into a local and assign from it (and
        # read it off `s` rather than off the accumulator `st`). A different
        # executable shape, observably identical result. Ports the sibling's
        # pos-local-temp.
        "module": _impl(
            "  let mut st := s\n"
            "  -- the underlying table with the named entry dropped\n"
            "  let t := eraseKey s.classLookups lookupName\n"
            "  st := { st with classLookups := t }\n"
            "  -- invalidate the reader snapshot\n"
            "  st := { st with cache := none }\n"
            "  return st\n"),
        "rationale": (
            "a correct impl that binds the dropped-entry table to a local `t` "
            "(read off the INPUT rather than off the accumulator) and assigns "
            "from it is observably identical to the frozen one: `t = eraseKey "
            "s.classLookups lookupName`, so clause (1) discharges, and the "
            "snapshot write is untouched so (2) and hence (3)/(4) do too. "
            "Defends all four clauses. The frozen tactic bodies close it "
            "unchanged. Ports the sibling's pos-local-temp; if it FAILS => "
            "SPEC-TOO-STRONG (over-fit to a trivial local reshape)."
        ),
    },
    {
        "id": "pos-direct-literal",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest HONEST correct impl: a direct structure literal, no
        # `Id.run do` / `let mut` at all. This is the shape refinement.md names
        # as the archetypal positive control, and it is NOT an ungrounded-oracle
        # echo: both components are computed from the function's OWN arguments by
        # transparent total `def`s (there is no opaque answer-key term to echo,
        # and the axioms region is empty). Because the whole `Id.run do` scaffold
        # is gone, both frozen tactic bodies need retuning — an HONEST reproof:
        # each `theorem` STATEMENT stays byte-identical, the retune only drops
        # the now-inapplicable `Id.run`/`pure` unfolding steps, and no
        # axiom/lemma/sorry/native_decide is introduced.
        "module": _swap(
            _swap(
                _swap(
                    _swap(_BASE, _IMPL_HEAD + _IMPL_BODY,
                          "def implementation_unregisterLookup\n"
                          "    (s : LookupState) (lookupName : String) : LookupState :=\n"
                          "  { classLookups := eraseKey s.classLookups lookupName,\n"
                          "    cache := none }\n"),
                    _IMPL_DOC,
                    "/-- Remove the entry named `lookupName` from the registry: the resulting\n"
                    "registry is the input table with every entry of that name dropped, and it\n"
                    "carries no reader snapshot. -/\n"),
                _PROOF_CORRECT,
                "  intro s lookupName\n"
                "  unfold problem_spec_unregisterLookup implementation_unregisterLookup\n"
                "  simp only [getLookups, Option.getD_none]\n"
                "  refine ⟨trivial, trivial, trivial, ?_⟩\n"
                "  simp only [eraseKey, keys, List.mem_map, List.mem_filter, bne_iff_ne, ne_eq,\n"
                "    not_exists, not_and]\n"
                "  rintro p ⟨_, hne⟩ rfl\n"
                "  exact hne rfl\n"),
            _PROOF_DET,
            "  intro s lookupName r h\n"
            "  obtain ⟨h1, h2, -, -⟩ := h\n"
            "  unfold implementation_unregisterLookup\n"
            "  cases r\n"
            "  simp_all\n"),
        "rationale": (
            "the cheapest HONEST correct impl: a direct structure literal with no "
            "mutable-accumulator scaffold, i.e. a genuinely different executable "
            "shape reaching the same state. Both components are GROUNDED in the "
            "function's own arguments via transparent total defs (`eraseKey "
            "s.classLookups lookupName` and the cleared snapshot), so this is a "
            "positive control rather than an ungrounded-oracle echo — there is no "
            "opaque answer-key term here to echo, and any WRONG component fails "
            "the postcondition (the seven rivals below demonstrate that). Defends "
            "all four clauses. Both `theorem` statements are kept byte-identical "
            "and the tactic bodies are honestly re-closed by dropping the "
            "now-inapplicable `Id.run`/`pure` unfolding steps — no new "
            "axiom/lemma/sorry/native_decide. If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — ADDED BY AUDIT. Confirm the obligation is SATISFIABLE
    # (non-vacuous) at a normal, F2P-shaped input. An earlier revision recorded
    # this lane as N/A on the ground that the frozen obligation binds no
    # precondition hypothesis; that is not the right test on a TOTAL carrier,
    # where the analogue of PRECOND-TOO-STRONG is the modeled behavior being
    # unsatisfiable at exactly the shape the failing tests exercise. So the
    # sibling's two `Requires`-admission cases re-express here as: discharge the
    # spec predicate BY EVALUATION at that concrete input as a `have`, then close
    # the frozen obligation verbatim. Nothing is assumed — no new declaration, no
    # axiom, both `theorem` statements byte-identical, the ground instance is a
    # `have` PREPENDED to the existing tactic body which then runs unchanged.
    # =====================================================================
    {
        "id": "admiss-ground-registry",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_INTRO,
            "  have _ground : problem_spec_unregisterLookup\n"
            "      { classLookups := [(\"alpha\", 1), (\"beta\", 2)],\n"
            "        cache := some [(\"alpha\", 1), (\"beta\", 2)] }\n"
            "      \"alpha\"\n"
            "      (implementation_unregisterLookup\n"
            "        { classLookups := [(\"alpha\", 1), (\"beta\", 2)],\n"
            "          cache := some [(\"alpha\", 1), (\"beta\", 2)] }\n"
            "        \"alpha\") := by\n"
            "    unfold problem_spec_unregisterLookup "
            "implementation_unregisterLookup\n"
            "    decide\n"
            + _PROOF_INTRO),
        "rationale": (
            "ADMISSIBILITY / PRECOND-TOO-STRONG. The obligation is discharged at "
            "an F2P-shaped input — a registry holding TWO distinct named entries "
            "with a WARM reader snapshot (`cache := some ...`) that currently "
            "agrees with the table, removing one of the two names — by evaluation "
            "(`decide`) as a `have`, after which the frozen obligation is closed "
            "verbatim by the unchanged frozen tactic body. That input shape is the "
            "one the failing tests exercise: a name is registered alongside "
            "another, has been read at least once (hence the populated snapshot), "
            "and is then removed, with the sibling entry required to survive. If "
            "this case FAILED, all four conjuncts would be jointly unsatisfiable "
            "at exactly that input — the total-carrier analogue of a precondition "
            "so strong it excludes normal calls — and every expect='reject' "
            "outcome in this battery would be attributable to a vacuous "
            "postcondition rather than to the spec. It verifies, so the four "
            "conjuncts are jointly SATISFIABLE at a normal input and the reject "
            "lane's rejections mean what they claim. Re-expresses the sibling's "
            "admiss-incoming-precond-noncontradictory and admiss-caller-in-region: "
            "there the incoming state had to be exhibited as non-contradictory for "
            "a caller to discharge `Requires`; here the same content is asserted "
            "as a ground instance of the postcondition. Nothing is assumed — no "
            "new declaration/axiom/sorry, statement byte-identical."
        ),
    },

    # =====================================================================
    # UNIQUENESS RIVALS — wrong impls sharing the frozen spec that MUST be
    # rejected (else SPEC-TOO-WEAK). Each carries a machine-checked witness at
    # its OWN concrete input, and the refinement argument for why its faithful
    # real counterpart would NOT resolve the failing tests. The witnesses vary
    # both input binders — `lookupName` over seven distinct names, and `s` over
    # one-, two- and three-entry tables with the snapshot field taking `none`
    # and `some` — so no binder is pinned across the battery.
    # =====================================================================
    {
        "id": "weak-snapshot-blind-removal",
        "kind": "uniqueness",
        "expect": "reject",
        # THE canonical discriminator: drop the entry from the table and leave
        # the reader snapshot exactly as it came in. This is the pre-change
        # behaviour and the bundle's load-bearing rival.
        "module": _impl(
            "  let mut st := s\n"
            "  st := { st with classLookups := eraseKey st.classLookups lookupName }\n"
            "  return st\n"),
        "refinement": (
            "this is the pre-change behaviour verbatim: the underlying table is "
            "edited but the memoized reader snapshot is never invalidated — the "
            "re-sync the change adds is simply absent. Its faithful real "
            "counterpart is therefore the unpatched tree, which fails BOTH "
            "failing tests. One asserts that immediately after a name is "
            "removed the reader view no longer contains it; with a stale "
            "snapshot the reader keeps reporting the removed name, so the "
            "assertion fails. The other drops its own now-redundant manual "
            "snapshot-invalidation call and relies on the removal operation to "
            "do it, so with a snapshot-blind removal the reader still resolves "
            "the removed name to the old entry instead of falling through to the "
            "generic handler. A verifying rival here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECT from clause (2) result.cache = none: the body never touches "
            "the snapshot, so it retains its incoming value where the "
            "postcondition demands it be cleared — and consequently also "
            "violates (3) getLookups result = result.classLookups and (4) "
            "lookupName ∉ keys (getLookups result), since the retained snapshot "
            "still lists the removed name. Clause (1) is kept CORRECT, isolating "
            "the snapshot half. Refuted at a one-entry table whose snapshot is a "
            "`some` still listing the removed name. The load-bearing "
            "discriminator of the whole bundle; if it VERIFIED => SPEC-TOO-WEAK "
            "(the spec would admit the pre-change behaviour)."
        ),
        "witness": _wit('{ classLookups := [("k1", 7)], cache := some [("k1", 7)] }',
                        "k1",
                        "stale snapshot retained: the removed name is still reported"),
    },
    {
        "id": "weak-reprime-current",
        "kind": "uniqueness",
        "expect": "reject",
        # The SHARPEST near-miss in the set, and the reason clause (2) is stated
        # as `cache = none` rather than as a property of what the snapshot
        # CONTAINS: re-prime the snapshot with the correctly-erased table instead
        # of clearing it. Clauses (1), (3) and (4) all HOLD — the reader sees the
        # right entries and the removed name is gone — so ONLY clause (2)
        # refutes it. Its witness is therefore at a DIFFERENT input point from
        # weak-snapshot-blind-removal's and refutes it for a different reason.
        "module": _impl(
            "  let mut st := s\n"
            "  st := { st with classLookups := eraseKey st.classLookups lookupName }\n"
            "  st := { st with cache := some st.classLookups }\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal that, instead of emptying the "
            "memo, RE-PRIMES it with a freshly computed snapshot. It looks right "
            "at the moment of removal — the reader immediately sees the correct "
            "entries — but the memo is now populated rather than empty, so it no "
            "longer recomputes and every SUBSEQUENT table change is invisible to "
            "readers until something else invalidates it. The operation the "
            "change calls empties the memo; it does not re-prime it. So a "
            "re-priming counterpart re-introduces exactly the staleness class "
            "the change exists to remove: the next registration or removal that "
            "relies on the memo being empty reads through to a snapshot taken "
            "before it, and the pass-to-pass suite (which registers, uses and "
            "removes many names in sequence, including nested "
            "register/unregister scopes) breaks. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (2) result.cache = none ALONE — this is the only "
            "rival in the battery that isolates clause (2). Clause (1) holds "
            "(the table is correctly erased), and because the re-primed snapshot "
            "content EQUALS that erased table, (3) getLookups result = "
            "result.classLookups and (4) lookupName ∉ keys (getLookups result) "
            "hold too. Only `cache = none` fails: the snapshot was re-primed, "
            "not cleared. This pins that clause (2) is load-bearing on its own "
            "and not merely a proxy for (3)/(4). Refuted at a TWO-entry table "
            "with a `some` snapshot — a strictly different sub-domain from "
            "weak-snapshot-blind-removal, which is refuted for retaining a stale "
            "snapshot rather than for writing a correct one. If it VERIFIED => "
            "SPEC-TOO-WEAK (clause (2) would be hollow and a re-priming removal "
            "would slip through)."
        ),
        "witness": _wit(
            '{ classLookups := [("k6", 7), ("k7", 4)], cache := some [("k6", 7)] }',
            "k6",
            "snapshot re-primed with the correct table instead of cleared: only "
            "clause (2) fails"),
    },
    {
        "id": "weak-table-blind-removal",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror omission: invalidate the snapshot but never drop the entry
        # from the table. Ports the sibling's weak-view-only-no-delete.
        "module": _impl(
            "  let mut st := s\n"
            "  st := { st with cache := none }\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal that invalidates the memo but "
            "never deletes the entry from the underlying table. The table still "
            "registers the name, so the very next read recomputes from it and "
            "STILL resolves the removed name — the failing test's assertion that "
            "the removed name is absent from the reader view fails, and the "
            "other failing test still resolves the removed entry instead of "
            "falling through to the generic handler. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (1) result.classLookups = eraseKey s.classLookups "
            "lookupName: the body leaves the table untouched, so it still holds "
            "the removed name where the postcondition demands it be dropped — "
            "and consequently also violates (4) lookupName ∉ keys (getLookups "
            "result), since with the snapshot cleared the reader recomputes the "
            "name straight back. Clause (2) is kept CORRECT, isolating the table "
            "half — the exact mirror of weak-snapshot-blind-removal. Refuted at a "
            "one-entry table with an already-empty snapshot. Ports the sibling's "
            "weak-view-only-no-delete. If it VERIFIED => SPEC-TOO-WEAK."
        ),
        "witness": _wit('{ classLookups := [("k2", 3)], cache := none }', "k2",
                        "table untouched: the removed name is recomputed straight back"),
    },
    {
        "id": "weak-noop",
        "kind": "uniqueness",
        "expect": "reject",
        # Does nothing at all. Pins that the spec is not vacuously satisfiable.
        # Ports the sibling's weak-noop.
        "module": _impl(
            "  let mut st := s\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal that returns without touching "
            "either the table or the memo. The name stays registered and stays "
            "visible to readers, so both failing tests fail outright — the "
            "removed name is still in the reader view, and the other test still "
            "resolves it to the registered entry. Does NOT resolve."
        ),
        "rationale": (
            "REJECT: the postcondition is NOT vacuously satisfiable. A no-op "
            "returns the input, which violates clause (1) result.classLookups = "
            "eraseKey s.classLookups lookupName (the named entry is still there) "
            "and clause (4) lookupName ∉ keys (getLookups result). Refuted at a "
            "TWO-entry table with an empty snapshot, removing the FIRST entry — "
            "so the witness also exercises a table where erasure must preserve a "
            "sibling entry. Ports the sibling's weak-noop. If it VERIFIED => "
            "SPEC-TOO-WEAK (the spec would be satisfiable without doing the work)."
        ),
        "witness": _wit('{ classLookups := [("k3", 5), ("k4", 6)], cache := none }',
                        "k3", "no-op: the named entry is still registered"),
    },
    {
        "id": "weak-frame-table-other-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME attack on the table: both correct writes, PLUS collateral
        # erasure of an UNRELATED name. Ports the sibling's
        # weak-frame-store-other-clobber, which attacked its per-key Old() store
        # frame; here the frame is the second half of clause (1)'s equation.
        # Isolates clause (1): the snapshot is handled correctly, so (2), (3) and
        # (4) all hold and ONLY the table equation fails.
        "module": _impl(
            "  let mut st := s\n"
            "  st := { st with classLookups := eraseKey st.classLookups lookupName }\n"
            "  st := { st with classLookups := eraseKey st.classLookups \"other\" }\n"
            "  st := { st with cache := none }\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal that, besides the requested "
            "name, also deletes a still-registered UNRELATED name from the "
            "table. That name stops resolving for every later reader, so the "
            "operation changes behaviour for a registration it was required to "
            "leave intact. The pass-to-pass suite registers and uses many names "
            "and relies on removal being surgical — including nested scopes that "
            "register one name inside another's lifetime and expect the outer one "
            "to survive the inner removal — so it breaks. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (1) result.classLookups = eraseKey s.classLookups "
            "lookupName, whose equation pins the ENTIRE table post-state and so "
            "carries the table FRAME as well as the removal: erasing an unrelated "
            "name makes the result differ from `eraseKey s.classLookups "
            "lookupName`, which retains it. This rival isolates clause (1) — the "
            "snapshot is correctly cleared, so (2) holds and (3)/(4) follow — "
            "making it the exact counterpart of weak-reprime-current on the other "
            "independent clause. Refuted at a two-entry table containing both the "
            "removed name and the unrelated one, the only witness whose input "
            "carries the collaterally-erased key. Ports the sibling's "
            "weak-frame-store-other-clobber (there a per-key Old() frame clause; "
            "here the frame half of clause (1)'s equation). If it VERIFIED => "
            "SPEC-TOO-WEAK (the table frame would be unpinned)."
        ),
        "witness": _wit(
            '{ classLookups := [("k5", 1), ("other", 9)], cache := none }', "k5",
            "an unrelated registration is collaterally erased from the table"),
    },
    {
        "id": "weak-frame-view-other-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME attack on the reader view: correct table erasure, but the
        # snapshot is re-primed with a view that DROPS an unrelated still-present
        # entry (an over-broad eviction). Ports the sibling's
        # weak-frame-view-other-clobber.
        "module": _impl(
            "  let mut st := s\n"
            "  st := { st with classLookups := eraseKey st.classLookups lookupName }\n"
            "  st := { st with cache := some (st.classLookups.drop 1) }\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal whose memo handling is "
            "over-broad — it evicts the removed name but, in recomputing, also "
            "loses a DIFFERENT still-registered name's resolution. That other "
            "name stops resolving on the next read even though it was never "
            "unregistered, so the reader view no longer reflects the names it "
            "must expose and the pass-to-pass suite that registers and reads "
            "several names at once breaks. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (3) getLookups result = result.classLookups (and "
            "clause (2) result.cache = none): the snapshot is populated with a "
            "view that omits an unrelated still-present entry, so what readers "
            "see is no longer the current table — the view FRAME is violated. "
            "Clause (1) is kept correct, isolating the reader-view half. Refuted "
            "at a THREE-entry table (the widest input in the battery), removing "
            "the first entry so that two unrelated entries must survive in the "
            "view and one provably does not. Ports the sibling's "
            "weak-frame-view-other-clobber (there a per-key Old() view frame "
            "clause). If it VERIFIED => SPEC-TOO-WEAK (the view frame would be "
            "unpinned)."
        ),
        "witness": _wit(
            '{ classLookups := [("k10", 3), ("keep1", 11), ("keep2", 12)], '
            'cache := none }', "k10",
            "over-broad eviction: an unrelated entry is lost from the reader view"),
    },
    {
        "id": "weak-view-bogus-value",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL / WRONG-VALUE: correct table erasure, but the snapshot is
        # re-primed with the removed name REBOUND to a bogus entry, so the
        # removed name still resolves — to the wrong thing. A sharper miss than
        # leaving the snapshot stale. Ports the sibling's weak-view-bogus-value.
        "module": _impl(
            "  let mut st := s\n"
            "  st := { st with classLookups := eraseKey st.classLookups lookupName }\n"
            "  st := { st with cache := some ((lookupName, 1) :: st.classLookups) }\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal that, instead of emptying the "
            "memo, rebinds the removed name's memoized entry to some other "
            "entry. A read of the removed name still RESOLVES — to the wrong "
            "entry — so the failing test's assertion that the removed name is "
            "absent from the reader view fails, and the other failing test gets "
            "the wrong object back rather than falling through to the generic "
            "handler. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (4) lookupName ∉ keys (getLookups result), the "
            "sharpest available miss on the reader view: the removed name is not "
            "merely still present by staleness, it is explicitly REBOUND, so the "
            "view provably lists it (and clauses (2) and (3) fail too, the "
            "snapshot being populated and unequal to the table). Clause (1) is "
            "kept correct. Refuted at a one-entry table whose incoming snapshot "
            "is a `some` listing an extra name not in the table — the only "
            "witness whose snapshot and table disagree on the incoming state. "
            "Note the incoming snapshot is NOT load-bearing for THIS refutation: "
            "the rival overwrites that field unconditionally, so it is refuted "
            "identically at the same table with `cache := none` (machine-checked: "
            "clause profile [1,0,0,0] either way). The incoming `some` is "
            "load-bearing only for weak-snapshot-blind-removal, which RETAINS it. "
            "Ports the sibling's weak-view-bogus-value. If it VERIFIED => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _wit(
            '{ classLookups := [("k8", 8)], cache := some [("k8", 8), ("k9", 2)] }',
            "k8",
            "removed name rebound in the reader view: it still resolves, wrongly"),
    },
    {
        "id": "weak-table-extra-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Clause (1) is documented as carrying BOTH halves of the
        # table frame — the removal AND "nothing added" — but every pre-existing
        # rival attacks it by REMOVING too much (weak-frame-table-other-clobber,
        # weak-table-blind-removal, weak-noop) or by removing too little. None
        # ADDS an entry, so the "nothing added" half of the equation was asserted
        # in the manifest's prose and never demonstrated. This rival adds one.
        "module": _impl(
            "  let mut st := s\n"
            "  st := { st with classLookups := eraseKey st.classLookups lookupName }\n"
            "  st := { st with classLookups := st.classLookups ++ [(\"zz\", 0)] }\n"
            "  st := { st with cache := none }\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal that correctly drops the "
            "requested name but also INTRODUCES a registration that was never "
            "asked for. A name no caller registered now resolves, so reads of it "
            "stop falling through to the generic handler and start returning an "
            "entry the registry invented. The pass-to-pass suite asserts the exact "
            "set of registered names after a removal, so it breaks. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause (1) result.classLookups = eraseKey s.classLookups "
            "lookupName, attacking the half of that equation no other rival "
            "reaches: not 'too much removed' but 'something ADDED'. The equation "
            "pins the table post-state exactly, so an appended entry makes the "
            "result differ from `eraseKey s.classLookups lookupName`. Clause (2) "
            "is kept correct (the snapshot is cleared) so (3) holds, and (4) holds "
            "too since the added name is not the removed one — machine-checked "
            "clause profile [0,1,1,1], so this rival isolates clause (1) via "
            "INSERTION alone. If it VERIFIED => SPEC-TOO-WEAK (the 'nothing added' "
            "half of the table frame would be unpinned)."
        ),
        "witness": _wit(
            '{ classLookups := [("k11", 2), ("keep3", 5)], cache := none }', "k11",
            "a spurious entry is added to the table"),
    },
    {
        "id": "weak-erase-first-only",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. `eraseKey` is a FILTER: it drops EVERY entry of that
        # name. No pre-existing rival distinguishes "drop all" from "drop the
        # first", and no pre-existing witness uses a table with a repeated name,
        # so the multiplicity the frozen spec pins was never tested. This rival
        # drops only the first match; it is refutable only on a duplicate-key
        # table, which is exactly where its witness states the refutation.
        "module": _impl(
            "  let mut st := s\n"
            "  -- drop only the FIRST entry of that name, keeping later duplicates\n"
            "  let pre := st.classLookups.takeWhile (fun p => p.1 != lookupName)\n"
            "  let post := (st.classLookups.dropWhile (fun p => p.1 != lookupName)).drop 1\n"
            "  st := { st with classLookups := pre ++ post }\n"
            "  st := { st with cache := none }\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal that stops at the first entry "
            "matching the name instead of clearing every one of them. Wherever a "
            "name has more than one entry in the table, one survives and the name "
            "KEEPS resolving after being unregistered — the exact symptom the "
            "failing tests pin, restricted to the multiply-registered case. A "
            "suite that registers the same name twice, or registers over an "
            "existing name and then removes it, still sees the removed name "
            "resolve. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (1) result.classLookups = eraseKey s.classLookups "
            "lookupName and, consequentially, clause (4) lookupName ∉ keys "
            "(getLookups result): `eraseKey` is a FILTER, so the equation demands "
            "EVERY entry of that name be gone; a first-match-only removal leaves a "
            "duplicate behind, and with the snapshot correctly cleared the reader "
            "recomputes and still reports the removed name. Machine-checked clause "
            "profile [0,1,1,0] at a two-entry table both of whose entries carry the "
            "removed name — a sub-domain (repeated key) no other witness in the "
            "battery visits. This rival is observably IDENTICAL to the frozen impl "
            "on every duplicate-free table, so it is refutable only there, which is "
            "why the witness input is shaped that way. If it VERIFIED => "
            "SPEC-TOO-WEAK (removal multiplicity would be unpinned)."
        ),
        "witness": _wit(
            '{ classLookups := [("k12", 1), ("k12", 2)], cache := none }', "k12",
            "only the first entry of that name is dropped: a duplicate survives"),
    },
    {
        "id": "weak-table-survivor-values-clobbered",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Clause (1) is an equation on `List (String × Nat)`, so it
        # pins the surviving entries' VALUES (the `Nat` payloads) as well as which
        # NAMES survive. Every other rival in the battery is refutable on the
        # key-set alone: each either keeps/drops the wrong names, or reorders, or
        # touches only the snapshot. So a spec whose clause (1) had been weakened
        # from a list equation to a statement about `keys` — i.e. that pinned only
        # the surviving NAMES and not what they resolve TO — would pass the whole
        # pre-audit battery unchanged. This rival has the exactly-right key set in
        # the right order and clobbers only the payloads.
        "module": _impl(
            "  let mut st := s\n"
            "  st := { st with classLookups :=\n"
            "    (eraseKey st.classLookups lookupName).map (fun p => (p.1, 0)) }\n"
            "  st := { st with cache := none }\n"
            "  return st\n"),
        "refinement": (
            "faithful real counterpart: a removal that drops the requested name "
            "correctly and leaves the right set of names registered, but resets "
            "every surviving name's registered entry to a different one. Each "
            "surviving name still resolves, so nothing looks absent, but it "
            "resolves to the WRONG entry — a reader that registered a name and "
            "then removed an unrelated one silently gets someone else's entry "
            "back. The pass-to-pass suite registers named entries and then asserts "
            "what those names resolve to, not merely that they resolve, so it "
            "breaks. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (1) result.classLookups = eraseKey s.classLookups "
            "lookupName, attacking the dimension no other rival reaches: the "
            "surviving entries' VALUES. Clause (1) is an equation between lists of "
            "`String × Nat` pairs, so it pins the payloads and not just the key "
            "set; this rival preserves the exact key set AND its order and changes "
            "only the `Nat` components. Machine-checked clause profile [0,1,1,1] at "
            "a two-entry table — the snapshot is correctly cleared so (2) holds and "
            "(3) follows, and (4) holds since the removed name is genuinely gone. "
            "Every other rival in the battery is refutable on the key set alone, so "
            "without this case a clause (1) weakened from a list equation to a "
            "`keys`-level statement would still pass the battery. If it VERIFIED => "
            "SPEC-TOO-WEAK (what surviving names resolve to would be unpinned)."
        ),
        "witness": _wit(
            '{ classLookups := [("k14", 4), ("keep6", 9)], cache := none }', "k14",
            "a surviving entry's value is clobbered while its name is preserved"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING (the full disposition of every sibling case).
#
#   nagini case                              -> here
#   ---------------------------------------------------------------------
#   pos-reorder-writes                       -> pos-reorder-writes        PORTED
#   pos-local-temp                           -> pos-local-temp            PORTED
#   admiss-incoming-precond-noncontradictory -> admiss-ground-registry    PORTED
#   admiss-caller-in-region                  -> admiss-ground-registry    PORTED
#   weak-store-only-viewblind                -> weak-snapshot-blind-removal PORTED (2)
#   weak-view-only-no-delete                 -> weak-table-blind-removal   PORTED (1)
#   weak-noop                                -> weak-noop                  PORTED (1,4)
#   weak-frame-store-other-clobber           -> weak-frame-table-other-clobber PORTED (1)
#   weak-frame-view-other-clobber            -> weak-frame-view-other-clobber  PORTED (2,3)
#   weak-view-bogus-value                    -> weak-view-bogus-value      PORTED (2,3,4)
#   (no sibling counterpart)                 -> pos-direct-literal         ADDED
#   (no sibling counterpart)                 -> weak-reprime-current       ADDED
#   (no sibling counterpart)                 -> weak-table-extra-entry     ADDED (audit)
#   (no sibling counterpart)                 -> weak-erase-first-only      ADDED (audit)
#   (no sibling counterpart)                 -> weak-table-survivor-values-clobbered ADDED (audit)
#   AXIOM_TESTS (none)                       -> (none)                     N/A (G-AX)
#
# 14 lean SPEC cases: 3 soundness, 1 admissibility, 10 uniqueness. Case-count
# parity with the sibling is not the target; clause and binder coverage is.
#
# PORTED (both admissibility cases -> admiss-ground-registry): an earlier
#   revision of this manifest recorded the lane as N/A because the lean
#   obligation binds NO precondition hypothesis, and a later audit RETRACTED
#   that reason. 'The frozen obligation has no precondition' is not the test on
#   a total carrier: the analogue of PRECOND-TOO-STRONG here is the obligation
#   being UNSATISFIABLE at exactly an F2P-shaped input, which is directly tested
#   by discharging the spec predicate at that concrete input by evaluation, as a
#   `have`, before closing the frozen obligation verbatim. The sibling's two
#   cases exhibited the incoming state as non-contradictory so a caller could
#   discharge `Requires`; the ported case asserts the same content as a ground
#   instance of the postcondition at a two-entry registry with a WARM snapshot.
#   Expressible and verified (exit 0), so the lane ships. Both sibling cases map
#   to the one lean case because the distinction they drew — assertion in-region
#   vs. a caller discharging the precondition — was an artifact of Viper's
#   proof obligation and of Nagini's ban on nested functions; neither survives
#   onto a carrier with no precondition to discharge.
# ADDED (pos-direct-literal): no sibling counterpart — the sibling's impl was
#   assignment-only into caller-owned dicts, with no return value and so no
#   "return the whole answer directly" shape to test. Here the impl RETURNS a
#   record, so the direct structure literal is the cheapest honest correct impl
#   and the natural third positive. It is a positive control and not an
#   ungrounded-oracle echo: both components are computed from the arguments by
#   transparent total defs, the axioms region is empty, and there is no opaque
#   answer-key term to echo. It is also the case that exercises the honest-
#   reproof path (both `theorem` statements byte-identical, tactic bodies
#   retuned only to drop the now-absent `Id.run`/`pure` unfolding steps).
# ADDED (weak-reprime-current): no sibling counterpart, because the sibling's
#   carrier cannot express it. The sibling models the reader view as a DICT that
#   is written per key, so "the memo is empty" is not a state it can distinguish
#   from "the memo contains the right entries"; its clause (2) is
#   view[name]==unregistered(), a statement about a key's VALUE. This backend
#   models the memo as an `Option`, so `cache = none` (cleared) and `cache = some
#   <the right table>` (re-primed) are distinct states and clause (2) pins the
#   former. That makes a re-priming rival expressible AND wrong here, and it is
#   the only rival isolating clause (2): clauses (1), (3) and (4) all hold of it.
#   Without it, clause (2) would be attacked only by rivals that also violate
#   (3)/(4), and a spec whose clause (2) had been weakened to a statement about
#   the snapshot's CONTENTS would pass the battery unchanged.
# FRAME / PERMISSION-MUTATION: the sibling has no `Acc(.,1/2)` read-only input
#   (both dicts are full-permission, since the operation legitimately writes
#   them), so it ships no permission-mutation rival either — it attacks its
#   per-key `Old()` frame clauses directly. Those attacks port intact as
#   weak-frame-table-other-clobber (clause (1)) and
#   weak-frame-view-other-clobber (clauses (2)/(3)): on this referentially
#   transparent carrier the postcondition equates the whole post-state to a
#   function of the input, so disturbing an unrelated name IS a clause
#   violation. There is no fractional-permission wall to subvert and none is
#   fabricated.
# DIVERGENCE / NON-TERMINATION: the sibling carries no diverge-*/nonterm-*/
#   weak-diverge case, so there is nothing to port. Recorded as a KNOWN SPEC
#   HOLE. An earlier revision of this manifest called the class vacuous 'in the
#   strong sense -- not "the spec admits it", but "it cannot be written"',
#   claiming a diverging body would not elaborate. The audit MEASURED that and it
#   is false: `partial def spin xs k := spin xs k` with the table component set
#   to `spin s.classLookups lookupName` elaborates without complaint (Lean admits
#   `partial def` through an `Inhabited` default and discharges no termination
#   obligation -- this bundle sets no `loom.semantics.termination` at all, so
#   there is no total-semantics check to fail), and only the PROOF breaks. What
#   makes the class unshippable is instead the witness side: `decide` against
#   that rival fails with `Tactic `decide` failed for proposition` because the
#   opaque `spin` application never reduces, i.e. a STUCK REDUCTION carrying no
#   information about the claim rather than a refutation. So no witness of this
#   battery's shape discriminates and the class is a hole in the spec, not a
#   complete lane. (Cf. the corpus-wide termination-semantics finding.)
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this gate ignores it.
#   Nothing to port regardless — the sibling declares no @ContractOnly axioms,
#   this bundle's axioms region is EMPTY and its opaque_callees list is empty,
#   and the snapshot-invalidation effect is modeled DEEPLY rather than assumed.
#
# CLAUSE / BINDER / POINT COVERAGE (what the gate does NOT check).
#   The single obligation `correct_unregisterLookup` is DEFENDED by three
#   soundness + one admissibility expect="verify" case and ATTACKED by ten
#   expect="reject" cases.
#   Every top-level conjunct is attacked, and each INDEPENDENT one in isolation:
#     (1) result.classLookups = eraseKey s.classLookups lookupName
#         — attacked by weak-table-blind-removal, weak-noop, and IN ISOLATION by
#           weak-frame-table-other-clobber (which satisfies (2), (3) and (4)).
#           Both HALVES of the equation are now attacked separately: "too much
#           removed" by weak-frame-table-other-clobber, "something ADDED" by
#           weak-table-extra-entry (profile [0,1,1,1]), and removal MULTIPLICITY
#           ("drop every match", not just the first) by weak-erase-first-only
#           (profile [0,1,1,0]) — the two cases the audit added, because the
#           insertion half and the duplicate-key sub-domain were claimed by the
#           prose above and demonstrated by no rival. A second audit added
#           weak-table-survivor-values-clobbered (profile [0,1,1,1]), which pins
#           the surviving entries' VALUES: it keeps the exact key set AND order
#           and clobbers only the `Nat` payloads, so it is the only rival not
#           refutable on the key set alone. Without it, a clause (1) weakened
#           from a list equation to a `keys`-level statement would pass.
#     (2) result.cache = none
#         — attacked by weak-snapshot-blind-removal, weak-frame-view-other-
#           clobber, weak-view-bogus-value, and IN ISOLATION by
#           weak-reprime-current (which satisfies (1), (3) and (4)).
#     (3) getLookups result = result.classLookups
#         — attacked by weak-snapshot-blind-removal, weak-frame-view-other-
#           clobber, weak-view-bogus-value.
#     (4) lookupName ∉ keys (getLookups result)
#         — attacked by weak-table-blind-removal, weak-noop,
#           weak-snapshot-blind-removal, weak-view-bogus-value.
#   (3) and (4) are DERIVED conjuncts — each follows from (1) ∧ (2) — so no rival
#   can violate them while satisfying both independent clauses; that is a fact
#   about the spec, not a coverage gap, and the two independent clauses are each
#   isolated above.
#   The input binders are `s` (whose two fields are probed separately) and
#   `lookupName`. Across the nine reject witnesses — nine DISTINCT input
#   points — no binder is held fixed:
#     lookupName        ten distinct values (k1, k6, k2, k3, k5, k10, k8, k11,
#                       k12, k14) across the reject witnesses, plus "alpha" at
#                       the admissibility ground instance; the removed entry is
#                       at position 0 in some tables and has surviving siblings
#                       in others.
#     s.classLookups    one-, two- and three-entry tables; distinct keys and
#                       distinct values; inputs that do and do not contain the
#                       key a rival collaterally erases; and (added by the audit)
#                       a table with the SAME key twice, so removal multiplicity
#                       is exercised rather than assumed.
#     s.cache           BOTH constructors exercised: `none` (weak-table-blind-
#                       removal, weak-noop, weak-frame-table-other-clobber,
#                       weak-frame-view-other-clobber) and `some`
#                       (weak-snapshot-blind-removal, weak-reprime-current,
#                       weak-view-bogus-value). Load-bearing rather than
#                       incidental: weak-snapshot-blind-removal RETAINS that
#                       incoming value where the frozen impl overwrites it, so
#                       the pre-value is what the refutation turns on, and
#                       weak-view-bogus-value's incoming snapshot disagrees with
#                       its table (listing a name the table does not), so a spec
#                       that ignored the incoming snapshot could not refute it.
#   Every witness states its refutation at literal inputs and binds NOTHING, so
#   there are no hypotheses that could be jointly unsatisfiable and no
#   consistency probe applies. All ten were checked with scripts/lean_verify.sh:
#   each ELABORATES against its own rival (exit 0) and FAILS on the frozen
#   solution (exit 1) — and the gold-side failure is in every case the SEMANTIC
#   one, `decide` reporting that it "proved that the proposition ¬(...) is false",
#   i.e. gold provably satisfies all four conjuncts at that literal input. No
#   gold-side failure is a stuck reduction, an unknown identifier or a type
#   error, so each is a genuine discriminator rather than a syntactic accident.
#   All three positives build (exit 0); two under the frozen tactic bodies
#   unchanged, pos-direct-literal under the honest retune described above.
#
# AUDIT PROBES that found NO spec hole (recorded so the negative result is not
# re-derived). Five further wrong impls were built and their clause profiles
# machine-checked; each is refuted by the frozen spec, so none is a hole: a
# whole-table wipe [0,1,1,1], an inverted filter keeping only the named entry
# [0,1,1,0], a snapshot primed with the EMPTY list rather than cleared [1,0,0,1],
# plus the two promoted to cases above. Three CORRECT reshapes were also proven
# against the frozen spec (exit 0), so it is not over-fit: a `!(p.1 == k)`
# filter, a `match`-on-record destructuring, and a foldr-based erase needing an
# inductive bridging lemma to relate it to `eraseKey` — the last being a
# genuinely different algorithm, not a reformatting, which is the strongest
# available evidence that clause (1) pins the RESULT rather than the method.
#
# SECOND AUDIT (independent re-derivation). Every declared outcome reproduced:
# all 12 pre-existing variants rebuilt to their declared exit codes, and for all
# 9 pre-existing reject cases the FOUR-quadrant build was run rather than the two
# the gate does — witness-on-rival 0, witness-on-gold 1, and the FORGERY pair
# (the same witness with the `¬` dropped, i.e. asserting the impl is CORRECT at
# that point) 0 on gold and 1 on the rival. The gold-side exit code therefore
# TRACKS the claim rather than being constant, which is what makes it evidence;
# both directions print `Tactic \`decide\` proved that the proposition ...`, a
# plain evaluation with no stuck reduction, unknown identifier or type error.
# Clause profiles were re-derived independently by #eval over the transcribed
# rivals and every one matched its rationale, including the two isolation claims
# the battery leans on (weak-reprime-current [1,0,1,1], clause (2) alone;
# weak-frame-table-other-clobber [0,1,1,1], clause (1) alone). All 10 rivals are
# observably != gold at their own witness point (decide (rival = gold) = false),
# so no case is vacuous. Statement integrity was checked mechanically: for every
# case the file text OUTSIDE the impl and proof regions is byte-identical to the
# frozen solution and both frozen `theorem` statements are byte-identical, with
# pos-direct-literal the only case touching a tactic body at all.
#
# FURTHER AUDIT PROBES that found NO spec hole (recorded so they are not
# re-derived). Four more wrong impls, aimed at what the rival set left
# unattacked, were built and profiled; all four are REFUTED by the frozen spec:
# survivor ORDER reversed [0,1,1,1] and survivor VALUES clobbered [0,1,1,1]
# (both promoted/considered as cases — the second was added, the first was not,
# since a `keys`-level weakening is the sharper of the two and the values rival
# subsumes the order one's signature), over-broad PREFIX matching that erases
# any name having the requested one as a prefix [0,1,1,1], and a snapshot cleared
# only CONDITIONALLY on table length [1,0,0,0]. Two further CORRECT reshapes were
# proven against the frozen spec (exit 0), adding to the three already recorded:
# a `List.partition`-based erase (`.2` of the partition, plus a `match` on the
# record and `Option.none` spelled long-hand), and a structurally RECURSIVE
# erase — a different algorithm again, related to `eraseKey` only through an
# inductive bridging lemma. The recursive one is reported as a reshape that
# verifies but is NOT shippable as a case: proving it needs a named bridging
# lemma, and variant_scope correctly refuses a variant that declares a new
# theorem ('declares new theorem/lemma [eraseRec_eq]'), so it stays a probe.
# Where an E-attempt first failed it was traced to the audit's own proof-script
# bug (a `not ∘ f` vs `!f` normal-form mismatch in the partition reshape, fixed
# by adding `Function.comp_def` to the simp set) rather than to the spec.
AXIOM_TESTS = []
