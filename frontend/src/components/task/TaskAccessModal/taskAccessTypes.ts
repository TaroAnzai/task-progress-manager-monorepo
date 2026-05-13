import type {
  AccessEntry,
  AccessEntryAccessLevel,
  AccessEntrySubjectType,
  AccessLevelInput,
  TaskAccessListResponse,
  TaskAccessResponse,
} from '@/api/generated/taskProgressAPI.schemas';

export type AccessSubjectType = AccessEntrySubjectType;

export type TaskAccessLevel = AccessEntryAccessLevel;

export type EditableTaskAccessLevel = Exclude<TaskAccessLevel, 'OWNER'>;

export type AccessSubjectItem = {
  subjectType: AccessSubjectType;
  refId: number;
  name: string;
  description?: string;
};

export type TaskAccessItem = AccessSubjectItem & {
  accessLevel: TaskAccessLevel;
};

export type AccessSubjectSearchResult = AccessSubjectItem & {
  alreadyAdded: boolean;
};
export type TaskAccessApiResponse = TaskAccessListResponse;

export type TaskAccessApiItem = TaskAccessResponse;

export type TaskAccessApiInput = AccessLevelInput;

export type TaskAccessApiEntry = AccessEntry;
