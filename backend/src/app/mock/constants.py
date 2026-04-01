DEMO_PROJECT_TITLE = "Demo Project"
DEMO_PROJECT_DESCRIPTION = "Стартовый проект для демонстрации ролей, команд и задач."
DEMO_TEAM_NAME = "Core Team"
DEMO_TEAM_DESCRIPTION = "Основная команда стартового проекта."

DEMO_USERS: tuple[tuple[str, str, str], ...] = (
    ("teamlead1", "teamlead1@example.com", "TeamLead One"),
    ("alicework", "alicework@example.com", "Alice Workman"),
    ("bobworker", "bobworker@example.com", "Bob Worker"),
    ("charlie8", "charlie8@example.com", "Charlie Ray"),
)

DEMO_TASKS: tuple[tuple[str, str, str, int, int], ...] = (
    (
        "Prepare backlog",
        "Собрать и описать стартовый бэклог проекта.",
        "alicework",
        120,
        3,
    ),
    (
        "Design board",
        "Подготовить структуру доски задач и статусов.",
        "bobworker",
        180,
        5,
    ),
    (
        "Setup notifications",
        "Проверить уведомления и сценарии оповещений.",
        "charlie8",
        220,
        7,
    ),
)
