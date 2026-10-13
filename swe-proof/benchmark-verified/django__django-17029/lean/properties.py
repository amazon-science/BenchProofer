"""properties.py — G-PBT falsification battery for django__django-17029 (lean).

PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
mechanics re-expressed against this backend's carrier. NOT a Lean module; a
record of adversarially-reasoned cases the G-PBT gate executes and stamps a
verdict onto.

Each SPEC case is a FULL ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte: region surgery edits only text strictly inside
``-- impl-start`` / ``-- impl-end`` and, where a positive legitimately reproves,
the tactic body inside ``-- proof-start`` / ``-- proof-end``. Both regions are
elided by the consumer spec view, so ``markers.same_spec`` holds by
construction; the ``theorem correct_clearCaches`` STATEMENT is kept
byte-identical in every case and no case introduces an ``axiom`` / ``sorry`` /
``admit`` / ``native_decide`` / new lemma. So a rejection is always attributable
to the postcondition, never to a tampered obligation.

DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json). ONE
obligation over ONE structure-valued binder:

    problem_spec_clearCaches (st : CacheRegistry) (result : CacheRegistry) : Prop :=
      result.nameLookupCache = [] ∧
      result.entityListCache = [] ∧
      result.ready = st.ready

    theorem correct_clearCaches :
      ∀ (st : CacheRegistry), problem_spec_clearCaches st (implementation_clearCaches st)

The discard operation must return the registry to a clean state: after it runs,
*every* memoized result is gone, so the next query recomputes from current
registry contents instead of being served from a stale cache. There is NO
precondition hypothesis in the obligation, so the admitted domain is TOTAL —
every registry state is in-domain, including the already-empty corner.

THREE independent top-level conjuncts, all LOAD-BEARING, no slack anywhere:

  (Q1) ``result.nameLookupCache = []`` — the DISCRIMINATING clause. The reported
       behaviour is precisely a discard that empties one memoizing query's
       result cache while leaving another query's memoized answers in place; a
       later caller then still receives stale results for that query. A body
       that never writes this field, drops only its head, re-primes it, pins it
       to a copy of the OTHER cache's pre-value, or guards its discard on the
       other cache's state fails here.
  (Q2) ``result.entityListCache = []`` — the same requirement for the second
       memoizing query. The spec demands EVERY memoized result be gone, not
       just the one the issue names, so this clause is attacked in its own
       right.
  (Q3) ``result.ready = st.ready`` — the FRAME clause. The readiness flag is
       only consulted; a discard that also writes it (to either literal, or to
       a value recomputed from the cache contents) fails here even though both
       caches end up empty.

BINDER STRUCTURE (read before judging binder coverage). The obligation binds one
argument, ``st : CacheRegistry``, but it is a THREE-FIELD structure and each
clause names a different field, so the meaningful input axes are the fields —
and a rival is free to COUPLE them, making one clause's outcome depend on
another field. Four rivals exist specifically to exercise that coupling
(``weak-coupled-guard``, ``weak-proxy-prevalue``, ``weak-flag-from-cache``,
``weak-guard-on-ready``),
because a battery whose witnesses all held a field fixed would verify such a
rival and never notice. The twelve reject witnesses probe TWELVE DISTINCT input
points and vary all three fields: ``nameLookupCache`` over
{empty, one entry, two entries} with both ``some`` and ``none`` values,
``entityListCache`` over {empty, one entry, two entries} covering all four
inclusion-flag key pairs and both empty and non-empty value lists, and ``ready``
over {true, false}. No field is pinned.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS here, and the sibling reaches the same
    conclusion from the other direction. There it reasons over two FULL heap
    permissions on the occupancy fields and asks whether a read-only
    half-permission input could be overwritten to satisfy the post-image
    vacuously; it records that there is no such read-only input, both fields
    being genuinely written. On this carrier the question cannot even be posed:
    Lean is referentially transparent, ``st`` is an immutable value with no heap
    footprint, no aliasing and no fractional-permission system. Not fabricated
    (porting map: vacuous here). What DOES exist here and has no sibling
    counterpart is a real frame CLAUSE (Q3) over a field the sibling's carrier
    does not model at all, so the three ``weak-flag-*`` rivals below attack the
    frame obligation directly rather than as a permission question.

  * UNGROUNDED-ORACLE ECHO — N/A on both backends for the same reason. The
    ``pure`` region declares only the input structure; the ``axioms`` region is
    empty. There is no opaque callee, no answer-key helper and no oracle in the
    contract. Q1/Q2 are pinned to the literal ``[]`` and Q3 to the input's own
    field, all grounded directly in the required post-state, so there is no
    value an "echo" could carry that satisfies the post-image yet is wrong. The
    honest cheapest faithful body is therefore "write ``[]`` twice, keep the
    flag", which is what the positive controls are. Consequently the carrier is
    fully TRANSPARENT and every witness below closes by ``decide`` at literal
    inputs, binding NOTHING — so no witness can be inconsistent-by-hypothesis
    and the gate's consistency probe has nothing to find.

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE here, and specifically NOT
    vacuous: the earlier reading ("a diverging body cannot be WRITTEN on a total
    carrier") was measured FALSE and is corrected here. Two diverging bodies ARE
    definable in the impl region and both were built:

      (i) ``while true do s := s`` inside the frozen ``Id.run do`` skeleton —
          the impl region elaborates cleanly (Lean compiles ``while`` to
          ``forIn Lean.Loop.mk``, whose recursion is not structural), and
      (ii) ``partial def implementation_clearCaches st := implementation_clearCaches st``.

    Both are REJECTED, so the spec does not admit divergence and there is no
    spec hole: (i) fails the frozen obligation with ``Application type
    mismatch: rfl has type ?m = ?m but is expected to have type
    (implementation_clearCaches st).ready = st.ready`` — the loop term never
    reduces to a record, so not even the FRAME clause closes.

    What blocks the case is the WITNESS half, not definability. The refutation
    must ELABORATE against the rival, and the rival's result is
    ``forIn Lean.Loop.mk ...``, which the kernel cannot reduce: the battery's
    own ``decide`` witness shape fails against it with ``Tactic `decide` failed
    for proposition ... forIn Lean.Loop.mk`` (exit 1) — the documented
    stuck-reduction class, which the gate scores ``witness-unproven`` /
    ``witness-undecided``, an INCONCLUSIVE outcome that fails the gate rather
    than passing it. Nor does a hypothesis-conditioned witness rescue it: stated
    at a point described by hypothesis (``(implementation_clearCaches r).ready =
    false``) it elaborates against the rival (exit 0) but ALSO against the frozen
    solution (exit 0) — on gold the hypothesis is false, so ``simp [h]`` closes
    the goal from a contradiction — which the gate scores ``witness-vacuous``.
    A ``witness_reference`` cannot help either: it replaces the GOLD-side
    subject, and the blocked half here is the rival side. So the class is real
    and correctly rejected, but no admissible witness for it exists on this
    carrier; it is recorded as a KNOWN UNSHIPPABLE class rather than as vacuous
    (a vacuous class would claim the battery is complete). This bundle sets no
    ``loom.semantics.termination`` option — it is a plain total Lean ``def`` —
    so the ``partial``-semantics known-hole reading in
    ``the corpus-wide termination-semantics finding`` does not apply either.

  * SELF-ECHO — the sibling's ``weak-self-echo`` (discharge the contract by
    calling the function under spec) is INEXPRESSIBLE here, and was dropped only
    after being built and run. See the footer for the exact error.

  * AXIOM lane — DROPPED. The gate ignores ``AXIOM_TESTS``, and this bundle
    declares no ``axiom`` in any case (the discard is modeled deeply as two
    field writes; the standard-library memoization wrapper whose emptied-cache
    effect they refine is an A-reference validated out-of-band by G-AX).

WITNESS PLACEMENT. The spec is a bare Prop over a decidable-equality carrier
(lists of string/option/bool tuples), so each reject rival reaches it directly:
``¬ problem_spec_clearCaches r (implementation_clearCaches r)`` at a concrete
registry literal ``r``, closed by ``decide`` after unfolding. Checked in a file
whose ``proof`` region the gate strips, so no tactic script can mask the verdict
— which matters here because every rival RESHAPES the impl and the frozen
``refine ⟨rfl, rfl, rfl⟩`` script fails on a merely-reshaped-but-correct body
too. Every reject witness below was run against BOTH the rival (exit 0,
elaborates) and the frozen solution (exit 1, ``decide`` proves the spec HOLDS
there) with two real builds each, and was SEEN to discriminate. None uses
``sorry`` / ``admit`` / ``native_decide`` and none introduces a declaration.
"""
from pathlib import Path

