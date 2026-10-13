# P2 adversarial audit — django__django-10973

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1.1-1.11: the psql argument vector is exactly
[psql, -U user, -h host, -p str(port), dbname], verbatim (colons/backslashes
untransformed) and independent of the password."""
import os, signal, subprocess
from django.db.backends.postgresql.client import DatabaseClient

calls = []
def fake(args, **kw):
    calls.append(list(args))
    class R: returncode = 0
    return R()
subprocess.run = fake
subprocess.check_call = fake

# verbatim tricky values
user = r"u:s\er"
host = "::1"
port = 5432
db   = r"db:na\me"

# with password
DatabaseClient.runshell_db({'user': user, 'host': host, 'port': port,
                            'database': db, 'password': 'p:w\\d'})
# without password
DatabaseClient.runshell_db({'user': user, 'host': host, 'port': port,
                            'database': db, 'password': ''})

expected = ['psql', '-U', user, '-h', host, '-p', str(port), db]
print("with-pass  args:", calls[0])
print("no-pass    args:", calls[1])
print("expected       :", expected)
ok = calls[0] == expected and calls[1] == expected
if not ok:
    raise SystemExit("arg vector mismatch or password-dependent")
print("OK: arg vector correct, verbatim, password-independent")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.3/1.5/1.7/1.8: when user/host/port are absent, no flag is appended;
the database name is appended unconditionally (empty string when absent)."""
import subprocess
from django.db.backends.postgresql.client import DatabaseClient

calls = []
def fake(args, **kw):
    calls.append(list(args));
    class R: returncode = 0
    return R()
subprocess.run = fake
subprocess.check_call = fake

# everything absent
DatabaseClient.runshell_db({})
print("all-absent args:", calls[0])
if calls[0] != ['psql', '']:
    raise SystemExit("expected ['psql',''] when all params absent")

# only db present
calls.clear()
DatabaseClient.runshell_db({'database': 'mydb'})
print("only-db args:", calls[0])
if calls[0] != ['psql', 'mydb']:
    raise SystemExit("expected ['psql','mydb']")

# ensure no stray -U/-h/-p
for c in ('-U', '-h', '-p'):
    if c in calls[0]:
        raise SystemExit(f"unexpected {c}")
print("OK: absent params emit no flags; dbname always last")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.4/2.6: password supplied => child env has PGPASSWORD set
verbatim (colons & non-ASCII intact); env is otherwise a copy of os.environ;
the parent's own environment is NOT mutated (no PGPASSWORD, no PGPASSFILE)."""
import os, subprocess
from django.db.backends.postgresql.client import DatabaseClient

captured = {}
def fake(args, **kw):
    captured['env'] = kw.get('env')
    class R: returncode = 0
    return R()
subprocess.run = fake
subprocess.check_call = fake  # base uses check_call(args) with no env -> None

os.environ['SBU_MARKER'] = 'sentinel-value'
os.environ.pop('PGPASSWORD', None)
os.environ.pop('PGPASSFILE', None)

pw = 'sés:ame'  # non-ascii + colon
DatabaseClient.runshell_db({'database': 'd', 'password': pw})

env = captured['env']
print("child env is None?:", env is None)
if env is None:
    raise SystemExit("child env not passed (base behavior)")
print("PGPASSWORD in child:", repr(env.get('PGPASSWORD')))
if env.get('PGPASSWORD') != pw:
    raise SystemExit("PGPASSWORD not verbatim")
if env.get('SBU_MARKER') != 'sentinel-value':
    raise SystemExit("child env is not a copy of os.environ")
# parent env must be untouched
if 'PGPASSWORD' in os.environ:
    raise SystemExit("parent os.environ was mutated with PGPASSWORD")
if 'PGPASSFILE' in os.environ:
    raise SystemExit("parent os.environ was mutated with PGPASSFILE")
