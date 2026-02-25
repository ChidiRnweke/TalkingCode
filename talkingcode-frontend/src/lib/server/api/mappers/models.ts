import type { components } from '$lib/api/schema';

type RawModelInfo = components['schemas']['ModelInfoResponse'];

export interface ModelOption {
	id: string;
	label: string;
}

export function mapModel(raw: RawModelInfo): ModelOption {
	return {
		id: raw.id,
		label: raw.label
	};
}
