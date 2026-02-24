<script lang="ts">
	import { PromptInputController, setPromptInputProvider } from "./attachments-context.svelte.js";
	import { untrack } from "svelte";

	interface Props {
		initialInput?: string;
		accept?: string;
		multiple?: boolean;
		children?: import("svelte").Snippet;
	}

	let { initialInput = "", accept, multiple = true, children }: Props = $props();

	let controller = new PromptInputController(
		untrack(() => initialInput),
		untrack(() => accept),
		untrack(() => multiple),
	);

	setPromptInputProvider(controller);
</script>

{#if children}
	{@render children()}
{/if}
