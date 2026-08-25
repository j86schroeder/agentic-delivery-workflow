# Agentic Delivery Workflow

A practical example of AI-assisted software delivery using a coding agent inside a real GitHub repository.

This repository demonstrates a normal software-development workflow in which the coding agent performs implementation work while a human remains responsible for requirements, engineering decisions, review, correction, verification, and delivery.

## Delivery workflow

1. Business requirement captured in a GitHub Issue
2. Testable acceptance criteria defined before implementation
3. Development performed on a feature branch
4. Coding agent implements against the requirement
5. Human reviews the agent-produced code
6. Review findings are turned into corrective feedback
7. Agent revises the implementation
8. Human independently runs tests and verifies behavior
9. Changes are reviewed through a pull request
10. Approved work is merged into `main`

The example application is intentionally small so the delivery process and engineering decisions remain easy to inspect.

## Start here

See GitHub Issue #1 for the initial business requirement and acceptance criteria.
