import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Your new Vector Store ID:
VECTOR_STORE_ID = "vs_684a9ed579788191846098a478006016"

# 1) Retrieve the existing assistant configuration
assistant = openai.beta.assistants.retrieve(ASSISTANT_ID)

# 2) Update it to use file_search via your vector store
updated = openai.beta.assistants.update(
    assistant_id=ASSISTANT_ID,
    name=assistant.name,
    instructions=assistant.instructions,
    model=assistant.model,
    tools=[{"type": "file_search"}],
    tool_resources={
        "file_search": {
            "vector_store_ids": [VECTOR_STORE_ID]
        }
    }
)

print("✅ Assistant updated. File Search now uses Vector Store:", VECTOR_STORE_ID)
