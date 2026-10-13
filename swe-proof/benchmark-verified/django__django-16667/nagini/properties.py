# properties.py — PBT manifest for django__django-16667. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# loads SPEC_TESTS / AXIOM_TESTS and stamps RESULT. Spec cases are full model.py
# variants built by region-surgery — every swap edits ONLY the text BETWEEN the
# `# impl-start` / `# impl-end` markers, so the frozen spec (axioms/pure/pre/
# post-conditions + signatures) is byte-identical and same_spec is guaranteed.
#
# Defended surface (read model.py + refinement.md + mapping.md):
#   value_from_components(all_blank: bool, all_present: bool, kind: int) -> List[int]
#   maps SelectDateWidget.value_from_datadict's reconstruction of a date from three
#   submitted components. The gold patch ADDS `except OverflowError: return "0-0-0"`.
#   The load-bearing postcondition the patch defends is:
#     Implies(all_present and not all_blank and kind == 2,
#             ToSeq(Result()) == zero_zero_zero())   # the "0-0-0" sentinel [48,45,48,45,48]
#   plus the implicit NO-RAISE contract (value_from_components declares NO Exsures,
#   so on kind 2 the constructor's DateCapacityOverflow must be CAUGHT, not escape —
#   that is exactly the prepatch bug). The other branches are pinned:
#     all_blank        -> absent_text() (the empty rendering)
#     not all_present  -> raw_value()   (== retrieve_raw(), the data.get(name)
#                         raw-retrieval callee — fully abstract, may be absent
#                         or arbitrary submitted text)
#     kind 0 -> success_text()      (== render_success(), the strftime callee)
#     kind 1 -> out_of_range_text() (== render_out_of_range(), the %-format fallback)
#     kind 0/1/2 (all-present, non-blank) -> len(ToSeq(Result())) > 0  (non-empty).
#
# NOTE on read-only inputs / FRAME-MUTATION: there is NO Acc(x,1/2) read-only
# input here. The three params are primitive value types (bool, bool, int) passed
# by value — there is no list_pred-backed input predicate to overwrite, so the
# frame-mutation weakness class is structurally N/A (see 'assessment'). The only
# Acc(list_pred(...)) is on Result() (the freshly-materialised output).
#
# NOTE on UNGROUNDED-ORACLE: the success/out-of-range/raw oracles (success_text /
# out_of_range_text / raw_value) are abstract @ContractOnly (the first two
# constrained only to len>0; raw_value fully unconstrained — the real
# data.get(name) may be None or arbitrary raw text). An impl cannot fabricate
# their exact PSeq value; the ONLY way to obtain it is to call the pinned
# materializer render_success()/render_out_of_range()/retrieve_raw(). So there is
# no "wrong echo that still verifies" — the oracle is grounded in the callee. The
# echo attack instead manifests as a CROSS-branch substitution (return the wrong
# branch's grounded text), covered by rivals weak-echo-kind2 / weak-swap-kind0.

from pathlib import Path

