#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11095.

This bundle consumes NO @ContractOnly axioms: both modelled operations (the
selection hook and the materialisation of live editors) are modelled DEEPLY in
model.py. What G-AX validates here is the **A-reference** — that the deep model
faithfully captures the real Python semantics of the two cooperating
administration operations the patch defines/changes:

  (default hook) the selection hook, with no override, reports EXACTLY the
      configured collection in order — modelled by
        ToSeq(select_applicable_editors(...)) == ToSeq(self.configured)

  (materialisation) the materialisation builds one live editor per identifier
      reported by the SELECTION HOOK (not the configured collection directly),
      in the reported order, keeping exactly those whose access context grants
      the entry — modelled by
        ToSeq(materialize_editors(...)) == kept(reported, granted)
      with `reported` = the hook's report (NOT `configured`). When the hook is
      overridden to narrow/alter the report, the materialised editors track the
      report; reading the configured collection instead (the pre-patch bug)
      would ignore the override.

It executes the REAL Django ``ModelAdmin.get_inlines`` /
``ModelAdmin.get_inline_instances`` on:

  * the default ``ModelAdmin`` (the hook reports the configured ``inlines``,
    in order, and the materialised instances are one per configured inline);
  * a subclass overriding ``get_inlines`` to return narrowed subsets (the exact
    F2P scenario, ``test_get_inline_instances_override_get_inlines``): the
    materialised instances are of EXACTLY the reported classes, in order — the
    discriminating behaviour the deep model pins (built from the report, not
    from ``inlines``), and which the pre-patch code would get wrong.

Run inside the official SWE-bench container for the instance, where Django is
importable, WITH the gold patch applied (the base image has no ``get_inlines``).
Exit 0 (printing ``G-AX OK: … N observations``) iff every obligation holds.
SKIP (return 0) fires ONLY when ``import django`` itself raises ``ImportError``
(the check is run outside the container); a configuration or setup error is NOT
swallowed — it raises and the check exits non-zero, so a misconfiguration can
never masquerade as a pass. The orchestrator runs it in-container with gold.
"""
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        # Register only apps that ship in the official image. The test-model
        # twins use app_label="contenttypes" (an already-registered backend
        # app) so django.setup() succeeds without any bundle-local package.
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.admin",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def main():
    # SKIP is legitimate ONLY when Django itself cannot be imported (the check
    # is run outside the container). A configuration/setup error is NOT a skip:
    # let it raise so a future misconfiguration cannot masquerade as a pass.
    try:
        import django  # noqa: F401
    except ImportError as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not importable in this environment: %r" % (exc,))
        return 0

    _configure_django()
    from django.contrib import admin
    from django.contrib.admin.sites import AdminSite
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.contenttypes.admin import GenericTabularInline
    from django.db import models

    site = AdminSite()

    # Structural twins of the test's models (a host + a generic-related child).
    class Episode(models.Model):
        class Meta:
            app_label = "contenttypes"

    class Media(models.Model):
        content_type = models.ForeignKey(ContentType, models.CASCADE)
        object_id = models.PositiveIntegerField()
        content_object = GenericForeignKey()

        class Meta:
            app_label = "contenttypes"

    # Two distinct generic-inline editor classes (identity is what the test
    # observes via type(...)).
    class MediaInline(GenericTabularInline):
        model = Media

    class AlternateInline(GenericTabularInline):
        model = Media

    # A request whose user grants every permission (the F2P MockSuperUser): the
    # permission filter keeps every reported editor, so the observable is purely
    # the SOURCE the materialisation iterates.
    class MockSuperUser:
        def has_perm(self, perm, obj=None):
            return True

        def has_module_perms(self, app_label):
            return True

    class MockRequest:
        pass

    request = MockRequest()
    request.user = MockSuperUser()

    observations = 0

    def cls_seq(instances):
        return [type(i) for i in instances]

    # (default hook) get_inlines reports exactly the configured inlines in order,
    # and the default materialisation builds one editor per configured inline.
    class DefaultAdmin(admin.ModelAdmin):
        inlines = (AlternateInline, MediaInline)

    da = DefaultAdmin(Episode, site)
    assert list(da.get_inlines(request, None)) == [AlternateInline, MediaInline], (
        "default get_inlines must report the configured inlines in order")
    assert cls_seq(da.get_inline_instances(request)) == [AlternateInline, MediaInline], (
        "default get_inline_instances must materialise one editor per configured "
        "inline, in order")
    observations += 1

    # (materialisation tracks the hook) the exact F2P scenario: an override that
    # narrows the report depending on the request.
    class EpisodeAdmin(admin.ModelAdmin):
        inlines = (AlternateInline, MediaInline)

        def get_inlines(self, request, obj):
            if hasattr(request, "name"):
                if request.name == "alternate":
                    return self.inlines[:1]
                elif request.name == "media":
                    return self.inlines[1:2]
            return []

    ma = EpisodeAdmin(Episode, site)

    # empty report => no editors materialised (NOT the configured two).
    assert list(ma.get_inlines(request, None)) == [], "override (no name) must report []"
    assert ma.get_inline_instances(request) == [], (
        "materialisation read the configured inlines instead of the empty report "
        "(the pre-patch bug)")
    observations += 1

    for name, inline_class in (("alternate", AlternateInline), ("media", MediaInline)):
        request.name = name
        reported = list(ma.get_inlines(request, None))
        assert reported == [inline_class], (
            "override get_inlines(%r) must report exactly [%r]" % (name, inline_class))
        instances = ma.get_inline_instances(request)
        assert cls_seq(instances) == [inline_class], (
            "materialisation must build editors from the hook's report %r, not "
            "from the configured inlines %r (the pre-patch bug)"
            % (reported, list(ma.inlines)))
        # The discriminator: the report differs from the configured collection,
        # and the result tracks the report (not the configured collection).
        assert reported != list(ma.inlines), (
            "test scenario must exercise a report differing from the configured "
            "collection")
        observations += 1

    print("G-AX OK: deep model validated against the real "
          "ModelAdmin.get_inlines / get_inline_instances over %d observations; "
          "the default hook reports the configured inlines in order and "
          "materialisation builds editors from the hook's report (not the "
          "configured collection), tracking an overriding narrowed report."
          % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
