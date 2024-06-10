<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Button from 'flowbite-svelte/Button.svelte';
	import { getContext } from 'svelte';
	import { type Writable } from 'svelte/store';
	export let input = '';
	let inputString = getContext<Writable<string>>('input');

	let action = () => {
		inputString.set(input);
	};
</script>

<Button class="p-8" on:click={action}>
	<P class="lg:text-lg text-primary-50">{input}</P>
</Button>
