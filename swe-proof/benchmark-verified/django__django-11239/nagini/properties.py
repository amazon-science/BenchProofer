"""properties.py — PBT falsification manifest for django__django-11239.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical"). The battery is
reasoned from THIS spec's defended surface, not stamped out by a corruption
template.

The function under spec
-----------------------
    build_pg_env(conn_params: Dict[int, int]) -> Dict[int, int]

models the PostgreSQL process-environment publication the gold patch adds to
`DatabaseClient.runshell_db`. For each of the five recognised connection
settings it publishes the dedicated PG* environment variable iff that setting is
supplied (token present in the input mapping), carrying the value verbatim:

    setting_password()=0    -> envvar_password()=100      (PGPASSWORD)
    setting_sslmode()=1     -> envvar_sslmode()=101        (PGSSLMODE)
    setting_sslrootcert()=2 -> envvar_sslrootcert()=102    (PGSSLROOTCERT)
    setting_sslcert()=3     -> envvar_sslcert()=103        (PGSSLCERT)
    setting_sslkey()=4      -> envvar_sslkey()=104         (PGSSLKEY)

The input is READ-ONLY: Requires(Acc(dict_pred(conn_params), 1/2)) and the
postcondition GIVES BACK that half-permission (Ensures(Acc(dict_pred(
conn_params), 1/2))). So the frame-mutation attack (directive 5) APPLIES and is
MANDATORY: an impl that WRITES to conn_params to satisfy a postcondition
vacuously must be REJECTED for insufficient permission.

The load-bearing postcondition clauses (model.py:121-147)
---------------------------------------------------------
For each setting X in {password, sslmode, sslrootcert, sslcert, sslkey}:
  (Bx) (envvar_X() in Result()) == (setting_X() in conn_params)
       — the PRESENCE biconditional: the variable is published iff the setting
         is supplied. The four SSL biconditionals are the DISCRIMINATING clauses
         (model_prepatch publishes only PGPASSWORD and FAILS the first SSL one).
  (Vx) Implies(setting_X() in conn_params,
               Result()[envvar_X()] == conn_params[setting_X()])
       — the VALUE clause: when published, the value is verbatim.
  (NS) Forall e: e in Result() => e is one of the five envvar tokens
       — NO-SPURIOUS-KEYS: the result holds no key outside the five names.

The oracle is GROUNDED, not an answer-key
-----------------------------------------
There is NO @Pure answer-key that returns the whole published mapping; the
postcondition pins Result() entirely as a function of `conn_params` (membership +
per-key value) via the five biconditionals + value clauses + no-spurious Forall.
The @Pure helpers (setting_*/envvar_*) are bare constant tokens (0..4, 100..104),
not an oracle that does the work. So there is no opaque oracle an impl could echo
WITHOUT doing the publication — building the mapping IS the work, and any echo
that disagrees with the biconditionals/value/no-spurious clauses is rejected.
Hence ungrounded-oracle ECHO does not apply (directive 2); instead we supply
honest cheapest-correct positive controls (reordered writes / local-reshape) that
MUST verify. Stated in the StructuredOutput assessment.

No control-flow / raise / side-effect difference is observable
--------------------------------------------------------------
`build_pg_env` is total over its precondition domain (any Dict[int,int]); it
never raises and has no side effect other than building the fresh result dict
(and it must NOT touch the read-only input — see frame-mutation). The real callee
`runshell_db` does launch a subprocess, but the modeled behaviour is exactly the
PG* publication carried in the returned mapping (mapping.md §2/§A7); the subprocess
launch is outside the value abstraction and is exercised in the AXIOM lane (the
real callee is driven there). The control-flow-effect class therefore does not
apply to the SPEC lane; stated in 'assessment'.

Axiom lane
----------
meta.axioms == [] (NO @ContractOnly axiom): the publication is modeled DEEPLY.
The single soundness obligation is the A-reference — the deep model == the real
`DatabaseClient.runshell_db` PG* publication on the F2P/P2P domain. The AXIOM_TESTS
reuse + strengthen axiom_check.py (which the runner does NOT mount in-container, so
the probes are SELF-CONTAINED): (1) axiom-soundness drives the GENUINE
`runshell_db` (subprocess.run intercepted, exactly as the repo's own
tests/dbshell/test_postgresql.py does) on boundary + fuzz connection-parameter
mappings and asserts the published PG* mapping == the deep model; (2)
axiom-containment confirms every callee-input the MODEL can reach (any subset of
the five settings, supplied or absent/empty) is handled by the real callee
without raising.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY text inside build_pg_env's `# impl-start` / `# impl-end` body, so
`markers.same_spec` is GUARANTEED and a rejection is attributable to the
POSTCONDITION / the permission system catching wrong behaviour, never to a
tampered spec. Each `expect:"reject"` rival carries the refinement argument that
its faithful real patch would NOT resolve the F2P/P2P.
"""
from pathlib import Path

