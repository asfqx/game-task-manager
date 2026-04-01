import { authorizedRequest, createApiUrl, readApiError } from '../../../shared/api/http';
import type {
  CreatePreSignedURLResponse,
  CreateInvitationPayload,
  InvitationResponse,
  CreateProjectPayload,
  CreateTaskPayload,
  CreateTeamPayload,
  LvlResponse,
  NotificationResponse,
  ProjectDetailResponse,
  ProjectResponse,
  TaskResponse,
  TeamResponse,
  XpAccrualLogResponse,
  UpdateTaskPayload,
  UpdateTeamPayload,
  UpdateUserProfilePayload,
  UpdateUserProfileResponse,
  UserProfileResponse,
  UserShortResponse,
} from './types';

export function getProfile(accessToken: string): Promise<UserProfileResponse> {
  return authorizedRequest<UserProfileResponse>(accessToken, '/users/me/');
}

export function getLvls(accessToken: string): Promise<LvlResponse[]> {
  return authorizedRequest<LvlResponse[]>(accessToken, '/lvls/');
}

export function updateMyProfile(
  accessToken: string,
  payload: UpdateUserProfilePayload,
): Promise<UpdateUserProfileResponse> {
  return authorizedRequest<UpdateUserProfileResponse>(accessToken, '/users/me/', {
    method: 'PATCH',
    body: payload,
  });
}

export function getMyAvatarUploadUrl(
  accessToken: string,
): Promise<CreatePreSignedURLResponse> {
  return authorizedRequest<CreatePreSignedURLResponse>(accessToken, '/users/me/avatar/upload-url');
}

export async function uploadAvatarFile(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Content-Type': file.type || 'image/png',
    },
    body: file,
  });

  if (!response.ok) {
    throw new Error(`Не удалось загрузить аватар (${response.status})`);
  }
}

export function getUserProfileByUuid(
  accessToken: string,
  userUuid: string,
): Promise<UserProfileResponse> {
  return authorizedRequest<UserProfileResponse>(accessToken, `/users/${userUuid}`);
}

export function getProjects(accessToken: string): Promise<ProjectResponse[]> {
  return authorizedRequest<ProjectResponse[]>(accessToken, '/projects/');
}

export function getProject(
  accessToken: string,
  projectUuid: string,
): Promise<ProjectDetailResponse> {
  return authorizedRequest<ProjectDetailResponse>(accessToken, `/projects/${projectUuid}`);
}

export function createProject(
  accessToken: string,
  payload: CreateProjectPayload,
): Promise<ProjectDetailResponse> {
  return authorizedRequest<ProjectDetailResponse>(accessToken, '/projects/', {
    method: 'POST',
    body: payload,
  });
}

export function deleteProject(accessToken: string, projectUuid: string): Promise<void> {
  return authorizedRequest<void>(accessToken, `/projects/${projectUuid}`, {
    method: 'DELETE',
  });
}

export function leaveProject(accessToken: string, projectUuid: string): Promise<void> {
  return authorizedRequest<void>(accessToken, `/projects/${projectUuid}/leave`, {
    method: 'POST',
  });
}

export function getTeam(accessToken: string, teamUuid: string): Promise<TeamResponse> {
  return authorizedRequest<TeamResponse>(accessToken, `/teams/${teamUuid}`);
}

export function getTeams(accessToken: string): Promise<TeamResponse[]> {
  return authorizedRequest<TeamResponse[]>(accessToken, '/teams/');
}

export function createTeam(
  accessToken: string,
  payload: CreateTeamPayload,
): Promise<TeamResponse> {
  return authorizedRequest<TeamResponse>(accessToken, '/teams/', {
    method: 'POST',
    body: payload,
  });
}

export function updateTeam(
  accessToken: string,
  teamUuid: string,
  payload: UpdateTeamPayload,
): Promise<TeamResponse> {
  return authorizedRequest<TeamResponse>(accessToken, `/teams/${teamUuid}`, {
    method: 'PATCH',
    body: payload,
  });
}

export function addTeamMember(
  accessToken: string,
  teamUuid: string,
  userUuid: string,
): Promise<TeamResponse> {
  return authorizedRequest<TeamResponse>(accessToken, `/teams/${teamUuid}/members`, {
    method: 'POST',
    body: { user_uuid: userUuid },
  });
}

export function removeTeamMember(
  accessToken: string,
  teamUuid: string,
  userUuid: string,
): Promise<void> {
  return authorizedRequest<void>(accessToken, `/teams/${teamUuid}/members/${userUuid}`, {
    method: 'DELETE',
  });
}

export function leaveTeam(accessToken: string, teamUuid: string): Promise<void> {
  return authorizedRequest<void>(accessToken, `/teams/${teamUuid}/leave`, {
    method: 'POST',
  });
}

export function getTasks(
  accessToken: string,
  teamUuid?: string,
): Promise<TaskResponse[]> {
  return authorizedRequest<TaskResponse[]>(accessToken, '/tasks/', {
    query: { team_uuid: teamUuid },
  });
}

export function getNotifications(accessToken: string): Promise<NotificationResponse[]> {
  return authorizedRequest<NotificationResponse[]>(accessToken, '/notifications/');
}

