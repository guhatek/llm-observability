"""
Complete LLM Observability Demo with Langfuse + OpenTelemetry
Works with Ollama and sends traces to multiple backends
"""

from openai import OpenAI
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
import time
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import workflow
from traceloop.sdk.tracing.manual import LLMMessage, LLMUsage, track_llm_call

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OTEL_ENDPOINT = "http://localhost:4318"
DEFAULT_MODEL = "llama3.1:8b"

#export TRACELOOP_BASE_URL="http://localhost:4317"                     
#export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

class LLMObservabilityAgent:
    """Agent with built-in observability using OpenTelemetry"""
    
    def __init__(self, service_name="ollama-demo-agent"):
        # Setup OpenTelemetry
        resource = Resource.create({"service.name": service_name})
        # keep service name for metric attributes
        self.service_name = service_name

                # Initialize OpenLLMetry instrumentation for Ollama
        Traceloop.init(
            app_name="openllmetry-ollama-chatbot",
            disable_batch=True,  # For local development to see traces immediately
            api_key="local-dev-key",  # Use local dev key for local Traceloop instance
            #endpoint=TRACELOOP_BASE_URL
        )
        
        # Setup Tracing
        trace_provider = TracerProvider(resource=resource)
        #(endpoint=OTEL_ENDPOINT, insecure=True)
        #trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        #trace.set_tracer_provider(trace_provider)
        #self.tracer = trace.get_tracer(__name__)
        
        # Setup Metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=OTEL_ENDPOINT)
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        meter = metrics.get_meter(__name__)
        
        # Create custom metrics
        self.request_counter = meter.create_counter(
            "llm_requests_total",
            description="Total number of LLM requests"
        )
        self.token_counter = meter.create_counter(
            "llm_tokens_total",
            description="Total tokens used"
        )
        self.latency_histogram = meter.create_histogram(
            "llm_request_duration",
            description="LLM request duration in seconds",
            unit="s"
        )
        
        # Initialize Ollama client
        self.client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        
        print(f"✅ {service_name} initialized with observability")
        print(f"📊 Sending traces to: {OTEL_ENDPOINT}")
    
    def chat(self, prompt: str, model: str = DEFAULT_MODEL, **kwargs):
        """
        Send a chat request with full observability
        """
        with track_llm_call(vendor="ollama", type="chat") as span:
            span.report_request(
                model=DEFAULT_MODEL,
                messages=[
                    LLMMessage(role="user", content=prompt)
                ],
            )
            
            start_time = time.time()
            
            try:
                # Make the LLM call
                #with self.tracer.start_as_current_span("llm.completion"):
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 500)
                )
                
                duration = time.time() - start_time
                
                # Extract response
                content = response.choices[0].message.content
                
                # Record metrics
                self.request_counter.add(1, {"model": model, "status": "success", "service": self.service_name})
                self.latency_histogram.record(duration, {"model": model, "service": self.service_name})
                
                if hasattr(response, 'usage') and response.usage:
                    total_tokens = response.usage.total_tokens
                    self.token_counter.add(
                        total_tokens,
                        {"model": model, "type": "total", "service": self.service_name}
                    )
                    #span.set_attribute("llm.tokens.total", total_tokens)
                    #span.set_attribute("llm.tokens.prompt", response.usage.prompt_tokens)
                    #span.set_attribute("llm.tokens.completion", response.usage.completion_tokens)
                    span.report_response(response.model, [text.message.content for text in response.choices])
                    span.report_usage(
                        LLMUsage(
                            prompt_tokens=response.usage.prompt_tokens,
                            completion_tokens=response.usage.completion_tokens,
                            total_tokens=total_tokens,
                            #=response.usage.cache_creation_input_tokens,
                            #cache_read_input_tokens=response.usage.cache_read_input_tokens,
                        )
                    )
                
                # Add response attributes
                span._span.set_attribute("llm.response", content[:100])
                span._span.set_attribute("llm.duration_ms", duration * 1000)
                span._span.set_attribute("llm.finish_reason", response.choices[0].finish_reason)
                
                return {
                    "content": content,
                    "duration": duration,
                    "tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0,
                    "model": model
                }
                
            except Exception as e:
                # Record error
                span._span.set_attribute("error", True)
                span._span.set_attribute("error.message", str(e))
                self.request_counter.add(1, {"model": model, "status": "error", "service": self.service_name})
                
                print(f"❌ Error: {e}")
                return None

def run_demo():
    """Run a complete demo with various queries"""
    
    print("\n" + "="*70)
    print("🚀 LLM Observability Demo Starting")
    print("="*70)
    
    # Initialize agent
    agent = LLMObservabilityAgent()
    
    # Demo queries
    queries = [
        {
            "prompt": "What is machine learning in one sentence?",
            "category": "definition"
        }#,
        #{
        #    "prompt": "Explain Docker containers in simple terms.",
        #    "category": "technical"
        #},
        #{
        #    "prompt": "What are the benefits of observability in software systems?",
        #    "category": "architecture"
        #},
        #{
        #    "prompt": "Write a haiku about debugging code.",
        #    "category": "creative"
        #},
        #{
        #    "prompt": "Compare REST APIs with GraphQL.",
        #    "category": "comparison"
        #}
    ]
    
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 Query {i}/{len(queries)}: {query['prompt']}")
        print("-" * 70)
        
        result = agent.chat(query["prompt"])
        
        if result:
            print(f"✅ Response: {result['content']}")
            print(f"⏱️  Duration: {result['duration']:.2f}s")
            print(f"🎯 Tokens: {result['tokens']}")
            results.append(result)
        else:
            print("❌ Failed to get response")
        
        print("-" * 70)
        time.sleep(0.5)  # Brief pause between requests
    
    # Summary
    print("\n" + "="*70)
    print("📊 Demo Summary")
    print("="*70)
    print(f"Total queries: {len(queries)}")
    print(f"Successful: {len(results)}")
    #print(f"Average duration: {sum(r['duration'] for r in results) / len(results):.2f}s")
    print(f"Total tokens: {sum(r['tokens'] for r in results)}")
    print("\n🔍 View traces and metrics:")
    print("  - Jaeger UI:     http://localhost:16686")
    print("  - Prometheus:    http://localhost:9090")
    print("  - Grafana:       http://localhost:3001")
    print("="*70 + "\n")

def simple_test():
    """Simple test without instrumentation"""
    print("🧪 Running simple test...")
    
    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": "Say hello!"}]
        )
        print(f"✅ Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        simple_test()
    else:
        run_demo()