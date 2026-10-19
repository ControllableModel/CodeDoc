"""Judge library: criterion-aligned judging, aggregation and statistics.

``query``      prompt construction + model calls for single- and multi-round judging
``aggregate``  turning per-dimension scores into the reported numbers
``stats``      agreement (Fleiss / weighted kappa, ICC) and uncertainty

The split exists because reviewers correctly pointed out that the *aggregation
rule* embeds assumptions (unidimensionality, equal weights, additivity). Keeping
aggregation in its own module makes those assumptions inspectable and lets the
sensitivity analysis run over the same raw scores.
"""

__all__ = ["aggregate", "stats"]
