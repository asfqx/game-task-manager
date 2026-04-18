import type { ProjectDetailResponse, TaskResponse } from '../api/types';
import { formatDate, formatTaskStatusLabel } from '../utils';

type ProjectTaskReportPageProps = {
  project: ProjectDetailResponse;
  tasks: TaskResponse[];
  isLoading: boolean;
  onBackToProject: () => void;
  onBackToProjects: () => void;
  onTaskSelect: (taskUuid: string) => void;
};

type ProjectTaskReportSectionProps = {
  title: string;
  subtitle: string;
  tasks: TaskResponse[];
  emptyText: string;
  onTaskSelect: (taskUuid: string) => void;
};

type ActivityChartPoint = {
  dateKey: string;
  label: string;
  shortLabel: string;
  count: number;
};

type PositionedActivityChartPoint = ActivityChartPoint & {
  x: number;
  y: number;
};

type ProjectTaskActivityChartProps = {
  completedTasks: TaskResponse[];
  isLoading: boolean;
};

const MONTH_LABELS = [
  'января',
  'февраля',
  'марта',
  'апреля',
  'мая',
  'июня',
  'июля',
  'августа',
  'сентября',
  'октября',
  'ноября',
  'декабря',
];

function getStatusClassName(status: TaskResponse['status']): string {
  return `status-${status.toLowerCase().replace('_', '-')}`;
}

function getDeadlineLabel(task: TaskResponse): string {
  return task.deadline ? formatDate(task.deadline) : 'Без дедлайна';
}

function sortCompletedTasks(left: TaskResponse, right: TaskResponse): number {
  const leftDate = Date.parse(left.completed_at ?? left.updated_at);
  const rightDate = Date.parse(right.completed_at ?? right.updated_at);

  return rightDate - leftDate;
}

