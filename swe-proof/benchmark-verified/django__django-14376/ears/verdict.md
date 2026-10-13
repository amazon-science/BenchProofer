# P2 adversarial audit — django__django-14376

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# R1.1 & R1.2 (POSITIVE CONTROL): get_connection_params records NAME under
# 'database' (not 'db') and PASSWORD under 'password' (not 'passwd').
import sys, types
mysqldb = types.ModuleType('MySQLdb'); mysqldb.version_info=(1,4,0); mysqldb.__version__='1.4.0'
mysqldb.connect=lambda **kw: None
class _Any:
    _n=0
    def __getattr__(self,k):
        _Any._n+=1; return _Any._n
c=types.ModuleType('MySQLdb.constants'); c.CLIENT=_Any(); c.FIELD_TYPE=_Any()
cv=types.ModuleType('MySQLdb.converters'); cv.conversions={}
mysqldb.constants=c; mysqldb.converters=cv
sys.modules['MySQLdb']=mysqldb; sys.modules['MySQLdb.constants']=c; sys.modules['MySQLdb.converters']=cv
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}); django.setup()
from django.db.backends.mysql.base import DatabaseWrapper
sd={'ENGINE':'django.db.backends.mysql','NAME':'mydb','USER':'u','PASSWORD':'secret',
    'HOST':'localhost','PORT':'3306','OPTIONS':{},'TIME_ZONE':None,'CONN_MAX_AGE':0,
    'AUTOCOMMIT':True,'ATOMIC_REQUESTS':False,'CONN_HEALTH_CHECKS':False}
kw=DatabaseWrapper(sd,'default').get_connection_params()
print("keys:", sorted(kw.keys()))
ok = (kw.get('database')=='mydb' and 'db' not in kw
      and kw.get('password')=='secret' and 'passwd' not in kw)
print("database==mydb:", kw.get('database')=='mydb', "| no 'db':", 'db' not in kw)
print("password==secret:", kw.get('password')=='secret', "| no 'passwd':", 'passwd' not in kw)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.3 & R1.4 & R1.5: empty NAME/PASSWORD add no entry; other keys preserved.
import sys, types
mysqldb = types.ModuleType('MySQLdb'); mysqldb.version_info=(1,4,0); mysqldb.__version__='1.4.0'
mysqldb.connect=lambda **kw: None
class _Any:
    _n=0
    def __getattr__(self,k):
        _Any._n+=1; return _Any._n
c=types.ModuleType('MySQLdb.constants'); c.CLIENT=_Any(); c.FIELD_TYPE=_Any()
cv=types.ModuleType('MySQLdb.converters'); cv.conversions={}
mysqldb.constants=c; mysqldb.converters=cv
sys.modules['MySQLdb']=mysqldb; sys.modules['MySQLdb.constants']=c; sys.modules['MySQLdb.converters']=cv
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}); django.setup()
from django.db.backends.mysql.base import DatabaseWrapper
def params(**over):
    sd={'ENGINE':'django.db.backends.mysql','NAME':'mydb','USER':'u','PASSWORD':'secret',
        'HOST':'localhost','PORT':'3306','OPTIONS':{},'TIME_ZONE':None,'CONN_MAX_AGE':0,
        'AUTOCOMMIT':True,'ATOMIC_REQUESTS':False,'CONN_HEALTH_CHECKS':False}
    sd.update(over)
    return DatabaseWrapper(sd,'default').get_connection_params()

kw=params(NAME='', PASSWORD='')
print("empty NAME/PWD keys:", sorted(kw.keys()))
r3 = ('database' not in kw and 'db' not in kw)      # R1.3
r4 = ('password' not in kw and 'passwd' not in kw)  # R1.4
# R1.5: other pre-existing entries preserved (user/host/port from a full config)
kw2=params()
r5 = (kw2.get('user')=='u' and kw2.get('host')=='localhost' and kw2.get('port')==3306)
# unix socket branch
kw3=params(HOST='/var/run/mysqld/mysqld.sock')
r5b = (kw3.get('unix_socket')=='/var/run/mysqld/mysqld.sock' and 'host' not in kw3)
print("R1.3 no db-name:", r3, "| R1.4 no pwd:", r4, "| R1.5 others:", r5, "| socket:", r5b)
sys.exit(0 if (r3 and r4 and r5 and r5b) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R2: database-name selection precedence in settings_to_cmd_args_env.
import sys
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}); django.setup()
from django.db.backends.mysql.client import DatabaseClient

