# P2 adversarial audit — django__django-14053

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_no_dup.py`, `probe_2_final_hash.py`, `probe_3_nonadjustable.py`, `probe_4_dry_run.py`, `probe_5_max_passes.py`, `probe_6_rewrite_correct.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_no_dup.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_no_dup.py` → holds on the patched tree (good)

```python
"""Requirement 1 (crit 1,2,3) + positive control: each original name yielded
at most once across a multi-pass rewrite. Also the core fixed behavior.
Exits 0 iff no original name (excluding the 'All' error record) is duplicated."""
import os, tempfile, shutil, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, STATIC_URL='/static/', INSTALLED_APPS=[])
    django.setup()
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import FileSystemStorage

class MyStorage(HashedFilesMixin, FileSystemStorage):
    pass

def build_chain(tmp, n):
    names = []
    for i in range(n):
        name = 'a%d.css' % i
        names.append(name)
        content = ('.c%d{background:url("a%d.css")}\n' % (i, i + 1)) if i < n - 1 else '.c%d{color:red}\n' % i
        open(os.path.join(tmp, name), 'w').write(content)
    return names

tmp = tempfile.mkdtemp()
try:
    s = MyStorage(location=tmp, base_url='/static/')
    names = build_chain(tmp, 4)
    paths = {name: (s, name) for name in names}
    recs = list(s.post_process(paths, dry_run=False))
    origs = [r[0] for r in recs if not (isinstance(r[2], Exception))]
    print("records:", recs)
    print("original names yielded:", origs)
    dups = [x for x in set(origs) if origs.count(x) > 1]
    print("duplicates:", dups)
    assert not dups, "duplicate original names yielded: %r" % dups
    # each of our 4 files must appear (they are all adjusted across passes)
    assert set(origs) >= set(names), "missing some files: %r" % (set(names) - set(origs))
    print("OK: each original name yielded exactly once")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

Attack 2 — `probe_2_final_hash.py` → holds on the patched tree (good)

```python
"""Requirement 2 (crit 1,2,3): the single record for a multi-pass adjustable
file carries its FINAL hashed name (the one stored in hashed_files / that the
last pass produced), never a superseded intermediate. Exits 0 iff the yielded
hashed_name for every file equals the final stored hashed name."""
import os, tempfile, shutil, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, STATIC_URL='/static/', INSTALLED_APPS=[])
    django.setup()
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import FileSystemStorage

class MyStorage(HashedFilesMixin, FileSystemStorage):
    pass

def build_chain(tmp, n):
    names = []
    for i in range(n):
        name = 'a%d.css' % i
        names.append(name)
        content = ('.c%d{background:url("a%d.css")}\n' % (i, i + 1)) if i < n - 1 else '.c%d{color:red}\n' % i
        open(os.path.join(tmp, name), 'w').write(content)
    return names

tmp = tempfile.mkdtemp()
try:
    s = MyStorage(location=tmp, base_url='/static/')
    names = build_chain(tmp, 4)
    paths = {name: (s, name) for name in names}
    recs = list(s.post_process(paths, dry_run=False))
    yielded = {r[0]: r[1] for r in recs if not isinstance(r[2], Exception)}
    print("yielded name->hash:", yielded)
    # hashed_files maps a "clean" cache key (base_url + name style). Compare
    # against what stored_name/hashed_name resolves to now — the FINAL name.
    ok = True
    for name in names:
        final = s.stored_name(name)  # resolves to the stored (final) hashed name
        y = yielded.get(name)
        print("file %s: yielded=%s final=%s" % (name, y, final))
        if y != final:
            ok = False
    assert ok, "a yielded hashed name is not the final stored hashed name"
    print("OK: every yielded hashed name is the final hashed name")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

Attack 3 — `probe_3_nonadjustable.py` → holds on the patched tree (good)

```python
"""Requirement 4 crit 1 (+ Req 1 crit): a non-adjustable file (e.g. a .png,
which matches for hashing but has no ref-rewriting patterns) is yielded exactly
once and is NOT deferred/deduplicated away. Also verify an adjustable file that
needs NO rewriting after pass 1 is still yielded exactly once (Req1 crit4)."""
import os, tempfile, shutil, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, STATIC_URL='/static/', INSTALLED_APPS=[])
    django.setup()
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import FileSystemStorage

