import { createContext } from "react";

import type { UserWithScopes } from "@/api/generated/taskProgressAPI.schemas";

export interface UserContextType {
  user: UserWithScopes | null;
  loading: boolean;
  sessionError: unknown | null;
  refetchUser: () => void;
  hasAdminScope: () => boolean;
  hasSystemAdminScope: () => boolean;
  getUserRole: () => string;
}

export const UserContext = createContext<UserContextType>({
  user: null,
  loading: true,
  sessionError: null,
  refetchUser: () => {},
  hasAdminScope: () => false,
  hasSystemAdminScope: () => false,
  getUserRole: () => "",
});
