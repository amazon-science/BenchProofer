# properties.py — G-PBT falsification battery for django__django-10973 (lean).
# Ported from the nagini sibling battery; re-expressed against this backend's
# carrier. NOT a Lean module — a record of adversarial cases the spec-lane gate
# executes, each editing ONLY the impl region (and, for positives, the proof
# body) of the frozen Solution.lean, so `same_spec` holds by construction.
#
# Defended surface (this backend's model):
#   dbShellCommand(host port dbname user passwd : String)
#       -> (List String × Option String)
#   The observable pair handed to the child process: (args_vector, password_env).
#   The spec has TWO independent top-level clauses:
#     (C1) args_vector = ["psql"] ++ (-U user if user≠"") ++ (-h host if host≠"")
#          ++ (-p port if port≠"") ++ [dbname]        # binders: user, host, port, dbname
#     (C2) password_env = (none if passwd="" else some passwd)   # binder: passwd
#
# CARRIER NOTE — this bundle models MORE than the nagini sibling. Nagini abstracts
# only the password copy (its `password_env_value`); this backend also models the
# full argument vector (C1). So the nagini password cases port to C2 rivals, and
# C1 gets fresh rivals with no nagini counterpart — required to vary every binder
# and attack every clause. Chasing nagini's case list would UNDER-cover C1.
#
# VACUOUS LANES (stated, not fabricated):
#   * FRAME-MUTATION: nagini's mandatory frame-mut-write rival (a write-back into
#     the read-only Acc(...,1/2) input) has NO counterpart here. Lean is
#     referentially transparent — no aliasing, no fractional permission — so there
#     is no "write to an input" a rival could perform. Omitted, legitimately.
#   * AXIOM_TESTS: the axiom lane is G-AX's job; this gate ignores it. The model
#     has no `opaque` callee and no consumed axiom, so there is nothing to test.
#
# ADMISSIBILITY IS *NOT* VACUOUS HERE — see `admiss-ground`. "The frozen
# obligation carries no precondition, so there is nothing to admit" is the wrong
# analogue on a total carrier. The thing PRECOND-TOO-STRONG detects here is the
# obligation being UNSATISFIABLE at exactly an F2P-shaped input, which is a real
# and checkable risk: the two clauses are exact equalities over a `String`
# carrier whose `≠ ""` guards and `Option` conditional could in principle be
# jointly unsatisfiable at a concrete point while the ∀-statement still elaborates
# through a case split. `admiss-ground` discharges the spec predicate at one
# concrete fully-populated input BY EVALUATION (`decide`), as a `have`, before
# closing the frozen obligation verbatim — so it tests satisfiability at a real
# point rather than restating the theorem.
#
# WITNESS — every reject case carries a Lean `example` refuting the rival at ONE
# concrete `decide`-able input. It is checked in a file with the proof obligation
# stripped, and must (1) elaborate against the rival and (2) FAIL against the
# frozen solution, so it is a real discriminator and not a tautology. All witness
# inputs use short literals so `decide` reduces without opaque terms. Password
# transforms are spelled over `passwd.data` (structural) rather than
# `String.replace` (well-founded recursion `decide` cannot reduce).
from pathlib import Path

INSTANCE = "django__django-10973"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl-region def, verbatim (everything the impl markers enclose).
# Every variant _swap()s inside here (and, for the soundness positive, the proof
# tactic body). The spec view elides both regions, so same_spec is guaranteed.
_IMPL = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some passwd
  return (args, passwordEnv)"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The frozen proof tactic body (everything after `:= by`). Only the soundness
