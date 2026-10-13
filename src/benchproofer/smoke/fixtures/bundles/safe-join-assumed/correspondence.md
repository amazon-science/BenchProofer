# Where each obligation comes from

The task asks `safe_join` for the normalized join of an untrusted request onto a
directory, and for `None` when that join would land outside the directory. Three
obligations say what an accepted result is -- normalized, inside the root, and the place
the request actually pointed at -- and the fourth says that nothing else is refused,
which is what keeps a specification satisfied by refusing everything out of reach.

Normalizing is `posixpath.normpath`, which the `axioms` region models, so every
obligation that mentions where a request lands rests on that model. `axioms.py` is what
puts it to the real callee.

- `def property_an_accepted_path_is_normalized(root, relative):` -> `safe_join`, `paths.py`
- `assert all(part not in ("", ".", "..") for part in result.split("/"))` -> `normpath`, `posixpath.normpath`
- `def property_an_accepted_path_is_under_the_root(root, relative):` -> `safe_join`, `root`
- `assert under(root, result)` -> `escapes`, `root`
- `def property_an_accepted_path_is_where_the_request_points(root, relative):` -> `safe_join`, `relative`
- `assert result == resolve(root, relative)` -> `joined`, `normpath`
- `def property_a_request_is_refused_only_when_it_escapes(root, relative):` -> `safe_join`, `paths.py`
- `assert (impl(root, relative) is None) == escapes` -> `safe_join`, `relative`

The statement fixes `root` as a normalized relative directory, so the specification
draws only such roots and says nothing about what `safe_join` does with any other kind.
