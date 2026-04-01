import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';

import type { LvlResponse, UserProfileResponse, UserTeamSummaryResponse } from '../api/types';
import { AvatarImage } from './AvatarImage';
import { formatDate, resolveAvatarUrl } from '../utils';

type ProfileFormState = {
  fio: string;
  username: string;
  email: string;
  telegram: string;
  phone_number: string;
};

type PasswordResetFormState = {
  email: string;
  token: string;
  newPassword: string;
};

type UserProfileDrawerProps = {
  profile: UserProfileResponse | null;
  isLoading: boolean;
  isOwnProfile: boolean;
  onClose: () => void;
  onSaveProfile: (payload: ProfileFormState) => Promise<void>;
  onUploadAvatar: (file: File) => Promise<void>;
  onLoadLevels: () => Promise<LvlResponse[]>;
  onRequestPasswordReset: (email: string) => Promise<void>;
  onConfirmPasswordReset: (payload: PasswordResetFormState) => Promise<void>;
};

type TeamProgressItem = UserTeamSummaryResponse & {
  nextLevel: LvlResponse | null;
  progressPercent: number;
};

const emptyProfileForm: ProfileFormState = {
  fio: '',
  username: '',
  email: '',
  telegram: '',
  phone_number: '',
};

const emptyPasswordResetForm: PasswordResetFormState = {
  email: '',
  token: '',
  newPassword: '',
};