# positive touches this — the reject rivals keep the frozen script untouched
# (their rejection is attested by the witness, not by the tactic breakage the
# reshaped impl would otherwise cause).
_PROOF = """\
  intro host port dbname user passwd
  unfold problem_spec_dbShellCommand implementation_dbShellCommand
  refine ⟨?_, ?_⟩ <;>
    simp only [Id.run, ne_eq] <;>
    by_cases hu : user = "" <;> by_cases hh : host = "" <;>
      by_cases hp : port = "" <;> by_cases hpw : passwd = "" <;>
      simp only [hu, hh, hp, hpw, not_true, not_false_iff,
        if_neg, if_pos] <;> rfl"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY the impl-region def replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof):
    """Full Solution.lean with the impl def AND the proof tactic body replaced.

    The `theorem correct_dbShellCommand : ... := by` STATEMENT stays byte-identical;
    only the tactics after `:= by` change (rule 2).
    """
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVE — must VERIFY.
# ---------------------------------------------------------------------------

# pos-functional: a structurally-different but behaviourally-identical impl. It
# builds the pair DIRECTLY as a pure functional expression (no `Id.run do`, no
# `let mut`, no `for`/`if`-statement mutation), matching the spec's own shape, and
# is reproven with a two-line `exact ⟨rfl, rfl⟩`. Both clauses hold verbatim. If it
# fails => SPEC-TOO-STRONG (a faithful correct impl rejected).
_POS_IMPL = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String :=
  (["psql"]
      ++ (if user ≠ "" then ["-U", user] else [])
      ++ (if host ≠ "" then ["-h", host] else [])
      ++ (if port ≠ "" then ["-p", port] else [])
      ++ [dbname],
   if passwd = "" then none else some passwd)"""

_POS_PROOF = """\
  intro host port dbname user passwd
  unfold problem_spec_dbShellCommand implementation_dbShellCommand
  exact ⟨rfl, rfl⟩"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY POSITIVE — must VERIFY.
# ---------------------------------------------------------------------------

# admiss-ground: the impl region is left FROZEN (byte-identical to gold); only the
# tactic body is prefixed with a ground instance. It discharges the spec predicate
# at ONE concrete fully-populated input — every one of the five binders non-empty,
# with a colon-bearing password and a numeric port, i.e. the shape of a normal
# connection the F2P suite drives — by evaluation (`decide`), as a `have`, and then
# closes the frozen obligation verbatim with the unchanged frozen script.
#
# This is the total-carrier analogue of nagini's admiss-reads. Nothing is assumed:
# no new declaration, no axiom, the theorem STATEMENT is byte-identical, and the
# ground instance is a `have` inside the existing tactic body. If it FAILS, the
# modeled obligation is unsatisfiable at exactly an F2P-shaped input — the
# PRECOND-TOO-STRONG direction, which no `expect="reject"` case can detect and
# which the soundness positive does not test either (that one varies the IMPL and
# reproves the same ∀-statement; this one pins a concrete POINT of the domain).
_ADMISS_PROOF = (
    '  have _ground : problem_spec_dbShellCommand "h" "444" "db" "u" "p:w"\n'
    '      (implementation_dbShellCommand "h" "444" "db" "u" "p:w") := by\n'
    '    unfold problem_spec_dbShellCommand implementation_dbShellCommand\n'
    '    decide\n'
) + _PROOF


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each changes ONLY the impl region; the frozen proof body is left intact.
# ---------------------------------------------------------------------------

# --- Clause C2 (password_env) ---

# pw-colon: the pre-patch escaping reborn — expose the password with its colon
# separators escaped (':' -> '\\:'), spelled over passwd.data so `decide` reduces.
# Correct on every colon-free password, wrong on any password containing a colon.
_C2_COLON = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  let escaped : String :=
    ⟨passwd.data.flatMap (fun c => if c = ':' then ['\\\\', ':'] else [c])⟩
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some escaped
  return (args, passwordEnv)"""

# pw-uncond: always provisions the password, even when it is empty. Attacks the
# empty->none direction of C2's conditional.
_C2_UNCOND = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  let passwordEnv : Option String := some passwd
  return (args, passwordEnv)"""

# pw-forgot: never provisions the password. Attacks the nonempty->some direction
# of C2's conditional (the "forgot to set the env entry" mistake).
_C2_FORGOT = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  let passwordEnv : Option String := none
  return (args, passwordEnv)"""

# --- Clause C1 (args_vector) ---

# args-drop-user: omits the -U user flag/value entirely. Attacks the `user` binder.
_C1_DROP_USER = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some passwd
  return (args, passwordEnv)"""

# args-uncond-host: appends the -h host flag UNCONDITIONALLY, even when host is
# empty. Attacks the emptiness guard on the `host` binder.
_C1_UNCOND_HOST = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some passwd
  return (args, passwordEnv)"""

