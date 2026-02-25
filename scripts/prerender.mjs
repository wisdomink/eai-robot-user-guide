import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const dist = path.resolve(root, 'dist')

// Read sidebar config to get all routes
const sidebar = JSON.parse(
  fs.readFileSync(path.resolve(root, 'src/content/sidebar.json'), 'utf-8')
)

// Collect all routes: home + all section pages
const routes = [
  { slug: '/', title: 'FF Master Ultra Edition' },
  ...sidebar.sections.flatMap(section =>
    section.pages.map(page => ({ slug: page.slug, title: page.title }))
  ),
]

// Load the SSR module
const { render } = await import(path.resolve(dist, 'server/entry-server.js'))

// Read the client-built index.html as template
const template = fs.readFileSync(path.resolve(dist, 'index.html'), 'utf-8')

console.log(`Pre-rendering ${routes.length} routes...\n`)

for (const route of routes) {
  const appHtml = render(route.slug)

  // Inject rendered HTML into template
  let html = template.replace('<!--ssr-outlet-->', appHtml)

  // Set page-specific <title>
  const pageTitle =
    route.slug === '/'
      ? 'EAI Robot - User Manual'
      : `${route.title} - EAI Robot Manual`
  html = html.replace(
    '<title>EAI Robot - User Manual</title>',
    `<title>${pageTitle}</title>`
  )

  // Write to dist/[slug]/index.html
  const filePath =
    route.slug === '/'
      ? path.resolve(dist, 'index.html')
      : path.resolve(dist, route.slug.slice(1), 'index.html')

  fs.mkdirSync(path.dirname(filePath), { recursive: true })
  fs.writeFileSync(filePath, html)

  console.log(`  ✓ ${route.slug} → ${path.relative(dist, filePath)}`)
}

console.log(`\nDone! ${routes.length} pages pre-rendered.`)
