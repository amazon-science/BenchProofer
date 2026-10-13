# P2 adversarial audit — sphinx-doc__sphinx-8721

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_epub_default.py`, `probe_2_epub_enabled.py`, `probe_3_singlehtml.py`, `probe_4_html_pages.py`, `probe_5_html_backlink.py`, `probe_6_no_data_early_return.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_epub_default.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_epub_default.py` → holds on the patched tree (good)

```python
"""Req 1 (1.1/1.2) + POSITIVE CONTROL: the 'make html epub' scenario. An HTML
build first populates the shared doctree env with _viewcode_modules; then the
epub build reuses that env (freshenv=False), so collect_pages runs with module
data present. With the default config (viewcode_enable_epub=False) the epub
build must NOT write per-module source pages.

This is the faithful reproduction of the reported bug (a fresh standalone epub
build never populates _viewcode_modules because doctree_read gates it, so it
cannot discriminate). HOLD iff _modules/spam/mod1.xhtml is absent from the epub
outdir. Fails at base (page written), holds patched (collect_pages gates)."""
import os, sys, shutil, tempfile, io

def mkbuild(buildername, src, out, doctree, confoverrides=None, freshenv=True):
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, doctree, buildername,
                 confoverrides=confoverrides or {}, status=None,
                 warning=io.StringIO(), freshenv=freshenv)
    app.build()
    return app

root = None
for base in ["/testbed", os.getcwd()]:
    p = os.path.join(base, "tests/roots/test-ext-viewcode")
    if os.path.isdir(p):
        root = p; break
if root is None:
    print("NO_TESTROOT"); sys.exit(2)
tmp = tempfile.mkdtemp(prefix="vc_")
src = os.path.join(tmp, "src"); shutil.copytree(root, src)
dt = os.path.join(tmp, "doctrees")

# 1) html build populates the shared env
ah = mkbuild("html", src, os.path.join(tmp, "html"), dt)
nmod = len(getattr(ah.builder.env, "_viewcode_modules", {}))
# 2) epub build reuses the shared doctree env (freshenv=False)
oute = os.path.join(tmp, "epub")
ae = mkbuild("epub", src, oute, dt, freshenv=False)
nmod2 = len(getattr(ae.builder.env, "_viewcode_modules", {}))

modpage = os.path.join(oute, "_modules", "spam", "mod1.xhtml")
exists = os.path.exists(modpage)
print("html env modules =", nmod, "; epub env modules =", nmod2)
print("epub default (shared env): mod1.xhtml exists =", exists)
sys.exit(1 if exists else 0)
```

Attack 2 — `probe_2_epub_enabled.py` → holds on the patched tree (good)

```python
"""Req 2.2: epub build with viewcode_enable_epub=True must WRITE a per-module
source page for each module with collected data. HOLD iff _modules/spam/mod1.xhtml
exists."""
import os, sys, shutil, tempfile

def build(buildername, confoverrides=None):
    root = None
    for base in ["/testbed", os.getcwd()]:
        p = os.path.join(base, "tests/roots/test-ext-viewcode")
        if os.path.isdir(p):
            root = p; break
    if root is None:
        print("NO_TESTROOT"); sys.exit(2)
    tmp = tempfile.mkdtemp(prefix="vc_")
    src = os.path.join(tmp, "src"); shutil.copytree(root, src)
    out = os.path.join(tmp, "out"); doctree = os.path.join(tmp, "doctree")
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, doctree, buildername,
                 confoverrides=confoverrides or {}, status=None,
                 warning=__import__("io").StringIO(), freshenv=True)
    app.build()
    return app, out

app, out = build("epub", {"viewcode_enable_epub": True})
modpage = os.path.join(out, "_modules", "spam", "mod1.xhtml")
exists = os.path.exists(modpage)
print("epub enabled: mod1.xhtml exists =", exists)
sys.exit(0 if exists else 1)
```

Attack 3 — `probe_3_singlehtml.py` → holds on the patched tree (good)

```python
"""Req 3.1: singlehtml build must emit NO per-module source pages and NO viewcode
index page. Uses the shared-env scenario (html build first populates
_viewcode_modules) so the module data IS present when collect_pages runs for
singlehtml — otherwise the criterion would hold trivially. HOLD iff neither
_modules/spam/mod1.html nor _modules/index.html exists in the singlehtml outdir."""
import os, sys, shutil, tempfile, io

