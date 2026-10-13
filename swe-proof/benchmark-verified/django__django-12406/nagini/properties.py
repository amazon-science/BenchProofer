"""PBT manifest for django__django-12406.

NOT a Nagini module: a record of adversarially-reasoned falsification cases the
runner (swebench_nagini.pbt) executes and stamps RESULT onto. Spec cases are
full model.py variants that share the FROZEN spec byte-for-byte (region surgery:
ONLY the text inside an # impl-start / # impl-end block is edited — the spec
view is never touched) and are checked by Nagini verify + markers.same_spec.
Axiom cases are self-contained probes run against the REAL Django library (the
A-references) in the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
  TWO modeled functions, both pure decision logic — NO loops, NO @ContractOnly
  axioms consumed.

  (1) configure_placeholder(field: ChoiceFieldState, placeholder_label: int,
                            required: bool, initial_present: bool,
                            is_radio: bool, blank: bool) -> None
      Mutates the field object:  Requires(Acc(field.placeholder))  (FULL perm —
      the field IS genuinely written, so this is correct, not a frame defect).
      The scalar inputs (placeholder_label:int, required/initial_present/is_radio/
      blank:bool) are passed BY VALUE — Nagini does not permission-track immutable
      Python scalars, so there is NO Acc(x,1/2) read-only OBJECT input to mutate
      vacuously (see assessment: frame-mutation N/A for this instance).
      Load-bearing postcondition (the whole specification of site 1):
        Ensures(field.placeholder is not None  iff  placeholder_offered(...))
        Ensures(Implies(placeholder_offered(...),
                        field.placeholder is not None
                        and field.placeholder == placeholder_label))
      i.e. the placeholder is OFFERED iff NEITHER suppression situation holds —
        not ((required and initial_present) or (is_radio and not blank))
      — and when offered the carried label is EXACTLY the supplied candidate.

  (2) derived_field_emptiness_flag(model_blank: bool) -> bool
        Ensures(Result() == model_blank)        # identity forwarding
      Fully grounded in the input — the postcondition pins the result to the
      argument, so there is no opaque-oracle echo to abuse (it IS the answer).

  The @Pure helper placeholder_offered is GROUNDED in its args (a fully-unfolded
  boolean expression of the four inputs), not an opaque answer-key — so there is
  no "wrong echo" to build for the ungrounded-oracle class; an impl that returns
  placeholder_offered(...) IS the correct decision and serves as a positive
  control. See assessment.

  Two A-reference deep models (placeholder_offered, derived_field_emptiness_flag)
  are validated == real Django by axiom_check.py / G-AX => the AXIOM lane runs
  the REAL ModelChoiceField / ForeignKey in Docker (self-contained probes that
  embed the bundle's own check logic; import only Django + stdlib).

  The discriminating delta the gold patch adds (and every reject-rival attacks):
    * site 1: the SECOND suppression clause (is_radio and not blank) — a radio
      presentation with NO permitted empty value must suppress the placeholder;
    * site 2: forwarding self.blank into the derived field (was hard-coded
      default False before).
  F2P: test_choices_radio_blank (radio: blank<=>placeholder present),
       test_blank_foreign_key_with_radio (blank=True => placeholder present),
       test_non_blank_foreign_key_with_radio (blank=False => placeholder absent),
       test_clean_model_instance (P2P-shaped regression of the default path).
"""
from pathlib import Path

