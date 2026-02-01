# Reflection: Integrating Memory as Reasoning

## Background

Inspired by Plastic Labs' "Memory as Reasoning" article, which argues that memory systems should treat memory as a prediction/reasoning task rather than pure storage and retrieval.

## What Pyramid Already Does Well

Pyramid's tiered structure isn't just compression — it's a **differential temporal resolution model** that mirrors human memory:

- Recent events: high detail (tier 0, daily)
- Older events: gist only (higher tiers, compressed)

This is distinct from simple summarization. The recency bias is a feature.

## The Gap: Integration

What Pyramid currently lacks is a lateral process that connects new observations to existing knowledge:

```
new observation → compare to existing model → note connection/contradiction/confirmation
```

Without this, each observation exists in isolation until compressed.

## The Solution: Reflection as Observation

Rather than adding new tables or concepts, we treat **meta-observations as regular observations**. The reflection process generates observations that:

1. Note patterns across recent observations
2. Connect new observations to existing model knowledge  
3. Make predictions about likely future behavior/needs
4. Validate or invalidate previous predictions

These flow through the same pipeline: stored → assigned to models → compressed into summaries.

## Types of Observations

All are stored identically, distinguished only by textual content:

**First-order observations** (extracted from conversations):
```
[6] User asked about invoice templates
```

**Pattern observations** (noting trends):
```
[5] The consulting practice observations are accumulating rapidly — this is becoming a central focus
```

**Predictive observations**:
```
[4] PREDICT: User will likely need contract templates soon given consulting trajectory
```

**Validation observations**:
```
[6] Previous prediction about invoicing tools confirmed by today's conversation
```

## The Reflection Process

Runs as part of summarization (or separately). Given:

- New observations since last reflection
- Current state of relevant models (pyramids)

Generate observations that synthesize, predict, and validate.

## The Self-Reinforcing Loop

```
Week 1: Extract observations → summarize
Week 2: Extract observations → reflect (generates meta-obs) → summarize
Week 3: Extract observations → reflect (sees week 2 predictions, validates) → summarize
```

The reflection process sees its own past predictions in the model pyramids, naturally validating or invalidating them. The system becomes self-correcting without explicit rewriting.

## Why This Avoids Drift

A naive approach rewrites models on each new observation:

```
model = llm(old_model + new_observation)
```

This drifts badly — each rewrite loses fidelity, compounds errors.

Our approach is append-only:
- Base observations are immutable
- Reflection adds new observations (doesn't modify old ones)
- Compression is deterministic from inputs
- The pyramid provides stability while reflection provides dynamism

## Textual Conventions

Use text prefixes rather than schema changes:

- `PREDICT:` for predictive observations
- `CONFIRMED:` / `CONTRADICTED:` for validation observations

This keeps the data model simple and lets everything flow through unchanged pipelines.

## Next Steps

1. Add reflection step to summarization process
2. Design the reflection prompt carefully
3. Test on subset of conversations to see how models evolve
4. Measure prediction hit rate over time
