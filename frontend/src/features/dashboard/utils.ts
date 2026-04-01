import type { ProjectDetailResponse, TaskStatus, TeamResponse } from './api/types';
import type { ParticipantEntry } from './models';

export function formatDate(value: string | null): string {
  if (!value) return 'Не задано';

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export function normalizeDateTime(value: string): string | null {
  return value ? new Date(value).toISOString() : null;
}

export function formatTaskStatusLabel(status: TaskStatus): string {
  switch (status) {
    case 'CREATED':
      return 'Бэклог';
    case 'IN_WORK':
      return 'В работе';
    case 'ON_CHECK':
      return 'На проверке';
    case 'DONE':
      return 'Выполнено';
    default:
      return status;
  }
}

export function resolveAvatarUrl(avatarUrl: string | null): string | null {
  if (!avatarUrl) {
    return null;
  }

  if (/^https?:\/\//i.test(avatarUrl)) {
    return avatarUrl;
  }

  const encodedPath = avatarUrl
    .split('/')
    .map((part) => encodeURIComponent(part))
    .join('/');

  const protocol = typeof window !== 'undefined' ? window.location.protocol : 'http:';
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

  return `${protocol}//${hostname}:9000/avatars/${encodedPath}`;
}

export function extractAvatarObjectName(uploadUrl: string): string {
  const url = new URL(uploadUrl);
  const path = decodeURIComponent(url.pathname);
  const marker = '/avatars/';
  const markerIndex = path.indexOf(marker);

  if (markerIndex === -1) {
    throw new Error('Не удалось определить путь к загруженному аватару.');
  }

  return path.slice(markerIndex + marker.length);
}

export function buildTeamParticipants(team: TeamResponse): ParticipantEntry[] {
  const entries = new Map<string, ParticipantEntry>();

  if (team.lead && team.lead_uuid) {
    entries.set(team.lead_uuid, {
      uuid: team.lead_uuid,
      fio: team.lead.fio,
      username: team.lead.username,
      avatarUrl: resolveAvatarUrl(team.lead.avatar_url ?? null),
      roleLabel: 'Тимлид',
      meta: team.project.title,
    });
  }

  for (const member of team.members) {
    if (!member.user) continue;
    const existing = entries.get(member.user_uuid);

    entries.set(member.user_uuid, {
      uuid: member.user_uuid,
      fio: member.user.fio,
      username: member.user.username,
      avatarUrl: resolveAvatarUrl(member.user.avatar_url ?? null),
      roleLabel: member.is_team_lead ? 'Тимлид' : 'Участник',
      meta: member.lvl
        ? `Уровень ${member.lvl.value} · XP ${member.xp_amount}`
        : `XP ${member.xp_amount}`,
    });

    if (existing && existing.roleLabel === 'Тимлид') {
      entries.set(member.user_uuid, {
        ...entries.get(member.user_uuid)!,
        roleLabel: 'Тимлид',
      });
    }
  }

  return Array.from(entries.values()).sort((left, right) =>
    left.fio.localeCompare(right.fio, 'ru'),
  );
}

export function buildProjectParticipants(
  project: ProjectDetailResponse,
  teams: TeamResponse[],
): ParticipantEntry[] {
  const entries = new Map<string, ParticipantEntry>();

  if (project.creator) {
    entries.set(project.creator_uuid, {
      uuid: project.creator_uuid,
      fio: project.creator.fio,
      username: project.creator.username,
      avatarUrl: resolveAvatarUrl(project.creator.avatar_url ?? null),
      roleLabel: 'Владелец проекта',
      meta: project.title,
    });
  }

  for (const team of teams) {
    for (const participant of buildTeamParticipants(team)) {
      const existing = entries.get(participant.uuid);

      if (!existing) {
        entries.set(participant.uuid, {
          ...participant,
          meta: team.name,
        });
        continue;
      }

      const roleLabel =
        existing.roleLabel === 'Владелец проекта' ||
        existing.roleLabel === 'Тимлид' ||
        participant.roleLabel !== 'Тимлид'
          ? existing.roleLabel
          : 'Тимлид';

      const metaParts = new Set(
        [existing.meta, team.name]
          .flatMap((value) => value.split(' · '))
          .filter(Boolean),
      );

      entries.set(participant.uuid, {
        ...existing,
        roleLabel,
        meta: Array.from(metaParts).join(' · '),
      });
    }
  }

  return Array.from(entries.values()).sort((left, right) =>
    left.fio.localeCompare(right.fio, 'ru'),
  );
}
