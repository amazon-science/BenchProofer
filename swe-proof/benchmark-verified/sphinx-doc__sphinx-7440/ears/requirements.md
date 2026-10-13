# Requirements: Case-sensitive glossary terms

## Introduction

The documentation builder maintains a glossary of terms and lets authors
cross-reference those terms with an inline role. Glossary terms are registered
as cross-reference targets in the standard domain, and each term also produces a
general-index entry.

Historically the builder registered every glossary term under a case-folded
(all-lowercase) key, and the term cross-reference role also case-folded its
target before looking it up. As a consequence two glossary terms whose text
differed only in letter case (for example `MySQL` versus `mysql`) collapsed to a
single registered key: the second term was reported as a duplicate of the first
and could not be defined or linked independently. In addition, the key under
which a term was registered disagreed with the text shown in its index entry.

The goal is to treat glossary terms case-sensitively end to end: a term is
identified by its text with the exact characters preserved (including letter
case), both where it is registered/looked up and where it appears in the index.
The affected code lives in the standard domain module (`sphinx/domains/std.py`),
specifically the glossary-term construction routine (`make_glossary_term`) that
registers the term via `note_object` and builds the index entry, and the
declaration of the `term` cross-reference role.

## Requirement 1: Register glossary terms under a case-preserving key

**User story:** As a documentation author, I want two glossary terms that differ
only in letter case to be treated as distinct terms, so that entries like
`MySQL` and `mysql` can both be defined without one being rejected as a
duplicate of the other.

**Acceptance criteria**
1. WHEN a glossary term is processed by `make_glossary_term`, THEN the system
   SHALL register the term as a `term` object whose name is the term's text with
   all original characters preserved, without applying any letter-case folding.
2. IF two glossary terms have text that is identical after case folding but
   differs in actual letter case, THEN the system SHALL register them as two
   separate `term` objects and SHALL NOT report the second one as a duplicate of
   the first.
3. WHEN the registered `term` objects are enumerated, THEN each glossary term
   SHALL appear with a name equal to its original, case-preserved text.

## Requirement 2: Index entry matches the case-preserved term

**User story:** As a documentation reader, I want a glossary term to appear in
the general index exactly as it was written, so that the indexed text and the
term's registered identifier agree.

**Acceptance criteria**
1. WHEN `make_glossary_term` builds the general-index entry for a glossary term,
   THEN the indexed term text SHALL be the term's original, case-preserved text.
2. The system SHALL keep the index entry text and the term's registered object
   name equal to the same original, case-preserved term text (no case-folded
   variant for either).

## Requirement 3: Resolve term cross-references case-sensitively

**User story:** As a documentation author, I want a `term` cross-reference to
target the term text exactly as I wrote it, so that references to case-distinct
terms resolve to the correct definition.

**Acceptance criteria**
1. WHEN a `term` cross-reference is created, THEN the system SHALL use the
   reference target text as written and SHALL NOT case-fold it before resolving
   the target.
2. WHEN a `term` cross-reference is resolved against the registered glossary
   terms, THEN it SHALL match a term whose case-preserved name equals the
   reference target and SHALL NOT match a term that only agrees after case
   folding.

## Requirement 4: Preserve existing glossary parsing and diagnostics

**User story:** As a documentation author, I want the existing glossary
behaviors and warnings to remain unchanged, so that case sensitivity is the only
change in how glossaries are handled.

**Acceptance criteria**
1. WHEN a glossary defines the exact same term text more than once, THEN the
   system SHALL emit a duplicate-term warning identifying the term and the
   location of the other instance.
2. WHEN glossary terms are not separated correctly (for example an empty line
   between grouped terms, or a definition not preceded by an empty line before a
   term), THEN the system SHALL emit the corresponding glossary structure
   warning as before.
3. The system SHALL continue to support glossary entries that carry a classifier
   (a term followed by ` : classifier`), producing the term node from the term
   portion only.
4. The system SHALL continue to ignore glossary lines that are comments and
   SHALL continue to support the sorted-output option, preserving the previously
   established ordering and grouping of terms.
5. WHEN a single glossary definition is preceded by multiple term lines, THEN the
   system SHALL register each of those terms and attach them to the shared
   definition as before.
