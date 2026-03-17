# 3. Adopt DaisyUI for UI components

**Date**: 2026-03-17

## Status

Accepted

## Context

We initially used Tailwind CSS for styling and attempted to build a set of base components ourselves within `base.css`. While this approach provided flexibility, it required additional effort to create, maintain, and standardize common UI components across the application.

As the project evolved, the need for a consistent design system and faster development of UI elements became more apparent.

## Decision

We will adopt DaisyUI as a component library on top of Tailwind CSS.

DaisyUI provides a comprehensive set of pre-built, themeable components out of the box, allowing us to accelerate development while maintaining consistency in design. It integrates seamlessly with our existing Tailwind setup and reduces the need to build and maintain custom base components.

## Consequences

- Faster development of UI components using ready-made building blocks
- Improved consistency across the application’s design
- Reduced maintenance effort compared to custom-built base styles
- Slight increase in dependency footprint
- Less granular control over component styling compared to fully custom implementations, though still flexible via Tailwind utilities
