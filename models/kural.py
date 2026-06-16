class Kural:
    def __init__(
        self,
        number: int,
        line1: str,
        line2: str,
        translation: str,
        mv: str,
        sp: str,
        mk: str,
        explanation: str,
        couplet: str,
        transliteration1: str,
        transliteration2: str
    ):
        self.number = number
        self.line1 = line1
        self.line2 = line2
        self.translation = translation
        self.mv = mv
        self.sp = sp
        self.mk = mk
        self.explanation = explanation
        self.couplet = couplet
        self.transliteration1 = transliteration1
        self.transliteration2 = transliteration2

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            number=data.get("Number"),
            line1=data.get("Line1"),
            line2=data.get("Line2"),
            translation=data.get("Translation"),
            mv=data.get("mv"),
            sp=data.get("sp"),
            mk=data.get("mk"),
            explanation=data.get("explanation"),
            couplet=data.get("couplet"),
            transliteration1=data.get("transliteration1"),
            transliteration2=data.get("transliteration2")
        )

    def to_dict(self):
        return {
            "number": self.number,
            "line1": self.line1,
            "line2": self.line2,
            "translation": self.translation,
            "mv": self.mv,
            "sp": self.sp,
            "mk": self.mk,
            "explanation": self.explanation,
            "couplet": self.couplet,
            "transliteration1": self.transliteration1,
            "transliteration2": self.transliteration2
        }