export function UserProfileDrawer({
  profile,
  isLoading,
  isOwnProfile,
  onClose,
  onSaveProfile,
  onUploadAvatar,
  onLoadLevels,
  onRequestPasswordReset,
  onConfirmPasswordReset,
}: UserProfileDrawerProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [isLevelsOpen, setIsLevelsOpen] = useState(false);
  const [isLevelsLoading, setIsLevelsLoading] = useState(false);
  const [isPasswordResetOpen, setIsPasswordResetOpen] = useState(false);
  const [isRequestingPasswordCode, setIsRequestingPasswordCode] = useState(false);
  const [isConfirmingPasswordReset, setIsConfirmingPasswordReset] = useState(false);
  const [levels, setLevels] = useState<LvlResponse[]>([]);
  const [form, setForm] = useState<ProfileFormState>(emptyProfileForm);
  const [passwordResetForm, setPasswordResetForm] = useState<PasswordResetFormState>(emptyPasswordResetForm);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [successText, setSuccessText] = useState<string | null>(null);

  useEffect(() => {
    if (!profile) {
      setForm(emptyProfileForm);
      setPasswordResetForm(emptyPasswordResetForm);
      setIsEditing(false);
      setIsPasswordResetOpen(false);
      setErrorText(null);
      setSuccessText(null);
      return;
    }

    setForm({
      fio: profile.fio ?? '',
      username: profile.username ?? '',
      email: profile.email ?? '',
      telegram: profile.telegram ?? '',
      phone_number: profile.phone_number ?? '',
    });
    setPasswordResetForm({
      email: profile.email ?? '',
      token: '',
      newPassword: '',
    });
    setIsEditing(false);
    setIsPasswordResetOpen(false);
    setErrorText(null);
    setSuccessText(null);
  }, [profile]);

  useEffect(() => {
    if (!profile?.teams.length || levels.length || isLevelsLoading) {
      return;
    }

    let cancelled = false;

    void (async () => {
      setIsLevelsLoading(true);
      try {
        const nextLevels = await onLoadLevels();
        if (!cancelled) {
          setLevels(nextLevels);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorText(error instanceof Error ? error.message : 'Не удалось загрузить уровни.');
        }
      } finally {
        if (!cancelled) {
          setIsLevelsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isLevelsLoading, levels.length, onLoadLevels, profile]);

  const avatarUrl = profile ? resolveAvatarUrl(profile.avatar_url) : null;
  const sortedLevels = useMemo(
    () => [...levels].sort((left, right) => left.required_xp - right.required_xp),
    [levels],
  );

  const primaryProgress = useMemo(() => {
    if (!profile?.teams.length) {
      return null;
    }

    return [...profile.teams].sort((left, right) => {
      const leftLevelXp = left.lvl?.required_xp ?? -1;
      const rightLevelXp = right.lvl?.required_xp ?? -1;
      if (rightLevelXp !== leftLevelXp) {
        return rightLevelXp - leftLevelXp;
      }

      return right.xp_amount - left.xp_amount;
    })[0];
  }, [profile]);

  const teamProgressItems = useMemo<TeamProgressItem[]>(() => {
    if (!profile?.teams.length) {
      return [];
    }

    return profile.teams.map((team) => {
      const hasLevelScale = sortedLevels.length > 0;
      const nextLevel = hasLevelScale && team.lvl
        ? sortedLevels.find((level) => level.required_xp > team.lvl.required_xp) ?? null
        : null;

      const progressPercent = (() => {
        if (!hasLevelScale) {
          return team.lvl ? 0 : Math.max(0, Math.min(100, team.xp_amount));
        }

        if (!team.lvl) {
          return Math.max(0, Math.min(100, team.xp_amount));
        }

        if (!nextLevel) {
          return 100;
        }

        const baseXp = team.lvl.required_xp;
        const rangeXp = Math.max(nextLevel.required_xp - baseXp, 1);
        return Math.max(0, Math.min(100, ((team.xp_amount - baseXp) / rangeXp) * 100));
      })();

      return {
        ...team,
        nextLevel,
        progressPercent,
      };
    });
  }, [profile, sortedLevels]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setErrorText(null);
    setSuccessText(null);

    try {
      await onSaveProfile(form);
      setIsEditing(false);
      setSuccessText('Профиль сохранён.');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : 'Не удалось сохранить профиль.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAvatarChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';

    if (!file) {
      return;
    }

    setIsUploadingAvatar(true);
    setErrorText(null);
    setSuccessText(null);

    try {
      await onUploadAvatar(file);
      setSuccessText('Аватар обновлён.');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : 'Не удалось загрузить аватар.');
    } finally {
      setIsUploadingAvatar(false);
    }
  }

  async function handleOpenLevels() {
    setIsLevelsOpen((current) => !current);

    if (levels.length || isLevelsOpen) {
      return;
    }

    setIsLevelsLoading(true);
    try {
      setLevels(await onLoadLevels());
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : 'Не удалось загрузить уровни.');
    } finally {
      setIsLevelsLoading(false);
    }
  }

  async function handlePasswordResetRequest() {
    if (!passwordResetForm.email.trim()) {
      setErrorText('Укажите email для отправки кода.');
      setSuccessText(null);
      return;
    }

    setIsRequestingPasswordCode(true);
    setErrorText(null);
    setSuccessText(null);

    try {
      await onRequestPasswordReset(passwordResetForm.email.trim());
      setSuccessText('Код для смены пароля отправлен на почту.');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : 'Не удалось отправить код.');
    } finally {
      setIsRequestingPasswordCode(false);
    }
  }

  async function handlePasswordResetConfirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsConfirmingPasswordReset(true);
    setErrorText(null);
    setSuccessText(null);

    try {
      await onConfirmPasswordReset({
        email: passwordResetForm.email.trim(),
        token: passwordResetForm.token.trim(),
        newPassword: passwordResetForm.newPassword,
      });
      setPasswordResetForm((current) => ({
        ...current,
        token: '',
        newPassword: '',
      }));
      setIsPasswordResetOpen(false);
      setSuccessText('Пароль успешно обновлён.');
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : 'Не удалось обновить пароль.');
    } finally {
      setIsConfirmingPasswordReset(false);
    }
  }

  if (!profile && !isLoading) {
    return null;
  }

  return (
    <div className="profile-drawer-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="profile-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-profile-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="profile-drawer__header">
          <div className="profile-drawer__title">
            <span className="metric-chip">
              {isOwnProfile ? 'Мой профиль' : profile?.role === 'admin' ? 'Администратор' : 'Профиль участника'}
            </span>
            <h3 id="user-profile-title">{profile?.fio ?? 'Загружаем профиль...'}</h3>
            <p>{profile ? `@${profile.username}` : 'Подтягиваем данные пользователя'}</p>
          </div>
          <div className="profile-drawer__header-actions">
            {isOwnProfile && profile ? (
              <>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setIsPasswordResetOpen((current) => !current);
                    setErrorText(null);
                    setSuccessText(null);
                  }}
                >
                  {isPasswordResetOpen ? 'Скрыть смену пароля' : 'Изменить пароль'}
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setIsEditing((current) => !current);
                    setErrorText(null);
                    setSuccessText(null);
                  }}
                >
                  {isEditing ? 'Отменить' : 'Редактировать'}
                </button>
              </>
            ) : null}
            <button type="button" className="secondary-button" onClick={onClose}>
              Закрыть
            </button>
          </div>
        </div>

        <div className="profile-drawer__body">
          {isLoading && !profile ? (
            <div className="profile-drawer__empty">Загружаем профиль пользователя...</div>
          ) : profile ? (
            <>
              <section className="profile-hero-card">
                <div className="profile-hero-card__avatar-wrap">
                  <AvatarImage
                    src={avatarUrl}
                    alt={profile.fio}
                    fallbackText={profile.fio.slice(0, 1).toUpperCase()}
                    imageClassName="profile-hero-card__avatar-image"
                    fallbackClassName="profile-hero-card__avatar-fallback"
                  />
                  {isOwnProfile ? (
                    <label className="profile-hero-card__upload-button">
                      {isUploadingAvatar ? 'Загружаем...' : 'Изменить аватар'}
                      <input type="file" accept="image/*" hidden onChange={handleAvatarChange} />
                    </label>
                  ) : null}
                </div>

                <div className="profile-hero-card__info">
                  <strong>{profile.fio}</strong>
                  <span>@{profile.username}</span>
                  <span>{profile.email}</span>
                  {profile.telegram ? <span>Telegram: {profile.telegram}</span> : null}
                  {profile.phone_number ? <span>Телефон: {profile.phone_number}</span> : null}
                </div>
              </section>

              <section className="profile-level-card">
                <div className="profile-level-card__header">
                  <div>
                    <span>Прогресс по командам</span>
                    <strong>
                      {primaryProgress?.lvl
                        ? `Максимальный уровень ${primaryProgress.lvl.value}`
                        : 'Уровни по командам'}
                    </strong>
                  </div>
                  <button type="button" className="secondary-button" onClick={() => void handleOpenLevels()}>
                    {isLevelsOpen ? 'Скрыть уровни' : 'Посмотреть все уровни'}
                  </button>
                </div>

                {teamProgressItems.length ? (
                  <div className="profile-level-card__team-list">
                    {teamProgressItems.map((team) => (
                      <article key={team.team_uuid} className="profile-level-card__team-item">
                        <div className="profile-level-card__team-header">
                          <div>
                            <strong>{team.team_name}</strong>
                            <span>{team.project_title}</span>
                          </div>
                          <strong className="profile-level-card__team-level">
                            {team.lvl ? `Уровень ${team.lvl.value}` : 'Без уровня'}
                          </strong>
                        </div>
                        <div className="profile-level-card__progress">
                          <div className="profile-level-card__progress-bar">
                            <div
                              className="profile-level-card__progress-value"
                              style={{ width: `${team.progressPercent}%` }}
                            />
                          </div>
                          <div className="profile-level-card__progress-meta">
                            <span>{`XP ${team.xp_amount}`}</span>
                            <span>
                              {!sortedLevels.length
                                ? 'Шкала уровней загружается'
                                : team.nextLevel
                                ? `До уровня ${team.nextLevel.value}: ${Math.max(team.nextLevel.required_xp - team.xp_amount, 0)} XP`
                                : team.lvl
                                  ? 'Максимальный уровень'
                                  : 'Уровень не назначен'}
                            </span>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="profile-drawer__empty">Пользователь пока не состоит в командах.</div>
                )}

                {isLevelsOpen ? (
                  <div className="profile-level-card__levels">
                    {isLevelsLoading ? (
                      <div className="profile-drawer__empty">Загружаем уровни...</div>
                    ) : sortedLevels.length ? (
                      sortedLevels.map((level) => (
                        <article
                          key={level.uuid}
                          className={`profile-level-card__level-item${primaryProgress?.lvl?.uuid === level.uuid ? ' is-current' : ''}`}
                        >
                          <strong>{level.value}</strong>
                          <span>{level.required_xp} XP</span>
                        </article>
                      ))
                    ) : (
                      <div className="profile-drawer__empty">Список уровней пока пуст.</div>
                    )}
                  </div>
                ) : null}
              </section>

              {isOwnProfile && isPasswordResetOpen ? (
                <form className="workspace-form profile-password-card" onSubmit={handlePasswordResetConfirm}>
                  <div className="section-heading">
                    <h3>Смена пароля</h3>
                  </div>
                  <label className="field">
                    <span>Email</span>
                    <input
                      type="email"
                      value={passwordResetForm.email}
                      onChange={(event) =>
                        setPasswordResetForm((current) => ({ ...current, email: event.target.value }))
                      }
                      required
                    />
                  </label>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => void handlePasswordResetRequest()}
                    disabled={isRequestingPasswordCode}
                  >
                    {isRequestingPasswordCode ? 'Отправляем код...' : 'Получить код'}
                  </button>
                  <div className="form-grid">
                    <label className="field">
                      <span>Код из письма</span>
                      <input
                        type="text"
                        value={passwordResetForm.token}
                        onChange={(event) =>
                          setPasswordResetForm((current) => ({ ...current, token: event.target.value }))
                        }
                        required
                      />
                    </label>
                    <label className="field">
                      <span>Новый пароль</span>
                      <input
                        type="password"
                        value={passwordResetForm.newPassword}
                        onChange={(event) =>
                          setPasswordResetForm((current) => ({ ...current, newPassword: event.target.value }))
                        }
                        minLength={6}
                        required
                      />
                    </label>
                  </div>
                  <button type="submit" className="primary-button" disabled={isConfirmingPasswordReset}>
                    {isConfirmingPasswordReset ? 'Сохраняем пароль...' : 'Сохранить новый пароль'}
                  </button>
                </form>
              ) : null}

              {isOwnProfile && isEditing ? (
                <form className="workspace-form" onSubmit={handleSubmit}>
                  <div className="form-grid">
                    <label className="field">
                      <span>ФИО</span>
                      <input
                        type="text"
                        value={form.fio}
                        onChange={(event) => setForm((current) => ({ ...current, fio: event.target.value }))}
                        required
                      />
                    </label>
                    <label className="field">
                      <span>Username</span>
                      <input
                        type="text"
                        value={form.username}
                        onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
                        required
                      />
                    </label>
                  </div>
                  <div className="form-grid">
                    <label className="field">
                      <span>Email</span>
                      <input
                        type="email"
                        value={form.email}
                        onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                        required
                      />
                    </label>
                    <label className="field">
                      <span>Telegram</span>
                      <input
                        type="text"
                        value={form.telegram}
                        onChange={(event) => setForm((current) => ({ ...current, telegram: event.target.value }))}
                      />
                    </label>
                  </div>
                  <label className="field">
                    <span>Телефон</span>
                    <input
                      type="text"
                      value={form.phone_number}
                      onChange={(event) => setForm((current) => ({ ...current, phone_number: event.target.value }))}
                    />
                  </label>
                  <button type="submit" className="primary-button" disabled={isSaving}>
                    {isSaving ? 'Сохраняем...' : 'Сохранить профиль'}
                  </button>
                </form>
              ) : null}

              {successText ? <div className="notice notice--success">{successText}</div> : null}
              {errorText ? <div className="notice notice--error">{errorText}</div> : null}

              <div className="profile-drawer__meta-grid">
                <div className="profile-drawer__meta-card">
                  <span>Статус</span>
                  <strong>{profile.status}</strong>
                </div>
                <div className="profile-drawer__meta-card">
                  <span>Команд</span>
                  <strong>{profile.teams.length}</strong>
                </div>
                <div className="profile-drawer__meta-card">
                  <span>Выполнено задач</span>
                  <strong>{profile.completed_tasks.length}</strong>
                </div>
                <div className="profile-drawer__meta-card">
                  <span>Последний вход</span>
                  <strong>{formatDate(profile.last_login_at)}</strong>
                </div>
              </div>

              <section className="profile-drawer__section">
                <div className="section-heading">
                  <h3>Команды</h3>
                  <span>{profile.teams.length}</span>
                </div>
                {profile.teams.length ? (
                  <div className="profile-drawer__list">
                    {profile.teams.map((team) => (
                      <article key={team.team_uuid} className="profile-drawer__list-card">
                        <div>
                          <strong>{team.team_name}</strong>
                          <span>{team.project_title}</span>
                        </div>
                        <div className="profile-drawer__list-meta">
                          <span>{team.is_team_lead ? 'Тимлид' : 'Участник'}</span>
                          <span>{team.lvl ? `Уровень ${team.lvl.value}` : 'Без уровня'}</span>
                          <span>XP {team.xp_amount}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="profile-drawer__empty">Пользователь пока не состоит в командах.</div>
                )}
              </section>

              <section className="profile-drawer__section">
                <div className="section-heading">
                  <h3>Выполненные задачи</h3>
                  <span>{profile.completed_tasks.length}</span>
                </div>
                {profile.completed_tasks.length ? (
                  <div className="profile-drawer__list">
                    {profile.completed_tasks.map((task) => (
                      <article key={task.task_uuid} className="profile-drawer__list-card">
                        <div>
                          <strong>{task.title}</strong>
                          <span>
                            {task.project_title} · {task.team_name}
                          </span>
                        </div>
                        <div className="profile-drawer__list-meta">
                          <span>XP {task.xp_amount}</span>
                          <span>{formatDate(task.completed_at)}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="profile-drawer__empty">У пользователя пока нет завершённых задач.</div>
                )}
              </section>
            </>
          ) : null}
        </div>
      </aside>
    </div>
  );
}
