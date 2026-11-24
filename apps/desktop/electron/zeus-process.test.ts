import { describe, expect, it } from 'vitest'

import { commandLineIsZeusRuntime } from './zeus-process'

// HX003: process identity comes from a whole argv TOKEN, never an argv substring.
describe('commandLineIsZeusRuntime (HX003 token matching)', () => {
  it('matches a real Zeus gateway command line', () => {
    expect(commandLineIsZeusRuntime('zeus\0gateway\0run')).toBe(true)
    expect(commandLineIsZeusRuntime('zeus gateway run')).toBe(true)
    expect(commandLineIsZeusRuntime('zeus --profile work gateway run')).toBe(true)
  })

  it('matches a Zeus launched by an interpreter (basename of a path token)', () => {
    expect(commandLineIsZeusRuntime('/venv/bin/python\0/venv/bin/zeus\0gateway\0run')).toBe(true)
    expect(commandLineIsZeusRuntime('C:\\Zeus\\zeus.exe gateway run')).toBe(true)
  })

  // The bug this replaces: a bare `.includes('zeus')` matched any of these.
  it('does NOT match an unrelated process whose path merely contains "zeus"', () => {
    expect(commandLineIsZeusRuntime('vim /home/user/zeus-notes.txt')).toBe(false)
    expect(commandLineIsZeusRuntime('/opt/zeusbrew/bin/tool --run')).toBe(false)
    expect(commandLineIsZeusRuntime('node /srv/zeus-dashboard/server.js')).toBe(false)
    expect(commandLineIsZeusRuntime('cat ~/.zeus/config.yaml')).toBe(false)
  })

  // G2 (#150283): the real unmanaged-gateway launch is `python -m zeus_cli.main … gateway
  // run`, which the executable-basename-only matcher REJECTED — so findRunningGatewayProfiles
  // missed a live gateway at first launch / profile repair. Mirror the canonical Python matcher
  // (gateway.status.looks_like_gateway_command_line): recognize the module entry point, by argv
  // TOKENS not a substring, carrying the gateway subcommand.
  it('matches a module-launched gateway (python -m zeus_cli.main … gateway run)', () => {
    expect(commandLineIsZeusRuntime('python\0-m\0zeus_cli.main\0-p\0x\0gateway\0run')).toBe(true)
    expect(commandLineIsZeusRuntime('python -m zeus_cli.main -p x gateway run')).toBe(true)
    expect(commandLineIsZeusRuntime('/venv/bin/python /venv/lib/zeus_cli/main.py gateway run')).toBe(true)
    expect(commandLineIsZeusRuntime('python -m zeus_cli.main --profile work gateway run')).toBe(true)
  })

  it('does NOT match a module entry without the gateway subcommand, nor an unrelated zeus-tool path', () => {
    // A zeus_cli.main invocation that is not a gateway (e.g. `chat`) is not a running gateway.
    expect(commandLineIsZeusRuntime('python -m zeus_cli.main chat')).toBe(false)
    // HX003: no substring; an unrelated tool whose path contains "zeus" is never a runtime.
    expect(commandLineIsZeusRuntime('/opt/zeus-tool/foo gateway run')).toBe(false)
    // `-p gateway` is a profile value, not a subcommand.
    expect(commandLineIsZeusRuntime('python -m zeus_cli.main -p gateway chat')).toBe(false)
  })
})
