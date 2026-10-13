"""PBT falsification battery for django__django-14315.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TESTS entry is a full model.py variant built by region-surgery -- ONLY the
text inside a `# impl-start`/`# impl-end` block is edited, so the frozen spec
(axioms / pure / pre / post-conditions + signatures) is byte-identical and
`same_spec` holds. Each AXIOM_TESTS entry is a self-contained stdlib-only probe
the runner executes in the instance Docker image.

Defended surface (two modeled functions, both with READ-ONLY inputs):

  normalized_environment(env: Dict[int,int]) -> Optional[Dict[int,int]]
      Requires Acc(dict_pred(env), 1/2)  -- env is READ-ONLY.
      Pins: len(env)==0 -> Result() is None;  len(env)>0 -> Result() is env
      (object identity -- the SAME mapping, not a copy).

  effective_environment(env: Optional[Dict[int,int]], base: Dict[int,int])
                        -> Optional[Dict[int,int]]
      Requires Acc(env,1/2) (when env is not None) and Acc(base,1/2) -- BOTH
      inputs READ-ONLY.
      Pins: env is None -> None;  env empty -> None;  env non-empty ->
      (Result() is not None) AND the merge semantics (env wins on a shared key;
      base carried through where env does not override). Calls the env_merge
      axiom (@ContractOnly) on the non-empty path.

The load-bearing clauses: (a) the empty/None -> None normalisation at BOTH
sites (the exact behaviour the gold patch adds; the bug the prepatch leaves), and
(b) the env-wins / base-carried merge value clauses. There is NO @Pure
answer-key oracle (the normalisation/merge is spelled out in the impl), and the
non-empty result is pinned by object identity (normalized_environment) or by the
input-grounded value Foralls (effective_environment) -- so there is no opaque
oracle to echo; the uniqueness attacks below instead exploit (i) read-only
permission, (ii) the None-ness partial domain, (iii) merge direction, and
(iv) key invention (closed by the exported no-spurious-keys clause on
effective_environment).
"""
from pathlib import Path

INSTANCE = "django__django-14315"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact impl-region text of the two functions (unique substrings of model.py).
# Edits are confined to these blocks => same_spec is guaranteed.
# ---------------------------------------------------------------------------
_NORM_IMPL = (
    "    if len(env) == 0:\n"
    "        return None\n"
    "    return env\n"
)

_EFF_IMPL = (
    "    if env is None:\n"
    "        return None\n"
    "    if len(env) == 0:\n"
    "        return None\n"
    "    merged = env_merge(base, env)\n"
    "    return merged\n"
)


# ---------------------------------------------------------------------------
# SPEC_TESTS
# ---------------------------------------------------------------------------
SPEC_TESTS = []

# --- 1. FRAME-MUTATION on normalized_environment (read-only env) ------------
# env is held at Acc(dict_pred(env), 1/2): READ-ONLY. A rival that WRITES to it
# needs full permission and must be rejected for INSUFFICIENT PERMISSION. The
# gold None-ness / identity clauses are kept verbatim so the rejection is
# attributable to the write, not to a value mismatch.
SPEC_TESTS.append({
    "id": "frame-mut-normalized-write-env",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _NORM_IMPL,
        "    env[0] = 0\n"
        "    if len(env) == 0:\n"
        "        return None\n"
        "    return env\n",
    ),
    "refinement": (
        "The gold patch is `return args, (env or None)`: it reports the env "
        "mapping unchanged. A patch that MUTATES the built env dict before "
        "reporting it would corrupt the command's environment (and, since the "
        "same object flows into runshell, the env handed to subprocess.run). "
        "test_basic / test_nopass / test_parameters assert the returned env "
        "exactly equals the expected mapping (or None); an injected key 0 makes "
        "those equalities fail, so the faithful mutating patch does NOT resolve."),
    "rationale": (
        "Rejected by the permission system: writing env[0] needs full "
        "Acc(dict_pred(env)) but the precondition grants only 1/2. A byte-fuzzer "
        "never tries to mutate a read-only input; this is the project's #1 class."),
})