def sd(name='cfgname', options=None):
    return {'NAME':name,'USER':'u','PASSWORD':'','HOST':'','PORT':'','OPTIONS':options or {}}

def run(name, options, params=None):
    args, env = DatabaseClient.settings_to_cmd_args_env(sd(name, options), params or [])
    return args

# R2.1: OPTIONS['database'] wins over db and NAME
a = run('cfgname', {'database':'optdb','db':'legacydb'})
r1 = a[-1]=='optdb'
# R2.2: no 'database' but 'db' -> use db over NAME
a = run('cfgname', {'db':'legacydb'})
r2 = a[-1]=='legacydb'
# R2.3: neither -> NAME
a = run('cfgname', {})
r3 = a[-1]=='cfgname'
# R2.5: chosen non-empty name is final token, after flags before params
a = run('cfgname', {'database':'optdb'}, ['--extra'])
r5 = (a[-1]=='--extra' and a[-2]=='optdb')
# R2.6: chosen empty name (NAME empty, no options) -> no db token appended.
# With USER set, args ends at the --user flag; no bare db-name token follows.
a = run('', {})
r6 = (a==['mysql','--user=u']) and not any(not x.startswith('-') for x in a[1:])
print("R2.1:",r1,"R2.2:",r2,"R2.3:",r3,"R2.5:",r5,"R2.6:",r6)
print("sample r5 args:", run('cfgname', {'database':'optdb'}, ['--extra']))
sys.exit(0 if (r1 and r2 and r3 and r5 and r6) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2.4: OPTIONS['database'] present but EMPTY -> selection by key presence, not
# truthiness: empty chosen name, MUST NOT fall back to 'db' or NAME.
import sys
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}); django.setup()
from django.db.backends.mysql.client import DatabaseClient

sd = {'NAME':'cfgname','USER':'u','PASSWORD':'','HOST':'','PORT':'',
      'OPTIONS':{'database':'','db':'legacydb'}}
args, env = DatabaseClient.settings_to_cmd_args_env(sd, [])
print("args:", args)
# Empty chosen name -> no db token; must NOT contain legacydb or cfgname; and
# no bare (non-flag) positional db token appears after argv[0].
positionals = [x for x in args[1:] if not x.startswith('-')]
ok = ('legacydb' not in args) and ('cfgname' not in args) and (positionals==[])
print("no fallback to db/NAME and no db token:", ok, "| positionals:", positionals)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3 (password precedence) + R4 (password via env not argv; other flags preserved).
import sys
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}); django.setup()
from django.db.backends.mysql.client import DatabaseClient

def sd(pwd='cfgpwd', options=None, host='localhost', port='3306', user='u', name='mydb'):
    o={'OPTIONS':options or {}}
    return {'NAME':name,'USER':user,'PASSWORD':pwd,'HOST':host,'PORT':port,**o}

def run(**kw):
    return DatabaseClient.settings_to_cmd_args_env(sd(**kw), [])

# R3.1: OPTIONS['password'] wins
a,e = run(options={'password':'optpwd','passwd':'legacy'})
r31 = (e.get('MYSQL_PWD')=='optpwd')
# R3.2: passwd fallback
a,e = run(options={'passwd':'legacy'})
r32 = (e.get('MYSQL_PWD')=='legacy')
# R3.3: neither -> configured PASSWORD
a,e = run(options={})
r33 = (e.get('MYSQL_PWD')=='cfgpwd')
# R4.1: password conveyed in env, never in argv
a,e = run(options={'password':'topsecret'})
r41 = ('topsecret' not in a) and (e.get('MYSQL_PWD')=='topsecret') and \
      (not any('topsecret' in x for x in a))
# R4.2: no password -> no env mapping
a,e = run(pwd='', options={})
r42 = (e is None)
# R4.3: other flags preserved (user/host/port formatting)
a,e = run(options={})
r43 = ('--user=u' in a and '--host=localhost' in a and '--port=3306' in a)
# socket variant
a,e = run(host='$SCRATCH', options={})
r43b = any(x.startswith('--socket=$SCRATCH') for x in a)
print("R3.1:",r31,"R3.2:",r32,"R3.3:",r33)
print("R4.1:",r41,"R4.2:",r42,"R4.3:",r43,"socket:",r43b)
sys.exit(0 if all([r31,r32,r33,r41,r42,r43,r43b]) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R4.4 (extra params appended after db token) + R4.5 (missing required key fails).
import sys
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}); django.setup()
from django.db.backends.mysql.client import DatabaseClient

