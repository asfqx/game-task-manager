import type { TaskFormState } from './models';

export const EMPTY_TASK_FORM: TaskFormState = {
  title: '',
  description: '',
  assigneeUserUuid: '',
  xpAmount: '100',
  deadline: '',
};
