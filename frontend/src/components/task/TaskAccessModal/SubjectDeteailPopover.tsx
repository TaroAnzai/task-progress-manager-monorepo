import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

import {
  useGetGroupsGroupIdMembers,
  useGetOrganizationsOrgId,
  useGetUsersUserId,
} from '@/api/generated/taskProgressAPI';
import { AccessEntrySubjectType } from '@/api/generated/taskProgressAPI.schemas';

import type { TaskAccessItem } from './taskAccessTypes';

type Props = {
  item: TaskAccessItem;
  getSubjectIcon: (subjectType: AccessEntrySubjectType) => React.ReactNode;
  getSubjectTypeLabel: (subjectType: AccessEntrySubjectType) => string;
};

export const SubjectDeteailPopover = ({ item, getSubjectIcon, getSubjectTypeLabel }: Props) => {
  const { data: user } = useGetUsersUserId(item.refId, {
    query: { enabled: item.subjectType === AccessEntrySubjectType.USER },
  });
  const { data: organization } = useGetOrganizationsOrgId(item.refId, {
    query: { enabled: item.subjectType === AccessEntrySubjectType.ORGANIZATION },
  });
  const { data: group } = useGetGroupsGroupIdMembers(item.refId, {
    query: { enabled: item.subjectType === AccessEntrySubjectType.GROUP },
  });

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-slate-50"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-base">
            {getSubjectIcon(item.subjectType)}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate text-sm font-medium text-slate-900">{item.name}</span>

              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                {getSubjectTypeLabel(item.subjectType)}
              </span>
            </div>

            {item.description && (
              <p className="mt-0.5 truncate text-xs text-slate-500">{item.description}</p>
            )}
          </div>
        </button>
      </PopoverTrigger>

      <PopoverContent side="bottom" align="start" className="w-72">
        <div className="text-sm font-medium text-slate-900">{item.name}</div>

        <div className="mt-1 text-xs text-slate-500">{getSubjectTypeLabel(item.subjectType)}</div>

        {item.description && <p className="mt-2 text-sm text-slate-600">{item.description}</p>}
        {item.subjectType === AccessEntrySubjectType.USER && user && (
          <>
            <p className="mt-2 text-sm text-slate-600">{user.organization_name}</p>
            <p className="mt-2 text-sm text-slate-600">{user.email}</p>
          </>
        )}
        {item.subjectType === AccessEntrySubjectType.ORGANIZATION && organization && (
          <p className="mt-2 text-sm text-slate-600"></p>
        )}
        {item.subjectType === AccessEntrySubjectType.GROUP &&
          group &&
          group.users.map((user) => (
            <p key={user.id} className="mt-2 text-sm text-slate-600">
              {user.name}
            </p>
          ))}
      </PopoverContent>
    </Popover>
  );
};
