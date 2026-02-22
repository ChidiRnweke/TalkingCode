<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { ChatLayout, ChatHeader, HomeHeader } from '$lib/components/layout';
	import { chatStore } from '$lib/stores';
	import { page } from '$app/stores';

	let { children } = $props();
	let isHomePage = $derived($page.url.pathname === '/');
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<ChatLayout>
	{#if isHomePage}
		<HomeHeader />
	{:else}
		<ChatHeader phase={chatStore.phase} currentPath={$page.url.pathname} />
	{/if}
	{@render children()}
</ChatLayout>
