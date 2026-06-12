import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

import {
  useGetGroupsGroupId,
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
  console.log(item);
  const user = useGetUsersUserId(item.refId, {
    query: { enabled: item.subjectType === AccessEntrySubjectType.USER },
  });
  const organization = useGetOrganizationsOrgId(item.refId, {
    query: { enabled: item.subjectType === AccessEntrySubjectType.ORGANIZATION },
  });
  const group = useGetGroupsGroupId(item.refId, {
    query: { enabled: item.subjectType === AccessEntrySubjectType.GROUP },
  });

  console.log(user, organization, group);

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
      </PopoverContent>
    </Popover>
  );
};
