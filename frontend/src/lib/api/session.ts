type SessionHandlers = {
  getAccessToken: () => string | null;
  onRefreshed: (token: string) => void;
  onExpired: () => void;
};

let handlers: SessionHandlers = {
  getAccessToken: () => null,
  onRefreshed: () => undefined,
  onExpired: () => undefined,
};

export function configureApiSession(next: SessionHandlers): void { handlers = next; }
export function getApiSession(): SessionHandlers { return handlers; }