# --- 2. FRAME-MUTATION on effective_environment (read-only base = os.environ)
# base models os.environ and is held at Acc(dict_pred(base), 1/2): READ-ONLY.
# A rival that writes into base before merging must be rejected for insufficient
# permission. Gold control flow + merge kept verbatim.
SPEC_TESTS.append({
    "id": "frame-mut-effective-write-base",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _EFF_IMPL,
        "    if env is None:\n"
        "        return None\n"
        "    if len(env) == 0:\n"
        "        return None\n"
        "    base[0] = 0\n"
        "    merged = env_merge(base, env)\n"
        "    return merged\n",
    ),
    "refinement": (
        "base models os.environ; the gold expression `{**os.environ, **env}` "
        "builds a FRESH dict and never mutates os.environ in place. A patch that "
        "wrote into os.environ would persistently inject a bogus variable into "
        "the parent process environment, corrupting every later subprocess and "
        "the test harness's own environment -- the dbshell F2P tests assert the "
        "exact env passed to subprocess.run, which an injected key 0 breaks, so "
        "the mutating patch does NOT resolve."),
    "rationale": (
        "Rejected by the permission system: base[0]=0 needs full "
        "Acc(dict_pred(base)) but only 1/2 is held. Frame condition / "
        "fractional permission -- the mandatory read-only-input attack."),
})

# --- 3. FRAME-MUTATION on effective_environment (read-only env) -------------
# env (Optional) is held at Acc(...,1/2) on the non-None branch: also READ-ONLY.
SPEC_TESTS.append({
    "id": "frame-mut-effective-write-env",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _EFF_IMPL,
        "    if env is None:\n"
        "        return None\n"
        "    env[0] = 0\n"
        "    if len(env) == 0:\n"
        "        return None\n"
        "    merged = env_merge(base, env)\n"
        "    return merged\n",
    ),
    "refinement": (
        "The gold `{**os.environ, **env}` reads env, never writes it. The env "
        "object is the very dict settings_to_cmd_args_env built; mutating it here "
        "would alter the command's reported environment. The dbshell F2P tests "
        "assert the exact env mapping, which the injected key breaks -- the "
        "mutating patch does NOT resolve."),
    "rationale": (
        "Rejected by the permission system: env[0]=0 needs full Acc(dict_pred(env)) "
        "but the non-None branch holds only 1/2. Frame-mutation on the optional "
        "read-only input."),
})

# --- 4. PARTIAL-DOMAIN: drop the empty->None normalisation (the actual bug) -
# This is exactly model_prepatch's defect: an empty (non-None) command mapping
# is sent through the merge instead of normalised to None. It is correct on the
# None and non-empty sub-domains but WRONG on env=={}.
SPEC_TESTS.append({
    "id": "partial-domain-effective-empty-not-normalised",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _EFF_IMPL,
        "    if env is None:\n"
        "        return None\n"
        "    merged = env_merge(base, env)\n"
        "    return merged\n",
    ),
    "refinement": (
        "This is the pre-patch behaviour the gold fixes: `if env: env = "
        "{**os.environ, **env}` left an empty {} unchanged, so the subprocess "
        "received an empty/merged environment instead of inheriting os.environ "
        "(env=None). test_runshell_use_environ asserts subprocess.run is called "
        "with env=None for env in {None, {}}; an empty mapping flowing into the "
        "merge yields a non-None dict, so the faithful patch does NOT resolve "
        "(this is the G-DIFF prepatch defect)."),
    "rationale": (
        "Rejected by the postcondition Implies(env is not None and len(env)==0, "
        "Result() is None): env_merge Ensures Result() is not None, contradicting "
        "the required None on the empty branch."),
})

