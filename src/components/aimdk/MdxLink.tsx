import { Link } from 'react-router-dom'

/** MDX anchor: internal paths use React Router; external use target=_blank. */
export function MdxLink({ href, children, ...rest }: React.ComponentProps<'a'>) {
  if (!href) return <a {...rest}>{children}</a>
  if (href.startsWith('http://') || href.startsWith('https://') || href.startsWith('mailto:')) {
    return (
      <a href={href} rel="noopener noreferrer" target="_blank" {...rest}>
        {children}
      </a>
    )
  }
  if (href.startsWith('/')) {
    return (
      <Link to={href} {...rest}>
        {children}
      </Link>
    )
  }
  return (
    <a href={href} {...rest}>
      {children}
    </a>
  )
}
