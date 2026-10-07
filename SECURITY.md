# Security Policy

tally's whole promise is exactness: the same program always produces the same
output and the same SHA-256 proof. A bug that breaks that promise is a
security issue, not a normal bug.

## Reporting a vulnerability

Please do not open a public issue for security problems.

- Email: corey@slidphilabs.com with the subject line `tally security`
- Or use GitHub's private vulnerability reporting on this repository
  (Security tab, "Report a vulnerability")

Include the program or input involved, steps to reproduce, and what you
expected versus what happened.

You can expect an acknowledgement within 3 business days. We will keep you
updated while we investigate and credit you in the changelog unless you prefer
to stay anonymous.

## In scope

- Proof divergence: two runs of the same program producing different digests
- Trace forgery: a modified execution that still produces a pinned proof
- Deterministic errors becoming non-deterministic (same program, different
  message across runs)
- Anything that lets a program read input, the clock, or randomness into the
  machine

## Out of scope

- Deployments of tally we do not run
- Social engineering, spam, or denial-of-service against anything hosting tally
