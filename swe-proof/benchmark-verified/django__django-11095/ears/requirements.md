# Requirements: Customizable inline selection hook for ModelAdmin

## Introduction

The Django admin's `ModelAdmin` class (in `django/contrib/admin/options.py`)
builds the set of inline editors shown on a model's admin add/change page. The
list of inline classes to use is declared statically via the `ModelAdmin.inlines`
attribute, and `ModelAdmin.get_inline_instances(request, obj=None)` instantiates
each of those classes into inline instances (after applying view/change/add/
delete permission filtering).

Today, the only way to vary the inlines per-request or per-object is to override
`get_inline_instances` and re-implement its entire instantiation-and-permission
loop. This forces callers to duplicate framework logic they should not need to
touch.

The goal is to introduce a dedicated, overridable hook — `get_inlines(request, obj)`
— that returns the collection of inline classes to use, and to have
`get_inline_instances` source its inline classes from that hook rather than
reading the `inlines` attribute directly. This lets subclasses choose inlines
based on the request or the model instance by overriding a single small method,
with no change to the default behavior.

## Requirement 1: Inline-class selection hook

**User story:** As a developer customizing a `ModelAdmin`, I want a single hook
that returns the inline classes to use for a given request and object, so that I
can vary the inlines by request or instance without re-implementing the
instantiation loop.

**Acceptance criteria**
1. The system SHALL provide a method on `ModelAdmin` that accepts a request and a
   model object (the object being edited, or `None` on an add page) and returns
   the collection of inline classes to be used for that request/object.
2. WHEN the hook is called on a `ModelAdmin` that has not customized it, THEN the
   hook SHALL return the value of the instance's `inlines` attribute.
3. The system SHALL allow a `ModelAdmin` subclass to override this hook to return
   a different collection of inline classes, and the returned collection SHALL be
   the one that is subsequently used to build inline instances.

## Requirement 2: Inline instantiation sources classes from the hook

**User story:** As a developer, I want `get_inline_instances` to build its
instances from the selection hook, so that overriding the hook changes which
inlines appear.

**Acceptance criteria**
1. WHEN `get_inline_instances(request, obj)` is called, THEN it SHALL obtain the
   inline classes to instantiate by calling the selection hook with the same
   request and object, rather than reading the `inlines` attribute directly.
2. WHEN a subclass overrides the selection hook to return a particular collection
   of inline classes, THEN `get_inline_instances` SHALL instantiate exactly those
   classes, in the returned order, and no others.
3. WHEN the selection hook returns an empty collection for a given request/object,
   THEN `get_inline_instances` SHALL return an empty list of inline instances.
4. WHEN the selection hook returns a collection containing a single inline class,
   THEN `get_inline_instances` SHALL return a list whose corresponding element is
   an instance of exactly that inline class (its runtime type is that class).

## Requirement 3: Preserve existing instantiation and permission behavior

**User story:** As a maintainer, I want the existing behavior of
`get_inline_instances` and related admin machinery to be unchanged for callers
that do not customize the hook, so that this addition is backward compatible.

**Acceptance criteria**
1. The system SHALL keep the default set of inline instances identical to the
   prior behavior: for a `ModelAdmin` that does not override the hook, the inline
   instances built from `inlines` SHALL be the same as before this change.
2. WHILE a request is supplied to `get_inline_instances`, the system SHALL keep
   applying the existing per-inline permission filtering: an inline whose class
   grants none of view/change, add, or delete permission for the request/object
   SHALL be excluded from the returned instances.
3. WHILE a request is supplied, IF an inline does not grant add permission for the
   request/object, THEN the system SHALL keep setting that inline instance's
   maximum number of forms to zero.
4. The system SHALL keep each inline instance constructed from the admin's model
   and admin site, exactly as before.
5. The system SHALL keep `get_formsets_with_inlines` and the admin add/change
   views working with the inline instances produced through the hook, so that
   formsets continue to correspond to their inlines and existing add/edit/delete
   admin flows for models with inlines are unaffected.
