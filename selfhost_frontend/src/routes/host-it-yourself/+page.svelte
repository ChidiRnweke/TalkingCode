<script lang="ts">
	import Heading from 'flowbite-svelte/Heading.svelte';
	import Paragraph from '../../components/typography/Paragraph.svelte';
	import List from 'flowbite-svelte/List.svelte';
	import Li from 'flowbite-svelte/Li.svelte';
	import InlineCode from '../../components/typography/InlineCode.svelte';
	import A from 'flowbite-svelte/A.svelte';
</script>

<article class="lg:mx-52 grid grid-cols-1 gap-y-10 mb-10">
	<header>
		<Heading class="mb-12">Running the app yourself</Heading>
		<Paragraph>
			From the beginning, I wanted to make running <em>TalkingCode</em> as easy as possible. I
			wanted to provide a way for people to host it themselves. This article will walk you through
			the steps needed to host <em>TalkingCode</em> yourself.
		</Paragraph>
	</header>

	<section>
		<Heading tag="h2" class="mb-8">Summary</Heading>
		<Paragraph>
			To host <em>TalkingCode</em> yourself you will need to have the following:
			<List tag="ol">
				<Li>Install Docker and Docker compose</Li>
				<Li>Get an OpenAI and GitHub API key</Li>
				<Li>Copy over the compose files</Li>
				<Li>Create a .env file with the necessary config variables</Li>
				<Li>Run the containers</Li>
				<Li>Run the pipeline using Dagster</Li>
				<Li>Use the application through the OpenAPI docs, curl or your own frontend.</Li>
			</List>
			If that sounds like a lot, don't worry. I'll walk you through it step by step.
		</Paragraph>
	</section>

	<section>
		<Heading tag="h2" class="mb-8">Requirements</Heading>
		<Paragraph>
			To host <bold>TalkingCode</bold> yourself you will need to have the following:
			<List tag="ul">
				<Li>Docker and Docker Compose installed on your machine.</Li>
				<Li
					>An OpenAI API key. You can learn how to get one
					<A href="https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key"
						>here</A
					>
				</Li>
				<Li
					>A GitHub personal access token. You can learn how to do that
					<A
						href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token"
					>
						here
					</A>
				</Li>
			</List>
		</Paragraph>
	</section>
	<section>
		<Heading tag="h2" class="mb-8">Getting started</Heading>
		<Paragraph>
			After you have the above requirements, you can make an empty folder, for example
			<InlineCode>TalkingCode</InlineCode>. Afterwards you need to copy over both the
			<InlineCode>compose.backend.yml</InlineCode> and
			<InlineCode>compose.dataprocessing.yml</InlineCode> files from the repository. You can find them
			<A href="https://github.com/ChidiRnweke/TalkingCode">here.</A>
			<bold>Note:</bold> The folder also contains files called
			<InlineCode>compose.*.override.yml</InlineCode> you do not need to copy these files over. You may
			also just clone the repository instead of copying the files over.
		</Paragraph>
	</section>
	<section>
		<Heading tag="h2" class="mb-8">Configuration through environment variables</Heading>
		<Paragraph>
			After you have copied the files over, you need to create a file called
			<InlineCode>.env</InlineCode>. You can do this by running the following command:
			<InlineCode>touch .env</InlineCode>
			After you have created the file, you need to add a few mandatory environment variables. The rest
			are optional. Another thing you could do is use the <InlineCode
				>config/env.template</InlineCode
			> file as a starting point. You can copy the contents of the file and paste it into the <InlineCode
				>.env</InlineCode
			>.
		</Paragraph>

		<section class="my-8">
			<Heading tag="h3" class="mb-2">Mandatory environment variables</Heading>
			<Paragraph>
				These are the mandatory environment variables that you need to add to the
				<InlineCode>.env</InlineCode>. Without these, the application will not work. The list is
				kept as small as possible to make it easier to get started.
				<List tag="ul">
					<Li>
						<InlineCode>OPENAI_EMBEDDING_API_KEY</InlineCode> - This is your OpenAI API key.
					</Li>
					<Li>
						<InlineCode>GITHUB_API_TOKEN</InlineCode> - This is your GitHub personal access token.
					</Li>
					<Li>
						<InlineCode>WHITELISTED_EXTENSIONS</InlineCode> - The extensions that are allowed to be embedded.
						They need to be formatted as a JSON list. For example,
						<InlineCode>'["py", "js"]'</InlineCode>.
					</Li>
					<Li>
						<InlineCode>SYSTEM_PROMPT</InlineCode> - The prompt that the chat model will use. This should
						be a short to medium length description of the tasks the model will be asked to perform.
						For example, I specify it needs to answer questions about my projects without straying too
						far from the topic.
					</Li>
				</List>
			</Paragraph>
		</section>

		<section>
			<Heading tag="h3" class="mb-2">Optional environment variables</Heading>
			<Paragraph>
				Aside from the mandatory environment variables, there are also optional environment
				variables that you can add to the <InlineCode>.env</InlineCode>. These are used to configure
				the postgres database and tweak the models used by the application. If you're just trying it
				out, you can stick with the defaults.

				<List tag="ul">
					<Li>
						<InlineCode>POSTGRES_USER</InlineCode> - This is the username for the Postgres database.
						For example, you can use <InlineCode>postgres</InlineCode>.
					</Li>
					<Li>
						<InlineCode>POSTGRES_PASSWORD</InlineCode> - This is the password for the Postgres database.
						For example, you can use <InlineCode>postgres</InlineCode>.
					</Li>
					<Li>
						<InlineCode>POSTGRES_DB</InlineCode> - This is the name of the Postgres database. For example,
						you can use <InlineCode>TalkingCode</InlineCode>.
					</Li>
					<Li>
						<InlineCode>POSTGRES_HOST</InlineCode> - This is the host for the Postgres database. For
						example, you can use <InlineCode>localhost</InlineCode>.
					</Li>
					<Li>
						<InlineCode>POSTGRES_PORT</InlineCode> - This is the port for the Postgres database. For
						example, you can use <InlineCode>5432</InlineCode>.
					</Li>
					<Li>
						<InlineCode>BLACKLISTED_FILES</InlineCode> - The files that are not allowed to be embedded.
						They need to be formatted as a JSON list. For example,
						<InlineCode>'["package-lock.json", "package.json"]'</InlineCode>
					</Li>
					<Li>
						<InlineCode>EMBEDDING_MODEL</InlineCode> - The openAI model to use for embedding. For example,
						<InlineCode>text-embedding-3-large</InlineCode>. The choice is up to you. The full list
						of models can be found on
						<A href="https://beta.openai.com/docs/guides/embeddings">openAI's website</A>.
					</Li>
					<Li>
						<InlineCode>MAX_SPEND</InlineCode> - The maximum amount of money you want to spend on the
						OpenAI API per day. The number isn't 100 % accurate but it's a good, conservative estimate.
						The default is 1.5 dollars / day.
					</Li>
					<Li>
						<InlineCode>CHAT_MODEL</InlineCode> - The openAI model to use for generating answers. For
						example,
						<InlineCode>gpt-4o</InlineCode>. There is a trade-off between speed, cost, and quality
						where
						<InlineCode>gpt-4o</InlineCode> does well in all three. The full list of models can be found
						on
						<A href="https://beta.openai.com/docs/guides/chat">openAI's website</A>.
					</Li>
					<Li>
						<InlineCode>TOP_K</InlineCode> - The number of retrieved documents to consider for the RAG
						model. The default is 5 but you can change it to any number you like.
					</Li>
					<Li>
						<InlineCode>DAGSTER_PORT</InlineCode> - The port that the Dagster UI will be available on.
						The default is 3000, but that might conflict with other services you have running. You can
						change it to any number you like. The UI will be available on
						<InlineCode>localhost:PORT</InlineCode>
						.
					</Li>
					<Li>
						<InlineCode>BACKEND_PORT</InlineCode> - The port that the FastAPI backend will be available
						on. The default is 8000, but that might conflict with other services you have running. You
						can change it to any number you like. The backend will be available on
						<InlineCode>localhost:PORT</InlineCode>. You can browse to the docs by going to
						<InlineCode>localhost:PORT/docs</InlineCode>
						to start making requests with a low barrier to entry.
					</Li>
				</List>
			</Paragraph>
		</section>
	</section>
	<section>
		<Heading tag="h2" class="mb-8">Running the containers</Heading>
		<Paragraph>
			The next step is to run the containers. You can do this by running the following commands:
			<List tag="ol">
				<Li>
					<InlineCode>docker-compose -f --env-file .env compose.backend.yml up -d</InlineCode>
				</Li>
				<Li>
					<InlineCode>
						docker-compose -f --env.file .env compose.dataprocessing.yml up -d
					</InlineCode>
				</Li>
			</List>
			After you have run the commands, you can check if the containers are running by running the following
			command: <InlineCode>docker ps</InlineCode>. You should see three containers running. One for
			the backend, one for the database, and one for the data processing.
		</Paragraph>
	</section>

	<section>
		<Heading tag="h2" class="mb-8">Running the pipeline using dagster</Heading>
		<Paragraph>
			After you have the containers running, you can run the pipeline using Dagster. You can browse
			to <InlineCode>localhost:3000</InlineCode> or
			<InlineCode>localhost:DAGSTER_PORT</InlineCode> if you have changed the port. This will bring up
			the Dagster UI. You can then start the pipeline by clicking on the
			<em>materialize all</em> button.
		</Paragraph>
	</section>

	<section>
		<Heading tag="h2" class="mb-8">Using the application</Heading>
		<Paragraph>
			After you have started the pipeline, you can start using the application. You can browse to
			<InlineCode>localhost:8000/docs</InlineCode> or
			<InlineCode>localhost:BACKEND_PORT/docs</InlineCode> if you have changed the port. This will bring
			up the FastAPI docs. You can then start making requests to the API. You will have to provide your
			own frontend to interact with the API. You're free to use the frontend I used as a starting point.
		</Paragraph>
	</section>

	<section>
		<Heading tag="h2" class="mb-8">Conclusion</Heading>
		<Paragraph>
			That's it! You now have a fully working version of <bold>TalkingCode</bold> running on your machine.
			You can now start asking questions and see the model generate answers. If you have any questions
			or need help, feel free to reach out.
		</Paragraph>
	</section>
</article>
