# P2 adversarial audit — django__django-11239

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_ssl_env.py`, `probe_2_omit_absent.py`, `probe_3_args_unaffected.py`, `probe_4_password_regression.py`, `probe_5_nonstring_coerce.py`, `probe_6_each_maps_only_own.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_ssl_env.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_ssl_env.py` → holds on the patched tree (good)

```python
# Positive control: Req1.1-1.4 — supplied ssl params land in child env under
# PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY.
import os, sys, signal, subprocess
from django.db.backends.postgresql import client

captured = {}
def fake_run(args, check, env):
    captured['args'] = args
    captured['env'] = env
subprocess.run = fake_run
signal.signal = lambda *a, **k: signal.SIG_DFL

conn = {
    'database': 'db', 'user': 'u', 'host': 'h', 'port': 5432,
    'sslmode': 'verify-ca',
    'sslrootcert': '/root.crt',
    'sslcert': '/client.crt',
    'sslkey': '/client.key',
}
client.DatabaseClient.runshell_db(conn)
env = captured['env']
print('env ssl vars:', {k: env.get(k) for k in
      ['PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY']})
ok = (env.get('PGSSLMODE') == 'verify-ca'
      and env.get('PGSSLROOTCERT') == '/root.crt'
      and env.get('PGSSLCERT') == '/client.crt'
      and env.get('PGSSLKEY') == '/client.key')
print('HOLDS' if ok else 'FAILS')
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_omit_absent.py` → holds on the patched tree (good)

```python
# Req2.1-2.5 — absent (missing or empty) ssl params must NOT set the vars, and
# no other transport-security var is introduced. Also check empty-string absence.
import sys, signal, subprocess
from django.db.backends.postgresql import client

captured = {}
def fake_run(args, check, env):
    captured['env'] = env
subprocess.run = fake_run
signal.signal = lambda *a, **k: None

# Case A: entirely missing
client.DatabaseClient.runshell_db({'database': 'db', 'user': 'u'})
envA = captured['env']
# Case B: present but empty string -> treated as absent
client.DatabaseClient.runshell_db({
    'database': 'db', 'sslmode': '', 'sslrootcert': '',
    'sslcert': '', 'sslkey': ''})
envB = captured['env']

names = ['PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY']
print('missing case:', {k: envA.get(k) for k in names})
print('empty  case:', {k: envB.get(k) for k in names})
ok = all(k not in envA for k in names) and all(k not in envB for k in names)
print('HOLDS' if ok else 'FAILS')
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_args_unaffected.py` → holds on the patched tree (good)

```python
# Req3.7 + Req3.1-3.5 — ssl params must NOT appear in the arg vector; arg vector
# built from executable, -U user, -h host, -p port(str), dbname last.
import sys, signal, subprocess
from django.db.backends.postgresql import client

captured = {}
def fake_run(args, check, env):
    captured['args'] = list(args)
subprocess.run = fake_run
signal.signal = lambda *a, **k: None

conn = {
    'database': 'mydb', 'user': 'me', 'host': 'srv', 'port': 6543,
    'sslmode': 'verify-full', 'sslrootcert': '/r.crt',
    'sslcert': '/c.crt', 'sslkey': '/c.key',
}
client.DatabaseClient.runshell_db(conn)
args = captured['args']
print('args:', args)

exe = client.DatabaseClient.executable_name
ssl_vals = {'verify-full', '/r.crt', '/c.crt', '/c.key'}
no_ssl_in_args = not (ssl_vals & set(args))
shape_ok = (
    args[0] == exe
    and '-U' in args and args[args.index('-U') + 1] == 'me'
    and '-h' in args and args[args.index('-h') + 1] == 'srv'
    and '-p' in args and args[args.index('-p') + 1] == '6543'
    and args[-1] == 'mydb'
)
print('exe:', exe, 'no_ssl_in_args:', no_ssl_in_args, 'shape_ok:', shape_ok)
ok = no_ssl_in_args and shape_ok
print('HOLDS' if ok else 'FAILS')
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_password_regression.py` → holds on the patched tree (good)

```python
# Req3.6 + Req3.8 — password forwarding preserved; env inherits os.environ;
# dbname appended even when empty. Regression criteria.
import os, sys, signal, subprocess
from django.db.backends.postgresql import client

os.environ['SBU_MARKER'] = 'inherited'
captured = {}
def fake_run(args, check, env):
    captured['args'] = list(args)
    captured['env'] = env
subprocess.run = fake_run
signal.signal = lambda *a, **k: None

# with password
client.DatabaseClient.runshell_db({'database': '', 'password': 'secret'})
env = captured['env']
args = captured['args']
print('args (empty db):', args)
print('PGPASSWORD:', env.get('PGPASSWORD'), 'inherited:', env.get('SBU_MARKER'))
with_pw_ok = (env.get('PGPASSWORD') == 'secret'
              and env.get('SBU_MARKER') == 'inherited'
              and args[-1] == '')

# without password -> PGPASSWORD must not be set
client.DatabaseClient.runshell_db({'database': 'd'})
env2 = captured['env']
print('no-pw PGPASSWORD present:', 'PGPASSWORD' in env2)
no_pw_ok = 'PGPASSWORD' not in env2

