/**
 * Postinstall fix for libsodium ESM module resolution.
 *
 * The libsodium-wrappers ESM entry point does `import e from "./libsodium.mjs"`
 * but the npm package doesn't ship that file. We create a symlink from
 * libsodium-wrappers/dist/modules-esm/libsodium.mjs ->
 * libsodium/dist/modules-esm/libsodium.mjs
 *
 * Additionally, the libsodium ESM module uses `(this)` which is `undefined` in
 * strict ESM context. The compiled 0.7.16+ version already includes
 * `export default Module;` so only the symlink is needed.
 */
import { existsSync, symlinkSync, unlinkSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const target = resolve(
  __dirname,
  "node_modules/libsodium-wrappers/dist/modules-esm/libsodium.mjs"
);

const source = "../../../libsodium/dist/modules-esm/libsodium.mjs";

if (!existsSync(target)) {
  try {
    symlinkSync(source, target);
    console.log("✓ libsodium ESM symlink created");
  } catch (e) {
    console.warn("⚠ Could not create libsodium ESM symlink:", e.message);
  }
} else {
  console.log("✓ libsodium ESM symlink already exists");
}
