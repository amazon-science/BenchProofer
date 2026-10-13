# Requirements: Keep auto-generated xunit setup/teardown fixtures private in the fixture listing

## Introduction

The pytest test framework automatically synthesizes autouse fixtures to run the
classic xunit-style setup/teardown hook pairs at module, function, class, and
method granularity, as well as the corresponding `unittest.TestCase`
setup/teardown hook pairs (the class-scoped and instance-scoped setup/teardown
callables provided by unittest). These fixtures are created programmatically in
`src/_pytest/python.py` (the `_inject_setup_module_fixture`,
`_inject_setup_function_fixture`, `_inject_setup_class_fixture`, and
`_inject_setup_method_fixture` methods) and in `src/_pytest/unittest.py` (the
`_make_xunit_fixture` helper). Each is given a unique, non-user-facing name built
from a fixed descriptive template plus the owning object's name.

The fixture listing produced by `pytest --fixtures` (implemented in
`_showfixtures_main`) and by `pytest --fixtures-per-test` (implemented in
`_show_fixtures_per_test`, via its `write_fixture` helper) already treats a
fixture whose name begins with an underscore as private: at the default
verbosity such fixtures are omitted, and they are shown only when extra
verbosity (`-v`) is requested. Because these synthesized fixtures carry no
docstring, when they are shown the listing emits a "no docstring available"
notice for each.

Starting with the 6.2.0 release the synthesized fixture names no longer began
with an underscore, so they leaked into the default `--fixtures` output and
tripped tooling that flags undocumented fixtures. The goal is to restore the
prior contract: these generated fixtures are private (their names begin with an
underscore) and therefore hidden at the default verbosity, while remaining
visible under increased verbosity — with their existing behavior otherwise
unchanged.

## Requirement 1: Synthesized xunit/unittest setup-teardown fixtures are private

**User story:** As a developer who runs `pytest --fixtures`, I want the
framework-generated setup/teardown fixtures to be treated as private so that
they do not clutter the default fixture listing and do not trip CI checks that
forbid undocumented fixtures.

**Acceptance criteria**

1. WHEN pytest synthesizes an autouse fixture for a module-level, function-level,
   class-level, or method-level xunit setup/teardown pair, THEN the framework
   SHALL assign that fixture a name whose first character is an underscore.
2. WHEN pytest synthesizes the autouse fixture that runs a `unittest.TestCase`
   setup/teardown pair (such as the class-scoped fixture generated for a test
   case's class-level setup/teardown callables), THEN the framework SHALL assign
   that fixture a name whose first character is an underscore.
3. The system SHALL derive the remainder of each such generated name (everything
   after the leading underscore) from the same fixed descriptive template and
   the same owning-object name that were used previously, so that the generated
   name differs from the previous name only by the added leading underscore.
4. The system SHALL keep every generated setup/teardown fixture's name unique per
   owning object, so that distinct owning objects still receive distinct fixture
   names.

## Requirement 2: The default fixture listing hides these generated fixtures

**User story:** As a developer, I want `pytest --fixtures` at default verbosity
to omit these generated fixtures so that only user-facing fixtures are listed.

**Acceptance criteria**

1. WHEN `pytest --fixtures` is run at the default verbosity against tests that
   define xunit-style module/function/class/method setup/teardown hooks, THEN the
   fixture listing SHALL NOT include any of the synthesized setup/teardown
   fixtures.
2. WHEN `pytest --fixtures` is run at the default verbosity against a
   `unittest.TestCase` that defines class-level (or other supported) unittest
   setup/teardown callables, THEN the fixture listing SHALL NOT include the
   synthesized fixture for that hook.
3. IF the only fixtures that would otherwise be shown are these synthesized
   setup/teardown fixtures, THEN the "no docstring available" notice SHALL NOT
   appear anywhere in the default-verbosity fixture listing output.
4. WHEN a fixture listing is produced at the default verbosity, THEN the run
   SHALL complete successfully with a zero exit status.

## Requirement 3: Increased verbosity still reveals the generated fixtures

**User story:** As a developer debugging fixture resolution, I want to still be
able to see the generated setup/teardown fixtures when I ask for verbose output.

**Acceptance criteria**

1. WHEN `pytest --fixtures -v` is run against tests that define xunit-style
   module/function/class/method setup/teardown hooks, THEN the fixture listing
   SHALL include the synthesized setup/teardown fixtures.
2. WHEN a synthesized setup/teardown fixture is shown under increased verbosity
   and it has no docstring, THEN the listing SHALL emit exactly one "no docstring
   available" notice for that fixture.
3. WHEN `pytest --fixtures -v` is run against a set of tests that produces
   multiple such docstring-less synthesized fixtures, THEN the listing SHALL emit
   one "no docstring available" notice per shown synthesized fixture.
4. WHEN `pytest --fixtures -v` is run against a `unittest.TestCase` defining
   class-level setup/teardown callables, THEN the listing SHALL include the
   synthesized fixture and emit its "no docstring available" notice.
5. WHEN a fixture listing is produced under increased verbosity, THEN the run
   SHALL complete successfully with a zero exit status.

## Requirement 4: Preserve existing setup/teardown execution behavior

**User story:** As a user relying on xunit and unittest setup/teardown, I want
the renamed fixtures to run exactly as before so that renaming them private does
not change test execution.

**Acceptance criteria**

1. The system SHALL keep each synthesized setup/teardown fixture autouse and at
   its established scope (module, class, or function as appropriate), so that the
   corresponding setup and teardown hooks continue to run for their tests.
2. WHILE running a test whose class or module defines setup/teardown hooks, the
   system SHALL invoke those setup and teardown callables at the same points in
   the lifecycle as before the fixtures were made private.
3. The system SHALL continue to honor skip conditions on unittest test cases when
   the synthesized fixture runs, so that a skipped case is not set up.
4. The system SHALL continue to run any registered class-level and instance-level
   cleanup functions on success, on setup failure, and on teardown failure,
   unchanged by the fixture renaming.
