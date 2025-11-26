#!/usr/bin/env python3
"""
Test script for pricing service integration
"""
from pricing_service import PricingService

def test_pricing_service():
    """Test the pricing service functionality"""
    print("=" * 80)
    print("Testing Pricing Service")
    print("=" * 80)
    print()

    # Initialize pricing service
    pricing_service = PricingService()

    # Test 1: Fetch pricing data
    print("Test 1: Fetching pricing data from OpenRouter...")
    pricing_data = pricing_service.get_pricing_data()
    print(f"✓ Fetched pricing for {len(pricing_data)} models")
    print()

    # Test 2: Get specific model pricing
    print("Test 2: Getting GPT-4 pricing...")
    gpt4_pricing = pricing_service.get_model_pricing('openai/gpt-4')
    if gpt4_pricing:
        print(f"✓ GPT-4 pricing:")
        print(f"  - Prompt: ${gpt4_pricing['prompt']:.6f} per token")
        print(f"  - Completion: ${gpt4_pricing['completion']:.6f} per token")
    else:
        print("✗ Could not fetch GPT-4 pricing (using fallback)")
    print()

    # Test 3: Calculate cost
    print("Test 3: Calculating cost for 1M tokens...")
    cost = pricing_service.calculate_cost('openai/gpt-4', 500_000, 500_000)
    print(f"✓ Cost for 1M tokens (GPT-4): ${cost:.2f}")
    print()

    # Test 4: Migration savings estimate
    print("Test 4: Estimating migration savings...")
    savings = pricing_service.estimate_migration_savings(
        estimated_monthly_tokens=(5_000_000, 5_000_000),
        openai_models={'gpt-4': 1.0}
    )
    print(f"✓ Migration savings estimate:")
    print(f"  - OpenAI cost: ${savings['openai_cost']}/month")
    print(f"  - Mistral cost: ${savings['mistral_cost']}/month")
    print(f"  - Savings: ${savings['savings']}/month ({savings['percentage']}%)")
    print()

    # Test 5: Model comparison
    print("Test 5: Comparing GPT-4 vs Mistral Large...")
    comparison = pricing_service.get_model_comparison('gpt-4')
    if comparison:
        print(f"✓ Comparison:")
        print(f"  OpenAI: {comparison['openai']['name']}")
        print(f"    - Cost per 1M tokens: ${comparison['openai']['cost_per_1m_tokens']}")
        print(f"  Mistral: {comparison['mistral']['name']}")
        print(f"    - Cost per 1M tokens: ${comparison['mistral']['cost_per_1m_tokens']}")
        print(f"  Savings: ${comparison['savings']['per_1m_tokens']} per 1M tokens ({comparison['savings']['percentage']}%)")
    else:
        print("✗ Could not compare models")
    print()

    # Test 6: Mixed model usage
    print("Test 6: Estimating savings with mixed model usage...")
    mixed_savings = pricing_service.estimate_migration_savings(
        estimated_monthly_tokens=(10_000_000, 10_000_000),
        openai_models={
            'gpt-4': 0.3,
            'gpt-4-turbo': 0.5,
            'gpt-3.5-turbo': 0.2
        }
    )
    print(f"✓ Mixed usage savings estimate:")
    print(f"  - OpenAI cost: ${mixed_savings['openai_cost']}/month")
    print(f"  - Mistral cost: ${mixed_savings['mistral_cost']}/month")
    print(f"  - Savings: ${mixed_savings['savings']}/month ({mixed_savings['percentage']}%)")
    print()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)

if __name__ == '__main__':
    test_pricing_service()
