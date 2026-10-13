#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12304 (nagini).

Refutes (never proves) the refinement leg: does the MODEL agree with the REAL
patched repository function it claims to model?  G-VERIFY (impl |= spec) and
G-PBT (no wrong impl |= spec) never look at the repository, so this is the only
gate that executes real repo code against the model's impl region.

SHADOW (provenance `direct`)
---------------------------
The `# impl-start` / `# impl-end` region of `model.py`, copied VERBATIM below as
`build_template_usable_grouping` (the region contains no contract calls, so
nothing had to be stripped; the pure region of model.py is empty, so there is no
@Pure helper to copy, and no PSeq/ToSeq carrier occurs in this model, so no
sequence shim is needed):

    grouping = base_class_creation(identity)  # type: EnumGrouping
    if flag_name_taken_by_choice(identity):
        raise PreserveFlagNameTaken()
    grouping.preserve_when_callable = True
    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
    return delivered

Its @ContractOnly callees have no body to copy, so ALL of them are bridged to the
REAL repo / stdlib code they axiomatize (mapping.md section 3) — the axioms are
exercised, not assumed:

  * `base_class_creation(identity)` <-> the unchanged BASE construction step:
    `super().__new__(metacls, classname, bases, classdict)` at
    `django/db/models/enums.py:28` TOGETHER WITH the derived per-choice tables
    the same step records (`cls._value2label_map_` at line 29, the `label`
    property at line 33).  The bridge runs the REAL `ChoicesMeta.__new__` **as it
    exists at base_commit** — obtained from the repository itself with
    `git show HEAD:django/db/models/enums.py` inside the container and exec'd as
    a module (`enums_base_commit`), never retyped here — with the
    value-distinctness step alone REMOVED (the module's `enum` name is swapped
    for a proxy whose `unique` is the identity function) so that step is reached
    through its own bridge instead of twice.  The script asserts that this
    base_commit text differs from the patched working tree by exactly ONE added
    line, `cls.do_not_call_in_templates = True`, so the bridge provably contains
    the whole unchanged remainder of the function and nothing of the modelled
    edit.  Using the raw `enum.EnumMeta.__new__` alone would instead drop
    unchanged steps the oracle performs and make the frame comparison vacuous.
    The bridge is TOTAL, exactly as the axiom is: it either returns the produced
    object or reports `BaseStepRefused` carrying the real callee's own exception.
  * `finalize_grouping(grouping, identity)` <-> the unchanged value-distinctness
    step `enum.unique(cls)` at `django/db/models/enums.py:35` (line 34 at
    base_commit).  Returns the object the real callee hands back (asserting the
    axiom's `Result() is grouping` and flag-preservation clauses against it), or
    reports `RepeatedChoiceValue` carrying the real `ValueError`.
  * `flag_name_taken_by_choice(identity)` <-> the table the REAL unchanged
    `enum.EnumMeta.__setattr__` guard consults, `name in
    cls.__dict__['_member_map_']`; when it reports True the bridge additionally
    asserts the real binding really is refused, and when it reports False the
    shadow's own subsequent assignment goes through the real guard, so the
    predicate is checked on both sides.
  * `resolved_in_template(grouping)` <-> the unchanged template
    variable-resolution rule `django.template.base.Variable._resolve_lookup`
    (`django/template/base.py:816`, callable step at 851-866; mapping.md
    section 3.2).  The bridge drives the REAL `Variable('x').resolve(ctx)`
    inside a TEMPLATE-BOUND `Context` (so the failed-invoke branch can reach
    `context.template.engine.string_if_invalid`), with a deliberately
    NON-EMPTY `string_if_invalid` sentinel so "the object itself" and "the
    invalid value" can never be confused with each other or with `''`.

ORACLE
------
The REAL patched repo function is CALLED, not transliterated:
`django.db.models.enums.ChoicesMeta.__new__` (`django/db/models/enums.py:11`,
the gold patch adds the assignment at body line 34), invoked through the normal
class-creation path `ChoicesMeta(classname, bases, classdict)` from the patched
module imported off `/testbed` (the gate applies `patch.diff` before this script
runs).  The script additionally asserts via `inspect.getsource` that the ambient
`ChoicesMeta.__new__` carries the added `cls.do_not_call_in_templates = True`
line and exits non-zero otherwise, so it can never silently diff the shadow
against unpatched code.

OUTCOME TAGS (the spec's case split, made executable)
-----------------------------------------------------
The modelled function has FOUR outcomes and the differential compares which one
each leg produces, not merely whether both raised:

    delivered         the grouping is handed back, flagged
    base-refused      the base construction step refused the declaration
    flag-name-taken   recording the flag was refused, because one of the
                      grouping's own declared choices already occupies its name
    repeats-value     the value-distinctness step refused, because two declared
                      choices share a value

On the SHADOW leg the tag is which model exception escaped (`BaseStepRefused` /
`PreserveFlagNameTaken` / `RepeatedChoiceValue`) — i.e. the `Exsures` the spec
demands.  On the ORACLE leg the tag is read off the REAL traceback, by the line
of `django/db/models/enums.py` the exception escaped from: the flag-recording
line, the `return enum.unique(cls)` line, or any earlier line of the function.
Those line numbers are located in the patched source at run time (never
hard-coded), so the classification is the repository's own structure rather than
this script's opinion.  For `base-refused` and `repeats-value` the two legs'
exception TYPE and MESSAGE are compared as well, so a bridge that reported the
right tag with the wrong report would still be caught.

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
The model's carrier `EnumGrouping` keeps only the two facts the behaviour
touches; the real value is an enumeration class object.  `GroupingRef` is a
thin two-field view onto a REAL class object that inverts the bijection:

    grouping.identity                <-> id(cls)          (CPython id() > 0,
                                          asserted, so `Requires(identity > 0)`
                                          holds and never collides with the
                                          sentinel 0)
    grouping.preserve_when_callable  <-> getattr(cls, 'do_not_call_in_templates',
                                          False) / setattr(cls, ..., True)
    INVALID_VALUE == 0               <-> the engine's `string_if_invalid`
    resolved_in_template(g)          <-> id(cls) when the REAL resolution rule
                                          yields the class object itself, else 0

Generation runs concrete -> abstract: a shape (base kind + member list) is put
through the real unchanged base construction step FIRST, and the resulting
object's `id()` is the `identity` handed to the shadow, so every generated input
satisfies `Requires(identity > 0)` by construction (re-asserted at runtime, and
the axiom's own `Ensures(Result().identity == identity)` is checked against the
real callee rather than assumed).  For a declaration the base step REFUSES there
is no produced object, so the identity handed to the shadow is the (positive)
`id()` of the recorded refusal instead; no clause about the delivered grouping is
reachable on that leg, only the refusal report.

`declaration_available(identity)` — the model's single-use resource — is
inverted as a consumption counter on the pending record: the bridge asserts the
base construction step is entered at most ONCE per declaration, which is the
executable reading of a resource that is consumed and never returned.

OBSERVABLES compared per input (shadow vs oracle, both over real class objects)
------------------------------------------------------------------------------
  * the outcome tag above (all four outcomes occur in the domain);
  * for a refusal, the real exception type and message the report carries;
  * `preserve_when_callable` read back the way the unchanged consumer reads it;
  * identity preservation: the returned object IS the one the base construction
    step produced (observed by spying on the real `enum.EnumMeta.__new__` call
    the metaclass makes on the oracle leg, and by object identity against the
    pending record on the shadow leg) — the executable reading of
    `Ensures(Result().identity == identity)` plus the provenance token;
  * the resolution outcome through the REAL template rule ('self' vs the
    invalid sentinel) — the discriminating postcondition
    `resolved_in_template(Result()) == identity != INVALID_VALUE`;
  * the frame: members (name/value/label), `choices` / `names` / `labels` /
    `values`, `_value2label_map_`, and the produced class's own `__dict__` key
    set, so a shadow that perturbed anything else than the flag would be caught.

INPUT DOMAIN
------------
10 ancestry kinds x member configurations.  The ancestry families deliberately
cover BOTH initial states of the flag that mapping.md section 3.1 leaves
havoced, on both legs: `raw:*` (bases `(int|str, enum.Enum)` / `(enum.Enum,)` —
flag ABSENT after base construction), `flagged:*` (shared bases pre-carrying
`do_not_call_in_templates = True` — flag INHERITED-TRUTHY after base
construction, the case in which an impl that toggled or conditionally set the
flag would diverge), `own:*` (each leg's own `IntegerChoices` / `TextChoices` /
`Choices`, the real-world ancestry), and `bad:bool` (a declared kind that cannot
carry the declared choice values, which the base construction step refuses).
Member configurations cover the empty enum, a singleton, the exact F2P `Suit`
shape (`DIAMOND = 1, 'Diamond'`), auto-derived labels, list/tuple label forms,
multi-element values, lazy (`gettext_lazy`) labels, `__empty__`, negative / zero
/ empty-string values, AND the three refusal shapes: a choice declared under the
flag's own name, two choices sharing a value, both at once (which pins the
ORDER the two refusals are made in), and a choice named after a derived table the
base step itself binds.  Boundary shapes are enumerated first (every ancestry x
every member configuration, and each impl-relevant branch — both havoced initial
flag states, and all four outcome tags — taken many times), then seeded fuzz over
the same space fills the count to 100000 inputs, drawing repeated values and the
flag's own name with positive probability so the refusal legs are fuzzed too.

DISCRIMINATION SELF-TEST
------------------------
After the differential passes, the same differential is re-run with the shadow's
body MUTATED, once per mutation, and each mutant MUST be reported as disagreeing:
the assignment omitted (= the pre-patch impl), the assignment inverted (toggling
the incoming flag), the value-distinctness step dropped, the two refusal reports
swapped, the distinctness step run BEFORE the flag is recorded (the ORDER
mutation), and a body that reports the taken-name refusal unconditionally.  All
six are caught, so a green verdict here is not vacuous.

Pinned seed: SEED = 12304 (recorded in mapping.md under `## G-CONF`).
Exit 0 iff zero disagreements; on disagreement the input and both observations
are printed and the exit code is 1.  stdlib + Django (the repo under test) only.
"""
import enum
import gc
import inspect
import json
import random
import subprocess
import sys
import traceback
import types

SEED = 12304
N_TOTAL = 100_000

# model.py module constant: the invalid-value sentinel a template substitutes
# when a variable lookup fails to produce a usable object.
INVALID_VALUE = 0

# A deliberately NON-EMPTY string_if_invalid: the real rule substitutes
# context.template.engine.string_if_invalid on the failed-invoke branch, and the
# model abstracts that to INVALID_VALUE.  A distinctive value keeps "the object
# itself" and "the invalid value" strictly distinguishable (and distinct from '').
STRING_IF_INVALID = 'SBN_INVALID_SENTINEL'

THE_ADDED_LINE = 'cls.do_not_call_in_templates = True'
THE_FINAL_LINE = 'return enum.unique(cls)'
ENUMS_REL = 'django/db/models/enums.py'

# The name the preserve-when-callable flag is recorded under — hence the name one
# of the grouping's own declared choices can already occupy.
FLAG_NAME = 'do_not_call_in_templates'
# A derived per-choice table the BASE construction step itself binds; a choice
# declared under this name is refused by that step, before any flag is recorded.
TABLE_NAME = 'label'


# ---------------------------------------------------------------------------
# model.py's declared exceptions -- the Exsures the spec demands, mirrored so
# the shadow can be run as ordinary Python.
# ---------------------------------------------------------------------------
class BaseStepRefused(Exception):
    """model.py: the BASE construction step refused the declaration."""


class PreserveFlagNameTaken(Exception):
    """model.py: recording the flag was refused (its name is a declared choice)."""


class RepeatedChoiceValue(Exception):
    """model.py: the value-distinctness step refused (two choices share a value)."""


# ---------------------------------------------------------------------------
# type bridge (mapping.md section 2, inverted): a two-field view onto a REAL
# enumeration class object, exposing exactly the model carrier's two fields.
# ---------------------------------------------------------------------------
class GroupingRef:
    """`EnumGrouping` over the real value: `identity` <-> id(cls);
    `preserve_when_callable` <-> getattr/setattr of the
    `do_not_call_in_templates` attribute the unchanged consumer reads."""

    __slots__ = ('cls',)

    def __init__(self, cls):
        object.__setattr__(self, 'cls', cls)

    @property
    def identity(self):
        ident = id(self.cls)
        assert ident > 0, 'identity bridge broken: id() must be positive'
        return ident

    def __getattr__(self, name):
        if name == 'preserve_when_callable':
            return bool(getattr(self.cls, FLAG_NAME, False))
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == 'preserve_when_callable':
            # mapping.md section 2: identical boolean assignment, which goes
            # through the REAL enum.EnumMeta.__setattr__ guard.
            setattr(self.cls, FLAG_NAME, value)
            return
        raise AttributeError(name)


# ---------------------------------------------------------------------------
# @ContractOnly callee bridges -- the REAL repo / stdlib code the axioms model.
# ---------------------------------------------------------------------------
# The abstract `identity` is the only argument the model's base construction
# takes; the concrete shape it is built from is ambient (the model abstracts it
# away), threaded through this module-level slot, exactly as the pre-built real
# object is.
_PENDING = None


class _EnumSansUnique:
    """The real `enum` module with ONLY the value-distinctness step neutralised.

    The base construction step the axiom `base_class_creation` models is
    enums.py:28-33 -- everything the modelled function does BEFORE recording the
    flag.  The distinctness step at the last line is a SEPARATE axiom with its
    own bridge, so running it inside this one would exercise it twice and would
    make the shadow refuse a repeated choice value BEFORE the flag is recorded,
    which is precisely the ordering the spec forbids.  Swapping the module's
    `enum` name for this proxy removes that one step and nothing else."""

    def __init__(self, real):
        self.real = real

    def __getattr__(self, name):
        return getattr(self.real, name)

    @staticmethod
    def unique(cls):
        return cls


def base_class_creation(identity):
    """Bridge for the @ContractOnly axiom `base_class_creation` (mapping.md
    section 3.1): the unchanged base construction step, i.e. the REAL
    base_commit `ChoicesMeta.__new__` minus its final value-distinctness step.
    It has already run over the ambient shape; this returns the produced object
    and CHECKS the axiom's `Ensures(Result().identity == identity)` against it
    rather than assuming it -- or reports the refusal the real callee made,
    which is the axiom's `Exsures(BaseStepRefused, base_step_refuses(identity))`.
    """
    p = _PENDING
    assert p is not None, 'bridge misuse: no pending declaration'
    assert p['identity'] == identity, (
        'bridge misuse: base_class_creation called with identity %r, the pending '
        'declaration is %r' % (identity, p['identity']))
    # `Requires(declaration_available(identity))`: the resource is CONSUMED and
    # never returned, so the step is enterable at most once per declaration.
    p['uses'] += 1
    assert p['uses'] == 1, (
        'declaration_available violated: the base construction step was entered '
        '%d times for ONE declaration' % p['uses'])
    if p['base_exc'] is not None:
        raise BaseStepRefused(str(p['base_exc']))
    ref = p['ref']
    assert ref.identity == identity, (
        'base_class_creation axiom violated by the real callee: produced '
        'identity %r != requested %r' % (ref.identity, identity))
    return ref


def flag_name_taken_by_choice(identity):
    """Bridge for the @Pure @ContractOnly axiom `flag_name_taken_by_choice`
    (mapping.md section 3.3): the table the REAL unchanged
    `enum.EnumMeta.__setattr__` guard consults before rebinding a name.  When it
    reports True, the real binding is additionally attempted and asserted to be
    refused, so the abstraction is checked against the callee it stands for."""
    p = _PENDING
    assert p is not None and p['identity'] == identity, 'bridge misuse'
    if p['ref'] is None:
        # No object exists: unreachable from the shadow, which reports the base
        # step's refusal first.  The declaration's own answer is still defined.
        return any(name == FLAG_NAME for name, _v in p['members'])
    cls = p['ref'].cls
    taken = FLAG_NAME in cls.__dict__.get('_member_map_', {})
    if taken:
        refused = None
        try:
            setattr(cls, FLAG_NAME, True)
        except Exception as exc:                       # noqa: BLE001
            refused = exc
        assert isinstance(refused, AttributeError), (
            'flag_name_taken_by_choice bridge unsound: the real guard did NOT '
            'refuse the binding it reports as taken (got %r)' % (refused,))
    return taken


def finalize_grouping(grouping, identity):
    """Bridge for the @ContractOnly axiom `finalize_grouping` (mapping.md section
    3.4): the REAL unchanged value-distinctness step `enum.unique(cls)`.  Returns
    the object it hands back -- asserting the axiom's `Result() is grouping`,
    identity and flag-preservation clauses against the real callee -- or reports
    `RepeatedChoiceValue`, the axiom's Exsures."""
    p = _PENDING
    assert p is not None and p['identity'] == identity, 'bridge misuse'
    cls = grouping.cls
    flag_before = bool(getattr(cls, FLAG_NAME, False))
    try:
        out = enum.unique(cls)
    except ValueError as exc:
        raise RepeatedChoiceValue(str(exc)) from exc
    assert out is cls, (
        'finalize_grouping axiom violated by the real callee: enum.unique '
        'returned a different object (%r, not %r)' % (out, cls))
    ref = GroupingRef(out)
    assert ref.identity == identity, (
        'finalize_grouping axiom violated: identity %r != %r'
        % (ref.identity, identity))
    assert ref.preserve_when_callable == flag_before, (
        'finalize_grouping axiom violated: the flag changed across the real '
        'callee (%r -> %r)' % (flag_before, ref.preserve_when_callable))
    return ref


def resolved_in_template(grouping):
    """Bridge for the @Pure @ContractOnly axiom `resolved_in_template`
    (mapping.md section 3.2): drives the REAL
    `django.template.base.Variable._resolve_lookup` callable step through a
    template-bound Context, and abstracts the outcome the way the model does --
    the grouping's own identity when the object is preserved, else
    INVALID_VALUE."""
    from django.template import Context
    obj = grouping.cls
    ctx = Context({'x': obj})
    with ctx.bind_template(_TEMPLATE):
        resolved = _VARIABLE.resolve(ctx)
    if resolved is obj:
        return grouping.identity
    if resolved == STRING_IF_INVALID:
        return INVALID_VALUE
    raise AssertionError('unexpected resolution result %r' % (resolved,))


# ---------------------------------------------------------------------------
# SHADOW: the impl region of model.py, VERBATIM (no contract calls occur in it).
# ---------------------------------------------------------------------------
def build_template_usable_grouping(identity):
    # impl-start
    grouping = base_class_creation(identity)  # type: EnumGrouping
    if flag_name_taken_by_choice(identity):
        raise PreserveFlagNameTaken()
    grouping.preserve_when_callable = True
    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping
    return delivered
    # impl-end


# --- MUTANTS (discrimination self-test only; NOT the shadow) ----------------
def mutant_omit(identity):
    """The pre-patch impl: base construction, no flag established, no guard."""
    grouping = base_class_creation(identity)
    return finalize_grouping(grouping, identity)


def mutant_toggle(identity):
    """A conditional/toggling impl -- indistinguishable from the shadow when the
    incoming flag is absent, wrong when it is inherited-truthy."""
    grouping = base_class_creation(identity)
    if flag_name_taken_by_choice(identity):
        raise PreserveFlagNameTaken()
    grouping.preserve_when_callable = not grouping.preserve_when_callable
    return finalize_grouping(grouping, identity)


def mutant_skip_finalize(identity):
    """Drops the value-distinctness step: a repeated choice value is delivered."""
    grouping = base_class_creation(identity)
    if flag_name_taken_by_choice(identity):
        raise PreserveFlagNameTaken()
    grouping.preserve_when_callable = True
    return grouping


def mutant_swap_reports(identity):
    """Reports the duplicate-value refusal where the flag's name is taken."""
    grouping = base_class_creation(identity)
    if flag_name_taken_by_choice(identity):
        raise RepeatedChoiceValue('swapped')
    grouping.preserve_when_callable = True
    return finalize_grouping(grouping, identity)


def mutant_finalize_first(identity):
    """Runs the distinctness step BEFORE recording the flag -- the ORDER
    mutation, observationally different exactly where both refusals apply."""
    grouping = base_class_creation(identity)
    checked = finalize_grouping(grouping, identity)
    if flag_name_taken_by_choice(identity):
        raise PreserveFlagNameTaken()
    checked.preserve_when_callable = True
    return checked


def mutant_always_refuse(identity):
    """Reports the taken-name refusal on every declaration."""
    base_class_creation(identity)
    raise PreserveFlagNameTaken()


# ---------------------------------------------------------------------------
# environment: patched module (oracle) + base_commit module (callee bridge)
# ---------------------------------------------------------------------------
_TEMPLATE = None
_VARIABLE = None
PATCHED = None
BASE = None
FLAG_LINENO = None
UNIQUE_LINENO = None


def _bootstrap():
    global _TEMPLATE, _VARIABLE, PATCHED, BASE, FLAG_LINENO, UNIQUE_LINENO
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={},
            USE_I18N=True,
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': False,
                'OPTIONS': {'string_if_invalid': STRING_IF_INVALID},
            }],
        )
        django.setup()
    from django.template import Template
    from django.template.base import Variable
    _TEMPLATE = Template('{{ x }}')
    _VARIABLE = Variable('x')

    # ORACLE: the REAL patched module off /testbed.
    import django.db.models.enums as patched_mod
    PATCHED = patched_mod
    src_patched = inspect.getsource(patched_mod.ChoicesMeta.__new__)
    if THE_ADDED_LINE not in src_patched:
        print('ERROR: ambient ChoicesMeta.__new__ is NOT patched (missing %r); '
              'refusing to diff against unpatched code' % THE_ADDED_LINE)
        return False

    # Locate the two lines the outcome classification reads, in the patched file
    # itself -- never hard-coded, so the tags are the repository's structure.
    patched_lines = open('/testbed/%s' % ENUMS_REL).read().splitlines()
    for i, line in enumerate(patched_lines, 1):
        if line.strip() == THE_ADDED_LINE:
            FLAG_LINENO = i
        elif line.strip() == THE_FINAL_LINE:
            UNIQUE_LINENO = i
    if FLAG_LINENO is None or UNIQUE_LINENO is None:
        print('ERROR: could not locate the flag-recording line (%r) and the '
              'value-distinctness line (%r) in the patched %s'
              % (THE_ADDED_LINE, THE_FINAL_LINE, ENUMS_REL))
        return False
    if not FLAG_LINENO < UNIQUE_LINENO:
        print('ERROR: the flag is recorded at line %d, the distinctness step at '
              'line %d -- the modelled order does not hold in the repository'
              % (FLAG_LINENO, UNIQUE_LINENO))
        return False

    # CALLEE BRIDGE: the same file at base_commit, read from the repository.
    base_src = subprocess.check_output(
        ['git', 'show', 'HEAD:%s' % ENUMS_REL], cwd='/testbed').decode('utf-8')
    if THE_ADDED_LINE in base_src:
        print('ERROR: base_commit source already carries %r' % THE_ADDED_LINE)
        return False
    # provenance guard: the bridge must be the whole unchanged remainder of the
    # modeled function -- i.e. differ from the patched file by exactly the one
    # added line and nothing else.
    import difflib
    changed = [l for l in difflib.unified_diff(
        base_src.splitlines(), patched_lines, n=0)
        if l[:1] in '+-' and not l.startswith(('+++', '---'))]
    if changed != ['+        %s' % THE_ADDED_LINE]:
        print('ERROR: patched file differs from base_commit by more than the '
              'modeled line: %r' % (changed,))
        return False
    BASE = types.ModuleType('enums_base_commit')
    BASE.__dict__['__name__'] = 'enums_base_commit'
    exec(compile(base_src, '%s@base_commit' % ENUMS_REL, 'exec'), BASE.__dict__)
    return True


