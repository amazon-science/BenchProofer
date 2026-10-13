# properties.py — PBT falsification battery for django__django-11790.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec. Region surgery (editing ONLY inside impl-start/impl-end)
# GUARANTEES same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   configure_username_field(declared_max_length: Optional[int],
#                            widget_attrs: Dict[str, object]) -> int
#   resolves the identifier field's length limit (declared-or-default 254) and
#   writes that SAME resolved value into BOTH (1) the returned field-level limit
#   and (2) the widget attribute map under the 'maxlength' token (attr_maxlength()).
#   The dropped second write is the regression (#27515) the gold patch restores.
#
#   widget_attrs is held at FULL permission (Requires(dict_pred(widget_attrs)),
#   NOT Acc(...,1/2)) because it is genuinely mutated in place. => NO read-only
#   input; the MANDATORY frame-mutation (insufficient-permission) class does NOT
#   apply. The corresponding attack here is value-level: a rival that disturbs a
#   pre-existing attribute is caught by the value-preservation postcondition, not
#   by a permission error. (See 'assessment'.)
#
#   DOMAIN IS TOTAL. `dict_pred(widget_attrs)` is the ONLY precondition: the spec
#   states no requirement about what the widget already carries, so every clause
#   below binds on EVERY starting state. This matters for the reject lane: two
#   membership preconditions previously restricted the domain
#   (`attr_maxlength() not in widget_attrs`, `attr_other() in widget_attrs`), and
#   inside the excluded region every postcondition was discharged VACUOUSLY --
#   a rival could deviate arbitrarily there and still verify, while under a
#   faithful refinement that deviation is real behaviour on states the caller
#   does reach (a widget already advertising its own length limit; a widget with
#   no other attribute at all). W8-W11 below are exactly that class, and they are
#   load-bearing only because the domain is now total.
#
#   resolve_limit is a @Pure helper but it is GROUNDED: fully unfolded as
#   `declared if declared is not None else default_limit()` (= 254), a pure
#   function of the single arg. There is NO opaque answer-key / exact-marker to
#   echo without doing the work, so the ungrounded-oracle-echo class does NOT
#   apply; instead the resolution is attacked via a partial-domain rival that
#   hardcodes the default and diverges on the declared-non-default branch.
#
# Load-bearing post clauses (each rejects a distinct wrong impl):
#   C1  Result() == resolve_limit(declared_max_length)          (field value)
#   C2  attr_maxlength() in widget_attrs                        (widget attr present)
#   C3  widget_attrs[attr_maxlength()] == limit_value(resolve_limit(...))
#                                                               (widget value)
#   C4  widget_attrs[attr_maxlength()] == limit_value(Result())  (field == widget)
#   C5  Forall(a: a!=maxlength => (a in widget_attrs) == Old(a in widget_attrs))
#       (membership frame: no other key added OR dropped — rejects a rival
#       that writes any spurious extra widget attribute)
#   C6  Forall(a: a!=maxlength & Old(a in widget_attrs) =>
#              widget_attrs[a] == Old(widget_attrs[a]))
#       (value frame: every pre-existing attribute keeps its exact value)
#   C7  Old(attr_other() in widget_attrs) =>
#         attr_other() in widget_attrs & widget_attrs[attr_other()] ==
#         Old(widget_attrs[attr_other()])
#       (constant-witness membership+value preservation, a concrete instance of
#        C5/C6, GUARDED so it does not smuggle back the dropped precondition:
#        when the widget carried no such attribute, the operation does not
#        invent one and the clause says nothing about it)
#
# F2P (instance.json): test_username_field_max_length_matches_user_model asserts
#   widget.attrs.get('maxlength') == 255 (CustomEmailField, declared=255);
#   test_username_field_max_length_defaults_to_254 asserts == 254
#   (IntegerUsernameUser, declared=None). Both also assert field.max_length.
#   The two branches (declared int / declared None) are both witnessed.

from pathlib import Path

INSTANCE = "django__django-11790"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the exact impl-region body (verbatim from model.py, between the markers) --
# Every variant is produced by _swap on this block; the markers themselves and
# everything outside the impl region (signature, pre/post-conditions, @Pure
# helpers) are NEVER touched => same_spec is guaranteed.
_IMPL = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs[attr_maxlength()] = username_max_length\n"
    "    return field_max_length\n"
)

# sanity: the gold body appears verbatim & uniquely in the frozen model.
assert _BASE.count(_IMPL) == 1, "IMPL anchor drift"


