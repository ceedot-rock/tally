# Contributing to tally

Thanks for helping keep the smallest honest machine honest.

## Ground rules

- tally is deterministic down to the byte: the same program always prints the
  same stdout and the same SHA-256 proof, on every machine, every run.
- Errors are deterministic too: division by zero, stack underflow, bad jumps,
  bad labels — same program, same message, every time.
- Integer math only, arbitrary precision. No floats, no clock, no randomness,
  no input.

## Quick check

```sh
python3 test_tally.py
```

CI runs the full suite plus an independent determinism check on every pull
request.

## Adding an opcode or changing the machine

1. Add the opcode to `tally.py` (assemble + run + the opcode table in the
   README).
2. Pin the new behavior as gold in `test_tally.py`: expected stdout, expected
   proof digest, expected step count.
3. If an existing program's trace changes by even one byte, its pins must be
   regenerated deliberately — run the suite, confirm the new pins by hand,
   and say so in the PR.
4. Open a pull request using the template.

## Examples

New examples go in `examples/` with a one-line description added to the
README's example list. Every example is covered by the gold pins in
`test_tally.py`.

## Licensing

tally is Apache-2.0. By contributing you agree your contribution may be
distributed under that license.
