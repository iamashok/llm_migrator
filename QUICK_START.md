# Quick Start - Test This Tool in 60 Seconds

Want to see the tool in action immediately? Here's how:

## Option 1: Test on the Included Examples (Recommended)

```bash
# Navigate to the project directory
cd openai-to-mistral

# Run the scanner on the example OpenAI code
python migrate_to_mistral.py scan ./examples

# That's it! You'll see a full migration guide with:
# - Detected API calls
# - Cost savings estimate  
# - Side-by-side code examples
# - Files to update
```

**Expected output:** Detection of 5 OpenAI API calls, $200/month savings estimate

---

## Option 2: Save Output to File

```bash
python migrate_to_mistral.py scan ./examples --output my_migration_guide.txt

# Now you can view the guide in your editor
cat my_migration_guide.txt
```

---

## Option 3: Test on Your Own Code

```bash
# Scan your actual codebase
python migrate_to_mistral.py scan /path/to/your/project

# Or scan current directory
python migrate_to_mistral.py scan .
```

---

## What You'll See

The tool outputs a comprehensive migration guide including:

✅ **Summary**
- Number of API calls detected
- Pattern breakdown (chat, streaming, embeddings, etc.)
- Cost savings estimate

✅ **Migration Examples**
- BEFORE code (OpenAI)
- AFTER code (Mistral)
- Key changes highlighted
- Migration effort estimate

✅ **Next Steps**
- Installation instructions
- Files to update with line numbers
- Links to Mistral docs and support

---

## Example Output Preview

```
🔍 Scanning ./examples for OpenAI API calls...

================================================================================
🚀 MIGRATION GUIDE: OpenAI → Mistral AI
================================================================================

📊 SUMMARY
Found 5 OpenAI API call(s) across 1 file(s)

Pattern breakdown:
  • chat: 3 call(s)
  • embedding: 2 call(s)

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

[... more examples ...]
```

---

## Compare Before and After Code

Want to see exactly what changes? Compare the example files:

```bash
# View the original OpenAI code
cat examples/example_openai_app.py

# View the migrated Mistral code
cat examples/example_mistral_app.py

# Or use diff to see changes
diff examples/example_openai_app.py examples/example_mistral_app.py
```

---

## Verify the Tool Works

Quick smoke test:

```bash
# Should detect 5 OpenAI API calls
python migrate_to_mistral.py scan ./examples | grep "Found"
# Output: Found 5 OpenAI API call(s) across 1 file(s)
```

---

## Troubleshooting

**"python: command not found"**
→ Try `python3` instead: `python3 migrate_to_mistral.py scan ./examples`

**"No OpenAI API calls detected"**
→ Make sure you're scanning a directory with Python files that use OpenAI
→ The tool only detects `from openai import` or `import openai` patterns

**"Permission denied"**
→ Make the script executable: `chmod +x migrate_to_mistral.py`

---

## Next Steps

Once you've tested it:

1. ✅ Read `README.md` for full documentation
2. ✅ Check `MIGRATION_GUIDE.md` for quick reference
3. ✅ Read `HOW_TO_USE_IN_APPLICATION.md` for positioning strategy
4. ✅ Review `BLOG_POST.md` for thought leadership content
5. ✅ Create GitHub repository and push the code
6. ✅ Update your application materials

---

## Share Your Results

Test it and it works? Great!

- Star the repo (once you create it)
- Share on LinkedIn with your migration story
- Tag @MistralAI and mention potential savings
- Include in your application

---

**Ready to test?**

```bash
cd openai-to-mistral
python migrate_to_mistral.py scan ./examples
```

**That's it! You'll see the full migration guide in under 60 seconds.**
