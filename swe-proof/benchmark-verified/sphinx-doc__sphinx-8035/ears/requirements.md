# Requirements: selectable private members for autodoc

## Introduction

The autodoc extension (`sphinx.ext.autodoc`) generates API documentation by
enumerating the members of a module or class and, for each candidate, making a
keep-or-drop decision. Members whose names begin with an underscore are treated
as *private*.

Historically the `:private-members:` option behaved as an all-or-nothing flag:
when present it documented **every** private member, and when absent it
documented **none**. This mirrors the older behavior of `:members:` before it
accepted an explicit argument list. Users have asked for `:private-members:` to
accept arguments so that only the named private members are documented, exactly
the way `:members:` already supports naming specific members.

This document specifies the behavior of the `:private-members:` option for the
`automodule` and `autoclass` directives (and the corresponding programmatic
autodoc options). The goal, in behavioral terms: `:private-members:` must
support three shapes — omitted, present-with-no-argument, and
present-with-a-name-list — and the set of documented members must follow from
that shape, while the previously supported "omitted" and "no-argument" behaviors
are preserved unchanged.

Throughout, a *documented* member is one that carries a docstring (or is being
kept because undocumented members are also being requested). A member is
considered *public* when it is explicitly marked as public via its metadata
(e.g. a `:meta public:` field), even if its name begins with an underscore;
conversely a member may be marked private via its metadata (e.g.
`:meta private:`).

## Requirement 1: `:private-members:` accepts an explicit list of names

**User story:** As a documentation author, I want to pass specific member names
to `:private-members:`, so that I can document only one or two chosen private
members instead of all of them.

**Acceptance criteria**

1. The `:private-members:` option SHALL accept an optional argument that is a
   list of member names (the same comma-separated argument form already accepted
   by the `:members:` and `:special-members:` options), for both the
   `automodule` and `autoclass` directives.
2. WHEN documentation is generated for a module or class with `:private-members:`
   given an explicit list of names, THEN the system SHALL document every private
   member whose own name appears in that list.
3. WHEN documentation is generated with `:private-members:` given an explicit
   list of names, THEN the system SHALL NOT document any private member whose
   name is absent from that list.
4. IF a private member's name is in the supplied list but the member is only
   present because it was inherited from an ancestor that inherited-members
   filtering has been told to leave out, THEN the system SHALL still omit that
   member.
5. WHEN `:private-members:` names a member that is written into the generated
   output, THEN the system SHALL emit that member's full documentation block —
   its signature/definition line, its owning-module line, and its docstring
   text — just as it would for any other documented member.

## Requirement 2: omitting `:private-members:` documents no private members

**User story:** As a documentation author who has not asked for private members,
I want private members to stay out of the output, so that default documentation
only shows the public API.

**Acceptance criteria**

1. WHEN documentation is generated for a module or class and the
   `:private-members:` option is not supplied, THEN the system SHALL omit every
   member that is treated as private.
2. WHEN documentation is generated with `:members:` requested and
   `:private-members:` omitted, THEN the system SHALL still document a member
   that is explicitly marked public via its metadata (for example a member
   carrying a `:meta public:` field), even when that member's name begins with
   an underscore.
3. WHEN documentation is generated with `:members:` requested and
   `:private-members:` omitted, THEN the system SHALL omit a member that is
   private (for example a member carrying a `:meta private:` field or whose name
   begins with an underscore and is not marked public).

## Requirement 3: `:private-members:` with no argument documents all private members

**User story:** As a documentation author, I want `:private-members:` given
without any argument to keep documenting every private member, so that existing
projects that rely on the flag behavior continue to work.

**Acceptance criteria**

1. WHEN documentation is generated with `:private-members:` present but given no
   argument, THEN the system SHALL document all private members that are
   documented (or that are being kept because undocumented members were also
   requested), in addition to the public members.
2. WHEN `:members:` and an argument-less `:private-members:` are both requested
   for a module containing both a public-marked member and a private member,
   THEN the system SHALL document both members, each with its full documentation
   block (signature/definition line, owning-module line, and docstring).
3. The system SHALL preserve this argument-less behavior as equivalent to the
   prior all-private-members behavior, so that no project relying on the bare
   `:private-members:` option observes a change.

## Requirement 4: private-member decision is fully determined

**User story:** As a maintainer, I want the keep/drop decision for a private
member to be unambiguous for every combination of inputs, so that output is
deterministic and predictable.

**Acceptance criteria**

1. The system SHALL decide whether to keep a private member solely from: the
   shape of the `:private-members:` selection (omitted, all, or an explicit name
   list), the member's own name, whether the member is documented or
   undocumented-members are being kept, and whether the member is a
   left-out inherited member.
2. IF a private member is neither documented nor covered by a request to keep
   undocumented members, THEN the system SHALL omit it regardless of the
   `:private-members:` selection.
3. WHEN the `:private-members:` selection is "all", THEN the system SHALL keep a
   documented private member without regard to inherited-member filtering.
4. WHEN the `:private-members:` selection is an explicit list, THEN the system
   SHALL keep a documented private member exactly when its name is in the list
   and it is not a left-out inherited member.
