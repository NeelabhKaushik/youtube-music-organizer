# YouTube Music Mood Organizer

**Turn your Liked Songs into seven private playlists.** Go from gym fuel to 2 AM blues, with a dedicated home for Desi hip-hop.

**Jolly / Feel Good · High Adrenaline · Sad / 2 AM · Deep Focus · Chill / Late Night · Romantic · DHH Essentials**

Runs on macOS with Python 3.10+ and [Ollama](https://ollama.com/). Classification runs locally with no paid API.

## Get started

1. Copy the request headers from a signed-in YouTube Music tab using the [browser authentication guide](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html). Keep the headers local.
2. Start Ollama, then run these commands from the repo:

   ```sh
   pbpaste | ./organize-once.sh auth
   ollama pull qwen3:4b
   ./organize-once.sh
   ```

3. Open `data/preview.csv`. Enter the displayed approval hash when you’re happy with the mix, or press Enter to stop. Run `./organize-once.sh review` to return to the preview later.

Tracks can land in several moods. Uncertain picks stay out of the upload, and your original likes stay intact. Backups and credentials stay local. Keep `data/sync.json` so reruns can resume without duplicating playlists.

The script removes its temporary Python environment on exit. If you downloaded the model just for this run, remove it with `ollama rm qwen3:4b`.