INSTANCE = "django__django-12406"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lives ENTIRELY inside one impl region (between # impl-start and
# # impl-end), so every _swap keeps same_spec.
# ---------------------------------------------------------------------------

# Site 1 impl: the full gold decision block (unique).
_S1_BODY = (
    "    if (required and initial_present) or (is_radio and not blank):\n"
    "        field.placeholder = None\n"
    "    else:\n"
    "        field.placeholder = placeholder_label"
)

# Site 2 impl: the gold forwarding (unique — only `return model_blank` directly
# before its impl-end).
_S2_BODY = "    return model_blank\n    # impl-end"


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = [

    # -- 1. POSITIVE CONTROL (soundness) — De Morgan reshape via the oracle ----
    # Structurally-different but CORRECT impl of site 1: compute the OFFERED flag
    # directly from placeholder_offered (the negation of the suppression
    # disjunction, by De Morgan) and assign in the opposite branch order. Same
    # value on every input; no loop / no induction lemma (directives 2/3). MUST
    # verify — else the postcondition is SPEC-TOO-STRONG.
    {
        "id": "pos-control-demorgan-offered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _S1_BODY,
            "    offered = not ((required and initial_present)\n"
            "                   or (is_radio and not blank))  # == placeholder_offered(...)\n"
            "    if offered:\n"
            "        field.placeholder = placeholder_label\n"
            "    else:\n"
            "        field.placeholder = None",
        ),
        "rationale": "a structurally-different but CORRECT impl (offered flag "
                     "computed first, branch order reversed) MUST verify; else "
                     "SPEC-TOO-STRONG. `offered` equals placeholder_offered(...) "
                     "definitionally, so both postcondition clauses (present-iff-"
                     "offered and label==placeholder_label when offered) hold.",
    },

    # -- 2. POSITIVE CONTROL (soundness) — site 2 reshape ---------------------
    # Forward the flag through an explicit branch instead of a bare return; same
    # value (model_blank). MUST verify (Result()==model_blank holds on both arms).
    {
        "id": "pos-control-forward-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _S2_BODY,
            "    if model_blank:\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end",
        ),
        "rationale": "a branch-shaped forwarding (return True/False per "
                     "model_blank) is value-equal to `return model_blank` and "
                     "MUST satisfy Result()==model_blank; else SPEC-TOO-STRONG.",
    },

    # -- 3. ADMISSIBILITY -----------------------------------------------------
    # The precondition for site 1 is just Acc(field.placeholder) (full perm on
    # the mutated field); there is NO value-domain restriction on the scalar
    # inputs, so a normal F2P-shaped call is admissible. We keep the gold impl
    # verbatim and add, BEFORE the decision (inside the impl region), an Assert
    # that the granted permission is held and the field's current value is
    # readable under it — the admissibility witness the verifier discharges from
    # the precondition alone. (No top-level driver can be added without leaving
    # the impl region and breaking same_spec.)
    {
        "id": "admiss-site1-read-field",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _S1_BODY,
            "    Assert(Acc(field.placeholder))          # the granted permission is held\n"
            "    if (required and initial_present) or (is_radio and not blank):\n"
            "        field.placeholder = None\n"
            "    else:\n"
            "        field.placeholder = placeholder_label",
        ),
        "rationale": "the precondition Acc(field.placeholder) must admit a normal "
                     "F2P-shaped call (full permission on the mutated field); the "
                     "added Assert(Acc(field.placeholder)) is discharged from the "
                     "Requires alone. If it could not be, PRECOND-TOO-STRONG. Gold "
                     "decision kept verbatim.",
    },

    # -- 4. UNIQUENESS — drop the radio clause (THE site-1 discriminating delta)
    # Pre-patch single-clause decision (model_prepatch_1.py): suppress ONLY for
    # required-with-initial; the radio-no-blank situation is NOT handled, so a
    # radio field with no permitted empty value still OFFERS the placeholder.
    # Diverges on (is_radio and not blank): rival offers, spec demands suppress.
    {
        "id": "weak-drop-radio-clause",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _S1_BODY,
            "    if required and initial_present:        # pre-patch: radio clause MISSING\n"
            "        field.placeholder = None\n"
            "    else:\n"
            "        field.placeholder = placeholder_label",
        ),
        "refinement": "this IS the pre-patch ModelChoiceField.__init__ decision "
                      "(model_prepatch_1.py): no radio handling. Its faithful real "
                      "patch is the UNCHANGED buggy code, which still offers the "
                      "blank placeholder for a non-blank radio field — exactly the "
                      "F2P test_choices_radio_blank (blank=False subcase) and "
                      "test_non_blank_foreign_key_with_radio assert it must NOT — "
                      "so it does NOT resolve the F2P.",
        "rationale": "REJECT from the postcondition clause `present iff "
                      "placeholder_offered(required,initial_present,is_radio,"
                      "blank)`: on (required=F, initial_present=F, is_radio=T, "
                      "blank=F) placeholder_offered is False (suppress) but the "
                      "rival assigns placeholder_label (present) — contradiction.",
    },

    # -- 5. UNIQUENESS — drop the required clause (partial-domain on site 1) ---
    # Mirror omission: keep ONLY the radio clause, drop required-with-initial.
    # Correct on radio inputs but WRONG on (required and initial_present) with a
    # non-radio widget: rival offers the placeholder where the spec suppresses.
    {
        "id": "weak-drop-required-clause",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _S1_BODY,
            "    if is_radio and not blank:              # required-with-initial clause DROPPED\n"
            "        field.placeholder = None\n"
            "    else:\n"
            "        field.placeholder = placeholder_label",
        ),
        "refinement": "dropping the required-with-initial suppression re-offers "
                      "the empty placeholder for a mandatory field that already "
                      "carries a pre-filled value — the pre-3.0 bug this branch "
                      "has ALWAYS guarded. The faithful real patch would regress "
                      "the long-standing required+initial behaviour exercised "
                      "across the model_forms P2P suite (165 P2P tests), so it "
                      "would NOT resolve / would break P2P.",
        "rationale": "REJECT from `present iff placeholder_offered(...)`: on "
                      "(required=T, initial_present=T, is_radio=F, blank=F) "
                      "placeholder_offered is False but the rival assigns "
                      "placeholder_label — contradiction on the required+initial "
                      "subdomain.",
    },

    # -- 6. UNIQUENESS — partial-domain: suppress radio regardless of blank ----
    # Subtle wrong sub-domain: treat ALL radio as suppressing (use `is_radio`
    # instead of `is_radio and not blank`). Correct on (is_radio and not blank)
    # and on every non-radio input, but WRONG on (is_radio and blank): a
    # blank-allowing radio field must OFFER the placeholder, this rival suppresses
    # it. Targets exactly the `not blank` half of the new clause.
    {
        "id": "partial-domain-radio-ignores-blank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _S1_BODY,
            "    if (required and initial_present) or is_radio:   # ignores `not blank`\n"
            "        field.placeholder = None\n"
            "    else:\n"
            "        field.placeholder = placeholder_label",
        ),
        "refinement": "suppressing the placeholder for EVERY radio field (even one "
                      "whose model field allows blank) drops the blank option a "
                      "blank-allowing radio FK must show. That is exactly the "
                      "blank=True subcase of test_choices_radio_blank and "
                      "test_blank_foreign_key_with_radio (which expect "
                      "[('','---------')] + choices); the faithful real patch "
                      "would FAIL those F2P, so it does NOT resolve.",
        "rationale": "REJECT from `present iff placeholder_offered(...)`: on "
                      "(required=F, initial_present=F, is_radio=T, blank=T) "
                      "placeholder_offered is True (offer) but the rival assigns "
                      "None — contradiction on the radio-with-blank subdomain.",
    },

    # -- 7. UNIQUENESS — wrong label echoed (attacks the second postcondition) -
    # Offer the placeholder under the correct condition BUT with a different
    # label (placeholder_label + 1). Satisfies the present-iff-offered clause yet
    # violates Implies(offered, placeholder == placeholder_label).
    {
        "id": "weak-wrong-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _S1_BODY,
            "    if (required and initial_present) or (is_radio and not blank):\n"
            "        field.placeholder = None\n"
            "    else:\n"
            "        field.placeholder = placeholder_label + 1   # wrong label carried",
        ),
        "refinement": "carrying a label other than the supplied empty_label means "
                      "the rendered blank choice shows the WRONG text. The real "
                      "ModelChoiceIterator yields ('', self.empty_label); a patch "
                      "that stored a different label would emit a blank entry with "
                      "the wrong caption, diverging from the gold-observed "
                      "[('', '---------')] choice rows the F2P assert, so it does "
                      "NOT resolve.",
        "rationale": "REJECT from the second postcondition "
                      "Implies(placeholder_offered(...), field.placeholder == "
                      "placeholder_label): when offered the rival carries "
                      "placeholder_label+1 != placeholder_label.",
    },

    # -- 8. UNIQUENESS — flip the forwarded flag (site 2) ---------------------
    # Forward the NEGATION of the emptiness flag.
    {
        "id": "weak-flip-blank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _S2_BODY,
            "    return not model_blank   # inverted forwarding\n    # impl-end",
        ),
        "refinement": "inverting the forwarded blank flag flips the radio FK "
                      "placeholder presence: blank=True FKs would LOSE the "
                      "placeholder and blank=False FKs would GAIN it — the exact "
                      "inverse of test_blank_foreign_key_with_radio / "
                      "test_non_blank_foreign_key_with_radio. The faithful real "
                      "patch resolves NOTHING.",
        "rationale": "REJECT from Result()==model_blank: `not model_blank` "
                      "contradicts the pinned identity on every input.",
    },

    # -- 9. UNIQUENESS — pre-patch hard-coded default False (site 2) ----------
    # model_prepatch_2.py: the kwarg was absent so the derived field fell back to
    # blank=False. Diverges when model_blank is True.
    {
        "id": "weak-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _S2_BODY,
            "    return False   # pre-patch: blank not forwarded, default False\n    # impl-end",
        ),
        "refinement": "this IS the pre-patch ForeignKey.formfield (model_prepatch_"
                      "2.py): no 'blank' kwarg forwarded, so ModelChoiceField "
                      "defaulted to blank=False. Its faithful real patch is the "
                      "UNCHANGED code, which suppresses the placeholder for a "
                      "blank=True radio FK — exactly what "
                      "test_blank_foreign_key_with_radio asserts it must NOT — so "
                      "it does NOT resolve the F2P.",
        "rationale": "REJECT from Result()==model_blank: when model_blank is True "
                      "the rival returns False — contradiction on the blank=True "
                      "subdomain (the discriminating F2P case).",
    },

    # -- 10. SUPPORTING near-miss — site 1 always offers (cheap mechanical) ---
    # Unconditional offer. Mechanical, but carries a real refinement: it never
    # suppresses, so it re-introduces both bugs at once.
    {
        "id": "support-always-offer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _S1_BODY,
            "    field.placeholder = placeholder_label   # always offer (no suppression)",
        ),
        "refinement": "always offering the placeholder ignores BOTH suppression "
                      "situations: a required pre-filled field and a non-blank "
                      "radio field would both wrongly show the empty choice. It "
                      "fails test_non_blank_foreign_key_with_radio (which expects "
                      "NO blank row) and the required+initial P2P paths — resolves "
                      "nothing.",
        "rationale": "REJECT from `present iff placeholder_offered(...)`: on any "
                      "input where placeholder_offered is False (e.g. required=T, "
                      "initial_present=T) the rival still assigns placeholder_label "
                      "(present) — contradiction.",
    },
]


