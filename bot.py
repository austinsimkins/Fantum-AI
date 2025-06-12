import os, re, time, openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── secrets (all set as Render / host ENV-VARS) ───────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")          # sk-…
ASSISTANT_ID    = os.getenv("ASSISTANT_ID")           # asst_…

# If you want to limit which files get attached, give them a prefix.
# Leave this as "" to attach *every* file whose purpose = assistants
TRANSCRIPT_PREFIX = "sales_transcript"

# ── Slack app bootstrap ───────────────────────────────────────────────────
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),               # xoxb-…
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"), # 9e…
)

# ── helper: grab every assistant-file ID that matches our prefix ──────────
def get_transcript_file_ids() -> list[str]:
    """
    Return the IDs of files (purpose='assistants') whose filename starts
    with TRANSCRIPT_PREFIX.  If the prefix is blank, return *all* IDs.
    """
    files = openai.files.list(purpose="assistants").data   # ← top-level list
    return [
        f.id                                               # file-XYZ
        for f in files
        if (not TRANSCRIPT_PREFIX) or f.filename.startswith(TRANSCRIPT_PREFIX)
    ]

# ── Slack listener (@Fantum AI mention) ───────────────────────────────────
@app.event("app_mention")
def handle_mention(body, say, logger):
    # strip the “@Fantum AI” tag
    question  = re.sub(r"<@[^>]+>", "", body["event"]["text"]).strip()
    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]

    # 1️⃣ Create a new assistant thread
    thread = openai.beta.threads.create()

    # 2️⃣ Post the user’s question (+ any files) into that thread
    openai.beta.threads.messages.create(
        thread_id = thread.id,
        role      = "user",
        content   = question,
        file_ids  = get_transcript_file_ids(),     # ← attach transcripts here
    )

    # 3️⃣ Kick off the run
    run = openai.beta.threads.runs.create(
        thread_id    = thread.id,
        assistant_id = ASSISTANT_ID,
    )

    # 4️⃣ Poll until finished
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

    # 5️⃣ Fetch the assistant’s first message
    answer = (
        openai.beta.threads.messages.list(thread_id=thread.id).data[0]
        .content[0].text.value
        + "\n\nDoes that help?"
    )

    # 6️⃣ Post reply back in Slack
    say(
        channel   = body["event"]["channel"],
        text      = answer,
        thread_ts = thread_ts,
        username  = "Fantum Specter",
        # icon_url = "https://YOUR-LOGO.png",   # optional branding
    )


# ── Launch Socket Mode listener ───────────────────────────────────────────
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
