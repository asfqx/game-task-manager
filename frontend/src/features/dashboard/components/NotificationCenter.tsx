import type { NotificationResponse } from '../api/types';
import type { NotificationToast } from '../models';
import { formatDate } from '../utils';

type NotificationCenterProps = {
  notifications: NotificationResponse[];
  toasts: NotificationToast[];
  isPanelOpen: boolean;
  onOpenPanel: () => void;
  onClosePanel: () => void;
  onDismissToast: (toastUuid: string) => void;
};

export function NotificationCenter({
  notifications,
  toasts,
  isPanelOpen,
  onOpenPanel,
  onClosePanel,
  onDismissToast,
}: NotificationCenterProps) {
  return (
    <>
      <button
        type="button"
        className="notification-fab"
        aria-label="Открыть уведомления"
        onClick={onOpenPanel}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M12 3.75a4.5 4.5 0 0 0-4.5 4.5v2.12c0 .77-.2 1.52-.57 2.2l-1.1 1.98a1.5 1.5 0 0 0 1.31 2.23h9.72a1.5 1.5 0 0 0 1.31-2.23l-1.1-1.98a4.6 4.6 0 0 1-.57-2.2V8.25a4.5 4.5 0 0 0-4.5-4.5Zm-2.25 15a2.25 2.25 0 0 0 4.5 0"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {notifications.length ? (
          <span className="notification-fab__badge">{notifications.length}</span>
        ) : null}
      </button>

      {toasts.length ? (
        <div className="notification-toast-stack" aria-live="polite" aria-atomic="false">
          {toasts.map((toast) => (
            <article key={toast.uuid} className="notification-toast">
              <div className="notification-toast__header">
                <strong>{toast.senderLabel}</strong>
                <button
                  type="button"
                  className="notification-toast__close"
                  onClick={() => onDismissToast(toast.uuid)}
                >
                  Закрыть
                </button>
              </div>
              <p>{toast.content}</p>
              <span>{formatDate(toast.createdAt)}</span>
            </article>
          ))}
        </div>
      ) : null}

      {isPanelOpen ? (
        <div className="notification-panel-backdrop" role="presentation" onClick={onClosePanel}>
          <aside
            className="notification-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="notification-panel-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="notification-panel__header">
              <div>
                <h3 id="notification-panel-title">Все уведомления</h3>
              </div>
              <button type="button" className="secondary-button" onClick={onClosePanel}>
                Закрыть
              </button>
            </div>
            <div className="notification-feed notification-feed--panel">
              {notifications.length ? (
                notifications.map((notification) => (
                  <article key={notification.uuid} className="notification-feed__item">
                    <strong>{notification.sender_user?.fio ?? 'Система'}</strong>
                    <p>{notification.content}</p>
                    <span>{formatDate(notification.created_at)}</span>
                  </article>
                ))
              ) : (
                <div className="notification-feed__empty">У вас нет уведомлений</div>
              )}
            </div>
          </aside>
        </div>
      ) : null}
    </>
  );
}
