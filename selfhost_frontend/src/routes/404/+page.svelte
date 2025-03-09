<script lang="ts">
	import Heading from 'flowbite-svelte/Heading.svelte';
	import Paragraph from '../../components/typography/Paragraph.svelte';
</script>

<article class="lg:mx-52 grid grid-cols-1 gap-y-10 mb-10">
	<header>
		<Heading>Page not found.</Heading>
	</header>

	<section>
		<Heading tag="h2" class="text-primary-700 text-xl mb-8">404: Page not found.</Heading>
		<Paragraph>
			Sorry, this page does not exist. Please check the URL and try again. If you think this is a
			mistake, please reach out to me on LinkedIn, GitHub, or even Instagram.
		</Paragraph>
	</section>
</article>
