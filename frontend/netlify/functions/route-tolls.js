import { handleRouteTollsRequest } from '../../server/routeTollsProxy.js'

export async function handler(event) {
  const headers = new Headers(event.headers)
  const host = headers.get('host')
  const protocol = headers.get('x-forwarded-proto') ||
    (host?.startsWith('localhost') ? 'http' : 'https')
  const rawUrl = event.rawUrl || `${protocol}://${host}${event.path}`
  const body = event.isBase64Encoded
    ? Buffer.from(event.body ?? '', 'base64')
    : event.body
  const request = new Request(rawUrl, {
    method: event.httpMethod,
    headers,
    body: ['GET', 'HEAD'].includes(event.httpMethod) ? undefined : body,
  })
  const response = await handleRouteTollsRequest(request)
  return {
    statusCode: response.status,
    headers: Object.fromEntries(response.headers.entries()),
    body: await response.text(),
  }
}
