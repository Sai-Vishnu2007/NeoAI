# LLM Provider Setup Guide

This guide explains how to configure your AI Agent to use different LLM providers: **DeepSeek Cloud API**, **Google Gemini**, or **Local Ollama**.

---

## 📋 Overview

Your backend has been refactored to support three LLM providers:

| Provider | Type | Best For | Reasoning Support |
|----------|------|----------|-------------------|
| **DeepSeek** | Cloud API | Advanced reasoning (R1 model) | ✅ Yes (via `<think>` tags) |
| **Gemini** | Cloud API | Fast, cost-effective responses | ⚠️ Limited (no think tags) |
| **Local Ollama** | Local | Privacy, offline usage | ✅ Yes (via `<think>` tags) |

---

## 🚀 Quick Start

### Step 1: Install New Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `openai>=1.0.0` (for DeepSeek via OpenAI SDK)
- `google-generativeai>=0.3.0` (for Gemini)
- Existing dependencies remain unchanged

### Step 2: Configure Your .env File

Your `.env` file now includes these new variables:

```env
# LLM Provider Configuration
LLM_PROVIDER=deepseek  # Options: "deepseek", "gemini", "local"

# DeepSeek Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-reasoner  # or deepseek-chat

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-thinking-exp-01-21  # or gemini-1.5-flash

# Local Ollama Configuration (backup)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1
```

### Step 3: Get Your API Keys

#### 🔑 DeepSeek API Key
1. Visit: https://platform.deepseek.com/
2. Sign up or log in
3. Go to "API Keys" section
4. Create a new API key
5. Copy the key and paste it in `.env` as `DEEPSEEK_API_KEY`

**Recommended Models:**
- `deepseek-reasoner` - For R1 reasoning model (with `<think>` tags)
- `deepseek-chat` - For V3 chat model (faster, no reasoning)

#### 🔑 Google Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it in `.env` as `GEMINI_API_KEY`

**Recommended Models:**
- `gemini-2.0-flash-thinking-exp-01-21` - Latest thinking model
- `gemini-1.5-flash` - Fast, stable model
- `gemini-1.5-pro` - Most capable model

---

## ⚙️ Configuration Details

### Option 1: DeepSeek Cloud (Recommended for Reasoning)

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-reasoner
```

**Features:**
- ✅ Advanced reasoning with `<think>` tags
- ✅ Separates thought process from final answer
- ✅ Excellent for complex problem-solving
- 💰 Pay-as-you-go pricing

**Use Case:** When you need transparent reasoning and step-by-step thinking

---

### Option 2: Google Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXX
GEMINI_MODEL=gemini-2.0-flash-thinking-exp-01-21
```

**Features:**
- ✅ Very fast responses
- ✅ Multimodal capabilities (if needed later)
- ⚠️ No native `<think>` tags (thought_process will be empty)
- 💰 Free tier available with generous quotas

**Use Case:** When you need fast, reliable responses without explicit reasoning

---

### Option 3: Local Ollama (Legacy/Backup)

```env
LLM_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1
```

**Features:**
- ✅ Complete privacy (runs locally)
- ✅ No API costs
- ✅ Supports `<think>` tags (with DeepSeek R1)
- ⚠️ Requires powerful hardware
- ⚠️ Slower than cloud APIs

**Use Case:** When privacy is critical or you're offline

---

## 🔄 Switching Between Providers

To switch providers, simply change the `LLM_PROVIDER` value in your `.env` file:

```bash
# For DeepSeek
LLM_PROVIDER=deepseek

# For Gemini
LLM_PROVIDER=gemini

# For Local Ollama
LLM_PROVIDER=local
```

Then restart your backend server:

```bash
python start_server.py
```

The system will automatically initialize the correct client on startup.

---

## 🧪 Testing Your Setup

### Test from Command Line

Run the LLM engine directly to test your configuration:

```bash
python backend/llm_engine.py
```

This will:
1. Load your `.env` configuration
2. Initialize the selected LLM provider
3. Test the connection
4. Run a sample prompt
5. Display the response with thought process (if available)

### Expected Output

**For DeepSeek:**
```
🚀 Initializing DeepSeek client (Cloud API via OpenAI SDK)
✓ Connected to LLM provider successfully

Prompt: What is the capital of France? Explain briefly.

Generating response...

================================================================================
THOUGHT PROCESS:
================================================================================
The question is asking for the capital of France. This is straightforward 
geographical knowledge. The capital of France is Paris.

================================================================================
FINAL ANSWER:
================================================================================
The capital of France is Paris. It is the country's largest city and has been 
the capital since the 12th century.
```

