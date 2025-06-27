import os, re, openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── load keys from environment ───────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID   = os.getenv("ASSISTANT_ID")

# ── initialize your Slack app ────────────────────────────────────
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)

# ── handle @mentions ──────────────────────────────────────────────
@app.event("app_mention")
def handle_mention(body, say):
    # strip out the @bot mention
    user_q    = re.sub(r"<@[^>]+>", "", body["event"]["text"]).strip()
    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]

    # 1) start a new Assistant thread
    thread = openai.beta.threads.create()

    # 2) add the user’s question
    openai.beta.threads.messages.create(
        thread.id,
        role="user",
        content=user_q,
    )

    # 3) run the assistant (no file attachments)
    run = openai.beta.threads.runs.create(
        thread.id,
        assistant_id=ASSISTANT_ID,
    )

    # 4) wait until it finishes, using keyword args for retrieve
    while run.status != "completed":
        run = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )

    # 5) grab the assistant’s reply
    reply = openai.beta.threads.messages.list(thread.id).data[0]\
                .content[0].text.value

    # 6) respond in Slack thread
   app.client.chat_postMessage(
        channel=body["event"]["channel"],
        text=f"{reply}\n\nDoes that help?",
        thread_ts=thread_ts
        mrkdwn=False  # disables Slack markdown
    )

# ── start the Socket Mode listener ───────────────────────────────
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
