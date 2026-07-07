#!/bin/sh
# Import LexFlow workflows — purge duplicates first, then import once.
set -e

DB="/home/node/.n8n/database.sqlite"
PURGE="/purge-managed-workflows.js"

if [ -f "$DB" ] && [ -f "$PURGE" ]; then
  echo "==> n8n: purging managed workflows (prevent duplicates)"
  node "$PURGE" || true
fi

echo "==> n8n: importing LexFlow workflows from /workflows"

find /workflows -mindepth 1 -type d ! -name '.*' | sort | while read -r dir; do
  if ls "$dir"/*.json >/dev/null 2>&1; then
    echo "    import $dir"
    n8n import:workflow --separate --input="$dir" || true
  fi
done

echo "==> n8n: activating catalog workflows"
if [ -f /workflows/catalog.json ]; then
  node -e "
    const fs = require('fs');
    const catalog = JSON.parse(fs.readFileSync('/workflows/catalog.json','utf8'));
    const { execSync } = require('child_process');
    const list = execSync('n8n list:workflow 2>/dev/null', { encoding: 'utf8' });
    const rows = list.trim().split('\n').filter(Boolean);
    const byName = {};
    for (const line of rows) {
      const [id, ...rest] = line.split('|');
      const name = rest.join('|').trim();
      byName[name] = id.trim();
    }
    for (const item of catalog) {
      if (item.trigger === 'manual') continue;
      const id = byName[item.display_name] || byName[item.name];
      if (id) {
        console.log('    activate ' + (item.display_name || item.name));
        try { execSync('n8n update:workflow --id=' + id + ' --active=true', { stdio: 'inherit' }); } catch (e) {}
      }
    }
  " || true
fi

echo "==> n8n: starting server on :5678 (host maps to localhost:5679)"
exec n8n start
