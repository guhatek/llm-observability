# Langtrace Implementation

This implementation demonstrates LLM observability using Langtrace, a lightweight and developer-friendly observability platform specifically designed for LLM applications with automatic instrumentation capabilities.

## 📋 Overview

Langtrace provides:
- **Automatic Instrumentation**: Zero-code instrumentation for popular LLM frameworks
- **Distributed Tracing**: OpenTelemetry-based tracing for LLM operations
- **Real-time Monitoring**: Live metrics and trace visualization
- **Evaluation Framework**: Built-in evaluation tools for LLM outputs
- **Privacy-First**: Can run fully on-premises

## 🎯 Key Features

- One-line SDK initialization
- Automatic prompt and response capture
- Token usage and cost tracking
- Support for multiple LLM providers
- Custom attributes and metadata
- Integration with Jaeger, Prometheus, and other backends
- Minimal performance overhead

## 📦 Installation

```bash
# Navigate to the langtrace directory
cd langtrace

# Install dependencies
pip install -r requirements.txt
```

## 📄 Dependencies

The `requirements.txt` includes:

```
langtrace-python-sdk>=2.0.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-exporter-otlp>=1.21.0
requests>=2.31.0
python-dotenv>=1.0.0
```

## ⚙️ Configuration

### Option 1: Using Langtrace Cloud

