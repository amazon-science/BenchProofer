"""PBT falsification battery for django__django-14534.

Target spec (FROZEN): `label_target_id(ctx: ChoiceContext) -> Optional[int]`
in model.py. It models post-patch `BoundWidget.id_for_label`, whose gold body
is `return self.data['attrs'].get('id')`. The defended surface:

  Read-only inputs (all at fractional permission -> MUST NOT be mutated):
    Requires/Ensures Acc(ctx.attrs, 1/2), Acc(dict_pred(ctx.attrs), 1/2),
                     Acc(ctx.name, 1/2), Acc(ctx.index, 1/2)
  Frame:   Ensures(ctx.attrs is Old(ctx.attrs))            # dict not swapped
  Clause1: Implies(id_key() in ctx.attrs, Result() is not None)
  Clause2: Implies(id_key() in ctx.attrs, Result() == ctx.attrs[id_key()])
           # present -> the RECORDED id verbatim (honours the configured prefix)
  Clause3: Implies(not (id_key() in ctx.attrs), Result() is None)
           # absent  -> None (no fabrication from name/index)

The oracle is GROUNDED in the input: clause 2 pins Result() to ctx.attrs[id_key()],
a fully-unfolded function of the argument; id_key() is the constant key token (1),
not an opaque answer-key. So there is no "wrong echo that still verifies" attack
(see UNGROUNDED-ORACLE note in assessment); instead the falsification pressure is
on the two value clauses (present == recorded id; absent == None) and on the
read-only permission discipline.

Authoring: region-surgery via _swap, editing ONLY text inside the single
# impl-start / # impl-end region of label_target_id. The frozen spec (the
ChoiceContext class, pure id_key(), pre/post-conditions) is never touched, so
same_spec holds for every spec case by construction.

Axiom lane: there are NO consumed @ContractOnly axioms (the axioms region is a
comment). There is ONE A-reference deep model: label_target_id == real
post-patch BoundWidget.id_for_label == attrs.get('id'). PLAN §2.4 checks an
A-reference like an axiom: the deep model must equal the real callee on every
caller-reachable input (axiom-soundness) and every callee-input the model can
reach must lie in the callee's domain (axiom-containment). Both probes drive the
genuine Django subwidget data path in-container (apply_gold=True), reusing the
logic of axiom_check.py.
"""
from pathlib import Path

INSTANCE = "django__django-14534"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not present")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region of label_target_id (between # impl-start / # impl-end).
_GOLD_IMPL = """    if id_key() in ctx.attrs:
        return ctx.attrs[id_key()]
    return None"""

# Sanity: the gold model.py impl region is exactly this text (so every variant is
# a single-occurrence in-region edit). If the bundle drifts, _swap raises.
assert _GOLD_IMPL in _BASE, "model.py impl region drifted from expected gold body"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): structurally-different but CORRECT impl.
# Branch-reorder + early-return on absence + local-variable binding of the
# lookup. Keeps the exact gold proof obligations (same membership test, same
# lookup `ctx.attrs[id_key()]`); only the executable shape changes. Must verify
# (else SPEC-TOO-STRONG: a faithful correct impl is rejected).
# ---------------------------------------------------------------------------
_pos_control = _swap(
    _BASE, _GOLD_IMPL,
    """    if not (id_key() in ctx.attrs):
        return None
    recorded = ctx.attrs[id_key()]  # type: int
    return recorded""")


# ---------------------------------------------------------------------------
# ADMISSIBILITY: confirm the precondition admits a normal F2P-shaped input by
# reading every read-only grant under its fractional permission, then returning
# the gold result. If the Requires could not be established / read for a
# legitimate input this would fail -> PRECOND-TOO-STRONG. (Done in-region: a
# top-level caller would change spec_view and break same_spec.)
# ---------------------------------------------------------------------------
_admiss = _swap(
    _BASE, _GOLD_IMPL,
    """    # read each read-only grant under its 1/2 permission (admissibility)
    Assert(Acc(ctx.attrs, 1 / 2))
    Assert(Acc(dict_pred(ctx.attrs), 1 / 2))
    Assert(Acc(ctx.name, 1 / 2))
    Assert(Acc(ctx.index, 1 / 2))
    nm = ctx.name    # type: int
    ix = ctx.index   # type: int
    Assert(nm == ctx.name and ix == ctx.index)
    present = id_key() in ctx.attrs  # type: bool
    if present:
        return ctx.attrs[id_key()]
    return None""")


