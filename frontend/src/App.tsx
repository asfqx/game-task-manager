import { type FormEvent, useEffect, useState } from 'react';

import {
  checkRole,
  confirmEmail,
  confirmPasswordReset,
  loginUser,
  requestEmailConfirmation,
  requestPasswordReset,
  registerUser,
} from './api/auth';
import DashboardPage from './dashboard/DashboardPage';

type AuthMode = 'login' | 'register';
type RegisterStep = 'form' | 'confirm';
type ResetStep = 'request' | 'confirm';

type Notice = {
  kind: 'success' | 'error' | 'info';
  text: string;
} | null;

type SessionState = {
  accessToken: string;
  role: string | null;
};

const ACCESS_TOKEN_KEY = 'task-manager.access-token';
const ROLE_KEY = 'task-manager.user-role';
const DASHBOARD_PATH = '/dashboard';

const heroHighlights = [
  {
    value: 'Одна лента работы',
    label: 'Задачи, команды и прогресс собираются в одном аккуратном пространстве.',
  },
  {
    value: 'XP и рост',
    label: 'Каждая закрытая задача двигает личный и командный прогресс вперед.',
  },
  {
    value: 'Мягкий фокус',
    label: 'Светлый минималистичный интерфейс без перегруженных экранов и шума.',
  },
];

function normalizeFlow(value: string | null): 'login' | 'register' | 'confirm' | 'reset' | null {
  if (!value) {
    return null;
  }

  const normalized = value.trim().toLowerCase();

  if (normalized === 'login' || normalized === 'signin') {
    return 'login';
  }

  if (normalized === 'register' || normalized === 'signup') {
    return 'register';
  }

  if (
    normalized === 'confirm' ||
    normalized === 'confirm-email' ||
    normalized === 'confirmemail' ||
    normalized === 'email-confirm'
  ) {
    return 'confirm';
  }

  if (
    normalized === 'reset' ||
    normalized === 'reset-password' ||
    normalized === 'resetpassword' ||
    normalized === 'password-reset'
  ) {
    return 'reset';
  }

  return null;
}

function readSearchParams(): URLSearchParams {
  return new URLSearchParams(window.location.search);
}

function readInitialEmail(): string {
  const searchParams = readSearchParams();
  return searchParams.get('email') ?? '';
}

function readInitialToken(): string {
  const searchParams = readSearchParams();
  return searchParams.get('token') ?? searchParams.get('code') ?? '';
}

function resolveInitialAuthMode(): AuthMode {
  const searchParams = readSearchParams();
  const flow =
    normalizeFlow(searchParams.get('mode')) ??
    normalizeFlow(searchParams.get('flow')) ??
    normalizeFlow(searchParams.get('tab'));

  if (flow === 'register' || flow === 'confirm') {
    return 'register';
  }

  return 'login';
}

function resolveInitialRegisterStep(initialToken: string): RegisterStep {
  const searchParams = readSearchParams();
  const flow =
    normalizeFlow(searchParams.get('mode')) ??
    normalizeFlow(searchParams.get('flow')) ??
    normalizeFlow(searchParams.get('tab'));

  if (flow === 'confirm' || !!initialToken) {
    return 'confirm';
  }

  return 'form';
}

function resolveInitialResetState(initialToken: string): {
  isOpen: boolean;
  step: ResetStep;
} {
  const searchParams = readSearchParams();
  const flow =
    normalizeFlow(searchParams.get('mode')) ??
    normalizeFlow(searchParams.get('flow')) ??
    normalizeFlow(searchParams.get('tab'));

  if (flow === 'reset') {
    return {
      isOpen: true,
      step: initialToken ? 'confirm' : 'request',
    };
  }

  return {
    isOpen: false,
    step: 'request',
  };
}

