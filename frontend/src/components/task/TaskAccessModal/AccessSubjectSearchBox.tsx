import { useMemo, useRef, useState } from 'react';

import { getSubjectIcon, getSubjectTypeLabel } from './accessSubjectUtils';
import type {
  AccessSubjectItem,
  AccessSubjectSearchResult,
  AccessSubjectType,
} from './taskAccessTypes';

type AccessSubjectSearchBoxProps = {
  searchResults: AccessSubjectSearchResult[];
  isLoading?: boolean;
  onSearchChange: (keyword: string) => void;
  onAddSubject: (subject: AccessSubjectItem) => void;
};

const FILTERS: Array<'ALL' | AccessSubjectType> = ['ALL', 'USER', 'ORGANIZATION', 'GROUP'];

const getFilterLabel = (filter: 'ALL' | AccessSubjectType) => {
  if (filter === 'ALL') return 'すべて';
  return getSubjectTypeLabel(filter);
};

export const AccessSubjectSearchBox = ({
  searchResults,
  isLoading = false,
  onSearchChange,
  onAddSubject,
}: AccessSubjectSearchBoxProps) => {
  const [keyword, setKeyword] = useState('');
  const [filterType, setFilterType] = useState<'ALL' | AccessSubjectType>('ALL');
  const [isFocused, setIsFocused] = useState(false);

  const closeTimerRef = useRef<number | null>(null);

  const filteredResults = useMemo(() => {
    if (filterType === 'ALL') return searchResults;
    return searchResults.filter((item) => item.subjectType === filterType);
  }, [searchResults, filterType]);

  const showPopover = isFocused && keyword.trim().length > 0;

  const handleChangeKeyword = (value: string) => {
    setKeyword(value);
    onSearchChange(value);
  };

  const handleFocus = () => {
    if (closeTimerRef.current) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    setIsFocused(true);
  };

  const handleBlur = () => {
    closeTimerRef.current = window.setTimeout(() => {
      setIsFocused(false);
    }, 150);
  };

  const handleAdd = (subject: AccessSubjectSearchResult) => {
    if (subject.alreadyAdded) return;

    onAddSubject({
      subjectType: subject.subjectType,
      refId: subject.refId,
      name: subject.name,
      description: subject.description,
    });

    setKeyword('');
    onSearchChange('');
    setIsFocused(false);
  };

  return (
    <section className="space-y-3">
      <div>
        <h3 className="text-sm font-semibold text-slate-900">追加する対象</h3>
        <p className="mt-1 text-xs text-slate-500">
          ユーザー、組織、グループを検索して追加します。追加時の権限はVIEWです。
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter}
            type="button"
            onClick={() => setFilterType(filter)}
            className={[
              'rounded-full border px-3 py-1 text-xs transition',
              filterType === filter
                ? 'border-slate-900 bg-slate-900 text-white'
                : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50',
            ].join(' ')}
          >
            {getFilterLabel(filter)}
          </button>
        ))}
      </div>

      <div className="relative">
        <input
          value={keyword}
          onChange={(event) => handleChangeKeyword(event.target.value)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder="名前・組織名・グループ名で検索"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
        />

        {showPopover && (
          <div className="absolute z-50 mt-2 max-h-72 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg">
            {isLoading ? (
              <div className="px-3 py-4 text-sm text-slate-500">検索中...</div>
            ) : filteredResults.length === 0 ? (
              <div className="px-3 py-4 text-sm text-slate-500">該当する対象がありません。</div>
            ) : (
              <ul className="py-1">
                {filteredResults.map((item) => (
                  <li key={`${item.subjectType}:${item.refId}`}>
                    <button
                      type="button"
                      disabled={item.alreadyAdded}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => handleAdd(item)}
                      className={[
                        'flex w-full items-center gap-3 px-3 py-2 text-left text-sm',
                        item.alreadyAdded
                          ? 'cursor-not-allowed bg-slate-50 text-slate-400'
                          : 'hover:bg-slate-50',
                      ].join(' ')}
                    >
                      <span className="text-base">{getSubjectIcon(item.subjectType)}</span>

                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{item.name}</span>
                        {item.description && (
                          <span className="block truncate text-xs text-slate-500">
                            {item.description}
                          </span>
                        )}
                      </span>

                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                        {getSubjectTypeLabel(item.subjectType)}
                      </span>

                      {item.alreadyAdded && (
                        <span className="text-xs text-slate-400">追加済み</span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
