import { useMemo } from 'react'
import { Fragment, jsx, jsxs } from 'react/jsx-runtime'
import { evaluateSync } from '@mdx-js/mdx'
import remarkGfm from 'remark-gfm'
import rehypeSlug from 'rehype-slug'
import rehypeAutolinkHeadings from 'rehype-autolink-headings'

import { getAimdkRaw } from '@/content/aimdk-raw'
import { stripYamlFrontmatter } from '@/content/stripYamlFrontmatter'
import { SdkLinkCard } from './SdkLinkCard'
import { MdxLink } from './MdxLink'
import { MdxImg } from './MdxImg'

/** Rewrite legacy /en and /zh links in MDX body to /docs-prefixed routes. */
function rewriteDocLinks(md: string): string {
  return md
    .replace(/\]\(\/en\//g, '](/docs/en/')
    .replace(/\]\(\/zh\//g, '](/docs/zh/')
    .replace(/\]\(\/en\)/g, '](/docs/en)')
    .replace(/\]\(\/zh\)/g, '](/docs/zh)')
}

function getMdxComponents() {
  return {
    a: MdxLink,
    img: MdxImg,
    SdkLinkCard,
  }
}

interface AimdkMdxBodyProps {
  contentFile: string
}

export default function AimdkMdxBody({ contentFile }: AimdkMdxBodyProps) {
  const { node, error } = useMemo(() => {
    const raw = getAimdkRaw(contentFile)
    if (!raw) {
      return { node: null, error: 'Missing content file.' }
    }
    const body = stripYamlFrontmatter(raw)
    const fixed = rewriteDocLinks(body)
    try {
      const mod = evaluateSync(fixed, {
        Fragment,
        jsx,
        jsxs,
        // Always use production JSX transform; `development: true` requires `jsxDEV` from
        // `react/jsx-dev-runtime`, which we do not pass here.
        development: false,
        remarkPlugins: [remarkGfm],
        rehypePlugins: [rehypeSlug, [rehypeAutolinkHeadings, { behavior: 'wrap' as const }]],
        useMDXComponents: getMdxComponents,
      })
      const Content = mod.default
      return { node: <Content />, error: null }
    } catch (e: unknown) {
      return {
        node: null,
        error: e instanceof Error ? e.message : String(e),
      }
    }
  }, [contentFile])

  if (error) {
    return <p className="text-red-600 text-sm">Failed to render MDX: {error}</p>
  }

  return <div className="md-body aimdk-mdx max-w-none">{node}</div>
}
