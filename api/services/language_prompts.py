"""Per-language lemmatization rules for word enhancement prompts."""

_RULES: dict[str, str] = {
    "fr": """LEMMATIZATION RULES FOR FRENCH:
- Nouns: nominative singular with definite article.
    Use "l'" before vowel or silent h (l'homme, l'eau, l'amour).
    Use "le" for masculine nouns starting with a consonant (le chien, le temps).
    Use "la" for feminine nouns starting with a consonant (la femme, la maison).
    Example: "chiens" -> "le chien", "femmes" -> "la femme", "arbres" -> "l'arbre".
- Verbs: infinitive form.
    Pronominal/reflexive verbs: keep "se" (se lever, se souvenir, se heurter).
    Example: "il se leve" -> "se lever", "je me souviens" -> "se souvenir".
- Adjectives: masculine singular citation form.
    Example: "belle" -> "beau", "vieille" -> "vieux", "heureuse" -> "heureux".
- Adverbs: no change (sans cesse, tout a coup remain as-is).
- Fixed expressions: preserve exactly as given.
    A fixed expression is a multi-word unit whose meaning cannot be derived from its parts,
    or a prepositional phrase functioning as a single lexical unit.
    Examples: "au debut", "sans cesse", "faire confiance", "des lors", "tout a coup".
    Set is_fixed_expression to true for these.""",

    "es": """LEMMATIZATION RULES FOR SPANISH:
- Nouns: nominative singular with definite article.
    Use "el" for masculine (el perro, el libro).
    Use "la" for feminine (la casa, la mujer).
    Exception: feminine nouns beginning with stressed "a" or "ha" take "el" in singular (el agua, el hacha).
    Example: "perros" -> "el perro", "casas" -> "la casa".
- Verbs: infinitive form.
    Reflexive verbs: keep "-se" suffix on the infinitive (levantarse, sentarse, llamarse).
    Example: "se levanta" -> "levantarse", "me llamo" -> "llamarse".
- Adjectives: masculine singular (bueno, grande, bello).
- Fixed expressions: preserve exactly as given.
    Examples: "a pesar de", "sin embargo", "de repente", "a menudo", "en seguida".
    Set is_fixed_expression to true for these.""",

    "it": """LEMMATIZATION RULES FOR ITALIAN:
- Nouns: nominative singular with definite article.
    Use "il" for masculine nouns beginning with a consonant (il cane, il libro).
    Use "lo" for masculine nouns beginning with s+consonant, z, gn, pn, ps, x, y (lo studente, lo zaino, lo pneumatico).
    Use "l'" before any vowel for both genders (l'amico, l'acqua).
    Use "la" for feminine nouns beginning with a consonant (la casa, la donna).
    Example: "cani" -> "il cane", "studenti" -> "lo studente", "amici" -> "l'amico".
- Verbs: infinitive form.
    Reflexive verbs: keep "-si" suffix on the infinitive (alzarsi, sedersi, chiamarsi).
    Example: "si alza" -> "alzarsi".
- Adjectives: masculine singular (bello, buono, grande).
- Fixed expressions: preserve exactly as given.
    Examples: "a poco a poco", "di solito", "per forza", "in bocca al lupo".
    Set is_fixed_expression to true for these.""",

    "ru": """LEMMATIZATION RULES FOR RUSSIAN:
- Russian has no articles. Do NOT add any.
- Nouns: nominative singular case.
    Example: "книги" -> "книга", "домов" -> "дом".
- Verbs: imperfective infinitive as the citation form.
    If the verb only exists in perfective aspect, use the perfective infinitive.
    If a common aspectual pair exists, put the perfective partner alone in secondary_translation
    (e.g. lemma: "писать", translation: "<target language translation>", secondary_translation: "написать").
    Do NOT repeat the imperfective in secondary_translation.
    Example: "написал" -> lemma "писать", secondary_translation "написать".
- Adjectives: masculine nominative singular long form.
    Example: "красивая" -> "красивый", "большого" -> "большой".
- Fixed expressions: preserve exactly as given.
    Examples: "ни в коем случае", "тем не менее", "само собой разумеется".
    Set is_fixed_expression to true for these.""",

    "zh": """LEMMATIZATION RULES FOR CHINESE:
- Chinese has no articles. Do NOT add any.
- Output the lemma as: simplified characters immediately followed by pinyin with tone marks in
  parentheses, no spaces between syllables in the pinyin.
    Example: 开始 -> "开始 (kāishǐ)", 学习 -> "学习 (xuéxí)", 漂亮 -> "漂亮 (piàoliang)".
- Verbs, nouns, adjectives: use the base dictionary form (Chinese has no conjugation or declension).
- Chengyu (成语) and other fixed 4-character expressions: preserve exactly and mark as fixed expression.
    Example: 马到成功 -> "马到成功 (mǎdàochénggōng)".
- Other fixed expressions and set phrases: preserve exactly as given.
    Set is_fixed_expression to true for all multi-word fixed units.""",

    "default": """LEMMATIZATION RULES:
- Verbs: infinitive form.
- Nouns: singular form. Add a definite article only if the language grammatically requires one
  to convey gender (Romance languages). Do not add articles for languages without grammatical
  gender marking via articles (e.g. English, Russian, Chinese, Japanese, Arabic).
- Adjectives: citation/base form.
- Fixed expressions: preserve exactly as given. Set is_fixed_expression to true.""",
}


def get_language_rules(lang_code: str) -> str:
    """Return the lemmatization rules string for the given ISO 639-1 language code.

    Matching is case-insensitive. Falls back to the default rules for unsupported languages.
    """
    return _RULES.get(lang_code.lower() if lang_code else "", _RULES["default"])