INSTANCE = "django__django-11239"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The full gold impl body (the five conditional publications + return), captured
# as one unique anchor in model.py. Positive controls and structural rivals swap
# this whole block; targeted rivals swap a single conditional within it.
# ---------------------------------------------------------------------------
_GOLD_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    if setting_password() in conn_params:\n"
    "        env[envvar_password()] = conn_params[setting_password()]\n"
    "    if setting_sslmode() in conn_params:\n"
    "        env[envvar_sslmode()] = conn_params[setting_sslmode()]\n"
    "    if setting_sslrootcert() in conn_params:\n"
    "        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]\n"
    "    if setting_sslcert() in conn_params:\n"
    "        env[envvar_sslcert()] = conn_params[setting_sslcert()]\n"
    "    if setting_sslkey() in conn_params:\n"
    "        env[envvar_sslkey()] = conn_params[setting_sslkey()]\n"
    "    return env\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) REORDER positive control. Publish the five settings in REVERSE order
# (sslkey first ... password last). The publication is straight-line (no loop /
# no invariant to preserve), so there is no proof obligation to drop; only the
# executable ORDER of the five independent conditional writes changes. Each write
# is to a DISTINCT key (the five envvar tokens never collide), so order is
# irrelevant to the result and every biconditional/value/no-spurious clause holds
# exactly as for gold. If this CORRECT impl fails to verify, the postcondition is
# over-fit to the gold write order => SPEC-TOO-STRONG.
_POS_REORDER_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    if setting_sslkey() in conn_params:\n"
    "        env[envvar_sslkey()] = conn_params[setting_sslkey()]\n"
    "    if setting_sslcert() in conn_params:\n"
    "        env[envvar_sslcert()] = conn_params[setting_sslcert()]\n"
    "    if setting_sslrootcert() in conn_params:\n"
    "        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]\n"
    "    if setting_sslmode() in conn_params:\n"
    "        env[envvar_sslmode()] = conn_params[setting_sslmode()]\n"
    "    if setting_password() in conn_params:\n"
    "        env[envvar_password()] = conn_params[setting_password()]\n"
    "    return env\n"
)
_POS_REORDER = _swap(_BASE, _GOLD_BODY, _POS_REORDER_BODY)

# (5b) LOCAL-RESHAPE positive control. For each setting, read the supplied value
# into a typed local first, then publish it — a different data shape (read-then-
# write via a local) instead of the inline `env[k] = conn_params[k]`. Same
# behaviour. If it fails => SPEC-TOO-STRONG (over-fit to the inline-write form).
_POS_LOCAL_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    if setting_password() in conn_params:\n"
    "        v0 = conn_params[setting_password()]  # type: int\n"
    "        env[envvar_password()] = v0\n"
    "    if setting_sslmode() in conn_params:\n"
    "        v1 = conn_params[setting_sslmode()]  # type: int\n"
    "        env[envvar_sslmode()] = v1\n"
    "    if setting_sslrootcert() in conn_params:\n"
    "        v2 = conn_params[setting_sslrootcert()]  # type: int\n"
    "        env[envvar_sslrootcert()] = v2\n"
    "    if setting_sslcert() in conn_params:\n"
    "        v3 = conn_params[setting_sslcert()]  # type: int\n"
    "        env[envvar_sslcert()] = v3\n"
    "    if setting_sslkey() in conn_params:\n"
    "        v4 = conn_params[setting_sslkey()]  # type: int\n"
    "        env[envvar_sslkey()] = v4\n"
    "    return env\n"
)
_POS_LOCAL = _swap(_BASE, _GOLD_BODY, _POS_LOCAL_BODY)

# (6) ADMISSIBILITY. A self-call build_pg_env(conn_params) on the in-scope
# F2P-shaped input (a Dict[int,int] under the half-permission the caller holds)
# must establish the precondition. The caller holds Acc(dict_pred(conn_params),
# 1/2) — EXACTLY the callee's Requires — and the callee Ensures it back, so after
# the probe the caller still holds its half-permission and the real publication
# runs unchanged. We Assert the probe is non-None (its own postcondition) to pin
# that the call site succeeded. If the call site cannot establish the Requires for
# a legitimate input => PRECOND-TOO-STRONG. We prepend BEFORE the gold body's
# first line (the unique `env = {}` anchor).
_ENV_INIT_ANCHOR = "    env = {}  # type: Dict[int, int]\n"
_ADMISS_PREFIX = (
    "    _probe = build_pg_env(conn_params)\n"
    "    Assert(_probe is not None)\n"
    + _ENV_INIT_ANCHOR
)
_ADMISS = _swap(_BASE, _ENV_INIT_ANCHOR, _ADMISS_PREFIX)


