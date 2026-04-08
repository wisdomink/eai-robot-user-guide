import { useEffect, useMemo } from 'react'
import { useLocation, Navigate } from 'react-router-dom'
import ContentLayout from '@/components/layout/ContentLayout'
import AimdkMdxBody from '@/components/aimdk/AimdkMdxBody'
import aimdkManifest from '@/generated/aimdk-manifest.json'

type ManifestEntry = (typeof aimdkManifest.entries)[number]

function normalizePath(p: string): string {
  const t = p.replace(/\/+$/, '') || '/'
  return t
}

export default function AimdkDocPage() {
  const { pathname } = useLocation()

  const entry = useMemo((): ManifestEntry | undefined => {
    const n = normalizePath(pathname)
    return aimdkManifest.entries.find((e) => normalizePath(e.eaiRoute) === n)
  }, [pathname])

  const title = entry?.navTitle || entry?.title || 'AimDK'

  useEffect(() => {
    document.title = `${title} - EAI Robot Manual`
  }, [title])

  if (!entry) {
    return <Navigate to="/futurist" replace />
  }

  return (
    <ContentLayout>
      <AimdkMdxBody contentFile={entry.contentFile} />
    </ContentLayout>
  )
}
