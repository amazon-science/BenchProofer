# P2 adversarial audit — django__django-14315

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 3/3 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_runshell_none.py`, `probe_2_pg_none.py`, `probe_3_layer.py`, `probe_4_args_check.py`, `probe_5_env_vars.py`, `probe_6_base_notimpl.py`, `probe_7_base_empty_dict.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 3 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 3: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_runshell_none.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_runshell_none.py` → holds on the patched tree (good)

```python
"""Req 1.1 / 1.3 (POSITIVE CONTROL): runshell with NO overrides -> subprocess.run(env=None).
At base the empty-dict env is passed straight through as {} (falsy but not None-forced correctly)."""
import os, subprocess
from types import SimpleNamespace
from django.db.backends.postgresql.client import DatabaseClient

captured = {}
def fake_run(args, env=None, check=None, **kw):
    captured['args'] = args
    captured['env'] = env
    captured['check'] = check
    return SimpleNamespace(returncode=0)
subprocess.run = fake_run

# no password, no service, no ssl, no passfile -> no overrides
settings = {'NAME': 'db', 'USER': '', 'PASSWORD': '', 'HOST': '', 'PORT': '', 'OPTIONS': {}}
conn = SimpleNamespace(settings_dict=settings)
client = DatabaseClient(conn)
client.runshell(parameters=[])

print("captured env =", repr(captured.get('env')))
assert captured.get('env') is None, "env passed to subprocess.run must be None when no overrides"
print("OK: subprocess.run received env=None")
```

Attack 2 — `probe_2_pg_none.py` → holds on the patched tree (good)

```python
"""Req 3.1 / 3.3: PG settings_to_cmd_args_env returns None (not {}) as env when no overrides."""
from types import SimpleNamespace
from django.db.backends.postgresql.client import DatabaseClient