INSTANCE = "django__django-16667"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# the exact gold impl body between the markers (region-surgery target)
_GOLD_IMPL = (
    "    if all_blank:\n"
    "        empty = []  # type: List[int]\n"
    "        return empty\n"
    "    if all_present:\n"
    "        try:\n"
    "            date_token = construct_date(kind)\n"
    "            return render_success()\n"
    "        except DateOutOfRange:\n"
    "            return render_out_of_range()\n"
    "        except DateCapacityOverflow:\n"
    "            result = [48, 45, 48, 45, 48]  # type: List[int]\n"
    "            return result\n"
    "    return retrieve_raw()\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Return _BASE with the gold impl body replaced by `new_body` (both are the
    text strictly between # impl-start and # impl-end, so the spec is untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ----------------------------------------------------------------------------
# SPEC LANE
# ----------------------------------------------------------------------------
SPEC_TESTS = [

    # ---- POSITIVE CONTROL (soundness): structurally-different CORRECT impl ----
    # Reorder the branch cascade: handle the not-all-present raw fallback FIRST
    # via a guard, then the all-blank absent case, then the all-present
    # construction with the `try` un-nested from any `if`. Same observable
    # behaviour, different control shape. The except order is also flipped
    # (overflow before out-of-range) — independent classes, so order is
    # irrelevant to correctness. Keeps the same grounded callees
    # (retrieve_raw / render_success / render_out_of_range) and the same
    # sentinel code points. Must VERIFY (else SPEC-TOO-STRONG).
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if not all_present:\n"
            "        return retrieve_raw()\n"
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    try:\n"
            "        date_token = construct_date(kind)\n"
            "    except DateCapacityOverflow:\n"
            "        sentinel = [48, 45, 48, 45, 48]  # type: List[int]\n"
            "        return sentinel\n"
            "    except DateOutOfRange:\n"
            "        return render_out_of_range()\n"
            "    return render_success()\n"
        ),
        "rationale": "a correct impl with a reordered branch cascade and flipped "
                     "except order must verify; if not, the postcondition is "
                     "SPEC-TOO-STRONG (it forbids a faithful structural variant). "
                     "The not-all-present guard returns the grounded raw-retrieval "
                     "callee first; the all-present body returns each grounded "
                     "callee.",
    },

    # ---- ADMISSIBILITY: the precondition admits an F2P-shaped input -----------
    # The F2P input is (year=str(sys.maxsize+1), month=12, day=1) => all three
    # present, none blank, kind 2 (OverflowError). In the model that is
    # all_present=True, all_blank=False, kind=2. A caller asserts the Requires
    # holds for that input by self-calling. Must VERIFY (else PRECOND-TOO-STRONG).
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_success()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "        except DateCapacityOverflow:\n"
            "            result = [48, 45, 48, 45, 48]  # type: List[int]\n"
            "            return result\n"
            "    return retrieve_raw()\n"
            "\n\n"
            "def _admiss_caller() -> None:\n"
            "    # the F2P-shaped overflow input: all present, none blank, kind 2.\n"
            "    # The Requires (Implies(all_blank, all_present); kind in {0,1,2})\n"
            "    # must accept it, and the kind-2 postcondition must then pin the\n"
            "    # sentinel.\n"
            "    out = value_from_components(False, True, 2)\n"
            "    Assert(ToSeq(out) == zero_zero_zero())\n"
        ),
        "rationale": "the precondition must admit the exact F2P overflow input "
                     "(all_present, not all_blank, kind 2); the self-call site "
                     "establishes Requires and asserts the pinned sentinel. If it "
                     "fails, PRECOND-TOO-STRONG. The extra def is OUTSIDE every "
                     "marker region but is not part of the spec view's contracts; "
                     "same_spec holds because spec_view elides only impl regions "
                     "and the signature set is unchanged — verified in self-check.",
    },

    # ---- CONTROL-FLOW-EFFECT (the prepatch bug): drop the overflow handler ----
    # This is the exact pre-patch implementation: catch ONLY DateOutOfRange and let
    # DateCapacityOverflow escape. value_from_components declares NO Exsures, so on
    # kind 2 an escaping exception violates the implicit no-raise contract. MUST be
    # REJECTED for "method may raise an exception" (the no-Exsures obligation).
    {
        "id": "reject-drop-overflow-handler",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_success()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "    return retrieve_raw()\n"
        ),
        "refinement": "this is the literal pre-patch body (catches only ValueError, "
                      "omits `except OverflowError: return \"0-0-0\"`). Its faithful "
                      "real patch lets OverflowError escape value_from_datadict on "
                      "the F2P input (year=sys.maxsize+1), so the request 500-crashes "
                      "instead of producing \"0-0-0\" — the form is never invalid with "
                      "'Enter a valid date.' Both F2P tests "
                      "(test_form_field overflow case, test_value_from_datadict "
                      "(str(sys.maxsize+1),'12','1')->'0-0-0') FAIL. verify⇏resolve.",
        "rationale": "rejection comes from the implicit no-Exsures contract on "
                     "value_from_components: on kind 2 the construct_date axiom's "
                     "Exsures(DateCapacityOverflow, kind==2) fires and, uncaught, "
                     "escapes a method that declares no exceptions. This is exactly "
                     "the G-DIFF discriminator (model_prepatch.py fails the same way).",
    },

    # ---- PARTIAL-DOMAIN / UNGROUNDED-ECHO: wrong-but-non-empty on kind 2 -------
    # Handle the overflow branch but return the SUCCESS callee's text instead of
    # the sentinel. It satisfies len>0 (success_text is non-empty) and never
    # raises, so it passes every clause EXCEPT the kind-2 pin
    # (ToSeq(Result()) == zero_zero_zero()). MUST be REJECTED by that clause.
    {
        "id": "reject-echo-success-on-kind2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_success()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "        except DateCapacityOverflow:\n"
            "            return render_success()\n"
            "    return retrieve_raw()\n"
        ),
        "refinement": "its faithful real patch is `except OverflowError: return "
                      "date_value.strftime(input_format)` — but date_value was never "
                      "bound (the constructor raised), so the real code is a NameError "
                      "/ at best returns some non-'0-0-0' string. The F2P "
                      "test_value_from_datadict asserts the overflow input maps to "
                      "exactly '0-0-0', and test_form_field asserts the field rejects "
                      "with 'Enter a valid date.' (which requires the '0-0-0' value to "
                      "flow into clean and fail). Returning the strftime text resolves "
                      "NEITHER. verify⇏resolve.",
        "rationale": "rejection comes from the discriminating clause "
                     "Implies(all_present and not all_blank and kind==2, "
                     "ToSeq(Result()) == zero_zero_zero()): success_text() is "
                     "non-empty but != zero_zero_zero() (success_text is abstract and "
                     "the verifier cannot prove it equals the concrete sentinel).",
    },

    # ---- SENTINEL-CONTENT corruption: wrong code points on kind 2 -------------
    # Return a NEAR-MISS sentinel "0-0-1" ([48,45,48,45,49]) on overflow: non-empty,
    # no raise, but != zero_zero_zero(). Supporting case for the exact-content pin.
    {
        "id": "reject-wrong-sentinel-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_success()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "        except DateCapacityOverflow:\n"
            "            result = [48, 45, 48, 45, 49]  # type: List[int]\n"
            "            return result\n"
            "    return retrieve_raw()\n"
        ),
        "refinement": "its faithful real patch is `except OverflowError: return "
                      "\"0-0-1\"` (or any non-'0-0-0' string). The F2P "
                      "test_value_from_datadict asserts == '0-0-0' verbatim, so it "
                      "FAILS. verify⇏resolve.",
        "rationale": "rejection from the exact-content pin "
                     "ToSeq(Result()) == zero_zero_zero() = PSeq(48,45,48,45,48): "
                     "[48,45,48,45,49] differs in the last code point. Supporting "
                     "near-miss for the load-bearing sentinel clause.",
    },

    # ---- VALUE-MASK: empty (absent) on kind 2 ---------------------------------
    # Return [] on overflow. This collapses the text branch into the absent value,
    # violating BOTH len>0 and the sentinel pin. MUST be REJECTED. (It also breaks
    # the None<->[] bijection on which the whole abstraction rests.)
    {
        "id": "reject-empty-on-kind2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_success()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "        except DateCapacityOverflow:\n"
            "            blank = []  # type: List[int]\n"
            "            return blank\n"
            "    return retrieve_raw()\n"
        ),
        "refinement": "its faithful real patch is `except OverflowError: return None` "
                      "(or return \"\"). The F2P test_value_from_datadict asserts the "
                      "overflow input -> '0-0-0', not None/''; and test_form_field "
                      "needs the '0-0-0' string to reach clean() and raise the "
                      "ValidationError. Returning None makes the widget report an "
                      "absent value (the field would say 'This field is required.' or "
                      "skip), resolving NEITHER F2P. verify⇏resolve.",
        "rationale": "rejection from BOTH the non-empty pin "
                     "Implies(all_present and not all_blank, len(ToSeq(Result()))>0) "
                     "and the sentinel pin; an empty result on a text branch is "
                     "indistinguishable from absent and is explicitly forbidden.",
    },

    # ---- BRANCH-SWAP: wrong grounded text on kind 0 (cross-branch echo) -------
    # On the success path (kind 0) return the out-of-range fallback callee's text
    # instead of the success render. Both are non-empty, neither raises, so it
    # passes len>0 and the kind-1/kind-2 clauses — but violates the kind-0 pin
    # (ToSeq(Result()) == success_text()). MUST be REJECTED. This is the true
    # 'echo the wrong grounded oracle' attack.
    {
        "id": "reject-swap-text-on-kind0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_out_of_range()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "        except DateCapacityOverflow:\n"
            "            result = [48, 45, 48, 45, 48]  # type: List[int]\n"
            "            return result\n"
            "    return retrieve_raw()\n"
        ),
        "refinement": "its faithful real patch returns the '%s-%s-%s' pseudo-ISO "
                      "fallback on the SUCCESS path instead of "
                      "date_value.strftime(input_format). For a valid date like "
                      "(2010,1,1) the P2P tests (test_value_from_datadict's valid "
                      "rows, the round-trip datefield tests) assert the canonical "
                      "rendered date, not the pseudo-ISO fallback, so they FAIL. "
                      "verify⇏resolve.",
        "rationale": "rejection from the kind-0 pin "
                     "Implies(all_present and not all_blank and kind==0, "
                     "ToSeq(Result()) == success_text()): out_of_range_text() and "
                     "success_text() are distinct abstract callees and the verifier "
                     "cannot prove out_of_range_text()==success_text().",
    },

    # ---- NOT-ALL-PRESENT must echo the raw callee (partial-domain, else branch)
    # The not-all-present fallback returns a fabricated sentinel instead of the
    # raw-retrieval callee's value. On all_present=False this violates
    # Implies(not all_present, ToSeq(Result()) == raw_value()): raw_value() is
    # fully abstract, so no fabricated literal can be proven equal to it.
    {
        "id": "reject-nonempty-not-all-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_success()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "        except DateCapacityOverflow:\n"
            "            result = [48, 45, 48, 45, 48]  # type: List[int]\n"
            "            return result\n"
            "    fallback = [48, 45, 48, 45, 48]  # type: List[int]\n"
            "    return fallback\n"
        ),
        "refinement": "its faithful real patch makes the not-all-present `else` "
                      "branch return '0-0-0' rather than `data.get(name)` (which is "
                      "None for the observed inputs). The P2P test_value_from_datadict "
                      "rows ((None,'12','1')->None, ('2000',None,'1')->None, "
                      "('2000','12',None)->None) assert None, not '0-0-0', so they "
                      "FAIL. verify⇏resolve.",
        "rationale": "rejection from Implies(not all_present, "
                     "ToSeq(Result())==raw_value()): raw_value() is the fully "
                     "abstract raw-retrieval callee's value, so the fabricated "
                     "sentinel [48,45,48,45,48] cannot be proven equal to it. "
                     "Guards the unchanged not-all-present branch — the ONLY way "
                     "to satisfy the pin is to return retrieve_raw() itself.",
    },

    # ---- NOT-ALL-PRESENT must not hard-code absent (unfaithful-model guard) ---
    # The not-all-present fallback returns a fabricated EMPTY list instead of the
    # raw-retrieval callee's value. The real `return data.get(name)` can yield a
    # NON-None raw string (e.g. a whole-date text posted under the bare field
    # name), so pinning this branch to emptiness would be an UNFAITHFUL model —
    # exactly the defect a prior audit found in an earlier spec revision. The
    # abstract raw_value() pin rejects the fabricated empty just as it rejects
    # the fabricated sentinel: [] cannot be proven equal to raw_value().
    {
        "id": "reject-empty-literal-not-all-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if all_blank:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_success()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "        except DateCapacityOverflow:\n"
            "            result = [48, 45, 48, 45, 48]  # type: List[int]\n"
            "            return result\n"
            "    empty2 = []  # type: List[int]\n"
            "    return empty2\n"
        ),
        "refinement": "its faithful real patch replaces the not-all-present "
                      "`return data.get(name)` with `return None` unconditionally. "
                      "The real callee returns the RAW submitted value under the "
                      "bare field name — value_from_datadict({'mydate':'2008-4-1'},"
                      "{},'mydate') == '2008-4-1' at base_commit — so hard-coding "
                      "None diverges from the repo (e.g. DateField round-trips that "
                      "post the composite value under the bare name would break). "
                      "verify⇏resolve for that behaviour change.",
        "rationale": "rejection from Implies(not all_present, "
                     "ToSeq(Result())==raw_value()): the fabricated empty list "
                     "cannot be proven equal to the fully abstract raw_value(). "
                     "This is the faithfulness guard: the branch must return the "
                     "retrieval callee's own value, not a hard-coded absent.",
    },

    # ---- ALL-BLANK must stay absent (partial-domain on the first branch) ------
    # The all-blank fast path returns a non-empty value. Violates
    # Implies(all_blank, ==absent_text()). (all_blank => all_present by Requires,
    # so this is a distinct sub-domain from the not-all-present case.)
    {
        "id": "reject-nonempty-all-blank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if all_blank:\n"
            "        nonblank = [48, 45, 48, 45, 48]  # type: List[int]\n"
            "        return nonblank\n"
            "    if all_present:\n"
            "        try:\n"
            "            date_token = construct_date(kind)\n"
            "            return render_success()\n"
            "        except DateOutOfRange:\n"
            "            return render_out_of_range()\n"
            "        except DateCapacityOverflow:\n"
            "            result = [48, 45, 48, 45, 48]  # type: List[int]\n"
            "            return result\n"
            "    return retrieve_raw()\n"
        ),
        "refinement": "its faithful real patch makes the all-blank case "
                      "(y==m==d=='') return '0-0-0' instead of None. The P2P "
                      "test_value_from_datadict row (('','',''),None) asserts None, so "
                      "it FAILS; the field would also stop reporting 'This field is "
                      "required.' for an entirely blank submission. verify⇏resolve.",
        "rationale": "rejection from Implies(all_blank, "
                     "ToSeq(Result())==absent_text()): a non-empty result on the "
                     "all-blank branch violates the absent-value pin. Guards the "
                     "unchanged all-blank fast path.",
    },
]


