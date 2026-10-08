"""Search articles managed in the local operator workbench."""

from langchain_core.tools import tool

from src.db.support_data import list_articles


@tool
def search_product_guide(query: str) -> str:
    """Search active product guide articles by Chinese or English keywords."""
    normalized = query.strip().lower()
    if not normalized:
        return "未提供查询内容，请描述想了解的产品功能。"

    ranked = []
    for article in list_articles(active_only=True):
        terms = [term.strip() for term in article["keywords"].split(",") if term.strip()]
        score = sum(2 for term in terms if term in normalized)
        if article["title"].lower() in normalized:
            score += 3
        if score:
            ranked.append((score, article))

    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return "产品指南中没有匹配内容。请不要猜测，可以建议用户创建支持工单。"
    return "\n\n".join(
        f"{article['title']}：{article['content']}" for _, article in ranked[:3]
    )


knowledge_tools = [search_product_guide]
