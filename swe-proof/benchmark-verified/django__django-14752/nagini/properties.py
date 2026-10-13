# properties.py — PBT falsification battery for django__django-14752.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant built by region-surgery that edits
# ONLY text inside an # impl-start / # impl-end block (the frozen spec — axioms,
# pure, pre/post-conditions, signatures — is never touched, so same_spec holds by
# construction). The runner checks expect="verify" iff (same_spec AND verifies)
# and expect="reject" iff (same_spec AND does NOT verify).
#
# DEFENDED SURFACE (reasoned, not mechanical):
#   build_results(view, recs, to_field_name) -> List[Entry]
#     read-only inputs:  Acc(list_pred(recs), 1/2)        [the queryset]
#                        Acc(recs[k].id_text, 1/8), Acc(recs[k].display_text, 1/8)
#     load-bearing post:  len(Result()) == len(recs)                       (alignment)
#                         Result()[k] is record_entry(view, recs[k], tf)   (DEFERRAL,
#                            by reference identity, to the opaque late-bound step)
#     frame: the half/eighth read permissions on recs are RETURNED unchanged.
#   default_record_entry(view, rec, to_field_name) -> Entry
#     read-only inputs:  Acc(rec.id_text, 1/2), Acc(rec.display_text, 1/2)
#     load-bearing post:  Result().id_val   == lookup_text(rec, to_field_name)
#                         Result().text_val == display(rec)
#
# The dispatch pin uses the OPAQUE record_entry (Ensures(True)) via `is`, so there
# is no answer-key contents to echo: the only way to satisfy the post is to call
# the late-bound step. The default's oracle (lookup_text/display) is GROUNDED in
# rec's own fields, so there is no WRONG echo either. See 'assessment'.

from pathlib import Path

INSTANCE = "django__django-14752"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- exact impl-region anchors (verbatim from model.py, inside # impl-start/end) ---

# default_record_entry impl (single line between its impl markers)
_DRE_IMPL = "    return Entry(lookup_text(rec, to_field_name), display(rec))"

# build_results impl: the whole loop body (everything between its impl markers).
_BR_IMPL = (
    "    result = []  # type: List[Entry]\n"
    "    i = 0\n"
    "    while i < len(recs):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(recs), 1 / 2))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),\n"
    "                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(recs))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                  result[k] is record_entry(view, recs[k], to_field_name)))))\n"
    "        Invariant(MustTerminate(len(recs) - i + 1))\n"
    "        # invariants-end\n"
    "        result.append(record_entry(view, recs[i], to_field_name))\n"
    "        i = i + 1\n"
    "    return result"
)


def _assert_base():
    if _DRE_IMPL not in _BASE:
        raise AssertionError("default_record_entry impl anchor drifted")
    if _BASE.count(_DRE_IMPL) != 1:
        raise AssertionError("default_record_entry impl anchor not unique")
    if _BR_IMPL not in _BASE:
        raise AssertionError("build_results impl anchor drifted")
    if _BASE.count(_BR_IMPL) != 1:
        raise AssertionError("build_results impl anchor not unique")


_assert_base()


# =============================== SPEC_TESTS ==================================

SPEC_TESTS = []

# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL — build_results, structurally different but CORRECT.
#     Local-variable reshape: bind the dispatched entry to a typed local before
#     appending (NOT a loop-direction flip — directive 3 — and NOT dropping any
#     framing invariant — directive 2). Must verify, else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_pos_br = _swap(
    _BASE, _BR_IMPL,
    "    result = []  # type: List[Entry]\n"
    "    i = 0\n"
    "    while i < len(recs):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(recs), 1 / 2))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),\n"
    "                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(recs))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                  result[k] is record_entry(view, recs[k], to_field_name)))))\n"
    "        Invariant(MustTerminate(len(recs) - i + 1))\n"
    "        # invariants-end\n"
    "        e = record_entry(view, recs[i], to_field_name)  # type: Entry\n"
    "        result.append(e)\n"
    "        i = i + 1\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "pos-control-localvar",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_br,
    "rationale": "A correct build_results that binds the dispatched entry to a "
                 "typed local before append (structural reshape, every gold "
                 "invariant kept verbatim). It still calls record_entry per "
                 "record in order, so the deferral postcondition holds. If a "
                 "faithful correct impl cannot verify => SPEC-TOO-STRONG.",
})