export function getXpAccrualLogs(
  accessToken: string,
  projectUuid?: string,
): Promise<XpAccrualLogResponse[]> {
  return authorizedRequest<XpAccrualLogResponse[]>(accessToken, '/system-logging/xp/', {
    query: { limit: '200' },
  }).then((logs) =>
    projectUuid
      ? logs.filter((log) => log.task?.project_uuid === projectUuid)
      : logs,
  );
}

export function getInvitations(accessToken: string): Promise<InvitationResponse[]> {
  return authorizedRequest<InvitationResponse[]>(accessToken, '/invitations/');
}

export function createInvitation(
  accessToken: string,
  payload: CreateInvitationPayload,
): Promise<InvitationResponse> {
  return authorizedRequest<InvitationResponse>(accessToken, '/invitations/', {
    method: 'POST',
    body: payload,
  });
}

export function acceptInvitation(
  accessToken: string,
  invitationUuid: string,
): Promise<InvitationResponse> {
  return authorizedRequest<InvitationResponse>(accessToken, `/invitations/${invitationUuid}/accept`, {
    method: 'POST',
  });
}

export function rejectInvitation(
  accessToken: string,
  invitationUuid: string,
): Promise<InvitationResponse> {
  return authorizedRequest<InvitationResponse>(accessToken, `/invitations/${invitationUuid}/reject`, {
    method: 'POST',
  });
}

type NotificationStreamHandlers = {
  onNotification: (notification: NotificationResponse) => void;
  onError?: (error: Error) => void;
};

function parseSseEvent(chunk: string): { event: string; data: string } | null {
  const lines = chunk
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    return null;
  }

  const event = lines.find((line) => line.startsWith('event:'))?.slice(6).trim() ?? 'message';
  const data = lines
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trim())
    .join('\n');

  return data ? { event, data } : null;
}

export function subscribeToNotificationStream(
  accessToken: string,
  handlers: NotificationStreamHandlers,
): () => void {
  const controller = new AbortController();
  const decoder = new TextDecoder();
  let reconnectTimer: number | null = null;
  let closed = false;

  const connect = async () => {
    try {
      const response = await fetch(createApiUrl('/notifications/stream'), {
        method: 'GET',
        credentials: 'include',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: 'text/event-stream',
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(await readApiError(response));
      }

      if (!response.body) {
        throw new Error('Поток уведомлений недоступен.');
      }

      const reader = response.body.getReader();
      let buffer = '';

      while (!closed) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split(/\r?\n\r?\n/);
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          const event = parseSseEvent(part);
          if (!event || event.event !== 'notification') {
            continue;
          }

          const payload = JSON.parse(event.data) as {
            notification?: NotificationResponse;
          };

          if (payload.notification) {
            handlers.onNotification(payload.notification);
          }
        }
      }
    } catch (error) {
      if (closed || controller.signal.aborted) {
        return;
      }

      handlers.onError?.(
        error instanceof Error ? error : new Error('Не удалось подключить поток уведомлений.'),
      );
    }

    if (!closed) {
      reconnectTimer = window.setTimeout(() => {
        void connect();
      }, 3000);
    }
  };

  void connect();

  return () => {
    closed = true;
    controller.abort();
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer);
    }
  };
}

export function searchUsers(
  accessToken: string,
  query: string,
): Promise<UserShortResponse[]> {
  return authorizedRequest<UserShortResponse[]>(accessToken, '/users/directory', {
    query: { q: query.trim() || undefined },
  });
}

export function createTask(
  accessToken: string,
  payload: CreateTaskPayload,
): Promise<TaskResponse> {
  return authorizedRequest<TaskResponse>(accessToken, '/tasks/', {
    method: 'POST',
    body: payload,
  });
}

export function updateTask(
  accessToken: string,
  taskUuid: string,
  payload: UpdateTaskPayload,
): Promise<TaskResponse> {
  return authorizedRequest<TaskResponse>(accessToken, `/tasks/${taskUuid}`, {
    method: 'PATCH',
    body: payload,
  });
}

export function acceptTask(accessToken: string, taskUuid: string): Promise<TaskResponse> {
  return authorizedRequest<TaskResponse>(accessToken, `/tasks/${taskUuid}/accept`, {
    method: 'POST',
  });
}

export function submitTaskForReview(
  accessToken: string,
  taskUuid: string,
): Promise<TaskResponse> {
  return authorizedRequest<TaskResponse>(accessToken, `/tasks/${taskUuid}/submit-for-review`, {
    method: 'POST',
  });
}

export function approveTask(accessToken: string, taskUuid: string): Promise<TaskResponse> {
  return authorizedRequest<TaskResponse>(accessToken, `/tasks/${taskUuid}/approve`, {
    method: 'POST',
  });
}

export function rejectTask(
  accessToken: string,
  taskUuid: string,
  reviewComment: string,
): Promise<TaskResponse> {
  return authorizedRequest<TaskResponse>(accessToken, `/tasks/${taskUuid}/reject`, {
    method: 'POST',
    body: { review_comment: reviewComment },
  });
}
