#!/usr/bin/env python3
"""tally test suite — gold outputs and pinned proofs.

Every example program has its expected stdout AND its expected SHA-256
execution proof pinned below. If any byte of output or any step of the
trace changes, the suite fails. That is the point.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tally import assemble, run, TallyError

HERE = os.path.dirname(os.path.abspath(__file__))

# program -> (expected stdout, expected proof, expected steps)
GOLD = {
    "add.tally": (
        "42\n",
        "99a3b380eeff2f095bf18f051063335b07bc05c0b0115d1d6c22c03ea32004c4",
        5,
    ),
    "fact.tally": (
        "3628800\n",
        "356ac55658a3df48ac9149f4f1e3d200e0c51f9a4cb48ddf4fec6ca2b50d64c6",
        93,
    ),
    "fib.tally": (
        "0\n1\n1\n2\n3\n5\n8\n13\n21\n34\n",
        "8d15b7bc0d9d00d0370b807d6ad79d870ddd839ba3c134a97bf174cd403a69e0",
        131,
    ),
    "hello.tally": (
        "Hi!\n",
        "60005e48da4604c3cd2c8aee5e48b506f6b76f16109a3036676af6dcd4ffdea1",
        9,
    ),
}

failures = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        failures.append(name)


def test_gold():
    print("gold programs (stdout + proof + steps):")
    for prog, (exp_out, exp_proof, exp_steps) in GOLD.items():
        with open(os.path.join(HERE, "examples", prog)) as f:
            code = assemble(f.read())
        out, proof, steps = run(code)
        check(f"{prog} stdout", out == exp_out, f"got {out!r}")
        check(f"{prog} proof", proof == exp_proof, f"got {proof}")
        check(f"{prog} steps", steps == exp_steps, f"got {steps}")


def test_determinism():
    print("determinism (two runs, same proof):")
    with open(os.path.join(HERE, "examples", "fib.tally")) as f:
        code = assemble(f.read())
    _, p1, _ = run(code)
    _, p2, _ = run(code)
    check("fib proof stable across runs", p1 == p2)


def test_errors():
    print("error cases (all deterministic TallyError):")
    cases = {
        "div by zero": "push 1\npush 0\ndiv\nhalt\n",
        "mod by zero": "push 1\npush 0\nmod\nhalt\n",
        "stack underflow": "add\nhalt\n",
        "unknown opcode": "frobnicate\nhalt\n",
        "unknown label": "jmp nowhere\nhalt\n",
        "bad integer": "push abc\nhalt\n",
        "emit out of range": "push 99999999\nemit\nhalt\n",
        "emit surrogate": "push 0xD800\nemit\nhalt\n",
        "duplicate label": "x:\nx:\nhalt\n",
    }
    for name, src in cases.items():
        try:
            run(assemble(src))
            check(name, False, "no error raised")
        except TallyError:
            check(name, True)
    # determinism of errors: same program, same message
    try:
        run(assemble("push 1\npush 0\ndiv\nhalt\n"))
    except TallyError as e1:
        try:
            run(assemble("push 1\npush 0\ndiv\nhalt\n"))
        except TallyError as e2:
            check("error messages deterministic", str(e1) == str(e2))


def test_semantics():
    print("semantics:")
    def ev(src):
        return run(assemble(src))[0]
    check("floored div", ev("push -7\npush 2\ndiv\nprint\nhalt\n") == "-4\n")
    check("floored mod", ev("push -7\npush 2\nmod\nprint\nhalt\n") == "1\n")
    check("eq", ev("push 3\npush 3\neq\nprint\nhalt\n") == "1\n")
    check("lt", ev("push 2\npush 3\nlt\nprint\nhalt\n") == "1\n")
    check("gt false", ev("push 2\npush 3\ngt\nprint\nhalt\n") == "0\n")
    check("jnz taken", ev("push 1\njnz yes\npush 0\nprint\nhalt\nyes:\npush 7\nprint\nhalt\n") == "7\n")
    check("comments ignored", ev("; hello\npush 1 ; trailing\nprint\nhalt\n") == "1\n")


if __name__ == "__main__":
    test_gold()
    test_determinism()
    test_errors()
    test_semantics()
    print()
    if failures:
        print(f"{len(failures)} FAILURES: {failures}")
        sys.exit(1)
    print("all green — tally never lies.")
