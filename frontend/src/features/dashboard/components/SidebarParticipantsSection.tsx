import type { ParticipantEntry } from '../models';
import { AvatarImage } from './AvatarImage';

type SidebarParticipantsSectionProps = {
  title: string;
  subtitle: string;
  participants: ParticipantEntry[];
  isLoading: boolean;
  onParticipantClick: (userUuid: string) => void;
};

export function SidebarParticipantsSection({
  title,
  subtitle,
  participants,
  isLoading,
  onParticipantClick,
}: SidebarParticipantsSectionProps) {
  return (
    <section className="sidebar-section">
      <div className="section-heading">
        <h2>{title}</h2>
        <span>{participants.length}</span>
      </div>
      <p className="sidebar-section__subtitle">{subtitle}</p>
      <div className="sidebar-participants">
        {isLoading ? (
          <div className="sidebar-participants__empty">Загружаем участников...</div>
        ) : participants.length ? (
          participants.map((participant) => (
            <button
              key={participant.uuid}
              type="button"
              className="sidebar-participant-card"
              onClick={() => onParticipantClick(participant.uuid)}
            >
              <AvatarImage
                src={participant.avatarUrl}
                alt={participant.fio}
                fallbackText={participant.fio.charAt(0).toUpperCase() || '?'}
                imageClassName="participant-avatar"
                fallbackClassName="participant-avatar participant-avatar--fallback"
              />
              <div className="sidebar-participant-card__content">
                <div className="sidebar-participant-card__identity">
                  <strong>{participant.fio}</strong>
                </div>
              </div>
            </button>
          ))
        ) : (
          <div className="sidebar-participants__empty">Участники не найдены.</div>
        )}
      </div>
    </section>
  );
}
