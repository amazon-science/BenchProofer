# properties.py — PBT falsification battery for django__django-15987.
#
# NOT a Nagini module: a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants built by region-surgery (edits ONLY inside the
# # impl-start / # impl-end region — which the spec_view elides together with
# the nested invariants — so the frozen spec (axioms/pure/pre/post-conditions +
# signature) is byte-identical and markers.same_spec holds). Each spec case is
# checked by Nagini verify + markers.same_spec; the axiom case is a real-callee
# probe run in the instance Docker image.
#
# Defended surface (from model.py + refinement.md + mapping.md + instance.json):
#   default_dir_is_listed(value_matches: List[bool], is_path_object: List[bool]) -> bool
#     * BOTH inputs are READ-ONLY: Requires AND Ensures Acc(list_pred(.),1/2),
#       plus the frame clauses ToSeq(.)==Old(ToSeq(.)) on both lists.
#       => FRAME-MUTATION is MANDATORY: a rival that WRITES either input list
#          must be rejected for insufficient permission (half-perm forbids it).
#     * the load-bearing postcondition clause is
#           Result() == any_match(ToSeq(value_matches))
#       which names ONLY value_matches; is_path_object is deliberately pinned OUT
#       of the RHS. So a verifying impl's output is the exact disjunction of the
#       per-entry path-string matches, and a matching path-object entry can never
#       be suppressed.  This is the whole content of the gold fix
#       (`app_dir in [str(d) for d in fixture_dirs]` replacing `app_dir in
#       fixture_dirs`): the pre-patch raw membership suppressed a Path entry
#       (a PurePath is never raw-== a str) — modeled by is_path_object.
#     * any_match is GROUNDED, not an ungrounded oracle: it is a @Pure
#       front-recursive fold fully unfolded over the input value_matches (a
#       function of the args), NOT an opaque answer-key marker. Returning it
#       directly IS the correct answer — there is no WRONG echo to construct
#       (see 'assessment'); the honest disjunctive accumulator is supplied as a
#       positive control instead.
#     * there is no raise / side-effect channel invisible to the value
#       abstraction: the model abstracts taking-the-raise-branch as Result()==True
#       (the F2P only observes assertRaisesMessage), so the boolean Result() IS
#       the observable. => no control-flow-effect / capability-token case (N/A).
#
# Axiom lane: the bundle has NO @ContractOnly axiom (axioms region empty,
# meta.axioms == []). It DOES carry an A-reference deep model (`any_match` +
# the value_matches/is_path_object per-entry abstraction) validated == the real
# str()/pathlib membership by axiom_check.py / G-AX. We re-run that soundness
# obligation in Docker as an axiom-soundness probe (real callee, fuzzed configs).
from pathlib import Path

INSTANCE = "django__django-15987"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — all strictly INSIDE the # impl-start / # impl-end region.
# ---------------------------------------------------------------------------

# The load-bearing decision block (the entry-by-entry presence accumulation).
_DECISION = (
    "        # Compare by path string (the entry coerced to its path string equals\n"
    "        # the default directory's path string).\n"
    "        if value_matches[i - 1]:\n"
    "            result = True\n"
)


