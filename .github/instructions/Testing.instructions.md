---
description: 'Use these guidelines when generating or updating tests.'
applyTo: tests/**
---
# Testing Guidelines

## Test conventions

* Write clear, focused tests that verify one behavior at a time.
* Use descriptive test names that explain the expected result.
* Follow the Arrange-Act-Assert pattern.
* Keep tests independent and repeatable.
* Start with the simplest case, then add edge cases and failure paths.
* Mock external dependencies when they would make tests slow or flaky.

## Repository-specific guidance

* Prefer tests that validate scripts, hooks, or generated assets end to end when possible.
* Keep fixture data small and easy to read.
* Document any manual verification steps when full automation is not practical.