# =========================== POSITIVE CONTROL ===========================
# Structurally-different but CORRECT: the dict write is performed FIRST and the
# field-level limit is derived AFTERWARD, from the value carried in the widget
# map, via a read-back that ESTABLISHES the field==widget agreement rather than
# assuming it. Same observable content; only the executable order/data-flow
# changes (no loop, no fold, no lemma needed — directive-3 safe). Note the
# read-back goes through the opaque value domain: the value read out of the map
# cannot be returned as a number directly (nothing may be computed from it), so
# the agreement is established by asserting the injection. Must verify, else
# SPEC-TOO-STRONG.
_POS = (
    "    resolved = resolve_limit(declared_max_length)\n"
    "    widget_attrs[attr_maxlength()] = resolved\n"
    "    Assert(widget_attrs[attr_maxlength()] == limit_value(resolved))\n"
    "    return resolved\n"
)
POS = _swap(_BASE, _IMPL, _POS)


# =========================== ADMISSIBILITY ===========================
# Confirms the precondition admits a normal F2P-shaped input. The precondition
# is now just full permission (dict_pred) -- the operation is TOTAL over
# starting states, so there is no membership conjunct left to probe for
# admissibility. We build a concrete widget map, then exercise the declared=255
# (CustomEmailField) branch on it, asserting the resolution and the post-state
# the spec demands. A separate top-level helper would break same_spec
# (spec_view captures module-level defs), so the probe lives INSIDE the impl
# region, before the gold body, which is kept verbatim after it. If the
# Requires rejected a normal input these asserts would fail =>
# PRECOND-TOO-STRONG.
#
# DOMAIN-TOTALITY NOTE. Two membership preconditions
# (`attr_maxlength() not in widget_attrs`, `attr_other() in widget_attrs`) were
# REMOVED from the spec, because they were an unstated domain restriction: the
# real call site does not occupy only those states (a caller may hand in a
# widget that already advertises a length limit of its own, or one carrying no
# other attribute at all), and every clause below was therefore discharged
# VACUOUSLY on the excluded states -- an impl could do anything there and still
# verify. The probe accordingly also witnesses the two formerly-excluded
# pre-states as admissible and pins the required post-state on each.
#
# TERMINATION NOTE. This probe was originally a literal SELF-CALL
# (`echoed = configure_username_field(255, sample)`). Once the spec acquired
# Requires(MustTerminate(2)) that form became structurally unverifiable, and
# correctly so: a direct self-call has caller level == callee level (both 2), so
# Nagini reports `Obligation leak check failed. Callee configure_username_field
# might not take all unsatisfied obligations from the caller.` Raising the level
# CANNOT fix it -- caller and callee share one precondition, so the level moves
# in lockstep and can never strictly decrease. Unbounded self-recursion is
# exactly what the obligation exists to reject, so the probe is re-expressed
# WITHOUT recursing: the same witness map, the same resolution facts, and the
# same post-state, established by an inlined gold transition on the witness.
# This is a STRENGTHENING, not a weakening -- the deleted version asserted only
# `echoed == 255` and the widget read; this one additionally pins both branches
# of resolve_limit and the preservation of the pre-existing attribute's value.
_ADMISS = (
    "    sample = {attr_other(): 7}  # type: Dict[str, object]\n"
    # the sole Requires conjunct holds of a normal F2P-shaped input
    "    Assert(dict_pred(sample))\n"
    # both branches of the resolution are in-domain and give the F2P values
    "    Assert(resolve_limit(255) == 255)\n"
    "    Assert(resolve_limit(None) == default_limit())\n"
    # the gold transition, inlined on the witness (no recursion => no leak)
    "    sample[attr_maxlength()] = resolve_limit(255)\n"
    "    Assert(attr_maxlength() in sample)\n"
    "    Assert(sample[attr_maxlength()] == limit_value(255))\n"
    # the pre-existing unrelated attribute survives untouched
    "    Assert(sample[attr_other()] == limit_value(7))\n"
    # DOMAIN TOTALITY, witness 1: a widget that ALREADY advertises a length
    # limit of its own is admissible, and the required post-state replaces that
    # stale limit with the resolved one (formerly excluded by
    # `attr_maxlength() not in widget_attrs`).
    "    stale = {attr_other(): 7, attr_maxlength(): 75}  # type: Dict[str, object]\n"
    "    Assert(dict_pred(stale))\n"
    "    stale[attr_maxlength()] = resolve_limit(None)\n"
    "    Assert(stale[attr_maxlength()] == limit_value(default_limit()))\n"
    "    Assert(stale[attr_other()] == limit_value(7))\n"
    # DOMAIN TOTALITY, witness 2: a widget carrying NO other attribute is
    # admissible, and the required post-state establishes the length limit
    # without inventing any other attribute (formerly excluded by
    # `attr_other() in widget_attrs`).
    "    bare = {}  # type: Dict[str, object]\n"
    "    Assert(dict_pred(bare))\n"
    "    bare[attr_maxlength()] = resolve_limit(255)\n"
    "    Assert(bare[attr_maxlength()] == limit_value(255))\n"
    "    Assert(attr_other() not in bare)\n"
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs[attr_maxlength()] = username_max_length\n"
    "    return field_max_length\n"
)
ADMISS = _swap(_BASE, _IMPL, _ADMISS)