class MyStorage(HashedFilesMixin, FileSystemStorage):
    pass

tmp = tempfile.mkdtemp()
try:
    s = MyStorage(location=tmp, base_url='/static/')
    # non-adjustable file: png (not matched by the css url patterns)
    open(os.path.join(tmp, 'img.png'), 'wb').write(b'\x89PNG\r\n\x1a\nHELLO')
    # adjustable css that references NOTHING -> no rewriting needed
    open(os.path.join(tmp, 'plain.css'), 'w').write('.x{color:blue}\n')
    names = ['img.png', 'plain.css']
    paths = {name: (s, name) for name in names}
    recs = list(s.post_process(paths, dry_run=False))
    print("records:", recs)
    origs = [r[0] for r in recs if not isinstance(r[2], Exception)]
    print("origs:", origs)
    assert origs.count('img.png') == 1, "png not yielded exactly once: %r" % origs
    assert origs.count('plain.css') == 1, "plain.css not yielded exactly once: %r" % origs
    print("OK: non-adjustable png and no-rewrite css each yielded exactly once")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

Attack 4 — `probe_4_dry_run.py` → holds on the patched tree (good)

```python
"""Requirement 5 crit 3: dry_run performs no post-processing and yields nothing."""
import os, tempfile, shutil, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, STATIC_URL='/static/', INSTALLED_APPS=[])
    django.setup()
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import FileSystemStorage

class MyStorage(HashedFilesMixin, FileSystemStorage):
    pass

tmp = tempfile.mkdtemp()
try:
    s = MyStorage(location=tmp, base_url='/static/')
    open(os.path.join(tmp, 'a0.css'), 'w').write('.c{background:url("a1.css")}\n')
    open(os.path.join(tmp, 'a1.css'), 'w').write('.d{color:red}\n')
    names = ['a0.css', 'a1.css']
    paths = {name: (s, name) for name in names}
    recs = list(s.post_process(paths, dry_run=True))
    print("dry_run records:", recs)
    assert recs == [], "dry_run yielded records: %r" % recs
    print("OK: dry_run yields nothing")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

Attack 5 — `probe_5_max_passes.py` → holds on the patched tree (good)

```python
"""Requirement 4 crit 3: when substitutions are still occurring after the final
allowed pass, post_process still yields the 'max passes exceeded' error record.
We force this by setting max_post_process_passes small relative to a long chain.
Also verifies (Req 4 crit 2 shape) that exception records are yielded, not
deduplicated. Exits 0 iff an 'All'/RuntimeError max-passes record is present AND
non-error original names remain de-duplicated."""
import os, tempfile, shutil, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, STATIC_URL='/static/', INSTALLED_APPS=[])
    django.setup()
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import FileSystemStorage

class MyStorage(HashedFilesMixin, FileSystemStorage):
    max_post_process_passes = 1  # too few to converge a long chain

def build_chain(tmp, n):
    names = []
    for i in range(n):
        name = 'a%d.css' % i
        names.append(name)
        content = ('.c%d{background:url("a%d.css")}\n' % (i, i + 1)) if i < n - 1 else '.c%d{color:red}\n' % i
        open(os.path.join(tmp, name), 'w').write(content)
    return names

tmp = tempfile.mkdtemp()
try:
    s = MyStorage(location=tmp, base_url='/static/')
    names = build_chain(tmp, 6)
    paths = {name: (s, name) for name in names}
    recs = list(s.post_process(paths, dry_run=False))
    print("records:", recs)
    errs = [r for r in recs if isinstance(r[2], Exception)]
    print("error records:", errs)
    has_max = any(isinstance(r[2], RuntimeError) and 'Max post-process passes' in str(r[2]) for r in recs)
    assert has_max, "no max-passes-exceeded record yielded"
    # non-error names still deduplicated
    origs = [r[0] for r in recs if not isinstance(r[2], Exception)]
    dups = [x for x in set(origs) if origs.count(x) > 1]
    assert not dups, "duplicate non-error names: %r" % dups
    print("OK: max-passes record yielded and non-error names deduplicated")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

