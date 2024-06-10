<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Button from 'flowbite-svelte/Button.svelte';
	let action: () => void;
</script>

<Button class="p-8" on:click={action}>
	<P class="text-sm text-primary-50"><slot /></P>
</Button>
