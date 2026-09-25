# Code Review Process

## Pull Request Requirements

Every pull request must link to a tracking ticket and include a description of what changed and why.
All existing automated tests must pass, and new functionality requires new tests covering the happy
path and at least one edge case. PRs that only refactor existing code without behavior changes may
skip the new-test requirement but must still pass the existing suite.

## Reviewer Approvals

A pull request requires a minimum of two reviewer approvals before it can merge: at least one from a
senior engineer on the team, and at least one from someone outside the immediate feature team when the
change touches shared infrastructure or public APIs. Branch protection rules on `main` enforce this
automatically and block merges until both approvals are recorded.

## CI and Static Analysis Gates

Continuous integration must pass before merge, including unit tests, linting, and static security
scanning. A failing CI run blocks merge regardless of review approvals. Flaky tests should be fixed or
quarantined, not repeatedly re-run to force a pass.

## Review Turnaround and Escalation

Reviewers are expected to provide initial feedback within 24-48 business hours of a PR being opened.
If a PR sits without review past 48 hours, the author should ping the team channel; if it remains
stale past 5 business days, it should be escalated to the engineering manager. Authors are expected to
respond to review comments within one business day to keep review cycles moving.
