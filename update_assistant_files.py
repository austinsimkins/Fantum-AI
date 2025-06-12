import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Get all assistant-purpose file IDs
files = openai.files.list(purpose='assistants').data
file_ids = [f.id for f in files]

# Fetch current assistant
assistant = openai.beta.assistants.retrieve(ASSISTANT_ID)

# Recreate the assistant with updated file list
openai.beta.assistants.update(
    assistant_id=ASSISTANT_ID,
    name=assistant.name,
    instructions=assistant.instructions,
    model=assistant.model,
    tools=[{"type": "retrieval"}],
    tool_resources={
        "file_search": {
            "file_ids": file_ids
        }
    }
)

print("✅ Assistant updated with files:", file_ids)