# ----------------------------------------------------------------------------
# AXIOM LANE — construct_date / render_success / render_out_of_range are all
# A-consumed @ContractOnly callees over the stdlib (datetime.date, strftime, the
# %-format fallback). The bundle ships axiom_check.py (G-AX). We re-run the real
# callee in Docker and assert BOTH soundness (every rejection is exactly one of
# {OverflowError, ValueError}, overflow precedes range) and CALLER-DOMAIN
# CONTAINMENT (every (y,m,d) triple the model can reach is in the axiom's
# Requires domain kind in {0,1,2} — i.e. datetime.date never escapes with any
# other class). The probe is self-contained (stdlib only), opens nothing on disk,
# prints a diagnostic, exit 0 iff the obligation holds.
# ----------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
import datetime, random, sys

def real_kind(y, m, d):
    """Run the REAL datetime.date(int(y),int(m),int(d)); report 0 accepted,
    1 ValueError, 2 OverflowError, or None for ANY OTHER escaping class
    (which would make construct_date's {0,1,2} contract UNSOUND)."""
    try:
        datetime.date(int(y), int(m), int(d))
        return 0
    except OverflowError:
        return 2
    except ValueError:
        return 1
    except Exception:
        return None

def check(y, m, d, expected):
    obs = real_kind(y, m, d)
    if obs is None:
        print("UNSOUND: (%r,%r,%r) escaped {OverflowError,ValueError}" % (y, m, d))
        sys.exit(1)
    if obs != expected:
        print("UNSOUND: (%r,%r,%r) expected kind %d, real datetime.date kind %d"
              % (y, m, d, expected, obs))
        sys.exit(1)

