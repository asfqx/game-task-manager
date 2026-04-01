import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { confirmPasswordReset, requestPasswordReset } from '../api/auth';
import {
  acceptTask,
  addTeamMember,
  acceptInvitation,
  approveTask,
  createInvitation,
  createProject,
  createTask,
  createTeam,
  deleteProject,
  getInvitations,
  getLvls,
  getNotifications,
  getMyAvatarUploadUrl,
  getProfile,
  getUserProfileByUuid,
  getProject,
  getProjects,
  getXpAccrualLogs,
  getTeams,
  getTasks,
  getTeam,
  leaveProject,
  leaveTeam,
  removeTeamMember,
  rejectTask,
  rejectInvitation,
  searchUsers,
  submitTaskForReview,
  subscribeToNotificationStream,
  updateMyProfile,
  updateTask,
  updateTeam,
  uploadAvatarFile,
  type InvitationResponse,
  type NotificationResponse,
  type ProjectDetailResponse,
  type ProjectResponse,
  type TaskResponse,
  type TeamResponse,
  type UserProfileResponse,
  type UserShortResponse,
  type XpAccrualLogResponse,
} from '../api/dashboard';
import { EMPTY_TASK_FORM } from '../features/dashboard/constants';
import { AppSelect } from '../features/dashboard/components/AppSelect';
import { AvatarImage } from '../features/dashboard/components/AvatarImage';
import { DateTimePicker } from '../features/dashboard/components/DateTimePicker';
import { InvitationsPage } from '../features/dashboard/components/InvitationsPage';
import { ModalShell } from '../features/dashboard/components/ModalShell';
import { NotificationCenter } from '../features/dashboard/components/NotificationCenter';
import { SidebarParticipantsSection } from '../features/dashboard/components/SidebarParticipantsSection';
import { TaskBoard } from '../features/dashboard/components/TaskBoard';
import { TaskDrawer } from '../features/dashboard/components/TaskDrawer';
import { UserProfileDrawer } from '../features/dashboard/components/UserProfileDrawer';
import type {
  DashboardPageProps,
  Notice,
  NotificationToast,
  ParticipantEntry,
  TaskFormState,
} from '../features/dashboard/models';
import {
  buildProjectParticipants,
  buildTeamParticipants,
  extractAvatarObjectName,
  formatDate,
  normalizeDateTime,
  resolveAvatarUrl,
} from '../features/dashboard/utils';

type DashboardRoute = {
  page: 'projects' | 'invitations';
  projectId: string | null;
  teamId: string | null;
};

function parseDashboardRoute(pathname: string): DashboardRoute {
  const segments = pathname.split('/').filter(Boolean);

  if (!segments.length || segments[0] !== 'dashboard') {
    return {
      page: 'projects',
      projectId: null,
      teamId: null,
    };
  }

  if (segments[1] === 'invitations') {
    return {
      page: 'invitations',
      projectId: null,
      teamId: null,
    };
  }

  if (segments[1] !== 'projects' || !segments[2]) {
    return {
      page: 'projects',
      projectId: null,
      teamId: null,
    };
  }

  return {
    page: 'projects',
    projectId: segments[2],
    teamId: segments[3] === 'teams' && segments[4] ? segments[4] : null,
  };
}

function buildDashboardPath(route: DashboardRoute): string {
  if (route.page === 'invitations') {
    return '/dashboard/invitations';
  }

  if (!route.projectId) {
    return '/dashboard';
  }

  if (!route.teamId) {
    return `/dashboard/projects/${route.projectId}`;
  }

  return `/dashboard/projects/${route.projectId}/teams/${route.teamId}`;
}

