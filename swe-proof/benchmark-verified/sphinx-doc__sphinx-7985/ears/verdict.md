# P2 adversarial audit — sphinx-doc__sphinx-7985

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
"""Positive control + Req2.4: a reference that looks like a source-tree path
and does NOT resolve to an existing entry (and matches no ignore pattern) SHALL
be reported 'broken'. On base this is reported 'local' (never broken)."""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_")
    out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    rows = [json.loads(l) for l in open(path.join(out, "output.json")) if l.strip()]
    txtp = path.join(out, "output.txt")
    return rows, (open(txtp).read() if path.exists(txtp) else "")

def status_of(rows, uri):
    for r in rows:
        if r.get("uri") == uri:
            return r.get("status")
    return None

rows, txt = build([("dangling", "does_not_exist.rst")])
st = status_of(rows, "does_not_exist.rst")
print("status for dangling internal ref =", st)
if st != "broken":
    print("FAIL: expected 'broken', got", st)
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req2.2: an internal reference that DOES resolve to an existing file in the
source dir SHALL be reported 'working'."""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_"); out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    rows = [json.loads(l) for l in open(path.join(out, "output.json")) if l.strip()]
    txtp = path.join(out, "output.txt")
    return rows, (open(txtp).read() if path.exists(txtp) else "")

def status_of(rows, uri):
    for r in rows:
        if r.get("uri") == uri:
            return r.get("status")
    return None

rows, txt = build([("exists", "present.txt")], files=["present.txt"])
st = status_of(rows, "present.txt")
print("status for existing internal ref =", st)
if st != "working":
    print("FAIL: expected 'working', got", st); sys.exit(1)
print("PASS"); sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2.3: an internal reference that does NOT resolve but matches a configured
linkcheck_ignore pattern SHALL be reported 'ignored' (not broken)."""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_"); out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    rows = [json.loads(l) for l in open(path.join(out, "output.json")) if l.strip()]
    txtp = path.join(out, "output.txt")
    return rows, (open(txtp).read() if path.exists(txtp) else "")

def status_of(rows, uri):
    for r in rows:
        if r.get("uri") == uri:
            return r.get("status")
    return None

rows, txt = build([("ign", "missing_ignored.rst")],
                  extra_conf="linkcheck_ignore = ['missing_ignored.*']\n")
st = status_of(rows, "missing_ignored.rst")
print("status for missing-but-ignored internal ref =", st)
if st != "ignored":
    print("FAIL: expected 'ignored', got", st); sys.exit(1)
