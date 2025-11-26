#!/usr/bin/env python3
"""
Real-time pricing service for OpenRouter models
Fetches and caches model pricing data from OpenRouter API
"""
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from threading import Lock
import os


class PricingService:
    """Service for fetching and calculating model pricing from OpenRouter"""

    # OpenRouter API endpoint
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"

    # Cache pricing data for 1 hour to avoid excessive API calls
    CACHE_DURATION = timedelta(hours=1)

    # Model mappings: OpenAI model -> equivalent OpenRouter model IDs
    OPENAI_TO_OPENROUTER = {
        'gpt-4': 'openai/gpt-4',
        'gpt-4-turbo': 'openai/gpt-4-turbo',
        'gpt-4-turbo-preview': 'openai/gpt-4-turbo-preview',
        'gpt-4o': 'openai/gpt-4o',
        'gpt-4o-mini': 'openai/gpt-4o-mini',
        'gpt-3.5-turbo': 'openai/gpt-3.5-turbo',
        'text-embedding-ada-002': 'openai/text-embedding-ada-002',
        'text-embedding-3-small': 'openai/text-embedding-3-small',
        'text-embedding-3-large': 'openai/text-embedding-3-large',
    }

    # Mistral equivalents for migration suggestions
    OPENAI_TO_MISTRAL = {
        'gpt-4': 'mistralai/mistral-large',
        'gpt-4-turbo': 'mistralai/mistral-large',
        'gpt-4-turbo-preview': 'mistralai/mistral-large',
        'gpt-4o': 'mistralai/mistral-large',
        'gpt-4o-mini': 'mistralai/mistral-small',
        'gpt-3.5-turbo': 'mistralai/mistral-small',
        'text-embedding-ada-002': 'mistralai/mistral-embed',
        'text-embedding-3-small': 'mistralai/mistral-embed',
        'text-embedding-3-large': 'mistralai/mistral-embed',
    }

    def __init__(self):
        self._pricing_cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_lock = Lock()  # Thread-safe lock for cache operations
        self.api_key = os.environ.get('OPENROUTER_API_KEY', '')

    def _is_cache_valid(self) -> bool:
        """Check if cached pricing data is still valid"""
        if self._pricing_cache is None or self._cache_timestamp is None:
            return False
        return datetime.now() - self._cache_timestamp < self.CACHE_DURATION

    def _fetch_pricing_data(self, max_retries: int = 3) -> Dict:
        """
        Fetch pricing data from OpenRouter API with retry logic.

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            Dict of model pricing data

        Note:
            Falls back to hardcoded pricing if all retries fail
        """
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        last_error = None

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.OPENROUTER_API_URL,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                # Validate response structure
                if 'data' not in data:
                    raise ValueError("Invalid API response: missing 'data' field")

                # Convert to dict keyed by model ID for easier lookup
                pricing_dict = {}
                for model in data.get('data', []):
                    model_id = model.get('id')
                    pricing = model.get('pricing', {})
                    if model_id and pricing:
                        pricing_dict[model_id] = {
                            'prompt': float(pricing.get('prompt', 0)),
                            'completion': float(pricing.get('completion', 0)),
                            'name': model.get('name', model_id),
                            'context_length': model.get('context_length', 0),
                        }

                # Cache the results
                self._pricing_cache = pricing_dict
                self._cache_timestamp = datetime.now()

                return pricing_dict

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout (attempt {attempt + 1}/{max_retries})"
                print(f"Warning: OpenRouter API timeout: {e}")

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 'unknown'
                last_error = f"HTTP {status_code} (attempt {attempt + 1}/{max_retries})"
                print(f"Warning: OpenRouter API HTTP error {status_code}: {e}")

                # Don't retry on 4xx errors (client errors)
                if e.response and 400 <= e.response.status_code < 500:
                    break

            except requests.exceptions.RequestException as e:
                last_error = f"Network error (attempt {attempt + 1}/{max_retries})"
                print(f"Warning: OpenRouter API network error: {e}")

            except (ValueError, KeyError) as e:
                last_error = f"Invalid response (attempt {attempt + 1}/{max_retries})"
                print(f"Warning: Invalid OpenRouter API response: {e}")
                break  # Don't retry on data format errors

            except Exception as e:
                last_error = f"Unexpected error (attempt {attempt + 1}/{max_retries})"
                print(f"Warning: Unexpected error fetching pricing: {e}")
                break

            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                import time
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait_time)

        print(f"Warning: All retries exhausted. Last error: {last_error}")
        print("Falling back to hardcoded pricing estimates")
        return self._get_fallback_pricing()

    def _get_fallback_pricing(self) -> Dict:
        """Fallback pricing data if OpenRouter API is unavailable"""
        return {
            'openai/gpt-4': {'prompt': 0.00003, 'completion': 0.00006, 'name': 'GPT-4'},
            'openai/gpt-4-turbo': {'prompt': 0.00001, 'completion': 0.00003, 'name': 'GPT-4 Turbo'},
            'openai/gpt-4o': {'prompt': 0.000005, 'completion': 0.000015, 'name': 'GPT-4o'},
            'openai/gpt-4o-mini': {'prompt': 0.00000015, 'completion': 0.0000006, 'name': 'GPT-4o Mini'},
            'openai/gpt-3.5-turbo': {'prompt': 0.0000005, 'completion': 0.0000015, 'name': 'GPT-3.5 Turbo'},
            'mistralai/mistral-large': {'prompt': 0.000008, 'completion': 0.000024, 'name': 'Mistral Large'},
            'mistralai/mistral-small': {'prompt': 0.000001, 'completion': 0.000003, 'name': 'Mistral Small'},
            'mistralai/mistral-embed': {'prompt': 0.0000001, 'completion': 0.0000001, 'name': 'Mistral Embed'},
        }

    def get_pricing_data(self) -> Dict:
        """Get pricing data, using cache if valid or fetching if needed (thread-safe)"""
        # Fast path: check cache without lock
        if self._is_cache_valid():
            return self._pricing_cache

        # Slow path: acquire lock and fetch if still needed
        with self._cache_lock:
            # Double-check after acquiring lock (another thread may have fetched)
            if self._is_cache_valid():
                return self._pricing_cache

            # Fetch new pricing data
            return self._fetch_pricing_data()

    def get_model_pricing(self, model_id: str) -> Optional[Dict]:
        """Get pricing for a specific model"""
        pricing_data = self.get_pricing_data()
        return pricing_data.get(model_id)

    def calculate_cost(
        self,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for a model given token counts.

        Args:
            model_id: OpenRouter model ID (e.g., 'openai/gpt-4')
            prompt_tokens: Number of prompt tokens (must be non-negative)
            completion_tokens: Number of completion tokens (must be non-negative)

        Returns:
            Total cost in dollars

        Raises:
            ValueError: If token counts are negative
        """
        # Validate input
        if prompt_tokens < 0:
            raise ValueError(f"prompt_tokens must be non-negative, got {prompt_tokens}")
        if completion_tokens < 0:
            raise ValueError(f"completion_tokens must be non-negative, got {completion_tokens}")

        pricing = self.get_model_pricing(model_id)
        if not pricing:
            return 0.0

        prompt_cost = prompt_tokens * pricing['prompt']
        completion_cost = completion_tokens * pricing['completion']
        return prompt_cost + completion_cost

    def estimate_migration_savings(
        self,
        estimated_monthly_tokens: Tuple[int, int] = (5_000_000, 5_000_000),
        openai_models: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Estimate cost savings from migrating to Mistral

        Args:
            estimated_monthly_tokens: Tuple of (prompt_tokens, completion_tokens) per month
            openai_models: Dict of {model_name: usage_percentage} for OpenAI models
                          If None, assumes 100% GPT-4 usage

        Returns:
            Dict with cost breakdown and savings

        Raises:
            ValueError: If token counts are negative or usage percentages invalid
        """
        if openai_models is None:
            openai_models = {'gpt-4': 1.0}

        prompt_tokens, completion_tokens = estimated_monthly_tokens

        # Validate token counts
        if prompt_tokens < 0:
            raise ValueError(f"prompt_tokens must be non-negative, got {prompt_tokens}")
        if completion_tokens < 0:
            raise ValueError(f"completion_tokens must be non-negative, got {completion_tokens}")

        # Validate usage percentages
        for model_name, usage_pct in openai_models.items():
            if usage_pct < 0 or usage_pct > 1:
                raise ValueError(f"Usage percentage for {model_name} must be between 0 and 1, got {usage_pct}")

        # Calculate OpenAI costs
        openai_total = 0.0
        openai_breakdown = {}

        for model_short_name, usage_pct in openai_models.items():
            model_id = self.OPENAI_TO_OPENROUTER.get(model_short_name)
            if not model_id:
                continue

            cost = self.calculate_cost(
                model_id,
                int(prompt_tokens * usage_pct),
                int(completion_tokens * usage_pct)
            )
            openai_total += cost
            openai_breakdown[model_short_name] = cost

        # Calculate Mistral costs (using equivalent models)
        mistral_total = 0.0
        mistral_breakdown = {}

        for model_short_name, usage_pct in openai_models.items():
            mistral_model_id = self.OPENAI_TO_MISTRAL.get(model_short_name)
            if not mistral_model_id:
                continue

            cost = self.calculate_cost(
                mistral_model_id,
                int(prompt_tokens * usage_pct),
                int(completion_tokens * usage_pct)
            )
            mistral_total += cost
            mistral_breakdown[model_short_name] = cost

        savings = openai_total - mistral_total
        savings_percentage = (savings / openai_total * 100) if openai_total > 0 else 0

        return {
            'openai_cost': round(openai_total, 2),
            'mistral_cost': round(mistral_total, 2),
            'savings': round(savings, 2),
            'percentage': round(savings_percentage, 1),
            'openai_breakdown': {k: round(v, 2) for k, v in openai_breakdown.items()},
            'mistral_breakdown': {k: round(v, 2) for k, v in mistral_breakdown.items()},
        }

    def get_model_comparison(self, openai_model: str) -> Optional[Dict]:
        """Get side-by-side comparison of OpenAI model vs Mistral equivalent"""
        openai_id = self.OPENAI_TO_OPENROUTER.get(openai_model)
        mistral_id = self.OPENAI_TO_MISTRAL.get(openai_model)

        if not openai_id or not mistral_id:
            return None

        openai_pricing = self.get_model_pricing(openai_id)
        mistral_pricing = self.get_model_pricing(mistral_id)

        if not openai_pricing or not mistral_pricing:
            return None

        # Calculate savings for 1M tokens (equal prompt/completion)
        openai_cost_per_1m = self.calculate_cost(openai_id, 500_000, 500_000)
        mistral_cost_per_1m = self.calculate_cost(mistral_id, 500_000, 500_000)
        savings_per_1m = openai_cost_per_1m - mistral_cost_per_1m
        savings_pct = (savings_per_1m / openai_cost_per_1m * 100) if openai_cost_per_1m > 0 else 0

        return {
            'openai': {
                'id': openai_id,
                'name': openai_pricing['name'],
                'prompt_price': openai_pricing['prompt'],
                'completion_price': openai_pricing['completion'],
                'cost_per_1m_tokens': round(openai_cost_per_1m, 2),
            },
            'mistral': {
                'id': mistral_id,
                'name': mistral_pricing['name'],
                'prompt_price': mistral_pricing['prompt'],
                'completion_price': mistral_pricing['completion'],
                'cost_per_1m_tokens': round(mistral_cost_per_1m, 2),
            },
            'savings': {
                'per_1m_tokens': round(savings_per_1m, 2),
                'percentage': round(savings_pct, 1),
            }
        }
