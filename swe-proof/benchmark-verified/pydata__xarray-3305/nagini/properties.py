"""PBT manifest for pydata__xarray-3305 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (region-surgery: only
the text strictly inside an `# impl-start` / `# impl-end` region is edited) and
swap the implementation; they are checked by Nagini verify + markers.same_spec.
Axiom cases are real-callee probes run in the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md / instance):

  Two modeled functions over a metadata-keep selection (xarray quantile keep_attrs):

    * reduce_result_metadata(self_meta: List[int], keep_metadata: Optional[bool])
        site 1 (Variable.quantile). self_meta is the source attribute payload;
        keep_metadata is the three-valued keep flag (None = unspecified).
        Pre : Acc(list_pred(self_meta), 1/2)            <- self_meta is READ-ONLY
        Post: Acc(list_pred(self_meta), 1/2)            (returns the read perm)
              Acc(list_pred(Result()))                  (full perm on result)
              ToSeq(Result()) == selected_meta(ToSeq(self_meta),
                                                resolve_keep(keep_metadata))
        LOAD-BEARING clause: the last Ensures. selected_meta(src, keep) is a
        fully-unfolded @Pure deep model:  keep -> src ;  not keep -> empty.
        resolve_keep(keep) is None -> ambient_keep_default() ; else keep.
        So when the flag resolves True the result must be a COPY of self_meta,
        and when it resolves False (incl. None under the default config) it must
        be EMPTY. The oracle is GROUNDED in the inputs (a pure function of
        self_meta + the flag), fully unfolded — there is NO opaque answer-key to
        echo, so the directive-2 "ungrounded-oracle echo" attack does not apply
        (an honest cheapest-impl positive control replaces it; see assessment).

    * entrypoint_reduce_metadata(self_meta, keep_metadata)
        site 2 (Dataset.quantile per-variable delegation). Same spec; its impl
        forwards the flag UNCHANGED to site 1. The discriminating content is the
        forwarding: the pre-patch bug dropped the flag (forwarded None).

  Read-only inputs: self_meta in BOTH functions is Acc(list_pred(.), 1/2).
  => the FRAME-MUTATION probe is MANDATORY (a rival that WRITES self_meta to
  satisfy the postcondition by side effect must be REJECTED for insufficient
  permission).

Axiom lane: one @ContractOnly axiom `ambient_keep_default` (A-consumed),
  @Pure, NO Requires (unconditional domain), Ensures(Result() == False). It
  stands for xarray.core.options._get_keep_attrs(default=False), consulted only
  on the keep_metadata is None branch, sound under OPTIONS["keep_attrs"]==
  "default" (the baseline every F2P/P2P runs under). axiom-soundness reuses the
  persisted axiom_check.py (real resolver == False under default config + the
  True/False boundary). axiom-containment is trivial: the axiom has no Requires
  (empty-precondition domain admits every call), so every model-reachable call
  site is in-domain — we make this concrete + confirm the only call site is
  resolve_keep's None branch.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3305"
FLOAT_ENCODING = None  # meta.json float_encoding is null (int code-point carrier)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each strictly INSIDE an impl region; editing keeps the spec).
# ---------------------------------------------------------------------------

# reduce_result_metadata (site 1) — the WHOLE impl body (gold).
_SITE1_BODY = (
    "    keep = keep_metadata\n"
    "    if keep is None:\n"
    "        keep = ambient_keep_default()\n"
    "    result = []  # type: List[int]\n"
    "    if keep:\n"
    "        result = list(self_meta)\n"
    "    return result"
)

# entrypoint_reduce_metadata (site 2) — the WHOLE impl body (gold).
_SITE2_BODY = (
    "    result = reduce_result_metadata(self_meta, keep_metadata)\n"
    "    return result"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): site 1, branch-reorder + early return ---
    # Structurally different (drop-branch early-returns an empty typed local; no
    # pre-initialized `result`; keep-branch falls through), behaviourally
    # identical: drop -> empty, keep -> a copy of self_meta. No loops/invariants
    # in the gold proof, so this reshape introduces no proof gap. The empty list
    # is bound to a TYPED LOCAL before return (Nagini `# type:` rule). MUST
    # verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-site1-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _SITE1_BODY,
            "    keep = keep_metadata\n"
            "    if keep is None:\n"
            "        keep = ambient_keep_default()\n"
            "    if not keep:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    result = list(self_meta)\n"
            "    return result"),
        "rationale": "a correct impl with the keep/drop branches reordered (early "
                     "return on drop, fall-through copy on keep) is behaviourally "
                     "identical at every resolved-flag value and must verify "
                     "against the frozen postcondition (else SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): site 2, inline the delegation ----------
    # Drops the `result` temporary; the forwarding call is the same. MUST verify.
    {
        "id": "pos-site2-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _SITE2_BODY,
            "    return reduce_result_metadata(self_meta, keep_metadata)"),
        "rationale": "a behaviourally-identical reshape (inline the forwarding "
                     "call, drop the temporary) must verify (else SPEC-TOO-STRONG).",
    },

    # -- ADMISSIBILITY: the precondition admits a normal F2P-shaped input -----
    # The forwarding call site IS the admissibility witness: entrypoint holds
    # Acc(list_pred(self_meta),1/2) and reduce_result_metadata Requires exactly
    # that. This variant additionally Asserts the half-permission is in hand at
    # the call site (a no-op for a verifying spec) before the gold forwarding. If
    # the Requires could not be established for a legitimate caller, the Assert /
    # call would fail => PRECOND-TOO-STRONG. It verifies, so the precondition is
    # satisfiable by an in-domain caller threading a 1/2 permission through.
    {
        "id": "admiss-site2-precond",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _SITE2_BODY,
            "    Assert(Acc(list_pred(self_meta), 1 / 2))\n"
            "    result = reduce_result_metadata(self_meta, keep_metadata)\n"
            "    return result"),
        "rationale": "entrypoint's own Requires (Acc(list_pred(self_meta),1/2)) "
                     "establishes site 1's Requires at the forwarding call; the "
                     "Assert confirms the half-permission is in hand for a normal "
                     "input and the self-call verifies (else PRECOND-TOO-STRONG).",
    },

    # -- FRAME-MUTATION (uniqueness): write the read-only self_meta -----------
    # MANDATORY: self_meta is Acc(list_pred(self_meta),1/2) — READ-ONLY. This
    # rival appends to self_meta inside the keep branch (only 1/2 permission held)
    # while keeping the gold copy. It must be REJECTED for INSUFFICIENT PERMISSION
    # (list.append needs the full list_pred). Gold logic otherwise verbatim, so
    # the rejection is attributable to the write, not a proof gap.
    {
        "id": "frame-mutate-self_meta",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SITE1_BODY,
            "    keep = keep_metadata\n"
            "    if keep is None:\n"
            "        keep = ambient_keep_default()\n"
            "    result = []  # type: List[int]\n"
            "    if keep:\n"
            "        self_meta.append(0)\n"
            "        result = list(self_meta)\n"
            "    return result"),
        "refinement": "the faithful real patch (mutating self._attrs of the source "
                      "Variable before copying) corrupts the caller's source object "
                      "in place; the gold patch copies (attrs = self._attrs) and "
                      "never mutates the source, and the P2P tests that re-read the "
                      "original attrs after a quantile would observe the corruption, "
                      "so such a patch would NOT resolve the suite.",
        "rationale": "rejected by the permission system: self_meta is held at "
                     "Acc(list_pred,1/2); `list.append` requires the full predicate, "
                     "so the write is INSUFFICIENT-PERMISSION. If it verified, the "
                     "read-only frame is unguarded (SPEC-TOO-WEAK).",
    },

    # -- FRAME-MUTATION supporting case: in-place index write -----------------
    # A different write shape on the same read-only input. self_meta[0] = ...
    # also needs the full list_pred. Guarded so it only runs when self_meta is
    # non-empty, keeping the gold value otherwise; the write itself is rejected.
    {
        "id": "frame-mutate-self_meta-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SITE1_BODY,
            "    keep = keep_metadata\n"
            "    if keep is None:\n"
            "        keep = ambient_keep_default()\n"
            "    if len(self_meta) > 0:\n"
            "        self_meta[0] = 0\n"
            "    result = []  # type: List[int]\n"
            "    if keep:\n"
            "        result = list(self_meta)\n"
            "    return result"),
        "refinement": "overwriting an entry of the source payload in place is not a "
                      "faithful keep_attrs fix — the gold patch reads self._attrs "
                      "without mutating it; a patch that rewrites the source would "
                      "change what the original object reports and fail the P2P "
                      "attribute-preservation expectations, so it would not resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: an in-place store to "
                     "self_meta needs the full list_pred but only 1/2 is held. "
                     "Frame integrity of the read-only source payload.",
    },

    # -- PARTIAL-DOMAIN (uniqueness): always KEEP (ignore the flag) -----------
    # `result = list(self_meta)` unconditionally. Correct on the resolved-keep
    # subdomain, WRONG on the resolved-drop subdomain (incl. keep_metadata=False
    # and the None-under-default path), where the postcondition requires empty.
    {
        "id": "partial-always-keep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SITE1_BODY,
            "    result = list(self_meta)\n"
            "    return result"),
        "refinement": "always copying the source attrs (attrs = self._attrs "
                      "unconditionally) honours keep_attrs=True but ignores "
                      "keep_attrs=False/None; the F2P test_quantile passes "
                      "keep_attrs=True (so it would pass) but the P2P "
                      "test_reduce_keep_attrs and the documented default "
                      "(keep_attrs=False -> no attrs) expect dropped attrs, so a "
                      "patch that always keeps would NOT resolve the suite.",
        "rationale": "rejected by ToSeq(Result()) == selected_meta(.., "
                     "resolve_keep(keep_metadata)): on the drop subdomain "
                     "selected_meta is empty but list(self_meta) is non-empty "
                     "whenever self_meta is non-empty. If it verified the drop "
                     "behaviour is unpinned (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): always DROP = the site-1 pre-patch bug ---
    # `result = []` always. This IS model_prepatch_1: the metadata is
    # unconditionally empty (return Variable(new_dims, qs) with attrs None).
    # Correct on the resolved-drop subdomain, WRONG when the flag resolves True.
    {
        "id": "partial-always-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SITE1_BODY,
            "    result = []  # type: List[int]\n"
            "    return result"),
        "refinement": "this IS the site-1 pre-patch behaviour (return Variable("
                      "new_dims, qs) — attrs unconditionally None); on the F2P "
                      "test_quantile with keep_attrs=True the result attrs are empty "
                      "instead of {'units':'K'}, so `assert actual.attrs == "
                      "self.attrs` fails — it is exactly the bug, does NOT resolve.",
        "rationale": "rejected by the load-bearing Ensures: when "
                     "resolve_keep(keep_metadata) is True selected_meta is a copy of "
                     "self_meta but the result is empty. model_prepatch_1.py fails "
                     "on this exact clause (G-DIFF).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): INVERTED flag ---------------------------
    # keep is honoured but inverted: copy on drop, empty on keep. Wrong on BOTH
    # the keep and the drop subdomains whenever self_meta is non-empty.
    {
        "id": "partial-inverted-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SITE1_BODY,
            "    keep = keep_metadata\n"
            "    if keep is None:\n"
            "        keep = ambient_keep_default()\n"
            "    result = []  # type: List[int]\n"
            "    if not keep:\n"
            "        result = list(self_meta)\n"
            "    return result"),
        "refinement": "inverting the flag (attrs = self._attrs if NOT keep_attrs) "
                      "drops attrs exactly when the user asked to keep them and "
                      "keeps them when asked to drop — the F2P keep_attrs=True case "
                      "loses the attrs (assert fails) and the default-drop P2P keeps "
                      "them; it would not resolve.",
        "rationale": "rejected by the load-bearing Ensures: selected_meta(.., keep) "
                     "and selected_meta(.., not keep) differ whenever self_meta is "
                     "non-empty. Partial-domain (both branches) divergence.",
    },

    # -- PARTIAL-DOMAIN (uniqueness): wrong None default (treat None as KEEP) --
    # The explicit True/False branches are correct; only the unspecified (None)
    # path is wrong — it keeps instead of consulting the ambient drop default.
    # Discriminates the consumed axiom's exact value: ambient_keep_default()==False.
    {
        "id": "partial-none-defaults-keep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SITE1_BODY,
            "    keep = keep_metadata\n"
            "    if keep is None:\n"
            "        keep = True\n"
            "    result = []  # type: List[int]\n"
            "    if keep:\n"
            "        result = list(self_meta)\n"
            "    return result"),
        "refinement": "defaulting the unspecified flag to keep (instead of "
                      "_get_keep_attrs(default=False) == False) reverses the "
                      "documented default: keep_attrs=None would keep attrs. The "
                      "default-drop behaviour is what the patch's docstring and the "
                      "P2P paths rely on; a patch that keeps by default would change "
                      "the default observable and not resolve.",
        "rationale": "rejected by ToSeq(Result()) == selected_meta(.., "
                     "resolve_keep(None)) where resolve_keep(None) == "
                     "ambient_keep_default() == False (the consumed axiom Ensures): "
                     "selected_meta(.., False) is empty but the impl returns a copy. "
                     "Partial-domain (None subdomain) divergence pinned by the axiom.",
    },

    # -- CONTROL-FLOW (uniqueness): site 2 DROPS the forwarded flag = bug 2 ----
    # entrypoint forwards None instead of keep_metadata. This IS model_prepatch_2
    # (the Dataset.quantile delegation omitting keep_attrs). Correct when the
    # caller's flag already resolves to drop; WRONG when the caller asked True.
    {
        "id": "site2-drops-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SITE2_BODY,
            "    result = reduce_result_metadata(self_meta, None)\n"
            "    return result"),
        "refinement": "this IS the site-2 pre-patch behaviour (var.quantile(q, "
                      "dim=reduce_dims, interpolation=interpolation) — keep_attrs not "
                      "forwarded, so the per-variable reduction received None and "
                      "resolved to drop). The F2P goes DataArray.quantile -> "
                      "Dataset.quantile -> Variable.quantile with keep_attrs=True; "
                      "if site 2 forwards None the attrs are dropped and `assert "
                      "actual.attrs == self.attrs` fails — exactly the bug, does NOT "
                      "resolve.",
        "rationale": "rejected by entrypoint's load-bearing Ensures: forwarding None "
                     "makes the result == selected_meta(.., resolve_keep(None)) == "
                     "empty, but the postcondition pins it to selected_meta(.., "
                     "resolve_keep(keep_metadata)) which is a copy when the caller's "
                     "keep_metadata is True. model_prepatch_2.py fails here (G-DIFF).",
    },
]


# ===========================================================================
# AXIOM LANE  (one @ContractOnly axiom: ambient_keep_default, A-consumed)
# ===========================================================================
#
# The runner mounts ONLY the probe script at /work; axiom_check.py / model.py are
# NOT in-container. The axiom-soundness probe therefore EMBEDS axiom_check.py's
# source (read on the HOST at manifest-load time) and EXECUTES the real callee
# xarray.core.options._get_keep_attrs(default=False) (and the e2e selection) —
# it never scrapes source. Files are opened utf-8-safe.

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# axiom-soundness: ambient_keep_default() == _get_keep_attrs(default=False) ==
# False under the default ambient config, plus the True/False boundary, plus the
# deep selection model == real Variable.quantile / DataArray.quantile. Reuses the
# persisted, gold-grounded axiom_check.py (apply_gold=True, since its e2e sections
# need the patched keep_attrs kwarg). exit 0 iff every obligation holds; the probe
# treats exit 2 (run-mode: gold not applied) as a harness error, not as "holds".
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# ---- PBT axiom-soundness driver (appended) --------------------------------
import sys as _sys
print("PBT axiom-soundness: running the real _get_keep_attrs(default=False) "
      "resolver (default config == False + True/False boundary) and the deep "
      "selection model vs real Variable.quantile / DataArray.quantile")
try:
    main()
    # main() calls sys.exit(); if it returns without exiting, treat as sound.
    _sys.exit(0)
except SystemExit as _e:
    _code = _e.code if isinstance(_e.code, int) else 1
    if _code == 0:
        _sys.exit(0)           # sound
    elif _code == 2:
        # run-mode: gold not applied (patched signature missing). The runner
        # invokes axiom probes with apply_gold=True, so this should not happen;
        # surface it as a failure rather than silently passing.
        print("PBT axiom-soundness FAIL: axiom_check.py exited 2 (run-mode: gold "
              "not applied). Expected apply_gold=True for the e2e sections.")
        _sys.exit(1)
    else:
        _sys.exit(1)           # real axiom/model violation
"""

