export type UserRole = "customer" | "owner" | "staff" | "kitchen" | "driver";
export interface User { id: string; name: string; phone?: string; email?: string; role: UserRole; createdAt: string; }
