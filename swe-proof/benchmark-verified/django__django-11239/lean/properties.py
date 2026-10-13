"""properties.py — G-PBT falsification battery for django__django-11239 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for the admissibility positive, inside the ``-- proof-start`` / ``-- proof-end``
region — is changed, so ``markers.same_spec`` holds and the single
``theorem correct_runShell`` STATEMENT stays byte-identical). An
``expect="verify"`` case passes iff it is in scope AND the file elaborates with
the obligation closed (no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``); an ``expect="reject"`` case passes iff it is in scope
AND it does NOT verify AND its refutation ``witness`` holds of the rival while
FAILING on the frozen solution.

PORT NOTE. This ports the nagini falsification battery
(``../nagini/properties.py``). The nagini bundle models a single function
``build_pg_env(conn_params) -> Dict`` over an integer-keyed dict carrier and
pins the published environment as a DICTIONARY (membership + per-key value +
a no-spurious-keys Forall), with the command-line argument vector left
UNMODELED. This lean bundle models the SAME purely-functional core but over a
richer carrier: the modeled function returns BOTH observable components of the
invocation — the ordered command-line argument vector AND the ordered list of
injected environment entries — and the postcondition pins each to a grounded
structural equation over the input connection parameters. See ``assessment`` at
the bottom for the full nagini→lean accounting.

DEFENDED SURFACE (one modeled behavior; two independent top-level clauses).
``problem_spec_runShell cp result`` pins EXACTLY:

  * (C-args)  ``result.args = specArgs cp`` — the argument vector is the
    executable name, then a flag pair for each supplied routing parameter, then
    the database name last.
  * (C-env)   ``result.pgEnv = specPgEnv cp`` — the injected environment is, in
    fixed injection order, one entry per supplied secret/transport-security
    parameter, each carrying that parameter's value verbatim under its dedicated
    library variable name; a parameter that is absent (empty string) contributes
    nothing, and no other entry appears.

Because the environment is modeled as an ORDERED LIST of (name, value) pairs
(not a set/dict), C-env simultaneously pins PRESENCE (which of the five
parameters are injected), VALUE (verbatim), ABSENCE of any spurious entry, and
the correct parameter→variable wiring — the equation to ``specPgEnv cp`` fails
if any one of these is wrong.

CAVEAT ON THAT STRENGTH (audit finding, recorded here rather than repaired,
because the spec is frozen and a spec change must re-clear the equivalence and
leakage gates). The ordered-list model also pins the INJECTION ORDER, and
injection order is NOT observable in the modeled behavior: the environment
entries are consumed as a name-keyed mapping, so two impls that inject the same
name/value set in different sequences are indistinguishable to every F2P and
PASS_TO_PASS assertion. C-env is therefore stronger than the behavior it stands
for, and an order-permuted but otherwise faithful impl is rejected by the frozen
spec even though its faithful real counterpart WOULD resolve. Measured, not
argued — see ``spec_holes`` in the audit payload and the ``assessment`` note on
the dropped nagini "reorder" positive. The consequence for THIS battery is only
that a reorder case cannot be carried as a soundness positive; every case below
is unaffected, since none of them depends on the order clause for its outcome.

BINDER STRUCTURE. The spec predicate has ONE input binder, ``cp`` (a
``ConnParams`` with nine string fields); ``result`` is the output. Although
there is a single binder, the reject witnesses vary DISTINCT fields of ``cp``
(sslmode / sslkey / password / dbname / the empty record), so each rival is
refuted at the sub-domain its wrong branch actually governs — no field is held
fixed across every witness. The eight reject witnesses probe eight DISTINCT
``cp`` values (pts=8).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory
    frame-mutation rival writes back onto its read-only input to be caught by
    the fractional-permission system. This carrier is referentially transparent:
    ``cp`` is an immutable value, there is no ``mut`` input binder, no aliasing,
    and no read-only cell to overwrite. The frame obligation is instead
    discharged structurally — C-args/C-env pin the result ENTIRELY as a function
    of ``cp``, so an impl cannot leave any output component unconstrained. No
    substitute probe is fabricated (porting map: vacuous here).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by structural equations (``specArgs``/``specPgEnv``) built directly
    from ``cp``'s fields. There is no opaque answer key an impl could echo —
    assembling each list from the supplied parameters IS the work. In its place
    the battery carries honest cheapest-implementation POSITIVE CONTROLS.

  * PARTIAL-DOMAIN / VALUE / NO-SPURIOUS / CROSS-WIRE — APPLY. Every nagini
    uniqueness rival re-expresses as an attack on C-env: publish only the
    password and none of the transport-security parameters (the pre-fix bug);
    drop one parameter's injection; inject a spurious extra entry; inject a
    parameter's variable with a wrong (blanked) value; cross-wire one parameter's
    variable onto another's guard/source. One ADDED rival attacks C-args (the
    argument-vector clause the nagini carrier does not model at all).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen proof is tuned to the frozen syntactic
form), so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean ``example`` that states the
spec predicate directly at one concrete ``cp`` of small string literals and
closes by ``unfold``+``decide`` — the connection fields are concrete strings, so
``specArgs``/``specPgEnv`` and the impl loop both reduce and ``decide`` settles
the (in)equality. Each witness binds NOTHING in its head (``cp`` is a ground
record literal), so there are no hypotheses whose joint consistency could be in
question. Each was checked with two real ``lake env lean`` builds to HOLD of its
rival and to FAIL on the frozen solution, so it discriminates rather than
asserting a tautology. An independent audit re-derived all of these builds from
scratch and confirmed, additionally, that every gold-side failure is a SEMANTIC
refutation — ``decide`` reports the concrete proposition FALSE — and not a
missing identifier, a type error, an unfolding failure or a timeout, which is
the failure mode a discrimination check cannot otherwise distinguish.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
shell-invocation assembler that mis-injects (or omits, or spuriously adds) one
environment entry, or mis-builds the argument vector, so the child process the
interactive client launches sees a wrong environment/command line, and the F2P
test — which asserts the captured PG* environment is EXACTLY the four
transport-security entries — would mismatch. So the faithful patch would NOT
resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (every operation is a primitive modeled deeply); the axiom lane is
G-AX's job, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-11239"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each unique inside Solution.lean; verified at load) ----
# One conditional environment-injection line per modeled parameter, the env-list
# initialiser, the database-name append (C-args), and one routing-flag line.
_I_PW = ('  if cp.password    ≠ "" then pgEnv := pgEnv ++ '
         '[("PGPASSWORD",    cp.password)]')
_I_MODE = ('  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ '
           '[("PGSSLMODE",     cp.sslmode)]')
_I_CERT = ('  if cp.sslcert     ≠ "" then pgEnv := pgEnv ++ '
           '[("PGSSLCERT",     cp.sslcert)]')
_I_KEY = ('  if cp.sslkey      ≠ "" then pgEnv := pgEnv ++ '
          '[("PGSSLKEY",      cp.sslkey)]')
_I_ENVINIT = '  let mut pgEnv : List (String × String) := []'
_I_DBNAME = '  args := args ++ [cp.dbname]'
_I_USER = '  if cp.user ≠ "" then args := args ++ ["-U", cp.user]'
_I_PORT = '  if cp.port ≠ "" then args := args ++ ["-p", cp.port]'

# The frozen proof's `intro` line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = '  intro cp'


def _wit(cp):
    """A refutation witness: state the frozen spec predicate directly at the
    concrete `cp`, then `unfold`+`decide`. Holds of a rival that violates the
    spec at `cp`; fails on gold (which satisfies the spec everywhere)."""
    return (
        f"example : ¬ problem_spec_runShell {cp}\n"
        f"    (implementation_runShell {cp}) := by\n"
        "  unfold problem_spec_runShell implementation_runShell specArgs specPgEnv\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_runShell` statement byte-identical and closes with the
    # FROZEN proof body (no proof authoring, no helper lemma, no assumption).
    # =====================================================================
    {
        "id": "pos-local-reshape-env",
        "kind": "soundness",
        "expect": "verify",
        # Read the supplied secret value into a typed local first, then inject it
        # (read-then-append shape instead of the inline append). Definitionally
        # identical to the frozen loop body, so the frozen proof still closes.
        "module": _swap(
            _BASE, _I_PW,
            '  if cp.password    ≠ "" then\n'
            '    let v := cp.password\n'
            '    pgEnv := pgEnv ++ [("PGPASSWORD",    v)]'),
        "rationale": "structurally-different CORRECT impl: the secret parameter's "
                     "value is bound to a typed local then injected (read-then-append "
                     "shape) instead of the inline append. Same behavior on every "
                     "input, so C-args and C-env both still hold — else SPEC-TOO-STRONG "
                     "(over-fit to the inline-append form). Definitionally the frozen "
                     "loop body, so the frozen proof closes; statement byte-identical, "
                     "no new axiom/lemma. Ports nagini's pos-local-reshape.",
    },
    {
        "id": "pos-local-reshape-args",
        "kind": "soundness",
        "expect": "verify",
        # The C-args analogue of the above: read the routing value into a local
        # then append its flag pair. Defends the argument-vector clause with a
        # correct reshape (the nagini carrier had no such clause to defend).
        "module": _swap(
            _BASE, _I_USER,
            '  if cp.user ≠ "" then\n'
            '    let u := cp.user\n'
            '    args := args ++ ["-U", u]'),
        "rationale": "structurally-different CORRECT impl on the argument-vector side: "
                     "the routing value is bound to a typed local then its flag pair is "
                     "appended. Same behavior, so C-args and C-env both hold — else "
                     "SPEC-TOO-STRONG. Frozen proof closes; statement byte-identical, no "
                     "new axiom/lemma. Defends C-args, which the nagini carrier does not "
                     "model (added positive; see assessment).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition, so
    # the nagini precondition-admission self-call re-expresses as: discharge the
    # spec predicate by evaluation at the F2P transport-security combination as a
    # `have`, then close the frozen obligation verbatim. Nothing is assumed: no
    # new declaration, statement byte-identical, ground instance is a `have`
    # prepended to the existing tactic body.
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _ground : problem_spec_runShell '
            '{ sslmode := "verify-ca", sslrootcert := "root.crt", '
            'sslcert := "client.crt", sslkey := "client.key" }\n'
            '      (implementation_runShell '
            '{ sslmode := "verify-ca", sslrootcert := "root.crt", '
            'sslcert := "client.crt", sslkey := "client.key" }) := by\n'
            '    unfold problem_spec_runShell implementation_runShell '
            'specArgs specPgEnv\n'
            '    decide\n'
            + _P_INTRO),
        "rationale": "the obligation is discharged at the F2P transport-security "
                     "combination (all four SSL parameters supplied) by evaluation as a "
                     "`have`, then the frozen obligation is closed verbatim. Verifies, "
                     "else the modeled behavior would be unsatisfiable at exactly a "
                     "normal F2P input (the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, statement byte-identical, ground "
                     "instance is a `have` in the existing tactic body. Ports nagini's "
                     "admiss-selfcall.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: inject only the password, none of the SSL params ----
    {
        "id": "rival-prepatch-only-password",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: inject PGPASSWORD only; drop the four transport-security
        # injections entirely.
        "module": _swap(
            _swap(_swap(_swap(_BASE, _I_MODE + "\n", ""),
                        _I_CERT + "\n", ""),
                  _I_KEY + "\n", ""),
            '  if cp.sslrootcert ≠ "" then pgEnv := pgEnv ++ '
            '[("PGSSLROOTCERT", cp.sslrootcert)]\n', ""),
        "refinement": "this IS the pre-fix behavior: only the password is injected and "
                      "none of the transport-security parameters. Its faithful real "
                      "patch is the unmodified assembler (no SSL parameter reads or "
                      "environment injections). The F2P case drives the assembler with a "
                      "transport-security-configured connection and asserts the captured "
                      "PG* environment is EXACTLY the four SSL entries; the pre-fix "
                      "assembler injects NONE of them, so the assertion mismatches. It "
                      "would NOT resolve (this is exactly the defect the fix repairs).",
        "rationale": "REJECT from C-env: with a transport-security parameter supplied, "
                     "specPgEnv lists its entry but the rival's pgEnv omits it, so "
                     "`result.pgEnv = specPgEnv cp` fails. Refuted at cp with "
                     "sslmode='verify-ca' (rival pgEnv=[], spec pgEnv=[(PGSSLMODE,…)]).",
        "witness": _wit('{ sslmode := "verify-ca" }'),
    },

    # ---- drop a single parameter's injection (partial-domain) ----
    {
        "id": "rival-drop-sslkey",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on four of the five secret/SSL parameters; omits the client
        # private key's injection entirely.
        "module": _swap(_BASE, _I_KEY + "\n", ""),
        "refinement": "PARTIAL-DOMAIN: injects password + the first three transport "
                      "parameters correctly but omits the client private key's "
                      "injection. Its faithful real patch forgets one parameter's "
                      "environment write (a partial feature implementation). The F2P "
                      "case supplies the client key and asserts its entry is present in "
                      "the captured PG* environment; the rival's environment is missing "
                      "it, so the assertion mismatches. It would NOT resolve.",
        "rationale": "REJECT from C-env on the client-key sub-domain: when that "
                     "parameter is supplied, specPgEnv appends its entry but the rival "
                     "never does, so `result.pgEnv = specPgEnv cp` fails. Refuted at cp "
                     "with sslkey='k'.",
        "witness": _wit('{ sslkey := "k" }'),
    },

    # ---- inject a spurious extra entry (no-spurious clause) ----
    {
        "id": "rival-spurious-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Inject all five parameters correctly BUT also add an extra environment
        # entry unconditionally, under a name that is none of the five dedicated
        # library variables.
        "module": _swap(
            _BASE, _I_ENVINIT + "\n",
            _I_ENVINIT + "\n  pgEnv := pgEnv ++ [(\"PGEXTRA\", \"x\")]\n"),
        "refinement": "injects all five parameters correctly but ALSO adds one extra "
                      "environment entry outside the dedicated set. Its faithful real "
                      "patch writes some additional environment variable beyond the "
                      "modeled ones. The F2P case asserts the captured PG* environment "
                      "EQUALS exactly the expected set (not a superset); an extra entry "
                      "makes the sets unequal, so the assertion mismatches. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C-env (no-spurious): specPgEnv lists only the entries "
                     "for supplied modeled parameters, but the rival's pgEnv carries an "
                     "extra ('PGEXTRA','x'), so `result.pgEnv = specPgEnv cp` fails even "
                     "when no parameter is supplied. Refuted at the empty cp "
                     "(rival pgEnv=[('PGEXTRA','x')], spec pgEnv=[]).",
        "witness": _wit('{ }'),
    },

    # ---- inject a parameter's variable with a wrong (blanked) value ----
    {
        "id": "rival-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Inject PGPASSWORD's ENTRY (present iff supplied) but with a constant
        # blank value instead of the supplied one — presence correct, value wrong.
        "module": _swap(
            _BASE, _I_PW,
            '  if cp.password    ≠ "" then pgEnv := pgEnv ++ '
            '[("PGPASSWORD",    "")]'),
        "refinement": "injects the password variable when supplied but carries a "
                      "constant blank value instead of the supplied secret (presence "
                      "correct, value wrong). Its faithful real patch sets the variable "
                      "to a fixed/placeholder string rather than the parameter's value. "
                      "A PASS_TO_PASS case asserts the captured environment carries the "
                      "SUPPLIED password value; the rival carries the placeholder, so "
                      "the assertion mismatches. It would NOT resolve.",
        "rationale": "REJECT from C-env (value): specPgEnv pins the entry value to "
                     "cp.password, but the rival emits the blank '', so "
                     "`result.pgEnv = specPgEnv cp` fails whenever the supplied value is "
                     "non-blank. Refuted at cp with password='pw' "
                     "(rival [(PGPASSWORD,'')], spec [(PGPASSWORD,'pw')]).",
        "witness": _wit('{ password := "pw" }'),
    },

    # ---- cross-wire one parameter's variable onto another's guard/source ----
    {
        "id": "rival-crosswire-sslcert",
        "kind": "uniqueness",
        "expect": "reject",
        # Inject the client-certificate VARIABLE keyed off the SSL-mode parameter
        # (guard and source both the security-mode parameter), dropping the genuine
        # client-certificate injection.
        "module": _swap(
            _BASE, _I_CERT,
            '  if cp.sslmode     ≠ "" then pgEnv := pgEnv ++ '
            '[("PGSSLCERT",     cp.sslmode)]'),
        "refinement": "cross-wires the client-certificate variable: it is injected when "
                      "the SECURITY-MODE parameter is supplied, carrying that "
                      "parameter's value, and the genuine client-certificate injection "
                      "is dropped. Its faithful real patch is a copy-paste wiring bug "
                      "(the cert variable guarded/sourced by the mode parameter). Under "
                      "the F2P case, which supplies BOTH the mode and the client "
                      "certificate, the cert variable carries the mode value (and its "
                      "position/value are wrong), so the captured environment mismatches "
                      "the expected set. It would NOT resolve. Pins that each parameter "
                      "maps to its OWN distinct variable.",
        "rationale": "REJECT from C-env (cross-wire): specPgEnv injects the cert entry "
                     "iff the cert parameter is supplied, sourced from it; the rival "
                     "ties it to the mode parameter, so with only the mode supplied the "
                     "rival's pgEnv carries a spurious (PGSSLCERT, mode) entry that "
                     "specPgEnv lacks, and `result.pgEnv = specPgEnv cp` fails. Refuted "
                     "at cp with sslmode='m'.",
        "witness": _wit('{ sslmode := "m" }'),
    },

    # ---- ADDED: attack the argument-vector clause (C-args) ----
    {
        "id": "rival-drop-dbname",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the final database-name append, so the argument vector is missing
        # its last element. Attacks C-args — the clause the nagini carrier does
        # not model at all.
        "module": _swap(_BASE, _I_DBNAME + "\n", ""),
        "refinement": "omits the database name from the argument vector. Its faithful "
                      "real patch drops the trailing database-name argument, so the "
                      "interactive client is launched with no database to connect to. "
                      "The PASS_TO_PASS cases assert the exact argument list including "
                      "the database name last; the rival's list is missing it, so the "
                      "assertion mismatches. It would NOT resolve.",
        "rationale": "REJECT from C-args: specArgs always appends cp.dbname last, but "
                     "the rival's args omit it, so `result.args = specArgs cp` fails. "
                     "Refuted at cp with dbname='db' (rival args=['psql'], spec "
                     "args=['psql','db']). One of three rivals exercising C-args.",
        "witness": _wit('{ dbname := "db" }'),
    },

    # ---- cross-wire WITHIN the argument vector (C-args value clause) ----
    # AUDIT-ADDED. The pre-audit battery attacked C-args only by DELETION
    # (drop-dbname). Deletion leaves the per-parameter VALUE wiring of the
    # routing flags unprobed: a rival could pair the right flag with the wrong
    # parameter's value and no existing case would notice. Verified by hand:
    # module build exit 1, witness exit 0 against the rival and exit 1 on the
    # frozen solution with `decide` reporting the concrete claim false.
    {
        "id": "rival-crosswire-port-value",
        "kind": "uniqueness",
        "expect": "reject",
        # The routing-port flag is emitted under the right guard but carries the
        # HOST parameter's value instead of the port's.
        "module": _swap(
            _BASE, _I_PORT,
            '  if cp.port ≠ "" then args := args ++ ["-p", cp.host]'),
        "refinement": "the routing-port flag is emitted when the port parameter is "
                      "supplied but carries the HOST parameter's value. Its faithful "
                      "real patch is a copy-paste wiring bug in the argument-vector "
                      "assembly (right flag, wrong source parameter). The PASS_TO_PASS "
                      "cases assert the exact argument list, in which the port flag is "
                      "followed by the port value and the host flag by the host value; "
                      "the rival emits the host value in the port position, so the list "
                      "comparison mismatches. It would NOT resolve.",
        "rationale": "REJECT from C-args (value wiring): specArgs pairs the port flag "
                     "with cp.port, but the rival pairs it with cp.host, so "
                     "`result.args = specArgs cp` fails whenever both are supplied and "
                     "differ. Refuted at cp with port='444', host='h' (rival args end "
                     "['-h','h','-p','h','']; spec ['-h','h','-p','444','']). Probes the "
                     "per-parameter value wiring of C-args, which the deletion rival "
                     "leaves untouched.",
        "witness": _wit('{ port := "444", host := "h" }'),
    },

    # ---- drop the absence guard: inject unconditionally (C-env presence) ----
    # AUDIT-ADDED. Every pre-audit C-env rival attacks a SUPPLIED parameter
    # (omission, wrong value, cross-wire) or adds an entry under a name outside
    # the modeled set. None attacks the ABSENCE direction for a modeled variable:
    # an impl that always injects a dedicated variable, blank when the parameter
    # is unsupplied. That is the presence biconditional's other half, and it is
    # the shape a real "just always set it" patch takes. Verified by hand: module
    # build exit 1, witness exit 0 against the rival and exit 1 on the frozen
    # solution with `decide` reporting the concrete claim false.
    {
        "id": "rival-uncond-inject",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the non-emptiness guard on the secret parameter: its variable is
        # injected on every invocation, blank when the parameter is unsupplied.
        "module": _swap(
            _BASE, _I_PW,
            '  pgEnv := pgEnv ++ [("PGPASSWORD",    cp.password)]'),
        "refinement": "injects the secret's variable UNCONDITIONALLY, so an invocation "
                      "with no secret configured still publishes it, bound to the empty "
                      "string. Its faithful real patch omits the supplied-ness test and "
                      "always writes the variable. A PASS_TO_PASS case drives a "
                      "connection with NO secret and asserts the captured PG* "
                      "environment is EMPTY; the rival publishes a blank entry, so the "
                      "assertion mismatches. It would NOT resolve.",
        "rationale": "REJECT from C-env (absence half of the presence biconditional): "
                     "specPgEnv contributes nothing for an unsupplied parameter, but the "
                     "rival appends its entry regardless, so "
                     "`result.pgEnv = specPgEnv cp` fails at any cp whose secret is "
                     "absent. Refuted at cp with user='u' and no secret (rival "
                     "pgEnv=[(PGPASSWORD,'')], spec pgEnv=[]). Distinct from "
                     "rival-spurious-entry, which adds a name OUTSIDE the modeled set: "
                     "here a MODELED variable is published when it must be absent.",
        "witness": _wit('{ user := "u" }'),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation rival, 4 uniqueness
# rivals) plus 2 AXIOM cases. This bundle models the SAME purely-functional core
# but over a carrier that ALSO models the command-line argument vector, so the
# accounting is:
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-reorder                  -> (none)                     DROPPED (see below)
#   pos-local-reshape            -> pos-local-reshape-env       PORTED
#   (none)                       -> pos-local-reshape-args      ADDED (defends C-args)
#   admiss-selfcall              -> admiss-f2p-ground           RE-EXPRESSED
#   rival-frame-mutate-input     -> (none)                     VACUOUS (see below)
#   rival-prepatch-only-password -> rival-prepatch-only-password PORTED
#   rival-drop-sslkey            -> rival-drop-sslkey           PORTED
#   rival-spurious-key           -> rival-spurious-entry        PORTED
#   rival-wrong-value            -> rival-wrong-value           PORTED
#   rival-crosswire-sslcert      -> rival-crosswire-sslcert     PORTED
#   (none)                       -> rival-drop-dbname           ADDED (attacks C-args)
#   (none)                       -> rival-crosswire-port-value  AUDIT-ADDED (C-args value)
#   (none)                       -> rival-uncond-inject         AUDIT-ADDED (C-env absence)
#   AXIOM_TESTS (2)              -> (none)                     DROPPED (G-AX)
#
# DROPPED (pos-reorder): the nagini reorder positive publishes the five settings
#   in REVERSE order and is correct THERE because nagini's carrier is a DICT
#   (unordered) — key order does not matter. This lean carrier models the injected
#   environment as an ORDERED LIST of (name, value) pairs, and the postcondition
#   pins `result.pgEnv = specPgEnv cp` where specPgEnv fixes the injection ORDER.
#   Reversing the injection sequence produces a DIFFERENT list, so the frozen spec
#   REJECTS it and it cannot be carried as a soundness positive here.
#   AUDIT CORRECTION. The pre-audit note above called this a clean CARRIER reason
#   and claimed the lean model is legitimately "strictly stronger". That reading is
#   wrong and the audit measured it: the reorder impl is not merely unprovable on
#   this carrier, it genuinely VIOLATES C-env (a witness stating the violation at
#   the four-parameter transport-security input elaborates against it, exit 0),
#   while the same reorder is a FAITHFUL implementation of the modeled behavior —
#   injection order is not observable, since the entries are consumed as a
#   name-keyed mapping and every official assertion compares them as such. So the
#   drop is forced, but what forces it is an over-strong clause in the FROZEN spec,
#   not a distinction the carrier legitimately keeps. Recorded as a spec finding
#   (see the CAVEAT in the module docstring); NOT repaired here, because the spec is
#   frozen and a spec change must re-clear the equivalence and leakage gates.
#   In its place the two local-reshape positives supply honest
#   structurally-different correct controls that DO verify.
# RE-EXPRESSED (admiss-f2p-ground): the sibling self-call establishes the callee
#   precondition under the caller's half-permission. The frozen lean theorem
#   carries NO precondition (it is ∀ cp, …), so the honest analogue is to show the
#   modeled behavior is SATISFIABLE at a normal F2P input: discharge the spec
#   predicate at the four-SSL-parameter combination the F2P test uses, as a `have`,
#   then close the frozen obligation verbatim.
# VACUOUS (rival-frame-mutate-input): the sibling's mandatory frame-mutation rival
#   writes back onto its read-only input to be caught by the fractional-permission
#   system. Lean is referentially transparent — `cp` is an immutable value, there
#   is no `mut` input binder, no aliasing, no read-only cell to overwrite — so the
#   permission-mutation class is VACUOUS here. The frame obligation is discharged
#   structurally instead: C-args/C-env pin the result ENTIRELY as a function of
#   `cp`, so no output component is left unconstrained. No substitute is fabricated.
# ADDED (pos-local-reshape-args, rival-drop-dbname): the nagini carrier models
#   ONLY the environment publication; this lean carrier ALSO models the
#   command-line argument vector (C-args). This backend's coverage tool requires
#   every top-level clause DEFENDED and ATTACKED, so C-args gets a correct-reshape
#   positive and a drop-dbname rival. These are not fabricated for an unmodeled
#   behavior — they attack/defend a real, load-bearing clause of the SAME modeled
#   spec that the nagini carrier simply did not represent.
#
# AUDIT-ADDED (rival-crosswire-port-value, rival-uncond-inject): an independent
#   audit found two unattacked directions and closed them. C-args was attacked
#   only by DELETION, leaving the per-parameter VALUE wiring of the routing flags
#   unprobed (a right-flag/wrong-source rival was unrefuted by every existing
#   case); and every C-env rival attacked a SUPPLIED parameter or a name outside
#   the modeled set, leaving the ABSENCE half of the presence biconditional for a
#   MODELED variable unprobed. Both new rivals were verified with real builds:
#   module exit 1, witness exit 0 against the rival, witness exit 1 on the frozen
#   solution with `decide` reporting the concrete claim false.
#
# POINT SPREAD. The eight reject witnesses probe eight DISTINCT cp values (pts=8):
#   { sslmode := "verify-ca" }     rival-prepatch-only-password   C-env
#   { sslkey := "k" }              rival-drop-sslkey              C-env
#   { }                            rival-spurious-entry           C-env
#   { password := "pw" }           rival-wrong-value              C-env
#   { sslmode := "m" }             rival-crosswire-sslcert        C-env
#   { dbname := "db" }             rival-drop-dbname              C-args
#   { port := "444", host := "h" } rival-crosswire-port-value     C-args  (added)
#   { user := "u" }                rival-uncond-inject            C-env   (added)
#   Distinct fields of the single `cp` binder are exercised (sslmode, sslkey,
#   password, dbname, port+host, user, the empty record), so no field is held
#   fixed across every witness, and the two added points are the only ones that
#   bind TWO fields at once (the cross-wire needs both to differ). Both top-level
#   clauses are attacked (C-env by six rivals, C-args by two) and both are
#   defended by a positive control. Each clause is now attacked in more than one
#   DIRECTION: C-env by omission, wrong value, cross-wire, spurious name and
#   unconditional injection; C-args by deletion and by wrong value wiring.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (every op is modeled deeply — mapping.md: axioms=[], no A-reference), so
# there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
