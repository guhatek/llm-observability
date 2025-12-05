# Plain OpenTelemetry Implementation

This implementation demonstrates direct instrumentation of an LLM chatbot using the OpenTelemetry SDK without any high-level abstractions. This gives you complete control over what telemetry data is collected and how it's structured.

## 📋 Overview

This example shows how to manually instrument an Ollama-based chatbot with:
- **Traces**: Span creation for LLM operations with detailed attributes
- **Metrics**: Custom metrics for token usage, latency, and request counts
- **Logs**: Structured logging with trace context correlation

## 🎯 Key Features

- Manual span creation and management
- Custom span attributes for LLM-specific data
- Metric instrumentation (counters, histograms, gauges)
- Trace context propagation
- Error tracking and exception recording
- Integration with OTel Collector

## 📦 Installation

```bash
# Navigate to the otel directory
cd otel

# Install dependencies
pip install -r requirements.txt
```

## 📄 Dependencies

The `requirements.txt` includes:

```
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-exporter-otlp>=1.21.0
opentelemetry-instrumentation>=0.42b0
requests>=2.31.0
```

## ⚙️ Configuration

### Environment Variables

Set these environment variables before running (optional, defaults provided):

```bash
# OpenTelemetry Collector endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"

# Service name
export OTEL_SERVICE_NAME="llm-chatbot-otel"

# Ollama endpoint
export OLLAMA_ENDPOINT="http://localhost:11434"

# Log level
export LOG_LEVEL="INFO"
```

### OTel Collector Configuration

Ensure your `otel-collector-config.yaml` includes OTLP receivers:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
```

## 🚀 Running the Chatbot

### Start the observability stack first:

```bash
# From the project root
docker-compose up -d
```

### Run the chatbot:

```bash
python chatbot_otel.py
```

### Interact with the chatbot:

```
You: Hello! How are you?
Bot: I'm doing well, thank you for asking! ...

You: What can you help me with?
Bot: I can help you with various tasks...

You: exit
```

## 📊 What Gets Instrumented

### Traces

Each LLM interaction creates spans with the following structure:

```
chat_interaction
├── generate_response
│   ├── ollama_request
│   └── process_streaming_response
└── log_interaction
```

**Span Attributes:**
- `llm.model`: Model name (llama3.1:8b)
- `llm.prompt`: User input
- `llm.response`: Model output
- `llm.tokens.input`: Input token count
- `llm.tokens.output`: Output token count
- `llm.tokens.total`: Total tokens used
- `llm.duration_ms`: Request duration
- `llm.temperature`: Temperature setting
- `http.method`, `http.url`, `http.status_code`: HTTP details

### Metrics

Custom metrics collected:

```python
# Counter: Total number of LLM requests
llm_requests_total{model="llama3.1:8b", status="success"}

# Histogram: Request duration distribution
llm_request_duration_seconds{model="llama3.1:8b"}

# Counter: Token usage
llm_tokens_total{model="llama3.1:8b", type="input"}
llm_tokens_total{model="llama3.1:8b", type="output"}

# Counter: Errors
llm_errors_total{model="llama3.1:8b", error_type="timeout"}
```

### Logs

Structured logs with trace correlation:

```json
{
  "timestamp": "2025-12-04T10:30:45.123Z",
  "level": "INFO",
  "message": "LLM request completed",
  "trace_id": "1234567890abcdef",
  "span_id": "fedcba0987654321",
  "service": "llm-chatbot-otel",
  "model": "llama3.1:8b",
  "tokens": 150,
  "duration_ms": 1250
}
```

## 🔍 Viewing Telemetry Data

### Jaeger (Traces)

1. Open http://localhost:16686
2. Select service: `llm-chatbot-otel`
3. Click "Find Traces"
4. Explore individual traces to see:
   - Span hierarchy and timing
   - LLM prompts and responses
   - Token usage per request
   - Error details if any

### Prometheus (Metrics)

1. Open http://localhost:9090
2. Query examples:
   ```promql
   # Request rate
   rate(llm_requests_total[5m])
   
   # Average request duration
   rate(llm_request_duration_seconds_sum[5m]) / rate(llm_request_duration_seconds_count[5m])
   
   # Total tokens per minute
   rate(llm_tokens_total[1m]) * 60
   
   # Error rate
   rate(llm_errors_total[5m])
   ```

### Grafana (Dashboards)

1. Open http://localhost:3000 (admin/admin)
2. Add Prometheus as a data source
3. Add Jaeger as a data source
4. Create dashboard panels with queries like:
   - Request throughput over time
   - P50, P95, P99 latency
   - Token consumption trends
   - Error rates

## 🧪 Testing Different Scenarios

### Test Error Handling

```bash
# Stop Ollama temporarily
ollama stop

