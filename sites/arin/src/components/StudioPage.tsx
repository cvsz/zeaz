import { useEffect, useMemo, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { ApiError, api, type AgentMessage, type Asset, type Connector, type Invite, type Project, type ProjectVersion, type User, type Workspace } from '../api'
import { categories } from '../data'

type StudioTab = 'build' | 'files' | 'settings' | 'team'

function projectIdFromPath() {
  const match = window.location.pathname.match(/^\/studio\/([^/]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

function readableError(error: unknown) {
  return error instanceof ApiError ? error.message : 'Something went wrong. Please try again.'
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function StudioPage() {
  const [user, setUser] = useState<User | null>(null)
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState(projectIdFromPath())
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [assets, setAssets] = useState<Asset[]>([])
  const [versions, setVersions] = useState<ProjectVersion[]>([])
  const [connectors, setConnectors] = useState<Connector[]>([])
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [members, setMembers] = useState<Array<User & { role: Workspace['role']; created_at: string }>>([])
  const [invites, setInvites] = useState<Invite[]>([])
  const [activeTab, setActiveTab] = useState<StudioTab>('build')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [workspaceName, setWorkspaceName] = useState('')
  const [newPrompt, setNewPrompt] = useState('')
  const [newCategory, setNewCategory] = useState(categories[0].id)
  const [filePath, setFilePath] = useState('index.html')
  const [fileContent, setFileContent] = useState('')
  const [settingsDraft, setSettingsDraft] = useState<Record<string, string>>({})
  const [messageDraft, setMessageDraft] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<Invite['role']>('viewer')
  const [inviteToken, setInviteToken] = useState('')
  const [connectorKind, setConnectorKind] = useState('webhook')
  const [connectorLabel, setConnectorLabel] = useState('')
  const [connectorUrl, setConnectorUrl] = useState('')
  const [connectorSecret, setConnectorSecret] = useState('')

  const selectedWorkspace = useMemo(() => {
    if (!selectedProject) return workspaces[0] ?? null
    return workspaces.find((workspace) => workspace.id === selectedProject.workspace_id) ?? null
  }, [selectedProject, workspaces])

  useEffect(() => {
    document.title = 'Studio — Arin'
    let active = true
    async function load() {
      try {
        const session = await api.session()
        if (!active) return
        setUser(session.user)
        const workspaceResponse = await api.workspaces()
        if (!active) return
        setWorkspaces(workspaceResponse.workspaces)
        const projectResponse = await api.projects()
        if (!active) return
        setProjects(projectResponse.projects)
        if (!selectedProjectId && projectResponse.projects[0]) setSelectedProjectId(projectResponse.projects[0].id)
      } catch (caught) {
        if (caught instanceof ApiError && caught.status === 401) {
          window.location.assign('/auth?next=/studio')
          return
        }
        if (active) setError(readableError(caught))
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => { active = false }
  }, [selectedProjectId])

  useEffect(() => {
    if (!selectedProjectId) {
      setSelectedProject(null)
      return
    }
    let active = true
    async function loadProject() {
      try {
        const [projectResponse, assetResponse, connectorResponse, messageResponse, versionResponse] = await Promise.all([
          api.project(selectedProjectId),
          api.assets(selectedProjectId),
          api.connectors(selectedProjectId),
          api.messages(selectedProjectId),
          api.versions(selectedProjectId),
        ])
        if (!active) return
        setSelectedProject(projectResponse.project)
        setAssets(assetResponse.assets)
        setConnectors(connectorResponse.connectors)
        setMessages(messageResponse.messages)
        setVersions(versionResponse.versions)
        const firstFile = Object.keys(projectResponse.project.files ?? {})[0] ?? 'index.html'
        setFilePath(firstFile)
        setFileContent(projectResponse.project.files?.[firstFile] ?? '')
        setSettingsDraft(projectResponse.project.settings ?? {})
        const workspace = workspaces.find((item) => item.id === projectResponse.project.workspace_id)
        if (workspace) await loadTeam(workspace.id, active)
      } catch (caught) {
        if (active) setError(readableError(caught))
      }
    }
    void loadProject()
    return () => { active = false }
  // Workspace membership is needed to load the team panel, but project changes are the trigger.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProjectId])

  useEffect(() => {
    const nextContent = selectedProject?.files?.[filePath]
    if (typeof nextContent === 'string') setFileContent(nextContent)
  }, [filePath, selectedProject])

  async function loadTeam(workspaceId: string, active = true) {
    try {
      const [memberResponse, inviteResponse] = await Promise.all([
        api.members(workspaceId),
        api.invites(workspaceId),
      ])
      if (active) {
        setMembers(memberResponse.members)
        setInvites(inviteResponse.invites)
      }
    } catch (caught) {
      if (active && !(caught instanceof ApiError && caught.status === 403)) setError(readableError(caught))
    }
  }

  function selectProject(projectId: string) {
    setSelectedProjectId(projectId)
    window.history.pushState({}, '', `/studio/${encodeURIComponent(projectId)}`)
  }

  async function refreshProjects(workspaceId?: string) {
    const response = await api.projects(workspaceId)
    setProjects(response.projects)
    return response.projects
  }

  async function handleCreateWorkspace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!workspaceName.trim() || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await api.createWorkspace(workspaceName.trim())
      setWorkspaces((current) => [...current, response.workspace])
      setWorkspaceName('')
      setStatus('Workspace created.')
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const workspace = selectedWorkspace ?? workspaces[0]
    if (!workspace || !newPrompt.trim() || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await api.createProject(workspace.id, newPrompt.trim(), newCategory)
      setProjects((current) => [response.project, ...current])
      setNewPrompt('')
      selectProject(response.project.id)
      setActiveTab('build')
      setStatus('Draft generated. Review it in the live preview.')
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleBuild(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedProject || !newPrompt.trim() || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await api.buildProject(selectedProject.id, newPrompt.trim())
      setSelectedProject(response.project)
      setProjects((current) => current.map((project) => project.id === response.project.id ? response.project : project))
      setStatus('New version generated. The preview is ready.')
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleSaveFile() {
    if (!selectedProject || busy) return
    setBusy(true)
    setError('')
    try {
      await api.updateFile(selectedProject.id, filePath, fileContent)
      const response = await api.project(selectedProject.id)
      setSelectedProject(response.project)
      setProjects((current) => current.map((project) => project.id === response.project.id ? response.project : project))
      setStatus(`Saved ${filePath} as a new version.`)
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleRestore(versionId: string) {
    if (!selectedProject || busy) return
    setBusy(true)
    setError('')
    try {
      await api.restoreVersion(selectedProject.id, versionId)
      const [projectResponse, versionResponse] = await Promise.all([
        api.project(selectedProject.id),
        api.versions(selectedProject.id),
      ])
      setSelectedProject(projectResponse.project)
      setProjects((current) => current.map((project) => project.id === projectResponse.project.id ? projectResponse.project : project))
      setVersions(versionResponse.versions)
      setStatus(`Restored version ${versionResponse.versions[0]?.version_number ?? ''}.`)
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedProject || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await api.settings(selectedProject.id, settingsDraft)
      setSettingsDraft(response.settings)
      setSelectedProject((current) => current ? { ...current, settings: response.settings } : current)
      setStatus('Branding and SEO settings saved.')
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handlePublish() {
    if (!selectedProject || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await api.publish(selectedProject.id)
      setSelectedProject((current) => current ? { ...current, status: 'published' } : current)
      setProjects((current) => current.map((project) => project.id === selectedProject.id ? { ...project, status: 'published' } : project))
      setStatus(`Published at /app/${response.deployment.slug}`)
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file || !selectedProject) return
    if (file.size > 5 * 1024 * 1024) {
      setError('Assets must be 5 MB or smaller.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const response = await api.uploadAsset(selectedProject.id, file)
      setAssets((current) => [response.asset, ...current])
      setStatus(`${file.name} uploaded.`)
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
      event.target.value = ''
    }
  }

  async function handleMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedProject || !messageDraft.trim() || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await api.addMessage(selectedProject.id, messageDraft.trim())
      setMessages((current) => [...current, response.message])
      setMessageDraft('')
      setStatus('Agent instruction saved to project history.')
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleConnector(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedProject || !connectorLabel.trim() || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await api.createConnector(selectedProject.id, connectorKind, connectorLabel.trim(), {
        url: connectorUrl.trim(),
        secret: connectorSecret,
      })
      setConnectors((current) => [response.connector, ...current])
      setConnectorLabel('')
      setConnectorUrl('')
      setConnectorSecret('')
      setStatus('Connector saved securely.')
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedWorkspace || !inviteEmail.trim() || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await api.invite(selectedWorkspace.id, inviteEmail.trim(), inviteRole)
      setInvites((current) => [{ ...response.invite, token: undefined }, ...current])
      setInviteToken(response.invite.token ?? '')
      setInviteEmail('')
      setStatus('Invite created. Copy the token from the secure response if you need to deliver it manually.')
    } catch (caught) {
      setError(readableError(caught))
    } finally {
      setBusy(false)
    }
  }

  async function handleWorkspaceChange(event: ChangeEvent<HTMLSelectElement>) {
    const workspaceId = event.target.value
    try {
      const nextProjects = await refreshProjects(workspaceId)
      if (nextProjects[0]) selectProject(nextProjects[0].id)
      else setSelectedProject(null)
    } catch (caught) {
      setError(readableError(caught))
    }
  }

  async function handleLogout() {
    try {
      await api.logout()
    } finally {
      window.location.assign('/')
    }
  }

  if (loading) {
    return <main className="studio-loading"><span className="loading-orbit" aria-hidden="true" />Loading your workspace…</main>
  }

  return (
    <main className="studio-shell">
      <aside className="studio-sidebar" aria-label="Arin workspace navigation">
        <div className="studio-sidebar__top">
          <a className="studio-brand" href="/" aria-label="Arin home">
            <span className="brand__mark" aria-hidden="true"><img src="/assets/logo.svg" alt="" /></span>
            <span>Arin</span>
          </a>
          <span className="studio-label">Studio</span>
        </div>

        <label className="studio-field studio-field--small">
          <span>Workspace</span>
          <select value={selectedWorkspace?.id ?? ''} onChange={handleWorkspaceChange} disabled={!workspaces.length}>
            {!workspaces.length && <option value="">No workspace yet</option>}
            {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
          </select>
        </label>

        <div className="studio-sidebar__section-heading">
          <span>Projects</span>
          <span>{projects.length}</span>
        </div>
        <nav className="project-list" aria-label="Projects">
          {projects.map((project) => (
            <button key={project.id} type="button" className={project.id === selectedProjectId ? 'is-active' : ''} onClick={() => selectProject(project.id)}>
              <span className="project-list__dot" data-status={project.status} aria-hidden="true" />
              <span>{project.settings?.title || project.name}</span>
              <small>{project.category}</small>
            </button>
          ))}
          {!projects.length && <p className="studio-empty studio-empty--sidebar">Create a project to see it here.</p>}
        </nav>

        <div className="studio-sidebar__bottom">
          <div className="studio-user"><span className="avatar">{user?.name.slice(0, 1).toUpperCase()}</span><span><strong>{user?.name}</strong><small>{user?.email}</small></span></div>
          <button className="sidebar-link" type="button" onClick={() => void handleLogout()}>Log out <span aria-hidden="true">↗</span></button>
        </div>
      </aside>

      <section className="studio-main">
        <header className="studio-topbar">
          <div><span className="studio-kicker">Workspace / {selectedWorkspace?.name ?? 'New workspace'}</span><h1>{selectedProject ? (selectedProject.settings?.title || selectedProject.name) : 'Your app studio'}</h1></div>
          {selectedProject && <div className="studio-topbar__actions"><span className={`status-chip status-chip--${selectedProject.status}`}>{selectedProject.status}</span><button className="button button--primary button--compact" type="button" onClick={() => void handlePublish()} disabled={busy || selectedProject.status === 'published'}>{selectedProject.status === 'published' ? 'Published' : 'Publish'} <span aria-hidden="true">↗</span></button></div>}
        </header>

        {error && <div className="studio-alert studio-alert--error" role="alert">{error}<button type="button" onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}
        {status && <div className="studio-alert" role="status">{status}<button type="button" onClick={() => setStatus('')} aria-label="Dismiss status">×</button></div>}

        {!workspaces.length && (
          <section className="studio-onboarding panel-card">
            <span className="studio-kicker">First step</span>
            <h2>Create a workspace for your team.</h2>
            <p>Projects, versions, assets, and invitations are scoped to a workspace so your work stays organized.</p>
            <form className="inline-form" onSubmit={handleCreateWorkspace}><input value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} placeholder="e.g. Acme Operations" aria-label="Workspace name" required /><button className="button button--primary" type="submit" disabled={busy}>Create workspace</button></form>
          </section>
        )}

        {workspaces.length > 0 && !selectedProject && (
          <section className="studio-create panel-card">
            <span className="studio-kicker">New project</span>
            <h2>What should Arin build?</h2>
            <p>Describe a useful business app. Arin creates an editable draft with a live preview and version history.</p>
            <form className="new-project-form" onSubmit={handleCreateProject}>
              <textarea value={newPrompt} onChange={(event) => setNewPrompt(event.target.value)} placeholder="Build a customer portal where clients can see project status and send updates…" rows={4} required maxLength={10000} />
              <div className="new-project-form__footer"><select value={newCategory} onChange={(event) => setNewCategory(event.target.value)} aria-label="Project category">{categories.map((category) => <option key={category.id} value={category.id}>{category.label}</option>)}</select><button className="button button--primary" type="submit" disabled={busy}>Generate draft <span aria-hidden="true">→</span></button></div>
            </form>
          </section>
        )}

        {selectedProject && (
          <div className="studio-workspace">
            <nav className="studio-tabs" aria-label="Project tools">
              {(['build', 'files', 'settings', 'team'] as StudioTab[]).map((tab) => <button type="button" key={tab} className={activeTab === tab ? 'is-active' : ''} onClick={() => setActiveTab(tab)}>{tab === 'build' ? 'Build' : tab === 'files' ? 'Files & preview' : tab === 'settings' ? 'Branding & SEO' : 'Team & connectors'}</button>)}
            </nav>

            {activeTab === 'build' && <BuildPanel project={selectedProject} prompt={newPrompt} setPrompt={setNewPrompt} onSubmit={handleBuild} busy={busy} messages={messages} messageDraft={messageDraft} setMessageDraft={setMessageDraft} onMessage={handleMessage} />}
            {activeTab === 'files' && <FilesPanel project={selectedProject} filePath={filePath} setFilePath={setFilePath} fileContent={fileContent} setFileContent={setFileContent} onSave={handleSaveFile} assets={assets} onUpload={handleUpload} versions={versions} onRestore={handleRestore} busy={busy} />}
            {activeTab === 'settings' && <SettingsPanel draft={settingsDraft} setDraft={setSettingsDraft} onSubmit={handleSettings} busy={busy} />}
            {activeTab === 'team' && <TeamPanel workspace={selectedWorkspace} members={members} invites={invites} inviteToken={inviteToken} setInviteToken={setInviteToken} inviteEmail={inviteEmail} setInviteEmail={setInviteEmail} inviteRole={inviteRole} setInviteRole={setInviteRole} onInvite={handleInvite} connectors={connectors} connectorKind={connectorKind} setConnectorKind={setConnectorKind} connectorLabel={connectorLabel} setConnectorLabel={setConnectorLabel} connectorUrl={connectorUrl} setConnectorUrl={setConnectorUrl} connectorSecret={connectorSecret} setConnectorSecret={setConnectorSecret} onConnector={handleConnector} busy={busy} />}
          </div>
        )}
      </section>
    </main>
  )
}

type BuildPanelProps = {
  project: Project
  prompt: string
  setPrompt: (value: string) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  busy: boolean
  messages: AgentMessage[]
  messageDraft: string
  setMessageDraft: (value: string) => void
  onMessage: (event: FormEvent<HTMLFormElement>) => void
}

function BuildPanel({ project, prompt, setPrompt, onSubmit, busy, messages, messageDraft, setMessageDraft, onMessage }: BuildPanelProps) {
  return (
    <div className="build-layout">
      <section className="builder-column">
        <div className="panel-card builder-card">
          <div className="panel-card__heading"><div><span className="studio-kicker">Prompt builder</span><h2>Keep shaping the product.</h2></div><span className="version-badge">Version {project.current_version_id ? 'ready' : 'new'}</span></div>
          <form onSubmit={onSubmit}>
            <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={7} maxLength={10000} aria-label="Project build prompt" placeholder="Tell Arin what to change…" required />
            <div className="builder-card__footer"><span>{project.category} app · immutable versions</span><button className="button button--primary" type="submit" disabled={busy}>{busy ? 'Generating…' : 'Generate next version'} <span aria-hidden="true">→</span></button></div>
          </form>
        </div>
        <form className="panel-card agent-card" onSubmit={onMessage}>
          <div className="panel-card__heading"><div><span className="studio-kicker">Agent history</span><h2>Leave an instruction.</h2></div><span className="count-badge">{messages.length}</span></div>
          <div className="message-history">{messages.length ? messages.map((message) => <div className={`message-bubble message-bubble--${message.role}`} key={message.id}><span>{message.role}</span><p>{message.content}</p></div>) : <p className="studio-empty">No instructions yet. Describe the next change for the project.</p>}</div>
          <div className="message-compose"><input value={messageDraft} onChange={(event) => setMessageDraft(event.target.value)} placeholder="e.g. Make the dashboard easier to scan…" maxLength={32000} /><button className="button button--soft button--compact" type="submit" disabled={busy || !messageDraft.trim()}>Save</button></div>
        </form>
      </section>
      <section className="preview-column panel-card"><div className="panel-card__heading"><div><span className="studio-kicker">Live preview</span><h2>Safe, isolated draft</h2></div><span className="preview-dot"><i /> Online</span></div><div className="preview-frame-wrap"><iframe title="Project live preview" className="preview-frame" src={`/preview/${encodeURIComponent(project.id)}?version=${encodeURIComponent(project.current_version_id ?? '')}`} sandbox="allow-scripts allow-forms" /></div><p className="panel-help">The generated app runs in a sandboxed frame and cannot access your Arin session.</p></section>
    </div>
  )
}

type FilesPanelProps = {
  project: Project
  filePath: string
  setFilePath: (value: string) => void
  fileContent: string
  setFileContent: (value: string) => void
  onSave: () => void
  assets: Asset[]
  onUpload: (event: ChangeEvent<HTMLInputElement>) => void
  versions: ProjectVersion[]
  onRestore: (versionId: string) => void
  busy: boolean
}

function FilesPanel({ project, filePath, setFilePath, fileContent, setFileContent, onSave, assets, onUpload, versions, onRestore, busy }: FilesPanelProps) {
  const files = Object.keys(project.files ?? {})
  return (
    <div className="files-layout">
      <section className="panel-card code-card"><div className="panel-card__heading"><div><span className="studio-kicker">Versioned files</span><h2>Edit the generated app.</h2></div><button className="button button--primary button--compact" type="button" onClick={onSave} disabled={busy}>Save version</button></div><div className="code-editor"><nav aria-label="Project files">{files.map((path) => <button type="button" key={path} className={filePath === path ? 'is-active' : ''} onClick={() => setFilePath(path)}>{path}</button>)}</nav><textarea value={fileContent} onChange={(event) => setFileContent(event.target.value)} spellCheck={false} aria-label={`${filePath} source`} /></div></section>
      <section className="panel-card asset-card"><div className="panel-card__heading"><div><span className="studio-kicker">Assets</span><h2>Bring your brand in.</h2></div><label className="button button--soft button--compact">Upload<input type="file" accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml,image/avif,application/pdf" onChange={onUpload} hidden /></label></div><p className="panel-help">Images and PDFs up to 5 MB. Files are stored outside the public filesystem and only exposed to published projects.</p><div className="asset-list">{assets.map((asset) => <div className="asset-row" key={asset.id}><span className="asset-icon">{asset.mime_type.startsWith('image/') ? '▧' : '□'}</span><span><strong>{asset.original_name}</strong><small>{formatBytes(asset.size_bytes)}</small></span><a href={asset.url} target="_blank" rel="noreferrer">Open</a></div>)}{!assets.length && <p className="studio-empty">No assets uploaded yet.</p>}</div><div className="version-history"><div className="version-history__heading"><span className="studio-kicker">Version history</span><span>{versions.length}</span></div>{versions.map((version) => <div className="version-row" key={version.id}><span><strong>v{version.version_number}</strong><small>{version.source} · {new Date(version.created_at).toLocaleString()}</small></span><button type="button" onClick={() => onRestore(version.id)} disabled={busy || version.id === project.current_version_id}>Restore</button></div>)}</div></section>
    </div>
  )
}

type SettingsPanelProps = { draft: Record<string, string>; setDraft: (value: Record<string, string>) => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; busy: boolean }

function SettingsPanel({ draft, setDraft, onSubmit, busy }: SettingsPanelProps) {
  function update(key: string, value: string) { setDraft({ ...draft, [key]: value }) }
  return <form className="panel-card settings-card" onSubmit={onSubmit}><div className="panel-card__heading"><div><span className="studio-kicker">Branding & SEO</span><h2>Make the app feel like yours.</h2></div><button className="button button--primary button--compact" type="submit" disabled={busy}>Save settings</button></div><p className="panel-help">These values are stored with the project and become the public app’s title and description.</p><div className="settings-grid"><label><span>App title</span><input value={draft.title ?? ''} onChange={(event) => update('title', event.target.value)} maxLength={160} required /></label><label><span>SEO title</span><input value={draft.seo_title ?? ''} onChange={(event) => update('seo_title', event.target.value)} maxLength={160} placeholder="Optional search title" /></label><label className="settings-grid__wide"><span>Description</span><textarea value={draft.description ?? ''} onChange={(event) => update('description', event.target.value)} maxLength={500} rows={3} /></label><label className="settings-grid__wide"><span>SEO description</span><textarea value={draft.seo_description ?? ''} onChange={(event) => update('seo_description', event.target.value)} maxLength={320} rows={3} /></label><label><span>Primary color</span><input value={draft.primary_color ?? '#3039f4'} onChange={(event) => update('primary_color', event.target.value)} pattern="#[0-9a-fA-F]{6}" /></label><label><span>Accent color</span><input value={draft.accent_color ?? '#f59e0b'} onChange={(event) => update('accent_color', event.target.value)} pattern="#[0-9a-fA-F]{6}" /></label></div></form>
}

type TeamPanelProps = { workspace: Workspace | null; members: Array<User & { role: Workspace['role']; created_at: string }>; invites: Invite[]; inviteToken: string; setInviteToken: (value: string) => void; inviteEmail: string; setInviteEmail: (value: string) => void; inviteRole: Invite['role']; setInviteRole: (value: Invite['role']) => void; onInvite: (event: FormEvent<HTMLFormElement>) => void; connectors: Connector[]; connectorKind: string; setConnectorKind: (value: string) => void; connectorLabel: string; setConnectorLabel: (value: string) => void; connectorUrl: string; setConnectorUrl: (value: string) => void; connectorSecret: string; setConnectorSecret: (value: string) => void; onConnector: (event: FormEvent<HTMLFormElement>) => void; busy: boolean }

function TeamPanel({ workspace, members, invites, inviteToken, setInviteToken, inviteEmail, setInviteEmail, inviteRole, setInviteRole, onInvite, connectors, connectorKind, setConnectorKind, connectorLabel, setConnectorLabel, connectorUrl, setConnectorUrl, connectorSecret, setConnectorSecret, onConnector, busy }: TeamPanelProps) {
  return <div className="team-layout"><section className="panel-card team-card"><div className="panel-card__heading"><div><span className="studio-kicker">Workspace team</span><h2>Build together.</h2></div><span className="count-badge">{members.length}</span></div><div className="member-list">{members.map((member) => <div className="member-row" key={member.id}><span className="avatar avatar--small">{member.name.slice(0, 1).toUpperCase()}</span><span><strong>{member.name}</strong><small>{member.email}</small></span><em>{member.role}</em></div>)}</div>{workspace?.role === 'owner' ? <form className="invite-form" onSubmit={onInvite}><h3>Invite a teammate</h3><div className="form-row"><input type="email" value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} placeholder="teammate@example.com" required /><select value={inviteRole} onChange={(event) => setInviteRole(event.target.value as Invite['role'])}><option value="viewer">Viewer</option><option value="editor">Editor</option></select><button className="button button--primary button--compact" type="submit" disabled={busy}>Invite</button></div></form> : <p className="panel-help">Only workspace owners can create invitations.</p>}{inviteToken && <div className="invite-token"><span>One-time invite token</span><code>{inviteToken}</code><button type="button" onClick={() => { void navigator.clipboard?.writeText(inviteToken); setInviteToken('') }}>Copy and hide</button></div>}<div className="invite-list">{invites.map((invite) => <div className="invite-row" key={invite.id}><span>{invite.email}</span><small>{invite.accepted_at ? 'Accepted' : `Pending · ${invite.role}`}</small></div>)}</div></section><section className="panel-card connector-card"><div className="panel-card__heading"><div><span className="studio-kicker">Connectors</span><h2>Keep your tools in sync.</h2></div><span className="count-badge">{connectors.length}</span></div><p className="panel-help">Connector credentials are encrypted at rest and never returned to the browser after creation.</p><form className="connector-form" onSubmit={onConnector}><div className="form-row"><select value={connectorKind} onChange={(event) => setConnectorKind(event.target.value)}><option value="webhook">Webhook</option><option value="rest_api">REST API</option><option value="stripe">Stripe</option><option value="notion">Notion</option><option value="github">GitHub</option></select><input value={connectorLabel} onChange={(event) => setConnectorLabel(event.target.value)} placeholder="Connector label" required /></div><input type="url" value={connectorUrl} onChange={(event) => setConnectorUrl(event.target.value)} placeholder="https://example.com/endpoint" /><input type="password" value={connectorSecret} onChange={(event) => setConnectorSecret(event.target.value)} placeholder="Secret (encrypted)" /><button className="button button--soft" type="submit" disabled={busy}>Save connector</button></form><div className="connector-list">{connectors.map((connector) => <div className="connector-row" key={connector.id}><span className="connector-mark">⌁</span><span><strong>{connector.label}</strong><small>{connector.kind}</small></span><em>{connector.status}</em></div>)}</div></section></div>
}