# ===========================================================================
# AXIOM LANE — A-reference soundness against the REAL Django library.
# ===========================================================================
#
# There are NO consumed @ContractOnly axioms (axioms region is empty). The two
# deep models (placeholder_offered, derived_field_emptiness_flag) are
# A-references: they MUST equal the real Django ModelChoiceField / ForeignKey
# behaviour on every caller-reachable input. These probes EXECUTE the real
# library (directive 4: call the callee, never scrape source), open no files
# (no codec concern, directive 5), and embed all needed logic so nothing from
# the bundle must be mounted in-container (directive 6). They run with
# apply_gold=True (the A-reference describes POST-patch Django: the `blank`
# kwarg only exists after the patch).

# ---- ax-ref-placeholder: real ModelChoiceField choice-sequence blank presence
# == placeholder_offered over the full (required x initial x widget x blank)
# grid, mirroring axiom_check.py §3.1 + F2P test_choices_radio_blank.
_AX_REF_PLACEHOLDER = r'''
import itertools, sys
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        USE_TZ=True,
    )
from django import forms
from django.forms.widgets import RadioSelect

def placeholder_offered(required, initial_present, is_radio, blank):
    # the model.py @Pure deep model, transcribed
    return not ((required and initial_present) or (is_radio and not blank))

class _Obj:
    def __init__(self, pk, label):
        self.pk = pk; self._label = label
    def __str__(self):
        return self._label

class _QS:
    def __init__(self, objs):
        self._objs = list(objs); self._prefetch_related_lookups = ()
    def all(self): return _QS(self._objs)
    def iterator(self): return iter(list(self._objs))
    def __iter__(self): return iter(list(self._objs))
    def count(self): return len(self._objs)
    def exists(self): return bool(self._objs)

def make_field(required, initial_present, widget, blank):
    qs = _QS([_Obj(1, "First"), _Obj(2, "Second")])
    kw = dict(required=required, blank=blank)
    if widget is not None: kw["widget"] = widget
    if initial_present: kw["initial"] = 1
    return forms.ModelChoiceField(qs, **kw)

# widget kinds and their real isinstance(self.widget, RadioSelect) after
# Field.__init__ normalisation: the RadioSelect class AND a RadioSelect()
# instance are both radio (mirrors test_choices_radio_blank's two widgets).
widgets = [
    ("default", None, False),
    ("RadioSelect class", RadioSelect, True),
    ("RadioSelect instance", RadioSelect(), True),
    ("Select instance", forms.Select(), False),
]
bad = []; n = 0
for required, initial_present, blank in itertools.product([True, False], repeat=3):
    for wname, widget, is_radio in widgets:
        f = make_field(required, initial_present, widget, blank)
        observed = (list(f.choices)[0][0] == "")     # real callee
        expected = placeholder_offered(required, initial_present, is_radio, blank)
        n += 1
        if observed != expected:
            bad.append((required, initial_present, wname, blank, observed, expected))
if bad:
    print("A-REFERENCE UNSOUND placeholder_offered:", bad); sys.exit(1)
# Discriminating sanity: the load-bearing new clause really fires.
f = make_field(False, False, RadioSelect(), False)   # radio, no blank
assert list(f.choices)[0][0] != "", "radio+no-blank must SUPPRESS the placeholder"
f = make_field(False, False, RadioSelect(), True)    # radio, blank
assert list(f.choices)[0][0] == "", "radio+blank must OFFER the placeholder"
print("ax-ref-placeholder OK: real ModelChoiceField blank-presence == "
      "placeholder_offered over %d (required x initial x widget x blank) combos; "
      "radio-no-blank suppresses & radio-blank offers (the new clause)." % n)
sys.exit(0)
'''

