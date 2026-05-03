import os
from groq import Groq

try:
    api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a friendly AI Project Estimator Assistant."},
            {"role": "user", "content": "i wnat to create an ai startup"}
        ],
        temperature=0.5
    )
    print("Success:", response.choices[0].message.content)
except Exception as e:
    import traceback
    traceback.print_exc()
