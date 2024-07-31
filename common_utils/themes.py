import re

from pydantic import BaseModel, model_validator


class ThemeParamsSchema(BaseModel):
    # Photo example
    # https://core.telegram.org/file/400780400851/2/6GwDkk6T-aY.416569/b591d589108b487d63
    # var(--tg-theme-bg-color)
    bg_color: str = "telegram"
    # var(--tg-theme-text-color)
    text_color: str = "telegram"
    # var(--tg-theme-hint-color)
    hint_color: str = "telegram"
    # var(--tg-theme-link-color)
    link_color: str = "telegram"
    # var(--tg-theme-button-color)
    button_color: str = "telegram"
    # var(--tg-theme-button-text-color)
    button_text_color: str = "telegram"
    # var(--tg-theme-secondary-bg-color)
    secondary_bg_color: str = "telegram"
    # var(--tg-theme-header-bg-color)
    header_bg_color: str = "telegram"
    # var(--tg-theme-accent-text-color)
    accent_text_color: str = "telegram"
    # var(--tg-theme-section-bg-color)
    section_bg_color: str = "telegram"
    # var(--tg-theme-section-header-text-color)
    section_header_text_color: str = "telegram"
    # var(--tg-theme-section-separator-color)
    section_separator_color: str = "telegram"
    # var(--tg-theme-subtitle-text-color)
    subtitle_text_color: str = "telegram"
    # var(--tg-theme-destructive-text-color)
    destructive_text_color: str = "telegram"

    @model_validator(mode='after')
    def check_valid_hex_colors(self):
        data = self.dict()
        for k, v in data.items():
            if v != "telegram" and not is_valid_hex_code(v):
                raise ValueError(f'parameter {k} should be valid hex color or "telegram"')
        return data


# Пример пресозданной нами темы, которую можно предлагать клиенту
THEME_EXAMPLE_PRESET = ThemeParamsSchema(
    bg_color="#000",
    text_color="#fff",
    hint_color="#e3e3e3",
    link_color="#893fff",
    button_color="#893fff",
    button_text_color="#fff",
    secondary_bg_color="#000",
    header_bg_color="#000",
    accent_text_color="#893fff",
    section_bg_color="#000",
    section_header_text_color="#e3e3e3",
    section_separator_color="#e3e3e3",
    subtitle_text_color="#e3e3e3",
    destructive_text_color="#ff4949",
)


def is_valid_hex_code(string: str) -> bool:
    """Проверяет, валидный ли цвет передал пользователь"""

    regex = r"#[a-f\d]{3}(?:[a-f\d]?|(?:[a-f\d]{3}(?:[a-f\d]{2})?)?)\b"

    p = re.compile(regex)

    if string is None:
        return False

    if re.search(p, string):
        return True
    else:
        return False
