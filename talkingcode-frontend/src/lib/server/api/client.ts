import createClient from 'openapi-fetch';
import type { paths } from '$lib/api/schema';

type OpenApiClient = ReturnType<typeof createClient<paths>>;

export type ApiClient = OpenApiClient;
