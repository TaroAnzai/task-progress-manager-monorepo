import { createContext } from "react";

import type { UserWithScopes } from "@/api/generated/taskProgressAPI.schemas";

export interface UserContextType {
  user: UserWithScopes | null;
  loading: boolean;
  refetchUser: () => void;
  hasAdminScope: () => boolean;
  hasSystemAdminScope: () => boolean;
  getUserRole: () => string;
}

export const UserContext = createContext<UserContextType>({
  user: null,
  loading: true,
  refetchUser: () => {},
  hasAdminScope: () => false,
  hasSystemAdminScope: () => false,
  getUserRole: () => "",
});
