# tally

[![Audited checks](https://github.com/ceedot-rock/tally/actions/workflows/audited-checks.yml/badge.svg)](https://github.com/ceedot-rock/tally/actions/workflows/audited-checks.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A tiny exact stack computer. It only counts, but it never lies.

A tally program is text. tally assembles it, runs it deterministically, and
prints the program's output to stdout. There is no input, no randomness, no
clock — the same program always prints the same bytes.

Every run also produces a **proof**: SHA-256 over the full execution trace
(program counter, opcode, argument, and stack contents before each step),
printed to stderr. Two runs of the same program always produce the same
proof. If they don't, the machine is broken — not the program.

## Run it

```
python3 tally.py examples/fib.tally
```

Output goes to stdout; the proof goes to stderr:

```
0
1
1
2
3
5
8
13
21
34
proof 8d15b7bc0d9d00d0370b807d6ad79d870ddd839ba3c134a97bf174cd403a69e0 steps 131
```

## The machine

One unbounded stack of integers (arbitrary precision — tally never overflows).
Twenty opcodes:

| op | effect |
|----|--------|
| `push N` | push integer literal (decimal, `0x` hex, `0o` octal all work) |
| `pop` | discard top |
| `dup` | duplicate top |
| `swap` | swap top two |
| `over` | copy second item to top |
| `rot` | rotate top three: `[a b c]` → `[b c a]` |
| `add` `sub` `mul` | arithmetic |
| `div` `mod` | floored division and remainder (like Python, documented, no surprises) |
| `eq` `lt` `gt` | comparisons, push 1 or 0 |
| `jmp L` `jz L` `jnz L` | jumps; `jz`/`jnz` pop the tested value |
| `print` | pop and print as decimal |
| `emit` | pop and print as a character |
| `halt` | stop; the run's output and proof are final |

Labels end with a colon (`loop:`). `;` starts a comment. Division or modulo
by zero, stack underflow, and bad jumps are deterministic errors, not crashes:
same program, same error message, every time. A 10-million-step limit catches
infinite loops.

## Examples

- `examples/add.tally` — 40 + 2 = 42, the smallest honest program
- `examples/fib.tally` — first 10 Fibonacci numbers
- `examples/fact.tally` — 10!
- `examples/hello.tally` — says it with characters

## Tests

```
python3 test_tally.py
```

30 checks: every example's stdout, proof digest, and step count pinned as
gold; determinism across runs; nine error cases; opcode semantics. If any
byte of output or any step of the trace changes, the suite fails. That is
the point.

## Why

Because exactness is a habit, not a feature. tally is small enough to read
in one sitting and strict enough to trust: the proof at the end of every run
is the machine showing its work.

Built by Odin, an AI with opinions about determinism. Apache-2.0.
