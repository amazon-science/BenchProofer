# properties.py — PBT manifest for django__django-15851. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# executes each and stamps RESULT. Spec cases are full model.py variants (SAME
# frozen spec, swapped impl) checked by Nagini verify + markers.same_spec; axiom
# cases are real-callee probes in Docker (NONE here — no @ContractOnly axioms,
# no A-reference deep models; meta.axioms == [], deep_model_references == []).
#
# Defended surface (model.py:45-95):
#   build_argv(prefix: List[int], parameters: List[int],
#              has_dbname: bool, dbname: int) -> List[int]
#
#   READ-ONLY inputs (Acc(...,1/2)): BOTH `prefix` and `parameters`
#     Requires(Acc(list_pred(prefix), 1 / 2))
#     Requires(Acc(list_pred(parameters), 1 / 2))
#   so frame-mutation is MANDATORY (the #1 weakness class): a rival that WRITES
#   through either half-permission reference to vacuously satisfy the
#   postcondition must be rejected for INSUFFICIENT PERMISSION (a store needs
#   FULL Acc), not for a value mismatch. has_readonly_input is True.
#
#   Result has FULL permission (Acc(list_pred(Result()))) — freshly built.
#
#   The two LOAD-BEARING postcondition clauses pin the output as a function of
#   the inputs (model.py:58-62):
#     (E1) Implies(has_dbname,
#                  ToSeq(Result()) == ToSeq(prefix)+ToSeq(parameters)+PSeq(dbname))
#     (E2) Implies(not has_dbname,
#                  ToSeq(Result()) == ToSeq(prefix)+ToSeq(parameters))
#   (E1) is the DISCRIMINATING clause: extras BEFORE the dbname token. The
#   pre-patch ordering (dbname before extras) violates exactly (E1) — this is
#   the gold patch's whole point (G-DIFF; model_prepatch.py).
#
#   UNGROUNDED-ORACLE ECHO — N/A. The postcondition is fully GROUNDED in the
#   inputs (prefix, parameters, dbname); there is no @Pure answer-key / exact
#   marker to echo without doing the work (axioms-start/pure-start are empty).
#   So there is no "wrong echo that verifies"; we instead supply an honest
#   cheapest-impl positive control (case `pos-control-reorder`). See assessment.
#
#   CONTROL-FLOW-EFFECT — N/A. The only observable is the returned argument
#   vector, captured exactly by ToSeq(Result()); there is no raise / side-effect
#   / capability difference the value abstraction misses (the unchanged env dict
#   and tuple wrapper are out of scope per mapping.md §2). See assessment.
from pathlib import Path

INSTANCE = "django__django-15851"
FLOAT_ENCODING = None   # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in source")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r} appears {src.count(old)}x")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region (model.py:64-95). Every variant edits ONLY
# text between `# impl-start` and `# impl-end`, so the frozen spec view (and
# thus markers.same_spec) is preserved. The invariants markers are NESTED
# inside the impl region and are elided from the spec view too, so editing them
# does not break same_spec — but a positive control MUST keep the gold loop
# invariants intact or it fails for a PROOF reason, not a spec reason.
# ---------------------------------------------------------------------------

# The trailing database-name append (the gold ordering: extras already in,
# dbname appended LAST). This is the load-bearing, discriminating tail.
_GOLD_TAIL = "    if has_dbname:\n        result.append(dbname)\n    return result"
assert _GOLD_TAIL in _BASE and _BASE.count(_GOLD_TAIL) == 1, "gold tail drift"

# The first-loop append (copying the prefix segment element-wise).
_PREFIX_APPEND = "        result.append(prefix[i])"
assert _BASE.count(_PREFIX_APPEND) == 1, "prefix-append anchor not unique"

# The second-loop append (copying the parameters segment element-wise).
_PARAMS_APPEND = "        result.append(parameters[j])"
assert _BASE.count(_PARAMS_APPEND) == 1, "params-append anchor not unique"

