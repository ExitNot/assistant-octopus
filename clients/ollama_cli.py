import argparse
import asyncio
from services.ollama_llm import OllamaClient, OllamaModel, OllamaAPIError

def parse_args():
    parser = argparse.ArgumentParser(description="Ollama LLM CLI client")
    parser.add_argument("prompt", type=str, help="Prompt to send to the LLM")
    parser.add_argument(
        "--model",
        type=str,
        choices=[m.name.lower() for m in OllamaModel],
        default="LLAMA3_2",
        help="Model to use (default: gemma)",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream the response instead of waiting for the full output",
    )
    return parser.parse_args()

async def main():
    args = parse_args()
    model = OllamaModel[args.model.upper()]
    client = OllamaClient()
    try:
        if args.stream:
            async for chunk in await client.generate(prompt=args.prompt, model=model, stream=True):
                print(chunk, end="", flush=True)
            print()
        else:
            result = await client.generate(model=model, prompt=args.prompt)
            print(result)
    except OllamaAPIError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 