# --- shared, pre-flagged ancestries (usable by BOTH metaclass variants) ------
def _make_shared_bases():
    class FlaggedInt(int, enum.Enum):
        pass

    class FlaggedStr(str, enum.Enum):
        pass

    class FlaggedPlain(enum.Enum):
        pass

    for k in (FlaggedInt, FlaggedStr, FlaggedPlain):
        # inherited-truthy initial flag: the second realizable initial state of
        # the havoced axiom (mapping.md section 3.1).
        setattr(k, FLAG_NAME, True)
    return {'flagged:int': (FlaggedInt,), 'flagged:str': (FlaggedStr,),
            'flagged:plain': (FlaggedPlain,)}


SHARED = None

ANCESTRIES = ('own:int', 'own:str', 'own:plain',
              'raw:int', 'raw:str', 'raw:plain',
              'flagged:int', 'flagged:str', 'flagged:plain',
              'bad:bool')

# the value flavour each ancestry's member values must have
FLAVOR = {'own:int': 'int', 'own:str': 'str', 'own:plain': 'plain',
          'raw:int': 'int', 'raw:str': 'str', 'raw:plain': 'plain',
          'flagged:int': 'int', 'flagged:str': 'str', 'flagged:plain': 'plain',
          'bad:bool': 'int'}