big = sys.maxsize + 1          # the exact F2P overflow trigger
bigger = 10 ** 30
neg_big = -(2 ** 70)

# kind 0 — constructor ACCEPTS a representable valid date.
for t in [(2000,12,1),(2010,1,1),(1,1,1),(9999,12,31),(2016,2,29),
          (2017,2,28),(2020,11,30),("2000","12","1"),("0002010","01","09")]:
    check(t[0], t[1], t[2], 0)

# kind 1 — out-of-range / not a real calendar date -> ValueError.
for t in [(2010,13,1),(2010,0,1),(2010,2,31),(2010,1,0),(2010,4,31),
          (2015,2,29),(0,1,1),(10000,1,1),(-1,1,1),(2010,-1,1),(2010,1,-5)]:
    check(t[0], t[1], t[2], 1)
# int() of blank / non-numeric text also raises ValueError (kind 1 in the model).
for bad in ["", "abc", "  ", "1.5", "0x10", "2010a"]:
    check(bad, "12", "1", 1)

# kind 2 — capacity-overflow (magnitude exceeds C long) -> OverflowError.
for t in [(big,12,1),(big,0,0),(big,13,40),(bigger,1,1),(neg_big,2,31),
          (1,big,1),(1,1,big),(str(big),"12","1"),(str(bigger),"1","1")]:
    check(t[0], t[1], t[2], 2)

