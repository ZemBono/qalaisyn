"""Standard Cyrillic Kazakh -> the official Kazakh Latin alphabet (2021 version).
Kazakhstan plans to move to this alphabet, so Qalaisyn can output either script."""

LATIN_2021 = {
    "а": "a", "ә": "ä", "б": "b", "в": "v", "г": "g", "ғ": "ğ", "д": "d", "е": "e", "ё": "io", "ж": "j",
    "з": "z", "и": "i", "й": "i", "к": "k", "қ": "q", "л": "l", "м": "m", "н": "n", "ң": "ñ", "о": "o",
    "ө": "ö", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ұ": "ū", "ү": "ü", "ф": "f", "х": "h",
    "һ": "h", "ц": "ts", "ч": "ç", "ш": "ş", "щ": "şş", "ъ": "", "ы": "y", "і": "ı", "ь": "", "э": "e",
    "ю": "iu", "я": "ia",
}


def to_latin(text: str) -> str:
    return "".join(LATIN_2021.get(ch, ch) for ch in text)


if __name__ == "__main__":
    print(to_latin("ұшақ кешігіп жатыр ма"), "|", to_latin("сәлем қалайсың"))
