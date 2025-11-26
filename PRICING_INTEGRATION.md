# Real-Time Pricing Integration

The LLM Migrator now includes real-time pricing lookup from OpenRouter's API to calculate accurate cost savings for migrations.

## Features

- **Real-Time Pricing**: Fetches current model pricing from OpenRouter API
- **Automatic Model Detection**: Detects which OpenAI models are being used in your codebase
- **Accurate Cost Calculations**: Calculates real cost savings based on actual model usage
- **Smart Caching**: Caches pricing data for 1 hour to minimize API calls
- **Fallback Pricing**: Uses fallback pricing if OpenRouter API is unavailable

## How It Works

1. **Model Detection**: The scanner analyzes your codebase to detect:
   - Which OpenAI models you're using (gpt-4, gpt-3.5-turbo, etc.)
   - Usage patterns (chat, embeddings, completions)
   - Frequency of API calls

2. **Pricing Lookup**: Fetches real-time pricing from OpenRouter for:
   - OpenAI models (gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.)
   - Equivalent Mistral models (mistral-large, mistral-small, mistral-embed)

3. **Cost Calculation**: Estimates monthly costs based on:
   - Detected model usage distribution
   - Estimated token volumes (default: 10M tokens/month)
   - Real pricing from OpenRouter

4. **Savings Projection**: Shows you:
   - Current OpenAI costs
   - Projected Mistral costs
   - Dollar amount savings
   - Percentage reduction

## API Integration

### OpenRouter API

The pricing service uses the OpenRouter API:

```
GET https://openrouter.ai/api/v1/models
```

**Authentication**: Optional (works without API key, but may have rate limits)

To set an API key for higher rate limits:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

Get your API key at: https://openrouter.ai/keys

### Response Format

The API returns pricing data including:
- `prompt`: Cost per prompt token
- `completion`: Cost per completion token
- `name`: Model name
- `context_length`: Maximum context window

## Usage Examples

### Basic Usage (Web UI)

Simply scan your codebase through the web UI - pricing calculations happen automatically:

```bash
python3 app.py
# Navigate to http://localhost:5000
# Enter your directory or GitHub URL
# View real-time cost savings
```

### Programmatic Usage

```python
from pricing_service import PricingService

# Initialize service
pricing_service = PricingService()

# Get pricing for specific model
gpt4_pricing = pricing_service.get_model_pricing('openai/gpt-4')
print(f"GPT-4 prompt cost: ${gpt4_pricing['prompt']}")

# Calculate migration savings
savings = pricing_service.estimate_migration_savings(
    estimated_monthly_tokens=(5_000_000, 5_000_000),  # 5M prompt, 5M completion
    openai_models={'gpt-4': 0.7, 'gpt-3.5-turbo': 0.3}  # 70% GPT-4, 30% GPT-3.5
)

print(f"Monthly savings: ${savings['savings']}")
print(f"Percentage reduction: {savings['percentage']}%")

# Compare specific models
comparison = pricing_service.get_model_comparison('gpt-4')
print(f"OpenAI: ${comparison['openai']['cost_per_1m_tokens']}/1M tokens")
print(f"Mistral: ${comparison['mistral']['cost_per_1m_tokens']}/1M tokens")
```

### Test the Integration

Run the test script to verify the pricing integration:

```bash
python3 test_pricing.py
```

This will test:
- Fetching pricing data from OpenRouter
- Getting specific model pricing
- Calculating costs for token volumes
- Estimating migration savings
- Comparing model costs

## Model Mappings

### OpenAI → Mistral Equivalents

| OpenAI Model | Mistral Equivalent | Use Case |
|--------------|-------------------|----------|
| gpt-4 | mistral-large | Complex reasoning, high quality |
| gpt-4-turbo | mistral-large | Fast, complex tasks |
| gpt-3.5-turbo | mistral-small | General purpose, cost-effective |
| text-embedding-ada-002 | mistral-embed | Text embeddings |

### OpenRouter Model IDs

The service uses OpenRouter's model ID format:
- `openai/gpt-4`
- `openai/gpt-4-turbo`
- `openai/gpt-3.5-turbo`
- `mistralai/mistral-large`
- `mistralai/mistral-small`
- `mistralai/mistral-embed`

## Caching

The pricing service caches model pricing data for **1 hour** to:
- Reduce API calls to OpenRouter
- Improve response times
- Minimize rate limiting issues

Cache is automatically refreshed when expired.

## Error Handling

The service includes robust error handling:

1. **API Unavailable**: Falls back to hardcoded pricing estimates
2. **Missing Models**: Uses sensible defaults (gpt-4 equivalent)
3. **Network Errors**: Logs warning and continues with fallback pricing

## Fallback Pricing

If OpenRouter API is unavailable, the service uses these fallback rates (approximate):

| Model | Prompt | Completion |
|-------|--------|------------|
| GPT-4 | $0.03/1K | $0.06/1K |
| GPT-4 Turbo | $0.01/1K | $0.03/1K |
| GPT-3.5 Turbo | $0.0005/1K | $0.0015/1K |
| Mistral Large | $0.008/1K | $0.024/1K |
| Mistral Small | $0.001/1K | $0.003/1K |

## Real-World Examples

### Example 1: Pure GPT-4 Usage

**Current Setup:**
- 10M tokens/month (5M prompt, 5M completion)
- 100% GPT-4

**Results:**
- OpenAI cost: $450/month
- Mistral cost: $40/month
- **Savings: $410/month (91.1%)**

### Example 2: Mixed Usage

**Current Setup:**
- 20M tokens/month (10M prompt, 10M completion)
- 30% GPT-4
- 50% GPT-4 Turbo
- 20% GPT-3.5 Turbo

**Results:**
- OpenAI cost: $474/month
- Mistral cost: $65.60/month
- **Savings: $408.40/month (86.2%)**

## Dependencies

The pricing service requires:
```
requests>=2.31.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Future Enhancements

Potential improvements:
- [ ] Support for custom token volume estimates
- [ ] Historical pricing trends
- [ ] Per-endpoint cost breakdown
- [ ] Integration with actual usage logs
- [ ] ROI calculator based on current spend

## Contributing

To contribute to the pricing integration:

1. Test with `python3 test_pricing.py`
2. Ensure fallback pricing is up-to-date
3. Update model mappings as new models are released
4. Keep OpenRouter API integration current

## Support

For issues with pricing integration:
- Check OpenRouter status: https://status.openrouter.ai/
- Verify your API key (if using one)
- Review fallback pricing accuracy
- Submit issues at: https://github.com/iamashok/llm_migrator/issues
