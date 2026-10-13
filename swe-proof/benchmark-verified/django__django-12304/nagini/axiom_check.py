#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12304.

Validates the A-consumed axioms in model.py against the REAL Django / stdlib
callees, in-container:

  (A-consumed) `base_class_creation` ↔ the unchanged base class-construction
      step: `super().__new__(...)` (`enum.EnumMeta.__new__`) together with the
      derived per-choice tables the same step records
      (`cls._value2label_map_`, the `label` property).  The axiom pins the
      identity of the produced class object and issues the provenance token; it
      deliberately leaves the initial `preserve_when_callable` value
      UNCONSTRAINED, because the real initial value varies: a class with no
      flagged ancestor carries no `do_not_call_in_templates` attribute
      (`getattr(..., False)` is `False`), while a class constructed under an
      already-flagged base INHERITS the attribute (truthy right after
      `super().__new__` — e.g. the patched `IntegerChoices`/`TextChoices`/user
      subclasses inherit it from `Choices`).  The check below demonstrates BOTH
      initial states are realizable through the real callee, so any axiom
      Ensures pinning the initial flag (either way) would be unsound.  Its
      Exsures leg is grounded too: the step refuses a declaration whose declared
      kind cannot carry the declared choice values, and one that names a choice
      after a table this step must itself bind, and it delivers otherwise.

  (A-consumed) `finalize_grouping` ↔ the unchanged value-distinctness step
      `enum.unique(cls)`, which the construction hands the finished grouping to
      and whose result it delivers.  Grounded on all four clauses: it hands back
      THE SAME object, it leaves the modelled flag exactly as it found it, it
      refuses EXACTLY the declarations that repeat a choice value
      (`ValueError: duplicate values found in ...`), and it is total otherwise.

  (A-consumed) `flag_name_taken_by_choice` / `repeats_choice_value` /
      `base_step_refuses` ↔ the tables the three real refusal mechanisms
      consult.  The flag's recording is a GUARDED binding: the unchanged
      `enum.EnumMeta.__setattr__` refuses to rebind a name that is one of the
      class's own declared members (`AttributeError: Cannot reassign
      members.`) and succeeds otherwise.  The three predicates are shown
      INDEPENDENT (every combination realizable) and the construction's ORDER
      is shown observable: recording the flag before the distinctness step makes
      a declaration that both takes the flag's name and repeats a value report
      the taken-name refusal, while the opposite order reports the duplicate.

  (A-consumed) `resolved_in_template` ↔ the unchanged template
      variable-resolution rule `Variable._resolve_lookup`'s callable-handling
      step (`django/template/base.py:851-866`), SPECIALISED to a callable whose
      no-argument invocation cannot succeed (a class object that requires a
      constructor argument — exactly what an enumeration grouping is):
        • flagged `do_not_call_in_templates`  -> the object is preserved
          (resolution yields the object itself)              == identity
        • not flagged                          -> the no-arg call fails, the
          result is `string_if_invalid` (invalid-value sentinel) == INVALID

The model is also exercised end-to-end against the REAL Django `Choices` /
`IntegerChoices` produced by the patched metaclass, on the exact F2P template
`{{ Suit.DIAMOND.label }}|{{ Suit.DIAMOND.value }}`.  (The gold impl sets the
flag unconditionally, so the axiom's unconstrained initial flag is irrelevant
to the end-to-end behaviour; what matters is the flag is True AFTER the
metaclass runs, which the F2P rendering confirms.)

This gate runs at base_commit (axioms model UNCHANGED callees), so every check
below is written to be tree-independent: the refusal mechanisms are exercised by
composing the real unchanged callees directly (`enum.EnumMeta.__new__`,
`enum.EnumMeta.__setattr__`, `enum.unique`) rather than by relying on the one
line the modelled edit adds, and the end-to-end check branches on whether the
ambient metaclass carries the flag.

Imports the standard library plus Django; configures a minimal settings module
with the template engine enabled (no database access is performed).  Exit 0 iff
every observation matches the axioms' Ensures.
"""
import random
import sys

# The name the preserve-when-callable flag is recorded under on the grouping —
# and therefore the name a declared choice can collide with.
FLAG_NAME = 'do_not_call_in_templates'


INVALID_VALUE = 0  # model.py's invalid-value sentinel (string_if_invalid stand-in)

# A deliberately NON-EMPTY string_if_invalid.  The real resolution rule
# substitutes context.template.engine.string_if_invalid on the failed-invoke
# branch; the model abstracts that to INVALID_VALUE.  Using a non-empty,
# distinctive sentinel (rather than the default '') exercises the abstraction
# boundary properly: the invalid result must equal string_if_invalid for ANY
# configured value and must never be the object itself.
STRING_IF_INVALID = 'SBN_INVALID_SENTINEL'


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': False,
                'OPTIONS': {'string_if_invalid': STRING_IF_INVALID},
            }],
            USE_I18N=False,
        )
        django.setup()


def _resolve_bound(obj):
    """Resolve the variable `x` bound to `obj` through the REAL resolution rule
    via a TEMPLATE-BOUND context.

    `Variable.resolve` must run inside a context whose `template` is bound: on
    the failed-invoke branch the rule dereferences
    `context.template.engine.string_if_invalid`, so a bare `Context(...)`
    (whose `.template` defaults to `None`) would raise `AttributeError`.  We
    bind a real `Template('{{ x }}')` exactly as ordinary rendering does, so the
    invalid-value path resolves to the configured `string_if_invalid`.
    """
    from django.template import Context, Template
    from django.template.base import Variable
    t = Template('{{ x }}')
    ctx = Context({'x': obj})
    with ctx.bind_template(t):
        return Variable('x').resolve(ctx)


# --- (A-consumed) resolved_in_template against the REAL resolution rule -------
# A class object that requires a constructor argument (so `current()` raises a
# required-argument TypeError) is exactly the grouping scenario the axiom
# specialises to.  We drive the REAL Template/Context resolution and read what
# the variable resolves to (the object itself vs. the invalid sentinel).

def _make_require_arg_callable(do_not_call, extra=None):
    """Build a callable class whose no-arg construction fails (a `value`
    argument is required), optionally carrying do_not_call_in_templates and any
    unrelated `extra` attributes (which must not perturb the rule)."""
    ns = {'__init__': (lambda self, value: None)}
    if do_not_call is not None:
        ns['do_not_call_in_templates'] = do_not_call
    if extra:
        ns.update(extra)
    return type('RequireArg', (object,), ns)


def check_resolution_rule(flag):
    # premise of the axiom's specialisation: a no-argument construction must
    # fail with a *required-argument* TypeError.
    cls = _make_require_arg_callable(flag)
    et = None
    try:
        cls()
    except Exception as e:  # noqa: BLE001 - we assert on the exact type below
        et = type(e)
    assert et is TypeError, (
        "scenario invalid: %r() raised %r, expected a required-argument "
        "TypeError" % (cls, et))

    # the model's flag is a boolean; the real rule branches on the *truthiness*
    # of getattr(current, 'do_not_call_in_templates', False).
    truthy = bool(getattr(cls, 'do_not_call_in_templates', False))
    resolved = _resolve_bound(cls)

    if truthy:
        # preserve-when-callable -> resolution yields the object ITSELF
        # (Result() == identity in the model).
        assert resolved is cls, (
            "resolved_in_template unsound (preserve): do_not_call_in_templates"
            "=%r resolved to %r, expected the class object itself"
            % (flag, resolved))
    else:
        # not flagged -> the no-arg call fails -> string_if_invalid (the invalid
        # sentinel, INVALID_VALUE in the model), i.e. NOT the object itself and
        # equal to the configured string_if_invalid for ANY configured value.
        assert resolved is not cls, (
            "resolved_in_template unsound (invoke): do_not_call_in_templates"
            "=%r resolved to the object itself, expected the invalid sentinel"
            % (flag,))
        assert resolved == STRING_IF_INVALID, (
            "resolved_in_template unsound: expected string_if_invalid %r, "
            "got %r" % (STRING_IF_INVALID, resolved))


# --- (A-consumed) base_class_creation against the REAL super().__new__ --------
# The axiom leaves the initial preserve-when-callable flag UNCONSTRAINED.  This
# check demonstrates that both initial states are realizable through the real
# callee (enum.EnumMeta.__new__), so leaving it unconstrained is the ONLY sound
# contract:
#   (a) a class with no flagged ancestor carries no do_not_call_in_templates
#       attribute right after super().__new__  -> getattr default False;
#   (b) a class constructed under an already-flagged base INHERITS the
#       attribute -> truthy right after super().__new__ (this is exactly what
#       happens for IntegerChoices/TextChoices/user subclasses once the patched
#       ChoicesMeta has flagged the Choices base).

def check_base_construction():
    import enum

    class Plain(enum.Enum):
        A = 1
        B = 2

    # (a) no flagged ancestor: the base construction yields no flag (falsy)
    assert getattr(Plain, 'do_not_call_in_templates', False) is False, (
        "base_class_creation: a plainly-constructed enum class (no flagged "
        "ancestor) unexpectedly carries do_not_call_in_templates")

    # (b) flagged ancestor: right after super().__new__ the subclass already
    # INHERITS the flag — so an axiom pinning the initial value to False would
    # be UNSOUND against the real callee.
    observed = {}

    class ObservingMeta(enum.EnumMeta):
        def __new__(metacls, classname, bases, classdict, **kwds):
            cls = super().__new__(metacls, classname, bases, classdict, **kwds)
            observed[classname] = getattr(
                cls, 'do_not_call_in_templates', 'ABSENT')
            cls.do_not_call_in_templates = True
            return cls

    class Root(enum.Enum, metaclass=ObservingMeta):
        pass

    class Sub(int, Root):
        A = 1

    assert observed.get('Root') == 'ABSENT', (
        "expected the flag ABSENT right after super().__new__ for the root "
        "class (no flagged ancestor), got %r" % (observed.get('Root'),))
    assert observed.get('Sub') is True, (
        "expected the flag INHERITED (True) right after super().__new__ for a "
        "subclass of a flagged base, got %r — the axiom's unconstrained "
        "initial flag would otherwise be pinnable" % (observed.get('Sub'),))


# --- (A-consumed) the three REFUSAL mechanisms, composed as the construction ---
# composes them.  Written against the real UNCHANGED callees only
# (enum.EnumMeta.__new__ / __setattr__ / enum.unique), so it grounds the axioms
# at base_commit exactly as it would on the patched tree.

def _declare(members, bases=(int,)):
    """Run ONLY the base construction step over a declaration, using the real
    unchanged `enum.EnumMeta`: prepare the classdict, bind the declared choices
    under their own names, create the class object.  Raises whatever the real
    step raises."""
    import enum
    meta = enum.EnumMeta
    full = tuple(bases) + (enum.Enum,)
    cd = meta.__prepare__('Probe', full)
    for name, value in members:
        cd[name] = value
    return meta('Probe', full, cd)


def _record_flag(cls):
    """The recording of the preserve-when-callable flag: a GUARDED binding
    through the real unchanged `enum.EnumMeta.__setattr__`."""
    setattr(cls, FLAG_NAME, True)
    return cls


def check_base_step_refusal():
    """`base_class_creation` is TOTAL over declarations: it either delivers a
    class object with the requested identity, or REFUSES.  Grounds the Exsures
    leg against the real callee(s), and the delivery leg against an ordinary
    declaration."""
    import enum
    from django.db import models

    # (i) delivery: an ordinary declaration yields a class object, and the
    # object the step produced is the object it returns (identity).
    cls = _declare([('A', 1), ('B', 2)])
    assert isinstance(cls, enum.EnumMeta), (
        'base_class_creation: an ordinary declaration must yield a class object')
    assert id(cls) > 0, 'identity bridge premise: id() must be positive'

    # (ii) refusal — the declared kind cannot carry the declared choice values.
    # `bool` cannot be subclassed, so the base construction step itself refuses.
    refused = None
    try:
        _declare([('A', True)], bases=(bool,))
    except Exception as exc:  # noqa: BLE001
        refused = exc
    assert isinstance(refused, TypeError), (
        'base_class_creation Exsures unsound: a declaration whose declared kind '
        'cannot carry the values must be refused by the base step, got %r'
        % (refused,))
    assert 'acceptable base type' in str(refused), (
        'unexpected base-step refusal message %r' % (str(refused),))

    # (iii) refusal — the declaration names a choice after a table this step
    # must itself bind (`label`, bound by the same step that records
    # `_value2label_map_`).  Exercised through the ambient metaclass, which
    # performs that binding at both base_commit and the patched tree.
    refused2 = None
    try:
        class _Clash(models.IntegerChoices):
            label = 1, 'Label'
            B = 2, 'B'
    except Exception as exc:  # noqa: BLE001
        refused2 = exc
    assert isinstance(refused2, AttributeError), (
        'base_class_creation Exsures unsound: a declaration naming a choice '
        'after a table the base step binds must be refused, got %r' % (refused2,))

    # (iv) the base step does NOT refuse a declaration that merely repeats a
    # choice value: that refusal belongs to the value-distinctness step at the
    # very END of the construction.  This is what makes the repeated-value case
    # an ordinary in-domain declaration rather than one the base step rejects.
    dup = _declare([('A', 1), ('B', 1)])
    assert isinstance(dup, enum.EnumMeta), (
        'base_class_creation must ACCEPT a declaration that repeats a choice '
        'value — the distinctness refusal happens later, after the flag is '
        'recorded')
    return True


def check_finalize_grouping():
    """`finalize_grouping` ↔ the real unchanged `enum.unique`.  All four clauses:
    same object back, modelled flag untouched, refuses exactly the declarations
    that repeat a choice value, total otherwise."""
    import enum

    # (i) same object back, over a range of shapes.
    for members in ([('A', 1)], [('A', 1), ('B', 2)],
                    [('A', 1), ('B', 2), ('C', 3)], []):
        cls = _declare(members)
        out = enum.unique(cls)
        assert out is cls, (
            'finalize_grouping unsound: Ensures(Result() is grouping) violated — '
            'enum.unique returned %r, not the object it was given' % (out,))
        assert id(out) == id(cls), 'identity must be preserved by the step'

    # (ii) the modelled flag comes back exactly as it went in — absent, False and
    # True — so the step cannot launder a flag that was never recorded and cannot
    # clear one that was.
    for pre in ('ABSENT', False, True):
        cls = _declare([('A', 1), ('B', 2)])
        if pre != 'ABSENT':
            setattr(cls, FLAG_NAME, pre)
        before = getattr(cls, FLAG_NAME, 'ABSENT')
        out = enum.unique(cls)
        after = getattr(out, FLAG_NAME, 'ABSENT')
        assert after == before, (
            'finalize_grouping unsound: Ensures(Result().preserve_when_callable '
            '== Old(grouping.preserve_when_callable)) violated — flag %r became '
            '%r' % (before, after))

    # (iii) refuses EXACTLY the declarations that repeat a choice value, over a
    # seeded fuzz of value multisets.
    rng = random.Random(12304)
    accepted = refusals = 0
    for _ in range(600):
        k = rng.randint(1, 5)
        values = [rng.randint(0, 3) for _ in range(k)]
        members = [('M%d' % i, v) for i, v in enumerate(values)]
        cls = _declare(members)
        repeats = len(set(values)) != len(values)
        exc = None
        try:
            out = enum.unique(cls)
        except Exception as e:  # noqa: BLE001
            exc = e
        if repeats:
            refusals += 1
            assert isinstance(exc, ValueError), (
                'finalize_grouping Exsures unsound: a declaration repeating a '
                'choice value (%r) must be refused, got %r' % (values, exc))
            assert 'duplicate values found' in str(exc), (
                'unexpected distinctness refusal message %r' % (str(exc),))
        else:
            accepted += 1
            assert exc is None and out is cls, (
                'finalize_grouping unsound: a declaration with distinct values '
                '(%r) must be accepted and handed back, got %r' % (values, exc))
    assert accepted and refusals, (
        'the distinctness fuzz must realize BOTH outcomes (accepted=%d '
        'refused=%d)' % (accepted, refusals))
    return accepted, refusals


def check_flag_name_guard():
    """`flag_name_taken_by_choice` ↔ the table the real unchanged
    `enum.EnumMeta.__setattr__` consults.  Recording a name is refused with
    `AttributeError('Cannot reassign members.')` EXACTLY when that name is one of
    the class's own declared members, and succeeds otherwise."""
    rng = random.Random(123041)
    names = [FLAG_NAME, 'A', 'B', 'label_ish', 'zz', 'other', 'DIAMOND']
    taken_refused = free_bound = 0
    for _ in range(400):
        k = rng.randint(1, 3)
        member_names = rng.sample(names, k)
        members = [(n, i + 1) for i, n in enumerate(member_names)]
        cls = _declare(members)
        target = rng.choice(names)
        is_member = target in cls.__dict__.get('_member_map_', {})
        exc = None
        try:
            setattr(cls, target, True)
        except Exception as e:  # noqa: BLE001
            exc = e
        if is_member:
            taken_refused += 1
            assert isinstance(exc, AttributeError), (
                'flag_name_taken_by_choice unsound: rebinding a declared '
                'choice name %r must be refused, got %r' % (target, exc))
            assert 'Cannot reassign members' in str(exc), (
                'unexpected guard message %r' % (str(exc),))
        else:
            free_bound += 1
            assert exc is None, (
                'flag_name_taken_by_choice unsound: binding a name %r that is '
                'NOT a declared choice must succeed, got %r' % (target, exc))
            assert getattr(cls, target) is True
    assert taken_refused and free_bound, (
        'the guard fuzz must realize BOTH outcomes (refused=%d bound=%d)'
        % (taken_refused, free_bound))

    # the case the spec turns on: the flag's OWN name declared as a choice.
    cls = _declare([(FLAG_NAME, 1), ('B', 2)])
    exc = None
    try:
        _record_flag(cls)
    except Exception as e:  # noqa: BLE001
        exc = e
    assert isinstance(exc, AttributeError), (
        'the recording of the flag must be REFUSED when a declared choice '
        'already occupies its name, got %r' % (exc,))
    return taken_refused, free_bound


def check_refusal_independence():
    """The three declaration predicates are INDEPENDENT: every combination is
    realizable through the real callees, so no clause of the spec may be
    discharged by assuming one predicate settles another."""
    import enum

    def observe(members, bases=(int,)):
        """(base_refuses, flag_name_taken, repeats_value) as the real callees
        report them, each mechanism probed on its own."""
        base_refuses = False
        try:
            probe = _declare(members, bases=bases)
        except Exception:  # noqa: BLE001
            return (True, None, None)
        taken = FLAG_NAME in probe.__dict__.get('_member_map_', {})
        # probe the distinctness step on a FRESH object so the guard probe above
        # cannot influence it
        fresh = _declare(members, bases=bases)
        repeats = False
        try:
            enum.unique(fresh)
        except ValueError:
            repeats = True
        return (base_refuses, taken, repeats)

    combos = {}
    shapes = [
        # (declaration, expected combination)
        (((int,), [('A', 1), ('B', 2)]), (False, False, False)),
        (((int,), [('A', 1), ('B', 1)]), (False, False, True)),
        (((int,), [(FLAG_NAME, 1), ('B', 2)]), (False, True, False)),
        (((int,), [(FLAG_NAME, 1), ('B', 1)]), (False, True, True)),
        (((bool,), [('A', True)]), (True, None, None)),
        (((bool,), [(FLAG_NAME, True), ('B', True)]), (True, None, None)),
    ]
    for (bases, members), expected in shapes:
        got = observe(members, bases=bases)
        assert got == expected, (
            'declaration-predicate independence: declaration %r (bases %r) was '
            'expected to realize %r, the real callees report %r'
            % (members, bases, expected, got))
        combos[got] = combos.get(got, 0) + 1
    # all four combinations of the two later predicates, plus the base refusal
    assert len([k for k in combos if k[0] is False]) == 4, (
        'the four combinations of flag_name_taken_by_choice x '
        'repeats_choice_value must all be realizable, got %r' % (combos,))
    assert any(k[0] is True for k in combos), (
        'base_step_refuses must be realizable independently, got %r' % (combos,))
    return combos


def check_refusal_order():
    """The construction records the flag BEFORE handing the grouping to the
    value-distinctness step, and that order is OBSERVABLE.  Grounds the
    `not flag_name_taken_by_choice` conjunct of the RepeatedChoiceValue Exsures:
    a declaration that BOTH names a choice after the flag's name AND repeats a
    choice value reports the taken-name refusal, never the duplicate one."""
    import enum

    members = [(FLAG_NAME, 1), ('B', 1)]   # both conditions hold

    # order as the construction composes them: record the flag, then check.
    cls = _declare(members)
    first = None
    try:
        _record_flag(cls)
        enum.unique(cls)
    except Exception as exc:  # noqa: BLE001
        first = exc
    assert isinstance(first, AttributeError) and 'Cannot reassign members' in str(first), (
        'refusal order unsound: with the flag recorded first, the taken-name '
        'refusal must be what escapes, got %r' % (first,))

    # the OPPOSITE order, to show the two are genuinely distinguishable (this is
    # what the weak-finalize-before-flag reject case models).
    cls2 = _declare(members)
    second = None
    try:
        enum.unique(cls2)
        _record_flag(cls2)
    except Exception as exc:  # noqa: BLE001
        second = exc
    assert isinstance(second, ValueError) and 'duplicate values found' in str(second), (
        'refusal order unsound: with the distinctness step first, the duplicate '
        'refusal must be what escapes, got %r' % (second,))
    assert type(first) is not type(second), (
        'the two orders must be observably different for the ordering clause to '
        'have content')
    return type(first).__name__, type(second).__name__


# --- end-to-end against the REAL patched Choices, on the F2P template ----------

_F2P_OBSERVED = []


def check_real_choices_f2p():
    from django.db import models
    from django.template import Context, Template

    class Suit(models.IntegerChoices):
        DIAMOND = 1, 'Diamond'
        SPADE = 2, 'Spade'
        HEART = 3, 'Heart'
        CLUB = 4, 'Club'

    has_flag = bool(getattr(Suit, 'do_not_call_in_templates', False))
    _F2P_OBSERVED.append(has_flag)

    # premise: a no-argument construction of the grouping fails with a
    # required-argument TypeError (this is what the resolution rule reacts to).
    et = None
    try:
        Suit()
    except Exception as e:  # noqa: BLE001
        et = type(e)
    assert et is TypeError, (
        "REAL premise: Suit() raised %r, expected a required-argument TypeError"
        % et)

    template = Template('{{ Suit.DIAMOND.label }}|{{ Suit.DIAMOND.value }}')
    output = template.render(Context({'Suit': Suit}))

    if has_flag:
        # patched metaclass: the grouping is preserved, members resolve.
        assert output == 'Diamond|1', (
            "patched Choices F2P mismatch: expected 'Diamond|1', got %r" % output)
        # and the variable `Suit` itself resolves to the class object, when
        # resolved through a template-bound context.
        resolved = _resolve_bound_var('Suit', Suit)
        assert resolved is Suit, (
            "patched Choices: `Suit` must resolve to the class itself, got %r"
            % resolved)
    else:
        # pre-patch state: `Suit()` is invoked, fails, members are unreachable;
        # the configured string_if_invalid is substituted, so members do not
        # render (the rendered output never contains a resolved member label).
        assert 'Diamond' not in output, (
            "pre-patch Choices F2P: members unexpectedly resolved, got %r"
            % output)


def _resolve_bound_var(name, obj):
    """Resolve an arbitrarily-named variable through a template-bound context."""
    from django.template import Context, Template
    from django.template.base import Variable
    t = Template('{{ %s }}' % name)
    ctx = Context({name: obj})
    with ctx.bind_template(t):
        return Variable(name).resolve(ctx)


def main():
    _bootstrap_django()

    check_base_construction()
    check_base_step_refusal()
    fin_accepted, fin_refused = check_finalize_grouping()
    guard_refused, guard_bound = check_flag_name_guard()
    combos = check_refusal_independence()
    order = check_refusal_order()

    # The resolution rule across the patched / unpatched / absent flag, plus
    # an extended fuzz over truthy/falsy flag VALUES and unrelated attributes
    # (which must not perturb the rule).  This is exactly the raise/sentinel
    # fuzzing SPEC_GUIDE directive 7 mandates: every branch dereferences the
    # invalid-value sentinel (string_if_invalid) on the failed-invoke path.
    #
    #   truthy flag values  -> rule preserves the object (Result()==identity)
    #   falsy / absent flag -> no-arg invoke fails -> string_if_invalid (INVALID)
    truthy_flags = [True, 1, 'yes', ' ', [0], (0,), object(), 1.5, -1]
    falsy_flags = [False, 0, '', None, [], (), 0.0]
    rng = random.Random(12304)
    extras = [None, {'alters_data': False}, {'q': 1},
              {'value': 9}, {'unrelated': object()}]

    # base trio (boolean True / boolean False / attribute-absent), repeated to
    # guard against any non-determinism in the engine state.
    for _ in range(2000):
        for base_flag in (True, False, None):
            check_resolution_rule(base_flag)

    # extended fuzz over flag truthiness + unrelated attributes.
    for _ in range(2000):
        flag = rng.choice(truthy_flags + falsy_flags)
        extra = rng.choice(extras)
        cls = _make_require_arg_callable(flag, extra)
        # premise: no-arg construction fails with a required-argument TypeError.
        et = None
        try:
            cls()
        except Exception as e:  # noqa: BLE001
            et = type(e)
        assert et is TypeError, (
            "fuzz scenario invalid: cls() raised %r not TypeError (flag=%r)"
            % (et, flag))
        truthy = bool(getattr(cls, 'do_not_call_in_templates', False))
        resolved = _resolve_bound(cls)
        if truthy:
            assert resolved is cls, (
                "fuzz preserve viol flag=%r extra=%r -> %r"
                % (flag, extra, resolved))
        else:
            assert resolved is not cls and resolved == STRING_IF_INVALID, (
                "fuzz invoke viol flag=%r extra=%r -> %r (expected %r)"
                % (flag, extra, resolved, STRING_IF_INVALID))

    check_real_choices_f2p()

    print("G-AX OK: base_class_creation (initial flag UNCONSTRAINED: absent/"
          "falsy with no flagged ancestor, inherited-truthy under a flagged "
          "base, both realized through the real enum.EnumMeta.__new__; TOTAL — "
          "refuses an unusable declared kind and a choice named after a table it "
          "binds, ACCEPTS a repeated choice value); finalize_grouping (real "
          "enum.unique: same object back, modelled flag untouched across "
          "absent/False/True, refuses exactly the repeated-value declarations — "
          "%d accepted / %d refused over a seeded fuzz); the declaration "
          "predicates (real enum.EnumMeta.__setattr__ guard: %d refusals on "
          "declared-choice names, %d bindings on free names; independence combos "
          "%r; refusal ORDER observable — flag-first yields %s, "
          "distinctness-first yields %s); and "
          "resolved_in_template (preserve -> "
          "object itself; otherwise -> string_if_invalid) sound against the "
          "REAL Variable._resolve_lookup over 6000+ template-bound resolutions "
          "(base trio + truthiness/attribute fuzz); the REAL Django "
          "IntegerChoices in this tree carries the flag=%r and the F2P template "
          "'{{ Suit.DIAMOND.label }}|{{ Suit.DIAMOND.value }}' renders "
          "accordingly (flagged -> 'Diamond|1'; unflagged -> the members do not "
          "resolve, which is the end-to-end reading of the postcondition this "
          "spec demands)."
          % (fin_accepted, fin_refused, guard_refused, guard_bound,
             sorted(combos), order[0], order[1],
             _F2P_OBSERVED[-1] if _F2P_OBSERVED else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