def bases_for(kind, mod):
    """The base classes for an ancestry kind on one leg (`mod` is the patched or
    the base_commit enums module)."""
    family, flavor = kind.split(':')
    if family == 'own':
        return {'int': (mod.IntegerChoices,), 'str': (mod.TextChoices,),
                'plain': (mod.Choices,)}[flavor]
    if family == 'raw':
        return {'int': (int, enum.Enum), 'str': (str, enum.Enum),
                'plain': (enum.Enum,)}[flavor]
    if family == 'bad':
        # a declared kind that cannot carry the declared choice values: the base
        # construction step itself refuses this declaration.
        return (bool, enum.Enum)
    return SHARED[kind]


def _classdict(mod, kind, members):
    meta = mod.ChoicesMeta
    bases = bases_for(kind, mod)
    cd = meta.__prepare__('Suit', bases)
    for name, value in members:
        cd[name] = value
    return meta, bases, cd


def build_oracle(kind, members):
    """Run the ORACLE leg: the REAL patched `ChoicesMeta.__new__`, whole.
    Returns (tag, class object or None, base_id or None, exception or None)."""
    meta, bases, cd = _classdict(PATCHED, kind, members)
    box = []
    original = enum.EnumMeta.__new__

    def spying(metacls, classname, bs, cdict, **kw):
        obj = original(metacls, classname, bs, cdict, **kw)
        if not box:
            box.append(id(obj))
        return obj

    enum.EnumMeta.__new__ = spying
    try:
        out = meta('Suit', bases, cd)
    except BaseException as exc:                       # noqa: BLE001
        return _oracle_tag(exc), None, None, exc
    finally:
        enum.EnumMeta.__new__ = original
    return 'delivered', out, (box[0] if box else None), None


