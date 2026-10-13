"""properties.py — G-PBT falsification battery for django__django-15851 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct buildShellArgs`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier: ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE. ONE contracted method — the assembly of the command-line
argument vector that invokes the database shell:

  buildShellArgs (leading : List String) (dbname : Option String)
                 (parameters : List String) return (args : List String)
    ensures args = builtArgs leading dbname parameters

where ``builtArgs leading dbname parameters = leading ++ parameters ++
dbnameToken dbname`` and ``dbnameToken dbname = dbname.toList`` (``some s ↦ [s]``,
``none ↦ []``). There are NO ``require`` clauses: every input is in-domain.

The single ensures clause is a total value equality with THREE independent
structural pieces, each pinned by a distinct binder:
  (P1) the vector BEGINS with the leading segment ``leading`` (the executable
       plus the connection-option flags);
  (P2) the caller-supplied extra arguments ``parameters`` come NEXT, BEFORE the
       database-name token — this is the DISCRIMINATING ordering the gold change
       establishes (the extras must precede the database name);
  (P3) the optional database-name token ``dbnameToken dbname`` comes LAST — a
       singleton when a database is named, nothing otherwise.
The F2P test pins exactly (P2): the assembled vector for a named database with
one extra argument must place the extra BEFORE the database name.

INPUT BINDERS varied by the reject witnesses: ``leading`` (length 3 / 1 / 2 / 2),
``dbname`` (``some`` / ``some`` / ``none`` / ``some``), ``parameters``
(``["--help"]`` / ``["-x"]`` / ``["-c","q"]`` / ``["-c","vacuum"]``). No witness
pins any of the three to one value, and each rival is refuted at a point where
its own defect actually fires.

ADMISSIBILITY. Carried, as ``admiss-f2p-shaped``. The method has no ``require``
clauses, so the literal "a normal input is admitted" probe is vacuous; the
analogue that still has teeth on a total carrier is that the obligation be
SATISFIABLE and NON-DEGENERATE at an F2P-shaped input, which that case
discharges by evaluation at a concrete point before the frozen obligation closes
in general. Its liveness is measured, not asserted: flipping its first conjunct
to the opposite ordering makes the build FAIL.

ADVERSARIAL READ of the nagini classes (see the module footer for the full port
accounting):
  * FRAME-MUTATION — VACUOUS on this backend. On nagini both ``prefix`` and
    ``parameters`` carry a fractional heap permission ``Acc(...,1/2)`` and a
    rival that WRITES either must be rejected for insufficient permission (the
    nagini sibling's MANDATORY, #1-weakness lane). Lean and Velvet are
    referentially transparent: every parameter is an immutable value (no ``mut``
    binder on any method input — ``leading``/``dbname``/``parameters`` are all
    read-only by construction), there is no heap and no aliasing, so there is no
    read-only input to overwrite and no substitute probe to build. Not
    fabricated, not substituted — reported as vacuous. The nagini
    ``frame-mutate-prefix`` and ``frame-mutate-parameters`` rivals have no
    counterpart here.
  * PARTIAL-DOMAIN / ORDERING — the core of the port and where the bug lives.
    The nagini ``atk-prepatch-ordering`` (dbname token BEFORE the extras — the
    literal pre-patch code) ports directly to ``atk-prepatch-ordering`` here.
    The nagini ``atk-drop-dbname`` (never emit the database-name token) ports to
    ``atk-drop-dbname``. The nagini ``atk-prefix-after-params`` (leading segment
    emitted AFTER the extras) ports to ``atk-leading-after-params``.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as on nagini. ``builtArgs`` /
    ``dbnameToken`` are total, fully-unfolded ``def``s of the method's own
    arguments in the ``pure`` region and the ``axioms`` region is empty (this
    bundle axiomatizes nothing — mapping.md §3); there is no opaque answer key a
    wrong impl could echo without doing the work. The honest control is
    therefore the cheapest faithful reshape (``pos-assoc-reshape``).
  * CONTROL-FLOW-EFFECT — N/A, exactly as on nagini: the only observable is the
    returned argument vector, captured exactly by the ensures equality; there is
    no raise / side-effect / capability difference the value abstraction misses
    (the unchanged ``env`` dict and the ``runshell`` wrapper are out of scope per
    mapping.md §1).

AXIOM lane: DROPPED. The axiom lane is G-AX's job; this bundle declares no
``axiom`` and axiomatizes no callee (mapping.md §3 — the assembled vector is pure
in-process list concatenation modeled deeply with ``++`` and ``Option.toList``).
The gate ignores ``AXIOM_TESTS`` regardless. The nagini sibling likewise had
``AXIOM_TESTS == []``.
"""
from pathlib import Path