print("PASS"); sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req1.4: a non-http reference carrying an explicit <lowercase-letters>://
scheme (e.g. foo://bar, an unsupported transfer scheme) SHALL be reported
'unchecked' rather than resolved as a path. Base reports 'local'."""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_"); out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    rows = [json.loads(l) for l in open(path.join(out, "output.json")) if l.strip()]
    txtp = path.join(out, "output.txt")
    return rows, (open(txtp).read() if path.exists(txtp) else "")

def status_of(rows, uri):
    for r in rows:
        if r.get("uri") == uri:
            return r.get("status")
    return None

# ftp://host is an explicit scheme://; must be 'unchecked', never 'broken'/'working'
rows, txt = build([("ftp", "ftp://ftp.example.com/pub/file")])
st = status_of(rows, "ftp://ftp.example.com/pub/file")
print("status for ftp:// scheme ref =", st)
if st != "unchecked":
    print("FAIL: expected 'unchecked', got", st); sys.exit(1)
print("PASS"); sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req1.2 & Req1.3: in-page anchor (#...) and mailto: references SHALL be
reported 'unchecked' (must NOT become 'broken' by the new path resolver)."""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_"); out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    rows = [json.loads(l) for l in open(path.join(out, "output.json")) if l.strip()]
    txtp = path.join(out, "output.txt")
    return rows, (open(txtp).read() if path.exists(txtp) else "")

def status_of(rows, uri):
    for r in rows:
        if r.get("uri") == uri:
            return r.get("status")
    return None

rows, txt = build([("anchor", "#section"), ("mail", "mailto:nobody@example.com")])
sa = status_of(rows, "#section")
sm = status_of(rows, "mailto:nobody@example.com")
print("status for '#section' =", sa, "; status for mailto: =", sm)
ok = True
if sa != "unchecked":
    print("FAIL: anchor expected 'unchecked', got", sa); ok = False
if sm != "unchecked":
    print("FAIL: mailto expected 'unchecked', got", sm); ok = False
if not ok:
    sys.exit(1)
print("PASS"); sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req2.5 (normative SHALL): a broken internal reference SHALL be recorded in
the human-readable output.txt on its OWN line prefixed with the broken-status
marker '[broken]' and containing the failing reference string. (The trailing
"so that ... finishes with problems" clause is rationale, not a separate SHALL;
the gold patch does not increment statuscode for local refs, so this probe
encodes only the recorded-marker-line obligation.)"""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_"); out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    txtp = path.join(out, "output.txt")
    txt = open(txtp).read() if path.exists(txtp) else ""
    return txt

txt = build([("dangling", "no_such_file.rst")])
print("output.txt:\n" + txt)
broken_lines = [l for l in txt.splitlines()
                if "[broken]" in l and "no_such_file.rst" in l]
if not broken_lines:
    print("FAIL: no '[broken]' line for the dangling ref in output.txt"); sys.exit(1)
print("PASS: found broken marker line ->", broken_lines[0]); sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req4.1 & Req4.5: exactly one structured result record per checked reference,
each carrying filename, lineno, status, code, uri, info. Total records == number
of references. Uses only network-free internal refs so it is deterministic."""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_"); out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    rows = [json.loads(l) for l in open(path.join(out, "output.json")) if l.strip()]
    return rows

links = [("a", "good.txt"),          # working
         ("b", "bad.rst"),           # broken
         ("c", "#anchor"),           # unchecked
         ("d", "mailto:x@y.z")]      # unchecked
rows = build(links, files=["good.txt"])
uris = {r["uri"] for r in rows}
print("n_rows =", len(rows), "; uris =", sorted(uris))
required = {"filename", "lineno", "status", "code", "uri", "info"}
ok = True
if len(rows) != len(links):
    print("FAIL: expected", len(links), "records, got", len(rows)); ok = False
for r in rows:
    missing = required - set(r.keys())
    if missing:
        print("FAIL: record missing fields", missing, "->", r); ok = False
for _, u in links:
    if u not in uris:
        print("FAIL: no record for reference", u); ok = False
if not ok:
    sys.exit(1)
print("PASS"); sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req2.4: a reference that looks like a source-tree path
and does NOT resolve to an existing entry (and matches no ignore pattern) SHALL
be reported 'broken'. On base this is reported 'local' (never broken)."""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_")
    out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    rows = [json.loads(l) for l in open(path.join(out, "output.json")) if l.strip()]
    txtp = path.join(out, "output.txt")
    return rows, (open(txtp).read() if path.exists(txtp) else "")

def status_of(rows, uri):
    for r in rows:
        if r.get("uri") == uri:
            return r.get("status")
    return None

rows, txt = build([("dangling", "does_not_exist.rst")])
st = status_of(rows, "does_not_exist.rst")
print("status for dangling internal ref =", st)
if st != "broken":
    print("FAIL: expected 'broken', got", st)
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7985: linkcheck classifies non-http references locally. Base returns 'local' for every non-http ref (never verified); gold resolves them to working/ignored/broken and returns 'unchecked' for <scheme>:// refs.

Probes (all run in the official image):
- probe_1 (POSITIVE CONTROL, Req2.4): dangling internal ref -> 'broken'. HOLDS gold, FAILS base ('local'). Discriminates.
- probe_2 (Req2.2): existing source-tree file -> 'working'. HOLDS gold.
- probe_3 (Req2.3): missing ref matching linkcheck_ignore -> 'ignored'. HOLDS gold.
- probe_4 (Req1.4): ftp://host explicit scheme -> 'unchecked'. HOLDS gold.
- probe_5 (Req1.2/1.3): '#anchor' and 'mailto:' -> 'unchecked'. HOLDS gold.
- probe_6 (Req2.5 normative SHALL): broken internal ref recorded on its own '[broken]' line in output.txt. HOLDS gold. NOTE: initial version also asserted statuscode==1 ('finishes with problems'); the gold patch does NOT populate self.broken for local refs so statuscode stays 0. That clause is rationale ('so that ...'), not a separate SHALL, so probe_6 was corrected to encode only the recorded-marker-line obligation. This is a minor spec-prose over-implication, not a violation.
- probe_7 (Req4.1/4.5): one structured record per reference with all 6 fields (filename/lineno/status/code/uri/info); count == #refs. HOLDS gold.

CANDIDATE PATCH (weak.diff): naive fix that resolves path existence (working/broken) but omits BOTH the scheme:// -> unchecked branch and the ignore-pattern -> ignored branch. Applies at base. My suite REJECTS it: probe_3 VIOLATED (missing-but-ignored ref wrongly 'broken'). (probe_4 still held because base kept the ftp: prefix in the unchecked tuple; the ignore-branch omission is the discriminator.) This demonstrates the suite discriminates a requirements-non-conforming implementation.

All 7 probes HOLD on the gold-patched tree; positive control fails at base (prepatch_reproduced=true); a plausibly-wrong candidate is rejected. No too-weak candidate survived. Verdict SOUND.

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
"""Positive control + Req2.4: a reference that looks like a source-tree path
and does NOT resolve to an existing entry (and matches no ignore pattern) SHALL
be reported 'broken'. On base this is reported 'local' (never broken)."""
import io, json, sys, tempfile
from os import path

def build(links, extra_conf="", files=None):
    from sphinx.application import Sphinx
    src = tempfile.mkdtemp(prefix="lc_src_")
    out = tempfile.mkdtemp(prefix="lc_out_")
    dtd = tempfile.mkdtemp(prefix="lc_dtd_")
    conf = ("master_doc = 'index'\nsource_suffix = '.txt'\n"
            "exclude_patterns = ['_build']\nlinkcheck_anchors = False\n"
            "linkcheck_timeout = 1\n" + extra_conf)
    open(path.join(src, "conf.py"), "w").write(conf)
    body = ["Test", "===="]
    for text, uri in links:
        body += ["", "* `%s <%s>`_" % (text, uri)]
    body.append("")
    open(path.join(src, "index.txt"), "w").write("\n".join(body))
    for fn in (files or []):
        open(path.join(src, fn), "w").write("x\n")
    app = Sphinx(src, src, out, dtd, "linkcheck", freshenv=True,
                 status=io.StringIO(), warning=io.StringIO())
    app.build(force_all=True)
    rows = [json.loads(l) for l in open(path.join(out, "output.json")) if l.strip()]
    txtp = path.join(out, "output.txt")
    return rows, (open(txtp).read() if path.exists(txtp) else "")

def status_of(rows, uri):
    for r in rows:
        if r.get("uri") == uri:
            return r.get("status")
    return None

rows, txt = build([("dangling", "does_not_exist.rst")])
st = status_of(rows, "does_not_exist.rst")
print("status for dangling internal ref =", st)
if st != "broken":
    print("FAIL: expected 'broken', got", st)
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7985: linkcheck classifies non-http references locally. Base returns 'local' for every non-http ref (never verified); gold resolves them to working/ignored/broken and returns 'unchecked' for <scheme>:// refs.

Probes (all run in the official image):
- probe_1 (POSITIVE CONTROL, Req2.4): dangling internal ref -> 'broken'. HOLDS gold, FAILS base ('local'). Discriminates.
- probe_2 (Req2.2): existing source-tree file -> 'working'. HOLDS gold.
- probe_3 (Req2.3): missing ref matching linkcheck_ignore -> 'ignored'. HOLDS gold.
- probe_4 (Req1.4): ftp://host explicit scheme -> 'unchecked'. HOLDS gold.
- probe_5 (Req1.2/1.3): '#anchor' and 'mailto:' -> 'unchecked'. HOLDS gold.
- probe_6 (Req2.5 normative SHALL): broken internal ref recorded on its own '[broken]' line in output.txt. HOLDS gold. NOTE: initial version also asserted statuscode==1 ('finishes with problems'); the gold patch does NOT populate self.broken for local refs so statuscode stays 0. That clause is rationale ('so that ...'), not a separate SHALL, so probe_6 was corrected to encode only the recorded-marker-line obligation. This is a minor spec-prose over-implication, not a violation.
- probe_7 (Req4.1/4.5): one structured record per reference with all 6 fields (filename/lineno/status/code/uri/info); count == #refs. HOLDS gold.

CANDIDATE PATCH (weak.diff): naive fix that resolves path existence (working/broken) but omits BOTH the scheme:// -> unchecked branch and the ignore-pattern -> ignored branch. Applies at base. My suite REJECTS it: probe_3 VIOLATED (missing-but-ignored ref wrongly 'broken'). (probe_4 still held because base kept the ftp: prefix in the unchecked tuple; the ignore-branch omission is the discriminator.) This demonstrates the suite discriminates a requirements-non-conforming implementation.

All 7 probes HOLD on the gold-patched tree; positive control fails at base (prepatch_reproduced=true); a plausibly-wrong candidate is rejected. No too-weak candidate survived. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Emulated the exact patched check() decision logic and probed representative inputs: ''->unchecked, '#anchor'->unchecked, 'mailto:a@b'->unchecked, 'ftp://x/y'->unchecked, 'foo.rst'(exists)->working, 'sub/'(exists)->working, 'missing.rst'->broken, 'ignoreme'(matches ignore)->ignored, 'http/https'->web path. All consistent with requirements. Note requirements correctly do NOT list 'ftp:' among the unconditional-unchecked prefixes (the patch removed it), and Req 1.4 correctly captures that ftp://-style schemes now fall to the uri_re branch — a subtle boundary the requirements got right.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior at the right altitude and do not transmit the hidden tests. Checked every candidate: (1) Status vocabulary (unchecked/working/ignored/broken/redirected) are code-level states, legitimate to name and derivable from the public problem_statement's desire to classify links. (2) The classifier rules (empty ref, '#', 'mailto:', '<lowercase>://' scheme, resolve path against srcdir, ignore-patterns) restate the gold logic but as behavioral requirements — this is the intended translation, not a leak; no fix-invented identifiers (uri_re, to_ignore, srcdir, self.good/broken) appear. (3) Req 2.5's 'failing reference string on its own line prefixed with the broken-status marker' generalizes the test's '[broken] path/to/notfound' assertion but does NOT quote the marker literal '[broken]' or the path 'path/to/notfound'. (4) Req 4.2 ('correct source line number ... including references that follow a newly checked internal reference') echoes the test's lineno 16->18 shift for image2.png, but expresses it as a genuine behavioral invariant rather than reconstructing the specific line numbers or node ids. (5) Req 4.5 ('one record per reference, total equals count') generalizes len(rows)==10 without leaking the count. No test names, file paths (test_build_linkcheck.py, links.txt), function names (test_defaults/test_anchors_ignored/test_defaults_json), parametrization ids, or verbatim gold-patch lines are present. No case enumeration mirrors the parametrized fixture (e.g., no mention of conf.py, google image URLs by count, localhost:7777). This is faithful behavioral specification, not test transmission.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