def _oracle_tag(exc):
    """Which outcome the REAL patched function produced, read off the line of
    `enums.py` the exception escaped from (located at run time)."""
    lns = [fr.lineno for fr in traceback.extract_tb(exc.__traceback__)
           if fr.filename.endswith(ENUMS_REL)]
    if not lns:
        return 'outside-construction'
    ln = lns[-1]
    if ln == FLAG_LINENO:
        return 'flag-name-taken'
    if ln == UNIQUE_LINENO:
        return 'repeats-value'
    return 'base-refused'


def run_base_step(kind, members):
    """The BASE construction step alone (enums.py:28-33 at base_commit), with the
    value-distinctness step neutralised so it is reached only through its own
    bridge."""
    real = BASE.__dict__['enum']
    BASE.__dict__['enum'] = _EnumSansUnique(real)
    try:
        meta, bases, cd = _classdict(BASE, kind, members)
        return meta('Suit', bases, cd)
    finally:
        BASE.__dict__['enum'] = real


def prepare(kind, members):
    """Put the declaration through the base construction step ONCE and record
    the pending state the bridges read (the inverted
    `declaration_available(identity)` resource)."""
    try:
        obj = run_base_step(kind, members)
    except BaseException as exc:                       # noqa: BLE001
        # no object exists; the identity handed to the shadow is the positive
        # id() of the recorded refusal, and only the refusal report is reachable.
        return {'kind': kind, 'members': members, 'ref': None,
                'base_exc': exc, 'identity': id(exc), 'uses': 0}
    ref = GroupingRef(obj)
    return {'kind': kind, 'members': members, 'ref': ref, 'base_exc': None,
            'identity': ref.identity, 'uses': 0}