print("OK: PGPASSWORD verbatim in child copy; parent env untouched")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.3/2.5: no password supplied => PGPASSWORD is NOT defined in the child
env; and NO temporary password file mechanism is used (NamedTemporaryFile is
never called, PGPASSFILE never set in child or parent)."""
import os, subprocess
from django.db.backends.postgresql import client as clientmod
from django.db.backends.postgresql.client import DatabaseClient
import django.core.files.temp as tempmod

captured = {}
def fake(args, **kw):
    captured['env'] = kw.get('env')
    class R: returncode = 0
    return R()
subprocess.run = fake
subprocess.check_call = fake

# detect any temp-file creation
ntf_calls = []
orig = tempmod.NamedTemporaryFile
def spy(*a, **k):
    ntf_calls.append((a, k))
    return orig(*a, **k)
tempmod.NamedTemporaryFile = spy
if hasattr(clientmod, 'NamedTemporaryFile'):
    clientmod.NamedTemporaryFile = spy

os.environ.pop('PGPASSWORD', None)
os.environ.pop('PGPASSFILE', None)

DatabaseClient.runshell_db({'database': 'd', 'password': ''})

env = captured['env']
print("child env is None?:", env is None)
print("NamedTemporaryFile calls:", len(ntf_calls))
if len(ntf_calls) != 0:
    raise SystemExit("temporary password file was created")
# child env, if provided, must not have PGPASSWORD or PGPASSFILE
if env is not None:
    if 'PGPASSWORD' in env:
        raise SystemExit("PGPASSWORD defined despite no password")
    if 'PGPASSFILE' in env and env.get('PGPASSFILE') != os.environ.get('PGPASSFILE'):
        raise SystemExit("PGPASSFILE injected into child")
if 'PGPASSFILE' in os.environ:
    raise SystemExit("PGPASSFILE set in parent env")
print("OK: no password => no PGPASSWORD, no temp file, no PGPASSFILE")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2: SIGINT is ignored (SIG_IGN) while the client is launched, and
the previously-installed handler is restored when runshell_db returns
(including when the client raises)."""
import signal, subprocess
from django.db.backends.postgresql.client import DatabaseClient

# install a distinctive handler before the call
def my_handler(signum, frame):
    pass
prev = signal.signal(signal.SIGINT, my_handler)

seen = {}
def fake(args, **kw):
    seen['during'] = signal.getsignal(signal.SIGINT)
    class R: returncode = 0
    return R()
subprocess.run = fake
subprocess.check_call = fake

DatabaseClient.runshell_db({'database': 'd'})
after_ok = signal.getsignal(signal.SIGINT)

# now failure path: client raises -> handler must still be restored
def boom(args, **kw):
    seen['during_fail'] = signal.getsignal(signal.SIGINT)
    raise subprocess.CalledProcessError(1, args)
subprocess.run = boom
subprocess.check_call = boom
raised = False
try:
    DatabaseClient.runshell_db({'database': 'd'})
except Exception:
    raised = True
after_fail = signal.getsignal(signal.SIGINT)

# restore for cleanliness
signal.signal(signal.SIGINT, prev)

print("during launch:", seen.get('during'))
print("after success:", after_ok, "  restored==my_handler:", after_ok is my_handler)
print("during fail  :", seen.get('during_fail'))
print("after fail   :", after_fail, "  raised:", raised)

if seen.get('during') != signal.SIG_IGN:
    raise SystemExit("SIGINT not ignored during launch")
if after_ok is not my_handler:
    raise SystemExit("handler not restored after success")
if seen.get('during_fail') != signal.SIG_IGN:
    raise SystemExit("SIGINT not ignored during launch (fail path)")
if after_fail is not my_handler:
    raise SystemExit("handler not restored after failure")
if not raised:
    raise SystemExit("failure was not propagated")
print("OK: SIGINT ignored during launch, restored on success and failure")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.2/4.3: a nonzero client exit raises (rather than returning normally),
and runshell delegates to runshell_db with the connection's params."""
import subprocess
from django.db.backends.postgresql.client import DatabaseClient

# --- 4.2: nonzero exit raises ---
def nonzero(args, **kw):
    # emulate check=True semantics: run with check=True must raise
    if kw.get('check'):
        raise subprocess.CalledProcessError(2, args)
    class R:
        returncode = 2
    return R()
subprocess.run = nonzero
def cc_nonzero(args, **kw):
    raise subprocess.CalledProcessError(2, args)
subprocess.check_call = cc_nonzero

raised = False
try:
    DatabaseClient.runshell_db({'database': 'd'})
except Exception as e:
    raised = True
    print("raised:", type(e).__name__)
if not raised:
    raise SystemExit("nonzero exit did not raise")

# --- 4.3: runshell delegates to runshell_db(get_connection_params()) ---
captured = {}
def fake(args, **kw):
    class R: returncode = 0
    return R()
subprocess.run = fake
subprocess.check_call = fake

orig = DatabaseClient.runshell_db.__func__
def spy(cls, conn_params):
    captured['params'] = conn_params
    return orig(cls, conn_params)
DatabaseClient.runshell_db = classmethod(spy)

class Conn:
    def get_connection_params(self):
        return {'database': 'sentinel_db', 'user': 'x'}
