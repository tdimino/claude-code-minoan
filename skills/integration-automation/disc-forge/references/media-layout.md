# Media library layout

disc-forge sources music from a local folder or from a remote host over SSH,
written as an ssh-style `host:/path`:

```
<ssh-host>:/Volumes/<Volume>/<Album Folder>/
```

`<ssh-host>` is any alias from `~/.ssh/config`. Quote the whole string: library
paths almost always contain spaces, which is why staging uses tar-over-SSH
rather than rsync (see `gotchas.md` §2).

## Machine-local layout

If `~/.claude/agent_docs/music.md` exists, it is the canonical layout for this
machine: the host alias, the volume and how to mount it, and the album table.
Read it to resolve an album name to a source path. Don't copy the album table
into this skill; it would drift.

## Duplicate formats

Album folders often hold MP3+WMA or MP3+M4A copies of the same tracks.
`stage_tracks.py --format mp3` (the default) keeps one format.