Attack 6 — `probe_6_rewrite_correct.py` → holds on the patched tree (good)

```python
"""Requirement 5 crit 1&2 + Requirement 3 crit 2: multi-pass reference
rewriting still works and resolves to FINAL hashed names. After post_process,
the stored hashed file for each referrer must contain the FINAL hashed name of
the file it references (not the original name, not an intermediate). Also
verifies name<->hash association integrity via stored_name lookups.
Exits 0 iff every referrer's final content points at the referee's final hash."""
import os, re, tempfile, shutil, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, STATIC_URL='/static/', INSTALLED_APPS=[])
    django.setup()
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import FileSystemStorage

class MyStorage(HashedFilesMixin, FileSystemStorage):
    pass

def build_chain(tmp, n):
    names = []
    for i in range(n):
        name = 'a%d.css' % i
        names.append(name)
        content = ('.c%d{background:url("a%d.css")}\n' % (i, i + 1)) if i < n - 1 else '.c%d{color:red}\n' % i
        open(os.path.join(tmp, name), 'w').write(content)
    return names

tmp = tempfile.mkdtemp()
try:
    s = MyStorage(location=tmp, base_url='/static/')
    names = build_chain(tmp, 4)
    paths = {name: (s, name) for name in names}
    recs = list(s.post_process(paths, dry_run=False))
    ok = True
    for i in range(len(names) - 1):
        referrer = names[i]
        referee = names[i + 1]
        final_referrer = s.stored_name(referrer)      # final hashed filename
        final_referee = os.path.basename(s.stored_name(referee))
        content = open(os.path.join(tmp, final_referrer)).read()
        print("referrer %s -> file %s content=%r ; expect ref to %s"
              % (referrer, final_referrer, content, final_referee))
        if final_referee not in content:
            ok = False
        # must NOT still contain the original unhashed referee name as a url
        if re.search(r'url\(["\']?%s["\']?\)' % re.escape(referee), content):
            print("  !! still references original unhashed name", referee)
            ok = False
    assert ok, "reference rewriting did not resolve to final hashed names"
    print("OK: nested references rewritten to final hashed names")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_no_dup.py`