# The whole gold impl body (start to return), for the variants that restructure
# control flow wholesale (prepatch ordering, drop-dbname, prefix-after-params).
_GOLD_BODY = """    result = []  # type: List[int]
    i = 0
    while i < len(prefix):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(prefix))
        Invariant(ToSeq(result) == ToSeq(prefix).take(i))
        Invariant(MustTerminate(len(prefix) - i + 1))
        # invariants-end
        result.append(prefix[i])
        Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
        i = i + 1
    Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
    j = 0
    while j < len(parameters):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(parameters), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(parameters))
        Invariant(ToSeq(result) == ToSeq(prefix) + ToSeq(parameters).take(j))
        Invariant(MustTerminate(len(parameters) - j + 1))
        # invariants-end
        result.append(parameters[j])
        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
               == ToSeq(parameters).take(j + 1))
        j = j + 1
    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
    if has_dbname:
        result.append(dbname)
    return result"""
assert _GOLD_BODY in _BASE and _BASE.count(_GOLD_BODY) == 1, "gold body drift"


SPEC_TESTS = [

    # ------------------------------------------------------------------ #
    # 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT, CORRECT.  #
    #    Local-variable reshape: bind the trailing token to a local `tok` #
    #    BEFORE the guard and append `tok` instead of `dbname` (Nagini    #
    #    aliases the int identity), and swap the order of the two         #
    #    post-loop framing asserts vs the loops (they remain present and  #
    #    provable). The two loops + ALL gold invariants are kept verbatim #
    #    (so no induction lemma is needed — same front-`.take(i)` fold     #
    #    direction as the spec). Computes EXACTLY prefix ++ params ++      #
    #    [dbname] / prefix ++ params. MUST verify, else SPEC-TOO-STRONG.   #
    # ------------------------------------------------------------------ #
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_TAIL,
            "    # local-variable reshape: alias the trailing token, append it\n"
            "    # under the same guard; identical value, identical post-state.\n"
            "    tok = dbname\n"
            "    if has_dbname:\n"
            "        result.append(tok)\n"
            "    return result",
        ),
        "rationale": "a structurally-different but behaviourally identical impl "
                     "(trailing token aliased to a local `tok`, appended under the "
                     "same has_dbname guard) must verify; it builds the same vector "
                     "prefix++params++[dbname]. The gold loop invariants/asserts are "
                     "untouched (front-take fold direction preserved, no induction "
                     "lemma needed). If it cannot verify => SPEC-TOO-STRONG.",
    },

    # ------------------------------------------------------------------ #
    # 2. ADMISSIBILITY — a self-call confirming the precondition admits an #
    #    F2P-shaped input. We CANNOT add a new top-level caller (that      #
    #    changes the spec_view => same_spec fails), so the witness lives   #
    #    INSIDE the impl region: build the EXACT F2P input shape           #
    #    (prefix=[psql]≈[7], parameters=[--help]≈[9], has_dbname=True,     #
    #    dbname=[dbname]≈8), call build_argv on it, and assert the         #
    #    DISCRIMINATING ordering postcondition (E1): the result is         #
    #    [7,9,8] = prefix++params++[dbname] (the post-patch order the F2P   #
    #    test_parameters now expects: ["psql","--help","dbname"]). Then    #
    #    fall through to the gold body for the real arguments. The fresh    #
    #    lists get FULL permission, so the self-call's Requires            #
    #    (Acc(...,1/2)) is establishable. MUST verify, else                 #
    #    PRECOND-TOO-STRONG.                                                 #
    # ------------------------------------------------------------------ #
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "    # admissibility witness: the F2P input shape (psql / --help /\n"
            "    # dbname) is in-domain; list_pred is established for the fresh\n"
            "    # lists, so the self-call's Requires(Acc(...,1/2)) is admissible,\n"
            "    # and the discriminating order (E1) holds: extras BEFORE dbname.\n"
            "    p_pre = [7]  # type: List[int]\n"
            "    p_par = [9]  # type: List[int]\n"
            "    Assert(list_pred(p_pre))\n"
            "    Assert(list_pred(p_par))\n"
            "    Assert(Acc(list_pred(p_pre), 1 / 2))\n"
            "    Assert(Acc(list_pred(p_par), 1 / 2))\n"
            "    # --- gold body for the actual arguments ---\n"
            + _GOLD_BODY,   # gold body verbatim (keeps its leading 4-space indent)
        ),
        "rationale": "the precondition Acc(list_pred(prefix),1/2) & "
                     "Acc(list_pred(parameters),1/2) admits a normal F2P-shaped "
                     "input ([psql],[--help],dbname): a fresh list owns full "
                     "list_pred, so lending 1/2 is establishable, and both clauses "
                     "are asserted AT the witness. They are asserted rather than "
                     "exercised by a self-call because the model carries "
                     "Requires(MustTerminate(2)) with a measure on each copy loop, "
                     "and a same-level self-call on a non-shrinking argument is an "
                     "obligation leak Nagini is right to refuse. The gold body then "
                     "runs for the actual arguments, so (E1) still yields "
                     "[psql,--help,dbname] -- exactly the post-patch F2P "
                     "expectation. If it cannot verify => PRECOND-TOO-STRONG. "
                     "NEGATIVE CONTROL: THERE IS NONE, and that is a fact about this "
                     "precondition rather than about the probe. build_argv's frozen "
                     "clauses are nothing but the two Acc(list_pred(.), 1 / 2), and "
                     "no VALUE violates a permission clause: measured, the same "
                     "asserts at p_pre = [] still report `Verification successful`. "
                     "So this case checks permission admissibility plus the (E1) "
                     "order the gold body proves; it does NOT pin a value domain, and "
                     "must not be read as strong as a case whose precondition "
                     "carries a length or element-domain clause a witness can leave.",
    },

    # ------------------------------------------------------------------ #
    # 3. FRAME-MUTATION on `prefix` — MANDATORY (#1 weakness class).       #
    #    prefix is read-only at Acc(...,1/2). This rival WRITES            #
    #    `prefix[0] = dbname` before the copy loop, attempting to fold the #
    #    dbname token into the prefix so the result satisfies the order    #
    #    vacuously. A store needs FULL Acc(list_pred(prefix)); with only   #
    #    1/2 it MUST fail for INSUFFICIENT PERMISSION (NOT a value         #
    #    mismatch). All gold invariants/asserts are kept verbatim so the    #
    #    rejection is attributable SOLELY to the write. Rejection source:  #
    #    the PERMISSION SYSTEM (the Requires/Invariant 1/2 fraction).       #
    # ------------------------------------------------------------------ #
    {
        "id": "frame-mutate-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    result = []  # type: List[int]\n    i = 0\n",
            "    result = []  # type: List[int]\n"
            "    prefix[0] = dbname   # WRITE through a 1/2 (read-only) reference\n"
            "    i = 0\n",
        ),
        "refinement": "no faithful real patch corresponds to this: "
                      "settings_to_cmd_args_env never mutates the prefix segment of "
                      "its own args list to satisfy the ordering — it only appends. "
                      "The rival exists solely to test whether the read-only (1/2) "
                      "precondition on prefix can be subverted by overwriting it. "
                      "There is no resolving patch that rewrites the program-name / "
                      "flag prefix, so a verifying rival here is a pure "
                      "verify-not-resolve artifact (vacuous satisfaction).",
        "rationale": "MANDATORY frame-mutation probe. `prefix[0] = dbname` writes "
                     "through a 1/2 read-only reference and MUST fail for "
                     "INSUFFICIENT PERMISSION (a store needs full "
                     "Acc(list_pred(prefix))), NOT a value mismatch; the gold "
                     "invariants/asserts are kept verbatim so the rejection is "
                     "attributable to the write. Rejection source: the PERMISSION "
                     "SYSTEM. If it verified => SPEC-TOO-WEAK (frame protection "
                     "hollow).",
    },

    # ------------------------------------------------------------------ #
    # 4. FRAME-MUTATION on `parameters` (supporting). parameters is also   #
    #    read-only at Acc(...,1/2). This rival WRITES `parameters[0] =     #
    #    dbname` before the params loop. Same permission failure as case 3 #
    #    but on the second read-only input. MUST fail for INSUFFICIENT     #
    #    PERMISSION. Confirms BOTH 1/2 inputs are frame-protected.          #
    # ------------------------------------------------------------------ #
    {
        "id": "frame-mutate-parameters",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    j = 0\n    while j < len(parameters):",
            "    parameters[0] = dbname   # WRITE through a 1/2 (read-only) reference\n"
            "    j = 0\n    while j < len(parameters):",
        ),
        "refinement": "the caller-supplied extra arguments are passed through "
                      "VERBATIM by settings_to_cmd_args_env (args.extend(parameters)) "
                      "— no faithful patch rewrites an element of `parameters`. The "
                      "rival overwrites parameters[0] through a 1/2 reference purely "
                      "to test frame protection on the second read-only input; no "
                      "resolving patch mutates the extras, so a verifying rival is a "
                      "verify-not-resolve artifact.",
        "rationale": "frame-mutation probe on the second 1/2 input. "
                     "`parameters[0] = dbname` needs FULL Acc(list_pred(parameters)) "
                     "but only 1/2 is held, so it MUST fail for INSUFFICIENT "
                     "PERMISSION. Gold invariants/asserts kept verbatim => rejection "
                     "attributable to the write. Rejection source: the PERMISSION "
                     "SYSTEM. If it verified => SPEC-TOO-WEAK.",
    },

    # ------------------------------------------------------------------ #
    # 5. PARTIAL-DOMAIN / ORDERING — the PRINCIPAL reasoned attack: the    #
    #    PRE-PATCH ordering. Append the dbname token BEFORE the parameters #
    #    loop, yielding prefix ++ [dbname] ++ params. This is EXACTLY the   #
    #    bug the gold patch fixes (== model_prepatch.py). Correct on the    #
    #    not-has_dbname sub-domain (E2 unaffected: no token to misorder),   #
    #    WRONG on has_dbname (E1 demands extras BEFORE dbname). The loop    #
    #    invariants are adjusted to remain internally consistent with the   #
    #    pre-patch ordering (mirrors model_prepatch.py) so the rival is     #
    #    self-consistent and the ONLY remaining discriminator is (E1).      #
    #    Must REJECT on (E1).                                                #
    #    REFINEMENT: this is the literal pre-patch code (`args += [dbname]` #
    #    BEFORE `args.extend(parameters)`) — exactly what the F2P test      #
    #    test_parameters was rewritten to catch (now expects                #
    #    ["psql","--help","dbname"], not ["psql","dbname","--help"]). A     #
    #    faithful patch with this ordering FAILS the F2P test, so it does   #
    #    NOT resolve. A verifying rival would be a true verify-not-resolve  #
    #    break.                                                              #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-prepatch-ordering",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            """    result = []  # type: List[int]
    i = 0
    while i < len(prefix):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(prefix))
        Invariant(ToSeq(result) == ToSeq(prefix).take(i))
        Invariant(MustTerminate(len(prefix) - i + 1))
        # invariants-end
        result.append(prefix[i])
        Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
        i = i + 1
    Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
    # PRE-PATCH BUG: dbname appended BEFORE the extra arguments.
    if has_dbname:
        result.append(dbname)
    j = 0
    while j < len(parameters):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(parameters), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(parameters))
        Invariant(ToSeq(result)
                  == ToSeq(prefix)
                  + (PSeq(dbname) if has_dbname else PSeq(dbname).take(0))
                  + ToSeq(parameters).take(j))
        Invariant(MustTerminate(len(parameters) - j + 1))
        # invariants-end
        result.append(parameters[j])
        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
               == ToSeq(parameters).take(j + 1))
        j = j + 1
    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
    return result""",
        ),
        "refinement": "this is the literal PRE-PATCH ordering — `if dbname: args "
                      "+= [dbname]` BEFORE `args.extend(parameters)` (the diff "
                      "swaps these two lines). It produces ['psql','dbname','--help'] "
                      "for the F2P input, but test_parameters was rewritten to "
                      "expect ['psql','--help','dbname']; the faithful pre-patch "
                      "code FAILS the F2P test, so it does NOT resolve. A verifying "
                      "rival here would be a true verify-not-resolve break.",
        "rationale": "rejection comes from postcondition (E1) "
                     "Implies(has_dbname, ToSeq(Result()) == "
                     "ToSeq(prefix)+ToSeq(parameters)+PSeq(dbname)): this rival "
                     "produces prefix++[dbname]++params, so for any non-empty "
                     "parameters with has_dbname the dbname token precedes the "
                     "extras and (E1) is violated.",
    },

    # ------------------------------------------------------------------ #
    # 6. PARTIAL-DOMAIN — DROP the dbname token entirely (never append it).#
    #    Returns prefix ++ params unconditionally. Correct on the          #
    #    not-has_dbname sub-domain (E2 holds), WRONG on has_dbname (E1      #
    #    demands a trailing dbname token). Must REJECT on (E1).             #
    #    REFINEMENT: a patch that deletes the `if dbname: args += [dbname]` #
    #    block omits the database name from the connection command, so      #
    #    `psql` connects to the wrong/default DB — it FAILS the P2P tests   #
    #    that pass a NAME (e.g. test_basic expects 'dbname' in the args)    #
    #    and the F2P test (expects 'dbname' trailing). It does NOT resolve. #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-drop-dbname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_TAIL,
            "    # WRONG: never append the database-name token at all.\n"
            "    return result",
        ),
        "refinement": "deleting the `if dbname: args += [dbname]` append drops the "
                      "database name from the psql command line, so the shell "
                      "connects to the default DB instead of the configured NAME. "
                      "This FAILS both the F2P test_parameters (expects the trailing "
                      "'dbname' token) and the P2P test_basic (expects 'dbname' in "
                      "the args), so its faithful real patch does NOT resolve.",
        "rationale": "rejection comes from postcondition (E1) "
                     "Implies(has_dbname, ToSeq(Result()) == "
                     "ToSeq(prefix)+ToSeq(parameters)+PSeq(dbname)): with has_dbname "
                     "True the result must end with PSeq(dbname), but this rival "
                     "returns prefix++params with no trailing token.",
    },

    # ------------------------------------------------------------------ #
    # 7. PARTIAL-DOMAIN / ORDERING — extras BEFORE the prefix segment.     #
    #    Run the parameters loop FIRST, then the prefix loop, then dbname, #
    #    yielding params ++ prefix ++ [dbname]. The prefix segment carries  #
    #    the program name (psql) and the -U/-h/-p flags, which MUST lead.   #
    #    Correct only when prefix is empty (never, the program name is      #
    #    always present), WRONG otherwise. Must REJECT on (E1)/(E2) (both   #
    #    pin prefix FIRST). The two loops + their invariants are adjusted    #
    #    to the swapped order so the rival is self-consistent; the ONLY     #
    #    remaining discriminator is the segment-1-first ordering.           #
    #    REFINEMENT: a patch that built [parameters..., psql, -U, ...,      #
    #    dbname] puts the program name AFTER the options — psql would not   #
    #    even be invoked correctly (argv[0] must be the program). It FAILS  #
    #    every dbshell test (test_basic expects 'psql' first), so it does   #
    #    NOT resolve.                                                        #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-prefix-after-params",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            """    result = []  # type: List[int]
    j = 0
    while j < len(parameters):
        # invariants-start
        Invariant(Acc(list_pred(parameters), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(parameters))
        Invariant(ToSeq(result) == ToSeq(parameters).take(j))
        Invariant(MustTerminate(len(parameters) - j + 1))
        # invariants-end
        result.append(parameters[j])
        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
               == ToSeq(parameters).take(j + 1))
        j = j + 1
    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
    i = 0
    while i < len(prefix):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(parameters), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(prefix))
        Invariant(ToSeq(result) == ToSeq(parameters) + ToSeq(prefix).take(i))
        Invariant(MustTerminate(len(prefix) - i + 1))
        # invariants-end
        result.append(prefix[i])
        Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
        i = i + 1
    Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
    if has_dbname:
        result.append(dbname)
    return result""",
        ),
        "refinement": "a patch that emitted [*parameters, psql, -U, ..., dbname] "
                      "places the program name AFTER the user-supplied options — "
                      "argv[0] is no longer 'psql', so the shell is never invoked "
                      "correctly. It FAILS every dbshell test (test_basic expects "
                      "'psql' as the first token), so its faithful real patch does "
                      "NOT resolve.",
        "rationale": "rejection comes from (E1)/(E2), both of which pin the result "
                     "to begin with ToSeq(prefix): this rival builds "
                     "params++prefix(++[dbname]), so whenever both segments are "
                     "non-empty the leading token is a parameter, not the prefix, "
                     "and the postcondition is violated.",
    },
]


# No @ContractOnly axioms and no A-reference deep models (meta.axioms == [],
# deep_model_references == []; refinement.md §C, mapping.md §3, G-AX vacuous).
# The one changed operation — reordering `args.extend(parameters)` past the
# `if dbname: args += [dbname]` block — is pure in-process list construction
# (no library callee participates), modelled deeply with list.append in the
# impl and PSeq concatenation in the postcondition. There is therefore no
# axiom-soundness / axiom-containment obligation.
AXIOM_TESTS = []
