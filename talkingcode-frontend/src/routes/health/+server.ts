import { json, type RequestHandler } from '@sveltejs/kit';

import { ServerFactory } from '$lib/server/ServerFactory';

export const GET: RequestHandler = async ({ fetch }) => {
	const controller = ServerFactory.getHealthController(fetch);
	const report = await controller.checkHealth();

	return json(report, {
		status: report.status === 'failed' ? 500 : 200
	});
};
