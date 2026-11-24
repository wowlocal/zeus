import type { ApprovalCopy } from './types_approval'

export const ruApproval: Partial<ApprovalCopy> = {
  gatewayDisconnected: 'Шлюз Zeus не подключён',
  sendFailed: 'Не удалось отправить ответ на подтверждение',
  run: 'Выполнить',
  command: 'Команда',
  moreOptions: 'Больше опций подтверждения',
  allowSession: 'Разрешить в этом сеансе',
  alwaysAllowMenu: 'Всегда разрешать…',
  jumpToApproval: 'Нужно подтверждение',
  reject: 'Отклонить',
  alwaysTitle: 'Всегда разрешать эту команду?',
  alwaysDescription: pattern =>
    `Это добавит паттерн «${pattern}» в ваш постоянный список разрешений (~/.zeus/config.yaml). Zeus больше не будет спрашивать о подобных командах — ни в этом сеансе, ни в будущем.`,
  alwaysAllow: 'Всегда разрешать',
  deny: 'Запретить',
  allow: 'Разрешить',
  allowHint: 'До выключения песочницы',
  denyReason: 'Причина запрета',
  denyReasonPlaceholder: 'Объясните Zeus причину (необязательно)',
  access: {
    title: 'Доступ к папке',
    readOnly: 'Только чтение',
    readWrite: 'Чтение и запись',
    timedOut: folder =>
      `Время ожидания запроса истекло — доступ к папке ${folder} не предоставлен. Попросите Zeus попробовать ещё раз.`,
    alwaysTitle: 'Всегда разрешать эту папку?',
    alwaysDescription: 'Папка добавляется в песочницу этого профиля. Zeus больше не спросит о ней ни в одном чате.'
  },
  network: {
    title: 'Доступ к сайту',
    timedOut: site =>
      `Время ожидания запроса истекло — доступ к ${site} не предоставлен. Попросите Zeus попробовать ещё раз.`,
    alwaysTitle: 'Всегда разрешать этот сайт?',
    alwaysDescription:
      'Сайт добавляется в разрешённые сайты этого профиля. Zeus больше не спросит о нём ни в одном чате.'
  }
}
