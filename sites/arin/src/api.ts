export type User = {
  id: string
  email: string
  name: string
}

export type Session = {
  user: User
  csrf_token: string
  expires_at: string
}

export type Workspace = {
  id: string
  name: string
  slug: string
  role: 'owner' | 'editor' | 'viewer'
}

export type Project = {
  id: string
  workspace_id: string
  name: string
  slug: string
  prompt: string
  category: string
  status: 'draft' | 'published' | 'archived'
  current_version_id: string | null
  settings: Record<string, string>
  files?: Record<string, string>
  created_at: string
  updated_at: string
}

export type Asset = {
  id: string
  project_id: string
  original_name: string
  storage_name: string
  mime_type: string
  size_bytes: number
  created_at: string
  url: string
}

export type Connector = {
  id: string
  project_id: string
  kind: string
  label: string
  status: 'active' | 'disabled' | 'error'
  created_at: string
  updated_at: string
}

export type AgentMessage = {
  id: string
  project_id: string
  user_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  version_id: string | null
  created_at: string
}

export type ProjectVersion = {
  id: string
  version_number: number
  source: string
  created_by: string
  created_at: string
}

export type Invite = {
  id: string
  workspace_id: string
  email: string
  role: 'editor' | 'viewer'
  expires_at: string
  accepted_at: string | null
  created_at: string
  token?: string
}

export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

let csrfToken = ''

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  const method = (init.method ?? 'GET').toUpperCase()
  const isAuthBootstrap = path === '/api/auth/register' || path === '/api/auth/login'
  if (method !== 'GET' && method !== 'HEAD') {
    headers.set('Content-Type', 'application/json')
    if (!isAuthBootstrap && csrfToken) headers.set('X-CSRF-Token', csrfToken)
  }

  const response = await fetch(path, { ...init, headers, credentials: 'include' })
  const contentType = response.headers.get('Content-Type') ?? ''
  const payload = contentType.includes('application/json')
    ? await response.json() as Record<string, unknown>
    : null
  if (!response.ok) {
    const error = payload?.error as { code?: string; message?: string } | undefined
    throw new ApiError(response.status, error?.code ?? 'request_failed', error?.message ?? 'Request failed')
  }
  if (payload && typeof payload.csrf_token === 'string') csrfToken = payload.csrf_token
  return payload as T
}

function jsonBody(value: unknown): RequestInit {
  return { method: 'POST', body: JSON.stringify(value) }
}

function putJson(value: unknown): RequestInit {
  return { method: 'PUT', body: JSON.stringify(value) }
}

function base64FromBytes(bytes: Uint8Array): string {
  let result = ''
  const chunkSize = 0x8000
  for (let index = 0; index < bytes.length; index += chunkSize) {
    result += String.fromCharCode(...bytes.subarray(index, index + chunkSize))
  }
  return btoa(result)
}

export const api = {
  async register(email: string, name: string, password: string) {
    return request<{ user: User }>('/api/auth/register', jsonBody({ email, name, password }))
  },

  async login(email: string, password: string) {
    return request<{ user: User; csrf_token: string; expires_at: string }>(
      '/api/auth/login',
      jsonBody({ email, password }),
    )
  },

  async session() {
    return request<Session>('/api/auth/session')
  },

  async logout() {
    const result = await request<void>('/api/auth/logout', jsonBody({}))
    csrfToken = ''
    return result
  },

  async workspaces() {
    return request<{ workspaces: Workspace[] }>('/api/workspaces')
  },

  async createWorkspace(name: string) {
    return request<{ workspace: Workspace }>('/api/workspaces', jsonBody({ name }))
  },

  async members(workspaceId: string) {
    return request<{ members: Array<User & { role: Workspace['role']; created_at: string }> }>(
      `/api/workspaces/${encodeURIComponent(workspaceId)}/members`,
    )
  },

  async projects(workspaceId?: string) {
    const suffix = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ''
    return request<{ projects: Project[] }>(`/api/projects${suffix}`)
  },

  async project(projectId: string) {
    return request<{ project: Project }>(`/api/projects/${encodeURIComponent(projectId)}`)
  },

  async createProject(workspaceId: string, prompt: string, category: string) {
    return request<{ project: Project }>(
      '/api/projects',
      jsonBody({ workspace_id: workspaceId, prompt, category }),
    )
  },

  async buildProject(projectId: string, prompt: string) {
    return request<{ project: Project }>(
      `/api/projects/${encodeURIComponent(projectId)}/build`,
      jsonBody({ prompt }),
    )
  },

  async updateFile(projectId: string, path: string, content: string) {
    return request<{ version: Record<string, unknown> }>(
      `/api/projects/${encodeURIComponent(projectId)}/files/${encodeURIComponent(path)}`,
      putJson({ content }),
    )
  },

  async versions(projectId: string) {
    return request<{ versions: ProjectVersion[] }>(`/api/projects/${encodeURIComponent(projectId)}/versions`)
  },

  async restoreVersion(projectId: string, versionId: string) {
    return request<{ version: ProjectVersion }>(
      `/api/projects/${encodeURIComponent(projectId)}/versions/${encodeURIComponent(versionId)}/restore`,
      jsonBody({}),
    )
  },

  async preview(projectId: string) {
    return `/preview/${encodeURIComponent(projectId)}`
  },

  async publish(projectId: string) {
    return request<{ deployment: { slug: string; status: string } }>(
      `/api/projects/${encodeURIComponent(projectId)}/publish`,
      jsonBody({}),
    )
  },

  async unpublish(projectId: string) {
    return request<void>(`/api/projects/${encodeURIComponent(projectId)}/unpublish`, jsonBody({}))
  },

  async settings(projectId: string, settings: Record<string, string>) {
    return request<{ settings: Record<string, string> }>(
      `/api/projects/${encodeURIComponent(projectId)}/settings`,
      putJson({ settings }),
    )
  },

  async assets(projectId: string) {
    return request<{ assets: Asset[] }>(`/api/projects/${encodeURIComponent(projectId)}/assets`)
  },

  async uploadAsset(projectId: string, file: File) {
    const bytes = new Uint8Array(await file.arrayBuffer())
    return request<{ asset: Asset }>(
      `/api/projects/${encodeURIComponent(projectId)}/assets`,
      jsonBody({ filename: file.name, mime_type: file.type, data_base64: base64FromBytes(bytes) }),
    )
  },

  async connectors(projectId: string) {
    return request<{ connectors: Connector[] }>(`/api/projects/${encodeURIComponent(projectId)}/connectors`)
  },

  async createConnector(projectId: string, kind: string, label: string, config: Record<string, string>) {
    return request<{ connector: Connector }>(
      `/api/projects/${encodeURIComponent(projectId)}/connectors`,
      jsonBody({ kind, label, config }),
    )
  },

  async messages(projectId: string) {
    return request<{ messages: AgentMessage[] }>(`/api/projects/${encodeURIComponent(projectId)}/messages`)
  },

  async addMessage(projectId: string, content: string, role: AgentMessage['role'] = 'user') {
    return request<{ message: AgentMessage }>(
      `/api/projects/${encodeURIComponent(projectId)}/messages`,
      jsonBody({ role, content }),
    )
  },

  async invites(workspaceId: string) {
    return request<{ invites: Invite[] }>(`/api/workspaces/${encodeURIComponent(workspaceId)}/invites`)
  },

  async invite(workspaceId: string, email: string, role: Invite['role']) {
    return request<{ invite: Invite }>(
      `/api/workspaces/${encodeURIComponent(workspaceId)}/invites`,
      jsonBody({ email, role }),
    )
  },
}
