<script lang="ts">
	import P from 'flowbite-svelte/P.svelte';
	import Avatar from 'flowbite-svelte/Avatar.svelte';
	export let text =
		'<section class="generated">\n  <h3>Chidi’s Experience with Rust</h3> <p>Chidi Nweke showcases his experience with Rust through several projects hosted on his GitHub. Here are a couple of notable examples:</p>  <ul>    <li>     <b>Tic-Tac-Toe in Rust</b>    <p>This project is a simple implementation of the classic game Tic-Tac-Toe. It\'s designed to help Chidi practice basic constructs of the Rust language. The project is organized into several key modules such as <i>main.rs</i>, <i>logic.rs</i>, <i>formatting.rs</i>, <i>game_loop.rs</i>, and <i>squares.rs</i>.</p>\n      <a href="https://github.com/ChidiRnweke/tictactoe_rs">Explore the Rust Tic-Tac-Toe project</a>\n    </li>\n    \n    <li>\n      <b>URL Shortener Service</b>\n      <p>Chidi also developed a URL shortener service in Rust. This service efficiently converts long URLs into shorter, easy-to-remember links. The Rust version of this project is actively deployed, boasting a remarkably low idle memory consumption of just 8 megabytes, compared to the 160 megabytes consumed by the Scala version. The project includes modules for configuration loading (<i>config.rs</i>), database operations (<i>shorten.rs</i>), and HTTP service handling (<i>main.rs</i>).</p>\n      <a href="https://github.com/ChidiRnweke/squishlink_rs">Explore the Rust-based URL Shortener Service</a>\n    </li>\n  </ul>\n  \n  <p>These projects highlight Chidi’s growing expertise and hands-on experience with Rust, showcasing his ability to apply the language to various problem domains effectively.</p>\n</section>\n';
</script>

<section class="flex flex-row place-items-start gap-x-20">
	<div>
		<Avatar src="/portrait.jpg" rounded border size="xl" class="max-w-fit" />
		<P class="text-center font-semibold text-primary-900">Chidi Nweke</P>
	</div>
	<P class="text-lg leading-10">
		<div class="generated">
			{@html text}
		</div>
	</P>
</section>

<style>
	.generated :global(ul) {
		list-style-type: disc;
	}

	.generated :global(h3) {
		font-size: 1.5rem;
		font-weight: 600;
		color: blue-900;
	}

	.generated :global(p) {
		margin-top: 1rem;
	}
</style>