INSTANCE = "django__django-17029"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies WHOLLY inside the region it names and is unique in
# Solution.lean (both facts asserted at load), so every variant's edit is
# confined to the impl region plus, for the one positive that reproves, the
# proof body — and same_spec holds by construction.
# ---------------------------------------------------------------------------
_W_NAME = "  s := { s with nameLookupCache := [] }\n"
_W_ENT = "  s := { s with entityListCache := [] }\n"
_C_NAME = "  -- discard the name-lookup cache\n"
_C_ENT = "  -- discard the entity-list cache\n"
_C_TAIL = ("  -- a readiness-gated refresh of per-entity metadata runs here; it touches a\n"
           "  -- separate metadata layer and leaves both result caches (and `ready`) intact\n")
_HEAD = ("def implementation_clearCaches (st : CacheRegistry) : CacheRegistry := Id.run do\n"
         "  let mut s := st\n")

# The whole frozen impl region body, verbatim.
_IMPL = _HEAD + _C_NAME + _W_NAME + _C_ENT + _W_ENT + _C_TAIL + "  return s"

# The frozen proof body (tactic lines only, strictly inside proof-start/-end).
_PROOF = "  intro st\n  refine ⟨rfl, rfl, rfl⟩"

for _a in (_W_NAME, _W_ENT, _IMPL, _PROOF):
    assert _BASE.count(_a) == 1, f"frozen region anchor drifted: {_a!r}"


def _impl(body, proof=None):
    """Full Solution.lean variant: impl region replaced; proof body optionally
    RE-CLOSED (never weakened — the theorem statement is untouched)."""
    out = _swap(_BASE, _IMPL, body)
    return _swap(out, _PROOF, proof) if proof is not None else out


def _do(lines, proof=None):
    """A variant whose impl keeps the frozen `Id.run do` / `let mut s := st`
    skeleton and substitutes the sequence of state writes."""
    return _impl(_HEAD + lines + "  return s", proof)


# ---------------------------------------------------------------------------
# Witness helper. A refutation at a CONCRETE registry literal: `decide` computes
# both the spec and the impl there (the carrier is fully transparent), so the
# snippet binds NOTHING and cannot be inconsistent-by-hypothesis.
# ---------------------------------------------------------------------------
def _reg(name, entity, ready):
    return ("{ nameLookupCache := %s, entityListCache := %s, ready := %s }"
            % (name, entity, ready))


