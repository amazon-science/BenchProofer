#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14631 (nagini).

SHADOW — the impl region of `model.py`'s `clean_bound_initial_field`, copied
VERBATIM below with only the contract calls stripped (`Requires`/`Ensures`;
there are no `Invariant`/`Assert`/`Fold`/`Acc`/`MustTerminate` calls inside the
region itself, and no `# invariants-*` markers). Its `@Pure` dependencies
`bound_initial` and `normalise`, and the `FieldState` carrier, are copied over
the same way. No Nagini carrier shims are needed: the model works over plain
`int`s (no `PSeq`/`ToSeq` appears in the region). There is no `@ContractOnly`
callee to substitute a real function for — mapping.md §3 states the bundle
consumes no axioms; every operation the cleaned-value computation performs is
modelled deeply, and it is exactly that deep model this gate puts at risk.

ORACLE — the REAL patched repo function, CALLED, not transliterated:
`BaseForm._clean_fields` (`django/forms/forms.py:389` at base_commit; mapping.md
§1), reached the only way it is reachable, by driving a real bound Django form
end to end (`form.errors` -> `full_clean()` -> `_clean_fields()` ->
`bf.initial` / `field.clean`) and reading `form.cleaned_data[name]`. The gate
applies patch.diff to /testbed before this script runs and PYTHONPATH=/testbed
makes the patched module importable, so the patched line
`value = bf.initial if field.disabled else bf.data` and the real
`BoundField.initial` (`boundfield.py:212`, a `@cached_property` that strips
microseconds when `widget.supports_microseconds` is false) both execute
unmodified. Nothing about the form machinery is stubbed, replicated or
monkeypatched: the only instrumentation is a RECORDING wrapper around the
field's own initial *source* (the callable the repo would call anyway), which
is an input to the modeled function, not part of it.

That recording gives the check two independent ways to fail, both of which the
PRE-patch code would trip:
  (1) value: cleaned != normalise(first evaluation) — pre-patch used a fresh,
      un-normalised `get_initial_for_field` call, so a microsecond-bearing or
      stateful source disagrees;
  (2) effect: the source must be evaluated EXACTLY ONCE per form (the
      `@cached_property` the model encodes as "the single first evaluation",
      and the reason `clean_bound_initial_field` is granted no permission to
      `fs.fresh_eval` at all). A second evaluation is reported as a
      disagreement, not tolerated.

TYPE BRIDGE (mapping.md §2, inverted) — the model's carrier for a date/time
value is `int` = `whole_seconds * 1_000_000 + sub_second_units`; the repo wants
a real `datetime.datetime` / `datetime.time`. `encode_datetime` measures
microseconds from the fixed epoch `datetime.datetime.min` (axiom_check.py pins
the same bijection with epoch 2006-10-25; `datetime.min` is the same map with a
lower epoch, chosen so that EVERY representable datetime encodes `>= 0` and so
every generated input satisfies the model's `Requires(first_eval >= 0)`),
`encode_time` measures from midnight. Under both, the model's `normalise`
(floor to a multiple of 1_000_000) is exactly the repo's
`data.replace(microsecond=0)`, because the epoch has `microsecond == 0`.
Generation runs in the repo direction (build a real datetime/time, drive the
real form, encode both sides) so the input domain is by construction inside the
model's Requires.

MODELED BRANCH (mapping.md §2) — `field.disabled is True` and the field's
widget does NOT carry sub-second precision. Every generated form therefore uses
`disabled=True` and the field's default widget (`DateTimeInput`/`TimeInput`,
both `supports_microseconds = False`, `widgets.py:482`). A micro-supporting
widget is a different branch of `BoundField.initial` that this model does not
claim to cover, so feeding it here would test the model outside its stated
domain; it is deliberately excluded and said so, not silently avoided.

INPUTS — 100 000 Requires-satisfying inputs: 30 boundary cases first (the exact
F2P shape from the test patch, including its expected
`datetime(2006, 10, 25, 14, 30, 46)` and `cleaned == bf.initial` assertions;
sub-second 0 / 1 / 999999 / 500000; a stateless callable source; a plain
non-callable source; a `TimeField`; the `datetime.min` and `datetime.max`
extremes of the encoding; a source whose state advances by a large step), then
seeded fuzz over the full datetime range x sub-second range x {DateTimeField,
TimeField} x {form-`initial` dict source, field-`initial` source} x
{stateful, stateless, non-callable} to fill the count. The impl region is
straight-line (no branches), so branch coverage is over `normalise`'s two
regimes: sub-second == 0 (identity) and sub-second > 0 (a strict floor); both
regimes are covered in the boundary set and their counts are reported.
The modeled input space is infinite, so this is sampling, not enumeration.