# Run the chatbot - observe error traces
python chatbot_otel.py
```

### Test Performance

```bash
# Send multiple rapid requests
# Observe latency metrics and trace timing
```

### Test Different Models

Modify the code to use different Ollama models:

```python
MODEL_NAME = "llama3.1:70b"  # or any other model
```

## 📝 Code Structure

### Key Components

**1. OTel Setup:**
```python
def setup_telemetry():
    # Initialize TracerProvider
    # Initialize MeterProvider
    # Configure OTLP exporters
    # Set global providers
```

**2. Span Creation:**
```python
with tracer.start_as_current_span("operation_name") as span:
    span.set_attribute("key", "value")
    # Your code here
```

**3. Metrics Recording:**
```python
request_counter.add(1, {"model": model_name, "status": "success"})
duration_histogram.record(duration, {"model": model_name})
```

**4. Context Propagation:**
```python
from opentelemetry.trace import get_current_span
span = get_current_span()
trace_id = span.get_span_context().trace_id
```

## 🎓 Learning Points

This implementation teaches:

1. **Manual Instrumentation**: How to create and manage spans manually
2. **Custom Attributes**: Adding domain-specific attributes to traces
3. **Metric Types**: Using counters, histograms, and gauges
4. **Context Propagation**: Maintaining trace context across operations
5. **Error Handling**: Capturing and reporting errors in spans
6. **Exporter Configuration**: Setting up OTLP exporters
7. **Semantic Conventions**: Following OTel semantic conventions

## 🔧 Customization

### Add Custom Attributes

```python
span.set_attribute("app.user_id", user_id)
span.set_attribute("app.session_id", session_id)
span.set_attribute("llm.prompt_template", template_name)
```

### Create Custom Metrics

```python
custom_gauge = meter.create_gauge(
    name="llm.queue_size",
    description="Current queue size",
    unit="requests"
)
custom_gauge.set(queue_length, {"priority": "high"})
```

### Add Resource Attributes

```python
resource = Resource.create({
    "service.name": "llm-chatbot",
    "service.version": "1.0.0",
    "deployment.environment": "production",
    "host.name": socket.gethostname()
})
```

## ⚠️ Common Issues

### Issue: Traces not appearing in Jaeger
**Solution**: 
- Verify OTel Collector is running: `docker-compose ps`
- Check collector logs: `docker-compose logs otel-collector`
- Ensure endpoint is correct: `http://localhost:4318`

### Issue: High memory usage
**Solution**: 
- Reduce batch size in span processor
- Implement sampling for high-volume scenarios
- Use async exporters

### Issue: Missing metrics
**Solution**: 
- Check metric exporter configuration
- Verify Prometheus is scraping the collector
- Check for metric name conflicts

## 📚 Additional Resources

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [OTel Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Span Processors](https://opentelemetry.io/docs/instrumentation/python/exporters/)

## 🎯 Next Steps

- Explore automatic instrumentation libraries
- Implement distributed tracing across services
- Create custom Grafana dashboards
- Set up alerting rules in Prometheus
- Add sampling strategies for production