# ===========================================================================
# FRAME-MUTATION (MANDATORY) + UNIQUENESS RIVALS — expect "reject"
# ===========================================================================

# (FRAME-MUTATION — MANDATORY, directive 5) Before publishing, the rival WRITES
# back onto the read-only input `conn_params` (overwriting the sslmode setting's
# value with the password's, mutating the caller's connection-parameter mapping in
# place), then publishes from it. To assign `conn_params[...] = ...` Nagini needs
# FULL permission on conn_params, but the precondition grants only Acc(dict_pred(
# conn_params), 1/2). The write is REJECTED for INSUFFICIENT PERMISSION — before
# any postcondition is even considered. The gold publications are otherwise kept
# verbatim so the rejection is attributable solely to the input write.
#
# Refinement (why its faithful real patch would NOT resolve): the half-permission
# Acc(dict_pred(conn_params), 1/2) abstracts the gold patch's contract that
# `runshell_db` READS `conn_params` (`conn_params.get('sslmode','')` etc.) and
# does NOT mutate the caller's `conn_params` dict — it builds a SEPARATE
# `subprocess_env` mapping. A real patch that wrote back into `conn_params` (e.g.
# `conn_params['sslmode'] = conn_params['password']` before publishing) would
# corrupt the caller's connection settings, which are reused for the actual DB
# connection / aliased by the connection object — publishing the password's value
# under PGSSLMODE and clobbering the configured sslmode. The F2P test_ssl_certificate
# supplies sslmode='verify-ca' and asserts PGSSLMODE == 'verify-ca'; a clobber to
# the password value gives PGSSLMODE == <password> (or nothing if no password),
# so the test FAILS. It would NOT resolve. The half-permission is exactly the spec
# defending that read-only contract.
_RIVAL_FRAME_MUTATE_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    if setting_password() in conn_params:\n"
    "        conn_params[setting_sslmode()] = conn_params[setting_password()]\n"
    "        env[envvar_password()] = conn_params[setting_password()]\n"
    "    if setting_sslmode() in conn_params:\n"
    "        env[envvar_sslmode()] = conn_params[setting_sslmode()]\n"
    "    if setting_sslrootcert() in conn_params:\n"
    "        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]\n"
    "    if setting_sslcert() in conn_params:\n"
    "        env[envvar_sslcert()] = conn_params[setting_sslcert()]\n"
    "    if setting_sslkey() in conn_params:\n"
    "        env[envvar_sslkey()] = conn_params[setting_sslkey()]\n"
    "    return env\n"
)
_RIVAL_FRAME_MUTATE = _swap(_BASE, _GOLD_BODY, _RIVAL_FRAME_MUTATE_BODY)

# (uniqueness — PRE-PATCH bug) Publish ONLY the password and never the four TLS
# settings — exactly model_prepatch.py (the pre-patch runshell_db that wrote only
# PGPASSWORD). Satisfies the password biconditional/value, the no-spurious clause,
# and (vacuously) the absent SSL biconditionals only when no SSL setting is
# supplied — but VIOLATES every SSL biconditional (Bsslmode, ...) whenever the
# corresponding setting IS supplied (then envvar_X() not in Result() though
# setting_X() in conn_params).
#
# Refinement: this IS the pre-patch behaviour; its faithful real patch is the
# unmodified runshell_db (no `sslmode = conn_params.get('sslmode','')` reads, no
# `if sslmode: subprocess_env['PGSSLMODE'] = str(sslmode)` writes). Under it the
# F2P test_ssl_certificate — a TLS-configured connection — yields an empty PG*
# dict {} instead of {PGSSLMODE, PGSSLROOTCERT, PGSSLCERT, PGSSLKEY}: the
# assertEqual FAILS. It would NOT resolve (this is exactly the bug the patch fixes,
# G-DIFF / model_prepatch).
_RIVAL_PREPATCH_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    if setting_password() in conn_params:\n"
    "        env[envvar_password()] = conn_params[setting_password()]\n"
    "    return env\n"
)
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_BODY, _RIVAL_PREPATCH_BODY)