# ---------------------------------------------------------------------------
# FRAME-MUTATION (MANDATORY — ctx.attrs/name/index are all read-only Acc(.,1/2)).
# A rival that WRITES into the read-only attribute mapping to satisfy the
# postcondition. The dict carries only Acc(dict_pred(ctx.attrs), 1/2); a write
# `ctx.attrs[id_key()] = ...` needs FULL dict_pred permission, so this must be
# REJECTED for INSUFFICIENT PERMISSION (not a postcondition failure). Gold
# logic is otherwise verbatim, so the rejection is attributable to the write.
# Refinement: the faithful real patch would do
#   self.data['attrs']['id'] = self.data['attrs'].get('id'); return ...['id']
# i.e. it stamps an 'id' key into the per-option attrs dict that BoundWidget
# shares with the rendered control. On the auto_id=False (no-id) config the
# real attrs has NO 'id' key; writing one fabricates an identifier into the
# rendered <input>/<option>, and `.get('id')` then returns that fabricated
# value instead of None -> F2P test_iterable_boundfield_select (expects None)
# FAILS. So a verifying mutation would be a true verify-not-resolve break.
# ---------------------------------------------------------------------------
_frame_mut_dict = _swap(
    _BASE, _GOLD_IMPL,
    """    ctx.attrs[id_key()] = ctx.name   # ILLEGAL write into read-only attrs (only 1/2 dict_pred)
    if id_key() in ctx.attrs:
        return ctx.attrs[id_key()]
    return None""")

# Supporting frame variant: overwrite the read-only field handle ctx.name
# (Acc(ctx.name, 1/2) is read-only). Needs full field permission -> rejected.
# Refinement: a real patch that reassigns self.data['name'] mutates the shared
# per-option context BoundWidget.data, corrupting the name used elsewhere when
# rendering the option -> regresses the rendered markup the P2P tests assert.
_frame_mut_field = _swap(
    _BASE, _GOLD_IMPL,
    """    ctx.name = ctx.index   # ILLEGAL write to read-only field (only Acc(ctx.name, 1/2))
    if id_key() in ctx.attrs:
        return ctx.attrs[id_key()]
    return None""")


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN A: correct on the id-PRESENT sub-domain, wrong on ABSENT.
# When the attribute mapping records no id, this fabricates a non-None value
# from name/index instead of None -> violates clause 3
# (Implies(not in, Result() is None)). MUST be REJECTED.
# Refinement: this is `attrs.get('id') or 'id_%s_%s'%(name,index)`. On the
# auto_id=False config (Select, no 'id' key) the real method must return None
# (F2P test_iterable_boundfield_select asserts fields[0].id_for_label is None);
# this rival returns a fabricated 'id_name_0' -> that F2P FAILS. Faithful real
# patch does NOT resolve.
# ---------------------------------------------------------------------------
_partial_absence = _swap(
    _BASE, _GOLD_IMPL,
    """    if id_key() in ctx.attrs:
        return ctx.attrs[id_key()]
    fabricated = ctx.name * 1000 + ctx.index  # type: int
    return fabricated""")


# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN B: correct on the id-ABSENT sub-domain (returns None), wrong on
# PRESENT. When an id IS recorded, returns a value fabricated from name/index
# rather than the recorded id -> violates clause 2
# (Implies(in, Result() == ctx.attrs[id_key()])). MUST be REJECTED.
# Refinement: ignores the recorded (fully-resolved, prefix-honouring) id. On the
# auto_id='prefix_%s' config the recorded id is 'prefix_field_0' but this
# returns the name/index fabrication 'id_field_0' -> F2P
# test_boundfield_subwidget_id_for_label (asserts 'prefix_field_0') FAILS.
# Faithful real patch does NOT resolve.
# ---------------------------------------------------------------------------
_partial_present = _swap(
    _BASE, _GOLD_IMPL,
    """    if id_key() in ctx.attrs:
        fabricated = ctx.name * 1000 + ctx.index  # type: int
        return fabricated
    return None""")


