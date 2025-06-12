import os, re, time, openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── secrets (in Render env-vars) ───────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID   = os.getenv("ASSISTANT_ID")

# Optional: only pull files whose names start with this prefix
TRANSCRIPT_PREFIX = "sales_transcript"  # "" → attach every assistant file

# ── initialize Slack app ────────────────────────────────────
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)

# ── helper: fetch assistant-purpose file IDs ────────────────
def get_transcript_file_ids() -> list[str]:
    resp = openai.files.list(purpose="assistants")
    return [
        f.id
        for f in resp.data
        if (not TRANSCRIPT_PREFIX) or f.filename.startswith(TRANSCRIPT_PREFIX)
    ]

# ── Slack event handler ─────────────────────────────────────
@app.event("app_mention")
def handle_mention(body, say, logger):
    question  = re.sub(r"<@[^>]+>", "", body["event"]["text"]).strip()
    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]

    # 1) start a new assistant thread
    thread = openai.beta.threads.create()

    # 2) post the user message + attach transcripts here!
    openai.beta.threads.messages.create(
        thread_id = thread.id,
        role      = "user",
        content   = question,
        file_ids  = get_transcript_file_ids(),   # ← correct placement
    )

    # 3) run the assistant
    run = openai.beta.threads.runs.create(
        thread_id    = thread.id,
        assistant_id = ASSISTANT_ID,
    )

    # 4) wait for it to finish
    while run.status not in ("completed", "failed", "cancelled"):
        time.sleep(1.5)
        run = openai.beta.threads.runs.retrieve(
            thread_id = thread.id,
            run_id    = run.id,
        )

    if run.status != "completed":
        logger.error(f"Assistant run failed: {run}")
        say(
            channel   = body["event"]["channel"],
            text      = "⚠️ Sorry, I couldn’t answer that.",
            thread_ts = thread_ts,
        )
        return

    # 5) fetch the reply and send back to Slack
    answer = (
        openai.beta.threads.messages.list(thread_id=thread.id).data[0]
        .content[0].text.value
        + "\n\nDoes that help?"
    )

    say(
        channel   = body["event"]["channel"],
        text      = answer,
        thread_ts = thread_ts,
        username  = "Fantum Specter",
    )

# ── start Socket Mode ────────────────────────────────────────
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