# ---------------------------------------------------------------------------
# (1b) POSITIVE CONTROL — default_record_entry, local-variable reshape.
#      Cheapest faithful default body via a named local. Must verify.
# ---------------------------------------------------------------------------
_pos_dre = _swap(
    _BASE, _DRE_IMPL,
    "    e = Entry(lookup_text(rec, to_field_name), display(rec))  # type: Entry\n"
    "    return e",
)
SPEC_TESTS.append({
    "id": "pos-control-default-localvar",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_dre,
    "rationale": "The default conversion built via a typed local then returned: "
                 "id_val == lookup_text(rec, tf), text_val == display(rec) still "
                 "hold. A structurally-different correct default must verify "
                 "(else SPEC-TOO-STRONG).",
})

# ---------------------------------------------------------------------------
# (2) ADMISSIBILITY — the precondition must ADMIT a normal F2P-shaped use.
#     Inside default_record_entry's impl, assert the axiom obligations are
#     establishable from the precondition (Acc(rec.id_text,1/2) >= the 1/8 that
#     lookup_text needs). If the precondition were too strong/weak to support the
#     default conversion call, this assert (or the call) would fail to verify.
#     Keeps the exact gold return, so verification is attributable to the precond.
# ---------------------------------------------------------------------------
_adm_dre = _swap(
    _BASE, _DRE_IMPL,
    "    Assert(lookup_text(rec, to_field_name) == rec.id_text)\n"
    "    Assert(display(rec) == rec.display_text)\n"
    "    return Entry(lookup_text(rec, to_field_name), display(rec))",
)
SPEC_TESTS.append({
    "id": "admiss-default-precond-admits",
    "kind": "admissibility",
    "expect": "verify",
    "module": _adm_dre,
    "rationale": "The precondition Acc(rec.id_text,1/2)/Acc(rec.display_text,1/2) "
                 "must admit calling lookup_text/display (each need only 1/8) on a "
                 "normal record and let their Ensures ground to rec's fields. If "
                 "the precondition could not support the default conversion the "
                 "asserts/calls would not verify => PRECOND-TOO-STRONG.",
})

# ---------------------------------------------------------------------------
# (3) DISPATCH-DROP / DEFERRAL DEFEAT — build_results inlines the DEFAULT entry
#     instead of deferring to the late-bound step (this is exactly the pre-patch
#     bug). It cannot prove Result()[k] is record_entry(view, recs[k], tf): a
#     freshly built default Entry is not the opaque dispatched value. expect=reject.
#     This is the PARTIAL-DOMAIN attack at the spec level: correct ONLY for a
#     responder whose conversion step equals the default; wrong for any override.
# ---------------------------------------------------------------------------
_inline_br = _swap(
    _BASE, _BR_IMPL,
    "    result = []  # type: List[Entry]\n"
    "    i = 0\n"
    "    while i < len(recs):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(recs), 1 / 2))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),\n"
    "                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(recs))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                  result[k] is record_entry(view, recs[k], to_field_name)))))\n"
    "        Invariant(MustTerminate(len(recs) - i + 1))\n"
    "        # invariants-end\n"
    "        result.append(Entry(lookup_text(recs[i], to_field_name), display(recs[i])))\n"
    "        i = i + 1\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "weak-inline-default",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _inline_br,
    "refinement": "The faithful real patch is the PRE-PATCH get(): build each "
                  "entry inline as {'id': str(getattr(obj,tf)), 'text': str(obj)} "
                  "instead of calling self.serialize_result(obj, tf). It IGNORES a "
                  "subclass override, so test_serialize_result (which overrides "
                  "serialize_result to add a 'posted' key and asserts every result "
                  "entry carries it) FAILS => does not resolve the F2P.",
    "rationale": "Rejection comes from the build_results postcondition/loop "
                 "invariant Result()[k] is record_entry(view, recs[k], tf): a "
                 "freshly-constructed default Entry is reference-distinct from the "
                 "opaque dispatched value and cannot be proved `is` it.",
})

