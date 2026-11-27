import { handleRouteTollsRequest } from '../server/routeTollsProxy.js'

export default function handler(request) {
  return handleRouteTollsRequest(request)
}
