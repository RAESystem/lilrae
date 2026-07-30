# Security policy

## Report a vulnerability

Do not report suspected vulnerabilities through a public issue. Use
[GitHub private vulnerability reporting](https://github.com/RAESystem/lilrae/security/advisories/new).

Include the affected version or commit, reproduction steps, expected and actual
behavior, impact, and a minimal proof of concept when practical. Do not include
live credentials or sensitive native logs.

## Backend execution boundary

The current baseline does not execute a backend. It has no listener, subprocess,
container, VM, credential reader, runtime environment binding, persistence, or
host mutation. Its public command exposes help and version metadata only.

Future backend work is security-sensitive at the point where untrusted RAES
inputs meet concrete host effects. That boundary must validate published RAES
models before mutation; isolate process, container, network, and filesystem
effects; keep credentials out of arguments and logs; bound readiness and
timeouts; provide rollback and teardown; and redact native errors before
producing RAES-owned portable diagnostics.

Repository automation is also security-sensitive. Dependencies come only from
the approved registry, actions use immutable commit pins, workflow permissions
are least-privilege, and Sonar credentials are unavailable to fork code.

## Response expectations

LilRAE has one maintainer and no security response SLA. Reports are reviewed as
time allows. Avoid publishing exploit details until the maintainer has had a
reasonable opportunity to assess and mitigate the issue.
