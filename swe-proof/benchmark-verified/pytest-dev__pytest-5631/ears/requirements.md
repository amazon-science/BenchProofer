# Requirements: Detect mock-patch arguments without triggering ambiguous truth-value errors

## Introduction

When pytest collects a test function decorated with `mock.patch`/
`unittest.mock.patch`, it must determine how many of the function's mandatory
positional arguments are actually supplied by the patch decorators (so those
arguments are not treated as missing fixtures). This is computed by
`num_mock_patch_args(function)` in `src/_pytest/compat.py`, which is called from
`getfuncargnames` in the same module during fixture-info collection.

Each patch decorator records a *patching* descriptor on the function's
`patchings` attribute. A decorator consumes one mandatory positional argument
only when it does **not** bind a named attribute and its replacement value is
the sentinel "default" object (`DEFAULT`) exported by the mock module — the
marker that tells mock to auto-create a mock for that argument. A decorator that
supplies an explicit replacement value (`new=<something>`) does not consume an
argument.

The previous implementation decided whether a replacement was the sentinel by
testing membership with `p.new in sentinels`, which relies on `==` equality.
When the replacement value is an object whose equality comparison does not
return an ordinary boolean — for example a NumPy array, whose `==` yields an
array and whose truth value is therefore ambiguous — this membership test raises
`ValueError` ("The truth value of an array with more than one element is
ambiguous"). Because this happens during collection, the whole test module fails
to collect.

The goal is to detect sentinel-default replacements using object **identity**
rather than equality, so that a patch whose replacement is an array-like (or any
object with a non-boolean/ambiguous `==`) is handled without error, while the
mock-argument count remains exactly what it was for all ordinary replacements.

## Requirement 1: Count mock-patch arguments using identity, not equality

**User story:** As a pytest user who patches a target with an array-like value
(e.g. `@patch(target=..., new=np.array([...]))`), I want my test to collect and
run, so that the presence of such a replacement does not break collection.

**Acceptance criteria**

1. WHEN `num_mock_patch_args` inspects a function's `patchings` and any patching's
   replacement value is an object whose equality comparison does not yield a
   plain boolean (such as a NumPy-like array whose truth value is ambiguous),
   THEN `num_mock_patch_args` SHALL determine whether that replacement is a
   sentinel default by object identity and SHALL NOT raise, and SHALL NOT allow
   any exception from that value's equality comparison to propagate.
2. WHEN a test function is decorated with a patch whose replacement is such an
   array-like value and is collected by pytest, THEN collection SHALL succeed and
   the test SHALL be run to a normal (non-error) outcome, rather than failing to
   collect with an ambiguous-truth-value error.
3. The system SHALL classify a patching's replacement as a sentinel default only
   when the replacement is the very same object as one of the recognised
   sentinel defaults, using identity comparison rather than equality comparison.

## Requirement 2: Preserve the mock-argument count for ordinary replacements

**User story:** As a maintainer, I want the number of arguments attributed to
mock decorators to stay exactly correct for normal patches, so that fixture
resolution and argument counting are unchanged for existing tests.

**Acceptance criteria**

1. WHEN a function has one or more patchings, THEN `num_mock_patch_args` SHALL
   return the count of patchings that both do not bind a named attribute and
   whose replacement is a recognised sentinel default object.
2. WHEN a patching binds a named attribute, THEN that patching SHALL NOT be
   counted, regardless of its replacement value.
3. WHEN a patching's replacement value is an explicit object supplied by the
   caller (i.e. it is not the same object as any recognised sentinel default),
   THEN that patching SHALL NOT be counted.
4. WHEN a patching does not bind a named attribute and its replacement is a
   recognised sentinel default object, THEN that patching SHALL be counted.
5. The recognised sentinel defaults SHALL be the `DEFAULT` objects exported by
   the `mock` module and the `unittest.mock` module, taken from whichever of
   those modules are currently imported.
6. WHEN a function has no patchings (the attribute is absent or empty), THEN
   `num_mock_patch_args` SHALL return zero.

## Requirement 3: Preserve fixture-argument resolution for patched tests (regression protection)

**User story:** As a maintainer, I want `getfuncargnames` and downstream fixture
resolution to keep working for functions decorated with mock patches, so that
existing patched tests, unittest-mock tests, and fixture combinations continue
to pass unchanged.

**Acceptance criteria**

1. The system SHALL keep excluding, from a decorated function's mandatory
   positional argument names, exactly the number of leading arguments accounted
   for by counted mock-patch decorators, so that those auto-created mock
   arguments are not mistaken for required fixtures.
2. WHEN a test function is decorated with `unittest.mock.patch` in the ordinary
   way (auto-created mocks and/or explicit replacements), THEN the test SHALL
   collect and run with its outcomes unchanged from prior behavior.
3. WHEN a patched test also declares pytest fixtures as parameters, THEN those
   fixtures SHALL continue to be resolved and injected correctly alongside the
   mock-supplied arguments.
4. The system SHALL continue to expose the argument-name computation performed by
   `getfuncargnames` so that wrapped functions and patched functions report the
   same mandatory-argument names as before this change.
