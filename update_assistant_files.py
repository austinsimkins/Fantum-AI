import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Get all assistant-purpose files
files = openai.files.list(purpose='assistants').data
file_ids = [f.id for f in files]

# Fetch the existing assistant config
assistant = openai.beta.assistants.retrieve(ASSISTANT_ID)

# ✅ Update assistant with file search tool and attach files
updated_assistant = openai.beta.assistants.update(
    assistant_id=ASSISTANT_ID,
    name=assistant.name,
    instructions=assistant.instructions,
    model=assistant.model,
    tools=[{"type": "file_search"}],  # valid tool type
    file_ids=file_ids  # 🔥 THIS is where the files go
)

print("✅ Assistant updated with files:", file_ids)
