# Requirements: Correct qualified name for mocked stand-in objects

## Introduction

When autodoc encounters attribute access on a module listed in
`autodoc_mock_imports`, it fabricates lightweight stand-in objects to represent
the referenced symbols. These stand-ins are produced by the mock machinery in
`sphinx/ext/autodoc/mock.py` — specifically the `_MockObject` class and the
`_make_subclass` factory. Each stand-in is created with a *short name*: the
final dotted component of the symbol it represents (e.g. `Class` for
`pkg.sub.Class`).

Downstream renderers in `sphinx/util/typing.py` — notably `restify` — build a
complete reference by joining a stand-in's containing module path with the
*qualified name* the stand-in reports (via its `__qualname__` attribute). At
base revision, a freshly constructed stand-in reports an **empty** qualified
name, so the rendered reference truncates to the module path followed by a
trailing dot (e.g. `pkg.sub.` instead of `pkg.sub.Class`). This is visible in
generated documentation as a "Bases" entry that ends at the dot with the class
name missing.

The goal is that a mock stand-in reports a qualified name equal to the short
name it was created with, so that renderers produce complete references, while
leaving the rendering of all non-mock objects and the existing string rendering
of mocks unchanged.

## Requirement 1: Stand-in objects carry their short name

**User story:** As a documentation author using `autodoc_mock_imports`, I want
each fabricated stand-in object to remember the short name it represents, so
that tools reading it can reconstruct a complete reference to the symbol.

**Acceptance criteria**

1. WHEN a stand-in type is created by the subclass factory in
   `sphinx/ext/autodoc/mock.py` for a given short name, THEN the resulting type
   SHALL expose that short name as its name attribute (`__name__`).
2. The base mock object class SHALL define a default name attribute
   (`__name__`) equal to the empty string, so that a directly instantiated base
   mock object has a well-defined, empty short name.
3. WHEN a stand-in is produced through chained attribute access or item access
   on a mocked module or object (each access yielding a new stand-in for the
   accessed component), THEN each produced stand-in's name attribute SHALL be
   the accessed component's short name (the single dotted component just
   accessed), not the full dotted path and not the empty string.

## Requirement 2: Reported qualified name equals the short name

**User story:** As a renderer consuming a mock stand-in, I want the stand-in's
reported qualified name to equal its short name, so that I can form a complete
dotted reference rather than one that dangles at the separating dot.

**Acceptance criteria**

1. WHEN a stand-in object is constructed (its initializer runs), THEN it SHALL
   set its reported qualified name (`__qualname__`) to its own short name
   (`__name__`).
2. IF the stand-in was created with a non-empty short name, THEN the reported
   qualified name SHALL be that same non-empty short name.
3. IF the stand-in is a directly instantiated base mock object (no short name
   supplied), THEN the reported qualified name SHALL be the empty string,
   preserving the base object's prior behavior.
4. The reported qualified name SHALL contain only the short name — it SHALL NOT
   be prefixed with the module path or any other dotted components.

## Requirement 3: reST references to mocked symbols are complete

**User story:** As a reader of generated documentation, I want references to
mocked symbols (e.g. base classes inherited from mocked packages) to name the
symbol fully, so that "Bases" entries and type references are meaningful.

**Acceptance criteria**

1. WHEN `restify` in `sphinx/util/typing.py` is given a mock stand-in
   representing a symbol whose short name is non-empty, THEN it SHALL produce a
   reST class reference whose target is the stand-in's module path joined by a
   single dot to the short name (i.e. `<module>.<short name>`).
2. The produced reference SHALL NOT end at a trailing dot with the final
   component missing.
3. WHEN the stand-in represents a symbol reached by multi-level access such as
   `<module>.<attr>.<attr>`, THEN the rendered reference SHALL preserve the
   accumulated module path as the prefix and append the final short name as the
   last component, yielding the full dotted reference for that symbol.

## Requirement 4: Preserve rendering of non-mock objects

**User story:** As a maintainer, I want the qualified-name fix to be scoped to
mock stand-ins only, so that documentation of ordinary classes, containers,
callables, unions, type variables, literals, forward references, aliases,
PEP 585 generics, and broken/annotated hints is unaffected.

**Acceptance criteria**

1. The system SHALL leave the reST rendering (`restify`) of ordinary (non-mock)
   classes, builtins, typing containers, `Callable`, `Union`/`Optional`, type
   variables, type aliases, forward references, `Literal`, PEP 585 generics, and
   broken type hints unchanged from the base behavior.
2. The system SHALL leave the string rendering (`stringify`) of those same
   non-mock annotation kinds unchanged from the base behavior.
3. WHEN `stringify` in `sphinx/util/typing.py` is given a mock stand-in, THEN it
   SHALL continue to return the stand-in's display name as it did at base
   revision (the mock's string rendering SHALL remain unchanged by this fix).

## Requirement 5: Preserve existing mock object behavior

**User story:** As a maintainer, I want the fix to add the short-name/qualified
-name behavior without disturbing the mock objects' other established behaviors,
so that autodoc mocking keeps working as before.

**Acceptance criteria**

1. The system SHALL keep every other established attribute and behavior of mock
   stand-in objects intact — including the display name (`__display_name__`),
   module attribution (`__module__`), the mock marker, decorator-argument
   recording, and the container/callable/iteration protocols (e.g. length zero,
   empty iteration, membership always false, attribute and item access yielding
   further stand-ins).
2. The system SHALL continue to construct a subclassing stand-in when a mock
   object is used as a base class, so that classes inheriting from mocked
   classes are still documented.
