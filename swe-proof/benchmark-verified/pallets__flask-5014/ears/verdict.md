# P2 adversarial audit — pallets__flask-5014

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req1.1/1.2: empty name -> ValueError at construction (POSITIVE CONTROL)
import sys
from flask import Blueprint
try:
    bp = Blueprint("", __name__)
    print("NO ERROR: instance returned for empty name:", bp)
    sys.exit(1)
except ValueError as e:
    print("OK: ValueError raised for empty name:", e)
    sys.exit(0)
except Exception as e:
    print("WRONG EXC TYPE:", type(e).__name__, e)
    sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.3: emptiness check is independent of the import_name value.
# Empty name must be rejected with ValueError for varied (importable) import_names.
import sys
from flask import Blueprint
fails = []
for import_name in ["flask", "os", "__main__"]:
    try:
        Blueprint("", import_name)
        fails.append(("no-error", import_name))
    except ValueError:
        pass
    except Exception as e:
        fails.append((type(e).__name__, import_name))
if fails:
    print("FAIL: empty name not rejected with ValueError for:", fails)
    sys.exit(1)
print("OK: empty name rejected regardless of import_name")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2.1/2.2: dotted non-empty name still raises ValueError.
import sys
from flask import Blueprint
try:
    Blueprint("a.b", __name__)
    print("FAIL: dotted name accepted")
    sys.exit(1)
except ValueError as e:
    print("OK: dotted name rejected:", e)
    sys.exit(0)
except Exception as e:
    print("WRONG EXC:", type(e).__name__, e)
    sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.1/3.2: valid non-empty non-dotted name succeeds and name attr preserved.
import sys
from flask import Blueprint
try:
    bp = Blueprint("admin", __name__)
except Exception as e:
    print("FAIL: valid name raised:", type(e).__name__, e)
    sys.exit(1)
if bp.name != "admin":
    print("FAIL: name attr mismatch:", bp.name)
    sys.exit(1)
print("OK: valid blueprint constructed, name =", bp.name)
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req3.3/3.4: valid blueprint keeps full capabilities: construction options,
# registration on app, routing, endpoint building, url_prefix.
import sys
from flask import Flask, Blueprint

bp = Blueprint("shop", __name__, url_prefix="/shop", subdomain="s",
               url_defaults={"k": "v"}, cli_group="shopcli")

@bp.route("/item")
def item():
    return "item"

# whitespace-only name is truthy -> must still be accepted (falsy check only)
ws = Blueprint(" ", __name__)
if ws.name != " ":
    print("FAIL: whitespace name not preserved:", repr(ws.name))
    sys.exit(1)

app = Flask(__name__)
app.register_blueprint(bp)

with app.test_request_context():
    from flask import url_for
    url = url_for("shop.item")
if not url.endswith("/shop/item"):
    print("FAIL: url building wrong:", url)
    sys.exit(1)

# construction options preserved
if bp.url_prefix != "/shop" or bp.subdomain != "s" or bp.cli_group != "shopcli":
    print("FAIL: options not preserved", bp.url_prefix, bp.subdomain, bp.cli_group)
    sys.exit(1)

print("OK: valid blueprint fully functional, url =", url)
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.1/1.2: empty name -> ValueError at construction (POSITIVE CONTROL)
import sys
from flask import Blueprint
try:
    bp = Blueprint("", __name__)
    print("NO ERROR: instance returned for empty name:", bp)
    sys.exit(1)
except ValueError as e:
    print("OK: ValueError raised for empty name:", e)
    sys.exit(0)
except Exception as e:
    print("WRONG EXC TYPE:", type(e).__name__, e)
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: validate Blueprint(name) at construction so an empty name raises ValueError, preserving dotted-name rejection and all valid-name behavior. Gold patch adds `if not name: raise ValueError(...)` before the `.`-check.

Probes (all run via nl_attack on the official image):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): Blueprint('', __name__) raises ValueError. PATCHED: HOLDS (exit0). BASE: VIOLATED (returns <Blueprint ''>, exit1) -> discriminates.
- probe_2 (Req1.3): empty name rejected with ValueError regardless of (importable) import_name (flask/os/__main__). PATCHED: HOLDS. NOTE: first draft used import_name='some.module' which is not importable and raised ImportError from super().__init__() before the name check reached — that was a probe artifact (check is placed after super().__init__), fixed by using importable names.
- probe_3 (Req2.1/2.2): dotted non-empty name 'a.b' still raises ValueError. PATCHED: HOLDS.
- probe_4 (Req3.1/3.2): valid 'admin' constructs and name attr preserved. PATCHED: HOLDS.
- probe_5 (Req3.3/3.4): valid blueprint keeps full capabilities — construction options (url_prefix/subdomain/url_defaults/cli_group), whitespace-only name ' ' accepted+preserved (falsy check only, not str.strip), app registration, routing, url_for endpoint building. PATCHED: HOLDS.

