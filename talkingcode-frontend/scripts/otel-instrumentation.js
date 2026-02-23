import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-grpc';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { SimpleLogRecordProcessor } from '@opentelemetry/sdk-logs';
import { logs, SeverityNumber } from '@opentelemetry/api-logs';
import { trace, context } from '@opentelemetry/api';

let sdk = null;
let otelLogger = null;
let consoleBridged = false;

const originalConsole = {
  log: console.log.bind(console),
  info: console.info.bind(console),
  warn: console.warn.bind(console),
  error: console.error.bind(console),
  debug: console.debug.bind(console),
};

function bridgeConsoleLogs() {
  if (consoleBridged) return;
  const loggerProvider = logs.getLoggerProvider();
  otelLogger = loggerProvider.getLogger('console');

  const severityMap = {
    debug: SeverityNumber.DEBUG,
    log: SeverityNumber.INFO,
    info: SeverityNumber.INFO,
    warn: SeverityNumber.WARN,
    error: SeverityNumber.ERROR,
  };

  for (const [method, severity] of Object.entries(severityMap)) {
    console[method] = (...args) => {
      originalConsole[method](...args);
      if (!otelLogger) return;
      try {
        const message = args.map((arg) => (typeof arg === 'object' ? JSON.stringify(arg) : String(arg))).join(' ');
        const activeContext = context.active();
        const span = trace.getSpan(activeContext);
        const spanContext = span?.spanContext();
        otelLogger.emit({
          severityNumber: severity,
          severityText: method.toUpperCase(),
          body: message,
          timestamp: Date.now(),
          context: activeContext,
          attributes: spanContext
            ? { trace_id: spanContext.traceId, span_id: spanContext.spanId }
            : undefined,
        });
      } catch {
        // ignore
      }
    };
  }

  consoleBridged = true;
}

export function initTelemetry(serviceName = 'talkingcode-frontend') {
  const endpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
  if (!endpoint) {
    process.stdout.write('[OTel] endpoint not set; telemetry disabled\n');
    return null;
  }

  const resource = resourceFromAttributes({
    [ATTR_SERVICE_NAME]: serviceName,
    [ATTR_SERVICE_VERSION]: process.env.npm_package_version || '0.0.1',
    'deployment.environment': process.env.OTEL_ENVIRONMENT || process.env.NODE_ENV || 'development',
  });

  const traceExporter = new OTLPTraceExporter({ url: endpoint });
  const logExporter = new OTLPLogExporter({ url: endpoint });

  sdk = new NodeSDK({
    resource,
    traceExporter,
    logRecordProcessors: [new SimpleLogRecordProcessor(logExporter)],
    instrumentations: [
      getNodeAutoInstrumentations({
        '@opentelemetry/instrumentation-fs': { enabled: false },
        '@opentelemetry/instrumentation-dns': { enabled: false },
        '@opentelemetry/instrumentation-net': { enabled: false },
      }),
    ],
  });

  sdk.start();
  bridgeConsoleLogs();
  return sdk;
}

export async function shutdownTelemetry() {
  if (sdk) await sdk.shutdown();
}