def mkbuild(buildername, src, out, doctree, confoverrides=None, freshenv=True):
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, doctree, buildername,
                 confoverrides=confoverrides or {}, status=None,
                 warning=io.StringIO(), freshenv=freshenv)
    app.build()
    return app

root = None
for base in ["/testbed", os.getcwd()]:
    p = os.path.join(base, "tests/roots/test-ext-viewcode")
    if os.path.isdir(p):
        root = p; break
if root is None:
    print("NO_TESTROOT"); sys.exit(2)
tmp = tempfile.mkdtemp(prefix="vc_")
src = os.path.join(tmp, "src"); shutil.copytree(root, src)
dt = os.path.join(tmp, "doctrees")
ah = mkbuild("html", src, os.path.join(tmp, "html"), dt)
print("html env modules =", len(getattr(ah.builder.env, "_viewcode_modules", {})))
outs = os.path.join(tmp, "single")
a = mkbuild("singlehtml", src, outs, dt, freshenv=False)
mod = os.path.join(outs, "_modules", "spam", "mod1.html")
idx = os.path.join(outs, "_modules", "index.html")
me = os.path.exists(mod); ie = os.path.exists(idx)
print("singlehtml: mod1.html exists =", me, "; _modules/index.html exists =", ie)
sys.exit(0 if (not me and not ie) else 1)
```

Attack 4 — `probe_4_html_pages.py` → holds on the patched tree (good)

```python
"""Req 4.1: ordinary HTML build must build & emit a highlighted source page for
each collected module AND the viewcode index page. HOLD iff both
_modules/spam/mod1.html and _modules/index.html exist."""
import os, sys, shutil, tempfile

def build(buildername, confoverrides=None):
    root = None
    for base in ["/testbed", os.getcwd()]:
        p = os.path.join(base, "tests/roots/test-ext-viewcode")
        if os.path.isdir(p):
            root = p; break
    if root is None:
        print("NO_TESTROOT"); sys.exit(2)
    tmp = tempfile.mkdtemp(prefix="vc_")
    src = os.path.join(tmp, "src"); shutil.copytree(root, src)
    out = os.path.join(tmp, "out"); doctree = os.path.join(tmp, "doctree")
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, doctree, buildername,
                 confoverrides=confoverrides or {}, status=None,
                 warning=__import__("io").StringIO(), freshenv=True)
    app.build()
    return app, out

app, out = build("html")
mod1 = os.path.join(out, "_modules", "spam", "mod1.html")
mod2 = os.path.join(out, "_modules", "spam", "mod2.html")
idx = os.path.join(out, "_modules", "index.html")
m1 = os.path.exists(mod1); m2 = os.path.exists(mod2); ie = os.path.exists(idx)
print("html: mod1=%s mod2=%s index=%s" % (m1, m2, ie))
sys.exit(0 if (m1 and m2 and ie) else 1)
```

Attack 5 — `probe_5_html_backlink.py` → holds on the patched tree (good)

```python
"""Req 4.3: for a standard HTML build the highlighted source content and the
[docs] back-link anchors must be unchanged. HOLD iff mod1.html contains the
viewcode-back [docs] anchor to spam.Class1 and the index.html has the two
_modules/spam/mod1.html#func1 back-references (as the upstream test asserts)."""
import os, re, sys, shutil, tempfile

def build(buildername, confoverrides=None):
    root = None
    for base in ["/testbed", os.getcwd()]:
        p = os.path.join(base, "tests/roots/test-ext-viewcode")
        if os.path.isdir(p):
            root = p; break
    if root is None:
        print("NO_TESTROOT"); sys.exit(2)
    tmp = tempfile.mkdtemp(prefix="vc_")
    src = os.path.join(tmp, "src"); shutil.copytree(root, src)
    out = os.path.join(tmp, "out"); doctree = os.path.join(tmp, "doctree")
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, doctree, buildername,
                 confoverrides=confoverrides or {}, status=None,
                 warning=__import__("io").StringIO(), freshenv=True)
    app.build()
    return app, out

