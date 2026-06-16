import json
import re
from models.kural import Kural

TOPIC_FALLBACKS = {
    "god": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "lord": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "worship": [1, 2, 7, 9],
    "education": [391, 392, 393, 394, 395, 396, 397, 398, 399, 400],
    "learning": [391, 392, 393, 394, 395, 396, 397, 398, 399, 400],
    "study": [391, 392, 393],
    "wisdom": [391, 392, 393, 421, 422, 423],
    "virtue": [31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
    "righteousness": [31, 32, 33],
    "friendship": [781, 782, 783, 784, 785, 786, 787, 788, 789, 790],
    "friend": [781, 782, 783, 784, 785],
    "anger": [301, 302, 303, 304, 305, 306, 307, 308, 309, 310],
    "wrath": [301, 302, 303],
    "love": [71, 72, 73, 74, 75, 76, 77, 78, 79, 80],
    "family": [41, 42, 43, 44, 45],
    "truth": [291, 292, 293, 294, 295],
    "wealth": [751, 752, 753, 754, 755]
}

class KuralDatabase:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._kurals = []
        self.load_kurals()

    def load_kurals(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            self._kurals = [Kural.from_dict(item) for item in data]
        except Exception as e:
            print(f"Error loading database file: {e}")
            self._kurals = []

    def find_by_number(self, num: int) -> Kural:
        for kural in self._kurals:
            if kural.number == num:
                return kural
        return None

    def search(self, query: str, exclude_numbers: list = None) -> list:
        # 1. Direct number lookup (if query contains a number)
        nums = re.findall(r'\b\d+\b', query)
        if nums:
            num = int(nums[0])
            if 1 <= num <= 1330:
                k = self.find_by_number(num)
                if k:
                    return [k]

        # 2. Text-based search
        words = re.sub(r'[^\w\s]', '', query.lower()).split()
        stop_words = {
            "tell", "me", "a", "kural", "about", "what", "is", "the", "say", 
            "on", "in", "to", "for", "of", "with", "show", "give", "find", 
            "explain", "meaning", "translation", "thirukkural", "thirukural"
        }
        search_words = [w for w in words if w not in stop_words and len(w) > 1]
        
        if not search_words:
            search_words = words

        if not search_words:
            return []

        scored_kurals = []
        for k in self._kurals:
            # Skip if Kural is excluded (already shown)
            if exclude_numbers and k.number in exclude_numbers:
                continue

            score = 0
            
            # Apply static topic fallback boosts
            for word in search_words:
                if word in TOPIC_FALLBACKS:
                    boost_nums = TOPIC_FALLBACKS[word]
                    if k.number in boost_nums:
                        rank = boost_nums.index(k.number)
                        score += 100 - (rank * 10)

            # Match fields
            fields = [
                (k.translation, 3),
                (k.explanation, 3),
                (k.line1, 2),
                (k.line2, 2),
                (k.mv, 2),
                (k.sp, 2),
                (k.transliteration1, 1),
                (k.transliteration2, 1)
            ]
            
            for text, weight in fields:
                if text:
                    cleaned_text = text.lower()
                    for word in search_words:
                        if word in cleaned_text:
                            if f" {word} " in f" {cleaned_text} ":
                                score += weight * 3
                            else:
                                score += weight
                                
            if score > 0:
                scored_kurals.append((score, k))

        # If all matched Kurals are excluded, loop back by searching without exclusions
        if not scored_kurals and exclude_numbers:
            return self.search(query, exclude_numbers=None)

        # Sort descending by score, then ascending by Kural number
        scored_kurals.sort(key=lambda x: (x[0], -x[1].number), reverse=True)
        return [item[1] for item in scored_kurals[:5]]
