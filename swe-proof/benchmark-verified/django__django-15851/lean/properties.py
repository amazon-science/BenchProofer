# properties.py — G-PBT falsification battery for django__django-15851 (lean).
# Ported from the nagini sibling battery and re-expressed against this backend's
# carrier. NOT a Lean module — a record of adversarial cases the spec-lane gate
# executes, each editing ONLY the impl region (and, for the positive, the proof
# body) of the frozen Solution.lean, so `same_spec` holds by construction.
#
# Defended surface (this backend's model):
#   shellArgs (executable : String) (user host port dbname : Option String)
#             (parameters : List String) -> List String
#   The single obligation `correct_shellArgs` pins the returned vector with ONE
#   top-level clause (an equality), so every rival attacks the same clause; what
#   distinguishes them is which INPUT BINDER each abuses:
#     result = [executable]
#                ++ optFlag "-U" user ++ optFlag "-h" host ++ optFlag "-p" port
#                ++ parameters
#                ++ dbname.toList
#   binders: executable, user, host, port, dbname, parameters.
#
# CARRIER NOTE — this bundle models MORE than the nagini sibling. Nagini abstracts
# the program-name/flag "prefix" and the extra "parameters" as two opaque int
# lists; this backend models each connection option (user/host/port) as its own
# optional-flag contribution and the trailing database name as its own optional.
# So the nagini ordering attack (extras vs the trailing token) ports to the
# principal rival here, and the per-option binders get fresh rivals with no
# nagini counterpart — required to vary every binder and keep the single clause
# attacked from every side. Chasing nagini's case list alone would UNDER-cover
# the option binders this carrier exposes.
#
# VACUOUS LANES (stated, not fabricated):
#   * FRAME-MUTATION: nagini's MANDATORY frame-mutation rivals (a write-back
#     through a read-only half-permission input) have NO counterpart here. Lean is
#     referentially transparent — no aliasing, no fractional permission — so there
#     is no "write to an input" a rival could even express. Omitted, legitimately.
#   * DIVERGENCE / NON-TERMINATION: no counterpart is landable here. This carrier
#     is a plain Lean file, so totality is enforced by the ELABORATOR, not by a
#     discharged obligation: a recursive helper with no decreasing measure is
#     rejected at definition time (`fail to show termination for ...`), so the
#     rival module never compiles and no witness could be checked against it. The
#     only way to write one is `partial`, which does not model divergence — it
#     yields a TOTAL but opaque function, observationally equal to the frozen impl
#     wherever the diverging branch is unreachable, so it is not a WRONG rival
#     either. Measured, not assumed. Omitted for the carrier's reason.
#
# ADMISSIBILITY (present, NOT omitted): this obligation is `∀ inputs, spec (impl
#   inputs)` with no hypothesis, so there is no precondition to admit in the
#   nagini sense. The analogue on a total carrier is the obligation being
#   UNSATISFIABLE at exactly a normal, use-shaped input, which is a real failure
#   mode and is tested directly by `admiss-shaped-input`: it discharges the
#   obligation at one concrete such input BY EVALUATION as a `have`, then closes
#   the frozen obligation verbatim. See that case.
#   * AXIOM_TESTS: the axiom lane is G-AX's job; this gate ignores it. The model
#     has no `opaque` callee and no consumed axiom (the reordering is modeled
#     deeply as list concatenation), so there is nothing to test.
#
# WITNESS — every reject case carries a Lean `example` refuting the rival at ONE
# concrete `decide`-able input. It is checked in a file with the proof obligation
# stripped, and must (1) elaborate against the rival and (2) FAIL against the
# frozen solution, so it is a real discriminator, not a tautology. Every witness
# input uses short literals so `decide` reduces without any opaque term.
from pathlib import Path

INSTANCE = "django__django-15851"

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
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  args := args ++ parameters
  if let some d := dbname then
    args := args ++ [d]
  return args"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The frozen proof tactic body (everything after `:= by`). Only the soundness
