/** MDX image — standard img for docs (no next/image). */
export function MdxImg(props: React.ImgHTMLAttributes<HTMLImageElement>) {
  const { src, alt, className, ...rest } = props
  if (!src || typeof src !== 'string') return null
  return (
    <img
      src={src}
      alt={alt ?? ''}
      className={className ?? 'max-w-full rounded-lg border border-gray-200'}
      {...rest}
    />
  )
}
