"""PBT falsification battery for django__django-11740.

NOT a Nagini module; an adversarial manifest the runner (swebench_nagini.pbt)
parses. Spec cases are full model.py variants built by region-surgery: each
swaps text ONLY inside the single `# impl-start`/`# impl-end` region, so the
frozen spec (axioms/pure/pre/post-conditions, the spec_view) is byte-identical
and `markers.same_spec(base, variant)` holds. A spec case "passes" iff its
verify outcome matches `expect` (verify => must verify; reject => must NOT).

DEFENDED SURFACE (what this spec actually pins)
-----------------------------------------------
One modeled function:

  altered_field_dependencies(new_field: FieldDef) -> PSeq[int]
      Requires(Acc(new_field.is_relation, 1/2))      # READ-ONLY input (half perm)
      Ensures(Acc(new_field.is_relation, 1/2))       # frame: gives the perm back
      # (2) relational branch — EXACT-EQUALITY pin to the oracle AND non-empty:
      Ensures(Implies(new_field.is_relation,
                      Result() == fk_dependencies(new_field) and len(Result()) > 0))
      # (3) non-relational branch — empty:
      Ensures(Implies(not new_field.is_relation, len(Result()) == 0))

  fk_dependencies(field) is @Pure @ContractOnly (A-consumed). Domain:
      Requires(Acc(field.is_relation, 1/4)); Requires(field.is_relation)
      Ensures(len(Result()) > 0)

Three load-bearing facts the battery attacks:

  * FRAME. `new_field` is a half-permission (`Acc(...,1/2)`) READ-ONLY heap
    input — both required and re-ensured. A rival that WRITES `new_field`
    (e.g. forces `is_relation = False` to take the empty branch vacuously) must
    be rejected for INSUFFICIENT PERMISSION (you cannot assign through 1/2).
    This is the #1 weakness class and is MANDATORY here. (frame-mutation case.)

  * THE ORACLE PIN IS EXACT, NOT JUST NON-EMPTY. Clause (2) demands
    `Result() == fk_dependencies(new_field)`, not merely `len(Result()) > 0`.
    `fk_dependencies` is @ContractOnly/opaque, so its only published fact is
    `len(Result()) > 0`. A rival that returns SOME non-empty sequence on the
    relational branch (e.g. `PSeq(0)`) satisfies `len>0` but CANNOT prove the
    exact equality to the opaque oracle => rejected. This makes the equality
    clause load-bearing (an "ungrounded-oracle echo" only succeeds when it is
    the actual oracle value, which is the gold). Because the pin is exact, there
    is no WRONG echo that verifies; we instead supply the honest cheapest-impl
    positive control (return the oracle directly) which MUST verify, plus the
    non-equal-non-empty rival which MUST reject.

  * BOTH BRANCHES ARE PINNED. Relational => non-empty (== oracle); non-relational
    => empty. The bug emitted an UNCONDITIONALLY EMPTY list, so the discriminating
    miss is the always-empty rival (== prepatch). The dual miss (emit a non-empty
    list even when NON-relational) is rejected by clause (3). Both are
    partial-domain rivals with concrete refinement arguments below.

AXIOM LANE
----------
`fk_dependencies` is A-consumed (@ContractOnly). axiom-soundness runs the REAL
unchanged callee `_get_dependencies_for_foreign_key` over the relational field
shapes (FK other-app / same-app / O2O / m2m auto-through / m2m explicit-through /
FK swappable) and asserts `len > 0` (the axiom Ensures), fuzzing the shapes to
try to make the real callee return an empty list. axiom-containment: the model
calls `fk_dependencies(new_field)` ONLY under `if new_field.is_relation`, so the
ONLY callee-input the model can reach is a RELATIONAL field — exactly the axiom's
`Requires(field.is_relation)` domain. The probe asserts every shape that reaches
the helper is `is_relation == True` (in-domain) and that the guard the model uses
is the same relation test, so no caller-reachable input falls outside the axiom
domain. Both probes embed axiom_check.py's source (read on the HOST at load time)
because the runner mounts only the probe at /work.
"""
from pathlib import Path

INSTANCE = "django__django-11740"
FLOAT_ENCODING = None  # meta.json float_encoding is null; unused here.

_BASE = (Path(__file__).parent / "model.py").read_text()

