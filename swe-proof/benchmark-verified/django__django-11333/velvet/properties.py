"""properties.py — G-PBT falsification battery for django__django-11333 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct sharedHandle`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  sharedHandle (requested : Option String) (ambient : String)
      return (out : Option String)
    ensures out = some (lookupKey requested ambient)

where the pure helper is the resolution
  ``lookupKey none ambient = ambient`` ; ``lookupKey (some u) _ = u``.

The operation hands back a shared object associated with an OPTIONAL identifier,
where object identity is modeled by the storage key (mapping.md §2: identity ⟺
key equality), carried as an ``Option String``. The single top-level ``ensures``
clause pins the returned key to the RESOLVED identifier:

  (C1) ``out = some (lookupKey requested ambient)``

which is one predicate combining THREE distinguishable obligations, each keyed
on a different binder value:
  * the result is always PRESENT (``some _``, never the bare absent sentinel);
  * on an OMITTED identifier (``requested = none``) the key is the ambient
    default ``ambient`` — so an omitted request shares its object with an
    explicit request for that default;
  * on a PRESENT identifier (``requested = some u``) the key is ``u`` itself,
    and ``ambient`` is IGNORED.
Both input binders are load-bearing: ``requested`` selects the branch, and
``ambient`` is the returned key on the ``none`` branch. There is no opaque
oracle to echo (the ``axioms`` region is empty; ``lookupKey`` is a fully
unfolded pure function), so the unique satisfier IS the resolved key.

CARRIER NARROWING (this bundle vs the sibling battery). The sibling contracts a
richer function over a mutable memo table: it carries an explicit cache, a
``cached``/``existing``/``fresh`` HIT/MISS split, a distinctness (only-the-
resolved-slot-changed) clause, and a cache-only-grows clause, and its rivals
attack each of those. This bundle models ONLY the purely functional core the
fix actually turns on — WHICH key the shared object is stored under — as a total
function ``requested ↦ resolved key``. The memo table, the HIT/MISS value split,
and the distinctness/growth clauses are NOT modeled here (there is no cache
state on this carrier: repeated-call identity is refined away to key equality,
validated out-of-band by G-CONF). Rivals attached to those unmodeled behaviors
therefore have NO counterpart and are legitimately omitted; see the footer for
the case-by-case accounting.

ADVERSARIAL READ of the sibling's classes:
  * FRAME-MUTATION — VACUOUS on this backend. Lean and Velvet are referentially
    transparent: ``requested``/``ambient`` are immutable values, this bundle
    declares no ``mut`` parameter, there is no heap and no aliasing. There is no
    read-only input to overwrite and no permission system to trip. The sibling's
    own refinement already records this class as inapplicable to this instance
    (the cache is genuinely mutated by gold, the scalars are immutable), so it
    is doubly vacuous here. No substitute is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. C1 pins ``out`` to ``lookupKey requested
    ambient`` which is a fully-unfolded pure function of the two input binders;
    there is no answer-key term a wrong impl could echo. The cheapest correct
    impl resolves the key honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: a rival
    that takes the key from the request AS RECEIVED is correct on every present
    identifier and diverges only on the omitted-identifier sub-domain (the exact
    pre-fix bug); a rival that resolves an omitted identifier to a WRONG default
    constant is correct only when the ambient default happens to equal that
    constant; a rival that always returns the ambient default is correct only on
    the omitted-identifier sub-domain; and a rival that conflates an explicitly
    EMPTY identifier with an omitted one is correct everywhere except at that one
    boundary point.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
four witnesses sit at four DISTINCT input points and vary BOTH binders: the
raw-key and wrong-default rivals are refuted on the OMITTED-identifier branch (at
two distinct ambient defaults "A" and "D"), and the ignore-request and
empty-treated-absent rivals on the PRESENT-identifier branch (``some "B"``
against ambient "C", and the empty-content boundary ``some ""`` against ambient
"Z") — so both branches of ``lookupKey`` are attacked, ``ambient`` is
demonstrated load-bearing on the ``none`` branch (the wrong-default rival
diverges only in ``ambient``'s value), and no clause is demonstrated at a single
pinned point. Every witness closes by ``decide``, i.e. by EVALUATION of the
extracted tester at a fully concrete input, so its gold-side failure is a
computed refutation of the concrete claim rather than a tactic mismatch: the
claim's negation is what changes the exit code (measured in both directions).

ADMISSIBILITY. Carried by ``admiss-resolved-key-satisfiable``. The frozen
obligation has no precondition, but that is NOT a reason to drop the lane — on a
total carrier the analogue is whether the obligation is SATISFIABLE at an
F2P-shaped input, since an obligation unsatisfiable exactly where the behavior is
observed is indistinguishable from one every impl meets. See the footer.
"""
from pathlib import Path

