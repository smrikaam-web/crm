export const SUB_STATUS_OPTIONS_MAP = {
  'Not Contacted': ['Voice mail', 'No answer'],
  'Not Valid': ['Wrong number', 'Others'],
}

export function getSubStatusOptions(mainStatus) {
  return SUB_STATUS_OPTIONS_MAP[mainStatus] || []
}

export function isSubStatusRequired(mainStatus) {
  return Boolean(SUB_STATUS_OPTIONS_MAP[mainStatus])
}
