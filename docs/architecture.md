# StoryForge AI Architecture

StoryForge AI is a deterministically driven offline intelligence system designed to act as an advanced semantic backend for story generation and tracking.

## Core Design Principles
1. **100% Offline Logic**: The system relies on string parsing, list sorting, Breadth-First-Search (BFS) traversals, and token arithmetic rather than local LLMs to establish logic chains securely.
2. **Deterministic Outputs**: Given the same text or ruleset, outputs do not vary or hallucinate.
3. **Data Independence**: Complex aggregations (like Multi-Story Universes) do not permanently rewrite local Story storage blocks.

## The 10 AI Layers

1. **Memory Engine**: Generates a local dictionary mapping `characters`, `events`, `locations`.
2. **Relationship Engine**: Creates semantic link schemas `(entity_A, entity_B, relationship_type)`.
3. **Character Engine**: Appends array arrays (`traits`, `known_facts`) to characters recursively.
4. **Analysis Engine**: Inspects story pacing ratios, extracting strengths/weaknesses algorithmically.
5. **Consistency Engine**: Validates memory schemas against logic rules, stamping flag warnings dynamically.
6. **Preference Engine**: Learns user writing patterns silently appending arrays to `user_profile.json`.
7. **Training Mode**: Evaluates DOCX, PDF, and TXT structures globally modifying generic `training_profile.json` fingerprint weights.
8. **Universe Engine**: Clusters linked stories sharing character structures independently in `universes/`.
9. **Graph Engine**: Builds breadth-first mathematical graphs calculating nodal adjacency to discover cluster overlaps.
10. **Context Injection**: Trims memory queries sequentially prioritizing high-impact constraints strictly within an 8000 char threshold.
