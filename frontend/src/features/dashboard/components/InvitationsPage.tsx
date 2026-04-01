import type { FormEvent } from 'react';

import type { InvitationResponse, TeamResponse, UserProfileResponse } from '../api/types';
import { formatDate } from '../utils';
import { AppSelect } from './AppSelect';

type InvitationsPageProps = {
  profile: UserProfileResponse | null;
  teams: TeamResponse[];
  invitations: InvitationResponse[];
  inviteTeamUuid: string;
  inviteRecipientLogin: string;
  busyAction: string | null;
  onInviteTeamUuidChange: (value: string) => void;
  onInviteRecipientLoginChange: (value: string) => void;
  onCreateInvitation: (event: FormEvent<HTMLFormElement>) => void;
  onAcceptInvitation: (invitationUuid: string) => void;
  onRejectInvitation: (invitationUuid: string) => void;
};

export function InvitationsPage({
  profile,
  teams,
  invitations,
  inviteTeamUuid,
  inviteRecipientLogin,
  busyAction,
  onInviteTeamUuidChange,
  onInviteRecipientLoginChange,
  onCreateInvitation,
  onAcceptInvitation,
  onRejectInvitation,
}: InvitationsPageProps) {
  const incomingInvitations = invitations.filter(
    (invitation) => invitation.recipient_user_uuid === profile?.uuid,
  );
  const outgoingInvitations = invitations.filter(
    (invitation) => invitation.sender_user_uuid === profile?.uuid,
  );

  return (
    <section className="workspace-panel invitations-page">
      <div className="project-summary-card project-summary-card--project">
        <div className="project-summary-card__content">
          <span className="board-header__eyebrow">Приглашения</span>
          <strong>Приглашения в команды</strong>
          <p>Здесь можно отправлять приглашения по email или username и обрабатывать входящие запросы.</p>
        </div>
      </div>

      <section className="workspace-panel workspace-panel--nested">
        <div className="section-heading">
          <h3>Отправить приглашение</h3>
        </div>
        <form className="workspace-form" onSubmit={onCreateInvitation}>
          <div className="form-grid">
            <div className="field">
              <span>Команда</span>
              <AppSelect
                value={inviteTeamUuid}
                onChange={onInviteTeamUuidChange}
                placeholder="Выберите команду"
                options={[
                  { value: '', label: 'Выберите команду' },
                  ...teams.map((team) => ({
                    value: team.uuid,
                    label: `${team.project.title} · ${team.name}`,
                  })),
                ]}
              />
            </div>
            <label className="field">
              <span>Email или username</span>
              <input
                type="text"
                value={inviteRecipientLogin}
                onChange={(event) => onInviteRecipientLoginChange(event.target.value)}
                placeholder="user@example.com или username"
                required
              />
            </label>
          </div>
          <button type="submit" className="primary-button" disabled={busyAction === 'create-invitation'}>
            {busyAction === 'create-invitation' ? 'Отправляем...' : 'Отправить приглашение'}
          </button>
        </form>
      </section>

      <div className="workspace-grid">
        <section className="workspace-panel workspace-panel--nested">
          <div className="section-heading">
            <h3>Входящие</h3>
            <span>{incomingInvitations.length}</span>
          </div>
          <div className="invitation-list">
            {incomingInvitations.length ? (
              incomingInvitations.map((invitation) => (
                <article key={invitation.uuid} className="invitation-card">
                  <div className="invitation-card__header">
                    <div>
                      <strong>{invitation.team.name}</strong>
                      <span>{invitation.project.title}</span>
                    </div>
                    <span className={`metric-chip invitation-status invitation-status--${invitation.status.toLowerCase()}`}>
                      {invitation.status}
                    </span>
                  </div>
                  <p>
                    От {invitation.sender_user?.fio ?? invitation.sender_user?.username ?? 'Системы'}
                  </p>
                  <span className="invitation-card__date">{formatDate(invitation.created_at)}</span>
                  {invitation.status === 'WAITING' ? (
                    <div className="invitation-card__actions">
                      <button
                        type="button"
                        className="primary-button"
                        onClick={() => onAcceptInvitation(invitation.uuid)}
                        disabled={busyAction === `accept-invitation-${invitation.uuid}`}
                      >
                        Принять
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => onRejectInvitation(invitation.uuid)}
                        disabled={busyAction === `reject-invitation-${invitation.uuid}`}
                      >
                        Отклонить
                      </button>
                    </div>
                  ) : null}
                </article>
              ))
            ) : (
              <div className="task-empty-state">Пока нет входящих приглашений.</div>
            )}
          </div>
        </section>

        <section className="workspace-panel workspace-panel--nested">
          <div className="section-heading">
            <h3>Отправленные</h3>
            <span>{outgoingInvitations.length}</span>
          </div>
          <div className="invitation-list">
            {outgoingInvitations.length ? (
              outgoingInvitations.map((invitation) => (
                <article key={invitation.uuid} className="invitation-card">
                  <div className="invitation-card__header">
                    <div>
                      <strong>{invitation.team.name}</strong>
                      <span>{invitation.project.title}</span>
                    </div>
                    <span className={`metric-chip invitation-status invitation-status--${invitation.status.toLowerCase()}`}>
                      {invitation.status}
                    </span>
                  </div>
                  <p>{invitation.team.description ?? 'Описание команды пока не заполнено.'}</p>
                  <span className="invitation-card__date">
                    {formatDate(invitation.resolved_at ?? invitation.created_at)}
                  </span>
                </article>
              ))
            ) : (
              <div className="task-empty-state">Пока нет отправленных приглашений.</div>
            )}
          </div>
        </section>
      </div>
    </section>
  );
}
