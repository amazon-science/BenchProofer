# P2 adversarial audit — django__django-9296

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from django.core.paginator import Paginator, Page

# Req1.1/1.2/1.4: iter() returns iterator; iterating yields one Page per page_range
# number; each yielded page identical in contents to page(number).
objs = list(range(1, 24))  # 23 items
p = Paginator(objs, per_page=5)  # 5 pages: 5,5,5,5,3

it = iter(p)
if not hasattr(it, "__next__"):
    print("FAIL: iter(paginator) did not return an iterator")
    sys.exit(1)

pages = list(p)
expected_numbers = list(p.page_range)
got_numbers = [pg.number for pg in pages]
print("page_range:", expected_numbers, "iterated numbers:", got_numbers)

if not all(isinstance(pg, Page) for pg in pages):
    print("FAIL: not all yielded objects are Page instances")
    sys.exit(1)
if got_numbers != expected_numbers:
    print("FAIL: iterated page numbers != page_range")
    sys.exit(1)
for n in expected_numbers:
    via_iter = [x for x in pages if x.number == n][0]
    via_call = p.page(n)
    if list(via_iter.object_list) != list(via_call.object_list):
        print("FAIL: contents differ for page", n)
        sys.exit(1)
print("PASS: iteration yields Page per page_range with identical contents")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from django.core.paginator import Paginator

# Req1.3: ascending page-number order beginning at page 1, same ordering as page_range.
objs = list(range(100))
p = Paginator(objs, per_page=7)
nums = [pg.number for pg in p]
print("numbers:", nums)
if not nums:
    print("FAIL: no pages yielded")
    sys.exit(1)
if nums[0] != 1:
    print("FAIL: does not begin at page 1")
    sys.exit(1)
if nums != sorted(nums):
    print("FAIL: not ascending")
    sys.exit(1)
if nums != list(p.page_range):
    print("FAIL: order != page_range")
    sys.exit(1)
print("PASS: ascending from 1, matches page_range")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from django.core.paginator import Paginator

# Req1.5: final partial page honors orphans; consistent with page(num_pages).
# 23 items, per_page 5, orphans 0 -> last page has 3 items.
p = Paginator(list(range(1, 24)), per_page=5, orphans=0)
pages = list(p)
last = pages[-1]
print("num_pages", p.num_pages, "last number", last.number, "last len", len(last.object_list))
if last.number != p.num_pages:
    print("FAIL: last iterated page != num_pages")
    sys.exit(1)
if list(last.object_list) != list(p.page(p.num_pages).object_list):
    print("FAIL: last page contents differ from page(num_pages)")
    sys.exit(1)
if list(last.object_list) != [21, 22, 23]:
    print("FAIL: trailing remainder wrong", list(last.object_list))
    sys.exit(1)

# orphans case: 23 items, per_page 5, orphans 3 -> last 8 fold into page 4
p2 = Paginator(list(range(1, 24)), per_page=5, orphans=3)
pages2 = list(p2)
print("orphans num_pages", p2.num_pages, "counts", [len(x.object_list) for x in pages2])
if p2.num_pages != 4:
    print("FAIL: orphans num_pages wrong")
    sys.exit(1)
if list(pages2[-1].object_list) != list(p2.page(4).object_list):
    print("FAIL: orphan last page mismatch")
    sys.exit(1)
print("PASS: final partial page honors orphans, matches page(num_pages)")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from django.core.paginator import Paginator

# Req1.6 single page; Req1.7 empty page_range; Req1.8 lazy next() + StopIteration.

# single page
p1 = Paginator(list(range(3)), per_page=10)
pages = list(p1)
print("single: numbers", [x.number for x in pages])
if len(pages) != 1 or pages[0].number != 1:
    print("FAIL: single page iteration wrong")
    sys.exit(1)

# empty object_list, allow_empty_first_page=False -> 0 pages, page_range empty
p0 = Paginator([], per_page=5, allow_empty_first_page=False)
print("empty num_pages", p0.num_pages, "page_range", list(p0.page_range))
empty_pages = list(p0)
if empty_pages != []:
    print("FAIL: empty paginator yielded pages", empty_pages)
    sys.exit(1)

# lazy next() + StopIteration
p2 = Paginator(list(range(12)), per_page=5)  # 3 pages
it = iter(p2)
seen = []
try:
    while True:
        seen.append(next(it).number)
except StopIteration:
    pass
print("lazy numbers", seen)
if seen != list(p2.page_range):
    print("FAIL: lazy next order wrong")
    sys.exit(1)
# after exhaustion, another next raises StopIteration
try:
    next(it)
    print("FAIL: no StopIteration after exhaustion")
    sys.exit(1)
except StopIteration:
    pass
