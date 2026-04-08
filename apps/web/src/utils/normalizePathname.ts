/** Strip trailing slashes for stable route comparisons (except root). */
export function normalizePathname(pathname: string): string {
  if (pathname === '/') return '/'
  const t = pathname.replace(/\/+$/, '')
  return t || '/'
}