# precedence witness: overflow takes precedence over a co-occurring range error,
# so the F2P-style (sys.maxsize+1, 13, 40) routes to the OverflowError handler,
# never the ValueError fallback — this is what makes kind 2 the F2P outcome.
if real_kind(big, 13, 40) != 2 or real_kind(big, 0, 0) != 2:
    print("UNSOUND: OverflowError must precede range ValueError")
    sys.exit(1)

# randomized fuzz: confirm {OverflowError, ValueError} is exhaustive for integer
# args across a wide boundary-biased mix (so the widget's two-handler try covers
# every failure) and all three outcomes are exercised.
rng = random.Random(16667)
counts = {0:0, 1:0, 2:0}
def comp():
    r = rng.randint(0, 3)
    if r == 0: return rng.randint(-3, 13000)
    if r == 1: return sys.maxsize + rng.randint(-4, 6)
    if r == 2: return rng.choice([10**25, -(10**25), 2**64, -(2**64)])
    return rng.randint(-50, 60)
for _ in range(200000):
    y, m, d = comp(), comp(), comp()
    k = real_kind(y, m, d)
    if k is None:
        print("UNSOUND: (%r,%r,%r) escaped {OverflowError,ValueError}" % (y, m, d))
        sys.exit(1)
    counts[k] += 1
