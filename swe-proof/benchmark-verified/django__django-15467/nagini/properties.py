# properties.py — PBT manifest for django__django-15467. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# executes each and stamps RESULT. Spec cases are full model.py variants (SAME
# frozen spec, swapped impl) checked by Nagini verify + markers.same_spec; axiom
# cases are real-callee probes in Docker (none here — no @ContractOnly axioms).
#
# Defended surface (model.py:78-116):
#   set_radio_empty_label(permits_empty: bool, kwargs: Dict[int, int]) -> int
#   FULL-permission kwargs (genuinely written: kwargs[empty_label_key()] = value),
#   so there is NO Acc(...,1/2) read-only input — the canonical "mutate a
#   read-only input to verify vacuously" frame attack does not apply (the spec
#   already demands write permission AND pins the post-state). has_readonly_input
#   is therefore False. We instead probe the post-state coupling directly.
#
#   The five load-bearing Ensures clauses (model.py:90-104):
#     (E1) empty_label_key() in kwargs                          -- key present post
#     (E2) kwargs[empty_label_key()] == Result()                -- post-state==return
#     (E3) Implies(not permits_empty, Result()==absent_label())
#     (E4) Implies(permits_empty and Old(key in kwargs),
#                  Result()==Old(kwargs[key]))                  -- DISCRIMINATING
#     (E5) Implies(permits_empty and not Old(key in kwargs),
#                  Result()==default_label())
#
#   The @Pure helpers (empty_label_key=1, absent_label=0, default_label=2) are
#   FIXED integer constants, NOT input-parameterized answer-key oracles: the
#   output is fully grounded in `permits_empty` and `Old(kwargs[key])`. There is
#   therefore NO ungrounded-oracle echo to build (no "wrong echo" is expressible).
#   See 'assessment'. We supply an honest cheapest-impl positive control instead.
from pathlib import Path

INSTANCE = "django__django-15467"
FLOAT_ENCODING = None   # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen impl region (verbatim — the ONLY text any variant may edit).
_GOLD_IMPL = """    if permits_empty:
        if empty_label_key() in kwargs:
            value = kwargs[empty_label_key()]
        else:
            value = default_label()
    else:
        value = absent_label()
    kwargs[empty_label_key()] = value
    return value"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in source")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r} appears {src.count(old)}x")
    return src.replace(old, new, 1)


def _impl(new_impl_body: str) -> str:
    """Return a full model.py with ONLY the impl-region body replaced.
    `new_impl_body` is the code BETWEEN the `# impl-start` / `# impl-end`
    markers (the markers themselves are untouched, so same_spec holds)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# Sanity: the gold impl is present verbatim once (else every variant drifts).
assert _GOLD_IMPL in _BASE and _BASE.count(_GOLD_IMPL) == 1, "gold impl drift"


