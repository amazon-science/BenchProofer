#!/usr/bin/env python3
"""G-AX — validate the one nontrivial behavioral fact the model relies on, against
the REAL repo callees (`django.db.backends.ddl_references`).

There is NO consumed `axiom <callee>_prop` in the bundle (the axioms region is
empty; the reference objects are modeled deeply as Lean structures). This check
validates the single A-reference fact (refinement.md): the bug mechanism that the
model `TableId.matchesName (.wrapped _) _ = false` encodes —

    a Columns reference whose stored `table` is a Table OBJECT never reports
    `references_column(<string>, col) == True`, whereas one whose stored `table`
    is the bare STRING does.

We run the real `Columns` / `Table` over boundary + fuzz inputs and assert:
  (1) wrapped-object table  ⇒ references_column(s, col) is False for every query
      (matches `TableId.wrapped` → `matchesName = false`);
  (2) bare-string table     ⇒ references_column(s, col) == (s == table and
      col in columns)  (matches `TableId.name`);
  (3) references_table(s) holds for a Table(s, ...) object iff s == its name
      (the table-part model).

stdlib-only (+ in-tree django import). exit 0 iff sound.
"""
import sys


def quote_name(s):
    return s


def main() -> int:
    from django.db.backends.ddl_references import Table, Columns

    tables = ["t", "t2", "schema_author", ""]
    colsets = [["name"], ["name", "age"], ["a", "b", "c"]]
    queries_t = ["t", "t2", "other", "schema_author", ""]
    queries_c = ["name", "age", "a", "missing", ""]

    checked = 0
    for table in tables:
        for columns in colsets:
            # (1) PRE-PATCH shape: store a Table OBJECT as the columns' table.
            wrapped = Columns(Table(table, quote_name), list(columns), quote_name)
            # (2) POST-PATCH shape: store the bare string.
            bare = Columns(table, list(columns), quote_name)
            for qt in queries_t:
                for qc in queries_c:
                    # (1) wrapped object never matches a string query.
                    if wrapped.references_column(qt, qc) is not False:
                        print(f"UNSOUND: wrapped Columns matched references_column"
                              f"({qt!r},{qc!r}) table={table!r} cols={columns!r}")
                        print("status=fail")
                        return 1
                    # (2) bare string matches the structural predicate exactly.
                    want = (table == qt) and (qc in columns)
                    got = bool(bare.references_column(qt, qc))
                    if got != want:
                        print(f"UNSOUND: bare Columns references_column({qt!r},{qc!r})"
                              f"={got} want={want} table={table!r} cols={columns!r}")
                        print("status=fail")
                        return 1
                    checked += 1
                # (3) table-part model: Table(table,...).references_table.
                tref = Table(table, quote_name)
                if bool(tref.references_table(qt)) != (table == qt):
                    print(f"UNSOUND: Table.references_table({qt!r})!=({table!r}=={qt!r})")
                    print("status=fail")
                    return 1

    print(f"checked={checked} all observations meet the modeled properties")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