function sortRemainingTasks(left: TaskResponse, right: TaskResponse): number {
  const leftDeadline = left.deadline ? Date.parse(left.deadline) : Number.POSITIVE_INFINITY;
  const rightDeadline = right.deadline ? Date.parse(right.deadline) : Number.POSITIVE_INFINITY;

  if (leftDeadline !== rightDeadline) {
    return leftDeadline - rightDeadline;
  }

  return left.title.localeCompare(right.title, 'ru');
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function formatActivityDate(date: Date): string {
  return `${date.getDate()} ${MONTH_LABELS[date.getMonth()]}`;
}

function buildActivityPoints(completedTasks: TaskResponse[]): ActivityChartPoint[] {
  const tasksByDate = new Map<string, { date: Date; count: number }>();

  for (const task of completedTasks) {
    const completedAt = task.completed_at;

    if (!completedAt) {
      continue;
    }

    const date = new Date(completedAt);
    const dateKey = [
      date.getFullYear(),
      String(date.getMonth() + 1).padStart(2, '0'),
      String(date.getDate()).padStart(2, '0'),
    ].join('-');
    const current = tasksByDate.get(dateKey);

    tasksByDate.set(dateKey, {
      date,
      count: (current?.count ?? 0) + 1,
    });
  }

  return Array.from(tasksByDate.entries())
    .sort(([, left], [, right]) => left.date.getTime() - right.date.getTime())
    .slice(-9)
    .map(([dateKey, item]) => ({
      dateKey,
      label: formatActivityDate(item.date),
      shortLabel: String(item.date.getDate()),
      count: item.count,
    }));
}

function buildSmoothPath(points: PositionedActivityChartPoint[]): string {
  if (!points.length) {
    return '';
  }

  if (points.length === 1) {
    return `M ${points[0].x} ${points[0].y}`;
  }

  const commands = [`M ${points[0].x} ${points[0].y}`];

  for (let index = 0; index < points.length - 1; index += 1) {
    const previous = points[index - 1] ?? points[index];
    const current = points[index];
    const next = points[index + 1];
    const afterNext = points[index + 2] ?? next;

    const controlOneX = current.x + (next.x - previous.x) / 6;
    const controlOneY = current.y + (next.y - previous.y) / 6;
    const controlTwoX = next.x - (afterNext.x - current.x) / 6;
    const controlTwoY = next.y - (afterNext.y - current.y) / 6;

    commands.push(
      `C ${controlOneX} ${controlOneY} ${controlTwoX} ${controlTwoY} ${next.x} ${next.y}`,
    );
  }

  return commands.join(' ');
}

function ProjectTaskActivityChart({
  completedTasks,
  isLoading,
}: ProjectTaskActivityChartProps) {
  const activityPoints = buildActivityPoints(completedTasks);
  const chartWidth = 760;
  const chartHeight = 260;
  const plotLeft = 46;
  const plotTop = 26;
  const plotWidth = 660;
  const plotHeight = 168;
  const baselineY = plotTop + plotHeight;
  const maxCount = Math.max(...activityPoints.map((point) => point.count), 4);
  const tickStep = Math.max(1, Math.ceil(maxCount / 4));
  const yMax = tickStep * 4;
  const yTicks = Array.from({ length: 5 }, (_, index) => index * tickStep);
  const positionedPoints = activityPoints.map((point, index) => {
    const x = activityPoints.length === 1
      ? plotLeft + plotWidth / 2
      : plotLeft + (plotWidth * index) / (activityPoints.length - 1);
    const y = baselineY - (point.count / yMax) * plotHeight;

    return {
      ...point,
      x,
      y,
    };
  });
  const linePath = positionedPoints.length === 1
    ? `M ${plotLeft} ${positionedPoints[0].y} L ${plotLeft + plotWidth} ${positionedPoints[0].y}`
    : buildSmoothPath(positionedPoints);
  const areaPath = positionedPoints.length === 1
    ? `M ${plotLeft} ${positionedPoints[0].y} L ${plotLeft + plotWidth} ${positionedPoints[0].y} L ${plotLeft + plotWidth} ${baselineY} L ${plotLeft} ${baselineY} Z`
    : positionedPoints.length
      ? `${linePath} L ${positionedPoints[positionedPoints.length - 1].x} ${baselineY} L ${positionedPoints[0].x} ${baselineY} Z`
    : '';
  const activePoint = positionedPoints.reduce<PositionedActivityChartPoint | null>(
    (current, point) => {
      if (!current || point.count >= current.count) {
        return point;
      }

      return current;
    },
    null,
  );
  const tooltipWidth = 190;
  const tooltipHeight = 62;
  const tooltipX = activePoint
    ? clamp(activePoint.x - tooltipWidth / 2, plotLeft + 8, plotLeft + plotWidth - tooltipWidth - 8)
    : 0;
  const tooltipY = activePoint ? Math.max(12, activePoint.y - tooltipHeight - 18) : 0;

  return (
    <section className="project-task-report__activity-card">
      <div className="project-task-report__activity-header">
        <div>
          <span className="board-header__eyebrow">Динамика завершений</span>
          <h3>Активность команды</h3>
        </div>
        <span className="metric-chip">Выполненные задачи</span>
      </div>

      {isLoading ? (
        <div className="project-task-report__empty">Загружаем активность команды...</div>
      ) : activityPoints.length ? (
        <div className="project-task-report__activity-chart-wrap">
          <svg
            className="project-task-report__activity-chart"
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            role="img"
            aria-label="Диаграмма активности команды по выполненным задачам"
          >
            <defs>
              <linearGradient id="project-task-activity-fill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="rgba(69, 146, 118, 0.32)" />
                <stop offset="100%" stopColor="rgba(69, 146, 118, 0.02)" />
              </linearGradient>
            </defs>

            {yTicks.map((tick) => {
              const y = baselineY - (tick / yMax) * plotHeight;

              return (
                <g key={tick}>
                  <line
                    className="project-task-report__activity-grid-line"
                    x1={plotLeft}
                    x2={plotLeft + plotWidth}
                    y1={y}
                    y2={y}
                  />
                  <text
                    className="project-task-report__activity-axis-label"
                    x={plotLeft - 16}
                    y={y + 4}
                  >
                    {tick}
                  </text>
                </g>
              );
            })}

            {positionedPoints.map((point) => (
              <text
                key={point.dateKey}
                className="project-task-report__activity-axis-label project-task-report__activity-axis-label--x"
                x={point.x}
                y={baselineY + 30}
              >
                {point.shortLabel}
              </text>
            ))}

            <path className="project-task-report__activity-area" d={areaPath} />
            <path className="project-task-report__activity-line" d={linePath} />

            {positionedPoints.map((point) => (
              <circle
                key={point.dateKey}
                className={point.dateKey === activePoint?.dateKey
                  ? 'project-task-report__activity-point project-task-report__activity-point--active'
                  : 'project-task-report__activity-point'}
                cx={point.x}
                cy={point.y}
                r={point.dateKey === activePoint?.dateKey ? 6 : 4}
              />
            ))}

            {activePoint ? (
              <g className="project-task-report__activity-tooltip">
                <rect
                  x={tooltipX}
                  y={tooltipY}
                  width={tooltipWidth}
                  height={tooltipHeight}
                  rx={14}
                />
                <text x={tooltipX + 18} y={tooltipY + 25}>
                  <tspan className="project-task-report__activity-tooltip-label">
                    Завершено задач: {activePoint.count}
                  </tspan>
                  <tspan
                    className="project-task-report__activity-tooltip-value"
                    x={tooltipX + 18}
                    dy={19}
                  >
                    {activePoint.label}
                  </tspan>
                </text>
              </g>
            ) : null}
          </svg>
        </div>
      ) : (
        <div className="project-task-report__empty">
          Активность появится после первой выполненной задачи.
        </div>
      )}
    </section>
  );
}

function ProjectTaskReportSection({
  title,
  subtitle,
  tasks,
  emptyText,
  onTaskSelect,
}: ProjectTaskReportSectionProps) {
  return (
    <section className="project-task-report__section">
      <div className="section-heading">
        <div>
          <h3>{title}</h3>
          <p className="project-task-report__section-subtitle">{subtitle}</p>
        </div>
      </div>

      {tasks.length ? (
        <div className="project-task-report__list">
          {tasks.map((task) => (
            <button
              key={task.uuid}
              type="button"
              className="project-task-report__row"
              onClick={() => onTaskSelect(task.uuid)}
            >
              <div className="project-task-report__task-main">
                <span
                  className={`metric-chip status-pill ${getStatusClassName(task.status)}`}
                >
                  {formatTaskStatusLabel(task.status)}
                </span>
                <strong>{task.title}</strong>
                <p>{task.description ?? 'Описание задачи пока не заполнено.'}</p>
              </div>

              <div className="project-task-report__meta-grid">
                <div className="project-task-report__meta-card">
                  <span>Исполнитель</span>
                  <strong>{task.assignee_user?.fio ?? 'Без исполнителя'}</strong>
                </div>
                <div className="project-task-report__meta-card">
                  <span>Дедлайн</span>
                  <strong>{getDeadlineLabel(task)}</strong>
                </div>
                <div className="project-task-report__meta-card">
                  <span>Команда</span>
                  <strong>{task.team.name}</strong>
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="project-task-report__empty">{emptyText}</div>
      )}
    </section>
  );
}

export function ProjectTaskReportPage({
  project,
  tasks,
  isLoading,
  onBackToProject,
  onBackToProjects,
  onTaskSelect,
}: ProjectTaskReportPageProps) {
  const completedTasks = tasks
    .filter((task) => task.status === 'DONE')
    .sort(sortCompletedTasks);
  const remainingTasks = tasks
    .filter((task) => task.status !== 'DONE')
    .sort(sortRemainingTasks);
  const teamsWithTasks = new Set(tasks.map((task) => task.team_uuid)).size;

  return (
    <section className="workspace-panel project-task-report">
      <div className="project-summary-card project-summary-card--project project-task-report__hero">
        <div className="project-summary-card__content">
          <span className="board-header__eyebrow">Отчет по задачам</span>
          <strong>{project.title}</strong>
          <p>
            Сводка по выполненным и оставшимся задачам проекта
          </p>
        </div>
        <div className="project-summary-card__actions project-summary-card__actions--row">
          <button type="button" className="secondary-button" onClick={onBackToProject}>
            К проекту
          </button>
          <button type="button" className="secondary-button" onClick={onBackToProjects}>
            К проектам
          </button>
        </div>
      </div>

      <div className="project-task-report__stats">
        <article className="project-task-report__stat-card">
          <span>Всего задач</span>
          <strong>{tasks.length}</strong>
        </article>
        <article className="project-task-report__stat-card project-task-report__stat-card--done">
          <span>Выполнены</span>
          <strong>{completedTasks.length}</strong>
        </article>
        <article className="project-task-report__stat-card project-task-report__stat-card--remaining">
          <span>Остались</span>
          <strong>{remainingTasks.length}</strong>
        </article>
        <article className="project-task-report__stat-card">
          <span>Команды</span>
          <strong>{teamsWithTasks}</strong>
        </article>
      </div>

      <ProjectTaskActivityChart
        completedTasks={completedTasks}
        isLoading={isLoading}
      />

      {isLoading ? (
        <div className="project-task-report__empty">Загружаем задачи проекта...</div>
      ) : (
        <>
          <ProjectTaskReportSection
            title="Оставшиеся задачи"
            subtitle="Бэклог, задачи в работе и задачи на проверке."
            tasks={remainingTasks}
            emptyText="Невыполненных задач не осталось."
            onTaskSelect={onTaskSelect}
          />

          <ProjectTaskReportSection
            title="Выполненные задачи"
            subtitle="Все задачи, которые уже отмечены как выполненные."
            tasks={completedTasks}
            emptyText="В этом проекте пока нет выполненных задач."
            onTaskSelect={onTaskSelect}
          />
        </>
      )}
    </section>
  );
}
