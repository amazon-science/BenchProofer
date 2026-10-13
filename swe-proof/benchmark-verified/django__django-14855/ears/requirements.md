# Requirements: Correct admin-site namespace for readonly ForeignKey links

## Introduction

In Django's admin, when a model instance is viewed or edited and one of its
`ForeignKey` fields is listed in `readonly_fields`, the admin renders that field
as a hyperlink pointing at the related object's change page — provided the
related model is registered in the admin.

The markup for that link is produced by
`AdminReadonlyField.get_admin_url` in `django/contrib/admin/helpers.py`. It
builds a change-view route name from the related model's application label and
model name, then asks the URL resolver (`django.urls.reverse`) to turn that
route name plus the related object's primary key into a concrete URL, and wraps
the result in an anchor tag via `format_html`.

The defect: `get_admin_url` calls the resolver without telling it which admin
site is currently in effect. Admin URL patterns are namespaced per admin site,
so when the page is served by a custom (non-default) admin site, the resolver
falls back to the default `admin` namespace and produces a URL under the default
`/admin/…` prefix instead of the custom site's `/custom-admin/…` prefix. The
link therefore points into the wrong admin deployment.

The goal is that the generated link resolves under the namespace of the admin
site actually serving the page, for both the default admin site and any custom
admin site, while preserving all existing behavior of this method (route-name
construction, primary-key encoding, anchor markup, and the plain-text fallback).

## Requirement 1: Resolve readonly ForeignKey links against the current admin site

**User story:** As a developer who registers models on a custom-named admin
site, I want readonly ForeignKey fields to link to the related object's change
page on that same custom site, so that following the link keeps me within the
admin deployment I am using rather than jumping to the default admin site.

**Acceptance criteria**

1. WHEN `AdminReadonlyField.get_admin_url` resolves the change-view route for a
   related object, THEN it SHALL pass the name of the admin site associated with
   the current model admin to the URL resolver as the value that selects the
   current application/namespace instance.
2. The system SHALL derive that admin-site name from the model admin handling
   the current page (i.e. the model admin's associated admin site), not from a
   hard-coded or default admin site.
3. WHEN the readonly field is rendered on a page served by a custom (non-default)
   admin site whose URL patterns are namespaced under that site's name, THEN the
   generated link URL SHALL resolve under that custom site's namespace and URL
   prefix.
4. WHEN the readonly field is rendered on a page served by the default admin
   site, THEN the generated link URL SHALL resolve under the default admin
   namespace and URL prefix, exactly as before.
5. IF the related object's primary key is a string (or otherwise contains
   characters requiring URL encoding), THEN the resolved link URL SHALL use the
   URL-encoded form of that primary key, and the namespace-correct resolution of
   criterion 3 SHALL still apply.

## Requirement 2: Preserve existing link construction and fallback behavior

**User story:** As a Django maintainer, I want the change to affect only which
admin site's namespace is used, so that route-name construction, anchor markup,
and error handling continue to behave as before and no regressions are
introduced.

**Acceptance criteria**

1. The system SHALL build the change-view route name from the related model's
   application label and model name, targeting that model's admin change view,
   unchanged from the prior behavior.
2. WHEN the resolver successfully produces a URL, THEN `get_admin_url` SHALL
   return an anchor element whose destination is that URL and whose visible text
   is the related object's display representation.
3. IF the resolver cannot produce a URL for the route (no matching admin URL
   exists — e.g. the related model is not registered in the admin), THEN
   `get_admin_url` SHALL NOT raise, and SHALL instead return the related
   object's plain-text display representation with no anchor markup.
4. The system SHALL continue to render a readonly ForeignKey field as a link
   only when the related model is registered in admin, and as plain text
   otherwise, on both the default and custom admin sites.
5. The system SHALL leave the behavior of readonly ManyToMany references,
   reverse OneToOne references, and non-field/text readonly rendering unchanged.