# =========================== UNIQUENESS / REJECT rivals ===========================

# --- W1 dropped widget write (== the regression / model_prepatch) ---
# Omits the second write entirely: configures only the field-level limit, never
# establishing widget_attrs[maxlength]. This is EXACTLY the pre-patch behaviour
# (#27515 regression) and exactly model_prepatch.py. Faithful real patch: the
# pre-patch single line `self.fields['username'].max_length = ... or 254` with no
# widget write -> form.fields['username'].widget.attrs.get('maxlength') is None ->
# both F2P tests (which assert it == 255 / 254) FAIL. Headline weakness.
# Rejected by C2 (attr_maxlength() in widget_attrs): the attribute is never added.
_W1_DROP_WIDGET = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    return field_max_length\n"
)
W1_DROP_WIDGET = _swap(_BASE, _IMPL, _W1_DROP_WIDGET)


# --- W2 widget gets WRONG (constant default) value; field correct ---
# Returns the correctly resolved field limit but writes the DEFAULT 254 into the
# widget regardless of the declared maximum. Correct on the declared=None branch
# (resolve_limit==254); DIVERGES on the declared-int branch (e.g. 255), where the
# widget would advertise maxlength=254 while server-side validation allows 255.
# This is the value-double-mask: field and widget no longer carry the SAME value.
# Faithful real patch: `widget.attrs['maxlength'] = 254` (a hardcoded literal)
# instead of the hoisted `username_max_length`. F2P
# test_username_field_max_length_matches_user_model asserts
# widget.attrs.get('maxlength') == 255 -> FAILS. Rejected by C3
# (widget_attrs[maxlength] == resolve_limit(declared)): on declared=255 the
# constant 254 != 255 (and by C4, field 255 != widget 254).
_W2_WIDGET_DEFAULT = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs[attr_maxlength()] = default_limit()\n"
    "    return field_max_length\n"
)
W2_WIDGET_DEFAULT = _swap(_BASE, _IMPL, _W2_WIDGET_DEFAULT)


# --- W3 field/return off by one; widget correct ---
# Writes the correct resolved value into the widget but RETURNS resolved+1 as the
# field-level limit. Field and widget diverge (the two no longer carry the same
# value). Faithful real patch: `self.fields['username'].max_length =
# username_max_length + 1` while the widget write stays correct -> server-side
# validation cap is one off from the rendered cap; the F2P assertion
# form.fields['username'].max_length == 255 FAILS. Rejected by C1
# (Result() == resolve_limit(declared)) and by C4 (Result() == widget value).
_W3_FIELD_OFFBY1 = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length + 1\n"
    "    widget_attrs[attr_maxlength()] = username_max_length\n"
    "    return field_max_length\n"
)
W3_FIELD_OFFBY1 = _swap(_BASE, _IMPL, _W3_FIELD_OFFBY1)


# --- W4 wrong widget KEY (writes the unrelated attr_other token) ---
# Writes the resolved value but under attr_other() (a pre-existing unrelated
# attribute) instead of attr_maxlength(). The dedicated length-limit attribute is
# still never established. Faithful real patch: a typo'd key, e.g.
# `widget.attrs['max_length'] = username_max_length` (underscore — not the HTML
# 'maxlength' attribute the browser honours) -> form.fields['username']
# .widget.attrs.get('maxlength') is still None -> both F2P tests FAIL. Rejected by
# C2 (attr_maxlength() in widget_attrs): the maxlength token is never added. (Also
# clobbers attr_other -> C6/C7, but C2 is the primary rejection.)
_W4_WRONG_KEY = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs[attr_other()] = username_max_length\n"
    "    return field_max_length\n"
)
W4_WRONG_KEY = _swap(_BASE, _IMPL, _W4_WRONG_KEY)


