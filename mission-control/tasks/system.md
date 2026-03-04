# Mission Control - Task Management System

## Overview
A Kanban-style task management system for Core Growth AI operations.

## Boards
- `octavious-assist/` - Octavious Labs / Assist sales & marketing campaign

---

## Task Structure
```json
{
  "id": "unique-id",
  "title": "Task title",
  "description": "Task description",
  "status": "todo|in_progress|done",
  "priority": "high|medium|low",
  "subAgent": "email|linkedin|ads|general",
  "dueDate": "2026-03-15",
  "createdAt": "2026-03-02",
  "updatedAt": "2026-03-02"
}
```

---

## Sub-Agents / Lanes
| Lane | Purpose | Color |
|------|---------|-------|
| 📧 Email | Email sequences, outreach | Blue |
| 🔗 LinkedIn | Profile research, connection requests | Blue |
| 📣 Ads | Ad copy, creative, campaigns | Purple |
| 🎯 General | Research, strategy, misc | Gray |

---

*System v0.1 - Last updated: 2026-03-02*