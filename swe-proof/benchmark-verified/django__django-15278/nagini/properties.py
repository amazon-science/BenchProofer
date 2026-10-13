# properties.py — PBT falsification battery for django__django-15278. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between
# `add_column`'s `# impl-start` / `# impl-end` is edited; the spec view — axioms,
# the @Pure needs_full_rebuild, pre-/post-conditions, signatures — is never touched),
# checked by Nagini verify + markers.same_spec. The axiom lane probes the single
# A-consumed @ContractOnly callee `has_effective_default` against the REAL Django
# SQLite backend `editor.effective_default(field) is not None` (see AXIOM_TESTS).
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   add_column(col: ColumnSpec) -> int
#   Models the gold sqlite3 add_field() routing decision: choose the FULL-REBUILD
#   route (Result()==1, the gold `self._remake_table(...)`) iff the column is a
#   primary key, OR unique, OR non-nullable, OR carries an effective DB default;
#   choose the in-place APPEND route (Result()==0, the gold `super().add_field(...)`)
#   ONLY for a column carrying NONE of those four constraints. The gold patch PREPENDS
#   the two disjuncts `field.primary_key or field.unique` to the pre-patch predicate
#   `not field.null or self.effective_default(field) is not None`. The F2P witness is
#   a nullable, defaultless `OneToOneField` (unique=True, null=True, primary_key=False,
#   no default): pre-patch it routed to APPEND (`ALTER TABLE ... ADD COLUMN ... UNIQUE`,
#   which SQLite rejects); post-patch it MUST route to REBUILD purely because of the
#   uniqueness constraint.
#
#   PRECONDITION (three half-permission READS — the column is READ-ONLY):
#     (P1) Requires(Acc(col.primary_key, 1/2))
#     (P2) Requires(Acc(col.unique,      1/2))
#     (P3) Requires(Acc(col.nullable,    1/2))
#   POSTCONDITION (three framing/permission returns + the load-bearing pins):
#     (Q-perm) Ensures(Acc(col.primary_key,1/2)) / Acc(col.unique,1/2) / Acc(col.nullable,1/2)
#     (Q0) Ensures(Result()==1 or Result()==0)               -- route is a 2-valued discriminator
#     (Q1) Ensures((Result()==1) == needs_full_rebuild(col)) -- THE load-bearing pin, BOTH directions
#     (Q2) Ensures(Implies(col.primary_key, Result()==1))    -- a pk column always rebuilds
#     (Q3) Ensures(Implies(col.unique, Result()==1))         -- a unique column always rebuilds
#     (Q4) Ensures(Implies(not col.nullable, Result()==1))   -- a non-nullable column always rebuilds
#     (Q5) Ensures(Implies(has_effective_default(col), Result()==1)) -- a defaulted column always rebuilds
#     (Q6) Ensures(Implies(Result()==0,
#                          (not pk) and (not unique) and nullable and (not has_effective_default(col))))
#            -- the APPEND route is taken ONLY when EVERY constraint is absent.
#   Q1 alone PINS the route to the grounded predicate `needs_full_rebuild(col)` in
#   BOTH directions; Q2..Q6 redundantly fortify each disjunct (Q3 is the exact disjunct
#   the gold patch ADDS — the nullable defaultless unique column). There is no slack:
#   a rival that misroutes ANY column fails Q1 (and at least one of Q2..Q6).
#
# FRAME-MUTATION lane is MANDATORY: every field of `col` is granted at Acc(...,1/2)
#   (READ-ONLY). A rival that WRITES any flag of `col` to satisfy the postcondition
#   vacuously must be REJECTED for INSUFFICIENT PERMISSION. The real add_field() only
#   READS field.primary_key/field.unique/field.null (and reads effective_default); a
#   write would mutate the caller's shared model Field object. Byte-fuzzers never think
#   to mutate the input — this is the project's #1 weakness class.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q1 pins the route to
#   `needs_full_rebuild(col)`, a @Pure helper that COMPUTES the decision from the
#   argument: `col.primary_key or col.unique or (not col.nullable) or
#   has_effective_default(col)`. It is fully GROUNDED in `col` — there is no opaque
#   answer-key / exact marker an impl could echo without doing the work. The fourth
#   disjunct `has_effective_default(col)` is itself @ContractOnly with NO Ensures, so
#   the verifier treats it only as a deterministic, side-effect-free boolean FUNCTION
#   of `col` — an impl cannot guess its value, it must CALL it (or call
#   needs_full_rebuild, which calls it). Hence the unique satisfier of Q1 IS the
#   grounded routing decision; the honest control is the cheapest faithful impl that
#   COMPUTES that decision (pos-call-helper / pos-disjunct-reorder below), not a wrong
#   echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: the ONLY behavioural effect modelled is the route choice,
#   and it is reported as the int Result() discriminator (1=rebuild branch / 0=append
#   branch). There is no raise/side-effect difference invisible to the value
#   abstraction — Q0..Q6 govern the discriminator directly, so a route swap is fully
#   observable. The weak-swap-route rival (returns the WRONG label on every column) is
#   the capability-free discriminator for this fork; no separate token plumbing needed.
#
# PARTIAL-DOMAIN lane: heavily exercised. A rival can route correctly on most columns
#   yet diverge on a sub-domain that is EXACTLY one of the gold disjuncts:
#     - weak-prepatch    : drops BOTH new disjuncts (pre-patch predicate) => misroutes
#                          the nullable defaultless unique (or pk) column. == model_prepatch.
#     - weak-drop-unique : drops ONLY `col.unique` => misroutes EXACTLY the F2P
#                          (nullable defaultless OneToOneField).
#     - weak-drop-pk     : drops ONLY `col.primary_key` => misroutes a nullable
#                          defaultless primary-key column.
#     - weak-always-rebuild / weak-always-append : pin only one route.
#
# AXIOM lane: meta.axioms has ONE A-consumed @ContractOnly callee `has_effective_default`
#   (deep_model_references == []). Its contract is the WEAKEST possible — NO Ensures,
#   only fractional read permissions on the column flags — so AXIOM-UNSOUNDNESS reduces
#   to: on the REAL Django SQLite backend, `editor.effective_default(field) is not None`
#   is a DETERMINISTIC, SIDE-EFFECT-FREE boolean read of the field (the only thing the
#   @Pure no-Ensures modelling assumes), AND the real four-way routing predicate equals
#   the model's needs_full_rebuild over the four signals. AXIOM-CONTAINMENT: the model
#   only ever calls has_effective_default on a `ColumnSpec` whose three flags are
#   readable (Requires Acc(...,1/8); the caller holds 1/2 >> 1/8) — i.e. on the very
#   abstraction of a real Field, which is exactly the domain effective_default accepts.
#   Both probes RUN the real callee in-container (apply_gold=True); they embed the
#   bundle's own axiom_check.py oracle (read on the HOST at load time — the runner
#   mounts only the probe), opened encoding="utf-8".
from pathlib import Path

