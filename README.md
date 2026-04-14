# Skills

A collection of Claude Code skills for managing everyday tools without leaving your terminal.

| Skill | Description |
|-------|-------------|
| [spotify](./spotify/) | Full Spotify control — search songs, manage playlists, control playback queue, see what's playing |
| [gmail](./gmail/) | Send, draft, read, reply, forward, and triage Gmail emails |
| [gws-google-docs](./gws-google-docs/) | Read and edit Google Docs — insert, format, manage headings, tables, and images |

---

## Installing skills

Skills are managed with [Skills Manager](https://github.com/talktoajayprakash/skillsmanager) (`sm`), a CLI for discovering, installing, and sharing agent skills across devices.

### 1. Install Skills Manager

```bash
npm install -g skillsmanager
```

### 2. Register this collection

```bash
sm collection create skills --backend github --repo talktoajayprakash/skills
```

### 3. Install a skill

```bash
# Install for Claude Code
sm install spotify --agent claude --collection skills
sm install gmail --agent claude --collection skills
sm install gws-google-docs --agent claude --collection skills
```

Once installed, the skill is available globally across all your projects at `~/.claude/skills/<name>/`.

---

## Managing skills with Skills Manager

### List all available skills

```bash
sm list
```

### Search for skills

```bash
sm search spotify
```

### Install to a specific project only

```bash
sm install spotify --agent claude --collection skills --scope project
```

### Update a skill after local edits

If you modify a skill locally and want to push the change back to this repo:

```bash
sm update ~/.claude/skills/spotify
```

### Uninstall a skill

```bash
sm uninstall spotify --agent claude
```

### Check what's registered

```bash
sm registry list
```

---

## How skills work

Each skill is a directory containing a `SKILL.md` file. The SKILL.md bundles together:
- **Natural language instructions** — when to activate, what to do, workflow tips
- **Scripts** — CLI tools or Python scripts the agent can run directly
- **Context** — command reference, gotchas, patterns

The scripts don't need to be perfect. If a script is outdated or broken, the agent can fix it and commit the change back. Skills evolve as they get used.

---

## Prerequisites by skill

**spotify** — requires a Spotify Developer app:
1. Create an app at [developer.spotify.com](https://developer.spotify.com/dashboard)
2. Set the redirect URI to `http://127.0.0.1:8888/callback`
3. Copy `.env.example` to `.env` in the skill directory and fill in your credentials
4. Install the Python dependency: `pip install spotipy`
5. Run `python3 spotify_cli.py auth` once to authenticate

**gmail / gws-google-docs** — requires the `gws` CLI:
```bash
brew install talktoajayprakash/tap/gws
gws auth login
```

---

## License

MIT
