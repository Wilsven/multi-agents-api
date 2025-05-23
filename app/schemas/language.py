from enum import Enum


class LanguageChoice(Enum):
    ENGLISH = "english"
    CHINESE = "chinese"
    MALAY = "malay"
    TAMIL = "tamil"
    UNKNOWN = "unknown"


class SynthesisVoiceNames:

    voice_mapping = {
        LanguageChoice.ENGLISH.value: "en-US-EmmaNeural",
        LanguageChoice.CHINESE.value: "zh-CN-XiaoxiaoNeural",
        LanguageChoice.MALAY.value: "ms-MY-YasminNeural",
        LanguageChoice.TAMIL.value: "ta-SG-VenbaNeural",
    }


class LanguageISO639_1:
    language_mapping = {
        LanguageChoice.ENGLISH.value: "en",
        LanguageChoice.CHINESE.value: "zh",
        LanguageChoice.MALAY.value: "ms",
        LanguageChoice.TAMIL.value: "ta",
    }
