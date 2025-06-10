from enum import Enum
from typing import Dict

class Language(Enum):
    """Enumeration of supported language/geo combinations."""
    # (code, gl, hl, name, source_tag)
    EN = ("en", "us", "en", "English", "Source")
    KO = ("ko", "kr", "ko", "Korean", "출처")
    ZH = ("zh", "cn", "zh-cn", "Chinese", "Source")
    JA = ("ja", "jp", "ja", "Japanese", "Source")
    
    DE = ("de", "de", "de", "German", "Source")
    FR = ("fr", "fr", "fr", "French", "Source")
    ES = ("es", "es", "es", "Spanish", "Source")
    IT = ("it", "it", "it", "Italian", "Source")
    NL = ("nl", "nl", "nl", "Dutch", "Source")
    PT = ("pt", "pt", "pt", "Portuguese", "Source")
    RU = ("ru", "ru", "ru", "Russian", "Source")
    PL = ("pl", "pl", "pl", "Polish", "Source")
    SE = ("sv", "se", "sv", "Swedish", "Source")
    NO = ("no", "no", "no", "Norwegian", "Source")
    DK = ("da", "dk", "da", "Danish", "Source")
    FI = ("fi", "fi", "fi", "Finnish", "Source")
    
    AR = ("ar", "ar", "ar", "Arabic", "Source")
    BR = ("pt", "br", "pt-br", "Portuguese", "Source")
    IN = ("hi", "in", "hi", "Hindi", "Source")
    ID = ("id", "id", "id", "Indonesian", "Source")
    TR = ("tr", "tr", "tr", "Turkish", "Source")
    TH = ("th", "th", "th", "Thai", "Source")
    VN = ("vi", "vn", "vi", "Vietnamese", "Source")

    @classmethod
    def from_code(cls, code: str) -> "Language":
        """Return the matching language enum or default to English (EN)."""
        return next((lang for lang in cls if lang.value[0] == code), cls.EN)

    @property
    def query_params(self) -> Dict[str, str]:
        """Parameters expected by the Serper API (gl, hl)."""
        _, gl, hl, name, source_tag = self.value
        return {"gl": gl, "hl": hl, "name": name, "source_tag": source_tag}


if __name__ == "__main__":
    # 테스트 예시 추가
    print(Language.from_code("en").query_params)
    print(Language.from_code("ko").query_params)
    print(Language.from_code("de").query_params)
    print(Language.from_code("fr").query_params)
    print(Language.from_code("es").query_params)