/**
 * Strip leading YAML frontmatter (`---` … `---`) without Node-only APIs.
 * Used in the browser for developer MDX; avoids `gray-matter` (depends on Buffer).
 */
export function stripYamlFrontmatter(raw: string): string {
  const text = raw.replace(/^\uFEFF/, '')
  const lines = text.split(/\r?\n/)
  if (lines[0]?.trim() !== '---') return text
  for (let i = 1; i < lines.length; i++) {
    if (lines[i]?.trim() === '---') {
      return lines.slice(i + 1).join('\n')
    }
  }
  return text
}
