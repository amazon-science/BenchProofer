# P2 adversarial audit — django__django-16333

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_commit_persists.py`, `probe_2_exact_set.py`, `probe_3_deferred.py`, `probe_4_deferred_later.py`, `probe_5_password.py`, `probe_6_mismatch.py`, `probe_7_no_m2m.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_commit_persists.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_commit_persists.py` → holds on the patched tree (good)

```python
import subprocess, sys, os
# Req 1.1 & 1.2: committed save persists the user AND its m2m selections exactly.
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from auth_tests.models.with_many_to_many import CustomUserWithM2M, Organization
class Probe(TestCase):
    def test(self):
        class F(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)
        org = Organization.objects.create(name="org1")
        data = {"username":"a@b.com","password1":"pw12345x","password2":"pw12345x","orgs":[str(org.pk)]}
        f = F(data)
        assert f.is_valid(), f.errors
        user = f.save(commit=True)
        # reload from DB to prove it was persisted, not just in-memory
        reloaded = CustomUserWithM2M._default_manager.get(pk=user.pk)
        self.assertSequenceEqual(reloaded.orgs.all(), [org])
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_exact_set.py` → holds on the patched tree (good)

```python
import subprocess, sys, os
# Req 1.2: querying yields EXACTLY the submitted set - none omitted, none added.
# Create 3 orgs, submit only 2; ensure exactly those 2 stored (the third must NOT appear).
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from auth_tests.models.with_many_to_many import CustomUserWithM2M, Organization
class Probe(TestCase):
    def test(self):
        class F(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)
        o1=Organization.objects.create(name="o1")
        o2=Organization.objects.create(name="o2")
        o3=Organization.objects.create(name="o3")
        data={"username":"a@b.com","password1":"pw12345x","password2":"pw12345x",
              "orgs":[str(o1.pk),str(o3.pk)]}
        f=F(data)
        assert f.is_valid(), f.errors
        user=f.save(commit=True)
        got=set(CustomUserWithM2M._default_manager.get(pk=user.pk).orgs.values_list("pk",flat=True))
        assert got=={o1.pk,o3.pk}, ("got",got,"expected",{o1.pk,o3.pk})
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_deferred.py` → holds on the patched tree (good)

```python
import subprocess, sys, os
# Req 3.1 & 3.3: commit=False writes NOTHING (no user row, no m2m) but returns the built user.
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from auth_tests.models.with_many_to_many import CustomUserWithM2M, Organization
class Probe(TestCase):
    def test(self):
        class F(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)
        org=Organization.objects.create(name="org1")
        data={"username":"a@b.com","password1":"pw12345x","password2":"pw12345x","orgs":[str(org.pk)]}
        f=F(data)
        assert f.is_valid(), f.errors
        before=CustomUserWithM2M._default_manager.count()
        user=f.save(commit=False)
        assert user is not None, "must return the built instance"
        # no user row written
        assert CustomUserWithM2M._default_manager.count()==before, "deferred save must not write user"
        assert user.pk is None, ("deferred user should be unsaved, pk=",user.pk)
        # deferred m2m mechanism available
        assert hasattr(f,"save_m2m"), "deferred save must expose save_m2m"
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_deferred_later.py` → holds on the patched tree (good)

```python
import subprocess, sys, os
# Req 3.2: after a deferred save, caller can persist m2m later via the deferred mechanism.
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from auth_tests.models.with_many_to_many import CustomUserWithM2M, Organization
class Probe(TestCase):
    def test(self):
        class F(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)
        org=Organization.objects.create(name="org1")
        data={"username":"a@b.com","password1":"pw12345x","password2":"pw12345x","orgs":[str(org.pk)]}
        f=F(data)
        assert f.is_valid(), f.errors
        user=f.save(commit=False)
        assert user.pk is None
        # caller persists later
        user.save()
        f.save_m2m()
        self.assertSequenceEqual(CustomUserWithM2M._default_manager.get(pk=user.pk).orgs.all(), [org])
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_password.py` → holds on the patched tree (good)

```python
import subprocess, sys, os
# Req 2.1 & 2.2: returned user has password set from password1 (both commit True and False), returns instance.
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from auth_tests.models.with_many_to_many import CustomUserWithM2M, Organization
class Probe(TestCase):
    def test(self):
        class F(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)
        org=Organization.objects.create(name="org1")
        for commit in (True, False):
            data={"username":"u%s@b.com"%commit,"password1":"S3cretPW!","password2":"S3cretPW!","orgs":[str(org.pk)]}
            f=F(data)
            assert f.is_valid(), f.errors
            user=f.save(commit=commit)
            assert user is not None, "must return instance"
            assert user.check_password("S3cretPW!"), ("password not derived, commit=",commit)
            assert not user.check_password("wrong"), "wrong password accepted"
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_mismatch.py` → holds on the patched tree (good)

```python
import subprocess, sys, os
# Req 2.3: password-confirmation/mismatch checks unchanged: mismatched passwords => invalid.
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from auth_tests.models.with_many_to_many import CustomUserWithM2M, Organization
class Probe(TestCase):
    def test(self):
        class F(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)
        org=Organization.objects.create(name="org1")
        data={"username":"a@b.com","password1":"S3cretPW!","password2":"different!","orgs":[str(org.pk)]}
        f=F(data)
        assert not f.is_valid(), "mismatched passwords must be invalid"
        assert "password2" in f.errors, ("expected password2 error, got",f.errors)
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7_no_m2m.py` → holds on the patched tree (good)

```python
import subprocess, sys, os
# Req 4.1: committed save on a plain model with NO m2m fields persists the user, no error.
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
class Probe(TestCase):
    def test(self):
        # default UserCreationForm uses auth.User which has no m2m form fields exposed
        data={"username":"plainuser","password1":"S3cretPW!","password2":"S3cretPW!"}
        f=UserCreationForm(data)
        assert f.is_valid(), f.errors
        user=f.save(commit=True)
        assert user.pk is not None, "user must be persisted"
        assert User.objects.filter(pk=user.pk).exists()
        assert user.check_password("S3cretPW!")
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_commit_persists.py`

```python
import subprocess, sys, os
# Req 1.1 & 1.2: committed save persists the user AND its m2m selections exactly.
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from auth_tests.models.with_many_to_many import CustomUserWithM2M, Organization
class Probe(TestCase):
    def test(self):
        class F(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)
        org = Organization.objects.create(name="org1")
        data = {"username":"a@b.com","password1":"pw12345x","password2":"pw12345x","orgs":[str(org.pk)]}
        f = F(data)
        assert f.is_valid(), f.errors
        user = f.save(commit=True)
        # reload from DB to prove it was persisted, not just in-memory
        reloaded = CustomUserWithM2M._default_manager.get(pk=user.pk)
        self.assertSequenceEqual(reloaded.orgs.all(), [org])
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: django__django-16333. Gold fix adds `if hasattr(self,'save_m2m'): self.save_m2m()` after `user.save()` inside the `if commit:` block of UserCreationForm.save(). Probes run the repo's own tests/runtests.py against auth_tests with an injected temp test module (the CustomUserWithM2M model uses a custom manager `custom_objects`, so probes query via `_default_manager`).