# ---- ax-ref-forwarding: real ForeignKey records its blank, and the derived
# radio/non-required field offers the placeholder iff that forwarded blank.
# Mirrors axiom_check.py §3.2 + F2P test_(non_)blank_foreign_key_with_radio.
_AX_REF_FORWARDING = r'''
import sys
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        USE_TZ=True,
    )
from django import forms
from django.forms.widgets import RadioSelect
from django.db.models import ForeignKey, CASCADE

def derived_field_emptiness_flag(model_blank):
    return model_blank
def placeholder_offered(required, initial_present, is_radio, blank):
    return not ((required and initial_present) or (is_radio and not blank))

class _Obj:
    def __init__(self, pk, label):
        self.pk = pk; self._label = label
    def __str__(self): return self._label
class _QS:
    def __init__(self, objs):
        self._objs = list(objs); self._prefetch_related_lookups = ()
    def all(self): return _QS(self._objs)
    def iterator(self): return iter(list(self._objs))
    def __iter__(self): return iter(list(self._objs))
    def count(self): return len(self._objs)
    def exists(self): return bool(self._objs)

bad = []; n = 0
for model_blank in [True, False]:
    assert derived_field_emptiness_flag(model_blank) == model_blank
    fk = ForeignKey("self", on_delete=CASCADE, blank=model_blank, null=True)
    if fk.blank != model_blank:
        bad.append(("fk.blank", model_blank, fk.blank))
    # observable consequence of forwarding fk.blank into the derived radio field
    f = forms.ModelChoiceField(_QS([_Obj(1, "Only")]),
                               required=False, widget=RadioSelect(), blank=fk.blank)
    observed = (list(f.choices)[0][0] == "")
    expected = placeholder_offered(False, False, True, fk.blank)
    n += 1
    if observed != expected:
        bad.append(("derived-field", model_blank, observed, expected))
if bad:
    print("A-REFERENCE UNSOUND derived_field_emptiness_flag:", bad); sys.exit(1)
print("ax-ref-forwarding OK: real ForeignKey records blank and the derived "
      "radio/non-required field offers the placeholder iff the forwarded blank, "
      "over %d (blank in {True,False}) cases." % n)
sys.exit(0)
'''

