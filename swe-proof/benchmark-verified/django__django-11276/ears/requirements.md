# Requirements — HTML escaping in `django.utils.html`

## Introduction

`django.utils.html.escape()` is Django's core HTML-escaping helper: it converts
the HTML-significant characters in a text value into their character-reference
forms so the value can be embedded safely in HTML output. It is invoked heavily
during template and form rendering, so its output text is observable throughout
the framework (form widgets, form/field error and help rendering, the admin,
the technical debug/exception report, template filters such as `addslashes`,
`title`, `make_list`, and the `url` template tag output).

Historically `escape()` maintained its own per-character translation table and
`django.utils.html.urlize()` carried a private, ad-hoc unescaping helper that
reversed only five hard-coded HTML entities. Both duplicated behavior that the
Python standard library already provides (`html.escape()` and
`html.unescape()`).

The goal of this change is to make `escape()` produce escaping that is
consistent with the Python standard library escaper and to make `urlize()`
recover the original characters of an HTML-escaped URL using a full,
standards-based HTML entity decoder. The single externally visible behavioral
change is that the apostrophe/single-quote character is now emitted as the
hexadecimal numeric character reference rather than the legacy decimal one; all
other escaping outputs are unchanged. This document specifies the observable
behavior that must hold after the change and the pre-existing behavior that must
be preserved.

The affected module is `django/utils/html.py`; the affected callables are the
module-level `escape(text)` function and the `urlize(...)` function (its internal
URL-decoding step).

---

## Requirement 1: Escape the single-quote as a hexadecimal numeric reference

**User story:** As a Django template/form author, I want the escaping helper to
encode the single-quote character the same way the standard library does, so
that escaped output is consistent with the wider ecosystem and any code or tests
comparing against the standard form agree.

**Acceptance criteria**

1. WHEN `django.utils.html.escape(text)` is called with a text value that
   contains one or more single-quote (`'`, U+0027) characters, THEN `escape`
   SHALL replace each single-quote occurrence with the exact literal sequence
   `&#x27;`.
2. The system SHALL NOT emit the legacy decimal form `&#39;` for the
   single-quote character from `escape`.
3. WHEN the input contains multiple single-quote characters, THEN `escape` SHALL
   replace every occurrence (not only the first), each with `&#x27;`.

---

## Requirement 2: Preserve the escaping of the other HTML-significant characters

**User story:** As a maintainer relying on Django's autoescaping for XSS safety,
I want the ampersand, angle brackets, and double-quote to keep escaping exactly
as before, so that the change is limited to the single-quote form and no safety
regression is introduced.

**Acceptance criteria**

1. WHEN `escape(text)` is called with a text containing an ampersand (`&`), THEN
   `escape` SHALL replace each ampersand with the literal sequence `&amp;`.
2. WHEN the input contains a less-than sign (`<`), THEN `escape` SHALL replace
   each occurrence with the literal sequence `&lt;`.
3. WHEN the input contains a greater-than sign (`>`), THEN `escape` SHALL replace
   each occurrence with the literal sequence `&gt;`.
4. WHEN the input contains a double-quote (`"`, U+0022), THEN `escape` SHALL
   replace each occurrence with the literal sequence `&quot;`.
5. The system SHALL leave every character that is not one of `&`, `<`, `>`, `"`,
   or `'` unchanged in the output.

---

## Requirement 3: Ampersand-first ordering and stability of escaped output

**User story:** As a developer, I want escaping to be well-defined and stable so
that already-produced entity text is not corrupted and results are predictable.

**Acceptance criteria**

1. WHEN a character is replaced, THEN `escape` SHALL insert replacement text that
   is composed only of literal ASCII characters, such that the ampersands
   introduced by the replacements are themselves not re-escaped a second time
   within the same call.
2. The system SHALL produce output equivalent to performing the ampersand (`&`)
   substitution first, so that the `&` characters in the resulting entity
   sequences (`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&#x27;`) are never doubled into
   `&amp;...`.
3. WHEN `escape` is called on an empty text, THEN `escape` SHALL return an empty
   result.
