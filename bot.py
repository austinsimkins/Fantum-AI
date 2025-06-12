@app.event("app_mention")
def handle_mention(body, say, logger):
    question  = re.sub(r"<@[^>]+>", "", body["event"]["text"]).strip()
    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]

    # create a new thread
    thread = openai.beta.threads.create()

    # add user message (❌ no file_ids here)
    openai.beta.threads.messages.create(
        thread_id = thread.id,
        role      = "user",
        content   = question,
    )

    # run assistant (✅ attach files here)
    run = openai.beta.threads.runs.create(
        thread_id    = thread.id,
        assistant_id = ASSISTANT_ID,
        file_ids     = get_transcript_file_ids(),
    )

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

    say(
        channel   = body["event"]["channel"],
        text      = answer,
        thread_ts = thread_ts,
        username  = "Fantum Specter",
    )
