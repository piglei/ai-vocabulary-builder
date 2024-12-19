from voc_builder.infras.store import get_sys_settings_store
from voc_builder.system.constants import TargetLanguage


def get_target_language() -> str:
    """Get the target language for generating the vocabulary.

    * Simplified Chinese is used if the target language is not set.
    """
    s = get_sys_settings_store().get_system_settings()
    if not (s and s.target_language):
        return TargetLanguage.SIMPLIFIED_CHINESE.value.name
    lan = TargetLanguage.get_by_code(s.target_language)
    assert lan
    return lan.value.name
