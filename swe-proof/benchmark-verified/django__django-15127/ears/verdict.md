# P2 adversarial audit — django__django-15127

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control (R1.1, R1.5): under a runtime MESSAGE_TAGS override,
Message.level_tag reflects the override rather than a stale cached value.
HOLDS on patched tree, must FAIL at base."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'django.contrib.messages',
    ],
    MESSAGE_TAGS={},
    DATABASES={},
)
django.setup()

from django.contrib.messages.storage.base import Message
from django.test.utils import override_settings

with override_settings(MESSAGE_TAGS={40: 'mycustomerror'}):
    m = Message(40, 'hello')
    tag = m.level_tag
    print('level_tag under override:', repr(tag))
    assert tag == 'mycustomerror', f"expected 'mycustomerror', got {tag!r}"
print('OK')
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R1.1/R1.2: after MESSAGE_TAGS change, cached LEVEL_TAGS equals merge of
DEFAULT_TAGS with the override (override wins on shared levels)."""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.messages'],
    MESSAGE_TAGS={}, DATABASES={},
)
django.setup()

from django.contrib.messages.storage import base
from django.contrib.messages import constants
from django.test.utils import override_settings

override = {constants.INFO: 'INFO_OVERRIDE'}
with override_settings(MESSAGE_TAGS=override):
    expected = {**constants.DEFAULT_TAGS, **override}
    print('LEVEL_TAGS:', base.LEVEL_TAGS)
    print('expected  :', expected)
    assert base.LEVEL_TAGS == expected, "cached mapping != merged expected"
    assert base.LEVEL_TAGS[constants.INFO] == 'INFO_OVERRIDE', "override did not win"
    assert base.LEVEL_TAGS[constants.DEBUG] == 'debug', "unrelated default lost"
print('OK')
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R1.3: recomputed mapping includes custom numeric levels not among defaults,
and R1.4: an empty-string override maps to '' (no fallback to default tag)."""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.messages'],
    MESSAGE_TAGS={}, DATABASES={},
)
django.setup()

from django.contrib.messages.storage import base
from django.contrib.messages import constants
from django.test.utils import override_settings

override = {12: 'custom_level', constants.ERROR: ''}
with override_settings(MESSAGE_TAGS=override):
    lt = base.LEVEL_TAGS
    print('LEVEL_TAGS:', lt)
    assert lt.get(12) == 'custom_level', "custom numeric level missing"
    assert lt.get(constants.ERROR) == '', f"empty override not honored: {lt.get(constants.ERROR)!r}"
    # also via level_tag property
    from django.contrib.messages.storage.base import Message
    assert Message(constants.ERROR, 'x').level_tag == '', "level_tag not empty for empty override"
print('OK')
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R2.1/R2.2: a setting-changed for a setting OTHER than MESSAGE_TAGS leaves
the cached mapping untouched; and after the override exits, mapping restores.
Also checks that unrelated change does not clobber a prior MESSAGE_TAGS value."""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.messages'],
    MESSAGE_TAGS={}, DATABASES={}, USE_TZ=False,
)
django.setup()

from django.contrib.messages.storage import base
from django.contrib.messages import constants
from django.test.utils import override_settings

baseline = dict(base.LEVEL_TAGS)
print('baseline:', baseline)

# Change an unrelated setting; mapping must not change.
with override_settings(USE_TZ=True):
    print('after unrelated change:', base.LEVEL_TAGS)
    assert base.LEVEL_TAGS == baseline, "unrelated setting change disturbed mapping"

# Nested: set MESSAGE_TAGS, then change unrelated inside -> MESSAGE_TAGS value kept.
with override_settings(MESSAGE_TAGS={constants.INFO: 'ii'}):
    snap = dict(base.LEVEL_TAGS)
    assert snap[constants.INFO] == 'ii'
    with override_settings(USE_TZ=True):
        assert base.LEVEL_TAGS == snap, "unrelated change wiped MESSAGE_TAGS override"

# After all overrides exit, restored to baseline.
assert base.LEVEL_TAGS == baseline, "mapping not restored to baseline"
print('OK')
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3.1/R3.2: MessagesConfig.ready() registers a handler on the
setting_changed signal (no project wiring). Verify a receiver is connected and
that firing the signal with MESSAGE_TAGS recomputes LEVEL_TAGS."""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.messages'],
    MESSAGE_TAGS={}, DATABASES={},
)
django.setup()

