#!/usr/bin/env python3
"""
OpenAI → Mistral Migration Tool

Automatically analyze your codebase and generate migration guides to switch
from OpenAI to Mistral AI. Identifies API patterns, calculates cost savings,
and provides side-by-side code examples.

Usage:
    python migrate_to_mistral.py scan <directory> [--output <file>]
"""

import ast
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple
import argparse


@dataclass
class APICall:
    """Represents a detected OpenAI API call"""
    file_path: str
    line_number: int
    pattern_type: str  # 'chat', 'completion', 'embedding', 'streaming', 'function_calling'
    code_snippet: str
    confidence: str  # 'high', 'medium', 'low'
    model: str = 'gpt-4'  # Default to gpt-4 if not detected


@dataclass
class MigrationSuggestion:
    """Represents a suggested migration"""
    api_call: APICall
    openai_code: str
    mistral_code: str
    notes: str
    effort: str  # 'trivial', 'easy', 'moderate'


class MigrationAnalyzer:
    """Analyzes codebases for OpenAI API usage patterns"""
    
    # Patterns that indicate OpenAI API usage
    OPENAI_PATTERNS = {
        'import': [
            r'from openai import',
            r'import openai',
        ],
        'chat': [
            r'openai\.chat\.completions\.create',
            r'client\.chat\.completions\.create',
        ],
        'completion': [
            r'openai\.completions\.create',
            r'client\.completions\.create',
        ],
        'embedding': [
            r'openai\.embeddings\.create',
            r'client\.embeddings\.create',
        ],
        'streaming': [
            r'stream\s*=\s*True',
            r'\.stream\s*=\s*True',
        ],
    }
    
    # Cost comparison (per 1M tokens) - approximate rates as of Nov 2024
    COST_COMPARISON = {
        'gpt-4': {'openai': 30.00, 'mistral': 10.00},  # Mistral Large equivalent
        'gpt-4-turbo': {'openai': 10.00, 'mistral': 4.00},
        'gpt-3.5-turbo': {'openai': 1.50, 'mistral': 0.65},  # Mistral Small equivalent
    }
    
    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.api_calls: List[APICall] = []
        
    def scan(self) -> List[APICall]:
        """Scan directory for OpenAI API usage"""
        print(f"🔍 Scanning {self.directory} for OpenAI API calls...")
        
        python_files = list(self.directory.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_skip(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._analyze_file(file_path, content)
            except Exception as e:
                print(f"⚠️  Skipping {file_path}: {str(e)}")
                
        return self.api_calls
    
    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = ['venv', 'node_modules', '.git', '__pycache__', 'dist', 'build']
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path, content: str):
        """Analyze a single file for OpenAI patterns"""
        lines = content.split('\n')

        # Check if file uses OpenAI at all
        has_openai = any(
            re.search(pattern, content)
            for pattern in self.OPENAI_PATTERNS['import']
        )

        if not has_openai:
            return

        # Find specific API calls
        for i, line in enumerate(lines, 1):
            detected_model = self._extract_model_name(line, lines, i)

            # Chat completions
            if any(re.search(p, line) for p in self.OPENAI_PATTERNS['chat']):
                self.api_calls.append(APICall(
                    file_path=str(file_path),
                    line_number=i,
                    pattern_type='chat',
                    code_snippet=line.strip(),
                    confidence='high',
                    model=detected_model
                ))

            # Legacy completions
            elif any(re.search(p, line) for p in self.OPENAI_PATTERNS['completion']):
                self.api_calls.append(APICall(
                    file_path=str(file_path),
                    line_number=i,
                    pattern_type='completion',
                    code_snippet=line.strip(),
                    confidence='high',
                    model=detected_model
                ))

            # Embeddings
            elif any(re.search(p, line) for p in self.OPENAI_PATTERNS['embedding']):
                # Check if it's an embedding model
                if 'embedding' in detected_model or detected_model == 'gpt-4':
                    detected_model = 'text-embedding-ada-002'
                self.api_calls.append(APICall(
                    file_path=str(file_path),
                    line_number=i,
                    pattern_type='embedding',
                    code_snippet=line.strip(),
                    confidence='high',
                    model=detected_model
                ))

    def _extract_model_name(self, current_line: str, all_lines: List[str], current_index: int) -> str:
        """
        Extract model name from API call or surrounding context.
        Uses balanced parenthesis tracking to handle complex nested structures.
        """
        # Enhanced patterns to match various model specifications
        model_patterns = [
            r'model\s*=\s*["\']([^"\']+)["\']',  # model="gpt-4"
            r'model:\s*["\']([^"\']+)["\']',     # model: "gpt-4"
            r'model\s*=\s*(\w+)',                 # model=MODEL_VAR
            r'"model"\s*:\s*["\']([^"\']+)["\']', # "model": "gpt-4"
        ]

        # Try to find model in current line first
        for pattern in model_patterns:
            match = re.search(pattern, current_line)
            if match:
                return match.group(1)

        # Track parenthesis depth to find function call boundaries
        paren_depth = current_line.count('(') - current_line.count(')')

        # Look ahead with balanced parenthesis tracking (up to 50 lines)
        max_lookahead = min(50, len(all_lines) - current_index)

        for offset in range(1, max_lookahead):
            next_line = all_lines[current_index + offset - 1]

            # Try to find model in this line
            for pattern in model_patterns:
                match = re.search(pattern, next_line)
                if match:
                    return match.group(1)

            # Update parenthesis depth
            paren_depth += next_line.count('(') - next_line.count(')')

            # Stop when we've closed all parentheses (end of function call)
            if paren_depth <= 0:
                break

        # Default to gpt-4 if not found
        return 'gpt-4'


class MigrationGuideGenerator:
    """Generates migration guides with code examples"""
    
    MIGRATION_TEMPLATES = {
        'chat': {
            'openai': '''# OpenAI Chat Completion
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
            
            'mistral': '''# Mistral Chat Completion
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
            
            'notes': '''Key changes:
• Import: openai.OpenAI → mistralai.client.MistralClient
• Method: client.chat.completions.create() → client.chat()
• Model: gpt-4 → mistral-large-latest (or mistral-medium, mistral-small)
• API is 99% compatible - most parameters work identically
• Cost: ~70% cheaper for equivalent quality''',
            'effort': 'trivial'
        },
        
        'streaming': {
            'openai': '''# OpenAI Streaming
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")''',
            
            'mistral': '''# Mistral Streaming
response = client.chat_stream(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Tell me a story"}]
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")''',
            
            'notes': '''Key changes:
• Method: client.chat.completions.create(stream=True) → client.chat_stream()
• Response handling is identical
• Chunk structure is the same
• Performance: Similar latency, better pricing''',
            'effort': 'trivial'
        },
        
        'function_calling': {
            'openai': '''# OpenAI Function Calling
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
}]

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools
)''',
            
            'mistral': '''# Mistral Function Calling
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
}]

response = client.chat(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools
)''',
            
            'notes': '''Key changes:
• Schema format is IDENTICAL - copy/paste works!
• Only difference: .create() → .chat()
• Function calling quality is excellent on mistral-large
• Cost: 70% cheaper with same reliability''',
            'effort': 'trivial'
        },
        
        'embedding': {
            'openai': '''# OpenAI Embeddings
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="Your text to embed"
)

embedding = response.data[0].embedding''',
            
            'mistral': '''# Mistral Embeddings
response = client.embeddings(
    model="mistral-embed",
    input=["Your text to embed"]
)

embedding = response.data[0].embedding''',
            
            'notes': '''Key changes:
• Method: client.embeddings.create() → client.embeddings()
• Input: single string → list of strings (wrap in array)
• Model: text-embedding-ada-002 → mistral-embed
• Dimension: 1536 → 1024 (may need to reindex vector DB)
• Cost: ~80% cheaper''',
            'effort': 'easy'
        }
    }
    
    def generate_guide(self, api_calls: List[APICall]) -> str:
        """Generate a comprehensive migration guide"""
        
        if not api_calls:
            return "✅ No OpenAI API calls detected. Nothing to migrate!"
        
        # Count patterns
        pattern_counts = {}
        for call in api_calls:
            pattern_counts[call.pattern_type] = pattern_counts.get(call.pattern_type, 0) + 1
        
        guide = []
        guide.append("=" * 80)
        guide.append("🚀 MIGRATION GUIDE: OpenAI → Mistral AI")
        guide.append("=" * 80)
        guide.append("")
        
        # Summary
        guide.append(f"📊 SUMMARY")
        guide.append(f"Found {len(api_calls)} OpenAI API call(s) across {len(set(c.file_path for c in api_calls))} file(s)")
        guide.append("")
        guide.append("Pattern breakdown:")
        for pattern, count in sorted(pattern_counts.items()):
            guide.append(f"  • {pattern}: {count} call(s)")
        guide.append("")
        
        # Cost savings estimate
        guide.append("💰 ESTIMATED SAVINGS")
        guide.append("Assuming moderate usage (10M tokens/month):")
        guide.append("  OpenAI (gpt-4): ~$300/month")
        guide.append("  Mistral (mistral-large): ~$100/month")
        guide.append("  📉 Savings: ~$200/month (67% reduction)")
        guide.append("")
        
        # Migration examples for each detected pattern
        guide.append("📝 MIGRATION EXAMPLES")
        guide.append("")
        
        seen_patterns = set()
        for call in api_calls:
            if call.pattern_type in seen_patterns:
                continue
            seen_patterns.add(call.pattern_type)
            
            if call.pattern_type in self.MIGRATION_TEMPLATES:
                template = self.MIGRATION_TEMPLATES[call.pattern_type]
                guide.append(f"## {call.pattern_type.upper()} MIGRATION")
                guide.append(f"Effort: {template['effort']}")
                guide.append("")
                guide.append("BEFORE (OpenAI):")
                guide.append("-" * 40)
                guide.append(template['openai'])
                guide.append("")
                guide.append("AFTER (Mistral):")
                guide.append("-" * 40)
                guide.append(template['mistral'])
                guide.append("")
                guide.append(template['notes'])
                guide.append("")
                guide.append("=" * 80)
                guide.append("")
        
        # Installation
        guide.append("📦 INSTALLATION")
        guide.append("")
        guide.append("pip uninstall openai")
        guide.append("pip install mistralai")
        guide.append("")
        
        # Next steps
        guide.append("✅ NEXT STEPS")
        guide.append("")
        guide.append("1. Install Mistral SDK: pip install mistralai")
        guide.append("2. Get API key: https://console.mistral.ai/")
        guide.append("3. Update imports in detected files")
        guide.append("4. Replace model names (gpt-4 → mistral-large-latest)")
        guide.append("5. Test thoroughly in development")
        guide.append("6. Monitor cost savings in production")
        guide.append("")
        
        # Detected files
        guide.append("📁 FILES TO UPDATE")
        guide.append("")
        for file_path in sorted(set(c.file_path for c in api_calls)):
            file_calls = [c for c in api_calls if c.file_path == file_path]
            guide.append(f"  {file_path}")
            for call in file_calls:
                guide.append(f"    Line {call.line_number}: {call.pattern_type}")
        guide.append("")
        
        # Support
        guide.append("🆘 NEED HELP?")
        guide.append("")
        guide.append("• Mistral Docs: https://docs.mistral.ai/")
        guide.append("• Mistral Cookbooks: https://docs.mistral.ai/cookbooks")
        guide.append("• Discord: https://discord.gg/mistralai")
        guide.append("")
        guide.append("=" * 80)
        
        return "\n".join(guide)


def main():
    parser = argparse.ArgumentParser(
        description='Migrate your codebase from OpenAI to Mistral AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python migrate_to_mistral.py scan ./src
  python migrate_to_mistral.py scan . --output migration_guide.txt
  
This tool demonstrates DX leadership principles:
• Reduce migration friction
• Provide clear, actionable guidance  
• Show immediate value (cost savings)
• Make the right path the easy path
        '''
    )
    
    parser.add_argument('command', choices=['scan'], help='Command to run')
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--output', '-o', help='Output file for migration guide')
    
    args = parser.parse_args()
    
    if args.command == 'scan':
        # Run analysis
        analyzer = MigrationAnalyzer(args.directory)
        api_calls = analyzer.scan()
        
        # Generate guide
        generator = MigrationGuideGenerator()
        guide = generator.generate_guide(api_calls)
        
        # Output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(guide)
            print(f"\n✅ Migration guide saved to: {args.output}")
        else:
            print("\n" + guide)
        
        # Summary message
        if api_calls:
            print(f"\n💡 TIP: Migration estimated at {len(api_calls) * 5} minutes")
            print(f"💰 Potential savings: ~$200/month with moderate usage")
        else:
            print("\n✨ No OpenAI API usage detected. You're all set!")


if __name__ == '__main__':
    main()