# positive touches this — the reject rivals keep the frozen script intact (their
# rejection is attested by the witness, not by the tactic breakage a reshaped
# impl would otherwise cause).
_PROOF = """\
  intro executable user host port dbname parameters
  unfold problem_spec_shellArgs implementation_shellArgs optFlag
  cases user <;> cases host <;> cases port <;> cases dbname <;>
    simp only [Id.run, Option.toList, bind, pure, List.nil_append,
      List.cons_append, List.append_nil]"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY the impl-region def replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof):
    """Full Solution.lean with the impl def AND the proof tactic body replaced.

    The `theorem correct_shellArgs : ... := by` STATEMENT stays byte-identical;
    only the tactics after `:= by` change (rule 2).
    """
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


def _wit(ex, user, host, port, dbname, params):
    """A refutation `example`: the spec predicate is FALSE at this concrete input
    for the rival impl. `decide` closes it; it fails on gold (which satisfies the
    spec everywhere), making it a real discriminator. Arguments are pre-formatted
    Lean fragments (`'"psql"'`, `'none'`, `'(some "d")'`, `'["x"]'`)."""
    args = f'{ex} {user} {host} {port} {dbname} {params}'
    return (
        f'example : ¬ problem_spec_shellArgs {args}\n'
        f'    (implementation_shellArgs {args}) := by\n'
        f'  unfold problem_spec_shellArgs implementation_shellArgs optFlag\n'
        f'  decide'
    )


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVE — must VERIFY.
# ---------------------------------------------------------------------------

# pos-functional: a structurally-different but behaviourally-identical impl. It
# builds the vector DIRECTLY as a pure functional expression (no `Id.run do`, no
# `let mut`, no `if let` statement mutation), spelling each optional contribution
# as an explicit `match` that is definitionally the spec's own `optFlag` /
# `Option.toList`. Reproven by casing the optionals and `rfl`. It computes the
# exact same vector, so it MUST verify; else SPEC-TOO-STRONG (a faithful correct
# impl rejected).
_POS_IMPL = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String :=
  [executable]
    ++ (match user with | none => [] | some u => ["-U", u])
    ++ (match host with | none => [] | some h => ["-h", h])
    ++ (match port with | none => [] | some p => ["-p", p])
    ++ parameters
    ++ (match dbname with | none => [] | some d => [d])"""

_POS_PROOF = """\
  intro executable user host port dbname parameters
  unfold problem_spec_shellArgs implementation_shellArgs optFlag
  cases user <;> cases host <;> cases port <;> cases dbname <;>
    simp only [Option.toList, List.nil_append, List.cons_append,
      List.append_nil]"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY POSITIVE — must VERIFY.
# ---------------------------------------------------------------------------

# admiss-shaped-input: the frozen obligation carries no hypothesis, so there is
# no precondition to admit in the fractional-permission sense. The analogue on
# this total carrier is the obligation being UNSATISFIABLE at exactly a normal,
# use-shaped input — a spec so tight that no impl could meet it there would
# still let the frozen file build (the ∀ would be closed by the very tactic that
# is tuned to it) while making the modeled behavior unrealizable in practice.
# This case tests that directly: it discharges `problem_spec_shellArgs` at ONE
# concrete input of the shape the fix's own regression exercises — a database
# name present AND the caller-supplied parameter list non-empty, the exact
# combination where the ordering clause is load-bearing — BY EVALUATION
# (`decide`, no appeal to the frozen ∀), as a `have` placed before the frozen
# tactic body, which then closes the obligation verbatim. Nothing is assumed:
# no new declaration, no axiom, statement byte-identical, impl region untouched
# (it is the frozen impl). If the `have` cannot close => the spec is
# unsatisfiable at a normal input, the PRECOND-TOO-STRONG analogue.
_ADMISS_PROOF = """\
  have _shaped : problem_spec_shellArgs "psql" none none none (some "d")
      ["--param"]
      (implementation_shellArgs "psql" none none none (some "d")
        ["--param"]) := by
    unfold problem_spec_shellArgs implementation_shellArgs optFlag
    decide
