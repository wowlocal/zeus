import assert from 'node:assert/strict'

import { test } from 'vitest'

import { handleLaunchDeepLink, registerDeepLinkProtocol } from './deep-link-protocol'

function run(env: NodeJS.ProcessEnv, defaultApp = true) {
  const calls: unknown[][] = []
  const log: string[] = []
  registerDeepLinkProtocol({
    app: { setAsDefaultProtocolClient: (...args: unknown[]) => { calls.push(args);

 return true } },
    protocol: 'zeus',
    env,
    defaultApp,
    argv: ['/electron', '.'],
    execPath: '/electron',
    resolve: entry => `/checkout/${entry}`,
    log: line => log.push(line)
  })

  return { calls, log }
}

test('the E2E/dev guard leaves the OS zeus:// handler untouched; normal launches still register', () => {
  const skipped = run({ ZEUS_DESKTOP_SKIP_PROTOCOL_REGISTRATION: '1' })
  assert.deepEqual(skipped.calls, [])
  assert.match(skipped.log.join('\n'), /registration skipped/)

  assert.deepEqual(run({}).calls, [['zeus', '/electron', ['/checkout/.']]])
  assert.deepEqual(run({}, false).calls, [['zeus']])
})

function launch(url: string, ready = true) {
  let activated = 0
  const handled = handleLaunchDeepLink(url, ['zeus-dev', 'zeus'], { ready, activate: () => { activated += 1 } })

  return { handled, activated }
}

test('zeus://launch only focuses the app, whatever it carries, malformed tails included', () => {
  for (const url of ['zeus://launch', 'zeus://launch/', 'zeus://launch/chat/new?prompt=rm%20-rf', 'zeus://launch/%', 'zeus-dev://launch?x=1']) {
    assert.deepEqual(launch(url), { handled: true, activated: 1 }, url)
  }

  // A window still booting reveals itself; the link is consumed without an early show.
  assert.deepEqual(launch('zeus://launch', false), { handled: true, activated: 0 })

  for (const url of ['zeus://', 'zeus://open/launch', 'zeus://plugin/install?repo=launch', 'zeus://launcher', 'zeus://close-preview', 'other://launch', 'not a url']) {
    assert.deepEqual(launch(url), { handled: false, activated: 0 }, url)
  }
})
