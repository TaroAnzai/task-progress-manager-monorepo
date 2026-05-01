// src/utils/errorHandler.ts
const isObject = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null;

const firstStringDeep = (v: unknown): string | null => {
  if (typeof v === 'string') return v;
  if (Array.isArray(v)) {
    for (const item of v) {
      const s = firstStringDeep(item);
      if (s) return s;
    }
    return null;
  }
  if (isObject(v)) {
    for (const val of Object.values(v)) {
      const s = firstStringDeep(val);
      if (s) return s;
    }
  }
  return null;
};

export const extractErrorMessage = (error: unknown): string => {
  // axios 風: { response: { data: ... } } を構造で判定
  if (isObject(error) && 'response' in error) {
    const resp = (error as Record<string, unknown>).response;
    if (isObject(resp) && 'data' in resp) {
      const data = (resp as Record<string, unknown>).data;

      if (isObject(data)) {
        // marshmallow 風: { errors: {...} } 最初の文字列を深掘りで取得
        if ('errors' in data) {
          const msg = firstStringDeep((data as Record<string, unknown>).errors);
          if (msg) return msg;
        }
        // 一般的: { message: "..." } / { status: "..." }
        const message = (data as { message?: unknown }).message;
        if (typeof message === 'string') return message;

        const status = (data as { status?: unknown }).status;
        if (typeof status === 'string') return status;
      }
    }
  }

  // 標準的な Error
  if (error instanceof Error && typeof error.message === 'string') {
    return error.message;
  }

  return '不明なエラーが発生しました';
};
