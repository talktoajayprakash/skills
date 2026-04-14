---
name: spotify
description: Search songs, manage playlists, control playback queue, and play/pause on Spotify. Use when the user asks anything about Spotify — music, playlists, queue, playing, searching for songs.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Spotify — Search, Playlists, Queue & Playback Control

This skill uses the Spotify CLI bundled at `~/.claude/skills/spotify/spotify_cli.py` to manage Spotify via the Web API.

The CLI script, `.env` credentials, and token cache all live inside the skill directory so the skill is fully self-contained.

**CLI shorthand used below:**
```
SPOTIFY="python3 ~/.claude/skills/spotify/spotify_cli.py"
```

## Setup

### 1. Create a Spotify Developer app

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in with your Spotify account
2. Click **Create app**
3. Fill in:
   - **App name**: anything (e.g. "Claude Code")
   - **App description**: anything
   - **Redirect URI**: `http://127.0.0.1:8888/callback` — must be exact
   - **APIs used**: check **Web API**
4. Click **Save**

### 2. Get your credentials

1. Open your new app and click **Settings**
2. Copy the **Client ID**
3. Click **View client secret** and copy the **Client Secret**

### 3. Configure the .env file

```bash
cp ~/.claude/skills/spotify/.env.example ~/.claude/skills/spotify/.env
```

Edit `.env` and fill in your values:

```
SPOTIPY_CLIENT_ID=paste_client_id_here
SPOTIPY_CLIENT_SECRET=paste_client_secret_here
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### 4. Install the Python dependency

```bash
pip install spotipy
```

### 5. Authenticate

```bash
python3 ~/.claude/skills/spotify/spotify_cli.py auth
```

A browser window opens — log in with Spotify and click **Agree**. The token is cached at `.spotify_token_cache` and auto-refreshes from then on. You only need to do this once.

---

## When to trigger

Activate this skill whenever the user asks to:
- Search for a song, artist, album, or playlist
- List, create, rename, or delete playlists
- Add or remove songs from a playlist
- See what's currently playing
- View or manage the playback queue
- Control playback (play, pause, skip, previous, shuffle, repeat)
- Like or unlike songs
- List or switch playback devices

## CLI Reference

All commands use: `python3 ~/.claude/skills/spotify/spotify_cli.py <command> [args]`

### Authentication

```bash
python3 ~/.claude/skills/spotify/spotify_cli.py auth
```

### Search

```bash
# Search for tracks (default)
python3 ~/.claude/skills/spotify/spotify_cli.py search "song name or query"

# Search by type
python3 ~/.claude/skills/spotify/spotify_cli.py search "query" -t artist
python3 ~/.claude/skills/spotify/spotify_cli.py search "query" -t album
python3 ~/.claude/skills/spotify/spotify_cli.py search "query" -t playlist

# Limit results
python3 ~/.claude/skills/spotify/spotify_cli.py search "query" -l 20
```

### Playlists

```bash
# List all playlists
python3 ~/.claude/skills/spotify/spotify_cli.py playlists

# Show tracks in a playlist
python3 ~/.claude/skills/spotify/spotify_cli.py playlist-tracks PLAYLIST_ID

# Create a playlist
python3 ~/.claude/skills/spotify/spotify_cli.py playlist-create "My Playlist" -d "Description" --private

# Add tracks to a playlist
python3 ~/.claude/skills/spotify/spotify_cli.py playlist-add PLAYLIST_ID spotify:track:TRACK_ID1 spotify:track:TRACK_ID2

# Remove tracks from a playlist
python3 ~/.claude/skills/spotify/spotify_cli.py playlist-remove PLAYLIST_ID spotify:track:TRACK_ID

# Rename a playlist
python3 ~/.claude/skills/spotify/spotify_cli.py playlist-rename PLAYLIST_ID "New Name"

# Delete (unfollow) a playlist
python3 ~/.claude/skills/spotify/spotify_cli.py playlist-delete PLAYLIST_ID
```

### Now Playing & Queue

```bash
# What's playing now
python3 ~/.claude/skills/spotify/spotify_cli.py now-playing

# Show the queue
python3 ~/.claude/skills/spotify/spotify_cli.py queue

# Add tracks to queue
python3 ~/.claude/skills/spotify/spotify_cli.py queue-add spotify:track:TRACK_ID
```

### Playback Controls

```bash
python3 ~/.claude/skills/spotify/spotify_cli.py play
python3 ~/.claude/skills/spotify/spotify_cli.py pause
python3 ~/.claude/skills/spotify/spotify_cli.py skip
python3 ~/.claude/skills/spotify/spotify_cli.py previous
python3 ~/.claude/skills/spotify/spotify_cli.py shuffle on    # or off
python3 ~/.claude/skills/spotify/spotify_cli.py repeat track  # or context, off
```

### Devices

```bash
# List available devices
python3 ~/.claude/skills/spotify/spotify_cli.py devices

# Transfer playback to a device
python3 ~/.claude/skills/spotify/spotify_cli.py transfer DEVICE_ID
```

### Liked Songs

```bash
python3 ~/.claude/skills/spotify/spotify_cli.py like spotify:track:TRACK_ID
python3 ~/.claude/skills/spotify/spotify_cli.py unlike spotify:track:TRACK_ID
```

## Workflow Tips

- **Search then act**: When the user asks to add a song, first `search` for it, show results, then use the `spotify:track:...` URI from the results to `playlist-add` or `queue-add`.
- **Playlist IDs**: Can be the full URI (`spotify:playlist:...`), the URL, or just the ID. Get IDs from `playlists` command.
- **Multiple tracks**: `playlist-add`, `queue-add`, `like`, `unlike` accept multiple URIs space-separated.
- **Active device required**: Playback commands (play, pause, skip, queue-add) require an active Spotify device. If commands fail with "No active device", ask the user to open Spotify on a device first, or use `devices` + `transfer`.

## Important Notes

- Queue management is limited by Spotify API — you can add to queue but cannot reorder or remove items
- Playback commands require an active Spotify device. Open Spotify on any device first if commands return "No active device"
- Token cache lives at `~/.claude/skills/spotify/.spotify_token_cache` and auto-refreshes — no need to re-auth
