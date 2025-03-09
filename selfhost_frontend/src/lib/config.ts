export interface Config {
	githubToken: string;
	openaiKey: string;
	dbType: 'sqlite' | 'postgres';
	dbUrl: string;
	qdrantMode: 'local' | 'server';
	qdrantUrl: string;
}

export async function saveConfig(config: Config): Promise<void> {
	try {
		await fetch('/api/config', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(config)
		});
	} catch (error) {
		console.error('Failed to save configuration:', error);
		throw error;
	}
}

export async function loadConfig(): Promise<Config | null> {
	try {
		const response = await fetch('/api/config');
		if (!response.ok) {
			return null;
		}
		return await response.json();
	} catch (error) {
		console.error('Failed to load configuration:', error);
		return null;
	}
}
