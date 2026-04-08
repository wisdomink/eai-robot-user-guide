import { Link } from 'react-router-dom'

export interface SdkLinkCardProps {
  title: string
  description?: string
  href: string
  platform?: string
}

/** AimDK download / link cards — eai styling only (not robotics). */
export function SdkLinkCard({ title, description, href, platform }: SdkLinkCardProps) {
  const external = href.startsWith('http://') || href.startsWith('https://')
  const internalDocs = href.startsWith('/docs/')
  const linkClass = 'font-medium text-black underline underline-offset-2 hover:opacity-70'
  return (
    <div className="not-prose my-4 rounded-xl border border-gray-200 bg-gray-50 p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-black">{title}</h3>
      {platform ? <p className="mt-1 text-sm text-black">{platform}</p> : null}
      {description ? <p className="mt-2 text-sm text-black">{description}</p> : null}
      <p className="mt-3">
        {external ? (
          <a href={href} className={linkClass} rel="noopener noreferrer" target="_blank">
            Open link →
          </a>
        ) : internalDocs ? (
          <Link to={href} className={linkClass}>
            Open page →
          </Link>
        ) : (
          <a href={href} className={linkClass}>
            Open page →
          </a>
        )}
      </p>
    </div>
  )
}