def build_shadow(kind, members, impl):
    """Run the SHADOW leg. Returns (tag, GroupingRef or None, pending, exception)."""
    global _PENDING
    p = prepare(kind, members)
    _PENDING = p
    try:
        out = impl(p['identity'])
    except BaseStepRefused as exc:
        return 'base-refused', None, p, exc
    except PreserveFlagNameTaken as exc:
        return 'flag-name-taken', None, p, exc
    except RepeatedChoiceValue as exc:
        return 'repeats-value', None, p, exc
    except BaseException as exc:                       # noqa: BLE001
        return 'shadow-error:%s' % type(exc).__name__, None, p, exc
    finally:
        _PENDING = None
    return 'delivered', out, p, None


# ---------------------------------------------------------------------------
# observation: abstract both legs to comparable tuples
# ---------------------------------------------------------------------------
def observe(grouping, base_id):
    obj = grouping.cls
    members = [(m.name, repr(m.value), str(m.label)) for m in obj]
    v2l = sorted((repr(k), str(v)) for k, v in obj._value2label_map_.items())
    dict_keys = sorted(obj.__dict__.keys())
    resolved = resolved_in_template(grouping)
    return {
        # the flag, read the way the unchanged consumer reads it
        'preserve_when_callable': grouping.preserve_when_callable,
        # Ensures(Result().identity == identity) + built_from_declaration: the
        # returned object IS the one the unchanged base construction step produced
        'identity_preserved': (base_id is None) or (id(obj) == base_id),
        # Ensures(resolved_in_template(Result()) == identity != INVALID_VALUE)
        'resolution': ('self' if resolved == grouping.identity else
                       ('invalid' if resolved == INVALID_VALUE else 'other')),
        # frame: everything else the grouping carries must be untouched
        'members': members,
        'value2label': v2l,
        'choices': [(repr(v), str(l)) for v, l in obj.choices],
        'names': list(obj.names),
        'labels': [str(l) for l in obj.labels],
        'values': [repr(v) for v in obj.values],
        'dict_keys': dict_keys,
    }


