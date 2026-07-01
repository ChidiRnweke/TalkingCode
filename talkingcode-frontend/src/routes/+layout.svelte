<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { ChatLayout, ChatHeader } from '$lib/components/layout';
	import { chatStore } from '$lib/stores';
	import { page } from '$app/state';
	import { ModeWatcher } from 'mode-watcher';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<ModeWatcher />

<ChatLayout>
	<ChatHeader phase={chatStore.phase} currentPath={page.url.pathname} />
	{@render children()}
</ChatLayout>
