import { getSubjectIcon, getSubjectTypeLabel } from './accessSubjectUtils';
import type { EditableTaskAccessLevel, TaskAccessItem, TaskAccessLevel } from './taskAccessTypes';

type CurrentAccessListProps = {
  items: TaskAccessItem[];
  onChangeAccessLevel: (item: TaskAccessItem, accessLevel: EditableTaskAccessLevel) => void;
  onRemove: (item: TaskAccessItem) => void;
};

const EDITABLE_LEVELS: EditableTaskAccessLevel[] = ['VIEW', 'EDIT', 'FULL'];

const getAccessLevelClassName = (accessLevel: TaskAccessLevel) => {
  switch (accessLevel) {
    case 'OWNER':
      return 'bg-purple-100 text-purple-700 border-purple-200';
    case 'FULL':
      return 'bg-red-100 text-red-700 border-red-200';
    case 'EDIT':
      return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'VIEW':
      return 'bg-blue-100 text-blue-700 border-blue-200';
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200';
  }
};

export const CurrentAccessList = ({
  items,
  onChangeAccessLevel,
  onRemove,
}: CurrentAccessListProps) => (
  <section className="space-y-3">
    <div>
      <h3 className="text-sm font-semibold text-slate-900">現在の権限</h3>
      <p className="mt-1 text-xs text-slate-500">
        追加済みの対象はここで権限を変更できます。OWNERは変更できません。
      </p>
    </div>

    <div className="overflow-hidden rounded-md border border-slate-200">
      {items.length === 0 ? (
        <div className="px-4 py-6 text-center text-sm text-slate-500">
          権限が設定されている対象はありません。
        </div>
      ) : (
        <ul className="divide-y divide-slate-200">
          {items.map((item) => {
            const isOwner = item.accessLevel === 'OWNER';

            return (
              <li
                key={`${item.subjectType}:${item.refId}`}
                className="flex items-center gap-3 px-4 py-3"
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

                {isOwner ? (
                  <div className="flex items-center gap-2">
                    <span
                      className={[
                        'rounded-full border px-2 py-1 text-xs font-semibold',
                        getAccessLevelClassName(item.accessLevel),
                      ].join(' ')}
                    >
                      OWNER
                    </span>
                    <span className="text-xs text-slate-400">🔒 変更不可</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <select
                      value={item.accessLevel}
                      onChange={(event) =>
                        onChangeAccessLevel(item, event.target.value as EditableTaskAccessLevel)
                      }
                      className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                    >
                      {EDITABLE_LEVELS.map((level) => (
                        <option key={level} value={level}>
                          {level}
                        </option>
                      ))}
                    </select>

                    <button
                      type="button"
                      onClick={() => onRemove(item)}
                      className="rounded-md px-2 py-1 text-sm text-red-600 hover:bg-red-50"
                    >
                      削除
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  </section>
);