# --- 5. PARTIAL-DOMAIN: drop the empty->None at site 2 (normalized_environment)
# Returns the empty mapping verbatim instead of None -- model_prepatch_2's bug.
SPEC_TESTS.append({
    "id": "partial-domain-normalized-empty-not-none",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _NORM_IMPL,
        "    return env\n",
    ),
    "refinement": (
        "Pre-patch site 2 (`return args, env`) returned the empty {} dict; the "
        "gold `return args, (env or None)` normalises it to None. test_nopass / "
        "test_parameters assert the returned env element equals None (not {}); "
        "returning the empty mapping verbatim makes those equalities fail, so the "
        "faithful patch does NOT resolve (the G-DIFF model_prepatch_2 defect)."),
    "rationale": (
        "Rejected by the postcondition Implies(len(env)==0, Result() is None): "
        "the empty input must map to None, but `return env` returns {} (not None)."),
})

# --- 6. UNIQUENESS: swapped merge direction (base wins instead of env) ------
# Returns env_merge(env, base) -- the WRONG unpack order ({**env, **os.environ}),
# so os.environ overrides the command's variables on a shared key.
SPEC_TESTS.append({
    "id": "uniqueness-effective-swapped-merge",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, "    merged = env_merge(base, env)\n",
        "    merged = env_merge(env, base)\n",
    ),
    "refinement": (
        "The gold is `{**os.environ, **env}` -- the command env wins on a shared "
        "key. Swapping to `{**env, **os.environ}` lets an inherited os.environ "
        "value clobber a PG* variable the client just set (e.g. PGPASSWORD, "
        "PGHOST). The dbshell F2P tests (test_basic, test_nopass, test_passfile, "
        "test_service, ...) assert the exact env dict passed to subprocess.run, "
        "where the PG* values must come from the connection settings -- the "
        "swapped merge gives os.environ's value instead, so the patch does NOT "
        "resolve."),
    "rationale": (
        "Rejected by Implies(k in env, Result()[k]==env[k]): with the swapped "
        "merge the axiom only guarantees Result()[k]==base[k] on a shared key, "
        "which the verifier cannot reconcile with the required env[k]."),
})

# --- 7. UNIQUENESS (supporting): inject a spurious key into the merge -------
# A near-miss with a real refinement: add a key the result has no business
# holding. The spec SHOULD reject it -- the universally-quantified env-wins
# clause forces Result()[k]==env[k] for EVERY env including one containing key 0,
# which contradicts the hard-coded 0 -> 0 write.
SPEC_TESTS.append({
    "id": "uniqueness-effective-spurious-key",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE,
        "    merged = env_merge(base, env)\n"
        "    return merged\n",
        "    merged = env_merge(base, env)\n"
        "    merged[0] = 0\n"
        "    return merged\n",
    ),
    "refinement": (
        "The gold merge `{**os.environ, **env}` never invents a key absent from "
        "both inputs. Injecting key 0->0 would hand the subprocess a bogus env "
        "variable; the dbshell F2P tests assert the exact env dict, so the "
        "faithful patch does NOT resolve. (Supporting near-miss: it also collides "
        "with any input where 0 is a real env key with a different value.)"),
    "rationale": (
        "Rejected twice over: by Implies(k in env, Result()[k]==env[k]) "
        "quantified over ALL envs (for an env where 0 maps to a value != 0, the "
        "hard write 0->0 violates the required value), and by the exported "
        "no-spurious-keys clause Implies(k in Result(), (k in env) or (k in "
        "base)) for inputs where 0 is in neither mapping."),
})

# --- 8. POSITIVE CONTROL (soundness): normalized_environment, branch reorder
# Structurally different (test the positive predicate first), behaviourally
# identical. Must verify (else SPEC-TOO-STRONG). No framing lemma is needed --
# the postcondition is two independent Implies, both still discharged.
SPEC_TESTS.append({
    "id": "pos-control-normalized-reordered",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _NORM_IMPL,
        "    if len(env) > 0:\n"
        "        return env\n"
        "    return None\n",
    ),
    "rationale": (
        "A correct, structurally-different impl (non-empty branch first) must "
        "verify; the two postcondition Implies clauses hold on each branch with "
        "no extra lemma. If it failed, the spec would be too strong."),
})

