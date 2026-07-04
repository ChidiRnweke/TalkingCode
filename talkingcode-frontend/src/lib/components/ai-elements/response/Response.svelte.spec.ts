import { page } from 'vitest/browser';
import { describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Response from './Response.svelte';

describe('Response', () => {
	it('renders inline code without typography-generated backticks', async () => {
		render(Response, { content: 'Use `term` here.' });

		const inlineCode = page.getByText('term');
		await expect.element(inlineCode).toBeInTheDocument();

		const code = document.querySelector('[data-streamdown-codespan]');
		expect(code?.textContent).toBe('term');
		expect(code?.closest('.prose')?.className).toContain("[&_code::before]:content-['']");
		expect(code?.closest('.prose')?.className).toContain("[&_code::after]:content-['']");
	});
});
