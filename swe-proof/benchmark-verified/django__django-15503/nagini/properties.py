"""properties.py — PBT falsification manifest for django__django-15503.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The bundle models the single changed function of the gold
patch — the new `HasKeyLookup.compile_json_path_final_key`, which compiles the
FINAL key of a key-membership test into the object-member JSON path step
`."key"` for EVERY key (numeric or not), so a numeric key like "1111"/"000" no
longer becomes the array-element step `[1111]`/`[0]`. There are NO @ContractOnly
axioms (meta.axioms == []), so AXIOM_TESTS == []. The A-reference deep model
(`member_access_segment` / `json_string_literal`) is validated == the real
django callee (`".%s" % json.dumps(key)`) by axiom_check.py (G-AX), out-of-band
of this PBT.

THE DEFENDED SURFACE
--------------------
`compile_final_key_segment(key: List[int]) -> List[int]`
    Reads a key (a `str`, modelled as a `List[int]` of Unicode code points) held
    at `Acc(list_pred(key), 1/2)` — READ-ONLY — and returns the final path step.
    The key domain is `in_domain(ToSeq(key))`: printable ASCII 32..126 minus the
    double quote (34) and backslash (92), exactly where `json.dumps` is the
    verbatim quote-wrap. The LOAD-BEARING postcondition pins the WHOLE sequence:

        Ensures(ToSeq(Result()) == member_access_segment(ToSeq(key)))
        #  member_access_segment(k) = PSeq(46) + PSeq(34) + k + PSeq(34)
        #                           = '.'      + '"'      + key + '"'
    plus the explicit structural pins that fall out of it:
        Ensures(len(Result()) == len(key) + 3)
        Ensures(Result()[0] == 46)                       # '.'
        Ensures(Result()[1] == 34)                       # opening '"'
        Ensures(Result()[len(Result()) - 1] == 34)       # closing '"'
        Ensures(Forall i in [0,len(key)): Result()[i+2] == key[i])  # verbatim

    `member_access_segment(ToSeq(key))` is GROUNDED in the input: it is a
    syntactic function of `key` (a `@Pure` concatenation `PSeq(46)+PSeq(34)+key
    +PSeq(34)`, fully unfolded by Viper), NOT an opaque answer-key oracle. There
    is therefore NO wrong constant an impl could echo to satisfy the
    full-sequence equality — see the ungrounded-oracle note below; instead the
    spec is exercised by an honest cheapest-impl positive control.

ATTACKS THIS SPEC MUST SURVIVE
------------------------------
  * FRAME-MUTATION (MANDATORY: `key` is Acc(list_pred(key),1/2) read-only):
    `frame-mutate-key` writes through `key` before/while reading it. It must
    fail for INSUFFICIENT PERMISSION (a store needs full permission; only 1/2
    is held). The gold postcondition is kept verbatim so the rejection is
    attributable to the WRITE, not to a weakened spec. A byte-fuzzer never finds
    this — it is the project's #1 weakness class.

  * UNGROUNDED-ORACLE ECHO is N/A here: the postcondition equality pins the whole
    sequence to `member_access_segment(ToSeq(key))`, a function of the arg fully
    unfolded by the verifier. There is no opaque marker / answer-key constant to
    echo without doing the work (any constant-returning impl fails the verbatim
    Forall and the length pin). Per directive 2, the honest cheapest-impl
    positive control `honest-cheapest` stands in: the cheapest faithful impl
    still has to copy each `key[i]` between the fixed `.\"` prefix and `\"`
    suffix; it must verify.

  * PARTIAL-DOMAIN:
    - `prepatch-array-index` is the actual pre-patch bug surface: for an
      all-digit key emit the array-element step `[` + key + `]` (code points
      91/93) instead of the member-access step. It is "correct"-shaped for the
      array routing but is the exact F2P discriminator; it must reject (this is
      the behaviour `model_prepatch.py` encodes).
    - `drop-last-char` pins all but the final key character (off-by-one on the
      loop bound), correct on the empty-key/short sub-domain but wrong whenever
      `len(key) >= 1`.
    - `skip-first-char` pins all but the first key character, the symmetric
      off-by-one.

  * VALUE-LEVEL DOUBLE-MASK / wrong-quote: `wrong-quote` emits a single quote
    (39) instead of the JSON double quote (34) around the key. The full-sequence
    equality AND the explicit `Result()[1]==34` / closing-quote pins reject it —
    the postcondition is not a value-proxy that could drop a disagreeing index.

  * POSITIVE CONTROL (soundness): `pos-prefix-reshape` is a structurally-
    different but CORRECT impl — it builds the `.\"` prefix by two separate
    one-element appends (`[46]` then `+[34]`) instead of the `[46,34]` literal,
    and keeps the loop with the SAME gold invariants verbatim (so no proof
    obligation is dropped — directive 2). It must verify (else SPEC-TOO-STRONG).

  * ADMISSIBILITY: `admiss-numeric-key` self-calls compile_final_key_segment on
    an F2P-shaped numeric key "123" (code points [49,50,51], in_domain holds)
    and asserts the precondition is establishable and the result length is
    len(key)+3. If the call cannot establish Requires => PRECOND-TOO-STRONG.

  CONTROL-FLOW-EFFECT is N/A: compile_final_key_segment is a pure value
  computation — there is no raise / early-return / side-effect path that the
  value abstraction misses; the only observable is the returned sequence, and it
  is pinned in full by the equality clause. No capability-token rival is needed.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end` (the swap anchors include the
nested `# invariants-start/end` block, which the spec_view elides, so it is part
of the impl region for same_spec purposes). `markers.same_spec` is therefore
guaranteed and a rejection comes from the POSTCONDITION (or the permission
system), never from a tampered spec. Each `expect:"reject"` rival carries the
refinement argument that its faithful real patch would NOT resolve the F2P
(`test_has_key_number` / `test_has_keys`, which exercise numeric object keys
"123"/"456"/"999"/"789"/"777"/"000").
"""
from pathlib import Path

