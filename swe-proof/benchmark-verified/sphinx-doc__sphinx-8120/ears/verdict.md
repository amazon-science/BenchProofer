# P2 adversarial audit — sphinx-doc__sphinx-8120

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_override.py`, `probe_2_output.py`, `probe_3_fallback.py`, `probe_4_nobuiltin.py`, `probe_5_init_sentinel.py`, `probe_6_countrycode.py`, `probe_7_nolang.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_override.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_override.py` → holds on the patched tree (good)

```python
"""Req1.1 (POSITIVE CONTROL): a user-configured catalog that redefines a
built-in system message wins over the bundled translation after init.
Holds on patched tree; must FAIL at base (bundled 'Schnellsuche' wins)."""
import os, sys, tempfile, shutil
from babel.messages import pofile
from babel.messages.catalog import Catalog
from sphinx import locale
from sphinx.application import Sphinx

work = tempfile.mkdtemp(prefix="sbu_probe1_")
try:
    src = os.path.join(work, "src")
    os.makedirs(src)
    open(os.path.join(src, "conf.py"), "w").write(
        "project='p'\nlanguage='de'\nlocale_dirs=['locales']\n"
        "gettext_auto_build=True\nmaster_doc='index'\n")
    open(os.path.join(src, "index.rst"), "w").write("Title\n=====\n\nhi\n")
    ld = os.path.join(src, "locales", "de", "LC_MESSAGES")
    os.makedirs(ld)
    cat = Catalog()
    cat.add("Quick search", "QUICK SEARCH")
    with open(os.path.join(ld, "sphinx.po"), "wb") as f:
        pofile.write_po(f, cat)

    locale.translators.clear()
    app = Sphinx(src, src, os.path.join(work, "out"),
                 os.path.join(work, "dt"), "html",
                 status=None, warning=sys.stderr)
    got = app.translator.gettext("Quick search")
    print("gettext('Quick search') =", repr(got))
    print("mo exists:", os.path.exists(os.path.join(ld, "sphinx.mo")))
    ok = got == "QUICK SEARCH"
    sys.exit(0 if ok else 1)
finally:
    locale.translators.clear()
    shutil.rmtree(work, ignore_errors=True)
```

Attack 2 — `probe_2_output.py` → holds on the patched tree (good)

```python
"""Req1.2: with an overriding project catalog, built HTML output contains the
project-supplied translation of the overridden system message."""
import os, sys, tempfile, shutil
from babel.messages import pofile
from babel.messages.catalog import Catalog
from sphinx import locale
from sphinx.application import Sphinx

work = tempfile.mkdtemp(prefix="sbu_probe2_")
try:
    src = os.path.join(work, "src")
    os.makedirs(src)
    open(os.path.join(src, "conf.py"), "w").write(
        "project='p'\nlanguage='de'\nlocale_dirs=['locales']\n"
        "gettext_auto_build=True\nmaster_doc='index'\n")
    open(os.path.join(src, "index.rst"), "w").write("Title\n=====\n\nhi\n")
    ld = os.path.join(src, "locales", "de", "LC_MESSAGES")
    os.makedirs(ld)
    cat = Catalog()
    cat.add("Quick search", "QUICK SEARCH")
    with open(os.path.join(ld, "sphinx.po"), "wb") as f:
        pofile.write_po(f, cat)
    locale.translators.clear()
    out = os.path.join(work, "out")
    app = Sphinx(src, src, out, os.path.join(work, "dt"), "html",
                 status=None, warning=sys.stderr)
    app.build()
    html = open(os.path.join(out, "index.html")).read()
    present = "QUICK SEARCH" in html
    print("QUICK SEARCH in output:", present)
    sys.exit(0 if present else 1)
finally:
    locale.translators.clear()
    shutil.rmtree(work, ignore_errors=True)