ok = with_pw_ok and no_pw_ok
print('HOLDS' if ok else 'FAILS')
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_nonstring_coerce.py` → holds on the patched tree (good)

```python
# Req1.6 — a supplied non-string ssl value is injected in string form.
import sys, signal, subprocess
from django.db.backends.postgresql import client

captured = {}
def fake_run(args, check, env):
    captured['env'] = env
subprocess.run = fake_run
signal.signal = lambda *a, **k: None

# non-string truthy values
conn = {
    'database': 'db',
    'sslmode': 12345,
    'sslrootcert': 678,
}
client.DatabaseClient.runshell_db(conn)
env = captured['env']
print('PGSSLMODE:', repr(env.get('PGSSLMODE')),
      'PGSSLROOTCERT:', repr(env.get('PGSSLROOTCERT')))
ok = (env.get('PGSSLMODE') == '12345'
      and isinstance(env.get('PGSSLMODE'), str)
      and env.get('PGSSLROOTCERT') == '678')
print('HOLDS' if ok else 'FAILS')
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_each_maps_only_own.py` → holds on the patched tree (good)

```python
# Req2.5 + Req1 mapping — each supplied ssl param maps ONLY to its own var, and
# no unrelated PG* transport var is introduced. Supply exactly one param at a
# time and check exactly one of the four vars appears.
import sys, signal, subprocess
from django.db.backends.postgresql import client

names = ['PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY']
mapping = {
    'sslmode': 'PGSSLMODE',
    'sslrootcert': 'PGSSLROOTCERT',
    'sslcert': 'PGSSLCERT',
    'sslkey': 'PGSSLKEY',
}

captured = {}
def fake_run(args, check, env):
    captured['env'] = env
subprocess.run = fake_run
signal.signal = lambda *a, **k: None

# baseline env keys with no ssl
client.DatabaseClient.runshell_db({'database': 'db'})
base_keys = set(captured['env'].keys())

ok = True
for param, var in mapping.items():
    client.DatabaseClient.runshell_db({'database': 'db', param: 'VAL'})
    env = captured['env']
    new_pg = {k for k in env.keys() - base_keys if k.startswith('PGSSL')}
    print(param, '-> new PGSSL vars:', new_pg, 'value:', env.get(var))
    if new_pg != {var} or env.get(var) != 'VAL':
        ok = False
print('HOLDS' if ok else 'FAILS')
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_ssl_env.py`

```python
# Positive control: Req1.1-1.4 — supplied ssl params land in child env under
# PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY.
import os, sys, signal, subprocess
from django.db.backends.postgresql import client

captured = {}
def fake_run(args, check, env):
    captured['args'] = args
    captured['env'] = env
subprocess.run = fake_run
signal.signal = lambda *a, **k: signal.SIG_DFL

conn = {
    'database': 'db', 'user': 'u', 'host': 'h', 'port': 5432,
    'sslmode': 'verify-ca',
    'sslrootcert': '/root.crt',
    'sslcert': '/client.crt',
    'sslkey': '/client.key',
}
client.DatabaseClient.runshell_db(conn)
env = captured['env']
print('env ssl vars:', {k: env.get(k) for k in
      ['PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY']})
ok = (env.get('PGSSLMODE') == 'verify-ca'
      and env.get('PGSSLROOTCERT') == '/root.crt'
      and env.get('PGSSLCERT') == '/client.crt'
      and env.get('PGSSLKEY') == '/client.key')
print('HOLDS' if ok else 'FAILS')
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-11239: forward PostgreSQL TLS client-cert params (sslmode/sslrootcert/sslcert/sslkey) into the dbshell child env as PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY. All probes monkeypatch subprocess.run/signal.signal to capture the assembled argv + env.

Probes (all HOLD on gold-patched):
- probe_1 (Req1.1-1.4, POSITIVE CONTROL): four supplied ssl params land in child env under the four PG* vars. HOLDS patched, VIOLATED at base (base env has all four None) => discriminates.
- probe_2 (Req2.1-2.5): missing AND empty-string ssl params set none of the four vars.
- probe_3 (Req3.1-3.5,3.7): argv = [psql,-U user,-h host,-p port(str),dbname-last] and contains no ssl values.
- probe_4 (Req3.6,3.8): PGPASSWORD forwarded iff password supplied; env inherits os.environ (SBU_MARKER); dbname appended even when empty.
- probe_5 (Req1.6): non-string ssl values (int) coerced to str in env.
- probe_6 (Req2.5): supplying exactly one ssl param introduces exactly its own PGSSL var and no other.

Candidate wrong-fixes, both REJECTED by suite:
- weak_partial (only PGSSLMODE forwarded): rejected by probe_1 (root/cert/key None), probe_5, probe_6. Passes 2/3/4.
- weak_args (all four ssl params pushed into argv via --set instead of env): rejected by probe_1 (no env vars), probe_3 (ssl in argv), probe_5, probe_6.