SPEC_TESTS = [
    # --- POSITIVE CONTROL (soundness) -------------------------------------
    # Structurally-different but CORRECT: replace the branch with a disjunctive
    # accumulator `result = result or value_matches[i - 1]`. Same backward sweep
    # and the same `.drop(i)` framing (so the front-recursive any_match unfold and
    # the loop invariant `result == any_match(ToSeq(value_matches).drop(i))` stay
    # valid — `any_match(drop(i-1)) == value_matches[i-1] or any_match(drop(i))`),
    # but no `if`/branch. Every gold framing Assert is kept verbatim. MUST verify;
    # if it cannot, the postcondition is SPEC-TOO-STRONG.
    {
        "id": "pos-control-disjunctive-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _DECISION,
            "        # Accumulate the presence disjunction by path string (no branch).\n"
            "        result = result or value_matches[i - 1]\n",
        ),
        "rationale": "a correct but branch-free impl with the gold framing intact "
                     "must verify against Result()==any_match(...) (else "
                     "SPEC-TOO-STRONG). It keeps the .drop(i) framing the "
                     "front-recursive any_match needs.",
    },

    # --- ADMISSIBILITY ----------------------------------------------------
    # Confirm the precondition (half-permission read access + len==len) admits a
    # normal F2P-shaped input: read BOTH read-only lists at a reachable index and
    # assert a precondition-derived fact (is_path_object[i-1] is a bool, and the
    # parallel index is in range by len==len). This exercises Acc(.,1/2) reads on
    # both inputs; it verifies iff the precondition accepts a normal input. If it
    # cannot establish the read, the precondition is PRECOND-TOO-STRONG.
    {
        "id": "admiss-reachable-read",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _DECISION,
            "        # Admissibility: the precondition must permit reading BOTH\n"
            "        # parallel read-only inputs at a reachable index (len==len).\n"
            "        Assert(is_path_object[i - 1] or not is_path_object[i - 1])\n"
            "        if value_matches[i - 1]:\n"
            "            result = True\n",
        ),
        "rationale": "the half-permission read of is_path_object[i-1] at a "
                     "reachable index (in range via the len==len invariant) must "
                     "be permitted for a normal input, else PRECOND-TOO-STRONG.",
    },

    # --- FRAME-MUTATION (MANDATORY: value_matches is Acc(.,1/2) read-only) -
    # The rival WRITES the read-only value_matches list (value_matches[i-1]=True)
    # before/while reading it. Even though it then computes the gold decision, the
    # half-permission Requires/Ensures + ToSeq(.)==Old(.) frame forbid ANY write
    # => the verifier MUST reject for INSUFFICIENT PERMISSION on list_pred. The
    # gold decision and all framing asserts are otherwise verbatim, so the
    # rejection is attributable to the write, not a logic change.
    {
        "id": "frame-mutation-write-value_matches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECISION,
            "        # Frame violation: write the READ-ONLY value_matches list.\n"
            "        if value_matches[i - 1]:\n"
            "            value_matches[i - 1] = True\n"
            "            result = True\n",
        ),
        "refinement": "a faithful real patch that WRITES back into settings."
                      "FIXTURE_DIRS while testing membership mutates shared "
                      "configuration; the gold patch reads `[str(d) for d in "
                      "fixture_dirs]` without ever mutating FIXTURE_DIRS, so a "
                      "mutating variant is not the gold behaviour and is not what "
                      "resolves the F2P. Here it is rejected purely on permission.",
        "rationale": "rejection comes from the permission system: only "
                     "Acc(list_pred(value_matches),1/2) is held, so any write to "
                     "value_matches[i-1] fails for insufficient permission (and "
                     "would also break ToSeq(value_matches)==Old(...)).",
    },

    # --- FRAME-MUTATION (supporting: the OTHER read-only input) -----------
    # Same attack on is_path_object (also Acc(.,1/2), also pinned by
    # ToSeq(is_path_object)==Old(...)). A write to it must be rejected for
    # insufficient permission. Cheap supporting case that still carries the same
    # refinement: the gold never mutates FIXTURE_DIRS.
    {
        "id": "frame-mutation-write-is_path_object",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECISION,
            "        # Frame violation: write the READ-ONLY is_path_object list.\n"
            "        is_path_object[i - 1] = False\n"
            "        if value_matches[i - 1]:\n"
            "            result = True\n",
        ),
        "refinement": "the gold membership test reads FIXTURE_DIRS entries (via "
                      "str(d)) and never assigns into the list; a variant that "
                      "writes is_path_object models mutating the configuration "
                      "collection, which is not the resolving behaviour.",
        "rationale": "rejection comes from the permission system: only half "
                     "permission on is_path_object is held, so the write fails "
                     "for insufficient permission (and breaks its Old(ToSeq(.)) "
                     "frame clause).",
    },

    # --- VALUE-DOUBLE-MASK / the EXACT pre-patch bug (uniqueness) ---------
    # The pre-patch buggy decision: `value_matches[i-1] and not is_path_object[i-1]`
    # — let path-object-ness SUPPRESS a real path-string match. This is the
    # behaviour the gold patch removes. It must be rejected because the
    # postcondition RHS names ONLY value_matches (is_path_object pinned out), so a
    # config with a single value-matching path-object entry forces
    # Result()==any_match(value_matches)==True while this impl returns False.
    {
        "id": "weak-prepatch-pathobject-suppression",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECISION,
            "        # Pre-patch bug: a path-object entry is suppressed even when\n"
            "        # its path string matches (raw membership `app_dir in dirs`).\n"
            "        if value_matches[i - 1] and not is_path_object[i - 1]:\n"
            "            result = True\n",
        ),
        "refinement": "this IS model_prepatch: its faithful real patch is the "
                      "ORIGINAL `app_dir in fixture_dirs` (raw membership), which "
                      "misses a pathlib.Path entry equal-by-string to app_dir (a "
                      "PurePath is never raw-== a str) — exactly the new F2P "
                      "test_fixture_dirs_with_default_fixture_path_as_pathlib, "
                      "which it FAILS. So it does NOT resolve.",
        "rationale": "rejection comes from the postcondition clause "
                     "Result()==any_match(ToSeq(value_matches)) (is_path_object "
                     "excluded) sensed by the loop invariant "
                     "result==any_match(ToSeq(value_matches).drop(i)); a "
                     "value-matching path-object entry forces the disjunction "
                     "True while this impl yields False.",
    },

    # --- PARTIAL-DOMAIN: skip the first entry (index 0) -------------------
    # A rival correct on every entry EXCEPT index 0: it stops accumulating once
    # i == 1, so a default directory listed as the FIRST FIXTURE_DIRS entry is
    # never detected. Diverges from any_match exactly when the only match is at
    # index 0 (e.g. FIXTURE_DIRS == [<the default dir>]) — which is the shape of
    # the F2P (a single matching entry). Must be rejected.
    {
        "id": "partial-domain-skip-index-0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECISION,
            "        # Partial domain: ignore the first configured entry (index 0).\n"
            "        if i > 1 and value_matches[i - 1]:\n"
            "            result = True\n",
        ),
        "refinement": "a real patch that skips the first FIXTURE_DIRS entry of "
                      "the membership test misses a default directory listed as "
                      "that first entry; the F2P uses FIXTURE_DIRS=[Path(_cur_dir)/"
                      "'fixtures'] (a single entry at index 0), so this would FAIL "
                      "to raise ImproperlyConfigured and would NOT resolve.",
        "rationale": "rejection comes from the postcondition "
                     "Result()==any_match(ToSeq(value_matches)): on a config whose "
                     "only match is at index 0 the disjunction is True while this "
                     "impl, having skipped i==1, returns False — caught by the "
                     "final loop invariant at i==0.",
    },

    # --- PARTIAL-DOMAIN: pin only the last entry (index len-1) -------------
    # A rival that reports presence ONLY from the last configured entry: it sets
    # result solely on the first loop step (i == len). Correct when the match (if
    # any) is at the last index, wrong whenever a match exists only at an earlier
    # index. Diverges from the full disjunction. Must be rejected.
    {
        "id": "partial-domain-only-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECISION,
            "        # Partial domain: only the LAST configured entry can set it.\n"
            "        if i == len(value_matches) and value_matches[i - 1]:\n"
            "            result = True\n",
        ),
        "refinement": "a real patch whose membership test consults only the last "
                      "FIXTURE_DIRS entry misses a default directory listed at any "
                      "earlier position; for a multi-entry FIXTURE_DIRS with the "
                      "default dir not last it would fail to raise and NOT resolve.",
        "rationale": "rejection comes from Result()==any_match(ToSeq(value_matches)): "
                     "a config matching only at an earlier index makes the "
                     "disjunction True while this impl returns False; the loop "
                     "invariant result==any_match(ToSeq(value_matches).drop(i)) "
                     "fails after the first iteration.",
    },

    # --- CONSTANT FALSE (supporting near-miss) ----------------------------
    # The cheapest wrong impl: never detect anything. Correct only on the
    # no-match sub-domain. Rejected by the postcondition on any matching config.
    {
        "id": "weak-constant-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _DECISION,
            # Written as a DELETION of the presence branch rather than as
            # `if False:`: Nagini's front end rejects a statement it can prove
            # unreachable (`dead.code`), and a rival that fails to translate
            # proves nothing about the spec (43c6680f6). A constant-false guard
            # is not control flow, so this is the same rival.
            "        # Always-miss: no presence branch at all, so `result` keeps\n"
            "        # its initial False for every entry.\n",
        ),
        "refinement": "a real patch that always returns 'not present' never raises "
                      "ImproperlyConfigured even when a default directory IS listed "
                      "in FIXTURE_DIRS; it fails the F2P (and the P2P duplicate "
                      "guards) and does NOT resolve.",
        "rationale": "rejection comes from Result()==any_match(ToSeq(value_matches)): "
                     "on any config with a match the disjunction is True while this "
                     "impl returns False; the loop invariant fails at the first "
                     "matching index.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-reference deep-model soundness obligation (G-AX).
