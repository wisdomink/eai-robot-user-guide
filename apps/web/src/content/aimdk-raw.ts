/**
 * Eager raw MDX sources for developer docs (path keys relative to this file).
 */
export const aimdkRawModules = import.meta.glob('./aimdk/content/**/*.mdx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

export function getAimdkRaw(contentFile: string): string {
  const key = `./aimdk/content/${contentFile}`
  return aimdkRawModules[key] ?? ''
}