# --- W5 clobbers a pre-existing widget attribute (value preservation) ---
# Performs the correct maxlength write but ALSO overwrites attr_other() (a focus/
# autocomplete hint already configured on the widget). widget_attrs is FULL
# permission so this write is ALLOWED by the permission system; it is the
# VALUE-PRESERVATION postcondition that must reject it (the project's value-level
# analogue of frame-mutation, since there is no Acc(...,1/2) read-only input).
# Faithful real patch: a config block that resets `widget.attrs['autofocus']`
# (or 'autocapitalize'/'autocomplete') while adding maxlength -> the
# PASS_TO_PASS html-autocomplete-attribute tests (which assert those hints
# survive) regress. Rejected by the value frame C6 (and its constant witness
# C7: widget_attrs[attr_other()] == Old(widget_attrs[attr_other()])): the value
# was overwritten with the resolved limit + 1, which is not the value the
# attribute arrived with. (The overwriting value is a fresh number rather than a
# computation on the READ value, because nothing may be computed from a value
# read out of the opaque attribute-value domain -- see the carrier note in
# model.py. The clause under test is unchanged: a pre-existing attribute's value
# must survive.)
_W5_CLOBBER_OTHER = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs[attr_maxlength()] = username_max_length\n"
    "    widget_attrs[attr_other()] = username_max_length + 1\n"
    "    return field_max_length\n"
)
W5_CLOBBER_OTHER = _swap(_BASE, _IMPL, _W5_CLOBBER_OTHER)


# --- W7 spurious EXTRA widget attribute alongside the correct write ---
# Performs the correct maxlength write AND the correct return, but ALSO writes a
# spurious additional widget attribute (an arbitrary fresh attribute name). Historically
# this class BROKE the bundle (G-EQ atk_*_spurious_key): the old spec carried
# only a no-key-dropped Forall, so a rival adding an extra key still verified,
# and its faithful patch (e.g. widget.attrs['autocomplete'] = username_max_length
# clobbering the UsernameField autocomplete hint) fails PASS_TO_PASS
# test_html_autocomplete_attributes / test_inactive_user. Faithful real patch:
# `widget.attrs['spurious'] = username_max_length` added beside the gold write
# (or, worse, targeting a real attribute name like 'autocomplete'). Rejected by
# C5, the membership-frame Forall (a != maxlength => (a in widget_attrs) ==
# Old(a in widget_attrs)): the fresh name was not present before.
_W7_SPURIOUS_EXTRA = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs[attr_maxlength()] = username_max_length\n"
    "    widget_attrs['spurious'] = username_max_length\n"
    "    return field_max_length\n"
)
W7_SPURIOUS_EXTRA = _swap(_BASE, _IMPL, _W7_SPURIOUS_EXTRA)


# --- W8 partial-domain: leaves a STALE length limit standing ---
# Performs the widget write ONLY when the widget does not already advertise a
# length limit. On a widget that carries one already, the stale limit survives
# while the RETURNED server-side limit is the freshly resolved one, so the
# rendered cap and the validation cap disagree -- exactly the split the fix
# exists to prevent. This is the rival class the removed
# `attr_maxlength() not in widget_attrs` precondition used to make vacuous: the
# whole deviating branch lay outside the spec domain, so Nagini discharged it
# without looking. Faithful real patch: the widget write wrapped in
# `if 'maxlength' not in widget.attrs:`. A subclass that declares its own
# `username = CharField(max_length=75)` gets 'maxlength' pre-set to '75' by
# CharField.widget_attrs, so the form renders maxlength="75" while
# field.max_length is the user model's resolved limit. Rejected by C3
# (widget_attrs[attr_maxlength()] == resolve_limit(declared)) and C4
# (Result() == widget value), which now bind on that pre-state too.
_W8_STALE_MAXLENGTH = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    if attr_maxlength() not in widget_attrs:\n"
    "        widget_attrs[attr_maxlength()] = username_max_length\n"
    "    return field_max_length\n"
)
W8_STALE_MAXLENGTH = _swap(_BASE, _IMPL, _W8_STALE_MAXLENGTH)


# --- W9 boundary: skips the widget write on a bare widget ---
# Performs the gold write only when some other attribute is already configured
# on the widget; on a widget carrying none, the length-limit attribute is never
# established at all -- the regression, surviving on one pre-state. This is the
# rival class the removed `attr_other() in widget_attrs` precondition made
# vacuous. Faithful real patch: the widget write guarded by
# `if widget.attrs:`. A subclass declaring `username = CharField()` or
# `IntegerField()` has an EMPTY widget attrs dict, so maxlength is never
# rendered for it. Rejected by C2 (attr_maxlength() in widget_attrs), which now
# binds on the bare pre-state too.
_W9_BARE_SKIP = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    if attr_other() in widget_attrs:\n"
    "        widget_attrs[attr_maxlength()] = username_max_length\n"
    "    return field_max_length\n"
)
W9_BARE_SKIP = _swap(_BASE, _IMPL, _W9_BARE_SKIP)