INSTANCE = "django__django-15278"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
# Read the bundle's G-AX oracle on the HOST (the runner mounts ONLY the probe at /work,
# so axiom_check.py is NOT in-container) and embed its source into the axiom probes.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen `add_column` impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`). Every spec variant _swap()s ONLY this
# block, so the edit never touches the spec (axioms / @Pure needs_full_rebuild /
# pre-/post-conditions + the signature). same_spec is computed over the spec_view,
# which elides every impl region, so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    if (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col)):
        return 1
    else:
        return 0"""

assert _BASE.count(_IMPL) == 1, "add_column impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the add_column impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-call-helper: structurally DIFFERENT but behaviourally identical and faithful.
# Instead of INLINING the four-way disjunction, it calls the @Pure spec helper
# needs_full_rebuild(col) directly and maps its boolean to the route int. This is the
# cheapest HONEST impl that computes the grounded decision (the genuine "satisfier" of
# Q1) — it cannot be an ungrounded echo because needs_full_rebuild is computed from
# `col`, not asserted. The caller holds Acc(col.*,1/2); needs_full_rebuild needs only
# Acc(col.*,1/4), so the call is admissible. No write => the Q-perm framing is
# preserved verbatim. If this FAILS => SPEC-TOO-STRONG (a faithful correct impl that
# routes via the spec predicate is rejected).
_POS_CALL_HELPER = """\
    if needs_full_rebuild(col):
        return 1
    else:
        return 0"""

# pos-disjunct-reorder: the SAME inlined four-way disjunction, but with the operands
# permuted into a structurally different order (default-first, then nullable, then
# unique, then pk). Boolean `or` is commutative, so the guard is semantically
# identical to the gold guard and to needs_full_rebuild's body; the verifier discharges
# `a or b or c or d == d or c or b or a` trivially. Keeps the gold control-flow shape
# (if/return-1/else/return-0) and adds no write. If this FAILS => SPEC-TOO-STRONG.
_POS_REORDER = """\
    if (has_effective_default(col) or (not col.nullable) or
            col.unique or col.primary_key):
        return 1
    else:
        return 0"""

# pos-negated-append-first: same decision, branches REORDERED — test the NEGATED guard
# (the APPEND condition: not pk and not unique and nullable and no default) FIRST and
# return 0 in that branch, else 1. Mutually-exclusive reshape of the control flow that
# keeps the same semantics; exercises Q6 (the append-only condition) directly. No
# write. If this FAILS => SPEC-TOO-STRONG.
_POS_NEGATED = """\
    if ((not col.primary_key) and (not col.unique) and
            col.nullable and (not has_effective_default(col))):
        return 0
    else:
        return 1"""

# admiss-reads: an admissibility positive control. The precondition is the three
# half-permission reads Acc(col.primary_key/unique/nullable, 1/2). This control keeps
# the gold body VERBATIM but FIRST asserts, under those half-permissions, that the
# three routing flags a normal F2P-shaped column carries are readable (no write, so no
# extra permission demand). If the precondition could not admit a legitimate column,
# this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal column descriptor is in-domain; the three\n"
    "    # half-permissions admit reading each routing flag.\n"
    "    Assert(col.primary_key == col.primary_key)\n"
    "    Assert(col.unique == col.unique)\n"
    "    Assert(col.nullable == col.nullable)\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — every flag of `col` is Acc(...,1/2), READ-ONLY).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold guard/return body VERBATIM (so the rejection is
# attributable SOLELY to the added write, not to a value mismatch), then WRITES BACK
# into the read-only input: col.primary_key = col.primary_key. A no-op store, but a
# STORE — it demands FULL write permission on col.primary_key, which the caller granted
# only at 1/2. The verifier must reject for insufficient permission.
_FRAME_MUT = (
    "    # Frame violation: write back into the read-only (Acc(...,1/2)) input flag.\n"
    "    col.primary_key = col.primary_key\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN / ROUTE-SWAP RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-prepatch: the EXACT pre-patch predicate (model_prepatch.py) — it DROPS BOTH new
# disjuncts `col.primary_key or col.unique`, routing on `(not col.nullable) or
# has_effective_default(col)` alone. On the F2P (nullable, defaultless, unique, not pk)
# the guard is False => returns 0 (APPEND), but needs_full_rebuild(col) is True (unique)
# => Q1 `(Result()==1)==needs_full_rebuild(col)` is False (and Q3 `Implies(unique,
# Result()==1)` is violated).
_WEAK_PREPATCH = """\
    if ((not col.nullable) or has_effective_default(col)):
        return 1
    else:
        return 0"""

# weak-drop-unique: PARTIAL-DOMAIN. Drops ONLY the `col.unique` disjunct (keeps pk,
# nullable, default). Correct on every column EXCEPT the unique-but-otherwise-appendable
# one — which is EXACTLY the F2P (nullable defaultless OneToOneField): the guard is
# False => returns 0, but needs_full_rebuild is True => Q1 false / Q3 violated.
_WEAK_DROP_UNIQUE = """\
    if (col.primary_key or
            (not col.nullable) or has_effective_default(col)):
        return 1
    else:
        return 0"""

# weak-drop-pk: PARTIAL-DOMAIN. Drops ONLY the `col.primary_key` disjunct. Misroutes a
# nullable, defaultless, non-unique PRIMARY-KEY column: guard False => returns 0, but
# needs_full_rebuild is True (pk) => Q1 false / Q2 `Implies(primary_key, Result()==1)`
# violated.
_WEAK_DROP_PK = """\
    if (col.unique or
            (not col.nullable) or has_effective_default(col)):
        return 1
    else:
        return 0"""

# weak-always-append: hard-codes the in-place APPEND route for every column. On any
# column needing a rebuild (e.g. the F2P unique column, or a pk, or non-nullable, or
# defaulted) needs_full_rebuild is True but Result()==0 => Q1 false (and the relevant
# Q2..Q5 violated; Q6's implication forces all-constraints-absent, contradicted). This
# is what a real patch that deleted the predicate (always super().add_field) would do.
_WEAK_ALWAYS_APPEND = """\
    return 0"""

# weak-always-rebuild: hard-codes the FULL-REBUILD route for every column. On a genuinely
# appendable column (not pk, not unique, nullable, no default) needs_full_rebuild is
# False but Result()==1 => Q1 false. This is what a real patch that always
# _remake_table'd would do (correct routing but the wrong action set for appendable
# columns; it over-rebuilds, breaking the P2P append paths).
_WEAK_ALWAYS_REBUILD = """\
    return 1"""

# weak-swap-route: CONTROL-FLOW / route-label swap. Computes the CORRECT predicate but
# emits the OPPOSITE discriminator — returns 0 where it should rebuild and 1 where it
# should append. On the F2P (needs_full_rebuild True) it returns 0 => Q1
# `(Result()==1)==needs_full_rebuild(col)` is False. Models a real patch that wired the
# branches backwards (super().add_field on the rebuild case, _remake_table on append).
_WEAK_SWAP_ROUTE = """\
    if (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col)):
        return 0
    else:
        return 1"""


SPEC_TESTS = [
    {
        "id": "pos-call-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_CALL_HELPER),
        "rationale": (
            "structurally-different but CORRECT impl: routes via a direct call to the "
            "@Pure spec helper needs_full_rebuild(col) instead of inlining the "
            "disjunction. The caller holds Acc(col.*,1/2); the helper needs only "
            "Acc(col.*,1/4), so the call is admissible, and Q1 "
            "((Result()==1)==needs_full_rebuild(col)) holds by construction. No write, "
            "so Q-perm framing is preserved. This is the genuine grounded satisfier of "
            "Q1 (NOT an ungrounded echo: needs_full_rebuild COMPUTES from col). If it "
            "FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-disjunct-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but CORRECT impl: the SAME four-way disjunction with "
            "operands permuted (default, nullable, unique, pk). Boolean `or` is "
            "commutative, so the guard equals the gold guard / needs_full_rebuild's body "
            "and the verifier discharges the reordering trivially. Same if/return shape, "
            "no write. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-negated-append-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_NEGATED),
        "rationale": (
            "structurally-different but CORRECT impl: tests the NEGATED (append-only) "
            "condition first and returns 0 there, else 1 — a mutually-exclusive branch "
            "reorder with identical semantics that exercises Q6 (the all-constraints-"
            "absent append condition) directly. No write. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (three Acc(col.*,1/2) half-permission reads) must admit a "
            "normal F2P-shaped column descriptor: each routing flag is readable under "
            "its half-permission. The gold impl is otherwise verbatim (only reads/asserts "
            "added, no write). If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold add_field() only READS field.primary_key / field.unique / "
            "field.null (and reads effective_default(field)); it NEVER assigns to them. "
            "A faithful real patch that wrote back into the model Field object would "
            "mutate the caller's shared field instance (Django reuses Field objects "
            "across the schema editor and the model meta), corrupting subsequent "
            "operations — it would diverge from the gold's read-only routing and would "
            "not faithfully resolve. The store here is a no-op only by coincidence; the "
            "point is the spec must forbid ANY write to the input."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: each col flag is granted at "
            "Acc(col.*,1/2) (P1..P3); the store col.primary_key=col.primary_key demands "
            "FULL write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold guard/return body is kept verbatim so the "
            "rejection is attributable solely to the write. If it VERIFIES => the "
            "read-only frame is hollow (frame-mutation, the #1 weakness class)."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): the original guard "
            "`if not field.null or self.effective_default(field) is not None:` omits the "
            "`field.primary_key or field.unique` disjuncts the gold patch adds. Its "
            "faithful real patch is the UNCHANGED repo, which routes a nullable defaultless "
            "unique OneToOneField to super().add_field (in-place `ALTER TABLE ... ADD "
            "COLUMN ... UNIQUE`, which SQLite rejects) instead of _remake_table. It fails "
            "the F2P test_add_field_o2o_nullable. Does NOT resolve — exactly the change "
            "the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q1 ((Result()==1)==needs_full_rebuild(col)) and Q3 "
            "(Implies(col.unique, Result()==1)): on the F2P column (unique=True, "
            "nullable=True, no default, not pk) the rival's guard is False so it returns "
            "0, but needs_full_rebuild(col) is True (unique) and Q3 forces Result()==1. "
            "If it VERIFIES => SPEC-TOO-WEAK (the new disjuncts are not enforced). "
            "Supporting near-miss carrying the strongest refinement (the literal pre-patch)."
        ),
    },
    {
        "id": "weak-drop-unique",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_UNIQUE),
        "refinement": (
            "dropping ONLY the `field.unique` disjunct is what a real patch that added "
            "`field.primary_key` but forgot `field.unique` would do. It routes EVERY "
            "column correctly EXCEPT a unique-but-otherwise-appendable one — which is "
            "EXACTLY the F2P (a nullable, defaultless, non-pk OneToOneField, forced "
            "unique=True). On that column it emits `ALTER TABLE ... ADD COLUMN ... "
            "UNIQUE`, which SQLite rejects, failing test_add_field_o2o_nullable. A "
            "genuine PARTIAL-DOMAIN break on the uniqueness sub-domain; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q1 and Q3 (Implies(col.unique, Result()==1)): for the F2P "
            "column the rival sets the guard False (unique dropped, all other signals "
            "absent) and returns 0, but needs_full_rebuild(col) is True (it still ORs "
            "col.unique) and Q3 demands Result()==1. PARTIAL-DOMAIN: pins every signal "
            "except uniqueness. If it VERIFIES => SPEC-TOO-WEAK on the unique sub-domain."
        ),
    },
    {
        "id": "weak-drop-pk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_PK),
        "refinement": (
            "dropping ONLY the `field.primary_key` disjunct is the dual mistake — it "
            "misroutes a nullable, defaultless, non-unique PRIMARY-KEY column to the "
            "in-place append route, which SQLite cannot express (ADD COLUMN PRIMARY "
            "KEY). It fails any P2P/scenario adding such a field via the SQLite backend. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q1 and Q2 (Implies(col.primary_key, Result()==1)): for a "
            "nullable defaultless non-unique pk column the rival's guard is False so it "
            "returns 0, but needs_full_rebuild(col) is True (pk) and Q2 demands "
            "Result()==1. PARTIAL-DOMAIN on the primary-key sub-domain. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-always-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_APPEND),
        "refinement": (
            "always returning the append route is what a real patch that DELETED the "
            "routing predicate (always super().add_field) would do — it tries in-place "
            "`ALTER TABLE ... ADD COLUMN` for EVERY column, including pk/unique/"
            "non-null/defaulted ones SQLite cannot append. It fails the F2P (the unique "
            "OneToOneField) and every P2P that adds a constrained column. Does NOT "
            "resolve. Bound to a bare `return 0` (the declared int return; no `# type:` "
            "pitfall)."
        ),
        "rationale": (
            "REJECTED by Q1 ((Result()==1)==needs_full_rebuild(col)) and Q2..Q5: on any "
            "column needing rebuild (e.g. the F2P unique column) needs_full_rebuild is "
            "True but Result()==0, so Q1 is False and the matching Q-implication is "
            "violated. If it VERIFIES => SPEC-TOO-WEAK (the rebuild route is unpinned)."
        ),
    },
    {
        "id": "weak-always-rebuild",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_REBUILD),
        "refinement": (
            "always returning the rebuild route is what a real patch that hard-coded "
            "_remake_table for every add_field would do — it over-rebuilds the whole "
            "table even for a genuinely appendable column (not pk, not unique, nullable, "
            "no default), which the gold patch deliberately keeps on the cheap in-place "
            "append path. It changes the observable behaviour of the unchanged append "
            "branch and fails the P2P tests that exercise super().add_field on an "
            "appendable column. Does NOT resolve. Bound to a bare `return 1`."
        ),
        "rationale": (
            "REJECTED by Q1 and Q6 (Implies(Result()==0, all-constraints-absent)): on "
            "an appendable column needs_full_rebuild is False but Result()==1, so Q1 "
            "((Result()==1)==needs_full_rebuild(col)) is False. CONTROL-FLOW (dual to "
            "always-append): the append fork is removed. If it VERIFIES => SPEC-TOO-WEAK "
            "(the append route is unpinned)."
        ),
    },
    {
        "id": "weak-swap-route",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP_ROUTE),
        "refinement": (
            "computing the correct predicate but emitting the OPPOSITE discriminator is "
            "what a real patch that wired the branches backwards would do — "
            "super().add_field on the rebuild case and _remake_table on the append "
            "case. Every column then takes the wrong action: appendable columns get "
            "rebuilt and constrained columns get an impossible in-place ADD COLUMN. It "
            "fails the F2P and the P2P append paths. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q1 ((Result()==1)==needs_full_rebuild(col)): the rival returns "
            "0 exactly when needs_full_rebuild is True and 1 when it is False, so Q1 is "
            "False on EVERY column. CONTROL-FLOW-EFFECT / route-label swap: the int "
            "discriminator makes the swap fully observable to the value abstraction. If "
            "it VERIFIES => SPEC-TOO-WEAK (the route labels are not pinned to the "
            "decision)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-consumed @ContractOnly callee `has_effective_default` vs the REAL
# Django SQLite backend `editor.effective_default(field) is not None`.
# meta.axioms == [has_effective_default] (A-consumed; deep_model_references == []). Its
# contract is the WEAKEST possible (NO Ensures, only fractional read permissions), so:
#   * axiom-soundness  : the real callee must be a DETERMINISTIC, SIDE-EFFECT-FREE
#                        boolean read (re-evaluation gives the same answer and does not
#                        mutate the field's routing flags) AND the real four-way routing
#                        predicate must equal the model's needs_full_rebuild over the
#                        four signals (incl. the discriminating nullable defaultless
#                        OneToOneField). This is exactly what axiom_check.py establishes.
#   * axiom-containment: the model calls has_effective_default ONLY on a `ColumnSpec`
#                        whose three flags are readable (Requires Acc(...,1/8); caller
#                        holds 1/2) — i.e. on the abstraction of a real Field. Every such
#                        reachable callee-input is a real Django Field, which is exactly
#                        effective_default's domain — no reachable input lies outside it.
# Both probes RUN the real callee in-container (apply_gold=True). The runner mounts ONLY
# the probe at /work, so axiom_check.py is NOT in-container — its source is read on the
# HOST at load time (encoding="utf-8") and embedded into each probe string.
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = (
    "# ax-sound-has_effective_default: run the bundle's own G-AX oracle (axiom_check.py),\n"
    "# embedded verbatim below, which exercises the REAL Django SQLite backend over 14\n"
    "# field witnesses (incl. the discriminating nullable defaultless OneToOneField) and\n"
    "# asserts (1) editor.effective_default(field) is-not-None is deterministic + does not\n"
    "# mutate the routing flags, and (2) the real routing predicate == the model's\n"
    "# needs_full_rebuild. Exit 0 iff the axiom (weakest: a pure boolean read) is sound.\n"
    "import sys\n"
    + _AXIOM_CHECK_SRC
    # axiom_check.py ends with `if __name__ == '__main__': sys.exit(main())`; the probe
    # runs as __main__, so main() executes against the real backend and sets the exit
    # code. A defensive fallback in case the guard is ever changed:
    + "\nsys.exit(main())\n"
)

_AX_COVER_PROBE = (
    "# ax-cover-has_effective_default: AXIOM-CONTAINMENT. The model applies\n"
    "# has_effective_default ONLY to a ColumnSpec abstraction of a real Field whose\n"
    "# three routing flags are readable. The real callee effective_default(field)\n"
    "# accepts ANY model Field; enumerate the reachable witnesses (the same 14 the model\n"
    "# can route, spanning pk / unique / nullable / default / blank-non-null / relational)\n"
    "# and assert effective_default(field) raises NOTHING and returns a value whose\n"
    "# is-not-None is a clean boolean for every one — i.e. every caller-reachable\n"
    "# callee-input lies INSIDE effective_default's domain. A reachable input that made\n"
    "# effective_default raise / fall outside its domain => AXIOM-TOO-WEAK-FOR-CALLER.\n"
    "import os\n"
    "import sys\n"
    "\n"
    "\n"
    "def _setup_django():\n"
    "    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'axiom_cover_settings')\n"
    "    import django\n"
    "    from django.conf import settings\n"
    "    if not settings.configured:\n"
    "        settings.configure(\n"
    "            DEBUG=True,\n"
    "            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',\n"
    "                                   'NAME': ':memory:'}},\n"
    "            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],\n"
    "            USE_TZ=False,\n"
    "        )\n"
    "    django.setup()\n"
    "\n"
    "\n"
    "def main():\n"
    "    _setup_django()\n"
    "    from django.db import connection\n"
    "    from django.db.models import (\n"
    "        BooleanField, IntegerField, CharField, DateTimeField,\n"
    "        BinaryField, OneToOneField, ForeignKey,\n"
    "    )\n"
    "    from django.db.models.deletion import CASCADE, SET_NULL\n"
    "    from django.contrib.auth.models import User\n"
    "\n"
    "    def mk(field):\n"
    "        field.set_attributes_from_name('probe')\n"
    "        return field\n"
    "\n"
    "    # exactly the reachable abstraction domain: every column the model can route.\n"
    "    witnesses = [\n"
    "        mk(OneToOneField(User, CASCADE, null=True)),\n"
    "        mk(OneToOneField(User, SET_NULL, null=True, blank=True)),\n"
    "        mk(ForeignKey(User, CASCADE, null=True)),\n"
    "        mk(IntegerField(null=True)),\n"
    "        mk(CharField(max_length=10, null=True)),\n"
    "        mk(DateTimeField(null=True)),\n"
    "        mk(IntegerField(null=False)),\n"
    "        mk(IntegerField(null=True, unique=True)),\n"
    "        mk(CharField(max_length=10, null=True, unique=True)),\n"
    "        mk(IntegerField(primary_key=True)),\n"
    "        mk(IntegerField(null=True, default=7)),\n"
    "        mk(BooleanField(null=True, default=False)),\n"
    "        mk(CharField(max_length=10, null=False, blank=True)),\n"
    "        mk(BinaryField(null=True)),\n"
    "    ]\n"
    "    fails = 0\n"
    "    with connection.schema_editor() as editor:\n"
    "        for field in witnesses:\n"
    "            try:\n"
    "                val = editor.effective_default(field)\n"
    "            except Exception as e:  # noqa: BLE001\n"
    "                fails += 1\n"
    "                print('CONTAINMENT FAIL: effective_default raised on reachable '\n"
    "                      'witness %r: %s' % (field, e))\n"
    "                continue\n"
    "            b = (val is not None)\n"
    "            if b not in (True, False):\n"
    "                fails += 1\n"
    "                print('CONTAINMENT FAIL: is-not-None not boolean for %r' % (field,))\n"
    "    if fails:\n"
    "        print('AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) outside '\n"
    "              'effective_default domain' % fails)\n"
    "        return 1\n"
    "    print('AXIOM-CONTAINMENT OK: every caller-reachable column (the %d-witness '\n"
    "          'abstraction domain incl. the nullable OneToOneField) lies inside '\n"
    "          'effective_default(field) is-not-None domain (no raise, clean boolean).'\n"
    "          % len(witnesses))\n"
    "    return 0\n"
    "\n"
    "\n"
    "sys.exit(main())\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-has_effective_default",
        "axiom": "has_effective_default",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "has_effective_default is the single A-consumed @ContractOnly callee, "
            "modelling `editor.effective_default(field) is not None`. Its contract is the "
            "WEAKEST possible (NO Ensures, only fractional read permissions), so soundness "
            "= the real callee is a deterministic, side-effect-free boolean read AND the "
            "real four-way routing predicate equals the model's needs_full_rebuild. The "
            "probe embeds the bundle's own axiom_check.py oracle (read on the HOST at load "
            "time, encoding-safe) and runs it against the REAL Django SQLite backend on 14 "
            "field witnesses incl. the discriminating nullable defaultless OneToOneField. "
            "If the real callee disagrees / mutates flags anywhere => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-has_effective_default",
        "axiom": "has_effective_default",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: the model calls has_effective_default ONLY on a ColumnSpec "
            "abstraction of a real Field whose three flags are readable (Requires "
            "Acc(...,1/8); caller holds 1/2). Every reachable callee-input is therefore a "
            "real Django Field, and effective_default(field) accepts any Field. The probe "
            "runs the real callee on exactly the reachable witness domain (the 14 columns "
            "the model can route) and asserts it raises nothing and yields a clean boolean "
            "is-not-None for each. A reachable input outside effective_default's domain => "
            "AXIOM-TOO-WEAK-FOR-CALLER (none expected: covering more than the caller "
            "reaches would be sound, not a defect)."
        ),
    },
]
