#!/usr/bin/env python3
"""Spotify CLI — search, manage playlists, and control playback queue."""

import argparse
import json
import os
import sys

import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPE = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-library-read "
    "user-library-modify"
)

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".spotify_token_cache")
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def load_env():
    """Load .env file into environment if it exists."""
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def get_spotify():
    """Return an authenticated Spotify client."""
    load_env()
    auth_manager = SpotifyOAuth(
        scope=SCOPE,
        cache_path=CACHE_PATH,
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


# ── Auth ────────────────────────────────────────────────────────────────────

def cmd_auth(_args):
    """Authenticate with Spotify (opens browser for OAuth)."""
    sp = get_spotify()
    user = sp.current_user()
    print(f"Authenticated as: {user['display_name']} ({user['id']})")
    print(f"Email: {user.get('email', 'N/A')}")
    print(f"Followers: {user['followers']['total']}")
    print(f"Account type: {user.get('product', 'N/A')}")


# ── Search ──────────────────────────────────────────────────────────────────

def cmd_search(args):
    """Search for tracks, artists, albums, or playlists."""
    sp = get_spotify()
    search_type = args.type or "track"
    results = sp.search(q=args.query, type=search_type, limit=args.limit)

    key = search_type + "s"
    items = results[key]["items"]

    if not items:
        print(f"No {search_type}s found for '{args.query}'")
        return

    if search_type == "track":
        print(f"{'#':<4} {'Track':<40} {'Artist':<30} {'Album':<30} {'URI'}")
        print("-" * 140)
        for i, t in enumerate(items, 1):
            artists = ", ".join(a["name"] for a in t["artists"])
            print(f"{i:<4} {t['name'][:39]:<40} {artists[:29]:<30} {t['album']['name'][:29]:<30} {t['uri']}")
    elif search_type == "artist":
        print(f"{'#':<4} {'Artist':<40} {'Genres':<50} {'URI'}")
        print("-" * 110)
        for i, a in enumerate(items, 1):
            genres = ", ".join(a.get("genres", [])[:3])
            print(f"{i:<4} {a['name'][:39]:<40} {genres[:49]:<50} {a['uri']}")
    elif search_type == "album":
        print(f"{'#':<4} {'Album':<40} {'Artist':<30} {'Year':<6} {'URI'}")
        print("-" * 120)
        for i, a in enumerate(items, 1):
            artists = ", ".join(ar["name"] for ar in a["artists"])
            year = a.get("release_date", "")[:4]
            print(f"{i:<4} {a['name'][:39]:<40} {artists[:29]:<30} {year:<6} {a['uri']}")
    elif search_type == "playlist":
        print(f"{'#':<4} {'Playlist':<40} {'Owner':<25} {'Tracks':<8} {'URI'}")
        print("-" * 120)
        for i, p in enumerate(items, 1):
            print(f"{i:<4} {p['name'][:39]:<40} {p['owner']['display_name'][:24]:<25} {p['tracks']['total']:<8} {p['uri']}")


# ── Playlists ───────────────────────────────────────────────────────────────

def cmd_playlists(_args):
    """List the current user's playlists."""
    sp = get_spotify()
    results = sp.current_user_playlists(limit=50)
    playlists = [p for p in results["items"] if p is not None]

    # Paginate through all playlists
    while results["next"]:
        results = sp.next(results)
        playlists.extend(p for p in results["items"] if p is not None)

    print(f"{'#':<4} {'Playlist':<45} {'Public':<8} {'URI'}")
    print("-" * 130)
    for i, p in enumerate(playlists, 1):
        public = "Yes" if p.get("public") else "No"
        name = p.get("name") or "(untitled)"
        print(f"{i:<4} {name[:44]:<45} {public:<8} {p['uri']}")
    print(f"\nTotal: {len(playlists)} playlists")


def cmd_playlist_tracks(args):
    """Show tracks in a playlist."""
    sp = get_spotify()
    playlist_id = args.playlist_id

    # Get playlist info
    playlist = sp.playlist(playlist_id)
    print(f"Playlist: {playlist['name']} (by {playlist['owner']['display_name']})")

    results = sp.playlist_items(playlist_id, limit=100)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])

    print(f"Total tracks: {len(tracks)}\n")
    print(f"{'#':<5} {'Track':<40} {'Artist':<30} {'Album':<30} {'Duration':<8} {'URI'}")
    print("-" * 150)
    for i, entry in enumerate(tracks, 1):
        # API may use 'track' or 'item' key
        t = entry.get("track") or entry.get("item")
        if not t:
            continue
        artists = ", ".join(a["name"] for a in t.get("artists", []))
        dur_ms = t.get("duration_ms", 0)
        mins, secs = divmod(dur_ms // 1000, 60)
        dur = f"{mins}:{secs:02d}"
        album = t.get("album", {}).get("name", "") if isinstance(t.get("album"), dict) else ""
        print(f"{i:<5} {t['name'][:39]:<40} {artists[:29]:<30} {album[:29]:<30} {dur:<8} {t['uri']}")


def cmd_playlist_create(args):
    """Create a new playlist."""
    sp = get_spotify()
    user_id = sp.current_user()["id"]
    public = not args.private
    playlist = sp.user_playlist_create(
        user_id,
        args.name,
        public=public,
        description=args.description or "",
    )
    print(f"Created playlist: {playlist['name']}")
    print(f"URI: {playlist['uri']}")
    print(f"URL: {playlist['external_urls']['spotify']}")


def cmd_playlist_add(args):
    """Add tracks to a playlist."""
    sp = get_spotify()
    uris = args.track_uris
    sp.playlist_add_items(args.playlist_id, uris)
    print(f"Added {len(uris)} track(s) to playlist.")


def cmd_playlist_remove(args):
    """Remove tracks from a playlist."""
    sp = get_spotify()
    uris = args.track_uris
    sp.playlist_remove_all_occurrences_of_items(args.playlist_id, uris)
    print(f"Removed {len(uris)} track(s) from playlist.")


def cmd_playlist_delete(args):
    """Unfollow (delete) a playlist."""
    sp = get_spotify()
    sp.current_user_unfollow_playlist(args.playlist_id)
    print(f"Unfollowed/deleted playlist {args.playlist_id}")


def cmd_playlist_rename(args):
    """Rename a playlist."""
    sp = get_spotify()
    sp.playlist_change_details(args.playlist_id, name=args.name)
    print(f"Renamed playlist to: {args.name}")


# ── Queue & Playback ───────────────────────────────────────────────────────

def cmd_now_playing(_args):
    """Show currently playing track."""
    sp = get_spotify()
    current = sp.current_playback()
    if not current or not current.get("item"):
        print("Nothing is currently playing.")
        return

    t = current["item"]
    artists = ", ".join(a["name"] for a in t["artists"])
    progress_s = current["progress_ms"] // 1000
    duration_s = t["duration_ms"] // 1000
    p_min, p_sec = divmod(progress_s, 60)
    d_min, d_sec = divmod(duration_s, 60)

    print(f"Track:    {t['name']}")
    print(f"Artist:   {artists}")
    print(f"Album:    {t['album']['name']}")
    print(f"Progress: {p_min}:{p_sec:02d} / {d_min}:{d_sec:02d}")
    print(f"Device:   {current['device']['name']} ({current['device']['type']})")
    print(f"Shuffle:  {'On' if current['shuffle_state'] else 'Off'}")
    print(f"Repeat:   {current['repeat_state']}")
    print(f"URI:      {t['uri']}")


def cmd_queue(_args):
    """Show the current playback queue."""
    sp = get_spotify()
    q = sp.queue()

    if q.get("currently_playing"):
        t = q["currently_playing"]
        artists = ", ".join(a["name"] for a in t["artists"])
        print(f"Now playing: {t['name']} — {artists}\n")

    items = q.get("queue", [])
    if not items:
        print("Queue is empty.")
        return

    print(f"{'#':<4} {'Track':<45} {'Artist':<35} {'URI'}")
    print("-" * 130)
    for i, t in enumerate(items, 1):
        artists = ", ".join(a["name"] for a in t["artists"])
        print(f"{i:<4} {t['name'][:44]:<45} {artists[:34]:<35} {t['uri']}")


def cmd_queue_add(args):
    """Add a track to the playback queue."""
    sp = get_spotify()
    for uri in args.track_uris:
        sp.add_to_queue(uri)
    print(f"Added {len(args.track_uris)} track(s) to queue.")


def cmd_skip(_args):
    """Skip to the next track."""
    sp = get_spotify()
    sp.next_track()
    print("Skipped to next track.")


def cmd_previous(_args):
    """Go back to the previous track."""
    sp = get_spotify()
    sp.previous_track()
    print("Went to previous track.")


def cmd_pause(_args):
    """Pause playback."""
    sp = get_spotify()
    sp.pause_playback()
    print("Playback paused.")


def cmd_play(_args):
    """Resume playback."""
    sp = get_spotify()
    sp.start_playback()
    print("Playback resumed.")


def cmd_shuffle(args):
    """Toggle shuffle on/off."""
    sp = get_spotify()
    state = args.state.lower() in ("on", "true", "1", "yes")
    sp.shuffle(state)
    print(f"Shuffle {'on' if state else 'off'}.")


def cmd_repeat(args):
    """Set repeat mode (off, track, context)."""
    sp = get_spotify()
    sp.repeat(args.mode)
    print(f"Repeat set to: {args.mode}")


def cmd_devices(_args):
    """List available playback devices."""
    sp = get_spotify()
    devices = sp.devices()["devices"]
    if not devices:
        print("No active devices found.")
        return
    print(f"{'#':<4} {'Device':<35} {'Type':<15} {'Active':<8} {'ID'}")
    print("-" * 100)
    for i, d in enumerate(devices, 1):
        active = ">>>" if d["is_active"] else ""
        print(f"{i:<4} {d['name'][:34]:<35} {d['type'][:14]:<15} {active:<8} {d['id']}")


def cmd_transfer(args):
    """Transfer playback to a device."""
    sp = get_spotify()
    sp.transfer_playback(args.device_id)
    print(f"Transferred playback to device {args.device_id}")


# ── Liked Songs ─────────────────────────────────────────────────────────────

def cmd_like(args):
    """Save tracks to liked songs."""
    sp = get_spotify()
    sp.current_user_saved_tracks_add(args.track_uris)
    print(f"Liked {len(args.track_uris)} track(s).")


def cmd_unlike(args):
    """Remove tracks from liked songs."""
    sp = get_spotify()
    sp.current_user_saved_tracks_delete(args.track_uris)
    print(f"Unliked {len(args.track_uris)} track(s).")


# ── CLI Parser ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Spotify CLI")
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # auth
    sub.add_parser("auth", help="Authenticate with Spotify")

    # search
    p = sub.add_parser("search", help="Search Spotify")
    p.add_argument("query", help="Search query")
    p.add_argument("-t", "--type", choices=["track", "artist", "album", "playlist"], default="track")
    p.add_argument("-l", "--limit", type=int, default=10)

    # playlists
    sub.add_parser("playlists", help="List your playlists")

    # playlist-tracks
    p = sub.add_parser("playlist-tracks", help="Show tracks in a playlist")
    p.add_argument("playlist_id", help="Playlist ID or URI")

    # playlist-create
    p = sub.add_parser("playlist-create", help="Create a new playlist")
    p.add_argument("name", help="Playlist name")
    p.add_argument("-d", "--description", help="Playlist description")
    p.add_argument("--private", action="store_true", help="Make playlist private")

    # playlist-add
    p = sub.add_parser("playlist-add", help="Add tracks to a playlist")
    p.add_argument("playlist_id", help="Playlist ID or URI")
    p.add_argument("track_uris", nargs="+", help="Track URIs to add")

    # playlist-remove
    p = sub.add_parser("playlist-remove", help="Remove tracks from a playlist")
    p.add_argument("playlist_id", help="Playlist ID or URI")
    p.add_argument("track_uris", nargs="+", help="Track URIs to remove")

    # playlist-delete
    p = sub.add_parser("playlist-delete", help="Unfollow/delete a playlist")
    p.add_argument("playlist_id", help="Playlist ID or URI")

    # playlist-rename
    p = sub.add_parser("playlist-rename", help="Rename a playlist")
    p.add_argument("playlist_id", help="Playlist ID or URI")
    p.add_argument("name", help="New name")

    # now-playing
    sub.add_parser("now-playing", help="Show currently playing track")

    # queue
    sub.add_parser("queue", help="Show playback queue")

    # queue-add
    p = sub.add_parser("queue-add", help="Add tracks to queue")
    p.add_argument("track_uris", nargs="+", help="Track URIs to add")

    # playback controls
    sub.add_parser("skip", help="Skip to next track")
    sub.add_parser("previous", help="Previous track")
    sub.add_parser("pause", help="Pause playback")
    sub.add_parser("play", help="Resume playback")

    # shuffle
    p = sub.add_parser("shuffle", help="Toggle shuffle")
    p.add_argument("state", choices=["on", "off"])

    # repeat
    p = sub.add_parser("repeat", help="Set repeat mode")
    p.add_argument("mode", choices=["off", "track", "context"])

    # devices
    sub.add_parser("devices", help="List playback devices")

    # transfer
    p = sub.add_parser("transfer", help="Transfer playback to device")
    p.add_argument("device_id", help="Device ID")

    # like/unlike
    p = sub.add_parser("like", help="Save tracks to liked songs")
    p.add_argument("track_uris", nargs="+", help="Track URIs")
    p = sub.add_parser("unlike", help="Remove from liked songs")
    p.add_argument("track_uris", nargs="+", help="Track URIs")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "auth": cmd_auth,
        "search": cmd_search,
        "playlists": cmd_playlists,
        "playlist-tracks": cmd_playlist_tracks,
        "playlist-create": cmd_playlist_create,
        "playlist-add": cmd_playlist_add,
        "playlist-remove": cmd_playlist_remove,
        "playlist-delete": cmd_playlist_delete,
        "playlist-rename": cmd_playlist_rename,
        "now-playing": cmd_now_playing,
        "queue": cmd_queue,
        "queue-add": cmd_queue_add,
        "skip": cmd_skip,
        "previous": cmd_previous,
        "pause": cmd_pause,
        "play": cmd_play,
        "shuffle": cmd_shuffle,
        "repeat": cmd_repeat,
        "devices": cmd_devices,
        "transfer": cmd_transfer,
        "like": cmd_like,
        "unlike": cmd_unlike,
    }

    try:
        commands[args.command](args)
    except spotipy.SpotifyException as e:
        print(f"Spotify API error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
