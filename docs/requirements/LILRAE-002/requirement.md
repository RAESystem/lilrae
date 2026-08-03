---
id: LILRAE-002
title: "Govern the repository and release baseline"
status: DRAFT
type: CONSTRAINT
priority: MUST
wave: 1
created_at: 2026-07-30T03:46:45.929809Z
updated_at: 2026-07-30T03:46:45.929809Z
---

# LILRAE-002 — Govern the repository and release baseline

## Statement

LilRAE SHALL use one canonical verification graph and consistent public identities across its distribution, import package, CLI, GitHub repository, Ground Control project, SonarCloud project, and Release Please configuration. Feature pull requests SHALL target protected dev, only dev SHALL promote to protected main, and release automation SHALL remain publication-disabled until a real backend exists. The verification graph SHALL build the source distribution and wheel and smoke-test the installed wheel outside the source tree.

## Rationale

The empty repository needs an enforceable integration and promotion baseline without creating a placeholder backend release or allowing service configuration to drift.
