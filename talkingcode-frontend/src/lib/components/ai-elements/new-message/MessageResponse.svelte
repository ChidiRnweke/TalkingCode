<script lang="ts">
	import Response from "../response/Response.svelte";
	import type { ComponentProps } from "svelte";

	type Props = ComponentProps<typeof Response> & {
		content: string;
	};

	let { content, ...restProps }: Props = $props();
</script>

<Response {content} {...restProps} />
