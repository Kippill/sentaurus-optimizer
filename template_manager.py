from pathlib import Path
import re


TEMPLATES_DIR = Path("templates")


def _format_value(value):
    """
    Преобразует Python-значение в аккуратный текст
    для Sentaurus cmd.
    """

    if isinstance(value, float):
        return f"{value:.12g}"

    return str(value)


def render_template(template_name, replacements):
    """
    Читает шаблон и заменяет:

        __TOKEN__

    значениями из replacements.
    """

    template_path = (
        TEMPLATES_DIR / template_name
    )

    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}"
        )

    text = template_path.read_text(
        encoding="utf-8"
    )

    for key, value in replacements.items():

        token = f"__{key}__"

        text = text.replace(
            token,
            _format_value(value)
        )

    # Ищем оставшиеся незаменённые токены
    remaining = re.findall(
        r"__[A-Z0-9_]+__",
        text
    )

    if remaining:
        remaining = sorted(set(remaining))

        raise ValueError(
            "В шаблоне остались "
            "незаменённые параметры:\n"
            + "\n".join(remaining)
        )

    return text


def save_rendered_template(
    template_name,
    output_path,
    replacements
):
    """
    Создаёт готовый Sentaurus cmd
    из шаблона.
    """

    text = render_template(
        template_name,
        replacements
    )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        text,
        encoding="utf-8"
    )

    return output_path