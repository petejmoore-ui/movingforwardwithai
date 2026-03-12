# build.md
## Build Protocol for This Repository

---

## 0. Status of This File

This file is **authoritative**.

If build.md conflicts with:
- README
- comments
- docs
- intuition
- speed
- convenience

**build.md wins.**

If you are an AI model, treat this file as a **hard system rule**.
If you are a human, treat this file as a **professional contract**.

---

## 1. Purpose

This repository is built under a **disciplined engineering protocol**.

Code is not allowed to appear before intent.
Changes are not allowed without structure.
Speed is never allowed to override correctness.

This protocol exists to:
- prevent architecture drift
- prevent silent complexity
- prevent local optimizations that harm the system
- force clarity before implementation
- keep the codebase evolvable over years, not weeks

---

## 2. The Only Allowed Build Sequence

Every change MUST follow this order.  
No steps may be skipped.

### Step 1 — Understand
You must explicitly identify:
- what already exists
- where similar logic already lives
- what abstractions are already present
- what contracts already exist

If you cannot explain this in writing, you do not understand the system yet.

### Step 2 — Plan
Before writing code, you MUST write a plan that includes:
- files to touch
- new files (if any)
- functions/classes to add or modify
- data flow changes
- failure cases
- test strategy

If you are an LLM, output the plan first and wait for confirmation.

### Step 3 — Test (Design)
You must define how correctness will be verified:
- unit tests
- integration tests
- invariants
- assertions
- monitoring signals

If something cannot be tested, you must explain why.

### Step 4 — Implement
Only now may code be written.

Rules:
- prefer extending existing modules over creating new ones
- no duplicate helpers
- no “temporary” hacks
- no commented-out code
- no unused abstractions
- no silent behavior changes

### Step 5 — Refactor
After implementation:
- remove duplication
- simplify logic
- rename unclear symbols
- reduce surface area
- align with architecture boundaries

Refactoring is not optional. It is part of finishing.

### Step 6 — Document
Every non-obvious decision MUST be documented:
- why this abstraction exists
- why this boundary matters
- why alternatives were rejected

Docs are short, local, and factual.

### Step 7 — Verify
Before considering work done:
- tests pass
- code is readable
- no unused paths exist
- build is deterministic
- behavior matches plan

Only after verification is the change considered complete.

---

## 3. Architecture Discipline

### 3.1 Layer Boundaries Are Law

This repo follows strict layering:
- ingestion / perception
- processing / compression
- synthesis / outputs
- orchestration / scheduling
- storage / persistence

Code MUST live in the correct layer.
Cross-layer shortcuts are forbidden.

### 3.2 Reuse Before Create

Before adding a new module, you MUST prove:
- no existing module can be extended
- no existing abstraction fits
- no refactor would make reuse possible

If reuse is possible, creation is illegal.

### 3.3 Data Flows Are Explicit

Data must flow through named structures.
No anonymous dicts.
No implicit coupling.
No magic fields.

If data shape changes, the contract must change explicitly.

---

## 4. Rules for LLMs (Opus 4.5 Specific)

If you are an LLM working in this repo:

- Never write code before a plan
- Never modify more files than planned
- Never invent new architecture without justification
- Never skip tests
- Never inline large logic without naming it
- Never copy patterns from other repos blindly
- Never assume missing structure — ask or stop

If information is missing:
1. Stop
2. State what is missing
3. Propose the smallest assumption
4. Wait for confirmation

You are not an autocomplete.
You are a disciplined engineer.

---

## 5. What “Done” Means

A change is only “done” when:

- it follows the build sequence
- tests exist or are explicitly waived
- code is readable by a stranger
- behavior is documented
- no TODOs remain
- no dead paths exist
- the architecture is still simpler than before

If any of these fail, the change is incomplete.

---

## 6. When to Extend vs Refactor

### Extend when:
- the abstraction is correct
- the boundary is clean
- complexity does not increase
- behavior is consistent

### Refactor when:
- logic is duplicated
- conditionals grow
- naming becomes vague
- responsibilities blur
- tests become hard to write

Refactoring is not a failure.
Avoiding it is.

---

## 7. Tests Are Part of the Feature

Code without tests is a draft.

Every meaningful change must include:
- at least one assertion of correctness
- at least one failure case
- at least one regression guard

Hope is not a strategy.
Tests are.

---

## 8. Changes That Are Explicitly Forbidden

- copy/paste abstractions
- silent behavior changes
- adding flags to avoid fixing design
- global state without justification
- skipping tests “for now”
- writing code without understanding existing code
- optimizing before measuring
- building features without verifying purpose

If you feel tempted to do any of these:
Stop.
Re-read this file.
Start again.

---

## 9. The Prime Directive

If you are ever unsure what to do:

**Make the system more understandable, not more clever.**

This repo optimizes for:
- long-term clarity
- correctness
- evolvability
- trust

Not for speed.
Not for vibes.
Not for demos.

---

## 10. Final Rule

If following this protocol feels slow,
that is the point.

This file exists to make bad code feel illegal
and good code feel inevitable.

---