```

Attack 3 — `probe_3_fallback.py` → holds on the patched tree (good)

```python
"""Req1.4 / Req2.1: a message absent from the user catalog still falls back to
the bundled built-in translation, while the overridden one uses the user value.
User 'de' catalog defines only 'Quick search'; 'Fig. %s' must remain the
bundled German 'Abb. %s'."""
import os, sys, tempfile, shutil
from babel.messages import pofile
from babel.messages.catalog import Catalog
from sphinx import locale
from sphinx.application import Sphinx

work = tempfile.mkdtemp(prefix="sbu_probe3_")
try:
    src = os.path.join(work, "src")
    os.makedirs(src)
    open(os.path.join(src, "conf.py"), "w").write(
        "project='p'\nlanguage='de'\nlocale_dirs=['locales']\n"
        "gettext_auto_build=True\nmaster_doc='index'\n")
    open(os.path.join(src, "index.rst"), "w").write("Title\n=====\n\nhi\n")
    ld = os.path.join(src, "locales", "de", "LC_MESSAGES")
    os.makedirs(ld)
    cat = Catalog()
    cat.add("Quick search", "QUICK SEARCH")   # only overrides this one
    with open(os.path.join(ld, "sphinx.po"), "wb") as f:
        pofile.write_po(f, cat)
    locale.translators.clear()
    app = Sphinx(src, src, os.path.join(work, "out"),
                 os.path.join(work, "dt"), "html", status=None, warning=sys.stderr)
    over = app.translator.gettext("Quick search")
    fig = app.translator.gettext("Fig. %s")
    listing = app.translator.gettext("Listing %s")
    print("override 'Quick search' ->", repr(over))
    print("fallback 'Fig. %s' ->", repr(fig))
    print("fallback 'Listing %s' ->", repr(listing))
    ok = (over == "QUICK SEARCH" and fig == "Abb. %s" and listing == "Quellcode %s")
    sys.exit(0 if ok else 1)
finally:
    locale.translators.clear()
    shutil.rmtree(work, ignore_errors=True)
```

Attack 4 — `probe_4_nobuiltin.py` → holds on the patched tree (good)

```python
"""Req2.1 / Req2.2: with NO overriding user catalog, the translator returns the
bundled built-in 'de' translations exactly as before (bundled must still be
searched)."""
import os, sys, tempfile, shutil
from sphinx import locale
from sphinx.application import Sphinx

work = tempfile.mkdtemp(prefix="sbu_probe4_")
try:
    src = os.path.join(work, "src")
    os.makedirs(src)
    open(os.path.join(src, "conf.py"), "w").write(
        "project='p'\nlanguage='de'\nmaster_doc='index'\n")
    open(os.path.join(src, "index.rst"), "w").write("Title\n=====\n\nhi\n")
    locale.translators.clear()
    app = Sphinx(src, src, os.path.join(work, "out"),
                 os.path.join(work, "dt"), "html", status=None, warning=sys.stderr)
    qs = app.translator.gettext("Quick search")
    fig = app.translator.gettext("Fig. %s")
    print("'Quick search' ->", repr(qs))
    print("'Fig. %s' ->", repr(fig))
    ok = (qs == "Schnellsuche" and fig == "Abb. %s")
    sys.exit(0 if ok else 1)
finally:
    locale.translators.clear()
    shutil.rmtree(work, ignore_errors=True)
```

Attack 5 — `probe_5_init_sentinel.py` → holds on the patched tree (good)

```python
"""Req4.1/4.3 + Req2.4: locale.init accepts a search list mixing the None
system-default sentinel, a nonexistent dir, and the bundled locale dir in any
order; skips locations with no catalog without raising; reports
has_translation True for a language with bundled translations ('de')."""
import os, sys
import gettext as _g
from sphinx import locale

pkg = os.path.join(os.path.dirname(__import__('sphinx').__file__), 'locale')
locale.translators.clear()
# order: None sentinel first, then a nonexistent dir, then bundled -> should
# skip missing and load bundled de.
dirs = [None, "/nonexistent/path/xyz", pkg]
translator, has = locale.init(dirs, "de")
val = translator.gettext("Quick search")
print("has_translation:", has)
print("'Quick search' ->", repr(val))