# --- 9. POSITIVE CONTROL (soundness): effective_environment, merged guard ---
# Collapse the two early returns into a single disjunctive guard; same behaviour,
# same env_merge call. Must verify.
SPEC_TESTS.append({
    "id": "pos-control-effective-disjunctive-guard",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _EFF_IMPL,
        "    if env is None or len(env) == 0:\n"
        "        return None\n"
        "    merged = env_merge(base, env)\n"
        "    return merged\n",
    ),
    "rationale": (
        "A correct restructure (the None and empty guards fused with `or`) keeps "
        "the same merge on the non-empty path and must verify; the disjunction "
        "discharges the env-None and empty None-ness clauses together. If it "
        "failed, the spec / proof would be too strong for a faithful variant."),
})

# --- 10. ADMISSIBILITY: the preconditions accept a normal F2P-shaped input --
# The only preconditions are permission accesses (Acc(...,1/2)); there is no
# value-domain Requires that could over-constrain a legitimate input. This case
# keeps the gold control flow and adds a tautological value assertion that is
# discharged ONLY if the precondition grants enough to read len(env) on the
# non-empty path -- confirming the Requires admits a normal non-empty mapping
# (the dbshell shape) all the way through the merge. Must verify.
SPEC_TESTS.append({
    "id": "admiss-effective-normal-input",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE, _EFF_IMPL,
        "    if env is None:\n"
        "        return None\n"
        "    if len(env) == 0:\n"
        "        return None\n"
        "    Assert(len(env) > 0)\n"
        "    merged = env_merge(base, env)\n"
        "    return merged\n",
    ),
    "rationale": (
        "Admissibility: on the merge path the precondition must grant read access "
        "to env (Acc(...,1/2)) so that len(env) is observable and > 0; the "
        "Assert is discharged from the preceding guards under the Requires. If the "
        "precondition were too strong (e.g. unsatisfiable for a non-empty mapping) "
        "this normal F2P-shaped input would not verify => PRECOND-TOO-STRONG."),
})


# ---------------------------------------------------------------------------
# AXIOM_TESTS -- env_merge is the one @ContractOnly axiom (A-consumed).
# No flag_dependency / provenance config: it is PEP 448 dict-unpacking, which is
# configuration-independent, so the probe runs the real `{**base, **overlay}`
# directly. (The two A-reference deep models -- normalized_environment and
# effective_environment -- are validated by axiom_check.py / G-AX, not re-probed
# here; they are not @ContractOnly axioms.)
# ---------------------------------------------------------------------------
AXIOM_TESTS = []

