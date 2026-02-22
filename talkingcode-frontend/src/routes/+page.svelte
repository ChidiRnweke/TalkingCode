<script lang="ts">
	import { goto } from '$app/navigation';
</script>

<div class="flex flex-1 flex-col items-center justify-center">
	<h1 class="text-4xl font-bold">Welcome to TalkingCode</h1>
	<p class="mt-4">Hero section coming soon...</p>
	<button 
		class="mt-8 rounded-lg bg-primary px-6 py-2 text-white"
		onclick={() => goto('/chat')}
	>
		Go to Chat
	</button>
</div>