# axiom-containment: ambient_keep_default has NO Requires (unconditional domain),
# so the callee-input domain is the whole space — every model-reachable call is
# trivially in-domain (covering MORE than the caller reaches is SOUND). We make
# the obligation concrete: (1) the model's only call to ambient_keep_default is on
# resolve_keep's `keep is None` branch (and the matching impl None branch), and
# (2) the real resolver is callable with NO arguments under the default config
# (no input precondition can be violated). Static + a real no-arg call; stdlib +
# xarray; utf-8-safe; reads nothing from disk.
_MODEL_SRC = (Path(__file__).parent / "model.py").read_text(encoding="utf-8")

_AX_COVER_PROBE = (
    "import sys, ast\n"
    "SRC = " + repr(_MODEL_SRC) + "\n"
    "tree = ast.parse(SRC)\n"
    "# 1) enumerate every call to ambient_keep_default and its enclosing fn.\n"
    "callers = {}\n"
    "for node in ast.walk(tree):\n"
    "    if isinstance(node, ast.FunctionDef):\n"
    "        callers[node.name] = node\n"
    "sites = []  # (enclosing_func, n_args)\n"
    "for fname, fnode in callers.items():\n"
    "    for sub in ast.walk(fnode):\n"
    "        if isinstance(sub, ast.Call) and getattr(sub.func, 'id', None) == 'ambient_keep_default':\n"
    "            sites.append((fname, len(sub.args)))\n"
    "print('ambient_keep_default call sites (caller, n_args):')\n"
    "for s in sites: print('  ', s)\n"
    "if not sites:\n"
    "    print('NO call sites found'); sys.exit(1)\n"
    "# 2) every call passes ZERO arguments (the axiom/callee is nullary) and the\n"
    "#    only callers are resolve_keep (the @Pure resolver, None branch) and\n"
    "#    reduce_result_metadata (the impl None branch). Any other caller / arity\n"
    "#    would reach the callee differently than modeled.\n"
    "bad_arity = [s for s in sites if s[1] != 0]\n"
    "if bad_arity:\n"
    "    print('ambient_keep_default called with arguments (axiom is nullary):', bad_arity); sys.exit(1)\n"
    "caller_set = set(f for f, _ in sites)\n"
    "expected = {'resolve_keep', 'reduce_result_metadata'}\n"
    "if caller_set - expected:\n"
    "    print('UNEXPECTED caller of ambient_keep_default:', caller_set - expected); sys.exit(1)\n"
    "# 3) the axiom has NO Requires (unconditional domain). Confirm the real\n"
    "#    resolver it stands for is callable with the supplied default under the\n"
    "#    default config (no input precondition to violate) and the call site is\n"
    "#    the None branch (drop default), matching resolve_keep's guard.\n"
    "import xarray as xr\n"
    "from xarray.core.options import _get_keep_attrs, OPTIONS\n"
    "assert OPTIONS['keep_attrs'] == 'default', ('unexpected baseline config: %r' % (OPTIONS['keep_attrs'],))\n"
    "v = _get_keep_attrs(default=False)\n"
    "if v is not False:\n"
    "    print('real resolver returned %r under default config (expected False)' % (v,)); sys.exit(1)\n"
    "print('AXIOM-CONTAINMENT OK: ambient_keep_default is nullary with NO Requires "
    "(unconditional domain); its only call sites are resolve_keep / "
    "reduce_result_metadata on the keep-is-None branch, each passing zero "
    "arguments. Every caller-reachable callee input is trivially inside the "
    "(empty-precondition) axiom domain, and the real _get_keep_attrs(default=False) "
    "is callable and returns False under the default config.')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-ambient_keep_default",
        "axiom": "ambient_keep_default",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the proof consumes ambient_keep_default()==False; the real "
                     "xarray.core.options._get_keep_attrs(default=False) must return "
                     "False under OPTIONS['keep_attrs']=='default' (the F2P/P2P "
                     "baseline), and the deep selection model must equal the real "
                     "Variable.quantile / DataArray.quantile. If the real resolver "
                     "returned anything but False under the default config the axiom "
                     "(and the None-branch proof) would be AXIOM-UNSOUND. Runs the "
                     "gold-grounded axiom_check.py in the instance image "
                     "(apply_gold=True for the post-patch e2e sections).",
    },
    {
        "id": "ax-cover-ambient_keep_default",
        "axiom": "ambient_keep_default",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "ambient_keep_default is nullary with NO Requires "
                     "(unconditional domain); every model call site (resolve_keep / "
                     "reduce_result_metadata, keep-is-None branch) passes zero "
                     "arguments, so every caller-reachable callee input is inside the "
                     "axiom domain (containment holds trivially). There is no "
                     "reachable input outside the domain, so AXIOM-TOO-WEAK-FOR-"
                     "CALLER cannot arise.",
    },
]
