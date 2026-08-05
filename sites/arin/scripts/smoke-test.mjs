import assert from 'node:assert/strict'
import { readFile, readdir } from 'node:fs/promises'
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join, relative } from 'node:path'

const projectRoot = join(dirname(fileURLToPath(import.meta.url)), '..')
const port = Number(process.env.SMOKE_PORT || 4173)
const baseUrl = `http://127.0.0.1:${port}`

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function waitForPreview(server) {
  const deadline = Date.now() + 8_000

  while (Date.now() < deadline) {
    if (server.exitCode !== null) {
      throw new Error(`vite preview exited before becoming ready (code ${server.exitCode})`)
    }

    try {
      const response = await fetch(`${baseUrl}/`)
      if (response.ok) return
    } catch {
      // The preview server is still starting.
    }

    await wait(100)
  }

  throw new Error(`timed out waiting for vite preview at ${baseUrl}`)
}

async function collectFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) {
      files.push(...await collectFiles(path))
    } else {
      files.push(path)
    }
  }

  return files
}

async function assertPage(pathname) {
  const response = await fetch(`${baseUrl}${pathname}`)
  const body = await response.text()

  assert.equal(response.status, 200, `${pathname} should return the SPA shell`)
  assert.match(response.headers.get('content-type') || '', /text\/html/)
  assert.match(body, /<div id="root"><\/div>/)
  assert.match(body, /Arin/)
}

const server = spawn('npm', ['exec', '--', 'vite', 'preview', '--host', '127.0.0.1', '--port', String(port), '--strictPort'], {
  cwd: projectRoot,
  stdio: 'ignore',
})

try {
  await waitForPreview(server)
  await assertPage('/')
  await assertPage('/docs/welcome')
  await assertPage('/auth')
  await assertPage('/studio')

  const bundleFiles = (await collectFiles(join(projectRoot, 'dist/assets'))).filter((path) => path.endsWith('.js'))
  const bundle = (await Promise.all(bundleFiles.map((path) => readFile(path, 'utf8')))).join('\n')
  assert.match(bundle, /Build your first app with Arin/)
  assert.match(bundle, /\/api\/projects/)
  assert.match(bundle, /Live preview/)
  assert.match(bundle, /Branding & SEO/)
  assert.match(bundle, /Publish/)

  const assetRoot = join(projectRoot, 'public', 'assets')
  const assetFiles = (await collectFiles(assetRoot)).filter((path) => /\.(?:svg|png|jpe?g|woff2)$/i.test(path))

  for (const file of assetFiles) {
    const assetPath = `/${relative(assetRoot, file).split('\\').join('/')}`
    const response = await fetch(`${baseUrl}/assets${assetPath}`)
    assert.equal(response.status, 200, `${assetPath} should be served locally`)
  }

  console.log(`Smoke test passed: ${assetFiles.length} local assets and 4 SPA routes verified.`)
} finally {
  server.kill('SIGTERM')
}
