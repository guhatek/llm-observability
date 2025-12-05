# LLM Observability Demo

A comprehensive demonstration of LLM observability using various frameworks with a local Ollama Llama 3.1 8B chatbot. This project showcases how to instrument and monitor LLM applications using different observability tools.

## 📋 Overview

This repository contains examples of implementing observability for LLM applications using:
- **Plain OpenTelemetry (OTel)**: Direct instrumentation with OpenTelemetry SDK
- **Langfuse**: LLM engineering platform with tracing capabilities
- **Langtrace**: Purpose-built observability for LLM applications
- **OpenLLMetry**: OpenTelemetry-based LLM observability
- **Opik**: Open-source LLM evaluation and observability

Each implementation sends metrics, logs, and traces to a local observability stack consisting of:
- **OpenTelemetry Collector**: Central data collection and processing
- **Jaeger**: Distributed tracing visualization
- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards

## 🏗️ Architecture

```
┌─────────────┐
│   Chatbot   │
│  (Llama3.1) │
└──────┬──────┘
       │
       ├─────────────┬─────────────┬─────────────┬─────────────┐
       │             │             │             │             │
   ┌───▼───┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌───▼────┐
   │ OTel  │   │Langfuse │   │Langtrace│   │OpenLL   │   │  Opik  │
   │       │   │         │   │         │   │Metry    │   │        │
   └───┬───┘   └────┬────┘   └────┬────┘   └────┬────┘   └───┬────┘
       │             │             │             │             │
       └─────────────┴─────────────┴─────────────┴─────────────┘
                                   │
                          ┌────────▼────────┐
                          │ OTel Collector  │
                          └────────┬────────┘
                                   │
                   ┌───────────────┼───────────────┐
                   │               │               │
              ┌────▼────┐    ┌────▼────┐    ┌─────▼─────┐
              │ Jaeger  │    │Prometheus│    │  Grafana  │
              └─────────┘    └──────────┘    └───────────┘
```

## 🚀 Prerequisites

Before getting started, ensure you have the following installed:

### Required Software
- **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
- **Docker & Docker Compose**: [Install Docker](https://docs.docker.com/get-docker/)
- **Ollama**: [Install Ollama](https://ollama.ai/download)
- **Git**: [Install Git](https://git-scm.com/downloads)

### System Requirements
- **RAM**: Minimum 16GB (recommended for running Llama 3.1 8B)
- **Disk Space**: At least 10GB free space
- **CPU**: Modern multi-core processor

## 📥 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/llm-observability-demo.git
cd llm-observability-demo
```

### 2. Install Ollama and Pull Llama 3.1 Model

```bash
# Install Ollama (if not already installed)
# For macOS/Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# For Windows, download from https://ollama.ai/download

# Pull the Llama 3.1 8B model
ollama pull llama3.1:8b

# Verify the model is available
ollama list
```

### 3. Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 4. Start the Observability Stack

```bash
# Start OpenTelemetry Collector, Jaeger, Prometheus, and Grafana
docker-compose up -d

# Verify all services are running
docker-compose ps
```

### 5. Access the Observability UIs

Once the stack is running, you can access:

- **Jaeger UI**: http://localhost:16686 (Distributed tracing)
- **Prometheus UI**: http://localhost:9090 (Metrics)
- **Grafana UI**: http://localhost:3000 (Dashboards, default login: admin/admin)
- **OpenTelemetry Collector**: http://localhost:4318 (OTLP HTTP endpoint)

## 📂 Project Structure

```
llm-observability-demo/
├── README.md                      # This file
├── docker-compose.yml             # Observability stack configuration
├── otel-collector-config.yaml    # OpenTelemetry Collector config
├── prometheus.yml                 # Prometheus configuration
├── requirements.txt               # Common Python dependencies
├── common/                        # Shared utilities
│   ├── __init__.py
│   └── chatbot.py                # Base chatbot implementation
├── otel/                          # Plain OpenTelemetry implementation
│   ├── README.md
│   ├── requirements.txt
│   └── chatbot_otel.py
├── langfuse/                      # Langfuse implementation
│   ├── README.md
│   ├── requirements.txt
│   └── chatbot_langfuse.py
├── langtrace/                     # Langtrace implementation
│   ├── README.md
│   ├── requirements.txt
│   └── chatbot_langtrace.py
├── openllmetry/                   # OpenLLMetry implementation
│   ├── README.md
│   ├── requirements.txt
│   └── chatbot_openllmetry.py
└── opik/                          # Opik implementation
    ├── README.md
    ├── requirements.txt
    └── chatbot_opik.py
```

## 🎯 Quick Start

### Running Individual Implementations

Each framework has its own directory with a dedicated README. Choose the framework you want to explore:

1. **[Plain OpenTelemetry](./otel/README.md)**: Direct OTel instrumentation
   ```bash
   cd otel && pip install -r requirements.txt && python chatbot_otel.py
   ```

2. **[Langfuse](./langfuse/README.md)**: LLM engineering platform
   ```bash
   cd langfuse && pip install -r requirements.txt && python chatbot_langfuse.py
   ```

3. **[Langtrace](./langtrace/README.md)**: Purpose-built LLM observability
   ```bash
   cd langtrace && pip install -r requirements.txt && python chatbot_langtrace.py
   ```

4. **[OpenLLMetry](./openllmetry/README.md)**: OTel-based LLM observability
   ```bash
   cd openllmetry && pip install -r requirements.txt && python chatbot_openllmetry.py
   ```

5. **[Opik](./opik/README.md)**: Open-source LLM evaluation
   ```bash
   cd opik && pip install -r requirements.txt && python chatbot_opik.py
   ```

## 📊 What You'll Observe

Each implementation captures:

### Traces
- LLM request/response cycles
- Token usage per request
- Latency and duration metrics
- Error tracking and stack traces
- Conversation context and history

### Metrics
- Request rate and throughput
- Token consumption (input/output)
- Response time percentiles
- Error rates
- Model performance metrics

### Logs
- Structured application logs
- LLM prompt and completion logs
- Error and warning messages
- Debug information

## 🧹 Cleanup

To stop and remove all containers:

```bash
# Stop all services
docker-compose down

# Remove volumes (this will delete all data)
docker-compose down -v

# Deactivate Python virtual environment
deactivate
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM serving
- [OpenTelemetry](https://opentelemetry.io/) for observability standards
- [Jaeger](https://www.jaegertracing.io/) for tracing
- [Prometheus](https://prometheus.io/) for metrics
- [Grafana](https://grafana.com/) for visualization
- All the amazing observability framework creators

## 📚 Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Langfuse Documentation](https://langfuse.com/docs)
- [Langtrace Documentation](https://docs.langtrace.ai/)
- [OpenLLMetry Documentation](https://github.com/traceloop/openllmetry)
- [Opik Documentation](https://www.comet.com/docs/opik/)
- [Ollama Documentation](https://github.com/ollama/ollama)

## ❓ Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check if the model is available: `ollama list`
- Default Ollama endpoint: `http://localhost:11434`

### Docker Issues
- Ensure Docker daemon is running
- Check port conflicts (16686, 9090, 3000, 4318)
- Review logs: `docker-compose logs -f`

### Python Dependencies
- Use Python 3.9 or higher
- Create a fresh virtual environment if issues persist
- Ensure pip is up to date: `pip install --upgrade pip`

For more specific issues, please check the individual framework READMEs.