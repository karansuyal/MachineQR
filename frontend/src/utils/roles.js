export const ROLES = {
  ADMIN: "admin",
  TECHNICIAN: "technician",
  OPERATOR: "operator",
};

export const ROLE_OPTIONS = [
  { value: ROLES.ADMIN, label: "Admin" },
  { value: ROLES.TECHNICIAN, label: "Technician" },
  { value: ROLES.OPERATOR, label: "Operator" },
];

export const roleLabel = (role) => ROLE_OPTIONS.find((r) => r.value === role)?.label ?? role;
