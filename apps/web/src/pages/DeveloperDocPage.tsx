import { useEffect, useMemo } from 'react'
import { useLocation, Navigate } from 'react-router-dom'
import ContentLayout from '@/components/layout/ContentLayout'
import AimdkMdxBody from '@/components/aimdk/AimdkMdxBody'
import aimdkManifest from '@/generated/aimdk-manifest.json'
import { normalizePathname } from '@/utils/normalizePathname'

type ManifestEntry = (typeof aimdkManifest.entries)[number]

export default function DeveloperDocPage() {
  const { pathname } = useLocation()

  const entry = useMemo((): ManifestEntry | undefined => {
    const n = normalizePathname(pathname)
    return aimdkManifest.entries.find((e) => normalizePathname(e.eaiRoute) === n)
  }, [pathname])

  const title = entry?.navTitle || entry?.title || 'Developer documentation'

  useEffect(() => {
    document.title = `${title} - EAI Robot Manual`
  }, [title])

  if (!entry) {
    const n = normalizePathname(pathname)
    // Unknown /developer/* → English hub; avoid infinite redirect if manifest is missing /developer/en
    const fallback = n === '/developer/en' ? '/futurist' : '/developer/en'
    return <Navigate to={fallback} replace />
  }

  return (
    <ContentLayout>
      <AimdkMdxBody contentFile={entry.contentFile} />
    </ContentLayout>
  )
}