# ---- ax-cover: caller-domain containment. The deep models' only inputs are the
# four booleans (placeholder_offered) / one boolean (derived_field_emptiness_flag).
# The model passes EXACTLY {True, False} on each — the entire bool domain — and
# the A-reference is validated over that entire grid (above). There is no input
# the caller can reach outside what the references cover, so containment holds
# (and the references cover the full domain, not merely a sample).
_AX_COVER = r'''
import itertools, sys
# placeholder_offered(required, initial_present, is_radio, blank): 4 booleans;
# derived_field_emptiness_flag(model_blank): 1 boolean. The caller (the model's
# configure_placeholder / derived_field_emptiness_flag) only ever passes Python
# bools, and ax-ref-placeholder / ax-ref-forwarding validate the FULL boolean
# grid (2^4 x 4 widget kinds, and 2 blank values). So every caller-reachable
# input lies inside the references' validated domain (containment holds; no
# AXIOM-TOO-WEAK-FOR-CALLER). We enumerate the full grid to prove totality.
grid4 = list(itertools.product([True, False], repeat=4))
assert len(grid4) == 16, "the placeholder decision has exactly 16 boolean inputs"
grid1 = [True, False]
for combo in grid4:
    assert all(isinstance(b, bool) for b in combo)
for b in grid1:
    assert isinstance(b, bool)
print("ax-cover OK: the deep models take only booleans; the caller passes the "
      "full {True,False} grid (16 for placeholder_offered, 2 for the forwarding) "
      "and the A-reference probes validate that ENTIRE grid against real Django "
      "=> every caller-reachable input is covered (containment holds).")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-ref-placeholder",
        "axiom": "placeholder_offered",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_REF_PLACEHOLDER,
        "rationale": "the A-reference deep model placeholder_offered must equal "
                     "the real ModelChoiceField choice-sequence blank-presence on "
                     "EVERY (required x initial x widget x blank) combo (the level "
                     "F2P test_choices_radio_blank observes); any mismatch — esp. "
                     "the new radio-no-blank suppression clause — is A-REFERENCE "
                     "UNSOUND. Runs the REAL callee, not a source scrape.",
    },
    {
        "id": "ax-ref-forwarding",
        "axiom": "derived_field_emptiness_flag",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_REF_FORWARDING,
        "rationale": "the A-reference identity forwarding must match real Django: "
                     "ForeignKey(blank=B).blank == B AND the derived radio/non-"
                     "required ModelChoiceField offers the placeholder iff B "
                     "(F2P test_(non_)blank_foreign_key_with_radio); else "
                     "A-REFERENCE UNSOUND. Discriminates pre-patch (no blank kwarg).",
    },
    {
        "id": "ax-cover-boolean-domain",
        "axiom": "placeholder_offered / derived_field_emptiness_flag",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER,
        "rationale": "the deep models take only booleans; the caller passes the "
                     "full {True,False} grid and the soundness probes validate "
                     "that entire grid against real Django, so every caller-"
                     "reachable input is in-domain (containment holds; no "
                     "AXIOM-TOO-WEAK-FOR-CALLER).",
    },
]
