# LLM Migrator
# Version 1- OpenAI → Mistral Migration Tool

**Automatically analyze your codebase and generate migration guides to switch from OpenAI to Mistral AI.**

Scan your project, identify OpenAI API usage, and get side-by-side code comparisons with cost savings analysis.

---

## Quick Start

```bash
# Scan your codebase
python migrate_to_mistral.py scan ./src

# Save migration guide to file
python migrate_to_mistral.py scan ./src --output migration_guide.txt

# Try the web UI
python3 app.py
# Visit http://localhost:5000
```

---

## Features

- 🔍 **Automatic Detection** - Scans Python codebases for OpenAI API patterns
- 📊 **Cost Analysis** - Calculates potential savings from switching to Mistral
- 📝 **Migration Examples** - Generates side-by-side code comparisons
- 🌐 **Web Interface** - Modern UI with GitHub repository scanning
- 🎯 **Effort Estimates** - Shows migration complexity for each pattern
- 📁 **File Mapping** - Lists exact files and line numbers to update

---

## Example Output

```
🔍 Scanning ./examples for OpenAI API calls...

================================================================================
🚀 MIGRATION GUIDE: OpenAI → Mistral AI
================================================================================

📊 SUMMARY
Found 5 OpenAI API call(s) across 1 file(s)

Pattern breakdown:
  • chat: 2 call(s)
  • embedding: 2 call(s)
  • streaming: 1 call(s)

💰 ESTIMATED SAVINGS
Assuming moderate usage (10M tokens/month):
  OpenAI (gpt-4): ~$300/month
  Mistral (mistral-large): ~$100/month
  📉 Savings: ~$200/month (67% reduction)

📝 MIGRATION EXAMPLES

## CHAT MIGRATION
Effort: trivial

BEFORE (OpenAI):
----------------------------------------
from openai import OpenAI
client = OpenAI(api_key="your-key")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

AFTER (Mistral):
----------------------------------------
from mistralai.client import MistralClient
client = MistralClient(api_key="your-key")

response = client.chat(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Supported Patterns

The tool identifies these OpenAI API patterns:

| Pattern | Difficulty | Savings |
|---------|-----------|---------|
| **Chat Completions** | Trivial | 70% |
| **Streaming** | Trivial | 70% |
| **Function Calling** | Trivial | 70% |
| **Embeddings** | Easy | 80% |

---

## Web Interface

Launch the web UI for an interactive experience:

```bash
# Install Flask (only dependency for web UI)
pip install flask

# Start the server
python3 app.py
```

Features:
- **Local Directory Scanning** - Analyze projects on your machine
- **GitHub Repository Scanning** - Clone and analyze any public repo
- **Visual Cost Comparison** - Interactive charts and statistics
- **Downloadable Reports** - Export migration guides

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/openai-to-mistral
cd openai-to-mistral

# No dependencies for CLI! Uses only Python stdlib
python migrate_to_mistral.py scan ./your-project

# For web UI, install Flask
pip install flask
```

---

## Migration Example: RAG Application

**Before (OpenAI):**
```python
from openai import OpenAI
import pinecone

client = OpenAI()

# Generate embedding
embedding = client.embeddings.create(
    model="text-embedding-ada-002",
    input=query
).data[0].embedding

# Chat with context
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Answer based on context"},
        {"role": "user", "content": f"Context: {results}\n\nQuestion: {query}"}
    ]
)
```

**After (Mistral):**
```python
from mistralai.client import MistralClient
import pinecone

client = MistralClient()

# Generate embedding
embedding = client.embeddings(
    model="mistral-embed",
    input=[query]  # Note: wrap in list
).data[0].embedding

# Chat with context
response = client.chat(
    model="mistral-large-latest",
    messages=[
        {"role": "system", "content": "Answer based on context"},
        {"role": "user", "content": f"Context: {results}\n\nQuestion: {query}"}
    ]
)
```

**Changes:**
1. Import statement (1 line)
2. Embedding method (1 line)
3. Chat method (1 line)
4. Model names (2 places)

**Time:** 5 minutes
**Savings:** ~70% on inference costs
**Risk:** Low (API is 95% compatible)

---

## Model Mapping

| OpenAI Model | Mistral Equivalent | Use Case |
|--------------|-------------------|----------|
| gpt-4 / gpt-4-turbo | mistral-large-latest | Complex reasoning, code |
| gpt-3.5-turbo | mistral-small-latest | Simple tasks, high volume |
| text-embedding-ada-002 | mistral-embed | Embeddings for RAG |

---

## Cost Comparison (Per 1M Tokens)

### Chat Completions

| Model | OpenAI Price | Mistral Price | Savings |
|-------|--------------|---------------|---------|
| **High-end** | $30 (GPT-4) | $10 (Large) | 67% |
| **Mid-tier** | $10 (GPT-4 Turbo) | $4 (Large) | 60% |
| **Volume** | $1.50 (GPT-3.5) | $0.65 (Small) | 57% |

### Embeddings

| Model | OpenAI Price | Mistral Price | Savings |
|-------|--------------|---------------|---------|
| **Standard** | $0.13 (Ada-002) | $0.02 (mistral-embed) | 85% |

### Real-World Example

**Scenario:** AI support chatbot processing 10M tokens/month

- OpenAI (gpt-4): **$300/month**
- Mistral (large): **$100/month**
- **Annual savings: $2,400**

For a startup with 5 AI features, that's **$12k/year** in savings.

---

## Architecture

```
migrate_to_mistral.py
├── MigrationAnalyzer      # Scans code for OpenAI patterns
│   ├── Pattern matching (regex)
│   ├── AST analysis for context
│   └── Confidence scoring
│
└── MigrationGuideGenerator # Creates actionable guides
    ├── Code diffs (before/after)
    ├── Cost calculations
    └── Effort estimates

app.py                     # Flask web application
├── GitHub repository cloning
├── Temporary file management
└── REST API endpoints
```

---

## Limitations

- **Python only** - JavaScript/TypeScript support planned for v2
- **Pattern-based detection** - May miss dynamic or obfuscated usage
- **No auto-rewriting** - Generates guides for manual migration (safer)
- **Requires testing** - Always test migrated code thoroughly

---

## Roadmap

**v1.0** (Current)
- ✅ Python codebase scanning
- ✅ Pattern detection for chat, streaming, embeddings
- ✅ Side-by-side code examples
- ✅ Cost calculations
- ✅ Web UI with GitHub scanning

**v2.0** (Planned)
- [ ] JavaScript/TypeScript support
- [ ] Auto-generate PR with migrations
- [ ] Integration tests generation
- [ ] Performance comparison reports

**v3.0** (Future)
- [ ] CI/CD integration
- [ ] Gradual rollout strategies
- [ ] A/B testing framework
- [ ] Real-time cost monitoring

---

## Contributing

Contributions are welcome! Here's how you can help:

- **Report bugs** - Open an issue with reproduction steps
- **Suggest patterns** - Help us detect more OpenAI API patterns
- **Add features** - Submit PRs for new functionality
- **Improve docs** - Better examples, clearer explanations

---

## License

MIT License - feel free to use, modify, and share.

---

**Try it now:** `python migrate_to_mistral.py scan ./your-code`
