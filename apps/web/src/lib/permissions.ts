import type { UserProfile } from "@lexflow/shared";

export const PERM = {
  VIEW_CASES: "case:view",
  MANAGE_CLIENTS: "client:manage",
  CREATE_CASE: "case:create",
  REQUEST_AI: "ai:request",
  APPROVE_AI: "ai:approve",
  VIEW_AUDIT: "audit:read",
  OPERATIONS: "operations:dashboard",
  MANAGE_USERS: "admin:users",
  MANAGE_WORKFLOWS: "workflow:manage",
  PORTAL_ACCESS: "portal:access",
} as const;

export type Permission = (typeof PERM)[keyof typeof PERM];
export type LoginAudience = "enterprise" | "portal";

export const PORTAL_ROLE = "Client";

export function hasPermission(
  permissions: string[] | undefined,
  permission: Permission,
): boolean {
  return permissions?.includes(permission) ?? false;
}

export function canAccessEnterpriseDashboard(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.VIEW_CASES);
}

export function canAccessPortal(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.PORTAL_ACCESS);
}

export function isPortalUser(user: UserProfile | null | undefined): boolean {
  if (!user) return false;
  return canAccessPortal(user.permissions) && !canAccessEnterpriseDashboard(user.permissions);
}

export function isEnterpriseUser(user: UserProfile | null | undefined): boolean {
  if (!user) return false;
  return canAccessEnterpriseDashboard(user.permissions);
}

export function canCreateCase(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.CREATE_CASE);
}

export function canManageClients(permissions: string[] | undefined): boolean {
  return hasPermission(permissions, PERM.MANAGE_CLIENTS);
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
