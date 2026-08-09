export const AUTH_REDIRECT_PATH = '/studio'

// Arin currently has one post-auth destination. Ignore the query value so an
// attacker cannot turn login into an open redirect.
export function safeAuthRedirect(_requestedPath: string | null): string {
  return AUTH_REDIRECT_PATH
}
