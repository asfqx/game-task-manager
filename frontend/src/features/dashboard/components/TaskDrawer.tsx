import type { FormEvent } from 'react';

import type { TaskResponse, UserProfileResponse } from '../api/types';
import type { TaskFormState } from '../models';
import { formatDate } from '../utils';
import { AppSelect } from './AppSelect';
import { DateTimePicker } from './DateTimePicker';

type MemberOption = {
  user_uuid: string;
  user: {
    fio: string;
  } | null;
};

type TaskDrawerProps = {
  profile: UserProfileResponse | null;
  task: TaskResponse | null;
  canManageTasks: boolean;
  busyAction: string | null;
  teamMemberOptions: MemberOption[];
  taskEditForm: TaskFormState;
  rejectComment: string;
  onClose: () => void;
  onTaskEditFormChange: (updater: (current: TaskFormState) => TaskFormState) => void;
  onRejectCommentChange: (value: string) => void;
  onUpdateTask: (event: FormEvent<HTMLFormElement>) => void;
  onAcceptTask: () => void;
  onSubmitForReview: () => void;
  onManagerSubmitForReview: () => void;
  onApproveTask: () => void;
  onRejectTask: () => void;
};

export function TaskDrawer({
  profile,
  task,
  canManageTasks,
  busyAction,
  teamMemberOptions,
  taskEditForm,
  rejectComment,
  onClose,
  onTaskEditFormChange,
  onRejectCommentChange,
  onUpdateTask,
  onAcceptTask,
  onSubmitForReview,
  onManagerSubmitForReview,
  onApproveTask,
  onRejectTask,
}: TaskDrawerProps) {
  if (!task) {
    return null;
  }

  const isAssignee = !!profile && task.assignee_user_uuid === profile.uuid;

  return (
    <div className="task-drawer-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="task-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="task-drawer-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="task-drawer__header">
          <div className="task-drawer__title">
            <span className="metric-chip">{task.status}</span>
            <h3 id="task-drawer-title">{task.title}</h3>
            <p>{task.assignee_user?.fio ?? 'Без исполнителя'}</p>
          </div>
          <button type="button" className="secondary-button" onClick={onClose}>
            Закрыть
          </button>
        </div>

        <div className="task-drawer__body">
          <div className="task-drawer__meta-grid">
            <div className="task-drawer__meta-card">
              <span>Статус</span>
              <strong>{task.status}</strong>
            </div>
            <div className="task-drawer__meta-card">
              <span>XP</span>
              <strong>{task.xp_amount}</strong>
            </div>
            <div className="task-drawer__meta-card">
              <span>Дедлайн</span>
              <strong>{formatDate(task.deadline)}</strong>
            </div>
            <div className="task-drawer__meta-card">
              <span>Команда</span>
              <strong>{task.team.name}</strong>
            </div>
          </div>

          <div className="task-drawer__description">
            <span>Описание</span>
            <p>{task.description ?? 'Описание задачи пока не заполнено.'}</p>
          </div>

          {task.review_comment ? (
            <div className="task-drawer__description task-drawer__description--comment">
              <span>Комментарий тимлида</span>
              <p>{task.review_comment}</p>
            </div>
          ) : null}

          {canManageTasks ? (
            <form className="workspace-form" onSubmit={onUpdateTask}>
              <div className="form-grid">
                <label className="field">
                  <span>Название</span>
                  <input
                    type="text"
                    value={taskEditForm.title}
                    onChange={(event) =>
                      onTaskEditFormChange((current) => ({
                        ...current,
                        title: event.target.value,
                      }))
                    }
                    required
                  />
                </label>
                <div className="field">
                  <span>Исполнитель</span>
                  <AppSelect
                    value={taskEditForm.assigneeUserUuid}
                    onChange={(value) =>
                      onTaskEditFormChange((current) => ({
                        ...current,
                        assigneeUserUuid: value,
                      }))
                    }
                    options={teamMemberOptions.map((member) => ({
                      value: member.user_uuid,
                      label: member.user?.fio ?? 'Без имени',
                    }))}
                  />
                </div>
              </div>
              <div className="form-grid">
                <label className="field">
                  <span>XP</span>
                  <input
                    type="number"
                    min={0}
                    value={taskEditForm.xpAmount}
                    onChange={(event) =>
                      onTaskEditFormChange((current) => ({
                        ...current,
                        xpAmount: event.target.value,
                      }))
                    }
                  />
                </label>
                <div className="field">
                  <span>Дедлайн</span>
                  <DateTimePicker
                    value={taskEditForm.deadline}
                    onChange={(value) =>
                      onTaskEditFormChange((current) => ({
                        ...current,
                        deadline: value,
                      }))
                    }
                  />
                </div>
              </div>
              <label className="field">
                <span>Описание</span>
                <textarea
                  value={taskEditForm.description}
                  onChange={(event) =>
                    onTaskEditFormChange((current) => ({
                      ...current,
                      description: event.target.value,
                    }))
                  }
                  rows={3}
                />
              </label>
              <button type="submit" className="primary-button" disabled={busyAction === 'update-task'}>
                {busyAction === 'update-task' ? 'Сохраняем...' : 'Сохранить задачу'}
              </button>
            </form>
          ) : null}

          <div className="task-detail-actions">
            {isAssignee && task.status === 'CREATED' ? (
              <button
                type="button"
                className="primary-button"
                onClick={onAcceptTask}
                disabled={busyAction === 'accept-task'}
              >
                Принять в работу
              </button>
            ) : null}

            {isAssignee && task.status === 'IN_WORK' ? (
              <button
                type="button"
                className="primary-button"
                onClick={onSubmitForReview}
                disabled={busyAction === 'submit-review'}
              >
                Отправить на проверку
              </button>
            ) : null}

            {canManageTasks && task.status === 'IN_WORK' ? (
              <button
                type="button"
                className="secondary-button"
                onClick={onManagerSubmitForReview}
                disabled={busyAction === 'submit-review'}
              >
                Взять на проверку
              </button>
            ) : null}

            {canManageTasks && (task.status === 'ON_CHECK' || task.status === 'IN_WORK') ? (
              <button
                type="button"
                className="primary-button"
                onClick={onApproveTask}
                disabled={busyAction === 'approve-task'}
              >
                Отметить выполненной
              </button>
            ) : null}

            {canManageTasks && task.status === 'ON_CHECK' ? (
              <div className="workspace-form">
                <label className="field">
                  <span>Комментарий</span>
                  <textarea
                    value={rejectComment}
                    onChange={(event) => onRejectCommentChange(event.target.value)}
                    rows={3}
                  />
                </label>
                <button
                  type="button"
                  className="secondary-button secondary-button--danger"
                  onClick={onRejectTask}
                  disabled={busyAction === 'reject-task'}
                >
                  Вернуть на доработку
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </aside>
    </div>
  );
}