# (uniqueness — PARTIAL-DOMAIN, the sslkey setting) Publish password + sslmode +
# sslrootcert + sslcert correctly but OMIT the sslkey publication entirely. Correct
# on four of the five settings; diverges only on the sslkey sub-domain. Violates
# the sslkey biconditional Bsslkey: when setting_sslkey() in conn_params, the gold
# requires envvar_sslkey() in Result(), but this rival never publishes it.
#
# Refinement: its faithful real patch is a runshell_db that adds the sslmode/
# sslrootcert/sslcert publications but FORGETS the `if sslkey: subprocess_env[
# 'PGSSLKEY'] = str(sslkey)` write (a partial implementation of the feature). Under
# it the F2P test_ssl_certificate — which supplies sslkey='client.key' and asserts
# 'PGSSLKEY': 'client.key' is in the published PG* dict — gets a dict MISSING
# PGSSLKEY: the assertEqual FAILS. It would NOT resolve.
_RIVAL_DROP_SSLKEY_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    if setting_password() in conn_params:\n"
    "        env[envvar_password()] = conn_params[setting_password()]\n"
    "    if setting_sslmode() in conn_params:\n"
    "        env[envvar_sslmode()] = conn_params[setting_sslmode()]\n"
    "    if setting_sslrootcert() in conn_params:\n"
    "        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]\n"
    "    if setting_sslcert() in conn_params:\n"
    "        env[envvar_sslcert()] = conn_params[setting_sslcert()]\n"
    "    return env\n"
)
_RIVAL_DROP_SSLKEY = _swap(_BASE, _GOLD_BODY, _RIVAL_DROP_SSLKEY_BODY)

# (uniqueness — NO-SPURIOUS-KEYS) Publish all five settings correctly BUT also
# publish an extra environment variable under a token (200) that is NOT one of the
# five dedicated names, unconditionally. Satisfies all five biconditionals + value
# clauses, but VIOLATES the no-spurious Forall (NS): 200 in Result() yet 200 is
# none of envvar_password()/sslmode()/sslrootcert()/sslcert()/sslkey().
#
# Refinement: its faithful real patch is a runshell_db that, besides the five
# dedicated writes, ALSO publishes some extra `subprocess_env['PGSOMETHING'] = ...`
# (a credential/transport-security variable outside the five). The F2P
# test_ssl_certificate asserts the published PG* dict EQUALS exactly
# {PGSSLMODE, PGSSLROOTCERT, PGSSLCERT, PGSSLKEY} (assertEqual, not subset), and
# the P2P test_basic asserts exactly {PGPASSWORD: 'somepassword'} — an extra PG*
# key makes the dicts unequal: the assertEqual FAILS. It would NOT resolve. (The
# extra token 200 publishes no real-world variable; it stands for any spurious PG*
# key the spec forbids.)
_RIVAL_SPURIOUS_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    env[200] = 0\n"
    "    if setting_password() in conn_params:\n"
    "        env[envvar_password()] = conn_params[setting_password()]\n"
    "    if setting_sslmode() in conn_params:\n"
    "        env[envvar_sslmode()] = conn_params[setting_sslmode()]\n"
    "    if setting_sslrootcert() in conn_params:\n"
    "        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]\n"
    "    if setting_sslcert() in conn_params:\n"
    "        env[envvar_sslcert()] = conn_params[setting_sslcert()]\n"
    "    if setting_sslkey() in conn_params:\n"
    "        env[envvar_sslkey()] = conn_params[setting_sslkey()]\n"
    "    return env\n"
)
_RIVAL_SPURIOUS = _swap(_BASE, _GOLD_BODY, _RIVAL_SPURIOUS_BODY)

# (uniqueness — VALUE clause) Publish the password variable, but with a CONSTANT
# value (0) instead of the supplied one. Satisfies the password presence
# biconditional (PGPASSWORD present iff supplied) but VIOLATES the value clause
# Vpassword: when setting_password() in conn_params and conn_params[...] != 0,
# Result()[envvar_password()] == 0 != conn_params[setting_password()].
#
# Refinement: its faithful real patch is a runshell_db that publishes
# subprocess_env['PGPASSWORD'] = <a fixed/placeholder string> instead of
# str(passwd) — the variable is present but carries the wrong value. Under it the
# P2P test_basic asserts {'PGPASSWORD': 'somepassword'} but observes the
# placeholder: the assertEqual FAILS. It would NOT resolve. (The presence-only
# biconditional alone does NOT pin the value; the value clause does.)
_RIVAL_WRONG_VALUE_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    if setting_password() in conn_params:\n"
    "        env[envvar_password()] = 0\n"
    "    if setting_sslmode() in conn_params:\n"
    "        env[envvar_sslmode()] = conn_params[setting_sslmode()]\n"
    "    if setting_sslrootcert() in conn_params:\n"
    "        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]\n"
    "    if setting_sslcert() in conn_params:\n"
    "        env[envvar_sslcert()] = conn_params[setting_sslcert()]\n"
    "    if setting_sslkey() in conn_params:\n"
    "        env[envvar_sslkey()] = conn_params[setting_sslkey()]\n"
    "    return env\n"
)
_RIVAL_WRONG_VALUE = _swap(_BASE, _GOLD_BODY, _RIVAL_WRONG_VALUE_BODY)