# R4.4: extra params at the very end, after db-name token
sd = {'NAME':'mydb','USER':'u','PASSWORD':'','HOST':'','PORT':'','OPTIONS':{}}
args, env = DatabaseClient.settings_to_cmd_args_env(sd, ['-e', 'SELECT 1'])
print("args:", args)
r44 = (args[-2:]==['-e','SELECT 1']) and (args[-3]=='mydb')

# R4.5: missing required top-level key -> fail (raise), not silent partial command
bad = {'USER':'u','PASSWORD':'','HOST':'','PORT':'','OPTIONS':{}}  # NAME missing
raised = False
try:
    DatabaseClient.settings_to_cmd_args_env(bad, [])
except Exception as ex:
    raised = True
    print("raised:", type(ex).__name__)
print("R4.4:", r44, "R4.5 raises:", raised)
sys.exit(0 if (r44 and raised) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 & R1.2 (POSITIVE CONTROL): get_connection_params records NAME under
# 'database' (not 'db') and PASSWORD under 'password' (not 'passwd').
import sys, types
mysqldb = types.ModuleType('MySQLdb'); mysqldb.version_info=(1,4,0); mysqldb.__version__='1.4.0'
mysqldb.connect=lambda **kw: None
class _Any:
    _n=0
    def __getattr__(self,k):
        _Any._n+=1; return _Any._n
c=types.ModuleType('MySQLdb.constants'); c.CLIENT=_Any(); c.FIELD_TYPE=_Any()
cv=types.ModuleType('MySQLdb.converters'); cv.conversions={}
mysqldb.constants=c; mysqldb.converters=cv
sys.modules['MySQLdb']=mysqldb; sys.modules['MySQLdb.constants']=c; sys.modules['MySQLdb.converters']=cv
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}); django.setup()
from django.db.backends.mysql.base import DatabaseWrapper
sd={'ENGINE':'django.db.backends.mysql','NAME':'mydb','USER':'u','PASSWORD':'secret',
    'HOST':'localhost','PORT':'3306','OPTIONS':{},'TIME_ZONE':None,'CONN_MAX_AGE':0,
    'AUTOCOMMIT':True,'ATOMIC_REQUESTS':False,'CONN_HEALTH_CHECKS':False}
kw=DatabaseWrapper(sd,'default').get_connection_params()
print("keys:", sorted(kw.keys()))
ok = (kw.get('database')=='mydb' and 'db' not in kw
      and kw.get('password')=='secret' and 'passwd' not in kw)
print("database==mydb:", kw.get('database')=='mydb', "| no 'db':", 'db' not in kw)
print("password==secret:", kw.get('password')=='secret', "| no 'passwd':", 'passwd' not in kw)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14376: MySQL backend should use non-deprecated driver kwargs (database/password instead of db/passwd) in base.py get_connection_params, and client.py settings_to_cmd_args_env should honor the modern OPTIONS['database']/'password' keys with db/passwd fallback, selecting by KEY PRESENCE not truthiness.

Environment note: MySQLdb is not installed in the image, so mysql.base fails to import at module level. Probes 1-2 (Requirement 1) install a minimal fake MySQLdb stub (version_info + auto-attribute CLIENT/FIELD_TYPE namespaces + empty conversions) so base.py imports; then instantiate DatabaseWrapper and call get_connection_params. Probes 3-6 (Requirements 2-4) exercise DatabaseClient.settings_to_cmd_args_env directly (no driver needed). Each probe is fully self-contained (runner copies only the single file).

### PROBES (all HOLD on gold-patched tree):
- probe_1.py = R1.1 & R1.2 (POSITIVE CONTROL): NAME recorded under 'database' not 'db'; PASSWORD under 'password' not 'passwd'. Patched keys={database,password,...}; BASE keys={db,passwd,...} -> FAILS at base. Discriminates.
- probe_2.py = R1.3/R1.4/R1.5: empty NAME/PASSWORD add no db-name/password entry; user/host/port and unix_socket branch preserved.
- probe_3.py = R2.1/R2.2/R2.3/R2.5/R2.6: db-name precedence OPTIONS['database'] > OPTIONS['db'] > NAME; chosen name is final token after flags before extra params; empty chosen name appends no bare positional token. (R2.6/R2.5 checks use 'no bare non-flag positional' rather than exact args to tolerate the --user flag.)
- probe_4.py = R2.4: OPTIONS['database']=='' present -> selection by key presence, must NOT fall back to db/NAME; no positional db token. Patched OK; BASE and both weak candidates append 'legacydb' -> caught.
- probe_5.py = R3.1/R3.2/R3.3 + R4.1/R4.2/R4.3: password precedence password>passwd>PASSWORD; password conveyed via MYSQL_PWD env and never in argv; env=None when no password; user/host/port/socket flag formatting preserved.
- probe_6.py = R4.4 + R4.5: extra parameters appended after the db-name token; missing required top-level key (NAME) raises rather than silently building a partial command.

