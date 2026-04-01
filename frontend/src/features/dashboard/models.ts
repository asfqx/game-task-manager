import type { TaskResponse, TaskStatus } from './api/types';

export type Notice = {
  kind: 'success' | 'error' | 'info';
  text: string;
} | null;

export type DashboardPageProps = {
  accessToken: string;
  onLogout: () => void;
};

export type TaskFormState = {
  title: string;
  description: string;
  assigneeUserUuid: string;
  xpAmount: string;
  deadline: string;
};

export type ParticipantEntry = {
  uuid: string;
  fio: string;
  username: string;
  avatarUrl: string | null;
  roleLabel: string;
  meta: string;
};

export type NotificationToast = {
  uuid: string;
  content: string;
  senderLabel: string;
  createdAt: string;
};

export type TaskBoardColumn = {
  status: TaskStatus;
  title: string;
  tasks: TaskResponse[];
};
