import { requestJson } from '../shared/api/http';

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

export async function registerUser(payload: RegisterPayload): Promise<void> {
  await requestJson<void>('/auth/register', {
    body: payload,
  });
}

export async function loginUser(
  payload: LoginPayload,
): Promise<TokenPairResponse> {
  return requestJson<TokenPairResponse>('/auth/login', {
    body: payload,
  });
}

export async function requestEmailConfirmation(email: string): Promise<void> {
  await requestJson<void>('/auth/email-confirm/request', {
    query: { email },
  });
}

export async function confirmEmail(
  email: string,
  token: string,
): Promise<void> {
  await requestJson<void>('/auth/email-confirm/confirm', {
    query: { token },
    body: { email },
  });
}

export async function requestPasswordReset(email: string): Promise<void> {
  await requestJson<void>('/auth/password-reset/request', {
    query: { email },
  });
}

export async function confirmPasswordReset(
  email: string,
  token: string,
  newPassword: string,
): Promise<void> {
  await requestJson<void>('/auth/password-reset/confirm', {
    query: { token },
    body: {
      email,
      new_password: newPassword,
    },
  });
}

export async function checkRole(accessToken: string): Promise<UserRoleResponse> {
  return requestJson<UserRoleResponse>('/auth/check_role', {
    body: {
      access_token: accessToken,
    },
  });
}
