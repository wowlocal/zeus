import { describe, expect, it } from 'vitest'

import { isZeusCloudUrl } from './zeus-cloud'

describe('isZeusCloudUrl', () => {
  it('recognises production and staging agent hosts, nothing else', () => {
    expect(isZeusCloudUrl('https://ares-3009.agents.nousresearch.com')).toBe(true)
    expect(isZeusCloudUrl('https://ares--app.agents.staging-nousresearch.com/')).toBe(true)
    expect(isZeusCloudUrl('https://agents.nousresearch.com.evil.example')).toBe(false)
    expect(isZeusCloudUrl('https://my-box.tailnet.ts.net')).toBe(false)
    expect(isZeusCloudUrl('not a url')).toBe(false)
    expect(isZeusCloudUrl(undefined)).toBe(false)
  })
})
