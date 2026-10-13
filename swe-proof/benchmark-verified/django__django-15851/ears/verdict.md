# P2 adversarial audit — django__django-15851

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control: extra params precede the dbname (Req 1.1/1.2/1.4).
Holds patched, fails at base."""
import sys
from django.db.backends.postgresql.client import DatabaseClient as C

args, env = C.settings_to_cmd_args_env({"NAME": "dbname"}, ["--help"])
print("args:", args, "env:", env)
expected = ["psql", "--help", "dbname"]
if args != expected:
    print("FAIL: expected", expected)
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.2/1.3: multiple extra params preserved in original order, dbname last."""
import sys
from django.db.backends.postgresql.client import DatabaseClient as C

params = ["-c", "select 1", "--set", "x=y"]
args, env = C.settings_to_cmd_args_env({"NAME": "mydb"}, params)
print("args:", args)
# dbname must be last
if args[-1] != "mydb":
    print("FAIL: dbname not last")
    sys.exit(1)
# extra params must appear contiguously in order immediately before dbname
if args[-len(params)-1:-1] != params:
    print("FAIL: params not in order immediately before dbname")
    sys.exit(1)
# none dropped/duplicated
for p in params:
    if args.count(p) != 1:
        print("FAIL: param count wrong for", p)
        sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2: order = psql, -U user, -h host, -p port, extra params, dbname."""
import sys
from django.db.backends.postgresql.client import DatabaseClient as C

settings = {"NAME": "db", "USER": "u", "HOST": "h", "PORT": 5432}
args, env = C.settings_to_cmd_args_env(settings, ["-c", "q"])
print("args:", args)
expected = ["psql", "-U", "u", "-h", "h", "-p", "5432", "-c", "q", "db"]
if args != expected:
    print("FAIL: expected", expected)
    sys.exit(1)
# Req 2.6: omit missing settings
args2, _ = C.settings_to_cmd_args_env({"NAME": "db"}, [])
print("args2:", args2)
if any(f in args2 for f in ("-U", "-h", "-p")):
    print("FAIL: flags emitted for missing settings")
    sys.exit(1)
if args2 != ["psql", "db"]:
    print("FAIL: expected [psql, db]")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3: default dbname 'postgres' when no name/service; still after params."""
import sys
from django.db.backends.postgresql.client import DatabaseClient as C

args, env = C.settings_to_cmd_args_env({}, ["--help"])
print("args:", args)
if args[-1] != "postgres":
    print("FAIL: default dbname not 'postgres' as last elem")
    sys.exit(1)
if args != ["psql", "--help", "postgres"]:
    print("FAIL: expected [psql, --help, postgres]")
    sys.exit(1)
# configured name is used
args2, _ = C.settings_to_cmd_args_env({"NAME": "custom"}, ["--help"])
if args2[-1] != "custom":
    print("FAIL: configured name not used/last")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1/4.6: PGPASSWORD in env, password never in args."""
import sys
from django.db.backends.postgresql.client import DatabaseClient as C

settings = {"NAME": "db", "USER": "u", "PASSWORD": "sekret"}
args, env = C.settings_to_cmd_args_env(settings, ["-c", "q"])
print("args:", args, "env:", env)
if env is None or env.get("PGPASSWORD") != "sekret":
    print("FAIL: PGPASSWORD not set")
    sys.exit(1)
if "sekret" in args:
    print("FAIL: password leaked into args")
    sys.exit(1)
print("OK")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.2/4.3/4.4/4.5: service, passfile, SSL env; None when nothing set."""
import sys
from django.db.backends.postgresql.client import DatabaseClient as C

# None env when nothing configured
_, env0 = C.settings_to_cmd_args_env({"NAME": "db"}, [])
print("env0:", env0)
if env0 is not None:
    print("FAIL: env should be None")
    sys.exit(1)

settings = {
    "NAME": "db",
    "OPTIONS": {
        "service": "svc",
        "passfile": "/pf",
        "sslmode": "require",
        "sslrootcert": "/rc",
        "sslcert": "/c",
        "sslkey": "/k",
    },
}
args, env = C.settings_to_cmd_args_env(settings, [])
print("args:", args, "env:", env)
want = {
    "PGSERVICE": "svc",
    "PGPASSFILE": "/pf",
    "PGSSLMODE": "require",
    "PGSSLROOTCERT": "/rc",
    "PGSSLCERT": "/c",
    "PGSSLKEY": "/k",
}
for k, v in want.items():
    if env.get(k) != v:
        print("FAIL:", k, "expected", v, "got", env.get(k))
        sys.exit(1)
    if v in args:
        print("FAIL: SSL/service value leaked into args:", v)
        sys.exit(1)
