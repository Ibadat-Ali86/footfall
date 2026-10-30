# Security Policy

## Supported Versions

This project is pre-release (Phase 0). Only the latest commit on `main` is supported.

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Email: ibadcodes@gmail.com

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

You will receive a response within **72 hours**. We aim to resolve confirmed vulnerabilities within **14 days** and will credit researchers (unless they prefer to remain anonymous).

## Disclosure Policy

We follow coordinated disclosure. Please give us reasonable time to investigate and patch before publishing details.

## Kill Switch

If a critical data integrity issue is discovered, the MCP server can be put into safe mode via an environment flag. This returns a fixed `data_unavailable` response to all tool calls while the issue is investigated.

## Scope

In scope:
- The MCP server and its tool endpoints
- The data pipeline and collectors
- The static export and dashboard
- Dependency vulnerabilities

Out of scope:
- Issues in third-party APIs we consume (report to them directly)
- Social engineering
