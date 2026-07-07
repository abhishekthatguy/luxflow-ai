export const PERM = {
  CREATE_CASE: "case:create",
  REQUEST_AI: "ai:request",
  APPROVE_AI: "ai:approve",
  VIEW_AUDIT: "audit:read",
  OPERATIONS: "operations:dashboard",
  MANAGE_USERS: "admin:users",
  MANAGE_WORKFLOWS: "workflow:manage",
} as const;

export type Permission = (typeof PERM)[keyof typeof PERM];

export function hasPermission(
  permissions: string[] | undefined,
  permission: Permission,
): boolean {
  return permissions?.includes(permission) ?? false;
}

export function canCreateCase(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.CREATE_CASE);
}

export function canRequestAi(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.REQUEST_AI);
}

export function canApproveAi(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.APPROVE_AI);
}

export function canViewOperations(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.OPERATIONS);
}

export function canManageWorkflows(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.MANAGE_WORKFLOWS);
}

export function canManageUsers(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.MANAGE_USERS);
}

export function canViewAudit(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.VIEW_AUDIT);
}
