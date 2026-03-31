const FALLBACK_API_BASE_URL = 'http://localhost:8000/api/v1';

const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? FALLBACK_API_BASE_URL;

export type TaskStatus = 'CREATED' | 'IN_WORK' | 'ON_CHECK' | 'DONE';

export type UserShortResponse = {
  uuid: string;
  username: string;
  fio: string;
};

export type LvlSummaryResponse = {
  uuid: string;
  value: string;
  required_xp: number;
};

export type UserTeamSummaryResponse = {
  team_uuid: string;
  team_name: string;
  project_uuid: string;
  project_title: string;
  is_team_lead: boolean;
  xp_amount: number;
  lvl_uuid: string | null;
  lvl: LvlSummaryResponse | null;
};

export type UserProfileResponse = {
  uuid: string;
  email: string;
  username: string;
  fio: string;
  role: string;
  status: string;
  avatar_url: string | null;
  telegram: string | null;
  phone_number: string | null;
  created_at: string | null;
  updated_at: string | null;
  last_login_at: string | null;
  teams: UserTeamSummaryResponse[];
};

export type TeamMemberResponse = {
  uuid: string;
  user_uuid: string;
  user: UserShortResponse | null;
  added_by_uuid: string | null;
  added_by: UserShortResponse | null;
  lvl_uuid: string | null;
  lvl: LvlSummaryResponse | null;
  xp_amount: number;
  joined_at: string;
  is_team_lead: boolean;
};

export type TeamResponse = {
  uuid: string;
  project_uuid: string;
  project: {
    uuid: string;
    title: string;
  };
  name: string;
  description: string | null;
  lead_uuid: string | null;
  lead: UserShortResponse | null;
  created_by_uuid: string | null;
  created_by: UserShortResponse | null;
  members_count: number;
  members: TeamMemberResponse[];
  created_at: string;
  updated_at: string;
};

export type TaskResponse = {
  uuid: string;
  team_uuid: string;
  team: {
    uuid: string;
    name: string;
    project_uuid: string;
    project_title: string;
  };
  issuer_user_uuid: string | null;
  issuer_user: UserShortResponse | null;
  assignee_user_uuid: string | null;
  assignee_user: UserShortResponse | null;
  title: string;
  description: string | null;
  review_comment: string | null;
  xp_amount: number;
  status: TaskStatus;
  deadline: string | null;
  accepted_at: string | null;
  submitted_for_review_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  assignee_team_progress: {
    xp_amount: number;
    lvl_uuid: string | null;
    lvl: LvlSummaryResponse | null;
  } | null;
};

export type NotificationResponse = {
  uuid: string;
  content: string;
  recipient_user_uuid: string | null;
  recipient_user: UserShortResponse | null;
  sender_user_uuid: string | null;
  sender_user: UserShortResponse | null;
  created_at: string;
};

export type CreateTaskPayload = {
  team_uuid: string;
  title: string;
  description: string | null;
  assignee_user_uuid: string;
  xp_amount: number;
  deadline: string | null;
};

export type UpdateTaskPayload = {
  title?: string;
  description?: string | null;
  assignee_user_uuid?: string;
  xp_amount?: number;
  deadline?: string | null;
};

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  query?: Record<string, string | undefined>;
  body?: unknown;
};

function createUrl(
  path: string,
  query?: Record<string, string | undefined>,
): string {
  const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value) {
        url.searchParams.set(key, value);
      }
    });
  }

  return url.toString();
}

async function readApiError(response: Response): Promise<string> {
  const fallbackMessage = `Ошибка ${response.status}`;

  try {
    const data = (await response.json()) as {
      detail?: unknown;
      message?: unknown;
    };

    return formatApiErrorDetail(data.detail ?? data.message) ?? fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

function formatApiErrorDetail(detail: unknown): string | null {
  if (!detail) {
    return null;
  }

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => formatApiErrorDetail(item))
      .filter((item): item is string => !!item);

    return parts.length ? parts.join('; ') : null;
  }

  if (typeof detail === 'object') {
    const record = detail as Record<string, unknown>;

    if (typeof record.msg === 'string') {
      const location =
        Array.isArray(record.loc) && record.loc.length
          ? `${record.loc.join('.')}: `
          : '';

      return `${location}${record.msg}`;
    }

    if (typeof record.detail === 'string') {
      return record.detail;
    }

    const parts = Object.values(record)
      .map((item) => formatApiErrorDetail(item))
      .filter((item): item is string => !!item);

    return parts.length ? parts.join('; ') : JSON.stringify(record);
  }

  return String(detail);
}

async function authorizedRequest<T>(
  accessToken: string,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${accessToken}`,
  };

  if (options.body) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(createUrl(path, options.query), {
    method: options.method ?? 'GET',
    credentials: 'include',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type');
  if (!contentType || !contentType.includes('application/json')) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function getProfile(accessToken: string): Promise<UserProfileResponse> {
  return authorizedRequest<UserProfileResponse>(accessToken, '/users/me/');
}

export function getTeams(accessToken: string): Promise<TeamResponse[]> {
  return authorizedRequest<TeamResponse[]>(accessToken, '/teams/');
}

export function getTasks(accessToken: string): Promise<TaskResponse[]> {
  return authorizedRequest<TaskResponse[]>(accessToken, '/tasks/');
}

export function getNotifications(
  accessToken: string,
): Promise<NotificationResponse[]> {
  return authorizedRequest<NotificationResponse[]>(accessToken, '/notifications/');
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

export function acceptTask(
  accessToken: string,
  taskUuid: string,
): Promise<TaskResponse> {
  return authorizedRequest<TaskResponse>(accessToken, `/tasks/${taskUuid}/accept`, {
    method: 'POST',
  });
}

export function submitTaskForReview(
  accessToken: string,
  taskUuid: string,
): Promise<TaskResponse> {
  return authorizedRequest<TaskResponse>(
    accessToken,
    `/tasks/${taskUuid}/submit-for-review`,
    {
      method: 'POST',
    },
  );
}

export function approveTask(
  accessToken: string,
  taskUuid: string,
): Promise<TaskResponse> {
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
    body: {
      review_comment: reviewComment,
    },
  });
}