from django.test.signals import setting_changed
from django.contrib.messages.storage import base
from django.contrib.messages import constants

# There must be at least one receiver connected to setting_changed
# originating from the messages app.
receivers = setting_changed._live_receivers(sender=None)
# _live_receivers may return (has_sync, receivers) tuple across versions
if isinstance(receivers, tuple):
    recv_list = receivers[-1]
else:
    recv_list = receivers
names = [getattr(r, '__name__', repr(r)) for r in recv_list]
print('setting_changed receivers:', names)
assert any('level_tag' in n.lower() or 'message' in n.lower() for n in names), \
    "no messages handler connected to setting_changed"

# Fire the signal directly (simulating Django's runtime change dispatch).
settings.MESSAGE_TAGS = {constants.WARNING: 'warned'}
setting_changed.send(sender=settings.__class__, setting='MESSAGE_TAGS',
                     value={constants.WARNING: 'warned'}, enter=True)
print('LEVEL_TAGS after signal:', base.LEVEL_TAGS)
assert base.LEVEL_TAGS.get(constants.WARNING) == 'warned', "handler did not recompute"
print('OK')
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R4.1/R4.3/R4.4: level_tag returns '' for a level absent from mapping;
Message equality depends only on level+message (extra_tags irrelevant); and
differing level or message -> not equal. Regression 'SHALL keep' criteria."""
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.messages'],
    MESSAGE_TAGS={}, DATABASES={},
)
django.setup()

from django.contrib.messages.storage.base import Message

# Absent level -> ''
m = Message(999, 'x')
print('level_tag for absent level 999:', repr(m.level_tag))
assert m.level_tag == '', "absent level should map to ''"

# Equality: same level+message, different extra_tags -> equal
a = Message(20, 'hello', extra_tags='foo')
b = Message(20, 'hello', extra_tags='bar')
assert a == b, "same level+message should be equal regardless of extra_tags"

# Differing level -> not equal
assert Message(20, 'hello') != Message(30, 'hello'), "differing level should be unequal"
# Differing message -> not equal
assert Message(20, 'hello') != Message(20, 'world'), "differing message should be unequal"
print('OK')
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""R1.6: if the override supplies tags for EVERY level with a built-in default,
the recomputed mapping equals the override exactly. R4.2: initial import-time
mapping already reflects configured overrides (checked at setup with a full
MESSAGE_TAGS in settings before any runtime change)."""
import django
from django.conf import settings
from django.contrib.messages import constants

full_override = {lvl: f"o{lvl}" for lvl in constants.DEFAULT_TAGS}
settings.configure(
    INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','django.contrib.messages'],
    MESSAGE_TAGS=dict(full_override), DATABASES={},
)
django.setup()

from django.contrib.messages.storage import base

# R4.2: import-time cached mapping reflects configured override.
print('import-time LEVEL_TAGS:', base.LEVEL_TAGS)
assert base.LEVEL_TAGS == full_override, "import-time mapping != configured override"

# R1.6: runtime override covering all default levels -> equals override exactly.
from django.test.utils import override_settings
full2 = {lvl: f"z{lvl}" for lvl in constants.DEFAULT_TAGS}
with override_settings(MESSAGE_TAGS=full2):
    print('runtime LEVEL_TAGS:', base.LEVEL_TAGS)
    assert base.LEVEL_TAGS == full2, "full override did not equal exactly"
print('OK')
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (R1.1, R1.5): under a runtime MESSAGE_TAGS override,
Message.level_tag reflects the override rather than a stale cached value.
HOLDS on patched tree, must FAIL at base."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'django.contrib.messages',
    ],
    MESSAGE_TAGS={},
    DATABASES={},
)
django.setup()

from django.contrib.messages.storage.base import Message
from django.test.utils import override_settings

with override_settings(MESSAGE_TAGS={40: 'mycustomerror'}):
    m = Message(40, 'hello')
    tag = m.level_tag
    print('level_tag under override:', repr(tag))
    assert tag == 'mycustomerror', f"expected 'mycustomerror', got {tag!r}"
