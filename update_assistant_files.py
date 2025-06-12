import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Get all assistant-purpose file IDs
files = openai.files.list(purpose='assistants').data
file_ids = [f.id for f in files]

# Fetch current assistant config
assistant = openai.beta.assistants.retrieve(ASSISTANT_ID)

# Update assistant to include all files using the new syntax
openai.beta.assistants.update(
    assistant_id=ASSISTANT_ID,
    name=assistant.name,
    instructions=assistant.instructions,
    model=assistant.model,
    tools=[{"type": "retrieval"}],
    tool_resources={
        "file_search": {
            "files": file_ids  # ✅ Correct key
        }
    }
)

print("✅ Assistant updated with files:", file_ids)
