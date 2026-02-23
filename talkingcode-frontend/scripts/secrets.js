// talkingcode-frontend/scripts/secrets.js
import 'dotenv/config';
import { InfisicalSDK } from '@infisical/sdk';

function isInfisicalEnabled() {
  return Boolean(process.env.INFISICAL_ENABLED);
}

async function loadFromInfisical() {
  const clientId = process.env.INFISICAL_CLIENT_ID;
  const clientSecret = process.env.INFISICAL_CLIENT_SECRET;
  const projectId = process.env.INFISICAL_PROJECT_ID;
  const environment = process.env.INFISICAL_ENVIRONMENT || 'prod';
  const siteUrl = process.env.INFISICAL_URL;

  if (!clientId || !clientSecret || !projectId || !siteUrl) {
    throw new Error('Missing Infisical credentials for frontend secrets loading');
  }

  const client = new InfisicalSDK({ siteUrl });
  await client.auth().universalAuth.login({ clientId, clientSecret });
  const secrets = await client.secrets().listSecrets({
    environment,
    projectId,
    includeImports: true,
  });

  const map = {};
  secrets.secrets.forEach((s) => {
    map[s.secretKey] = s.secretValue;
  });
  return map;
}

export async function loadFrontendSecrets() {
  let secretMap = {};
  if (isInfisicalEnabled()) {
    secretMap = await loadFromInfisical();
  }

  process.env.BACKEND_URL = process.env.BACKEND_URL || secretMap.BACKEND_URL || 'http://backend:8000';
  process.env.PUBLIC_BACKEND_URL = process.env.PUBLIC_BACKEND_URL || secretMap.PUBLIC_BACKEND_URL || process.env.BACKEND_URL;
  process.env.INGESTION_API_KEY = process.env.INGESTION_API_KEY || secretMap.INGESTION_API_KEY || '';

  process.env.OTEL_EXPORTER_OTLP_ENDPOINT = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || secretMap.OTEL_EXPORTER_OTLP_ENDPOINT || '';
  process.env.OTEL_SERVICE_NAME = process.env.OTEL_SERVICE_NAME || secretMap.OTEL_SERVICE_NAME || 'talkingcode-frontend';
  process.env.OTEL_ENVIRONMENT = process.env.OTEL_ENVIRONMENT || secretMap.OTEL_ENVIRONMENT || process.env.NODE_ENV || 'development';
}