# ---------------------------------------------------------------------------
# (4) PARTIAL-DOMAIN (first element) — defer for every record EXCEPT index 0,
#     where it inlines the default. Correct on all but the first row. Cannot
#     prove the invariant at k=0 => reject. A byte-fuzzer never builds this.
# ---------------------------------------------------------------------------
_firstrow_br = _swap(
    _BASE, _BR_IMPL,
    "    result = []  # type: List[Entry]\n"
    "    i = 0\n"
    "    while i < len(recs):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(recs), 1 / 2))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),\n"
    "                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(recs))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                  result[k] is record_entry(view, recs[k], to_field_name)))))\n"
    "        Invariant(MustTerminate(len(recs) - i + 1))\n"
    "        # invariants-end\n"
    "        if i == 0:\n"
    "            result.append(Entry(lookup_text(recs[i], to_field_name), display(recs[i])))\n"
    "        else:\n"
    "            result.append(record_entry(view, recs[i], to_field_name))\n"
    "        i = i + 1\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "weak-partial-firstrow-inline",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _firstrow_br,
    "refinement": "A faithful patch that special-cases the first matched record "
                  "to the inline default {'id':..., 'text':...} but defers the "
                  "rest would, for the first row, IGNORE the subclass override. "
                  "test_serialize_result orders by '-posted' and asserts the "
                  "'posted' key on EVERY entry including the first "
                  "(Question.objects.order_by('-posted')[0]); the first entry "
                  "would lack 'posted' => F2P fails.",
    "rationale": "Rejection comes from the loop invariant at k=0: the inlined "
                 "default Entry for record 0 is not `is` record_entry(view, "
                 "recs[0], tf), so the deferral postcondition is unprovable for "
                 "the first element.",
})

# ---------------------------------------------------------------------------
# (5) VALUE-SWAP — default_record_entry swaps id_val and text_val. Pins
#     id_val == display(rec) and text_val == lookup_text(rec, tf): violates BOTH
#     load-bearing post clauses. expect=reject.
# ---------------------------------------------------------------------------
_swap_dre = _swap(
    _BASE, _DRE_IMPL,
    "    return Entry(display(rec), lookup_text(rec, to_field_name))",
)
SPEC_TESTS.append({
    "id": "weak-default-swap-fields",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap_dre,
    "refinement": "The faithful real patch is serialize_result returning "
                  "{'id': str(obj), 'text': str(getattr(obj, tf))} — id and text "
                  "transposed. test_serialize_result asserts 'id': str(q.pk) and "
                  "'text': q.question; with id<->text swapped the asserted dict "
                  "mismatches => F2P fails (and every P2P over the default entry "
                  "fails too).",
    "rationale": "Rejection comes from default_record_entry's postcondition "
                 "Result().id_val == lookup_text(rec, tf) and Result().text_val "
                 "== display(rec): the swapped Entry satisfies neither.",
})

# ---------------------------------------------------------------------------
# (6) FRAME-MUTATION (MANDATORY — read-only inputs present). default_record_entry
#     holds rec.id_text at HALF permission (read-only). A rival that WRITES
#     rec.id_text to fabricate the field needs FULL permission and must fail for
#     INSUFFICIENT PERMISSION. The gold post (Result().id_val == lookup_text(rec,
#     tf)) is kept verbatim so the rejection is attributable to the write.
# ---------------------------------------------------------------------------
_framemut_dre = _swap(
    _BASE, _DRE_IMPL,
    "    rec.id_text = display(rec)\n"
    "    return Entry(lookup_text(rec, to_field_name), display(rec))",
)
SPEC_TESTS.append({
    "id": "reject-frame-mutation-rec",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _framemut_dre,
    "refinement": "A faithful patch whose serialize_result MUTATES the matched "
                  "model object (e.g. obj.<lookup>=str(obj) before reading it) "
                  "would corrupt the queryset row mid-serialization: the 'id' it "
                  "then emits is str(obj) not str(getattr(obj, tf)), and the "
                  "mutation is observable on later use of obj. test_serialize_"
                  "result asserts 'id': str(q.pk); a clobbered id => F2P fails. "
                  "serialize_result is purely read-only on obj.",
    "rationale": "Rejection comes from the PERMISSION SYSTEM: rec.id_text is held "
                 "at Acc(rec.id_text, 1/2); writing it needs full permission, so "
                 "the assignment fails for insufficient permission. A byte-fuzzer "
                 "never thinks to mutate a read-only input.",
})