function App() {
  const initialEmail = readInitialEmail();
  const initialToken = readInitialToken();
  const initialResetState = resolveInitialResetState(initialToken);

  const [mode, setMode] = useState<AuthMode>(resolveInitialAuthMode);
  const [registerStep, setRegisterStep] = useState<RegisterStep>(
    resolveInitialRegisterStep(initialToken),
  );
  const [showPasswordReset, setShowPasswordReset] = useState(initialResetState.isOpen);
  const [passwordResetStep, setPasswordResetStep] = useState<ResetStep>(initialResetState.step);
  const [notice, setNotice] = useState<Notice>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [session, setSession] = useState<SessionState | null>(null);

  const [loginForm, setLoginForm] = useState({
    login: initialEmail,
    password: '',
  });
  const [registerForm, setRegisterForm] = useState({
    email: initialEmail,
    username: '',
    fio: '',
    password: '',
  });
  const [emailConfirmForm, setEmailConfirmForm] = useState({
    email: initialEmail,
    token: initialToken,
  });
  const [passwordResetRequestForm, setPasswordResetRequestForm] = useState({
    email: initialEmail,
  });
  const [passwordResetConfirmForm, setPasswordResetConfirmForm] = useState({
    email: initialEmail,
    token: initialToken,
    newPassword: '',
  });

  useEffect(() => {
    const storedAccessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const storedRole = localStorage.getItem(ROLE_KEY);

    if (!storedAccessToken) {
      return;
    }

    setSession({
      accessToken: storedAccessToken,
      role: storedRole,
    });

    void (async () => {
      try {
        const roleResponse = await checkRole(storedAccessToken);
        setSession({
          accessToken: storedAccessToken,
          role: roleResponse.role,
        });
        localStorage.setItem(ROLE_KEY, roleResponse.role);
      } catch {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(ROLE_KEY);
        setSession(null);
      }
    })();
  }, []);

  useEffect(() => {
    const searchParams = readSearchParams();
    let hasChanges = false;

    for (const key of ['mode', 'flow', 'tab']) {
      if (searchParams.has(key)) {
        searchParams.delete(key);
        hasChanges = true;
      }
    }

    if (!hasChanges) {
      return;
    }

    const nextSearch = searchParams.toString();
    window.history.replaceState(null, '', nextSearch ? `${window.location.pathname}?${nextSearch}` : window.location.pathname);
  }, [mode, passwordResetStep, registerStep, showPasswordReset]);

  useEffect(() => {
    if (!session) {
      return;
    }

    if (!window.location.pathname.startsWith(DASHBOARD_PATH)) {
      window.history.replaceState(null, '', DASHBOARD_PATH);
    }
  }, [session]);

  function clearLocalSession() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    setSession(null);
    window.history.replaceState(null, '', '/');
  }

  function switchMode(nextMode: AuthMode) {
    setNotice(null);
    setMode(nextMode);

    if (nextMode === 'login') {
      setRegisterStep('form');
    }
  }

  function openPasswordReset() {
    setNotice(null);
    setShowPasswordReset(true);
  }

  function closePasswordReset() {
    setShowPasswordReset(false);
    setPasswordResetStep('request');
    setPasswordResetConfirmForm((currentState) => ({
      ...currentState,
      token: '',
      newPassword: '',
    }));
  }

  async function handleLoginSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction('login');
    setNotice(null);

    try {
      const tokenPair = await loginUser(loginForm);
      const roleResponse = await checkRole(tokenPair.access_token);

      localStorage.setItem(ACCESS_TOKEN_KEY, tokenPair.access_token);
      localStorage.setItem(ROLE_KEY, roleResponse.role);

      setSession({
        accessToken: tokenPair.access_token,
        role: roleResponse.role,
      });
      window.history.replaceState(null, '', DASHBOARD_PATH);
    } catch (error) {
      setNotice({
        kind: 'error',
        text:
          error instanceof Error
            ? error.message
            : 'Не удалось выполнить вход.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRegisterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction('register');
    setNotice(null);

    try {
      await registerUser({
        ...registerForm,
        role: 'user',
      });

      setEmailConfirmForm({
        email: registerForm.email,
        token: '',
      });
      setPasswordResetRequestForm({ email: registerForm.email });
      setPasswordResetConfirmForm((currentState) => ({
        ...currentState,
        email: registerForm.email,
      }));
      setRegisterStep('confirm');
      setNotice({
        kind: 'success',
        text: 'Аккаунт создан. Теперь подтвердите почту кодом из письма.',
      });
    } catch (error) {
      setNotice({
        kind: 'error',
        text:
          error instanceof Error
            ? error.message
            : 'Не удалось завершить регистрацию.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleEmailConfirmSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction('email-confirm');
    setNotice(null);

    try {
      await confirmEmail(emailConfirmForm.email, emailConfirmForm.token);
      setLoginForm((currentState) => ({
        ...currentState,
        login: emailConfirmForm.email,
      }));
      setMode('login');
      setRegisterStep('form');
      setNotice({
        kind: 'success',
        text: 'Почта подтверждена. Теперь можно войти по email и паролю.',
      });
    } catch (error) {
      setNotice({
        kind: 'error',
        text:
          error instanceof Error
            ? error.message
            : 'Не удалось подтвердить почту.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handleEmailResend() {
    setBusyAction('email-resend');
    setNotice(null);

    try {
      await requestEmailConfirmation(emailConfirmForm.email);
      setNotice({
        kind: 'info',
        text: 'Новый код подтверждения отправлен на почту.',
      });
    } catch (error) {
      setNotice({
        kind: 'error',
        text:
          error instanceof Error
            ? error.message
            : 'Не удалось отправить код подтверждения.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePasswordResetRequestSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setBusyAction('password-reset-request');
    setNotice(null);

    try {
      await requestPasswordReset(passwordResetRequestForm.email);
      setPasswordResetConfirmForm((currentState) => ({
        ...currentState,
        email: passwordResetRequestForm.email,
      }));
      setPasswordResetStep('confirm');
      setShowPasswordReset(true);
      setNotice({
        kind: 'success',
        text: 'Код для сброса отправлен. Введите его и задайте новый пароль.',
      });
    } catch (error) {
      setNotice({
        kind: 'error',
        text:
          error instanceof Error
            ? error.message
            : 'Не удалось запросить сброс пароля.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePasswordResetConfirmSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setBusyAction('password-reset-confirm');
    setNotice(null);

    try {
      await confirmPasswordReset(
        passwordResetConfirmForm.email,
        passwordResetConfirmForm.token,
        passwordResetConfirmForm.newPassword,
      );
      setLoginForm((currentState) => ({
        ...currentState,
        login: passwordResetConfirmForm.email,
      }));
      setPasswordResetConfirmForm((currentState) => ({
        ...currentState,
        token: '',
        newPassword: '',
      }));
      setPasswordResetStep('request');
      setShowPasswordReset(false);
      setMode('login');
      setNotice({
        kind: 'success',
        text: 'Пароль обновлен. Теперь можно войти с новыми данными.',
      });
    } catch (error) {
      setNotice({
        kind: 'error',
        text:
          error instanceof Error
            ? error.message
            : 'Не удалось обновить пароль.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  if (session) {
    return (
      <DashboardPage
        accessToken={session.accessToken}
        onLogout={clearLocalSession}
      />
    );
  }

  return (
    <main className="page-shell">
      <div className="page-glow page-glow-left" />
      <div className="page-glow page-glow-right" />

      <section className="hero-panel">
        <div className="hero-panel__content">
          <div className="hero-panel__intro">
            <div className="hero-badge">Task Manager • Focus XP Loop</div>
            <div>
              <h1>Задачи, команды и рост в одном понятном рабочем ритме.</h1>
              <p className="hero-copy">
                Светлый вход в систему для таск-менеджера с мягкой геймификацией:
                доска задач, уровни, опыт, уведомления и чистый фокус без визуальной
                перегрузки.
              </p>
            </div>
          </div>

          <div className="hero-progress-card">
            <div className="hero-progress-card__header">
              <span>Прогресс сезона</span>
              <strong>720 / 1000 XP</strong>
            </div>
            <div className="hero-progress-bar">
              <div className="hero-progress-bar__value" />
            </div>
            <div className="hero-progress-card__footer">
              <span>Следующий рубеж: Team Level 4</span>
              <span>+280 XP</span>
            </div>
          </div>

          <div className="hero-stats">
            {heroHighlights.map((item) => (
              <article
                key={item.value}
                className="hero-stat"
              >
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel__header">
          <div>
            <span className="eyebrow">Доступ в систему</span>
            <h2>
              {mode === 'login'
                ? 'Вход в рабочее пространство'
                : registerStep === 'confirm'
                  ? 'Подтверждение почты'
                  : 'Регистрация нового участника'}
            </h2>
          </div>
          <p>
            Регистрация идет через подтверждение почты. После создания аккаунта
            откроется шаг с вводом кода из письма.
          </p>
        </div>

        <div className="auth-tabs auth-tabs--compact">
          <button
            type="button"
            className={mode === 'login' ? 'auth-tab auth-tab--active' : 'auth-tab'}
            onClick={() => switchMode('login')}
          >
            Вход
          </button>
          <button
            type="button"
            className={mode === 'register' ? 'auth-tab auth-tab--active' : 'auth-tab'}
            onClick={() => switchMode('register')}
          >
            Регистрация
          </button>
        </div>

        {notice ? (
          <div className={`notice notice--${notice.kind}`}>{notice.text}</div>
        ) : null}

        {mode === 'login' ? (
          <form
            className="auth-form"
            onSubmit={handleLoginSubmit}
          >
            <label className="field">
              <span>Email или username</span>
              <input
                type="text"
                value={loginForm.login}
                onChange={(event) =>
                  setLoginForm((currentState) => ({
                    ...currentState,
                    login: event.target.value,
                  }))
                }
                placeholder="ivan.petrov@company.ru"
                required
                minLength={3}
              />
            </label>

            <label className="field">
              <span>Пароль</span>
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) =>
                  setLoginForm((currentState) => ({
                    ...currentState,
                    password: event.target.value,
                  }))
                }
                placeholder="Не меньше 8 символов"
                required
                minLength={8}
              />
            </label>

            <button
              type="submit"
              className="primary-button"
              disabled={busyAction === 'login'}
            >
              {busyAction === 'login' ? 'Входим...' : 'Войти'}
            </button>
          </form>
        ) : null}

        {mode === 'register' && registerStep === 'form' ? (
          <form
            className="auth-form"
            onSubmit={handleRegisterSubmit}
          >
            <label className="field">
              <span>ФИО</span>
              <input
                type="text"
                value={registerForm.fio}
                onChange={(event) =>
                  setRegisterForm((currentState) => ({
                    ...currentState,
                    fio: event.target.value,
                  }))
                }
                placeholder="Иван Петров"
                required
                minLength={5}
              />
            </label>

            <div className="form-grid">
              <label className="field">
                <span>Email</span>
                <input
                  type="email"
                  value={registerForm.email}
                  onChange={(event) =>
                    setRegisterForm((currentState) => ({
                      ...currentState,
                      email: event.target.value,
                    }))
                  }
                  placeholder="ivan.petrov@company.ru"
                  required
                />
              </label>

              <label className="field">
                <span>Username</span>
                <input
                  type="text"
                  value={registerForm.username}
                  onChange={(event) =>
                    setRegisterForm((currentState) => ({
                      ...currentState,
                      username: event.target.value,
                    }))
                  }
                  placeholder="ivan.petrov"
                  required
                  minLength={3}
                  maxLength={50}
                />
              </label>
            </div>

            <label className="field">
              <span>Пароль</span>
              <input
                type="password"
                value={registerForm.password}
                onChange={(event) =>
                  setRegisterForm((currentState) => ({
                    ...currentState,
                    password: event.target.value,
                  }))
                }
                placeholder="Минимум 8 символов"
                required
                minLength={8}
              />
            </label>

            <button
              type="submit"
              className="primary-button"
              disabled={busyAction === 'register'}
            >
              {busyAction === 'register' ? 'Создаем аккаунт...' : 'Продолжить'}
            </button>

            <div className="form-footnote">
              <span>После отправки формы откроется подтверждение почты.</span>
              <button
                type="button"
                className="inline-action"
                onClick={() => setRegisterStep('confirm')}
              >
                Уже есть код подтверждения
              </button>
            </div>
          </form>
        ) : null}

        {mode === 'register' && registerStep === 'confirm' ? (
          <form
            className="auth-form auth-form--confirmation"
            onSubmit={handleEmailConfirmSubmit}
          >
            <div className="support-card">
              <strong>Подтвердите регистрацию</strong>
              <span>
                Введите email и код из письма. Если письмо потерялось, можно
                отправить код повторно.
              </span>
            </div>

            <label className="field">
              <span>Email</span>
              <input
                type="email"
                value={emailConfirmForm.email}
                onChange={(event) =>
                  setEmailConfirmForm((currentState) => ({
                    ...currentState,
                    email: event.target.value,
                  }))
                }
                placeholder="ivan.petrov@company.ru"
                required
              />
            </label>

            <label className="field">
              <span>Код из письма</span>
              <input
                type="text"
                value={emailConfirmForm.token}
                onChange={(event) =>
                  setEmailConfirmForm((currentState) => ({
                    ...currentState,
                    token: event.target.value,
                  }))
                }
                placeholder="Введите код подтверждения"
                required
              />
            </label>

            <div className="form-actions">
              <button
                type="submit"
                className="primary-button"
                disabled={busyAction === 'email-confirm'}
              >
                {busyAction === 'email-confirm' ? 'Подтверждаем...' : 'Подтвердить почту'}
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={busyAction === 'email-resend'}
                onClick={() => void handleEmailResend()}
              >
                {busyAction === 'email-resend' ? 'Отправляем...' : 'Отправить код снова'}
              </button>
            </div>

            <div className="form-footnote">
              <button
                type="button"
                className="inline-action"
                onClick={() => setRegisterStep('form')}
              >
                Вернуться к регистрации
              </button>
            </div>
          </form>
        ) : null}

        <div className="auth-panel__footer">
          <button
            type="button"
            className="inline-action auth-panel__reset-toggle"
            onClick={() => {
              if (showPasswordReset) {
                closePasswordReset();
                return;
              }

              openPasswordReset();
            }}
          >
            {showPasswordReset ? 'Скрыть восстановление пароля' : 'Забыли пароль?'}
          </button>

          {showPasswordReset ? (
            <div className="auth-reset-card">
              {passwordResetStep === 'request' ? (
                <form
                  className="auth-form auth-form--reset"
                  onSubmit={handlePasswordResetRequestSubmit}
                >
                  <label className="field">
                    <span>Email</span>
                    <input
                      type="email"
                      value={passwordResetRequestForm.email}
                      onChange={(event) =>
                        setPasswordResetRequestForm({ email: event.target.value })
                      }
                      placeholder="ivan.petrov@company.ru"
                      required
                    />
                  </label>

                  <button
                    type="submit"
                    className="secondary-button"
                    disabled={busyAction === 'password-reset-request'}
                  >
                    {busyAction === 'password-reset-request'
                      ? 'Отправляем код...'
                      : 'Получить код сброса'}
                  </button>
                </form>
              ) : (
                <form
                  className="auth-form auth-form--reset"
                  onSubmit={handlePasswordResetConfirmSubmit}
                >
                  <label className="field">
                    <span>Email</span>
                    <input
                      type="email"
                      value={passwordResetConfirmForm.email}
                      onChange={(event) =>
                        setPasswordResetConfirmForm((currentState) => ({
                          ...currentState,
                          email: event.target.value,
                        }))
                      }
                      placeholder="ivan.petrov@company.ru"
                      required
                    />
                  </label>

                  <label className="field">
                    <span>Код из письма</span>
                    <input
                      type="text"
                      value={passwordResetConfirmForm.token}
                      onChange={(event) =>
                        setPasswordResetConfirmForm((currentState) => ({
                          ...currentState,
                          token: event.target.value,
                        }))
                      }
                      placeholder="Введите код сброса"
                      required
                    />
                  </label>

                  <label className="field">
                    <span>Новый пароль</span>
                    <input
                      type="password"
                      value={passwordResetConfirmForm.newPassword}
                      onChange={(event) =>
                        setPasswordResetConfirmForm((currentState) => ({
                          ...currentState,
                          newPassword: event.target.value,
                        }))
                      }
                      placeholder="Минимум 8 символов"
                      required
                      minLength={8}
                    />
                  </label>

                  <div className="form-actions">
                    <button
                      type="submit"
                      className="primary-button"
                      disabled={busyAction === 'password-reset-confirm'}
                    >
                      {busyAction === 'password-reset-confirm'
                        ? 'Сохраняем...'
                        : 'Обновить пароль'}
                    </button>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => setPasswordResetStep('request')}
                    >
                      Запросить код заново
                    </button>
                  </div>
                </form>
              )}
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}

export default App;