LAZY = None


def lazy(text):
    global LAZY
    if LAZY is None:
        from django.utils.translation import gettext_lazy
        LAZY = gettext_lazy
    return LAZY(text)


def _report(exc):
    """The report a refusal carries, as the declarer sees it: the real callee's
    exception type and message.  The shadow's model exceptions carry the real
    callee's message verbatim (str(cause)), so the two legs are comparable."""
    if exc is None:
        return None
    cause = exc.__cause__ if exc.__cause__ is not None else exc
    if isinstance(exc, (BaseStepRefused, RepeatedChoiceValue)):
        return str(exc) if exc.__cause__ is None else str(cause)
    return str(exc)


def check_case(kind, members, impl=build_template_usable_grouping):
    """Run oracle and shadow on one input; return None on agreement, else a
    (kind, members, oracle_obs, shadow_obs, differing keys) tuple."""
    o_tag, o_obj, o_base_id, o_exc = build_oracle(kind, members)
    s_tag, s_out, s_pending, s_exc = build_shadow(kind, members, impl)

    if o_tag == 'outside-construction':
        # the declaration was rejected before the modelled function was entered
        # (nothing the model speaks about); both legs must agree it is.
        if s_tag.startswith('shadow-error'):
            return None
        return (kind, members, {'tag': o_tag}, {'tag': s_tag},
                ['outcome-tag(pre-construction)'])

    if o_tag != s_tag:
        return (kind, members,
                {'tag': o_tag, 'report': _report(o_exc)},
                {'tag': s_tag, 'report': _report(s_exc)},
                ['outcome-tag'])

    if o_tag != 'delivered':
        # the refusal REPORT must be the real callee's own, passed on unchanged.
        if o_tag == 'flag-name-taken':
            if not (isinstance(o_exc, AttributeError)
                    and 'Cannot reassign members' in str(o_exc)):
                return (kind, members, {'report': _report(o_exc)},
                        {'report': _report(s_exc)},
                        ['flag-name-refusal-shape'])
            return None
        if _report(o_exc) != _report(s_exc):
            return (kind, members, {'tag': o_tag, 'report': _report(o_exc)},
                    {'tag': s_tag, 'report': _report(s_exc)},
                    ['refusal-report'])
        return None

    o_obs = observe(GroupingRef(o_obj), o_base_id)
    s_base = s_pending['ref']
    s_obs = observe(s_out, id(s_base.cls) if s_base is not None else None)
    diff = [k for k in o_obs if o_obs[k] != s_obs[k]]
    if diff:
        return (kind, members, o_obs, s_obs, diff)
    # the discriminating guarantee, independently of agreement
    if o_obs['resolution'] != 'self' or not o_obs['preserve_when_callable']:
        return (kind, members, o_obs, s_obs, ['oracle-not-preserved'])
    return None


