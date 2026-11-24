/**
 * The Webapp tab is served BY a Zeus Cloud agent (its own origin is the
 * agent). Cloud then owns every update: the app itself comes from that agent.
 * Kept free of the session store so low-level modules (notifications, the
 * settings manifest) can ask it without an import cycle.
 */

import { isZeusCloudUrl } from '@zeus/shared'

import { isBrowserHostedDesktop } from '@/lib/platform'

export function servedByZeusCloud(): boolean {
  return typeof window !== 'undefined' && isBrowserHostedDesktop() && isZeusCloudUrl(window.location.origin)
}