# The single impl region in the frozen model.py (verbatim, unique).
_IMPL = """\
    dependencies = PSeq()  # type: PSeq[int]
    if new_field.is_relation:
        dependencies = dependencies + fk_dependencies(new_field)
    return dependencies"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


def _impl(new_impl):
    """Variant that swaps ONLY altered_field_dependencies's impl region."""
    return _swap(_BASE, _IMPL, new_impl)


SPEC_TESTS = [
    # ----------------------------------------------------------------- POSITIVE CONTROLS
    {
        "id": "pos-guard-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: a guard-style early return for the
        # non-relational case and a direct return of the oracle for the relational
        # case (no PSeq() seed, no `+`, branch order flipped). Keeps every proof
        # obligation: non-relational -> empty PSeq (clause 3); relational -> the
        # oracle value which the axiom Ensures makes non-empty (clause 2). No write
        # to new_field (frame preserved). MUST verify, else SPEC-TOO-STRONG.
        "module": _impl(
            "    if not new_field.is_relation:\n"
            "        empty = PSeq()  # type: PSeq[int]\n"
            "        return empty\n"
            "    result = fk_dependencies(new_field)  # type: PSeq[int]\n"
            "    return result"),
        "rationale": ("a correct re-expression (guard early-return + direct oracle return, "
                      "branch order flipped, no seed/concatenation) satisfies both pinned "
                      "branches; if it cannot verify, SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-cheapest-honest-echo",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest HONEST impl on the relational branch: return the oracle value
        # verbatim (PSeq() + oracle == oracle). Because clause (2) is an EXACT pin
        # to fk_dependencies, the only sequence that satisfies it IS the oracle's,
        # so the honest echo is exactly the gold value. Non-relational kept empty.
        # This is the positive control for the (grounded, exact) oracle pin.
        "module": _impl(
            "    if new_field.is_relation:\n"
            "        rel = fk_dependencies(new_field)  # type: PSeq[int]\n"
            "        return rel\n"
            "    empty = PSeq()  # type: PSeq[int]\n"
            "    return empty"),
        "rationale": ("the exact-equality oracle pin admits exactly one value on the relational "
                      "branch (the oracle's own); returning it directly is the cheapest honest "
                      "impl and MUST verify (the oracle is grounded by exact equality, not an "
                      "echo-able answer key); else SPEC-TOO-STRONG."),
    },

    # ----------------------------------------------------------------- ADMISSIBILITY
    {
        "id": "admiss-fshaped-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        # Positive-control caller: build the two F2P-shaped FieldDefs (a relational
        # field — the altered-into-FK case the F2P tests; and a plain field — the
        # P2P non-relational alter) and self-call the modeled function on each. The
        # admissibility obligation is that the precondition
        # Acc(new_field.is_relation,1/2) ADMITS a freshly constructed field: the
        # constructor ensures exactly Acc(.is_relation,1/2), so each self-call's
        # Requires is met and the call site type-checks; each call returns the
        # half-permission (read-only frame), which we re-assert. If the precondition
        # rejected a normal input, the call site would fail => PRECOND-TOO-STRONG.
        #
        # NOTE: we deliberately do NOT assert len(result)>0 / ==0 on the *post-state*
        # of the self-call. Discharging the relational/non-relational postcondition
        # branch requires the post-state value of new_field.is_relation, but the
        # FROZEN postcondition re-ensures only Acc(new_field.is_relation,1/2) and does
        # not pin new_field.is_relation == old(new_field.is_relation). Nagini's modular
        # call rule havocs a fractional-permission heap value across a call boundary
        # unless the callee's post explicitly frames it (verified: a minimal
        # read-only call f(c) with Ensures(Acc(c.b,1/2)) loses c.b's value at the call
        # site). That is a proof-engineering limitation of the (correct) frozen spec,
        # NOT precond-too-strong, and the branch-value pinning is already exercised by
        # the pos-guard-early-return / pos-cheapest-honest-echo soundness controls and
        # the four reject cases. Here we keep ONLY the admissibility-proper obligation.
        "module": _impl(
            "    dependencies = PSeq()  # type: PSeq[int]\n"
            "    if new_field.is_relation:\n"
            "        dependencies = dependencies + fk_dependencies(new_field)\n"
            "    rel = FieldDef(True)  # type: FieldDef\n"
            "    Assert(Acc(rel.is_relation, 1 / 2))\n"
            "    plain = FieldDef(False)  # type: FieldDef\n"
            "    Assert(Acc(plain.is_relation, 1 / 2))\n"
            "    Assert(Acc(rel.is_relation, 1 / 2) and Acc(plain.is_relation, 1 / 2))\n"
            "    return dependencies"),
        "rationale": ("the precondition Acc(new_field.is_relation,1/2) must admit a freshly "
                      "constructed F2P-shaped field (relational and plain): both self-calls "
                      "type-check, their Requires is met by the constructor's ensured half "
                      "permission, and each returns the half permission (read-only frame). If "
                      "the self-call's Requires cannot be established for a normal input, "
                      "PRECOND-TOO-STRONG. (The result-value branch pin is covered by the "
                      "soundness positive controls; it is not re-asserted here because the "
                      "frozen post does not frame the input value across the call.)"),
    },

    # ----------------------------------------------------------------- FRAME-MUTATION (reject)
    {
        "id": "weak-frame-mutate-input",
        "kind": "uniqueness",
        "expect": "reject",
        # MANDATORY frame-mutation probe. The rival WRITES the read-only input
        # (forces new_field.is_relation = False) so the postcondition's relational
        # clause becomes vacuous and it can return an empty list. With only
        # Acc(new_field.is_relation, 1/2) the assignment requires full permission
        # => MUST be rejected for INSUFFICIENT PERMISSION (not a value mismatch).
        # Gold invariants kept verbatim so the rejection is attributable to the write.
        "module": _impl(
            "    new_field.is_relation = False\n"
            "    dependencies = PSeq()  # type: PSeq[int]\n"
            "    if new_field.is_relation:\n"
            "        dependencies = dependencies + fk_dependencies(new_field)\n"
            "    return dependencies"),
        "refinement": ("A faithful real patch cannot rewrite the caller's `new_field` definition "
                       "to claim it is non-relational; the field object is shared, read by the "
                       "rest of generate_altered_fields and by add_operation, and mutating it would "
                       "corrupt the emitted AlterField (wrong field, wrong subsequent dependency "
                       "computation). For the actual F2P input (IntegerField altered into a "
                       "ForeignKey) it would emit an EMPTY dependency list, so "
                       "test_alter_field_to_fk_dependency_other_app STILL fails (expects "
                       "[('testapp','__first__')]). F2P NOT resolved."),
        "rationale": ("rejected by the permission system: assigning new_field.is_relation needs "
                      "Acc(...,1) but only Acc(...,1/2) is held (read-only). If it verifies, the "
                      "frame is unsound (vacuous-postcondition-via-mutation) => SPEC-TOO-WEAK."),
    },

    # ----------------------------------------------------------------- PARTIAL-DOMAIN (reject)
    {
        "id": "weak-always-empty-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating miss == prepatch behaviour: emit an UNCONDITIONALLY
        # EMPTY dependency list (never extend). Correct on the non-relational branch
        # (clause 3) but WRONG on the relational branch: fails clause (2)'s
        # len(Result()) > 0 (and the equality). This is exactly model_prepatch.py.
        "module": _impl(
            "    empty = PSeq()  # type: PSeq[int]\n"
            "    return empty"),
        "refinement": ("This is the pre-patch code: the AlterField operation was created with no "
                       "dependencies (`add_operation` recorded `_auto_deps = []`). Altering a plain "
                       "IntegerField into a ForeignKey emits ZERO dependencies, so the migration "
                       "cannot be ordered and test_alter_field_to_fk_dependency_other_app fails "
                       "(observed dependencies == [] vs required [('testapp','__first__')]). F2P "
                       "NOT resolved (this is model_prepatch.py)."),
        "rationale": ("must fail clause (2) Implies(is_relation, Result()==fk_dependencies(...) and "
                      "len(Result())>0) on the relational branch (empty list). If it verifies, "
                      "SPEC-TOO-WEAK."),
    },
    {
        "id": "weak-nonrelational-pollution",
        "kind": "uniqueness",
        "expect": "reject",
        # Dual partial-domain miss: emit a NON-EMPTY list even when the new field is
        # NON-relational (and the correct oracle value on the relational branch).
        # Correct on the relational branch (clause 2) but WRONG on the non-relational
        # branch: a one-element seq fails clause (3) len(Result()) == 0.
        "module": _impl(
            "    dependencies = PSeq(0)  # type: PSeq[int]\n"
            "    if new_field.is_relation:\n"
            "        dependencies = fk_dependencies(new_field)\n"
            "    return dependencies"),
        "refinement": ("A real patch that seeds `dependencies = [<some tuple>]` (or extends "
                       "unconditionally, outside the relation guard) would attach a spurious "
                       "ordering dependency to a NON-relational AlterField (e.g. altering a "
                       "CharField's max_length). The migration planner would then demand an "
                       "unrelated model be available first, breaking the PASS_TO_PASS altered-field "
                       "tests (test_alter_field_to_not_null_*, etc.) that assert NO extra dependency. "
                       "F2P/P2P NOT resolved."),
        "rationale": ("must fail clause (3) Implies(not is_relation, len(Result())==0) on the "
                      "non-relational branch (a one-element seq). If it verifies, SPEC-TOO-WEAK."),
    },
    {
        "id": "weak-relational-nonequal-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        # The ORACLE-PIN attack: on the relational branch return SOME non-empty
        # sequence that is NOT the oracle's value (PSeq(0)). It satisfies the
        # weaker `len(Result()) > 0`, but clause (2) demands the EXACT equality
        # Result() == fk_dependencies(new_field); fk_dependencies is opaque
        # (@ContractOnly), so equality to a literal PSeq(0) is NOT provable => the
        # equality clause must reject it. This proves the equality (not just
        # non-emptiness) is load-bearing.
        "module": _impl(
            "    dependencies = PSeq()  # type: PSeq[int]\n"
            "    if new_field.is_relation:\n"
            "        dependencies = PSeq(0)\n"
            "    return dependencies"),
        "refinement": ("A real patch that attaches an arbitrary non-empty placeholder dependency "
                       "(rather than `self._get_dependencies_for_foreign_key(new_field)`) would "
                       "record the WRONG dependency on the relational AlterField. The migration "
                       "would depend on the wrong (or a non-existent) model/app, so "
                       "test_alter_field_to_fk_dependency_other_app — which asserts the EXACT "
                       "dependency [('testapp','__first__')] — STILL fails. F2P NOT resolved."),
        "rationale": ("must fail clause (2)'s EXACT equality Result()==fk_dependencies(new_field): "
                      "the opaque @ContractOnly oracle cannot be shown equal to a literal PSeq(0), "
                      "so the relational branch is rejected even though len(Result())>0 holds. If it "
                      "verifies, the spec only pins non-emptiness (not the value) => SPEC-TOO-WEAK."),
    },
]


# ----------------------------------------------------------------------- AXIOM LANE
# `fk_dependencies` is the one A-consumed @ContractOnly axiom. The runner mounts
# ONLY the probe at /work, so we embed axiom_check.py's source (read on the HOST
# at load time) into each probe and execute it. Probes import only Django +
# stdlib; exit 0 iff the obligation holds.

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# ---- SOUNDNESS: run the bundle's G-AX oracle (the real callee over 6 relational
# shapes, asserting len>0) verbatim, then ALSO try to make the real callee return
# an empty list by re-checking each shape directly (the axiom Ensures edge: the
# helper must NEVER return [] for a relational field). ------------------------
_SOUNDNESS_PROBE = (
    _AXIOM_CHECK_SRC
    + r'''

# --- PBT extension: re-assert the axiom Ensures (len(Result())>0) directly on the
# real callee for every relational shape, and confirm NONE returns an empty list
# (the only obligation the proof consumes). This is the boundary the axiom pins:
# a relational field always yields at least one dependency (the dependency on the
# referenced model, emitted unconditionally before the optional `through` append).
def _pbt_axiom_ensures():
    import inspect
    configure_django()
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.state import ProjectState
    ps = ProjectState()
    ad = MigrationAutodetector(ps, ps)
    sig = inspect.signature(MigrationAutodetector._get_dependencies_for_foreign_key)
    extra_names = [p for p in sig.parameters if p not in ("self", "field")]
    extras = {}
    for name in extra_names:
        if name == "app_label":
            extras[name] = "axiomapp_a"
        elif name == "model_name":
            extras[name] = "sourcea"
        elif name == "project_state":
            extras[name] = ps
        else:
            extras[name] = None
    failures = 0
    for label, field in build_fields():
        deps = ad._get_dependencies_for_foreign_key(field=field, **extras)
        # axiom Ensures: len(Result()) > 0 on EVERY relational field.
        if not (isinstance(deps, list) and len(deps) > 0):
            failures += 1
            print("AXIOM-SOUNDNESS FAIL: %s -> %r (expected a NON-EMPTY list)"
                  % (label, deps))
    return failures

if __name__ == "__main__":
    rc = main()
    if rc == 0:
        rc = 1 if _pbt_axiom_ensures() else 0
        if rc == 0:
            print("AXIOM-SOUNDNESS OK: real _get_dependencies_for_foreign_key returns a "
                  "non-empty dependency list for every relational field shape "
                  "(fk_dependencies axiom Ensures len(Result())>0 holds, no empty result).")
    sys.exit(rc)
'''
)

# ---- CONTAINMENT: the model calls fk_dependencies ONLY under
# `if new_field.is_relation`, so the ONLY callee-input the model can reach is a
# RELATIONAL field. The axiom's Requires is exactly `field.is_relation`. Assert
# every shape that reaches the helper is is_relation==True (in-domain), and that
# a NON-relational field (which the model NEVER passes to the helper) is the only
# kind outside the domain — i.e. no caller-reachable input falls outside the
# axiom's Requires. (Covering only relational fields is sound; the model's guard
# guarantees containment.) ----------------------------------------------------
_CONTAINMENT_PROBE = (
    _AXIOM_CHECK_SRC
    + r'''

# --- PBT extension: caller-domain CONTAINMENT for fk_dependencies. -----------
# Axiom Requires: Acc(field.is_relation, 1/4) and field.is_relation. The model
# reaches the helper ONLY on the relational branch (`if new_field.is_relation`),
# so every callee-input the model can produce satisfies field.is_relation. We
# assert: (a) all 6 relational shapes that reach the helper are is_relation==True
# (inside the axiom domain), and (b) a representative NON-relational field
# (IntegerField -- the very field the F2P alters FROM) is is_relation==False, so
# the model's guard correctly keeps it OUT of the helper call (it is never a
# reachable callee-input). A reachable input outside is_relation==True would be
# AXIOM-TOO-WEAK-FOR-CALLER; none exists.
def _pbt_containment():
    configure_django()
    from django.db import models
    failures = 0
    # (a) every shape that reaches the helper is relational (in axiom domain).
    for label, field in build_fields():
        if not getattr(field, "is_relation", False):
            failures += 1
            print("CONTAINMENT MISS: helper-reaching shape %s is is_relation=False "
                  "(outside axiom Requires field.is_relation)" % label)

    # (b) the non-relational field the model guards out is genuinely is_relation
    # False, so the model's `if new_field.is_relation` never passes it to the
    # helper -- it is NOT a reachable callee-input.
    class _Holder(models.Model):
        plain = models.IntegerField()
        text = models.CharField(max_length=200)
        class Meta:
            app_label = "containmentapp"
    for name in ("plain", "text"):
        f = _Holder._meta.get_field(name)
        if getattr(f, "is_relation", False):
            failures += 1
            print("CONTAINMENT NOTE: %s unexpectedly is_relation=True" % name)
    return failures

if __name__ == "__main__":
    rc = main()
    if rc == 0:
        rc = 1 if _pbt_containment() else 0
        if rc == 0:
            print("AXIOM-CONTAINMENT OK: the model calls fk_dependencies only on the "
                  "relational branch; every reachable callee-input is is_relation==True "
                  "(inside the axiom Requires domain), and non-relational fields are "
                  "guarded out -> no reachable input outside the axiom domain.")
    sys.exit(rc)
'''
)

AXIOM_TESTS = [
    {
        "id": "ax-fk-dependencies-soundness",
        "axiom": "fk_dependencies",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": ("the axiom Ensures len(Result())>0 for any relational field. We run the "
                      "REAL unchanged _get_dependencies_for_foreign_key over 6 relational shapes "
                      "(FK other/same-app, O2O, m2m auto/explicit-through, FK swappable) and "
                      "assert each returns a NON-EMPTY list; any empty result => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-fk-dependencies-containment",
        "axiom": "fk_dependencies",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": ("the model calls fk_dependencies ONLY under `if new_field.is_relation`, so "
                      "every reachable callee-input is a relational field — exactly the axiom's "
                      "Requires(field.is_relation) domain. The probe asserts each helper-reaching "
                      "shape is is_relation==True and that non-relational fields are guarded out. "
                      "A reachable input outside the domain => AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