# --- W10 partial-domain frame break: invents an attribute on a bare widget ---
# Performs the correct maxlength write everywhere, but on a widget that carried
# no other attribute it ALSO invents one. Correct on the states the old
# precondition admitted, wrong only in the region it excluded -- so this rival
# verified vacuously before and is caught now. Faithful real patch: the gold
# write plus `widget.attrs.setdefault('autofocus', username_max_length)`,
# forcing an autofocus hint onto subclass-declared username widgets that
# deliberately have none. Rejected by the membership frame C5 (a != maxlength
# => (a in widget_attrs) == Old(a in widget_attrs)) on the bare pre-state.
_W10_INVENT_ON_BARE = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs[attr_maxlength()] = username_max_length\n"
    "    if attr_other() not in widget_attrs:\n"
    "        widget_attrs[attr_other()] = username_max_length\n"
    "    return field_max_length\n"
)
W10_INVENT_ON_BARE = _swap(_BASE, _IMPL, _W10_INVENT_ON_BARE)


# --- W11 off-domain dict read (the atk_14 mechanism) ---
# Reads a key that the removed preconditions used to guarantee, inside a branch
# those preconditions used to prove infeasible. No Assert, no loop, no extra or
# dropped key -- just an indexing operation whose precondition Nagini formerly
# discharged from the excluded pre-state. Faithful real patch: on a widget that
# already advertises a length limit, `field.max_length = widget.attrs['autofocus']`
# -> KeyError for any subclass-declared username field, erroring out the four
# label/integer-username tests. Rejected because the dict-read precondition
# (attr_other() in widget_attrs) is no longer implied by the spec's domain, so
# the indexing itself no longer verifies.
_W11_OFFDOMAIN_READ = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    if attr_maxlength() in widget_attrs:\n"
    "        Assert(widget_attrs[attr_other()] == limit_value(0))\n"
    "    widget_attrs[attr_maxlength()] = username_max_length\n"
    "    return field_max_length\n"
)
W11_OFFDOMAIN_READ = _swap(_BASE, _IMPL, _W11_OFFDOMAIN_READ)


# --- W6 partial-domain: hardcode the default for BOTH field and widget ---
# Ignores the declared maximum entirely and uses the constant 254 for both the
# field and the widget. Correct on the declared=None branch
# (IntegerUsernameUser, F2P defaults-to-254); DIVERGES on the declared-int branch
# (CustomEmailField declared=255 -> should be 255). Faithful real patch: the
# resolution collapsed to the literal `254` (dropping the `or`), e.g. both writes
# use `254` -> F2P test_username_field_max_length_matches_user_model asserts
# max_length / maxlength == 255 -> FAILS. Rejected by C1 & C3 on the declared=255
# input (254 != resolve_limit(255) == 255).
_W6_HARDCODE_DEFAULT = (
    "    username_max_length = default_limit()\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs[attr_maxlength()] = username_max_length\n"
    "    return field_max_length\n"
)
W6_HARDCODE_DEFAULT = _swap(_BASE, _IMPL, _W6_HARDCODE_DEFAULT)


# --- W12 misdirected gold key: the limit published under the WRONG name ---
# Performs the resolution correctly and returns the correct field-level limit,
# and writes that correct number into the attribute mapping exactly once -- but
# under an attribute name that is not the dedicated one a browser honours. No
# exception, no extra key beside the intended one, no clobbering of a
# pre-existing hint, no divergence: as a shape it is a legitimate single-key
# update, which is why the frame clauses alone never caught it. Faithful real
# patch: `widget.attrs['maxlength_x'] = username_max_length` (or any other
# name), so `widget.attrs.get('maxlength')` is still None and the regression
# the bundle exists to sense is reinstated verbatim while every PASS_TO_PASS
# test still passes -- exactly the recorded G-EQ break (atk_2/atk_3), whose
# route was an index expression built out of the LENGTH domain
# (`default_limit() + 746 == 1000`) back when names were carried as ints.
# Rejected by C2/C3: the dedicated attribute name is never established. What
# makes the whole class unreachable now is the NAME CARRIER -- an attribute
# name is textual, disjoint from the length domain, so no arithmetic on numbers
# can produce one and the misdirected-key rival cannot even be written with a
# computed name (it is ill-typed). This case pins the carrier: if the name
# domain were ever put back to a numeric one, this rival would return.
_W12_MISDIRECTED_KEY = (
    "    username_max_length = resolve_limit(declared_max_length)\n"
    "    field_max_length = username_max_length\n"
    "    widget_attrs['maxlength_x'] = username_max_length\n"
    "    return field_max_length\n"
)
W12_MISDIRECTED_KEY = _swap(_BASE, _IMPL, _W12_MISDIRECTED_KEY)


