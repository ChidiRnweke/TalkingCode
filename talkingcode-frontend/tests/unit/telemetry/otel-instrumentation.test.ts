import { SeverityNumber } from '@opentelemetry/api-logs';
import { describe, expect, it } from 'vitest';

import { classifyConsoleLog } from '../../../scripts/otel-log-classifier.js';

describe('classifyConsoleLog', () => {
	it('exports HTTP 404 console errors as info', () => {
		const classification = classifyConsoleLog(
			'error',
			SeverityNumber.ERROR,
			'[404] GET /wp-load.php'
		);

		expect(classification).toEqual({
			severityNumber: SeverityNumber.INFO,
			severityText: 'INFO',
			attributes: {
				'http.response.status_code': 404,
				'http.request.method': 'GET'
			}
		});
	});

	it('keeps HTTP 5xx console errors as errors', () => {
		const classification = classifyConsoleLog(
			'error',
			SeverityNumber.ERROR,
			'[500] GET /api/chat'
		);

		expect(classification).toEqual({
			severityNumber: SeverityNumber.ERROR,
			severityText: 'ERROR',
			attributes: {
				'http.response.status_code': 500,
				'http.request.method': 'GET'
			}
		});
	});

	it('exports non-404 HTTP 4xx console errors as warnings', () => {
		const classification = classifyConsoleLog('error', SeverityNumber.ERROR, '[403] GET /admin');

		expect(classification).toEqual({
			severityNumber: SeverityNumber.WARN,
			severityText: 'WARN',
			attributes: {
				'http.response.status_code': 403,
				'http.request.method': 'GET'
			}
		});
	});

	it('keeps non-HTTP console errors as errors', () => {
		const classification = classifyConsoleLog(
			'error',
			SeverityNumber.ERROR,
			'Chat proxy error: boom'
		);

		expect(classification).toEqual({
			severityNumber: SeverityNumber.ERROR,
			severityText: 'ERROR',
			attributes: {}
		});
	});

	it('keeps non-HTTP warning severity unchanged', () => {
		const classification = classifyConsoleLog(
			'warn',
			SeverityNumber.WARN,
			'configuration warning'
		);

		expect(classification).toEqual({
			severityNumber: SeverityNumber.WARN,
			severityText: 'WARN',
			attributes: {}
		});
	});

	it('keeps non-HTTP info severity unchanged', () => {
		const classification = classifyConsoleLog('info', SeverityNumber.INFO, 'server started');

		expect(classification).toEqual({
			severityNumber: SeverityNumber.INFO,
			severityText: 'INFO',
			attributes: {}
		});
	});
});