INSTANCE = "django__django-11333"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen resolve-then-return body. Lies
# ---- wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap).
_IMPL = (
    "    let key := match requested with\n"
    "      | none   => ambient\n"
    "      | some u => u\n"
    "    return some key"
)

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script (`loom_solve`) is tuned to the
# ---- frozen match-then-return body. A positive control that reshapes the impl
# ---- may need to retune it; both the impl region and the `prove_correct` body
# ---- are elided from the spec view, so same_spec still holds and the
# ---- `prove_correct sharedHandle` obligation survives with an identical
# ---- statement. Unique in the file.
_PROOF = (
    "prove_correct sharedHandle by\n"
    "  loom_solve"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# A reshape whose residual goal is a per-constructor definitional equality closes
# with a `cases requested <;> rfl` tail after `loom_solve`.
_PROOF_CASES = (
    "prove_correct sharedHandle by\n"
    "  loom_solve\n"
    "  cases requested <;> rfl"
)


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced
    (frozen tactic script kept — used for reject rivals, expected NOT to
    verify)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Reshape the impl region AND retune the tactic body (soundness positives
    whose reshaped impl no longer matches the frozen script)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


def _impl_prefix(prefix):
    """Keep the ENTIRE frozen body and prepend an in-region `assert` to it, so
    the frozen `prove_correct` obligation still discharges verbatim while the
    added assertion becomes a live, separately-discharged goal. Used by the
    admissibility case."""
    return _swap(_BASE, _IMPL, prefix + _IMPL)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `sharedHandleTester requested ambient = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for sharedHandle\n"
            "prove_precondition_decidable_for sharedHandle\n"
            "prove_postcondition_decidable_for sharedHandle\n"
            "derive_tester_for sharedHandle\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-getd",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: resolve via the option-default combinator rather than an
        # explicit match. `requested.getD ambient` is definitionally the resolved
        # key, so C1 holds; the residual goal closes with a per-constructor `rfl`.
        "module": _impl_proof(
            "    return some (requested.getD ambient)",
            _PROOF_CASES),
        "rationale": (
            "`requested.getD ambient` computes the resolved key exactly "
            "(`none ↦ ambient`, `some u ↦ u`), so C1 (`out = some (lookupKey "
            "requested ambient)`) holds; a structurally-different but correct "
            "reshape (no explicit match). If it fails to verify the spec is "
            "SPEC-TOO-STRONG (over-fit to the explicit-match spelling)."
        ),
    },
    {
        "id": "pos-control-branch-some",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: push the `some` constructor into each match arm and return the
        # matched option directly, instead of resolving to a key and wrapping
        # once. Observationally identical; the frozen `loom_solve` still closes.
        "module": _impl(
            "    let out := match requested with\n"
            "      | none   => some ambient\n"
            "      | some u => some u\n"
            "    return out"),
        "rationale": (
            "a correct reshape that constructs the present result inside each "
            "match arm (`none ↦ some ambient`, `some u ↦ some u`) rather than "
            "wrapping a resolved key once; observationally identical, so C1 "
            "holds. A second structurally-different correct impl defends the "
            "soundness surface. If it fails => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at exactly the shape of the
    # failing test. The method carries no `require` clause, so the classic
    # "a normal input satisfies the precondition" probe has nothing to
    # establish; the analogue on a TOTAL carrier is that the obligation is
    # discharge-able at a concrete F2P-shaped input rather than being
    # unsatisfiable there — a spec no impl can meet at the very input the
    # behavior turns on reads exactly like a spec every impl meets. This case
    # discharges that by EVALUATION as in-region `assert` conjuncts, at the
    # concrete input triple the failing test exercises, and then closes the
    # frozen obligation verbatim (the whole frozen body is retained).
    # =====================================================================
    {
        "id": "admiss-resolved-key-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        # Three conjuncts, each keyed on the concrete point the failing test
        # uses: an omitted identifier and an explicit mention of the ambient
        # default land on the SAME key (the shared-object assertion); a
        # genuinely different identifier lands on a DISTINCT key (the
        # not-shared assertion); and the resolved key is PRESENT, never the
        # bare absent sentinel. Each conjunct was measured LIVE — negating any
        # one of them fails the build — so the assert is not vacuous padding.
        "module": _impl_prefix(
            "    assert (with_name_prefix `assert\n"
            '      (lookupKey none "cfg" = lookupKey (some "cfg") "cfg"\n'
            '       ∧ lookupKey (some "other") "cfg" ≠ lookupKey none "cfg"\n'
            '       ∧ (some (lookupKey none "cfg") : Option String) ≠ none))\n'),
        "rationale": (
            "PRECOND-TOO-STRONG analogue on a total carrier: the obligation is "
            "jointly satisfiable, and non-degenerate, at exactly the "
            "F2P-shaped input — an omitted identifier resolves to the SAME key "
            "as an explicit mention of the ambient default (so the two share "
            "one object), a distinct identifier resolves to a DIFFERENT key "
            "(so it does not), and the resolved key is always present. All "
            "three discharge by evaluation, and the frozen body is kept so C1 "
            "still discharges verbatim. If this case failed, the obligation "
            "would be unsatisfiable precisely where the behavior is observed, "
            "which no reject rival can detect. Re-aims the sibling's "
            "admiss-omitted-empty-cache, whose fresh-empty-cache permission "
            "half has no counterpart on a carrier with no cache state."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-raw-key",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-fix bug: take the key from the request AS RECEIVED,
        # WITHOUT resolving an omitted identifier to the ambient default. On a
        # present identifier this agrees with gold; on an omitted identifier it
        # returns the absent sentinel instead of the resolved default.
        "module": _impl("    return requested"),
        "refinement": (
            "this is the pre-change behavior: the shared object's identity is "
            "taken from the request as received, so an OMITTED identifier and an "
            "explicit mention of the ambient default land on DIFFERENT keys and "
            "get DIFFERENT objects. Its faithful counterpart is the unchanged "
            "code that memoizes on the raw argument, under which a defaulted "
            "request and an explicit-default request build two distinct shared "
            "objects — the failing test asserts they are the SAME object, so it "
            "would NOT resolve. Correct on every present identifier (a true "
            "partial-domain break, not a blanket wrong impl)."
        ),
        "rationale": (
            "REJECT from C1: on `requested = none` the spec requires "
            "`some ambient`, but this returns `none` (the absent sentinel), so "
            "`out ≠ some (lookupKey none ambient)`. This is the precise change "
            "the spec senses. If it verified => SPEC-TOO-WEAK (the omitted→"
            "default resolution unenforced). Refuted on the omitted-identifier "
            "branch at ambient \"A\"."
        ),
        "witness": _tester(
            'example : sharedHandleTester none "A" = false := by\n'
            '  decide\n'),
    },
    {
        "id": "weak-wrong-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolves an omitted identifier, but to a WRONG hardcoded default
        # constant instead of the ambient default. Present identifiers are
        # handled correctly; the omitted branch diverges whenever the ambient
        # default differs from the constant.
        "module": _impl('    return some (requested.getD "R")'),
        "refinement": (
            "a counterpart that DID move the resolution before the key but "
            "resolved an omitted identifier to a hardcoded default rather than "
            "the ambient one (a plausible half-fix). It shares its object with "
            "an explicit request for that hardcoded name, NOT for the ambient "
            "default the request actually intends, so a defaulted request and an "
            "explicit ambient-default request still get different objects — the "
            "failing test would NOT resolve, except in the degenerate case where "
            "the ambient default equals the hardcoded constant."
        ),
        "rationale": (
            "REJECT from C1: on `requested = none` with ambient \"D\" the spec "
            "requires `some \"D\"`, but this returns `some \"R\"`. This is the "
            "sub-domain that proves `ambient` is load-bearing on the `none` "
            "branch — a rival that ignored `ambient`'s value here would be caught "
            "only by this witness, distinct from weak-raw-key's (which fails "
            "regardless of `ambient`). If it verified => SPEC-TOO-WEAK (the "
            "resolved default not pinned to `ambient`)."
        ),
        "witness": _tester(
            'example : sharedHandleTester none "D" = false := by\n'
            '  decide\n'),
    },
    {
        "id": "weak-ignore-request",
        "kind": "uniqueness",
        "expect": "reject",
        # Always returns the ambient default, ignoring a present identifier.
        # Correct only on the omitted-identifier sub-domain; on any present
        # identifier it returns the wrong key.
        "module": _impl("    return some ambient"),
        "refinement": (
            "always hands back the object for the ambient default, ignoring an "
            "explicitly-named identifier. A counterpart of this shape would "
            "coalesce EVERY request onto the ambient default's object, so a "
            "request for a genuinely different identifier shares an object with "
            "the default when it must not — the failing test asserts a request "
            "for a distinct identifier gets a DISTINCT object, so it would NOT "
            "resolve. Correct only on the omitted-identifier sub-domain."
        ),
        "rationale": (
            "REJECT from C1: on `requested = some u` the spec requires "
            "`some u`, but this returns `some ambient`; with `u = \"B\"`, "
            "`ambient = \"C\"` these differ. This attacks the PRESENT-identifier "
            "branch of `lookupKey` (the `some u` arm) that neither omitted-branch "
            "rival touches, and varies both binders. If it verified => "
            "SPEC-TOO-WEAK (the present-identifier key unpinned)."
        ),
        "witness": _tester(
            'example : sharedHandleTester (some "B") "C" = false := by\n'
            '  decide\n'),
    },
    {
        "id": "weak-empty-treated-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolves correctly on an OMITTED identifier and on every non-empty
        # present identifier, but treats an explicitly-present EMPTY identifier
        # as if it had been omitted, resolving it to the ambient default. The
        # narrowest partial-domain break in the battery: it diverges from the
        # spec at exactly ONE point of the input space.
        "module": _impl(
            "    let key := match requested with\n"
            "      | none   => ambient\n"
            '      | some u => if u = "" then ambient else u\n'
            "    return some key"),
        "refinement": (
            "a counterpart that conflates an explicitly-supplied empty "
            "identifier with an omitted one — the classic falsy-versus-absent "
            "conflation — and so hands an explicit empty request the ambient "
            "default's shared object instead of its own. The failing test "
            "asserts a request for a distinct identifier gets a DISTINCT "
            "object; under this shape an explicitly empty identifier is "
            "coalesced onto the default's object, so an identity assertion "
            "distinguishing them would NOT resolve. Correct on the omitted "
            "identifier and on every non-empty one."
        ),
        "rationale": (
            "REJECT from C1: on `requested = some \"\"` the spec requires "
            "`some \"\"` (the present-identifier arm returns `u` itself, "
            "whatever its content), but this returns `some ambient`. Attacks "
            "the PRESENT-identifier arm at the empty-string boundary — a "
            "pinned boundary input none of the other rivals reaches, since "
            "weak-ignore-request breaks that arm for EVERY present identifier "
            "while this one is correct on all but a single point. If it "
            "verified => SPEC-TOO-WEAK (the present-identifier key pinned only "
            "for non-empty content)."
        ),
        "witness": _tester(
            'example : sharedHandleTester (some "") "Z" = false := by\n'
            '  decide\n'),
    },
]


# ---------------------------------------------------------------------------
# Sibling -> velvet accounting. The sibling battery has 7 SPEC cases (2
# soundness positives, 1 admissibility, 4 uniqueness rivals; AXIOM_TESTS empty).
# This bundle models only the purely-functional CORE the fix turns on — a single
# total function `sharedHandle : (Option String) (String) -> (Option String)`,
# WHICH key the shared object is stored under — where the sibling contracts a
# richer function over a mutable memo table (cache dict, cached/existing/fresh
# HIT/MISS split, distinctness + cache-only-grows clauses). The key-resolution
# surface carries across intact; the cache-state surface does not exist here
# (repeated-call identity is refined away to key equality, validated by G-CONF).
# Every sibling case is accounted for below.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-merge-tail       -> pos-control-getd                RE-SHAPED
#   pos-control-tmp-local        -> pos-control-branch-some         RE-SHAPED
#   admiss-omitted-empty-cache   -> admiss-resolved-key-satisfiable RE-AIMED
#   rival-overwrite-on-hit       -> (none)                          VACUOUS
#   rival-raw-key                -> weak-raw-key                    PORTED
#   rival-miss-returns-existing  -> weak-wrong-default (analogue)   RE-EXPRESSED
#   rival-corrupt-other-key      -> (none)                          VACUOUS
#                                   (+ weak-ignore-request ADDED)
#                                   (+ weak-empty-treated-absent ADDED)
#
# 1 ported, 1 re-expressed, 1 re-aimed, 2 positive controls re-shaped, 2
# vacuous; 2 rivals added for binder/boundary coverage.
#
# PORTED (rival-raw-key -> weak-raw-key): the sibling's raw-key rival keys the
#   memo on the RAW argument so an omitted selector lands in a separate slot and
#   the resolved-default slot is never populated. On this carrier that is exactly
#   `return requested` (take the key as received), rejected by C1 on
#   `requested = none`. This IS the modeled bug and the prepatch discriminator.
# RE-EXPRESSED (rival-miss-returns-existing -> weak-wrong-default): the sibling's
#   "wrong value on a sub-domain" (return the unconstrained `existing` scalar
#   instead of the resolved value) has no HIT/MISS carrier here, but its spirit —
#   a rival that produces the WRONG value on one sub-domain of a correct branch —
#   is re-expressed as resolving an omitted identifier to a wrong DEFAULT
#   constant, rejected by C1 only where `ambient` differs from the constant. This
#   is what makes the `ambient` binder load-bearing in the reject lane.
# RE-SHAPED (pos controls): the sibling's two correct reshapes (single-return
#   merge-tail; typed-local staging) become the two structurally-different
#   correct impls this carrier admits — the option-default combinator and the
#   push-`some`-into-arms form (one retunes the tactic body, which is elided from
#   the spec view).
# ADDED (2): weak-ignore-request — a rival that ignores a PRESENT identifier and
#   always returns the ambient default. No direct sibling counterpart, but it
#   attacks the `some u` branch of `lookupKey` that neither omitted-branch rival
#   touches, and varies both binders — closing binder/branch coverage.
#   weak-empty-treated-absent — conflates an explicitly-present EMPTY identifier
#   with an omitted one. Also no sibling counterpart (the sibling's selector is
#   an `int`, so it has no empty-content boundary at all). It is the narrowest
#   partial-domain break here — correct on the omitted identifier AND on every
#   non-empty present one, diverging at a single point — which is what makes it
#   a sharper SPEC-TOO-WEAK probe than weak-ignore-request, whose break is
#   total on the `some u` arm. The empty string is a pinned boundary input
#   (mapping.md §4), so this is a point the carrier genuinely distinguishes.
#
# RE-AIMED (admiss-omitted-empty-cache -> admiss-resolved-key-satisfiable): the
#   sibling's admissibility control establishes the fractional-permission
#   precondition on a fresh empty cache (`dict_pred({})`; `cached == (0 in {})
#   == False`). That permission/cache-state half genuinely has no counterpart
#   here: this method has NO precondition (the pre-conditions region is empty;
#   the contract is total over `(Option String) (String)`) and there is no cache
#   container to be empty. But "the frozen obligation has no precondition" does
#   NOT make the lane vacuous — the analogue on a TOTAL carrier is whether the
#   obligation is SATISFIABLE at an F2P-shaped input, since an obligation that
#   is unsatisfiable exactly where the behavior is observed reads identically to
#   one that every impl meets, and no reject rival can sense the difference. So
#   the lane is re-aimed rather than dropped: admiss-resolved-key-satisfiable
#   discharges, by evaluation at the concrete input triple the failing test
#   exercises, that the omitted identifier and an explicit mention of the
#   ambient default share one key, that a distinct identifier does not, and that
#   the resolved key is present — then closes the frozen obligation verbatim.
#   Each conjunct was measured LIVE (negating any one fails the build), so the
#   assert is not vacuous padding.
# VACUOUS (rival-overwrite-on-hit): the sibling's over-construct (django-12713)
#   rival rebuilds and re-stores the shared object on a cache HIT instead of
#   reusing it, rejected by the memoization value clause `Implies(cached, Result
#   == existing)`. This carrier has NO cache state and NO HIT/MISS distinction:
#   object identity is refined to key equality (mapping.md §2), so "reuse the
#   cached object vs rebuild it" is not observable — two calls with the same
#   resolved key ARE the same object by refinement. There is no `cached`/
#   `existing` scalar and no memo-value clause to violate; the class collapses
#   under the refinement and has no discriminating witness on this carrier. It is
#   dropped rather than faked (per the porting map, drop-and-say-so beats a rival
#   whose abstraction nagini kept but this carrier collapses).
# VACUOUS (rival-corrupt-other-key): the sibling's distinctness rival clobbers a
#   NEIGHBOURING cache slot on a miss, rejected by the Forall distinctness clause
#   `k != resolved => cache[k] == Old(cache[k])`. There is no cache container on
#   this carrier — the output is a single resolved key, not a mutated map — so
#   there is no other slot to corrupt and no distinctness/frame clause to
#   violate. The class has no counterpart here; dropped.
# FRAME-MUTATION: VACUOUS. Referentially-transparent backend, no `mut` parameter,
#   no heap, no aliasing, no permission system. The sibling itself already
#   records this class as inapplicable to this instance. No substitute fabricated.
#
# BINDER / CLAUSE COVERAGE. The two input binders are `requested : Option String`
#   and `ambient : String`; the single top-level clause C1 combines three
#   obligations (result present; `none ↦ ambient`; `some u ↦ u`). `requested` is
#   varied across `none` (weak-raw-key, weak-wrong-default), `some "B"`
#   (weak-ignore-request) and `some ""` (weak-empty-treated-absent), attacking
#   BOTH branches of `lookupKey` and, within the present-identifier arm, both a
#   non-empty identifier and the empty-content boundary. `ambient` is varied
#   across "A"/"C"/"D"/"Z" and is demonstrated LOAD-BEARING by weak-wrong-
#   default (which diverges from gold only in `ambient`'s value on the `none`
#   branch — a rival mishandling only `ambient` there is caught by no other
#   witness). Four DISTINCT witness input points (pts=4). Both the "always
#   present (some)" obligation and both resolution branches are attacked, and
#   the admissibility case pins a fifth point (the F2P-shaped triple) at which
#   the obligation is shown satisfiable rather than merely unfalsified.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (there are no consumed
#   axioms in this bundle in any case), and this gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
