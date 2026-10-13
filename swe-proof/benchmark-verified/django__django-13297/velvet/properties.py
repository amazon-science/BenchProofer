"""properties.py — G-PBT falsification battery for django__django-13297 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over a key→value mapping carrier,
``List (Nat × Value)`` → ``List (Nat × Wrapper)``):

  deferMapping (entries : List (Nat × Value)) return (out : List (Nat × Wrapper))
    ensures out = deferredOf entries                                    -- (C1)
    ensures ∀ v : Value, coerce (deferOne v) v.tag = Coerced.genuine v  -- (C2)

  where ``deferredOf`` maps each entry ``(k, v)`` to ``(k, deferOne v)`` and
  ``deferOne v = { forced := v, reported := none }``.

CLAUSE STRUCTURE (read before judging clause / binder coverage).

  * (C1) ``out = deferredOf entries`` is the SOLE load-bearing, impl-discriminating
    clause. It is a full structural equality on the input carrier — GROUNDED in the
    method input ``entries`` (directive 8), not an opaque answer key — and pins
    three independent facets simultaneously: (a) every KEY is carried through
    unchanged; (b) ORDER (and length) is preserved; (c) each value ``v`` becomes
    exactly ``deferOne v`` — i.e. it FORCES back to ``v`` (``forced := v``) AND it
    advertises the distinct proxy type rather than masquerading as ``v``'s own
    runtime type (``reported := none``, never ``some t``). The reject rivals below
    each attack one of these facets.

  * (C2) ``∀ v : Value, coerce (deferOne v) v.tag = Coerced.genuine v`` is
    IMPL-INDEPENDENT: it mentions neither ``out`` nor ``entries``. It is a closed
    statement about the FROZEN pure defs ``deferOne`` / ``coerce`` (it is literally
    the frozen ``coerce_deferOne`` lemma instantiated), so it holds for EVERY
    implementation and NO impl variant can falsify it. It is therefore not an
    attackable clause — it is the genuineness GUARANTEE the spec publishes, stated
    as a fact, and it is defended by the two soundness positives (which discharge
    it while reshaping the impl) rather than attacked by a rival. This is recorded
    honestly in the accounting below; do not read the absence of a C2-rival as a
    coverage gap — a clause no impl can violate has no falsifier by construction.
    (The witnesses below supply the C2 ``Decidable`` instance explicitly, via
    ``isTrue (fun v => coerce_deferOne v v.tag)``, precisely because it is a
    universally-quantified tautology the tester cannot auto-decide.)

BINDER STRUCTURE. The postcondition has ONE input binder, ``entries``, a list of
``(key : Nat) × (value : Value)`` where ``value`` carries ``tag : Nat`` (its
runtime type) and ``content : List Char`` (its payload). The reject witnesses
VARY the observable sub-fields across four distinct input points — keys
{1, 2, 7, 5}, tags {1, 3, 2}, content lengths {1, 2, 1, 1} — so no facet of the
carrier is pinned at a single value by every rival. pts=4.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS here, exactly as it is in the nagini sibling. The
    nagini surface holds a PURE immutable value-tag ``value: int`` carrying no
    ``Acc(...)`` permission, so it already has NO read-only frame-mutation surface;
    the sibling omits the class honestly. Lean/Velvet reinforce this: every input
    is an immutable value, no binder is ``mut``, there is no heap and no aliasing.
    Not fabricated (porting map: this class is vacuous here).
  * CAPABILITY LAUNDERING (nagini ``weak-launder-capability``) — has no counterpart
    on this carrier. Nagini's ``binder_castable`` is an abstract predicate whose
    IDENTITY (the specific wrapper/value/type it names) is the thing laundered
    across copies; the whole attack exploits that a capability is a first-class
    object that can be obtained for one wrapper and illegitimately pointed at
    another. Here genuineness is not a capability object — it is a STRUCTURAL
    property of each wrapper (``reported = none``), computed field-wise by
    ``deferredOf``. There is nothing to obtain-then-relabel: a wrapper either
    structurally equals ``deferOne v`` or it does not. The abstraction collapses the
    distinction the nagini rival needs, so the rival is not expressible; omitted
    with this reason rather than fabricated.
  * DIVERGENCE / NON-TERMINATION — no counterpart: the nagini sibling carries NO
    ``diverge-*`` / ``nonterm-*`` case, so there is no divergence hole to record for
    this instance.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches the postcondition through Velvet's own tester machinery:
``deferMappingTester entries = false`` says the extracted program's result
violates the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The postcondition's C2 clause is a ``∀``-quantified statement the tester
cannot auto-``Decidable``, so each witness supplies that instance explicitly with
``isTrue (fun v => coerce_deferOne v v.tag)`` (the frozen lemma) — C2 is a
tautology, so this is sound and adds no assumption. A rival with a STRAIGHT-LINE
(``List.map`` / loop-free) body has an extracted program that kernel-reduces
under ``decide``, exposing its C1 violation; the frozen solution's back-to-front
copy LOOP does not reduce, which is exactly what makes the same witness FAIL on
gold — the required discriminator. Every reject witness below was run against
both the rival (elaborates) and the frozen solution (fails to elaborate) with two
real builds.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (mapping.md §3:
the change is a callee-swap modeled DIRECTLY by ``Wrapper.reported`` + ``coerce``,
no unchanged foreign callee). The gate ignores ``AXIOM_TESTS`` regardless; the
nagini ``AXIOM_TESTS`` (real-callee probes) are G-AX's job and are dropped here.
"""
from pathlib import Path

