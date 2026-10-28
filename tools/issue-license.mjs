// tools/issue-license.mjs   usage: node issue-license.mjs keygen | node issue-license.mjs sign "<org>" <licId> <days>
import { generateKeyPairSync, createPrivateKey, sign } from "node:crypto";
import { writeFileSync, readFileSync } from "node:fs";
const b64u = (b) => Buffer.from(b).toString("base64url");
const [cmd, org, lic, days] = process.argv.slice(2);
if (cmd === "keygen") {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  writeFileSync("../shared/license/public-key.pem", publicKey.export({ type: "spki", format: "pem" }));
  writeFileSync(process.env.USERPROFILE + "/.antigravity-private.pem",
                privateKey.export({ type: "pkcs8", format: "pem" }));   // NEVER in the repo
} else if (cmd === "sign") {
  const now = Math.floor(Date.now() / 1000);
  const payload = { v: 1, kid: "demo-2026", lic, org, tier: "demo", iat: now, nbf: now,
                    exp: now + Number(days) * 86400, features: ["scan", "pdf"] };
  const head = "AG1." + b64u(JSON.stringify(payload));
  const key = createPrivateKey(readFileSync(process.env.USERPROFILE + "/.antigravity-private.pem"));
  console.log(head + "." + b64u(sign(null, Buffer.from(head, "ascii"), key)));
}
