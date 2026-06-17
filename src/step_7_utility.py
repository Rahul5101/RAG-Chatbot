# step_7_utility.py
import re


def escape_inner_quotes(text: str) -> str:
    """
    Escapes inner double quotes inside <a ...> and other HTML tags
    so the JSON remains valid.
    """
    # Escape quotes inside any <...> tag attributes
    def replacer(match):
        tag = match.group(0)
        # Escape only attribute quotes, not tag boundary < >
        tag = tag.replace('"', '\\"')
        return tag

    # Apply escaping to all HTML tags
    text = re.sub(r"<[^>]+>", replacer, text)
    return text


def replace_links(text: str, all_meta_data: list) -> str:
    """
    Replaces markdown-style [Source, page X](link)
    with <a href="SIGNED_URL" target="_blank">Source, page X</a>
    using metadata from all_meta_data list.
    """

    # Regex to match patterns like [Acts Collection 2025, page 12](link)
    pattern = r'\[([^\]]+?),\s*page\s*(\d+)\]\(link\)'

    def repl(match):
        source_name = match.group(1).strip()
        page = match.group(2).strip()

        # Remove everything after the last underscore (if present)
        if "_" in source_name:
            source_name = source_name.rsplit("_", 1)[0].strip()
        else:
            source_name = source_name.strip()

        # Find matching metadata entry
        matched_entry = next(
            (item for item in all_meta_data
             if item["source"].strip() == source_name and str(item.get("page", "")).strip() == page),
            None
        )

        if matched_entry and "signed_url" in matched_entry:
            return f'<a href="{matched_entry["signed_url"]}" target="_blank">{source_name}, page {page}</a>'
        else:
            # fallback: no match found, keep original text
            return f"{source_name}, page {page}"

    return re.sub(pattern, repl, text)



# def build_conversation_prompt(history) -> str:
#     """
#     Convert chat history + current user question
#     into a single prompt string
#     """

#     prompt_parts = []

#     for msg in history:
#         role = msg.get("role")
#         content = msg.get("content")

#         if not content:
#             continue

#         if role == "user":
#             prompt_parts.append(f"User: {content}")
#         elif role == "assistant":
#             prompt_parts.append(f"Assistant: {content}")

#     # Add current question
#     # prompt_parts.append(f"\nQuestion: {current_question}")

#     return "\n".join(prompt_parts)