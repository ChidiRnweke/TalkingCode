import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import fs from 'fs/promises';
import path from 'path';

const CONFIG_DIR = '.talkingcode';
const CONFIG_FILE = path.join(CONFIG_DIR, '.env');

export const POST: RequestHandler = async ({ request }) => {
	try {
		const config = await request.json();

		// Format the configuration as environment variables
		const envContent = [
			`GITHUB_API_TOKEN=${config.githubToken}`,
			`OPENAI_API_KEY=${config.openaiKey}`,
			`DATABASE_TYPE=${config.dbType}`,
			config.dbUrl ? `DATABASE_URL=${config.dbUrl}` : '',
			`QDRANT_MODE=${config.qdrantMode}`,
			config.qdrantUrl ? `QDRANT_URL=${config.qdrantUrl}` : ''
		]
			.filter(Boolean)
			.join('\n');

		// Ensure the .talkingcode directory exists
		await fs.mkdir(CONFIG_DIR, { recursive: true });

		// Write to .talkingcode/.env file
		await fs.writeFile(CONFIG_FILE, envContent);

		return json({ success: true });
	} catch (error) {
		console.error('Error saving configuration:', error);
		return json({ error: 'Failed to save configuration' }, { status: 500 });
	}
};

export const GET: RequestHandler = async () => {
	try {
		const exists = await fs
			.access(CONFIG_FILE)
			.then(() => true)
			.catch(() => false);
		if (!exists) {
			return json(null);
		}

		const content = await fs.readFile(CONFIG_FILE, 'utf-8');
		const config = content.split('\n').reduce(
			(acc, line) => {
				const [key, value] = line.split('=');
				if (!key || !value) return acc;

				switch (key) {
					case 'GITHUB_API_TOKEN':
						acc.githubToken = value;
						break;
					case 'OPENAI_API_KEY':
						acc.openaiKey = value;
						break;
					case 'DATABASE_TYPE':
						acc.dbType = value as 'sqlite' | 'postgres';
						break;
					case 'DATABASE_URL':
						acc.dbUrl = value;
						break;
					case 'QDRANT_MODE':
						acc.qdrantMode = value as 'local' | 'server';
						break;
					case 'QDRANT_URL':
						acc.qdrantUrl = value;
						break;
				}
				return acc;
			},
			{
				githubToken: '',
				openaiKey: '',
				dbType: '' as 'sqlite' | 'postgres',
				dbUrl: '',
				qdrantMode: '' as 'local' | 'server',
				qdrantUrl: ''
			}
		);

		return json(config);
	} catch (error) {
		console.error('Error loading configuration:', error);
		return json({ error: 'Failed to load configuration' }, { status: 500 });
	}
};
