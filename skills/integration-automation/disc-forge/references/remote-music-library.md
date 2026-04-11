# Pulling music from a remote machine

If the music library lives on another machine (a NAS, a Mac Mini acting as a media server, a Linux box over Tailscale), `stage_tracks.py` will reach it over SSH when the `--source` argument takes the form:

```
<host>:<absolute-path>
```

Where `<host>` is any `~/.ssh/config` alias or a direct hostname that SSH can resolve (LAN mDNS, Tailscale, `/etc/hosts`, etc.).

## Why tar-over-SSH, not rsync

macOS ships `openrsync 2.6.9` as `/usr/bin/rsync`. It splits remote paths on spaces — see `gotchas.md` #2. Album folders almost always contain spaces, so `stage_tracks.py` uses **tar-over-SSH** instead:

```bash
ssh <host> 'cd "<remote-path>" && tar cf - *.mp3' | tar xf - -C <local-staging>/
```

The remote path only has to survive one shell hop (the single-quoted ssh command), and tar archives with flat basenames. `stage_tracks.py` also runs the remote path through `shlex.quote` to defend against pathological album names that contain quote characters.

## SSH config cheatsheet

A minimal `~/.ssh/config` entry for a music server:

```
Host music-server
    HostName music.local
    User you
    IdentityFile ~/.ssh/id_ed25519
```

Then:

```bash
python3 ~/.claude/skills/disc-forge/scripts/burn_audio_cd.py \
  --source "music-server:/Volumes/Music/BSG Season 1 - OST/" \
  --name BSG-S1
```

## Tailscale note

If the remote host is reachable via Tailscale (and only via Tailscale — not LAN), SMB will NOT work because macOS File Sharing doesn't bind to the Tailscale tun interface. Use SSH. `stage_tracks.py` is already set up for this.
