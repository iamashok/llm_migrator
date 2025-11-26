#!/usr/bin/env python3
"""
Flask web UI for the OpenAI to Mistral migration tool
"""
from flask import Flask, render_template, request, jsonify
import os
import tempfile
import shutil
import subprocess
import re
from pathlib import Path
from migrate_to_mistral import MigrationAnalyzer
from pricing_service import PricingService

app = Flask(__name__)

# Store for temporary directories (for cleanup)
temp_dirs = []

# Initialize pricing service
pricing_service = PricingService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    """Scan a directory for OpenAI usage"""
    try:
        data = request.get_json()
        scan_path = data.get('path', '.')

        # Validate path
        if not os.path.exists(scan_path):
            return jsonify({'error': f'Path does not exist: {scan_path}'}), 400

        # Run the analyzer
        analyzer = MigrationAnalyzer(scan_path)
        api_calls = analyzer.scan()

        # Process results
        results = process_api_calls(api_calls)

        # Calculate real cost savings
        cost_savings = calculate_real_cost_savings(api_calls)

        # Format results for UI
        response = {
            'summary': {
                'total_calls': results['total_calls'],
                'files_affected': results['files_affected'],
                'patterns': results['patterns'],
                'models': results['models']
            },
            'files': results['files'],
            'cost_savings': cost_savings,
            'examples': get_migration_examples(results['patterns']),
            'effort_estimate': calculate_effort(results['total_calls'])
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/demo', methods=['GET'])
def demo():
    """Run a demo scan on the example files"""
    try:
        analyzer = MigrationAnalyzer('.')
        api_calls = analyzer.scan()

        # Process results
        results = process_api_calls(api_calls)

        # Calculate real cost savings
        cost_savings = calculate_real_cost_savings(api_calls)

        response = {
            'summary': {
                'total_calls': results['total_calls'],
                'files_affected': results['files_affected'],
                'patterns': results['patterns'],
                'models': results['models']
            },
            'files': results['files'],
            'cost_savings': cost_savings,
            'examples': get_migration_examples(results['patterns']),
            'effort_estimate': calculate_effort(results['total_calls'])
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scan-github', methods=['POST'])
def scan_github():
    """Scan a GitHub repository for OpenAI usage"""
    temp_dir = None
    try:
        data = request.get_json()
        github_url = data.get('url', '').strip()

        if not github_url:
            return jsonify({'error': 'Please provide a GitHub URL'}), 400

        # Validate GitHub URL
        if not is_valid_github_url(github_url):
            return jsonify({'error': 'Invalid GitHub URL. Must be a public GitHub repository URL'}), 400

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='migrate_scan_')
        temp_dirs.append(temp_dir)

        # Clone the repository
        try:
            clone_result = subprocess.run(
                ['git', 'clone', '--depth', '1', github_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=60
            )

            if clone_result.returncode != 0:
                return jsonify({'error': f'Failed to clone repository: {clone_result.stderr}'}), 400

        except subprocess.TimeoutExpired:
            return jsonify({'error': 'Repository clone timed out. Repository may be too large.'}), 400
        except Exception as e:
            return jsonify({'error': f'Error cloning repository: {str(e)}'}), 400

        # Run the analyzer on cloned repo
        analyzer = MigrationAnalyzer(temp_dir)
        api_calls = analyzer.scan()

        # Process results
        results = process_api_calls(api_calls)

        # Clean up file paths to be relative
        cleaned_files = {}
        for file_path, locations in results['files'].items():
            rel_path = str(Path(file_path).relative_to(temp_dir))
            cleaned_files[rel_path] = locations

        # Calculate real cost savings
        cost_savings = calculate_real_cost_savings(api_calls)

        response = {
            'summary': {
                'total_calls': results['total_calls'],
                'files_affected': results['files_affected'],
                'patterns': results['patterns'],
                'models': results['models'],
                'repo_url': github_url
            },
            'files': cleaned_files,
            'cost_savings': cost_savings,
            'examples': get_migration_examples(results['patterns']),
            'effort_estimate': calculate_effort(results['total_calls'])
        }

        # Cleanup temp directory
        cleanup_temp_dir(temp_dir)

        return jsonify(response)

    except Exception as e:
        # Cleanup on error
        if temp_dir:
            cleanup_temp_dir(temp_dir)
        return jsonify({'error': str(e)}), 500

def process_api_calls(api_calls):
    """Process APICall objects into summary format"""
    files = {}
    patterns = {}
    models = {}

    for call in api_calls:
        # Group by file
        if call.file_path not in files:
            files[call.file_path] = []
        files[call.file_path].append({
            'line': call.line_number,
            'pattern_type': call.pattern_type,
            'model': call.model
        })

        # Count patterns
        patterns[call.pattern_type] = patterns.get(call.pattern_type, 0) + 1

        # Count models
        models[call.model] = models.get(call.model, 0) + 1

    return {
        'total_calls': len(api_calls),
        'files_affected': len(files),
        'patterns': patterns,
        'files': files,
        'models': models
    }

def calculate_real_cost_savings(api_calls, estimated_monthly_tokens=(5_000_000, 5_000_000)):
    """Calculate real cost savings using OpenRouter pricing"""
    if not api_calls:
        return {
            'openai_cost': 0,
            'mistral_cost': 0,
            'savings': 0,
            'percentage': 0
        }

    # Count model usage
    model_counts = {}
    for call in api_calls:
        model_counts[call.model] = model_counts.get(call.model, 0) + 1

    total_calls = len(api_calls)

    # Calculate usage percentage for each model
    openai_models = {}
    for model, count in model_counts.items():
        openai_models[model] = count / total_calls

    # Use pricing service to estimate costs
    return pricing_service.estimate_migration_savings(
        estimated_monthly_tokens=estimated_monthly_tokens,
        openai_models=openai_models
    )

def get_migration_examples(patterns):
    """Get migration examples based on detected patterns"""
    examples = []

    if 'chat' in patterns:
        examples.append({
            'type': 'Chat Completion',
            'difficulty': 'trivial',
            'before': '''# OpenAI Chat Completion
from openai import OpenAI

client = OpenAI(api_key="your-openai-key")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=150
)

print(response.choices[0].message.content)''',
            'after': '''# Mistral Chat Completion
from mistralai.client import MistralClient

client = MistralClient(api_key="your-mistral-key")

response = client.chat(
    model="mistral-large-latest",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=150
)

print(response.choices[0].message.content)''',
            'key_changes': [
                'Import: openai.OpenAI → mistralai.client.MistralClient',
                'Method: client.chat.completions.create() → client.chat()',
                'Model: gpt-4 → mistral-large-latest',
                'API is 99% compatible',
                'Cost: ~70% cheaper'
            ]
        })

    if 'embedding' in patterns:
        examples.append({
            'type': 'Embeddings',
            'difficulty': 'easy',
            'before': '''# OpenAI Embeddings
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="Your text to embed"
)

embedding = response.data[0].embedding''',
            'after': '''# Mistral Embeddings
response = client.embeddings(
    model="mistral-embed",
    input=["Your text to embed"]
)

embedding = response.data[0].embedding''',
            'key_changes': [
                'Method: client.embeddings.create() → client.embeddings()',
                'Input: single string → list of strings',
                'Model: text-embedding-ada-002 → mistral-embed',
                'Dimension: 1536 → 1024',
                'Cost: ~80% cheaper'
            ]
        })

    return examples

def calculate_effort(total_calls):
    """Calculate effort estimate in minutes"""
    if total_calls == 0:
        return 0
    elif total_calls <= 5:
        return 15
    elif total_calls <= 20:
        return 60
    elif total_calls <= 50:
        return 120
    else:
        return 240

def is_valid_github_url(url):
    """Validate if URL is a proper GitHub repository URL"""
    patterns = [
        r'^https?://github\.com/[\w\-]+/[\w\-\.]+/?$',
        r'^https?://github\.com/[\w\-]+/[\w\-\.]+\.git$',
        r'^git@github\.com:[\w\-]+/[\w\-\.]+\.git$'
    ]
    return any(re.match(pattern, url) for pattern in patterns)

def cleanup_temp_dir(temp_dir):
    """Safely cleanup temporary directory"""
    try:
        if temp_dir in temp_dirs:
            temp_dirs.remove(temp_dir)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Failed to cleanup {temp_dir}: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    finally:
        # Cleanup all temp directories on exit
        for temp_dir in temp_dirs:
            cleanup_temp_dir(temp_dir)
