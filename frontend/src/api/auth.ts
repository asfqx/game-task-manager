const FALLBACK_AUTH_API_BASE_URL = 'http://localhost:8000/api/v1/auth';

const AUTH_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ??
  FALLBACK_AUTH_API_BASE_URL;

export type RegisterPayload = {
  email: string;
  username: string;
  password: string;
  fio: string;
  role: 'user';
};

export type LoginPayload = {
  login: string;
  password: string;
};

export type TokenPairResponse = {
  access_token: string;
  refresh_token: string;
};

export type UserRoleResponse = {
  role: string;
};

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  query?: Record<string, string | undefined>;
};

function createUrl(
  path: string,
  query?: Record<string, string | undefined>,
): string {
  const url = new URL(`${AUTH_API_BASE_URL}${path}`, window.location.origin);

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

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(createUrl(path, options.query), {
    method: options.method ?? 'POST',
    credentials: 'include',
    headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
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

export async function registerUser(payload: RegisterPayload): Promise<void> {
  await request<void>('/register', {
    body: payload,
  });
}

export async function loginUser(
  payload: LoginPayload,
): Promise<TokenPairResponse> {
  return request<TokenPairResponse>('/login', {
    body: payload,
  });
}

export async function requestEmailConfirmation(email: string): Promise<void> {
  await request<void>('/email-confirm/request', {
    query: { email },
  });
}

export async function confirmEmail(
  email: string,
  token: string,
): Promise<void> {
  await request<void>('/email-confirm/confirm', {
    query: { token },
    body: { email },
  });
}

export async function requestPasswordReset(email: string): Promise<void> {
  await request<void>('/password-reset/request', {
    query: { email },
  });
}

export async function confirmPasswordReset(
  email: string,
  token: string,
  newPassword: string,
): Promise<void> {
  await request<void>('/password-reset/confirm', {
    query: { token },
    body: {
      email,
      new_password: newPassword,
    },
  });
}

export async function checkRole(accessToken: string): Promise<UserRoleResponse> {
  return request<UserRoleResponse>('/check_role', {
    body: {
      access_token: accessToken,
    },
  });
}