# (uniqueness — CROSS-WIRED setting, value-level mis-mapping) Publish the sslcert
# variable keyed off the WRONG setting: it writes PGSSLCERT (envvar_sslcert) when
# the SSLMODE setting is supplied, carrying the sslmode value, and drops the
# genuine sslcert publication. So envvar_sslcert() in Result() tracks setting_sslmode()
# rather than setting_sslcert(). VIOLATES the sslcert biconditional Bsslcert: a
# connection supplying sslmode but NOT sslcert publishes PGSSLCERT (present though
# setting_sslcert() absent); and a connection supplying sslcert but NOT sslmode
# omits PGSSLCERT (absent though setting_sslcert() present).
#
# Refinement: its faithful real patch is a runshell_db with a copy-paste wiring
# bug — `if sslmode: subprocess_env['PGSSLCERT'] = str(sslmode)` (wrong guard /
# wrong source for the cert variable). Under the F2P test_ssl_certificate the
# connection supplies BOTH sslmode='verify-ca' and sslcert='client.crt', so the
# published PGSSLCERT would be 'verify-ca' (the sslmode value), not 'client.crt':
# the assertEqual FAILS. It would NOT resolve. This pins that each setting maps to
# its OWN distinct variable (settings never collide).
_RIVAL_CROSSWIRE_BODY = (
    "    env = {}  # type: Dict[int, int]\n"
    "    if setting_password() in conn_params:\n"
    "        env[envvar_password()] = conn_params[setting_password()]\n"
    "    if setting_sslmode() in conn_params:\n"
    "        env[envvar_sslmode()] = conn_params[setting_sslmode()]\n"
    "        env[envvar_sslcert()] = conn_params[setting_sslmode()]\n"
    "    if setting_sslrootcert() in conn_params:\n"
    "        env[envvar_sslrootcert()] = conn_params[setting_sslrootcert()]\n"
    "    if setting_sslkey() in conn_params:\n"
    "        env[envvar_sslkey()] = conn_params[setting_sslkey()]\n"
    "    return env\n"
)
_RIVAL_CROSSWIRE = _swap(_BASE, _GOLD_BODY, _RIVAL_CROSSWIRE_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT impl: the five independent "
                  "conditional publications are emitted in REVERSE order. Each targets a "
                  "DISTINCT envvar token (never colliding), so order is irrelevant to the "
                  "result and every biconditional/value/no-spurious clause holds as for gold. "
                  "Straight-line code, no loop invariant to drop. If it fails to verify, the "
                  "postcondition is over-fit to the gold write order => SPEC-TOO-STRONG."},
    {"id": "pos-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "structurally-different but CORRECT impl: each supplied value is read into a "
                  "typed local then published (read-then-write shape instead of the inline "
                  "env[k]=conn_params[k]). Same behaviour. Must verify, else the spec is "
                  "over-fit to the inline-write form => SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call build_pg_env(conn_params) on the in-scope F2P-shaped input (a "
                  "Dict[int,int] under the half-permission the caller holds and the callee "
                  "Ensures back) must establish the precondition and return a non-None mapping; "
                  "if the call site cannot establish the Requires for a legitimate input => "
                  "PRECOND-TOO-STRONG."},

    # ---- frame-mutation (MANDATORY) + uniqueness rivals (must be REJECTED) ----
    {"id": "rival-frame-mutate-input", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_MUTATE,
     "refinement": "WRITES back onto the read-only input conn_params "
                   "(conn_params[setting_sslmode()] = conn_params[setting_password()]) before "
                   "publishing. The half-permission Acc(dict_pred(conn_params), 1/2) abstracts "
                   "the gold contract that runshell_db READS conn_params "
                   "(conn_params.get('sslmode','') etc.) and builds a SEPARATE subprocess_env, "
                   "never mutating the caller's connection-parameter dict. A real patch that "
                   "clobbered conn_params['sslmode'] with the password value would corrupt the "
                   "connection settings (reused/aliased by the connection object) and publish "
                   "the wrong PGSSLMODE; the F2P test_ssl_certificate asserts "
                   "PGSSLMODE == 'verify-ca' and would observe the password value (or nothing): "
                   "the test FAILS. It would NOT resolve.",
     "rationale": "FRAME-MUTATION (directive 5). Rejection source: the PERMISSION SYSTEM — "
                  "assigning conn_params[...] needs full Acc(dict_pred(conn_params)) but the "
                  "precondition grants only 1/2, so the write fails for INSUFFICIENT PERMISSION "
                  "before any postcondition is considered. If it verified, a mutating impl "
                  "could satisfy the postcondition vacuously => SPEC-TOO-WEAK."},
    {"id": "rival-prepatch-only-password", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "publishes ONLY PGPASSWORD and never the four TLS variables — exactly "
                   "model_prepatch.py (the pre-patch runshell_db). Its faithful real patch is "
                   "the unmodified runshell_db (no sslmode/sslrootcert/sslcert/sslkey reads or "
                   "writes). Under it the F2P test_ssl_certificate — a TLS-configured "
                   "connection — yields an empty PG* dict {} instead of {PGSSLMODE, "
                   "PGSSLROOTCERT, PGSSLCERT, PGSSLKEY}: the assertEqual FAILS. It would NOT "
                   "resolve (this is the bug the patch fixes, G-DIFF).",
     "rationale": "Rejection source: the four SSL presence biconditionals "
                  "(envvar_sslmode() in Result()) == (setting_sslmode() in conn_params) "
                  "(model.py:126-140), violated whenever an SSL setting is supplied. If it "
                  "verified => SPEC-TOO-WEAK (admits the pre-patch only-password bug)."},
    {"id": "rival-drop-sslkey", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_SSLKEY,
     "refinement": "PARTIAL-DOMAIN (the sslkey setting): publishes password + sslmode + "
                   "sslrootcert + sslcert correctly but OMITS the PGSSLKEY publication. Its "
                   "faithful real patch is a runshell_db that forgot the "
                   "`if sslkey: subprocess_env['PGSSLKEY'] = str(sslkey)` write (a partial "
                   "feature implementation). Under it the F2P test_ssl_certificate — which "
                   "supplies sslkey='client.key' and asserts 'PGSSLKEY':'client.key' is in the "
                   "published PG* dict — observes a dict MISSING PGSSLKEY: the assertEqual "
                   "FAILS. It would NOT resolve.",
     "rationale": "partial-domain on the sslkey setting. Rejection source: the sslkey "
                  "biconditional (envvar_sslkey() in Result()) == (setting_sslkey() in "
                  "conn_params) (model.py:137-140), violated when sslkey is supplied. If it "
                  "verified => SPEC-TOO-WEAK (drops one TLS setting)."},
    {"id": "rival-spurious-key", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SPURIOUS,
     "refinement": "publishes all five settings correctly but ALSO publishes an extra variable "
                   "(token 200) outside the five dedicated names. Its faithful real patch is a "
                   "runshell_db that publishes some additional subprocess_env['PG...'] beyond "
                   "the five. The F2P test_ssl_certificate asserts the PG* dict EQUALS exactly "
                   "{PGSSLMODE, PGSSLROOTCERT, PGSSLCERT, PGSSLKEY} (assertEqual, not subset) "
                   "and P2P test_basic asserts exactly {PGPASSWORD:'somepassword'}; an extra "
                   "PG* key makes the dicts unequal: the assertEqual FAILS. It would NOT "
                   "resolve.",
     "rationale": "Rejection source: the NO-SPURIOUS-KEYS Forall "
                  "(model.py:143-147): e in Result() => e is one of the five envvar tokens, "
                  "violated by token 200. If it verified => SPEC-TOO-WEAK (admits a publication "
                  "with an extra variable)."},
    {"id": "rival-wrong-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_VALUE,
     "refinement": "publishes PGPASSWORD with a CONSTANT value (0) instead of the supplied one "
                   "(presence correct, value wrong). Its faithful real patch is a runshell_db "
                   "that sets subprocess_env['PGPASSWORD'] to a fixed/placeholder string rather "
                   "than str(passwd). Under it the P2P test_basic asserts "
                   "{'PGPASSWORD':'somepassword'} but observes the placeholder: the assertEqual "
                   "FAILS. It would NOT resolve. (The presence biconditional alone does NOT pin "
                   "the value.)",
     "rationale": "Rejection source: the password VALUE clause Implies(setting_password() in "
                  "conn_params, Result()[envvar_password()] == conn_params[setting_password()]) "
                  "(model.py:123-124), violated when the supplied value != 0. If it verified => "
                  "SPEC-TOO-WEAK (value not pinned)."},
    {"id": "rival-crosswire-sslcert", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CROSSWIRE,
     "refinement": "CROSS-WIRES the cert variable: publishes PGSSLCERT keyed off the SSLMODE "
                   "setting (carrying the sslmode value) and drops the genuine sslcert "
                   "publication, so PGSSLCERT's presence tracks setting_sslmode() instead of "
                   "setting_sslcert(). Its faithful real patch is a copy-paste wiring bug "
                   "(`if sslmode: subprocess_env['PGSSLCERT'] = str(sslmode)`). Under the F2P "
                   "test_ssl_certificate (which supplies BOTH sslmode='verify-ca' and "
                   "sslcert='client.crt') the published PGSSLCERT would be 'verify-ca' not "
                   "'client.crt': the assertEqual FAILS. It would NOT resolve. Pins that each "
                   "setting maps to its OWN distinct variable.",
     "rationale": "Rejection source: the sslcert biconditional (envvar_sslcert() in Result()) "
                  "== (setting_sslcert() in conn_params) (model.py:133-136) AND its value "
                  "clause — both broken because PGSSLCERT's presence/value are driven by the "
                  "sslmode setting. If it verified => SPEC-TOO-WEAK (settings collide)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real django callee) — the A-reference soundness +
# containment obligation. meta.axioms == [] (NO @ContractOnly axiom); the single
# soundness obligation is the deep model == real DatabaseClient.runshell_db PG*
# publication on the F2P/P2P domain. These reuse + strengthen axiom_check.py
# (which the runner does NOT mount in-container, so the probes are SELF-CONTAINED).
# The callee is the post-patch runshell_db, so apply_gold=True.
# ===========================================================================

# (axiom-soundness) Drive the GENUINE django DatabaseClient.runshell_db (with
# subprocess.run intercepted, exactly as the repo's own tests/dbshell/
# test_postgresql.py does) on boundary + fuzz connection-parameter mappings, and
# assert the PG* environment it publishes equals the deep model (each of the five
# settings -> its dedicated PG* variable, value verbatim, present iff supplied
# non-empty; no spurious PG* key). Fuzz includes the empty/sentinel/non-ascii/colon
# values that exercise the supplied-non-empty boundary and the str() coercion.
# Self-contained (stdlib + django only); file reads (none needed) would use
# encoding="utf-8".  apply_gold=True (the publication is the post-patch behaviour).
_AX_SOUNDNESS = r'''
import os
import random
import sys
from unittest import mock


SETTING_TO_ENVVAR = {
    "password": "PGPASSWORD",
    "sslmode": "PGSSLMODE",
    "sslrootcert": "PGSSLROOTCERT",
    "sslcert": "PGSSLCERT",
    "sslkey": "PGSSLKEY",
}


def deep_model_pg_env(conn_params):
    """Reference of model.py's deep model: for each recognised setting supplied
    with a non-empty value, publish its value verbatim under the dedicated PG*
    variable; otherwise leave that variable unset; no other PG* key."""
    env = {}
    for setting, envvar in SETTING_TO_ENVVAR.items():
        value = conn_params.get(setting, "")
        if value:
            env[envvar] = str(value)
    return env


def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(DATABASES={}, INSTALLED_APPS=[])
            django.setup()
        import subprocess
        from django.db.backends.postgresql.client import DatabaseClient
    except Exception as exc:
        print("AXIOM probe: django backend not importable (%r) — this lane MUST "
              "run in the instance image" % (exc,))
        return 1

    def real_pg_env(conn_params):
        captured = {}

        def _mock_run(*args, env=os.environ, **kwargs):
            captured.update({k: env[k] for k in env if k.startswith("PG")})
            return subprocess.CompletedProcess(list(*args) if args else [], 0)

        with mock.patch("subprocess.run", new=_mock_run):
            DatabaseClient.runshell_db(conn_params)
        return captured

    def check(cp):
        observed = real_pg_env(cp)
        expected = deep_model_pg_env(cp)
        if observed != expected:
            print("AXIOM-UNSOUND: deep model != real runshell_db on %r: "
                  "real published %r, model gives %r" % (cp, observed, expected))
            return False
        return True

    boundary = [
        {},
        {"database": "dbname", "user": "u", "host": "h", "port": "444"},
        {"password": "somepassword"},
        {"sslmode": "verify-ca"},
        {"sslrootcert": "root.crt"},
        {"sslcert": "client.crt"},
        {"sslkey": "client.key"},
        {"database": "dbname", "user": "someuser", "host": "somehost",
         "port": "444", "sslmode": "verify-ca", "sslrootcert": "root.crt",
         "sslcert": "client.crt", "sslkey": "client.key"},
        {"password": "p", "sslmode": "require", "sslrootcert": "ca.crt",
         "sslcert": "c.crt", "sslkey": "k.key"},
        {"password": "", "sslmode": "", "sslcert": ""},   # empty -> unset
        {"password": "some:password"},                    # colon value
        {"password": "sesame"},                           # ascii-safe value
    ]
    for cp in boundary:
        if not check(cp):
            return 1

    rng = random.Random(11239)
    keys = list(SETTING_TO_ENVVAR.keys())
    value_pool = ["", "x", "verify-ca", "root.crt", "client.crt",
                  "client.key", "some:val", "0", "p ss w0rd"]
    fuzz = 0
    for _ in range(5000):
        cp = {"database": "db", "user": "u", "host": "h", "port": "1"}
        for k in keys:
            if rng.random() < 0.5:
                cp[k] = rng.choice(value_pool)
        if not check(cp):
            return 1
        fuzz += 1

    print("AXIOM-SOUND: deep model (A-reference) == real DatabaseClient.runshell_db "
          "PG* publication on %d boundary + %d fuzz connection-parameter mappings "
          "(5 settings -> PGPASSWORD/PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY, "
          "value verbatim, present iff supplied non-empty, no spurious PG* key)."
          % (len(boundary), fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# (axiom-containment) Every callee-input the MODEL can REACH is handled by the
# real runshell_db without raising. The model's reachable callee-inputs are ANY
# subset of the five settings, each supplied (non-empty token present) or absent.
# We enumerate ALL 2**5 = 32 present/absent subsets (each present setting given a
# representative non-empty value) plus the empty/no-settings case and confirm the
# real runshell_db handles every one without raising — i.e. the whole modeled
# input domain lies inside the real callee's no-raise domain. (The model also
# admits empty-string values, which the real .get(k,'')+if-value path treats as
# absent — covered by the soundness fuzz; here we confirm the no-raise domain.)
# A reachable model input the callee could not handle => AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import os
import sys
from itertools import product
from unittest import mock


SETTINGS = ["password", "sslmode", "sslrootcert", "sslcert", "sslkey"]
REP_VALUE = {
    "password": "somepassword",
    "sslmode": "verify-ca",
    "sslrootcert": "root.crt",
    "sslcert": "client.crt",
    "sslkey": "client.key",
}


def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(DATABASES={}, INSTALLED_APPS=[])
            django.setup()
        import subprocess
        from django.db.backends.postgresql.client import DatabaseClient
    except Exception as exc:
        print("CONTAINMENT probe: django backend not importable (%r) — must run "
              "in image" % (exc,))
        return 1

    def _mock_run(*args, env=os.environ, **kwargs):
        return subprocess.CompletedProcess(list(*args) if args else [], 0)

    checked = 0
    # Every present/absent subset of the five settings (the entire modeled input
    # domain at the token level). A connection always carries the base routing
    # keys; the modeled settings vary.
    for mask in product([False, True], repeat=len(SETTINGS)):
        cp = {"database": "dbname", "user": "u", "host": "h", "port": "444"}
        for present, name in zip(mask, SETTINGS):
            if present:
                cp[name] = REP_VALUE[name]
        try:
            with mock.patch("subprocess.run", new=_mock_run):
                DatabaseClient.runshell_db(cp)
        except Exception as exc:
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable model input "
                  "(settings present=%r) is OUTSIDE the real runshell_db no-raise "
                  "domain (raised %r)" % (cp, exc))
            return 1
        checked += 1

    print("CONTAINMENT OK: every reachable model callee-input (all %d present/absent "
          "subsets of the five settings) is handled by the real "
          "DatabaseClient.runshell_db without raising. The modeled input domain "
          "(any subset of password/sslmode/sslrootcert/sslcert/sslkey) lies inside "
          "the real callee's no-raise domain." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-publication-sound", "axiom": "runshell_db_pg_publication_deep_model",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_SOUNDNESS,
     "rationale": "the bundle's single soundness obligation (A-reference): the deep "
                  "publication model (model.py's five conditional writes) must equal the REAL "
                  "DatabaseClient.runshell_db PG* publication on boundary + fuzz "
                  "connection-parameter mappings (subprocess.run intercepted, as the repo's own "
                  "test does), each setting -> its dedicated PG* variable, value verbatim, "
                  "present iff supplied non-empty, no spurious PG* key. The publication is the "
                  "post-patch behaviour (apply_gold=True). Any mismatch => the A-reference is "
                  "UNSOUND."},
    {"id": "ax-publication-containment", "axiom": "runshell_db_pg_publication_deep_model",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach (all 2**5 present/absent subsets of "
                  "the five settings — the entire modeled token-level input domain) is handled "
                  "by the real runshell_db without raising; the modeled input domain lies inside "
                  "the real callee's no-raise domain. A reachable input the callee could not "
                  "handle => AXIOM-TOO-WEAK-FOR-CALLER."},
]
