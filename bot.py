import os, re, openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# --- keys from your Render secrets ---
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID   = os.getenv("ASSISTANT_ID")

app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

@app.event("app_mention")
def handle_mention(body, say):
    # strip the @bot tag
    question  = re.sub(r"<@[^>]+>", "", body["event"]["text"]).strip()
    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]

    # ---- Ask your OpenAI Assistant ----
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(thread.id, role="user", content=question)
    run = openai.beta.threads.runs.create(thread.id, assistant_id=ASSISTANT_ID)
    while run.status != "completed":
        run = openai.beta.threads.runs.retrieve(thread.id, run.id)

    answer = openai.beta.threads.messages.list(thread.id).data[0]\
             .content[0].text.value + "\n\nDoes that help?"

    # ---- Reply in Slack ----
    say(
        channel=body["event"]["channel"],
        text=answer,
        thread_ts=thread_ts,
        username="Fantum Specter",
        icon_url="https://YOUR-LOGO-URL.png"      # swap to your logo URL or delete line
    )

if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
