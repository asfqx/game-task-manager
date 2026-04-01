import { API_BASE_URL } from './config';

export type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE';

export type RequestOptions = {
  method?: HttpMethod;
  query?: Record<string, string | undefined>;
  body?: unknown;
};

export function createApiUrl(
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

export function formatApiErrorDetail(detail: unknown): string | null {
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

export async function readApiError(response: Response): Promise<string> {
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

export async function requestJson<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(createApiUrl(path, options.query), {
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

export async function authorizedRequest<T>(
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

  const response = await fetch(createApiUrl(path, options.query), {
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