print('OK')
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree. Positive control (probe_1, R1.1/R1.5): Message.level_tag reflects a runtime MESSAGE_TAGS override -> HOLDS patched, FAILS at base (got 'error' instead of 'mycustomerror'), so it discriminates. Coverage: probe_2 R1.1/R1.2 merge-with-override; probe_3 R1.3 custom numeric level + R1.4 empty-string override maps to ''; probe_4 R2.1/R2.2 unrelated setting change leaves mapping untouched + nested restore; probe_5 R3.1/R3.2 ready() connects update_level_tags to setting_changed and firing the signal recomputes; probe_6 R4.1/R4.3/R4.4 absent-level '' + equality by level+message only; probe_7 R1.6 full override equals exactly + R4.2 import-time mapping reflects config. Candidate patch weak_nomerge (recomputes but assigns raw MESSAGE_TAGS without merging DEFAULT_TAGS) is REJECTED: probe_2 fails (defaults for non-overridden levels lost) and probe_4 fails (baseline restore breaks), demonstrating the suite discriminates a wrong implementation. No requirements-conforming patch found that would fail the hidden test. Requirements are faithful to the gold patch and discriminating.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control (R1.1, R1.5): under a runtime MESSAGE_TAGS override,
Message.level_tag reflects the override rather than a stale cached value.
HOLDS on patched tree, must FAIL at base."""
import django
from django.conf import settings

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'django.contrib.messages',
    ],
    MESSAGE_TAGS={},
    DATABASES={},
)
django.setup()

from django.contrib.messages.storage.base import Message
from django.test.utils import override_settings

with override_settings(MESSAGE_TAGS={40: 'mycustomerror'}):
    m = Message(40, 'hello')
    tag = m.level_tag
    print('level_tag under override:', repr(tag))
    assert tag == 'mycustomerror', f"expected 'mycustomerror', got {tag!r}"
print('OK')
```

Prepatch bug re-encoded as an attack: `True`.

7 probes, all HOLD on gold-patched tree. Positive control (probe_1, R1.1/R1.5): Message.level_tag reflects a runtime MESSAGE_TAGS override -> HOLDS patched, FAILS at base (got 'error' instead of 'mycustomerror'), so it discriminates. Coverage: probe_2 R1.1/R1.2 merge-with-override; probe_3 R1.3 custom numeric level + R1.4 empty-string override maps to ''; probe_4 R2.1/R2.2 unrelated setting change leaves mapping untouched + nested restore; probe_5 R3.1/R3.2 ready() connects update_level_tags to setting_changed and firing the signal recomputes; probe_6 R4.1/R4.3/R4.4 absent-level '' + equality by level+message only; probe_7 R1.6 full override equals exactly + R4.2 import-time mapping reflects config. Candidate patch weak_nomerge (recomputes but assigns raw MESSAGE_TAGS without merging DEFAULT_TAGS) is REJECTED: probe_2 fails (defaults for non-overridden levels lost) and probe_4 fails (baseline restore breaks), demonstrating the suite discriminates a wrong implementation. No requirements-conforming patch found that would fail the hidden test. Requirements are faithful to the gold patch and discriminating.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is minimal: apps.py gains update_level_tags(setting,**kwargs) filtering on setting=='MESSAGE_TAGS' and rebinding base.LEVEL_TAGS=get_level_tags(), plus MessagesConfig.ready() connecting it to django.test.signals.setting_changed. The modeling boundary is correct: requirements pin the observable changed behavior (cached mapping refresh on MESSAGE_TAGS change, no-op otherwise, level_tag reflecting it) rather than a narrow slice. R4 preserves pre-existing __eq__/level_tag behavior unchanged by the patch. All 3 override-signal cases (custom level, empty-string tag, full override) and the unrelated-setting no-op confirmed by direct probe on the instance image; the FAIL_TO_PASS test test_override_settings_level_tags matches R1/R5.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior and localize the change legitimately. All named identifiers (get_level_tags, LEVEL_TAGS, Message.level_tag, MessagesConfig, DEFAULT_TAGS, MESSAGE_TAGS) are public API — LEVEL_TAGS and level_tag are already in the problem_statement; MessagesConfig/get_level_tags are legitimate localization. The gold's fix-invented identifier `update_level_tags` is NOT present; Req 3 refers generically to a 'setting-changed signal'/'handler'. No test names, file paths, class names, parametrization ids, or quoted test/gold code appear. Edge-case criteria (Req 1.3 custom numeric level, 1.4 empty-string override, 1.6 override covering all defaults equals override exactly) echo the test fixture's shape but are genuine behavioral translations of get_level_tags' merge semantics rather than a reproduction of the specific {INFO:'info',...,12:'custom'} dict. Req 4.3/4.4 restate Message.__eq__ semantics (the PASS_TO_PASS test_eq) as behavior, not as test code. No semantic gold-reconstruction beyond the public problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