Pinned seed: 14631 (recorded in mapping.md, `## G-CONF`).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + the repo under test only.
"""
import datetime
import json
import random
import sys

SEED = 14631
N_TARGET = 100_000


# --------------------------------------------------------------------------
# SHADOW: model.py verbatim, contract calls stripped.
# --------------------------------------------------------------------------

class FieldState:
    def __init__(self, first_eval, fresh_eval):
        self.first_eval = first_eval
        self.fresh_eval = fresh_eval


# pure-start
def normalise(value):
    """Drop the sub-second component of an encoded date/time value. The
    encoding is `whole_seconds * 1_000_000 + sub_second_units` with
    `0 <= sub_second_units < 1_000_000`; normalisation floors to the whole
    second. Idempotent and a function of its argument alone."""
    return (value // 1000000) * 1000000


def bound_initial(fs):
    """The value exposed as the field's bound initial: the NORMALISED form of
    the SINGLE (first) evaluation of the initial source. This is the cached
    value reused everywhere the bound initial is read."""
    return normalise(fs.first_eval)
# pure-end


def clean_bound_initial_field(fs):
    # impl-start
    # Read the value through the field's bound initial (single cached,
    # normalised evaluation), then clean it. Cleaning a date/time value is the
    # identity on the value it is given.
    value = bound_initial(fs)
    cleaned = value
    return cleaned
    # impl-end


# --------------------------------------------------------------------------
# Type bridge (mapping.md §2, inverted).
# --------------------------------------------------------------------------

EPOCH = datetime.datetime.min          # 0001-01-01 00:00:00, microsecond == 0


def encode_datetime(dt):
    """datetime -> model int `whole_seconds * 1_000_000 + sub_second_units`."""
    delta = dt - EPOCH
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def decode_datetime(value):
    return EPOCH + datetime.timedelta(microseconds=value)


def encode_time(t):
    """time -> model int, measured from midnight (microsecond == 0 origin)."""
    return (t.hour * 3600 + t.minute * 60 + t.second) * 1000000 + t.microsecond


def decode_time(value):
    whole, us = divmod(value, 1000000)
    h, rem = divmod(whole, 3600)
    m, s = divmod(rem, 60)
    return datetime.time(h % 24, m, s, us)


def encode(value):
    if isinstance(value, datetime.datetime):
        return encode_datetime(value)
    if isinstance(value, datetime.time):
        return encode_time(value)
    raise TypeError("value outside the model carrier: %r" % (value,))


def decode(value, kind):
    return decode_datetime(value) if kind == 'datetime' else decode_time(value)


# --------------------------------------------------------------------------
# Real Django, real patched form machinery.
# --------------------------------------------------------------------------

def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            USE_TZ=False,              # from_current_timezone is the identity
            USE_I18N=False,
            DATABASES={},
            INSTALLED_APPS=[],
        )
    django.setup()


class RecordingSource:
    """The field's initial SOURCE — an input to the modeled function, not part
    of it. Stateful like the F2P helper's `FakeTime().now`: every evaluation
    advances its own state by `increment` seconds (increment == 0 gives a
    stateless source). Each evaluation is recorded, so the check can see the
    value of the FIRST evaluation (the model's `fs.first_eval`), the value a
    further independent evaluation yields (`fs.fresh_eval`), and HOW MANY
    evaluations the real patched code performed."""

    def __init__(self, base, increment, kind):
        self.base = base
        self.increment = increment
        self.kind = kind
        self.n = 0
        self.calls = []

    def __call__(self):
        self.n += 1
        value = self.base + datetime.timedelta(seconds=self.increment * self.n)
        if self.kind == 'time':
            value = value.time()
        self.calls.append(value)
        return value


def _forms():
    from django import forms

    class DateTimeForm(forms.Form):
        f = forms.DateTimeField(disabled=True)

    class TimeForm(forms.Form):
        f = forms.TimeField(disabled=True)

    return DateTimeForm, TimeForm


def drive_real(kind, source_mode, source, form_classes):
    """Drive the REAL patched `BaseForm._clean_fields` for one disabled field
    whose initial source is `source`, and report

        (cleaned value, first evaluation, n evaluations, bound initial)

    Nothing is stubbed: `form.errors` runs the real `full_clean()`, which runs
    the real `_clean_fields()`, whose patched body is
    `value = bf.initial if field.disabled else bf.data` followed by
    `field.clean(value)`.
    """
    DateTimeForm, TimeForm = form_classes
    cls = DateTimeForm if kind == 'datetime' else TimeForm
    if source_mode == 'form_initial':
        # source reached via BaseForm.initial (forms.py:490 self.initial.get)
        form = cls({}, initial={'f': source})
    else:
        # source reached via Field.initial (forms.py:490 field.initial); the
        # per-instance fields dict is a deepcopy, so this is a real field.
        form = cls({})
        form.fields['f'].initial = source
    if form.errors:
        raise AssertionError("real form errored: %r" % (form.errors,))
    cleaned = form.cleaned_data['f']
    # Read the bound initial BEFORE counting: the evaluation count must span the
    # whole "clean the field, then read its bound initial" window, because that
    # is the window over which the model claims a SINGLE evaluation (the
    # @cached_property, mapping.md §2 "the cache ↔ the single first
    # evaluation") and over which the F2P test asserts cleaned == bf.initial.
    # Counting before this read would miss the pre-patch double evaluation,
    # where cleaning evaluates the source once via get_initial_for_field and
    # bf.initial then evaluates it a SECOND time.
    real_bound_initial = form['f'].initial
    n_calls = source.n if isinstance(source, RecordingSource) else 0
    first = source.calls[0] if isinstance(source, RecordingSource) else source
    return cleaned, first, n_calls, real_bound_initial


def fresh_evaluation(source):
    """What a SECOND, independent evaluation of the same source yields — the
    model's `fs.fresh_eval` (mapping.md §2). Taken AFTER the real form has been
    cleaned, so it cannot perturb the run under test."""
    if isinstance(source, RecordingSource):
        return source()
    return source


# --------------------------------------------------------------------------
# Differential driver.
# --------------------------------------------------------------------------

class Stats:
    def __init__(self):
        self.checked = 0
        self.sub_zero = 0
        self.sub_positive = 0
        self.stateful_witness = 0


def check_one(case, form_classes, stats):
    """Return None on agreement, or a printable disagreement report."""
    kind, source_mode, source = case

    try:
        cleaned, first, n_calls, real_bound_initial = drive_real(
            kind, source_mode, source, form_classes)
    except AssertionError as exc:
        return ("DISAGREEMENT (real function refused the input):\n"
                "  input: kind=%s source_mode=%s source=%r\n"
                "  %s" % (kind, source_mode, _describe(source), exc))

    fresh = fresh_evaluation(source)

    first_code = encode(first)
    fresh_code = encode(fresh)
    if first_code < 0 or fresh_code < 0:          # model Requires
        raise AssertionError("generated input outside Requires: %r" % (case,))

    fs = FieldState(first_code, fresh_code)
    shadow = clean_bound_initial_field(fs)
    real = encode(cleaned)

    stats.checked += 1
    if first_code % 1000000 == 0:
        stats.sub_zero += 1
    else:
        stats.sub_positive += 1
    if fresh_code != normalise(first_code):
        stats.stateful_witness += 1

    if shadow != real:
        return ("DISAGREEMENT (cleaned value):\n"
                "  input: kind=%s source_mode=%s source=%r\n"
                "         first evaluation = %r (encoded %d)\n"
                "         fresh evaluation = %r (encoded %d)\n"
                "  shadow (model impl region) = %d (%r)\n"
                "  oracle (patched _clean_fields) = %d (%r)\n"
                "  real bound initial = %r"
                % (kind, source_mode, _describe(source), first, first_code,
                   fresh, fresh_code, shadow, decode(shadow, kind),
                   real, cleaned, real_bound_initial))

    if encode(real_bound_initial) != real:
        # model: Ensures(Result() == bound_initial(fs)), and mapping.md §1 binds
        # `bound_initial` to the real `BoundField.initial`. So the real cleaned
        # value must equal the real bound initial (the F2P test's own
        # `cleaned == bf.initial` assertion, over the whole input domain).
        return ("DISAGREEMENT (cleaned value != real bound initial):\n"
                "  input: kind=%s source_mode=%s source=%r\n"
                "  model: Result() == bound_initial(fs) (mapping.md §1 binds\n"
                "         bound_initial to BoundField.initial)\n"
                "  oracle cleaned value = %r\n"
                "  oracle BoundField.initial = %r"
                % (kind, source_mode, _describe(source), cleaned,
                   real_bound_initial))

    if n_calls > 1:
        # The model encodes the initial source as evaluated EXACTLY ONCE (the
        # @cached_property) and denies the cleaning step any permission to a
        # second evaluation. More than one real evaluation refutes that.
        return ("DISAGREEMENT (extra evaluation of the initial source):\n"
                "  input: kind=%s source_mode=%s source=%r\n"
                "  model: the source is evaluated exactly once (bound_initial\n"
                "         reads the single cached first evaluation; the impl\n"
                "         has no permission to fs.fresh_eval)\n"
                "  oracle: the real patched code evaluated it %d times: %r"
                % (kind, source_mode, _describe(source), n_calls,
                   source.calls[:n_calls]))

    return None


def _describe(source):
    if isinstance(source, RecordingSource):
        return ("RecordingSource(base=%r, increment=%d, kind=%s)"
                % (source.base, source.increment, source.kind))
    return "plain %r" % (source,)


# --------------------------------------------------------------------------
# Inputs: boundary cases, then seeded fuzz.
# --------------------------------------------------------------------------

F2P_BASE = datetime.datetime(2006, 10, 25, 14, 30, 45)
MAX_DAYS = (datetime.datetime.max - datetime.datetime.min).days


def boundary_cases():
    """Boundary cases: the exact F2P shape, both sub-second regimes of
    `normalise`, both source kinds, both source paths, both field types, and
    the extremes of the encoding."""
    cases = []
    for micro in (123456, 0, 1, 999999, 500000):
        # the exact F2P shape: stateful source advancing 1s per evaluation
        cases.append(('datetime', 'field_initial',
                      RecordingSource(F2P_BASE.replace(microsecond=micro), 1,
                                      'datetime')))
        cases.append(('datetime', 'form_initial',
                      RecordingSource(F2P_BASE.replace(microsecond=micro), 1,
                                      'datetime')))
        # stateless callable source (fresh == first)
        cases.append(('datetime', 'field_initial',
                      RecordingSource(F2P_BASE.replace(microsecond=micro), 0,
                                      'datetime')))
        # non-callable source
        cases.append(('datetime', 'form_initial',
                      F2P_BASE.replace(microsecond=micro)))
        # TimeField
        cases.append(('time', 'field_initial',
                      RecordingSource(F2P_BASE.replace(microsecond=micro), 1,
                                      'time')))
        cases.append(('time', 'form_initial',
                      F2P_BASE.replace(microsecond=micro).time()))
    # extremes of the encoding
    cases.append(('datetime', 'form_initial', datetime.datetime.min))
    cases.append(('datetime', 'form_initial', datetime.datetime.max))
    cases.append(('time', 'form_initial', datetime.time.min))
    cases.append(('time', 'form_initial', datetime.time.max))
    # a source whose state advances by a large step per evaluation
    cases.append(('datetime', 'field_initial',
                  RecordingSource(F2P_BASE.replace(microsecond=654321),
                                  86399, 'datetime')))
    cases.append(('time', 'field_initial',
                  RecordingSource(F2P_BASE.replace(microsecond=654321),
                                  3600, 'time')))
    return cases


def fuzz_case(rng):
    kind = 'datetime' if rng.random() < 0.5 else 'time'
    source_mode = 'field_initial' if rng.random() < 0.5 else 'form_initial'
    # a datetime anywhere in the representable range, leaving room for two
    # evaluations of a stateful source to stay in range
    base = (datetime.datetime.min
            + datetime.timedelta(days=rng.randint(0, MAX_DAYS - 1),
                                 seconds=rng.randint(0, 86399 - 2),
                                 microseconds=rng.randint(0, 999999)))
    roll = rng.random()
    if roll < 0.55:                       # stateful source (the F2P shape)
        source = RecordingSource(base, rng.randint(1, 43200), kind)
    elif roll < 0.8:                      # stateless callable source
        source = RecordingSource(base, 0, kind)
    else:                                 # plain, non-callable source
        source = base.time() if kind == 'time' else base
    return (kind, source_mode, source)


def f2p_exact_shape():
    """The literal F2P scenario from the test patch, with its own assertions:
    a disabled DateTimeField whose initial is `FakeTime().now`, microseconds
    123456 -> cleaned == datetime(2006, 10, 25, 14, 30, 46) == bf.initial."""
    from django import forms
    from django.forms.fields import DateTimeField

    out = []
    for micro, expected in ((123456, datetime.datetime(2006, 10, 25, 14, 30, 46)),
                            (0, datetime.datetime(2006, 10, 25, 14, 30, 46))):
        class FakeTime:
            def __init__(self):
                self.elapsed_seconds = 0

            def now(self, micro=micro):
                self.elapsed_seconds += 1
                return datetime.datetime(
                    2006, 10, 25, 14, 30, 45 + self.elapsed_seconds, micro)

        class DateTimeForm(forms.Form):
            dt = DateTimeField(initial=FakeTime().now, disabled=True)

        form = DateTimeForm({})
        if form.errors:
            out.append("F2P shape errored: %r" % (form.errors,))
            continue
        cleaned = form.cleaned_data['dt']
        bf_initial = form['dt'].initial
        if cleaned != expected:
            out.append("F2P shape (microseconds=%d): cleaned %r != %r"
                       % (micro, cleaned, expected))
        if cleaned != bf_initial:
            out.append("F2P shape (microseconds=%d): cleaned %r != bf.initial %r"
                       % (micro, cleaned, bf_initial))
        # and the shadow reproduces it from the first evaluation
        first = datetime.datetime(2006, 10, 25, 14, 30, 46, micro)
        shadow = clean_bound_initial_field(
            FieldState(encode_datetime(first),
                       encode_datetime(first + datetime.timedelta(seconds=1))))
        if shadow != encode_datetime(cleaned):
            out.append("F2P shape (microseconds=%d): shadow %r != oracle %r"
                       % (micro, decode_datetime(shadow), cleaned))
    return out


def main():
    setup_django()
    form_classes = _forms()

    problems = f2p_exact_shape()
    if problems:
        for p in problems:
            print("DISAGREEMENT (F2P shape): %s" % (p,))
        print(json.dumps({"checked": 0, "disagreements": len(problems),
                          "seed": SEED, "status": "fail"}))
        return 1

    stats = Stats()
    for case in boundary_cases():
        report = check_one(case, form_classes, stats)
        if report:
            print(report)
            print(json.dumps({"checked": stats.checked, "disagreements": 1,
                              "seed": SEED, "status": "fail"}))
            return 1
    n_boundary = stats.checked

    rng = random.Random(SEED)
    while stats.checked < N_TARGET:
        report = check_one(fuzz_case(rng), form_classes, stats)
        if report:
            print(report)
            print(json.dumps({"checked": stats.checked, "disagreements": 1,
                              "seed": SEED, "status": "fail"}))
            return 1

    print("G-CONF OK: the contract-stripped impl region of "
          "clean_bound_initial_field agrees with the REAL patched "
          "BaseForm._clean_fields (driven through a real bound Django form) on "
          "%d Requires-satisfying inputs (%d boundary + fuzz, seed %d): "
          "sub-second==0 %d, sub-second>0 %d, stateful-source witnesses %d "
          "(inputs where a fresh re-evaluation differs from the cached "
          "normalised one, i.e. the pre-patch path would disagree); the source "
          "was evaluated exactly once in every case; 0 disagreements."
          % (stats.checked, n_boundary, SEED, stats.sub_zero,
             stats.sub_positive, stats.stateful_witness))
    print(json.dumps({
        "checked": stats.checked,
        "disagreements": 0,
        "seed": SEED,
        "boundary": n_boundary,
        "sub_second_zero": stats.sub_zero,
        "sub_second_positive": stats.sub_positive,
        "stateful_witnesses": stats.stateful_witness,
        "oracle": "BaseForm._clean_fields (called, patched /testbed)",
        "shadow": "direct (contract-stripped impl region)",
        "status": "pass",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
