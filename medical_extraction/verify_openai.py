from openai import OpenAI
import os
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()  # Looks for .env file in same directory

# 2. Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 3. Test access with new SDK syntax
try:
    print("🧪 Testing OpenAI access with v1.0+ SDK...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("✅ GPT-4 Access Verified!")
    print(f"Response: {response}")
    print(f"First 5 chars of response: {response.choices[0].message.content[:5]}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\n🔧 Troubleshooting Steps:")
    print("1. Verify .env file exists with OPENAI_API_KEY=your_key_here")
    print("2. Check key at: https://platform.openai.com/api-keys")
    print("3. Ensure you're using openai>=1.0.0 (run: pip install --upgrade openai)")
    print("4. Try a new key if this one fails")