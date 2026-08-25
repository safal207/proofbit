'use strict';
const fs = require('fs');
const MAGIC = 0x50424637;
const KNOWN_MASK = 0x3f;
const CURRENT_VERSION = 5;
const CURRENT_MASK = 0x3f;
const CURRENT_DIGEST = 0xc43cd04df228379fn;
const STATEMENT = 0xfedcba9876543210n;
const AUTHORITY = 0xa17e0007;
const EPOCH = 7;
const TOKEN_BYTES = 56;

function parseArgs(argv) {
  const out = {mode: null, policyHex: null, input: null};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--mode') out.mode = argv[++i];
    else if (argv[i] === '--policy-hex') out.policyHex = argv[++i];
    else out.input = argv[i];
  }
  return out;
}
function parsePolicy(hex) {
  const b = Buffer.from(hex || '', 'hex');
  if (b.length !== 16) throw new Error('policy length');
  const version = b.readUInt16BE(0);
  const reserved = b.readUInt16BE(2);
  const mask = b.readUInt32BE(4);
  const digest = b.readBigUInt64BE(8);
  if (reserved !== 0) throw new Error('policy reserved');
  return {version, mask, digest};
}
function validate(b, mode, policyHex) {
  if (b.length !== TOKEN_BYTES) return false;
  const magic = b.readUInt32BE(0);
  const version = b.readUInt16BE(4);
  const flags = b.readUInt16BE(6);
  const mask = b.readUInt32BE(8);
  const digest = b.readBigUInt64BE(12);
  const statement = b.readBigUInt64BE(20);
  const authority = b.readUInt32BE(28);
  const epoch = b.readUInt32BE(32);
  const replay = b.readBigUInt64BE(36);
  const provenance = b.readBigUInt64BE(44);
  const outcome = b.readUInt8(52);
  let policy;
  if (mode === 'manual') policy = {version: CURRENT_VERSION, mask: CURRENT_MASK, digest: CURRENT_DIGEST};
  else {
    try { policy = parsePolicy(policyHex); } catch (_) { return false; }
  }
  if (magic !== MAGIC || flags !== 0) return false;
  if (b[53] !== 0 || b[54] !== 0 || b[55] !== 0) return false;
  if (version !== policy.version || mask !== policy.mask || (mask & ~KNOWN_MASK) !== 0) return false;
  if (digest !== policy.digest) return false;
  if (statement !== STATEMENT || authority !== AUTHORITY || epoch !== EPOCH) return false;
  if ((mask & 0x08) && replay === 0n) return false;
  if ((mask & 0x10) && provenance === 0n) return false;
  if ((mask & 0x20) && outcome !== 1) return false;
  return true;
}
const args = parseArgs(process.argv);
if (!args.mode || !args.input) process.exit(2);
const lines = fs.readFileSync(args.input, 'utf8').trim().split(/\n/).filter(Boolean);
const out = [];
for (const line of lines) {
  const [name, expected, rawHex] = line.split('\t');
  out.push(`${name}\t${validate(Buffer.from(rawHex, 'hex'), args.mode, args.policyHex) ? 1 : 0}`);
}
process.stdout.write(out.join('\n') + (out.length ? '\n' : ''));
