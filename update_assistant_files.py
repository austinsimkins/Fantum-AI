import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

files = openai.files.list(purpose='assistants')
file_ids = [file.id for file in files.data]

openai.beta.assistants.update(
    assistant_id=ASSISTANT_ID,
    tools=[{"type": "retrieval"}],
    file_ids=file_ids
)

print(f"✅ Assistant updated with files: {file_ids}")