if not (counts[0] > 0 and counts[1] > 0 and counts[2] > 0):
    print("fuzz failed to exercise all three outcomes: %r" % (counts,))
    sys.exit(1)

# the patch sentinel "0-0-0" decodes to the model code points.
if [ord(c) for c in "0-0-0"] != [48, 45, 48, 45, 48]:
    print("UNSOUND: zero_zero_zero sentinel mismatch")
    sys.exit(1)

# the unchanged renderings the model pins are NON-EMPTY (so absent == empty stays
# distinct from every text-producing branch).
for t in [(2000,12,1),(2010,1,1),(9999,12,31)]:
    dv = datetime.date(t[0], t[1], t[2])
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y", "%b %d %Y"):
        if len(dv.strftime(fmt)) == 0:
            print("UNSOUND: strftime produced empty text for %r %r" % (dv, fmt))
            sys.exit(1)
for (y, m, d) in [("","13","1"),("2010","","31"),("2010","2",""),
                  ("2010","13","40"),("abc","x","y")]:
    if len("%s-%s-%s" % (y or 0, m or 0, d or 0)) == 0:
        print("UNSOUND: pseudo-ISO fallback empty for (%r,%r,%r)" % (y, m, d))
        sys.exit(1)

print("AX-SOUND OK: real datetime.date sound vs construct_date axiom over "
      "boundary + 6 bad-text + overflow inputs and 200000 fuzz triples "
      "(outcomes %r); every rejection EXACTLY one of {OverflowError, ValueError}; "
      "overflow precedes range; sentinel '0-0-0'==[48,45,48,45,48]; renderings "
      "non-empty." % (counts,))
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import datetime, random, sys

# CALLER-DOMAIN CONTAINMENT for the construct_date axiom.
#
# The model only invokes construct_date(kind) inside the all-present, non-blank
# branch, with kind in {0,1,2} (the Requires). The R-refinement (mapping.md S2)
# binds kind to the OUTCOME of datetime.date(int(y),int(m),int(d)) on the three
# submitted text components: kind 0 == accepted, kind 1 == ValueError, kind 2 ==
# OverflowError. So the callee-inputs the caller can actually reach are EXACTLY
# the integer-argument datetime.date constructions arising from submitted text
# (y, m, d are decimal strings, possibly blank/garbage -> int() may itself raise
# ValueError, still kind 1).
#
# Containment obligation: every such reachable callee-input must land in the
# axiom's covered domain {0,1,2} — i.e. real datetime.date(int(...)) must NEVER
# escape with a class outside {OverflowError, ValueError}. A reachable input
# whose real outcome is None (some other class) would be AXIOM-TOO-WEAK-FOR-CALLER
# (a callee-input the caller reaches but the axiom's kind in {0,1,2} cannot
# describe). We enumerate the reachable shapes adversarially.