Probe/criterion/result (patched | base):
- probe_1_commit_persists (Req1.1,1.2; POSITIVE CONTROL): committed save persists user AND reloaded user.orgs == submitted set. HOLDS patched | VIOLATED base (orgs empty). Discriminates.
- probe_2_exact_set (Req1.2): 3 orgs exist, submit 2; stored set is EXACTLY those 2 (none omitted/added). HOLDS | VIOLATED base.
- probe_3_deferred (Req3.1,3.3): commit=False writes no user row (pk None) and exposes save_m2m. HOLDS both trees (regression).
- probe_4_deferred_later (Req3.2): after deferred save, user.save()+form.save_m2m() persists m2m. HOLDS both.
- probe_5_password (Req2.1,2.2): returned user has password derived from password1 for commit True and False; returns instance. HOLDS both.
- probe_6_mismatch (Req2.3): mismatched password2 => form invalid with password2 error. HOLDS both.
- probe_7_no_m2m (Req4.1): plain auth.User form commits with no m2m and no error. HOLDS both.

Wrong-fix candidates (both REJECTED by suite => suite discriminates):
- weak_always.diff: calls save_m2m() unconditionally (outside `if commit:`). probe_1 HOLDS but probe_3 (deferred) VIOLATED — save_m2m runs on commit=False, raising in related_descriptors (writes on unsaved instance). Rejected => not a too-weak escape.
- weak_order.diff: calls save_m2m() BEFORE user.save() inside `if commit:` (violates Req1.3 ordering). probe_1 VIOLATED (related-descriptor error / unsaved user). Rejected.

All 7 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced). Both plausible wrong fixes are rejected. No too-weak alternative found. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_commit_persists.py`, `probe_2_exact_set.py`, `probe_3_deferred.py`, `probe_4_deferred_later.py`, `probe_5_password.py`, `probe_6_mismatch.py`, `probe_7_no_m2m.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_commit_persists.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_commit_persists.py` → holds on the patched tree (good)

Attack 2 — `probe_2_exact_set.py` → holds on the patched tree (good)

Attack 3 — `probe_3_deferred.py` → holds on the patched tree (good)

Attack 4 — `probe_4_deferred_later.py` → holds on the patched tree (good)

Attack 5 — `probe_5_password.py` → holds on the patched tree (good)

Attack 6 — `probe_6_mismatch.py` → holds on the patched tree (good)

Attack 7 — `probe_7_no_m2m.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_commit_persists.py`

```python
import subprocess, sys, os
# Req 1.1 & 1.2: committed save persists the user AND its m2m selections exactly.
testcode = '''
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm
from auth_tests.models.with_many_to_many import CustomUserWithM2M, Organization
class Probe(TestCase):
    def test(self):
        class F(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)
        org = Organization.objects.create(name="org1")
        data = {"username":"a@b.com","password1":"pw12345x","password2":"pw12345x","orgs":[str(org.pk)]}
        f = F(data)
        assert f.is_valid(), f.errors
        user = f.save(commit=True)
        # reload from DB to prove it was persisted, not just in-memory
        reloaded = CustomUserWithM2M._default_manager.get(pk=user.pk)
        self.assertSequenceEqual(reloaded.orgs.all(), [org])
'''
p="tests/auth_tests/test_probe_ans.py"
open(p,"w").write(testcode)
try:
    r=subprocess.run([sys.executable,"tests/runtests.py","auth_tests.test_probe_ans","--verbosity=1"],capture_output=True,text=True)