INSTANCE = "django__django-15851"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl region body, verbatim (the straight-line assembly
# ---- strictly BETWEEN the region comment lines). It lies wholly inside the
# ---- `-- impl-start` / `-- impl-end` region the spec view elides and is unique
# ---- in the file (both facts asserted by `_swap`). Every variant replaces this
# ---- block only; the `ensures` clause and the method statement are untouched,
# ---- so `same_spec` holds and the obligation survives byte-identical.
_IMPL = (
    "    let mut args := leading\n"
    "    args := args ++ parameters\n"
    "    args := args ++ dbnameToken dbname\n"
    "    return args\n"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"


def _impl(new_impl):
    """Variant with the impl region body replaced; frozen proof body kept."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `buildShellArgsTester leading dbname parameters = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can interfere with the verdict. The method
# ---- has NO `require` clauses, so the tester's precondition guard is `True` at
# ---- every point and never shorts a witness to a vacuous `true`. All inputs
# ---- are `decide`-able string/option literals — no opaque term — so no
# ---- carrier conditioning (and thus no consistency obligation) is needed.
_TESTER = (
    "extract_program_for buildShellArgs\n"
    "prove_precondition_decidable_for buildShellArgs\n"
    "prove_postcondition_decidable_for buildShellArgs\n"
    "derive_tester_for buildShellArgs\n\n"
)


def _wit(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). This method has no `require`
    # clauses, so the classic "a normal input is admitted" probe is vacuous
    # as stated. The analogue on a total carrier is the one that still has
    # teeth: the obligation must be SATISFIABLE and NON-DEGENERATE at exactly
    # an F2P-shaped input. This case discharges that at a concrete point, by
    # evaluation, as a `have` inside the impl region, BEFORE the frozen impl
    # lines are re-emitted byte-identically and the frozen obligation closes
    # in general. Four conjuncts:
    #   (i)   the post-image at the F2P-shaped input (one named database, one
    #         extra argument) is the vector with the extra BEFORE the name;
    #   (ii)  it is NOT the opposite ordering — so the clause genuinely
    #         separates the two orders at this point rather than admitting
    #         both;
    #   (iii) it is NOT the token-less vector — so the trailing token is
    #         really present, i.e. the post-image is not degenerate;
    #   (iv)  the unnamed-database point is satisfiable too, so the obligation
    #         is live on BOTH branches of the optional token, not just one.
    # Liveness measured: replacing (i)'s right-hand side with the opposite
    # ordering makes the build FAIL (`decide` proves the conjunction false),
    # so the conjunction carries discriminating content and is not a
    # tautology the carrier would grant to anything.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            '    have hadm :\n'
            '        builtArgs ["psql"] (some "dbname") ["--help"]\n'
            '            = ["psql", "--help", "dbname"]\n'
            '        ∧ builtArgs ["psql"] (some "dbname") ["--help"]\n'
            '            ≠ ["psql", "dbname", "--help"]\n'
            '        ∧ builtArgs ["psql"] (some "dbname") ["--help"]\n'
            '            ≠ ["psql", "--help"]\n'
            '        ∧ builtArgs ["psql", "-h", "h"] none ["-c", "q"]\n'
            '            = ["psql", "-h", "h", "-c", "q"] := by\n'
            '      decide\n'
            + _IMPL
        ),
        "rationale": "PASS SOURCE = the single clause `args = builtArgs leading "
                     "dbname parameters`, discharged AT A CONCRETE F2P-SHAPED "
                     "INPUT before the frozen body closes it in general. The "
                     "admitted domain is total (the pre-conditions region is "
                     "empty), so the residual PRECOND-TOO-STRONG risk on this "
                     "carrier is not a rejected input but an obligation that is "
                     "UNSATISFIABLE or DEGENERATE at a normal input. The four "
                     "conjuncts pin, at one named-database point: the post-image "
                     "is the extras-before-name vector (satisfiable); it is NOT "
                     "the opposite ordering (the clause separates the orders "
                     "here); it is NOT the token-less vector (non-degenerate — "
                     "the trailing token is really emitted); and the unnamed "
                     "point is satisfiable too, so the obligation is live on both "
                     "branches of the optional token. The impl lines are "
                     "re-emitted byte-identically after the `have`, so the "
                     "ensures clause still discharges under the untouched frozen "
                     "proof. If it FAILS => PRECOND-TOO-STRONG (the obligation is "
                     "unsatisfiable at the very input the change exists to fix, "
                     "which no uniqueness rival would localize).",
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Instead of appending the
    # two tails onto the leading segment in sequence, it forms the tail
    # (extras then database-name token) FIRST and then prepends the leading
    # segment in a single concatenation. This is an associativity reshape:
    # it computes `leading ++ (parameters ++ dbnameToken dbname)`, equal to
    # `builtArgs = leading ++ parameters ++ dbnameToken dbname` for every
    # input, so the single ensures clause still discharges under the frozen
    # `loom_solve; simp_all [builtArgs, dbnameToken]` proof (associativity of
    # `++` is exactly what `simp_all` closes).
    # =====================================================================
    {
        "id": "pos-assoc-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let tail := parameters ++ dbnameToken dbname\n"
            "    return leading ++ tail\n"
        ),
        "rationale": "a reshape that builds the tail (extras then the "
                     "database-name token) first and prepends the leading "
                     "segment in one concatenation computes `leading ++ "
                     "(parameters ++ dbnameToken dbname)`, associatively equal "
                     "to `builtArgs leading dbname parameters` for every input, "
                     "so `args = builtArgs leading dbname parameters` still "
                     "discharges through the frozen proof. If it FAILS => "
                     "SPEC-TOO-STRONG (a faithful correct assembly is rejected).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument for why its faithful real
    # counterpart would still leave the F2P failing. No two rivals share a
    # refutation point; each varies all three binders.
    # =====================================================================
    {
        "id": "atk-prepatch-ordering",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug. The database-name token is appended BEFORE the caller's
        # extra arguments, yielding leading ++ dbnameToken dbname ++
        # parameters. Correct whenever no database is named (dbnameToken is
        # empty, nothing to misorder) OR the extras are empty; wrong on any
        # named database with a non-empty extras list — which is exactly the
        # F2P input.
        "module": _impl(
            "    let mut args := leading\n"
            "    args := args ++ dbnameToken dbname\n"
            "    args := args ++ parameters\n"
            "    return args\n"
        ),
        "refinement": "this is the pre-patch ordering — the optional "
                      "database-name token appended BEFORE the caller's extra "
                      "arguments instead of after. Its faithful real counterpart "
                      "is the UNCHANGED repo, which assembles the vector with the "
                      "database name ahead of the extras; the F2P test for a "
                      "named database with one extra argument was rewritten to "
                      "expect the extra FIRST and the database name last, so the "
                      "pre-patch ordering fails that assertion. It would NOT "
                      "resolve — a verifying rival here would be a true "
                      "verify-does-not-resolve break.",
        "rationale": "REJECT from `args = builtArgs leading dbname parameters`, "
                     "whose tail is `parameters ++ dbnameToken dbname` (extras "
                     "BEFORE the token — piece P2/P3): this rival emits "
                     "`dbnameToken dbname ++ parameters`, so for any named "
                     "database with a non-empty extras list the token precedes "
                     "the extras and the vectors differ. PARTIAL-DOMAIN: correct "
                     "only when the database is unnamed or the extras are empty. "
                     "If it VERIFIES => SPEC-TOO-WEAK (the ordering is not "
                     "pinned).",
        "witness": _wit(
            'buildShellArgsTester ["psql", "-U", "u"] (some "db") ["--help"]'
        ),
    },
    {
        "id": "atk-drop-dbname",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks piece P3: never append the database-name token. Returns
        # leading ++ parameters unconditionally. Correct exactly when no
        # database is named (the token is empty anyway); wrong on any named
        # database.
        "module": _impl(
            "    let mut args := leading\n"
            "    args := args ++ parameters\n"
            "    return args\n"
        ),
        "refinement": "dropping the database-name token omits the target "
                      "database from the shell command, so the shell connects to "
                      "the default database instead of the configured NAME. This "
                      "fails both the F2P test (which expects the database name "
                      "as the trailing element) and the PASS_TO_PASS cases that "
                      "pin a named database in the vector, so its faithful real "
                      "patch does NOT resolve.",
        "rationale": "REJECT from `args = builtArgs leading dbname parameters`, "
                     "whose tail is `dbnameToken dbname` (piece P3): with a named "
                     "database the post-image ends in the singleton token, but "
                     "this rival returns `leading ++ parameters` with no trailing "
                     "token. PARTIAL-DOMAIN: correct only when the database is "
                     "unnamed. Refuted at `dbname = some \"mydb\"`, a point no "
                     "other rival uses. If it VERIFIES => SPEC-TOO-WEAK (the "
                     "database-name token is not pinned).",
        "witness": _wit(
            'buildShellArgsTester ["psql"] (some "mydb") ["-x"]'
        ),
    },
    {
        "id": "atk-leading-after-params",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks piece P1: emit the caller's extras FIRST, then the leading
        # segment, then the database-name token — parameters ++ leading ++
        # dbnameToken dbname. The leading segment carries the executable name
        # (which MUST lead the vector) and the connection-option flags.
        # Correct only when there are no extras; wrong whenever both the extras
        # and the leading segment are non-empty (the leading segment always is
        # — it holds the executable). This is a distinct defect from
        # atk-prepatch-ordering: here the LEADING segment is misplaced, not the
        # database-name token, and it is refuted with dbname = none (where the
        # prepatch and drop rivals both agree with gold), pinning piece P1
        # independently of the token.
        "module": _impl(
            "    let mut args := parameters\n"
            "    args := args ++ leading\n"
            "    args := args ++ dbnameToken dbname\n"
            "    return args\n"
        ),
        "refinement": "a vector that emitted the caller's extras before the "
                      "leading segment puts the executable name AFTER the "
                      "user-supplied arguments — the first element is no longer "
                      "the program to invoke, so the shell is never launched "
                      "correctly. It fails every PASS_TO_PASS case (all expect "
                      "the executable as the leading element) as well as the "
                      "F2P, so its faithful real patch does NOT resolve.",
        "rationale": "REJECT from `args = builtArgs leading dbname parameters`, "
                     "whose head is `leading` (piece P1): this rival builds "
                     "`parameters ++ leading ++ dbnameToken dbname`, so whenever "
                     "the extras are non-empty the leading element is a caller "
                     "argument rather than the leading segment and the vectors "
                     "differ. Refuted at `dbname = none` with a two-element "
                     "leading segment — a point where the ordering-token rivals "
                     "agree with gold, so it demonstrates the head clause "
                     "independently. If it VERIFIES => SPEC-TOO-WEAK (the leading "
                     "segment is not pinned first).",
        "witness": _wit(
            'buildShellArgsTester ["psql", "-h"] none ["-c", "q"]'
        ),
    },
    {
        "id": "atk-drop-params",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks piece P2 by OMISSION rather than by misordering. The three
        # rivals above all emit the caller's extra arguments somewhere; none of
        # them tests that they are emitted AT ALL. This one drops them entirely,
        # returning leading ++ dbnameToken dbname. Correct exactly when the
        # extras are empty; wrong whenever the caller passes any. Refuted at a
        # fourth distinct point (a two-element leading segment, a named
        # database, TWO extra arguments) — the only rival whose extras list has
        # length 2 at its own refutation point.
        "module": _impl(
            "    let mut args := leading\n"
            "    args := args ++ dbnameToken dbname\n"
            "    return args\n"
        ),
        "refinement": "silently discarding the caller-supplied extra arguments "
                      "means the pass-through arguments never reach the shell at "
                      "all — the very arguments whose placement this change is "
                      "about would vanish instead of being positioned. The F2P "
                      "test pins a vector CONTAINING the extra argument, so a "
                      "faithful patch that dropped the extras fails it outright, "
                      "as do the PASS_TO_PASS cases that pass extras through. It "
                      "does NOT resolve.",
        "rationale": "REJECT from `args = builtArgs leading dbname parameters`, "
                     "whose middle segment is `parameters` (piece P2): this rival "
                     "returns `leading ++ dbnameToken dbname`, omitting the "
                     "extras entirely, so for any non-empty extras list the "
                     "vectors differ. This is the P2-BY-OMISSION probe the "
                     "ordering rivals leave unattacked — they all emit the extras "
                     "somewhere, so none of them shows the spec requires them to "
                     "be emitted at all. PARTIAL-DOMAIN: correct only when the "
                     "extras are empty. If it VERIFIES => SPEC-TOO-WEAK (the "
                     "presence of the extras is not pinned).",
        "witness": _wit(
            'buildShellArgsTester ["pg", "-p"] (some "prod") ["-c", "vacuum"]'
        ),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet port accounting. The nagini sibling has 7 SPEC cases
# (1 soundness positive, 1 admissibility, 5 uniqueness rivals — two of which are
# the mandatory frame-mutation rivals) plus 0 AXIOM cases. This bundle models the
# SAME purely-functional core: the argument-vector assembly. The nagini surface
# is `build_argv(prefix, parameters, has_dbname, dbname) -> List[int]` with the
# ordering guarantee split across (E1)/(E2); here it is `buildShellArgs (leading
# dbname parameters)` with the single equality `args = builtArgs leading dbname
# parameters` whose three structural pieces carry the same guarantee.
#
#   sibling case                -> here                        disposition
#   ----------------------------------------------------------------------
#   pos-control-reorder         -> pos-assoc-reshape           PORTED (re-shaped:
#       the sibling aliases the trailing token to a local; here the cheapest
#       faithful reshape is the associativity regrouping, since the frozen impl
#       is straight-line concatenation with no trailing-token guard to alias)
#   admiss-f2p-shaped           -> admiss-f2p-shaped           PORTED (re-aimed:
#       the sibling discharges a half-permission precondition at the F2P input;
#       there is no precondition here, so the case is re-aimed at the obligation
#       being satisfiable and non-degenerate at that same input — see the
#       ADMISSIBILITY paragraph in the module docstring)
#   frame-mutate-prefix         -> (none)                      VACUOUS (see below)
#   frame-mutate-parameters     -> (none)                      VACUOUS (see below)
#   atk-prepatch-ordering       -> atk-prepatch-ordering       PORTED (this IS the
#       bug on both carriers: the database-name token emitted before the extras)
#   atk-drop-dbname             -> atk-drop-dbname             PORTED
#   atk-prefix-after-params     -> atk-leading-after-params    PORTED
#   (no sibling)                -> atk-drop-params             ADDED (audit): the
#       P2-BY-OMISSION probe. Every ported rival emits the caller's extras
#       somewhere, so none of them showed the spec requires them to be emitted at
#       all; this one drops them and is refuted at a fourth distinct point.
#
# ADMISSIBILITY (admiss-f2p-shaped): CARRIED, re-aimed. The nagini case shows a
#   normal F2P-shaped input satisfies the half-permission precondition
#   `Acc(list_pred(prefix),1/2) & Acc(list_pred(parameters),1/2)`. This method has
#   NO `require` clauses, so that literal obligation does not exist here — but
#   "no precondition" is NOT a reason to drop the lane, because the analogue on a
#   total carrier is the obligation being unsatisfiable or degenerate at exactly
#   an F2P-shaped input. That is what the case discharges: by evaluation, as a
#   `have`, at a concrete point, before the frozen obligation closes in general.
#   Measured liveness (flip a conjunct => build fails) distinguishes it from a
#   tautology.
#
# FRAME/PERMISSION-MUTATION (frame-mutate-prefix, frame-mutate-parameters):
#   VACUOUS on this backend, for the reason the SPEC_GUIDE gives — Lean and
#   Velvet are referentially transparent, there is no heap, no aliasing and no
#   fractional permission, and `buildShellArgs` declares no `mut` binder on any
#   input (`leading`, `dbname`, `parameters` are all immutable values). There is
#   no read-only input to overwrite and thus no discriminating witness could
#   exist. The sibling calls this its MANDATORY class and its #1 weakness lane on
#   nagini; here both rivals simply cannot be expressed. Not fabricated, not
#   substituted — reported as vacuous.
#
# WITNESS DISTINCTNESS. No two rivals share a refutation point. Each is refuted
#   at a distinct (leading, dbname, parameters) triple:
#     atk-prepatch-ordering    (["psql","-U","u"], some "db",   ["--help"])
#     atk-drop-dbname          (["psql"],          some "mydb", ["-x"])
#     atk-leading-after-params (["psql","-h"],     none,        ["-c","q"])
#     atk-drop-params          (["pg","-p"],       some "prod", ["-c","vacuum"])
#   so `leading` moves (length 3 vs 1 vs 2 vs 2), `dbname` moves (some vs some vs
#   none vs some), and `parameters` moves (different contents, and length 1 vs 1
#   vs 2 vs 2). Every input binder of the spec predicate is varied, and each rival
#   is refuted where its own defect fires (the two token rivals at a named
#   database; the leading-order rival at an unnamed one, where the token rivals
#   would agree with gold; the extras-omission rival at a two-element extras list),
#   so no rival is a near-miss of another sharing a point it does not actually
#   fail at.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
#   axiom and axiomatizes no callee (mapping.md §3 — the assembly is pure list
#   concatenation modeled deeply as `builtArgs`/`dbnameToken`). The sibling also
#   shipped `AXIOM_TESTS == []`.
AXIOM_TESTS = []