""" + _PROOF


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each changes ONLY the impl region; the frozen proof body is left intact.
# ---------------------------------------------------------------------------

# atk-params-after-dbname: the PRINCIPAL reasoned attack (the nagini ordering
# rival). The caller-supplied parameters are contributed AFTER the trailing
# database name instead of before it. Correct whenever there is no database name
# OR no parameters; wrong exactly when both are present. Ports nagini's
# "pre-patch ordering" case.
_R_PARAMS_AFTER_DBNAME = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  if let some d := dbname then
    args := args ++ [d]
  args := args ++ parameters
  return args"""

# atk-drop-dbname: never contribute the trailing database name. Correct whenever
# no database name is present; wrong when one is. Ports nagini's "drop-dbname".
_R_DROP_DBNAME = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  args := args ++ parameters
  return args"""

# atk-drop-executable: omit the leading program name. Attacks the `executable`
# binder — the one element the vector must always begin with.
_R_DROP_EXECUTABLE = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args : List String := []
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  args := args ++ parameters
  if let some d := dbname then
    args := args ++ [d]
  return args"""

# atk-drop-user: omit the -U user option entirely. Attacks the `user` binder.
_R_DROP_USER = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  args := args ++ parameters
  if let some d := dbname then
    args := args ++ [d]
  return args"""

# atk-uncond-host: contribute the -h host option UNCONDITIONALLY, even when the
# host setting carries no value. Attacks the emptiness guard on the `host` binder.
_R_UNCOND_HOST = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  args := args ++ ["-h", host.getD ""]
  if let some p := port then
    args := args ++ ["-p", p]
  args := args ++ parameters
  if let some d := dbname then
    args := args ++ [d]
  return args"""

# atk-order-host-port: emit the port option before the host option. Attacks the
# positional ordering, jointly exercising the `host` and `port` binders.
_R_ORDER_HOST_PORT = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some p := port then
    args := args ++ ["-p", p]
  if let some h := host then
    args := args ++ ["-h", h]
  args := args ++ parameters
  if let some d := dbname then
    args := args ++ [d]
  return args"""

# atk-params-before-prefix: contribute the caller-supplied parameters BEFORE the
# program name (and before all options). Attacks the `parameters` position and
# the requirement that the vector lead with the program name. Ports nagini's
# "prefix-after-params" ordering rival to this carrier.
_R_PARAMS_BEFORE_PREFIX = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := parameters
  args := args ++ [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  if let some d := dbname then
    args := args ++ [d]
  return args"""


# atk-drop-params: never contribute the caller-supplied parameters at all.
# Attacks the `parameters` binder at its PRESENCE (rather than its position):
# every other rival that touches `parameters` misplaces it, so the requirement
# that the sequence be contributed AT ALL was unattacked. Correct whenever the
# parameter list is empty (a partial-domain break).
_R_DROP_PARAMS = """\
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  if let some d := dbname then
    args := args ++ [d]
  return args"""


