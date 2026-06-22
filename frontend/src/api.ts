export type HealthResult = {
  ok: boolean;
  status?: number;
  body?: unknown;
  error?: string;
};

const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const config = {
  apiUrl,
};

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