4. WHEN `escape` is applied to text that already contains entity sequences, THEN
   `escape` SHALL escape the ampersands of those existing sequences again
   (`escape` always escapes its input; callers needing conditional behavior use a
   separate helper), i.e. it SHALL NOT attempt to detect pre-escaped content.

---

## Requirement 4: Accept non-string inputs by coercing to text, and return a safe-marked result

**User story:** As a caller passing arbitrary values (numbers, model instances,
lazy strings) into templates, I want `escape` to handle them without error and
to return a value that the template layer treats as already-safe.

**Acceptance criteria**

1. WHEN `escape` is called with a value that is not a `str`, THEN `escape` SHALL
   first convert the value to its string form and then apply the escaping rules
   in Requirements 1–3 to that string form.
2. The system SHALL return a result that is marked as HTML-safe (so that the
   template autoescaping layer does not escape it a further time).
3. WHILE `escape` is applied to a lazy/deferred text value, the system SHALL
   preserve its lazy-evaluation behavior, returning a value that escapes to the
   same result when finally rendered.

---

## Requirement 5: `urlize` recovers original URL characters via full HTML entity decoding

**User story:** As a template author using the `urlize` filter, I want
HTML-escaped URLs inside text to be linked correctly, so that the generated
link targets use the real underlying characters even when the input contained
HTML entities.

**Acceptance criteria**

1. WHEN `urlize(text, ...)` processes a candidate word that is an HTML-escaped
   URL, THEN `urlize` SHALL decode HTML entities in that word before building the
   link target, so that `&amp;`, `&lt;`, `&gt;`, `&quot;`, and the single-quote
   entity (in both its decimal `&#39;` and hexadecimal `&#x27;` forms) are turned
   back into `&`, `<`, `>`, `"`, and `'` respectively.
2. The system SHALL use a standards-based HTML unescaping that recognizes the
   general set of named and numeric HTML entities, not only the five fixed
   entities the previous ad-hoc helper handled.
3. WHEN trailing punctuation is trimmed from a candidate word, THEN `urlize`
   SHALL decode entities before measuring/removing trailing punctuation so that
   semicolons that are part of an entity are not mistaken for trailing
   punctuation and stripped.

---

## Requirement 6: Preserve existing `urlize` linking, wrapping, and splitting behavior

**User story:** As a user of the `urlize` filter, I want all previously supported
URL-detection, punctuation-trimming, wrapping, and email behavior to keep
working, so that only the internal decoding mechanism changes and no
externally visible linking regression occurs.

**Acceptance criteria**

1. The system SHALL continue to convert `http://`, `https://`, `www.`-prefixed,
   and recognized top-level-domain links into clickable links as before.
2. The system SHALL continue to split words on whitespace, angle brackets, and
   quote characters, and SHALL continue to trim leading/trailing and balanced
   wrapping punctuation from candidate words as before.
3. The system SHALL continue to apply URL truncation (when a length limit is
   given), the `nofollow` attribute (when requested), and autoescaping of link
   text (when requested) exactly as before.
4. WHEN a candidate word looks like a bare email address, THEN `urlize` SHALL
   continue to produce a `mailto:` link as before.
5. The system SHALL keep the produced link markup and text identical to the prior
   behavior for all inputs that contain no HTML-entity sequences.

---

## Requirement 7: Preserve downstream rendering that depends on escaped output

**User story:** As a maintainer, I want the framework components that render
escaped user text — form widgets and form/field error and help output, the
admin's model/method documentation, template filters, the `url` template tag
output, and the technical debug/exception report — to keep functioning, with
the only change being the single-quote entity form.

**Acceptance criteria**

1. The system SHALL keep all rendered HTML produced through `escape` byte-for-byte
   identical to the prior behavior EXCEPT that any single-quote character now
   appears as `&#x27;` instead of `&#39;`.
2. WHEN user-supplied text containing a single-quote is rendered in a form
   widget, a form/field error or help text, or the technical debug/exception
   report page, THEN the surrounding component SHALL render successfully and the
   single-quote SHALL appear as `&#x27;` in the escaped output.
3. The system SHALL keep the escaping of `&`, `<`, `>`, and `"` in all these
   rendering paths unchanged from the prior behavior.