print("OK")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: extra params precede the dbname (Req 1.1/1.2/1.4).
Holds patched, fails at base."""
import sys
from django.db.backends.postgresql.client import DatabaseClient as C

args, env = C.settings_to_cmd_args_env({"NAME": "dbname"}, ["--help"])
print("args:", args, "env:", env)
expected = ["psql", "--help", "dbname"]
if args != expected:
    print("FAIL: expected", expected)
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django-15851: gold moves caller-supplied extra params BEFORE the database name in DatabaseClient.settings_to_cmd_args_env (postgresql/client.py). 6 probes cover all 4 requirements.

Probe results (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2/1.4, POSITIVE CONTROL): ['--help','dbname'] ordering. HOLDS patched, VIOLATED at base (base gives ['dbname','--help']) -> discriminates.
- probe_2 (Req1.2/1.3): multiple params preserved in original order, contiguous, immediately before dbname (last). HOLDS patched, VIOLATED base.
- probe_3 (Req2.1-2.6): full order psql,-U,-h,-p,params,dbname + omission of missing flags. HOLDS patched, VIOLATED base.
- probe_4 (Req3.1/3.2): default 'postgres' when no name; configured name used; both last after params. HOLDS patched, VIOLATED base.
- probe_5 (Req4.1/4.6): PGPASSWORD in env, password not in args. HOLDS.
- probe_6 (Req4.2-4.5,4.5-None): PGSERVICE/PGPASSFILE/PGSSL* env entries; env None when nothing configured; values not leaked to args. HOLDS.

CANDIDATE PATCH exercised: weak.diff extends args with parameters[::-1] (reversed) before dbname. Probes 1,4,5,6 pass (they use single or zero params) but probes 2 and 3 REJECT it (params out of order) -> suite discriminates wrong implementations. No requirements-conforming alternative that would fail hidden tests was found; the ordering criteria are pinned exactly by the F2P test (['psql','--help','dbname']).

All needed runs completed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: extra params precede the dbname (Req 1.1/1.2/1.4).
Holds patched, fails at base."""
import sys
from django.db.backends.postgresql.client import DatabaseClient as C

args, env = C.settings_to_cmd_args_env({"NAME": "dbname"}, ["--help"])
print("args:", args, "env:", env)
expected = ["psql", "--help", "dbname"]
if args != expected:
    print("FAIL: expected", expected)
    sys.exit(1)
print("OK")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django-15851: gold moves caller-supplied extra params BEFORE the database name in DatabaseClient.settings_to_cmd_args_env (postgresql/client.py). 6 probes cover all 4 requirements.

Probe results (all HOLD on gold-patched tree):
- probe_1 (Req1.1/1.2/1.4, POSITIVE CONTROL): ['--help','dbname'] ordering. HOLDS patched, VIOLATED at base (base gives ['dbname','--help']) -> discriminates.
- probe_2 (Req1.2/1.3): multiple params preserved in original order, contiguous, immediately before dbname (last). HOLDS patched, VIOLATED base.
- probe_3 (Req2.1-2.6): full order psql,-U,-h,-p,params,dbname + omission of missing flags. HOLDS patched, VIOLATED base.
- probe_4 (Req3.1/3.2): default 'postgres' when no name; configured name used; both last after params. HOLDS patched, VIOLATED base.
- probe_5 (Req4.1/4.6): PGPASSWORD in env, password not in args. HOLDS.
- probe_6 (Req4.2-4.5,4.5-None): PGSERVICE/PGPASSFILE/PGSSL* env entries; env None when nothing configured; values not leaked to args. HOLDS.

CANDIDATE PATCH exercised: weak.diff extends args with parameters[::-1] (reversed) before dbname. Probes 1,4,5,6 pass (they use single or zero params) but probes 2 and 3 REJECT it (params out of order) -> suite discriminates wrong implementations. No requirements-conforming alternative that would fail hidden tests was found; the ordering criteria are pinned exactly by the F2P test (['psql','--help','dbname']).

All needed runs completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probes A-D on gold-patched tree all pass; base twin diverges exactly on ordering. Requirements accurately and completely describe the reorder plus preserved surrounding behavior; no mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to the public module/classmethod (django/db/backends/postgresql/client.py :: DatabaseClient.settings_to_cmd_args_env) — legitimate. The core behavior (extra parameters must precede the database name for psql) is fully public in problem_statement, including the -c "select ..." example and the 'extra command-line argument ... ignored' behavior. All other requirements (program name psql, -U/-h/-p flag ordering, PGPASSWORD/PGSERVICE/PGPASSFILE/PGSSL* env mapping, 'postgres' default, credentials/SSL out of argv) are derivable from the source client.py, which is the target of the change, not from the hidden tests. No test file path (tests/dbshell/test_postgresql.py), test/class names (test_parameters, PostgreSqlDbshellCommandTestCase), quoted test literals ('dbname', '--help'), gold-patch lines, or fix-invented identifiers appear. No enumeration mirrors the test parametrization; the prose translates behavior rather than reconstructing the test. The FAIL_TO_PASS asserts (['psql','--help','dbname'], None), and the doc never quotes those literals.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
