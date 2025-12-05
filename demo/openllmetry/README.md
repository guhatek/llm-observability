# Ollama Chatbot with OpenLLMetry Observability

A Python chatbot demo using Ollama's llama3.1:8b model with comprehensive observability via OpenLLMetry and OpenTelemetry. All LLM calls are automatically traced and sent to a local OTEL collector for monitoring and analysis.

## Features

- 🤖 **Local LLM**: Uses Ollama with llama3.1:8b model
- 📊 **Full Observability**: Automatic tracing of all LLM calls via OpenLLMetry
- 🔍 **OpenTelemetry Integration**: Standard OTLP export to local collector
- 💬 **Conversation History**: Maintains context across messages
- 🌊 **Streaming Support**: Toggle between regular and streaming responses
- 📈 **Rich Metrics**: Token counts, latencies, response lengths, and more

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│   Chatbot   │─────▶│    Ollama    │      │ OpenLLMetry    │
│  (Python)   │      │  llama3.1:8b │      │ Instrumentation│
└─────────────┘      └──────────────┘      └────────────────┘
       │                                            │
       │                                            │
       ▼                                            ▼
┌─────────────────────────────────────────────────────────┐
│              OTEL Collector (localhost:4318)            │
└─────────────────────────────────────────────────────────┘
       │                                            │
       ▼                                            ▼
┌─────────────┐                              ┌─────────────┐
│   Jaeger    │                              │   Logging   │
│     UI      │                              │   Console   │
└─────────────┘                              └─────────────┘
```

## Prerequisites

- Python 3.8+
- Ollama installed and running
- Docker (for OTEL collector and Jaeger)

## Quick Start

### 1. Clone and Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

### 2. Start Ollama

```bash
# Install Ollama from https://ollama.ai/download

# Pull the model
ollama pull llama3.1:8b

# Start Ollama (usually runs automatically)
ollama serve
```

### 3. Start OTEL Collector

```bash
# Using Docker
docker run -p 4317:4317 -p 4318:4318 \
  -v $(pwd)/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml
```

### 4. Run the Chatbot

```bash
python chatbot.py
```

## Usage

Once running, you can interact with the chatbot:

```
You: Hello! How are you?

Bot: I'm doing well, thank you for asking! How can I help you today?

You: Tell me about Python decorators

Bot: Python decorators are a powerful feature that allows you to modify or extend...
```

### Available Commands

- `quit` or `exit` - End the conversation
- `clear` - Reset conversation history
- `stream` - Toggle streaming mode on/off

## Configuration

### requirements.txt

```
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-http
openllmetry
ollama
```

### OTEL Collector Configuration

The `otel-collector-config.yaml` configures how traces are received and exported:

```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
```

## Observability

### Captured Metrics

OpenLLMetry automatically captures:

- **Model Information**: Model name, version
- **Token Usage**: Prompt tokens, completion tokens
- **Performance**: Request duration, response time
- **Content**: Message count, response length
- **Context**: Conversation flow, streaming status

### Span Attributes

Each LLM call creates a span with attributes:

```python
{
  "llm.model": "llama3.1:8b",
  "llm.message_count": 4,
  "llm.prompt_tokens": 156,
  "llm.completion_tokens": 89,
  "llm.response_length": 542,
  "llm.streaming": false
}
```

## Visualization with Jaeger

For better trace visualization, add Jaeger:

### 1. Update OTEL Collector Config

```yaml
exporters:
  logging:
    loglevel: debug
  otlp/jaeger:
    endpoint: localhost:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging, otlp/jaeger]
```

### 2. Start Jaeger

```bash
docker run -d \
  --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest
```

### 3. View Traces

Open http://localhost:16686 in your browser to explore traces in the Jaeger UI.

## Docker Compose Setup

For simplified deployment, use Docker Compose:

```yaml
version: '3.8'

services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"
      - "4318:4318"

  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"
```

Start everything:

```bash
docker-compose up -d
```

## Advanced Usage

### Custom Span Attributes

Add custom attributes to track specific information:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("user.id", "user123")
    span.set_attribute("session.id", "session456")
    # Your code here
```

### Environment Variables

Configure via environment variables:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
export OTEL_SERVICE_NAME="ollama-chatbot"
export OTEL_TRACES_EXPORTER="otlp"
```

### Modify Model Parameters

Edit the `chat()` function to adjust model behavior:

```python
response = ollama.chat(
    model="llama3.1:8b",
    messages=conversation_history,
    options={
        "temperature": 0.9,      # Higher = more creative
        "num_predict": 1000,     # Max tokens
        "top_p": 0.9,           # Nucleus sampling
        "top_k": 40,            # Top-k sampling
    }
)
```

## Troubleshooting

### Ollama Issues

**Problem**: "Connection refused" or "Ollama not found"

```bash
# Check if Ollama is running
ps aux | grep ollama

# Check Ollama status
curl http://localhost:11434

# Restart Ollama
ollama serve
```

**Problem**: Model not found

```bash
# List available models
ollama list

# Pull the required model
ollama pull llama3.1:8b
```

### OTEL Collector Issues

**Problem**: No traces appearing in collector

- Verify collector is running: `docker ps | grep otel`
- Check endpoint URL: `http://localhost:4318/v1/traces`
- Review collector logs: `docker logs <container-id>`
- Test endpoint: `curl http://localhost:4318/v1/traces`

**Problem**: Port conflicts

```bash
# Find processes using port 4318
lsof -i :4318

# Kill conflicting process or change port in config
```

### Python Issues

**Problem**: Import errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check installed packages
pip list | grep -E "opentelemetry|openllmetry|ollama"
```

**Problem**: No spans exported

- Ensure `tracer_provider.force_flush()` is called before exit
- Check for Python exceptions in console
- Verify OpenLLMetry instrumentation is initialized before Ollama calls

## Performance Tips

1. **Batch Size**: Adjust batch processor in OTEL config for better throughput
2. **Temperature**: Lower values (0.3-0.5) for more focused responses
3. **Context Window**: Clear conversation history periodically to reduce token usage
4. **Streaming**: Enable streaming mode for better perceived performance

## Project Structure

```
.
├── chatbot.py                    # Main chatbot application
├── requirements.txt              # Python dependencies
├── otel-collector-config.yaml    # OTEL collector configuration
├── docker-compose.yml            # Docker Compose setup (optional)
└── README.md                     # This file
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [OpenLLMetry Documentation](https://github.com/traceloop/openllmetry)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OTEL Collector](https://opentelemetry.io/docs/collector/)

## License

MIT License - feel free to use this project for learning and development.

## Support

For issues and questions:
- Ollama: https://github.com/ollama/ollama/issues
- OpenLLMetry: https://github.com/traceloop/openllmetry/issues
- OpenTelemetry: https://github.com/open-telemetry/opentelemetry-python/issues

---

**Happy Chatting! 🤖📊**