# GenAI Metric Explainer — Design (Stage 6)
Clarivance Analytics Group · P10

## Purpose
A bounded LLM layer that explains semantic-model measures in plain English for
non-technical stakeholders. Augments the analytics layer; never replaces the
governed measure. Reuses the P9 explanation prompt pattern.

## Boundaries (safety)
- Grounded: the LLM receives ONLY values from the semantic model (docs/semantic_model.md),
  never raw tables. It explains numbers it is given; it does not compute them.
- Bounded prompt: fixed template, no free-form data access.
- No hallucinated figures: every number in the output must trace to a measure value
  passed in the prompt context.
- Versioned prompt: stored in src/explain/, changes tracked in git.

## Prompt template (bounded)
System: You are a supply-chain analyst. Explain the metric below to a
non-technical manager in 2-3 sentences. Use ONLY the figures provided. Do not
invent numbers. Do not speculate beyond the data.

Context: {measure_name} = {measure_value} for {period}.
Baseline / comparison: {baseline_value}.

## Example (grounded)
Input:  Delivery Success Rate = 0.88, baseline 0.90
Output: "Delivery success held at 88% this period, two points below the 90%
baseline. The shortfall is concentrated in 311 failed and 211 returned runs,
worth reviewing against depot capacity."

## Evaluation
Prompt regression test: fixed inputs -> assert output contains the provided
figures and no others. Same eval-as-tests principle as the dbt gate.

## Status
Design + contract complete. Live invocation deferred (no Foundry spend on trial).
Grounding surface (semantic_model.md) is in place, so this is implementable
without rework when P8 activates.