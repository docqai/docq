"""Functions that can post process nodes, typicaly after retrieval from an index using some search method like vector or BM25.

These aren't always implementations of LlamaIndex's `BaseNodePostProcessor` interface, but they are used in a similar way.
"""

from typing import Dict, List, Tuple

from llama_index.core.schema import NodeWithScore


def reciprocal_rank_fusion(results: Dict[str, List[NodeWithScore]]) -> List[NodeWithScore]:
    """Apply reciprocal rank fusion.

    The original paper uses k=60 for best results:
    https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf

    Note: we cannot implement this as a `NodePostProcessor` because we need to pass in multiple lists of nodes. If we flatten the lists into one the ranking calc will be different there for a different result.

    Args:
        results: A dictionary of results `NodeWithScore` from multiple search methods.
    """
    k = 60.0  # `k` is a parameter used to control the impact of outlier rankings.
    fused_scores = {}
    text_to_node = {}

    # compute reciprocal rank scores
    for nodes_with_scores in results.values():
        for rank, node_with_score in enumerate(sorted(nodes_with_scores, key=lambda x: x.score or 0.0, reverse=True)):
            text = node_with_score.node.get_content()
            text_to_node[text] = node_with_score
            if text not in fused_scores:
                fused_scores[text] = 0.0
            fused_scores[text] += 1.0 / (rank + k)

    # sort results
    reranked_results = dict(sorted(fused_scores.items(), key=lambda x: x[1], reverse=True))

    # adjust node scores
    reranked_nodes: List[NodeWithScore] = []
    for text, score in reranked_results.items():
        reranked_nodes.append(text_to_node[text])
        reranked_nodes[-1].score = score

    return reranked_nodes
