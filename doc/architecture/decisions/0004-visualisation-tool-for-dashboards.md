# 3. Visualisation tool for Dashboards

**Date:** 2025-11-13

**Updated**: 2026-03-17

**Previous ID**: ADR-0003

## Status

Accepted

## Context

Within the Swedish Pathogens Portal we develop and manage multiple dashboards. Each dashboard presents unique (and sometimes multiple) plots. To support data visualisation needs, we have evaluated two main options for generating and displaying plots:

- Plotly _(integrated directly within the Django app)_

- Apache Superset _(as an external visualisation service)_

The main goal was to find a solution that provides flexibility, ease of integration, and sufficient control over how plots are generated and displayed.

## Decision

We decided to use **Plotly** as the primary plotting library for generating visualisations for our dashboards.

**Rationale:**

- **Django Alignment:** Plotly integrates seamlessly with Django's template system and can be rendered server-side, maintaining our Django-based architecture.

    **Implementation Approach:**

    - Plots can be generated on the backend using the plotly python package.
    - The plots embedded in the template can be rendered in the frontend using the plotly JavaScript library.

- **Flexibility and Control:** Plotly allows full programmatic control over plot generation directly in Python, which fits well with our existing Django backend and development workflow.

- **Simplicity of Integration:** The overhead of managing a separate visualisation service is not outweighed by our current limited visualisation needs, thus simply embedding plots directly with the Django templates works more than sufficient.

**Considered Alternatives:**

- **Apache Superset:**

    - _Pros:_ Robust visualisation platform, role-based access control, built-in dashboard features.

    - _Cons:_ Adds operational overhead (requires a separate service), less flexible for embedding custom plots in Django templates, and our current visualisation needs do not justify the added complexity.

## Consequences

**Positive:**
- Plot generation logic stays within the Django codebase, ensuring straightforward integration, consistent development workflows, and minimal operational overhead.

**Negative:**
- The visualisation logic is tightly coupled to the Django application, which may limit scalability and flexibility if the number or complexity of the dashboards grows.
- All dashboard modifications must go through the portal team. High request volumes would substantially increase the team’s workload.


**Mitigation:**
- We should have a structured request process or batching of changes to reduce the number of ad-hoc modifications submitted to the portal team.
- If we wish to give users (researchers) the direct access to add/modify dashboards, we will re-evaluate Apache Superset or similar BI tools and make new decision based on the new requirement and use case.

