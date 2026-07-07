#!/usr/bin/env node
/**
 * Remove LexFlow-managed workflows from n8n SQLite before re-import.
 * Prevents duplicate workflows when import:workflow runs repeatedly.
 */
const fs = require("fs");
const path = require("path");

const DB_PATH = process.env.N8N_DB_PATH || "/home/node/.n8n/database.sqlite";
const CATALOG_PATH =
  process.env.N8N_CATALOG_PATH || "/workflows/catalog.json";

const LEGACY_NAMES = new Set([
  "document-upload-notify-v1",
  "Demo: My first AI Agent in n8n",
]);

function loadManagedNames() {
  const names = new Set(LEGACY_NAMES);
  try {
    const raw = fs.readFileSync(CATALOG_PATH, "utf8");
    const catalog = JSON.parse(raw);
    for item in catalog) {
      if (item.display_name) names.add(item.display_name);
      if (item.name) names.add(item.name);
    }
  } catch (err) {
    console.warn("WARN: could not read catalog.json — using legacy names only:", err.message);
  }
  return names;
}

async function main() {
  if (!fs.existsSync(DB_PATH)) {
    console.log("==> n8n purge: no database yet — skip");
    return;
  }

  const sqlite3 = require("/usr/local/lib/node_modules/n8n/node_modules/sqlite3");
  const managed = loadManagedNames();
  const db = new sqlite3.Database(DB_PATH);

  const all = await new Promise((resolve, reject) => {
    db.all("SELECT id, name FROM workflow_entity", (err, rows) =>
      err ? reject(err) : resolve(rows || [])
    );
  });

  const toDelete = all.filter((row) => managed.has(row.name));
  if (toDelete.length === 0) {
    console.log("==> n8n purge: no managed workflows to remove");
    db.close();
    return;
  }

  const ids = toDelete.map((r) => r.id);
  const placeholders = ids.map(() => "?").join(",");

  const run = (sql, params = []) =>
    new Promise((resolve, reject) => {
      db.run(sql, params, function (err) {
        if (err) reject(err);
        else resolve(this.changes);
      });
    });

  await run(`DELETE FROM workflows_tags WHERE workflowId IN (${placeholders})`, ids);
  await run(`DELETE FROM webhook_entity WHERE workflowId IN (${placeholders})`, ids);
  await run(`DELETE FROM shared_workflow WHERE workflowId IN (${placeholders})`, ids);
  const removed = await run(
    `DELETE FROM workflow_entity WHERE id IN (${placeholders})`,
    ids
  );

  console.log(`==> n8n purge: removed ${removed} managed workflow(s)`);
  for (const row of toDelete) {
    console.log(`    - ${row.name} (${row.id})`);
  }
  db.close();
}

main().catch((err) => {
  console.error("FAIL n8n purge:", err.message);
  process.exit(1);
});
