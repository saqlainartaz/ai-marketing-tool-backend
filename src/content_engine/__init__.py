from dotenv import load_dotenv

# Load .env from the working directory so providers reading os.environ
# (ANTHROPIC_API_KEY, VOYAGE_API_KEY, ENGINE_* switches) see it in every
# entrypoint — uvicorn, pytest, scripts. Existing env vars always win.
load_dotenv()