function DashboardPage({ accessToken, onLogout }: DashboardPageProps) {
  const initialRoute = parseDashboardRoute(window.location.pathname);
  const [currentPage, setCurrentPage] = useState<'projects' | 'invitations'>(initialRoute.page);
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [notificationToasts, setNotificationToasts] = useState<NotificationToast[]>([]);
  const [invitations, setInvitations] = useState<InvitationResponse[]>([]);
  const [availableTeams, setAvailableTeams] = useState<TeamResponse[]>([]);
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(initialRoute.projectId);
  const [selectedProject, setSelectedProject] = useState<ProjectDetailResponse | null>(null);
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(initialRoute.teamId);
  const [selectedTeam, setSelectedTeam] = useState<TeamResponse | null>(null);
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [directoryQuery, setDirectoryQuery] = useState('');
  const [directoryUsers, setDirectoryUsers] = useState<UserShortResponse[]>([]);
  const [projectForm, setProjectForm] = useState({ title: '', description: '' });
  const [invitationForm, setInvitationForm] = useState({ teamUuid: '', recipientLogin: '' });
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);
  const [isCreateTeamModalOpen, setIsCreateTeamModalOpen] = useState(false);
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [sidebarParticipants, setSidebarParticipants] = useState<ParticipantEntry[]>([]);
  const [sidebarParticipantsTitle, setSidebarParticipantsTitle] = useState('Участники');
  const [sidebarParticipantsSubtitle, setSidebarParticipantsSubtitle] = useState('Текущий контекст');
  const [sidebarParticipantsLoading, setSidebarParticipantsLoading] = useState(false);
  const [selectedUserProfile, setSelectedUserProfile] = useState<UserProfileResponse | null>(null);
  const [selectedUserProfileLoading, setSelectedUserProfileLoading] = useState(false);
  const [isNotificationPanelOpen, setIsNotificationPanelOpen] = useState(false);
  const [isTeamManagementModalOpen, setIsTeamManagementModalOpen] = useState(false);
  const [isXpLogsModalOpen, setIsXpLogsModalOpen] = useState(false);
  const [xpLogs, setXpLogs] = useState<XpAccrualLogResponse[]>([]);
  const [xpLogsLoading, setXpLogsLoading] = useState(false);
  const [expandedProjectTeamIds, setExpandedProjectTeamIds] = useState<string[]>([]);
  const [projectTeamDetails, setProjectTeamDetails] = useState<Record<string, TeamResponse>>({});
  const [projectTeamDetailsLoadingIds, setProjectTeamDetailsLoadingIds] = useState<string[]>([]);
  const [teamForm, setTeamForm] = useState({ name: '', description: '', leadUuid: '', memberUuids: [] as string[] });
  const [teamEditForm, setTeamEditForm] = useState({ name: '', description: '', leadUuid: '' });
  const [taskCreateForm, setTaskCreateForm] = useState<TaskFormState>(EMPTY_TASK_FORM);
  const [taskEditForm, setTaskEditForm] = useState<TaskFormState>(EMPTY_TASK_FORM);
  const [rejectComment, setRejectComment] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  const selectedTask = tasks.find((task) => task.uuid === selectedTaskId) ?? null;
  const inviteableTeams = useMemo(() => {
    if (!profile) {
      return [];
    }

    return availableTeams.filter((team) =>
      profile.role === 'admin' ||
      team.lead_uuid === profile.uuid ||
      projects.some((project) => project.uuid === team.project_uuid && project.creator_uuid === profile.uuid),
    );
  }, [availableTeams, profile, projects]);
  const isAdmin = profile?.role === "admin";
  const isProjectOwner = !!profile && !!selectedProject && (isAdmin || selectedProject.creator_uuid === profile.uuid);
  const isTeamLead = !!profile && !!selectedTeam && selectedTeam.lead_uuid === profile.uuid;
  const canManageTasks = !!selectedTeam && (isAdmin || isProjectOwner || isTeamLead);
  const canManageTeam = !!selectedTeam && (isAdmin || isProjectOwner || isTeamLead);
  const isCurrentUserInTeam = !!profile && !!selectedTeam && (
    selectedTeam.lead_uuid === profile.uuid ||
    selectedTeam.members.some((member) => member.user_uuid === profile.uuid)
  );
  const canLeaveProject = !!profile && !!selectedProject && selectedProject.creator_uuid !== profile.uuid;

  const teamMemberOptions = useMemo(
    () => (selectedTeam ? selectedTeam.members.filter((member) => member.user) : []),
    [selectedTeam],
  );
  const visibleProjectTeams = useMemo(() => {
    if (!selectedProject) {
      return [];
    }

    const availableTeamIds = new Set(availableTeams.map((team) => team.uuid));
    return selectedProject.teams.filter((team) => availableTeamIds.has(team.uuid));
  }, [availableTeams, selectedProject]);

  useEffect(() => {
    if (!accessToken || !visibleProjectTeams.length) {
      return;
    }

    const missingTeamIds = visibleProjectTeams
      .map((team) => team.uuid)
      .filter((teamUuid) => !projectTeamDetails[teamUuid] && !projectTeamDetailsLoadingIds.includes(teamUuid));

    if (!missingTeamIds.length) {
      return;
    }

    setProjectTeamDetailsLoadingIds((current) => [
      ...current,
      ...missingTeamIds.filter((teamUuid) => !current.includes(teamUuid)),
    ]);

    let cancelled = false;

    void Promise.all(
      missingTeamIds.map(async (teamUuid) => {
        try {
          const team = await getTeam(accessToken, teamUuid);
          if (cancelled) {
            return;
          }

          setProjectTeamDetails((current) => ({
            ...current,
            [teamUuid]: team,
          }));
        } catch (error) {
          if (!cancelled) {
            console.error(error);
          }
        } finally {
          if (!cancelled) {
            setProjectTeamDetailsLoadingIds((current) => current.filter((item) => item !== teamUuid));
          }
        }
      }),
    );

    return () => {
      cancelled = true;
    };
  }, [accessToken, projectTeamDetails, projectTeamDetailsLoadingIds, visibleProjectTeams]);

  const taskBoardColumns = useMemo(() => {
    const activeTasks = tasks.filter((task) => task.status !== 'DONE');

    return [
      {
        status: 'CREATED' as const,
        title: 'Бэклог',
        tasks: activeTasks.filter((task) => task.status === 'CREATED'),
      },
      {
        status: 'IN_WORK' as const,
        title: 'В работе',
        tasks: activeTasks.filter((task) => task.status === 'IN_WORK'),
      },
      {
        status: 'ON_CHECK' as const,
        title: 'На проверке',
        tasks: activeTasks.filter((task) => task.status === 'ON_CHECK'),
      },
    ];
  }, [tasks]);

  function applyRoute(route: DashboardRoute) {
    setCurrentPage(route.page);
    setSelectedProjectId(route.projectId);
    setSelectedTeamId(route.teamId);
  }

  function navigateToProjects() {
    const nextRoute = { page: 'projects' as const, projectId: null, teamId: null };
    window.history.pushState(null, '', buildDashboardPath(nextRoute));
    applyRoute(nextRoute);
  }

  function navigateToInvitations() {
    const nextRoute = { page: 'invitations' as const, projectId: null, teamId: null };
    window.history.pushState(null, '', buildDashboardPath(nextRoute));
    applyRoute(nextRoute);
  }

  function navigateToProject(projectId: string) {
    const nextRoute = { page: 'projects' as const, projectId, teamId: null };
    window.history.pushState(null, '', buildDashboardPath(nextRoute));
    applyRoute(nextRoute);
  }

  function navigateToTeam(projectId: string, teamId: string) {
    const nextRoute = { page: 'projects' as const, projectId, teamId };
    window.history.pushState(null, '', buildDashboardPath(nextRoute));
    applyRoute(nextRoute);
  }

  useEffect(() => {
    if (!accessToken) return;
    void loadWorkspace();
  }, [accessToken]);

  useEffect(() => {
    if (!window.location.pathname.startsWith('/dashboard')) {
      window.history.replaceState(null, '', buildDashboardPath(initialRoute));
    }
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      applyRoute(parseDashboardRoute(window.location.pathname));
      setSelectedTaskId(null);
      setSelectedUserProfile(null);
      setSelectedUserProfileLoading(false);
      setIsNotificationPanelOpen(false);
      setIsCreateProjectModalOpen(false);
      setIsCreateTeamModalOpen(false);
      setIsCreateTaskModalOpen(false);
      setIsTeamManagementModalOpen(false);
    };

    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  useEffect(() => {
    if (!accessToken) return;

    return subscribeToNotificationStream(accessToken, {
      onNotification: (notification) => {
        setNotifications((current) => {
          if (current.some((item) => item.uuid === notification.uuid)) {
            return current;
          }

          return [notification, ...current];
        });

        setNotificationToasts((current) => {
          if (current.some((item) => item.uuid === notification.uuid)) {
            return current;
          }

          return [
            {
              uuid: notification.uuid,
              content: notification.content,
              senderLabel: notification.sender_user?.fio ?? 'Система',
              createdAt: notification.created_at,
            },
            ...current,
          ].slice(0, 4);
        });

        window.setTimeout(() => {
          setNotificationToasts((current) => current.filter((item) => item.uuid !== notification.uuid));
        }, 15000);
      },
      onError: (error) => {
        setNotice((current) => current ?? { kind: 'info', text: error.message });
      },
    });
  }, [accessToken]);

  useEffect(() => {
    if (!selectedProjectId) {
      setSelectedProject(null);
      setSelectedTeamId(null);
      setExpandedProjectTeamIds([]);
      setProjectTeamDetails({});
      setProjectTeamDetailsLoadingIds([]);
      return;
    }
    void loadProject(selectedProjectId);
  }, [selectedProjectId]);

  useEffect(() => {
    if (!selectedTeamId) {
      setSelectedTeam(null);
      setTasks([]);
      setSelectedTaskId(null);
      return;
    }
    void loadTeamWorkspace(selectedTeamId);
  }, [selectedTeamId]);

  useEffect(() => {
    if (!selectedTask) {
      setTaskEditForm(EMPTY_TASK_FORM);
      setRejectComment('');
      return;
    }
    setTaskEditForm({
      title: selectedTask.title,
      description: selectedTask.description ?? '',
      assigneeUserUuid: selectedTask.assignee_user_uuid ?? '',
      xpAmount: String(selectedTask.xp_amount),
      deadline: selectedTask.deadline ? selectedTask.deadline.slice(0, 16) : '',
    });
    setRejectComment(selectedTask.review_comment ?? '');
  }, [selectedTask]);

  useEffect(() => {
    if (!selectedTask) return;

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedTaskId(null);
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedTask]);

  useEffect(() => {
    if (!selectedUserProfile && !selectedUserProfileLoading) return;

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedUserProfile(null);
        setSelectedUserProfileLoading(false);
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedUserProfile, selectedUserProfileLoading]);

  useEffect(() => {
    if (!isNotificationPanelOpen) return;

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsNotificationPanelOpen(false);
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isNotificationPanelOpen]);

  useEffect(() => {
    if (!selectedTeam) {
      setTeamEditForm({ name: '', description: '', leadUuid: '' });
      setTaskCreateForm(EMPTY_TASK_FORM);
      return;
    }
    setTeamEditForm({
      name: selectedTeam.name,
      description: selectedTeam.description ?? '',
      leadUuid: selectedTeam.lead_uuid ?? '',
    });
    const defaultAssignee =
      selectedTeam.members.find((member) => member.user_uuid !== selectedTeam.lead_uuid)?.user_uuid ??
      selectedTeam.members[0]?.user_uuid ??
      '';
    setTaskCreateForm({ ...EMPTY_TASK_FORM, assigneeUserUuid: defaultAssignee });
  }, [selectedTeam]);

  useEffect(() => {
    const query = directoryQuery.trim();
    if (!query) {
      setDirectoryUsers([]);
      return;
    }
    const timeoutId = window.setTimeout(() => {
      void searchUsers(accessToken, query).then(setDirectoryUsers).catch(() => setDirectoryUsers([]));
    }, 250);
    return () => window.clearTimeout(timeoutId);
  }, [accessToken, directoryQuery]);

  useEffect(() => {
    let cancelled = false;

    async function syncSidebarParticipants() {
      if (selectedTeam) {
        setSidebarParticipantsTitle('Участники команды');
        setSidebarParticipantsSubtitle(selectedTeam.name);
        setSidebarParticipants(buildTeamParticipants(selectedTeam));
        setSidebarParticipantsLoading(false);
        return;
      }

      if (selectedProject) {
        setSidebarParticipantsTitle('Участники проекта');
        setSidebarParticipantsSubtitle(selectedProject.title);
        setSidebarParticipantsLoading(true);
        try {
          const teams = await Promise.all(selectedProject.teams.map((team) => getTeam(accessToken, team.uuid)));
          if (cancelled) return;
          setSidebarParticipants(buildProjectParticipants(selectedProject, teams));
        } catch (error) {
          if (cancelled) return;
          setSidebarParticipants([]);
          setNotice({
            kind: 'error',
            text: error instanceof Error ? error.message : 'Не удалось загрузить участников проекта.',
          });
        } finally {
          if (!cancelled) {
            setSidebarParticipantsLoading(false);
          }
        }
        return;
      }

      setSidebarParticipantsTitle('Участники');
      setSidebarParticipantsSubtitle('Рабочее пространство');
      setSidebarParticipantsLoading(false);
      setSidebarParticipants(profile ? [{
        uuid: profile.uuid,
        fio: profile.fio,
        username: profile.username,
        avatarUrl: resolveAvatarUrl(profile.avatar_url),
        roleLabel: profile.role === 'admin' ? 'Администратор' : 'Участник',
        meta: 'Текущий пользователь',
      }] : []);
    }

    void syncSidebarParticipants();

    return () => {
      cancelled = true;
    };
  }, [accessToken, profile, selectedProject, selectedTeam]);

  async function loadWorkspace() {
    setIsLoading(true);
    try {
      const [profileResponse, notificationsResponse, projectsResponse, teamsResponse, invitationsResponse] = await Promise.all([
        getProfile(accessToken),
        getNotifications(accessToken),
        getProjects(accessToken),
        getTeams(accessToken),
        getInvitations(accessToken),
      ]);
      setProfile(profileResponse);
      setNotifications(notificationsResponse);
      setProjects(projectsResponse);
      setAvailableTeams(teamsResponse);
      setInvitations(invitationsResponse);
      setDashboardError(null);
    } catch (error) {
      setDashboardError(error instanceof Error ? error.message : 'Не удалось загрузить рабочее пространство.');
    } finally {
      setIsLoading(false);
    }
  }

  async function loadProject(projectUuid: string) {
    try {
      setSelectedProject(await getProject(accessToken, projectUuid));
      setDashboardError(null);
    } catch (error) {
      setDashboardError(error instanceof Error ? error.message : 'Не удалось загрузить проект.');
    }
  }

  async function loadTeamWorkspace(teamUuid: string) {
    try {
      const [teamResponse, tasksResponse] = await Promise.all([
        getTeam(accessToken, teamUuid),
        getTasks(accessToken, teamUuid),
      ]);
      setSelectedTeam(teamResponse);
      setTasks(tasksResponse);
      setSelectedTaskId((current) => current && tasksResponse.some((task) => task.uuid === current) ? current : null);
      setDashboardError(null);
    } catch (error) {
      setDashboardError(error instanceof Error ? error.message : 'Не удалось загрузить команду.');
    }
  }

  async function refreshProjects() {
    setProjects(await getProjects(accessToken));
  }

  async function refreshInvitations() {
    setInvitations(await getInvitations(accessToken));
  }

  async function refreshAvailableTeams() {
    setAvailableTeams(await getTeams(accessToken));
  }

  async function refreshProject() {
    if (selectedProjectId) {
      setSelectedProject(await getProject(accessToken, selectedProjectId));
    }
  }

  async function refreshTeam() {
    if (!selectedTeamId) return;
    const [teamResponse, tasksResponse] = await Promise.all([
      getTeam(accessToken, selectedTeamId),
      getTasks(accessToken, selectedTeamId),
    ]);
    setSelectedTeam(teamResponse);
    setTasks(tasksResponse);
  }

  async function refreshSidebarData() {
    const [profileResponse, notificationsResponse, invitationsResponse, teamsResponse] = await Promise.all([
      getProfile(accessToken),
      getNotifications(accessToken),
      getInvitations(accessToken),
      getTeams(accessToken),
    ]);
    setProfile(profileResponse);
    setNotifications(notificationsResponse);
    setInvitations(invitationsResponse);
    setAvailableTeams(teamsResponse);
  }

  async function withAction(actionKey: string, action: () => Promise<void>, successMessage: string) {
    setBusyAction(actionKey);
    setNotice(null);
    try {
      await action();
      setNotice({ kind: 'success', text: successMessage });
    } catch (error) {
      setNotice({
        kind: 'error',
        text: error instanceof Error ? error.message : 'Не удалось выполнить действие.',
      });
    } finally {
      setBusyAction(null);
    }
  }

  function toggleCreateTeamMember(userUuid: string) {
    setTeamForm((current) => ({
      ...current,
      memberUuids: current.memberUuids.includes(userUuid)
        ? current.memberUuids.filter((uuid) => uuid !== userUuid)
        : [...current.memberUuids, userUuid],
    }));
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await withAction('create-project', async () => {
      const createdProject = await createProject(accessToken, {
        title: projectForm.title,
        description: projectForm.description || null,
      });
      await refreshProjects();
      await refreshSidebarData();
      setProjectForm({ title: '', description: '' });
      setIsCreateProjectModalOpen(false);
      navigateToProject(createdProject.uuid);
    }, 'Проект создан.');
  }

  async function handleCreateInvitation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await withAction('create-invitation', async () => {
      await createInvitation(accessToken, {
        team_uuid: invitationForm.teamUuid,
        recipient_login: invitationForm.recipientLogin.trim(),
      });
      await refreshInvitations();
      await refreshAvailableTeams();
      setInvitationForm({ teamUuid: '', recipientLogin: '' });
    }, 'РџСЂРёРіР»Р°С€РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅРѕ.');
  }

  async function handleCreateTeam(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProject) return;
    await withAction('create-team', async () => {
      const nextTeam = await createTeam(accessToken, {
        project_uuid: selectedProject.uuid,
        name: teamForm.name,
        description: teamForm.description || null,
        lead_uuid: teamForm.leadUuid || null,
        member_uuids: Array.from(new Set(teamForm.memberUuids)),
      });
      await refreshProjects();
      await refreshProject();
      await refreshSidebarData();
      setTeamForm({ name: '', description: '', leadUuid: '', memberUuids: [] });
      setIsCreateTeamModalOpen(false);
      navigateToTeam(selectedProject.uuid, nextTeam.uuid);
    }, 'Команда создана.');
  }

  async function handleUpdateTeam(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTeam) return;
    await withAction('update-team', async () => {
      await updateTeam(accessToken, selectedTeam.uuid, {
        name: teamEditForm.name,
        description: teamEditForm.description || null,
        lead_uuid: teamEditForm.leadUuid || null,
      });
      await refreshTeam();
      await refreshProject();
      await refreshSidebarData();
    }, 'Команда обновлена.');
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTeam || !taskCreateForm.assigneeUserUuid) return;
    await withAction('create-task', async () => {
      const createdTask = await createTask(accessToken, {
        team_uuid: selectedTeam.uuid,
        title: taskCreateForm.title,
        description: taskCreateForm.description || null,
        assignee_user_uuid: taskCreateForm.assigneeUserUuid,
        xp_amount: Number(taskCreateForm.xpAmount),
        deadline: normalizeDateTime(taskCreateForm.deadline),
      });
      await refreshTeam();
      await refreshSidebarData();
      setTaskCreateForm({ ...EMPTY_TASK_FORM, assigneeUserUuid: createdTask.assignee_user_uuid ?? '' });
      setIsCreateTaskModalOpen(false);
      setSelectedTaskId(createdTask.uuid);
    }, 'Задача создана.');
  }

  async function handleUpdateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedTask) return;
    await withAction('update-task', async () => {
      await updateTask(accessToken, selectedTask.uuid, {
        title: taskEditForm.title,
        description: taskEditForm.description || null,
        assignee_user_uuid: taskEditForm.assigneeUserUuid,
        xp_amount: Number(taskEditForm.xpAmount),
        deadline: normalizeDateTime(taskEditForm.deadline),
      });
      await refreshTeam();
      await refreshSidebarData();
    }, 'Задача обновлена.');
  }

  async function handleTaskMutation(actionKey: string, action: () => Promise<TaskResponse>, successMessage: string) {
    await withAction(actionKey, async () => {
      const task = await action();
      await refreshTeam();
      await refreshSidebarData();
      setSelectedTaskId(task.uuid);
    }, successMessage);
  }

  async function handleDeleteProject() {
    if (!selectedProject) return;
    await withAction('delete-project', async () => {
      await deleteProject(accessToken, selectedProject.uuid);
      await refreshProjects();
      await refreshSidebarData();
      navigateToProjects();
    }, 'Проект удалён.');
  }

  async function handleLeaveProject() {
    if (!selectedProject) return;
    await withAction('leave-project', async () => {
      await leaveProject(accessToken, selectedProject.uuid);
      await refreshProjects();
      await refreshSidebarData();
      navigateToProjects();
    }, 'Вы покинули проект.');
  }

  async function handleLeaveTeam() {
    if (!selectedTeam) return;
    await withAction('leave-team', async () => {
      await leaveTeam(accessToken, selectedTeam.uuid);
      await refreshProjects();
      await refreshProject();
      await refreshSidebarData();
      navigateToProject(selectedProjectId ?? selectedTeam.project.uuid);
    }, 'Вы покинули команду.');
  }

  async function handleAddMember(userUuid: string) {
    if (!selectedTeam) return;
    await withAction(`add-member-${userUuid}`, async () => {
      await addTeamMember(accessToken, selectedTeam.uuid, userUuid);
      await refreshTeam();
      await refreshProject();
    }, 'Участник добавлен в команду.');
  }

  async function handleOpenProjectXpLogs() {
    if (!selectedProject) return;

    setIsXpLogsModalOpen(true);
    setXpLogsLoading(true);

    try {
      const logs = await getXpAccrualLogs(accessToken, selectedProject.uuid);
      setXpLogs(logs);
    } catch (error) {
      setNotice({
        kind: 'error',
        text: error instanceof Error ? error.message : 'Не удалось загрузить логи начисления XP.',
      });
    } finally {
      setXpLogsLoading(false);
    }
  }

  async function handleRemoveMember(userUuid: string) {
    if (!selectedTeam) return;
    await withAction(`remove-member-${userUuid}`, async () => {
      await removeTeamMember(accessToken, selectedTeam.uuid, userUuid);
      await refreshTeam();
      await refreshProject();
      await refreshSidebarData();
    }, '\u0423\u0447\u0430\u0441\u0442\u043d\u0438\u043a \u0443\u0434\u0430\u043b\u0451\u043d \u0438\u0437 \u043a\u043e\u043c\u0430\u043d\u0434\u044b.');
  }

  async function openUserProfile(userUuid: string) {
    const isOwnProfile = profile?.uuid === userUuid;

    if (isOwnProfile && profile) {
      setSelectedUserProfile(profile);
    } else {
      setSelectedUserProfile(null);
    }

    setSelectedUserProfileLoading(true);

    try {
      const userProfile = isOwnProfile
        ? await getProfile(accessToken)
        : await getUserProfileByUuid(accessToken, userUuid);
      setSelectedUserProfile(userProfile);
    } catch (error) {
      setNotice({
        kind: 'error',
        text: error instanceof Error ? error.message : 'Не удалось загрузить профиль пользователя.',
      });
    } finally {
      setSelectedUserProfileLoading(false);
    }
  }

  async function handleSaveOwnProfile(payload: {
    fio: string;
    username: string;
    email: string;
    telegram: string;
    phone_number: string;
  }) {
    await updateMyProfile(accessToken, {
      fio: payload.fio.trim(),
      username: payload.username.trim(),
      email: payload.email.trim(),
      telegram: payload.telegram.trim() || null,
      phone_number: payload.phone_number.trim() || null,
    });

    const [profileResponse, refreshedSelectedProfile] = await Promise.all([
      getProfile(accessToken),
      profile ? getUserProfileByUuid(accessToken, profile.uuid) : Promise.resolve(null),
    ]);

    setProfile(profileResponse);
    if (refreshedSelectedProfile) {
      setSelectedUserProfile(refreshedSelectedProfile);
    }
    setNotice({ kind: 'success', text: 'Профиль обновлён.' });
  }

  async function handleUploadOwnAvatar(file: File) {
    const { upload_url } = await getMyAvatarUploadUrl(accessToken);
    await uploadAvatarFile(upload_url, file);
    const avatarObjectName = extractAvatarObjectName(upload_url);
    await updateMyProfile(accessToken, { avatar_url: avatarObjectName });

    const [profileResponse, refreshedSelectedProfile] = await Promise.all([
      getProfile(accessToken),
      profile ? getUserProfileByUuid(accessToken, profile.uuid) : Promise.resolve(null),
    ]);

    setProfile(profileResponse);
    if (refreshedSelectedProfile) {
      setSelectedUserProfile(refreshedSelectedProfile);
    }
    setNotice({ kind: 'success', text: 'Аватар обновлён.' });
  }

  async function handleRequestOwnPasswordReset(email: string) {
    await requestPasswordReset(email);
  }

  async function handleConfirmOwnPasswordReset(payload: {
    email: string;
    token: string;
    newPassword: string;
  }) {
    await confirmPasswordReset(payload.email, payload.token, payload.newPassword);
  }

  async function handleInvitationDecision(
    actionKey: string,
    invitationUuid: string,
    action: (accessToken: string, invitationUuid: string) => Promise<InvitationResponse>,
    successMessage: string,
  ) {
    await withAction(actionKey, async () => {
      await action(accessToken, invitationUuid);
      await refreshInvitations();
      await refreshProjects();
      await refreshSidebarData();
    }, successMessage);
  }

  async function toggleProjectTeamParticipants(teamUuid: string) {
    const isExpanded = expandedProjectTeamIds.includes(teamUuid);
    if (isExpanded) {
      setExpandedProjectTeamIds((current) => current.filter((item) => item !== teamUuid));
      return;
    }

    setExpandedProjectTeamIds((current) => [...current, teamUuid]);

    if (projectTeamDetails[teamUuid]) {
      return;
    }

    setProjectTeamDetailsLoadingIds((current) =>
      current.includes(teamUuid) ? current : [...current, teamUuid],
    );

    try {
      const team = await getTeam(accessToken, teamUuid);
      setProjectTeamDetails((current) => ({
        ...current,
        [teamUuid]: team,
      }));
    } catch (error) {
      setNotice({
        kind: 'error',
        text: error instanceof Error ? error.message : 'Не удалось загрузить участников команды.',
      });
    } finally {
      setProjectTeamDetailsLoadingIds((current) => current.filter((item) => item !== teamUuid));
    }
  }

  if (isLoading) {
    return (
      <main className="dashboard-shell dashboard-shell--loading">
        <div className="dashboard-loading-card">
          <span className="dashboard-loading-card__badge">Workspace</span><div className="dashboard-loading-card__spinner" aria-hidden="true" />
          <strong>Загружаем проекты, команды и задачи...</strong>
          <p className="dashboard-loading-card__text">Сейчас подтянем ваше рабочее пространство.</p></div>
      </main>
    );
  }

  return (
    <main className="workspace-shell">
      <aside className="workspace-sidebar">
        <section className="workspace-card">
          <div className="workspace-card__header">
            <span className="workspace-card__badge">Task manager</span>
            <button type="button" className="ghost-button" onClick={onLogout}>Выйти</button>
          </div>
          <h1>Рабочее пространство</h1>
          <p>Главная страница показывает проекты, затем команды проекта, затем задачи команды.</p>
        </section>

        {profile ? <button type="button" className="sidebar-section profile-card profile-card--button" onClick={() => void openUserProfile(profile.uuid)}><div className="profile-card__identity"><AvatarImage src={resolveAvatarUrl(profile.avatar_url)} alt={profile.fio} fallbackText={profile.fio.slice(0, 1).toUpperCase()} imageClassName="profile-card__avatar-image" fallbackClassName="profile-card__avatar" /><div><strong>{profile.fio}</strong><span>{profile.role === 'admin' ? 'Администратор' : 'Участник'}</span></div></div></button> : null}

        <section className="sidebar-section sidebar-nav">
          <button type="button" className={currentPage === 'projects' ? 'secondary-button sidebar-nav__button is-active' : 'secondary-button sidebar-nav__button'} onClick={navigateToProjects}>Проекты</button>
          <button type="button" className={currentPage === 'invitations' ? 'secondary-button sidebar-nav__button is-active' : 'secondary-button sidebar-nav__button'} onClick={navigateToInvitations}>Приглашения</button>
        </section>

        {currentPage === 'projects' && (selectedProject || selectedTeam) ? <SidebarParticipantsSection
          title={sidebarParticipantsTitle}
          subtitle={sidebarParticipantsSubtitle}
          participants={sidebarParticipants}
          isLoading={sidebarParticipantsLoading}
          onParticipantClick={(userUuid) => {
            void openUserProfile(userUuid);
          }}
        /> : null}

      </aside>

      <section className="workspace-main">
        {dashboardError ? <div className="notice notice--error">{dashboardError}</div> : null}
        {notice ? <div className={`notice notice--${notice.kind}`}>{notice.text}</div> : null}

        {currentPage === 'invitations' ? <InvitationsPage
          profile={profile}
          teams={inviteableTeams}
          invitations={invitations}
          inviteTeamUuid={invitationForm.teamUuid}
          inviteRecipientLogin={invitationForm.recipientLogin}
          busyAction={busyAction}
          onInviteTeamUuidChange={(value) => setInvitationForm((current) => ({ ...current, teamUuid: value }))}
          onInviteRecipientLoginChange={(value) => setInvitationForm((current) => ({ ...current, recipientLogin: value }))}
          onCreateInvitation={handleCreateInvitation}
          onAcceptInvitation={(invitationUuid) => {
            void handleInvitationDecision(`accept-invitation-${invitationUuid}`, invitationUuid, acceptInvitation, 'Приглашение принято.');
          }}
          onRejectInvitation={(invitationUuid) => {
            void handleInvitationDecision(`reject-invitation-${invitationUuid}`, invitationUuid, rejectInvitation, 'Приглашение отклонено.');
          }}
        /> : null}

        {currentPage === 'projects' && !selectedProject ? <section className="workspace-panel">
          <div className="section-heading"><h3>{'Мои проекты'}</h3><div className="section-heading__actions"><button type="button" className="primary-button primary-button--compact" onClick={() => setIsCreateProjectModalOpen(true)}>{'Создать проект'}</button></div></div>
          <div className="workspace-grid">
            {projects.map((project) => <article key={project.uuid} className="workspace-item-card"><div className="workspace-item-card__header"><div><strong>{project.title}</strong><span>{project.creator?.fio ?? 'Без автора'}</span></div></div><p>{project.description ?? 'Описание проекта пока не заполнено.'}</p><div className="workspace-item-card__actions"><button type="button" className="primary-button" onClick={() => navigateToProject(project.uuid)}>Открыть проект</button></div></article>)}
          </div>
        </section> : null}

        {currentPage === 'projects' && selectedProject && !selectedTeam ? <section className="workspace-panel">
          <div className="project-summary-card project-summary-card--project"><div className="project-summary-card__content"><span className="board-header__eyebrow">Проект</span><strong>{selectedProject.title}</strong><p>{selectedProject.description ?? 'Описание проекта пока не заполнено.'}</p></div><div className="project-summary-card__actions project-summary-card__actions--row"><button type="button" className="secondary-button" onClick={navigateToProjects}>К проектам</button>{isProjectOwner ? <button type="button" className="secondary-button" onClick={() => void handleOpenProjectXpLogs()} disabled={xpLogsLoading}>{xpLogsLoading && isXpLogsModalOpen ? 'Загружаем логи...' : 'Логи XP'}</button> : null}{isProjectOwner ? <button type="button" className="primary-button" onClick={() => setIsCreateTeamModalOpen(true)}>Создать команду</button> : null}{canLeaveProject ? <button type="button" className="secondary-button" onClick={() => void handleLeaveProject()} disabled={busyAction === 'leave-project'}>Покинуть проект</button> : null}{isProjectOwner ? <button type="button" className="secondary-button secondary-button--danger" onClick={() => void handleDeleteProject()} disabled={busyAction === 'delete-project'}>Удалить проект</button> : null}</div></div>

          <div className="section-heading"><h3>Доступные команды</h3></div>
          {visibleProjectTeams.length ? <div className="workspace-grid workspace-grid--teams">{visibleProjectTeams.map((team) => {
            const teamDetail = projectTeamDetails[team.uuid];
            const isExpanded = expandedProjectTeamIds.includes(team.uuid);
            const participants = teamDetail ? buildTeamParticipants(teamDetail) : [];

            return <article key={team.uuid} className="workspace-item-card team-showcase-card"><div className="team-showcase-card__top"><div className="team-showcase-card__identity"><span className="team-showcase-card__badge">Команда</span><strong>{team.name}</strong><p className="team-showcase-card__description">{team.description ?? 'Описание команды пока не заполнено.'}</p></div><button type="button" className="metric-chip metric-chip--interactive" onClick={() => void toggleProjectTeamParticipants(team.uuid)}>{team.members_count} участников</button></div><div className="team-showcase-card__footer"><button type="button" className="secondary-button" onClick={() => void toggleProjectTeamParticipants(team.uuid)}>{isExpanded ? 'Скрыть участников' : 'Показать участников'}</button><button type="button" className="primary-button" onClick={() => navigateToTeam(selectedProject.uuid, team.uuid)}>Открыть команду</button></div>{isExpanded ? <div className="team-showcase-card__participants">{projectTeamDetailsLoadingIds.includes(team.uuid) && !teamDetail ? <div className="team-showcase-card__participants-empty">Загружаем участников...</div> : participants.length ? participants.map((participant) => <button key={participant.uuid} type="button" className="team-showcase-card__participant" onClick={() => void openUserProfile(participant.uuid)}><AvatarImage src={participant.avatarUrl} alt={participant.fio} fallbackText={participant.fio.charAt(0).toUpperCase() || '?'} imageClassName="participant-avatar" fallbackClassName="participant-avatar participant-avatar--fallback" /><div className="team-showcase-card__participant-content"><div className="team-showcase-card__participant-identity"><strong>{participant.fio}</strong><span>@{participant.username}</span></div><div className="team-showcase-card__participant-meta"><span>{participant.roleLabel}</span><span>{participant.meta}</span></div></div></button>) : <div className="team-showcase-card__participants-empty">Участники не найдены.</div>}</div> : null}<div className="team-showcase-card__lead-block"><AvatarImage src={resolveAvatarUrl(teamDetail?.lead?.avatar_url ?? null)} alt={team.lead_name ?? 'Team lead'} fallbackText={(team.lead_name ?? 'Не назначен').charAt(0).toUpperCase() || '?'} imageClassName="team-showcase-card__lead-avatar-image" fallbackClassName="team-showcase-card__lead-avatar" /><div className="team-showcase-card__lead-content"><span className="team-showcase-card__lead-label">Тимлид</span><span className="team-showcase-card__lead-name">{team.lead_name ?? 'Не назначен'}</span></div></div></article>;
          })}</div> : <div className="sidebar-participants__empty">У вас нет команд в этом проекте.</div>}
        </section> : null}

        {isCreateProjectModalOpen ? <ModalShell titleId="create-project-title" eyebrow="Проект" title="Создать проект" onClose={() => setIsCreateProjectModalOpen(false)}>
          <form className="workspace-form modal-card__form" onSubmit={handleCreateProject}>
            <div className="form-grid">
              <label className="field"><span>Название проекта</span><input type="text" value={projectForm.title} onChange={(event) => setProjectForm((current) => ({ ...current, title: event.target.value }))} required minLength={2} autoFocus /></label>
              <label className="field"><span>Описание</span><input type="text" value={projectForm.description} onChange={(event) => setProjectForm((current) => ({ ...current, description: event.target.value }))} /></label>
            </div>
            <div className="modal-card__actions">
              <button type="button" className="secondary-button" onClick={() => setIsCreateProjectModalOpen(false)}>Отмена</button>
              <button type="submit" className="primary-button" disabled={busyAction === 'create-project'}>{busyAction === 'create-project' ? 'Создаём...' : 'Создать проект'}</button>
            </div>
          </form>
        </ModalShell> : null}

        {selectedProject && isProjectOwner && isCreateTeamModalOpen ? <ModalShell titleId="create-team-title" eyebrow="Команда" title="Создать команду" subtitle="Управление проектом" sizeClassName="modal-card--team-management" onClose={() => setIsCreateTeamModalOpen(false)}>
          <form className="workspace-form modal-card__form" onSubmit={handleCreateTeam}>
            <div className="form-grid">
              <label className="field"><span>Название команды</span><input type="text" value={teamForm.name} onChange={(event) => setTeamForm((current) => ({ ...current, name: event.target.value }))} required minLength={2} autoFocus /></label>
              <label className="field"><span>Описание</span><input type="text" value={teamForm.description} onChange={(event) => setTeamForm((current) => ({ ...current, description: event.target.value }))} /></label>
            </div>
            <label className="field"><span>Поиск пользователей</span><input type="search" value={directoryQuery} onChange={(event) => setDirectoryQuery(event.target.value)} placeholder="Имя, username или email" /></label>
            {directoryUsers.length ? <div className="selector-list">{directoryUsers.map((user) => <div key={user.uuid} className="selector-list__item"><label className="selector-list__label"><input type="checkbox" checked={teamForm.memberUuids.includes(user.uuid)} onChange={() => toggleCreateTeamMember(user.uuid)} /><div className="selector-list__user"><AvatarImage src={resolveAvatarUrl(user.avatar_url ?? null)} alt={user.fio} fallbackText={user.fio.charAt(0).toUpperCase() || '?'} imageClassName="participant-avatar" fallbackClassName="participant-avatar participant-avatar--fallback" /><div className="selector-list__user-text"><strong>{user.fio}</strong><span>@{user.username}</span></div></div></label><button type="button" className={teamForm.leadUuid === user.uuid ? 'ghost-button is-active' : 'ghost-button'} onClick={() => setTeamForm((current) => ({ ...current, leadUuid: current.leadUuid === user.uuid ? '' : user.uuid, memberUuids: current.memberUuids.includes(user.uuid) ? current.memberUuids : [...current.memberUuids, user.uuid] }))}>{teamForm.leadUuid === user.uuid ? 'Тимлид' : 'Сделать тимлидом'}</button></div>)}</div> : null}
            <div className="modal-card__actions">
              <button type="button" className="secondary-button" onClick={() => setIsCreateTeamModalOpen(false)}>Отмена</button>
              <button type="submit" className="primary-button" disabled={busyAction === 'create-team'}>{busyAction === 'create-team' ? 'Создаём...' : 'Создать команду'}</button>
            </div>
          </form>
        </ModalShell> : null}

        {selectedProject && isProjectOwner && isXpLogsModalOpen ? <ModalShell titleId="project-xp-logs-title" eyebrow="XP" title="Логи начисления XP" subtitle={selectedProject.title} sizeClassName="modal-card--xp-logs" onClose={() => setIsXpLogsModalOpen(false)}>
          <div className="xp-logs-list">
            {xpLogsLoading ? <div className="sidebar-participants__empty">Загружаем логи начисления XP...</div> : xpLogs.length ? xpLogs.map((log) => <article key={log.uuid} className="xp-log-card"><div className="xp-log-card__header"><div><strong>+{log.xp_amount} XP</strong><span>{formatDate(log.issued_at)}</span></div><span className="metric-chip">{log.task?.team_name ?? 'Без команды'}</span></div><div className="xp-log-card__body"><strong>{log.task?.title ?? 'Задача удалена'}</strong><p>Получатель: {log.recipient_user?.fio ?? 'Не указан'}</p><p>Начислил: {log.issuer_user?.fio ?? 'Система'}</p></div></article>) : <div className="sidebar-participants__empty">В этом проекте пока нет логов начисления XP.</div>}
          </div>
        </ModalShell> : null}

        {selectedTeam && isTeamManagementModalOpen ? <div className="modal-backdrop" role="presentation" onClick={() => setIsTeamManagementModalOpen(false)}>
          <div className="modal-card modal-card--team-management" role="dialog" aria-modal="true" aria-labelledby="team-management-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-card__header">
              <div>
                <span className="board-header__eyebrow">Команда</span>
                <h3 id="team-management-title">Управление командой</h3>
                <p className="modal-card__subtitle">Редактирование состава и настроек команды</p>
              </div>
              <button type="button" className="ghost-button" onClick={() => setIsTeamManagementModalOpen(false)}>Закрыть</button>
            </div>
            <form className="workspace-form modal-card__form" onSubmit={handleUpdateTeam}>
              <div className="form-grid">
                <label className="field"><span>Название</span><input type="text" value={teamEditForm.name} onChange={(event) => setTeamEditForm((current) => ({ ...current, name: event.target.value }))} required /></label>
                <div className="field"><span>Тимлид</span><AppSelect value={teamEditForm.leadUuid} onChange={(value) => setTeamEditForm((current) => ({ ...current, leadUuid: value }))} options={[{ value: '', label: 'Не назначен' }, ...teamMemberOptions.map((member) => ({ value: member.user_uuid, label: member.user?.fio ?? 'Без имени' }))]} /></div>
              </div>
              <label className="field"><span>Описание</span><textarea value={teamEditForm.description} onChange={(event) => setTeamEditForm((current) => ({ ...current, description: event.target.value }))} rows={3} /></label>
              <button type="submit" className="primary-button" disabled={busyAction === 'update-team'}>{busyAction === 'update-team' ? 'Сохраняем...' : 'Сохранить команду'}</button>
              <label className="field"><span>Добавить участника</span><input type="search" value={directoryQuery} onChange={(event) => setDirectoryQuery(event.target.value)} placeholder="Имя, username или email" /></label>
              {directoryUsers.length ? <div className="selector-list">{directoryUsers.map((user) => <div key={user.uuid} className="selector-list__item"><div className="selector-list__user"><AvatarImage src={resolveAvatarUrl(user.avatar_url ?? null)} alt={user.fio} fallbackText={user.fio.charAt(0).toUpperCase() || '?'} imageClassName="participant-avatar" fallbackClassName="participant-avatar participant-avatar--fallback" /><div className="selector-list__user-text"><strong>{user.fio}</strong><span>@{user.username}</span></div></div><button type="button" className="ghost-button" onClick={() => void handleAddMember(user.uuid)} disabled={busyAction === `add-member-${user.uuid}`}>Добавить</button></div>)}</div> : null}
              <div className="team-members-panel">
                <div className="section-heading">
                  <h3>Участники команды</h3>
                  <span>{selectedTeam.members.length}</span>
                </div>
                {selectedTeam.members.length ? <div className="selector-list">{selectedTeam.members.map((member) => <div key={member.uuid} className="selector-list__item"><div className="selector-list__user"><AvatarImage src={resolveAvatarUrl(member.user?.avatar_url ?? null)} alt={member.user?.fio ?? 'Участник'} fallbackText={(member.user?.fio ?? 'У').charAt(0).toUpperCase() || '?'} imageClassName="participant-avatar" fallbackClassName="participant-avatar participant-avatar--fallback" /><div className="selector-list__user-text"><strong>{member.user?.fio ?? 'Без имени'}</strong><span>{member.user_uuid === selectedTeam.lead_uuid ? 'Тимлид' : `@${member.user?.username ?? 'unknown'}`}</span></div></div>{member.user_uuid === selectedTeam.lead_uuid ? <button type="button" className="ghost-button is-active" disabled>Тимлид</button> : <button type="button" className="ghost-button ghost-button--danger" onClick={() => void handleRemoveMember(member.user_uuid)} disabled={busyAction === `remove-member-${member.user_uuid}`}>{busyAction === `remove-member-${member.user_uuid}` ? 'Удаляем...' : 'Выгнать'}</button>}</div>)}</div> : <div className="sidebar-participants__empty">В команде пока нет участников.</div>}
              </div>
            </form>
          </div>
        </div> : null}

        {selectedTeam && canManageTasks && isCreateTaskModalOpen ? <ModalShell titleId="create-task-title" eyebrow="Задача" title="Создать задачу" subtitle="Тимлид или владелец проекта" sizeClassName="modal-card--team-management" onClose={() => setIsCreateTaskModalOpen(false)}>
          <form className="workspace-form modal-card__form" onSubmit={handleCreateTask}>
            <div className="form-grid">
              <label className="field"><span>Название</span><input type="text" value={taskCreateForm.title} onChange={(event) => setTaskCreateForm((current) => ({ ...current, title: event.target.value }))} required minLength={2} autoFocus /></label>
              <div className="field"><span>Исполнитель</span><AppSelect value={taskCreateForm.assigneeUserUuid} onChange={(value) => setTaskCreateForm((current) => ({ ...current, assigneeUserUuid: value }))} options={teamMemberOptions.map((member) => ({ value: member.user_uuid, label: member.user?.fio ?? 'Без имени' }))} /></div>
            </div>
            <div className="form-grid">
              <label className="field"><span>XP</span><input type="number" min={0} value={taskCreateForm.xpAmount} onChange={(event) => setTaskCreateForm((current) => ({ ...current, xpAmount: event.target.value }))} /></label>
              <div className="field"><span>Дедлайн</span><DateTimePicker value={taskCreateForm.deadline} onChange={(value) => setTaskCreateForm((current) => ({ ...current, deadline: value }))} /></div>
            </div>
            <label className="field"><span>Описание</span><textarea value={taskCreateForm.description} onChange={(event) => setTaskCreateForm((current) => ({ ...current, description: event.target.value }))} rows={3} /></label>
            <div className="modal-card__actions">
              <button type="button" className="secondary-button" onClick={() => setIsCreateTaskModalOpen(false)}>Отмена</button>
              <button type="submit" className="primary-button" disabled={busyAction === 'create-task'}>{busyAction === 'create-task' ? 'Создаём...' : 'Создать задачу'}</button>
            </div>
          </form>
        </ModalShell> : null}

        {currentPage === 'projects' && selectedProject && selectedTeam ? <section className="workspace-panel">
          <div className="project-summary-card project-summary-card--team-header"><div className="project-summary-card__content"><span className="board-header__eyebrow">Команда</span><strong>{selectedTeam.name}</strong><p>{selectedTeam.description ?? 'Описание команды пока не заполнено.'}</p></div><div className="project-summary-card__actions project-summary-card__actions--row"><button type="button" className="secondary-button" onClick={() => navigateToProject(selectedProject.uuid)}>К командам</button><button type="button" className="secondary-button" onClick={navigateToProjects}>К проектам</button>{canManageTasks ? <button type="button" className="primary-button" onClick={() => setIsCreateTaskModalOpen(true)}>Создать задачу</button> : null}{canManageTeam ? <button type="button" className="secondary-button" onClick={() => setIsTeamManagementModalOpen(true)}>Управление командой</button> : null}{isCurrentUserInTeam ? <button type="button" className="secondary-button" onClick={() => void handleLeaveTeam()} disabled={busyAction === 'leave-team'}>Покинуть команду</button> : null}</div></div>

          <TaskBoard
            columns={taskBoardColumns}
            selectedTaskId={selectedTaskId}
            onTaskSelect={setSelectedTaskId}
          />

        </section> : null}
      </section>

      <NotificationCenter
        notifications={notifications}
        toasts={notificationToasts}
        isPanelOpen={isNotificationPanelOpen}
        onOpenPanel={() => setIsNotificationPanelOpen(true)}
        onClosePanel={() => setIsNotificationPanelOpen(false)}
        onDismissToast={(toastUuid) => {
          setNotificationToasts((current) => current.filter((item) => item.uuid !== toastUuid));
        }}
      />

      <TaskDrawer
        profile={profile}
        task={selectedTask}
        canManageTasks={canManageTasks}
        busyAction={busyAction}
        teamMemberOptions={teamMemberOptions}
        taskEditForm={taskEditForm}
        rejectComment={rejectComment}
        onClose={() => setSelectedTaskId(null)}
        onTaskEditFormChange={(updater) => setTaskEditForm(updater)}
        onRejectCommentChange={setRejectComment}
        onUpdateTask={handleUpdateTask}
        onAcceptTask={() => {
          if (!selectedTask) return;
          void handleTaskMutation(
            'accept-task',
            () => acceptTask(accessToken, selectedTask.uuid),
            'Задача принята в работу.',
          );
        }}
        onSubmitForReview={() => {
          if (!selectedTask) return;
          void handleTaskMutation(
            'submit-review',
            () => submitTaskForReview(accessToken, selectedTask.uuid),
            'Задача отправлена на проверку.',
          );
        }}
        onManagerSubmitForReview={() => {
          if (!selectedTask) return;
          void handleTaskMutation(
            'submit-review',
            () => submitTaskForReview(accessToken, selectedTask.uuid),
            'Задача взята тимлидом на проверку.',
          );
        }}
        onApproveTask={() => {
          if (!selectedTask) return;
          void handleTaskMutation(
            'approve-task',
            () => approveTask(accessToken, selectedTask.uuid),
            'Задача отмечена выполненной.',
          );
        }}
        onRejectTask={() => {
          if (!selectedTask) return;
          void handleTaskMutation(
            'reject-task',
            () => rejectTask(accessToken, selectedTask.uuid, rejectComment.trim()),
            'Задача возвращена в работу.',
          );
        }}
      />

      <UserProfileDrawer
        profile={selectedUserProfile}
        isLoading={selectedUserProfileLoading}
        isOwnProfile={!!profile && !!selectedUserProfile && selectedUserProfile.uuid === profile.uuid}
        onClose={() => {
          setSelectedUserProfile(null);
          setSelectedUserProfileLoading(false);
        }}
        onSaveProfile={handleSaveOwnProfile}
        onUploadAvatar={handleUploadOwnAvatar}
        onLoadLevels={() => getLvls(accessToken)}
        onRequestPasswordReset={handleRequestOwnPasswordReset}
        onConfirmPasswordReset={handleConfirmOwnPasswordReset}
      />
    </main>
  );
}

export default DashboardPage;
