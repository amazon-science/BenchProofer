# Requirements: Preserve a parent's auto-generated alternate key when saving inlines

## Introduction

When Django's admin (or any code using inline formsets) renders a parent object
together with its related child rows, it builds a `BaseInlineFormSet` for the
children. While preparing each child form, `BaseInlineFormSet.add_fields` in
`django/forms/models.py` decides whether the parent instance's *linked key
attribute* (the field the child's foreign key points at) must be cleared so that
it is regenerated when the parent is saved.

The linked key is usually the parent's primary key, but a child foreign key can
instead point at an alternate field via `to_field`. When that alternate field
carries a `default` callable (for example a `UUIDField` with `default=uuid.uuid4`
that is `editable=False, unique=True`), the parent's value for it is meaningful
and must survive the save.

Before the fix, `add_fields` cleared the parent's linked key attribute to `None`
whenever the parent was being newly added and the linked key field had a default
— regardless of whether that field was the primary key and regardless of whether
submitted form data was present. As a result, adding a parent object together
with at least one child inline (so form data is present) wiped the parent's
auto-generated alternate key to `None`, and saving then failed with a null/
integrity error because the child's foreign key had nothing to point at.

The goal is to clear the parent's linked key attribute only when doing so is
safe — i.e. when it is the primary key (which is regenerated on save anyway) or
when there is no submitted form data — and otherwise to leave an auto-generated
alternate key untouched so it survives to be written and referenced by the
child rows. All other behavior of the "adding a new object" reset must be
preserved.

## Requirement 1: Keep a parent's auto-generated alternate key when form data is present

**User story:** As a developer registering a model whose primary-key-like field
is an alternate key with an auto-generating default (e.g. a `UUIDField` targeted
by a child's `ForeignKey(to_field=...)`), I want that value to be preserved when
I add the parent together with one or more inline children, so that the parent
saves successfully and the children can reference it instead of failing with a
null value.

**Acceptance criteria**

1. WHEN `BaseInlineFormSet.add_fields` prepares a child form for a parent
   instance that is being newly added, AND the child's foreign key targets an
   alternate field of the parent (a field other than the parent model's primary
   key) that carries a default, AND the child form carries submitted data, THEN
   `add_fields` SHALL leave the parent instance's linked key attribute unchanged
   (it SHALL NOT set it to `None`), so the auto-generated value is retained.
2. WHEN a parent object is added in an inline formset whose child foreign key
   targets such an alternate key with a default and submitted data is present,
   THEN the parent instance's linked key attribute SHALL retain its existing
   value at the point the child form fields are constructed, so that a
   subsequent save persists a non-null value for that field.

## Requirement 2: Still clear the linked key when clearing is safe

**User story:** As a maintainer, I want the parent's linked key attribute to
continue being cleared in the cases where clearing is correct, so that an
auto-generated primary key is regenerated on save and default-valued keys are
not persisted prematurely when there is no form data.

**Acceptance criteria**

1. WHEN `add_fields` prepares a child form for a parent instance that is being
   newly added, AND the linked key field is the parent model's primary key, AND
   that field has a default, THEN `add_fields` SHALL set the parent instance's
   linked key attribute to `None` so it is regenerated when the parent is saved.
2. WHEN `add_fields` prepares a child form for a parent instance that is being
   newly added, AND the linked key field has a default, AND the child form
   carries no submitted data, THEN `add_fields` SHALL set the parent instance's
   linked key attribute to `None` — this SHALL hold both when the linked key is
   the primary key and when it is an alternate (`to_field`) key.
3. The decision to clear the parent instance's linked key attribute SHALL be
   equivalent to: the parent is being newly added, AND the linked key field has
   a default, AND (the linked key field is the parent model's primary key OR the
   child form carries no submitted data). In every case where this combined
   condition does not hold, `add_fields` SHALL leave the attribute unchanged.

## Requirement 3: Preserve existing "adding a new object" behavior (regression protection)

**User story:** As a maintainer, I want every other branch of the parent-key
reset logic to behave exactly as before, so that removing the over-broad clear
does not regress primary-key handling, non-adding instances, or fields without a
default.

**Acceptance criteria**

1. IF the parent instance is not being newly added (it already exists / is not
   in the adding state), THEN `add_fields` SHALL leave the parent instance's
   linked key attribute unchanged, regardless of the field's default, whether it
   is the primary key, or whether form data is present.
2. IF the linked key field has no default, THEN `add_fields` SHALL leave the
   parent instance's linked key attribute unchanged, even when the parent is
   being newly added.
3. The choice of which field's default and identity are examined SHALL follow
   the existing resolution: the alternate field named by the relation's target
   `to_field` when the child foreign key targets a field other than the parent's
   primary key, and the parent model's primary key otherwise; and "is the
   primary key" SHALL be judged by comparing that field's attribute name to the
   parent model's primary key name.
4. WHEN `add_fields` completes, THEN it SHALL install the inline foreign-key
   form field for the child form as before, and SHALL modify only the parent
   instance's single linked key attribute (and no other attribute) when it
   performs a clear.
