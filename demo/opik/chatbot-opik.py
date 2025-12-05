"""
LLM Observability Demo with Ollama and Opik by Comet
Demonstrates comprehensive observability for LLM applications

Required packages:
pip install ollama opik opentelemetry-api opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-http
"""

import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# LLM imports
import ollama

# Opik imports
import opik
from opik import configure, opik_context, track 

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Opik Configuration
OPIK_API_KEY = os.getenv("OPIK_API_KEY", "local")
OPIK_WORKSPACE = os.getenv("OPIK_WORKSPACE", "default")
OPIK_PROJECT_NAME = os.getenv("OPIK_PROJECT_NAME", "my-local-demo")

# OpenTelemetry Configuration - HTTP endpoint (port 4318)
OTEL_COLLECTOR_ENDPOINT = os.getenv("OTEL_COLLECTOR_ENDPOINT", "http://localhost:4318")

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# ============================================================================
# OpenTelemetry Setup
# ============================================================================

def setup_opentelemetry():
    """Initialize OpenTelemetry with OTLP HTTP exporters"""
    
    # Create resource
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: "opik-chatbot-demo",
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "demo"
    })
    
    # Ensure endpoint has http:// prefix
    endpoint = OTEL_COLLECTOR_ENDPOINT
    if not endpoint.startswith(('http://', 'https://')):
        endpoint = f"http://{endpoint}"
    endpoint = endpoint.rstrip('/')
    
    logger.info(f"Configuring OpenTelemetry with HTTP endpoint: {endpoint}")
    
    # Setup Tracing with multiple exporters
    trace_provider = TracerProvider(resource=resource)
    
    # Add OTLP exporter for traces
    traces_endpoint = f"{endpoint}/v1/traces"
    logger.info(f"Trace endpoint: {traces_endpoint}")
    
    try:
        otlp_trace_exporter = OTLPSpanExporter(endpoint=traces_endpoint)
        trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
        logger.info("✓ OTLP Trace exporter configured")
    except Exception as e:
        logger.warning(f"Failed to configure OTLP trace exporter: {e}")
        logger.info("Adding console exporter as fallback")
        trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    
    trace.set_tracer_provider(trace_provider)
    
    # Setup Metrics
    metrics_endpoint = f"{endpoint}/v1/metrics"
    logger.info(f"Metric endpoint: {metrics_endpoint}")
    
    try:
        otlp_metric_exporter = OTLPMetricExporter(endpoint=metrics_endpoint)
        metric_reader = PeriodicExportingMetricReader(
            otlp_metric_exporter, 
            export_interval_millis=10000
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        logger.info("✓ OTLP Metric exporter configured")
    except Exception as e:
        logger.warning(f"Failed to configure OTLP metric exporter: {e}")
        logger.info("Adding console exporter as fallback")
        console_metric_reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(),
            export_interval_millis=10000
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[console_metric_reader])
    
    metrics.set_meter_provider(meter_provider)
    
    logger.info("OpenTelemetry configured successfully")
    
    return trace.get_tracer(__name__), metrics.get_meter(__name__)

# Initialize OpenTelemetry
tracer, meter = setup_opentelemetry()

# ============================================================================
# Opik Setup
# ============================================================================

# Configure Opik client
opik_client = opik.Opik(
    api_key=OPIK_API_KEY,
    workspace=OPIK_WORKSPACE,
    project_name=OPIK_PROJECT_NAME
)

logger.info(f"Opik configured - Project: {OPIK_PROJECT_NAME}, Workspace: {OPIK_WORKSPACE}")

# ============================================================================
# Custom Metrics
# ============================================================================

llm_request_counter = meter.create_counter(
    name="llm.requests.total",
    description="Total number of LLM requests",
    unit="1"
)

llm_token_counter = meter.create_counter(
    name="llm.tokens.total",
    description="Total number of tokens processed",
    unit="1"
)

llm_latency_histogram = meter.create_histogram(
    name="llm.request.duration",
    description="LLM request duration",
    unit="ms"
)