print("PASS: single/empty/lazy-next+StopIteration all correct")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from django.core.paginator import Paginator, Page, PageNotAnInteger, EmptyPage

# Req2 regression: page_range, num_pages, count, page(), validate_number, get_page,
# Page API preserved.
p = Paginator(list(range(1, 24)), per_page=5)  # 5 pages
if list(p.page_range) != [1, 2, 3, 4, 5]:
    print("FAIL: page_range", list(p.page_range)); sys.exit(1)
if p.num_pages != 5:
    print("FAIL: num_pages", p.num_pages); sys.exit(1)
if p.count != 23:
    print("FAIL: count", p.count); sys.exit(1)

# empty + not allow_empty_first_page -> 0 pages (Req2.2)
if Paginator([], per_page=5, allow_empty_first_page=False).num_pages != 0:
    print("FAIL: empty num_pages not 0"); sys.exit(1)

# validate_number errors (Req2.5)
try:
    p.validate_number("abc"); print("FAIL: no PageNotAnInteger"); sys.exit(1)
except PageNotAnInteger:
    pass
try:
    p.validate_number(0); print("FAIL: no EmptyPage for <1"); sys.exit(1)
except EmptyPage:
    pass
try:
    p.validate_number(999); print("FAIL: no EmptyPage for >pages"); sys.exit(1)
except EmptyPage:
    pass

# get_page fallbacks (Req2.6)
if p.get_page("x").number != 1:
    print("FAIL: get_page non-int not page 1"); sys.exit(1)
if p.get_page(999).number != p.num_pages:
    print("FAIL: get_page oob not last page"); sys.exit(1)

# Page API (Req2.8)
pg = p.page(2)
if len(pg) != 5: print("FAIL: len(page)", len(pg)); sys.exit(1)
if pg[0] != p.page(2).object_list[0]: print("FAIL: indexing"); sys.exit(1)
if not (pg.has_next() and pg.has_previous() and pg.has_other_pages()):
    print("FAIL: has_* on middle page"); sys.exit(1)
if pg.next_page_number() != 3 or pg.previous_page_number() != 1:
    print("FAIL: next/prev page number"); sys.exit(1)
if pg.start_index() != 6 or pg.end_index() != 10:
    print("FAIL: start/end index", pg.start_index(), pg.end_index()); sys.exit(1)

print("PASS: existing paging behavior preserved")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from django.core.paginator import Paginator, Page

# Req1.1/1.2/1.4: iter() returns iterator; iterating yields one Page per page_range
# number; each yielded page identical in contents to page(number).
objs = list(range(1, 24))  # 23 items
p = Paginator(objs, per_page=5)  # 5 pages: 5,5,5,5,3

it = iter(p)
if not hasattr(it, "__next__"):
    print("FAIL: iter(paginator) did not return an iterator")
    sys.exit(1)

pages = list(p)
expected_numbers = list(p.page_range)
got_numbers = [pg.number for pg in pages]
print("page_range:", expected_numbers, "iterated numbers:", got_numbers)

if not all(isinstance(pg, Page) for pg in pages):
    print("FAIL: not all yielded objects are Page instances")
    sys.exit(1)
if got_numbers != expected_numbers:
    print("FAIL: iterated page numbers != page_range")
    sys.exit(1)
for n in expected_numbers:
    via_iter = [x for x in pages if x.number == n][0]
    via_call = p.page(n)
    if list(via_iter.object_list) != list(via_call.object_list):
        print("FAIL: contents differ for page", n)
        sys.exit(1)
print("PASS: iteration yields Page per page_range with identical contents")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix adds Paginator.__iter__ that yields self.page(n) for n in self.page_range. Requirements faithfully mandate this.

Probes (all HOLD on patched tree; each encodes distinct criteria):
- probe_1 (Req1.1/1.2/1.4): iter() returns an iterator; iterating yields one Page per page_range number; each yielded page identical in contents to page(number). POSITIVE CONTROL: fails at base with 'Paginator object is not iterable' (TypeError) => prepatch reproduced.
- probe_2 (Req1.3): ascending order beginning at page 1, matching page_range.
- probe_3 (Req1.5): final partial page honors orphans (orphans=0 -> [21,22,23]; orphans=3 -> 4 pages), consistent with page(num_pages).
- probe_4 (Req1.6/1.7/1.8): single-page yields exactly one page; empty page_range (allow_empty_first_page=False) yields nothing; lazy next() returns pages in order then raises StopIteration.
- probe_5 (Req2 regression): page_range/num_pages/count preserved; validate_number raises PageNotAnInteger / EmptyPage; get_page fallbacks; Page len/index/has_*/next-prev/start-end index unchanged.

