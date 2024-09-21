<script lang="ts">
	import Heading from 'flowbite-svelte/Heading.svelte';
	import List from 'flowbite-svelte/List.svelte';
	import Li from 'flowbite-svelte/Li.svelte';
	import A from 'flowbite-svelte/A.svelte';
	import Paragraph from '../../components/typography/Paragraph.svelte';
	import InlineCode from '../../components/typography/InlineCode.svelte';
</script>

<article class="lg:mx-52 grid grid-cols-1 gap-y-10 mb-10">
	<header>
		<Heading>Some info about...</Heading>
	</header>
	<section>
		<Heading tag="h2" class="mb-8">The idea</Heading>
		<Paragraph>
			The idea is simple. Make a retrieval augmented generation (RAG) app that has access to all of
			my GitHub code. That way people can ask questions about my project and the models try, to the
			best of their ability, to formulate a coherent answer.
		</Paragraph>
	</section>

	<section>
		<Heading tag="h2" class="mb-8">The inspiration</Heading>
		<Paragraph>
			As a student I took the course "search engines and information retrieval" in approx. 2020.
			RAGs aren't named verbatim but the same idea is used there. The key part being embedding a
			document and a quey into a shared semantic space and then performing a search and ranking.
			Topics such as HNSW were also discussed.
		</Paragraph>
		<Paragraph>
			There has been a lot of hype surrounding GenAI for the past couple of years. As a machine
			learning engineer it's become a must-have skill. The point of the project is to prove to
			myself (and others) that building these kinds of applications are not difficult, they're an
			extension of what I already knew. <b>The end-to-end implementation took just one week</b> and that
			is with me only having time in select evenings and the weekend.
		</Paragraph>
	</section>

	<section class="grid grid-cols-1 gap-y-5">
		<Heading tag="h2" class="mb-8">The tech stack</Heading>
		<Paragraph>
			The summary of the tech stack is that it's a full-stack application built with Python in the
			backend and SvelteKit (Typescript) in the frontend. The backend is built using FastAPI and the
			database is Postgres with the PGVector extension. The app is hosted on a VPS running Ubuntu
			and is deployed using Docker and Docker Compose. The deployment is done using Ansible and
			GitHub Actions. All the code is available on GitHub.
		</Paragraph>
		<section>
			<Heading tag="h3" class="mb-8">The ETL: Python</Heading>
			<Paragraph>
				The ETL (extract, transform, load) process is done in Python. The code is available in the
				<InlineCode>data pipelines</InlineCode>
				folder. The code is simple and does the following:
				<List tag="ol" class="my-2">
					<Li>Extracts the data from the GitHub API</Li>
					<Li>Extract some of the data from the response</Li>
					<Li>Store in the database</Li>
				</List>
				After the data is stored in the database, the data is embedded.
			</Paragraph>
			<Paragraph>
				The entire process is orchestrated using <A href="https://dagster.io">Dagster</A>. The DAG
				consists of two nodes: one for extracting the data and one for embedding the data. The
				pipeline practices a strict separation of orchestration and computation. The orchestration
				is done in the Dagster pipeline and the computation is done in the Python code.
			</Paragraph>
		</section>
		<section>
			<Heading tag="h3" class="mb-8">The database: PGVector</Heading>
			<Paragraph>
				Vector databases are a hot topic right now. The idea is to store the data in a way that
				makes it easy to search and rank. The database used is good old Postgres with the
				<A href="https://github.com/pgvector/pgvector">PGVector</A>
				extension. The extension allows for storing vectors in the database and performing vector operations,
				in this case cosine similarity. This was a conscious choice over choosing a dedicated vector
				database like Chroma or Pinecone. The reason being that I wanted to keep the tech stack as simple
				as possible.
			</Paragraph>
		</section>
		<section>
			<Heading tag="h3" class="mb-8">The backend: FastAPI</Heading>
			<Paragraph>
				The API is built using FastAPI. For now the API only has one endpoint:
				<InlineCode>/answer</InlineCode>. FastAPI was also a conscious choice. The reason being that
				it has great asynchronous programming support and can be upgraded to use streaming responses
				and/or websockets. This is important because the RAG model can take a long time to generate
				an answer.
			</Paragraph>
		</section>
		<section>
			<Heading tag="h3" class="mb-8">The frontend: SvelteKit</Heading>
			<div class="grid grid-cols-1 gap-y-3">
				<Paragraph>
					The frontend is built using SvelteKit. The frontend keeps it simple. The root page is
					already used for the conversation. Aside from that there's this page, the about page, and
					the "host-it-yourself" page. The frontend uses server-side rendering which means that
					static pages are generated at build time and transparently served by the server. The rest
					is done client-side. The frontend is styled using TailwindCSS.
				</Paragraph>
				<Paragraph>
					I prefer making static sites because they're simple to make and simple to host. I chose
					SvelteKit because it's a great framework for building static sites. The framework comes
					with a lot of batteries included. The routing is simple and the API is easy to use. HTMX
					could also be used but I chose SvelteKit because I'm more familiar with it.
				</Paragraph>
			</div>
		</section>
	</section>
	<section>
		<Heading tag="h2" class="mb-8">The deployment and hosting</Heading>
		<Paragraph>
			The app is hosted on my own server. The server is a simple VPS running Ubuntu. The app is
			deployed using Docker and Docker Compose and is served using Caddy. The app is deployed using
			Ansible for all the configuration management. Each subsequent deployment is done using GitHub
			Actions. The app is deployed to the server using an SSH connection. The backend and the ETL
			are different services and are deployed separately.
		</Paragraph>
	</section>

	<section>
		<Heading tag="h2" class="mb-8">The future</Heading>
		<div class="grid grid-cols-1 gap-y-3">
			<Paragraph>
				I have a number of ideas for what can come next. They're all listed on GitHub as issues as
				well as on the projects board. The main idea is to improve the retrieval as well as the
				generation. The retrieval can be improved by using agents or by doing things such as
				rewriting the query. The generation can be used by providing more useful context and
				metadata. Before I go into that I want to make sure I have the ability to quantify the
				improvements. I have a number of ideas for how to do that as well.
			</Paragraph>
			<Paragraph>
				Some other things that are relevant is making the ETL more performant by removing the
				dependency on PyGithub and using the GitHub API directly, that way I can use asynchronous
				programming to vastly speed up the process. Another idea would be switching from ETL to ELT
				(extract, load, transform) and storing the raw data in the database and then transforming it
				as needed. This would allow for more flexibility in the data processing but would also
				require more storage on my VPS which is a cost I'm not willing to pay.
			</Paragraph>
		</div>
	</section>
</article>
