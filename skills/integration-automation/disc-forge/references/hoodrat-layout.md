# Hoodrat HDD layout

The canonical source of truth for the music library layout is **`~/.claude/agent_docs/music.md`**. That file has:

- Complete album table mapped to directory paths under `/Volumes/Hoodrat HDD/Musica/`
- Film and TV soundtracks (Star Wars, LotR, Blade Runner, BSG, Dune, etc.)
- Rock & alternative (Led Zeppelin, Pink Floyd, Jimi Hendrix, The Doors, etc.)
- Indie / post-rock, classical, game soundtracks, comedy, musicals
- Separate section for `/Volumes/Hoodrat HDD/iPhone Music/` (Philip Glass, mantras, etc.)
- "Accessing Hoodrat HDD from the Laptop" section with tar-over-SSH pattern (added during disc-forge development)

Don't duplicate the album table here — it would drift. Read `music.md` when you need to find a specific album path.

## Quick cheatsheet

- **Root**: `/Volumes/Hoodrat HDD/Musica/` (on the Mac Mini, not the laptop)
- **Mount path on Mac Mini**: `/Volumes/Hoodrat HDD` (if unmounted, run `ssh mac-mini-ts 'diskutil mount disk4s1'`)
- **SSH host alias**: `mac-mini-ts` (Tailscale; mDNS `mac-mini` is unreliable)
- **Transport for staging**: tar-over-SSH (not rsync — Apple's bundled openrsync breaks on spaces)

## Canonical source string for disc-forge

When Tom says "burn the X soundtrack to a CD," the source string takes this form:

```
mac-mini-ts:/Volumes/Hoodrat HDD/Musica/<ALBUM FOLDER>/
```

The album folder name can be looked up in `music.md`. Examples:

- `BSG Mini Series - OST`
- `BSG.S1 - OST`
- `Blade Runner - OST`
- `Star Wars - OSTs/Star Wars Episode VI Return of the Jedi`
- `Led Zeppelin - Remasters (2001) (2 CD)`
- `Dark Side Of The Moon`
- `Ludwig Van Beethoven (MP3@320Kbps)`

Album folders frequently have MP3+WMA or MP3+M4A duplicates. `stage_tracks.py --format mp3` (the default) filters to one format automatically.
