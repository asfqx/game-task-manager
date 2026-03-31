from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template


class BaseMailService:

    env = Environment(
        loader=FileSystemLoader(Path(__file__).parents[2] / "templates" / "mail"),
        enable_async=True,
    )

    @classmethod
    def get_template(cls, template_name: str) -> Template:

        return cls.env.get_template(template_name)
