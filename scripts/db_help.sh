#!/bin/bash

# Database Maintenance Quick Reference
# Run this script to see all available database maintenance commands

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Issue Tracker - Database Maintenance Tools            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "📦 BACKUP & RESTORE"
echo "  python3 scripts/backup_db.py backup    - Create new backup"
echo "  python3 scripts/backup_db.py restore   - Restore from backup"
echo "  python3 scripts/backup_db.py list      - List all backups"
echo ""

echo "🔍 INSPECTION & MONITORING"
echo "  python3 scripts/inspect_db.py stats    - Database statistics"
echo "  python3 scripts/inspect_db.py health   - Health check"
echo "  python3 scripts/inspect_db.py users    - List all users"
echo "  python3 scripts/inspect_db.py labels   - List all labels"
echo "  python3 scripts/inspect_db.py export   - Export data summary"
echo ""

echo "🧹 CLEANUP & MAINTENANCE"
echo "  python3 scripts/cleanup_db.py summary        - Maintenance summary"
echo "  python3 scripts/cleanup_db.py old-issues     - Clean old resolved issues"
echo "  python3 scripts/cleanup_db.py unused-labels  - Remove unused labels"
echo "  python3 scripts/cleanup_db.py vacuum         - Optimize database"
echo "  python3 scripts/cleanup_db.py reset          - ⚠️  Reset database (DANGER)"
echo ""

echo "🔧 INITIALIZATION & MIGRATION"
echo "  python3 scripts/init_db.py      - Initialize/reset database"
echo "  python3 scripts/migrate.py      - Run migrations"
echo ""

echo "📚 DOCUMENTATION"
echo "  cat DATABASE_MAINTENANCE.md     - Full maintenance guide"
echo "  cat README.md                   - Project documentation"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo ""
