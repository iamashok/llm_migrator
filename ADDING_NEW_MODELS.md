# Adding Support for New OpenAI Models

This document explains how to properly add support for new OpenAI models as they are released.

## Important Principles

**DO NOT add speculative pricing for unreleased models.**

The core value proposition of this tool is providing "Real-Time Pricing" based on actual, current data from OpenRouter. Adding estimated pricing for unreleased models:
- Undermines user trust
- Can lead to incorrect business decisions
- Violates the architectural pattern of data accuracy

## When to Add a New Model

Add a model to the mappings **ONLY** when:

1. ✅ The model is publicly released by OpenAI
2. ✅ The model appears in OpenRouter's API response
3. ✅ Real pricing data is available from OpenRouter

## How to Add a New Model

### Step 1: Verify Model Exists in OpenRouter

```python
from pricing_service import PricingService

service = PricingService()

# Check if model exists
if service.model_exists('openai/new-model'):
    print("Model found in OpenRouter!")
else:
    print("Model not yet available in OpenRouter")
```

### Step 2: Add to Model Mappings

Only after confirming the model exists, add it to `pricing_service.py`:

```python
OPENAI_TO_OPENROUTER = {
    # ... existing models ...
    'new-model': 'openai/new-model',  # Add here
}

OPENAI_TO_MISTRAL = {
    # ... existing models ...
    'new-model': 'mistralai/appropriate-equivalent',  # Add equivalent
}
```

### Step 3: DO NOT Add to Fallback Pricing

The fallback pricing should only contain models that:
- Are currently released
- Have stable, well-known pricing
- Are widely used

New models should NOT be added to fallback pricing until their pricing is stable.

### Step 4: Test the Integration

```python
# Test that pricing is fetched correctly
service = PricingService()

# Should return real pricing data
pricing = service.get_model_pricing('openai/new-model')
if pricing:
    print(f"Prompt: ${pricing['prompt']} per token")
    print(f"Completion: ${pricing['completion']} per token")

# Test migration savings
savings = service.estimate_migration_savings(
    estimated_monthly_tokens=(5_000_000, 5_000_000),
    openai_models={'new-model': 1.0}
)
print(f"Savings: ${savings['savings']}/month")
```

### Step 5: Add Tests

Add test cases to `test_edge_cases.py`:

```python
def test_new_model_detection(self):
    """Test detection of new-model in code"""
    content = '''
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="new-model",
    messages=[{"role": "user", "content": "test"}]
)
'''
    temp_file = self.create_temp_file(content)
    try:
        analyzer = MigrationAnalyzer(os.path.dirname(temp_file))
        calls = analyzer.scan()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].model, 'new-model')
    finally:
        os.unlink(temp_file)
```

## What Happens with Unknown Models

If a user's code uses a model that isn't in OpenRouter yet:

1. ✅ Model detection will still identify it
2. ✅ A warning will be logged: `"WARNING: Model 'X' not found in pricing data"`
3. ✅ Cost calculation will return 0.0 (rather than false data)
4. ✅ User can still see which files use the model
5. ✅ Migration suggestions won't include cost savings

This is the correct behavior - it's better to show no pricing than wrong pricing.

## Example: If GPT-5 is Released

**Before adding to code:**
```bash
# 1. Check if GPT-5 exists in OpenRouter
python3 -c "
from pricing_service import PricingService
service = PricingService()
if service.model_exists('openai/gpt-5'):
    print('GPT-5 is available!')
    pricing = service.get_model_pricing('openai/gpt-5')
    print(f'Real pricing: \${pricing[\"prompt\"]}/token')
else:
    print('GPT-5 not yet in OpenRouter - do not add to mappings')
"
```

**Only if verified, add to mappings:**
```python
OPENAI_TO_OPENROUTER = {
    # ... existing models ...
    'gpt-5': 'openai/gpt-5',  # Only add after verification
}

OPENAI_TO_MISTRAL = {
    # ... existing models ...
    'gpt-5': 'mistralai/mistral-large',  # Or appropriate equivalent
}
```

## Checklist for Adding New Models

- [ ] Model is publicly released by OpenAI
- [ ] Model confirmed to exist in OpenRouter API response
- [ ] Real pricing data available (not estimated)
- [ ] Added to `OPENAI_TO_OPENROUTER` mapping
- [ ] Added to `OPENAI_TO_MISTRAL` mapping with appropriate equivalent
- [ ] **NOT** added to `_get_fallback_pricing()` (unless it's a stable, widely-used model)
- [ ] Tests added to verify detection and pricing
- [ ] Documentation updated if needed
- [ ] Tested end-to-end with real code examples

## Antipatterns to Avoid

❌ **Don't add speculative pricing:**
```python
# BAD - GPT-5 not released yet
'openai/gpt-5': {'prompt': 0.00005, 'completion': 0.00010}
```

❌ **Don't add models "just in case":**
```python
# BAD - Adding models before they exist
'gpt-6': 'openai/gpt-6'
```

❌ **Don't silence warnings for missing models:**
```python
# BAD - Hiding that a model doesn't exist
if pricing is None:
    pricing = {'prompt': 0, 'completion': 0}  # Silent failure
```

## Best Practices

✅ **Wait for official release:**
Only add models after they're publicly available.

✅ **Verify with OpenRouter:**
Always check that OpenRouter has pricing before adding.

✅ **Log warnings:**
Let users know when a model isn't found.

✅ **Return None/0.0 for unknown models:**
Better to show no data than wrong data.

✅ **Document what's real vs estimated:**
Always be clear about data sources.

## Questions?

If you're unsure whether to add a model, ask:
1. Is it publicly released?
2. Does OpenRouter have it?
3. Do we have real pricing?

If the answer to any is "no", **don't add it yet**.
