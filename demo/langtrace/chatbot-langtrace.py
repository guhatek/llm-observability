import os
from langtrace_python_sdk import langtrace
import ollama
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


# Initialize LangTrace with OTEL collector endpoint
#langtrace.init(
#    api_key="your-langtrace-api-key",  # Optional if using self-hosted
#    write_spans_to_console=True,  # Debug: prints spans to console
#    custom_remote_exporter={
#        "endpoint": "http://localhost:4318/v1/traces",  # OTEL collector endpoint
#        "headers": {},
#    }
#)

OTLP_ENDPOINT = os.environ.get("OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
BATCH_EXPORT = False  # set True if you want batch sending behavior
SERVICE_NAME = "ollama-langtrace-chatbot"

# -------------------------
# Initialize Langtrace with OTLP exporter
# -------------------------
def init_langtrace_with_otlp():
    """
    Initialize langtrace SDK using an OTLPSpanExporter as the remote exporter.
    This instructs langtrace to forward spans via that exporter.
    """
    otlp_exporter = OTLPSpanExporter(
        endpoint=OTLP_ENDPOINT,
        # headers typically not required for local collector but can be passed as dict
        headers={"Content-Type": "application/json"},
    )

    # Initialize langtrace. `batch` controls whether traces are batched in Langtrace before
    # sending to the remote exporter; the docs show custom_remote_exporter usage
    langtrace.init(
        api_key="local-dev",                  # dummy key for local usage
        service_name=SERVICE_NAME,
        custom_remote_exporter=otlp_exporter, # ✅ EXPORTS TO LOCAL OTEL COLLECTOR
        batch=False,                           # ✅ instant flushing for local testing
        disable_instrumentations=None,  # instrument everything
        disable_tracing_for_functions=None,
        write_spans_to_console=False,
        #api_host="http://localhost:4318",
        )
    print(f"[langtrace] initialized with OTLP endpoint: {OTLP_ENDPOINT}")


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
        # Make API call to Ollama (traced by LangTrace)
        response = ollama.chat(
            model="llama3.1:8b",
            messages=conversation_history,
            options={
                "temperature": 0.7,
                "num_predict": 500  # max_tokens equivalent
            }
        )
        
        # Extract assistant's response
        assistant_message = response['message']['content']
        
        # Add assistant response to history
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message
    
    except Exception as e:
        return f"Error: {str(e)}"


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
    print("Ollama Chatbot with LangTrace Observability")
    print("=" * 60)
    print("Model: llama3.1:8b")
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'clear' to reset conversation history")
    print("Type 'stream' to toggle streaming mode")
    print("=" * 60)
    print()
    
    conversation_history = []
    use_streaming = False

    # Initialize langtrace exporter first so the LLM call is traced.
    init_langtrace_with_otlp()
    
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


if __name__ == "__main__":
    main()