**For Gemini:**
```
🚀 Initializing Google Gemini client (Cloud API)
✓ Connected to LLM provider successfully

Prompt: What is the capital of France? Explain briefly.

Generating response...

================================================================================
THOUGHT PROCESS:
================================================================================
(No explicit thought process)

================================================================================
FINAL ANSWER:
================================================================================
The capital of France is Paris. It is the country's largest city and serves as 
its political, economic, and cultural center.
```

---

## 🔍 Understanding the Response Format

All providers return a consistent format to `main.py`:

```python
{
    "thought_process": "...",  # Reasoning (empty for Gemini)
    "final_answer": "...",     # The actual response
    "full_response": "..."     # Raw output from the model
}
```

This ensures your **frontend doesn't need any changes** - it will work seamlessly with all providers.

---

## 💡 Recommendations

### For Production Use:
- **Primary:** DeepSeek (for reasoning capabilities)
- **Fallback:** Gemini (for speed and reliability)
- **Backup:** Local Ollama (for high-priority data)

### Cost Optimization:
- Use **Gemini** for simple queries
- Use **DeepSeek** for complex reasoning tasks
- Implement provider switching based on query complexity

### Development:
- Use **Gemini** free tier during development
- Switch to **DeepSeek** for reasoning testing
- Use **Local Ollama** when offline

---

## 🐛 Troubleshooting

### Error: "Invalid LLM_PROVIDER"
**Solution:** Check that `LLM_PROVIDER` in `.env` is one of: `deepseek`, `gemini`, or `local`

### Error: "API key not provided"
**Solution:** Ensure your API key is correctly set in `.env`:
- `DEEPSEEK_API_KEY` for DeepSeek
- `GEMINI_API_KEY` for Gemini

### Error: "Could not connect to LLM provider"
**Solutions:**
- Verify your API key is valid
- Check your internet connection
- For DeepSeek: Ensure you have API credits
- For Gemini: Check API quota limits
- For Local: Ensure Ollama is running (`ollama serve`)

### Empty Thought Process (Gemini)
**This is expected behavior.** Gemini doesn't use `<think>` tags by design. The `thought_process` field will be empty, which is fine - your frontend handles this gracefully.

### Import Errors
**Solution:** Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

---

## 📊 Performance Comparison

| Metric | DeepSeek R1 | Gemini 2.0 | Local Ollama |
|--------|-------------|------------|--------------|
| Speed | ⭐⭐⭐ (3/5) | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐ (2/5) |
| Reasoning | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐ (3/5) | ⭐⭐⭐⭐ (4/5) |
| Cost | $$ | $ (Free tier) | Free |
| Privacy | Cloud | Cloud | ⭐⭐⭐⭐⭐ Local |
| Reliability | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 📝 Code Changes Summary

### What Was Modified:

1. **requirements.txt** - Added `openai` and `google-generativeai`
2. **backend/llm_engine.py** - Refactored with:
   - `BaseLLMClient` - Abstract base class
   - `DeepSeekClient` - Cloud API via OpenAI SDK
   - `GeminiClient` - Google Gemini API
   - `LocalOllamaClient` - Legacy Ollama support
   - `get_llm_client()` - Factory function
3. **backend/main.py** - Updated to use `get_llm_client()`
4. **.env** - Added new configuration variables

### What Stayed the Same:

- ✅ Database schema (no migrations needed)
- ✅ Frontend code (fully compatible)
- ✅ API endpoints (no changes)
- ✅ Response format (consistent across providers)
- ✅ Memory system (Qdrant unchanged)

---

## 🎯 Next Steps

1. **Choose your provider** based on your needs
2. **Get your API key** from the provider's website
3. **Update your .env file** with the API key
4. **Run the test** using `python backend/llm_engine.py`
5. **Start your backend** with `python start_server.py`
6. **Test via frontend** - everything should work seamlessly!

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your `.env` configuration
3. Test each provider individually using `python backend/llm_engine.py`
4. Check the backend logs for detailed error messages

---

## 🔒 Security Notes

- **Never commit your `.env` file** to version control
- **Keep your API keys secret** - don't share them
- **Rotate keys regularly** for production use
- **Monitor API usage** to avoid unexpected costs
- **Set spending limits** in your provider dashboards

---

Happy coding! 🚀