# args-order: swaps the host and port segments (port emitted before host). Attacks
# C1's positional ordering, jointly exercising the `host` and `port` binders.
_C1_ORDER = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if port ≠ "" then
    args := args ++ ["-p", port]
  if host ≠ "" then
    args := args ++ ["-h", host]
  args := args ++ [dbname]
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some passwd
  return (args, passwordEnv)"""

# args-drop-port: omits the -p port flag/value entirely. Attacks the `port` binder,
# which no other rival varies on its OWN: args-order moves the port segment but
# keeps it present (and needs host non-empty too), so a spec that had dropped the
# port requirement while keeping the ordering of what remains would survive every
# other case here. Correct on every portless connection, wrong whenever a port is
# supplied — a true partial-domain break.
_C1_DROP_PORT = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  args := args ++ [dbname]
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some passwd
  return (args, passwordEnv)"""

# args-drop-dbname: omits the unconditional trailing dbname. Attacks the `dbname`
# binder (the one segment with no emptiness guard).
_C1_DROP_DBNAME = """\
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some passwd
  return (args, passwordEnv)"""


def _wit(host, port, dbname, user, passwd):
    """A refutation `example`: the spec predicate is FALSE at this concrete input
    for the rival impl. `decide` closes it; it fails on gold (which satisfies the
    spec everywhere), making it a real discriminator."""
    return (
        f'example : ¬ problem_spec_dbShellCommand "{host}" "{port}" "{dbname}" '
        f'"{user}" "{passwd}"\n'
        f'    (implementation_dbShellCommand "{host}" "{port}" "{dbname}" '
        f'"{user}" "{passwd}") := by\n'
        f'  unfold problem_spec_dbShellCommand implementation_dbShellCommand\n'
        f'  decide'
    )


