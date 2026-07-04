import { SeverityNumber } from '@opentelemetry/api-logs';

/** @typedef {'debug' | 'log' | 'info' | 'warn' | 'error'} ConsoleMethod */
/** @typedef {Record<string, string | number>} LogAttributes */

const httpStatusLogPattern = /^\[(\d{3})\]\s+([A-Z]+)\s+\S+/;

/**
 * Classify console messages before they are exported as OpenTelemetry logs.
 *
 * @param {ConsoleMethod} method
 * @param {number} defaultSeverity
 * @param {string} message
 * @returns {{ severityNumber: number; severityText: string; attributes: LogAttributes }}
 */
export function classifyConsoleLog(method, defaultSeverity, message) {
	const match = httpStatusLogPattern.exec(message);

	if (!match) {
		return {
			severityNumber: defaultSeverity,
			severityText: method.toUpperCase(),
			attributes: {}
		};
	}

	const statusCode = Number(match[1]);
	const requestMethod = match[2];

	if (statusCode >= 500) {
		return {
			severityNumber: SeverityNumber.ERROR,
			severityText: 'ERROR',
			attributes: {
				'http.response.status_code': statusCode,
				'http.request.method': requestMethod
			}
		};
	}

	if (statusCode >= 400 && statusCode !== 404) {
		return {
			severityNumber: SeverityNumber.WARN,
			severityText: 'WARN',
			attributes: {
				'http.response.status_code': statusCode,
				'http.request.method': requestMethod
			}
		};
	}

	return {
		severityNumber: SeverityNumber.INFO,
		severityText: 'INFO',
		attributes: {
			'http.response.status_code': statusCode,
			'http.request.method': requestMethod
		}
	};
}
