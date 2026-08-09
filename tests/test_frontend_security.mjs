import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { transformSync } from "esbuild";

async function importTypeScript(relativePath) {
  const filePath = path.resolve(new URL(`../${relativePath}`, import.meta.url).pathname);
  const source = fs.readFileSync(filePath, "utf8");
  const output = transformSync(source, { format: "esm", loader: "ts", target: "es2022" }).code;
  return import(`data:text/javascript,${encodeURIComponent(output)}`);
}

const { safeAuthRedirect } = await importTypeScript("sites/arin/src/security.ts");
const documentsSource = fs.readFileSync(
  path.resolve(new URL("../apps/web/src/documents.tsx", import.meta.url).pathname),
  "utf8",
);

assert.equal(safeAuthRedirect("/studio"), "/studio");
assert.equal(safeAuthRedirect("//attacker.example"), "/studio");
assert.equal(safeAuthRedirect("javascript:alert(1)"), "/studio");
assert.equal(documentsSource.includes("src={preview}"), false);
assert.equal(documentsSource.includes("URL.createObjectURL"), false);

console.log("frontend security regression tests passed");
