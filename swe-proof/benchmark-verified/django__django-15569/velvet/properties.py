"""properties.py — G-PBT falsification battery for django__django-15569 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct removeBinding`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method that removes a named binding from a
registry while keeping a derived, cached read-through view consistent with it:

  removeBinding (mut registry : List (String × Nat))
                (mut cached   : List (String × Nat))
                (inherited    : List (String × Nat))
                (name         : String) return (u : Unit)
    require hasKey registry name = true
    ensures registry = eraseKey registryOld name                 -- (C1)
    ensures cached   = recomputeLookups inherited registry        -- (C2)

The registry is the owned-binding store; the cached view exposes those bindings
overlaid on the inherited ones (the registry's own bindings winning) and is what
callers consult. Two independent load-bearing clauses:

  (C1) the registry's post-state is pinned EXACTLY to ``eraseKey registryOld
       name`` — this single equation carries BOTH facts the sibling split into
       two clauses: the named binding is dropped AND every OTHER binding is left
       untouched (the store frame). A rival that under-erases (leaves ``name``),
       over-erases (drops another key), or does nothing all diverge from C1.
  (C2) the cached view's post-state is pinned EXACTLY to ``recomputeLookups
       inherited registry`` — the re-derivation from the NOW-CURRENT registry.
       This is the DISCRIMINATING clause: the derived view must be re-synced
       after the store mutates, so a subsequent consultation no longer exposes
       the removed name (unless it is independently inherited). Pre-change the
       store was mutated but the derived view was left stale, which C2 rejects.
       Again this equation carries both the removal-is-reflected fact AND the
       view frame (other names, and inherited bindings, resolve exactly as the
       recompute dictates).

C2 IS A LIST EQUATION, NOT A MAPPING EQUATION (audited, machine-checked). The
carrier is `List (String × Nat)` and mapping.md §2 declares the bijection to the
real mapping type to be order-INSENSITIVE ("equality is as a key→value mapping"),
but `=` on the carrier is list equality, so C2 additionally pins the ORDER of the
view. A correct impl that produces the same mapping in another order — e.g.
`(recomputeLookups inherited registry).reverse` — is therefore rejected. Measured:
that variant fails with `⊢ (recomputeLookups …).reverse = recomputeLookups …`
unsolved, while `lookupKey` agrees on every key and the lengths match, so it is
faithful under the DECLARED bijection. No positive control asserts this, and the
audit did not ship one as expect="verify" (the frozen proof does not close it and
inventing a proof for a reshape the spec genuinely rejects would misreport the
result). This is a residual SPEC-TOO-STRONG concern recorded against the frozen
spec, not a defect in the battery; escalated in the audit payload rather than
patched here, because narrowing C2 to mapping equality is a SPEC change that must
re-clear the equivalence and leakage gates outside this lane. It is not a
verify-does-not-resolve break (it only makes the spec reject some correct impls,
never accept a wrong one), so nothing about the shipped guarantee is weakened.

WRITE-ORDER IS LOAD-BEARING HERE (a divergence from the sibling carrier). The
sibling's two writes (delete from the store, invalidate the view) were
independent per-key assignments that COMMUTED, so its ``pos-reorder-writes``
positive simply swapped two assignment statements. On this carrier C2 pins
``cached`` to a function of the POST-state ``registry``, so a naive statement
swap (set ``cached`` from the still-unerased ``registry``, then erase) is
GENUINELY WRONG — it recomputes the view from the stale registry and leaves the
removed name exposed. The faithful reorder positive therefore derives the view
from ``eraseKey registry name`` EXPLICITLY before committing the registry write;
that reaches the identical final state and is the structurally-different correct
control. (Accounting footer, RE-SHAPED.)

ADVERSARIAL READ of the sibling classes on this carrier:
  * FRAME / PERMISSION-MUTATION — the sibling has NO ``Acc(.,1/2)`` read-only
    input (both dicts are full-permission because the operation legitimately
    writes them), so it carries no permission-mutation rival; it instead attacks
    the per-key ``Old()`` frame with rivals that disturb an unrelated name. On
    THIS carrier there is no heap, no fractional permission, and no ``Old``
    primitive — the frame is pinned structurally: C1/C2 equate the WHOLE
    post-state to a function of the inputs, so "disturb an unrelated name" is a
    direct C1/C2 violation (the post-state no longer equals the pinned value).
    Those attacks port intact as ``weak-frame-store-other-clobber`` (C1) and
    ``weak-frame-view-other-clobber`` (C2); there is no separate permission wall
    to subvert and none is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. C1/C2 pin the post-state to
    ``eraseKey``/``recomputeLookups`` applied to the method's OWN inputs (both
    transparent ``def``s over the carrier, the ``axioms`` region is empty), not
    to an opaque answer-key term. There is no oracle to echo; the cheapest
    honest correct impl computes the two post-states directly, which the
    positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: an impl can under-erase,
    over-erase, leave the view stale, drop a still-valid (inherited or sibling)
    binding from the view, or rebind the removed name to a bogus value. Each is
    refuted at a concrete input on the sub-domain where it diverges.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line a single ``return`` over immutable values,
    no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``removeBindingTester registry cached inherited name = false`` says the extracted
program's observable (the mutated ``registry`` and ``cached``) violates the
method's postcondition at that concrete input. Checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The carriers are ``List (String × Nat)`` with decidable equality and
every witness argument is a concrete literal, so ``decide`` reduces the extracted
(straight-line) program and every witness closes by ``decide``. Each witness
binds nothing (literal registry / cached / inherited / name), so there are no
hypotheses to be inconsistent — no consistency probe applies. Every witness was
checked with ``scripts/lean_verify.sh``: it ELABORATES against its rival (exit 0)
and FAILS against the frozen solution (``decide`` proves the ``= false`` goal
false — exit 1), the required discrimination.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The sibling declares no
``@ContractOnly`` axioms either; the single deep-model reference (the
view-recompute) is validated out-of-band by axiom_check.py / G-AX (an
A-reference over the real ``get_lookups()``), a separate gate from the G-PBT
axiom lane, which this gate ignores regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15569"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, everything strictly
# ---- between the method's `-- impl-start` / `-- impl-end`. Every variant
# ---- replaces exactly this text, so each edit lies wholly inside the one impl
# ---- region and same_spec holds by construction (both facts asserted at load
# ---- by _swap).
_GOLD_IMPL = (
    "    registry := eraseKey registry name\n"
    "    cached := recomputeLookups inherited registry\n"
    "    return\n"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# ---- the frozen proof body (tactic script only; elided from the spec view).
# ---- The admissibility case, which adds an in-region assert, retunes ONLY this
# ---- block (a decide arm to clear the assert goal) without touching the spec or
# ---- dropping the `prove_correct removeBinding` obligation.
_PROOF = "prove_correct removeBinding by\n  loom_solve\n"
assert _BASE.count(_PROOF) == 1, "proof region drifted; update _PROOF"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. The
# ---- method returns `Unit` and takes two mutable carriers `registry` / `cached`
# ---- plus the read-only `inherited` and `name`, so the tester takes all four
# ---- and reports whether the resulting observable satisfies the postcondition.
def _tester(body):
    return ("extract_program_for removeBinding\n"
            "prove_precondition_decidable_for removeBinding\n"
            "prove_postcondition_decidable_for removeBinding\n"
            "derive_tester_for removeBinding\n\n" + body)


def _L(pairs):
    """A concrete `List (String × Nat)` literal for a witness input point."""
    return "[" + ", ".join(f'("{k}", {v})' for k, v in pairs) + "]"


def _witness(registry, cached, inherited, name):
    return _tester(
        f'example : removeBindingTester {_L(registry)} {_L(cached)} '
        f'{_L(inherited)} "{name}" = false := by\n  decide\n')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-reorder-derive-first",
        "kind": "soundness",
        "expect": "verify",
        # Faithful reorder: derive the view from the ERASED registry explicitly,
        # THEN commit the registry write. Reaches the identical final state as the
        # frozen body but in the opposite statement order. This is the carrier's
        # faithful analogue of the sibling's pos-reorder-writes — a NAIVE swap
        # (set cached from the still-unerased registry, then erase) would be
        # WRONG here because C2 pins cached to a function of the POST-state
        # registry, so the reorder must recompute from `eraseKey registry name`.
        # The value flow is unchanged, so the frozen proof closes as-is.
        "module": _impl(
            "    cached := recomputeLookups inherited (eraseKey registry name)\n"
            "    registry := eraseKey registry name\n"
            "    return\n"),
        "rationale": (
            "structurally different CORRECT impl: derive the cached view from the "
            "already-erased registry (`eraseKey registry name`) and only then "
            "commit the registry write. Reaches the identical final state, so both "
            "C1 (`registry = eraseKey registryOld name`) and C2 (`cached = "
            "recomputeLookups inherited registry`) discharge and the frozen proof "
            "closes unchanged. Ports the sibling pos-reorder-writes, RE-SHAPED "
            "because C2 depends on the post-state registry (a naive statement swap "
            "would be wrong here). If it fails => SPEC-TOO-STRONG (over-fit to the "
            "erase-then-recompute statement order)."),
    },
    {
        "id": "pos-local-temp",
        "kind": "soundness",
        "expect": "verify",
        # Bind the erased registry to a typed local `r` first, then assign both
        # the registry and the recomputed view from it. A different executable
        # shape, observably identical result; the frozen proof closes as-is.
        "module": _impl(
            "    let r := eraseKey registry name\n"
            "    registry := r\n"
            "    cached := recomputeLookups inherited r\n"
            "    return\n"),
        "rationale": (
            "a correct impl that computes the erased registry once into a typed "
            "local `r` and assigns both the registry and the recomputed view from "
            "it is observably identical to gold (`r = eraseKey registryOld name`, "
            "so C1 and C2 both discharge); the frozen proof closes as-is. Ports "
            "the sibling pos-local-temp; if it fails => SPEC-TOO-STRONG (over-fit "
            "to a trivial local reshape)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries a `require hasKey registry name = true`,
    # so the sibling's precondition-admissibility probe (a normal F2P-shaped
    # input satisfies the Requires) HAS a counterpart here. Expressed as an
    # in-region `assert`, at a concrete F2P-shaped input, that the precondition
    # holds AND the post-image is non-degenerate (the removal is observable): the
    # name is bound (`hasKey … = true`), erasing it empties the singleton
    # registry, and recomputing the view over empty inherited no longer exposes
    # it. The surrounding impl is kept verbatim so the method's own obligation
    # still discharges; the proof gains a `decide | rfl` arm to clear the assert.
    # The sibling used a nested/top-level caller to discharge the precondition;
    # that is infeasible here (spec_view elides only the impl/proof regions), so
    # the concrete in-region witness is the faithful expressible form.
    # =====================================================================
    {
        "id": "admiss-precond-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  '      hasKey [("exactly", 7)] "exactly" = true ∧\n'
                  '      eraseKey [("exactly", 7)] "exactly" = [] ∧\n'
                  '      recomputeLookups [] (eraseKey [("exactly", 7)] "exactly") = []))\n'),
            _PROOF,
            "prove_correct removeBinding by\n  loom_solve <;> first | decide | rfl\n"),
        "rationale": (
            "the precondition `hasKey registry name = true` is SATISFIABLE by a "
            "concrete F2P-shaped input (name `exactly` bound to a registry), and "
            "the post-image is non-degenerate there: erasing it empties the "
            "singleton registry (C1) and recomputing the view over empty inherited "
            "no longer exposes the name (C2). The in-region assert must discharge "
            "(else the precondition is over-constrained / the obligation "
            "degenerate); the impl is kept verbatim so `registry = eraseKey … ∧ "
            "cached = recomputeLookups …` still verifies. Ports the sibling "
            "admiss-caller-in-region as an in-region concrete witness (a "
            "nested/top-level caller is infeasible on this carrier). Else "
            "PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. The witnesses vary
    # `registry`, `cached` (pre-state), `inherited`, and `name` so no binder is
    # pinned across the battery.
    # =====================================================================
    {
        "id": "weak-store-only-viewblind",
        "kind": "uniqueness",
        "expect": "reject",
        # The canonical discriminator: the pre-change view-blind removal — update
        # the registry, leave the derived view stale. Correct on C1; violates C2.
        "module": _impl(
            "    registry := eraseKey registry name\n"
            "    return\n"),
        "refinement": (
            "this is the pre-change behaviour: the owned-binding store is mutated "
            "but the derived, cached read-through view is left stale (the missing "
            "re-sync the fix adds). Its faithful counterpart is the unpatched "
            "repo; on the next consultation the stale cached view STILL exposes "
            "the removed name, so the failing test's assertion that the removed "
            "name is no longer among the exposed lookups FAILS. It is the exact "
            "defect the fix corrects and would NOT resolve."),
        "rationale": (
            "REJECT from clause (C2) `cached = recomputeLookups inherited "
            "registry`: the body never re-syncs `cached`, so it keeps its stale "
            "pre-value while the post-image demands the re-derived view. C1 is "
            "kept correct, isolating C2. Refuted at registry=cached=[(exactly,7)], "
            "inherited=[], name=exactly (the stale cached still exposes `exactly`). "
            "The load-bearing discriminator of the whole bundle. If it verified => "
            "SPEC-TOO-WEAK (admits the bug)."),
        "witness": _witness([("exactly", 7)], [("exactly", 7)], [], "exactly"),
    },
    {
        "id": "weak-view-only-no-delete",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror omission: re-sync the view but forget to erase from the registry.
        # Because C2's view is recomputed from the (un-erased) registry, the view
        # still exposes the name too — but the DIRECT violation is C1 (the
        # registry still binds the removed name).
        "module": _impl(
            "    cached := recomputeLookups inherited registry\n"
            "    return\n"),
        "refinement": (
            "faithful counterpart: a removal that re-syncs the cached view but "
            "never drops the binding from the owned store. The store still "
            "registers the name, so the re-derived view recomputes it straight "
            "back and STILL exposes it — the failing test's assertion that the "
            "removed name is gone FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from clause (C1) `registry = eraseKey registryOld name`: the "
            "body leaves the registry unchanged, so it still binds the removed "
            "name where the post-image demands it be erased. Refuted at "
            "registry=cached=[(gt,3)], inherited=[], name=gt. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness([("gt", 3)], [("gt", 3)], [], "gt"),
    },
    {
        "id": "weak-noop",
        "kind": "uniqueness",
        "expect": "reject",
        # NO-OP: does nothing. Pins that the spec is not vacuously satisfiable.
        # Violates C1 (registry unchanged, still binds the name).
        "module": _impl(
            "    return\n"),
        "refinement": (
            "faithful counterpart: a removal that returns without touching the "
            "store or the cached view. The name stays bound and exposed, so both "
            "failing-test assertions fail outright. Does NOT resolve."),
        "rationale": (
            "REJECT: the spec is not vacuously satisfiable; a no-op leaves the "
            "registry unchanged, violating C1 (`registry = eraseKey registryOld "
            "name` demands the name be erased) — and C2 as well. Refuted at "
            "registry=[(lt,5)], cached=[], inherited=[], name=lt: the un-erased "
            "registry still binds `lt`. Ports the sibling weak-noop. If it "
            "verified => SPEC-TOO-WEAK."),
        "witness": _witness([("lt", 5)], [], [], "lt"),
    },
    {
        "id": "weak-frame-store-other-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME attack on the store: correct erase + re-sync, BUT also erase an
        # UNRELATED name from the registry. Violates C1's frame half (an unrelated
        # binding was disturbed, so registry != eraseKey registryOld name).
        "module": _impl(
            "    registry := eraseKey registry name\n"
            '    registry := eraseKey registry "other"\n'
            "    cached := recomputeLookups inherited registry\n"
            "    return\n"),
        "refinement": (
            "faithful counterpart: a removal that, besides the requested name, "
            "also drops a still-registered UNRELATED binding from the store. Any "
            "read of that other name no longer resolves — it changes behaviour for "
            "a lookup the operation must leave intact, so the pass-to-pass suite "
            "(which registers and uses many lookups) would break. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from clause (C1) `registry = eraseKey registryOld name`: this "
            "equation pins the ENTIRE registry post-state, so dropping an "
            "unrelated key makes `registry` differ from `eraseKey registryOld "
            "name` (the store frame is violated). Refuted at "
            "registry=[(exactly,7),(other,9)], cached=[], inherited=[], "
            "name=exactly: gold leaves `other` bound, the rival drops it. Ports "
            "the sibling weak-frame-store-other-clobber. If it verified => "
            "SPEC-TOO-WEAK (the store frame unpinned)."),
        "witness": _witness([("exactly", 7), ("other", 9)], [], [], "exactly"),
    },
    {
        "id": "weak-frame-view-other-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME attack on the view: correct erase + re-sync, BUT then drop an
        # UNRELATED (here inherited-derived) name from the cached view. Violates
        # C2's frame half (the view no longer equals the recompute).
        "module": _impl(
            "    registry := eraseKey registry name\n"
            '    cached := eraseKey (recomputeLookups inherited registry) "other"\n'
            "    return\n"),
        "refinement": (
            "faithful counterpart: a removal whose cache handling drops a "
            "DIFFERENT name's resolution from the derived view (an over-broad "
            "eviction). A read of that other name — here contributed by the "
            "inherited bindings — stops resolving on the next consultation, so the "
            "view no longer reflects the bindings it must expose; the pass-to-pass "
            "lookup suite breaks. Does NOT resolve."),
        "rationale": (
            "REJECT from clause (C2) `cached = recomputeLookups inherited "
            "registry`: this equation pins the ENTIRE view post-state, so dropping "
            "an unrelated (inherited-derived) name makes `cached` differ from the "
            "recompute (the view frame is violated). Refuted at "
            "registry=[(exactly,7)], cached=[], inherited=[(other,9)], "
            "name=exactly: gold's view exposes the inherited `other`, the rival "
            "drops it — and this is the ONLY witness exercising a non-empty "
            "`inherited` among the SIX PORTED rivals, demonstrating that binder is "
            "load-bearing (the view must surface inherited bindings); the two "
            "audit-added shadowing rivals also use a non-empty `inherited`, and "
            "note that at THIS witness point the removed name is NOT inherited, "
            "which is why the shadowing sub-domain needed its own cases. Ports the "
            "sibling "
            "weak-frame-view-other-clobber. If it verified => SPEC-TOO-WEAK (the "
            "view frame unpinned)."),
        "witness": _witness([("exactly", 7)], [], [("other", 9)], "exactly"),
    },
    {
        "id": "weak-view-bogus-value",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL / WRONG-VALUE: erase from the registry but rebind the removed
        # name in the cached view to a bogus entry, so the removed name still
        # resolves (to the wrong value). Violates C2 with a value provably !=
        # the recompute — a sharper miss than leaving the whole view stale.
        "module": _impl(
            "    registry := eraseKey registry name\n"
            "    cached := (name, 1) :: recomputeLookups inherited registry\n"
            "    return\n"),
        "refinement": (
            "faithful counterpart: a removal that, instead of re-syncing the "
            "cached view cleanly, rebinds the removed name's memoised entry to "
            "some other value. A read of the removed name still resolves (to the "
            "wrong lookup), so the failing test's assertion that the removed name "
            "is no longer exposed FAILS. Does NOT resolve."),
        "rationale": (
            "REJECT from clause (C2) `cached = recomputeLookups inherited "
            "registry`: the view is prefixed with a bogus `(name, 1)` binding, so "
            "it exposes the removed name and differs from the recompute (which "
            "does not bind an erased, non-inherited name). Refuted at "
            "registry=[(range,2)], cached=[], inherited=[], name=range: gold's "
            "view is empty, the rival's exposes `range`. A distinct sub-domain "
            "from weak-store-only-viewblind (a wrong-VALUE re-sync, not a stale "
            "one). Ports the sibling weak-view-bogus-value. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _witness([("range", 2)], [], [], "range"),
    },

    # =====================================================================
    # SHADOWING SUB-DOMAIN (added by the independent audit). The six rivals
    # above all leave ONE sub-domain of C2 unattacked: the input where the
    # removed name is ALSO contributed by `inherited`, i.e. where the registry's
    # own binding SHADOWS an inherited one. There the spec says the removal must
    # expose the inherited binding underneath — the removed name keeps resolving,
    # to the inherited value — and nothing in the ported set forces that. Both
    # rivals below agree with gold on every witness point the ported six use and
    # diverge only here, so each attacks a genuinely new point.
    # =====================================================================
    {
        "id": "weak-view-over-erase-shadowed",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-erase on the VIEW: after re-deriving it correctly, also strike the
        # removed name out of the view. Indistinguishable from gold whenever the
        # name is not inherited (the recompute does not bind it anyway) — which is
        # every witness point the ported six use — but WRONG exactly on the
        # shadowing sub-domain, where the view must fall back to the inherited
        # binding rather than lose the name entirely.
        "module": _impl(
            "    registry := eraseKey registry name\n"
            "    cached := eraseKey (recomputeLookups inherited registry) name\n"
            "    return\n"),
        "refinement": (
            "faithful counterpart: a removal that drops the name from the store, "
            "re-derives the view, and then additionally strikes that name out of "
            "the derived view. When the name is independently contributed at an "
            "outer level, the derived view must fall back to that outer binding — "
            "the name must still resolve, to the outer value. This rival makes it "
            "resolve to nothing, so a subsequent consultation of the view loses a "
            "binding that is still legitimately in force; the pass-to-pass suite "
            "(which resolves names contributed at outer levels) breaks. Does NOT "
            "resolve."),
        "rationale": (
            "REJECT from clause (C2) `cached = recomputeLookups inherited "
            "registry`: `eraseKey … name` applied on top of the recompute removes "
            "a binding the recompute legitimately contains whenever `inherited` "
            "binds `name`, so the view differs from the pinned value. Refuted at "
            "registry=[(alpha,7)], cached=[], inherited=[(alpha,42)], name=alpha: "
            "gold's view is [(alpha,42)] (the inherited binding surfaces), the "
            "rival's is []. This is the ONLY case in the battery exercising the "
            "SHADOWING sub-domain (removed name also inherited) — the collision "
            "case mapping.md §3.1 fuzzes but that the ported six never reach, "
            "since each of their witnesses has the name absent from `inherited`. "
            "If it verified => SPEC-TOO-WEAK (C2 unpinned where the overlay must "
            "fall through)."),
        "witness": _witness([("alpha", 7)], [], [("alpha", 42)], "alpha"),
    },
    {
        "id": "weak-view-precedence-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # OVERLAY PRECEDENCE inverted: recompute the view with the two carriers
        # swapped, so the inherited bindings win over the registry's own instead
        # of the other way round. Collapses to gold when the two carriers share no
        # key (again, every ported witness point) and diverges on a collision.
        "module": _impl(
            "    registry := eraseKey registry name\n"
            "    cached := recomputeLookups registry inherited\n"
            "    return\n"),
        "refinement": (
            "faithful counterpart: a removal whose view re-derivation combines the "
            "two levels in the wrong precedence, letting an outer binding override "
            "the level's own instead of the reverse. Every name bound at BOTH "
            "levels then resolves to the outer value, so reads of those names "
            "regress to a stale answer the level deliberately overrode; the "
            "pass-to-pass suite breaks. Does NOT resolve."),
        "rationale": (
            "REJECT from clause (C2) `cached = recomputeLookups inherited "
            "registry`: the argument order is inverted, so the overlay resolves "
            "shared keys the wrong way (the outer level wins where the level's own "
            "binding must). Refuted at registry=[(alpha,7),(beta,1)], cached=[], "
            "inherited=[(beta,99)], name=alpha: gold's view binds beta to 1 (the "
            "registry's own wins), the rival's binds it to 99. Attacks the "
            "PRECEDENCE half of C2, which no ported rival touches — all six agree "
            "with gold on inputs where the carriers share no key. If it verified "
            "=> SPEC-TOO-WEAK (the overlay direction unpinned)."),
        "witness": _witness([("alpha", 7), ("beta", 1)], [], [("beta", 99)],
                            "alpha"),
    },

    # =====================================================================
    # ADMISSIBILITY, second form (added by the independent audit). The case
    # above asserts the precondition is satisfiable at a LITERAL input, which is
    # a fact about literals, not about the obligation's own hypothesis. This one
    # asserts a consequence of the INCOMING `require` on the ACTUAL arguments —
    # the nagini sibling's admiss-incoming-precond-noncontradictory, which the
    # port recorded as MERGED but did not in fact express. If the incoming
    # precondition were contradictory or failed to deliver what it claims, this
    # assert could not discharge from the hypothesis alone.
    # =====================================================================
    {
        "id": "admiss-incoming-precond-usable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `incoming (\n"
                  "      (lookupKey registry name).isSome = true))\n"),
            _PROOF,
            "prove_correct removeBinding by\n"
            "  loom_solve <;> first | simp_all [hasKey] | decide | rfl\n"),
        "rationale": (
            "the INCOMING precondition is non-contradictory AND usable on the "
            "method's own arguments: `require hasKey registry name = true` must "
            "yield `(lookupKey registry name).isSome = true` for the actual "
            "`registry`/`name` (not for a literal), which is what makes the "
            "erase well-defined. Discharged from the hypothesis alone, so it "
            "witnesses that the require delivers the fact the operation depends "
            "on. Complements admiss-precond-nondegenerate, whose assert is over "
            "LITERALS and therefore says nothing about the obligation's own "
            "hypothesis; expresses the sibling "
            "admiss-incoming-precond-noncontradictory that the accounting footer "
            "recorded as MERGED. The impl is kept verbatim so C1/C2 still "
            "discharge. Else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE."),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING.
#
# The sibling contracts one function (`remove_registration`) over two
# full-permission mutable dicts (the owned store and the lru_cache-memoised
# view) and pins FOUR clauses: store[name]==unregistered(), view[name]==
# unregistered(), and the two per-key Old() frame clauses. This bundle models the
# SAME operation over two `List (String × Nat)` carriers and pins TWO clauses,
# each an EQUATION on the whole post-state:
#   C1  registry = eraseKey registryOld name
#   C2  cached   = recomputeLookups inherited registry
# The sibling's clause (1) (store deletion) and (3) (store frame) both fold into
# C1; clause (2) (view invalidation) and (4) (view frame) both fold into C2 —
# equating the WHOLE post-state to a function of the inputs pins the removed key
# AND every untouched key at once. Every sibling SPEC case is accounted for.
#
#   nagini case                              -> here
#   ---------------------------------------------------------------------
#   pos-reorder-writes                       -> pos-reorder-derive-first   RE-SHAPED
#   pos-local-temp                           -> pos-local-temp             PORTED
#   admiss-incoming-precond-noncontradictory -> admiss-incoming-precond-usable PORTED
#                                               (was recorded MERGED; the audit
#                                                found the merge was not actually
#                                                expressed and landed it)
#   admiss-caller-in-region                  -> admiss-precond-nondegenerate PORTED
#   weak-store-only-viewblind                -> weak-store-only-viewblind  PORTED (C2)
#   weak-view-only-no-delete                 -> weak-view-only-no-delete   PORTED (C1)
#   weak-noop                                -> weak-noop                  PORTED (C1)
#   weak-frame-store-other-clobber           -> weak-frame-store-other-clobber PORTED (C1)
#   weak-frame-view-other-clobber            -> weak-frame-view-other-clobber PORTED (C2)
#   weak-view-bogus-value                    -> weak-view-bogus-value      PORTED (C2)
#   AXIOM_TESTS (none)                       -> (none)                     N/A (G-AX)
#   (no sibling counterpart)                 -> weak-view-over-erase-shadowed  ADDED
#   (no sibling counterpart)                 -> weak-view-precedence-inverted  ADDED
#
# 12 velvet SPEC cases: 2 soundness, 2 admissibility, 8 uniqueness.
#
# ADDED BY THE INDEPENDENT AUDIT (3 cases). The ported six uniqueness rivals share
#   a blind spot: every one of their witnesses picks an input where the removed
#   name is ABSENT from `inherited` and where the two carriers share no key. On
#   such inputs the overlay is degenerate (a plain concatenation), so neither the
#   FALL-THROUGH behaviour (a removal must expose an inherited binding underneath)
#   nor the PRECEDENCE of the overlay (the registry's own binding wins over an
#   inherited one) is forced by any case — although both are load-bearing content
#   of C2 and mapping.md §3.1 names the collision case as the one it fuzzes.
#   Closed by weak-view-over-erase-shadowed (fall-through) and
#   weak-view-precedence-inverted (precedence); each rival agrees with gold on all
#   six ported witness points and diverges only on the new sub-domain, so neither
#   duplicates an existing case. Both machine-checked: rival build exit 1
#   (rejected, unsolved C2 goal), witness ELABORATES against the rival (exit 0)
#   and FAILS on the frozen solution by `decide` PROVING the tester claim false
#   (exit 1) — a semantic refutation, not a name/type/unfolding error.
#   admiss-incoming-precond-usable closes the third gap: the accounting above used
#   to record the sibling's admiss-incoming-precond-noncontradictory as MERGED into
#   admiss-precond-nondegenerate, but that case's assert is over LITERAL carriers
#   and so is a fact about literals, not about the incoming `require` — the merge
#   was never expressed. The added case asserts the require's consequence on the
#   ACTUAL arguments, dischargeable from the hypothesis alone (build exit 0).
#   Integrity of the assert form was confirmed by a probe the battery does not
#   ship: the same case with a FALSE assert (`hasKey [("exactly",7)] "absent"`)
#   fails (exit 1, `rfl` failed on the assert goal), so these asserts are
#   load-bearing rather than decoration.
#
# RE-SHAPED (pos-reorder-writes -> pos-reorder-derive-first): the sibling's two
#   writes (store delete, view invalidate) were independent per-key assignments
#   that COMMUTED, so its reorder positive just swapped two statements. Here C2
#   pins `cached` to a function of the POST-state `registry`, so a naive
#   statement swap would recompute the view from the STALE registry and be
#   genuinely wrong. The faithful reorder derives the view from `eraseKey
#   registry name` EXPLICITLY, then commits the registry write — the identical
#   final state, a structurally-different correct control (real build, exit 0).
# PORTED (pos-local-temp): compute the erased registry once into a typed local
#   and assign both carriers from it. Carries across intact (real build, exit 0).
# PORTED, ONE PER SIBLING (admiss-caller-in-region -> admiss-precond-nondegenerate;
#   admiss-incoming-precond-noncontradictory -> admiss-incoming-precond-usable):
#   the sibling carried TWO admissibility cases — one asserting the incoming
#   precondition is non-contradictory, one building a concrete input and asserting
#   every Requires conjunct. An earlier revision of this footer claimed the two
#   folded into one case because the precondition here has a single conjunct; the
#   independent audit rejected that. The two cases assert different things and the
#   fold dropped one of them: admiss-precond-nondegenerate's assert is over LITERAL
#   carriers (`hasKey [("exactly",7)] "exactly"`), so it is a fact about literals
#   and is provable with no reference to the obligation's hypothesis at all,
#   whereas the sibling's incoming-precond case is about what the incoming
#   `require` DELIVERS on the actual arguments. Both are now shipped: the literal
#   case (concrete F2P input satisfies the precondition and the post-image is
#   non-degenerate) and admiss-incoming-precond-usable (the require's consequence
#   on the actual `registry`/`name`, discharged from the hypothesis alone). Both
#   real builds, exit 0. A nested/top-level caller remains infeasible (spec_view
#   elides only impl/proof), so the in-region assert is the expressible form.
# PORTED (the six uniqueness rivals): every sibling uniqueness rival attacks a
#   modeled clause and ports directly, only the carrier changing from a nagini
#   dict fold to a Velvet `List (String × Nat)` — now each backed by a
#   machine-checked witness. weak-store-only-viewblind (the pre-patch view-blind
#   removal, the load-bearing C2 discriminator), weak-view-only-no-delete (C1),
#   weak-noop (C1), weak-frame-store-other-clobber (C1 frame),
#   weak-frame-view-other-clobber (C2 frame), weak-view-bogus-value (C2 wrong
#   value). Each carries its sibling refinement argument (unpatched-repo /
#   store-still-registers / no-op / unrelated-name-disturbed / bogus-rebind all
#   fail an F2P or P2P assertion).
# FRAME / PERMISSION-MUTATION: the sibling has NO Acc(.,1/2) read-only input (both
#   dicts are full-permission) and so carries no permission-mutation rival; it
#   attacks the per-key Old() frame directly. That ports intact
#   (weak-frame-store-other-clobber / weak-frame-view-other-clobber): on this
#   referentially-transparent carrier C1/C2 equate the whole post-state to a
#   function of the inputs, so disturbing an unrelated name is a direct clause
#   violation. No separate permission wall exists and none is fabricated.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line a single ``return`` over immutable values,
#   no loop and no recursion), so there is no control flow here to make
#   diverge: a diverging rival cannot be obtained by mutating this body, it has
#   to bring a loop of its own. When it does, the semantics refuse it. This
#   bundle sets ``loom.semantics.termination "total"`` AND carries
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
# DROPPED (AXIOM_TESTS): the sibling declares no @ContractOnly axioms; the single
#   deep-model reference (the view-recompute == real get_lookups()) is validated
#   by axiom_check.py / G-AX (an A-reference), a separate gate the G-PBT lane
#   ignores. AXIOM_TESTS = [].
#
# CLAUSE / BINDER / POINT COVERAGE. Both independent top-level clauses are
#   attacked AND defended:
#     C1 (registry = eraseKey registryOld name)  attacked by weak-view-only-no-
#        delete, weak-noop, weak-frame-store-other-clobber; defended by both
#        positives + admissibility.
#     C2 (cached = recomputeLookups inherited registry) attacked by weak-store-
#        only-viewblind, weak-frame-view-other-clobber, weak-view-bogus-value,
#        weak-view-over-erase-shadowed (fall-through), weak-view-precedence-
#        inverted (overlay direction); defended by both positives + both
#        admissibility cases.
#   The input binders are `registry`, `cached` (pre-state), `inherited`, `name`.
#   Across the EIGHT reject witnesses (eight DISTINCT inputs):
#     name       varied over {exactly, gt, lt, range, alpha}  (no fixed value)
#     registry   varied: 1- and 2-element lists, distinct keys/values
#     cached     varied over {stale-nonempty [(exactly,7)]/[(gt,3)], empty}
#                — load-bearing: weak-store-only-viewblind leaves the stale value,
#                  gold overwrites it, so the pre-value of `cached` is probed.
#     inherited  varied over {[], [(other,9)], [(alpha,42)], [(beta,99)]}, and —
#                  the distinction that matters, not just the spelling — across
#                  the three ways the overlay can be non-degenerate: inherited
#                  disjoint from the registry (weak-frame-view-other-clobber, the
#                  view must SURFACE an inherited binding), inherited binding the
#                  REMOVED name (weak-view-over-erase-shadowed, the view must FALL
#                  THROUGH to it), and inherited COLLIDING with a retained
#                  registry key (weak-view-precedence-inverted, the registry's own
#                  binding must WIN). The ported six only ever used the first, and
#                  on their inputs the overlay degenerates to concatenation.
#   No binder is pinned at a single value across the reject set. Each witness
#   binds nothing (literal carriers + literal name), so no consistency probe
#   applies (verified: consistency_probe returns None for each). All EIGHT checked
#   with scripts/lean_verify.sh: each ELABORATES against its rival (exit 0) and
#   FAILS against the frozen solution (exit 1) with `decide` PROVING the tester
#   claim false — a semantic refutation in every case, checked against the build
#   log, not merely a non-zero exit. Both positives and both admissibility cases
#   build (exit 0), the positives under the frozen proof unchanged.
#
# AUDIT PROBES NOT SHIPPED (recorded so the next reader need not re-run them).
#   Each was built for real; none is a battery case.
#     naive statement swap (`cached` from the still-unerased registry, then
#       erase) — REJECTED (exit 1, unsolved C2 goal `recomputeLookups inherited
#       registryOld = recomputeLookups inherited (eraseKey registryOld name)`),
#       confirming the docstring's claim that the reorder positive had to be
#       re-shaped rather than swapped.
#     admissibility with a FALSE assert — REJECTED (exit 1, `rfl` failed on the
#       assert goal), confirming the shipped asserts are load-bearing.
#     guarded impl (`if hasKey … then <gold> else <gold>`) — VERIFIES (exit 0):
#       a branch-shaped correct reshape is accepted.
#     stale-then-correct double assignment of `cached` — VERIFIES (exit 0): the
#       spec judges the final state, as intended, not the write sequence.
#     order-permuted view (`.reverse` of the recompute) — REJECTED (exit 1). A
#       correct impl under the declared order-insensitive bijection; see the
#       "C2 IS A LIST EQUATION" note in the module docstring. Escalated as a
#       spec-strength observation, NOT patched here.
AXIOM_TESTS = []
