// The Zeus home the desktop main process runs against, resolved once at boot.
// Resolving it here also registers it with the file-preview read guard, so the
// home's (and every profile's) credential stores are refused before any IPC
// read can be served.

import { resolveDesktopZeusHome } from './data-paths'
import { directoryExists } from './fs-probes'
import { setSensitiveZeusHome } from './hardening'
import { readWindowsUserEnvVar } from './windows-user-env'

export function resolveMainZeusHome(home: string): string {
  const zeusHome = resolveDesktopZeusHome({
    home,
    directoryExists,
    readWindowsHome: (): string | null => readWindowsUserEnvVar('ZEUS_HOME')
  })

  setSensitiveZeusHome(zeusHome)

  return zeusHome
}