SPEC_TESTS = [
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_IMPL, _POS_PROOF),
        "rationale": (
            "a structurally-different correct impl: the output pair is built as a "
            "pure functional expression (no Id.run/let mut/if-statement mutation), "
            "matching the spec's own shape, and reproven with `exact ⟨rfl, rfl⟩`. "
            "Both clauses (C1 args vector, C2 password) hold verbatim. If it fails "
            "=> SPEC-TOO-STRONG (a faithful correct impl rejected). The "
            "theorem STATEMENT is byte-identical; only the tactic body changed."
        ),
    },
    {
        "id": "admiss-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(_IMPL, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at ONE concrete fully-populated input — "
            "all five binders non-empty, colon-bearing password, numeric port, the "
            "shape of a normal connection — by evaluation as a `have`, before the "
            "frozen obligation is closed verbatim by the unchanged frozen script. "
            "The impl region is byte-identical to the frozen one; only the tactic "
            "body gains the ground instance. Verifies (else the modeled behavior "
            "would be unsatisfiable at exactly an F2P-shaped input, the "
            "PRECOND-TOO-STRONG direction that no reject case can detect and that "
            "the soundness positive does not test — that one varies the impl and "
            "reproves the same ∀-statement, this one pins a concrete point of the "
            "domain). Ports nagini's admiss-reads to a total carrier."
        ),
    },
    {
        "id": "pw-colon",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_C2_COLON),
        "refinement": (
            "this is the PRE-PATCH behaviour: the password run through the legacy "
            "separator-escaping (':' doubled with a leading backslash). Its faithful "
            "real patch is the unpatched code path, which exposes an escaped "
            "'some\\\\:password' where the F2P test with a colon-bearing password now "
            "asserts the RAW 'some:password'. Correct on every colon-free password "
            "(the other F2P inputs), so a true PARTIAL-DOMAIN break, not a blanket "
            "wrong impl. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C2 (password_env = some passwd): at a password containing a "
            "colon the exposed value gains an extra backslash code point, so it is "
            "not `some passwd`. Attacks the passwd binder on the colon sub-domain — "
            "exactly the boundary a byte-fuzzer would not isolate."
        ),
        "witness": _wit("", "", "d", "", "a:b"),
    },
    {
        "id": "pw-uncond",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_C2_UNCOND),
        "refinement": (
            "a real patch that set the password environment entry UNCONDITIONALLY "
            "(dropping the truthiness guard) would provision an empty value for a "
            "no-password connection, where the F2P no-password test asserts the "
            "entry is ABSENT (None). Correct on every non-empty password, so a true "
            "partial-domain break. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C2's empty->none direction: at passwd=\"\" the rival returns "
            "`some \"\"` while the spec demands `none`. Varies the passwd binder at "
            "the empty boundary, the value the frozen impl's guard exists to handle."
        ),
        "witness": _wit("", "", "d", "", ""),
    },
    {
        "id": "pw-forgot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_C2_FORGOT),
        "refinement": (
            "a real patch that never provisioned the password for the child (the "
            "'forgot to set the environment entry' mistake) exposes nothing for "
            "every non-empty password, failing every F2P that asserts the actual "
            "password reaches the child. Does NOT resolve. Cheap near-miss attacking "
            "the opposite direction of the C2 conditional from pw-uncond."
        ),
        "rationale": (
            "REJECTED by C2's nonempty->some direction: at passwd=\"x\" the rival "
            "returns `none` while the spec demands `some \"x\"`. Varies the passwd "
            "binder on the non-empty sub-domain."
        ),
        "witness": _wit("", "", "d", "", "x"),
    },
    {
        "id": "args-drop-user",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_C1_DROP_USER),
        "refinement": (
            "an impl that omitted the user flag/value from the client argument "
            "vector would produce a command line missing '-U <user>', failing every "
            "F2P that asserts the exact argument list for a connection with a user. "
            "This clause is modeled by THIS backend though the gold change did not "
            "touch it; the F2P tests still pin the whole vector, so a verifying rival "
            "here is a genuine verify-does-not-resolve break. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C1: at user=\"u\" the spec requires '-U' and 'u' in the "
            "vector but the rival omits them, so result.1 differs. Varies the `user` "
            "binder (held empty by every other reject witness)."
        ),
        "witness": _wit("", "", "d", "u", ""),
    },
    {
        "id": "args-uncond-host",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_C1_UNCOND_HOST),
        "refinement": (
            "an impl that appended the host flag unconditionally would emit an empty "
            "'-h' segment for a hostless connection, diverging from the exact "
            "argument vector the F2P tests assert for that case. Correct whenever a "
            "host is supplied, so a partial-domain break. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C1's host emptiness guard: at host=\"\" the spec omits the "
            "'-h' segment but the rival appends '-h' and '', so result.1 differs. "
            "Varies the `host` binder at its empty boundary."
        ),
        "witness": _wit("", "", "d", "", ""),
    },
    {
        "id": "args-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_C1_ORDER),
        "refinement": (
            "an impl that emitted the port segment before the host segment would "
            "reorder the client argument vector, failing every F2P that asserts the "
            "exact ordered argument list for a connection specifying both host and "
            "port. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C1's positional ordering: with both host and port supplied "
            "the rival yields [..., '-p', port, '-h', host, ...] while the spec fixes "
            "'-h' before '-p'. Jointly varies the `host` and `port` binders (both "
            "non-empty here, unlike every other witness)."
        ),
        "witness": _wit("h", "p", "d", "", ""),
    },
    {
        "id": "args-drop-port",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_C1_DROP_PORT),
        "refinement": (
            "an impl that omitted the port flag/value from the client argument "
            "vector would produce a command line missing '-p <port>', failing every "
            "F2P that asserts the exact argument list for a connection specifying a "
            "port. Correct on every portless connection, so a partial-domain break. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C1: at port=\"444\" the spec requires '-p' and '444' in the "
            "vector but the rival omits them, so result.1 differs. Varies the `port` "
            "binder ALONE — args-order relocates the port segment but keeps it "
            "present and needs host non-empty too, so without this case a spec that "
            "dropped the port requirement while pinning the order of the rest would "
            "survive the whole battery."
        ),
        "witness": _wit("", "444", "d", "", ""),
    },
    {
        "id": "args-drop-dbname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_C1_DROP_DBNAME),
        "refinement": (
            "an impl that dropped the trailing database name would produce a command "
            "line missing its final positional argument, failing every F2P (all of "
            "which supply a database name and assert it as the last argument). Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by C1's unconditional trailing dbname: the rival's result.1 is "
            "missing the final [dbname] element. Varies the `dbname` binder (the one "
            "C1 segment with no emptiness guard)."
        ),
        "witness": _wit("", "", "d2", "", ""),
    },
]

# No opaque callee, no consumed axiom in this bundle's proof; the axiom lane is
# G-AX's responsibility and this gate ignores it.
AXIOM_TESTS = []
