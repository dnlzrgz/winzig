import string
import emoji

emojis = set(emoji.EMOJI_DATA.keys())
punctuation_and_emojis = set(string.punctuation + "“”’‘¶■▌▲▼└│─√©" + "".join(emojis))

translation_table = str.maketrans(({char: " " for char in punctuation_and_emojis}))


def update_url_scores(old: dict[str, float], new: dict[str, float]) -> dict[str, float]:
    for url, score in new.items():
        old[url] = old.get(url, 0.0) + score

    return old


def normalize_text(text: str) -> str:
    normalized = text.translate(translation_table).lower()
    normalized = " ".join(normalized.split())
    return normalized


def get_top_urls(scores_dict: dict, n: int):
    sorted_urls = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    top_n_dict = dict(sorted_urls[:n])
    return top_n_dict
