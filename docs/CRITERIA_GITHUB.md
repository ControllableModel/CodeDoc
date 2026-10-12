# GitHub-style documentation criteria

Companion to [`CRITERIA_ISO.md`](CRITERIA_ISO.md). This file collects the GitHub-oriented
criteria used as the second instantiation of the criterion set `Q`, states their provenance,
and marks what is missing.

---

## 1. Generation-time guidelines

Verbatim from [`prompts/Github.txt`](../prompts/Github.txt), which declares the source as the
*GitHub documentation style guide*.

| Group | Guidelines |
|---|---|
| Reference Content | Decide whether to create standalone reference articles or embed them; ensure clear, consistent, beginner-friendly presentation; use suitable formats (lists, tables, headings). |
| Conceptual Content Guidelines | Begin with **About [topic]**; explain purpose and use cases with practical examples; include prerequisites and next steps. |
| Error Reference Content Guidelines | Help users recognise and understand issues clearly; separate troubleshooting from known issues; document errors transparently with solutions. |
| Tutorial Content Guidelines | Define target audience and learning goals upfront; use a clear developer tone with code examples; anticipate common questions and summarise accomplishments. |
| Getting Started Content Guidelines | Provide a concise, step-based quick-start (under 600 words); include prerequisites, troubleshooting tips and next steps. |
| Content Organization | Follow a unified content model with clear document types (Concept, Reference, Procedure); keep the structure simple and navigable; organise as Concept → Reference → Setup → Usage → Troubleshooting. |
| Title Standards | Use task-based gerund titles that are general and scalable; keep titles clear, descriptive and concise (max 80 characters, ideally 60). |
| Introduction Standards | Write a 1–2 sentence introduction with context and keywords; avoid repeating title terms. |
| Process Content Standards | Write procedural content as clear, step-by-step, task-oriented instructions; state permissions upfront using the format *"People with [role] can [action]"*. |
| Reusability Standards | Use reusable text variables to avoid duplicate content; mark product-specific features clearly with labeled notes and links. |

The same prompt also prescribes the required output structure (About, Description, Quick Start,
Parameters, Returns, Permissions & Access, Dependencies, Used By, Example Usage, Prerequisites,
Next Steps, Further Reading, Notes) and five "critical requirements" that emphasise the weak
areas (Further Reading ≥3–5 external resources, explicit Permissions & Access, ≥3 actionable
Next Steps, step-based Quick Start with troubleshooting, keyword-rich About that does not
repeat the title).

## 2. The evaluation rubric reported in the paper — 5 categories / 12 dimensions

Source: the manuscript's GitHub rubric table, reproduced here so the criteria are readable
from the artifact alone.

| Category | Dimension | Definition |
|---|---|---|
| Content Model | Title Standards | Ensure titles are clear, descriptive, and concise, typically within 60–80 characters. |
| Content Model | Category Title Naming | Use task-based gerund titles that remain general and scalable. |
| Article Content | Permission Declaration Standards | State permissions upfront using the form "People with [role] can [action]." |
| Article Content | Process Content Standards | Present procedures as clear step-by-step instructions. |
| Article Content | Next Steps Standards | Include follow-up links that guide users to the next relevant topic. |
| Article Content | Prerequisites Standards | List warnings and requirements before sensitive tasks. |
| Reference Content | Reference Content | Decide whether reference information should be presented as standalone articles or embedded sections. |
| Reference Content | Conceptual Content Guidelines | Begin with "About [topic]" and explain purpose and use cases clearly. |
| Reference Content | Error Reference Content Guidelines | Help users recognize and understand issues, separate from troubleshooting. |
| Tutorial Content | Tutorial Content Guidelines | Define the target audience and goals, and use a clear developer-oriented tone with examples. |
| Tutorial Content | Getting Started Content Guidelines | Provide a concise step-based quick start, preferably under 600 words. |
| Further Reading | Further Reading Standards | Provide a bulleted list of external or advanced resources. |

## 3. Known gaps

1. **No judge-facing definition was recovered for any GitHub dimension.** The archived judging
   transcripts (`5Score/DOTquality_mul_Eval.jsonl`) contain 18 per-dimension prompts and every
   one of them is an ISO dimension name. The GitHub-rubric judge runs clearly happened — every
   repository contributes `*quality_github.jsonl` / `*quality_github.md` outputs under
   `results/per-repository/` — but the prompts and per-dimension definitions behind those runs
   are not archived. If they were produced by a separate judging script, that script and its
   logs should be added.
2. **Related critique raised in review:** the GitHub *style guide* governs GitHub's own
   product documentation, not a general documentation standard for repositories hosted on the
   platform. That scoping question is a manuscript-level issue, not an artifact issue, but it
   is recorded here because it affects how the GitHub rubric should be described.