Candidate wrong patch 'reject_none_only' (weak.diff): rejects only name is None instead of falsy/empty. Applies at base_commit. Under this patch probes 1 and 2 are REJECTED (empty string '' still accepted), while probes 3/4/5 hold — demonstrates the suite discriminates the lazy 'falsy-misread' fix that would not resolve the hidden test (which asserts Blueprint('') raises).

Verdict SOUND: 5 distinct probes all hold on gold-patched tree; positive control fails at base (prepatch reproduced); >=1 candidate exercised and REJECTED by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req1.1/1.2: empty name -> ValueError at construction (POSITIVE CONTROL)
import sys
from flask import Blueprint
try:
    bp = Blueprint("", __name__)
    print("NO ERROR: instance returned for empty name:", bp)
    sys.exit(1)
except ValueError as e:
    print("OK: ValueError raised for empty name:", e)
    sys.exit(0)
except Exception as e:
    print("WRONG EXC TYPE:", type(e).__name__, e)
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: validate Blueprint(name) at construction so an empty name raises ValueError, preserving dotted-name rejection and all valid-name behavior. Gold patch adds `if not name: raise ValueError(...)` before the `.`-check.

Probes (all run via nl_attack on the official image):
- probe_1 (Req1.1/1.2, POSITIVE CONTROL): Blueprint('', __name__) raises ValueError. PATCHED: HOLDS (exit0). BASE: VIOLATED (returns <Blueprint ''>, exit1) -> discriminates.
- probe_2 (Req1.3): empty name rejected with ValueError regardless of (importable) import_name (flask/os/__main__). PATCHED: HOLDS. NOTE: first draft used import_name='some.module' which is not importable and raised ImportError from super().__init__() before the name check reached — that was a probe artifact (check is placed after super().__init__), fixed by using importable names.
- probe_3 (Req2.1/2.2): dotted non-empty name 'a.b' still raises ValueError. PATCHED: HOLDS.
- probe_4 (Req3.1/3.2): valid 'admin' constructs and name attr preserved. PATCHED: HOLDS.
- probe_5 (Req3.3/3.4): valid blueprint keeps full capabilities — construction options (url_prefix/subdomain/url_defaults/cli_group), whitespace-only name ' ' accepted+preserved (falsy check only, not str.strip), app registration, routing, url_for endpoint building. PATCHED: HOLDS.

Candidate wrong patch 'reject_none_only' (weak.diff): rejects only name is None instead of falsy/empty. Applies at base_commit. Under this patch probes 1 and 2 are REJECTED (empty string '' still accepted), while probes 3/4/5 hold — demonstrates the suite discriminates the lazy 'falsy-misread' fix that would not resolve the hidden test (which asserts Blueprint('') raises).

Verdict SOUND: 5 distinct probes all hold on gold-patched tree; positive control fails at base (prepatch reproduced); >=1 candidate exercised and REJECTED by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds `if not name: raise ValueError("'name' may not be empty.")` before the existing dot check in Blueprint.__init__. Requirements 1-3 map 1:1 to this: empty->ValueError as a falsy check independent of import_name (verified with empty import_name), dotted check preserved and independent, valid names unchanged. Req3.4 enumerates unchanged existing capabilities — appropriately scoped as preservation, not invented behavior. Probe ALL PASS on patched (exit 0), VIOLATED on base (empty accepted).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold adds `if not name: raise ValueError("'name' may not be empty.")`; hidden F2P is test_empty_name_not_allowed asserting Blueprint("", __name__) raises ValueError. All of this is public via problem_statement (empty name -> ValueError). Requirements contain no test path/name (test_empty_name_not_allowed absent), no quoted test/gold code, no fix-invented identifiers (the gold error string is not quoted), and no parametrization ids (the prefix-slash / nesting tuples are NOT enumerated; described only as behavioral prose). Module/function localization (flask.blueprints.Blueprint, Blueprint.__init__, src/flask/blueprints.py) is legitimate. Requirement 3.4's capability enumeration loosely tracks the PASS_TO_PASS regression suite but states general, publicly-known Flask blueprint features as preserved behavior rather than transmitting test identifiers/ids/code — legitimate regression-scope description, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
