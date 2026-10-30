'use strict';
// readLinesSync contract: the byte offsets and line numbers here are what
// Phase 3's resumable indexing will persist, so they are pinned exactly.
// Run: node --test tests/   (from the suite directory)

const assert = require('node:assert/strict');
const { describe, it, before, after } = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const LIB_DIR = process.env.TRACKER_LIB_DIR || path.resolve(__dirname, '../../../../lib');
const { readLinesSync, extractTranscript } = require(path.join(LIB_DIR, 'tracker-utils.js'));

let dir;
before(() => { dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tracker-lines-')); });
after(() => fs.rmSync(dir, { recursive: true, force: true }));

function file(name, content) {
  const p = path.join(dir, name);
  fs.writeFileSync(p, content);
  return p;
}

function read(p, opts) {
  const lines = [];
  const r = readLinesSync(p, (text, lineNo) => lines.push([lineNo, text]), opts);
  return { ...r, lines };
}

describe('readLinesSync', () => {
  it('empty file: no lines, end 0, no error', () => {
    assert.deepEqual(read(file('empty', '')), { end: 0, lines: [], error: null });
  });

  it('a lone unterminated line is left unread (end stays 0)', () => {
    const r = read(file('partial', '{"type":"user"'));
    assert.deepEqual([r.end, r.lines], [0, []]);
  });

  it('holds back the unterminated tail; end is just past the last newline', () => {
    const r = read(file('tail', 'a\nb\n{"half'));
    assert.deepEqual(r.lines, [[1, 'a'], [2, 'b']]);
    assert.equal(r.end, 4);
  });

  it('line numbers are physical: blank lines count but are not delivered', () => {
    const r = read(file('blank', 'a\n\nb\n'));
    assert.deepEqual(r.lines, [[1, 'a'], [3, 'b']]);
    assert.equal(r.end, 5);
  });

  it('multi-byte UTF-8 and U+2028 survive every chunk size', () => {
    const content = 'αβγ δ\n𓂀 ankh\n€uro\n';
    const p = file('utf8', content);
    const expected = [[1, 'αβγ δ'], [2, '𓂀 ankh'], [3, '€uro']];
    for (const chunkBytes of [1, 2, 3, 5, 7, 64]) {
      const r = read(p, { chunkBytes });
      assert.deepEqual(r.lines, expected, `chunkBytes=${chunkBytes}`);
      assert.equal(r.end, Buffer.byteLength(content), `chunkBytes=${chunkBytes}`);
    }
  });

  it('a line longer than the chunk is joined whole', () => {
    const long = 'x'.repeat(1000);
    const r = read(file('long', long + '\nshort\n'), { chunkBytes: 16 });
    assert.deepEqual(r.lines, [[1, long], [2, 'short']]);
  });

  it('resumes from a byte offset and line number', () => {
    const p = file('resume', 'one\ntwo\nthree\n');
    const r = read(p, { start: 4, startLine: 1 });
    assert.deepEqual(r.lines, [[2, 'two'], [3, 'three']]);
    assert.equal(r.end, 14);
  });

  it('skips an oversized line but still counts it and reads the next', () => {
    const r = read(file('oversized', 'ok\n' + 'y'.repeat(50) + '\nnext\n'), { chunkBytes: 8, maxLineBytes: 20 });
    assert.deepEqual(r.lines, [[1, 'ok'], [3, 'next']]);
    assert.equal(r.end, 3 + 51 + 5);
  });

  it('reports a missing file as an error, not as an empty read', () => {
    const r = read(path.join(dir, 'nope.jsonl'));
    assert.equal(r.error && r.error.code, 'ENOENT');
  });
});

describe('extractTranscript is chunk-size invariant', () => {
  it('rich fixture: identical meta at 7-byte and default chunks', () => {
    const fx = path.join(__dirname, 'fixtures', 'rich.jsonl');
    const small = extractTranscript(fx, { chunkBytes: 7 });
    const big = extractTranscript(fx);
    assert.deepEqual(small.meta, big.meta);
    assert.deepEqual(small.messages, big.messages);
    assert.deepEqual(small.titleEvents, big.titleEvents);
  });
});
