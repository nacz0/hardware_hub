export type HealthResult = {
  ok: boolean;
  status?: number;
  body?: unknown;
  error?: string;
};

export type UserRole = 'admin' | 'user' | string;

export type CurrentUser = {
  id: number;
  email: string;
  role: UserRole;
  createdAt: string;
};

export type HardwareStatus = 'Available' | 'In Use' | 'Repair' | 'Unknown' | string;

export type HardwareItem = {
  id: number;
  externalId?: number | null;
  name: string;
  brand?: string | null;
  purchaseDate?: string | null;
  status?: HardwareStatus | null;
  assignedTo?: string | null;
};

export type CreateUserInput = {
  email: string;
  password: string;
  role: 'admin' | 'user';
};

export type CreateHardwareInput = {
  externalId?: number | null;
  name: string;
  brand?: string | null;
  purchaseDate?: string | null;
  status: 'Available' | 'In Use' | 'Repair';
  notes?: string | null;
  assignedTo?: string | null;
  history?: string | null;
};

export type AuditSeverity = 'high' | 'medium' | 'low' | string;

export type AuditIssue = {
  severity: AuditSeverity;
  itemId: number;
  title: string;
  description: string;
  suggestedAction: string;
};

export type AuditReport = {
  summary: string;
  issues: AuditIssue[];
};

type ApiUser = {
  id: number;
  email: string;
  role: UserRole;
  created_at?: string;
  createdAt?: string;
};

type ApiHardwareItem = {
  id: number;
  external_id?: number | null;
  externalId?: number | null;
  name: string;
  brand?: string | null;
  purchase_date?: string | null;
  purchaseDate?: string | null;
  status?: HardwareStatus | null;
  assigned_to?: string | null;
  assignedTo?: string | null;
};

const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const tokenStorageKey = 'hardwareHub.jwt';

export const config = {
  apiUrl,
  tokenStorageKey,
};

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function getStoredToken(): string | null {
  return localStorage.getItem(tokenStorageKey);
}

export const tokenStore = {
  get: getStoredToken,
  set(token: string) {
    localStorage.setItem(tokenStorageKey, token);
  },
  clear() {
    localStorage.removeItem(tokenStorageKey);
  },
};

function normalizeUser(user: ApiUser): CurrentUser {
  return {
    id: user.id,
    email: user.email,
    role: user.role,
    createdAt: user.createdAt ?? user.created_at ?? '',
  };
}

function normalizeHardware(item: ApiHardwareItem): HardwareItem {
  return {
    id: item.id,
    externalId: item.externalId ?? item.external_id ?? null,
    name: item.name,
    brand: item.brand ?? null,
    purchaseDate: item.purchaseDate ?? item.purchase_date ?? null,
    status: item.status ?? null,
    assignedTo: item.assignedTo ?? item.assigned_to ?? null,
  };
}

function getErrorMessage(body: unknown, fallback: string): string {
  if (typeof body === 'string' && body.trim()) {
    return body;
  }

  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((entry) => {
          if (entry && typeof entry === 'object' && 'msg' in entry) {
            return String((entry as { msg: unknown }).msg);
          }

          return String(entry);
        })
        .join(', ');
    }
  }

  return fallback;
}

async function readBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json();
  }

  return response.text();
}

async function request<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    token?: string | null;
  } = {},
): Promise<T> {
  const headers = new Headers();
  headers.set('Accept', 'application/json');

  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
  }

  const token = options.token ?? getStoredToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${apiUrl}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : 'Network request failed');
  }

  const body = response.status === 204 ? null : await readBody(response);

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(body, `Request failed with status ${response.status}`),
      response.status,
    );
  }

  return body as T;
}

export async function getHealth(): Promise<HealthResult> {
  try {
    const response = await fetch(`${apiUrl}/health`);
    const contentType = response.headers.get('content-type') ?? '';
    const body = contentType.includes('application/json')
      ? await response.json()
      : await response.text();

    return {
      ok: response.ok,
      status: response.status,
      body,
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : 'Unknown health check error',
    };
  }
}

export async function login(email: string, password: string): Promise<CurrentUser> {
  const tokenResponse = await request<{ access_token: string }>('/auth/login', {
    method: 'POST',
    body: { email, password },
    token: null,
  });

  tokenStore.set(tokenResponse.access_token);

  try {
    return await getCurrentUser(tokenResponse.access_token);
  } catch (error) {
    tokenStore.clear();
    throw error;
  }
}

export async function getCurrentUser(token?: string | null): Promise<CurrentUser> {
  const user = await request<ApiUser>('/auth/me', { token });
  return normalizeUser(user);
}

export async function getHardware(): Promise<HardwareItem[]> {
  const hardware = await request<ApiHardwareItem[]>('/hardware');
  return hardware.map(normalizeHardware);
}

export async function createUserAccount(input: CreateUserInput): Promise<CurrentUser> {
  const user = await request<ApiUser>('/admin/users', {
    method: 'POST',
    body: input,
  });
  return normalizeUser(user);
}

export async function createHardware(input: CreateHardwareInput): Promise<HardwareItem> {
  const hardware = await request<ApiHardwareItem>('/hardware', {
    method: 'POST',
    body: input,
  });
  return normalizeHardware(hardware);
}

export async function deleteHardware(hardwareId: number): Promise<void> {
  await request<null>(`/hardware/${hardwareId}`, {
    method: 'DELETE',
  });
}

export async function markHardwareRepair(hardwareId: number): Promise<HardwareItem> {
  const hardware = await request<ApiHardwareItem>(`/hardware/${hardwareId}/repair`, {
    method: 'POST',
  });
  return normalizeHardware(hardware);
}

export async function rentHardware(hardwareId: number): Promise<HardwareItem> {
  const hardware = await request<ApiHardwareItem>(`/hardware/${hardwareId}/rent`, {
    method: 'POST',
  });
  return normalizeHardware(hardware);
}

export async function returnHardware(hardwareId: number): Promise<HardwareItem> {
  const hardware = await request<ApiHardwareItem>(`/hardware/${hardwareId}/return`, {
    method: 'POST',
  });
  return normalizeHardware(hardware);
}

export async function runInventoryAudit(): Promise<AuditReport> {
  return request<AuditReport>('/ai/audit', {
    method: 'POST',
  });
}