def _witness(name, entity, ready):
    r = _reg(name, entity, ready)
    return ("example :\n"
            "    ¬ problem_spec_clearCaches\n"
            f"      {r}\n"
            f"      (implementation_clearCaches {r}) := by\n"
            "  unfold problem_spec_clearCaches implementation_clearCaches\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify, else the postcondition is SPEC-TOO-STRONG (over-fit to
    # the frozen body's syntactic shape). Each keeps the byte-identical
    # obligation; the one that reshapes control flow honestly RE-CLOSES the
    # proof (no new axiom / lemma / sorry). All confirmed to verify with real
    # builds.
    # =====================================================================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Discard the two caches in the OPPOSITE textual order. They are
        # independent fields of an immutable value, so the final state is
        # identical and the frozen `rfl`-triple still closes.
        "module": _impl(_HEAD + _C_ENT + _W_ENT + _C_NAME + _W_NAME + _C_TAIL
                        + "  return s"),
        "rationale": (
            "structurally-different but CORRECT: the two INDEPENDENT field "
            "writes are performed in the opposite textual order (entity-list "
            "cache first, then name-lookup cache). No loop, no new lemma, no "
            "coupling — the post-state is identical on every input, so Q1 "
            "(`result.nameLookupCache = []`), Q2 (`result.entityListCache = "
            "[]`) and Q3 (`result.ready = st.ready`) all still discharge under "
            "the frozen tactic script. If it FAILS => SPEC-TOO-STRONG: a "
            "faithful, differently-shaped correct discard would be rejected "
            "for its textual order. (Sibling: pos-reorder.)"),
    },
    {
        "id": "pos-literal",
        "kind": "soundness",
        "expect": "verify",
        # Drop the imperative skeleton entirely: build the cleaned registry as
        # one record literal. Maximally different SHAPE, identical behaviour,
        # and the frozen proof still closes by reflexivity.
        "module": _impl(
            "def implementation_clearCaches (st : CacheRegistry) : CacheRegistry :=\n"
            "  { nameLookupCache := [], entityListCache := [], ready := st.ready }"),
        "rationale": (
            "structurally-different but CORRECT: the imperative "
            "bind-and-update skeleton is replaced by a single record literal "
            "that states the cleaned registry outright — both caches empty, "
            "the readiness flag carried through from the input. Behaviourally "
            "identical on every input, so all three clauses discharge under "
            "the frozen script. This is the cheapest HONEST body and it is not "
            "an ungrounded echo: Q1/Q2 are pinned to the literal `[]` and Q3 "
            "to the input's own field, so any WRONG value here fails the "
            "postcondition. If it FAILS => SPEC-TOO-STRONG. (Sibling: "
            "pos-localvar, whose typed-local reshaping is the same idea on a "
            "carrier with no record syntax.)"),
    },
    {
        "id": "pos-derive-after-clear",
        "kind": "soundness",
        "expect": "verify",
        # CORRECT-by-construction, and the exact dual of weak-proxy-prevalue
        # below: derive the entity-list cache FROM the name-lookup cache, but
        # only AFTER that cache has been emptied — so the derived value is `[]`
        # on every input. Shipped precisely to show the spec rejects the proxy
        # rival for the RIGHT reason (reading a stale pre-value) rather than
        # for deriving one field from another at all.
        "module": _do(
            "  s := { s with nameLookupCache := [] }\n"
            "  s := { s with entityListCache := s.nameLookupCache.map (fun _ => ((true, true), [])) }\n"),
        "rationale": (
            "structurally-different but CORRECT-by-construction: the "
            "name-lookup cache is emptied first, then the entity-list cache is "
            "DERIVED from that already-emptied cache (a map over the empty "
            "list, hence `[]`), so Q1 and Q2 both hold on every input and Q3 "
            "is untouched. This is the exact DUAL of the weak-proxy-prevalue "
            "rival, which performs the same derivation from the PRE-value; "
            "shipping both pins that the spec rejects the rival for reading a "
            "stale non-empty cache rather than for the derivation shape "
            "itself. If it FAILS => SPEC-TOO-STRONG. (Sibling: "
            "pos-copy-other.)"),
    },
    {
        "id": "pos-readiness-branch",
        "kind": "soundness",
        "expect": "verify",
        # Branch on the readiness flag and discard both caches on BOTH arms (in
        # opposite orders). The flag is only CONSULTED, never written, so the
        # post-state is the same on every input — but the branch is a real
        # reshaping, so the frozen `refine ⟨rfl, rfl, rfl⟩` no longer closes
        # and the proof is honestly re-closed by splitting the branch and
        # discharging each arm by reflexivity. The theorem STATEMENT is
        # byte-identical; no axiom, lemma, sorry or native_decide is added.
        "module": _do(
            "  if s.ready then\n"
            "    s := { s with nameLookupCache := [], entityListCache := [] }\n"
            "  else\n"
            "    s := { s with entityListCache := [], nameLookupCache := [] }\n",
            "  intro st\n"
            "  unfold problem_spec_clearCaches implementation_clearCaches\n"
            "  simp only [Id.run]\n"
            "  split <;> exact ⟨rfl, rfl, rfl⟩"),
        "rationale": (
            "structurally-different but CORRECT: the body branches on the "
            "readiness flag and empties BOTH caches on BOTH arms (in opposite "
            "orders), so the post-state is identical on every input and the "
            "flag is still only CONSULTED, never written — Q1, Q2 and Q3 all "
            "hold. The branch is what a faithful body that already consults "
            "that flag for its auxiliary refresh could equally look like. The "
            "frozen reflexivity triple no longer closes the branched goal, so "
            "the proof is honestly RE-CLOSED (`split` then reflexivity per "
            "arm) with the theorem statement byte-identical and nothing "
            "assumed. If it FAILS => SPEC-TOO-STRONG: the postcondition would "
            "be over-fit to a single straight-line branch shape."),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation carries NO precondition hypothesis, so the
    # sibling's "a normal input satisfies the precondition" probe is vacuous
    # here: nothing could exclude the failing-test-shaped input. Re-aimed at
    # the residual total-domain risk, that the post-image is DEGENERATE at the
    # corner that matters.
    # =====================================================================
    {
        "id": "admiss-primed-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The failing test primes BOTH memoized caches non-empty before the
        # discard, so the interesting corner is a registry where each cache
        # actually holds an entry and emptying it is a REAL transition rather
        # than a no-op. The in-region `have` pins exactly that corner: the
        # probe registry's two caches are each NON-empty, and the spec is
        # satisfied by the cleaned registry at that very point. The frozen
        # body and proof follow verbatim, so Q1/Q2/Q3 discharge as well. The
        # `have` is LIVE — replacing one conjunct with a false claim about the
        # same point leaves the build failing with `decide` proving that
        # conjunct false (confirmed out-of-band).
        "module": _do(
            "  let probe : CacheRegistry :=\n"
            "    { nameLookupCache := [(\"k\", some \"v\")],\n"
            "      entityListCache := [((true, false), [\"e\"])], ready := true }\n"
            "  have _live : probe.nameLookupCache ≠ [] ∧ probe.entityListCache ≠ [] ∧\n"
            "      problem_spec_clearCaches probe\n"
            "        { probe with nameLookupCache := [], entityListCache := [] } :=\n"
            "    ⟨by decide, by decide, rfl, rfl, rfl⟩\n"
            "  s := { s with nameLookupCache := [] }\n"
            "  s := { s with entityListCache := [] }\n"),
        "rationale": (
            "the modeled behaviour is admissible AND non-degenerate at the "
            "corner the failing test exercises: both memoizing queries' result "
            "caches are primed NON-EMPTY before the discard, so a registry "
            "whose two caches each genuinely hold an entry must be in-domain "
            "and emptying each must be a REAL state transition, not a no-op "
            "that would hold trivially. The in-region `have` pins exactly "
            "that: the probe registry's caches are each `≠ []`, and the "
            "postcondition is satisfied by the cleaned registry AT that point "
            "(so the post-image is inhabited where it matters, with the "
            "readiness flag carried through). The frozen body and proof follow "
            "verbatim, so Q1/Q2/Q3 discharge too. The `have` is LIVE — a false "
            "claim about the same point fails the build. Re-aimed from the "
            "sibling admiss-roundtrip, whose construct-a-fresh-registry / "
            "precondition-admission half has no counterpart on an obligation "
            "with no precondition hypothesis and no heap."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete registry literal, and the refinement argument that its
    # faithful counterpart would NOT resolve the failing test. Witnesses probe
    # ELEVEN DISTINCT points and vary all three fields (see BINDER STRUCTURE).
    # =====================================================================
    {
        "id": "weak-entity-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported defect: discard one memoizing query's memoized answers
        # and leave the other query's at whatever they were on entry. Isolates
        # Q1 — Q2 and Q3 are kept correct.
        "module": _do(_C_ENT + _W_ENT),
        "refinement": (
            "this is the pre-change behaviour the issue reports and the "
            "failing test observes: the registry's single discard operation "
            "empties the entity-list query's memoized answers but never "
            "touches the name-lookup query's, so that query keeps serving "
            "stale results after an operation documented as discarding ALL "
            "internal caches. Its faithful counterpart is the un-changed "
            "discard; the failing test primes that second cache, runs the "
            "discard, and then asserts that cache holds nothing, which FAILS "
            "because the entry primed for it is still retained. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from Q1 (`result.nameLookupCache = []`): the body never "
            "writes that field, so at return it still holds its arbitrary "
            "on-entry entries, which cannot be proven empty (the domain is "
            "total — every registry state is admitted). Q2 and Q3 are kept "
            "correct, isolating Q1 as the ONLY failing clause. If this "
            "VERIFIED the spec would admit the reported defect => "
            "SPEC-TOO-WEAK, and the discriminating content of the required "
            "behaviour would be unpinned. Refuted at a registry whose "
            "name-lookup cache holds one resolved entry and whose entity-list "
            "cache is non-empty, so leaving the first untouched is observable. "
            "(Sibling: weak-models-only.)"),
        "witness": _witness('[("k", some "v")]', '[((true, false), ["a"])]', 'true'),
    },
    {
        "id": "weak-name-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The DUAL omission: discard the second query's cache and leave the
        # first's. Isolates Q2 — Q1 and Q3 are kept correct.
        "module": _do(_C_NAME + _W_NAME),
        "refinement": (
            "the dual omission — a change that REPLACED the existing discard "
            "of one memoizing query's cache with a discard of the other, "
            "instead of adding it. The failing test primes each of the two "
            "memoized caches and asserts BOTH hold nothing after the discard; "
            "leaving the entity-list query's memoized answers in place FAILS "
            "the assertion about that cache. Does NOT resolve."),
        "rationale": (
            "REJECT from Q2 (`result.entityListCache = []`): that field is "
            "left at its on-entry value and is not provably empty. Q1 and Q3 "
            "are kept correct, isolating Q2. This is the mirror of "
            "weak-entity-only and is what pins that the spec requires EVERY "
            "memoized result to be discarded, not just the one the issue names "
            "— if it VERIFIED, a third of the post-image would be dead => "
            "SPEC-TOO-WEAK. Refuted at a DIFFERENT point from "
            "weak-entity-only: the surviving cache is the OTHER field, its "
            "entry carries an empty selected-entity list under the "
            "both-flags-set key, the name-lookup entry resolves to 'no such "
            "name', and the readiness flag is the opposite value — so the two "
            "witnesses jointly show the post-image constrains both caches. "
            "(Sibling: weak-swappable-only.)"),
        "witness": _witness('[("p", none)]', '[((true, true), [])]', 'false'),
    },
    {
        "id": "weak-neither",
        "kind": "uniqueness",
        "expect": "reject",
        # A no-op discard: return the registry untouched. Fails Q1 AND Q2.
        "module": _do(""),
        "refinement": (
            "a no-op discard is what an operation whose body short-circuited "
            "(an early return, or a body that was never wired up) would do: "
            "neither memoizing query's memoized answers are dropped, so both "
            "caches stay exactly as the failing test primed them. The test "
            "asserts BOTH hold nothing, so both assertions FAIL. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from Q1 AND Q2 simultaneously: both caches keep their "
            "on-entry entries and neither is provably empty. The floor case — "
            "if it VERIFIED the spec would not require ANY memoized result to "
            "be discarded => SPEC-TOO-WEAK, and every other case in this "
            "battery would be meaningless. Refuted at yet another point: both "
            "caches non-empty (at a third combination of resolved-name and "
            "inclusion-flag key shapes), so a body that empties neither is "
            "observably wrong on both clauses at once. (Sibling: "
            "weak-neither.)"),
        "witness": _witness('[("q", some "r")]', '[((false, true), ["z"])]', 'true'),
    },
    {
        "id": "weak-evict-one",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN by value: drop ONE memoized entry per cache instead of
        # all of them. Correct only where a cache held at most one entry.
        "module": _do(
            "  s := { s with nameLookupCache := s.nameLookupCache.tail }\n"
            "  s := { s with entityListCache := s.entityListCache.tail }\n"),
        "refinement": (
            "dropping a single memoized entry per cache models a discard that "
            "pops one memoization entry (e.g. the least-recently-used head) "
            "instead of discarding the whole cache. Whenever a cache retained "
            "two or more answers on entry it stays populated, so a later "
            "caller still receives stale results. The failing test primes the "
            "caches and asserts each holds nothing afterwards; a single-entry "
            "eviction leaves a non-empty cache for any query memoized more "
            "than once, which FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from Q1 AND Q2 on the two-or-more-entries sub-domain: for "
            "a cache holding n >= 2 entries the body leaves n-1 > 0, and the "
            "domain is total so both clauses must be proven for EVERY admitted "
            "registry. A genuine PARTIAL-DOMAIN-by-value break — the body is "
            "correct exactly where a cache held at most one entry, which is "
            "the sub-domain on which discarding is nearly a no-op anyway. If "
            "it VERIFIED the post-state would not actually be pinned to empty "
            "=> SPEC-TOO-WEAK on a cache-size boundary no byte-fuzzer targets. "
            "Refuted at the only witness in the battery where BOTH caches hold "
            "TWO entries, so both tails are non-empty and both clauses fail at "
            "once; the second entity-list entry also exercises the "
            "no-flags-set key with an empty value list. (Sibling: "
            "weak-decrement.)"),
        "witness": _witness('[("a", none), ("b", some "c")]',
                            '[((true, false), ["x"]), ((false, false), [])]',
                            'false'),
    },
    {
        "id": "weak-reprime-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: discard one cache correctly, then re-prime the other with
        # a fixed entry. Wrong at EVERY input, so its witness is placed at the
        # already-empty boundary — the one point at which several other rivals
        # here happen to be RIGHT.
        "module": _do(
            "  s := { s with entityListCache := [] }\n"
            "  s := { s with nameLookupCache := [(\"k\", none)] }\n"),
        "refinement": (
            "discarding one memoizing query's cache but leaving the other "
            "holding a fixed entry models a discard that empties the first "
            "cache and then immediately re-memoizes one canonical lookup on "
            "the way out (or never fully empties it). The failing test asserts "
            "that second cache holds nothing after the discard; a single "
            "retained entry FAILS that assertion just as the un-changed "
            "behaviour does. Does NOT resolve."),
        "rationale": (
            "REJECT from Q1 (`result.nameLookupCache = []`): the body pins "
            "that field to a one-entry list, and the clause demands exactly "
            "empty — there is no slack in the post-image, so a single retained "
            "memoized answer is as wrong as a full cache. Q2 and Q3 are kept "
            "correct, isolating Q1. Refuted at the ALREADY-EMPTY boundary "
            "(both caches empty on entry), which lies inside the sub-domain "
            "where weak-entity-only, weak-evict-one, weak-conditional-skip, "
            "weak-coupled-guard and weak-proxy-prevalue are ALL accidentally "
            "correct (measured: that is exactly the class where the "
            "name-lookup cache starts empty, so the both-caches-empty registry "
            "is one point of it rather than the only one) — so this witness is "
            "the case that shows the post-image bites even "
            "on a registry with nothing memoized, where the operation should "
            "be a no-op and this body instead CREATES stale state. (Sibling: "
            "weak-stale-swappable.)"),
        "witness": _witness('[]', '[]', 'true'),
    },
    {
        "id": "weak-conditional-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: discard the first cache ONLY when it was already
        # nearly-empty (fewer than two memoized answers); leave a fuller one
        # stale. Correct on the small-cache class, wrong exactly where the
        # defect is observable.
        "module": _do(
            "  s := { s with entityListCache := [] }\n"
            "  if s.nameLookupCache.length < 2 then\n"
            "    s := { s with nameLookupCache := [] }\n"),
        "refinement": (
            "emptying the first memoizing query's cache only when it already "
            "held fewer than two answers models a mis-guarded size "
            "optimisation that skips the discard on a fuller cache. The "
            "failing test primes that cache and asserts it holds nothing "
            "afterwards; on any run where two or more answers were memoized "
            "the cache stays populated and the assertion FAILS — and 'the "
            "cache is full' is precisely the situation in which a "
            "stale-memoization defect is observable at all. A genuine "
            "partial-domain break on the cache-size boundary. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from Q1 (`result.nameLookupCache = []`): on the sub-domain "
            "where that cache held two or more entries the body leaves it "
            "untouched and non-empty, so the clause cannot be proven for all "
            "admitted registries. Q2 and Q3 are kept correct, isolating Q1. "
            "Distinct from weak-evict-one, which is wrong on the same "
            "sub-domain but by leaving n-1 rather than n, so each is refuted by "
            "its own reasoning; and distinct from weak-entity-only, which is "
            "wrong on the WHOLE domain rather than just this class. Refuted at "
            "a registry whose name-lookup cache holds exactly TWO entries — "
            "the least size the guard excludes, the strongest point to place "
            "it — with the entity-list cache EMPTY, a combination no other "
            "witness uses. (Sibling: weak-conditional-skip.)"),
        "witness": _witness('[("s", some "t"), ("u", none)]', '[]', 'false'),
    },

    # ---- FIELD-COUPLING rivals. No sibling counterpart: they exist because
    # ---- each clause names one field's post-state, and a rival is free to
    # ---- make one clause's outcome depend on ANOTHER field. A battery whose
    # ---- witnesses all held a field at one value would verify these and never
    # ---- notice.
    {
        "id": "weak-coupled-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Discard the first cache only when the SECOND one was non-empty on
        # entry: makes Q1's outcome depend on the entity-list field. Correct on
        # the whole sub-domain where the second cache started non-empty — which
        # includes weak-entity-only's OWN witness point, so a battery that held
        # the entity-list cache non-empty throughout would verify this rival.
        "module": _do(
            "  if !s.entityListCache.isEmpty then\n"
            "    s := { s with nameLookupCache := [] }\n"
            "  s := { s with entityListCache := [] }\n"),
        "refinement": (
            "gating one memoizing query's discard on whether the OTHER "
            "query's cache currently holds anything models a discard that "
            "treats a single cache as the trigger for the whole clean-up — the "
            "second drop runs only when the first cache happened to be "
            "populated. Whenever the entity-list cache is already empty and "
            "the name-lookup cache is not (exactly how the reported behaviour "
            "was noticed: the name-lookup query is consulted on repeated runs "
            "while the entity-list cache has just been emptied) the "
            "name-lookup answers are never dropped, and the failing test's "
            "assertion that that cache holds nothing FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from Q1 (`result.nameLookupCache = []`): on the sub-domain "
            "where the entity-list cache starts empty, the guard is false and "
            "the name-lookup cache is left at its on-entry entries, so Q1 is "
            "not provable for all admitted registries. Q2 and Q3 are kept "
            "correct, isolating Q1. THE FIELD-COUPLING CASE: this rival makes "
            "Q1's outcome depend on the field Q2 names, so it is correct on the "
            "ENTIRE sub-domain where the entity-list cache starts non-empty — "
            "which includes weak-entity-only's own witness point, so a battery "
            "that held the entity-list cache non-empty throughout would verify "
            "it and report SOUND. (The two rivals are NOT nested: at a "
            "name-lookup-non-empty / entity-list-empty registry both are wrong, "
            "so neither witness subsumes the other.) Refuted at the corner that "
            "separates it from the "
            "frozen behaviour — entity-list cache empty (its own clause holds "
            "trivially) while the name-lookup cache holds an entry. If it "
            "VERIFIED, the spec would let one cache's discard be conditioned "
            "on the other's state => SPEC-TOO-WEAK."),
        "witness": _witness('[("g", some "h")]', '[]', 'true'),
    },
    {
        "id": "weak-proxy-prevalue",
        "kind": "uniqueness",
        "expect": "reject",
        # Derive the second cache from the FIRST cache's PRE-value, then empty
        # the first. Looks like the correct pos-derive-after-clear but reads
        # the value BEFORE the discard, so the second cache inherits the
        # first's stale size. Wrong exactly where the first cache was
        # non-empty.
        "module": _do(
            "  s := { s with entityListCache := s.nameLookupCache.map (fun _ => ((true, true), [])) }\n"
            "  s := { s with nameLookupCache := [] }\n"),
        "refinement": (
            "'synchronising' one memoizing query's cache to the other's, read "
            "BEFORE the other is discarded, models a discard that reports the "
            "second cache as matching the first while never actually dropping "
            "the second query's memoized answers — it rebuilds them from the "
            "first cache's stale contents. It only ever looks right when the "
            "first cache was already empty. The failing test primes both "
            "caches and asserts each holds nothing; the second inherits an "
            "entry per primed answer of the first and FAILS. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from Q2 (`result.entityListCache = []`): the field is "
            "DERIVED from the other cache's PRE-value, which the total domain "
            "admits at any size, so it is not provably empty. Q1 and Q3 are "
            "kept correct, isolating Q2. The NEAR-MISS of "
            "pos-derive-after-clear, which performs the same derivation AFTER "
            "the discard and is correct: the two ship together so the reject "
            "is attributable to reading a stale non-empty cache rather than to "
            "the derivation shape itself. Second field-coupling case — here "
            "Q2's post-value is SOURCED from another field rather than merely "
            "guarded by it, so the witness must be placed where that source is "
            "non-empty and its own field is EMPTY on entry (the mirror image "
            "of weak-coupled-guard's corner), which is where a battery holding "
            "the name-lookup cache empty would miss it. If it VERIFIED, the "
            "spec would accept one cache's contents standing in for the "
            "other's => SPEC-TOO-WEAK. (Sibling: the value-proxy reading of "
            "weak-copy-other, which the nagini carrier could only express in "
            "its already-cleared — and therefore CORRECT — order.)"),
        "witness": _witness('[("i", none)]', '[]', 'false'),
    },

    {
        "id": "weak-guard-on-ready",
        "kind": "uniqueness",
        "expect": "reject",
        # THIRD coupling direction, and the one the other two do not reach:
        # weak-coupled-guard couples cache->cache and weak-flag-from-cache
        # couples flag->cache, but nothing here made a CACHE clause depend on
        # the READINESS flag. This body gates Q1's discard on `ready`, which is
        # the field the spec says is only CONSULTED — so it reads the flag for a
        # purpose the frame clause never licenses.
        "module": _do("  s := { s with entityListCache := [] }\n"
                      "  if s.ready then\n"
                      "    s := { s with nameLookupCache := [] }\n"),
        "refinement": (
            "gating one memoizing query's discard on the readiness flag models "
            "a discard that folds that query's clean-up into the "
            "readiness-gated branch that performs the auxiliary per-entity "
            "metadata refresh, instead of running it unconditionally alongside "
            "the other discard. The registry performs a discard while it is NOT "
            "yet ready — during its own load sequence, and on the "
            "reconfiguration path the failing test runs under, which lowers the "
            "flag before discarding and reloading — so on exactly those runs "
            "that cache is never emptied and keeps serving stale results. The "
            "failing test asserts it holds nothing after the discard, which "
            "FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from Q1 (`result.nameLookupCache = []`): on the sub-domain "
            "where the flag enters `false` the guard is false and the "
            "name-lookup cache is left at its on-entry entries, so Q1 is not "
            "provable for all admitted registries. Q2 and Q3 are kept correct "
            "(the flag is only READ, so the frame still holds), isolating Q1. "
            "THE THIRD COUPLING DIRECTION: weak-coupled-guard makes a cache "
            "clause depend on the other CACHE and weak-flag-from-cache makes "
            "the FRAME clause depend on a cache, but this is the only rival "
            "that makes a CACHE clause depend on the READINESS flag — the axis "
            "a battery would miss by treating `ready` as write-only-frame and "
            "never varying it as an INPUT that other clauses can read. Refuted "
            "at a registry entering with the flag `false` and a non-empty "
            "name-lookup cache, so the guard is skipped and Q1 is observably "
            "violated while Q2/Q3 hold. If it VERIFIED, the spec would let a "
            "required discard be conditioned on a flag it may only consult => "
            "SPEC-TOO-WEAK."),
        "witness": _witness('[("d", some "e")]', '[((true, false), ["m"])]',
                            'false'),
    },

    # ---- FRAME-CLAUSE rivals. No sibling counterpart: the nagini carrier does
    # ---- not model the readiness flag at all, so Q3 is a clause this backend
    # ---- adds. All three empty BOTH caches correctly (Q1 and Q2 discharge) and
    # ---- fail ONLY on the frame — the shape a battery that read the spec as
    # ---- "two emptiness clauses" would never attack.
    {
        "id": "weak-flag-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _do(_W_NAME + _W_ENT + "  s := { s with ready := true }\n"),
        "refinement": (
            "the discard operation only CONSULTS the readiness flag, to decide "
            "whether its auxiliary per-entity metadata refresh runs; a body "
            "that also SETS the flag is a discard that reports the registry as "
            "ready as a side effect of clearing it. Its faithful counterpart "
            "does not resolve, and fails the target test itself rather than "
            "merely a neighbour: the registry's own load sequence performs a "
            "discard partway through, before the registry is ready, and the "
            "reconfiguration path the failing test runs under lowers the flag "
            "and then performs a discard before reloading. Forcing the flag up "
            "at that point makes the reload short-circuit as already-complete, "
            "so the registry is left with no applications configured and the "
            "test's own priming queries fail. Does NOT resolve."),
        "rationale": (
            "REJECT from Q3 (`result.ready = st.ready`) alone: the body pins "
            "the flag to `true`, so on the sub-domain where it entered `false` "
            "the frame clause is violated. Q1 and Q2 are kept fully correct — "
            "both caches ARE emptied — which is what makes this rival the "
            "sharpest test of the frame: a spec read as 'two emptiness "
            "clauses' would admit it. If it VERIFIED, the spec would permit a "
            "discard to mutate state it is only supposed to consult => "
            "SPEC-TOO-WEAK. Refuted at a registry entering with the flag "
            "`false` (the only sub-domain where this body is wrong) and both "
            "caches non-empty, so the emptiness clauses are non-trivially "
            "satisfied at the same point and the failure is unambiguously the "
            "frame."),
        "witness": _witness('[("w", none)]', '[((true, true), ["v"])]', 'false'),
    },
    {
        "id": "weak-flag-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _do(_W_NAME + _W_ENT + "  s := { s with ready := false }\n"),
        "refinement": (
            "the dual frame violation: a discard that lowers the readiness "
            "flag, on the reasoning that a registry whose memoized results "
            "were just dropped is no longer in a settled state. Its faithful "
            "counterpart does not resolve. The reconfiguration path the "
            "failing test runs under restores the flag and then performs a "
            "discard, which would immediately lower it again; the very next "
            "reconfiguration then rejects the request outright because the "
            "registry reports itself not ready, so the failing test errors "
            "instead of reaching its assertions — and a neighbouring test that "
            "asserts the main registry reports ready fails too. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from Q3 (`result.ready = st.ready`) alone: the body pins "
            "the flag to `false`, violating the frame on the sub-domain where "
            "it entered `true` — the EXACT COMPLEMENT of weak-flag-set's wrong "
            "sub-domain, which is why the two need separate witnesses at "
            "opposite flag values rather than sharing one. Q1 and Q2 are kept "
            "correct. Refuted at a registry entering with the flag `true`, an "
            "EMPTY name-lookup cache and a non-empty entity-list cache — a "
            "one-cache-empty corner no other witness occupies, which also "
            "shows the frame clause bites independently of how much was "
            "memoized."),
        "witness": _witness('[]', '[((false, false), ["u"])]', 'true'),
    },
    {
        "id": "weak-flag-from-cache",
        "kind": "uniqueness",
        "expect": "reject",
        # Third field-coupling case, and the subtlest: the flag is not pinned
        # to a literal but RECOMPUTED from a cache's pre-state, so it is
        # preserved on part of the domain and clobbered on the rest.
        "module": _do(_W_NAME + _W_ENT
                      + "  s := { s with ready := st.nameLookupCache.isEmpty }\n"),
        "refinement": (
            "recomputing the readiness flag from whether a cache was empty "
            "models a discard that infers the registry's settled state from "
            "its memoization state instead of leaving the flag alone. Its "
            "faithful counterpart does not resolve, and is strictly worse than "
            "pinning the flag because it is silently correct on part of the "
            "domain: whenever the queried cache happens to be empty the flag "
            "is raised, which is exactly the situation during the registry's "
            "own load sequence, so the reload short-circuits as "
            "already-complete and leaves no applications configured; and "
            "whenever that cache is populated the flag is lowered, so the next "
            "reconfiguration is rejected as not-ready. Either way the failing "
            "test does not reach its assertions. Does NOT resolve."),
        "rationale": (
            "REJECT from Q3 (`result.ready = st.ready`) alone: the flag is "
            "SOURCED from another field's pre-state, which the total domain "
            "admits at any value, so it is not provably equal to the incoming "
            "flag. Q1 and Q2 are kept correct. THIRD field-coupling case and "
            "the subtlest — unlike the two literal-pinning frame rivals this "
            "body PRESERVES the flag on half the domain (whenever the queried "
            "cache's emptiness happens to coincide with the incoming flag), so "
            "it is a strict NEAR-MISS of both and needs its own witness at the "
            "coincidence-breaking point: a registry entering with the flag "
            "`true` and a NON-EMPTY name-lookup cache, so the recomputed value "
            "is `false` and diverges. That combination is unique to this "
            "witness. If it VERIFIED, the spec would let the frame clause be "
            "discharged by any value derivable from the input rather than by "
            "the input's own field => SPEC-TOO-WEAK."),
        "witness": _witness('[("y", some "z")]', '[]', 'true'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING
#
# The sibling battery has 11 SPEC cases (3 soundness positives, 1
# admissibility, 7 uniqueness rivals) plus a two-case AXIOM lane, contracting a
# reset over a permission-bearing heap object with a three-clause precondition
# (two FULL permissions plus a total-correctness obligation) and a four-clause
# postcondition (two framing plus two load-bearing). This bundle models the
# same behaviour on a referentially-transparent carrier: ONE obligation over an
# immutable three-field structure, with no permissions to return and no
# precondition hypothesis. So both permission preconditions and both framing
# postconditions have no counterpart, and the total-correctness precondition is
# unnecessary rather than missing (see weak-diverge below).
#
#   sibling case (nagini)   -> here                            disposition
#   ---------------------------------------------------------------------------
#   pos-reorder             -> pos-reorder                     PORTED
#   pos-localvar            -> pos-literal                     PORTED (re-shaped)
#   pos-copy-other          -> pos-derive-after-clear           PORTED
#   admiss-roundtrip        -> admiss-primed-nondegenerate      RE-AIMED
#   weak-models-only        -> weak-entity-only                 PORTED (headline)
#   weak-swappable-only     -> weak-name-only                   PORTED
#   weak-neither            -> weak-neither                     PORTED
#   weak-decrement          -> weak-evict-one                   PORTED
#   weak-stale-swappable    -> weak-reprime-name                PORTED
#   weak-conditional-skip   -> weak-conditional-skip            PORTED
#   weak-diverge            -> (none)                    NO ADMISSIBLE WITNESS
#   weak-self-echo          -> (none)                           INEXPRESSIBLE
#   (no counterpart)        -> pos-readiness-branch             NEW (branch reshape)
#   (no counterpart)        -> weak-coupled-guard               NEW (field coupling)
#   (no counterpart)        -> weak-proxy-prevalue              NEW (field coupling)
#   (no counterpart)        -> weak-flag-set                    NEW (frame clause)
#   (no counterpart)        -> weak-flag-clear                  NEW (frame clause)
#   (no counterpart)        -> weak-flag-from-cache             NEW (frame coupling)
#   (no counterpart)        -> weak-guard-on-ready              NEW (ready coupling)
#   AXIOM_TESTS (2)         -> (none)                           DROPPED (G-AX's lane)
#
# PORTED (9 of 11). All three positives and all six value-level rivals carry
#   over: the sibling's occupancy-counter stores become field writes on an
#   immutable structure, and every argument survives, because the property being
#   attacked (a memoizing query's retained results are GONE afterwards) is the
#   same on both carriers. One mechanical difference is handled in the bodies
#   rather than reported as a blocker: the sibling's occupancy carrier is a
#   single Nat per cache, so its "decrement by one" and "clear to a non-zero
#   sentinel" rivals become "drop the head entry" and "re-prime with one entry"
#   here — the same partial-domain and near-miss arguments over a list carrier,
#   which is strictly richer (it also lets the eviction rival be refuted at a
#   two-entry cache directly). Each positive was confirmed to VERIFY with a real
#   build; each rival was confirmed NOT to verify; each witness was run against
#   the rival (exit 0) and against the frozen solution (exit 1, `decide`
#   proving the spec HOLDS there) and was SEEN to discriminate.
#
# RE-AIMED (admiss). The sibling's admissibility case constructs a fresh
#   registry, asserts the precondition admits it, applies the reset in-line and
#   asserts the result — a probe aimed at three `Requires` clauses. This
#   obligation has NO precondition hypothesis, so "a normal input is admitted"
#   is vacuous here: nothing could exclude it. The case is re-aimed at the
#   residual total-domain risk, that the post-image is degenerate at the corner
#   the failing test exercises (both caches primed NON-EMPTY, so each discard is
#   a real transition rather than a no-op). The in-region `have` is LIVE,
#   confirmed by replacing one conjunct with a false claim about the same point
#   and observing the build fail with `decide` proving that conjunct false.
#
# NO ADMISSIBLE WITNESS (weak-diverge) — the class is REAL and the spec REJECTS
#   it; what is missing is a witness the gate can score, so it is recorded as a
#   known unshippable class rather than as vacuous. The previous claim here ("a
#   diverging body cannot be WRITTEN on a total carrier") was measured FALSE and
#   is corrected: `while true do s := s` elaborates inside the frozen `Id.run do`
#   skeleton (Lean compiles it to `forIn Lean.Loop.mk`, not structural
#   recursion), and `partial def implementation_clearCaches st :=
#   implementation_clearCaches st` is definable too. Both were built and both are
#   REJECTED by the frozen obligation, the `while` body with `Application type
#   mismatch: rfl ... expected (implementation_clearCaches st).ready = st.ready`
#   — the loop term never reduces to a record, so not even the frame clause
#   closes. So there is NO spec hole. The blocker is the witness's RIVAL half:
#   the battery's `decide` shape fails against the diverging rival with
#   ``Tactic `decide` failed for proposition ... forIn Lean.Loop.mk`` (the
#   documented stuck-reduction class => `witness-unproven`/`witness-undecided`,
#   inconclusive, which FAILS the gate), and the hypothesis-conditioned
#   alternative elaborates against BOTH the rival and gold (exit 0 / exit 0 —
#   on gold the hypothesis is false and `simp [h]` closes from a contradiction)
#   => `witness-vacuous`. A `witness_reference` substitutes the GOLD-side
#   subject and so cannot repair a blocked RIVAL side. This bundle sets no
#   `loom.semantics.termination` option at all (plain total `def`), so the
#   `partial`-semantics known-hole reading in `the corpus-wide termination-semantics finding`
#   (all 401 `partial` bundles admit divergence, all 99 `total` bundles reject
#   it) does not transfer here either.
#
# INEXPRESSIBLE (weak-self-echo) — built, run, and dropped on the evidence, not
#   for proof difficulty. The sibling discharges the contract by calling the
#   function under spec, and is rejected there by an obligation-leak check.
#   Here the analogous body (`s := implementation_clearCaches s`) is rejected by
#   Lean's own totality checker before the postcondition is ever consulted:
#   "fail to show termination for implementation_clearCaches ... failed to infer
#   structural recursion: Not considering parameter st ...: it is unchanged in
#   the recursive calls ... no parameters suitable for structural recursion".
#   That would make the case pass for entirely the wrong reason (definability,
#   not the postcondition), and the SAME error breaks the WITNESS build — whose
#   success is the half that must hold; the witness build additionally reports
#   "Tactic `unfold` failed to unfold `implementation_clearCaches`", since a
#   definition that failed to elaborate has no equation to unfold. So no
#   discriminating witness exists and the rival is not refutable on this
#   carrier.
#
# NEW (7). None has a sibling counterpart; all were added for clause and field
#   coverage, which case-count parity would not have produced.
#   * pos-readiness-branch is the only positive that changes CONTROL FLOW, so it
#     is the only one that exercises the spec against a body the frozen tactic
#     script cannot close — it reproves honestly, with the theorem statement
#     byte-identical.
#   * weak-coupled-guard / weak-proxy-prevalue: each clause names one field's
#     post-state, so a rival can make one clause's outcome depend on ANOTHER
#     field, either by GUARDING the discard on it or by SOURCING the post-value
#     from it. Both are correct on the entire sub-domain where the other cache
#     is non-empty, so a battery that held that field non-empty across its
#     witnesses would verify them and report SOUND. Their witnesses sit at the
#     complementary corners that break that pinning.
#   * weak-flag-set / weak-flag-clear / weak-flag-from-cache attack Q3, the
#     FRAME clause, which the nagini carrier does not model at all (it has no
#     readiness field). All three empty BOTH caches correctly, so they are
#     invisible to any reading of the spec as "two emptiness clauses" — exactly
#     the failure mode that has sunk other ports. The first two are wrong on
#     COMPLEMENTARY flag sub-domains (so they cannot share a witness); the third
#     recomputes the flag from a cache's pre-state and is therefore a strict
#     near-miss of both, correct wherever that cache's emptiness happens to
#     coincide with the incoming flag, so it is refuted at the
#     coincidence-breaking point.
#
# DROPPED (AXIOM_TESTS). The axiom lane belongs to G-AX, which this gate
#   ignores, and this bundle declares no `axiom` in any case: the discard is
#   modeled deeply as two field writes, and the standard-library memoization
#   wrapper whose emptied-cache effect they refine is an A-reference validated
#   out-of-band.
#
# CLAUSE / FIELD COVERAGE (the part the gate does not check).
#   The single obligation `correct_clearCaches` is DEFENDED by 4 soundness
#   positives + the admissibility case and ATTACKED by 12 rivals. All THREE
#   independent top-level clauses are attacked:
#     Q1 `result.nameLookupCache = []` — weak-entity-only, weak-neither,
#        weak-evict-one, weak-reprime-name, weak-conditional-skip,
#        weak-coupled-guard, weak-guard-on-ready.
#     Q2 `result.entityListCache = []` — weak-name-only, weak-neither,
#        weak-evict-one, weak-proxy-prevalue.
#     Q3 `result.ready = st.ready`     — weak-flag-set, weak-flag-clear,
#        weak-flag-from-cache.
#   The twelve reject witnesses probe TWELVE DISTINCT registry literals
#   (pts=12). The obligation binds ONE argument, but it is a three-field
#   structure and each clause names a different field, so the input axes are
#   the fields — and every one is varied:
#     nameLookupCache : empty (weak-reprime-name, weak-flag-clear), one entry
#       resolving to a name (weak-entity-only, weak-neither,
#       weak-coupled-guard, weak-flag-from-cache), one entry resolving to "no
#       such name" (weak-name-only, weak-proxy-prevalue, weak-flag-set), one
#       entry resolving to a name with the flag `false` (weak-guard-on-ready), two
#       entries mixing both (weak-evict-one, weak-conditional-skip).
#     entityListCache : empty (weak-conditional-skip, weak-coupled-guard,
#       weak-proxy-prevalue, weak-reprime-name, weak-flag-from-cache), one
#       entry (six witnesses), two entries (weak-evict-one); all FOUR
#       inclusion-flag key pairs appear — (true,false), (true,true),
#       (false,true), (false,false) — with both empty and non-empty
#       selected-entity value lists.
#     ready : true (6 witnesses) and false (6 witnesses); the two literal frame
#       rivals sit at OPPOSITE values, which is forced since their wrong
#       sub-domains are complementary.
#   All four cache-emptiness combinations are covered (both empty, first empty
#   only, second empty only, both non-empty), and the cache-size boundary
#   (fewer than two vs two or more entries) is probed from both sides. So no
#   field is pinned, and no rival's refutation rests on a value another rival's
#   refutation also needs.
#   Every witness is stated at LITERAL inputs and binds NOTHING (the carrier is
#   fully transparent — `decide` computes both the spec and the impl), so no
#   witness can be inconsistent-by-hypothesis and the gate's consistency probe
#   is not even triggered. Each was run against the rival (exit 0) and the
#   frozen solution (exit 1) and was SEEN to discriminate.
AXIOM_TESTS = []
