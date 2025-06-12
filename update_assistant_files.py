import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key   = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID     = os.getenv("ASSISTANT_ID")

# 1) Pull down the list of all your assistant-purpose files
files = openai.files.list(purpose="assistants").data

# 2) Attach each file to your assistant (skip if already added)
for f in files:
    try:
        openai.beta.assistants.files.create(
            assistant_id=ASSISTANT_ID,
            file_id=f.id
        )
        print(f"➕ Attached {f.id}")
    except openai.error.InvalidRequestError as e:
        # if it’s already on the assistant, ignore that error
        if "already exists" in str(e):
            continue
        raise

# 3) Flip the assistant’s tool to file_search (only needs to run once)
assistant = openai.beta.assistants.retrieve(ASSISTANT_ID)
openai.beta.assistants.update(
    assistant_id=ASSISTANT_ID,
    name=assistant.name,
    instructions=assistant.instructions,
    model=assistant.model,
    tools=[{"type": "file_search"}],
)

print("✅ All files attached and file_search enabled!")