RESULTS on gold-patched tree: probes 1-6 ALL HOLD (exit 0).
POSITIVE CONTROL probe_1 at BASE: VIOLATED (db/passwd), so prepatch_reproduced=true — discriminating power confirmed by the runner-visible base run. probe_3 and probe_4 also fail at base.

### CANDIDATE PATCHES (both apply at base_commit; both REJECTED by the suite -> not too-weak):
- weakA.diff (naive/partial fix): fixes base.py only, leaves client.py using OPTIONS.get('db', NAME). Probe_1 HOLDS but probe_3 (R2.1: database key ignored) and probe_4 (R2.4 empty-key) VIOLATE. Would not resolve the client-side hidden tests.
- weakB.diff (truthiness bug): fixes base.py and client.py, but selects database via `OPTIONS.get('database') or OPTIONS.get('db', NAME)` (truthiness, not key presence). Probes 1,2,3,5,6 HOLD but probe_4 (R2.4) VIOLATES: with OPTIONS['database']=='' it wrongly falls back to 'db'='legacydb'. This is exactly the by-key-presence-not-truthiness distinction the requirements pin, and matches the gold code's nested .get structure.

Both wrong candidates are rejected, and every requirement criterion (incl. the SHALL-keep regressions in R1.5/R4.3/R4.4/R4.5) is encoded and holds on the patched tree. No requirement mandates behavior absent from gold; no probe-conforming alternative that resolves was found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
# R1.1 & R1.2 (POSITIVE CONTROL): get_connection_params records NAME under
# 'database' (not 'db') and PASSWORD under 'password' (not 'passwd').
import sys, types
mysqldb = types.ModuleType('MySQLdb'); mysqldb.version_info=(1,4,0); mysqldb.__version__='1.4.0'
mysqldb.connect=lambda **kw: None
class _Any:
    _n=0
    def __getattr__(self,k):
        _Any._n+=1; return _Any._n
c=types.ModuleType('MySQLdb.constants'); c.CLIENT=_Any(); c.FIELD_TYPE=_Any()
cv=types.ModuleType('MySQLdb.converters'); cv.conversions={}
mysqldb.constants=c; mysqldb.converters=cv
sys.modules['MySQLdb']=mysqldb; sys.modules['MySQLdb.constants']=c; sys.modules['MySQLdb.converters']=cv
import django
from django.conf import settings
settings.configure(DEBUG=True, DATABASES={}); django.setup()
from django.db.backends.mysql.base import DatabaseWrapper
sd={'ENGINE':'django.db.backends.mysql','NAME':'mydb','USER':'u','PASSWORD':'secret',
    'HOST':'localhost','PORT':'3306','OPTIONS':{},'TIME_ZONE':None,'CONN_MAX_AGE':0,
    'AUTOCOMMIT':True,'ATOMIC_REQUESTS':False,'CONN_HEALTH_CHECKS':False}
kw=DatabaseWrapper(sd,'default').get_connection_params()
print("keys:", sorted(kw.keys()))
ok = (kw.get('database')=='mydb' and 'db' not in kw
      and kw.get('password')=='secret' and 'passwd' not in kw)
print("database==mydb:", kw.get('database')=='mydb', "| no 'db':", 'db' not in kw)
print("password==secret:", kw.get('password')=='secret', "| no 'passwd':", 'passwd' not in kw)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14376: MySQL backend should use non-deprecated driver kwargs (database/password instead of db/passwd) in base.py get_connection_params, and client.py settings_to_cmd_args_env should honor the modern OPTIONS['database']/'password' keys with db/passwd fallback, selecting by KEY PRESENCE not truthiness.

Environment note: MySQLdb is not installed in the image, so mysql.base fails to import at module level. Probes 1-2 (Requirement 1) install a minimal fake MySQLdb stub (version_info + auto-attribute CLIENT/FIELD_TYPE namespaces + empty conversions) so base.py imports; then instantiate DatabaseWrapper and call get_connection_params. Probes 3-6 (Requirements 2-4) exercise DatabaseClient.settings_to_cmd_args_env directly (no driver needed). Each probe is fully self-contained (runner copies only the single file).

