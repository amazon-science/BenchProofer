# Requirements: Preserve mixed-case app labels when deconstructing string model references

## Introduction

Relational model fields in Django (`ForeignKey`, `ManyToManyField`, and their
shared base `ForeignObject` in `django/db/models/fields/related.py`) can point at
their target model either by a concrete model class or by a *lazy string
reference*. A lazy reference may be written either as a bare model name
(e.g. `"Category"`) or as an app-qualified name of the form
`"<app_label>.<ModelName>"` (e.g. `"DJ_RegLogin.Category"`).

When a foreign-key or foreign-object field is serialized for a migration, its
`deconstruct()` computes the value stored under `kwargs['to']`. Historically,
when the target was given as a string, that path lowercased the *entire*
reference string. That is correct for a bare name, but for an app-qualified name
it also lowercases the app-label segment. App labels are case-sensitive; if an
application declares a mixed-case label (e.g. `DJ_RegLogin`), the lowercased
`to` value no longer matches the real app label. The migration then carries a
lazy reference to an app that "isn't installed", and building project state
(`makemigrations` / `migrate`) fails with a `ValueError`.

The behavioral change is confined to the foreign-key / foreign-object
deconstruct path. `ManyToManyField` deconstructs through its own override, which
stores a string target reference verbatim (it does not lowercase either segment)
both before and after this change; that behavior is unchanged and must not be
altered. The goal is that deconstructing a string model reference on the
foreign-key / foreign-object path preserve the app-label segment's letter case
verbatim while still normalizing the model-name segment, so that project state
built from deconstructed models resolves all lazy references and no reference is
dropped.

## Requirement 1: Normalize a qualified string reference on the foreign-key path without altering the app label

**User story:** As a developer whose app has a mixed-case app label, I want
migrations generated for my foreign-key fields to keep my app label's case
intact, so that migrating my project does not crash with a spurious "app isn't
installed" error.

**Acceptance criteria**

1. WHEN a foreign-key or foreign-object field's target model is given as an
   app-qualified string of the form `<app_label>.<model_name>` (an app-label
   segment and a model-name segment joined by a single `.` separator), THEN the
   deconstructed `to` value SHALL be composed of the app-label segment reproduced
   with its letter case unchanged, the `.` separator, and the model-name segment
   with all cased characters lowercased.
2. WHEN such a foreign-key/foreign-object target string is app-qualified and its
   app-label segment contains upper-case characters, THEN those upper-case
   characters SHALL remain upper-case in the deconstructed `to` value.
3. WHEN such a foreign-key/foreign-object target string is app-qualified and its
   model-name segment contains upper-case characters, THEN those characters SHALL
   appear lowercased in the deconstructed `to` value.
4. The deconstructed `to` value for an app-qualified string reference on the
   foreign-key/foreign-object path SHALL differ from the fully-lowercased form of
   the reference whenever the app-label segment contains any upper-case character.

## Requirement 2: Preserve existing normalization for bare, non-string, and many-to-many references

**User story:** As a Django maintainer, I want the previously working reference
forms to behave exactly as before, so that this change fixes the mixed-case case
without regressing any other reference form.

**Acceptance criteria**

1. WHEN a foreign-key or foreign-object field's target model is given as a string
   that contains no `.` separator, THEN the deconstructed `to` value SHALL be that
   string with all cased characters lowercased.
2. IF a foreign-key or foreign-object field's target model is not given as a
   string (i.e. it is a model class), THEN the deconstructed `to` value SHALL be
   that model's lower-cased label, exactly as before this change.
3. The foreign-key/foreign-object deconstruction SHALL continue to populate all
   other keyword arguments (such as `on_delete`, `from_fields`, `to_fields`, and
   any parent-link or swappable handling) exactly as it did prior to this change;
   only the normalization of an app-qualified string `to` value changes.
4. WHEN a many-to-many field's target model is given as a string reference
   (whether bare or app-qualified), THEN the deconstructed `to` value SHALL retain
   that string verbatim — neither the app-label segment nor the model-name segment
   is altered — exactly as before this change.

## Requirement 3: Project state resolves mixed-case references end to end

**User story:** As a developer, I want project state assembled from models that
reference each other through a mixed-case app label to be fully constructible, so
that every declared model is present and no lazy reference is left dangling.

**Acceptance criteria**

1. WHEN project state is built from a set of models that all share a mixed-case
   app label and that reference one another by both a foreign-key relation and a
   many-to-many relation, THEN rendering that state's application registry SHALL
   succeed without raising a lazy-reference error.
2. WHEN the application registry is rendered from such a set of models, THEN the
   number of models it reports SHALL equal the number of distinct models that
   were added to the project state.
3. WHEN the deconstructed forms of such mixed-case-app-label models are used to
   rebuild the project state, THEN every lazy reference (from either the
   foreign-key or the many-to-many relation) SHALL still name an app label whose
   letter case matches the declaring app, so that no reference is left dangling.