SPEC_TESTS = [
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_IMPL, _POS_PROOF),
        "rationale": (
            "a structurally-different correct impl: the vector is built as a pure "
            "functional concatenation (no Id.run/let mut/if-let mutation), each "
            "optional contribution spelled as a `match` definitionally equal to "
            "the spec's own optFlag / Option.toList, reproven by casing the "
            "optionals and `rfl`. It computes the exact same vector, so it must "
            "verify; if it fails => SPEC-TOO-STRONG (a faithful correct impl "
            "rejected). The theorem STATEMENT is byte-identical; only the tactic "
            "body changed."
        ),
    },
    {
        "id": "admiss-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(_IMPL, _ADMISS_PROOF),
        "rationale": (
            "the obligation is DISCHARGED at one concrete use-shaped input — a "
            "database name present and a non-empty caller-supplied parameter "
            "list, the combination where the ordering clause is load-bearing — "
            "by evaluation (`decide`), as a `have` placed before the frozen "
            "tactic body, which then closes the frozen obligation verbatim. The "
            "frozen obligation carries no hypothesis, so there is no "
            "fractional-permission precondition to admit; the analogue on this "
            "total carrier is the spec being UNSATISFIABLE at exactly such an "
            "input, which this case rules out directly. Verifies; if the `have` "
            "could not close => the modeled behavior is unrealizable at a normal "
            "input, the PRECOND-TOO-STRONG analogue. Nothing is assumed: no new "
            "declaration, no axiom, the theorem STATEMENT is byte-identical, and "
            "the impl region is the frozen impl untouched — only the tactic body "
            "gains the ground instance (rule 2)."
        ),
    },
    {
        "id": "atk-drop-params",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_DROP_PARAMS),
        "refinement": (
            "an impl that never contributes the caller-supplied parameters "
            "silently discards everything the caller asked to pass through, so "
            "the client program is launched without them. It FAILS the test that "
            "supplies a parameter and asserts it in the vector, so its faithful "
            "real patch does NOT resolve. Correct whenever the parameter list is "
            "empty (a partial-domain break), so not a blanket-wrong impl."
        ),
        "rationale": (
            "REJECTED by the `++ parameters` portion of the clause: with a "
            "non-empty parameter list the spec splices the sequence in, but the "
            "rival omits it. Varies the `parameters` binder at its PRESENCE "
            "rather than its position — every other rival touching `parameters` "
            "misplaces the sequence, so the requirement that it be contributed "
            "at all was otherwise unattacked. Held with the database name absent "
            "so only the missing sequence differs."
        ),
        "witness": _wit('"psql"', "none", "none", "none", "none", '["x"]'),
    },
    {
        "id": "atk-params-after-dbname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_PARAMS_AFTER_DBNAME),
        "refinement": (
            "this is the pre-fix ordering: the caller-supplied parameters are "
            "contributed AFTER the trailing database name. The client program "
            "ignores every token that follows the database name, so those "
            "parameters are silently dropped — precisely the defect the change "
            "corrects. Its faithful real patch produces [prog, ..., dbname, "
            "*parameters] where the F2P test now asserts [prog, ..., *parameters, "
            "dbname]; it FAILS that test, so a verifying rival is a genuine "
            "verify-does-not-resolve break. Correct whenever no database name or "
            "no parameters are present (a true partial-domain break), so not a "
            "blanket-wrong impl."
        ),
        "rationale": (
            "REJECTED by the ordering clause: with a database name present and a "
            "non-empty parameter list the rival yields [..., dbname] ++ parameters "
            "while the spec requires parameters ++ [dbname]. Jointly varies the "
            "`dbname` (some) and `parameters` (non-empty) binders — the sub-domain "
            "where the two orderings diverge."
        ),
        "witness": _wit('"psql"', "none", "none", "none", '(some "d")', '["x"]'),
    },
    {
        "id": "atk-drop-dbname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_DROP_DBNAME),
        "refinement": (
            "an impl that never contributes the trailing database name produces a "
            "command line missing its final positional argument, so the client "
            "connects to the wrong/default database. It FAILS the tests that "
            "supply a database name and assert it as the last token, so its "
            "faithful real patch does NOT resolve. Correct whenever no database "
            "name is present (a partial-domain break)."
        ),
        "rationale": (
            "REJECTED by the trailing-dbname portion of the clause: with a "
            "database name present the spec ends the vector with `dbname.toList` = "
            "[d], but the rival omits it. Varies the `dbname` binder (present), "
            "holding parameters empty so ONLY the missing trailing token differs."
        ),
        "witness": _wit('"psql"', "none", "none", "none", '(some "d")', "[]"),
    },
    {
        "id": "atk-drop-executable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_DROP_EXECUTABLE),
        "refinement": (
            "an impl that omits the leading program name emits a vector whose "
            "first token is no longer the client program, so it is never invoked "
            "correctly. It FAILS every test (all assert the program name leads), "
            "so its faithful real patch does NOT resolve. This element is modeled "
            "by THIS backend though the change did not touch it; the tests still "
            "pin the whole vector, so a verifying rival here is a genuine "
            "verify-does-not-resolve break."
        ),
        "rationale": (
            "REJECTED by the leading-`[executable]` portion of the clause: the "
            "rival's vector never begins with the program name. Varies the "
            "`executable` binder (probed at a distinct value from the other "
            "witnesses so no rival holds it fixed)."
        ),
        "witness": _wit('"pg"', "none", "none", "none", "none", "[]"),
    },
    {
        "id": "atk-drop-user",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_DROP_USER),
        "refinement": (
            "an impl that omits the -U user option produces a command line lacking "
            "the connecting user, diverging from the exact vector the tests assert "
            "for a connection carrying a user. Correct whenever no user is present "
            "(a partial-domain break), so a genuine verify-does-not-resolve break "
            "rather than a blanket-wrong impl."
        ),
        "rationale": (
            "REJECTED by the `optFlag \"-U\" user` portion of the clause: at a "
            "present user the spec inserts [\"-U\", u] but the rival omits it. "
            "Varies the `user` binder (present), held absent by every other "
            "witness."
        ),
        "witness": _wit('"psql"', '(some "u")', "none", "none", "none", "[]"),
    },
    {
        "id": "atk-uncond-host",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_UNCOND_HOST),
        "refinement": (
            "an impl that contributes the -h host option unconditionally emits an "
            "empty '-h ' segment for a connection without a host, diverging from "
            "the exact vector the tests assert for that case. Correct whenever a "
            "host is present (a partial-domain break)."
        ),
        "rationale": (
            "REJECTED by the emptiness guard in `optFlag \"-h\" host`: at an absent "
            "host the spec contributes nothing but the rival appends [\"-h\", \"\"]. "
            "Varies the `host` binder at its absent boundary — the value the guard "
            "exists to handle."
        ),
        "witness": _wit('"psql"', "none", "none", "none", "none", "[]"),
    },
    {
        "id": "atk-order-host-port",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_ORDER_HOST_PORT),
        "refinement": (
            "an impl that emits the port option before the host option reorders "
            "the vector, failing every test that asserts the exact ordered vector "
            "for a connection specifying both a host and a port. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the positional ordering of the clause: with both a host "
            "and a port present the rival yields [..., \"-p\", p, \"-h\", h, ...] "
            "while the spec fixes \"-h\" before \"-p\". Jointly varies the `host` "
            "and `port` binders (both present here, unlike every other witness)."
        ),
        "witness": _wit('"psql"', "none", '(some "h")', '(some "p")', "none", "[]"),
    },
    {
        "id": "atk-params-before-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R_PARAMS_BEFORE_PREFIX),
        "refinement": (
            "an impl that contributes the caller-supplied parameters before the "
            "program name places the program name after the user-supplied tokens, "
            "so the first vector token is a parameter, not the program. It FAILS "
            "every test (all assert the program name leads), so its faithful real "
            "patch does NOT resolve. Correct only when the parameter list is empty."
        ),
        "rationale": (
            "REJECTED by the clause's fixing the vector to begin with [executable] "
            "then the options then `parameters`: this rival builds parameters ++ "
            "[executable] ++ ..., so with a non-empty parameter list the leading "
            "token is a parameter. Varies the `parameters` binder (non-empty), "
            "here holding the database name absent so the difference is isolated "
            "to the leading position."
        ),
        "witness": _wit('"psql"', "none", "none", "none", "none", '["z"]'),
    },
]

# No opaque callee, no consumed axiom in this bundle's proof (the reordering is
# modeled deeply as list concatenation); the axiom lane is G-AX's responsibility
# and this gate ignores it.
AXIOM_TESTS = []