# Req4.3 also: a list of only-missing locations must not raise and report False
locale.translators.clear()
tr2, has2 = locale.init(["/nope/a", "/nope/b"], "de")
print("all-missing has_translation:", has2)

ok = (has is True and val == "Schnellsuche" and has2 is False)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_countrycode.py` → holds on the patched tree (good)

```python
"""Req2.3: for a language with a country-code variant (de_AT), the loader still
searches the base language 'de', so bundled German translations are found."""
import os, sys
from sphinx import locale
pkg = os.path.join(os.path.dirname(__import__('sphinx').__file__), 'locale')
locale.translators.clear()
translator, has = locale.init([None, pkg], "de_AT")
val = translator.gettext("Quick search")
print("de_AT has_translation:", has, "'Quick search' ->", repr(val))
ok = (has is True and val == "Schnellsuche")
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7_nolang.py` → holds on the patched tree (good)

```python
"""Req4.2: when no language is configured, init still installs a translator and
does not fail (returns a NullTranslations-like translator, has_translation
False)."""
import sys
from sphinx import locale
locale.translators.clear()
translator, has = locale.init([None], None)
print("translator is not None:", translator is not None)
print("has_translation:", has)
# gettext must be callable and passthrough
val = translator.gettext("Quick search")
print("passthrough gettext ->", repr(val))
ok = (translator is not None and has is False and val == "Quick search")
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_override.py`

```python
"""Req1.1 (POSITIVE CONTROL): a user-configured catalog that redefines a
built-in system message wins over the bundled translation after init.
Holds on patched tree; must FAIL at base (bundled 'Schnellsuche' wins)."""
import os, sys, tempfile, shutil
from babel.messages import pofile
from babel.messages.catalog import Catalog
from sphinx import locale
from sphinx.application import Sphinx

work = tempfile.mkdtemp(prefix="sbu_probe1_")
try:
    src = os.path.join(work, "src")
    os.makedirs(src)
    open(os.path.join(src, "conf.py"), "w").write(
        "project='p'\nlanguage='de'\nlocale_dirs=['locales']\n"
        "gettext_auto_build=True\nmaster_doc='index'\n")
    open(os.path.join(src, "index.rst"), "w").write("Title\n=====\n\nhi\n")
    ld = os.path.join(src, "locales", "de", "LC_MESSAGES")
    os.makedirs(ld)
    cat = Catalog()
    cat.add("Quick search", "QUICK SEARCH")
    with open(os.path.join(ld, "sphinx.po"), "wb") as f:
        pofile.write_po(f, cat)

    locale.translators.clear()
    app = Sphinx(src, src, os.path.join(work, "out"),
                 os.path.join(work, "dt"), "html",
                 status=None, warning=sys.stderr)
    got = app.translator.gettext("Quick search")
    print("gettext('Quick search') =", repr(got))
    print("mo exists:", os.path.exists(os.path.join(ld, "sphinx.mo")))
    ok = got == "QUICK SEARCH"
    sys.exit(0 if ok else 1)
finally:
    locale.translators.clear()
    shutil.rmtree(work, ignore_errors=True)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8120: user-configured message catalogs must override bundled built-in translations. Gold fix reorders the catalog search list in Sphinx._init_i18n from [None, bundled, *user_dirs] to [None, *user_dirs, bundled] (the locale/__init__.py hunk is only a type-annotation change).

