#!/usr/bin/env python3
"""
Comprehensive unit tests for edge cases in pricing service and model detection
"""
import unittest
from pricing_service import PricingService
from migrate_to_mistral import MigrationAnalyzer
import tempfile
import os


class TestPricingServiceEdgeCases(unittest.TestCase):
    """Test edge cases for PricingService"""

    def setUp(self):
        self.service = PricingService()

    def test_negative_token_counts(self):
        """Test that negative token counts raise ValueError"""
        with self.assertRaises(ValueError) as context:
            self.service.calculate_cost('openai/gpt-4', -100, 100)
        self.assertIn('prompt_tokens must be non-negative', str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.service.calculate_cost('openai/gpt-4', 100, -100)
        self.assertIn('completion_tokens must be non-negative', str(context.exception))

    def test_zero_token_counts(self):
        """Test that zero token counts work correctly"""
        cost = self.service.calculate_cost('openai/gpt-4', 0, 0)
        self.assertEqual(cost, 0.0)

    def test_large_token_counts(self):
        """Test handling of very large token counts"""
        cost = self.service.calculate_cost('openai/gpt-4', 1_000_000_000, 1_000_000_000)
        self.assertGreater(cost, 0)
        self.assertIsInstance(cost, float)

    def test_invalid_model_id(self):
        """Test that invalid model IDs return 0.0 cost"""
        cost = self.service.calculate_cost('invalid/model', 1000, 1000)
        self.assertEqual(cost, 0.0)

    def test_invalid_usage_percentage(self):
        """Test that invalid usage percentages raise ValueError"""
        # Negative percentage
        with self.assertRaises(ValueError) as context:
            self.service.estimate_migration_savings(
                openai_models={'gpt-4': -0.5}
            )
        self.assertIn('must be between 0 and 1', str(context.exception))

        # Percentage > 1
        with self.assertRaises(ValueError) as context:
            self.service.estimate_migration_savings(
                openai_models={'gpt-4': 1.5}
            )
        self.assertIn('must be between 0 and 1', str(context.exception))

    def test_negative_monthly_tokens(self):
        """Test that negative monthly token counts raise ValueError"""
        with self.assertRaises(ValueError) as context:
            self.service.estimate_migration_savings(
                estimated_monthly_tokens=(-1000, 5000)
            )
        self.assertIn('prompt_tokens must be non-negative', str(context.exception))

    def test_empty_usage_models(self):
        """Test handling of empty model usage dict"""
        result = self.service.estimate_migration_savings(
            openai_models={}
        )
        # Should still return valid structure with zeros
        self.assertEqual(result['openai_cost'], 0.0)
        self.assertEqual(result['mistral_cost'], 0.0)

    def test_cache_invalidation(self):
        """Test that cache properly invalidates"""
        # Fetch pricing once
        pricing1 = self.service.get_pricing_data()

        # Manually invalidate cache
        self.service._cache_timestamp = None

        # Should fetch again
        pricing2 = self.service.get_pricing_data()

        # Both should be valid dicts
        self.assertIsInstance(pricing1, dict)
        self.assertIsInstance(pricing2, dict)

    def test_model_comparison_invalid_model(self):
        """Test model comparison with invalid model name"""
        result = self.service.get_model_comparison('invalid-model')
        self.assertIsNone(result)

    def test_mixed_usage_percentages_sum(self):
        """Test that usage percentages don't need to sum to 1.0"""
        # This should work fine - percentages are independent
        result = self.service.estimate_migration_savings(
            estimated_monthly_tokens=(1_000_000, 1_000_000),
            openai_models={
                'gpt-4': 0.3,
                'gpt-3.5-turbo': 0.2
            }
        )
        self.assertGreater(result['openai_cost'], 0)


class TestModelDetectionEdgeCases(unittest.TestCase):
    """Test edge cases for model detection"""

    def create_temp_file(self, content):
        """Helper to create temporary Python file"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        )
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def tearDown(self):
        """Clean up temp files"""
        # Cleanup handled by test methods

    def test_deeply_nested_function_call(self):
        """Test model detection in deeply nested function calls"""
        content = '''
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "test"
        },
        {
            "role": "user",
            "content": get_content(
                nested_call(
                    deep_call()
                )
            )
        }
    ],
    model="gpt-3.5-turbo",
    temperature=0.7
)
'''
        temp_file = self.create_temp_file(content)
        try:
            analyzer = MigrationAnalyzer(os.path.dirname(temp_file))
            calls = analyzer.scan()
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].model, 'gpt-3.5-turbo')
        finally:
            os.unlink(temp_file)

    def test_model_at_end_of_long_call(self):
        """Test detection when model is at the end of a very long call"""
        content = '''
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "test"}],
    temperature=0.7,
    max_tokens=100,
    top_p=1.0,
    frequency_penalty=0,
    presence_penalty=0,
    stop=[],
    logit_bias={},
    user="test-user",
    stream=False,
    model="gpt-4-turbo"
)
'''
        temp_file = self.create_temp_file(content)
        try:
            analyzer = MigrationAnalyzer(os.path.dirname(temp_file))
            calls = analyzer.scan()
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].model, 'gpt-4-turbo')
        finally:
            os.unlink(temp_file)

    def test_model_from_variable(self):
        """Test detection when model comes from a variable"""
        content = '''
from openai import OpenAI

MODEL_NAME = "gpt-4"
client = OpenAI()
response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[{"role": "user", "content": "test"}]
)
'''
        temp_file = self.create_temp_file(content)
        try:
            analyzer = MigrationAnalyzer(os.path.dirname(temp_file))
            calls = analyzer.scan()
            self.assertEqual(len(calls), 1)
            # Should detect MODEL_NAME as the model
            self.assertEqual(calls[0].model, 'MODEL_NAME')
        finally:
            os.unlink(temp_file)

    def test_json_style_model_specification(self):
        """Test detection with JSON-style model specification in dict"""
        content = '''
from openai import OpenAI

client = OpenAI()
params = {
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "test"}]
}
response = client.chat.completions.create(**params)
'''
        temp_file = self.create_temp_file(content)
        try:
            analyzer = MigrationAnalyzer(os.path.dirname(temp_file))
            calls = analyzer.scan()
            self.assertEqual(len(calls), 1)
            # Dictionary unpacking is not detected - defaults to gpt-4
            # This is a known limitation of static analysis
            self.assertEqual(calls[0].model, 'gpt-4')
        finally:
            os.unlink(temp_file)

    def test_no_model_specified(self):
        """Test that calls without model default to gpt-4"""
        content = '''
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "test"}]
)
'''
        temp_file = self.create_temp_file(content)
        try:
            analyzer = MigrationAnalyzer(os.path.dirname(temp_file))
            calls = analyzer.scan()
            self.assertEqual(len(calls), 1)
            # Should default to gpt-4
            self.assertEqual(calls[0].model, 'gpt-4')
        finally:
            os.unlink(temp_file)

    def test_multiple_calls_different_models(self):
        """Test detection of multiple calls with different models"""
        content = '''
from openai import OpenAI

client = OpenAI()

# First call
response1 = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "test"}]
)

# Second call
response2 = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "test"}]
)

# Embedding call
embedding = client.embeddings.create(
    model="text-embedding-ada-002",
    input="test"
)
'''
        temp_file = self.create_temp_file(content)
        try:
            analyzer = MigrationAnalyzer(os.path.dirname(temp_file))
            calls = analyzer.scan()
            self.assertEqual(len(calls), 3)

            models = [call.model for call in calls]
            self.assertIn('gpt-4', models)
            self.assertIn('gpt-3.5-turbo', models)
            self.assertIn('text-embedding-ada-002', models)
        finally:
            os.unlink(temp_file)


class TestCacheThreadSafety(unittest.TestCase):
    """Test cache invalidation edge cases"""

    def setUp(self):
        self.service = PricingService()

    def test_cache_expiry_boundary(self):
        """Test cache behavior at expiry boundary"""
        from datetime import timedelta

        # Fetch pricing
        pricing1 = self.service.get_pricing_data()

        # Set timestamp to just before expiry
        self.service._cache_timestamp -= timedelta(minutes=59, seconds=59)
        pricing2 = self.service.get_pricing_data()

        # Should still use cache
        self.assertIs(pricing1, pricing2)

        # Now expire it
        self.service._cache_timestamp -= timedelta(seconds=2)
        pricing3 = self.service.get_pricing_data()

        # Should be new data (or fallback)
        self.assertIsInstance(pricing3, dict)


def run_tests():
    """Run all test suites"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestPricingServiceEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestModelDetectionEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheThreadSafety))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ All edge case tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} test(s) had errors")
    print("=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
