// oe-warranty — claim validator (reference source, NOT shipped)
// The production bundle is minified from this logic.

const PREFIX = "cyber_quest{";
const KEY = Buffer.from("<key-hex>", "hex");   // per-build secret
const TARGET = Buffer.from("<target-b64>", "base64");

function mask(i) { return ((i * 0x1f + 0x03) & 0xff); }

function check(candidate) {
  if (typeof candidate !== "string") return false;
  if (!candidate.startsWith(PREFIX) || !candidate.endsWith("}")) return false;
  const body = candidate.slice(PREFIX.length, -1);
  if (body.length !== TARGET.length) return false;
  for (let i = 0; i < body.length; i++) {
    const g = body.charCodeAt(i) ^ KEY[i % KEY.length] ^ mask(i);
    if (g !== TARGET[i]) return false;
  }
  return true;
}

const input = process.argv[2] || "";
if (!input) { console.log("usage: node bundle.js <receipt-key>"); process.exit(1); }
if (check(input)) { console.log("warranty honored. receipt: " + input); }
else { console.log("claim denied."); process.exit(2); }
