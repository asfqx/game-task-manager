import type { PropsWithChildren, ReactNode } from 'react';

type ModalShellProps = PropsWithChildren<{
  titleId: string;
  eyebrow: string;
  title: string;
  subtitle?: string;
  sizeClassName?: string;
  onClose: () => void;
  actions?: ReactNode;
}>;

export function ModalShell({
  titleId,
  eyebrow,
  title,
  subtitle,
  sizeClassName,
  onClose,
  actions,
  children,
}: ModalShellProps) {
  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className={sizeClassName ? `modal-card ${sizeClassName}` : 'modal-card'}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-card__header">
          <div>
            <span className="board-header__eyebrow">{eyebrow}</span>
            <h3 id={titleId}>{title}</h3>
            {subtitle ? <p className="modal-card__subtitle">{subtitle}</p> : null}
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            Закрыть
          </button>
        </div>
        {children}
        {actions}
      </div>
    </div>
  );
}
