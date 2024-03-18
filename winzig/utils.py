import string
import emoji

translation_table = str.maketrans(
    {char: " " for char in string.punctuation + "“”’‘¶■▲▼"}
)


def update_url_scores(old: dict[str, float], new: dict[str, float]) -> dict[str, float]:
    for url, score in new.items():
        if url in old:
            old[url] += score
        else:
            old[url] = score

    return old


def normalize_text(text: str) -> str:
    normalized = emoji.replace_emoji(text, replace="")
    normalized = text.translate(translation_table).lower()
    normalized = " ".join(normalized.split())
    return normalized


def get_top_urls(scores_dict: dict, n: int):
    sorted_urls = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    top_n_urls = sorted_urls[:n]
    top_n_dict = dict(top_n_urls)
    return top_n_dict