settings = {'NAME': 'db', 'USER': '', 'PASSWORD': '', 'HOST': '', 'PORT': '', 'OPTIONS': {}}
args, env = DatabaseClient.settings_to_cmd_args_env(settings, [])
print("args =", args)
print("env =", repr(env))
assert env is None, "env component must be None when no connection-specific vars"
print("OK: env is None")
```

Attack 3 — `probe_3_layer.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.3 & 4.5: with a password override, runshell layers os.environ + overrides,
override wins, env is not None, PGPASSWORD present, password not in args."""
import os, subprocess
from types import SimpleNamespace
from django.db.backends.postgresql.client import DatabaseClient

os.environ['SBU_AMBIENT_MARKER'] = 'ambient_value'
os.environ['PGPASSWORD'] = 'AMBIENT_SHOULD_BE_OVERRIDDEN'

captured = {}
def fake_run(args, env=None, check=None, **kw):
    captured['args'] = args
    captured['env'] = env
    return SimpleNamespace(returncode=0)
subprocess.run = fake_run

settings = {'NAME': 'db', 'USER': 'u', 'PASSWORD': 'secretpw', 'HOST': 'h', 'PORT': '5432', 'OPTIONS': {}}
conn = SimpleNamespace(settings_dict=settings)
DatabaseClient(conn).runshell(parameters=[])

env = captured['env']
args = captured['args']
print("env is None?", env is None)
print("PGPASSWORD =", env.get('PGPASSWORD') if env else None)
print("ambient marker =", env.get('SBU_AMBIENT_MARKER') if env else None)
print("args =", args)
assert env is not None, "env must not be None when overrides present"
assert env.get('PGPASSWORD') == 'secretpw', "override must win over ambient PGPASSWORD"
assert env.get('SBU_AMBIENT_MARKER') == 'ambient_value', "ambient env must be preserved"
assert 'secretpw' not in args, "password must not appear in args"
print("OK: overrides layered on ambient, precedence correct, no leak")
```

Attack 4 — `probe_4_args_check.py` → holds on the patched tree (good)

```python
"""Req 1.4 & 4.1/4.2/4.3/4.4: args forwarded verbatim, check=True, psql first,
-U/-h/-p order, dbname/default, extra params appended."""
import subprocess
from types import SimpleNamespace
from django.db.backends.postgresql.client import DatabaseClient

captured = {}
def fake_run(args, env=None, check=None, **kw):
    captured['args'] = args
    captured['check'] = check
    return SimpleNamespace(returncode=0)
subprocess.run = fake_run

settings = {'NAME': 'mydb', 'USER': 'someuser', 'PASSWORD': '', 'HOST': 'myhost', 'PORT': '444', 'OPTIONS': {}}
conn = SimpleNamespace(settings_dict=settings)
DatabaseClient(conn).runshell(parameters=['--extra', 'X'])

args = captured['args']
print("args =", args)
print("check =", captured['check'])
assert captured['check'] is True, "check must be True"
assert args[0] == 'psql', "first element must be psql"
# order -U before -h before -p
iu, ih, ip = args.index('-U'), args.index('-h'), args.index('-p')
assert iu < ih < ip, "-U/-h/-p relative order"
assert args[iu+1] == 'someuser' and args[ih+1] == 'myhost' and args[ip+1] == '444'
assert 'mydb' in args, "dbname present"
assert '--extra' in args and 'X' in args, "extra params appended"
assert args.index('--extra') > ip, "extra after connection args"

# default dbname when neither name nor service
s2 = {'NAME': '', 'USER': '', 'PASSWORD': '', 'HOST': '', 'PORT': '', 'OPTIONS': {}}
a2, _ = DatabaseClient.settings_to_cmd_args_env(s2, [])
print("default-name args =", a2)
assert 'postgres' in a2, "default db name postgres"
print("OK: args/check/order/default all correct")
```

Attack 5 — `probe_5_env_vars.py` → holds on the patched tree (good)

```python
"""Req 4.6 & 3.2: service/ssl/passfile map to exact env entries, and env contains ONLY those keys."""
from django.db.backends.postgresql.client import DatabaseClient

settings = {
    'NAME': 'db', 'USER': '', 'PASSWORD': '', 'HOST': '', 'PORT': '',
    'OPTIONS': {
        'service': 'svc', 'sslmode': 'verify-full', 'sslrootcert': 'root.crt',
        'sslcert': 'c.crt', 'sslkey': 'k.key', 'passfile': '/pf',
    },
}
args, env = DatabaseClient.settings_to_cmd_args_env(settings, [])
print("env =", env)
expected = {
    'PGSERVICE': 'svc', 'PGSSLMODE': 'verify-full', 'PGSSLROOTCERT': 'root.crt',
    'PGSSLCERT': 'c.crt', 'PGSSLKEY': 'k.key', 'PGPASSFILE': '/pf',
}
assert env == expected, f"env must contain exactly the mapped vars, got {env}"
print("OK: exact env mapping for service/ssl/passfile")
```

Attack 6 — `probe_6_base_notimpl.py` → holds on the patched tree (good)

```python
"""Req 5.1: base settings_to_cmd_args_env raises NotImplementedError with the required message."""
from types import SimpleNamespace
from django.db.backends.base.client import BaseDatabaseClient

try:
    BaseDatabaseClient.settings_to_cmd_args_env({}, [])
    print("no error raised")
    raise SystemExit(1)
except NotImplementedError as e:
    msg = str(e)
    print("msg =", msg)
    assert 'settings_to_cmd_args_env()' in msg
    assert 'runshell()' in msg
    print("OK: NotImplementedError raised with expected message")
```

Attack 7 — `probe_7_base_empty_dict.py` → holds on the patched tree (good)

```python
"""Req 1.3 / 1.1: the BASE client itself must treat a supplied-but-empty {} env
identically to None -> pass env=None to subprocess.run. Uses a dummy subclass
returning ({...}, {}) so the discriminator is the base client, not the PG client."""
import subprocess
from types import SimpleNamespace
from django.db.backends.base.client import BaseDatabaseClient

class DummyClient(BaseDatabaseClient):
    def settings_to_cmd_args_env(self, settings_dict, parameters):
        return ['prog', 'arg'], {}   # supplied-but-empty mapping

captured = {}
def fake_run(args, env=None, check=None, **kw):
    captured['args'] = args
    captured['env'] = env
    captured['check'] = check
    return SimpleNamespace(returncode=0)
subprocess.run = fake_run

conn = SimpleNamespace(settings_dict={})
DummyClient(conn).runshell(parameters=[])
print("env =", repr(captured['env']), "check =", captured['check'])
assert captured['env'] is None, "empty {} env must be converted to None by base client"
assert captured['check'] is True
print("OK: base client converts empty {} to None")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_runshell_none.py`

```python
"""Req 1.1 / 1.3 (POSITIVE CONTROL): runshell with NO overrides -> subprocess.run(env=None).
At base the empty-dict env is passed straight through as {} (falsy but not None-forced correctly)."""
import os, subprocess
from types import SimpleNamespace
from django.db.backends.postgresql.client import DatabaseClient

captured = {}
def fake_run(args, env=None, check=None, **kw):
    captured['args'] = args
    captured['env'] = env
    captured['check'] = check
    return SimpleNamespace(returncode=0)
subprocess.run = fake_run

# no password, no service, no ssl, no passfile -> no overrides
settings = {'NAME': 'db', 'USER': '', 'PASSWORD': '', 'HOST': '', 'PORT': '', 'OPTIONS': {}}
conn = SimpleNamespace(settings_dict=settings)
client = DatabaseClient(conn)
client.runshell(parameters=[])

print("captured env =", repr(captured.get('env')))
assert captured.get('env') is None, "env passed to subprocess.run must be None when no overrides"
print("OK: subprocess.run received env=None")
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering all 5 requirements. On the gold-patched tree ALL 7 HOLD (exit 0). Positive controls that HOLD patched and FAIL at base: probe_1 (Req1.1/1.3 runshell passes env=None when no overrides), probe_2 (Req3.1/3.3 PG returns None not {}), probe_7 (Req1.3 base client converts supplied {} to None). prepatch_reproduced=true (probe_1 VIOLATED at base with AssertionError: env must be None). Probe coverage: p1 Req1.1/1.3 (runshell env=None); p2 Req3.1/3.3 (PG env None); p3 Req2.1/2.2/2.3 & 4.5 (layer os.environ+overrides, override precedence, PGPASSWORD set, password not in args, ambient preserved, env not None); p4 Req1.4 & 4.1-4.4 (args forwarded verbatim, check=True, psql first, -U/-h/-p order, dbname, default 'postgres', extra params appended after connection args); p5 Req4.6 & 3.2 (exact env mapping for service/sslmode/sslrootcert/sslcert/sslkey/passfile, no extra keys); p6 Req5.1 (base NotImplementedError with required message); p7 Req1.3 (base client empty {} -> None, isolated from PG via dummy subclass). 

Discriminating power demonstrated — three plausibly-wrong candidate patches, each REJECTED by the suite: (a) weak_base_only [fixes only base client, leaves PG returning {}] -> REJECTED by probe_2 (PG env not None); this variant would fail the hidden test_settings_to_cmd_args_env. (b) weak_always_dict [base client always builds a dict `{**os.environ, **(env or {})}`, never None] -> REJECTED by probe_1 and probe_7 (env is {ambient} not None); would fail test_runshell_use_environ. (c) weak_pg_only [fixes only PG, leaves base client `if env: env=...`] -> REJECTED by probe_7 (base client does not convert supplied {} to None); would fail the base SimpleDatabaseClientTests. No requirements-conforming candidate passed the full suite, so no TOO-WEAK finding. All candidate diffs apply cleanly at base_commit.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 3/3 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_runshell_none.py`, `probe_2_pg_none.py`, `probe_3_layer.py`, `probe_4_args_check.py`, `probe_5_env_vars.py`, `probe_6_base_notimpl.py`, `probe_7_base_empty_dict.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 3 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 3: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_runshell_none.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_runshell_none.py` → holds on the patched tree (good)

Attack 2 — `probe_2_pg_none.py` → holds on the patched tree (good)

Attack 3 — `probe_3_layer.py` → holds on the patched tree (good)

Attack 4 — `probe_4_args_check.py` → holds on the patched tree (good)

Attack 5 — `probe_5_env_vars.py` → holds on the patched tree (good)

Attack 6 — `probe_6_base_notimpl.py` → holds on the patched tree (good)

Attack 7 — `probe_7_base_empty_dict.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_runshell_none.py`

```python
"""Req 1.1 / 1.3 (POSITIVE CONTROL): runshell with NO overrides -> subprocess.run(env=None).
At base the empty-dict env is passed straight through as {} (falsy but not None-forced correctly)."""
import os, subprocess
from types import SimpleNamespace
from django.db.backends.postgresql.client import DatabaseClient

captured = {}
def fake_run(args, env=None, check=None, **kw):
    captured['args'] = args
    captured['env'] = env
    captured['check'] = check
    return SimpleNamespace(returncode=0)
subprocess.run = fake_run

# no password, no service, no ssl, no passfile -> no overrides
settings = {'NAME': 'db', 'USER': '', 'PASSWORD': '', 'HOST': '', 'PORT': '', 'OPTIONS': {}}
conn = SimpleNamespace(settings_dict=settings)
client = DatabaseClient(conn)
client.runshell(parameters=[])

print("captured env =", repr(captured.get('env')))
assert captured.get('env') is None, "env passed to subprocess.run must be None when no overrides"
print("OK: subprocess.run received env=None")
```

Prepatch bug re-encoded as an attack: `True`.

7 probes covering all 5 requirements. On the gold-patched tree ALL 7 HOLD (exit 0). Positive controls that HOLD patched and FAIL at base: probe_1 (Req1.1/1.3 runshell passes env=None when no overrides), probe_2 (Req3.1/3.3 PG returns None not {}), probe_7 (Req1.3 base client converts supplied {} to None). prepatch_reproduced=true (probe_1 VIOLATED at base with AssertionError: env must be None). Probe coverage: p1 Req1.1/1.3 (runshell env=None); p2 Req3.1/3.3 (PG env None); p3 Req2.1/2.2/2.3 & 4.5 (layer os.environ+overrides, override precedence, PGPASSWORD set, password not in args, ambient preserved, env not None); p4 Req1.4 & 4.1-4.4 (args forwarded verbatim, check=True, psql first, -U/-h/-p order, dbname, default 'postgres', extra params appended after connection args); p5 Req4.6 & 3.2 (exact env mapping for service/sslmode/sslrootcert/sslcert/sslkey/passfile, no extra keys); p6 Req5.1 (base NotImplementedError with required message); p7 Req1.3 (base client empty {} -> None, isolated from PG via dummy subclass). 

Discriminating power demonstrated — three plausibly-wrong candidate patches, each REJECTED by the suite: (a) weak_base_only [fixes only base client, leaves PG returning {}] -> REJECTED by probe_2 (PG env not None); this variant would fail the hidden test_settings_to_cmd_args_env. (b) weak_always_dict [base client always builds a dict `{**os.environ, **(env or {})}`, never None] -> REJECTED by probe_1 and probe_7 (env is {ambient} not None); would fail test_runshell_use_environ. (c) weak_pg_only [fixes only PG, leaves base client `if env: env=...`] -> REJECTED by probe_7 (base client does not convert supplied {} to None); would fail the base SimpleDatabaseClientTests. No requirements-conforming candidate passed the full suite, so no TOO-WEAK finding. All candidate diffs apply cleanly at base_commit.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The gold patch has two hunks: base/client.py `env = {**os.environ, **env} if env else None` and postgresql/client.py `return args, (env or None)`. The requirements pin exactly this changed observable behavior (empty/absent env -> None -> ambient inheritance; non-empty -> layered over os.environ with override precedence), correctly treating empty-dict and None identically (R1.3, R3.3), and correctly locate the boundary in BOTH runshell (base) and settings_to_cmd_args_env (postgresql). Reqs 4-5 fence pre-existing behavior without over-constraining. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found. All probed on the gold-patched tree in the instance image.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to BaseDatabaseClient.runshell and postgresql DatabaseClient.settings_to_cmd_args_env (legitimate) and translates behavior into EARS requirements. All content is derivable from the public problem_statement (postgresql client returns empty dict instead of None; os.environ not inherited; empty env passed to subprocess) plus existing public Django API surface. The None-vs-empty-mapping equivalence (Req 1.3) reflects the gold fix's semantics ({**os.environ, **env} if env else None), which is exactly the behavior the problem statement describes — spec translation, not test transmission. The PGPASSWORD/PGSERVICE/PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY/PGPASSFILE enumeration (Req 4.5/4.6) is pre-existing public env-var handling, not invented by the fix or tests. No test function/class names (test_runshell_use_environ, PostgreSqlDbshellCommandTestCase), file paths (tests/backends/base/test_client.py, tests/dbshell/test_postgresql.py), FAIL_TO_PASS ids, the mock.patch/subprocess.run assertion code, or the [None, {}] literal appear or are near-quoted. No case enumeration mirrors the test parametrization beyond the behaviorally-required None/{} equivalence.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
