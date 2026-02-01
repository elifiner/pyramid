---
name: Pyramid Memory Analysis
overview: Improve pyramid memory quality by giving LLMs better model context (samples + purpose descriptions), removing extraction-time importance scores, batching assignment, and switching from time-based to count/token-based spans.
todos:
  - id: schema-migration
    content: Remove importance column, create migration script to reset models/summaries
    status: completed
  - id: sample-context-assignment
    content: Add sample observations to assignment context in get_models_context()
    status: completed
  - id: batch-assignment
    content: Add BATCH=25 constant, process observations in smaller groups
    status: completed
  - id: drop-extraction-importance
    content: Remove importance from OBSERVE_TOOL in llm.py
    status: completed
  - id: count-based-step
    content: Replace SPAN with single STEP=10 constant for count-based tiers
    status: completed
  - id: narrative-summaries
    content: Change SUMMARIZE_SYSTEM_PROMPT from telegram to narrative prose style
    status: completed
  - id: model-aware-summarize
    content: Pass model name/purpose AND sample observations to summarize prompts
    status: completed
  - id: purpose-descriptions
    content: Update derive_model_description to generate purpose-based descriptions
    status: completed
isProject: false
---

# Pyramid Memory System Improvements

## Summary of Changes

1. **Model context for assignment**: Sample observations + purpose descriptions
2. **Model context for summarization**: Pass model name/purpose for filtering
3. **Drop extraction-time importance**: Let summarization LLM judge with full context
4. **Batch assignment**: New `BATCH` constant (e.g., 25 observations)
5. **Count-based spans**: Replace `SPAN = 1 day` with observation/token count

## Root Cause Analysis

### Problem 1: Model Assignment Lacks Context

**Evidence:**

- `self` has 1,816 observations (26% of total) - should be much smaller
- Massive model overlap and duplication

**Root Causes:**

- LLM sees no sample observations - can't distinguish what belongs where
- Batch sizes too large (100-900 at once) - leads to shortcuts
- Descriptions describe content ("Eli runs GrowthLab...") not purpose ("business-related info")

### Problem 2: Summarization Lacks Model Context

Summarize prompt doesn't know which model it's for - can't filter misplaced content.

### Problem 3: Importance Scores Set Too Early

Importance assigned at extraction without context. Better to let summarization LLM determine importance when it has the full picture.

### Problem 4: Time-Based Spans Create Uneven Summaries

With `SPAN = 1 day`, busy days have 50+ observations per model, quiet days have 2. Compression is wildly uneven.

---

## Implementation

### 1. Sample-Based Assignment Context

Update `get_models_context()` in [summarize.py](summarize.py) to include sample observations:

```python
def get_models_context(session):
    models = session.query(Model).all()
    lines = ["Available models:"]
    for m in models:
        lines.append(f"\n### {m.name}")
        lines.append(f"Purpose: {m.description or '(undefined)'}")
        
        samples = session.query(Observation).filter(
            Observation.model_id == m.id
        ).order_by(Observation.timestamp.desc()).limit(5).all()
        
        if samples:
            lines.append("Examples:")
            for s in samples:
                lines.append(f"  - {s.text}")
    
    return "\n".join(lines)
```

### 2. Batch Assignment

Add constant and batch processing:

```python
BATCH = 25  # Observations per assignment batch

def assign_models_to_observations(session, observations):
    for i in range(0, len(observations), BATCH):
        batch = observations[i:i + BATCH]
        # ... assignment logic for batch
        session.commit()
```

### 3. Purpose-Based Descriptions

Replace `derive_model_description()` in [export_models.py](export_models.py):

```python
def derive_model_purpose(session, model):
    samples = session.query(Observation).filter(
        Observation.model_id == model.id
    ).order_by(func.random()).limit(10).all()
    
    if not samples:
        return None
    
    sample_text = "\n".join(f"- {s.text}" for s in samples)
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user", 
            "content": f"""These observations are in model '{model.name}':

{sample_text}

Write a 1-sentence description of what KIND of information belongs here.
Focus on category/type, not specific content."""
        }]
    )
    return response.choices[0].message.content.strip()
```

### 4. Drop Extraction-Time Importance

In [llm.py](llm.py), simplify `OBSERVE_TOOL` - remove importance parameter. Observations are just text + timestamp.

### 5. Narrative Summaries

Replace telegram-style `SUMMARIZE_SYSTEM_PROMPT` with narrative prose:

```python
SUMMARIZE_SYSTEM_PROMPT = """You are a memory agent creating summaries.

Write in clear, readable narrative prose. Convey importance through word choice 
(e.g., "significantly", "notably", "critically") rather than markers or scores.

Preserve specific facts: names, dates, numbers, places.
Organize related information into coherent paragraphs."""
```

### 6. Count-Based Step

Replace time-based constants in [summarize.py](summarize.py):

```python
# Old
SPAN = timedelta(days=1)
STEP = 3

# New  
STEP = 10  # Single constant: 10 items per summary at all tiers
```

Tier 0 summarizes every 10 observations. Tier N summarizes every 10 tier N-1 summaries.

### 7. Model-Aware Summarization

Pass model context to summarize functions:

```python
def summarize_chunk(observations, model_name, model_description):
    obs_text = "\n".join(obs.text for obs in observations)
    
    system = f"""{SUMMARIZE_SYSTEM_PROMPT}

Model: {model_name}
Purpose: {model_description}

Only include information relevant to this model's purpose."""
```

---

## Constants

Single constant: `STEP = 10`

- Tier 0: Every 10 observations per model
- Tier 1: Every 10 tier 0 summaries
- Tier N: Every 10 tier N-1 summaries

Also: `BATCH = 25` for assignment batches

---

## Migration Strategy

1. **Keep observations** - 7000 observations preserved
2. **Delete non-base models** - Remove all except self/user/system
3. **Reset model_id** - Set all observations to NULL
4. **Delete summaries** - Wipe all summaries
5. **Remove importance column** - Drop from observations schema
6. **Re-run assignment** - With new batched, sample-based approach
7. **Re-run summarization** - With model context and count-based spans

---

## Design Principles

1. **Generic** - No hardcoded names; works for any agent
2. **Context-rich** - LLMs get samples + purpose for both assignment AND summarization
3. **Importance emerges** - Determined by summarization with context, not extraction
4. **Even compression** - Count-based spans create consistent tier sizes
5. **Single constant** - STEP=10 for all tiers

