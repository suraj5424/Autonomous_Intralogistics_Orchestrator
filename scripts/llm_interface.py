import os
import textwrap
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load .env file from project root
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

# ------------------------
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
cere_client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    # api_key=os.getenv("CEREBRAS_API_KEY"),  
    api_key=CEREBRAS_API_KEY,  
)

# Toggle mode: "fake", "cerebras"
LLM_MODE = "cerebras"

# ------------------------
# LLM FUNCTIONS
# ------------------------
def call_cerebras(prompt, model="gpt-oss-120b"):
    """
    Calls Cerebras API and returns assistant's message
    """
    response = cere_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# # Load the OpenRouter API key
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# # Initialize the OpenRouter client
# client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=OPENROUTER_API_KEY,
# )

# # Toggle mode: "fake", "openrouter"
# LLM_MODE = "openrouter"

# # ------------------------
# # LLM FUNCTIONS
# # ------------------------

# def call_cerebras(prompt, model="xiaomi/mimo-v2-flash:free"):
#     """
#     Calls OpenRouter API and returns assistant's message
#     """
#     response = client.chat.completions.create(
#         model=model,
#         messages=[{"role": "user", "content": prompt}],
#         extra_body={"reasoning": {"enabled": True}}  # Optional reasoning flag
#     )
#     return response.choices[0].message.content    

def print_response_chunks(response, chunk_size=80):
    for chunk in textwrap.wrap(response, chunk_size):
        print(chunk)

# ------------------------
# PROMPT BUILDER
# ------------------------
def build_prompt(row):
    """
    Build LLM prompt based on a warehouse order row
    """
    return f"""
You are an intralogistics operations expert.

Analyze the following warehouse order and robot status:

Order ID: {row.order_id}
Order Status: {row.status}
Robot ID: {row.robot_id}
Robot Health: {row.health_status}
Anomaly Count: {row.anomaly_count}
Order Risk Level: {row.order_risk}

Explain in simple business terms:
1. What is the problem (if any)?
2. Why it is happening?
3. What action should be taken next?

Keep the explanation short and clear.
"""