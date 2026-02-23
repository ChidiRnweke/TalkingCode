<script lang="ts">
	import { Streamdown, type StreamdownProps } from "svelte-streamdown";
	import Code from "svelte-streamdown/code"; // Shiki syntax highlighting
	import { cn } from "$lib/utils";
	import { mode } from "mode-watcher";
	import InlineCitation from "$lib/components/ai-elements/inline-citation/InlineCitation.svelte";

	// Import Shiki themes
	import githubLightDefault from "@shikijs/themes/github-light-default";
	import githubDarkDefault from "@shikijs/themes/github-dark-default";

	type Props = Omit<StreamdownProps, "sources"> & {
		class?: string;
		isStreaming?: boolean;
		sources?: Array<{
			index: number;
			repository: string;
			path: string;
			startLine: number | null;
			endLine: number | null;
			similarityScore: number;
		}>;
	};

	let { class: className, isStreaming = false, sources = [], ...restProps }: Props = $props();
	let currentTheme = $derived(
		mode.current === "dark" ? "github-dark-default" : "github-light-default"
	);

	const citationMap = $derived.by(() => {
		const entries = sources.map((source) => {
			const lineRef = source.startLine
				? `#L${source.startLine}${source.endLine ? `-L${source.endLine}` : ""}`
				: "";
			const url = `https://github.com/${source.repository}/blob/main/${source.path}${lineRef}`;
			const location = source.startLine
				? `Lines ${source.startLine}${source.endLine ? `-${source.endLine}` : ""}`
				: undefined;

			return [
				String(source.index),
				{
					title: `${source.repository}: ${source.path}`,
					url,
					location
				}
			] as const;
		});

		return Object.fromEntries(entries);
	});
</script>

<Streamdown
	class={cn(
		"prose prose-base dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 prose-ul:list-disc prose-ol:list-decimal prose-ul:pl-5 prose-ol:pl-5 [&_ul]:list-disc [&_ol]:list-decimal [&_ul]:pl-5 [&_ol]:pl-5 max-w-none size-full text-[1.04rem] leading-8 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 [&_strong]:font-bold [&_li]:my-1",
		isStreaming && 'streaming-cursor',
		className
	)}
	shikiTheme={currentTheme}
	baseTheme="shadcn"
	components={{ code: Code }}
	shikiThemes={{
		"github-light-default": githubLightDefault,
		"github-dark-default": githubDarkDefault,
	}}
	sources={citationMap}
	{...restProps}
>
	{#snippet inlineCitationPreview({ token })}
		<InlineCitation
			label={`[${token.keys[0]}]`}
			source={citationMap[token.keys[0]]}
		/>
	{/snippet}
</Streamdown>