Probe suite (7, all HOLD on gold-patched tree):
- probe_1_override.py (POSITIVE CONTROL, Req1.1): user 'de' sphinx.po redefining 'Quick search'->'QUICK SEARCH'; app.translator.gettext returns the user value. HOLDS patched, VIOLATED at base (base returns bundled 'Schnellsuche'). Discriminates.
- probe_2_output.py (Req1.2): built index.html contains 'QUICK SEARCH'. HOLDS.
- probe_3_fallback.py (Req1.4/2.1): user catalog overrides only 'Quick search'; 'Fig. %s'->'Abb. %s' and 'Listing %s'->'Quellcode %s' still fall back to bundled German. HOLDS.
- probe_4_nobuiltin.py (Req2.1/2.2): no user catalog -> bundled 'Schnellsuche'/'Abb. %s' returned as before. HOLDS.
- probe_5_init_sentinel.py (Req4.1/4.3/2.4): locale.init accepts [None, missing_dir, bundled] mixing sentinel+missing, skips missing without raising, reports has_translation True for de; all-missing list -> False. HOLDS.
- probe_6_countrycode.py (Req2.3): de_AT still searches base 'de'. HOLDS.
- probe_7_nolang.py (Req4.2): language None -> translator installed, no failure, passthrough gettext, has_translation False. HOLDS.

Candidate wrong patches (both REJECTED by the suite, demonstrating discrimination):
- weak.diff (cosmetic type-annotation hunk only, no reorder): probe_1 VIOLATED ('Schnellsuche'), probe_2 VIOLATED (output lacks 'QUICK SEARCH'). Rejected.
- weak2.diff (user dirs placed before bundled BUT bundled dir dropped entirely): probe_1 HOLDS but probe_3 VIOLATED (no fallback) and probe_4 VIOLATED (returns untranslated 'Quick search'). Rejected -- catches the too-weak reading that ignores the 'keep built-in' requirements.

Env: sphinx 3.3.0 image; runs used the swebench-lean conda python. All runs completed (no INCONCLUSIVE).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1_override.py`, `probe_2_output.py`, `probe_3_fallback.py`, `probe_4_nobuiltin.py`, `probe_5_init_sentinel.py`, `probe_6_countrycode.py`, `probe_7_nolang.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_override.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_override.py` → holds on the patched tree (good)

Attack 2 — `probe_2_output.py` → holds on the patched tree (good)

Attack 3 — `probe_3_fallback.py` → holds on the patched tree (good)

Attack 4 — `probe_4_nobuiltin.py` → holds on the patched tree (good)

Attack 5 — `probe_5_init_sentinel.py` → holds on the patched tree (good)

Attack 6 — `probe_6_countrycode.py` → holds on the patched tree (good)

Attack 7 — `probe_7_nolang.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_override.py`

```python
"""Req1.1 (POSITIVE CONTROL): a user-configured catalog that redefines a
built-in system message wins over the bundled translation after init.
Holds on patched tree; must FAIL at base (bundled 'Schnellsuche' wins)."""
import os, sys, tempfile, shutil
from babel.messages import pofile
from babel.messages.catalog import Catalog
from sphinx import locale
from sphinx.application import Sphinx

work = tempfile.mkdtemp(prefix="sbu_probe1_")
try:
    src = os.path.join(work, "src")
    os.makedirs(src)
    open(os.path.join(src, "conf.py"), "w").write(
        "project='p'\nlanguage='de'\nlocale_dirs=['locales']\n"
        "gettext_auto_build=True\nmaster_doc='index'\n")
    open(os.path.join(src, "index.rst"), "w").write("Title\n=====\n\nhi\n")
    ld = os.path.join(src, "locales", "de", "LC_MESSAGES")
    os.makedirs(ld)
    cat = Catalog()
    cat.add("Quick search", "QUICK SEARCH")
    with open(os.path.join(ld, "sphinx.po"), "wb") as f:
        pofile.write_po(f, cat)

    locale.translators.clear()
    app = Sphinx(src, src, os.path.join(work, "out"),
                 os.path.join(work, "dt"), "html",
                 status=None, warning=sys.stderr)
    got = app.translator.gettext("Quick search")
    print("gettext('Quick search') =", repr(got))
    print("mo exists:", os.path.exists(os.path.join(ld, "sphinx.mo")))
    ok = got == "QUICK SEARCH"
    sys.exit(0 if ok else 1)
