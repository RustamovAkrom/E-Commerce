type SessionHandlers = {
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
  onRefreshed: (token: string) => void;
  onExpired: () => void;
};

let handlers: SessionHandlers = {
  getAccessToken: () => null,
  getRefreshToken: () => null,
  onRefreshed: () => undefined,
  onExpired: () => undefined,
};

export function configureApiSession(next: SessionHandlers): void {
  handlers = next;
}
export function getApiSession(): SessionHandlers {
  return handlers;
}
