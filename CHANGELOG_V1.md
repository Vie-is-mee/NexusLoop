# NexusLoop Demo V1 — changes from v0.2

- Added explicit Supplier A output profile and Receiver B input requirement profile.
- Added document ingestion for JSON/CSV/TXT/PDF demo files.
- Added A↔B compatibility matrix covering resource type, quantity, quality, continuity, infrastructure, legal path and economics.
- Added visible AI processing trace.
- Reworked evidence planning so multiple actions can be available at once instead of a fixed checklist.
- Added decision factors and rejected-alternative explanations.
- Added human profile editing, plan override, AI re-plan request and custom constraints.
- Preserved non-overridable hard STOP behavior.
- Added task owner/source/cost/time display.
- Added Decision Pack with matched volume, receiver coverage, conditions, risks, impact and exportable HTML report.
- Added output specifically for Receiver B.
- Added 15 automated tests.
- Reworked UI navigation into seven explicit stages from Input to Result and Audit.

## V1.1 · Optional AI API + deterministic fallback

- Added `NexusAIRuntime` with optional OpenAI Responses API integration.
- Added `.env` configuration (`OPENAI_API_KEY`, `OPENAI_MODEL`, `NEXUSLOOP_AI_MODE`).
- LLM can semantically extract facts from unstructured TXT/PDF and choose/explain the next evidence action.
- Hard gates and candidate availability remain deterministic and cannot be overridden by LLM output.
- Invalid API output, missing key, timeout or API error automatically falls back to the built-in planner.
- Added `/api/ai/status` and visible UI status badge.
- Added planner provenance in the recommendation panel.
- Added one canonical single-file A↔B input bundle under `data/sample_inputs/`.
- Added support for uploading a shared A↔B JSON bundle.
- Test suite expanded to 18 tests.
