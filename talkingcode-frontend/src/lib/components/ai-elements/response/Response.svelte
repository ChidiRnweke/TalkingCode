<script lang="ts">
	import { Streamdown, type StreamdownProps } from "svelte-streamdown";
	import Code from "svelte-streamdown/code"; // Shiki syntax highlighting
	import { cn } from "$lib/utils";
	import { mode } from "mode-watcher";
	import * as HoverCard from "$lib/components/ui/hover-card";
	import {
		InlineCitationCard,
		InlineCitationCardBody,
		InlineCitationSource
	} from "$lib/components/ai-elements/inline-citation";

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

<!-- Key on the theme so the code blocks re-highlight when the user toggles
     light/dark; svelte-streamdown highlights once and won't otherwise update. -->
{#key currentTheme}
	<Streamdown
		class={cn(
			// prose-pre:* overrides the typography plugin's hardcoded dark pre
			// background/text, which otherwise beats the code theme's classes on
			// specificity and renders light-theme Shiki tokens on a dark box.
			"prose prose-base dark:prose-invert prose-pre:p-2 prose-pre:my-0 prose-pre:bg-transparent prose-pre:text-foreground [&_pre_code]:text-inherit max-w-none size-full text-base leading-[1.65] [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 [&_strong]:font-bold [&_li]:my-0.5 [&_li]:pl-2 [&_ul]:list-disc [&_ol]:list-decimal [&_ul]:pl-5 [&_ol]:pl-5 [&_ul]:my-4 [&_ol]:my-4 [&_p]:my-4",
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
			{@const source = citationMap[token.keys[0]]}
			{#if source}
				<InlineCitationCard>
					<HoverCard.Trigger
						class="ml-0.5 inline text-[0.72em] font-medium align-super text-primary underline decoration-primary/30 underline-offset-2 hover:decoration-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring cursor-pointer"
					>
						{source.title.split(': ').pop() || source.title}
					</HoverCard.Trigger>
					<InlineCitationCardBody>
						<div class="p-3">
							<InlineCitationSource
								title={source.title}
								url={source.url}
								description={source.location}
							/>
						</div>
					</InlineCitationCardBody>
				</InlineCitationCard>
			{:else}
				<span class="ml-0.5 inline text-[0.72em] font-medium align-super text-muted-foreground">
					{token.keys[0]}
				</span>
			{/if}
		{/snippet}
	</Streamdown>
{/key}