SPEC_TESTS = [
    {
        "id": "pos-control",
        "kind": "soundness",
        "expect": "verify",
        "module": POS,
        "rationale": "Structurally-different but CORRECT impl: the widget write "
                     "is performed FIRST, the returned value read back out of the "
                     "widget map (Result() == widget_attrs[maxlength]); identical "
                     "observable content, only executable order/data-flow changed "
                     "(no loop/fold/lemma). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "Probe on an F2P-shaped in-domain input (a widget map "
                     "{attr_other(): 7} satisfying all three Requires clauses, "
                     "declared=255 = the CustomEmailField branch) verifies, "
                     "confirming the precondition admits a normal input. A failure "
                     "would be PRECOND-TOO-STRONG. Formerly a literal self-call; "
                     "that form is structurally unverifiable under "
                     "Requires(MustTerminate(2)) because a direct self-call cannot "
                     "strictly decrease the obligation level (caller and callee "
                     "share one precondition), which is precisely the unbounded "
                     "recursion the obligation exists to reject. Re-expressed "
                     "without recursion and STRENGTHENED: it now also pins both "
                     "branches of resolve_limit and the value-preservation of the "
                     "pre-existing attribute.",
    },
    {
        "id": "w1-drop-widget-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W1_DROP_WIDGET,
        "refinement": "Omits the widget write entirely (== model_prepatch.py == "
                      "the #27515 regression): only the field-level limit is set, "
                      "widget.attrs['maxlength'] is never established. Faithful "
                      "real patch is the literal pre-patch single line; "
                      "form.fields['username'].widget.attrs.get('maxlength') is "
                      "None -> both F2P tests (assert == 255 / 254) FAIL -> does "
                      "NOT resolve (this is the bug the patch fixes).",
        "rationale": "Rejected by C2 Ensures(attr_maxlength() in widget_attrs): "
                     "the maxlength attribute is never added to the widget map.",
    },
    {
        "id": "w2-widget-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W2_WIDGET_DEFAULT,
        "refinement": "Returns the correctly resolved field limit but writes the "
                      "DEFAULT 254 into the widget regardless of the declared "
                      "maximum (value-double-mask: field and widget no longer "
                      "carry the same value). Faithful real patch: "
                      "widget.attrs['maxlength'] = 254 (a literal) instead of the "
                      "hoisted username_max_length. F2P "
                      "test_username_field_max_length_matches_user_model asserts "
                      "widget.attrs.get('maxlength') == 255 -> FAILS on the "
                      "declared=255 branch.",
        "rationale": "Rejected by C3 Ensures(widget_attrs[attr_maxlength()] == "
                     "resolve_limit(declared)): on declared=255, 254 != 255; and "
                     "by C4 Ensures(Result() == widget value): field 255 != "
                     "widget 254.",
    },
    {
        "id": "w3-field-offby1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W3_FIELD_OFFBY1,
        "refinement": "Writes the correct resolved value into the widget but "
                      "returns resolved+1 as the field-level limit (field and "
                      "widget diverge). Faithful real patch: "
                      "self.fields['username'].max_length = username_max_length + "
                      "1 with the widget write correct -> the F2P assertion "
                      "form.fields['username'].max_length == 255 FAILS (the "
                      "server-side cap is one off from the rendered cap).",
        "rationale": "Rejected by C1 Ensures(Result() == resolve_limit(declared)) "
                     "and C4 Ensures(Result() == widget_attrs[attr_maxlength()]): "
                     "resolved+1 equals neither the resolved limit nor the widget "
                     "value.",
    },
    {
        "id": "w4-wrong-widget-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W4_WRONG_KEY,
        "refinement": "Writes the resolved value under attr_other() (a pre-"
                      "existing unrelated attribute) instead of attr_maxlength() "
                      "-- the dedicated length-limit token is never set. Faithful "
                      "real patch: a typo'd key (e.g. 'max_length' with an "
                      "underscore, not the HTML 'maxlength' attribute the browser "
                      "honours) -> widget.attrs.get('maxlength') is still None -> "
                      "both F2P tests FAIL.",
        "rationale": "Rejected by C2 Ensures(attr_maxlength() in widget_attrs): "
                     "the maxlength token is never added. (It also clobbers "
                     "attr_other -> C6/C7, but C2 is the primary rejection.)",
    },
    {
        "id": "w5-clobber-preexisting-attr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W5_CLOBBER_OTHER,
        "refinement": "Performs the correct maxlength write but ALSO overwrites "
                      "attr_other() (a focus/autocomplete hint already configured "
                      "on the widget). Faithful real patch: a config block that "
                      "resets widget.attrs['autofocus']/'autocapitalize'/"
                      "'autocomplete' while adding maxlength -> the PASS_TO_PASS "
                      "test_html_autocomplete_attributes / "
                      "test_username_field_autocapitalize_none assertions regress.",
        "rationale": "widget_attrs is FULL permission so the write is ALLOWED by "
                     "the permission system; it is the VALUE-PRESERVATION frame "
                     "C6 (and its constant witness C7 "
                     "Ensures(widget_attrs[attr_other()] == "
                     "Old(widget_attrs[attr_other()]))) that rejects it (value "
                     "changed by +1). This is the value-level analogue of frame-"
                     "mutation here, since there is NO Acc(...,1/2) read-only "
                     "input -- see 'assessment'.",
    },
    {
        "id": "w6-hardcode-default-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W6_HARDCODE_DEFAULT,
        "refinement": "Ignores the declared maximum and uses 254 for BOTH writes. "
                      "Correct on the declared=None branch (IntegerUsernameUser, "
                      "F2P defaults-to-254); DIVERGES on the declared-int branch. "
                      "Faithful real patch: resolution collapsed to the literal "
                      "254 (the `or 254` dropping its left operand) -> F2P "
                      "test_username_field_max_length_matches_user_model "
                      "(declared=255) asserts both == 255 -> FAILS.",
        "rationale": "Rejected by C1 Ensures(Result() == resolve_limit(declared)) "
                     "and C3 Ensures(widget value == resolve_limit(declared)): on "
                     "the declared=255 input, 254 != resolve_limit(255) == 255. "
                     "Partial-domain rival (passes the None branch, fails the int "
                     "branch).",
    },
    {
        "id": "w7-spurious-extra-attr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W7_SPURIOUS_EXTRA,
        "refinement": "Performs the correct maxlength write and the correct "
                      "return but ALSO writes a spurious additional widget "
                      "attribute under a fresh name (the historical G-EQ "
                      "atk_*_spurious_key class). Faithful real patch: "
                      "widget.attrs['autocomplete'] = username_max_length added "
                      "beside the gold write, clobbering the UsernameField "
                      "autocomplete hint -> PASS_TO_PASS "
                      "test_html_autocomplete_attributes / test_inactive_user "
                      "(auth_tests.test_forms.AuthenticationFormTest) FAIL -> "
                      "does NOT resolve.",
        "rationale": "Rejected by the membership frame C5 Ensures(Forall(a: a != "
                     "attr_maxlength() => (a in widget_attrs) == Old(a in "
                     "widget_attrs))): the fresh name was absent before and "
                     "present after, violating the membership equality. The old "
                     "spec shipped only the no-key-dropped direction, which this "
                     "rival satisfied (the G-EQ break this frame now closes).",
    },
    {
        "id": "w8-stale-maxlength-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W8_STALE_MAXLENGTH,
        "refinement": "Performs the widget write ONLY when the widget does not "
                      "already advertise a length limit; on a widget that does, "
                      "the STALE limit survives while the returned server-side "
                      "limit is the freshly resolved one, so the rendered cap "
                      "and the validation cap disagree. Faithful real patch: the "
                      "widget write wrapped in `if 'maxlength' not in "
                      "widget.attrs:`. A subclass declaring `username = "
                      "CharField(max_length=75)` has 'maxlength' pre-set to '75' "
                      "by CharField.widget_attrs, so the form renders "
                      "maxlength=75 while field.max_length carries the user "
                      "model's resolved limit -> the rendered cap is wrong.",
        "rationale": "Rejected by C3 Ensures(widget_attrs[attr_maxlength()] == "
                     "resolve_limit(declared)) and C4 Ensures(Result() == widget "
                     "value). This is the class the REMOVED precondition "
                     "`attr_maxlength() not in widget_attrs` used to make "
                     "VACUOUS -- the deviating branch lay outside the spec "
                     "domain, so the verifier discharged it without looking.",
    },
    {
        "id": "w9-bare-widget-skip-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W9_BARE_SKIP,
        "refinement": "Performs the gold write only when some other attribute is "
                      "already configured on the widget; on a widget carrying "
                      "none, the length-limit attribute is never established -- "
                      "the regression surviving on one pre-state. Faithful real "
                      "patch: the widget write guarded by `if widget.attrs:`. A "
                      "subclass declaring `username = CharField()` or "
                      "`IntegerField()` has an EMPTY widget attrs dict, so "
                      "maxlength is never rendered for it.",
        "rationale": "Rejected by C2 Ensures(attr_maxlength() in widget_attrs), "
                     "which now binds on the bare pre-state too. This is the "
                     "class the REMOVED precondition `attr_other() in "
                     "widget_attrs` used to make VACUOUS.",
    },
    {
        "id": "w10-invent-attr-on-bare-widget",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W10_INVENT_ON_BARE,
        "refinement": "Performs the correct maxlength write everywhere, but on a "
                      "widget that carried no other attribute it ALSO invents "
                      "one -- correct on the states the old precondition "
                      "admitted, wrong only in the region it excluded. Faithful "
                      "real patch: the gold write plus "
                      "`widget.attrs.setdefault('autofocus', "
                      "username_max_length)`, forcing an autofocus hint onto "
                      "subclass-declared username widgets that deliberately "
                      "have none.",
        "rationale": "Rejected by the membership frame C5 Ensures(Forall(a: a != "
                     "attr_maxlength() => (a in widget_attrs) == Old(a in "
                     "widget_attrs))) evaluated on the bare pre-state. Under the "
                     "old domain restriction this rival verified vacuously; the "
                     "frame only became load-bearing there once the domain went "
                     "total.",
    },
    {
        "id": "w12-misdirected-gold-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W12_MISDIRECTED_KEY,
        "refinement": "The correct resolved limit, returned correctly and "
                      "written exactly once into the attribute mapping, but "
                      "under a name that is not the dedicated one. Faithful "
                      "real patch: `widget.attrs['maxlength_x'] = "
                      "username_max_length` -> `widget.attrs.get('maxlength')` "
                      "is still None, so both FAIL_TO_PASS tests fail while "
                      "PASS_TO_PASS stays perfect (nothing raises and no "
                      "pre-existing hint is disturbed).",
        "rationale": "Rejected by C2/C3: the dedicated attribute name is never "
                     "established. This is the recorded G-EQ break's class, and "
                     "the frame clauses could not see it because it IS a "
                     "single-key update -- it differs from gold only in WHICH "
                     "real attribute the key denotes. It is the textual name "
                     "domain that closes the class outright: a name is disjoint "
                     "from the length domain, so a key computed out of a length "
                     "is ill-typed rather than merely rejected. The case is kept "
                     "to pin that carrier against a regression to a numeric one.",
    },
    {
        "id": "w11-offdomain-dict-read",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W11_OFFDOMAIN_READ,
        "refinement": "Reads a key the removed preconditions used to guarantee, "
                      "inside a branch those preconditions used to prove "
                      "infeasible -- no Assert, no loop, no extra or dropped "
                      "key, just an indexing operation. Faithful real patch: on "
                      "a widget that already advertises a length limit, "
                      "`field.max_length = widget.attrs['autofocus']` -> "
                      "KeyError for any subclass-declared username field, "
                      "erroring out the label / integer-username tests.",
        "rationale": "Rejected because the dict-read precondition (attr_other() "
                     "in widget_attrs) is no longer implied by the spec's "
                     "domain, so the indexing itself does not verify. This is "
                     "the cleanest witness of the vacuity the domain "
                     "restriction created: under the old spec the branch was "
                     "provably unreachable, so ANY behaviour inside it verified "
                     "while being real under a faithful refinement.",
    },
]


# No @ContractOnly axioms in this bundle (meta.json axioms == []). The lone deep-
# model reference (A-reference: configure_username_field's resolve_limit + the two
# writes == the real AuthenticationForm.__init__ username-field configuration) is
# validated by axiom_check.py (G-AX) executing the REAL gold-patched form against
# 7 boundary + 200 fuzz user models. The deep model is fully spelled out in the
# impl region (no opaque @ContractOnly callee whose Ensures the proof consumes),
# so there is no axiom-soundness obligation to fuzz and no axiom-Requires domain to
# check for caller-containment in the SPEC sense. The axiom lane is therefore empty;
# the A-reference soundness is the existing, already-green G-AX (axiom_check.py).
AXIOM_TESTS = []  # type: list