def real_kind(y, m, d):
    try:
        datetime.date(int(y), int(m), int(d))
        return 0
    except OverflowError:
        return 2
    except ValueError:
        return 1
    except Exception as e:
        return ("OTHER", type(e).__name__)

reachable_violations = []

# Shape 1: well-formed decimal strings spanning valid, calendar-edge, far-range,
# and overflow magnitudes (what the three <select> components can submit).
texts = ["", " ", "0", "00", "1", "01", "0012", "12", "13", "28", "29", "30",
         "31", "32", "99", "100", "1582", "1900", "1999", "2000", "2010",
         "9999", "10000", "-1", "-12", "000", "  3 ", "+5",
         str(sys.maxsize), str(sys.maxsize + 1), str(-(sys.maxsize + 1)),
         str(10 ** 25), str(-(10 ** 30)), "abc", "1.0", "2e3", "0x1f"]
for y in texts:
    for m in ["1", "12", "13", "0", "02", str(sys.maxsize + 1), ""]:
        for d in ["1", "31", "0", str(sys.maxsize + 1), ""]:
            k = real_kind(y, m, d)
            if isinstance(k, tuple):
                reachable_violations.append((y, m, d, k[1]))

# Shape 2: direct integer reach (post-int() values), boundary-biased fuzz, to
# confirm no caller-reachable integer triple escapes {0,1,2}.
rng = random.Random(166670)
for _ in range(150000):
    def comp():
        r = rng.randint(0, 4)
        if r == 0: return rng.randint(-2, 13000)
        if r == 1: return sys.maxsize + rng.randint(-3, 5)
        if r == 2: return -(sys.maxsize) + rng.randint(-5, 3)
        if r == 3: return rng.choice([10**20, -(10**20), 2**63, -(2**63), 2**64])
        return rng.randint(0, 32)
    y, m, d = comp(), comp(), comp()
    k = real_kind(y, m, d)
    if isinstance(k, tuple):
        reachable_violations.append((y, m, d, k[1]))

if reachable_violations:
    print("AXIOM-TOO-WEAK-FOR-CALLER: caller-reachable construct_date inputs "
          "escape {0,1,2} (real class outside {OverflowError,ValueError}): "
          "%r" % (reachable_violations[:10],))
    sys.exit(1)

print("AX-CONTAIN OK: every caller-reachable construct_date input (decimal/blank/"
      "garbage text components -> int() -> datetime.date, plus 150000 boundary "
      "fuzz integer triples) lands in the axiom's covered domain {0,1,2}; real "
      "datetime.date never escapes with a class outside {OverflowError, "
      "ValueError}, so kind in {0,1,2} covers the full caller-reachable surface.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-construct-date",
        "axiom": "construct_date",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "construct_date is A-consumed: the proof consumes "
                     "Ensures(kind==0) + Exsures(DateOutOfRange,kind==1) + "
                     "Exsures(DateCapacityOverflow,kind==2), and the two-handler try "
                     "relies on {OverflowError,ValueError} being EXHAUSTIVE for "
                     "integer args with overflow preceding range. The probe runs the "
                     "real datetime.date and asserts exactly that; any escaping class "
                     "would be AXIOM-UNSOUND. Mirrors axiom_check.py (G-AX).",
    },
    {
        "id": "ax-contain-construct-date",
        "axiom": "construct_date",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "containment: every (y,m,d) the caller can reach (decimal/"
                     "blank/garbage submitted text -> int() -> datetime.date, plus "
                     "boundary-fuzzed integer triples) must lie in the axiom's "
                     "Requires domain kind in {0,1,2}. If any reachable input's real "
                     "outcome were a class outside {OverflowError,ValueError}, the "
                     "axiom would be AXIOM-TOO-WEAK-FOR-CALLER. Covering MORE than the "
                     "caller reaches would be sound; we check only that none escapes.",
    },
]
