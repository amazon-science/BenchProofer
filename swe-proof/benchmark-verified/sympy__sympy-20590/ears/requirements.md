# Requirements: restore immutable, dict-free instances for core symbolic objects

## Introduction

Core SymPy objects derive from the expression base class `Basic`
(`sympy/core/basic.py`), which is instantiated by concrete types such as
`Symbol` (`sympy/core/symbol.py`). Historically these instances were designed to
be **immutable** and memory-light: each concrete type fixes its instance memory
layout (its permitted attribute set) so that instances carry **no per-instance
attribute dictionary** (`__dict__`) and cannot receive arbitrary new attributes.

`Basic` mixes in the printing-support helper class `Printable`
(`sympy/core/_print_helpers.py`), which sits in the ancestry of every concrete
symbolic type. This mixin layer did not pin its instance layout: it declared no
fixed attribute set. In CPython, a class whose instances would otherwise be
layout-pinned still regains a per-instance `__dict__` if **any** ancestor layer
(other than the universal base object) fails to pin its layout. As a result,
instances of `Basic` subclasses (e.g. `Symbol('s')`) regained a `__dict__`,
became freely mutable (an arbitrary attribute could be assigned), and stopped
raising on unexpected attribute assignment — a regression from the intended
immutable behavior.

The goal is to make the printing-support mixin pin its instance layout with an
empty fixed attribute set, so that every ancestor layer of the core symbolic
types is layout-pinned again and instances no longer carry a per-instance
attribute dictionary, while leaving all existing construction, equality,
substitution, traversal and printing behavior of these objects unchanged.

## Requirement 1: Core symbolic instances carry no per-instance attribute dictionary

**User story:** As a user of SymPy, I want expression objects to have no
per-instance `__dict__`, so that they keep the intended lightweight, immutable
representation.

**Acceptance criteria**

1. WHEN an instance of the core expression base class `Basic` (or any of its
   concrete subclasses, such as `Symbol`) is created, THEN that instance SHALL
   NOT expose a `__dict__` attribute (accessing `__dict__` on it, or querying
   `hasattr(instance, '__dict__')`, SHALL report that it has none).
2. The system SHALL ensure that every ancestor layer of these core symbolic
   types, including the printing-support mixin, pins its instance layout (fixes
   its attribute set), so that no ancestor layer reintroduces a per-instance
   attribute dictionary.

## Requirement 2: Core symbolic instances reject arbitrary attribute assignment

**User story:** As a user, I want expression objects to be immutable with
respect to arbitrary attributes, so that accidental mutation is caught rather
than silently stored.

**Acceptance criteria**

1. WHEN code attempts to assign an attribute that is not part of a `Basic`
   instance's fixed layout (for example `instance.x = 1` where `x` is not a
   declared attribute), THEN the assignment SHALL raise `AttributeError`.
2. IF a `Basic` instance regained a per-instance attribute dictionary, THEN such
   an assignment would silently succeed; the system SHALL prevent this by keeping
   the instance dict-free as required above.

## Requirement 3: Existing behavior of core symbolic objects is unchanged (regression protection)

**User story:** As a maintainer, I want the layout change to affect only
whether instances carry a `__dict__`, so that all other behavior of these
objects is preserved.

**Acceptance criteria**

1. WHEN a `Basic` instance is constructed from sub-arguments and its
   composition is inspected, THEN its construction and structural identity
   behavior (its arguments and any comparison of structural sameness) SHALL be
   unchanged relative to the pre-change behavior.
2. WHEN two `Basic` instances are compared for equality or hashed, THEN equality
   and hashing SHALL behave exactly as before.
3. WHEN any operation that was already supported on a `Basic` instance before
   the change is applied to it (for example substitution and replacement,
   structural queries over its sub-expressions, and traversal or evaluation
   operations), THEN that operation SHALL return the same result it returned
   before the change.
4. The system SHALL keep the printing behavior provided by the mixin (string and
   representation output, and the Jupyter/LaTeX display hooks) unchanged.
5. The system SHALL continue to allow the declared, layout-pinned attributes of
   these types (the attributes that are part of their fixed layout) to be read
   and set as before.
6. The layout change SHALL alter no observable behavior of these objects other
   than the removal of the per-instance attribute dictionary described in
   Requirements 1 and 2.