INSTANCE = "django__django-13297"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The complete frozen impl body (back-to-front copy
# ---- loop). Lies wholly inside the single `-- impl-start` / `-- impl-end`
# ---- region and is unique in Solution.lean (both facts asserted at load by
# ---- _swap), so any surgery anchored on it stays within the elided impl region
# ---- and never touches the frozen spec. ----
_IMPL = (
    "    let mut result : List (Nat × Wrapper) := []\n"
    "    let mut i := entries.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ entries.length\n"
    "      invariant result = deferredOf (entries.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := entries[i - 1]!\n"
    "      result := (p.fst, deferOne p.snd) :: result\n"
    "      i := i - 1\n"
    "    return result"
)

# ---- impl-start marker: prepend an in-region assert without disturbing the
# ---- frozen loop or proof (used by the admissibility case). ----
_IMPL_START = "    -- impl-start\n"

# ---- the frozen proof body (everything under the `prove_correct` header). The
# ---- reject rivals keep it verbatim (their rejection is carried by the witness,
# ---- not by whether the frozen loop script happens to break on the reshape); the
# ---- soundness positives retune it, since a loop-free reshape removes the
# ---- loop-body goal `loom_solve` leaves for the frozen impl. ----
_PROOF = (
    "prove_correct deferMapping by\n"
    "  loom_solve\n"
    "  · rw [deferredOf_drop_step entries i (by omega) (by omega)]\n"
    "    simp_all"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_and_proof(new_impl: str, new_proof: str) -> str:
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery. The precondition is trivially true (no `require`), so the
# ---- tester's guard is vacuous and never excludes an input. The postcondition's
# ---- C2 clause is a `∀ v : Value` tautology the tester cannot auto-decide, so we
# ---- supply its Decidable instance as `isTrue (fun v => coerce_deferOne v v.tag)`
# ---- — the frozen lemma, adding no assumption. `deferMappingTester entries =
# ---- false` then says the extracted program violates C1 (`out = deferredOf
# ---- entries`) at that input. ----
_TESTER = (
    "extract_program_for deferMapping\n"
    "prove_precondition_decidable_for deferMapping\n"
    "prove_postcondition_decidable_for deferMapping by\n"
    "  exact isTrue (fun v => coerce_deferOne v v.tag)\n"
    "derive_tester_for deferMapping\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Each keeps the byte-identical
    # C1/C2 obligation and only reshapes the executable surface; the proof is
    # retuned because a loop-free reshape removes the loop-body goal `loom_solve`
    # leaves. Both verified out-of-band with real builds (~12s each).
    # =====================================================================
    {
        "id": "pos-direct-map",
        "kind": "soundness",
        "expect": "verify",
        # The maximally direct correct reshape: return the deferred mapping
        # directly, dropping the back-to-front copy loop entirely. `loom_solve`
        # closes it because `out = deferredOf entries` is now definitional and C2
        # is the frozen `coerce_deferOne` lemma.
        "module": _with_impl_and_proof(
            "    return deferredOf entries",
            "prove_correct deferMapping by\n  loom_solve",
        ),
        "rationale": "SIMPLIFY: a correct impl with a different executable shape "
                     "(direct return, no accumulate loop) must still verify; C1 "
                     "`out = deferredOf entries` holds definitionally and C2 is the "
                     "frozen genuineness lemma. Else SPEC-TOO-STRONG. "
                     "(Sibling: pos-direct-return.)",
    },
    {
        "id": "pos-branch-both-defer",
        "kind": "soundness",
        "expect": "verify",
        # A genuine control-flow reshape: split on the mapping's emptiness, but
        # BOTH branches produce the full deferred mapping, so C1 holds on every
        # path. (Branch-reorder, both arms correct — not a loop-direction flip.)
        "module": _with_impl_and_proof(
            "    if entries.length > 0 then\n"
            "      return deferredOf entries\n"
            "    else\n"
            "      return deferredOf entries",
            "prove_correct deferMapping by\n  loom_solve",
        ),
        "rationale": "a structurally-different (branched) impl in which EVERY path "
                     "produces the full deferred mapping must verify; both arms "
                     "satisfy C1 `out = deferredOf entries`. Else SPEC-TOO-STRONG. "
                     "(Sibling: pos-branch-both-resolvable.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has a trivially-true precondition (no `require`),
    # so no normal input is excluded. The residual risk is that the genuineness
    # guarantee is DEGENERATE at the F2P-shaped point. This case discharges an
    # in-region assert (auto-solved by loom_solve, checked out-of-band) that at a
    # concrete F2P-shaped value — a str payload deferred and asked by a consumer
    # dispatching on the value's OWN runtime type — the deferred value genuinely
    # coerces to the underlying value (never a passthrough). The frozen impl and
    # proof are kept verbatim, so C1/C2 still discharge.
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_START,
            _IMPL_START +
            "    assert (with_name_prefix `adm\n"
            "      (coerce (deferOne { tag := 1, content := ['R','e','n','e'] }) 1\n"
            "        = Coerced.genuine { tag := 1, content := ['R','e','n','e'] }))\n",
        ),
        "rationale": "the (trivial) precondition admits an F2P-shaped input (a str "
                     "payload, its own runtime type as target); the in-region assert "
                     "must discharge (else the genuineness guarantee would be "
                     "degenerate at the point that matters / PRECOND-TOO-STRONG), "
                     "and the frozen impl+proof are kept verbatim so C1/C2 still "
                     "discharge. (Sibling: admiss-concrete-input.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each is a STRAIGHT-LINE (`List.map`) impl so its extracted
    # tester reduces under `decide`, refuted at a concrete input by a witness that
    # ELABORATES against the rival and FAILS against the frozen loop-solution. Each
    # carries the refinement argument for why its faithful real counterpart would
    # NOT resolve the failing test. Together they attack all three facets of C1.
    # =====================================================================
    {
        "id": "weak-masquerade",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack — the pre-image behaviour: each value is deferred by a
        # wrapper that MASQUERADES as the value's own runtime type
        # (`reported := some tag`) instead of the distinct proxy type
        # (`reported := none`). Forces to the value (right payload) but is not
        # genuinely coercible by a type-dispatching consumer.
        "module": _with_impl(
            "    return entries.map (fun p => (p.fst, "
            "{ forced := p.snd, reported := some p.snd.tag }))"
        ),
        "refinement": "this IS the pre-patch wrapping: the deferred value's "
                      "advertised runtime type equals the wrapped value's own type, "
                      "so a downstream consumer that dispatches on runtime type "
                      "believes it already holds a genuine value and hands the "
                      "wrapper itself through unchanged; the wrapper (not a genuine "
                      "value) then reaches the parameter binder and raises the "
                      "regression error, so the filtering test FAILS — it would NOT "
                      "resolve the F2P.",
        "rationale": "REJECT from C1 `out = deferredOf entries`: `deferredOf` builds "
                     "each wrapper with `reported = none`, but the rival's wrappers "
                     "carry `reported = some tag ≠ none`, so `out ≠ deferredOf "
                     "entries`. If it VERIFIED the spec would admit the pre-patch bug "
                     "=> SPEC-TOO-WEAK. Attacks the `reported` (genuine-vs-masquerade) "
                     "facet of C1. Refuted at a single-entry str-payload mapping "
                     "(where the pre-patch crash actually occurs). (Siblings: "
                     "weak-opaque-wrapping, weak-bare-wrapped — both collapse to this "
                     "masquerade on this carrier.)",
        "witness": _witness(
            "deferMappingTester [(1, { tag := 1, content := ['a'] })]"
        ),
    },
    {
        "id": "weak-wrong-forced",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on the payload facet: defer each value with the DISTINCT proxy
        # type (reported = none, genuinely coercible), but to a wrapper that forces
        # to a DIFFERENT payload (an extra code point appended). Genuine, but the
        # forced value is wrong.
        "module": _with_impl(
            "    return entries.map (fun p => (p.fst, "
            "deferOne { tag := p.snd.tag, content := p.snd.content ++ ['?'] }))"
        ),
        "refinement": "a wrapper that forces to a DIFFERENT payload does not "
                      "faithfully stand in for the original URL kwarg; the resolved "
                      "context value differs from the value the view was given, so "
                      "the lookup keyed on the original value fails and the filtering "
                      "test FAILS — it would NOT resolve.",
        "rationale": "REJECT from C1: the rival's wrappers are genuinely coercible "
                     "(`reported = none`) but their `forced` payload is "
                     "`content ++ ['?'] ≠ content`, so `out ≠ deferredOf entries`. "
                     "Attacks the `forced`-payload facet of C1 (a facet the "
                     "masquerade rival, which forces correctly, does not test). If it "
                     "VERIFIED => SPEC-TOO-WEAK. Refuted at its own distinguishing "
                     "point (a two-char payload). (Sibling: weak-wrong-forced-value.)",
        "witness": _witness(
            "deferMappingTester [(2, { tag := 3, content := ['a','b'] })]"
        ),
    },
    {
        "id": "weak-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: correct (genuine defer) only on the value-tag == 1
        # sub-domain, masquerading elsewhere. Verifies on part of the input space
        # and is wrong on the rest.
        "module": _with_impl(
            "    return entries.map (fun p => (p.fst, "
            "if p.snd.tag = 1 then deferOne p.snd "
            "else { forced := p.snd, reported := some p.snd.tag }))"
        ),
        "refinement": "a patch that produces the genuinely-coercible wrapper for "
                      "some value-types and the masquerading stand-in for the rest "
                      "leaves the F2P value (a str, whose runtime type is NOT the "
                      "privileged sub-domain) wrapped as a masquerade; the consumer "
                      "hands it through unchanged and the filtering test still "
                      "crashes — it would NOT resolve.",
        "rationale": "REJECT from C1 on the tag≠1 sub-domain: there the rival's "
                     "wrapper carries `reported = some tag ≠ none`, so `out ≠ "
                     "deferredOf entries`. If it VERIFIED the spec would admit an "
                     "impl fixing only part of the input domain => SPEC-TOO-WEAK. "
                     "Refuted at a tag=2 entry (in the wrong sub-domain), a DISTINCT "
                     "point from the masquerade rival. (Sibling: weak-partial-domain.)",
        "witness": _witness(
            "deferMappingTester [(7, { tag := 2, content := ['c'] })]"
        ),
    },
    {
        "id": "weak-key-mangled",
        "kind": "uniqueness",
        "expect": "reject",
        # CARRIER-WIDENING rival (no nagini sibling — nagini models a single value,
        # not a key→value mapping). Each value is deferred FAITHFULLY (genuine,
        # right payload) but re-keyed (key + 1), attacking C1's key-preservation
        # facet, which the wider carrier here models and the nagini surface cannot.
        "module": _with_impl(
            "    return entries.map (fun p => (p.fst + 1, deferOne p.snd))"
        ),
        "refinement": "carrying each entry under a DIFFERENT key means the deferred "
                      "value lands in the context under a name the view never looks "
                      "up; the URL-capture kwarg is then absent from the context and "
                      "the view raises before any binding — the filtering test FAILS, "
                      "it would NOT resolve.",
        "rationale": "REJECT from C1 `out = deferredOf entries`: `deferredOf` "
                     "preserves each key `p.fst`, but the rival emits `p.fst + 1`, so "
                     "`out ≠ deferredOf entries`. Attacks the KEY-preservation facet "
                     "of C1 — surface this bundle's wider carrier models that the "
                     "nagini single-value surface has no counterpart for. If it "
                     "VERIFIED => SPEC-TOO-WEAK. Refuted at a key=5 entry (a fourth "
                     "distinct input point). (No sibling: carrier-widening ADD.)",
        "witness": _witness(
            "deferMappingTester [(5, { tag := 1, content := ['a'] })]"
        ),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus a 2-probe AXIOM lane and
# an honestly-omitted frame-mutation class. This bundle models a NARROWER core
# behaviour in one dimension (the purely functional per-entry deferral) and a
# WIDER carrier in another (a key→value mapping, not a single value tag). The
# accounting records every sibling case.
#
#   sibling case (nagini)          -> here
#   ---------------------------------------------------------------------
#   pos-direct-return              -> pos-direct-map            PORTED
#   pos-branch-both-resolvable     -> pos-branch-both-defer     PORTED
#   admiss-concrete-input          -> admiss-f2p-ground         RE-EXPRESSED
#   weak-bare-wrapped              -> weak-masquerade           COLLAPSED (see below)
#   weak-opaque-wrapping           -> weak-masquerade           COLLAPSED (see below)
#   weak-launder-capability        -> (none)                    N/A on carrier
#   weak-partial-domain            -> weak-partial-domain       PORTED
#   weak-wrong-forced-value        -> weak-wrong-forced         PORTED
#   (new, no sibling)              -> weak-key-mangled          ADDED (carrier-widen)
#   AXIOM_TESTS (2 probes)         -> (none)                    DROPPED (G-AX)
#
# COLLAPSED (weak-bare-wrapped + weak-opaque-wrapping -> weak-masquerade): both
#   nagini rivals satisfy the value facet (forces to the value) while failing the
#   capability facet — one via a bare constructor, one via the pre-patch opaque
#   wrapping. On this carrier the capability facet is modeled STRUCTURALLY by
#   `reported`: a wrapper that forces correctly but is not genuinely coercible is
#   exactly `reported = some tag` (masquerade). The two nagini impls therefore map
#   to the SAME rival here; shipping both would be two witnesses for one refutation.
#   Kept as one (weak-masquerade), which is the exact pre-patch bug (SimpleLazyObject
#   masquerading as the wrapped type).
# N/A (weak-launder-capability): nagini's capability laundering exploits that
#   `binder_castable` is a first-class abstract predicate whose IDENTITY can be
#   obtained for one wrapper and pointed at another. Here genuineness is a
#   field-computed structural property (`reported = none`), not an obtainable
#   object — there is nothing to launder. The abstraction collapses the distinction
#   the rival needs, so it is not expressible on this carrier. Omitted with reason
#   (not fabricated).
# ADDED (weak-key-mangled): the velvet carrier is WIDER than nagini's — a key→value
#   mapping, not a single `value: int`. C1 pins key-preservation, a facet nagini has
#   no surface for. The added rival re-keys each faithful wrapper, attacking exactly
#   that facet and giving a fourth distinct witness point.
# FRAME-MUTATION: vacuous, exactly as the nagini sibling reports it — the nagini
#   `value: int` is a pure immutable value-tag with no `Acc(...)`, so the class is
#   already N/A there; here it is doubly so (referential transparency, no `mut`).
#
# CLAUSE COVERAGE. C1 (`out = deferredOf entries`) is attacked on all three of its
#   facets — `reported`/genuine (weak-masquerade, weak-partial-domain), `forced`
#   payload (weak-wrong-forced), and key preservation (weak-key-mangled) — and
#   defended by both soundness positives. C2 (`∀ v, coerce (deferOne v) v.tag =
#   genuine v`) is IMPL-INDEPENDENT: it mentions neither `out` nor `entries` and is
#   the frozen `coerce_deferOne` lemma, true for every impl, so it has NO falsifier
#   by construction and is defended (not attacked) — recorded here so its lack of a
#   rival is not misread as a gap. The C1 ORDER facet is pinned by the spec but is
#   NOT F2P-load-bearing (a dict reordering does not change key-lookup, so a
#   reordering patch would still resolve); a reordering rival would therefore be a
#   spurious verify-does-imply-resolve case, so it is deliberately NOT shipped.
#
#   The four reject witnesses probe four DISTINCT input tuples: keys {1,2,7,5},
#   value tags {1,3,2}, content lengths {1,2,1,1}. pts=4. Each witness was SEEN to
#   discriminate: it ELABORATES against the rival (straight-line `List.map` tester
#   reduces under `decide`) and FAILS against the frozen loop-solution (whose
#   extracted program does not kernel-reduce), the required two-build check. The
#   witnesses supply C2's Decidable instance as `isTrue (fun v => coerce_deferOne v
#   v.tag)` (the frozen lemma) because C2 is a `∀`-tautology the tester cannot
#   auto-decide — no assumption is added, so the binders are trivially consistent.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no axiom
# (mapping.md §3: the callee-swap is modeled directly by `Wrapper.reported` +
# `coerce`, not behind a contract over an unchanged callee), so there is nothing to
# probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
