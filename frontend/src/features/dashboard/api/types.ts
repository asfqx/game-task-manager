export type TaskStatus = 'CREATED' | 'IN_WORK' | 'ON_CHECK' | 'DONE';
export type InvitationStatus = 'WAITING' | 'ACCEPTED' | 'REJECTED';

export type UserShortResponse = {
  uuid: string;
  username: string;
  fio: string;
  avatar_url?: string | null;
};

export type LvlSummaryResponse = {
  uuid: string;
  value: string;
  required_xp: number;
};

export type LvlResponse = LvlSummaryResponse & {
  created_at: string;
  updated_at: string;
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

export type UserCompletedTaskResponse = {
  task_uuid: string;
  title: string;
  team_uuid: string;
  team_name: string;
  project_uuid: string;
  project_title: string;
  xp_amount: number;
  completed_at: string | null;
};

export type UserProfileResponse = {
  uuid: string;
  email: string;
  username: string;
  fio: string;
  role: string;
  status: string;
  email_confirmed?: boolean;
  avatar_url: string | null;
  telegram: string | null;
  phone_number: string | null;
  created_at: string | null;
  updated_at: string | null;
  last_login_at: string | null;
  teams: UserTeamSummaryResponse[];
  completed_tasks: UserCompletedTaskResponse[];
};

export type ProjectTeamSummaryResponse = {
  uuid: string;
  name: string;
  description: string | null;
  lead_uuid: string | null;
  lead_name: string | null;
  members_count: number;
  created_at: string;
  updated_at: string;
};

export type ProjectResponse = {
  uuid: string;
  title: string;
  description: string | null;
  creator_uuid: string;
  creator: UserShortResponse | null;
  teams_count: number;
  created_at: string;
  updated_at: string;
};

export type ProjectDetailResponse = ProjectResponse & {
  teams: ProjectTeamSummaryResponse[];
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
    description: string | null;
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

export type XpAccrualLogResponse = {
  uuid: string;
  issued_at: string;
  xp_amount: number;
  recipient_user_uuid: string | null;
  recipient_user: UserShortResponse | null;
  issuer_user_uuid: string | null;
  issuer_user: UserShortResponse | null;
  task_uuid: string | null;
  task: {
    uuid: string;
    title: string;
    team_uuid: string;
    team_name: string;
    project_uuid: string;
    project_title: string;
  } | null;
};

export type InvitationResponse = {
  uuid: string;
  project_uuid: string;
  project: {
    uuid: string;
    title: string;
  };
  team_uuid: string;
  team: {
    uuid: string;
    name: string;
    description: string | null;
    project_uuid: string;
    project_title: string;
  };
  sender_user_uuid: string | null;
  sender_user: UserShortResponse | null;
  recipient_user_uuid: string;
  recipient_user: UserShortResponse | null;
  recipient_login: string;
  status: InvitationStatus;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
};

export type CreateInvitationPayload = {
  team_uuid: string;
  recipient_login: string;
};

export type UpdateUserProfilePayload = {
  username?: string;
  email?: string;
  fio?: string;
  avatar_url?: string | null;
  telegram?: string | null;
  phone_number?: string | null;
};

export type UpdateUserProfileResponse = {
  username: string;
  email: string;
  fio: string;
  avatar_url: string | null;
  telegram: string | null;
  phone_number: string | null;
};

export type CreatePreSignedURLResponse = {
  upload_url: string;
};

export type CreateProjectPayload = {
  title: string;
  description: string | null;
};

export type CreateTeamPayload = {
  project_uuid: string;
  name: string;
  description: string | null;
  lead_uuid: string | null;
  member_uuids: string[];
};

export type UpdateTeamPayload = {
  name?: string;
  description?: string | null;
  lead_uuid?: string | null;
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
