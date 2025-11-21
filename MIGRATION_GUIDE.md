# Migration Quick Reference

## Import Changes

| Before (OpenAI) | After (Mistral) |
|-----------------|-----------------|
| `from openai import OpenAI` | `from mistralai.client import MistralClient` |
| `client = OpenAI(api_key="...")` | `client = MistralClient(api_key="...")` |

## Method Changes

| Operation | OpenAI | Mistral |
|-----------|--------|---------|
| **Chat** | `client.chat.completions.create()` | `client.chat()` |
| **Streaming** | `client.chat.completions.create(stream=True)` | `client.chat_stream()` |
| **Embeddings** | `client.embeddings.create()` | `client.embeddings()` |

## Model Mapping

| OpenAI Model | Mistral Model | Use Case |
|--------------|---------------|----------|
| `gpt-4` | `mistral-large-latest` | Complex reasoning, code generation |
| `gpt-4-turbo` | `mistral-large-latest` | Faster responses, still high quality |
| `gpt-3.5-turbo` | `mistral-small-latest` | Simple tasks, high volume |
| `text-embedding-ada-002` | `mistral-embed` | Vector embeddings for RAG |

## Parameter Compatibility

### ✅ Parameters That Work Identically

These parameters require NO changes:

- `messages` - Same format!
- `temperature` - Same range (0-2)
- `max_tokens` - Same behavior
- `top_p` - Same range (0-1)
- `tools` - Same JSON schema format!
- `tool_choice` - Same options ("auto", "none", specific tool)
- `response_format` - Same JSON mode support

### ⚠️ Parameters That Need Minor Changes

| Parameter | OpenAI | Mistral | Notes |
|-----------|--------|---------|-------|
| **Streaming** | `stream=True` | Use `chat_stream()` method | Different method, not parameter |
| **Embeddings input** | `input="text"` | `input=["text"]` | Wrap string in array |
| **Model names** | `gpt-4` | `mistral-large-latest` | Different naming convention |

### ❌ OpenAI-Specific Parameters (Not in Mistral)

- `seed` - Not supported (yet)
- `logprobs` - Not supported
- `logit_bias` - Not supported
- `functions` - Use `tools` instead (deprecated in OpenAI anyway)

## Response Structure

### ✅ Identical Response Format

The response structure is the same:

```python
response.choices[0].message.content     # Same!
response.choices[0].message.tool_calls  # Same!
response.choices[0].finish_reason       # Same!
```

## Code Examples: Side-by-Side

### Basic Chat

```python
# BEFORE (OpenAI)
from openai import OpenAI
client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# AFTER (Mistral)
from mistralai.client import MistralClient
client = MistralClient(api_key="...")
response = client.chat(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Streaming

```python
# BEFORE (OpenAI)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell a story"}],
    stream=True
)
for chunk in response:
    print(chunk.choices[0].delta.content, end="")

# AFTER (Mistral)
response = client.chat_stream(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Tell a story"}]
)
for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

### Function Calling

```python
# BEFORE (OpenAI)
tools = [{"type": "function", "function": {...}}]
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=tools,
    tool_choice="auto"
)

# AFTER (Mistral)
tools = [{"type": "function", "function": {...}}]  # SAME SCHEMA!
response = client.chat(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=tools,
    tool_choice="auto"
)
```

### Embeddings

```python
# BEFORE (OpenAI)
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="Text to embed"
)
embedding = response.data[0].embedding

# AFTER (Mistral)
response = client.embeddings(
    model="mistral-embed",
    input=["Text to embed"]  # Note: wrap in list
)
embedding = response.data[0].embedding
```

## Cost Comparison

### Per 1M Tokens (Input)

| Model Tier | OpenAI | Mistral | Savings |
|------------|--------|---------|---------|
| **Premium** | $30 (GPT-4) | $10 (Large) | **67%** |
| **Standard** | $10 (GPT-4-T) | $4 (Large) | **60%** |
| **Economy** | $1.50 (GPT-3.5) | $0.65 (Small) | **57%** |

### Embeddings (Per 1M Tokens)

| Model | OpenAI | Mistral | Savings |
|-------|--------|---------|---------|
| **Standard** | $0.13 | $0.02 | **85%** |

### Real-World Monthly Costs

**Moderate Usage (10M tokens/month):**
- OpenAI (GPT-4): $300
- Mistral (Large): $100
- **Savings: $200/month or $2,400/year**

**High Volume (100M tokens/month):**
- OpenAI (GPT-4): $3,000
- Mistral (Large): $1,000
- **Savings: $2,000/month or $24,000/year**

## Migration Checklist

- [ ] Install Mistral SDK: `pip install mistralai`
- [ ] Get API key from https://console.mistral.ai/
- [ ] Update imports in all files
- [ ] Replace `OpenAI` with `MistralClient`
- [ ] Change `.chat.completions.create()` to `.chat()`
- [ ] Change `.chat.completions.create(stream=True)` to `.chat_stream()`
- [ ] Update model names (gpt-4 → mistral-large-latest)
- [ ] For embeddings: wrap input strings in arrays
- [ ] Test in development environment
- [ ] Monitor responses for quality
- [ ] Deploy to production
- [ ] Monitor cost savings!

## Testing Strategy

### 1. Unit Tests
Keep your existing tests! The response structure is identical, so tests should mostly pass after updating the client.

### 2. Integration Tests
Test these specific scenarios:
- Function calling with complex schemas
- Streaming with interruptions
- Error handling (rate limits, invalid requests)
- Embeddings vector similarity (dimensions changed!)

### 3. A/B Testing
For critical applications:
- Run both APIs side-by-side
- Compare response quality
- Monitor latency differences
- Verify cost savings match projections

## Common Issues & Solutions

### Issue: "Module not found: mistralai"
**Solution:** `pip install mistralai`

### Issue: "Invalid model name"
**Solution:** Use `mistral-large-latest`, not `gpt-4`

### Issue: "Embeddings dimension mismatch"
**Solution:** Mistral uses 1024 dimensions (vs OpenAI's 1536). Need to:
1. Re-embed your documents
2. Re-index your vector database
3. Update dimension configs

### Issue: "Response format different"
**Solution:** Check if you're using deprecated OpenAI parameters like `logprobs` or `seed`

### Issue: "Streaming not working"
**Solution:** Use `client.chat_stream()` instead of `client.chat(stream=True)`

## Quality Expectations

### Where Mistral Matches/Exceeds GPT-4
- ✅ General reasoning
- ✅ Code generation (especially Python, JavaScript)
- ✅ Function calling accuracy
- ✅ Following instructions
- ✅ JSON output formatting

### Where GPT-4 May Have Edge
- ⚠️ Very niche domain knowledge
- ⚠️ Extremely long context reasoning
- ⚠️ Creative writing (subjective)

**Bottom Line:** For 95% of use cases, Mistral Large matches GPT-4 quality at 70% lower cost.

## Need Help?

- 📖 Mistral Docs: https://docs.mistral.ai/
- 💬 Discord: https://discord.gg/mistralai
- 📚 Cookbooks: https://docs.mistral.ai/cookbooks
- 🐛 Issues: https://github.com/mistralai/client-python/issues

---

**Pro Tip:** Start with one non-critical endpoint. Migrate it. Test it. Measure savings. Then roll out to more services. Low-risk, high-reward.