```python
"""Requirement 1 (crit 1,2,3) + positive control: each original name yielded
at most once across a multi-pass rewrite. Also the core fixed behavior.
Exits 0 iff no original name (excluding the 'All' error record) is duplicated."""
import os, tempfile, shutil, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, STATIC_URL='/static/', INSTALLED_APPS=[])
    django.setup()
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import FileSystemStorage

class MyStorage(HashedFilesMixin, FileSystemStorage):
    pass

def build_chain(tmp, n):
    names = []
    for i in range(n):
        name = 'a%d.css' % i
        names.append(name)
        content = ('.c%d{background:url("a%d.css")}\n' % (i, i + 1)) if i < n - 1 else '.c%d{color:red}\n' % i
        open(os.path.join(tmp, name), 'w').write(content)
    return names

tmp = tempfile.mkdtemp()
try:
    s = MyStorage(location=tmp, base_url='/static/')
    names = build_chain(tmp, 4)
    paths = {name: (s, name) for name in names}
    recs = list(s.post_process(paths, dry_run=False))
    origs = [r[0] for r in recs if not (isinstance(r[2], Exception))]
    print("records:", recs)
    print("original names yielded:", origs)
    dups = [x for x in set(origs) if origs.count(x) > 1]
    print("duplicates:", dups)
    assert not dups, "duplicate original names yielded: %r" % dups
    # each of our 4 files must appear (they are all adjusted across passes)
    assert set(origs) >= set(names), "missing some files: %r" % (set(names) - set(origs))
    print("OK: each original name yielded exactly once")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14053: HashedFilesMixin.post_process must report each post-processed original file exactly once, carrying its FINAL hashed name.

Probe suite (all standalone python, run in the instance image; each builds a chain of CSS files a0->a1->a2->a3 via url() refs that force multi-pass rewriting, using HashedFilesMixin+FileSystemStorage):
- probe_1_no_dup.py (Req1 crit1-4; POSITIVE CONTROL): no original name yielded more than once, all files present. PATCHED: HOLDS (each of a0..a3 once). BASE: VIOLATED (each name yielded 4x -> ['a0'..'a3'] duplicated). Discriminates.
- probe_2_final_hash.py (Req2 crit1-3): every yielded hashed_name equals the final stored_name. PATCHED: HOLDS. BASE: HOLDS (base happens to yield final name last too, so not discriminating vs base) but this probe is the one that REJECTS the weak candidate.
- probe_3_nonadjustable.py (Req4 crit1): non-adjustable png + no-rewrite css each yielded exactly once, not deferred/duplicated. PATCHED: HOLDS.
- probe_4_dry_run.py (Req5 crit3): dry_run yields nothing. PATCHED: HOLDS.
- probe_5_max_passes.py (Req4 crit3 + Req4 crit2): with max_post_process_passes=1 over a 6-long chain, the 'Max post-process passes exceeded.' RuntimeError record is still yielded AND non-error names stay deduplicated. PATCHED: HOLDS. BASE: VIOLATED (duplicate names). Second discriminating leg.
- probe_6_rewrite_correct.py (Req5 crit1-2, Req3 crit2): after post_process each referrer's stored final file content points at the referee's FINAL hashed name, no original unhashed url remaining. PATCHED: HOLDS.

All 6 probes HOLD on the gold-patched tree. Positive control (probe_1) and probe_5 FAIL at base (prepatch_reproduced=true).

Candidate wrong-fix: weak_keepfirst.diff — the lazy dedup a weak reading permits: deduplicate by original name keeping the FIRST record seen (instead of overwriting with the newer/final one). It applies at base_commit and satisfies Req1 (each name once — probe_1 HOLDS) and preserves rewriting (probe_6 HOLDS), but VIOLATES Req2: it yields the INTERMEDIATE hashed name from an early pass (a0=ffef8f46.., a1=a0acbfea.. differ from the final a0=dbc3f975.., a1=212f2060..). probe_2 REJECTS it (exit 1). This demonstrates the suite discriminates a plausible-but-wrong implementation, so it is NOT a too-weak spec.

Verdict SOUND: >=6 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 candidate exercised and REJECTED by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_no_dup.py`, `probe_2_final_hash.py`, `probe_3_nonadjustable.py`, `probe_4_dry_run.py`, `probe_5_max_passes.py`, `probe_6_rewrite_correct.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_no_dup.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_no_dup.py` → holds on the patched tree (good)

Attack 2 — `probe_2_final_hash.py` → holds on the patched tree (good)

Attack 3 — `probe_3_nonadjustable.py` → holds on the patched tree (good)

Attack 4 — `probe_4_dry_run.py` → holds on the patched tree (good)

Attack 5 — `probe_5_max_passes.py` → holds on the patched tree (good)

Attack 6 — `probe_6_rewrite_correct.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_no_dup.py`