dc = DatabaseClient(Conn())
dc.runshell()
print("delegated params:", captured.get('params'))
if captured.get('params') != {'database': 'sentinel_db', 'user': 'x'}:
    raise SystemExit("runshell did not delegate connection params")
print("OK: nonzero exit raises; runshell delegates connection params")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3.py`

```python
"""Req 2.1/2.2/2.4/2.6: password supplied => child env has PGPASSWORD set
verbatim (colons & non-ASCII intact); env is otherwise a copy of os.environ;
the parent's own environment is NOT mutated (no PGPASSWORD, no PGPASSFILE)."""
import os, subprocess
from django.db.backends.postgresql.client import DatabaseClient

captured = {}
def fake(args, **kw):
    captured['env'] = kw.get('env')
    class R: returncode = 0
    return R()
subprocess.run = fake
subprocess.check_call = fake  # base uses check_call(args) with no env -> None

os.environ['SBU_MARKER'] = 'sentinel-value'
os.environ.pop('PGPASSWORD', None)
os.environ.pop('PGPASSFILE', None)

pw = 'sés:ame'  # non-ascii + colon
DatabaseClient.runshell_db({'database': 'd', 'password': pw})

env = captured['env']
print("child env is None?:", env is None)
if env is None:
    raise SystemExit("child env not passed (base behavior)")
print("PGPASSWORD in child:", repr(env.get('PGPASSWORD')))
if env.get('PGPASSWORD') != pw:
    raise SystemExit("PGPASSWORD not verbatim")
if env.get('SBU_MARKER') != 'sentinel-value':
    raise SystemExit("child env is not a copy of os.environ")
# parent env must be untouched
if 'PGPASSWORD' in os.environ:
    raise SystemExit("parent os.environ was mutated with PGPASSWORD")
if 'PGPASSFILE' in os.environ:
    raise SystemExit("parent os.environ was mutated with PGPASSFILE")
print("OK: PGPASSWORD verbatim in child copy; parent env untouched")
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes cover Reqs 1-4 including regression 'SHALL keep' criteria. probe_1: arg vector [psql,-U u,-h h,-p str(port),dbname], verbatim (colon/backslash untransformed), password-independent (Req 1.1-1.11). probe_2: absent params emit no flags; dbname always last, empty when absent (Req 1.3/1.5/1.7/1.8). probe_3 (POSITIVE CONTROL): password supplied => child env PGPASSWORD set verbatim incl non-ascii+colon, env is copy of os.environ (SBU_MARKER survives), parent env NOT mutated (Req 2.1/2.2/2.4/2.6). probe_4: no password => no PGPASSWORD, no NamedTemporaryFile, no PGPASSFILE (Req 2.3/2.5). probe_5: SIGINT SIG_IGN during launch, restored on success AND failure (Req 3.1/3.2). probe_6: nonzero exit raises; runshell delegates get_connection_params() (Req 4.2/4.3).

All 6 HOLD on gold-patched tree. Positive control probe_3 discriminates: VIOLATED at base (base passes no env => child env is None), HOLDS patched. (probe_1 & probe_4 correctly HOLD at base — arg vector and no-password-no-tempfile behaviors are unchanged by the fix, so they are regression checks not discriminators.)

Two wrong-fix candidates, both applied at base and REJECTED by the suite (probe_3 catches both):
- weak_escape: sets PGPASSWORD = _escape_pgpass(passwd) (colon/backslash escaped) — violates Req 2.2 verbatim delivery. probe_3 VIOLATED (would break test_column/test_accent).
- weak_envmutate: mutates the PARENT os.environ['PGPASSWORD'] instead of passing a child env — violates Req 2.4/2.6. probe_3 VIOLATED (child env None + parent mutated).

Suite discriminates wrong implementations; no requirement-conforming candidate found that fails the harness. Note: G-PANEL-3 fail (test-fixture leakage 'sésame'/'::1'/'some:password') is a leakage concern, orthogonal to G-EQ spec-fidelity. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_3.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_3.py`

```python
"""Req 2.1/2.2/2.4/2.6: password supplied => child env has PGPASSWORD set
verbatim (colons & non-ASCII intact); env is otherwise a copy of os.environ;
the parent's own environment is NOT mutated (no PGPASSWORD, no PGPASSFILE)."""
import os, subprocess
from django.db.backends.postgresql.client import DatabaseClient

captured = {}
def fake(args, **kw):
    captured['env'] = kw.get('env')
    class R: returncode = 0
    return R()
