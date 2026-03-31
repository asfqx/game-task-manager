import { useDeferredValue, useEffect, useState, type FormEvent } from 'react';

import {
  acceptTask,
  approveTask,
  createTask,
  getNotifications,
  getProfile,
  getTasks,
  getTeams,
  rejectTask,
  submitTaskForReview,
  type NotificationResponse,
  type TaskResponse,
  type TaskStatus,
  type TeamResponse,
  type UserProfileResponse,
} from '../api/dashboard';

type DashboardPageProps = {
  accessToken: string;
  onLogout: () => void;
};

type Notice = {
  kind: 'success' | 'error' | 'info';
  text: string;
} | null;

type UrgencyFilter = 'all' | 'overdue' | 'soon' | 'planned' | 'done';

const statusMeta: Record<TaskStatus, { label: string; tone: string }> = {
  CREATED: { label: 'Новые', tone: 'status-created' },
  IN_WORK: { label: 'В работе', tone: 'status-in-work' },
  ON_CHECK: { label: 'На проверке', tone: 'status-on-check' },
  DONE: { label: 'Закрытые', tone: 'status-done' },
};

function formatDate(dateValue: string | null): string {
  if (!dateValue) {
    return 'Не задано';
  }

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(dateValue));
}

function normalizeDateTime(value: string): string | null {
  return value ? new Date(value).toISOString() : null;
}

function getTaskUrgency(task: TaskResponse): UrgencyFilter {
  if (task.status === 'DONE') {
    return 'done';
  }

  if (!task.deadline) {
    return 'planned';
  }

  const diff = new Date(task.deadline).getTime() - Date.now();
  if (diff < 0) {
    return 'overdue';
  }
  if (diff <= 1000 * 60 * 60 * 24 * 2) {
    return 'soon';
  }
  return 'planned';
}