```python
"""Requirement 1 (crit 1,2,3) + positive control: each original name yielded
at most once across a multi-pass rewrite. Also the core fixed behavior.
Exits 0 iff no original name (excluding the 'All' error record) is duplicated."""
import os, tempfile, shutil, django
from django.conf import settings
if not settings.configured:
    settings.configure(DEBUG=True, STATIC_URL='/static/', INSTALLED_APPS=[])
    django.setup()
from django.contrib.staticfiles.storage import HashedFilesMixin
from django.core.files.storage import FileSystemStorage

class MyStorage(HashedFilesMixin, FileSystemStorage):
    pass

def build_chain(tmp, n):
    names = []
    for i in range(n):
        name = 'a%d.css' % i
        names.append(name)
        content = ('.c%d{background:url("a%d.css")}\n' % (i, i + 1)) if i < n - 1 else '.c%d{color:red}\n' % i
        open(os.path.join(tmp, name), 'w').write(content)
    return names

tmp = tempfile.mkdtemp()
try:
    s = MyStorage(location=tmp, base_url='/static/')
    names = build_chain(tmp, 4)
    paths = {name: (s, name) for name in names}
    recs = list(s.post_process(paths, dry_run=False))
    origs = [r[0] for r in recs if not (isinstance(r[2], Exception))]
    print("records:", recs)
    print("original names yielded:", origs)
    dups = [x for x in set(origs) if origs.count(x) > 1]
    print("duplicates:", dups)
    assert not dups, "duplicate original names yielded: %r" % dups
    # each of our 4 files must appear (they are all adjusted across passes)
    assert set(origs) >= set(names), "missing some files: %r" % (set(names) - set(origs))
    print("OK: each original name yielded exactly once")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14053: HashedFilesMixin.post_process must report each post-processed original file exactly once, carrying its FINAL hashed name.

Probe suite (all standalone python, run in the instance image; each builds a chain of CSS files a0->a1->a2->a3 via url() refs that force multi-pass rewriting, using HashedFilesMixin+FileSystemStorage):
- probe_1_no_dup.py (Req1 crit1-4; POSITIVE CONTROL): no original name yielded more than once, all files present. PATCHED: HOLDS (each of a0..a3 once). BASE: VIOLATED (each name yielded 4x -> ['a0'..'a3'] duplicated). Discriminates.
- probe_2_final_hash.py (Req2 crit1-3): every yielded hashed_name equals the final stored_name. PATCHED: HOLDS. BASE: HOLDS (base happens to yield final name last too, so not discriminating vs base) but this probe is the one that REJECTS the weak candidate.
- probe_3_nonadjustable.py (Req4 crit1): non-adjustable png + no-rewrite css each yielded exactly once, not deferred/duplicated. PATCHED: HOLDS.
- probe_4_dry_run.py (Req5 crit3): dry_run yields nothing. PATCHED: HOLDS.
- probe_5_max_passes.py (Req4 crit3 + Req4 crit2): with max_post_process_passes=1 over a 6-long chain, the 'Max post-process passes exceeded.' RuntimeError record is still yielded AND non-error names stay deduplicated. PATCHED: HOLDS. BASE: VIOLATED (duplicate names). Second discriminating leg.
- probe_6_rewrite_correct.py (Req5 crit1-2, Req3 crit2): after post_process each referrer's stored final file content points at the referee's FINAL hashed name, no original unhashed url remaining. PATCHED: HOLDS.

All 6 probes HOLD on the gold-patched tree. Positive control (probe_1) and probe_5 FAIL at base (prepatch_reproduced=true).

Candidate wrong-fix: weak_keepfirst.diff — the lazy dedup a weak reading permits: deduplicate by original name keeping the FIRST record seen (instead of overwriting with the newer/final one). It applies at base_commit and satisfies Req1 (each name once — probe_1 HOLDS) and preserves rewriting (probe_6 HOLDS), but VIOLATES Req2: it yields the INTERMEDIATE hashed name from an early pass (a0=ffef8f46.., a1=a0acbfea.. differ from the final a0=dbc3f975.., a1=212f2060..). probe_2 REJECTS it (exit 1). This demonstrates the suite discriminates a plausible-but-wrong implementation, so it is NOT a too-weak spec.

Verdict SOUND: >=6 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 candidate exercised and REJECTED by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified via nl_attack probe: gold-patched HOLDS (exit 0), base VIOLATED (duplicate names). Requirements are behavioral (dedup by original name, final hash, preserve error/max-pass/dry_run) rather than pinning a single branch/helper, so the modeling boundary matches the observable change.

Counterexample / evidence:

```
N/A — probe on gold-patched tree passed all assertions (no duplicate original names, yielded hash == final manifest hash, non-adjustable file yielded once); base tree fails the no-duplicates assertion, confirming requirements pin the actual change.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document is purely behavioral. Everything it asserts is either public in the problem_statement (multi-pass processing, max_post_process_passes, adjustable files, duplicate/intermediate yields, collectstatic stats overcount, subclass duplicate work, dry_run) or a legitimate localization (naming HashedFilesMixin.post_process, _post_process, storage.py, collectstatic.py — all needed to localize the change). The hidden test only adds an assertCountEqual no-duplicates assertion inside an existing test_post_processing; the requirements translate that into 'each original name at most once' behavior rather than transmitting the test. No test names/paths/ids (e.g. 'post_processing behaves correctly.', TestCollectionManifestStorage), no quoted test/gold code, and the gold-invented identifier (processed_adjustable_paths) is never surfaced. No case enumeration mirrors the parametrization. Legitimate spec.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
