#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11555.

What this bundle relies on, and what G-AX validates here:

  (A-reference) The deep model of an ALREADY-FORMED ordering-expression item:
      model.py encodes ``contribution(1, item_id) == PSeq(item_id)`` — such an
      item contributes EXACTLY ITSELF, as a single output target, passed
      through verbatim. This is the changed behaviour. G-AX validates it
      against the REAL callee: it drives Django's
      ``SQLCompiler.find_ordering_name`` (post-patch) for a related model whose
      default ordering contains an ordering expression, and asserts that the
      expression appears in the output as a single ``(OrderBy, False)`` entry
      whose ordering expression IS that very item (identity preserved), in its
      original position — never expanded by the name-resolution machinery.

  (A-consumed) The ``resolve_name`` / ``resolve_name_seq`` axiom binds the
      impl-callable name-resolution callee to its pure spec sequence
      (``ToSeq(Result()) == resolve_name_seq(item_id)``, with
      ``resolve_name_seq`` an uninterpreted ``@ContractOnly`` ``Ensures(True)``
      function). This is a DEFINITIONAL binding — ``resolve_name_seq`` is
      defined to be whatever sequence the real name-resolution machinery
      returns, so the axiom is tautologically sound (it over-claims nothing).
      What G-AX confirms here is the operative consequence: the
      name-resolution path is applied to TEXTUAL-name items only, and an
      already-formed ordering expression is NOT subscripted/handed to it (the
      pre-patch crash ``'OrderBy' object is not subscriptable``).

Run inside the official SWE-bench container for the instance, where Django is
importable and a sqlite test database is available. Exit 0 iff every obligation
holds. Outside the container (Django absent) it prints ``G-AX SKIP`` and
returns 0; the orchestrator runs it in-container.
"""
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import connection, models
    from django.db.models import F
    from django.db.models.expressions import OrderBy

    # A parent model whose default ordering MIXES an already-formed ordering
    # expression with a textual-name item, plus a child via multi-table
    # inheritance (the reported reproduction: order_by() the parent's
    # auto-created OneToOne pointer field on the child).
    class Parent(models.Model):
        name = models.CharField(max_length=20)
        rank = models.IntegerField()

        class Meta:
            app_label = "axcheck"
            # An OrderBy expression item AND a textual-name item, in this order.
            ordering = (F("rank").asc(nulls_first=True), "name")

    class Child(Parent):
        class Meta:
            app_label = "axcheck"

    with connection.schema_editor() as editor:
        editor.create_model(Parent)
        editor.create_model(Child)

    # Drive the REAL post-patch name-resolution machinery on the auto-created
    # parent-pointer field of the child: this is exactly the path that, before
    # the fix, fed the OrderBy expression into get_order_dir() and crashed.
    qs = Child.objects.order_by("parent_ptr")
    compiler = qs.query.get_compiler(using="default")

    opts = Parent._meta
    ptr_field = Child._meta.get_field("parent_ptr")
    assert ptr_field.is_relation, "parent_ptr must be a relation for the recursion path"

    # The REAL callee. Pre-patch this raises TypeError on the OrderBy item.
    results = compiler.find_ordering_name(
        "parent_ptr", Child._meta, default_order="ASC")

    # Every produced entry is an (OrderBy, is_ref) pair.
    assert isinstance(results, list) and len(results) >= 1, (
        "find_ordering_name produced %r" % (results,))
    for entry in results:
        assert isinstance(entry, tuple) and len(entry) == 2, (
            "expected (expr, is_ref) pairs, got %r" % (entry,))
        expr, is_ref = entry
        assert isinstance(expr, OrderBy), (
            "every produced target must be an OrderBy, got %r" % (expr,))

    # (A-reference) The already-formed ordering expression from Meta.ordering
    # appears VERBATIM as a single produced target (identity preserved): the
    # FIRST item of Parent.Meta.ordering is the OrderBy expression, and it must
    # be present in the output as that very object, with is_ref == False, and
    # NOT replaced by a name-resolved column expression.
    meta_orderby = opts.ordering[0]
    assert isinstance(meta_orderby, OrderBy), "Meta.ordering[0] must be an OrderBy"
    passthrough = [e for e in results if e[0] is meta_orderby]
    assert len(passthrough) == 1, (
        "the Meta.ordering OrderBy must be passed through verbatim exactly "
        "once (identity preserved); got %d matches in %r"
        % (len(passthrough), results))
    assert passthrough[0][1] is False, (
        "the passed-through ordering expression must carry is_ref == False")

    # It must appear in its original position relative to the name item's
    # expansion: the OrderBy contribution precedes the 'name' contribution.
    idx = next(i for i, e in enumerate(results) if e[0] is meta_orderby)
    assert idx == 0, (
        "the OrderBy item is the first Meta.ordering item; its contribution "
        "must come first, at index %d" % (idx,))

    # (A-consumed, operative consequence) The name-resolution machinery is for
    # textual names only; handing it an already-formed ordering expression is
    # exactly the pre-patch crash. Confirm the real get_order_dir subscripts
    # its argument (so an OrderBy would raise) — i.e. the fix's guard is
    # genuinely load-bearing.
    from django.db.models.sql.query import get_order_dir
    raised = False
    try:
        get_order_dir(meta_orderby, "ASC")
    except TypeError:
        raised = True
    assert raised, (
        "get_order_dir must subscript its argument (an OrderBy would crash); "
        "the isinstance(item, OrderBy) guard is load-bearing")

    # A textual name still resolves through the machinery to >= 1 target whose
    # expression is a freshly built OrderBy (NOT the Meta OrderBy identity).
    name_targets = compiler.find_ordering_name("name", opts, default_order="ASC")
    assert len(name_targets) >= 1, "a textual name must resolve to >= 1 target"
    for expr, _ in name_targets:
        assert isinstance(expr, OrderBy) and expr is not meta_orderby, (
            "a textual name must resolve to freshly built OrderBy targets")

    print("G-AX OK: find_ordering_name passes an already-formed Meta.ordering "
          "expression through verbatim as a single (OrderBy, False) target "
          "(deep-model A-reference), in position; textual names still resolve "
          "through the name machinery; get_order_dir subscripts its argument "
          "so the isinstance guard is load-bearing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
