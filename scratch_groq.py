import os
from groq import Groq

try:
    api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.5
    )
    print("Success:", response.choices[0].message.content)
except Exception as e:
    import traceback
    traceback.print_exc()
