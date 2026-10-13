## The property-based test suite, in `rivals/`

$rivals_rules

`rivals/index.toml` lists every case, one table each:

```toml
[[rival]]
id = "uniqueness-1"
kind = "uniqueness"
expect = "refute"
file = "uniqueness-1$extension"
rationale = "the single reason this case is interesting, in one sentence"
```
$witness
