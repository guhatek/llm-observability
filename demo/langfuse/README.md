# Langfuse Implementation

This implementation demonstrates LLM observability using Langfuse, an open-source LLM engineering platform that provides tracing, prompt management, and evaluation capabilities specifically designed for LLM applications.

## 📋 Overview

Langfuse offers a comprehensive solution for LLM observability with:
- **Traces**: Hierarchical tracking of LLM chains and agents
- **Generations**: Detailed LLM call tracking with prompts and completions
- **Spans**: Custom operation tracking within traces
- **Scores**: Quality evaluation and user feedback
- **Prompt Management**: Version control for prompts

## 🎯 Key Features

- Purpose-built for LLM applications
- Automatic prompt and completion tracking
- Token usage and cost tracking
- User feedback and scoring
- Prompt versioning and management
- Session grouping for conversations
- Web UI for exploration and analysis

## 📦 Installation

```bash
# Navigate to the langfuse directory
cd langfuse

# Install dependencies
pip install -r requirements.txt
```

## 📄 Dependencies

The `requirements.txt` includes:

```
langfuse>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

## ⚙️ Configuration

### Option 1: Using Langfuse Cloud

1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a new project
3. Get your API keys from the project settings

### Option 2: Self-Hosted Langfuse

Add Langfuse to your `docker-compose.yml`:

```yaml
services:
  langfuse-server:
    image: langfuse/langfuse:latest
    ports:
      - "3001:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@langfuse-db:5432/langfuse
      - NEXTAUTH_URL=http://localhost:3001
      - NEXTAUTH_SECRET=your-secret-key
      - SALT=your-salt
    depends_on:
      - langfuse-db

  langfuse-db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse_db:/var/lib/postgresql/data

volumes:
  langfuse_db:
```

### Environment Variables

Create a `.env` file in the `langfuse/` directory:

```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # or http://localhost:3001 for self-hosted

# Ollama Configuration
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Optional: Enable debug mode
LANGFUSE_DEBUG=false
```

## 🚀 Running the Chatbot

### Start the observability stack:

```bash
# From the project root
docker-compose up -d
```

### Run the chatbot:

```bash
# Make sure you're in the langfuse directory
cd langfuse

# Run the chatbot
python chatbot_langfuse.py
```

### Interact with the chatbot:

```
You: Tell me about observability
Bot: Observability is the ability to understand...

You: What are traces?
Bot: Traces represent the flow of execution...

You: /feedback 5 Great explanation!
Feedback recorded!

You: exit
```

## 📊 What Gets Instrumented

### Trace Hierarchy

Langfuse creates a structured trace hierarchy:

```
conversation_session
├── chat_turn_1
│   ├── generation (LLM call)
│   └── span (post-processing)
├── chat_turn_2
│   ├── generation (LLM call)
│   └── span (post-processing)
└── ...
```

### Generations (LLM Calls)

Each LLM interaction is captured as a generation:

```python
{
  "name": "llama3.1-response",
  "model": "llama3.1:8b",
  "input": "User prompt here",
  "output": "Model response here",
  "usage": {
    "input": 45,
    "output": 123,
    "total": 168
  },
  "metadata": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "stream": true
  }
}
```

### Traces

Traces group related operations:

```python
{
  "name": "chat_interaction",
  "session_id": "session_abc123",
  "user_id": "user_xyz",
  "tags": ["production", "chatbot"],
  "metadata": {
    "conversation_length": 5,
    "topic": "observability"
  }
}
```

### Spans

Custom operations within traces:

```python
{
  "name": "response_processing",
  "input": "raw_response",
  "output": "processed_response",
  "metadata": {
    "processing_time_ms": 45
  }
}
```

### Scores

User feedback and evaluations:

```python
{
  "name": "user_feedback",
  "value": 5,
  "comment": "Very helpful response!"
}
```

## 🔍 Viewing Data in Langfuse

### Web UI Access

1. Open your Langfuse URL:
   - Cloud: https://cloud.langfuse.com
   - Self-hosted: http://localhost:3001

2. Navigate to your project

3. Explore the interface:

### Traces View

- View all conversation traces
- Filter by session, user, or tags
- See hierarchical trace structure
- Analyze timing and performance

### Generations View

- List all LLM calls
- View prompts and completions
- Analyze token usage
- Track costs per generation

### Sessions View

- Group traces by conversation session
- Analyze user journeys
- Track conversation metrics

### Scores & Feedback

- View user ratings
- Analyze feedback trends
- Identify problematic generations

## 🎨 Advanced Features

### 1. Prompt Management

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Fetch a managed prompt
prompt = langfuse.get_prompt("chat-system-prompt", version=2)

# Use in your application
system_message = prompt.compile(
    name="User",
    topic="AI safety"
)
```