### PROBES (all HOLD on gold-patched tree):
- probe_1.py = R1.1 & R1.2 (POSITIVE CONTROL): NAME recorded under 'database' not 'db'; PASSWORD under 'password' not 'passwd'. Patched keys={database,password,...}; BASE keys={db,passwd,...} -> FAILS at base. Discriminates.
- probe_2.py = R1.3/R1.4/R1.5: empty NAME/PASSWORD add no db-name/password entry; user/host/port and unix_socket branch preserved.
- probe_3.py = R2.1/R2.2/R2.3/R2.5/R2.6: db-name precedence OPTIONS['database'] > OPTIONS['db'] > NAME; chosen name is final token after flags before extra params; empty chosen name appends no bare positional token. (R2.6/R2.5 checks use 'no bare non-flag positional' rather than exact args to tolerate the --user flag.)
- probe_4.py = R2.4: OPTIONS['database']=='' present -> selection by key presence, must NOT fall back to db/NAME; no positional db token. Patched OK; BASE and both weak candidates append 'legacydb' -> caught.
- probe_5.py = R3.1/R3.2/R3.3 + R4.1/R4.2/R4.3: password precedence password>passwd>PASSWORD; password conveyed via MYSQL_PWD env and never in argv; env=None when no password; user/host/port/socket flag formatting preserved.
- probe_6.py = R4.4 + R4.5: extra parameters appended after the db-name token; missing required top-level key (NAME) raises rather than silently building a partial command.

RESULTS on gold-patched tree: probes 1-6 ALL HOLD (exit 0).
POSITIVE CONTROL probe_1 at BASE: VIOLATED (db/passwd), so prepatch_reproduced=true — discriminating power confirmed by the runner-visible base run. probe_3 and probe_4 also fail at base.

### CANDIDATE PATCHES (both apply at base_commit; both REJECTED by the suite -> not too-weak):
- weakA.diff (naive/partial fix): fixes base.py only, leaves client.py using OPTIONS.get('db', NAME). Probe_1 HOLDS but probe_3 (R2.1: database key ignored) and probe_4 (R2.4 empty-key) VIOLATE. Would not resolve the client-side hidden tests.
- weakB.diff (truthiness bug): fixes base.py and client.py, but selects database via `OPTIONS.get('database') or OPTIONS.get('db', NAME)` (truthiness, not key presence). Probes 1,2,3,5,6 HOLD but probe_4 (R2.4) VIOLATES: with OPTIONS['database']=='' it wrongly falls back to 'db'='legacydb'. This is exactly the by-key-presence-not-truthiness distinction the requirements pin, and matches the gold code's nested .get structure.

Both wrong candidates are rejected, and every requirement criterion (incl. the SHALL-keep regressions in R1.5/R4.3/R4.4/R4.5) is encoded and holds on the patched tree. No requirement mandates behavior absent from gold; no probe-conforming alternative that resolves was found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed via nl_attack on the gold-patched tree. client.py assertions ran directly (settings_to_cmd_args_env has no mysqlclient dependency); base.py could not be imported (image lacks MySQLdb), so Req 1 was verified by reading the patched /testbed source, which matches the diff verbatim. No requirement mandates behavior the code lacks, forbids behavior it has, or invents unpatched behavior. Modeling boundary is correct: both collaborating functions covered, including the deprecated-fallback precedence chain and the empty-value key-presence semantics that the patch's nested .get() introduces.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the gold patch behavior into EARS acceptance criteria without transmitting the hidden tests. The core db→database / passwd→password rename and mysqlclient version rationale are all in the public problem_statement. Naming the two changed modules/functions (base.py:get_connection_params, client.py:settings_to_cmd_args_env) is legitimate localization. Precedence orderings (OPTIONS['database'] > OPTIONS['db'] > NAME, and the password analog) follow directly from the gold code's nested `.get()` calls, not from the test assertions. No test file path (tests/dbshell/test_mysql.py), test function names (test_options_non_deprecated_keys_preferred, test_options_override_settings_proper_values, test_parameters), test string literals (optiondbname, deprecatedoptiondbname, optionpassword), the subTest parametrization tuple, or verbatim gold lines appear. Requirement 2.4 (empty-value / key-presence-not-truthiness) actually describes `.get()` semantics that the tests do not exercise, so it is behavioral description rather than test reconstruction. No case enumeration mirrors the test parametrization beyond the db/database + passwd/password pairing already public in the problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
