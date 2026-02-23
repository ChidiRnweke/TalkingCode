// talkingcode-frontend/scripts/server.js
import { loadFrontendSecrets } from './secrets.js';
import { initTelemetry } from './otel-instrumentation.js';

await loadFrontendSecrets();
initTelemetry(process.env.OTEL_SERVICE_NAME || 'talkingcode-frontend');

await import('../build/index.js');
