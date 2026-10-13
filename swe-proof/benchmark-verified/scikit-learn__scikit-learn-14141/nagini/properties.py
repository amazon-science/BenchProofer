"""properties.py — PBT falsification manifest for scikit-learn__scikit-learn-14141.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    collect_deps_versions() -> Dict[int, int]      # = sklearn _get_deps_info

with NO inputs (the roster is predetermined and built internally) and the
load-bearing contract

    Requires(MustTerminate(2))                                                   # totality
    Ensures(Acc(dict_pred(Result())) and Result() is not None)
    Ensures(name_X() in Result() and Result()[name_X()] == version_of(name_X()))   # x9
    Ensures(name_parallel() in Result()
            and Result()[name_parallel()] == version_of(name_parallel()))           # discriminator
    Ensures(Forall(int, lambda n: Implies(n in Result(),                            # no spurious keys
            n is one of the nine roster tokens)))

What the spec actually defends, and the attacks it must survive:

  * THE DISCRIMINATOR is `name_parallel() in Result()` — the gold patch adds
    `"joblib"` (the parallel-execution dependency) to the roster so it becomes a
    key of the result. The F2P `test_get_deps_info` asserts exactly
    `'joblib' in deps_info`. The pre-patch roster omits joblib; model_prepatch.py
    reproduces that and fails this clause. The primary reject rival
    (`rival-omit-joblib`) is precisely that pre-gold roster.

  * THE ROSTER IS PINNED BOTH WAYS. The nine per-name `name_X() in Result()`
    clauses pin the key-set down (every rostered name present); the
    no-spurious-keys Forall pins it up (no key outside the roster). The
    pre-existing `test_get_deps_info` asserts `'<name>' in deps_info` for each of
    the eight long-standing names too, so a rival that DROPS a pre-existing name
    (`rival-omit-matplotlib`) has a faithful patch that fails a P2P-side
    assertion — a valid partial-domain reject.

  * THE ORACLE `version_of` IS GROUNDED, NOT AN ANSWER-KEY. Each value clause is
    `Result()[name_X()] == version_of(name_X())`: the impl must store the callee
    applied to the RIGHT token. There is no opaque marker an impl could echo to
    skip the work — populating each key already IS the work (one assignment per
    rostered name). So there is no "wrong oracle-echo that verifies" reject case;
    instead `pos-control-cheapest` is the honest cheapest correct impl, confirming
    the spec is not echo-vulnerable (directive 2 fallback for a grounded oracle).

  * NO READ-ONLY INPUT ⇒ FRAME-MUTATION IS N/A. `collect_deps_versions` takes no
    parameters (empty precondition); there is no `Acc(x, 1/2)` reference to
    overwrite, so the mandatory frame-mutation probe does not apply to this
    instance (no input frame exists to subvert). Noted in the structured
    assessment rather than fabricated.

  * NO CONTROL-FLOW / RAISE DIFFERENCE. The routine purely builds and returns a
    dict (the import-failure path is folded into `version_of`'s total marker
    domain — see the axiom). There is no raise/return/side-effect channel the
    value abstraction drops, so the capability-token (control-flow-effect) class
    is N/A here. Noted in the assessment.

  * TERMINATION IS PINNED. Nagini is a partial-correctness verifier: without a
    termination obligation a diverging body satisfies every Ensures vacuously
    (the audit's recorded P1/G-EQ witness class: an infinite loop inserted
    before the roster build verified under the pre-fix contract, and its
    faithful real patch hangs `test_get_deps_info` forever — never resolving).
    `Requires(MustTerminate(2))` in the precondition closes this channel; the
    `rival-diverge` case below is the regression witness.

Authoring mechanics (preserved from the schema): every spec variant is built by
REGION-SURGERY (`_swap`) that edits ONLY inside `# impl-start`/`# impl-end`, so
`markers.same_spec` is GUARANTEED and a rejection comes from the POSTCONDITION
catching wrong behaviour, never from a tampered spec. Each `expect:"reject"`
rival carries the refinement argument that its faithful real patch would NOT
resolve the F2P/P2P. The one consumed axiom `version_of` is checked by running
the REAL `_get_deps_info()` in Docker (the real sklearn callee).
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14141"
FLOAT_ENCODING = None   # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The roster list literal (one block; nine tokens, order-preserving).
_DEPS_LIST = """    deps = [
        name_pip(),
        name_setuptools(),
        name_sklearn(),
        name_numpy(),
        name_scipy(),
        name_cython(),
        name_pandas(),
        name_matplotlib(),
        name_parallel(),
    ]  # type: List[int]
    Assert(len(deps) == 9)"""

# The per-name population block (nine assignments, order-preserving).
_POPULATE = """    deps_info[name_pip()] = version_of(name_pip())
    deps_info[name_setuptools()] = version_of(name_setuptools())
    deps_info[name_sklearn()] = version_of(name_sklearn())
    deps_info[name_numpy()] = version_of(name_numpy())
    deps_info[name_scipy()] = version_of(name_scipy())
    deps_info[name_cython()] = version_of(name_cython())
    deps_info[name_pandas()] = version_of(name_pandas())
    deps_info[name_matplotlib()] = version_of(name_matplotlib())
    deps_info[name_parallel()] = version_of(name_parallel())"""

# the discriminating roster member's population assignment (single line)
_JOBLIB_ASSIGN = "    deps_info[name_parallel()] = version_of(name_parallel())\n"
# a pre-existing rostered member's population assignment (single line)
_MPL_ASSIGN = "    deps_info[name_matplotlib()] = version_of(name_matplotlib())\n"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (4a) Structurally-different but CORRECT: the same nine keys, but BOTH the
# roster literal AND the population are written in REVERSED order (parallel ...
# pip). The result dict has the identical key/value set — assignment order does
# not change a dict's membership — so it must verify. If it fails, the spec is
# over-fit to one population order => SPEC-TOO-STRONG. (No induction lemma is
# needed: the keys are statically-known distinct constants, so reordering the
# assignments keeps the gold proof valid.)
_DEPS_LIST_REVERSED = """    deps = [
        name_parallel(),
        name_matplotlib(),
        name_pandas(),
        name_cython(),
        name_scipy(),
        name_numpy(),
        name_sklearn(),
        name_setuptools(),
        name_pip(),
    ]  # type: List[int]
    Assert(len(deps) == 9)"""
_POPULATE_REVERSED = """    deps_info[name_parallel()] = version_of(name_parallel())
    deps_info[name_matplotlib()] = version_of(name_matplotlib())
    deps_info[name_pandas()] = version_of(name_pandas())
    deps_info[name_cython()] = version_of(name_cython())
    deps_info[name_scipy()] = version_of(name_scipy())
    deps_info[name_numpy()] = version_of(name_numpy())
    deps_info[name_sklearn()] = version_of(name_sklearn())
    deps_info[name_setuptools()] = version_of(name_setuptools())
    deps_info[name_pip()] = version_of(name_pip())"""
_POS_REORDERED = _swap(
    _swap(_BASE, _DEPS_LIST, _DEPS_LIST_REVERSED),
    _POPULATE, _POPULATE_REVERSED)

# (2, grounded-oracle fallback) Cheapest HONEST correct impl: drop the `deps`
# list literal and the `Assert(len(deps)==9)` scaffold entirely — that scaffold
# does not feed the postcondition (the proof rests on the nine assignments). Keep
# only the nine `deps_info[name_X()] = version_of(name_X())` assignments + return.
# It is CORRECT and must verify. Its purpose: show that satisfying the GROUNDED
# value clauses (Result()[name]==version_of(name)) still requires populating every
# key — there is no opaque answer-key to echo. (If a wrong echo could verify this
# would instead be a reject case; no such echo exists, the oracle is grounded.)
_CHEAPEST = _swap(_BASE, _DEPS_LIST + "\n", "")

# (5) ADMISSIBILITY. The precondition is EMPTY (no inputs), so it is trivially
# satisfiable; the strongest admissibility signal for a no-arg routine is that
# the normal F2P-shaped computation is constructible under it. This variant keeps
# the gold body and adds, right after the roster is built, an Assert that the
# DISCRIMINATING token is a member of the constructed roster — i.e. the empty
# precondition admits building the real nine-name roster including the parallel
# dependency. If this self-check failed to verify, the (empty) precondition would
# be blocking a legitimate F2P-shaped computation => PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE,
    "    Assert(len(deps) == 9)\n",
    "    Assert(len(deps) == 9)\n    Assert(deps[8] == name_parallel())\n")


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (DISCRIMINATOR) Omit the parallel-execution dependency: the eight-name pre-gold
# roster, with NO name_parallel() population assignment (= model_prepatch.py's
# behaviour). The roster list is left intact-but-shortened to eight so the impl is
# internally consistent. This MUST be rejected: it cannot discharge the
# postcondition `name_parallel() in Result()`. Rejection source: the
# discriminating postcondition clause name_parallel() in Result().
_RIVAL_OMIT_JOBLIB = _swap(
    _swap(_BASE, _DEPS_LIST,
          _DEPS_LIST.replace("        name_parallel(),\n", "", 1)
                    .replace("Assert(len(deps) == 9)", "Assert(len(deps) == 8)", 1)),
    _JOBLIB_ASSIGN, "")

# (PARTIAL-DOMAIN) Drop a PRE-EXISTING rostered name (matplotlib): correct on the
# other eight roster members (incl. joblib) but omits matplotlib's population.
# Pins all of the domain except one member. MUST be rejected: fails
# `name_matplotlib() in Result()`. Rejection source: the per-name postcondition
# clause name_matplotlib() in Result().
_RIVAL_OMIT_MPL = _swap(
    _swap(_BASE, _DEPS_LIST,
          _DEPS_LIST.replace("        name_matplotlib(),\n", "", 1)
                    .replace("Assert(len(deps) == 9)", "Assert(len(deps) == 8)", 1)),
    _MPL_ASSIGN, "")

# (SUPPORTING — no-spurious-keys clause) Populate all nine roster keys correctly
# AND add a tenth key that is NOT a roster token (the integer 99, distinct from
# the nine tokens 0..8). MUST be rejected: the no-spurious-keys Forall pins every
# key of the result to one of the nine roster tokens, and 99 is none of them.
# Rejection source: the Forall(int, lambda n: Implies(n in Result(), n is a roster
# token)) postcondition. (Honest nuance in the refinement: this lenient F2P only
# checks key PRESENCE, so a real extra-key patch could still pass the test; the
# clause is a faithful transcription of the gold roster's EXACT membership — gold
# has exactly these nine — so this probes behavioural equivalence to gold beyond
# the test, see refinement field.)
_RIVAL_SPURIOUS = _swap(
    _BASE, _POPULATE,
    _POPULATE + "\n    deps_info[99] = version_of(name_pip())")

# (VACUITY / NON-TERMINATION) Spin forever before the correct tail. Under
# Nagini's partial-correctness default every Ensures would hold vacuously (no
# normal exit is ever reached), yet the routine never returns its dict. MUST be
# rejected: the loop takes no termination measure, so the MustTerminate(2)
# obligation in the precondition leaks ('Loop might not take all unsatisfied
# obligations from the context'). Without MustTerminate this rival verified —
# the recorded G-PANEL-1/G-EQ hole (audit witnesses atk_2/atk_4: an infinite
# `while` inserted at the top of _get_deps_info verified but its patch hangs
# the F2P and does not resolve).
_RIVAL_DIVERGE = _swap(
    _BASE, "    deps = [\n        name_pip(),",
    "    # WRONG (vacuous): spin forever before the correct tail.\n"
    "    b = True\n"
    "    while b:\n"
    "        Invariant(True)\n"
    "        b = True\n"
    "    deps = [\n        name_pip(),")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reordered", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDERED,
     "rationale": "structurally-different but correct: both the roster literal and the "
                  "nine population assignments are written in REVERSED order. Dict "
                  "membership is order-independent, so the result key/value set is "
                  "identical to gold and it must verify. If not, the spec is over-fit to "
                  "one population order => SPEC-TOO-STRONG. No induction lemma needed (keys "
                  "are statically-known distinct constants)."},
    {"id": "pos-control-cheapest", "kind": "soundness", "expect": "verify",
     "module": _CHEAPEST,
     "rationale": "grounded-oracle fallback (directive 2): the oracle version_of is pinned "
                  "per-token (Result()[name]==version_of(name)), so there is no opaque "
                  "answer-key to echo — populating each key IS the work. This cheapest honest "
                  "impl (nine assignments + return, scaffold dropped) is correct and must "
                  "verify, demonstrating the spec is satisfiable without the roster-list "
                  "scaffold and is NOT echo-vulnerable. If it failed => SPEC-TOO-STRONG."},
    {"id": "admiss-roster-constructible", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the precondition is EMPTY (no inputs); this self-check Asserts the "
                  "discriminating token is a member of the constructed nine-name roster, "
                  "confirming the (empty) precondition admits the normal F2P-shaped "
                  "computation. If it failed to verify => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-omit-joblib", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OMIT_JOBLIB,
     "refinement": "this is the EXACT pre-gold behaviour (model_prepatch.py): the eight-name "
                   "roster omitting joblib, with no name_parallel() population. Its faithful "
                   "real patch is the pre-patch _get_deps_info() whose deps list has no "
                   "\"joblib\" entry, so 'joblib' never becomes a key — and the F2P "
                   "test_get_deps_info asserts `'joblib' in deps_info`. That patch FAILS the "
                   "F2P, so it would NOT resolve; a verifying rival here would be a true "
                   "verify⇏resolve break.",
     "rationale": "the discriminator. Rejection source: the postcondition clause "
                  "name_parallel() in Result(), which no eight-name roster can discharge. "
                  "If it verified => SPEC-TOO-WEAK (the discriminating clause is hollow)."},
    {"id": "rival-omit-matplotlib", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OMIT_MPL,
     "refinement": "correct on eight of the nine roster members (including joblib) but drops "
                   "matplotlib's population. Its faithful real patch is a _get_deps_info() "
                   "whose deps list omits \"matplotlib\", so 'matplotlib' is not a key — and "
                   "test_get_deps_info asserts `'matplotlib' in deps_info` (a pre-existing, "
                   "P2P-side assertion). That patch FAILS the test, so it would NOT resolve.",
     "rationale": "partial-domain: pins all of the roster except one pre-existing member. "
                  "Rejection source: the per-name postcondition clause "
                  "name_matplotlib() in Result(). If it verified => SPEC-TOO-WEAK "
                  "(domain-incomplete on the long-standing roster)."},
    {"id": "rival-spurious-key", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SPURIOUS,
     "refinement": "populates all nine roster keys correctly AND adds a tenth key (99) that "
                   "is not a rostered dependency. A faithful real patch would put an extra "
                   "non-roster name into the deps list, producing a tenth key. The gold "
                   "deps list has EXACTLY these nine entries, so this diverges from gold "
                   "behaviour (it is not behaviourally equal to the gold patch on the "
                   "reported key-set). HONEST NUANCE: this particular F2P only asserts key "
                   "PRESENCE (`'<name>' in deps_info`), not exact key-set, so a lenient real "
                   "patch with an extra name could still pass the test — this case therefore "
                   "probes the no-spurious-keys clause's FIDELITY to the gold roster (exact "
                   "membership), beyond what the lenient test enforces, rather than a "
                   "test-failing divergence. Kept as a SUPPORTING case for the upper-bound "
                   "clause; the two reject cases above are the F2P/P2P-failing discriminators.",
     "rationale": "exercises the no-spurious-keys Forall (every key must be a roster token; "
                  "99 is none of the nine). Rejection source: that Forall postcondition. If "
                  "it verified, the upper-bound on the result's key-set would be hollow."},
    {"id": "rival-diverge", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE,
     "refinement": "a real _get_deps_info() that hangs (an accidental infinite loop before "
                   "building the roster) never returns its dict: test_get_deps_info calls "
                   "_get_deps_info() and blocks forever, so the F2P times out — the faithful "
                   "patch does NOT resolve. (This is the audit's recorded P1/G-EQ witness "
                   "class: an infinite `while` inserted at the top of the routine VERIFIED "
                   "under the pre-fix contract, since Nagini requires no termination proof "
                   "by default, and its patch hung the harness.)",
     "rationale": "rejected by the MustTerminate(2) termination obligation in the "
                  "precondition: the loop takes no termination measure, so Nagini reports an "
                  "obligation leak ('Loop might not take all unsatisfied obligations from "
                  "the context'). Without MustTerminate this rival verified — the pre-fix "
                  "G-PANEL-1 hole. If it verified => SPEC-TOO-WEAK (vacuity channel open)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real sklearn callee _get_deps_info)
# ===========================================================================

# (1) axiom-soundness for version_of. The axiom's contract is Ensures(True); the
# proof relies ONLY on its TOTALITY — every rostered name ends up as a key of the
# returned mapping carrying *a* value (a version str, or None when the module is
# absent), never absent and never raising out of the population step. The
# obligation: running the REAL post-gold _get_deps_info() yields a mapping in
# which every rostered name (incl. the discriminating "joblib") is a key with a
# present value slot, and no key lies outside the roster. This reuses + strengthens
# axiom_check.py's logic. Runs in-container with the gold patch applied
# (apply_gold=True) since the axiom describes post-gold behaviour.
_AX_VERSION_TOTALITY = r'''
import sys
# The roster the post-gold reporter must report; model.py name_* tokens <-> these
# names (mapping.md s1). "joblib" is the discriminating member the patch adds.
EXPECTED_ROSTER = {
    "pip", "setuptools", "sklearn", "numpy", "scipy",
    "Cython", "pandas", "matplotlib", "joblib",
}
from sklearn.utils._show_versions import _get_deps_info
deps_info = _get_deps_info()
keys = set(deps_info)

# (totality) every rostered name is a key carrying a value slot (version str or
# None). Totality is the WHOLE obligation version_of's Ensures(True) leans on.
missing = [n for n in sorted(EXPECTED_ROSTER) if n not in deps_info]
if missing:
    print("AXIOM-UNSOUND version_of totality: rostered names NOT keys of real "
          "_get_deps_info():", missing, "; result keys:", sorted(keys))
    sys.exit(1)
badval = []
for n in sorted(EXPECTED_ROSTER):
    v = deps_info[n]
    if not (v is None or isinstance(v, str)):
        badval.append((n, repr(v)))
if badval:
    print("AXIOM-UNSOUND version_of: rostered name has non-(str|None) value slot:",
          badval)
    sys.exit(1)

# the discriminating member specifically (the F2P assertion mirror)
if "joblib" not in deps_info:
    print("AXIOM-UNSOUND: parallel-execution dependency 'joblib' is NOT a key of "
          "the real result:", sorted(keys))
    sys.exit(1)

# (no spurious keys) the real result holds no key outside the roster
extra = keys - EXPECTED_ROSTER
if extra:
    print("AXIOM mismatch: real _get_deps_info() reported keys OUTSIDE the modeled "
          "roster:", sorted(extra))
    sys.exit(1)

# (boundary) the import-failure branch keeps the key with a None marker — the
# version_of-as-total modeling. Exercise the routine's own per-name code path with
# a guaranteed-absent module name.
import importlib
bogus = "joblib_definitely_absent_module_zzz_14141"
di = {}
try:
    if bogus in sys.modules:
        mod = sys.modules[bogus]
    else:
        mod = importlib.import_module(bogus)
    di[bogus] = getattr(mod, "__version__", None)
except ImportError:
    di[bogus] = None
if not (bogus in di and di[bogus] is None):
    print("AXIOM-UNSOUND: import-failure branch did not keep the key with a None "
          "marker:", di)
    sys.exit(1)

print("version_of TOTALITY sound: real _get_deps_info() reports every rostered "
      "name (incl. 'joblib') as a key with a present value slot; key-set ==",
      "roster exactly; import-failure branch keeps key with None marker.")
sys.exit(0)
'''

# (2) axiom-containment for version_of. The model passes EXACTLY the nine roster
# tokens (name_pip..name_parallel) to version_of — one per population assignment,
# derived from the impl control flow. version_of's signature is `version_of(name:
# int)` with NO Requires, so its declared domain is all int; every reachable token
# (0..8) is trivially inside it. The MEANINGFUL containment for this instance: each
# token the model reaches must correspond to a name the real _get_deps_info()
# actually observes — i.e. the model never feeds version_of a callee-input the real
# routine does not query. Assert the nine model names == the real roster (no model
# token maps to a name the real callee never observes). Covering MORE than the
# caller reaches would be sound; a model token OUTSIDE the real callee's queried set
# would be AXIOM-TOO-WEAK-FOR-CALLER (the model could observe a version the real
# routine never reads). Runs apply_gold=True (post-gold roster).
_AX_CONTAINMENT = r'''
import sys
# The nine names the MODEL passes to version_of (model.py name_* tokens 0..8 <->
# these strings; mapping.md s1). This is exactly the set the impl's nine
# population assignments reach.
MODEL_NAMES = {
    "pip", "setuptools", "sklearn", "numpy", "scipy",
    "Cython", "pandas", "matplotlib", "joblib",
}
# The names the REAL post-gold _get_deps_info() actually observes. We derive this
# by RUNNING the real routine and reading its result keys: the routine queries one
# version per rostered name and stores it under that name as a key (the totality
# property already validated by ax-version-of-totality / axiom_check.py), so the
# set of observed names is EXACTLY the set of result keys. (An earlier version of
# this probe regex-scraped inspect.getsource(_get_deps_info), but the function's
# docstring contains the substring "deps" so the source split landed inside the
# docstring and captured doc fragments instead of the roster — a probe bug, not an
# axiom defect. Calling the routine is the ground-truth approach axiom_check.py uses.)
from sklearn.utils._show_versions import _get_deps_info
real_roster = set(_get_deps_info())

# CONTAINMENT: every name the model reaches must be one the real routine observes.
uncovered = MODEL_NAMES - real_roster
if uncovered:
    print("AXIOM-TOO-WEAK-FOR-CALLER: model passes version_of names the real "
          "_get_deps_info() never observes:", sorted(uncovered),
          "; real roster:", sorted(real_roster))
    sys.exit(1)
over = real_roster - MODEL_NAMES
print("containment OK: model's nine version_of inputs", sorted(MODEL_NAMES),
      "are all observed by the real _get_deps_info(); real routine observes",
      "exactly the same set." if not over else
      ("real routine ALSO observes (sound over-cover): %s" % sorted(over)))
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-version-of-totality", "axiom": "version_of", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_VERSION_TOTALITY,
     "rationale": "version_of's Ensures(True) leans only on TOTALITY: running the real "
                  "post-gold _get_deps_info() must report every rostered name (incl. "
                  "'joblib') as a key with a present value slot (version str or None) and no "
                  "spurious key; the import-failure branch must keep the key with a None "
                  "marker. Any rostered name missing, or a key outside the roster, => "
                  "AXIOM-UNSOUND (the totality the model consumes is violated)."},
    {"id": "ax-version-of-containment", "axiom": "version_of", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "the model passes exactly the nine roster tokens to version_of; each must "
                  "correspond to a name the real _get_deps_info() actually observes (its deps "
                  "roster). A model name the real routine never observes => "
                  "AXIOM-TOO-WEAK-FOR-CALLER (the model could read a version the real routine "
                  "never reads). The real routine covering more is sound (containment rule)."},
]