# ---------------------------------------------------------------------------
# SUPPORTING near-miss 1: the pre-patch bug verbatim (always fabricate from
# name/index, ignore attrs). Independent of attrs: violates clause 1/2 when id
# present AND clause 3 when absent. MUST be REJECTED (this is model_prepatch.py;
# G-DIFF already shows the spec senses it — replicated here as a cheap control).
# Refinement: identical to the removed buggy body; fails BOTH F2P tests.
# ---------------------------------------------------------------------------
_prepatch = _swap(
    _BASE, _GOLD_IMPL,
    """    fabricated = ctx.name * 1000 + ctx.index  # type: int
    return fabricated""")


# ---------------------------------------------------------------------------
# SUPPORTING near-miss 2: always return None. Correct ONLY where no id is
# recorded; when an id IS recorded it must equal that id (clause 1: not None,
# clause 2: == recorded). MUST be REJECTED.
# Refinement: drops the recorded id on every prefixed/default config; F2P
# test_boundfield_subwidget_id_for_label (expects 'prefix_field_0') FAILS.
# ---------------------------------------------------------------------------
_always_none = _swap(
    _BASE, _GOLD_IMPL,
    """    none_result = None  # type: Optional[int]
    return none_result""")


SPEC_TESTS = [
    {
        "id": "pos-control-reorder-early-return",
        "kind": "soundness", "expect": "verify",
        "module": _pos_control,
        "rationale": "branch-reorder (absence handled first) + local-binding of "
                     "the lookup keeps every gold proof obligation; a "
                     "structurally-different CORRECT impl must verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-read-only-grants",
        "kind": "admissibility", "expect": "verify",
        "module": _admiss,
        "rationale": "asserts all four read-only 1/2 grants hold and reads "
                     "name/index/attrs-membership for an F2P-shaped input; the "
                     "precondition must admit a normal input, else "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-write-attrs",
        "kind": "uniqueness", "expect": "reject",
        "module": _frame_mut_dict,
        "refinement": "stamping an 'id' into the shared per-option attrs dict "
                      "fabricates an identifier on the auto_id=False config where "
                      "attrs has no 'id'; .get('id') then returns it instead of "
                      "None, so F2P test_iterable_boundfield_select (expects None) "
                      "fails -> faithful real patch does NOT resolve.",
        "rationale": "write into ctx.attrs needs FULL dict_pred but only "
                     "Acc(dict_pred(ctx.attrs),1/2) is held -> rejected for "
                     "INSUFFICIENT PERMISSION (permission system, not a value "
                     "clause). #1 weakness class.",
    },
    {
        "id": "frame-mutation-write-name",
        "kind": "uniqueness", "expect": "reject",
        "module": _frame_mut_field,
        "refinement": "reassigning self.data['name'] mutates the shared per-option "
                      "BoundWidget.data, corrupting the option's name used in the "
                      "rendered markup the P2P forms tests assert -> faithful real "
                      "patch does NOT resolve.",
        "rationale": "write to ctx.name needs full field permission but only "
                     "Acc(ctx.name,1/2) is held -> rejected for INSUFFICIENT "
                     "PERMISSION. Supporting frame case.",
    },
    {
        "id": "partial-domain-absence-fabricates",
        "kind": "uniqueness", "expect": "reject",
        "module": _partial_absence,
        "refinement": "= attrs.get('id') or 'id_%s_%s'%(name,index); on the "
                      "auto_id=False (Select) config attrs has no 'id', real "
                      "id_for_label must be None, but this returns a fabricated "
                      "'id_name_0' -> F2P test_iterable_boundfield_select "
                      "(asserts None) fails. Faithful real patch does NOT resolve.",
        "rationale": "violates clause 3 Implies(not (id_key() in ctx.attrs), "
                     "Result() is None): on the absent sub-domain it returns a "
                     "non-None fabrication.",
    },
    {
        "id": "partial-domain-present-fabricates",
        "kind": "uniqueness", "expect": "reject",
        "module": _partial_present,
        "refinement": "ignores the recorded fully-resolved id; on auto_id='prefix_%s' "
                      "the recorded id is 'prefix_field_0' but this returns the "
                      "name/index fabrication 'id_field_0' -> F2P "
                      "test_boundfield_subwidget_id_for_label (asserts "
                      "'prefix_field_0') fails. Faithful real patch does NOT resolve.",
        "rationale": "violates clause 2 Implies(id_key() in ctx.attrs, Result() == "
                     "ctx.attrs[id_key()]): on the present sub-domain it returns a "
                     "value other than the recorded id.",
    },
    {
        "id": "support-prepatch-fabrication",
        "kind": "uniqueness", "expect": "reject",
        "module": _prepatch,
        "refinement": "verbatim pre-patch buggy body 'id_%s_%s'%(name,index); "
                      "independent of attrs; fails BOTH F2P tests (wrong prefix on "
                      "config 1, fabricated id instead of None on config 3). "
                      "Faithful real patch (= no patch) does NOT resolve.",
        "rationale": "violates clauses 1/2 (present: not the recorded id, and "
                     "is non-None) AND clause 3 (absent: non-None). This is "
                     "model_prepatch.py; supporting near-miss.",
    },
    {
        "id": "support-always-none",
        "kind": "uniqueness", "expect": "reject",
        "module": _always_none,
        "refinement": "drops the recorded id everywhere; on auto_id='prefix_%s' "
                      "and default auto_id='id_%s' the real method returns the "
                      "recorded id, not None -> F2P "
                      "test_boundfield_subwidget_id_for_label fails. Faithful real "
                      "patch does NOT resolve.",
        "rationale": "violates clause 1 Implies(id_key() in ctx.attrs, Result() "
                     "is not None) and clause 2 on the present sub-domain. "
                     "Supporting near-miss.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — the single A-reference deep model
#   label_target_id == real BoundWidget.id_for_label == attrs.get('id')
# checked PLAN §2.4-style. Both probes run in the instance image with the gold
# patch applied (apply_gold=True), import only Django (configured minimally) +
# stdlib, open nothing on disk, print a diagnostic, and exit(0) iff the
# obligation holds. They reuse the genuine Django subwidget data path of
# axiom_check.py (build real forms for the F2P/P2P configs and fuzzed variants).
# ---------------------------------------------------------------------------

# axiom-soundness probe: drive the REAL post-patch BoundWidget.id_for_label and
# assert it equals attrs.get('id') (the deep model's Result()) on the three
# pinned form configs PLUS fuzzed prefixes/choice-counts/widget-level ids. Also
# positively assert the pre-patch fabrication DIVERGES on the configured-prefix
# and no-id configs, so the equality is load-bearing, not vacuous. Any
# disagreement => AXIOM-UNSOUND.
_AX_SOUND = r'''
import sys, random

def _setup():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True, USE_TZ=False,
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={},
        )
        django.setup()

def main():
    try:
        _setup()
        from django.forms import (
            Form, ChoiceField, MultipleChoiceField,
            RadioSelect, Select, CheckboxSelectMultiple,
        )
    except Exception as e:
        print("AXIOM-SOUND ERROR: cannot import/configure Django: %r" % (e,))
        return 1

    def build_subwidgets(widget_cls, choices, auto_id, multiple):
        field_cls = MultipleChoiceField if multiple else ChoiceField
        class SomeForm(Form):
            field = field_cls(choices=choices, widget=widget_cls)
        form = SomeForm(auto_id=auto_id)
        return list(form["field"].subwidgets)

    def model_result(attrs):
        # model.py deep model over the real attrs dict: recorded id if 'id' in
        # attrs (id_key() token), else None.
        if "id" in attrs:
            return attrs["id"]
        return None

    def prepatch(data):
        return "id_%s_%s" % (data["name"], data["index"])

    n_sub = 0
    n_div = 0

    # --- the three pinned F2P/P2P configs ---
    configs = [
        (CheckboxSelectMultiple, [("a", "A"), ("b", "B")], "prefix_%s", True, "prefix_"),
        (RadioSelect, [("john", "John"), ("paul", "Paul")], True, False, "id_"),
        (Select, [("john", "John"), ("paul", "Paul")], False, False, None),
    ]
    for widget, choices, auto_id, multiple, prefix in configs:
        subs = build_subwidgets(widget, choices, auto_id, multiple)
        if not subs:
            print("AXIOM-SOUND ERROR: no subwidgets for auto_id=%r" % (auto_id,))
            return 1
        for idx, sw in enumerate(subs):
            data = sw.data
            real = sw.id_for_label                 # REAL post-patch property
            expected = data["attrs"].get("id")     # what attrs.get('id') gives
            if real != expected:
                print("AXIOM-UNSOUND: real id_for_label %r != attrs.get('id') %r "
                      "(auto_id=%r idx=%d)" % (real, expected, auto_id, idx))
                return 1
            if model_result(data["attrs"]) != expected:
                print("AXIOM-UNSOUND: deep model %r != real %r (auto_id=%r idx=%d)"
                      % (model_result(data["attrs"]), expected, auto_id, idx))
                return 1
            # load-bearing divergence of the buggy fabrication on the
            # discriminating configs (configured prefix; no id)
            fab = prepatch(data)
            if prefix is None:
                if expected is not None:
                    print("AXIOM-SOUND ERROR: no-id config recorded an id %r" % (expected,))
                    return 1
                if fab == expected:
                    print("AXIOM-SOUND ERROR: fabrication did not diverge from None")
                    return 1
                n_div += 1
            elif prefix == "prefix_":
                if not (isinstance(expected, str) and expected.startswith("prefix_")):
                    print("AXIOM-SOUND ERROR: prefix config did not honour prefix: %r" % (expected,))
                    return 1
                if fab == expected:
                    print("AXIOM-SOUND ERROR: fabrication did not diverge from prefixed id")
                    return 1
                n_div += 1
            n_sub += 1

    # --- fuzz prefixes / choice counts / widget-level attrs['id'] ---
    rng = random.Random(14534)
    for _ in range(300):
        k = rng.randint(1, 5)
        choices = [("c%d" % i, "C%d" % i) for i in range(k)]
        roll = rng.random()
        if roll < 0.34:
            widget, multiple = CheckboxSelectMultiple, True
        elif roll < 0.67:
            widget, multiple = RadioSelect, False
        else:
            widget, multiple = Select, False
        ar = rng.random()
        if ar < 0.34:
            auto_id = "p%d_%%s" % rng.randint(0, 99)
        elif ar < 0.67:
            auto_id = True          # default 'id_%s'
        else:
            auto_id = False         # no id generation
        try:
            subs = build_subwidgets(widget, choices, auto_id, multiple)
        except Exception as e:
            print("AXIOM-SOUND ERROR: build failed auto_id=%r: %r" % (auto_id, e))
            return 1
        for sw in subs:
            data = sw.data
            real = sw.id_for_label
            expected = data["attrs"].get("id")
            if real != expected:
                print("AXIOM-UNSOUND (fuzz): real %r != attrs.get('id') %r (auto_id=%r)"
                      % (real, expected, auto_id))
                return 1
            if model_result(data["attrs"]) != expected:
                print("AXIOM-UNSOUND (fuzz): deep model %r != real %r" %
                      (model_result(data["attrs"]), expected))
                return 1
            n_sub += 1

    print("AXIOM-SOUND OK: real BoundWidget.id_for_label == attrs.get('id') == "
          "deep model on %d real subwidgets; %d load-bearing fabrication "
          "divergences on the prefix/no-id configs." % (n_sub, n_div))
    return 0

sys.exit(main())
'''

# axiom-containment probe: enumerate EXACTLY the callee-inputs model.py can pass
# to the real callee (dict.get('id') over self.data['attrs']) and assert each
# lies in the callee's domain. The model reaches the real attrs dict only via
# `id_key() in ctx.attrs` (membership) and `ctx.attrs[id_key()]` (lookup of the
# 'id' key when present) -- i.e. the only key the model touches is 'id'. For
# real dict.get, the ENTIRE key space is in-domain (dict.get('id') is total: it
# returns None when absent), so containment is trivially satisfied for any attrs
# the model can reach. We confirm this concretely: across the three pinned
# configs + fuzz, every real per-option attrs dict (a) supports `'id' in attrs`
# and `attrs.get('id')` without error and (b) either has the 'id' key (lookup
# defined) or not (get returns None) -- exactly the two branches the model
# distinguishes. Covering MORE keys than the model touches would be SOUND; a
# reachable input outside the domain would be AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAIN = r'''
import sys, random

def _setup():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True, USE_TZ=False,
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={},
        )
        django.setup()

def main():
    try:
        _setup()
        from django.forms import (
            Form, ChoiceField, MultipleChoiceField,
            RadioSelect, Select, CheckboxSelectMultiple,
        )
    except Exception as e:
        print("AXIOM-CONTAIN ERROR: cannot import/configure Django: %r" % (e,))
        return 1

    def build_subwidgets(widget_cls, choices, auto_id, multiple):
        field_cls = MultipleChoiceField if multiple else ChoiceField
        class SomeForm(Form):
            field = field_cls(choices=choices, widget=widget_cls)
        form = SomeForm(auto_id=auto_id)
        return list(form["field"].subwidgets)

    checked = 0
    present = 0
    absent = 0

    def check_attrs(attrs, ctx):
        nonlocal checked, present, absent
        # the callee domain: attrs must be a mapping supporting membership of
        # the literal 'id' key and dict.get('id'); both are total over dict.
        if not hasattr(attrs, "get"):
            print("AXIOM-TOO-WEAK-FOR-CALLER: attrs has no .get (%s): %r" % (ctx, attrs))
            return False
        try:
            has = "id" in attrs            # the model's `id_key() in ctx.attrs`
            got = attrs.get("id")          # the callee `attrs.get('id')`
        except Exception as e:
            print("AXIOM-TOO-WEAK-FOR-CALLER: membership/get raised (%s): %r" % (ctx, e))
            return False
        if has:
            # the model then evaluates ctx.attrs[id_key()] -- must be defined
            try:
                v = attrs["id"]
            except Exception as e:
                print("AXIOM-TOO-WEAK-FOR-CALLER: 'id' in attrs but lookup raised "
                      "(%s): %r" % (ctx, e))
                return False
            if v != got:
                print("AXIOM-TOO-WEAK-FOR-CALLER: attrs['id'] %r != attrs.get('id') %r "
                      "(%s)" % (v, got, ctx))
                return False
            present += 1
        else:
            if got is not None:
                print("AXIOM-TOO-WEAK-FOR-CALLER: 'id' absent but get returned %r (%s)"
                      % (got, ctx))
                return False
            absent += 1
        checked += 1
        return True

    configs = [
        (CheckboxSelectMultiple, [("a", "A"), ("b", "B")], "prefix_%s", True),
        (RadioSelect, [("john", "John"), ("paul", "Paul")], True, False),
        (Select, [("john", "John"), ("paul", "Paul")], False, False),
    ]
    for widget, choices, auto_id, multiple in configs:
        for sw in build_subwidgets(widget, choices, auto_id, multiple):
            if not check_attrs(sw.data["attrs"], "auto_id=%r" % (auto_id,)):
                return 1

    rng = random.Random(20240534)
    for _ in range(300):
        k = rng.randint(1, 5)
        choices = [("c%d" % i, "C%d" % i) for i in range(k)]
        roll = rng.random()
        if roll < 0.34:
            widget, multiple = CheckboxSelectMultiple, True
        elif roll < 0.67:
            widget, multiple = RadioSelect, False
        else:
            widget, multiple = Select, False
        ar = rng.random()
        if ar < 0.34:
            auto_id = "p%d_%%s" % rng.randint(0, 99)
        elif ar < 0.67:
            auto_id = True
        else:
            auto_id = False
        try:
            subs = build_subwidgets(widget, choices, auto_id, multiple)
        except Exception as e:
            print("AXIOM-CONTAIN ERROR: build failed auto_id=%r: %r" % (auto_id, e))
            return 1
        for sw in subs:
            if not check_attrs(sw.data["attrs"], "fuzz auto_id=%r" % (auto_id,)):
                return 1

    print("AXIOM-CONTAIN OK: every caller-reachable attrs dict (%d total: "
          "%d with 'id', %d without) lies in the dict.get('id') domain "
          "(membership + lookup total over dict)." % (checked, present, absent))
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-id-for-label",
        "axiom": "label_target_id (A-reference: == real BoundWidget.id_for_label == attrs.get('id'))",
        "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
        "probe": _AX_SOUND,
        "rationale": "drives the REAL post-patch property over the 3 pinned form "
                     "configs + fuzz; if real id_for_label != attrs.get('id') == "
                     "deep model, AXIOM-UNSOUND. Also asserts the pre-patch "
                     "fabrication diverges where the F2P tests demand (equality "
                     "load-bearing).",
    },
    {
        "id": "ax-contain-attrs-get-domain",
        "axiom": "label_target_id (A-reference: dict.get('id') domain)",
        "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
        "probe": _AX_CONTAIN,
        "rationale": "every per-option attrs dict the model can reach supports "
                     "membership of 'id' + dict.get('id') (total over dict); a "
                     "reachable input outside that domain => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