# ---------------------------------------------------------------------------
# (6b) FRAME-MUTATION on the list element — build_results holds recs[i].id_text
#      at only 1/8. A rival that writes it (to forge the dispatched entry's fields)
#      must fail for insufficient permission. Every gold invariant kept verbatim.
# ---------------------------------------------------------------------------
_framemut_br = _swap(
    _BASE, _BR_IMPL,
    "    result = []  # type: List[Entry]\n"
    "    i = 0\n"
    "    while i < len(recs):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(recs), 1 / 2))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),\n"
    "                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(recs))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                  result[k] is record_entry(view, recs[k], to_field_name)))))\n"
    "        Invariant(MustTerminate(len(recs) - i + 1))\n"
    "        # invariants-end\n"
    "        recs[i].id_text = display(recs[i])\n"
    "        result.append(record_entry(view, recs[i], to_field_name))\n"
    "        i = i + 1\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "reject-frame-mutation-list-elem",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _framemut_br,
    "refinement": "A faithful builder that mutates each matched record's lookup "
                  "field while iterating the queryset would corrupt every row "
                  "(and break the post-iteration assertions the F2P/P2P make on "
                  "q.pk / q.question). The real get() comprehension only READS "
                  "each obj. A mutating builder does not resolve.",
    "rationale": "Rejection comes from the PERMISSION SYSTEM: recs[i].id_text is "
                 "held at only Acc(recs[i].id_text, 1/8); the write needs full "
                 "permission and fails for insufficient permission.",
})

# ---------------------------------------------------------------------------
# (7) LENGTH / ALIGNMENT (supporting partial-domain) — build_results that skips
#     the last record. Violates len(Result()) == len(recs). expect=reject.
# ---------------------------------------------------------------------------
_short_br = _swap(
    _BASE, _BR_IMPL,
    "    result = []  # type: List[Entry]\n"
    "    i = 0\n"
    "    while i < len(recs) - 1:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(recs), 1 / 2))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),\n"
    "                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(recs))\n"
    "        Invariant(len(result) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                  result[k] is record_entry(view, recs[k], to_field_name)))))\n"
    "        Invariant(MustTerminate(len(recs) - i + 1))\n"
    "        # invariants-end\n"
    "        result.append(record_entry(view, recs[i], to_field_name))\n"
    "        i = i + 1\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "weak-skip-last-record",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _short_br,
    "refinement": "A builder that drops the final matched record returns one "
                  "fewer result than there are records. test_serialize_result "
                  "asserts the results list equals one entry per Question (two "
                  "questions, ordered by '-posted'); a missing last entry => the "
                  "asserted list mismatches => F2P fails.",
    "rationale": "Rejection comes from the postcondition len(Result()) == "
                 "len(recs): the short loop produces len(recs)-1 entries (for a "
                 "non-empty list), which the verifier cannot reconcile with the "
                 "required length.",
})


# =============================== AXIOM_TESTS =================================
#
# The bundle has @ContractOnly axioms (record_entry A-consumed, lookup_text /
# display A-consumed) and one A-reference deep model (default_record_entry). All
# are validated out-of-band by axiom_check.py (G-AX). We re-express that ground
# truth as two self-contained probes that EXECUTE the real post-patch method
# bodies (quoted verbatim from patch.diff — Django is not stdlib-importable) and
# fuzz the obligations. Probes import only stdlib, set encoding="utf-8" on any
# file read (none needed here), print a diagnostic, and exit(0) iff the obligation
# holds else exit(1).

AXIOM_TESTS = []

# --- shared real-code preamble (verbatim post-patch bodies) ----------------
_REAL_CODE = r'''
import json, random, sys

# REAL post-patch bodies, verbatim from patch.diff (Django not stdlib-importable):
class AutocompleteJsonView:
    def serialize_result(self, obj, to_field_name):
        return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}
    def build_results(self, object_list, to_field_name):
        return [self.serialize_result(obj, to_field_name) for obj in object_list]

class Record:
    def __init__(self, attrs, text):
        self._attrs = dict(attrs); self._text = text
        for k, v in attrs.items(): setattr(self, k, v)
    def __str__(self): return self._text
'''

