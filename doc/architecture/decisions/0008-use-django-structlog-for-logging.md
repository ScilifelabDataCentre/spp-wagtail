# 8. Use `django-structlog` for application logging

**Date**: 2026-05-26

## Status

Accepted

## Context

The project requires a consistent and structured logging approach that supports both human-readable debugging and machine-readable log processing.

While Django’s default logging configuration is adequate for basic use cases, it does not provide structured JSON logging out of the box. We also want the application logs to integrate cleanly with external observability and analytics platforms in the future.

In addition, the application requires rotating log files with weekly rotation and retention of historical logs.

## Decision

We will use `django-structlog` as the primary logging solution for the Django application.

### Rationale

`django-structlog` provides structured logging capabilities that align well with the project's operational and observability requirements.

The logging configuration will:

- Produce structured JSON logs suitable for machine processing and observability tooling.
- Output logs to both the console and rotating log files.
- Use weekly log rotation with retention of historical backups.
- Provide consistent contextual logging across the application.

The main reasons for this decision are:

- Native support for JSON-formatted logs, making integration with log aggregation, monitoring, and analytics platforms straightforward.
- Consistent structured log entries across the application, improving searchability and traceability.
- Better support for contextual logging, including request IDs, user information, and correlation metadata.
- Improved compatibility with centralised logging systems and future observability tooling.

## Consequences

### Positive

- Logs are machine-readable and easier to process automatically.
- Improved debugging and traceability through structured contextual data.
- Easier integration with external observability platforms such as ELK/OpenSearch, Datadog, Loki, or Splunk if required in the future.
- More consistent logging practices across the project.

### Negative

- Slightly more complex than Django’s default logging configuration.
- Developers may need some familiarity with structured logging concepts.
- JSON logs are less readable when viewed directly in raw log files.

### Mitigation

- Official documentation and community resources are widely available for implementation and troubleshooting.
- Use console renderers or pretty-print formatting in local development environments where appropriate.
- Keep the logging configuration centralised and standardised to minimise maintenance overhead.