Candidate wrong patches (both REJECTED by suite => discriminating):
- weak.diff: 0-based `range(self.num_pages)` (yields page 0..n-1). Rejected by probes 1-4 (page(0) raises EmptyPage / wrong numbers); probe_5 correctly still holds (paging arithmetic untouched).
- weak2.diff: __iter__ yields raw object_list items instead of Page objects. Rejected by probes 1-4 (yielded objects aren't Pages); probe_5 correctly still holds.

All 5 probes HOLD on gold-patched tree; positive control discriminates (HOLD patched, FAIL base). No too-weak alternative found: every plausibly-wrong __iter__ variant is caught by the behavioral+contents probes.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
import sys
from django.core.paginator import Paginator, Page

# Req1.1/1.2/1.4: iter() returns iterator; iterating yields one Page per page_range
# number; each yielded page identical in contents to page(number).
objs = list(range(1, 24))  # 23 items
p = Paginator(objs, per_page=5)  # 5 pages: 5,5,5,5,3

it = iter(p)
if not hasattr(it, "__next__"):
    print("FAIL: iter(paginator) did not return an iterator")
    sys.exit(1)

pages = list(p)
expected_numbers = list(p.page_range)
got_numbers = [pg.number for pg in pages]
print("page_range:", expected_numbers, "iterated numbers:", got_numbers)

if not all(isinstance(pg, Page) for pg in pages):
    print("FAIL: not all yielded objects are Page instances")
    sys.exit(1)
if got_numbers != expected_numbers:
    print("FAIL: iterated page numbers != page_range")
    sys.exit(1)
for n in expected_numbers:
    via_iter = [x for x in pages if x.number == n][0]
    via_call = p.page(n)
    if list(via_iter.object_list) != list(via_call.object_list):
        print("FAIL: contents differ for page", n)
        sys.exit(1)
print("PASS: iteration yields Page per page_range with identical contents")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Gold fix adds Paginator.__iter__ that yields self.page(n) for n in self.page_range. Requirements faithfully mandate this.

Probes (all HOLD on patched tree; each encodes distinct criteria):
- probe_1 (Req1.1/1.2/1.4): iter() returns an iterator; iterating yields one Page per page_range number; each yielded page identical in contents to page(number). POSITIVE CONTROL: fails at base with 'Paginator object is not iterable' (TypeError) => prepatch reproduced.
- probe_2 (Req1.3): ascending order beginning at page 1, matching page_range.
- probe_3 (Req1.5): final partial page honors orphans (orphans=0 -> [21,22,23]; orphans=3 -> 4 pages), consistent with page(num_pages).
- probe_4 (Req1.6/1.7/1.8): single-page yields exactly one page; empty page_range (allow_empty_first_page=False) yields nothing; lazy next() returns pages in order then raises StopIteration.
- probe_5 (Req2 regression): page_range/num_pages/count preserved; validate_number raises PageNotAnInteger / EmptyPage; get_page fallbacks; Page len/index/has_*/next-prev/start-end index unchanged.

Candidate wrong patches (both REJECTED by suite => discriminating):
- weak.diff: 0-based `range(self.num_pages)` (yields page 0..n-1). Rejected by probes 1-4 (page(0) raises EmptyPage / wrong numbers); probe_5 correctly still holds (paging arithmetic untouched).
- weak2.diff: __iter__ yields raw object_list items instead of Page objects. Rejected by probes 1-4 (yielded objects aren't Pages); probe_5 correctly still holds.

All 5 probes HOLD on gold-patched tree; positive control discriminates (HOLD patched, FAIL base). No too-weak alternative found: every plausibly-wrong __iter__ variant is caught by the behavioral+contents probes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed via nl_attack on both patched and base trees. Modeling boundary = the __iter__ observable behavior, matching the diff exactly. No requirement mandates behavior the code lacks, forbids behavior it has, invents behavior, or pins a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The gold edit (__iter__ yielding self.page(page_num) over self.page_range) is quoted verbatim in the PUBLIC problem_statement, so any resemblance in the requirements traces to public material, not hidden tests. The hidden test (test_paginator_iteration: Paginator([1,2,3],2) expecting [1,2] then [3]) is not transmitted: no test function/class name, file path, parametrization id, or the specific [1,2,3]/per_page=2 -> [1,2],[3] case is reproduced. Requirements 1-8 translate iteration semantics (yield one Page per page_range number, ascending order, partial final page, single/empty page, lazy next()/StopIteration) into behavioral prose — the legitimate purpose. Requirement 2's references to page_range/num_pages/count/validate_number/get_page/UnorderedObjectListWarning correspond to PASS_TO_PASS regression coverage but are all public Paginator/Page API describing preserved behavior, not test-shaped reconstruction. Naming paginator.py and Paginator is proper localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
