#!/usr/bin/env python3
"""tally — a tiny exact stack computer.

A program is text. tally assembles it, runs it deterministically, and prints
the program's output to stdout. There is no input, no randomness, no clock:
the same program always prints the same bytes.

Every run also produces a *proof*: SHA-256 over the full execution trace
(pc, opcode, argument, and stack contents before each step), printed to
stderr. Two runs of the same program always produce the same proof.
If they don't, the machine is broken — not the program.

Usage:
    python3 tally.py program.tally
"""

import hashlib
import re
import sys

STEP_LIMIT = 10_000_000
LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class TallyError(Exception):
    """Any assembly or runtime failure. Deterministic: same program, same error."""


# ---------------------------------------------------------------- assembly

JUMPS = ("jmp", "jz", "jnz")


def assemble(src):
    """Assemble tally source text into a list of (op, arg) tuples."""
    code = []       # (op, arg_or_None, line_no)
    labels = {}
    for ln, raw in enumerate(src.splitlines(), 1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.endswith(":"):
            name = line[:-1].strip()
            if not LABEL_RE.match(name):
                raise TallyError(f"line {ln}: bad label {name!r}")
            if name in labels:
                raise TallyError(f"line {ln}: duplicate label {name!r}")
            labels[name] = len(code)
            continue
        parts = line.split()
        op, rest = parts[0].lower(), parts[1:]
        if len(rest) > 1:
            raise TallyError(f"line {ln}: too many arguments")
        code.append((op, rest[0] if rest else None, ln))

    resolved = []
    for op, arg, ln in code:
        if op in JUMPS:
            if arg is None:
                raise TallyError(f"line {ln}: {op} needs a label")
            if arg not in labels:
                raise TallyError(f"line {ln}: unknown label {arg!r}")
            resolved.append((op, labels[arg]))
        elif op == "push":
            if arg is None:
                raise TallyError(f"line {ln}: push needs an integer")
            try:
                resolved.append((op, int(arg, 0)))
            except ValueError:
                raise TallyError(f"line {ln}: bad integer {arg!r}")
        elif op in OPS:
            if arg is not None:
                raise TallyError(f"line {ln}: {op} takes no argument")
            resolved.append((op, None))
        else:
            raise TallyError(f"line {ln}: unknown opcode {op!r}")
    return resolved


# ---------------------------------------------------------------- execution

def _need(stack, n, op):
    if len(stack) < n:
        raise TallyError(f"stack underflow in {op}: need {n}, have {len(stack)}")


def run(code):
    """Execute assembled code. Returns (output_text, proof_hex, steps)."""
    stack = []
    out = []
    pc = 0
    steps = 0
    h = hashlib.sha256()

    def trace(op, arg):
        h.update(str(pc).encode())
        h.update(b"|" + op.encode())
        h.update(b"|" + (str(arg).encode() if arg is not None else b""))
        h.update(b"|" + repr(stack).encode() + b"\n")

    n = len(code)
    while True:
        if pc < 0 or pc >= n:
            raise TallyError(f"pc {pc} out of bounds (0..{n - 1})")
        op, arg = code[pc]
        trace(op, arg)
        steps += 1
        if steps > STEP_LIMIT:
            raise TallyError(f"step limit {STEP_LIMIT} exceeded (infinite loop?)")

        if op == "push":
            stack.append(arg)
        elif op == "pop":
            _need(stack, 1, op); stack.pop()
        elif op == "dup":
            _need(stack, 1, op); stack.append(stack[-1])
        elif op == "swap":
            _need(stack, 2, op); stack[-1], stack[-2] = stack[-2], stack[-1]
        elif op == "over":
            _need(stack, 2, op); stack.append(stack[-2])
        elif op == "rot":
            _need(stack, 3, op)
            c = stack.pop(); b = stack.pop(); a = stack.pop()
            stack.extend((b, c, a))
        elif op in ("add", "sub", "mul", "div", "mod"):
            _need(stack, 2, op)
            b = stack.pop(); a = stack.pop()
            if op == "add":
                stack.append(a + b)
            elif op == "sub":
                stack.append(a - b)
            elif op == "mul":
                stack.append(a * b)
            elif op == "div":
                if b == 0:
                    raise TallyError("division by zero")
                stack.append(a // b)   # floored, like the program says
            else:
                if b == 0:
                    raise TallyError("modulo by zero")
                stack.append(a % b)    # floored, matches div
        elif op in ("eq", "lt", "gt"):
            _need(stack, 2, op)
            b = stack.pop(); a = stack.pop()
            stack.append(1 if (a == b if op == "eq" else a < b if op == "lt" else a > b) else 0)
        elif op == "jmp":
            pc = arg
            continue
        elif op == "jz":
            _need(stack, 1, op)
            v = stack.pop()
            if v == 0:
                pc = arg
                continue
        elif op == "jnz":
            _need(stack, 1, op)
            v = stack.pop()
            if v != 0:
                pc = arg
                continue
        elif op == "print":
            _need(stack, 1, op)
            out.append(str(stack.pop()) + "\n")
        elif op == "emit":
            _need(stack, 1, op)
            v = stack.pop()
            if not 0 <= v < 0x110000 or 0xD800 <= v < 0xE000:
                raise TallyError(f"emit: {v} is not a valid character code")
            out.append(chr(v))
        elif op == "halt":
            return "".join(out), h.hexdigest(), steps
        else:  # pragma: no cover — assembler rejects unknown ops
            raise TallyError(f"bad opcode {op!r}")
        pc += 1


OPS = frozenset((
    "pop", "dup", "swap", "over", "rot",
    "add", "sub", "mul", "div", "mod",
    "eq", "lt", "gt",
    "print", "emit", "halt",
))


def main(argv):
    if len(argv) != 2:
        print("usage: tally.py program.tally", file=sys.stderr)
        return 2
    try:
        with open(argv[1], "r", encoding="utf-8") as f:
            src = f.read()
        code = assemble(src)
        output, proof, steps = run(code)
    except (TallyError, OSError, UnicodeDecodeError) as e:
        print(f"tally: error: {e}", file=sys.stderr)
        return 1
    sys.stdout.write(output)
    print(f"proof {proof} steps {steps}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