finally:
    locale.translators.clear()
    shutil.rmtree(work, ignore_errors=True)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-8120: user-configured message catalogs must override bundled built-in translations. Gold fix reorders the catalog search list in Sphinx._init_i18n from [None, bundled, *user_dirs] to [None, *user_dirs, bundled] (the locale/__init__.py hunk is only a type-annotation change).

Probe suite (7, all HOLD on gold-patched tree):
- probe_1_override.py (POSITIVE CONTROL, Req1.1): user 'de' sphinx.po redefining 'Quick search'->'QUICK SEARCH'; app.translator.gettext returns the user value. HOLDS patched, VIOLATED at base (base returns bundled 'Schnellsuche'). Discriminates.
- probe_2_output.py (Req1.2): built index.html contains 'QUICK SEARCH'. HOLDS.
- probe_3_fallback.py (Req1.4/2.1): user catalog overrides only 'Quick search'; 'Fig. %s'->'Abb. %s' and 'Listing %s'->'Quellcode %s' still fall back to bundled German. HOLDS.
- probe_4_nobuiltin.py (Req2.1/2.2): no user catalog -> bundled 'Schnellsuche'/'Abb. %s' returned as before. HOLDS.
- probe_5_init_sentinel.py (Req4.1/4.3/2.4): locale.init accepts [None, missing_dir, bundled] mixing sentinel+missing, skips missing without raising, reports has_translation True for de; all-missing list -> False. HOLDS.
- probe_6_countrycode.py (Req2.3): de_AT still searches base 'de'. HOLDS.
- probe_7_nolang.py (Req4.2): language None -> translator installed, no failure, passthrough gettext, has_translation False. HOLDS.

Candidate wrong patches (both REJECTED by the suite, demonstrating discrimination):
- weak.diff (cosmetic type-annotation hunk only, no reorder): probe_1 VIOLATED ('Schnellsuche'), probe_2 VIOLATED (output lacks 'QUICK SEARCH'). Rejected.
- weak2.diff (user dirs placed before bundled BUT bundled dir dropped entirely): probe_1 HOLDS but probe_3 VIOLATED (no fallback) and probe_4 VIOLATED (returns untranslated 'Quick search'). Rejected -- catches the too-weak reading that ignores the 'keep built-in' requirements.

Env: sphinx 3.3.0 image; runs used the swebench-lean conda python. All runs completed (no INCONCLUSIVE).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed gold-patched image: locale.init source unchanged except signature type; _init_i18n now builds [None] + repo.locale_dirs + [package_dir/locale]. Base commit shows old ordering. F2P=test_customize_system_message aligns with R1. Requirement boundary is the observable ordering change and its precedence/fallback consequences — correctly modeled.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the reordering fix behaviorally: user-configured catalog locations must precede the bundled built-in defaults, with the system-default sentinel first; auto-compile of an out-of-date user sphinx.po→sphinx.mo continues; init accepts the system-default sentinel among search locations. All module/function names cited (Sphinx._init_i18n in application.py, locale.init in locale/__init__.py, CatalogRepository, locale_dirs, sphinx.po/sphinx.mo, gettext_auto_build) are legitimate localization and largely public via the problem_statement. NONE of the hidden-test specifics leak: no test name (test_customize_system_message), path (tests/test_intl.py), the test language 'de', the override string 'Quick search', or expected value 'QUICK SEARCH'; no quoted test/gold code; no fix-invented identifiers (gold only reorders a list and widens a type hint to Optional[str], both described as behavior not code). The only test-adjacent detail is line 6's mention of 'search-box labels' as an example category of system messages, whereas the problem_statement's examples are figure/listing captions ('Fig. %s'/'Listing %s'); this names a well-known Sphinx message category, not the string/language/expected value, and cannot reconstruct the test — a soft hint at most, not gold/test reconstruction. Requirement enumerations mirror the fix's behavior (precedence, fallback, sentinel handling), not the single parametrized test case.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
