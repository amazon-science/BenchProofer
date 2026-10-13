# Requirements: Extensible per-item serialization in the admin autocomplete JSON view

## Introduction

The Django admin provides an AJAX endpoint that answers autocomplete lookups for
foreign-key and many-to-many fields backed by autocomplete widgets. This endpoint
is implemented by `AutocompleteJsonView` in
`django/contrib/admin/views/autocomplete.py`. Its `get()` method validates the
request, runs the search query, and returns a `JsonResponse` whose body contains a
`results` list (one entry per matched object) and a `pagination` object reporting
whether more result pages exist.

Today the conversion of each matched model object into its `results` entry is
hard-coded inline inside `get()`. Consumers who want to add extra attributes to
each entry (for richer, data-driven admin widgets) have no choice but to override
the entire `get()` method, duplicating request validation, permission checks,
querying, and response assembly. That duplicated code drifts out of sync as
`get()` evolves.

The goal is to introduce a dedicated, overridable extension point that converts a
single matched object into its `results` entry, and to have `get()` use that
extension point for every object. This lets subclasses customize an entry by
overriding one small method instead of the whole request handler, while leaving
the endpoint's observable behavior unchanged for the default (non-overriding)
case.

## Requirement 1: Dedicated per-object serialization extension point

**User story:** As a developer subclassing the admin autocomplete view, I want a
single small method that turns one matched object into its response entry, so that
I can add extra fields without reimplementing the whole request handler.

**Acceptance criteria**

1. The system SHALL provide, on `AutocompleteJsonView`, an instance method that
   accepts a single matched model object together with the resolved target field
   name and returns the dictionary representing that object's entry in the
   `results` list.
2. WHEN this method is invoked with a matched object and the resolved target field
   name, THEN it SHALL return a dictionary whose `id` key is the string form of
   the object's attribute named by the resolved target field name, and whose
   `text` key is the string form of the object.
3. The system SHALL expose this method as an overridable instance method (bound to
   `self`), so that a subclass can override it to change or extend the returned
   dictionary.
4. WHEN a subclass overrides this method to add additional keys to the returned
   dictionary (for example by merging extra keys onto the base dictionary), THEN
   those additional keys SHALL appear in the corresponding `results` entries of
   the endpoint response, alongside the default `id` and `text` keys.

## Requirement 2: `get()` builds results through the extension point

**User story:** As a maintainer, I want the request handler to delegate per-object
entry construction to the extension point, so that overriding that one method is
sufficient to customize every entry.

**Acceptance criteria**

1. WHEN `get()` assembles the `results` list, THEN it SHALL produce one entry per
   object in the current page's object list by invoking the per-object
   serialization extension point (Requirement 1) on `self` for each object, rather
   than constructing the entry dictionary inline.
2. The system SHALL preserve the order of `results` entries to match the order of
   the objects in the current page's object list.
3. IF the extension point is overridden on the view instance, THEN `get()` SHALL
   use the overriding implementation for every object (the dispatched method, not
   a fixed inline construction), so that customization takes effect uniformly.

## Requirement 3: Unchanged default response contract

**User story:** As an existing consumer of the autocomplete endpoint, I want the
response format to stay exactly the same when no customization is applied, so that
the refactor is risk-free.

**Acceptance criteria**

1. WHEN a valid autocomplete request is handled and the extension point is not
   overridden, THEN the response body SHALL be a JSON object with a `results` key
   and a `pagination` key, where `results` is a list of entries each containing
   exactly the `id` and `text` keys.
2. WHEN a valid autocomplete request is handled, THEN the `pagination` object's
   `more` value SHALL be the boolean reporting whether the current page has a
   following page.
3. WHEN a valid autocomplete request is handled, THEN the response SHALL be
   returned as a JSON HTTP response with status code 200.
4. The system SHALL keep each entry's `id` value as the string form of the
   object's attribute named by the resolved target field name, so that custom
   `to_field` resolution continues to determine the `id` value.

## Requirement 4: Preserve request validation, permission, and query behavior

**User story:** As a site administrator, I want the endpoint to keep all of its
existing validation, permission, and querying guarantees after the refactor, so
that security and correctness are not weakened.

**Acceptance criteria**

1. WHEN a request omits the required `app_label`, `model_name`, or `field_name`
   query parameters, or names an app/model that cannot be resolved, or names a
   field that does not exist or has no related model, or targets a related model
   that is not registered with the admin site, THEN the system SHALL raise a
   permission-denied error.
2. IF the requesting user lacks view permission for the related model, THEN the
   system SHALL raise a permission-denied error and SHALL NOT return results.
3. IF the resolved target field is not allowed as a `to_field` for the related
   model admin, THEN the system SHALL raise a permission-denied error.
4. WHEN the target model admin defines no search fields, THEN the system SHALL
   raise an HTTP 404 error rather than returning results.
5. The system SHALL resolve the target field name from the source field's remote
   field (falling back to the related model's primary key attribute name) and use
   that resolved name both to select the object attribute for the `id` value and
   as the argument passed to the per-object serialization extension point.
6. The system SHALL keep building the queryset from the model admin's queryset,
   applying the source field's limit-choices-to filter, applying the model admin's
   search results for the search term, and applying `distinct()` when the search
   indicates it is required.
7. The system SHALL keep paginating results using the model admin's paginator and
   the view's page size, so that paginated searches continue to report the correct
   `more` flag.
