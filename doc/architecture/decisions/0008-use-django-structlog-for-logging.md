# 8. Use `django-structlog` for application logging

**Date**: 2026-05-26

## Status

Accepted

## Context

The project requires a consistent and structured logging approach that supports both human-readable debugging and machine-readable log processing.

While Django’s default logging configuration is adequate for basic use cases, it does not provide structured JSON logging out of the box. We also want the application logs to integrate cleanly with external observability and analytics platforms in the future.

In addition, the application requires rotating log files with weekly rotation and retention of historical logs.

## Decision

We will use `django-structlog` and `structlog` for structured and contextual logging, together with Django/Python's standard logging framework for handlers, output destinations, and log rotation. 

The logging configuration will:

- Use structlog processors to enrich logs with consistent and structured metadata such as timestamps, log levels, logger names, and exception details.
- Use Django/Python logging handlers to output logs to both the console and rotating log files.
- Produce structured JSON logs for file output, while using a human-readable console renderer for console output.
- Use weekly log rotation with retention of historical backups (in production using PVC).

### Rationale

The solution combines `django-structlog` and `structlog` for structured and contextual log generation, while Python’s standard `logging` framework handles log routing, handlers, output streams, formatting integration, and rotating file management, providing logging capabilities that align well with the project's operational and observability requirements.

The main reasons for this decision are:

- Native support for JSON-formatted logs, making integration with log aggregation, monitoring, and analytics platforms straightforward.
- Consistent structured log entries across the application, improving searchability and traceability.
- Better support for contextual logging, including request IDs, user identifiers (where appropriate), and correlation metadata.
- Improved compatibility with centralised logging systems and future observability tooling.

## Consequences

### Positive

- Logs are machine-readable and easier to process automatically.
- Improved debugging and traceability through structured contextual data.
- Easier integration with external observability platforms such as ELK/OpenSearch, Datadog, Loki, or Splunk if required in the future.
- Ensure logs include consistent structured context (such as timestamps, log levels, logger names, and request correlation data) across the application.

### Negative

- Slightly more complex than Django’s default logging configuration.
- Developers may need some familiarity with structured logging concepts.
- JSON log files are optimised for machine processing and are less convenient for direct manual inspection.
- File-based log retention depends on persistent storage being available in the deployment environment.

### Mitigation

- Human-readable console logging remains available during local development and through pod console output in production environments.
- Use persistent volume claims (PVCs) or equivalent persistent storage in containerised environments to retain rotated log files.
- Official documentation and community resources are widely available for implementation and troubleshooting.
- Keep the logging configuration centralised and standardised to minimise maintenance overhead.