1. Sign up at [langtrace.ai](https://langtrace.ai)
2. Get your API key from the dashboard

### Option 2: Self-Hosted with OTel Collector

Configure to send directly to your OTel Collector (no Langtrace account needed).

### Environment Variables

Create a `.env` file in the `langtrace/` directory:

```bash
# Langtrace Configuration
LANGTRACE_API_KEY=lt_api_key_...  # Optional if self-hosting

# OpenTelemetry Configuration (for self-hosting)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=llm-chatbot-langtrace

# Ollama Configuration
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Disable Langtrace Cloud (for self-hosting)
LANGTRACE_DISABLE_CLOUD=true
```

## 🚀 Running the Chatbot

### Start the observability stack:

```bash
# From the project root
docker-compose up -d
```

### Run the chatbot:

```bash
# Make sure you're in the langtrace directory
cd langtrace

# Run the chatbot
python chatbot_langtrace.py
```

### Expected output:

```
Langtrace initialized successfully!
Chatbot ready! Type 'exit' to quit.

You: What is machine learning?
Bot: Machine learning is a subset of artificial intelligence...

You: exit
Goodbye!
```

## 📊 What Gets Instrumented

### Automatic Instrumentation

Langtrace automatically captures:

```python
# This is all you need to enable tracing!
from langtrace_python_sdk import langtrace

langtrace.init(
    api_key="your-key",  # Optional
    write_to_remote_url=False  # For self-hosted
)
```

### Trace Structure

```
llm_request
├── prompt_formatting
├── model_invocation
│   ├── token_counting
│   └── response_generation
└── response_processing
```

### Captured Attributes

**Automatic:**
- `llm.vendor`: Provider name (ollama)
- `llm.request.model`: Model identifier
- `llm.request.temperature`: Temperature setting
- `llm.request.max_tokens`: Maximum tokens
- `llm.prompts`: Full prompt text
- `llm.completions`: Complete response
- `llm.usage.prompt_tokens`: Input tokens
- `llm.usage.completion_tokens`: Output tokens
- `llm.usage.total_tokens`: Total tokens

**Custom:**
- `app.user_id`: User identifier
- `app.session_id`: Session identifier
- `app.conversation_id`: Conversation ID
- `app.context_length`: Number of messages in context

## 🔍 Viewing Data

### Langtrace Cloud Dashboard

If using Langtrace Cloud:

1. Login to https://app.langtrace.ai
2. Navigate to "Traces"
3. View:
   - Request/response pairs
   - Token usage analytics
   - Latency metrics
   - Error rates
   - Cost tracking

### Self-Hosted (Jaeger)

1. Open http://localhost:16686
2. Select service: `llm-chatbot-langtrace`
3. View traces with detailed LLM attributes
4. Analyze:
   - Request duration
   - Token consumption
   - Prompt/completion pairs
   - Error traces

### Prometheus Metrics

Langtrace exports standard OTel metrics:

```promql
# Request rate
rate(http_server_duration_count[5m])

# Token usage
sum(rate(llm_usage_total_tokens[5m]))

# Average latency
histogram_quantile(0.95, rate(http_server_duration_bucket[5m]))
```

## 🎨 Advanced Features

### 1. Custom Attributes

```python
from langtrace_python_sdk import with_langtrace_root_span

@with_langtrace_root_span("custom_operation")
def my_function():
    # This will be traced automatically
    pass
```

### 2. Manual Span Creation

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("custom_span") as span:
    span.set_attribute("custom.attribute", "value")
    # Your code here
```

### 3. User Context

```python
from langtrace_python_sdk import set_user_id, set_session_id

set_user_id("user-123")
set_session_id("session-abc")

# All subsequent traces will include this context
```

### 4. Prompt Templates Tracking

```python
from langtrace_python_sdk import with_langtrace_root_span

@with_langtrace_root_span("prompt_template")
def format_prompt(template, **kwargs):
    # Track which prompt template is being used
    span = trace.get_current_span()
    span.set_attribute("prompt.template.name", template)
    span.set_attribute("prompt.template.version", "v1.2")
    return template.format(**kwargs)
```

### 5. Evaluation Scores

```python
from langtrace_python_sdk import add_score

# Add evaluation score to current trace
add_score(
    name="relevance",
    value=0.95,
    reason="Response highly relevant to query"
)

add_score(
    name="factuality", 
    value=0.88,
    reason="Minor factual inaccuracy detected"
)
```

### 6. Error Tracking

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

span = trace.get_current_span()

try:
    # Your code
    pass
except Exception as e:
    span.record_exception(e)
    span.set_status(Status(StatusCode.ERROR, str(e)))
    raise
```

## 🧪 Testing Scenarios

### Test Different LLM Providers

Langtrace auto-instruments many providers:

```python
# Works with OpenAI
import openai
response = openai.chat.completions.create(...)

# Works with Anthropic
import anthropic
response = anthropic.messages.create(...)

# Works with Ollama (via requests)
response = requests.post(ollama_url, ...)
```

### Test Multi-Step Workflows

```python
from langtrace_python_sdk import with_langtrace_root_span

@with_langtrace_root_span("rag_pipeline")
def rag_workflow(query):
    # Step 1: Retrieve
    with tracer.start_as_current_span("retrieve"):
        docs = retrieve_documents(query)
    
    # Step 2: Generate
    with tracer.start_as_current_span("generate"):
        response = generate_response(query, docs)
    
    return response
```

### Test Streaming Responses

```python
# Langtrace handles streaming automatically
for chunk in stream_response():
    print(chunk, end="")
```

## 📝 Code Examples

### Basic Setup

```python
from langtrace_python_sdk import langtrace

# Initialize Langtrace
langtrace.init(
    api_key="your-key",  # Optional
    write_to_remote_url=False,  # True for cloud
    custom_remote_url="http://localhost:4318/v1/traces"
)

# Your LLM code - automatically traced!
response = call_llm(prompt)
```

### With Custom Context

```python
from langtrace_python_sdk import (
    langtrace, 
    with_langtrace_root_span,
    set_user_id
)

langtrace.init()

@with_langtrace_root_span("chat_interaction")
def chat(user_id, message):
    set_user_id(user_id)
    
    span = trace.get_current_span()
    span.set_attribute("conversation.topic", "AI")
    
    return generate_response(message)
```

### Async Support

```python
import asyncio
from langtrace_python_sdk import langtrace

langtrace.init()

async def async_chat(prompt):
    # Automatically traced in async context
    response = await async_llm_call(prompt)
    return response

asyncio.run(async_chat("Hello"))
```

## 🎓 Key Concepts

### 1. Zero-Config Instrumentation
Langtrace automatically instruments popular libraries without code changes.

### 2. OpenTelemetry Native
Built on OTel standards, works with any OTel-compatible backend.

### 3. Privacy Controls
All data can stay on-premises; cloud usage is optional.

### 4. Low Overhead
Async processing ensures minimal impact on application performance.

### 5. Provider Agnostic
Works with any LLM provider or framework.

## ⚠️ Common Issues

### Issue: Traces not appearing

**Solution:**
```python
# Force flush before application exit
from opentelemetry import trace

trace.get_tracer_provider().force_flush()
```

### Issue: Missing automatic instrumentation

**Solution:**
```bash
# Ensure library is installed BEFORE importing
pip install langtrace-python-sdk
# Then import before other libraries
from langtrace_python_sdk import langtrace
langtrace.init()
```

### Issue: High memory usage

**Solution:**
```python
langtrace.init(
    batch=True,
    batch_size=100,  # Adjust based on throughput
)
```

## 🔧 Configuration Options

### Initialization Parameters

```python
langtrace.init(
    api_key="lt_...",  # Langtrace Cloud API key
    write_to_remote_url=True,  # Send to Langtrace Cloud
    custom_remote_url="http://localhost:4318",  # Custom endpoint
    service_name="my-service",  # Service identifier
    disable_tracing_for_functions=["health_check"],  # Skip tracing
    disable_instrumentations={
        "openai": False,
        "anthropic": False,
    }
)
```

### Environment Variables

```bash
# Langtrace
LANGTRACE_API_KEY=lt_...
LANGTRACE_DISABLE_CLOUD=true

# OpenTelemetry
OTEL_SERVICE_NAME=my-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Resource attributes
OTEL_RESOURCE_ATTRIBUTES=environment=production,version=1.0.0
```

## 📊 Metrics Dashboard

### Key Metrics to Monitor

1. **Request Rate**: Total LLM requests per second
2. **Token Usage**: Input/output tokens over time
3. **Latency**: P50, P95, P99 response times
4. **Error Rate**: Failed requests percentage
5. **Cost**: Estimated API costs (if configured)

### Sample Grafana Queries

```promql
# Request rate by model
sum(rate(llm_request_duration_count[5m])) by (llm_request_model)

# Average tokens per request
rate(llm_usage_total_tokens_sum[5m]) / rate(llm_usage_total_tokens_count[5m])

# Error percentage
(sum(rate(llm_request_errors[5m])) / sum(rate(llm_requests_total[5m]))) * 100
```

## 📚 Additional Resources

- [Langtrace Documentation](https://docs.langtrace.ai)
- [Python SDK Guide](https://docs.langtrace.ai/supported-integrations/llm-frameworks/python-sdk)
- [GitHub Repository](https://github.com/Scale3-Labs/langtrace-python-sdk)
- [OpenTelemetry Integration](https://docs.langtrace.ai/tracing/send-traces-to-other-tools)
- [Evaluation Guide](https://docs.langtrace.ai/evaluations)

## 🎯 Next Steps

- Enable automatic instrumentation for your LLM framework
- Set up custom evaluation metrics
- Create real-time monitoring dashboards
- Implement alerting for anomalies
- Explore prompt optimization features