app, out = build("html")
mod1 = os.path.join(out, "_modules", "spam", "mod1.html")
idx = os.path.join(out, "index.html")
r = open(mod1, encoding="utf8").read()
r = re.sub('<span class="[^"]{,2}">', '<span>', r)
back = ('<a class="viewcode-back" href="../../index.html#spam.Class1">[docs]</a>' in r)
idxt = open(idx, encoding="utf8").read()
nfunc1 = idxt.count('href="_modules/spam/mod1.html#func1"')
print("mod1 [docs] backlink present =", back, "; index func1 backlinks =", nfunc1)
sys.exit(0 if (back and nfunc1 == 2) else 1)
```

Attack 6 — `probe_6_no_data_early_return.py` → holds on the patched tree (good)

```python
"""Req 4.2: collect_pages SHALL keep the early return that yields no pages when no
viewcode module data was collected (env has no _viewcode_modules). HOLD iff, after
building HTML but removing the _viewcode_modules attribute from the env,
collect_pages yields an empty sequence."""
import os, sys, shutil, tempfile

def build(buildername, confoverrides=None):
    root = None
    for base in ["/testbed", os.getcwd()]:
        p = os.path.join(base, "tests/roots/test-ext-viewcode")
        if os.path.isdir(p):
            root = p; break
    if root is None:
        print("NO_TESTROOT"); sys.exit(2)
    tmp = tempfile.mkdtemp(prefix="vc_")
    src = os.path.join(tmp, "src"); shutil.copytree(root, src)
    out = os.path.join(tmp, "out"); doctree = os.path.join(tmp, "doctree")
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, doctree, buildername,
                 confoverrides=confoverrides or {}, status=None,
                 warning=__import__("io").StringIO(), freshenv=True)
    app.build()
    return app, out

from sphinx.ext.viewcode import collect_pages
app, out = build("html")
env = app.builder.env
if hasattr(env, "_viewcode_modules"):
    delattr(env, "_viewcode_modules")
pages = list(collect_pages(app))
print("collect_pages with no _viewcode_modules yielded", len(pages), "page(s)")
sys.exit(0 if len(pages) == 0 else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_epub_default.py`

```python
"""Req 1 (1.1/1.2) + POSITIVE CONTROL: the 'make html epub' scenario. An HTML
build first populates the shared doctree env with _viewcode_modules; then the
epub build reuses that env (freshenv=False), so collect_pages runs with module
data present. With the default config (viewcode_enable_epub=False) the epub
build must NOT write per-module source pages.

This is the faithful reproduction of the reported bug (a fresh standalone epub
build never populates _viewcode_modules because doctree_read gates it, so it
cannot discriminate). HOLD iff _modules/spam/mod1.xhtml is absent from the epub
outdir. Fails at base (page written), holds patched (collect_pages gates)."""
import os, sys, shutil, tempfile, io

def mkbuild(buildername, src, out, doctree, confoverrides=None, freshenv=True):
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, doctree, buildername,
                 confoverrides=confoverrides or {}, status=None,
                 warning=io.StringIO(), freshenv=freshenv)
    app.build()
    return app

root = None
for base in ["/testbed", os.getcwd()]:
    p = os.path.join(base, "tests/roots/test-ext-viewcode")
    if os.path.isdir(p):
        root = p; break
if root is None:
    print("NO_TESTROOT"); sys.exit(2)
tmp = tempfile.mkdtemp(prefix="vc_")
src = os.path.join(tmp, "src"); shutil.copytree(root, src)
dt = os.path.join(tmp, "doctrees")

# 1) html build populates the shared env
ah = mkbuild("html", src, os.path.join(tmp, "html"), dt)
nmod = len(getattr(ah.builder.env, "_viewcode_modules", {}))
# 2) epub build reuses the shared doctree env (freshenv=False)
oute = os.path.join(tmp, "epub")
ae = mkbuild("epub", src, oute, dt, freshenv=False)
nmod2 = len(getattr(ae.builder.env, "_viewcode_modules", {}))

