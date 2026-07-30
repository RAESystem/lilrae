# Contribute to LilRAE

LilRAE is the complete personal and local RAES backend. Changes should preserve
the line between RAES-owned portable contracts and LilRAE-owned concrete
backend behavior.

## Choose the right repository

Propose portable semantics, schemas, protocol changes, diagnostics, or
conformance behavior in [RAES](https://github.com/RAESystem/rae). Propose
concrete realization, readiness, host/runtime security, rollback, teardown, and
backend-owned diagnostics here.

The backend is being generalized and migrated from `Brad-Edwards/aptl`.
Preserve useful history and behavior while keeping TechVault-specific packs,
plugins, MCPs, and research apparatus outside the generic core. Do not create a
parallel greenfield runtime for capability that should migrate.

Open an issue before adding a public capability or changing the execution
boundary. Keep unrelated work in separate pull requests.

## Branch and release workflow

1. Create a branch from `dev`.
2. Add tests before executable behavior.
3. Run focused tests while iterating and `make verify` before review.
4. Use a Conventional Commit pull-request title such as `feat:` or `fix:`.
5. Open the pull request against `dev`.

Only a reviewed same-repository `dev` pull request promotes to `main`. Release
Please owns the committed version, generated changelog, tag, and GitHub Release.
Its release commit returns through a reviewed `main` to `dev` pull request.

While LilRAE has no real backend, the Release Please pull request must not be
merged. Package-index publication is intentionally not configured.

## Verification graph

The canonical full gate is:

```shell
make verify
```

Useful focused commands are:

```shell
make test
make lint
make policy
```

`make policy` enforces the released RAES dependency boundary and cross-service
identity. Do not weaken it with a local environment option, test-only path
override, or CI-specific exception.

## Coding standards

- Support Python 3.11 and 3.12 and keep strict typing green.
- Prefer the standard library and existing RAES public contracts over new
  abstractions.
- Keep functions focused and diagnostics deterministic.
- Never print credentials, credential-bearing URLs, environment dumps, native
  payloads, or unredacted backend output.
- Do not add compatibility aliases, speculative backend registries, copied
  RAES models, or a second verification path.
- Do not edit `CHANGELOG.md`; Release Please owns it.

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