# (A) axiom-soundness for lookup_text / display / default_record_entry (A-reference):
#     the real default serialize_result produces an entry whose 'id' == str(getattr
#     (obj, tf)) (lookup_text) and 'text' == str(obj) (display), with EXACTLY the
#     two keys {'id','text'} — model.py's Entry(lookup_text(rec,tf), display(rec)).
_probe_default = _REAL_CODE + r'''

def model_default_entry(rec, tf):
    # model.py deep model: id_val == lookup_text == str(getattr), text_val == display == str
    return {'id': str(getattr(rec, tf)), 'text': str(rec)}

def check_default(rec, tf):
    real = AutocompleteJsonView().serialize_result(rec, tf)
    exp = model_default_entry(rec, tf)
    assert real == exp, "default deep model unsound: real=%r model=%r" % (real, exp)
    assert set(real.keys()) == {'id', 'text'}, "default entry shape drift: %r" % (real,)

boundary = [
    Record({'pk': 1}, 'Question 1'),
    Record({'pk': 42}, ''),
    Record({'pk': 0}, 'edge•case'),
    Record({'uuid': 'a1b2'}, "Joe's record"),
    Record({'name': 'x'}, '<b>html</b> & "stuff"'),
    Record({'pk': -7, 'extra': 'note'}, 'neg pk'),
]
for rec in boundary:
    for tf in ('pk', 'uuid', 'name'):
        if hasattr(rec, tf):
            check_default(rec, tf)

rng = random.Random(14752)
alphabet = "abcXYZ0129 &<>\"'•é;#"
for _ in range(20000):
    idv = rng.randint(-1000, 1000)
    txt = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
    check_default(Record({'pk': idv}, txt), 'pk')

print("AX default-reference OK: real serialize_result == deep model "
      "(id==str(getattr), text==str, keys=={id,text}) on 6 boundary + 20000 fuzz")
sys.exit(0)
'''
AXIOM_TESTS.append({
    "id": "ax-default-reference",
    "axiom": "default_record_entry",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _probe_default,
    "rationale": "A-reference: the deep model default_record_entry (Entry("
                 "lookup_text(rec,tf), display(rec))) must equal the real default "
                 "serialize_result {'id': str(getattr(obj,tf)), 'text': str(obj)} "
                 "with exactly the two keys. Executes the real body on boundary + "
                 "20000 fuzz records. If it diverges => the deep model / "
                 "lookup_text / display axioms are unsound.",
})

# (B) axiom-soundness/containment for record_entry (A-consumed dispatch): the
#     builder DEFERS each entry to the responder's OWN serialize_result, in order
#     — an overriding responder's extra field appears in EVERY entry (the F2P
#     scenario), and the base responder yields the default entries. Covers the
#     full set of caller-reachable inputs (any ordered batch incl. empty) the
#     model's build_results can pass to record_entry.
_probe_dispatch = _REAL_CODE + r'''

def check_dispatch(records, tf):
    class Extended(AutocompleteJsonView):
        def serialize_result(self, obj, tf2):
            base = super().serialize_result(obj, tf2)
            base['posted'] = str(getattr(obj, 'posted', ''))  # the F2P override
            return base
    view = Extended()
    built = view.build_results(records, tf)
    assert len(built) == len(records), "results not aligned 1:1 with records"
    for k, rec in enumerate(records):
        exp = view.serialize_result(rec, tf)
        assert built[k] == exp, "builder did not defer at %d: %r != %r" % (k, built[k], exp)
        assert 'posted' in built[k], "override IGNORED at %d (inlined default)" % k
    base_view = AutocompleteJsonView()
    base_built = base_view.build_results(records, tf)
    for k, rec in enumerate(records):
        assert base_built[k] == {'id': str(getattr(rec, tf)), 'text': str(rec)}, \
            "base builder entry mismatch at %d" % k
    json.dumps({'results': base_built})  # endpoint returns JsonResponse

# caller-reachable inputs: ordered batches incl. empty
check_dispatch([], 'pk')
check_dispatch([Record({'pk': i, 'posted': '2021-08-%02d' % (i + 1)}, 'r%d' % i)
                for i in range(5)], 'pk')

rng = random.Random(914752)
for _ in range(20000):
    n = rng.randint(0, 6)
    recs = [Record({'pk': rng.randint(-1000, 1000),
                    'posted': '2021-%02d-%02d' % (rng.randint(1, 12), rng.randint(1, 28))},
                   'r%d' % j) for j in range(n)]
    check_dispatch(recs, 'pk')

print("AX dispatch OK: builder defers to the late-bound conversion step (override "
      "appears in EVERY entry, in order; base yields default) on 2 boundary + "
      "20000 fuzz ordered batches")
sys.exit(0)
'''
AXIOM_TESTS.append({
    "id": "ax-dispatch-honoured",
    "axiom": "record_entry",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _probe_dispatch,
    "rationale": "A-consumed: build_results' postcondition Result()[k] is "
                 "record_entry(view, recs[k], tf) consumes the OPACITY/DISPATCH of "
                 "the late-bound step. The real post-patch builder defers to the "
                 "responder's own serialize_result, so an override appears in "
                 "every entry in order (the test_serialize_result scenario) and "
                 "the base responder yields default entries. If the real builder "
                 "did NOT defer, record_entry would be unsound for the caller.",
})
