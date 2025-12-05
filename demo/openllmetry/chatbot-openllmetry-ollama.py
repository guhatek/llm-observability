import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import workflow
from traceloop.sdk.tracing.manual import LLMMessage, LLMUsage, track_llm_call
import ollama
from openai import OpenAI

# Configure OpenTelemetry
resource = Resource(attributes={
    "service.name": "openllemetry-ollama-chatbot",
    "service.version": "1.0.0"
})

# Set up tracer provider
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

OLLAMA_BASE_URL = "http://localhost:11434/v1"
OTEL_ENDPOINT = "http://localhost:4317"
DEFAULT_MODEL = "llama3.1:8b"

client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

def initialize_openllmetry():
  
    TRACELOOP_BASE_URL = os.environ.get("TRACELOOP_BASE_URL", "http://localhost:4318")

    # Configure OTLP exporter to send to local collector
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4318/v1/traces",  # OTEL collector HTTP endpoint
        headers={}
    )

    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Initialize OpenLLMetry instrumentation for Ollama
    Traceloop.init(
        app_name="openllmetry-ollama-chatbot",
        disable_batch=True,  # For local development to see traces immediately
        api_key="local-dev-key",  # Use local dev key for local Traceloop instance
        #endpoint=TRACELOOP_BASE_URL
    )


# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

@workflow(name="chat")
def chat(message: str, conversation_history: list = None) -> str:
    """
    Send a message to the chatbot and get a response.
    
    Args:
        message: User's message
        conversation_history: List of previous messages for context
    
    Returns:
        Bot's response
    """
    if conversation_history is None:
        conversation_history = []
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": message
    })
    
    try:
        # Make API call to Ollama (automatically traced by OpenLLMetry)
        with track_llm_call(vendor="openai", type="chat") as span:
            span.report_request(
                model="llama3.1:8b",
                messages=[
                    LLMMessage(role="user", content=message)
                ],
            )
            
            response = ollama.chat(
                model="llama3.1:8b",
                messages=conversation_history,
                options={
                    "temperature": 0.7,
                    "num_predict": 500
                }
            )

            # Extract assistant's response
            assistant_message = response['message']['content']
            
            # Add metrics to span
            #span.set_attribute("llm.response_length", len(assistant_message))
            #if 'prompt_eval_count' in response:
            #    span.set_attribute("llm.prompt_tokens", response['prompt_eval_count'])
            #if 'eval_count' in response:
            #    span.set_attribute("llm.completion_tokens", response['eval_count'])

            
            # Add assistant response to history
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
    
    except Exception as e:
        return f"Error: {str(e)}"

@workflow(name="chat_stream")
def chat_stream(message: str, conversation_history: list = None):
    """
    Send a message to the chatbot and stream the response.
    
    Args:
        message: User's message
        conversation_history: List of previous messages for context
    
    Yields:
        Chunks of the bot's response
    """
    if conversation_history is None:
        conversation_history = []
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": message
    })
    
    try:
        with tracer.start_as_current_span("ollama.chat.stream") as span:
            span.set_attribute("llm.model", "llama3.1:8b")
            span.set_attribute("llm.streaming", True)
            
            # Stream response from Ollama
            stream = ollama.chat(
                model="llama3.1:8b",
                messages=conversation_history,
                stream=True,
                options={
                    "temperature": 0.7,
                    "num_predict": 500
                }
            )
            
            full_response = ""
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                yield content
            
            # Add metrics after streaming completes
            span.set_attribute("llm.response_length", len(full_response))
            
            # Add complete response to history
            conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
    
    except Exception as e:
        yield f"Error: {str(e)}"


def main():
    """Main chatbot loop."""
    print("=" * 60)
    print("Ollama Chatbot with OpenLLMetry Observability")
    print("=" * 60)
    print("Model: llama3.1:8b")
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'clear' to reset conversation history")
    print("Type 'stream' to toggle streaming mode")
    print("=" * 60)
    print()
    
    conversation_history = []
    use_streaming = False

    initialize_openllmetry()
    
    try:
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye!")
                break
            
            # Check for clear command
            if user_input.lower() == 'clear':
                conversation_history = []
                print("\n[Conversation history cleared]\n")
                continue
            
            # Check for stream toggle
            if user_input.lower() == 'stream':
                use_streaming = not use_streaming
                mode = "enabled" if use_streaming else "disabled"
                print(f"\n[Streaming mode {mode}]\n")
                continue
            
            # Get response from chatbot
            print("\nBot: ", end="", flush=True)
            
            if use_streaming:
                # Stream the response
                for chunk in chat_stream(user_input, conversation_history):
                    print(chunk, end="", flush=True)
                print("\n")
            else:
                # Get complete response
                response = chat(user_input, conversation_history)
                print(response)
                print()
    
    finally:
        # Ensure all spans are exported before exit
        tracer_provider.force_flush()


if __name__ == "__main__":
    main()