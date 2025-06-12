import os, re, openai, time
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── keys from your Render / host secrets ─────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID   = os.getenv("ASSISTANT_ID")

# (OPTIONAL) only pull files whose names start with this
TRANSCRIPT_PREFIX = "sales_transcript"          # edit or leave "" to grab everything

# ── Slack app bootstrap ──────────────────────────────────────────
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

# ── helper: grab every transcript file-id on the fly ─────────────
def get_transcript_file_ids():
    """
    Returns a list of file-ids whose filename starts with TRANSCRIPT_PREFIX.
    If TRANSCRIPT_PREFIX is '', it returns *all* assistant files.
    """
    files = openai.files.list(purpose="assistants").data
    return [
        f.id for f in files
        if (not TRANSCRIPT_PREFIX) or f.filename.startswith(TRANSCRIPT_PREFIX)
    ]

# ── Slack listener ───────────────────────────────────────────────
@app.event("app_mention")
def handle_mention(body, say, logger):
    # strip the @bot tag & grab thread
    question  = re.sub(r"<@[^>]+>", "", body["event"]["text"]).strip()
    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]

    # ── Ask OpenAI assistant ────────────────────────────────────
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id = thread.id,
        role      = "user",
        content   = question
    )

    run = openai.beta.threads.runs.create(
        thread_id    = thread.id,
        assistant_id = ASSISTANT_ID,
        file_ids     = get_transcript_file_ids()   # ← dynamic context
    )

    # simple poll loop until run completes
    while run.status not in ("completed", "failed", "cancelled"):
        time.sleep(1.5)
        run = openai.beta.threads.runs.retrieve(
            thread_id = thread.id,
            run_id    = run.id
        )

    if run.status != "completed":
        say(text="Sorry, I couldn’t finish that request 🤖", thread_ts=thread_ts)
        logger.error(f"Run failed: {run}")
        return

    answer = (
        openai.beta.threads.messages.list(thread_id=thread.id).data[0]
        .content[0].text.value
        + "\n\nDoes that help?"
    )

    # ── reply back in Slack ─────────────────────────────────────
    say(
        channel   = body["event"]["channel"],
        text      = answer,
        thread_ts = thread_ts,
        username  = "Fantum Specter",
        # icon_url = "https://YOUR-LOGO-URL.png",   # optional brand icon
    )

# ── kick things off ─────────────────────────────────────────────
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