# --- axiom-soundness: real {**base, **overlay} meets every env_merge Ensures
AXIOM_TESTS.append({
    "id": "ax-sound-env-merge",
    "axiom": "env_merge",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": r'''
import random, sys

def check(base, overlay):
    base_len, overlay_len = len(base), len(overlay)
    result = {**base, **overlay}                       # the REAL callee
    # Ensures: fresh non-empty result whenever an input is non-empty
    if base_len > 0 or overlay_len > 0:
        assert result, "unsound: empty merge of %r,%r" % (base, overlay)
    # Ensures: Result() is not None
    assert result is not None, "unsound: None result"
    # Ensures: every key of overlay present with overlay's value (overlay wins)
    for k, v in overlay.items():
        assert k in result and result[k] == v, (
            "unsound: overlay key %r->%r lost in %r" % (k, v, result))
    # Ensures: every base key not overridden keeps base's value
    for k, v in base.items():
        if k not in overlay:
            assert k in result and result[k] == v, (
                "unsound: base key %r->%r lost in %r" % (k, v, result))
    # Ensures: no spurious keys
    for k in result:
        assert k in base or k in overlay, (
            "unsound: spurious key %r in %r" % (k, result))
    # Ensures: inputs unmutated (lengths preserved -- {**a,**b} builds anew)
    assert len(base) == base_len and len(overlay) == overlay_len, (
        "unsound: input mutated")

# boundary pairs (empty/empty, disjoint, shared-key override, identical)
boundary = [
    ({}, {}), ({}, {1: 1}), ({1: 1}, {}),
    ({1: 1}, {1: 2}),                       # overlay wins on shared key
    ({1: 100, 2: 200, 3: 300}, {2: 999}),   # partial override
    ({1: 100, 2: 200, 3: 300}, {4: 4, 5: 5}),  # disjoint
    ({1: 1, 2: 2}, {1: 1, 2: 2}),           # identical
]
for b, o in boundary:
    check(b, o)

# randomized fuzz over the axiom Requires domain (any two int->int dicts)
rng = random.Random(14315)
def rmap():
    n = rng.randint(0, 6)
    return {rng.randrange(12): rng.randrange(100) for _ in range(n)}
for _ in range(20000):
    check(rmap(), rmap())

print("ax-sound-env-merge OK: real {**base,**overlay} meets every env_merge "
      "Ensures on %d boundary + 20000 fuzz pairs (inputs unmutated)." % len(boundary))
sys.exit(0)
''',
    "rationale": (
        "If the real PEP 448 merge violated any Ensures (overlay-wins, "
        "base-carried, no-spurious, fresh-non-empty, inputs-unmutated) the "
        "env_merge axiom would be AXIOM-UNSOUND. The merge is config-independent "
        "(no flag_dependency), so the host Python merge is faithful to Docker."),
})

# --- axiom-containment: every callee-input effective_environment can reach
# lies inside env_merge's Requires domain.
AXIOM_TESTS.append({
    "id": "ax-cover-env-merge",
    "axiom": "env_merge",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": r'''
import random, sys

# env_merge's Requires domain: Acc(dict_pred(base),1/2) and
# Acc(dict_pred(overlay),1/2) -- ANY two int->int dicts (no value/shape
# restriction). The MODEL calls env_merge(base, env) at exactly ONE site, on the
# control-flow path `env is not None and len(env) > 0`. So the reachable
# callee-inputs are: base = any Dict[int,int]; overlay = env = any NON-EMPTY
# Dict[int,int]. Containment holds iff every such pair is a valid env_merge input.
# Since the axiom domain is "any pair of dicts", the caller-reachable subset
# (any base, non-empty overlay) is strictly contained -- covering MORE (incl. the
# empty-overlay case the caller never reaches) is sound, not a defect.

def in_domain(d):
    # a valid env_merge operand: a dict usable in {**d, ...} (the dict_pred
    # carrier). Exercise it to confirm.
    try:
        _ = {**d}
        return isinstance(d, dict)
    except Exception:
        return False

def reachable_overlays():
    # the model only reaches env_merge with a NON-EMPTY env (the len(env)>0 guard)
    rng = random.Random(143150)
    yield {1: 1}
    yield {1: 10, 2: 20}
    yield {5: 0}
    for _ in range(5000):
        n = rng.randint(1, 6)          # >=1: non-empty, per the guard
        yield {rng.randrange(12): rng.randrange(100) for _ in range(n)}

def reachable_bases():
    rng = random.Random(143151)
    yield {}                            # os.environ may, in principle, be empty
    yield {1: 100}
    yield {1: 100, 2: 200, 3: 300}
    for _ in range(5000):
        n = rng.randint(0, 6)
        yield {rng.randrange(12): rng.randrange(100) for _ in range(n)}

bad = 0
# every reachable overlay (non-empty) is in-domain
for o in reachable_overlays():
    assert len(o) > 0, "model only reaches env_merge with non-empty env"
    if not in_domain(o):
        bad += 1
# every reachable base is in-domain
for b in reachable_bases():
    if not in_domain(b):
        bad += 1
# no reachable callee-input lies outside the axiom Requires domain
assert bad == 0, "AXIOM-TOO-WEAK-FOR-CALLER: %d reachable inputs outside domain" % bad

print("ax-cover-env-merge OK: every caller-reachable env_merge input (any base, "
      "non-empty overlay) lies inside the axiom Requires domain (any two dicts); "
      "the axiom covers a strict superset (sound).")
sys.exit(0)
''',
    "rationale": (
        "Containment: the model calls env_merge only on the len(env)>0 path, so "
        "overlay is always non-empty and base is any dict -- both inside the "
        "axiom's 'any two dicts' domain. A reachable input OUTSIDE the domain "
        "would be AXIOM-TOO-WEAK-FOR-CALLER; there is none."),
})
