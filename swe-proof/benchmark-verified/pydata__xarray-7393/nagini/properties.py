"""PBT manifest for pydata__xarray-7393 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (region-surgery: only
the text strictly inside the single `# impl-start` / `# impl-end` region — which
nests the loop `invariants` region — is edited) and swap the implementation;
they are checked by Nagini verify + markers.same_spec. The axiom case is a
real-callee probe run in the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md / instance):

  ONE modeled function: materialize_level(requested, declared, storage_type,
  level_values) — the `self.level is not None` branch of
  PandasMultiIndexingAdapter.__array__ (xarray/core/indexing.py:1533). It
  materialises one selected multi-index level into a dense array.

    requested:    Optional[int]   — caller-requested element type (None = none)
    declared:     int             — the wrapper's own declared element type
    storage_type: int             — the (possibly WIDER) element type the
                                     intermediate pandas storage reports; a
                                     NON-influencing input (the bug leaked it)
    level_values: List[int]       — per-label element values, READ-ONLY

    Pre : Acc(list_pred(level_values), 1/2)            <- level_values READ-ONLY
    Post: Acc(list_pred(level_values), 1/2)            (returns the read perm)
          Acc(Result().etype) and Acc(Result().values) and
              Acc(list_pred(Result().values))          (fresh, fully owned array)
          Result().etype == effective_type(requested, declared)   <- discriminator
          Implies(requested is None,     Result().etype == declared)
          Implies(requested is not None, Result().etype == requested)
          ToSeq(Result().values) == ToSeq(level_values)           <- value copy

  LOAD-BEARING clauses:
    (A) Result().etype == effective_type(requested, declared), reinforced by the
        two case clauses (None -> declared, else -> requested). storage_type does
        NOT appear anywhere in the postcondition, so the spec FORBIDS the result
        type from being the promoted storage type — this is precisely the bug.
    (B) ToSeq(Result().values) == ToSeq(level_values): the materialised values
        are exactly the input values, carried through unchanged.

  effective_type is a @Pure helper but it is GROUNDED — fully unfolded as
  `requested if requested is not None else declared`, a pure function of the
  args, and the postcondition independently pins both cases. There is NO opaque
  answer-key / exact marker to echo without doing the work, so the directive-2
  "ungrounded-oracle echo" attack has no target here (see assessment). The
  storage-leak rival below is the nearest analogue and the spec correctly
  REJECTS it.

  Read-only input: level_values is Acc(list_pred(.), 1/2)  =>  the FRAME-MUTATION
  probe is MANDATORY (a rival that WRITES level_values to satisfy a postcondition
  by side effect must be REJECTED for insufficient permission).

Axiom lane: the bundle has NO consumed @ContractOnly axioms (the axioms region
  is empty). The changed materialisation is an A-reference deep model
  (effective_type + the res.etype assignment + the value-copy loop) standing for
  `np.asarray(values, dtype=dtype)`. Per PBT_PLAN §4 the axiom lane covers
  A-reference deep models too: AXIOM_TESTS carries ONE axiom-soundness case that
  reuses the persisted, gold-grounded axiom_check.py — it EXECUTES the real
  np.asarray on deliberately-promoted storage and the real-xarray stack/.values
  round trip, asserting the deep model == the real callee. There is no
  Requires-bounded callee to enumerate, so axiom-containment is N/A (the deep
  model is unconditional over int codes; np.asarray is unchanged by the patch and
  modeled deeply, not via a Requires domain) — see assessment.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-7393"
FLOAT_ENCODING = None  # meta.json float_encoding is null (opaque int-code carrier)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The WHOLE gold impl-region body (everything strictly between # impl-start and
# # impl-end, including the nested loop invariants). Editing only this string
# guarantees same_spec — the frozen spec view is never touched.
# ---------------------------------------------------------------------------
_GOLD = (
    "    res = DenseArray()\n"
    "    dtype = requested  # type: Optional[int]\n"
    "    if dtype is None:\n"
    "        dtype = declared\n"
    "    # `dtype` is now the resolved element type; build the dense array with it.\n"
    "    res.etype = dtype\n"
    "    i = 0\n"
    "    while i < len(level_values):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
    "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
    "        Invariant(res.etype == effective_type(requested, declared))\n"
    "        Invariant(0 <= i and i <= len(level_values))\n"
    "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
    "        # invariants-end\n"
    "        res.values.append(level_values[i])\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(level_values).take(len(level_values)) == ToSeq(level_values))\n"
    "    return res\n"
    "    "
)

assert _GOLD in _BASE and _BASE.count(_GOLD) == 1, "gold impl anchor drifted"


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): reorder the dtype-resolution branch -----
    # Gold resolves `dtype = requested; if dtype is None: dtype = declared`. Here
    # the test is written the other way round (`if requested is None: declared
    # else requested`) — same value of `effective_type(requested, declared)` on
    # every input. The loop, the invariants, and the closing Assert are kept
    # VERBATIM (directive-2 pilot rule: a positive control keeps every framing
    # obligation it still needs), so this is a pure branch-reorder with no proof
    # gap. MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD,
            "    res = DenseArray()\n"
            "    if requested is None:\n"
            "        dtype = declared\n"
            "    else:\n"
            "        dtype = requested\n"
            "    res.etype = dtype\n"
            "    i = 0\n"
            "    while i < len(level_values):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == effective_type(requested, declared))\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(level_values).take(len(level_values)) == ToSeq(level_values))\n"
            "    return res\n"
            "    "),
        "rationale": "a behaviourally-identical reshape (resolve the element type "
                     "with the if/else written in the opposite order) computes the "
                     "same effective_type on every input and keeps the gold loop / "
                     "invariants / closing Assert verbatim, so it must verify against "
                     "the frozen postcondition (else SPEC-TOO-STRONG).",
    },

    # -- POSITIVE CONTROL (soundness): resolve via the @Pure helper directly ---
    # The grounded @Pure oracle `effective_type` is in scope; an honest impl may
    # compute the resolved type by calling it directly. This is the cheapest
    # CORRECT impl. The Invariant `res.etype == effective_type(requested,
    # declared)` then holds by definition of the assignment. Loop / invariants /
    # Assert kept verbatim. MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-effective-type-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD,
            "    res = DenseArray()\n"
            "    res.etype = effective_type(requested, declared)\n"
            "    i = 0\n"
            "    while i < len(level_values):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == effective_type(requested, declared))\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(level_values).take(len(level_values)) == ToSeq(level_values))\n"
            "    return res\n"
            "    "),
        "rationale": "the grounded @Pure helper effective_type is the spec's own "
                     "spelling of the resolution; computing res.etype by calling it "
                     "directly is the cheapest CORRECT impl and must verify (else "
                     "SPEC-TOO-STRONG). Doubles as the honest cheapest-impl positive "
                     "control standing in for the (inapplicable) ungrounded-oracle "
                     "echo: the oracle is fully grounded in the args, so echoing it "
                     "IS the correct answer.",
    },

    # -- ADMISSIBILITY: the precondition admits a normal F2P-shaped input ------
    # The F2P drives requested=None, declared=<narrow code>, storage_type=<wider
    # code>, level_values=<the promoted per-label values>. This variant asserts
    # the read-only half-permission on level_values is in hand at entry (exactly
    # the Requires) before running the gold body. If the Requires could not be
    # established for a legitimate caller the Assert would fail => PRECOND-TOO-
    # STRONG. It verifies, so the precondition is satisfiable by an in-domain
    # input. Gold body otherwise verbatim.
    {
        "id": "admiss-precond-halfperm",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD,
            "    Assert(Acc(list_pred(level_values), 1 / 2))\n"
            "    res = DenseArray()\n"
            "    dtype = requested  # type: Optional[int]\n"
            "    if dtype is None:\n"
            "        dtype = declared\n"
            "    res.etype = dtype\n"
            "    i = 0\n"
            "    while i < len(level_values):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == effective_type(requested, declared))\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(level_values).take(len(level_values)) == ToSeq(level_values))\n"
            "    return res\n"
            "    "),
        "rationale": "the Requires (Acc(list_pred(level_values),1/2)) must be "
                     "establishable for a normal F2P-shaped input; the leading Assert "
                     "confirms the half-permission is in hand at entry and the body "
                     "verifies (else PRECOND-TOO-STRONG). A read-only level_values "
                     "input is admissible.",
    },

    # -- FRAME-MUTATION (uniqueness) [MANDATORY]: append to read-only input ----
    # level_values is held at Acc(list_pred(.),1/2). This rival appends to it
    # before copying. `list.append` needs the FULL list_pred; only 1/2 is held,
    # so it MUST be REJECTED for INSUFFICIENT PERMISSION. The element-type
    # resolution and the copy are kept gold so the rejection is attributable to
    # the write. (Also note: after appending, the gold value invariant/Assert no
    # longer match, but the permission failure fires first.)
    {
        "id": "frame-mutate-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD,
            "    res = DenseArray()\n"
            "    dtype = requested  # type: Optional[int]\n"
            "    if dtype is None:\n"
            "        dtype = declared\n"
            "    res.etype = dtype\n"
            "    level_values.append(0)\n"
            "    i = 0\n"
            "    while i < len(level_values):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == effective_type(requested, declared))\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        i = i + 1\n"
            "    return res\n"
            "    "),
        "refinement": "the gold patch builds a FRESH array via np.asarray(values, "
                      "dtype=dtype) and never mutates `self.array.get_level_values("
                      "self.level).values` (the source pandas level-values storage). A "
                      "faithful real patch that mutated that shared storage in place "
                      "would corrupt the underlying MultiIndex level for every other "
                      "consumer of the same adapter (the P2P stack/unstack/sel/copy "
                      "tests re-read those level values), so it would NOT resolve the "
                      "suite.",
        "rationale": "rejected by the permission system: level_values is held at "
                     "Acc(list_pred,1/2); `list.append` requires the full predicate, "
                     "so the write is INSUFFICIENT-PERMISSION. If it verified the "
                     "read-only source frame would be unguarded (SPEC-TOO-WEAK).",
    },

    # -- FRAME-MUTATION supporting (uniqueness): in-place index store ----------
    # A different write shape on the same read-only input: store into
    # level_values[i] during the copy. Also needs the FULL list_pred. Guarded by
    # the loop bound so it is only attempted on a non-empty input; the store
    # itself is rejected for insufficient permission.
    {
        "id": "frame-mutate-index-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD,
            "    res = DenseArray()\n"
            "    dtype = requested  # type: Optional[int]\n"
            "    if dtype is None:\n"
            "        dtype = declared\n"
            "    res.etype = dtype\n"
            "    i = 0\n"
            "    while i < len(level_values):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == effective_type(requested, declared))\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        level_values[i] = 0\n"
            "        i = i + 1\n"
            "    return res\n"
            "    "),
        "refinement": "writing into the source level-values array element-by-element "
                      "is not the gold fix — np.asarray(values, dtype=dtype) reads the "
                      "values and returns a fresh array, leaving the source untouched. "
                      "A patch that overwrote the source in place would corrupt the "
                      "MultiIndex level observed by the P2P tests, so it would not "
                      "resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: an in-place store to "
                     "level_values[i] needs the full list_pred but only 1/2 is held. "
                     "Frame integrity of the read-only source values.",
    },

    # -- STORAGE-LEAK rival (uniqueness): res.etype = storage_type = the BUG ----
    # This IS model_prepatch: the materialised array carries the (wider) promoted
    # storage element type instead of the resolved declared/requested type. The
    # matching loop invariant is rewritten to res.etype == storage_type so the
    # body is internally consistent and the rejection lands squarely on the
    # LOAD-BEARING discriminator postcondition Result().etype == effective_type(
    # requested, declared) (false whenever storage_type != effective_type).
    {
        "id": "weak-storage-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD,
            "    res = DenseArray()\n"
            "    res.etype = storage_type\n"
            "    i = 0\n"
            "    while i < len(level_values):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == storage_type)\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(level_values).take(len(level_values)) == ToSeq(level_values))\n"
            "    return res\n"
            "    "),
        "refinement": "this IS the pre-patch behaviour (return self.array."
                      "get_level_values(self.level).values directly — the array "
                      "carries the pandas-promoted storage dtype). It is exactly the "
                      "reported bug: with declared=int32 / storage_type=int64 the F2P "
                      "test_restore_dtype_on_multiindexes[int32] asserts "
                      "str(.values.dtype)=='int32' and gets 'int64', so it FAILS — a "
                      "patch that leaks the storage type does NOT resolve.",
        "rationale": "rejected by the LOAD-BEARING discriminator Result().etype == "
                     "effective_type(requested, declared) (and the case clause "
                     "Implies(requested is None, etype==declared)): storage_type is "
                     "not constrained to equal effective_type, so on any witness with "
                     "storage_type != effective_type (e.g. requested=None, "
                     "declared!=storage_type) the postcondition fails. This is the "
                     "G-DIFF discriminator; if it verified the spec would admit the "
                     "bug (SPEC-TOO-WEAK).",
    },

    # -- PARTIAL-DOMAIN (uniqueness): always use declared, ignore requested ----
    # res.etype = declared unconditionally. Correct on the requested-is-None
    # subdomain (where effective_type == declared), WRONG on the requested-given
    # subdomain (where effective_type == requested != declared). Rejected by
    # Implies(requested is not None, Result().etype == requested).
    {
        "id": "partial-ignore-requested",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD,
            "    res = DenseArray()\n"
            "    res.etype = declared\n"
            "    i = 0\n"
            "    while i < len(level_values):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == declared)\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        i = i + 1\n"
            "    Assert(ToSeq(level_values).take(len(level_values)) == ToSeq(level_values))\n"
            "    return res\n"
            "    "),
        "refinement": "always using self.dtype (ignoring the caller's `dtype` "
                      "argument) diverges from the gold `np.asarray(values, "
                      "dtype=dtype)` whenever a caller passes an explicit dtype "
                      "(__array__(dtype=X) must honour X). It is NOT the equivalent "
                      "patch: it discards the requested-type contract that np.asarray "
                      "implements, so a faithful version is behaviourally unequal to "
                      "gold on the requested-given subdomain and would not be the "
                      "resolving patch.",
        "rationale": "rejected by Implies(requested is not None, Result().etype == "
                     "requested): on the requested-given subdomain declared != "
                     "requested makes the clause false. Partial-domain divergence on "
                     "the requested-type subdomain; if it verified the requested-type "
                     "case would be unpinned (SPEC-TOO-WEAK).",
    },

    # -- VALUE-CORRUPTION (uniqueness): extra trailing element -----------------
    # Correct element type, but the materialised values have one extra element
    # appended after the copy loop. Rejected by ToSeq(Result().values) ==
    # ToSeq(level_values) (length differs by one). The loop / invariants are gold
    # (they hold at exit); the post-loop append breaks value equality.
    {
        "id": "value-extra-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD,
            "    res = DenseArray()\n"
            "    dtype = requested  # type: Optional[int]\n"
            "    if dtype is None:\n"
            "        dtype = declared\n"
            "    res.etype = dtype\n"
            "    i = 0\n"
            "    while i < len(level_values):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == effective_type(requested, declared))\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        i = i + 1\n"
            "    res.values.append(0)\n"
            "    return res\n"
            "    "),
        "refinement": "np.asarray(values, dtype=dtype) preserves the length and "
                      "content of `values`; a materialisation that emits an extra "
                      "trailing element produces an array of the wrong length, "
                      "diverging from gold. The F2P/P2P read the materialised "
                      ".values (assert_array_equal / shape checks) and would observe "
                      "the corruption, so such a patch would not resolve.",
        "rationale": "rejected by ToSeq(Result().values) == ToSeq(level_values): after "
                     "the loop res.values == level_values, the extra append makes it "
                     "one element longer, so the value-preservation postcondition "
                     "fails. If it verified the value-copy clause would be unpinned "
                     "(SPEC-TOO-WEAK).",
    },

    # -- VALUE-CORRUPTION supporting (uniqueness): drop the last element -------
    # Correct element type, but the copy stops one short of the end. The loop
    # invariant ToSeq(res.values)==ToSeq(level_values).take(i) still holds with
    # i == len-1, but the value-preservation postcondition (full sequence) and
    # the closing equality fail on any non-empty input.
    {
        "id": "value-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD,
            "    res = DenseArray()\n"
            "    dtype = requested  # type: Optional[int]\n"
            "    if dtype is None:\n"
            "        dtype = declared\n"
            "    res.etype = dtype\n"
            "    i = 0\n"
            "    while i < len(level_values) - 1:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(level_values), 1 / 2))\n"
            "        Invariant(Acc(res.etype) and Acc(res.values) and Acc(list_pred(res.values)))\n"
            "        Invariant(res.etype == effective_type(requested, declared))\n"
            "        Invariant(0 <= i and i <= len(level_values))\n"
            "        Invariant(ToSeq(res.values) == ToSeq(level_values).take(i))\n"
            "        # invariants-end\n"
            "        res.values.append(level_values[i])\n"
            "        i = i + 1\n"
            "    return res\n"
            "    "),
        "refinement": "stopping the copy one element short emits a shorter array than "
                      "np.asarray(values, dtype=dtype) would; the materialised level "
                      "would be missing its last label. The F2P/P2P observe the "
                      "materialised values, so a truncating patch diverges from gold "
                      "and would not resolve.",
        "rationale": "rejected by ToSeq(Result().values) == ToSeq(level_values): on a "
                     "non-empty input res.values == take(len-1) != the full sequence, "
                     "so value-preservation fails. Partial-domain (last-element) "
                     "divergence; if it verified the value-copy clause would be "
                     "unpinned (SPEC-TOO-WEAK).",
    },
]


# ===========================================================================
# AXIOM LANE — A-reference deep model soundness (NO consumed @ContractOnly axiom)
# ===========================================================================
#
# The runner mounts ONLY the probe script at /work; axiom_check.py / model.py are
# NOT in-container. The axiom-soundness probe therefore EMBEDS axiom_check.py's
# source (read on the HOST at manifest-load time, utf-8-safe) and EXECUTES the
# real numpy / xarray callee — it never scrapes source. axiom_check.py is
# regime-detecting (RC=0 at base OR gold-applied), so we run it with
# apply_gold=True (the post-patch round-trip is the A-reference obligation).
#
# There is NO Requires-bounded @ContractOnly callee to enumerate, so there is no
# axiom-containment case: the deep model (effective_type + value copy) is
# unconditional over opaque int codes / List[int], and np.asarray — its
# real-world building block — is UNCHANGED by the patch and modeled deeply rather
# than via a Requires domain. (See assessment: containment is N/A here.)

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# axiom-soundness: the deep model (res.etype == effective_type(requested,
# declared), values carried through) == the real np.asarray on PROMOTED storage
# across the primitive cases + the real-xarray stack/.values round trip. Reuses
# the persisted, gold-grounded axiom_check.py verbatim and drives its main()
# (which sys.exit(0)s iff every obligation holds). Any non-zero exit is a real
# A-reference violation (AXIOM-UNSOUND for the deep model).
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# ---- PBT A-reference soundness driver (appended) --------------------------
import sys as _sys
print("PBT axiom-soundness: running the real np.asarray on deliberately-promoted "
      "storage (declared/effective != storage_type) across the primitive cases + "
      "the real-xarray stack/.values round trip; asserting the deep model "
      "(effective_type + value copy) == the real callee.")
try:
    _rc = main()
    _sys.exit(0 if _rc in (0, None) else 1)
except SystemExit as _e:
    _code = _e.code if isinstance(_e.code, int) else (0 if _e.code is None else 1)
    _sys.exit(0 if _code == 0 else 1)
"""

AXIOM_TESTS = [
    {
        "id": "ax-sound-np-asarray-deepmodel",
        "axiom": "effective_type + DenseArray construction (A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the changed materialisation is an A-reference deep model "
                     "(effective_type + the res.etype assignment + the value-copy "
                     "loop) standing for np.asarray(values, dtype=dtype) with dtype "
                     "defaulted to self.dtype. axiom_check.py EXECUTES the real "
                     "np.asarray on deliberately PROMOTED storage (storage_type wider "
                     "than the effective type) and asserts (a) the result element "
                     "type equals the effective type (requested if given, else "
                     "declared) — NEVER the storage type — and (b) the values are "
                     "carried through unchanged; plus the real-xarray "
                     "Dataset(...).stack(...)['bar'].values round trip restores the "
                     "declared dtype under the gold-applied regime. If the real "
                     "callee disagreed with the deep model the A-reference would be "
                     "AXIOM-UNSOUND. Runs in the instance image with apply_gold=True.",
    },
]
