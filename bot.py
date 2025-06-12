import os, re, time, openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── secrets (set as Render env-vars) ────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID   = os.getenv("ASSISTANT_ID")

# If you only want certain files, give them a prefix (else leave "")
TRANSCRIPT_PREFIX = "sales_transcript"          # "" → attach every assistant file

# ── Slack app bootstrap ─────────────────────────────────────────
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)

# ── helper: get every assistant-purpose file-id on the fly ──────
def get_transcript_file_ids() -> list[str]:
    """
    Return IDs of files whose filename begins with TRANSCRIPT_PREFIX.
    If the prefix is '', we return *all* assistant files.
    """
    resp = openai.files.list(purpose="assistants")      # top-level list call
    return [
        f.id
        for f in resp.data
        if (not TRANSCRIPT_PREFIX) or f.filename.startswith(TRANSCRIPT_PREFIX)
    ]

# ── Slack listener ──────────────────────────────────────────────
@app.event("app_mention")
def handle_mention(body, say, logger):
    # remove the “@Fantum AI” tag
    question  = re.sub(r"<@[^>]+>", "", body["event"]["text"]).strip()
    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]

    # ── Ask our Assistant ───────────────────────────────────────
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id = thread.id,
        role      = "user",
        content   = question,
    )

    run = openai.beta.threads.runs.create(
        thread_id    = thread.id,
        assistant_id = ASSISTANT_ID,
        file_ids     = get_transcript_file_ids(),   # dynamic context!
    )

    # simple poll loop until run finishes
    while run.status not in ("completed", "failed", "cancelled"):
        time.sleep(1.5)
        run = openai.beta.threads.runs.retrieve(
            thread_id = thread.id,
            run_id    = run.id,
        )

    if run.status != "completed":
        logger.error(f"Assistant run failed: {run}")
        say(channel=body["event"]["channel"],
            text="⚠️ Sorry, I couldn’t answer that.",
            thread_ts=thread_ts)
        return

    answer = (
        openai.beta.threads.messages.list(thread_id=thread.id).data[0]
        .content[0].text.value
        + "\n\nDoes that help?"
    )

    # ── reply in Slack ──────────────────────────────────────────
    say(
        channel   = body["event"]["channel"],
        text      = answer,
        thread_ts = thread_ts,
        username  = "Fantum Specter",
        # icon_url = "https://YOUR-LOGO.png",        # optional brand icon
    )

# ── kick things off ─────────────────────────────────────────────
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
