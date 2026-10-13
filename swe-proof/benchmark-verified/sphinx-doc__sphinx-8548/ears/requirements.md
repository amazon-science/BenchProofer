# Requirements: Inherited instance-attribute docstrings in autodoc class documentation

## Introduction

Sphinx's `autodoc` extension documents Python classes, including their *data
members* — instance attributes assigned in method bodies (for example
`self.attr = None  #: docstring`) whose documentation is recovered from
comment-style docstrings attached to those assignments. The comment docstrings
for such attributes are discovered by the module source analysis
(`sphinx.pycode.ModuleAnalyzer`) and recorded under a search-key that pairs a
*namespace* (the qualified name of the class the attribute belongs to) with the
attribute name.

The affected code is the class-member collection routine
`sphinx.ext.autodoc.importer.get_class_members`, together with its caller
`ClassDocumenter.get_object_members` in `sphinx.ext.autodoc.__init__`.

Previously, documented instance attributes were collected only for the exact
class being documented: the routine matched the recorded namespace against the
dotted object path of the target class and consulted only the analyzer of the
module currently being documented. As a result, an instance attribute that is
declared (with a comment docstring) only on a *base* class was never picked up
when documenting a derived class with `inherited-members` enabled, even though
inherited methods and other inherited members were documented correctly.

The goal is that attribute-docstring collection walks the full inheritance
chain, so that documented instance attributes contributed by base classes are
discovered and can appear in a derived class's documentation, while the existing
behavior for a class's own attributes and for name shadowing across the
hierarchy is preserved.

## Requirement 1: Collect documented instance attributes across the inheritance chain

**User story:** As a documentation author, I want an instance attribute whose
docstring is declared only on a base class to be documented on a derived class
when inherited members are requested, so that inherited data members are not
silently dropped from the derived class's documentation.

**Acceptance criteria**

1. WHEN `get_class_members` collects members for a target class, THEN the
   routine SHALL consider, for every class in the target class's method
   resolution order (the class itself and each of its base classes), the
   documented instance attributes recorded for that class.
2. WHEN a documented instance attribute is declared (with a comment-style
   docstring) only on a base class of the target class, THEN
   `get_class_members` SHALL include that attribute in the returned member
   table, associated with the base class that declares it and carrying that
   attribute's docstring.
3. WHEN documenting a class with both `members` and `inherited-members`
   enabled, THEN the generated output SHALL include an attribute directive for
   each documented instance attribute reachable through the inheritance chain,
   each rendered under the target class's module with its recorded docstring.
4. The system SHALL determine the documented instance attributes of a given
   class in the chain by analyzing the module that defines that class and
   matching recorded attribute entries whose namespace equals that class's own
   qualified name.

## Requirement 2: Preserve first-occurrence-wins precedence for shadowed attributes

**User story:** As a documentation author, I want an attribute redefined on a
derived class to keep the derived class's docstring rather than a base class's,
so that the most specific documentation is shown.

**Acceptance criteria**

1. The system SHALL process the inheritance chain most-derived-first (the target
   class before its base classes).
2. IF an attribute name has already been added to the member table while walking
   the chain, THEN `get_class_members` SHALL NOT overwrite that entry with a
   later occurrence of the same name from a base class.
3. WHEN the same attribute name carries different docstrings on a derived class
   and one of its base classes, THEN the documented attribute SHALL retain the
   derived class's docstring and drop the base class's.
4. The system SHALL preserve the insertion order of member entries, adding each
   newly discovered attribute after the members already collected.

## Requirement 3: Preserve documentation of a class's own attributes and other members

**User story:** As a documentation author, I want a class's own instance
attributes and its previously-supported members to keep being documented exactly
as before, so that this change does not regress existing output.

**Acceptance criteria**

1. WHEN documenting a class with `members` enabled but without inherited
   members, THEN the output SHALL include an attribute directive, with its
   docstring, for each documented instance attribute declared directly on that
   class, and SHALL NOT include attributes contributed only by base classes.
2. The system SHALL continue to collect directly-defined members, members
   declared in `__slots__`, enum members, and annotation-only members
   (for example `attr: int`) as before.
3. WHEN an attribute name is already present in the member table from an earlier
   collection pass, THEN the attribute-docstring pass SHALL NOT replace that
   existing entry.
4. The system SHALL continue to produce, for an ordinary class documented with
   default options, the same class signature line, module line, base-class
   listing, and member set it produced previously.

## Requirement 4: Robust handling of unanalyzable classes in the chain

**User story:** As a user documenting a class whose base classes come from
modules that cannot be source-analyzed, I want documentation generation to
proceed without error, so that a single unanalyzable base class does not break
the whole class's documentation.

**Acceptance criteria**

1. IF the source module of some class in the inheritance chain cannot be located
   or analyzed, THEN `get_class_members` SHALL skip that class's
   attribute-docstring contribution and continue processing the remaining
   classes without raising an error.
2. IF a class in the chain lacks the attributes needed to identify its module or
   qualified name, THEN the routine SHALL skip that class and continue, rather
   than propagating an attribute-lookup error.
3. WHEN attribute-docstring collection completes, THEN `get_class_members`
   SHALL return the accumulated member table regardless of whether any class in
   the chain was skipped.

## Requirement 5: Caller no longer supplies a single analyzer

**User story:** As a maintainer, I want the member-collection routine to derive
the needed source analysis itself per class in the chain, so that collection is
not limited to the analyzer of only the class currently being documented.

**Acceptance criteria**

1. WHEN `ClassDocumenter.get_object_members` requests the class members, THEN it
   SHALL obtain them from `get_class_members` using the target object, its
   object path, and the attribute-getter, without passing a single
   module-specific analyzer to constrain the collection.
2. The system SHALL obtain the documented attributes for each class in the chain
   from that class's own module rather than only from the module of the target
   class.