llm_error_counter = meter.create_counter(
    name="llm.errors.total",
    description="Total number of LLM errors",
    unit="1"
)

# ============================================================================
# LLM Chatbot Class with Opik Tracking
# ============================================================================

class OpikObservableChatbot:
    """Chatbot with comprehensive observability using Opik and OpenTelemetry"""
    
    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        self.conversation_history = []
        self.ollama_client = ollama.Client(host=OLLAMA_HOST)
        logger.info(f"Initialized chatbot with model: {model}")
    
    @track(name="chat_completion", capture_input=True, capture_output=True)
    def chat(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message and get a response with full observability
        
        Args:
            user_message: User's input message
            session_id: Optional session identifier for tracking
            
        Returns:
            Dictionary containing response and metadata
        """
        start_time = time.time()
        
        with tracer.start_as_current_span("llm_chat_request") as span:
            span.set_attribute("llm.model", self.model)
            span.set_attribute("llm.user_message_length", len(user_message))
            if session_id:
                span.set_attribute("session.id", session_id)
            
            try:
                # Add user message to history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_message
                })
                
                logger.info(f"Processing message: {user_message[:50]}...")
                
                # Call Ollama with observability
                response = self._call_ollama(user_message)
                
                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response["content"]
                })
                
                # Calculate metrics
                duration_ms = (time.time() - start_time) * 1000
                total_tokens = response.get("total_tokens", 0)
                prompt_tokens = response.get("prompt_tokens", 0)
                completion_tokens = response.get("completion_tokens", 0)
                
                # Update OpenTelemetry metrics
                llm_request_counter.add(1, {"model": self.model, "status": "success"})
                llm_token_counter.add(total_tokens, {"model": self.model, "type": "total"})
                llm_token_counter.add(prompt_tokens, {"model": self.model, "type": "prompt"})
                llm_token_counter.add(completion_tokens, {"model": self.model, "type": "completion"})
                llm_latency_histogram.record(duration_ms, {"model": self.model})
                
                # Set span attributes
                span.set_attribute("llm.response_length", len(response["content"]))
                span.set_attribute("llm.total_tokens", total_tokens)
                span.set_attribute("llm.prompt_tokens", prompt_tokens)
                span.set_attribute("llm.completion_tokens", completion_tokens)
                span.set_attribute("llm.duration_ms", duration_ms)
                span.set_attribute("llm.status", "success")

                opik_context.update_current_span( 
                    metadata={
                        "model": self.model,
                        "eval_duration": duration_ms,
                        "load_duration": duration_ms,
                        "prompt_eval_duration": duration_ms,
                        "prompt_eval_count": prompt_tokens,
                        "done": "done",
                        "done_reason": "done_reason",
                    },
                    usage={
                        "completion_tokens": completion_tokens,
                        "prompt_tokens": prompt_tokens,
                        "total_tokens": total_tokens,
                    },
                )
                
                # Log to Opik with detailed metadata
                #opik_client.log_traces(
                #    project_name=OPIK_PROJECT_NAME,
                #    traces=[{
                #        "name": "chat_completion",
                #        "input": {"message": user_message},
                #        "output": {"response": response["content"]},
                #        "metadata": {
                #            "model": self.model,
                ##            "session_id": session_id,
                 #           "duration_ms": duration_ms,
                 #           "total_tokens": total_tokens,
                 #           "prompt_tokens": prompt_tokens,
                 #           "completion_tokens": completion_tokens
                 #       },
                 ##   }]
                #)
                
                logger.info(f"Response generated in {duration_ms:.2f}ms with {total_tokens} tokens")
                
                return {
                    "response": response["content"],
                    "metadata": {
                        "model": self.model,
                        "duration_ms": duration_ms,
                        "total_tokens": total_tokens,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "session_id": session_id
                    }
                }
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Update error metrics
                llm_error_counter.add(1, {"model": self.model, "error_type": type(e).__name__})
                llm_request_counter.add(1, {"model": self.model, "status": "error"})
                
                # Update span with error
                span.set_attribute("llm.status", "error")
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.record_exception(e)
                
                # Log error to Opik
                #opik_client.log_traces(
                #    project_name=OPIK_PROJECT_NAME,
                #    traces=[{
                #        "name": "chat_completion_error",
                #        "input": {"message": user_message},
                #        "output": {"error": str(e)},
                #        "metadata": {
                #            "model": self.model,
                #            "session_id": session_id,
                #            "error_type": type(e).__name__
                #        },
                #        "tags": ["error", "ollama", self.model]
                #    }]
                #)
                
                logger.error(f"Error in chat: {str(e)}", exc_info=True)
                raise
    
    @track(name="ollama_api_call")
    def _call_ollama(self, message: str) -> Dict[str, Any]:
        """Make API call to Ollama with observability"""
        
        with tracer.start_as_current_span("ollama_api") as span:
            try:
                response = self.ollama_client.chat(
                    model=self.model,
                    messages=self.conversation_history,
                )
                
                # Extract token counts
                prompt_tokens = response.get("prompt_eval_count", 0)
                completion_tokens = response.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens
                
                span.set_attribute("llm.prompt_tokens", prompt_tokens)
                span.set_attribute("llm.completion_tokens", completion_tokens)
                span.set_attribute("llm.total_tokens", total_tokens)
                
                return {
                    "content": response["message"]["content"],
                    "total_tokens": total_tokens,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
                
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Ollama API error: {str(e)}")
                raise
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_history(self):
        """Get conversation history"""
        return self.conversation_history


# ============================================================================
# Demo Application
# ============================================================================

def run_demo():
    """Run interactive demo with observability"""
    
    print("=" * 70)
    print("LLM Observability Demo - Chatbot with Opik & OpenTelemetry")
    print("=" * 70)
    print(f"Model: {OLLAMA_MODEL}")
    print(f"Opik Project: {OPIK_PROJECT_NAME}")
    print(f"OTEL Collector: {OTEL_COLLECTOR_ENDPOINT}")
    print("=" * 70)
    print("\nCommands:")
    print("  - Type your message to chat")
    print("  - 'history' - View conversation history")
    print("  - 'clear' - Clear conversation history")
    print("  - 'quit' or 'exit' - Exit the demo")
    print("=" * 70)
    
    # Initialize chatbot
    chatbot = OpikObservableChatbot(model=OLLAMA_MODEL)
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"Started demo session: {session_id}")
    
    # Create Opik trace for the entire session
    with tracer.start_as_current_span("chatbot_session") as session_span:
        session_span.set_attribute("session.id", session_id)
        
        while True:
            try:
                user_input = input("\n🧑 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    chatbot.clear_history()
                    print("✅ Conversation history cleared")
                    continue
                
                if user_input.lower() == 'history':
                    print("\n📜 Conversation History:")
                    for i, msg in enumerate(chatbot.get_history(), 1):
                        role = "🧑 You" if msg["role"] == "user" else "🤖 Bot"
                        print(f"{i}. {role}: {msg['content'][:100]}...")
                    continue
                
                # Get response with observability
                result = chatbot.chat(user_input, session_id=session_id)
                
                # Display response
                print(f"\n🤖 Bot: {result['response']}")
                print(f"\n📊 Metrics:")
                print(f"   ⏱️  Duration: {result['metadata']['duration_ms']:.2f}ms")
                print(f"   🎫 Tokens: {result['metadata']['total_tokens']} "
                      f"(prompt: {result['metadata']['prompt_tokens']}, "
                      f"completion: {result['metadata']['completion_tokens']})")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                logger.error(f"Demo error: {str(e)}", exc_info=True)
        
        # Set final session attributes
        session_span.set_attribute("session.total_messages", len(chatbot.get_history()))
    
    # Flush observability data
    opik_client.flush()
    logger.info("Demo session ended, observability data flushed")


if __name__ == "__main__":
    run_demo()