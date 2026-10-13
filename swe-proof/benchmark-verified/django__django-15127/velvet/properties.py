"""properties.py — G-PBT falsification battery for django__django-15127 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — which the consumer spec view elides, so
``markers.same_spec`` holds and the single ``prove_correct`` obligation survives
with a byte-identical statement) and swaps in a candidate implementation; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates — the witness must ELABORATE against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method: a change-notification handler that
keeps a cached key→value lookup table in sync with configuration.

  refreshCachedTable (mut cached : List (Int × String))
      (changedKey : String) (watchedKey : String)
      (base overrides : List (Int × String))
      return (u : Unit)
    ensures changedKey = watchedKey → cached = recomputeTable base overrides
    ensures changedKey ≠ watchedKey → cached = cachedOld

The two ``ensures`` are independent top-level clauses guarded on the SAME
predicate ``changedKey = watchedKey``:

  * E1 (the RECOMPUTE clause) — when the changed key is the watched one, the
    cached table becomes ``recomputeTable base overrides``, the base entries
    overlaid by the override entries with OVERRIDES WINNING on shared keys.
    ``recomputeTable`` / ``lookupEntry`` are fully-unfolded ``def``s spelled out
    as a closed-form overlay of the inputs (``overrides ++ base.filter (key not
    overridden)``) — there is no opaque answer key to echo; evaluating it IS the
    correct computation. It is a deep A-reference validated ``== the real
    table-recompute callee`` by axiom_check.py (G-AX's job — mapping.md §3.1),
    NOT a consumed axiom.
  * E2 (the FRAME clause) — when any OTHER key changed, the cached table is left
    EXACTLY as it was on entry (``cached = cachedOld``). This is the Lean/Velvet
    analogue of the read-only frame discipline: the ``mut`` binder is pinned to
    its pre-state on the non-watched branch, so a handler that recomputes (or
    otherwise perturbs) the table on an unrelated key change is refuted.

BINDER STRUCTURE (read before judging binder coverage). Input binders of the
spec predicate: ``changedKey``, ``watchedKey``, ``base``, ``overrides``, and the
mut binder's entry value ``cachedOld``. The reject witnesses vary each:

  * ``changedKey`` vs ``watchedKey`` — six rivals probe the branch where they
    are EQUAL (E1 active), three probe the branch where they DIFFER
    ("OTHER"/"MESSAGE_TAGS", E2 active). So the guard binder is varied across both
    arms. Four of the E1 witnesses pin both key binders OFF the "MESSAGE_TAGS"
    spelling (both "ALT_KEY"), so the guard is exercised as a RELATION between the
    two binders and not as a test against a fixed name.
  * ``base`` / ``overrides`` — varied in length, key overlap, and VALUE: a shared
    key ([(1,"d")] vs [(1,"o")], to separate the merge DIRECTION), disjoint keys
    ([(10,"a")] vs [(20,"b")], to catch dropping the overrides entirely), an
    empty overrides ([(1,"a")] vs []), and an override entry whose value is the
    EMPTY STRING ([(1,"a")] vs [(2,"")], to catch a recompute that treats an
    empty value as "no override").
  * ``cachedOld`` — the E2 rivals probe a NON-EMPTY entry table ([(9,"z")]) so
    that recomputing over it is observably different from leaving it, i.e. the
    frame clause is a real transition and not a vacuous no-op, and a LENGTH-2
    entry table ([(9,"z"),(8,"y")]) where a mere REORDER of the frame is
    observable (at length ≤ 1 a reordering rival is indistinguishable from gold).

ADVERSARIAL READ of the nagini classes on this carrier (see footer for the full
case-by-case accounting):

  * FRAME / PERMISSION-MUTATION — the nagini sibling carries TWO MANDATORY
    permission-mutation rivals (write the merged values back into the read-only
    ``defaults`` / ``override`` records held at ``Acc(...,1/2)`` and return them).
    Lean and Velvet are referentially transparent: there is no heap, no aliasing,
    and no fractional permission to exceed, so a rival cannot "write a read-only
    input in place" — that exact probe is inexpressible. BUT the SOUNDNESS
    CONCERN it defends — that an input the operation must not disturb is actually
    left undisturbed — survives as the E2 frame clause ``cached = cachedOld``,
    and is attacked here by the E2 rivals (which perturb the cached table on the
    non-watched branch). So the permission MECHANISM is vacuous; the frame
    PROPERTY it stood in for is defended and attacked.
  * DIVERGENCE / NON-TERMINATION — nothing to ship, and the reason is a
    measurement, not an argument. The nagini sibling carries no ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` case, and this bundle runs under
    ``set_option loom.semantics.termination "total"``.
    Under ``total`` a postcondition is claimed of ALL runs, not only terminating
    ones, and the verifier demands a decreasing measure on every loop. The option
    cannot drift from the file's ``open TotalCorrectness DemonicChoice`` either,
    because the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured on THIS bundle, proof
    reduced to a bare ``loom_solve``: an unmeasured spun loop is refused at
    elaboration (``Decreasing annotations are required in total correctness
    semantics``), and the sharper shape that CARRIES a measure which does not
    decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``,
    body ``q := q``) is REJECTED on the measure's own goal -
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. The second shape is the one
    that matters, since it cannot be dismissed as merely missing an annotation. So a
    divergence rival is refuted by the semantics rather than by these ``ensures``,
    and there is no spec hole here to record. (An earlier version of this bullet
    reached the same disposition by citing an internal findings doc and a corpus
    census of a ``partial`` majority against a ``total`` minority. That census is
    withdrawn: all 500 velvet bundles set ``"total"``, so there is no split to be on
    a side of, and the conclusion rests on the builds above.)
  * UNGROUNDED-ORACLE ECHO — N/A. ``recomputeTable`` / ``lookupEntry`` are
    concrete ``def``s spelled out as a closed-form overlay of the inputs (no
    opaque answer key to echo); the nagini sibling notes the same — its
    ``merge_slot`` helper is GROUNDED in the input slots. The honest positive
    controls cover the cheapest correct impl (evaluate the recompute directly on
    the watched branch, return the entry table otherwise).
  * STALE-NO-DERIVATION / WRONG-MERGE / WRONG-BRANCH — the heart of the port,
    exactly as in nagini. The cheapest WRONG impl never re-derives (the prepatch
    bug), inverts the merge direction, drops the overrides, or inverts the guard;
    each is refuted by E1 or E2 at a concrete input.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
not a bare predicate, so a witness reaches the postcondition through Velvet's own
tester machinery: ``refreshCachedTableTester cached changedKey watchedKey base
overrides = false`` says the extracted program's observable post-state violates
the postcondition at that concrete input (the tester args follow the method's
parameter order, the ``mut`` binder's ENTRY value first). Checked in a file whose
``prove_correct`` block is stripped by the gate, so no tactic script can mask the
verdict. Every witness closes by ``decide`` over concrete ``Int``/``String``
literals — the carriers are fully transparent, so no witness binds a hypothesis
and there is no joint-satisfiability obligation. Each witness was verified
out-of-band with two real ``lean_verify.sh`` builds: green (``decide`` closes)
against its rival, red (``decide`` proves the tester is ``true``, i.e. gold
satisfies the postcondition there) against the frozen solution — and, by the
audit, with a THIRD build per case flipping the claim to ``= true`` to confirm
each exit code tracks what is asserted rather than the file's shape (see the
FORGERY CHECK paragraph in the footer for the observed inversions).

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; ``recomputeTable``
is a deep A-reference validated ``== the real table-recompute callee`` by
axiom_check.py (G-AX's job — mapping.md §3.1), not a consumed contract, and this
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15127"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The WHOLE executable body of refreshCachedTable (between -- impl-start and
# -- impl-end). It lies wholly inside the impl region and is unique in
# Solution.lean; both facts are asserted at load by _swap. Editing only this
# keeps markers.same_spec True and the single prove_correct statement
# byte-identical (the spec view elides the impl region and the proof body).
# ---------------------------------------------------------------------------
_IMPL = (
    "    cached := if changedKey = watchedKey then recomputeTable base overrides "
    "else cached\n"
    "    return"
)

assert _BASE.count(_IMPL) == 1, "impl region drifted"

# The frozen proof script. A variant may retune the TACTIC body (the statement
# stays byte-identical, which is what `variant_scope` checks); the admissibility
# case below does, to clear its extra in-region `assert` goal.
_PROOF = "prove_correct refreshCachedTable by\n  loom_solve\n"

assert _BASE.count(_PROOF) == 1, "proof region drifted"

# Discharges the frozen obligation AND the admissibility case's extra `assert`
# goal: `decide` for the closed conjuncts, and `intro h; simp_all` for the two
# that are contingent on what the impl actually assigned.
_PROOF_ADMISS = (
    "prove_correct refreshCachedTable by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | decide\n"
    "    | (repeat' apply And.intro) <;> first | decide | (intro h; simp_all) "
    "| simp_all\n"
)


# ---- witness preamble. `refreshCachedTableTester <cached> <changedKey>
# ---- <watchedKey> <base> <overrides> = false` reaches the method postcondition
# ---- through Velvet's tester machinery (args follow the method parameter order;
# ---- the mut binder's ENTRY value first); checked in a file whose prove_correct
# ---- block is stripped by the gate. Every witness `decide`s over concrete
# ---- Int/String literals. No `sorry`/`admit`/`native_decide`/`axiom`.
def _w(cached, changed, watched, base, overrides):
    args = f'{cached} {changed} {watched} {base} {overrides}'
    return (
        "extract_program_for refreshCachedTable\n"
        "prove_precondition_decidable_for refreshCachedTable\n"
        "prove_postcondition_decidable_for refreshCachedTable\n"
        "derive_tester_for refreshCachedTable\n\n"
        f"example : refreshCachedTableTester {args} = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG. Each keeps the
    # byte-identical two-clause obligation and only reshapes the executable
    # surface; the frozen `loom_solve` script still discharges both clauses.
    # All three verified out-of-band with real builds.
    #
    # AUDIT NOTE on their STRENGTH, stated rather than left implicit: the first
    # two are definitionally the frozen term (a `let`-staging and a guard
    # negation with the arms swapped), so on their own they cannot separate "the
    # spec admits every faithful shape" from "the spec admits every spelling of
    # gold's term". pos-control-statement-branch was added by the audit as the
    # one positive that is NOT defeq — it restructures the do-block into a
    # branching statement, so the obligation is discharged per arm. Two further
    # reshapes were measured and are NOT carried, for a reason worth recording:
    # inlining `recomputeTable`'s own body at the assignment site verifies only
    # after retuning the tactic (`simp_all [recomputeTable]`); under the frozen
    # script it leaves the E1 goal open. That is a TACTIC gap, not spec strength
    # — the frozen `loom_solve` does not unfold the pure def — and it is noted
    # here so a later reader does not mistake it for a soundness hole.
    # =====================================================================
    {
        "id": "pos-control-branch-flip",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: write the SAME conditional with the guard NEGATED and the two
        # arms swapped (`if changedKey ≠ watchedKey then cached else recompute`).
        # Observationally identical on both arms, so E1/E2 both still discharge
        # under the frozen script.
        "module": _swap(
            _BASE, _IMPL,
            "    cached := if changedKey ≠ watchedKey then cached "
            "else recomputeTable base overrides\n"
            "    return"),
        "rationale": "a correct reshape that negates the guard and swaps the two "
                     "arms: on the watched key it still assigns "
                     "`recomputeTable base overrides` (E1), and on any other key it "
                     "still leaves `cached` untouched (E2). A faithful reshape MUST "
                     "verify; if it did not the clauses would be over-fit to the "
                     "guard's syntactic FORM => SPEC-TOO-STRONG. (Sibling: "
                     "pos-control-reorder.)",
    },
    {
        "id": "pos-control-let-staged",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the recomputed table to a local FIRST, then select it in
        # the conditional. Same value, different statement shape.
        "module": _swap(
            _BASE, _IMPL,
            "    let t := recomputeTable base overrides\n"
            "    cached := if changedKey = watchedKey then t else cached\n"
            "    return"),
        "rationale": "a correct reshape that stages the recomputed table into a "
                     "named local before selecting it: the watched branch assigns "
                     "the identical `recomputeTable base overrides` (E1) and the "
                     "other branch leaves `cached` untouched (E2), so both clauses "
                     "discharge under the frozen script. If it failed the clause "
                     "would be over-fit to the impl FORM => SPEC-TOO-STRONG. "
                     "(Sibling: pos-control-inline.)",
    },
    {
        "id": "pos-control-statement-branch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: a real CONTROL-FLOW branch (an `if` STATEMENT with two
        # assignment arms) in place of one assignment of an `if` EXPRESSION.
        # Added by the audit: the two positives above are both zeta/iota
        # reductions of the frozen term (staging a `let`, and negating the guard
        # with the arms swapped), so each is definitionally the frozen impl and
        # neither can tell "the spec admits every faithful SHAPE" from "the spec
        # admits every spelling of gold's term". This one changes the do-block's
        # weakest-precondition structure — the obligation is discharged per ARM
        # from the branch hypothesis rather than by reducing one conditional —
        # and it still closes under the frozen `loom_solve` script.
        "module": _swap(
            _BASE, _IMPL,
            "    if changedKey = watchedKey then\n"
            "      cached := recomputeTable base overrides\n"
            "    else\n"
            "      cached := cached\n"
            "    return"),
        "rationale": "a correct reshape into a control-flow branch: the watched arm "
                     "assigns `recomputeTable base overrides` (E1) and the other arm "
                     "re-assigns `cached` to itself, leaving it at its entry value "
                     "(E2). This is the only positive here that is NOT definitionally "
                     "the frozen term — the two above are a `let`-staging and a "
                     "guard-negation of it, both defeq — so it is the one that probes "
                     "whether the spec admits a faithful CONTROL shape rather than a "
                     "re-spelling of gold's conditional. Must verify, else the clauses "
                     "are over-fit to the impl's statement form => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's admissibility probe (a self-call on an
    # F2P-shaped input) established that the half-permission precondition ADMITS
    # a normal input. This method declares no `require`, so nothing could exclude
    # a normal input and that exact probe is degenerate. It is NOT thereby
    # vacuous: on a total carrier the residual PRECOND-TOO-STRONG analogue is the
    # obligation being UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped
    # input, which an earlier revision of this manifest recorded as having "no
    # residual admissibility risk to re-aim at" — the audit measured that as
    # wrong and landed this case instead.
    #
    # It discharges an in-region `assert`, placed AFTER the body has computed its
    # effect, whose first two conjuncts name the values the impl ACTUALLY
    # assigned against the two `ensures` right-hand sides (so the discharge is
    # contingent on the impl, not on the spec text) and whose remaining conjuncts
    # evaluate the post-image at ONE concrete F2P-shaped configuration: a base of
    # three entries overlaid by an override that re-tags one shared key, sets a
    # second shared key to the EMPTY value, and adds a key the base lacks. Both
    # halves were measured live, not assumed:
    #   * falsifying one concrete conjunct (an override-only key's value) fails
    #     the build, so the assert is not decoration; and
    #   * keeping the assert over a DEGENERATE impl (`cached := []`) fails it on
    #     the two impl-contingent conjuncts, so those really are contingent.
    # The impl is kept verbatim so the method's own two clauses still discharge;
    # only the tactic body is retuned (allowed — the obligation statement stays
    # byte-identical and the body is elided from the spec view).
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-config",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "    let entry := cached\n"
                "    cached := if changedKey = watchedKey then "
                "recomputeTable base overrides else cached\n"
                "    assert (with_name_prefix `admiss (\n"
                "      (changedKey = watchedKey → "
                "cached = recomputeTable base overrides) ∧\n"
                "      (changedKey ≠ watchedKey → cached = entry) ∧\n"
                "      (recomputeTable [(10, \"a\"), (20, \"b\"), (30, \"c\")] "
                "[(20, \"z\"), (30, \"\"), (99, \"n\")]\n"
                "         = [(20, \"z\"), (30, \"\"), (99, \"n\"), (10, \"a\")]) ∧\n"
                "      (lookupEntry (recomputeTable "
                "[(10, \"a\"), (20, \"b\"), (30, \"c\")] "
                "[(20, \"z\"), (30, \"\"), (99, \"n\")]) 99 = some \"n\") ∧\n"
                "      (lookupEntry (recomputeTable "
                "[(10, \"a\"), (20, \"b\"), (30, \"c\")] "
                "[(20, \"z\"), (30, \"\"), (99, \"n\")]) 30 = some \"\") ∧\n"
                "      (lookupEntry (recomputeTable "
                "[(10, \"a\"), (20, \"b\"), (30, \"c\")] "
                "[(20, \"z\"), (30, \"\"), (99, \"n\")]) 20 = some \"z\") ∧\n"
                "      (recomputeTable [(10, \"a\"), (20, \"b\"), (30, \"c\")] "
                "[(20, \"z\"), (30, \"\"), (99, \"n\")]\n"
                "         ≠ [(10, \"a\"), (20, \"b\"), (30, \"c\")])))\n"
                "    return"),
            _PROOF, _PROOF_ADMISS),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at a concrete "
                     "F2P-shaped configuration, asserted in-region over the value the "
                     "body actually assigned. The two leading conjuncts restate the "
                     "two `ensures` right-hand sides against the computed `cached` and "
                     "the staged entry value, so the discharge is contingent on the "
                     "impl (measured: over a degenerate `cached := []` body they leave "
                     "`recomputeTable base overrides = []` unsolved). The remaining "
                     "conjuncts evaluate the post-image at ONE configuration that "
                     "carries all three interesting shapes at once — a shared key "
                     "re-tagged (20 -> \"z\"), a shared key set to the EMPTY value "
                     "(30 -> \"\"), and a key only the override supplies (99) — and "
                     "pin it DISTINCT from the base alone, i.e. the recompute really "
                     "is a transition and the override entries really do reach the "
                     "table. Measured live: falsifying one concrete conjunct fails the "
                     "build, so the assert is not decoration. If this could not "
                     "discharge the obligation would be unsatisfiable at exactly the "
                     "input the fix is about => the total-carrier analogue of "
                     "PRECOND-TOO-STRONG. (Sibling: admiss-f2p-shaped-input, re-aimed "
                     "— there is no `require` here to admit.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary the input
    # binders (see header BINDER STRUCTURE and footer coverage).
    # =====================================================================

    # ---- E1 (the recompute clause), watched-key branch --------------------
    {
        "id": "uniq-stale-no-derivation",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH BUG: never re-derive — leave the cached table as it was
        # regardless of which key changed. E2 holds trivially; E1 fails whenever
        # the entry table differs from the recompute (the F2P shape).
        "module": _swap(_BASE, _IMPL,
                        "    cached := cached\n    return"),
        "refinement": "this is the pre-patch behaviour: no change-notification "
                      "handler is registered, so the cached level→tag table is "
                      "never re-derived and the in-force (stale) mapping is kept "
                      "regardless of which setting changed. The sole failing test "
                      "overrides the tag configuration and asserts the cached table "
                      "reflects it; with no re-derivation the cached table keeps its "
                      "old contents and the assertion fails. Its faithful real patch "
                      "(the un-patched handler) is exactly what does NOT resolve.",
        "rationale": "REJECT from E1 (`changedKey = watchedKey → cached = "
                     "recomputeTable base overrides`): on the watched key the rival "
                     "leaves the entry table in place, which differs from the "
                     "recompute for any non-trivial config. Refuted at a watched-key "
                     "input whose entry cached=[] but recompute=[(1,\"a\")].",
        "witness": _w('[]', '"MESSAGE_TAGS"', '"MESSAGE_TAGS"',
                      '[(1, "a")]', '[]'),
    },
    {
        "id": "uniq-default-wins",
        "kind": "uniqueness",
        "expect": "reject",
        # The merge DIRECTION inverted: base wins on shared keys (base overlaid by
        # overrides where base lacks the key) — the wrong overlay order. Correct
        # only where base and overrides never share a key; wrong on any re-tagged
        # shared key (the F2P re-tags built-in levels).
        "module": _swap(
            _BASE, _IMPL,
            "    cached := if changedKey = watchedKey then "
            "(base ++ overrides.filter (fun kv => (lookupEntry base kv.1).isNone)) "
            "else cached\n"
            "    return"),
        "refinement": "overlaying the OTHER way round (base entries winning on "
                      "shared keys) corresponds to the wrong merge order — the "
                      "base defaults survive where the override re-tags a shared "
                      "level. The failing test re-tags a built-in level and asserts "
                      "the override token is in force; with the base winning the "
                      "old default token survives and the assertion fails. Does NOT "
                      "resolve.",
        "rationale": "REJECT from E1: the post-image is `recomputeTable base "
                     "overrides` = overrides overlaid on base (OVERRIDES WIN), but "
                     "the rival lists base first so base wins on a shared key. "
                     "Refuted at base=[(1,\"d\")], overrides=[(1,\"o\")]: gold binds "
                     "key 1 to \"o\", the rival to \"d\". Varies `base`/`overrides` "
                     "at a SHARED key (the merge-direction discriminator), and "
                     "varies `watchedKey`/`changedKey` OFF \"MESSAGE_TAGS\" (both "
                     "\"ALT_KEY\") to show E1 fires on the watched key whatever its "
                     "name — the guard compares the two key binders, not a literal.",
        "witness": _w('[]', '"ALT_KEY"', '"ALT_KEY"',
                      '[(1, "d")]', '[(1, "o")]'),
    },
    {
        "id": "uniq-drop-overrides",
        "kind": "uniqueness",
        "expect": "reject",
        # Recompute to the BASE entries alone, dropping the overrides entirely.
        # Correct only when overrides is empty; wrong on any non-empty overrides
        # (e.g. a custom level only the override supplies).
        "module": _swap(
            _BASE, _IMPL,
            "    cached := if changedKey = watchedKey then base else cached\n"
            "    return"),
        "refinement": "recomputing to the base defaults alone drops the override "
                      "entries — e.g. a custom level only the override configures "
                      "is absent from the cached table. The failing test configures "
                      "such an override and asserts it is reflected; with the "
                      "overrides dropped the cached table lacks that entry and the "
                      "assertion fails. Does NOT resolve.",
        "rationale": "REJECT from E1: the post-image includes the override entries "
                     "(`overrides ++ base.filter ...`), but the rival returns `base` "
                     "alone. Refuted at base=[(10,\"a\")], overrides=[(20,\"b\")] "
                     "(DISJOINT keys): gold's table contains key 20, the rival's "
                     "does not. Varies `base`/`overrides` at disjoint keys and a "
                     "non-empty overrides.",
        "witness": _w('[]', '"MESSAGE_TAGS"', '"MESSAGE_TAGS"',
                      '[(10, "a")]', '[(20, "b")]'),
    },

    # ---- E2 (the frame clause), non-watched-key branch --------------------
    {
        "id": "uniq-wrong-branch",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard inverted: recompute on any OTHER key and leave the table stale on
        # the watched key. Fails E1 on the watched key AND E2 on other keys.
        # Refuted here on the E2 arm (a non-watched key change that should be a
        # no-op but recomputes).
        "module": _swap(
            _BASE, _IMPL,
            "    cached := if changedKey ≠ watchedKey then "
            "recomputeTable base overrides else cached\n"
            "    return"),
        "refinement": "inverting the guard (re-derive on an unrelated key change, "
                      "leave the table stale when the WATCHED key changes) "
                      "corresponds to a handler guarded on the wrong condition. On "
                      "the failing test's watched-key change it would NOT re-derive "
                      "(the override goes unreflected), and it needlessly re-derives "
                      "on unrelated changes. Does NOT resolve.",
        "rationale": "REJECT from E2 (`changedKey ≠ watchedKey → cached = "
                     "cachedOld`): on a non-watched key the rival OVERWRITES the "
                     "cached table with the recompute instead of leaving it. "
                     "Refuted at changedKey=\"OTHER\" ≠ watchedKey=\"MESSAGE_TAGS\", "
                     "entry cached=[] but recompute=[(1,\"a\")]. Varies the guard "
                     "binder to the differing arm.",
        "witness": _w('[]', '"OTHER"', '"MESSAGE_TAGS"',
                      '[(1, "a")]', '[]'),
    },
    # ---- guard IDENTITY: the guard must compare the two key binders --------
    {
        "id": "uniq-guard-literal",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard against a FIXED key literal instead of against `watchedKey`.
        # Agrees with gold on every input whose watched key happens to be that
        # literal, and is wrong on every other watched key — the binder-identity
        # probe that a rival hard-coding the watched configuration key is caught.
        "module": _swap(
            _BASE, _IMPL,
            "    cached := if changedKey = \"K0\" then recomputeTable base "
            "overrides else cached\n"
            "    return"),
        "refinement": "guarding on a fixed key name rather than on the key the "
                      "handler actually watches corresponds to a handler wired to "
                      "the wrong configuration key. On the failing test's change to "
                      "the watched key it does NOT re-derive (the override goes "
                      "unreflected), and it re-derives on a change to the unrelated "
                      "key it does watch. Does NOT resolve.",
        "rationale": "REJECT from E1 AND E2: the clauses are stated over the "
                     "RELATION `changedKey = watchedKey`, so a guard on a constant "
                     "satisfies neither arm in general. Refuted at "
                     "changedKey=watchedKey=\"ALT_KEY\" (E1 demands the recompute "
                     "[(5,\"x\")]; the rival's guard is false there so it leaves "
                     "cached=[]). This is the binder-IDENTITY probe: the wrong impl "
                     "is correct at the one watched-key spelling and wrong at every "
                     "other. Coverage addition, not a closed hole — the audit "
                     "measured that uniq-default-wins' \"ALT_KEY\" witness already "
                     "refutes a constant-guard rival, so the CLASS was detectable; "
                     "what was missing was a case whose own rival IS that impl, so "
                     "the battery attests to it directly rather than incidentally.",
        "witness": _w('[]', '"ALT_KEY"', '"ALT_KEY"', '[(5, "x")]', '[]'),
    },
    {
        "id": "uniq-drop-empty-valued-override",
        "kind": "uniqueness",
        "expect": "reject",
        # Overlay the overrides but SKIP every override entry whose value is the
        # empty string, so such a key falls through to its base entry (or is
        # absent). Correct on every config whose overrides carry only non-empty
        # values; wrong exactly where an override deliberately sets an entry to
        # the empty value — the near-miss the sibling's empty-value case covered.
        "module": _swap(
            _BASE, _IMPL,
            "    cached := if changedKey = watchedKey then "
            "(overrides.filter (fun kv => kv.2 ≠ \"\") ++ "
            "base.filter (fun kv => (lookupEntry overrides kv.1).isNone)) "
            "else cached\n"
            "    return"),
        "refinement": "treating an override entry whose value is the EMPTY string "
                      "as \"no override\" corresponds to a re-derivation that "
                      "filters falsy values out of the override mapping. The "
                      "failing test's configuration deliberately sets several "
                      "entries to the empty value and asserts the recomputed table "
                      "reflects them exactly; with those entries skipped the "
                      "recomputed table either keeps the old default value for that "
                      "key or omits it, and the assertion fails. Does NOT resolve.",
        "rationale": "REJECT from E1: the post-image overlays EVERY override entry, "
                     "including one whose value is \"\", but the rival drops those. "
                     "Refuted at base=[(1,\"a\")], overrides=[(2,\"\")]: gold's "
                     "table binds key 2 to \"\", the rival's table has no key 2 at "
                     "all. Varies `overrides` along the VALUE axis (an empty-string "
                     "tag) that no other rival here touches — the sibling's "
                     "empty-value near-miss, which is NOT subsumed by "
                     "uniq-drop-overrides (that rival's witnesses all carry "
                     "non-empty values, so each of them holds of this rival too).",
        "witness": _w('[]', '"ALT_KEY"', '"ALT_KEY"',
                      '[(1, "a")]', '[(2, "")]'),
    },
    {
        "id": "uniq-recompute-always",
        "kind": "uniqueness",
        "expect": "reject",
        # Recompute UNCONDITIONALLY, ignoring the guard entirely. E1 holds; E2
        # fails on every non-watched key whose recompute differs from the entry
        # table — the frame is violated. Isolates E2 (the read-only-frame analogue
        # of the nagini permission-mutation rivals).
        "module": _swap(
            _BASE, _IMPL,
            "    cached := recomputeTable base overrides\n"
            "    return"),
        "refinement": "recomputing on EVERY setting change (never checking which "
                      "key changed) corresponds to a handler that reacts to "
                      "unrelated settings too — it clobbers the cached table on any "
                      "change, discarding whatever it held. A handler that ignores "
                      "the watched-key guard disturbs state the fix must leave "
                      "exactly as it was on unrelated changes; a faithful "
                      "always-recompute patch does NOT resolve (it re-derives from "
                      "possibly-unrelated new settings, and any test asserting the "
                      "table is untouched on an unrelated change fails).",
        "rationale": "REJECT from E2 (`changedKey ≠ watchedKey → cached = "
                     "cachedOld`): the rival overwrites the cached table "
                     "unconditionally, so on a non-watched key it is the recompute, "
                     "not the entry value. Refuted at a NON-EMPTY entry "
                     "cachedOld=[(9,\"z\")] with changedKey=\"OTHER\" ≠ "
                     "watchedKey=\"MESSAGE_TAGS\": E2 requires cached=[(9,\"z\")], "
                     "the rival yields [(1,\"a\")]. This is the E2-frame analogue "
                     "of the sibling's permission-mutation rivals; it varies the "
                     "mut binder's entry value `cachedOld` to a non-empty table so "
                     "the frame violation is observable.",
        "witness": _w('[(9, "z")]', '"OTHER"', '"MESSAGE_TAGS"',
                      '[(1, "a")]', '[]'),
    },
    # ---- E2 frame: PERTURB rather than clobber (audit addition) -------------
    {
        "id": "uniq-frame-perturbed",
        "kind": "uniqueness",
        "expect": "reject",
        # Recompute correctly on the watched key, but on any OTHER key REORDER the
        # cached table instead of leaving it. As a key->value MAPPING the entry
        # table is unchanged, so this rival is correct under the order-insensitive
        # reading of the carrier and wrong only under the literal list equality E2
        # states. Added by the audit as the sharpest probe of the frame clause: the
        # two E2 rivals above both replace the table with a different MAPPING, so
        # neither distinguishes "the frame is held" from "the frame is held as a
        # mapping". Its rejection is the machine-checked converse of the open
        # finding on the frozen spec recorded in the footer — it is carried as a
        # reject because the frozen `ensures` is what this battery is judged
        # against, and under that ensures the rival is genuinely refuted.
        "module": _swap(
            _BASE, _IMPL,
            "    cached := if changedKey = watchedKey then "
            "recomputeTable base overrides else cached.reverse\n"
            "    return"),
        "refinement": "reordering the cached table on an unrelated configuration "
                      "change corresponds to a handler that rebuilds the cached "
                      "mapping's storage on every change instead of leaving it alone. "
                      "Under the frozen frame clause — which pins the post-state to "
                      "the ENTRY VALUE, not to an equivalent mapping — this does not "
                      "leave the state the operation must not disturb undisturbed. "
                      "Does NOT resolve as a transliteration of the frame the fix "
                      "relies on. (Caveat, stated rather than hidden: read as a "
                      "key->value mapping this rival agrees with gold everywhere, so "
                      "its rejection attests to the frame clause AS WRITTEN. That "
                      "same over-strong reading is escalated as a finding on the "
                      "FROZEN spec in the footer; the two are the same measurement "
                      "seen from the two directions.)",
        "rationale": "REJECT from E2 (`changedKey ≠ watchedKey → cached = "
                     "cachedOld`): the rival yields the REVERSED entry table where E2 "
                     "demands the entry table itself. Refuted at a two-entry "
                     "cachedOld=[(9,\"z\"),(8,\"y\")] with changedKey=\"OTHER\" ≠ "
                     "watchedKey=\"MESSAGE_TAGS\". Varies the mut binder's entry value "
                     "to LENGTH 2 (every other witness here uses length ≤ 1, where "
                     "reversal is the identity and this rival is indistinguishable "
                     "from gold), which is why the case needs its own input point.",
        "witness": _w('[(9, "z"), (8, "y")]', '"OTHER"', '"MESSAGE_TAGS"',
                      '[(1, "a")]', '[]'),
    },
    # ---- E1: recompute from the WRONG pair of tables (audit addition) -------
    {
        "id": "uniq-args-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Call the recompute with its two table arguments TRANSPOSED. Distinct from
        # uniq-default-wins, which reimplements the overlay in the wrong order:
        # this rival keeps the recompute verbatim and mis-wires what flows into it,
        # so it is wrong on shared keys AND on the ORDER of the disjoint-key
        # entries. Added by the audit — no existing rival probes the two table
        # binders' IDENTITY (which argument is the base and which the override).
        "module": _swap(
            _BASE, _IMPL,
            "    cached := if changedKey = watchedKey then "
            "recomputeTable overrides base else cached\n"
            "    return"),
        "refinement": "passing the two tables to the recompute the other way round "
                      "corresponds to a re-derivation wired with its defaults and its "
                      "configured overrides transposed. The failing test re-tags "
                      "built-in levels and asserts the configured tokens are in "
                      "force; with the arguments transposed the defaults win on every "
                      "shared level and the assertion fails. Does NOT resolve.",
        "rationale": "REJECT from E1: the post-image is `recomputeTable base "
                     "overrides`, but the rival computes `recomputeTable overrides "
                     "base`. Refuted at base=[(1,\"d\")], overrides=[(1,\"o\")]: gold "
                     "binds key 1 to \"o\", the rival to \"d\". Probes the IDENTITY of "
                     "the two table binders (which argument is which), which "
                     "uniq-default-wins does not — that rival re-implements the "
                     "overlay, this one keeps it and mis-wires its inputs. Probed at a "
                     "base of LENGTH 2 that shares one key with the overrides and "
                     "keeps one of its own — a distinct input point from "
                     "uniq-default-wins' single shared key.",
        "witness": _w('[]', '"ALT_KEY"', '"ALT_KEY"',
                      '[(1, "d"), (2, "e")]', '[(1, "o")]'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame/permission-mutation rivals, 4 uniqueness
# rivals — stale-no-derivation, drop-custom-slot, default-wins, wrong-branch —
# plus a supporting empty-custom near-miss) and a 2-case AXIOM lane, contracting
# ONE function (derive_tags_for_setting) over three permission-bearing Tags
# records under a message-tags identifier. This bundle models the SAME
# purely-functional core — recompute the cached table from base overlaid by
# overrides on the watched key, leave it untouched otherwise — reshaped over the
# LIST carrier (`List (Int × String)`) this backend actually contracts. The
# value/merge surface carries across intact; the permission surface does not
# exist here. Every sibling case is accounted for below.
#
#   sibling case (nagini)          -> here                              disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder            -> pos-control-branch-flip           RE-EXPRESSED
#   pos-control-inline             -> pos-control-let-staged            RE-EXPRESSED
#   admiss-f2p-shaped-input        -> admiss-f2p-shaped-config          RE-AIMED (audit)
#   uniq-frame-mutate-defaults     -> uniq-recompute-always (E2 frame)  RE-EXPRESSED
#   uniq-frame-mutate-override     -> uniq-wrong-branch    (E2 frame)   RE-EXPRESSED
#   uniq-stale-no-derivation       -> uniq-stale-no-derivation          PORTED (central)
#   uniq-default-wins              -> uniq-default-wins                 PORTED
#   uniq-drop-custom-slot          -> uniq-drop-overrides               RE-EXPRESSED
#   uniq-empty-custom              -> uniq-drop-empty-valued-override   RE-EXPRESSED
#   uniq-wrong-branch              -> uniq-wrong-branch                 PORTED
#   (no sibling)                   -> uniq-guard-literal                ADDED (audit)
#   (no sibling)                   -> pos-control-statement-branch      ADDED (audit)
#   (no sibling)                   -> uniq-frame-perturbed              ADDED (audit)
#   (no sibling)                   -> uniq-args-swapped                 ADDED (audit)
#   AXIOM_TESTS (2)                -> (none)                            DROPPED (G-AX)
#
# 13 SPEC cases (3 soundness, 1 admissibility, 9 uniqueness).
#
# RE-EXPRESSED (positives): the sibling's reorder positive handles the
#   non-message-tags branch first; the analogue here negates the guard and swaps
#   the arms (pos-control-branch-flip). The sibling's inline positive stages each
#   merged slot into a local; the analogue stages the recomputed table into a
#   local before selecting it (pos-control-let-staged). Both keep the frozen
#   `loom_solve` proof, which closes untouched.
# RE-EXPRESSED (frame/permission rivals -> E2-frame rivals): the sibling's two
#   MANDATORY permission-mutation rivals write the merged values back into a
#   read-only input (`defaults` / `override`, held at Acc(...,1/2)) and return it,
#   rejected for INSUFFICIENT PERMISSION. That exact MECHANISM is inexpressible
#   here — Lean/Velvet are referentially transparent, there is no heap, no
#   aliasing, no fractional permission, and the modeled inputs are immutable
#   values. DEMONSTRATED by the audit rather than asserted: a rival that tries to
#   write a non-`mut` input (`base := recomputeTable base overrides`) does not
#   reach a permission verdict at all — it fails to ELABORATE, with
#   ``error: `base` cannot be mutated, only variables declared using `let mut`
#   can be mutated``. So the probe cannot even be stated as a spec question on
#   this carrier: the assignment is rejected by the language before any
#   obligation is generated, which is the difference between a carrier collapse
#   and a rival the port merely failed to land. But the SOUNDNESS PROPERTY those
#   rivals defend — that state the
#   operation must not disturb is actually left undisturbed — is present as the
#   E2 frame clause `cached = cachedOld`, and IS attacked: uniq-recompute-always
#   and uniq-wrong-branch both perturb the cached table on the non-watched branch
#   and are refuted by E2. So this is NOT a fabricated substitute for the
#   permission probe (that would be wrong per the porting map); it is the port of
#   the read-only-frame PROPERTY the permission machinery encoded, expressed the
#   way this carrier expresses it (directive-5: pin the unchanged frame with an
#   `ensures xOld = x`, which the spec does, and attack it).
# PORTED: stale-no-derivation (the central prepatch bug), default-wins (the merge
#   direction inverted), wrong-branch (the guard inverted) each port directly.
# RE-EXPRESSED (drop-custom-slot -> drop-overrides): the sibling drops the custom
#   level (slot c taken from defaults, which lacks it). Over the LIST carrier the
#   analogue drops the override entries entirely (recompute to `base` alone),
#   which is wrong precisely where an override supplies an entry the base lacks —
#   the same partial-domain failure at the same F2P-discriminating shape.
# RE-EXPRESSED (empty-custom -> drop-empty-valued-override): the sibling forces
#   the custom slot to the empty tag. An earlier revision of this manifest recorded
#   the class as FOLDED into uniq-drop-overrides on the ground that "on the LIST
#   carrier both collapse to the same point". That justification was WRONG and the
#   audit measured it: uniq-drop-overrides' rival returns `base` alone, and every
#   witness in this battery carries only NON-EMPTY values, so a rival that drops
#   only the empty-VALUED override entries satisfies all of them — the class was
#   genuinely unattacked. It is now carried by uniq-drop-empty-valued-override,
#   which varies `overrides` along the VALUE axis (an entry whose tag is "") and
#   is a distinct input point, not a duplicate.
# RE-AIMED (admiss-f2p-shaped-input -> admiss-f2p-shaped-config). The sibling
#   self-calls the function on an F2P-shaped input to show its half-permission
#   precondition admits it. This method declares NO `require` clause (the
#   pre-conditions region is empty), so that exact probe — "a normal input
#   satisfies the precondition" — has no counterpart here.
#
#   An earlier revision recorded the whole lane as VACUOUS on the ground that "the
#   post-image is a total function defined at every input, so the obligation is
#   satisfiable everywhere by construction — the two positive controls witness
#   it". The audit measured that as WRONG on two counts, which is why the lane is
#   now carried rather than omitted. (a) The stated reason is the one explicitly
#   ruled out: "the frozen obligation has no precondition" is not a demonstration
#   of vacuity, because the analogue on a total carrier is the obligation being
#   unsatisfiable or DEGENERATE at exactly an F2P-shaped input. (b) The claim that
#   the positive controls already witness it is false as stated: each of them
#   discharges the obligation SYMBOLICALLY, over universally quantified binders,
#   and never evaluates the post-image at any concrete configuration — so none of
#   them would notice a post-image that is degenerate at the input the fix is
#   about. admiss-f2p-shaped-config closes that by discharging the obligation at
#   ONE concrete F2P-shaped configuration, by evaluation, as an in-region assert,
#   before closing the frozen obligation verbatim. Both halves of its liveness
#   were measured with real builds rather than argued (see the case comment).
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   deep A-reference `recomputeTable == the real table-recompute callee`,
#   mapping.md §3.1); this bundle consumes no axiom `ensures`, and the gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Both top-level clauses are defended (three positive
#   controls plus the admissibility case) and attacked: E1 (recompute) by
#   uniq-stale-no-derivation, uniq-default-wins, uniq-drop-overrides,
#   uniq-drop-empty-valued-override and uniq-args-swapped; E2 (frame) by
#   uniq-wrong-branch, uniq-recompute-always and uniq-frame-perturbed; and the
#   guard's BINDER IDENTITY (that it relates the two key binders rather than
#   testing a constant) by uniq-guard-literal. The two TABLE binders' identity
#   (which argument is the base and which the override) is attacked by
#   uniq-args-swapped, and the frame's strength — held as a value, not merely as a
#   mapping — by uniq-frame-perturbed.
#   Every input binder of the spec predicate is varied by
#   the reject witnesses: the guard binders `changedKey`/`watchedKey` across BOTH
#   arms (equal on the E1 rivals, differing on the three E2 rivals) AND off the
#   "MESSAGE_TAGS" literal (four E1 witnesses pin both to "ALT_KEY", so a rival
#   hard-coding the watched key rather than comparing the two binders is caught —
#   uniq-guard-literal is exactly that rival); `base`
#   and `overrides` in length, key overlap and VALUE (shared key [(1,"d")]/[(1,"o")]
#   for the merge direction, disjoint keys [(10,"a")]/[(20,"b")] for the dropped
#   overrides, empty overrides elsewhere, and an empty-STRING override value
#   [(1,"a")]/[(2,"")] for the empty-value near-miss); and the mut binder's entry
#   value `cachedOld` at a NON-EMPTY table ([(9,"z")]) on the E2 always-recompute
#   rival so the frame violation is observable, and at a LENGTH-2 table
#   ([(9,"z"),(8,"y")]) on uniq-frame-perturbed, where a reordering of the frame
#   is observable at all. Every reject witness probes a DISTINCT input point
#   (pts=9).
# WITNESS DISCRIMINATION (two real builds per reject case at authoring, re-derived
#   independently by the audit): each witness ELABORATES against its rival (the
#   extracted program's post-state provably violates the postcondition at the
#   probed input, `decide` closes, exit 0) and FAILS against the frozen solution
#   (exit 1) with a PLAIN EVALUATION — `Tactic 'decide' proved that the
#   proposition refreshCachedTableTester <literals> = false is false`, i.e. the
#   kernel evaluated the tester at those literals, got `true`, and refuted the
#   claim. Nothing here is stuck: no `decide` gets wedged on an unreducible term,
#   no `Decidable` instance is missing, no unification fails, so the gold-side
#   exit code is a decision about the claim and not a tactic artifact.
#
#   FORGERY CHECK (attack B′, run by the audit for all nine reject cases). For
#   each witness, a second file differing ONLY in what it claims — the flipped
#   assertion `... = true` — was built against both subjects. Every flip INVERTED
#   both exit codes: gold 0 (the tester really is `true` there, so gold satisfies
#   the postcondition) and rival 1 (`decide` refutes it, `... = true is false`).
#   So each build's exit code tracks the claim rather than the file's shape, which
#   is what makes the gold-side failure admissible evidence. A forged witness
#   asserting gold is CORRECT at these points would be REJECTED here, not
#   recorded as a refutation.
#
#   No witness binds a hypothesis (the List/String carriers compute on literals),
#   so there is no joint-satisfiability obligation. No
#   `sorry`/`admit`/`native_decide`/`axiom` appears.
#
# WITNESS INDEPENDENCE (audit measurement — the claim each case is NOT subsumed).
#   Checked by cross-building witnesses against each other's rivals:
#   uniq-drop-overrides' witness FAILS against the drop-empty-valued-override
#   rival (exit 1), so the empty-value class really is unattacked by it and the
#   footer's non-subsumption claim below holds; conversely
#   uniq-drop-empty-valued-override's witness elaborates against the
#   uniq-drop-overrides rival (exit 0) and uniq-default-wins' witness elaborates
#   against the uniq-guard-literal rival (exit 0), which confirms — rather than
#   contradicts — the uniq-guard-literal rationale's own statement that the
#   constant-guard CLASS was already detectable incidentally and what the case adds
#   is a rival that IS that impl.
#
# ===========================================================================
# OPEN FINDING ON THE FROZEN SPEC (SPEC-TOO-STRONG; escalated, NOT patched here).
# Recorded by an independent audit of this battery. It is a property of the FROZEN
# `ensures`, so it cannot be fixed from this file — a spec change has to re-clear
# the equivalence and leakage gates, which are outside this lane.
#
# The E1 clause pins the post-state by LIST equality:
#     cached = recomputeTable base overrides
# but the declared carrier bijection (mapping.md §2, refinement.md row A1) says a
# real dictionary corresponds to a `List (Int × String)` **as a key→value
# mapping**, i.e. equality is ORDER-INSENSITIVE, and the sole failing test
# compares dictionaries, which is likewise order-insensitive. So list equality is
# STRICTLY STRONGER than the modeled behavior, and it rejects faithful impls.
#
# RE-DERIVED INDEPENDENTLY by a second audit, which did not take the first's word
# for it. Builds and exit codes as observed:
#   * The base-key-order overlay
#       base.map (fun kv => (kv.1, (lookupEntry overrides kv.1).getD kv.2))
#         ++ overrides.filter (fun kv => (lookupEntry base kv.1).isNone)
#     is REJECTED by the frozen spec (exit 1), with the E1 goal left open — the
#     failure names the clause (`ensures_2: changedKey = watchedKey → cached =
#     recomputeTable base overrides`), so it is the spec refusing the impl, not a
#     parse or type error. Two reproof attempts (`simp_all [recomputeTable,
#     lookupEntry]`, and a `decide`/`simp_all`/`omega` cascade) also failed
#     (exit 1 each), so it is not a tactic gap that a better script closes.
#   * Yet that impl is faithful AS A MAPPING, proven by `decide` in ONE file
#     (exit 0) at a concrete F2P-shaped configuration (a shared key re-tagged, a
#     shared key set to the empty value, an override-only key): it is a DIFFERENT
#     LIST from `recomputeTable`, it agrees with it on EVERY key either mentions,
#     it has the same length, and each contains every entry of the other — i.e.
#     same multiset, same mapping, different order.
#   * A pure REORDER of the frame (`cached.reverse` on the non-watched branch) is
#     likewise rejected under E2 (exit 1, goal open on `ensures_1`), which is the
#     same over-strong reading arriving through the frame clause. That rival is
#     now carried as uniq-frame-perturbed with the caveat written into its
#     refinement, rather than left as an unattacked shape.
#
# Machine-checked witness of the gap (first audit's builds, exit codes as
# observed):
#   * An impl that overlays the overrides onto the base IN BASE-KEY ORDER — i.e.
#     each base entry updated in place, then the override-only entries appended —
#     is REJECTED by the frozen spec (variant build exit 1, and a witness at
#     base=[(1,"a")], overrides=[(2,"b")] elaborates against it, exit 0, while
#     failing on gold, exit 1: a genuine semantic refutation). Two reproof attempts
#     also failed (exit 1), so this is the spec, not a tactic gap.
#   * Yet that impl is the MORE faithful transliteration of the real recompute:
#     it reproduces the real callee's own entry order exactly, whereas
#     `recomputeTable` (overrides first) does not. It agrees with
#     `recomputeTable` on every key, and is the same multiset of entries —
#     both proven by `decide` (exit 0) on the minimal input and on the
#     failing test's configuration shape.
#   * A plain REORDER of `recomputeTable`'s own output (base-survivors first,
#     overrides last) is rejected the same way (exit 1; witness discriminates,
#     rival exit 0 / gold exit 1).
#
# Consequence: `verify ⟹ correct` still holds (the spec is too strong, not too
# weak, so nothing wrong is admitted), but a correct patch can fail to verify.
# Disposition: escalate to the spec lane. Either weaken E1 to mapping equality
# (e.g. pin `lookupEntry cached k = lookupEntry (recomputeTable base overrides) k`
# for every k, plus a no-duplicate-key condition) or state the order the carrier
# is actually meant to fix. The positive controls above stay valid either way. One
# case, uniq-frame-perturbed, DOES depend on the over-strong reading and says so in
# its own refinement — it is the reject side of this same measurement, carried
# because the frozen `ensures` is what this battery is judged against.
# ===========================================================================
#
# ===========================================================================
# SPEC-TOO-WEAK PROBE (attack D — audit). Seven NEW wrong impls the battery did
# not contain were built against the frozen spec, aimed at what the existing
# rivals left unattacked. ALL SEVEN were REJECTED (exit 1), each with the goal
# left open on the clause it violates, so no spec hole was found in this
# direction:
#   * `recomputeTable overrides base`      (table binders transposed) -> E1 open
#   * `overrides ++ base`                  (overlay with no filter)   -> E1 open
#   * `recomputeTable base (overrides.take 1)` (only the first override) -> E1
#   * `(recomputeTable base overrides).mergeSort ...` (sorted post-image) -> E1
#   * `cached.eraseDups` on the frame arm  (frame deduplicated)       -> E2 open
#   * `cached.reverse` on the frame arm    (frame reordered)          -> E2 open
#   * guard on `changedKey.length = watchedKey.length` (a coarser relation
#     than equality, correct on every input whose two keys differ in length)
#                                                                     -> open
# The first and the sixth were kept as cases (uniq-args-swapped,
# uniq-frame-perturbed) because they attack binder identities no prior rival
# reached; the rest are recorded here as measured-and-rejected rather than
# carried, since their witnesses would duplicate input points the battery
# already probes.
# ===========================================================================
AXIOM_TESTS = []