finally:
    os.remove(p)
sys.stderr.write(r.stdout[-2500:]+r.stderr[-2500:])
ok=r.returncode==0
print("RESULT_OK" if ok else "RESULT_FAIL","rc=",r.returncode)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance: django__django-16333. Gold fix adds `if hasattr(self,'save_m2m'): self.save_m2m()` after `user.save()` inside the `if commit:` block of UserCreationForm.save(). Probes run the repo's own tests/runtests.py against auth_tests with an injected temp test module (the CustomUserWithM2M model uses a custom manager `custom_objects`, so probes query via `_default_manager`).

Probe/criterion/result (patched | base):
- probe_1_commit_persists (Req1.1,1.2; POSITIVE CONTROL): committed save persists user AND reloaded user.orgs == submitted set. HOLDS patched | VIOLATED base (orgs empty). Discriminates.
- probe_2_exact_set (Req1.2): 3 orgs exist, submit 2; stored set is EXACTLY those 2 (none omitted/added). HOLDS | VIOLATED base.
- probe_3_deferred (Req3.1,3.3): commit=False writes no user row (pk None) and exposes save_m2m. HOLDS both trees (regression).
- probe_4_deferred_later (Req3.2): after deferred save, user.save()+form.save_m2m() persists m2m. HOLDS both.
- probe_5_password (Req2.1,2.2): returned user has password derived from password1 for commit True and False; returns instance. HOLDS both.
- probe_6_mismatch (Req2.3): mismatched password2 => form invalid with password2 error. HOLDS both.
- probe_7_no_m2m (Req4.1): plain auth.User form commits with no m2m and no error. HOLDS both.

Wrong-fix candidates (both REJECTED by suite => suite discriminates):
- weak_always.diff: calls save_m2m() unconditionally (outside `if commit:`). probe_1 HOLDS but probe_3 (deferred) VIOLATED — save_m2m runs on commit=False, raising in related_descriptors (writes on unsaved instance). Rejected => not a too-weak escape.
- weak_order.diff: calls save_m2m() BEFORE user.save() inside `if commit:` (violates Req1.3 ordering). probe_1 VIOLATED (related-descriptor error / unsaved user). Rejected.

All 7 probes hold on the gold-patched tree; positive control fails at base and holds patched (prepatch reproduced). Both plausible wrong fixes are rejected. No too-weak alternative found. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on the gold-patched /testbed tree returned exactly: `def save(self, commit=True): user = super().save(commit=False); user.set_password(self.cleaned_data['password1']); if commit: user.save(); if hasattr(self, 'save_m2m'): self.save_m2m(); return user`. Base commit lacks save_m2m (probe VIOLATED at base). Ordering (user.save() before save_m2m()) confirmed. The hasattr guard is precisely what makes Req4's 'no error absent m2m' faithful — save_m2m only exists after a commit=False super().save(), so the guard is the real mechanism, correctly modeled. Requirements pin the changed observable behavior at the right boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to UserCreationForm.save() in django/contrib/auth/forms.py and describes the fix behaviorally (persist m2m selections on committed save; call the deferred save_m2m mechanism; preserve password derivation and non-committed behavior). The gold edit is `if hasattr(self, 'save_m2m'): self.save_m2m()`; the identifier `save_m2m` is NOT fix-invented and is explicitly present in the PUBLIC problem_statement ('omits to call self.save_m2m()'). No hidden-test artifacts leak: the doc never names the test function (test_custom_form_saves_many_to_many_field), the test file path (tests/auth_tests/test_forms.py), or the fixture identifiers introduced by the test (CustomUserWithM2M, Organization, `orgs`, ModelMultipleChoiceField-by-name). Requirement 1.2's 'exactly the set ... none omitted, none added' is a legitimate behavioral translation of the assertSequenceEqual check, not a transcription of test code. Requirement 4 (models without m2m fields) is a general safety generalization, not a mirror of any parametrized case (the FAIL_TO_PASS set is a single test). Everything is derivable from problem_statement + public Django ModelForm API.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
