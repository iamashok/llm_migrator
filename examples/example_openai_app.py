"""
Example: OpenAI API usage in a typical application
This file demonstrates common OpenAI patterns that the migration tool detects.
"""

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def chat_completion_example():
    """Basic chat completion"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    return response.choices[0].message.content


def streaming_example():
    """Streaming chat completion"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Tell me a story"}],
        stream=True
    )
    
    result = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="")
            result += content
    
    return result


def function_calling_example():
    """Function calling / tool use"""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "What's the weather in Paris?"}],
        tools=tools,
        tool_choice="auto"
    )
    
    return response.choices[0].message


def embedding_example():
    """Generate embeddings"""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input="Your text to embed here"
    )
    
    embedding = response.data[0].embedding
    return embedding


def batch_embedding_example():
    """Generate multiple embeddings"""
    texts = [
        "First document",
        "Second document",
        "Third document"
    ]
    
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    
    embeddings = [item.embedding for item in response.data]
    return embeddings


if __name__ == "__main__":
    print("🤖 Running OpenAI examples...")
    
    # Chat completion
    result = chat_completion_example()
    print(f"Chat: {result}")
    
    # Streaming
    print("\nStreaming: ", end="")
    streaming_example()
    
    # Function calling
    response = function_calling_example()
    print(f"\n\nFunction calling: {response}")
    
    # Embeddings
    embedding = embedding_example()
    print(f"\nEmbedding dimension: {len(embedding)}")
