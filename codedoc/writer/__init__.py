"""Writer library: prompt assembly and LLM access for documentation generation.

``prompt``  turns a dependency context into the structured, criterion-aware
            prompt (including the class/polymorphism blocks)
``llm``     thin OpenAI-compatible client used for both generation and judging
``templates`` the criteria templates shipped with the artifact
"""

from codedoc.writer.prompt import build_context_blocks, format_dep, build_prompt

__all__ = ["build_prompt", "format_dep", "build_context_blocks"]
