export interface ChatSdkVersionInfo {
  sdkVersion: string
  buildVersion: string
  buildTime: string | null
}

function resolveSdkVersion() {
  if (typeof __SDK_VERSION__ === 'string' && __SDK_VERSION__) {
    return __SDK_VERSION__
  }
  return 'dev'
}

function resolveBuildTime() {
  if (typeof __BUILD_TIME__ !== 'string' || !__BUILD_TIME__) {
    return null
  }
  const d = new Date(__BUILD_TIME__)
  if (Number.isNaN(d.getTime())) {
    return null
  }
  return d.toISOString()
}

function formatBuildVersion(buildTime: string | null) {
  if (!buildTime) return 'dev'
  const d = new Date(buildTime)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}.${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
}

export function getChatSdkVersionInfo(): ChatSdkVersionInfo {
  const buildTime = resolveBuildTime()
  return {
    sdkVersion: resolveSdkVersion(),
    buildVersion: formatBuildVersion(buildTime),
    buildTime,
  }
}