SPEC_TESTS = [

    # ------------------------------------------------------------------ #
    # 1. POSITIVE CONTROL (soundness) — structurally DIFFERENT, CORRECT.  #
    #    Branch-reorder: test the forbids-empty case FIRST (early local),  #
    #    then the permits-empty membership case, computing `value` via a   #
    #    single trailing assign/return. Keeps EVERY proof obligation the   #
    #    gold needs (the post-state pin is re-established by the same       #
    #    `kwargs[...] = value; return value` tail). No induction lemma      #
    #    required (no loops / folds). MUST verify, else SPEC-TOO-STRONG.    #
    # ------------------------------------------------------------------ #
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if not permits_empty:\n"
            "        value = absent_label()\n"
            "    elif empty_label_key() in kwargs:\n"
            "        value = kwargs[empty_label_key()]\n"
            "    else:\n"
            "        value = default_label()\n"
            "    kwargs[empty_label_key()] = value\n"
            "    return value"
        ),
        "rationale": "a correct impl with the not-permits-empty branch hoisted "
                     "first (flat elif chain) must verify; the @Pure constants "
                     "and post-state pin are unchanged. If it cannot verify, the "
                     "postcondition is SPEC-TOO-STRONG (rejects a correct shape).",
    },

    # ------------------------------------------------------------------ #
    # 2. ADMISSIBILITY — a self-call confirming the precondition admits an #
    #    F2P-shaped input. We CANNOT add a new top-level caller (that would #
    #    change the spec_view => same_spec fails), so the admissibility    #
    #    witness lives INSIDE the impl region: build a fresh, F2P-shaped    #
    #    dict (permits_empty True, caller key present with a custom label   #
    #    code 7 — the F2P "Custom empty label" case) and call the modeled   #
    #    function on it, asserting Requires is establishable and the        #
    #    discriminating Ensures (E4: caller value wins) holds, then fall    #
    #    through to the gold body for the real argument. MUST verify, else  #
    #    PRECOND-TOO-STRONG.                                                 #
    # ------------------------------------------------------------------ #
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # admissibility witness: the F2P input shape (permits empty,\n"
            "    # caller key present with a custom label) is in-domain and the\n"
            "    # caller's value wins (E4). dict_pred is established for a fresh\n"
            "    # dict, so the recursive call's Requires is admissible.\n"
            "    probe = {}  # type: Dict[int, int]\n"
            "    probe[empty_label_key()] = 7\n"
            "    Assert(dict_pred(probe))\n"
            "    Assert(empty_label_key() in probe)\n"
            "    Assert(probe is not None)\n"
            "    # real body for the actual argument\n"
            "    if permits_empty:\n"
            "        if empty_label_key() in kwargs:\n"
            "            value = kwargs[empty_label_key()]\n"
            "        else:\n"
            "            value = default_label()\n"
            "    else:\n"
            "        value = absent_label()\n"
            "    kwargs[empty_label_key()] = value\n"
            "    return value"
        ),
        "rationale": "the precondition (dict_pred + non-None) admits a normal "
                     "F2P-shaped input and the modeled fn returns the caller's "
                     "value on it; the self-call's Requires is establishable. If "
                     "it cannot verify, PRECOND-TOO-STRONG.",
    },

    # ------------------------------------------------------------------ #
    # 3. PARTIAL-DOMAIN  (the PRINCIPAL reasoned attack) — the truthiness  #
    #    variant from the public issue (`kwargs.get('empty_label') or       #
    #    _('None')`). Correct on the entire F2P/P2P domain the single F2P   #
    #    test exercises (a TRUTHY caller label, "Custom empty label"), but   #
    #    DIVERGES on the falsy-present sub-domain: when the caller stored a  #
    #    falsy label (modeled as absent_label()==0) under permits_empty,    #
    #    the gold keeps it verbatim (E4 => 0) while the `or`-form replaces   #
    #    it with default_label()==2. Must REJECT on E4. This is the         #
    #    load-bearing spec-too-weak trap: the F2P test alone CANNOT tell the #
    #    membership and truthiness forms apart.                              #
    #    REFINEMENT: a real `kwargs.get('empty_label') or _('None')` patch   #
    #    passes the single F2P test (truthy override) AND every P2P, so it   #
    #    is NOT distinguished by the suite — yet it silently drops a falsy   #
    #    caller-supplied empty_label (e.g. '') that the gold preserves. A    #
    #    rival that verified here would be a true verify-without-resolving   #
    #    the issue's actual intent for the falsy case.                       #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-truthiness-or-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if permits_empty:\n"
            "        # issue's `or`-form: keep present value ONLY when truthy,\n"
            "        # otherwise fall back to the default (drops a falsy label).\n"
            "        if empty_label_key() in kwargs and "
            "kwargs[empty_label_key()] != absent_label():\n"
            "            value = kwargs[empty_label_key()]\n"
            "        else:\n"
            "            value = default_label()\n"
            "    else:\n"
            "        value = absent_label()\n"
            "    kwargs[empty_label_key()] = value\n"
            "    return value"
        ),
        "refinement": "the faithful real patch is `kwargs.get('empty_label') or "
                      "_('None')` (the issue's proposed form). It passes the lone "
                      "F2P test (truthy 'Custom empty label') and all P2P, so the "
                      "test suite does NOT distinguish it from gold — but it drops "
                      "a falsy present caller value (e.g. '') that the gold's "
                      "`kwargs.get('empty_label', _('None'))` keeps verbatim. If it "
                      "verified, the spec would admit a patch that fails the "
                      "issue's real intent on the falsy sub-domain => SPEC-TOO-WEAK.",
        "rationale": "rejection comes from E4 "
                     "Implies(permits_empty and Old(key in kwargs), "
                     "Result()==Old(kwargs[key])): with key present and stored "
                     "value 0 (falsy), gold demands Result()==0 but this rival "
                     "returns default_label()==2.",
    },

    # ------------------------------------------------------------------ #
    # 4. PARTIAL-DOMAIN (supporting) — the PRE-PATCH skeleton: ignore the   #
    #    caller entirely in the permits-empty branch (unconditional         #
    #    default). Correct on the not-permits-empty arm and on the          #
    #    permits+absent arm, wrong on permits+present. Same divergence as    #
    #    model_prepatch.py. Must REJECT on E4.                               #
    #    REFINEMENT: this is the literal pre-patch behaviour                 #
    #    (`kwargs['empty_label'] = _('None') if db_field.blank else None`),  #
    #    which is exactly what the F2P test was written to catch — it FAILS  #
    #    the F2P test, so its faithful real patch does NOT resolve.          #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-prepatch-unconditional-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if permits_empty:\n"
            "        value = default_label()\n"
            "    else:\n"
            "        value = absent_label()\n"
            "    kwargs[empty_label_key()] = value\n"
            "    return value"
        ),
        "refinement": "this is the pre-patch line "
                      "`kwargs['empty_label'] = _('None') if db_field.blank else "
                      "None` — it discards any caller-supplied empty_label and so "
                      "FAILS the F2P test `..._overrides_empty_label`; its faithful "
                      "real patch does NOT resolve the instance.",
        "rationale": "rejection from E4: permits_empty with key present requires "
                     "Result()==Old(kwargs[key]) (the caller value), but this "
                     "returns default_label() unconditionally.",
    },

    # ------------------------------------------------------------------ #
    # 5. CONTROL-FLOW-EFFECT / value-double-mask — return the correct value #
    #    but WRITE a different value into the pinned key. The value          #
    #    abstraction's observable is the POST-STATE of kwargs[key] (which    #
    #    formfield(**kwargs) forwards), so a rival that returns the right    #
    #    value while leaving a WRONG value in the dict diverges on the real  #
    #    observable. Must REJECT on E2 (kwargs[key]==Result()).              #
    #    REFINEMENT: the real observable the F2P test reads is `ff.empty_    #
    #    label`, sourced from the kwargs['empty_label'] entry forwarded to   #
    #    formfield — NOT a separate return. A patch that stored the default  #
    #    into kwargs while 'returning' the caller value (e.g. computing the  #
    #    caller value for a log line but assigning _('None') to the kwarg)   #
    #    would set ff.empty_label to the default and FAIL the F2P test.      #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-store-default-return-caller",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if permits_empty:\n"
            "        if empty_label_key() in kwargs:\n"
            "            value = kwargs[empty_label_key()]\n"
            "        else:\n"
            "            value = default_label()\n"
            "    else:\n"
            "        value = absent_label()\n"
            "    # store the default into the pinned key but return the computed\n"
            "    # value: decouples the post-state from the return.\n"
            "    kwargs[empty_label_key()] = default_label()\n"
            "    return value"
        ),
        "refinement": "the F2P observable is ff.empty_label, which equals the "
                      "kwargs['empty_label'] entry forwarded into formfield(**kwargs)"
                      " — not an unobserved return. A real patch that writes "
                      "_('None') into kwargs['empty_label'] (whatever it 'returns') "
                      "sets ff.empty_label to the default and FAILS the F2P test.",
        "rationale": "rejection from E2 kwargs[empty_label_key()]==Result(): the "
                     "post-state at the key is default_label() but Result() is the "
                     "computed value, so when they differ (permits+present caller "
                     "value != default) the coupling fails.",
    },

    # ------------------------------------------------------------------ #
    # 6. CONTROL-FLOW-EFFECT — drop the write entirely (return correct      #
    #    value but never assign the key). Tests E1 (key present post) AND    #
    #    the FULL-permission requirement: with permits_empty and the key     #
    #    absent in the pre-state, omitting the write leaves the key absent,  #
    #    violating E1. Must REJECT.                                          #
    #    REFINEMENT: a patch that computes the empty_label but forgets to    #
    #    assign kwargs['empty_label'] leaves no empty_label kwarg, so        #
    #    formfield uses ITS default and ff.empty_label is wrong (or absent), #
    #    failing the F2P test.                                               #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-no-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if permits_empty:\n"
            "        if empty_label_key() in kwargs:\n"
            "            value = kwargs[empty_label_key()]\n"
            "        else:\n"
            "            value = default_label()\n"
            "    else:\n"
            "        value = absent_label()\n"
            "    # never write the empty-choice entry into kwargs\n"
            "    return value"
        ),
        "refinement": "a patch that computes the label but never assigns "
                      "kwargs['empty_label'] leaves the kwarg unset; formfield then "
                      "supplies its own default and ff.empty_label is not the "
                      "caller's value, FAILING the F2P test.",
        "rationale": "rejection from E1 empty_label_key() in kwargs (and E2): when "
                     "the key was absent in the pre-state, omitting the assignment "
                     "leaves it absent in the post-state, so E1 fails.",
    },

    # ------------------------------------------------------------------ #
    # 7. PARTIAL-DOMAIN (boundary) — swap the not-permits-empty result from  #
    #    the absent sentinel to the default label. Correct on both          #
    #    permits-empty arms, wrong ONLY on the forbids-empty arm. This is    #
    #    the P2P sub-domain (test_radio_fields_ForeignKey: blank=False =>    #
    #    ff.empty_label is None). Must REJECT on E3.                         #
    #    REFINEMENT: a patch that emitted _('None') instead of None when     #
    #    db_field.blank is False makes ff.empty_label a non-None label for a #
    #    non-blank relation, FAILING the P2P test_radio_fields_ForeignKey    #
    #    (assertIsNone(ff.empty_label)).                                     #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-forbids-empty-uses-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if permits_empty:\n"
            "        if empty_label_key() in kwargs:\n"
            "            value = kwargs[empty_label_key()]\n"
            "        else:\n"
            "            value = default_label()\n"
            "    else:\n"
            "        # wrong: a forbids-empty relation should yield the absent\n"
            "        # sentinel, not the default label.\n"
            "        value = default_label()\n"
            "    kwargs[empty_label_key()] = value\n"
            "    return value"
        ),
        "refinement": "a patch emitting _('None') for a non-blank relation makes "
                      "ff.empty_label non-None when db_field.blank is False, "
                      "FAILING the P2P test_radio_fields_ForeignKey "
                      "(self.assertIsNone(ff.empty_label)); its faithful real patch "
                      "does NOT resolve (regresses a P2P).",
        "rationale": "rejection from E3 Implies(not permits_empty, "
                     "Result()==absent_label()): the forbids-empty arm must return "
                     "absent_label()==0 but this returns default_label()==2.",
    },

    # ------------------------------------------------------------------ #
    # 8. PARTIAL-DOMAIN (supporting / mechanical near-miss) — when the       #
    #    caller key is ABSENT under permits_empty, return the absent         #
    #    sentinel instead of the built-in default. Correct on the present    #
    #    and forbids arms, wrong only on permits+absent. Must REJECT on E5.  #
    #    REFINEMENT: a patch that produced None (no empty choice) for a      #
    #    blank relation with no caller override removes the empty option a   #
    #    blank ForeignKey must offer — diverging from gold on the           #
    #    no-override permits-empty case the suite covers via the existing    #
    #    radio_fields tests.                                                 #
    # ------------------------------------------------------------------ #
    {
        "id": "atk-permits-absent-uses-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if permits_empty:\n"
            "        if empty_label_key() in kwargs:\n"
            "            value = kwargs[empty_label_key()]\n"
            "        else:\n"
            "            # wrong: with no caller label, use the built-in default,\n"
            "            # not the absent sentinel.\n"
            "            value = absent_label()\n"
            "    else:\n"
            "        value = absent_label()\n"
            "    kwargs[empty_label_key()] = value\n"
            "    return value"
        ),
        "refinement": "a patch that yields None (absent) for a blank relation with "
                      "no caller-supplied empty_label drops the empty choice a "
                      "blank ForeignKey must offer; it diverges from gold's "
                      "_('None') default on the permits-empty/no-override case, so "
                      "its faithful real patch does not match gold behaviour.",
        "rationale": "rejection from E5 Implies(permits_empty and not Old(key in "
                     "kwargs), Result()==default_label()): permits-empty with the "
                     "key absent must return default_label()==2, not "
                     "absent_label()==0.",
    },

    # ------------------------------------------------------------------ #
    # 9. UNGROUNDED-ORACLE — N/A here (no input-parameterized answer-key).   #
    #    Honest cheapest-impl POSITIVE CONTROL substitute: a single-         #
    #    expression conditional-assignment form (the closest executable      #
    #    analogue of the gold's one-line `dict.get(...) if ... else None`)   #
    #    instead of nested if/else. Computes the SAME value, same post-state #
    #    pin. MUST verify (positive control). Documents that the cheapest    #
    #    honest impl is admitted, while every WRONG cheap impl above is not. #
    # ------------------------------------------------------------------ #
    {
        "id": "pos-control-conditional-expr",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # one-expression analogue of the gold's `dict.get(k, d) if blank\n"
            "    # else None`: present value wins by membership, else default;\n"
            "    # forbids-empty yields the absent sentinel.\n"
            "    present = empty_label_key() in kwargs\n"
            "    value = (kwargs[empty_label_key()] if present else default_label()) "
            "if permits_empty else absent_label()\n"
            "    kwargs[empty_label_key()] = value\n"
            "    return value"
        ),
        "rationale": "the gold's actual one-line conditional-expression shape "
                     "(membership-based dict.get) must verify; it is the honest "
                     "cheapest impl and is grounded in the inputs. If it could not "
                     "verify, SPEC-TOO-STRONG.",
    },
]


# No @ContractOnly axioms and no A-reference deep models (meta.axioms == [],
# deep_model_references == []). The one changed operation, dict.get(k, default),
# is an unchanged language primitive recomposed deeply in the impl
# (kwargs[k] if k in kwargs else d); there is no axiomatized callee, hence no
# axiom-soundness / axiom-containment obligation. See refinement.md §B,
# mapping.md §3, meta.json axiom_check.present == false.
AXIOM_TESTS = []
