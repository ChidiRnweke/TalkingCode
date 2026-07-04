import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-grpc';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { SimpleLogRecordProcessor } from '@opentelemetry/sdk-logs';
import { logs, SeverityNumber } from '@opentelemetry/api-logs';
import { trace, context } from '@opentelemetry/api';
import { classifyConsoleLog } from './otel-log-classifier.js';

/** @typedef {'debug' | 'log' | 'info' | 'warn' | 'error'} ConsoleMethod */
/** @typedef {Record<string, string | number>} LogAttributes */

/** @type {NodeSDK | null} */
let sdk = null;
/** @type {import('@opentelemetry/api-logs').Logger | null} */
let otelLogger = null;
let consoleBridged = false;

// Capture truly original console methods immediately at module load
// (before any code has a chance to patch them)
/** @type {Record<ConsoleMethod, (...args: unknown[]) => void>} */
const originalConsole = {
	log: console.log.bind(console),
	info: console.info.bind(console),
	warn: console.warn.bind(console),
	error: console.error.bind(console),
	debug: console.debug.bind(console)
};

/**
 * Bridge console.log/warn/error to OpenTelemetry logs
 */
function bridgeConsoleLogs() {
	// Prevent double-patching which would cause infinite recursion
	if (consoleBridged) {
		originalConsole.warn('[OTel] Console already bridged, skipping');
		return;
	}

	// Get the global logger provider that NodeSDK sets up
	const loggerProvider = logs.getLoggerProvider();
	otelLogger = loggerProvider.getLogger('console');

	/** @type {Array<[ConsoleMethod, number]>} */
	const severityEntries = [
		['debug', SeverityNumber.DEBUG],
		['log', SeverityNumber.INFO],
		['info', SeverityNumber.INFO],
		['warn', SeverityNumber.WARN],
		['error', SeverityNumber.ERROR]
	];

	for (const [method, severity] of severityEntries) {
		console[method] = (...args) => {
			// Always call original console method
			originalConsole[method](...args);

			// Send to OTel if logger is available
			if (!otelLogger) return;

			try {
				const message = args
					.map((arg) => (typeof arg === 'object' ? JSON.stringify(arg) : String(arg)))
					.join(' ');
				const classification = classifyConsoleLog(method, severity, message);

				// Get current span context for trace correlation
				const activeContext = context.active();
				const span = trace.getSpan(activeContext);
				const spanContext = span?.spanContext();
				/** @type {LogAttributes} */
				const attributes = {
					...classification.attributes,
					...(spanContext
						? {
								trace_id: spanContext.traceId,
								span_id: spanContext.spanId
							}
						: {})
				};

				otelLogger.emit({
					severityNumber: classification.severityNumber,
					severityText: classification.severityText,
					body: message,
					timestamp: Date.now(),
					context: activeContext,
					attributes: Object.keys(attributes).length > 0 ? attributes : undefined
				});
			// eslint-disable-next-line @typescript-eslint/no-unused-vars
			} catch (e) {
				// Silently ignore OTel errors to prevent infinite loops
			}
		};
	}

	consoleBridged = true;
}

export function initTelemetry(serviceName = 'receipt2recipe') {
	const endpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT;

	if (!endpoint) {
		process.stdout.write('[OTel] OTEL_EXPORTER_OTLP_ENDPOINT is not set. Telemetry is disabled.\n');
		return null;
	}

	process.stdout.write(
		`[OTel] Initializing telemetry for ${serviceName}. Exporting to ${endpoint}\n`
	);

	const resource = resourceFromAttributes({
		[ATTR_SERVICE_NAME]: serviceName,
		[ATTR_SERVICE_VERSION]: process.env.npm_package_version || '0.0.1',
		'deployment.environment': process.env.OTEL_ENVIRONMENT || process.env.NODE_ENV || 'development'
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
				'@opentelemetry/instrumentation-pg': {
					enhancedDatabaseReporting: true
				},
				'@opentelemetry/instrumentation-http': {
					enabled: true
				},
				'@opentelemetry/instrumentation-dns': { enabled: false },
				'@opentelemetry/instrumentation-net': { enabled: false }
			})
		]
	});

	sdk.start();

	// Bridge console after SDK starts (so logger provider is registered)
	bridgeConsoleLogs();

	console.log('[OTel] Telemetry initialized successfully.');
	return sdk;
}

export async function shutdownTelemetry() {
	try {
		if (sdk) {
			await sdk.shutdown();
		}
		process.stdout.write('[OTel] Telemetry shut down successfully.\n');
	} catch (err) {
		process.stderr.write(`[OTel] Error shutting down telemetry: ${err}\n`);
	}
}

// Auto-initialize if this file is imported and OTEL_EXPORTER_OTLP_ENDPOINT is set
const endpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
const otelGlobal = /** @type {typeof globalThis & { __otel_initialized__?: boolean }} */ (globalThis);
if (endpoint && !otelGlobal.__otel_initialized__) {
	otelGlobal.__otel_initialized__ = true;
	initTelemetry();
}