subprocess.run = fake
subprocess.check_call = fake  # base uses check_call(args) with no env -> None

os.environ['SBU_MARKER'] = 'sentinel-value'
os.environ.pop('PGPASSWORD', None)
os.environ.pop('PGPASSFILE', None)

pw = 'sés:ame'  # non-ascii + colon
DatabaseClient.runshell_db({'database': 'd', 'password': pw})

env = captured['env']
print("child env is None?:", env is None)
if env is None:
    raise SystemExit("child env not passed (base behavior)")
print("PGPASSWORD in child:", repr(env.get('PGPASSWORD')))
if env.get('PGPASSWORD') != pw:
    raise SystemExit("PGPASSWORD not verbatim")
if env.get('SBU_MARKER') != 'sentinel-value':
    raise SystemExit("child env is not a copy of os.environ")
# parent env must be untouched
if 'PGPASSWORD' in os.environ:
    raise SystemExit("parent os.environ was mutated with PGPASSWORD")
if 'PGPASSFILE' in os.environ:
    raise SystemExit("parent os.environ was mutated with PGPASSFILE")
print("OK: PGPASSWORD verbatim in child copy; parent env untouched")
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes cover Reqs 1-4 including regression 'SHALL keep' criteria. probe_1: arg vector [psql,-U u,-h h,-p str(port),dbname], verbatim (colon/backslash untransformed), password-independent (Req 1.1-1.11). probe_2: absent params emit no flags; dbname always last, empty when absent (Req 1.3/1.5/1.7/1.8). probe_3 (POSITIVE CONTROL): password supplied => child env PGPASSWORD set verbatim incl non-ascii+colon, env is copy of os.environ (SBU_MARKER survives), parent env NOT mutated (Req 2.1/2.2/2.4/2.6). probe_4: no password => no PGPASSWORD, no NamedTemporaryFile, no PGPASSFILE (Req 2.3/2.5). probe_5: SIGINT SIG_IGN during launch, restored on success AND failure (Req 3.1/3.2). probe_6: nonzero exit raises; runshell delegates get_connection_params() (Req 4.2/4.3).

All 6 HOLD on gold-patched tree. Positive control probe_3 discriminates: VIOLATED at base (base passes no env => child env is None), HOLDS patched. (probe_1 & probe_4 correctly HOLD at base — arg vector and no-password-no-tempfile behaviors are unchanged by the fix, so they are regression checks not discriminators.)

Two wrong-fix candidates, both applied at base and REJECTED by the suite (probe_3 catches both):
- weak_escape: sets PGPASSWORD = _escape_pgpass(passwd) (colon/backslash escaped) — violates Req 2.2 verbatim delivery. probe_3 VIOLATED (would break test_column/test_accent).
- weak_envmutate: mutates the PARENT os.environ['PGPASSWORD'] instead of passing a child env — violates Req 2.4/2.6. probe_3 VIOLATED (child env None + parent mutated).

Suite discriminates wrong implementations; no requirement-conforming candidate found that fails the harness. Note: G-PANEL-3 fail (test-fixture leakage 'sésame'/'::1'/'some:password') is a leakage concern, orthogonal to G-EQ spec-fidelity. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces temp .pgpass file + _escape_pgpass with subprocess.run(env=os.environ.copy()+PGPASSWORD). Probe (patched tree, exit 0) confirmed all four requirements including the key semantic shifts: verbatim (no escaping) password delivery and PGPASSWORD-absent-when-no-password. Requirements correctly pin the removal of escaping and the file mechanism — the actual behavioral change — rather than a single branch.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior only. Public problem_statement already gives subprocess.run + PGPASSWORD + postgres client + 'simplifies escaping code'. Module/function/env-var names (runshell_db, client.py, psql, PGPASSWORD, PGPASSFILE, temporary password file) are legitimate localization and description of the OLD (pre-patch) behavior readable directly from the source, not test/gold-derived identifiers. The colon/backslash/accented-character examples (Req 1.10, 2.2) track the removed _escape_pgpass semantics (escapes ':' and '\\') and the removed UnicodeEncodeError path — they specify 'no transformation is applied' in behavioral terms rather than transmitting the tests. None of the hidden-test surface leaks: no test names/paths (test_basic/test_column/test_accent/test_nopass), no fixture literals ('someuser','somehost','444','rôle','sésame','some:user','::1'), no mock structure (subprocess.run patch, CompletedProcess), and no gold-invented identifiers reproduced. Examples are behavioral edge cases, not a mirror of the test parametrization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