### 2. User Feedback Collection

```python
# In your chatbot code
trace.score(
    name="user-rating",
    value=rating,  # 1-5
    comment=user_comment
)
```

### 3. Session Grouping

```python
# Group related interactions
trace = langfuse.trace(
    name="conversation",
    session_id=session_id,
    user_id=user_id
)
```

### 4. Custom Metadata

```python
generation = trace.generation(
    name="llm-call",
    metadata={
        "environment": "production",
        "feature_flags": ["new_ui", "beta_model"],
        "user_tier": "premium"
    }
)
```

### 5. Cost Tracking

```python
generation = trace.generation(
    name="gpt4-call",
    model="gpt-4",
    usage={
        "input": 100,
        "output": 200,
        "total": 300
    },
    model_parameters={
        "input_cost_per_token": 0.00003,
        "output_cost_per_token": 0.00006
    }
)
```

## 🧪 Testing Scenarios

### Test Conversation Flow

```python
# Start a multi-turn conversation
# Observe session grouping in Langfuse
```

### Test Feedback System

```python
# Provide ratings for responses
# Check scores in Langfuse dashboard
```

### Test Error Handling

```python
# Trigger an error
# Observe error traces and metadata
```

## 📝 Code Examples

### Basic Trace Creation

```python
from langfuse import Langfuse

langfuse = Langfuse()

trace = langfuse.trace(
    name="my-operation",
    user_id="user-123",
    session_id="session-abc"
)

generation = trace.generation(
    name="llm-call",
    model="llama3.1:8b",
    input="Hello, world!",
    output="Hi there! How can I help?",
    usage={"input": 10, "output": 15, "total": 25}
)

trace.score(
    name="user-rating",
    value=5
)
```

### Context Manager Pattern

```python
with langfuse.trace(name="chat") as trace:
    with trace.generation(name="llm") as gen:
        response = call_llm(prompt)
        gen.end(output=response)
```

### Async Support

```python
import asyncio
from langfuse import Langfuse

async def async_chat():
    langfuse = Langfuse()
    trace = langfuse.trace(name="async-chat")
    
    # Your async LLM call
    response = await async_llm_call()
    
    trace.generation(
        name="async-gen",
        output=response
    )
```

## 🎓 Key Concepts

### 1. Hierarchical Structure
Traces contain generations and spans, allowing complex operation tracking.

### 2. Async Processing
Langfuse uses async background processing for minimal latency impact.

### 3. Flexible Metadata
Attach any JSON-serializable data to traces, generations, or spans.

### 4. Cost Calculation
Automatic cost calculation based on token usage and model pricing.

### 5. Evaluation Scores
Multiple score types (ratings, classifications, numeric) for quality tracking.

## ⚠️ Common Issues

### Issue: API key errors
**Solution**: 
- Verify keys in `.env` file
- Check key permissions in Langfuse dashboard
- Ensure `LANGFUSE_HOST` matches your instance

### Issue: Traces not appearing
**Solution**: 
- Langfuse uses async processing (30-60s delay)
- Call `langfuse.flush()` to force immediate sending
- Check network connectivity to Langfuse host

### Issue: High memory usage
**Solution**: 
- Flush regularly in long-running applications
- Limit trace retention in memory
- Use batch mode for high throughput

## 🔧 Configuration Options

### SDK Configuration

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="https://cloud.langfuse.com",
    debug=False,
    enabled=True,  # Disable for testing
    flush_at=15,  # Batch size
    flush_interval=0.5  # Seconds
)
```

### Environment Variables

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_DEBUG=true
LANGFUSE_ENABLED=true
LANGFUSE_FLUSH_AT=15
LANGFUSE_FLUSH_INTERVAL=0.5
```

## 📚 Additional Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [Python SDK Reference](https://langfuse.com/docs/sdk/python)
- [Prompt Management Guide](https://langfuse.com/docs/prompts)
- [Evaluation & Scoring](https://langfuse.com/docs/scores)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)

## 🎯 Next Steps

- Set up prompt versioning
- Implement custom evaluation metrics
- Create dashboards for key metrics
- Integrate with your CI/CD pipeline
- Explore LangChain/LlamaIndex integration