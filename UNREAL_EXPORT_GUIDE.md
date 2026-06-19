# Unreal Engine Export Guide

StoryForge exports its Game Tools outputs into three formats natively: JSON, YAML, and CSV.

## CSV DataTables

Unreal Engine heavily utilizes DataTables for static narrative data. DataTables require flat, 1D CSV files where each row corresponds to a struct. 

### Flattening Arrays and Nested Objects
Because StoryForge objects (like `Campaigns`) inherently contain lists of IDs or sub-objects, the StoryForge `UnrealExportLayer` automatically flattens these fields.
- **Lists of Strings**: Converted to comma-separated strings.
- **Nested Objects/Lists of Dicts**: Converted to escaped JSON strings.

### Export Directory
All generated assets are exported to:
`exports/unreal/game_narrative/`

### Relational Schema
StoryForge intentionally prevents bloat by isolating complex objects. For example, exporting an Intelligent NPC generates five files:
1. `npcs.csv`
2. `npc_memory.csv`
3. `npc_relationships.csv`
4. `npc_goals.csv`
5. `npc_reactions.csv`

In Unreal Engine, create a primary struct for `NPC`, and use the `npc_id` column as a Row Name or foreign key reference to query the Memory and Relationship DataTables dynamically via Blueprint.