modpage = os.path.join(oute, "_modules", "spam", "mod1.xhtml")
exists = os.path.exists(modpage)
print("html env modules =", nmod, "; epub env modules =", nmod2)
print("epub default (shared env): mod1.xhtml exists =", exists)
sys.exit(1 if exists else 0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8721: collect_pages in sphinx/ext/viewcode.py must gate module-page emission on the builder name (suppress epub-family unless viewcode_enable_epub, suppress singlehtml) mirroring the doctree_read gate.

KEY REPRODUCTION INSIGHT: a fresh standalone epub build never triggers the bug because base doctree_read already gates epub, leaving env._viewcode_modules empty, so collect_pages has nothing to emit and the criterion holds trivially at base. The reported bug ('make html epub') only manifests when a prior HTML build populates the SHARED doctree env; the epub build then reuses that env (freshenv=False) and collect_pages emits pages. probe_1 and probe_3 use this shared-env scenario, matching how the upstream FAIL_TO_PASS test (SphinxTestApp shared doctree dir) reproduces it.

### PROBES (all HOLD on gold-patched tree; runner re-runs):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): shared-env html->epub, default config => no _modules/spam/mod1.xhtml. VIOLATED at base (mod1.xhtml written), HOLDS patched. Discriminates.
- probe_2 (Req 2.2): epub build with viewcode_enable_epub=True => mod1.xhtml IS written. HOLDS patched.
- probe_3 (Req 3.1): shared-env html->singlehtml => no _modules/spam/mod1.html and no _modules/index.html. HOLDS patched.
- probe_4 (Req 4.1): plain html build => mod1.html, mod2.html and _modules/index.html all written. HOLDS patched.
- probe_5 (Req 4.3 regression): plain html => mod1.html contains viewcode-back [docs] anchor to spam.Class1 and index.html has 2 back-refs to mod1#func1 (upstream assertions). HOLDS patched.
- probe_6 (Req 4.2 regression): after deleting env._viewcode_modules, collect_pages yields 0 pages (early return preserved). HOLDS patched.

### CANDIDATE PATCHES (both apply at base, both REJECTED by the suite => suite discriminates wrong fixes; neither is a too-weak finding):
- weak_partial.diff: gates only singlehtml, forgets epub. REJECTED by probe_1 (VIOLATED: epub mod1.xhtml written). Would fail FAIL_TO_PASS test_viewcode_epub_default.
- weak_ignore_config.diff: gates singlehtml AND epub but IGNORES viewcode_enable_epub (suppresses epub unconditionally). REJECTED by probe_2 (VIOLATED: enabled epub produces no page); HOLDS probe_1. Would fail PASS_TO_PASS test_viewcode_epub_enabled.

No requirements-conforming alternative patch found that fails the hidden tests: the requirements pin the exact three-way builder-name gate (epub-prefix+config, singlehtml, else emit), which coincides with the gold fix. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_epub_default.py`, `probe_2_epub_enabled.py`, `probe_3_singlehtml.py`, `probe_4_html_pages.py`, `probe_5_html_backlink.py`, `probe_6_no_data_early_return.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_epub_default.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_epub_default.py` → holds on the patched tree (good)

Attack 2 — `probe_2_epub_enabled.py` → holds on the patched tree (good)

Attack 3 — `probe_3_singlehtml.py` → holds on the patched tree (good)

Attack 4 — `probe_4_html_pages.py` → holds on the patched tree (good)

Attack 5 — `probe_5_html_backlink.py` → holds on the patched tree (good)

Attack 6 — `probe_6_no_data_early_return.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_epub_default.py`

```python
"""Req 1 (1.1/1.2) + POSITIVE CONTROL: the 'make html epub' scenario. An HTML
build first populates the shared doctree env with _viewcode_modules; then the
epub build reuses that env (freshenv=False), so collect_pages runs with module
data present. With the default config (viewcode_enable_epub=False) the epub
build must NOT write per-module source pages.

This is the faithful reproduction of the reported bug (a fresh standalone epub
build never populates _viewcode_modules because doctree_read gates it, so it
cannot discriminate). HOLD iff _modules/spam/mod1.xhtml is absent from the epub
outdir. Fails at base (page written), holds patched (collect_pages gates)."""
import os, sys, shutil, tempfile, io

def mkbuild(buildername, src, out, doctree, confoverrides=None, freshenv=True):
    from sphinx.application import Sphinx
    app = Sphinx(src, src, out, doctree, buildername,
                 confoverrides=confoverrides or {}, status=None,
                 warning=io.StringIO(), freshenv=freshenv)
    app.build()
    return app

root = None
for base in ["/testbed", os.getcwd()]:
    p = os.path.join(base, "tests/roots/test-ext-viewcode")
    if os.path.isdir(p):
        root = p; break
if root is None:
    print("NO_TESTROOT"); sys.exit(2)
tmp = tempfile.mkdtemp(prefix="vc_")
src = os.path.join(tmp, "src"); shutil.copytree(root, src)
dt = os.path.join(tmp, "doctrees")

# 1) html build populates the shared env
ah = mkbuild("html", src, os.path.join(tmp, "html"), dt)
nmod = len(getattr(ah.builder.env, "_viewcode_modules", {}))
# 2) epub build reuses the shared doctree env (freshenv=False)
oute = os.path.join(tmp, "epub")
ae = mkbuild("epub", src, oute, dt, freshenv=False)
nmod2 = len(getattr(ae.builder.env, "_viewcode_modules", {}))

modpage = os.path.join(oute, "_modules", "spam", "mod1.xhtml")
exists = os.path.exists(modpage)
print("html env modules =", nmod, "; epub env modules =", nmod2)
print("epub default (shared env): mod1.xhtml exists =", exists)
sys.exit(1 if exists else 0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8721: collect_pages in sphinx/ext/viewcode.py must gate module-page emission on the builder name (suppress epub-family unless viewcode_enable_epub, suppress singlehtml) mirroring the doctree_read gate.

KEY REPRODUCTION INSIGHT: a fresh standalone epub build never triggers the bug because base doctree_read already gates epub, leaving env._viewcode_modules empty, so collect_pages has nothing to emit and the criterion holds trivially at base. The reported bug ('make html epub') only manifests when a prior HTML build populates the SHARED doctree env; the epub build then reuses that env (freshenv=False) and collect_pages emits pages. probe_1 and probe_3 use this shared-env scenario, matching how the upstream FAIL_TO_PASS test (SphinxTestApp shared doctree dir) reproduces it.

### PROBES (all HOLD on gold-patched tree; runner re-runs):
- probe_1 (Req 1.1/1.2, POSITIVE CONTROL): shared-env html->epub, default config => no _modules/spam/mod1.xhtml. VIOLATED at base (mod1.xhtml written), HOLDS patched. Discriminates.
- probe_2 (Req 2.2): epub build with viewcode_enable_epub=True => mod1.xhtml IS written. HOLDS patched.
- probe_3 (Req 3.1): shared-env html->singlehtml => no _modules/spam/mod1.html and no _modules/index.html. HOLDS patched.
- probe_4 (Req 4.1): plain html build => mod1.html, mod2.html and _modules/index.html all written. HOLDS patched.
- probe_5 (Req 4.3 regression): plain html => mod1.html contains viewcode-back [docs] anchor to spam.Class1 and index.html has 2 back-refs to mod1#func1 (upstream assertions). HOLDS patched.
- probe_6 (Req 4.2 regression): after deleting env._viewcode_modules, collect_pages yields 0 pages (early return preserved). HOLDS patched.

### CANDIDATE PATCHES (both apply at base, both REJECTED by the suite => suite discriminates wrong fixes; neither is a too-weak finding):
- weak_partial.diff: gates only singlehtml, forgets epub. REJECTED by probe_1 (VIOLATED: epub mod1.xhtml written). Would fail FAIL_TO_PASS test_viewcode_epub_default.
- weak_ignore_config.diff: gates singlehtml AND epub but IGNORES viewcode_enable_epub (suppresses epub unconditionally). REJECTED by probe_2 (VIOLATED: enabled epub produces no page); HOLDS probe_1. Would fail PASS_TO_PASS test_viewcode_epub_enabled.

No requirements-conforming alternative patch found that fails the hidden tests: the requirements pin the exact three-way builder-name gate (epub-prefix+config, singlehtml, else emit), which coincides with the gold fix. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed observable behavior (which builders yield pages vs an empty sequence in html-collect-pages/collect_pages), not a narrow slice or helper — correct modeling boundary. Req 1.1 uses startswith("epub") matching the patch's family prefix (verified epub3 also suppressed). No mandated behavior absent from the code, none forbidden that the code has, nothing invented beyond the issue/fix. Probes run in the instance image on the gold-patched tree.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document uses only real Sphinx API/identifier names (collect_pages, html-collect-pages, doctree_read, viewcode_enable_epub, singlehtml, epub builder prefix) to localize the change — all legitimate. No hidden-test content is transmitted: no test file path (tests/test_ext_viewcode.py), no test function names (test_viewcode_epub_default/_enabled), no FAIL_TO_PASS/PASS_TO_PASS ids, and no quoted gold or test code. The concrete test artifact path _modules/spam/mod1.xhtml is NOT reproduced — the doc stays generic ('viewcode module-output directory', 'per-module page'). The epub/viewcode_enable_epub/make-html-epub behavior is already public in the problem_statement. The singlehtml suppression is gold-edit behavior described as a behavioral requirement with a real builder name; notably there is no singlehtml test, so it cannot mirror test parametrization. Requirements cover full behavioral space (epub-off/epub-on/singlehtml/plain-HTML), broader than and shaped independently of the two hidden tests. No fix-invented identifiers (the gold patch invents nothing). NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