All needed runs completed. >=5 probes hold on patched, positive control discriminates base vs patched, and at least one probe-conforming-partial candidate is rejected => suite has discriminating power. No too-weak or violation finding.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_ssl_env.py`, `probe_2_omit_absent.py`, `probe_3_args_unaffected.py`, `probe_4_password_regression.py`, `probe_5_nonstring_coerce.py`, `probe_6_each_maps_only_own.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_ssl_env.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_ssl_env.py` → holds on the patched tree (good)

Attack 2 — `probe_2_omit_absent.py` → holds on the patched tree (good)

Attack 3 — `probe_3_args_unaffected.py` → holds on the patched tree (good)

Attack 4 — `probe_4_password_regression.py` → holds on the patched tree (good)

Attack 5 — `probe_5_nonstring_coerce.py` → holds on the patched tree (good)

Attack 6 — `probe_6_each_maps_only_own.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_ssl_env.py`

```python
# Positive control: Req1.1-1.4 — supplied ssl params land in child env under
# PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY.
import os, sys, signal, subprocess
from django.db.backends.postgresql import client

captured = {}
def fake_run(args, check, env):
    captured['args'] = args
    captured['env'] = env
subprocess.run = fake_run
signal.signal = lambda *a, **k: signal.SIG_DFL

conn = {
    'database': 'db', 'user': 'u', 'host': 'h', 'port': 5432,
    'sslmode': 'verify-ca',
    'sslrootcert': '/root.crt',
    'sslcert': '/client.crt',
    'sslkey': '/client.key',
}
client.DatabaseClient.runshell_db(conn)
env = captured['env']
print('env ssl vars:', {k: env.get(k) for k in
      ['PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY']})
ok = (env.get('PGSSLMODE') == 'verify-ca'
      and env.get('PGSSLROOTCERT') == '/root.crt'
      and env.get('PGSSLCERT') == '/client.crt'
      and env.get('PGSSLKEY') == '/client.key')
print('HOLDS' if ok else 'FAILS')
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

django__django-11239: forward PostgreSQL TLS client-cert params (sslmode/sslrootcert/sslcert/sslkey) into the dbshell child env as PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY. All probes monkeypatch subprocess.run/signal.signal to capture the assembled argv + env.

Probes (all HOLD on gold-patched):
- probe_1 (Req1.1-1.4, POSITIVE CONTROL): four supplied ssl params land in child env under the four PG* vars. HOLDS patched, VIOLATED at base (base env has all four None) => discriminates.
- probe_2 (Req2.1-2.5): missing AND empty-string ssl params set none of the four vars.
- probe_3 (Req3.1-3.5,3.7): argv = [psql,-U user,-h host,-p port(str),dbname-last] and contains no ssl values.
- probe_4 (Req3.6,3.8): PGPASSWORD forwarded iff password supplied; env inherits os.environ (SBU_MARKER); dbname appended even when empty.
- probe_5 (Req1.6): non-string ssl values (int) coerced to str in env.
- probe_6 (Req2.5): supplying exactly one ssl param introduces exactly its own PGSSL var and no other.

Candidate wrong-fixes, both REJECTED by suite:
- weak_partial (only PGSSLMODE forwarded): rejected by probe_1 (root/cert/key None), probe_5, probe_6. Passes 2/3/4.
- weak_args (all four ssl params pushed into argv via --set instead of env): rejected by probe_1 (no env vars), probe_3 (ssl in argv), probe_5, probe_6.

All needed runs completed. >=5 probes hold on patched, positive control discriminates base vs patched, and at least one probe-conforming-partial candidate is rejected => suite has discriminating power. No too-weak or violation finding.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds sslmode/sslrootcert/sslcert/sslkey via conn_params.get(...,'') and, guarded by truthiness, injects str(value) into subprocess_env under PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY. Requirements pin exactly this observable boundary — the four env vars, truthy-gating (empty string treated as absent), str coercion, argv untouched by TLS params, and full preservation of prior argv/PGPASSWORD/signal behavior. Modeling boundary is correct (the changed observable = child env), not a narrow slice or an invented behavior. Probes run on the patched tree in the instance image confirm all criteria (subprocess.run mocked to capture args/env).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The four TLS connection params (sslmode, sslrootcert, sslcert, sslkey) and an example OPTIONS mapping are explicitly in the public problem_statement. The requirements map them to the standard PostgreSQL PGSSLMODE/PGSSLROOTCERT/PGSSLCERT/PGSSLKEY env vars — these are canonical PostgreSQL variable names dictated by behavior, not identifiers invented by the gold patch (the patch merely uses subprocess_env keys that the psql client reads). The doc names the module/classmethod (client.py, runshell_db) for localization, which is legitimate. No hidden-test content leaks: no test function names (test_ssl_certificate), no test file path (tests/dbshell/test_postgresql.py), no gold test literal values (verify-ca, root.crt, client.crt, client.key), no parametrization-mirroring enumeration. Requirement 3 restates pre-existing invocation/SIGINT behavior visible in the base code and the PASS_TO_PASS description, i.e. describes behavior rather than transmitting the tests. Str-coercion clause (Req1.6/3.4/3.6) matches str(...) in gold but is standard behavioral description, not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
