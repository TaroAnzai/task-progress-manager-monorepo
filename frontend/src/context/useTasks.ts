import { useContext } from "react";

import { TaskContext } from "./TaskContextBase";

export const useTasks = () => {
  const ctx = useContext(TaskContext);
  if (!ctx) throw new Error("useTasks must be used within a TaskProvider");
  return ctx;
}
