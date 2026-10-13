"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13439 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_len``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total query over one input carrier):

  len (self : CompSeq) : Option Nat
      result = some self.steps.length

A sequential composition is observed through its ordered list of steps. The
single modeled observable is the size the query reports for that composition.
The postcondition pins that size to the input's own step list: the result is
always a defined ``some n`` and ``n`` equals the number of steps the composition
holds. The size is carried in ``Option`` to record definedness — a defined size
is ``some n``, an undefined size is ``none`` — and for a composition it is always
defined. There is no free output component and no opaque oracle: the count is
grounded entirely in ``self.steps.length``, fully unfolded.

The postcondition is a SINGLE top-level clause with a SINGLE input binder
(``self``, read only through ``self.steps`` and its ``.length``). The
adversarial surface is therefore the value the query reports as a function of
the input's cardinality; the reject witnesses vary that cardinality across
``{0, 1, 2}`` so no rival can pass by getting one length right while mishandling
the rest.

ADVERSARIAL READ of the nagini classes on this carrier:

  * POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    implementation must still satisfy ``result = some self.steps.length``; if it
    cannot, the postcondition is SPEC-TOO-STRONG. Carried as an ACCUMULATING
    TRAVERSAL (walk the ordered step list with a mutable counter): the same
    observable value on every input, but NOT a term the kernel identifies with
    the frozen one — the frozen ``rfl`` body fails on it, so the obligation is
    genuinely re-established rather than re-accepted. (An earlier
    local-variable reshape was dropped in audit for exactly that reason: it was
    definitionally the frozen impl, closed by the frozen tactic body verbatim,
    and so could not have detected a SPEC-TOO-STRONG spec.)

  * ADMISSIBILITY — the nagini case re-derived IN-REGION that the read-only
    (half-permission) input was usable and reached a normal non-raising return.
    Lean is referentially transparent: the input is a plain immutable value and
    the frozen obligation carries NO precondition hypothesis (the query is
    total, ``∀`` unguarded), so there is no precondition binder to attack. The
    honest analogue confirms the obligation is SATISFIABLE at a normal,
    F2P-shaped input (a 2-step composition, exactly the cardinality the F2P
    exercises) by evaluation inside the proof region, alongside the frozen
    obligation. If that ground instance could not be discharged, the modeled
    behavior would be unsatisfiable at exactly the input the F2P demands.

  * PARTIAL-DOMAIN / under-count by one (uniqueness) — APPLIES, and is a
    load-bearing rival. Reporting one fewer than the step count (the
    truncated-traversal shape) violates ``result = some self.steps.length`` on
    every non-empty input; at the F2P 2-step composition it reports 1, and the
    F2P assertion demanding the count be 2 fails. NOTE (audit): this is NOT the
    prepatch leg on this carrier, despite the case id and the sibling backend's
    framing. The frozen prepatch leg reports an UNDEFINED size, so the rival that
    reproduces prepatch behavior here is ``undefined-size-never-defined``. The id
    is kept for cross-backend traceability; the refinement text records the
    correction.

  * PARTIAL-DOMAIN / constant at the F2P size (uniqueness) — APPLIES. Reporting
    the constant 2 is correct ONLY at the F2P cardinality and wrong at every
    other length; it violates the one clause on all lengths ≠ 2.

  * PARTIAL-DOMAIN / wrong only on the empty composition (uniqueness) — APPLIES,
    and isolates the empty sub-domain. Correct for every non-empty composition
    but reports 1 for the empty one, so ``result = some self.steps.length`` fails
    exactly where the step list is empty.

  * UNDEFINED SIZE (uniqueness) — APPLIES; added in audit. The ported rivals all
    attack the COUNT and none attacked the ``some``, so the definedness half of
    the clause was asserted by the prose and never demonstrated. A rival that
    reports ``none`` for every composition never reports a wrong number, and is
    rejected only because the clause pins definedness too.

  * CONTENT SENSITIVITY (uniqueness) — APPLIES; added in audit. Every ported
    rival is a function of the cardinality ALONE, so none of them probes the
    frame the spec view claims (a step's name/component is never inspected when
    counting). A rival that counts only the steps whose component is substantive
    is refuted at a 2-step composition holding one inert placeholder — the same
    length as the F2P witness, differing only in step CONTENT.

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY: the step list is held at a fractional
    (read-only) permission, so a rival that writes an element is rejected for
    insufficient permission before any value reasoning. Lean is referentially
    transparent: ``self`` is a plain immutable value, there is no half-permission
    to overwrite and no aliasing to exploit, so this class has NO expressible
    instance here. No substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against ``some self.steps.length``, built only from the input and fully
    unfolded. The bundle declares no ``opaque``/``axiom`` (the count is modeled
    directly as ``List.length``), so there is no answer key an implementation
    could echo without doing the work. The honest analogue is the
    cheapest-correct POSITIVE CONTROL above.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``rfl``) is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a ``decide``-able concrete input; each was checked (two
real builds) to HOLD of its rival and to FAIL on the frozen solution, so it
discriminates rather than asserting a tautology.