INSTANCE = "django__django-15503"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError("drift: %r not in model.py" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r (%d)" % (old, src.count(old)))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl region (verbatim, the surgery anchor). It spans the nested
# invariants block, which spec_view elides — so editing inside it is same_spec.
# ---------------------------------------------------------------------------
_GOLD_IMPL = (
    "    result = [46, 34]  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(key):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(key), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(key))\n"
    "        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))\n"
    "        Invariant(MustTerminate(len(key) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [key[i]]\n"
    "        i = i + 1\n"
    "    result = result + [34]\n"
    "    return result\n"
)


def _impl(new_body: str) -> str:
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ===========================================================================
# SPEC CASES
# ===========================================================================
SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): structurally-different CORRECT impl ------

    # Build the '.\"' prefix as two separate one-element appends ([46] then
    # +[34]) instead of the [46,34] literal. The loop is kept IDENTICAL with the
    # SAME gold invariants verbatim (no proof obligation dropped — directive 2):
    # at loop entry ToSeq(result) == PSeq(46)+PSeq(34) == PSeq(46,34), so the
    # invariant `ToSeq(result) == PSeq(46,34) + ToSeq(key).take(i)` still holds.
    # A faithful correct impl in a different shape MUST verify.
    {"id": "pos-prefix-reshape", "kind": "soundness", "expect": "verify",
     "module": _impl(
         "    result = [46]  # type: List[int]\n"
         "    result = result + [34]\n"
         "    i = 0\n"
         "    while i < len(key):\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(key), 1 / 2))\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        Invariant(0 <= i and i <= len(key))\n"
         "        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))\n"
         "        Invariant(MustTerminate(len(key) - i + 1))\n"
         "        # invariants-end\n"
         "        result = result + [key[i]]\n"
         "        i = i + 1\n"
         "    result = result + [34]\n"
         "    return result\n"),
     "rationale": "structurally-different but CORRECT: builds the '.\"' prefix by "
                  "two one-element appends ([46] then +[34]) rather than the "
                  "[46,34] literal, keeping the loop and ALL gold invariants "
                  "verbatim so no proof obligation is dropped. ToSeq(result) at "
                  "loop entry is PSeq(46)+PSeq(34)==PSeq(46,34), so the framing "
                  "invariant still discharges. Must verify (else SPEC-TOO-"
                  "STRONG)."},

    # honest cheapest positive control for the grounded oracle: the oracle is a
    # function of the arg (PSeq(46)+PSeq(34)+key+PSeq(34)), so the cheapest
    # faithful impl still has to copy each key[i] verbatim — there is no echo
    # shortcut. This IS the gold body (left unchanged); it must verify, proving
    # the spec is satisfiable by honest per-character work.
    {"id": "honest-cheapest", "kind": "soundness", "expect": "verify",
     "module": _impl(_GOLD_IMPL),
     "rationale": "grounded-oracle positive control: member_access_segment(key) "
                  "is a function of the arg (fully unfolded), so the cheapest "
                  "faithful impl still copies every key[i] between the fixed "
                  "'.\"' prefix and '\"' suffix. No constant-echo shortcut exists "
                  "for a grounded oracle. Must verify."},

    # -- ADMISSIBILITY: precondition admits an F2P-shaped numeric key ----------

    # The F2P (test_has_key_number) exercises numeric object keys including
    # "123"/"000". Self-call compile_final_key_segment on "123" ([49,50,51],
    # which is in_domain) and assert the result length is len(key)+3 == 6.
    {"id": "admiss-numeric-key", "kind": "admissibility", "expect": "verify",
     "module": _impl(_GOLD_IMPL +
                     "\n"
                     "\n"
                     "def _admiss_caller() -> None:\n"
                     "    # F2P shape: a numeric object key \"123\" -> [49,50,51].\n"
                     "    # in_domain holds (digits are printable ASCII, not\n"
                     "    # quote/backslash). A normal input must establish\n"
                     "    # Requires (else PRECOND-TOO-STRONG).\n"
                     "    k = [49, 50, 51]  # type: List[int]\n"
                     "    Assert(in_domain(ToSeq(k)))\n"
                     "    seg = compile_final_key_segment(k)\n"
                     "    Assert(len(seg) == 6)\n"),
     "rationale": "the precondition (Acc(list_pred(key),1/2) + in_domain) must "
                  "accept the F2P-shaped numeric key \"123\". in_domain holds for "
                  "decimal digits, so the self-call establishes Requires and the "
                  "result has length len(key)+3==6. If it cannot => PRECOND-TOO-"
                  "STRONG."},

    # -- FRAME-MUTATION (MANDATORY: `key` is Acc(list_pred(key),1/2) read-only) -

    # WRITE through `key` (held at 1/2) before reading it. Storing key[0]=34
    # would let an impl claim the input already carries the quote — but a store
    # through a 1/2 list_pred is INSUFFICIENT PERMISSION, so it must reject. The
    # gold postcondition is kept verbatim (the loop still reads key[i]); the
    # rejection is attributable to the WRITE, not to a weakened spec.
    {"id": "frame-mutate-key", "kind": "uniqueness", "expect": "reject",
     "module": _impl(
         "    result = [46, 34]  # type: List[int]\n"
         "    if len(key) > 0:\n"
         "        key[0] = 34  # write through 1/2 permission -> insufficient\n"
         "    i = 0\n"
         "    while i < len(key):\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(key), 1 / 2))\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        Invariant(0 <= i and i <= len(key))\n"
         "        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))\n"
         "        Invariant(MustTerminate(len(key) - i + 1))\n"
         "        # invariants-end\n"
         "        result = result + [key[i]]\n"
         "        i = i + 1\n"
         "    result = result + [34]\n"
         "    return result\n"),
     "refinement": "the real compile_json_path_final_key receives the key_transform "
                   "string (the last element of rhs_key_transforms) and only READS "
                   "it via json.dumps(key_transform); it never mutates the key. A "
                   "patch that overwrote the key characters would emit the wrong "
                   "JSON path step and the F2P (test_has_key_number, which checks "
                   "the membership SQL recovers keys \"123\"/\"000\"/...) would "
                   "fail. A mutating impl does NOT produce gold output, so it "
                   "would NOT resolve.",
     "rationale": "MANDATORY frame-mutation probe. `key[0] = 34` writes through "
                  "Acc(list_pred(key),1/2). Nagini requires FULL permission for a "
                  "store; with only 1/2 the assignment fails for INSUFFICIENT "
                  "PERMISSION. Rejection comes from the permission system, not the "
                  "postcondition (which is kept verbatim)."},

    # -- PARTIAL-DOMAIN: the pre-patch array-index bug (F2P discriminator) ------

    # The actual pre-patch behaviour for an all-digit key: emit the array-element
    # step '[' + key + ']' (code points 91/93) instead of the member-access step
    # '.\"' + key + '\"'. This is what model_prepatch.py encodes. Result()[0]
    # would be 91 (not 46), Result()[1] would be the first key digit (not 34),
    # and the full-sequence equality to member_access_segment fails.
    {"id": "prepatch-array-index", "kind": "uniqueness", "expect": "reject",
     "module": _impl(
         "    result = [91]  # type: List[int]\n"
         "    i = 0\n"
         "    while i < len(key):\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(key), 1 / 2))\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        Invariant(0 <= i and i <= len(key))\n"
         "        Invariant(ToSeq(result) == PSeq(91) + ToSeq(key).take(i))\n"
         "        # invariants-end\n"
         "        result = result + [key[i]]\n"
         "        i = i + 1\n"
         "    result = result + [93]\n"
         "    return result\n"),
     "refinement": "this IS the pre-patch array-element form (the unchanged "
                   "compile_json_path routed the final numeric key through the "
                   "`[%s] % int(key)` branch -> '[1111]'/'[0]'). It is the exact "
                   "F2P discriminator: test_has_key_number asserts a numeric "
                   "object key \"123\"/\"000\" is found via the object-member "
                   "path '.\"123\"', NOT the array-index path '[123]' (and the "
                   "array form even drops leading zeros, '000' -> '[0]'). A patch "
                   "keeping the array form does NOT resolve (model_prepatch.py).",
     "rationale": "PARTIAL-DOMAIN / the modeled bug: the array-element shape "
                  "yields Result()[0]==91 != 46 (violates Ensures(Result()[0]"
                  "==46)), Result()[1]==key[0] != 34, and ToSeq(Result()) != "
                  "member_access_segment(ToSeq(key)). Rejection from the framing "
                  "postcondition — exactly the G-DIFF discriminator."},

    # -- PARTIAL-DOMAIN: off-by-one on the loop bound (drop the last key char) --

    # Loop to len(key)-1, dropping the final key character. Correct only on the
    # empty key; for len(key)>=1 the verbatim Forall and the length pin fail.
    {"id": "drop-last-char", "kind": "uniqueness", "expect": "reject",
     "module": _impl(
         "    result = [46, 34]  # type: List[int]\n"
         "    i = 0\n"
         "    while i < len(key) - 1:\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(key), 1 / 2))\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        Invariant(0 <= i and i <= len(key))\n"
         "        Invariant(ToSeq(result) == PSeq(46, 34) + ToSeq(key).take(i))\n"
         "        Invariant(MustTerminate(len(key) - i + 1))\n"
         "        # invariants-end\n"
         "        result = result + [key[i]]\n"
         "        i = i + 1\n"
         "    result = result + [34]\n"
         "    return result\n"),
     "refinement": "dropping the last key character emits a path step for a "
                   "DIFFERENT (truncated) key, e.g. \"123\" -> '.\"12\"'. The "
                   "membership SQL would test the wrong key and the F2P "
                   "(test_has_key_number) would not find \"123\"/\"000\". A patch "
                   "that truncates the key does NOT resolve.",
     "rationale": "PARTIAL-DOMAIN off-by-one: for len(key)>=1 the result has "
                  "length len(key)+2 != len(key)+3 (violates Ensures(len(Result())"
                  "==len(key)+3)) and the verbatim Forall (Result()[i+2]==key[i]) "
                  "fails at i==len(key)-1. Rejection from the length / verbatim "
                  "postcondition. Correct only on the empty-key sub-domain."},

    # -- PARTIAL-DOMAIN: symmetric off-by-one (skip the FIRST key char) ---------

    # Start the copy at i=1, dropping key[0]. Correct only on the empty key.
    {"id": "skip-first-char", "kind": "uniqueness", "expect": "reject",
     "module": _impl(
         "    result = [46, 34]  # type: List[int]\n"
         "    i = 1\n"
         "    while i < len(key):\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(key), 1 / 2))\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        Invariant(1 <= i)\n"
         "        # invariants-end\n"
         "        result = result + [key[i]]\n"
         "        i = i + 1\n"
         "    result = result + [34]\n"
         "    return result\n"),
     "refinement": "skipping key[0] emits a path step for a DIFFERENT key, e.g. "
                   "\"123\" -> '.\"23\"'. The membership SQL tests the wrong key "
                   "and the F2P (test_has_key_number) fails to find \"123\". A "
                   "patch that drops the first character does NOT resolve.",
     "rationale": "PARTIAL-DOMAIN off-by-one: for len(key)>=1 the result is "
                  "missing key[0], so Result()[2]==key[1] != key[0] violates the "
                  "verbatim Forall (Result()[i+2]==key[i] at i==0) and the length "
                  "pin. Rejection from the verbatim / length postcondition."},

    # -- VALUE-LEVEL DOUBLE-MASK / wrong-quote: single quote instead of double ---

    # Wrap the key in single quotes (39) instead of the JSON double quote (34).
    # The full-sequence equality AND the explicit Result()[1]==34 / closing-quote
    # pins reject it — the postcondition is not a value-proxy that drops indices.
    {"id": "wrong-quote", "kind": "uniqueness", "expect": "reject",
     "module": _impl(
         "    result = [46, 39]  # type: List[int]\n"
         "    i = 0\n"
         "    while i < len(key):\n"
         "        # invariants-start\n"
         "        Invariant(Acc(list_pred(key), 1 / 2))\n"
         "        Invariant(Acc(list_pred(result)))\n"
         "        Invariant(0 <= i and i <= len(key))\n"
         "        Invariant(ToSeq(result) == PSeq(46, 39) + ToSeq(key).take(i))\n"
         "        # invariants-end\n"
         "        result = result + [key[i]]\n"
         "        i = i + 1\n"
         "    result = result + [39]\n"
         "    return result\n"),
     "refinement": "json.dumps emits DOUBLE quotes; a step '.\\'123\\'' is not "
                   "valid JSON-path syntax for the membership operator and the "
                   "database would not match the key, so the F2P "
                   "(test_has_key_number/test_has_keys) would fail. A patch "
                   "emitting single quotes does NOT resolve.",
     "rationale": "VALUE-LEVEL DOUBLE-MASK guard: single quote (39) != double "
                  "quote (34) at positions 1 and len-1. Ensures(Result()[1]==34), "
                  "Ensures(Result()[len-1]==34) and the full-sequence equality to "
                  "member_access_segment (which uses PSeq(34)) all reject it — the "
                  "spec pins the quote glyph, not just a value proxy."},
]

# ===========================================================================
# AXIOM CASES — none.
# ===========================================================================
# meta.axioms == [] (no @ContractOnly axioms). The single A-reference deep model
# (member_access_segment / json_string_literal) is validated == the real django
# callee `".%s" % json.dumps(key)` by axiom_check.py (G-AX, stdlib json only):
# equality on the F2P keys + 30 boundary + 70000 fuzz keys (incl. an all-digit
# stress set), 0 mismatch, plus the numeric-key array-index discriminator against
# the real compile_json_path. PBT's axiom lane only covers @ContractOnly axioms /
# A-reference deep-model containment not already discharged by G-AX; here G-AX
# already executes the real callee and asserts the deep-model equality on the
# whole modelled domain, so there is no additional axiom obligation for this lane.
AXIOM_TESTS = []
