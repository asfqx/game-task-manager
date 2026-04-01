import type { TaskBoardColumn } from '../models';
import { formatDate, formatTaskStatusLabel } from '../utils';

type TaskBoardProps = {
  columns: TaskBoardColumn[];
  selectedTaskId: string | null;
  onTaskSelect: (taskUuid: string) => void;
};

export function TaskBoard({
  columns,
  selectedTaskId,
  onTaskSelect,
}: TaskBoardProps) {
  return (
    <section className="workspace-panel workspace-panel--nested board-layout">
      <div className="section-heading">
        <h3>Доска задач</h3>
        <span>{columns.reduce((total, column) => total + column.tasks.length, 0)}</span>
      </div>
      <div className="board-columns">
        {columns.map((column) => (
          <section key={column.status} className="board-column">
            <div className="board-column__header">
              <div>
                <h3>{column.title}</h3>
                <span>{column.tasks.length} задач</span>
              </div>
              <span
                className={`metric-chip status-pill status-${column.status
                  .toLowerCase()
                  .replace('_', '-')}`}
              >
                {formatTaskStatusLabel(column.status)}
              </span>
            </div>
            <div className="board-column__cards">
              {column.tasks.length ? (
                column.tasks.map((task) => (
                  <button
                    key={task.uuid}
                    type="button"
                    className={`task-card ${selectedTaskId === task.uuid ? 'task-card--active' : ''}`}
                    onClick={() => onTaskSelect(task.uuid)}
                  >
                    <div className="task-card__header">
                      <div>
                        <strong>{task.title}</strong>
                        <span>{task.assignee_user?.fio ?? 'Без исполнителя'}</span>
                      </div>
                      <span
                        className={`metric-chip status-pill status-${task.status
                          .toLowerCase()
                          .replace('_', '-')}`}
                      >
                        {formatTaskStatusLabel(task.status)}
                      </span>
                    </div>
                    <p>{task.description ?? 'Описание не заполнено.'}</p>
                    {task.review_comment ? (
                      <div className="task-card__comment">
                        <span>Комментарий тимлида</span>
                        <strong>{task.review_comment}</strong>
                      </div>
                    ) : null}
                    <div className="task-card__footer">
                      <div className="task-card__meta">
                        <span>XP {task.xp_amount}</span>
                        <span>{formatDate(task.deadline)}</span>
                      </div>
                    </div>
                  </button>
                ))
              ) : (
                <div className="task-empty-state">Пока нет задач в этом статусе.</div>
              )}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}