# No @ContractOnly axiom is consumed; the trust point is that the per-entry
# abstraction (value_matches/is_path_object) and the any_match fold faithfully
# reflect the real str()/pathlib membership. We re-run the bundle's axiom_check
# logic against the REAL callee (os.path.join / str(Path) / PurePath.__eq__) on
# the explicit F2P scenario + boundary + 20000 fuzz configs, in Docker.
# axiom_check.py is read on the HOST at load time and embedded into the probe
# (the runner mounts ONLY the probe script in-container; bundle files are absent).
# ---------------------------------------------------------------------------

# Neutralize the bundle's own `if __name__ == "__main__": sys.exit(main())`
# guard (the probe is exec'd as __main__, which would otherwise run main()
# twice) and append a single explicit driver that classifies the outcome.
_AXIOM_CHECK_BODY = _AXIOM_CHECK_SRC.replace(
    'if __name__ == "__main__":\n    sys.exit(main())\n', "", 1
).replace(
    'if __name__ == "__main__":\n    sys.exit(main())', "", 1
)
if 'if __name__ == "__main__":' in _AXIOM_CHECK_BODY:
    raise AssertionError("axiom_check.py __main__ guard not stripped (drift)")

_AXIOM_SOUNDNESS_PROBE = (
    _AXIOM_CHECK_BODY
    + "\n\n"
    + "# --- PBT axiom-soundness driver (appended) -------------------------\n"
    + "import sys as _sys\n"
    + "try:\n"
    + "    _rc = main()\n"
    + "except AssertionError as _e:\n"
    + "    print('AXIOM-UNSOUND: A-reference deep model disagrees with the '\n"
    + "          'real str()/pathlib membership:', _e)\n"
    + "    _sys.exit(1)\n"
    + "print('axiom-soundness OK: any_match == real `app_dir in [str(d) for '\n"
    + "      'd in dirs]` and prepatch == real `app_dir in dirs` on F2P + '\n"
    + "      'boundary + 20000 fuzz real str/Path configs.')\n"
    + "_sys.exit(0 if _rc == 0 else 1)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-soundness-any_match-vs-real-membership",
        "axiom": "any_match (A-reference: value_matches/is_path_object abstraction)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_SOUNDNESS_PROBE,
        "rationale": "the deep model any_match must equal the real corrected "
                     "membership `app_dir in [str(d) for d in fixture_dirs]` and "
                     "the prepatch loop must equal raw `app_dir in fixture_dirs` "
                     "on every caller-reachable config (str/Path entries built "
                     "with the real os.path/pathlib machinery); a single "
                     "disagreement => AXIOM-UNSOUND. Containment is trivial here: "
                     "the model's only reachable callee-inputs are str/Path "
                     "entries reduced via str()/isinstance, which is exactly the "
                     "domain the probe fuzzes (F2P + 9 boundary + 20000 configs).",
    },
]