BINDER COVERAGE. The single input binder is the composition's step list. The
spec reads its cardinality; the frame claim is that it reads NOTHING ELSE off
it. The reject witnesses probe both axes — the cardinality, and (after the
audit) the step content at fixed cardinality:

  steps.length = 2  (under-count reports 1)      — the F2P-discriminating size
  steps.length = 1  (constant-2 reports 2)       — a non-F2P non-empty size
  steps.length = 0  (empty-off reports 1)        — the empty sub-domain
  steps.length = 2  (undefined size: `none`)     — the DEFINEDNESS half
  steps.length = 2, one inert step (reports 1)   — content-varying, length fixed

Spreading the cardinality across {0, 1, 2} is what attests that the reported
size must track the actual step count at every length, not just at the F2P
witness. The last two points are the ones a cardinality-only battery cannot
reach: one moves the result OUT of the `some` branch entirely, and one holds the
length at the F2P size while varying only what the steps contain, which is the
only way to demonstrate that the count does not depend on step content.

AXIOM lane: DROPPED. The nagini bundle records only the trivial refinement fact
that the real length equals the constructed stage count; there is no
``@ContractOnly`` axiom and no real callee whose contract must be validated. This
carrier consumes no ``opaque``/``axiom`` (the count is ``List.length``), so there
is no axiom-soundness obligation to probe here, and the axiom lane belongs to
G-AX in any case. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13439"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body (the single line after `Id.run do`) and the FULL
# frozen tactic body, so every replacement lands entirely inside the region it
# means to edit. The impl body `return some self.steps.length` is unique — the
# spec clause uses `result = some self.steps.length` (no `return`).
_IMPL_GOLD = "  return some self.steps.length"
_GOLD_PROOF = (
    "  intro self\n"
    "  unfold problem_spec_len implementation_len\n"
    "  rfl"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted; update _GOLD_PROOF"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_len` STATEMENT
    # is byte-identical.
    #
    # AUDIT REPAIR. The ported positive control bound the cardinality to a local
    # (`let n := self.steps.length; return some n`) and kept the frozen `rfl`
    # body. That reshape is DEFINITIONALLY the frozen impl — measured: the
    # frozen tactic body closes it verbatim, exit 0 — so it exercised no
    # soundness question at all: `rfl` closing means the elaborator saw the same
    # term. A positive control whose proof is the frozen proof, on a term the
    # kernel cannot distinguish from the frozen term, cannot detect a
    # SPEC-TOO-STRONG spec. Replaced by an ACCUMULATING TRAVERSAL: count the
    # steps by walking the list with a mutable counter. Measured to be
    # definitionally DISTINT from the frozen impl — the frozen `rfl` body FAILS
    # on it (`(forIn self.steps 0 …).run is not definitionally equal to
    # some self.steps.length`, exit 1) — so closing it requires the spec to
    # actually hold of a different computation, which is the soundness question
    # the case is supposed to ask. This is also the shape a real size query
    # would take if it counted the collection rather than asking for its length.
    # =====================================================================
    {
        "id": "pos-control-accumulating-traversal",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "  let mut n := 0\n"
                "  for _ in self.steps do\n"
                "    n := n + 1\n"
                "  return some n",
            ),
            # The tactic body MUST be re-derived: `variant_scope` requires the
            # theorem STATEMENT byte-identical but lets the body differ, which is
            # exactly the license a legitimate re-proof needs. `simp` discharges
            # the traversal's `forIn` accumulation against the spec's
            # `List.length`; no helper lemma, no new declaration, no assumption
            # token, and the obligation proven is the frozen one.
            _GOLD_PROOF,
            "  intro self\n"
            "  unfold problem_spec_len implementation_len\n"
            "  simp",
        ),
        "rationale": (
            "a structurally-different but CORRECT impl — count the steps by "
            "walking the ordered list with a mutable accumulator instead of "
            "asking the list for its cardinality directly — must still satisfy "
            "`result = some self.steps.length`; if it cannot, SPEC-TOO-STRONG. "
            "Unlike a local-variable rebinding, this reshape is NOT "
            "definitionally the frozen impl: the frozen `rfl` body fails on it "
            "(the `forIn` accumulation does not reduce to `self.steps.length` by "
            "definitional unfolding), so the obligation has to be re-established "
            "for the traversal's own value rather than re-accepted on a term the "
            "kernel already identifies with the frozen one. Source: soundness of "
            "the `result = some self.steps.length` clause under a "
            "value-equivalent but definitionally distinct reshape."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input rather than only provable in
    # the abstract. The frozen theorem carries NO precondition hypothesis (the
    # query is total, so `∀` is unguarded), so nagini's precondition-admission
    # probe has no binder to attack here; the honest analogue discharges the spec
    # predicate at the F2P ground input (a 2-step composition, the cardinality the
    # F2P exercises) inside the proof region, alongside the frozen obligation. If
    # that ground instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the input the F2P demands.
    # =====================================================================
    {
        "id": "admissibility-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_PROOF,
            "  intro self\n"
            "  have _ground : problem_spec_len { steps := [⟨\"a\",\"x\"⟩, ⟨\"b\",\"y\"⟩] }\n"
            "      (implementation_len { steps := [⟨\"a\",\"x\"⟩, ⟨\"b\",\"y\"⟩] }) := by\n"
            "    unfold problem_spec_len implementation_len\n"
            "    decide\n"
            "  unfold problem_spec_len implementation_len\n"
            "  rfl",
        ),
        "rationale": (
            "the obligation is discharged at the F2P-shaped ground input (a 2-step "
            "composition, where the reported size must be `some 2`) by `decide`, "
            "then the frozen obligation is closed verbatim. Verifies (else the spec "
            "is unsatisfiable at the normal input, the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "partial-domain-prepatch-undercount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "  return some (self.steps.length - 1)",
        ),
        "refinement": (
            "reporting one fewer than the step count mirrors reusing a truncated "
            "traversal that walks one fewer than the full step list. A faithful "
            "real patch of that shape reports 1 for the F2P 2-step composition, so "
            "the F2P assertion demanding the reported size be 2 FAILS; it also "
            "under-spans a self-indexing slice, dropping the terminal stage. It "
            "does NOT resolve. AUDIT CORRECTION: an earlier wording called this "
            "'the leg's prepatch behavior'. That is FALSE on this carrier and was "
            "carried over from the sibling backend, whose prepatch model really "
            "was the truncated count. Here the frozen prepatch leg reports an "
            "UNDEFINED size (`none`), which is the `undefined-size-never-defined` "
            "rival below — not this one. This case is an ordinary "
            "off-by-one partial-domain rival, load-bearing on its own merits "
            "(wrong on every non-empty input) but NOT the prepatch witness."
        ),
        "rationale": (
            "REJECT from `result = some self.steps.length`: this returns `some "
            "(self.steps.length - 1)`, violating the clause on every non-empty "
            "input. Refuted at the F2P-discriminating cardinality (a 2-step "
            "composition: the spec demands `some 2`, the rival yields `some 1`)."
        ),
        "witness": (
            "-- Refuted at the F2P 2-step composition: the reported size must be\n"
            "-- the full step count `some 2`, but an under-count yields `some 1`.\n"
            "example : ¬ problem_spec_len { steps := [⟨\"a\",\"x\"⟩, ⟨\"b\",\"y\"⟩] }\n"
            "    (implementation_len { steps := [⟨\"a\",\"x\"⟩, ⟨\"b\",\"y\"⟩] }) := by\n"
            "  unfold problem_spec_len implementation_len\n"
            "  decide\n"
        ),
    },
    {
        "id": "partial-domain-constant-f2p-size",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, "  return some 2"),
        "refinement": (
            "a faithful real patch returning the constant 2 passes the F2P "
            "assertion for the 2-step composition but is correct ONLY at that "
            "cardinality: a self-indexing slice over compositions of any other "
            "size relies on the reported count spanning the whole collection, so "
            "the pre-existing slice/index legs at other sizes break. It does NOT "
            "resolve — a constant is the canonical pins-only-part-of-the-domain "
            "rival."
        ),
        "rationale": (
            "REJECT from `result = some self.steps.length`: this returns the "
            "constant `some 2`, violating the clause on every input whose length "
            "≠ 2. Refuted at a singleton composition (length 1: the spec demands "
            "`some 1`, the rival yields `some 2`), a non-F2P non-empty length that "
            "moves the input cardinality off the F2P witness."
        ),
        "witness": (
            "-- Refuted at a singleton composition: the reported size must be\n"
            "-- `some 1`, but a constant-2 impl yields `some 2`.\n"
            "example : ¬ problem_spec_len { steps := [⟨\"a\",\"x\"⟩] }\n"
            "    (implementation_len { steps := [⟨\"a\",\"x\"⟩] }) := by\n"
            "  unfold problem_spec_len implementation_len\n"
            "  decide\n"
        ),
    },
    {
        "id": "partial-domain-empty-undercount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "  if self.steps.length == 0 then\n"
            "    return some 1\n"
            "  return some self.steps.length",
        ),
        "refinement": (
            "a faithful real patch that special-cased the empty composition to "
            "report size 1 (e.g. reporting the count-or-1) is correct for every "
            "non-empty composition but mis-reports the empty one, claiming one step "
            "where there are none; a self-indexing slice over the empty composition "
            "would over-span and index a non-existent stage. It diverges from the "
            "true count exactly on the empty sub-domain, so it does NOT resolve "
            "there."
        ),
        "rationale": (
            "REJECT from `result = some self.steps.length`: this returns `some 1` "
            "when the step list is empty (correct otherwise), violating the clause "
            "exactly on the empty sub-domain. Refuted at the empty composition "
            "(length 0: the spec demands `some 0`, the rival yields `some 1`), the "
            "smallest cardinality and the one neither other reject case probes."
        ),
        "witness": (
            "-- Refuted at the empty composition: the reported size must be\n"
            "-- `some 0`, but special-casing the empty case to 1 yields `some 1`.\n"
            "example : ¬ problem_spec_len { steps := [] }\n"
            "    (implementation_len { steps := [] }) := by\n"
            "  unfold problem_spec_len implementation_len\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # AUDIT ADDITION — the DEFINEDNESS half of the clause. Every ported rival
    # attacks the COUNT (`some k` for a wrong `k`) and none attacks the `some`
    # itself, so the battery never demonstrated that the spec forces the size to
    # be DEFINED at all. That half is load-bearing on this carrier: the result is
    # `Option Nat` precisely so an undefined size is expressible, and the clause
    # `result = some self.steps.length` pins definedness as well as the value. A
    # rival reporting an undefined size satisfies "never reports a wrong number"
    # while resolving nothing, and until this case existed the manifest's own
    # narrative ("the result is always a defined `some n`") was asserted rather
    # than demonstrated.
    # =====================================================================
    {
        "id": "undefined-size-never-defined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, "  return none"),
        "refinement": (
            "reporting NO size — leaving the size query undefined for every "
            "composition — is the behavior of the leg where the size query is "
            "simply not answerable on this kind of object at all. AUDIT NOTE: on "
            "this carrier THIS is the rival that reproduces the frozen prepatch "
            "leg's modeled behavior (an undefined size), which is why it is the "
            "load-bearing partial-domain rival and not merely a definedness "
            "curiosity; the off-by-one case above is an ordinary wrong-count "
            "rival. A faithful real "
            "patch of that shape reports no size for the F2P 2-step composition, "
            "so the F2P assertion demanding the reported size be 2 cannot even be "
            "evaluated, let alone hold; every self-indexing slice that spans "
            "'from the start up to the size' equally has no size to span to. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = some self.steps.length`: this returns `none`, "
            "violating the DEFINEDNESS half of the clause on every input — the "
            "half no other reject case probes, since the others all report a "
            "defined but wrong count. Refuted at the F2P 2-step composition "
            "(the spec demands `some 2`, the rival yields `none`, which is not "
            "`some` of anything)."
        ),
        "witness": (
            "-- Refuted at the F2P 2-step composition: the size must be DEFINED\n"
            "-- and equal to the step count (`some 2`); `none` is no size at all.\n"
            "example : ¬ problem_spec_len { steps := [⟨\"a\",\"x\"⟩, ⟨\"b\",\"y\"⟩] }\n"
            "    (implementation_len { steps := [⟨\"a\",\"x\"⟩, ⟨\"b\",\"y\"⟩] }) := by\n"
            "  unfold problem_spec_len implementation_len\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # AUDIT ADDITION — CONTENT INSENSITIVITY (the frame half of directive 5).
    # The spec view claims a step's `name`/`component` are "never inspected when
    # counting", and the three ported rivals are all functions of the CARDINALITY
    # alone — so every one of them could be refuted at a single step-content
    # profile, and none of them would notice a rival that counted only SOME of
    # the steps according to what they contain. This rival makes the count depend
    # on step content, and is refuted at a composition of the F2P cardinality:
    # two steps, one of them inert. That input point is what forces the reported
    # size to track the number of steps HELD rather than the number of steps
    # judged interesting, which is the claim the prose makes.
    # =====================================================================
    {
        "id": "content-sensitive-skips-inert-step",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "  return some (self.steps.filter (fun s => s.component != \"\")).length",
        ),
        "refinement": (
            "a faithful real patch that counted only the steps whose component is "
            "substantive — skipping inert placeholder steps — is correct for every "
            "composition that holds no placeholder, so it passes the plain F2P "
            "shape, but it under-reports for any composition built with a "
            "placeholder stage. Such compositions are ordinary: a placeholder is "
            "how a stage is held open while still occupying a position, and it "
            "still occupies an index. A slice spanning 'up to the size' would then "
            "drop real trailing stages. It does NOT resolve on that sub-domain."
        ),
        "rationale": (
            "REJECT from `result = some self.steps.length`: this counts only the "
            "steps whose `component` is non-empty, so the reported size depends on "
            "step CONTENT rather than on how many steps the composition holds — "
            "the frame the spec pins (the count is a function of the step list "
            "alone). Refuted at a 2-step composition whose second step is an inert "
            "placeholder (the spec demands `some 2` because two steps are held; "
            "the rival yields `some 1`). This is a content-varying input point "
            "that no cardinality-only rival can reach: it holds the length fixed "
            "at the F2P size and varies only what the steps contain."
        ),
        "witness": (
            "-- Refuted at a 2-step composition holding one inert placeholder\n"
            "-- step: the size counts steps HELD (`some 2`), not steps judged\n"
            "-- substantive, so skipping the placeholder's yield of `some 1` is wrong.\n"
            "example : ¬ problem_spec_len { steps := [⟨\"a\",\"x\"⟩, ⟨\"b\",\"\"⟩] }\n"
            "    (implementation_len { steps := [⟨\"a\",\"x\"⟩, ⟨\"b\",\"\"⟩] }) := by\n"
            "  unfold problem_spec_len implementation_len\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the size is `List.length` over
# the input's own step list, modeled directly, so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge (and that lane belongs to
# G-AX in any case).
AXIOM_TESTS = []