function DashboardPage({
  accessToken,
  onLogout,
}: DashboardPageProps) {
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [teams, setTeams] = useState<TeamResponse[]>([]);
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [selectedTaskUuid, setSelectedTaskUuid] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [searchValue, setSearchValue] = useState('');
  const [teamFilter, setTeamFilter] = useState('all');
  const [assigneeFilter, setAssigneeFilter] = useState('all');
  const [urgencyFilter, setUrgencyFilter] = useState<UrgencyFilter>('all');
  const [showCreatePanel, setShowCreatePanel] = useState(false);
  const [rejectComment, setRejectComment] = useState('');
  const [createForm, setCreateForm] = useState({
    teamUuid: '',
    title: '',
    description: '',
    assigneeUserUuid: '',
    xpAmount: '100',
    deadline: '',
  });

  const deferredSearchValue = useDeferredValue(searchValue);

  async function loadDashboard({ silent = false }: { silent?: boolean } = {}) {
    if (!silent) {
      setIsLoading(true);
    }

    try {
      const [profileResponse, teamsResponse, tasksResponse, notificationsResponse] =
        await Promise.all([
          getProfile(accessToken),
          getTeams(accessToken),
          getTasks(accessToken),
          getNotifications(accessToken),
        ]);

      setProfile(profileResponse);
      setTeams(teamsResponse);
      setTasks(tasksResponse);
      setNotifications(notificationsResponse);
      setDashboardError(null);
    } catch (error) {
      setDashboardError(
        error instanceof Error
          ? error.message
          : 'Не удалось загрузить данные рабочего пространства.',
      );
    } finally {
      if (!silent) {
        setIsLoading(false);
      }
    }
  }

  useEffect(() => {
    void loadDashboard();

    const refreshInterval = window.setInterval(() => {
      void loadDashboard({ silent: true });
    }, 30000);

    return () => window.clearInterval(refreshInterval);
  }, [accessToken]);

  const manageableTeams = teams.filter((team) => {
    if (!profile) {
      return false;
    }

    return profile.role === 'admin' || team.lead_uuid === profile.uuid;
  });

  useEffect(() => {
    if (!manageableTeams.length || createForm.teamUuid) {
      return;
    }

    const defaultTeam = manageableTeams[0];
    const defaultAssignee =
      defaultTeam.members.find((member) => !member.is_team_lead && member.user)?.user_uuid ??
      defaultTeam.members.find((member) => member.user)?.user_uuid ??
      '';

    setCreateForm((currentState) => ({
      ...currentState,
      teamUuid: defaultTeam.uuid,
      assigneeUserUuid: defaultAssignee,
    }));
  }, [manageableTeams, createForm.teamUuid]);

  const createTeam = manageableTeams.find((team) => team.uuid === createForm.teamUuid) ?? null;
  const createTeamMembers = createTeam?.members.filter((member) => member.user) ?? [];

  const filteredTasks = tasks.filter((task) => {
    if (teamFilter !== 'all' && task.team_uuid !== teamFilter) {
      return false;
    }

    if (assigneeFilter !== 'all' && task.assignee_user_uuid !== assigneeFilter) {
      return false;
    }

    if (urgencyFilter !== 'all' && getTaskUrgency(task) !== urgencyFilter) {
      return false;
    }

    const haystack = [
      task.title,
      task.description ?? '',
      task.team.name,
      task.team.project_title,
      task.assignee_user?.fio ?? '',
    ]
      .join(' ')
      .toLowerCase();

    return haystack.includes(deferredSearchValue.trim().toLowerCase());
  });

  useEffect(() => {
    if (selectedTaskUuid && !filteredTasks.some((task) => task.uuid === selectedTaskUuid)) {
      setSelectedTaskUuid(null);
    }
  }, [filteredTasks, selectedTaskUuid]);

  const selectedTask = tasks.find((task) => task.uuid === selectedTaskUuid) ?? null;
  const selectedTeam = teams.find((team) => team.uuid === selectedTask?.team_uuid) ?? null;
  const canCreateTasks = manageableTeams.length > 0;
  const canManageSelectedTask =
    !!profile &&
    !!selectedTeam &&
    (profile.role === 'admin' || selectedTeam.lead_uuid === profile.uuid);
  const isSelectedTaskAssignee =
    !!profile && !!selectedTask && selectedTask.assignee_user_uuid === profile.uuid;

  async function handleTaskMutation(
    actionKey: string,
    mutation: () => Promise<TaskResponse>,
    successMessage: string,
  ) {
    setBusyAction(actionKey);
    setNotice(null);

    try {
      const updatedTask = await mutation();

      setTasks((currentTasks) =>
        currentTasks.map((task) =>
          task.uuid === updatedTask.uuid ? updatedTask : task,
        ),
      );
      setSelectedTaskUuid(updatedTask.uuid);
      setNotice({ kind: 'success', text: successMessage });
      void loadDashboard({ silent: true });
    } catch (error) {
      setNotice({
        kind: 'error',
        text:
          error instanceof Error
            ? error.message
            : 'Не удалось выполнить действие с задачей.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!createForm.teamUuid || !createForm.assigneeUserUuid) {
      setNotice({
        kind: 'error',
        text: 'Выберите команду и исполнителя для задачи.',
      });
      return;
    }

    setBusyAction('create-task');
    setNotice(null);

    try {
      const createdTask = await createTask(accessToken, {
        team_uuid: createForm.teamUuid,
        title: createForm.title,
        description: createForm.description || null,
        assignee_user_uuid: createForm.assigneeUserUuid,
        xp_amount: Number(createForm.xpAmount),
        deadline: normalizeDateTime(createForm.deadline),
      });

      setTasks((currentTasks) => [createdTask, ...currentTasks]);
      setSelectedTaskUuid(createdTask.uuid);
      setCreateForm((currentState) => ({
        ...currentState,
        title: '',
        description: '',
        xpAmount: '100',
        deadline: '',
      }));
      setShowCreatePanel(false);
      setNotice({ kind: 'success', text: 'Задача поставлена и добавлена на доску.' });
      void loadDashboard({ silent: true });
    } catch (error) {
      setNotice({
        kind: 'error',
        text:
          error instanceof Error
            ? error.message
            : 'Не удалось создать задачу.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  const statusColumns = (Object.keys(statusMeta) as TaskStatus[]).map((status) => ({
    status,
    ...statusMeta[status],
    tasks: filteredTasks.filter((task) => task.status === status),
  }));

  if (isLoading) {
    return (
      <main className="dashboard-shell dashboard-shell--loading">
        <div className="dashboard-loading-card">
          <span className="dashboard-loading-card__badge">Workspace</span>
          <strong>Загружаем задачи, команды и уведомления...</strong>
        </div>
      </main>
    );
  }

  return (
    <main
      className={
        selectedTask ? 'dashboard-shell dashboard-shell--with-detail' : 'dashboard-shell'
      }
    >
      <aside className="dashboard-sidebar">
        <div className="workspace-card">
          <div className="workspace-card__header">
            <span className="workspace-card__badge">Task board</span>
            <button
              type="button"
              className="ghost-button"
              onClick={onLogout}
            >
              Выйти
            </button>
          </div>
          <h1>Рабочий центр команды</h1>
          <p>
            Доска задач, команды, уведомления и командный прогресс в одном
            экране.
          </p>
        </div>

        {profile ? (
          <section className="sidebar-section profile-card">
            <div className="profile-card__identity">
              <div className="profile-card__avatar">
                {profile.fio.slice(0, 1).toUpperCase()}
              </div>
              <div>
                <strong>{profile.fio}</strong>
                <span>{profile.role === 'admin' ? 'Администратор' : 'Участник'}</span>
              </div>
            </div>

            <div className="team-progress-list">
              {profile.teams.map((team) => (
                <article
                  key={team.team_uuid}
                  className="team-progress-item"
                >
                  <div className="team-progress-item__header">
                    <strong>{team.team_name}</strong>
                    <span>{team.is_team_lead ? 'Тимлид' : 'Участник'}</span>
                  </div>
                  <div className="team-progress-item__meta">
                    <span>{team.project_title}</span>
                    <span>
                      XP {team.xp_amount}
                      {team.lvl ? ` • lvl ${team.lvl.value}` : ''}
                    </span>
                  </div>
                  <div className="team-progress-item__bar">
                    <div
                      className="team-progress-item__bar-value"
                      style={{
                        width: `${Math.min(
                          100,
                          Math.round(
                            (team.xp_amount / Math.max(team.lvl?.required_xp ?? 1000, 1)) * 100,
                          ),
                        )}%`,
                      }}
                    />
                  </div>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <section className="sidebar-section">
          <div className="section-heading">
            <h2>Команды</h2>
            <span>{teams.length}</span>
          </div>
          <div className="team-list">
            {teams.map((team) => (
              <button
                key={team.uuid}
                type="button"
                className={
                  teamFilter === team.uuid
                    ? 'team-list__item team-list__item--active'
                    : 'team-list__item'
                }
                onClick={() => setTeamFilter(teamFilter === team.uuid ? 'all' : team.uuid)}
              >
                <div>
                  <strong>{team.name}</strong>
                  <span>{team.project.title}</span>
                </div>
                <span>{team.members_count}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="sidebar-section">
          <div className="section-heading">
            <h2>Уведомления</h2>
            <span>{notifications.length}</span>
          </div>
          <div className="notification-feed">
            {notifications.slice(0, 5).map((notification) => (
              <article
                key={notification.uuid}
                className="notification-feed__item"
              >
                <strong>{notification.sender_user?.fio ?? 'Система'}</strong>
                <p>{notification.content}</p>
                <span>{formatDate(notification.created_at)}</span>
              </article>
            ))}
          </div>
        </section>
      </aside>

      <section className="board-layout">
        <header className="board-header">
          <div>
            <span className="board-header__eyebrow">Главная страница</span>
            <h2>Доска задач в духе YouGile</h2>
          </div>
          <div className="board-header__actions">
            {canCreateTasks ? (
              <button
                type="button"
                className="primary-button"
                onClick={() => setShowCreatePanel((currentState) => !currentState)}
              >
                {showCreatePanel ? 'Скрыть форму' : 'Новая задача'}
              </button>
            ) : null}
            <button
              type="button"
              className="secondary-button"
              onClick={() => void loadDashboard()}
            >
              Обновить
            </button>
          </div>
        </header>

        <div className="board-filters">
          <label className="filter-field filter-field--search">
            <span>Поиск</span>
            <input
              type="search"
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
              placeholder="Название, команда, исполнитель..."
            />
          </label>

          <label className="filter-field">
            <span>Исполнитель</span>
            <select
              value={assigneeFilter}
              onChange={(event) => setAssigneeFilter(event.target.value)}
            >
              <option value="all">Все</option>
              {teams.flatMap((team) =>
                team.members
                  .filter((member) => member.user)
                  .map((member) => (
                    <option
                      key={`${team.uuid}-${member.user_uuid}`}
                      value={member.user_uuid}
                    >
                      {member.user?.fio}
                    </option>
                  )),
              )}
            </select>
          </label>

          <label className="filter-field">
            <span>Дедлайн</span>
            <select
              value={urgencyFilter}
              onChange={(event) => setUrgencyFilter(event.target.value as UrgencyFilter)}
            >
              <option value="all">Все</option>
              <option value="overdue">Просрочено</option>
              <option value="soon">Скоро дедлайн</option>
              <option value="planned">Плановые</option>
              <option value="done">Закрытые</option>
            </select>
          </label>
        </div>

        {dashboardError ? <div className="notice notice--error">{dashboardError}</div> : null}
        {notice ? <div className={`notice notice--${notice.kind}`}>{notice.text}</div> : null}

        {showCreatePanel && canCreateTasks ? (
          <section className="create-task-panel">
            <div className="section-heading">
              <h3>Постановка новой задачи</h3>
              <span>Для тимлида</span>
            </div>

            <form
              className="create-task-form"
              onSubmit={handleCreateTask}
            >
              <div className="form-grid">
                <label className="field">
                  <span>Команда</span>
                  <select
                    value={createForm.teamUuid}
                    onChange={(event) => {
                      const nextTeam =
                        manageableTeams.find((team) => team.uuid === event.target.value) ?? null;
                      const nextAssignee =
                        nextTeam?.members.find((member) => !member.is_team_lead && member.user)?.user_uuid ??
                        nextTeam?.members.find((member) => member.user)?.user_uuid ??
                        '';

                      setCreateForm((currentState) => ({
                        ...currentState,
                        teamUuid: event.target.value,
                        assigneeUserUuid: nextAssignee,
                      }));
                    }}
                  >
                    {manageableTeams.map((team) => (
                      <option
                        key={team.uuid}
                        value={team.uuid}
                      >
                        {team.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span>Исполнитель</span>
                  <select
                    value={createForm.assigneeUserUuid}
                    onChange={(event) =>
                      setCreateForm((currentState) => ({
                        ...currentState,
                        assigneeUserUuid: event.target.value,
                      }))
                    }
                  >
                    {createTeamMembers.map((member) => (
                      <option
                        key={member.user_uuid}
                        value={member.user_uuid}
                      >
                        {member.user?.fio}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="form-grid form-grid--wide">
                <label className="field">
                  <span>Название</span>
                  <input
                    type="text"
                    value={createForm.title}
                    onChange={(event) =>
                      setCreateForm((currentState) => ({
                        ...currentState,
                        title: event.target.value,
                      }))
                    }
                    placeholder="Подготовить новую доску"
                    required
                    minLength={2}
                  />
                </label>

                <label className="field">
                  <span>XP</span>
                  <input
                    type="number"
                    min={0}
                    value={createForm.xpAmount}
                    onChange={(event) =>
                      setCreateForm((currentState) => ({
                        ...currentState,
                        xpAmount: event.target.value,
                      }))
                    }
                  />
                </label>
              </div>

              <div className="form-grid form-grid--wide">
                <label className="field">
                  <span>Описание</span>
                  <textarea
                    value={createForm.description}
                    onChange={(event) =>
                      setCreateForm((currentState) => ({
                        ...currentState,
                        description: event.target.value,
                      }))
                    }
                    rows={4}
                    placeholder="Что именно нужно сделать и как понять, что задача готова?"
                  />
                </label>

                <label className="field">
                  <span>Дедлайн</span>
                  <input
                    type="datetime-local"
                    value={createForm.deadline}
                    onChange={(event) =>
                      setCreateForm((currentState) => ({
                        ...currentState,
                        deadline: event.target.value,
                      }))
                    }
                  />
                </label>
              </div>

              <button
                type="submit"
                className="primary-button"
                disabled={busyAction === 'create-task'}
              >
                {busyAction === 'create-task' ? 'Создаем...' : 'Поставить задачу'}
              </button>
            </form>
          </section>
        ) : null}

        <div className="board-columns">
          {statusColumns.map((column) => (
            <section
              key={column.status}
              className="board-column"
            >
              <header className="board-column__header">
                <div className={`status-pill ${column.tone}`}>{column.label}</div>
                <span>{column.tasks.length}</span>
              </header>

              <div className="board-column__cards">
                {column.tasks.map((task) => {
                  const urgency = getTaskUrgency(task);

                  return (
                    <button
                      key={task.uuid}
                      type="button"
                      className={
                        task.uuid === selectedTaskUuid
                          ? 'task-card task-card--active'
                          : 'task-card'
                      }
                      onClick={() =>
                        setSelectedTaskUuid((currentState) =>
                          currentState === task.uuid ? null : task.uuid,
                        )
                      }
                    >
                      <div className="task-card__header">
                        <strong>{task.title}</strong>
                        <span className={`task-card__urgency task-card__urgency--${urgency}`}>
                          {urgency === 'overdue'
                            ? 'Горит'
                            : urgency === 'soon'
                              ? 'Скоро'
                              : urgency === 'done'
                                ? 'Готово'
                                : 'План'}
                        </span>
                      </div>
                      <p>{task.description ?? 'Откройте карточку, чтобы увидеть детали.'}</p>
                      <div className="task-card__meta">
                        <span>{task.team.name}</span>
                        <span>{task.assignee_user?.fio ?? 'Без исполнителя'}</span>
                      </div>
                      <div className="task-card__footer">
                        <span>XP {task.xp_amount}</span>
                        <span>{formatDate(task.deadline)}</span>
                      </div>
                    </button>
                  );
                })}

                {!column.tasks.length ? (
                  <div className="task-empty-state">В этой колонке пока нет задач.</div>
                ) : null}
              </div>
            </section>
          ))}
        </div>
      </section>

      {selectedTask ? (
        <aside className="task-detail-panel">
          <header className="task-detail-panel__header">
            <div className="section-heading">
              <h2>Карточка задачи</h2>
              <span className={`status-pill ${statusMeta[selectedTask.status].tone}`}>
                {statusMeta[selectedTask.status].label}
              </span>
            </div>
            <button
              type="button"
              className="ghost-button"
              onClick={() => setSelectedTaskUuid(null)}
            >
              Закрыть
            </button>
          </header>

          <div className="task-detail-panel__title">
            <h3>{selectedTask.title}</h3>
            <p>{selectedTask.description ?? 'Описание пока не заполнено.'}</p>
          </div>

          <dl className="task-meta-list">
            <div>
              <dt>Команда</dt>
              <dd>{selectedTask.team.name}</dd>
            </div>
            <div>
              <dt>Проект</dt>
              <dd>{selectedTask.team.project_title}</dd>
            </div>
            <div>
              <dt>Исполнитель</dt>
              <dd>{selectedTask.assignee_user?.fio ?? 'Не назначен'}</dd>
            </div>
            <div>
              <dt>Поставил задачу</dt>
              <dd>{selectedTask.issuer_user?.fio ?? 'Система'}</dd>
            </div>
            <div>
              <dt>XP</dt>
              <dd>{selectedTask.xp_amount}</dd>
            </div>
            <div>
              <dt>Дедлайн</dt>
              <dd>{formatDate(selectedTask.deadline)}</dd>
            </div>
            <div>
              <dt>Создано</dt>
              <dd>{formatDate(selectedTask.created_at)}</dd>
            </div>
            <div>
              <dt>Обновлено</dt>
              <dd>{formatDate(selectedTask.updated_at)}</dd>
            </div>
          </dl>

          {selectedTask.assignee_team_progress ? (
            <section className="progress-card">
              <div className="section-heading">
                <h3>Командный прогресс исполнителя</h3>
                <span>
                  {selectedTask.assignee_team_progress.lvl
                    ? `lvl ${selectedTask.assignee_team_progress.lvl.value}`
                    : 'без уровня'}
                </span>
              </div>
              <div className="progress-card__row">
                <strong>{selectedTask.assignee_team_progress.xp_amount} XP</strong>
                <span>
                  Порог:
                  {' '}
                  {selectedTask.assignee_team_progress.lvl?.required_xp ?? 1000}
                </span>
              </div>
              <div className="team-progress-item__bar">
                <div
                  className="team-progress-item__bar-value"
                  style={{
                    width: `${Math.min(
                      100,
                      Math.round(
                        (selectedTask.assignee_team_progress.xp_amount /
                          Math.max(selectedTask.assignee_team_progress.lvl?.required_xp ?? 1000, 1)) *
                          100,
                      ),
                    )}%`,
                  }}
                />
              </div>
            </section>
          ) : null}

          {selectedTask.review_comment ? (
            <section className="comment-card">
              <h3>Комментарий по проверке</h3>
              <p>{selectedTask.review_comment}</p>
            </section>
          ) : null}

          <section className="task-actions">
            <div className="section-heading">
              <h3>Быстрые действия</h3>
              <span>{statusMeta[selectedTask.status].label}</span>
            </div>

            {isSelectedTaskAssignee && selectedTask.status === 'CREATED' ? (
              <button
                type="button"
                className="primary-button"
                disabled={busyAction === 'accept-task'}
                onClick={() =>
                  void handleTaskMutation(
                    'accept-task',
                    () => acceptTask(accessToken, selectedTask.uuid),
                    'Задача принята в работу.',
                  )
                }
              >
                {busyAction === 'accept-task' ? 'Принимаем...' : 'Принять в работу'}
              </button>
            ) : null}

            {isSelectedTaskAssignee && selectedTask.status === 'IN_WORK' ? (
              <button
                type="button"
                className="primary-button"
                disabled={busyAction === 'submit-review'}
                onClick={() =>
                  void handleTaskMutation(
                    'submit-review',
                    () => submitTaskForReview(accessToken, selectedTask.uuid),
                    'Задача отправлена на проверку.',
                  )
                }
              >
                {busyAction === 'submit-review'
                  ? 'Отправляем...'
                  : 'Отправить на проверку'}
              </button>
            ) : null}

            {canManageSelectedTask && selectedTask.status === 'ON_CHECK' ? (
              <>
                <button
                  type="button"
                  className="primary-button"
                  disabled={busyAction === 'approve-task'}
                  onClick={() =>
                    void handleTaskMutation(
                      'approve-task',
                      () => approveTask(accessToken, selectedTask.uuid),
                      'Задача подтверждена и закрыта.',
                    )
                  }
                >
                  {busyAction === 'approve-task' ? 'Подтверждаем...' : 'Подтвердить'}
                </button>

                <label className="field">
                  <span>Комментарий для отклонения</span>
                  <textarea
                    value={rejectComment}
                    onChange={(event) => setRejectComment(event.target.value)}
                    rows={4}
                    placeholder="Что нужно доработать?"
                  />
                </label>

                <button
                  type="button"
                  className="secondary-button"
                  disabled={busyAction === 'reject-task' || !rejectComment.trim()}
                  onClick={() =>
                    void handleTaskMutation(
                      'reject-task',
                      () => rejectTask(accessToken, selectedTask.uuid, rejectComment.trim()),
                      'Задача возвращена в работу с комментарием.',
                    )
                  }
                >
                  {busyAction === 'reject-task' ? 'Отклоняем...' : 'Отклонить'}
                </button>
              </>
            ) : null}
          </section>
        </aside>
      ) : null}
    </main>
  );
}

export default DashboardPage;