# ---------------------------------------------------------------------------
# input domain
# ---------------------------------------------------------------------------
NAMES = ['DIAMOND', 'SPADE', 'HEART', 'CLUB', 'FRESHMAN', 'SOPHOMORE',
         'A', 'B_C', 'z_x']


def member_configs(flavor):
    """Boundary member configurations for one value flavor, covering all four
    outcome tags."""
    if flavor == 'str':
        v = ['d', 's', 'h', '']
    else:
        v = [1, 2, 3, 0]
    out = [
        [],                                                   # empty enum
        [('DIAMOND', (v[0], 'Diamond'))],                     # exact F2P shape
        [('DIAMOND', (v[0], 'Diamond')), ('SPADE', (v[1], 'Spade'))],
        [('DIAMOND', v[0])],                                  # auto-derived label
        [('B_C', v[0]), ('z_x', v[1])],                       # auto label from name
        [('DIAMOND', [v[0], 'Diamond'])],                     # list label form
        [('DIAMOND', (v[0], lazy('Diamond')))],               # lazy label
        [('DIAMOND', (v[0], 'Diamond')), ('__empty__', '(Unknown)')],
        [('DIAMOND', (v[0], 'Diamond')), ('SPADE', v[1]),
         ('HEART', [v[2], lazy('Heart')])],                   # mixed forms
        [('DIAMOND', (v[3], 'Zero-ish'))],                    # 0 / '' value
        [(n, (val, 'L%d' % i)) for i, (n, val) in
         enumerate(zip(NAMES, range(10, 10 + len(NAMES))))]
        if flavor != 'str' else
        [(n, ('v%d' % i, 'L%d' % i)) for i, n in enumerate(NAMES)],
        # --- REFUSAL shapes: in the modelled domain, not outside it -----------
        # a choice declared under the flag's OWN name -> the recording of the
        # flag is refused (tag flag-name-taken)
        [(FLAG_NAME, (v[0], 'Flagged')), ('SPADE', (v[1], 'Spade'))],
        [(FLAG_NAME, (v[0], 'Flagged'))],
        # two choices sharing a value -> the value-distinctness step refuses
        # (tag repeats-value), AFTER the flag has been recorded
        [('DIAMOND', (v[0], 'Diamond')), ('SPADE', (v[0], 'Spade'))],
        [('DIAMOND', v[0]), ('SPADE', v[0]), ('HEART', (v[1], 'Heart'))],
        # BOTH at once -> pins the ORDER: the taken-name refusal is what the
        # construction reports, because the flag is recorded first
        [(FLAG_NAME, (v[0], 'Flagged')), ('SPADE', (v[0], 'Spade'))],
        [(FLAG_NAME, v[0]), ('SPADE', v[0]), ('HEART', v[0])],
        # a choice named after a derived table the BASE step itself binds ->
        # refused by that step (tag base-refused), before any flag is recorded
        [(TABLE_NAME, (v[0], 'Label')), ('SPADE', (v[1], 'Spade'))],
        [(TABLE_NAME, (v[0], 'Label')), ('SPADE', (v[0], 'Spade'))],
        [(TABLE_NAME, (v[0], 'Label')), (FLAG_NAME, (v[1], 'Flagged'))],
    ]
    if flavor == 'int':
        out.append([('DIAMOND', (-1, 'Neg')), ('SPADE', (-2, 'Neg2'))])
    if flavor == 'plain':
        # multi-element values (the *value, label split keeps a tuple)
        out.append([('DIAMOND', (1, 2, 'Diamond')), ('SPADE', (3, 4, 'Spade'))])
        out.append([('DIAMOND', (1, 2))])   # trailing non-str: no label given
    return out


def boundary_cases():
    for kind in ANCESTRIES:
        for members in member_configs(FLAVOR[kind]):
            yield kind, members


def fuzz_case(rng):
    kind = rng.choice(ANCESTRIES)
    flavor = FLAVOR[kind]
    k = rng.randint(0, 5)
    names = rng.sample(NAMES, k)
    # Values are drawn from a pool that ALLOWS repeats with positive probability,
    # so the value-distinctness refusal is fuzzed rather than avoided: a repeated
    # choice value is inside the modelled domain (it is refused at the very end,
    # after the flag is recorded, by a step the construction reaches normally).
    if flavor == 'str':
        pool = ['a', 'b', 'c', 'dd', 'e f', '', 'z', 'Q', 'ss']
    else:
        pool = list(range(-50, 50))
    if rng.random() < 0.25 and k:
        # deliberately repeat: draw from a tiny pool
        small = rng.sample(pool, min(2, len(pool)))
        values = [rng.choice(small) for _ in range(k)]
    else:
        values = rng.sample(pool, k)
    members = []
    for name, value in zip(names, values):
        r = rng.random()
        if r < 0.35:
            members.append((name, value))                      # auto label
        elif r < 0.6:
            members.append((name, (value, 'L_%s' % name)))
        elif r < 0.75:
            members.append((name, [value, 'L_%s' % name]))
        elif r < 0.9:
            members.append((name, (value, lazy('Lazy %s' % name))))
        elif flavor == 'plain':
            members.append((name, (value, value, 'Multi')))
        else:
            members.append((name, (value, '')))               # empty label
    # declare a choice under the flag's own name with positive probability, so
    # the taken-name refusal (and its ORDERING against a repeated value) is
    # fuzzed too; and a choice named after a derived table the base step binds.
    if rng.random() < 0.15:
        val = rng.choice(pool) if flavor != 'plain' else rng.choice(pool)
        members.append((FLAG_NAME, (val, 'Flagged')))
    if rng.random() < 0.08:
        val = rng.choice(pool) if flavor != 'plain' else rng.choice(pool)
        members.append((TABLE_NAME, (val, 'Label')))
    if k and rng.random() < 0.1:
        members.append(('__empty__', '(Unknown)'))
    return kind, members


