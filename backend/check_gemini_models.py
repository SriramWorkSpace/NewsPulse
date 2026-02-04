"""
Script to check available Gemini models and test the API key.
"""
import httpx
import json
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"✅ Found API Key: {GEMINI_API_KEY[:20]}...")


async def check_models():
    """List all available Gemini models."""
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        # List models endpoint
        url = "https://generativelanguage.googleapis.com/v1/models"
        
        print("\n📋 Fetching available Gemini models...\n")
        response = await client.get(url, params={"key": GEMINI_API_KEY})
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        models = data.get("models", [])
        
        print(f"Found {len(models)} models:\n")
        
        # Filter for generateContent models
        generate_models = []
        for model in models:
            name = model.get("name", "")
            supported_methods = model.get("supportedGenerationMethods", [])
            
            if "generateContent" in supported_methods:
                generate_models.append(model)
                model_id = name.replace("models/", "")
                print(f"✅ {model_id}")
                print(f"   Display Name: {model.get('displayName', 'N/A')}")
                print(f"   Description: {model.get('description', 'N/A')[:80]}...")
                print(f"   Supported: {', '.join(supported_methods)}")
                print()
        
        print(f"\n🎯 {len(generate_models)} models support generateContent")
        
        # Test a model
        if generate_models:
            test_model = generate_models[0].get("name", "").replace("models/", "")
            print(f"\n🧪 Testing {test_model}...")
            
            test_url = f"https://generativelanguage.googleapis.com/v1/models/{test_model}:generateContent"
            test_payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": "Say 'Hello, I am working!' in one sentence."}
                        ]
                    }
                ]
            }
            
            test_response = await client.post(
                test_url, 
                params={"key": GEMINI_API_KEY}, 
                json=test_payload
            )
            
            if test_response.status_code == 200:
                result = test_response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✅ Success! Response: {text.strip()}")
            else:
                print(f"❌ Failed: {test_response.status_code}")
                print(test_response.text)
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    import asyncio
    asyncio.run(check_models())