def main():
    if not _bootstrap():
        print('status=error')
        return 1
    global SHARED
    SHARED = _make_shared_bases()

    checked = 0
    n_boundary = 0
    initial_absent = 0
    initial_truthy = 0
    tags = {}

    def account(kind, members):
        """Record which havoced initial flag state and which outcome tag this
        shape exercises, reusing the shadow's own pending record so no extra
        class construction is needed and a refused declaration is handled."""
        o_tag, _o, _b, _e = build_oracle(kind, members)
        tags[o_tag] = tags.get(o_tag, 0) + 1
        return o_tag

    # boundary cases first
    for kind, members in boundary_cases():
        p = prepare(kind, members)
        if p['ref'] is not None and p['ref'].preserve_when_callable:
            initial_truthy += 1
        else:
            initial_absent += 1
        account(kind, members)
        bad = check_case(kind, members)
        if bad:
            print('DISAGREE (boundary) kind=%s members=%r keys=%r' %
                  (bad[0], bad[1], bad[4]))
            for k in bad[4]:
                print('  %s: oracle=%r shadow=%r' % (k, bad[2].get(k), bad[3].get(k)))
            print('status=fail')
            return 1
        checked += 1
        n_boundary += 1

    # every one of the four modelled outcomes must be realized by the boundary
    # domain -- otherwise the case split is not being differentiated at all.
    for required in ('delivered', 'base-refused', 'flag-name-taken',
                     'repeats-value'):
        if not tags.get(required):
            print('ERROR: the input domain did not realize the modelled outcome '
                  '%r (tags=%r); the case split is untested' % (required, tags))
            print('status=error')
            return 1

    # seeded fuzz over the same space, to the input count
    rng = random.Random(SEED)
    n_fuzz = 0
    while checked < N_TOTAL:
        kind, members = fuzz_case(rng)
        p = prepare(kind, members)
        if p['ref'] is not None and p['ref'].preserve_when_callable:
            initial_truthy += 1
        else:
            initial_absent += 1
        bad = check_case(kind, members)
        if bad:
            print('DISAGREE (fuzz) kind=%s members=%r keys=%r' %
                  (bad[0], bad[1], bad[4]))
            for k in bad[4]:
                print('  %s: oracle=%r shadow=%r' % (k, bad[2].get(k), bad[3].get(k)))
            print('status=fail')
            return 1
        checked += 1
        n_fuzz += 1
        if n_fuzz % 5000 == 0:
            gc.collect()

    if not (initial_absent and initial_truthy):
        print('ERROR: input domain did not exercise both havoced initial flag '
              'states (absent=%d truthy=%d)' % (initial_absent, initial_truthy))
        print('status=error')
        return 1

    # --- discrimination self-test: every mutated shadow MUST be caught --------
    discrimination = {}
    for label, impl in (('omit-assignment', mutant_omit),
                        ('toggle-assignment', mutant_toggle),
                        ('skip-distinctness', mutant_skip_finalize),
                        ('swap-refusal-reports', mutant_swap_reports),
                        ('distinctness-before-flag', mutant_finalize_first),
                        ('refuse-everywhere', mutant_always_refuse)):
        caught = 0
        for kind, members in boundary_cases():
            if check_case(kind, members, impl=impl) is not None:
                caught += 1
        discrimination[label] = caught
        if caught == 0:
            print('ERROR: mutant %s was NOT caught -- this check is vacuous'
                  % label)
            print('status=error')
            return 1

    print('G-CONF OK: shadow (model.py impl region, verbatim; @ContractOnly '
          'callees bridged to the real base_commit ChoicesMeta.__new__ minus its '
          'distinctness step, the real enum.unique, the real '
          'enum.EnumMeta.__setattr__ guard table and the real '
          'Variable._resolve_lookup) agrees with the REAL patched '
          'django.db.models.enums.ChoicesMeta.__new__ on %d inputs '
          '(%d boundary + %d fuzz, seed %d) over %d ancestries; outcome tags '
          'realized in the boundary domain: %r (classified by the enums.py line '
          'the real exception escaped from: flag recorded at %d, distinctness at '
          '%d); initial flag absent=%d inherited-truthy=%d; mutants caught: %r.'
          % (checked, n_boundary, n_fuzz, SEED, len(ANCESTRIES), tags,
             FLAG_LINENO, UNIQUE_LINENO, initial_absent, initial_truthy,
             discrimination))
    print(json.dumps({
        'checked': checked, 'disagreements': 0, 'seed': SEED,
        'boundary': n_boundary, 'fuzz': n_fuzz,
        'oracle': 'django.db.models.enums.ChoicesMeta.__new__ (called, patched)',
        'shadow': 'direct (verbatim impl region of model.py)',
        'outcome_tags': tags,
        'flag_lineno': FLAG_LINENO,
        'distinctness_lineno': UNIQUE_LINENO,
        'initial_flag_absent': initial_absent,
        'initial_flag_inherited_truthy': initial_truthy,
        'mutants_caught': discrimination,
        'status': 'pass',
    }))
    return 0


if __name__ == '__main__':
    sys.exit(main())
