# Testing

The testing strategy of the backend is using a combination of unit and integration tests. Both are written using the `pytest` framework. You can find the tests in the `tests` directory. Naturally, the unit tests are faster than the integration tests. The integration tests are slower because they require spinning up a PostgreSQL database using `Testcontainers`. You can run them separately using the `pytest /unit` or `pytest /integration` command.

## Unit tests

As much as possible, the backend is designed to be testable. The main units that are tested are the services. The services are the main components that interact with the database and the external APIs. The services are tested by writing stubs for the dependencies that they have. The tests are written in a way that they test the real behavior of the services.

These tests are low effort to write and maintain. They are also fast to run. They don't require spinning up a database or making API calls. The issue is that they don't test the interaction between the different parts of the backend. This is where the integration tests come in. 

## Integration tests

Integration tests actually capture a lot of the complexity of the backend. They test the interaction between the different parts of the backend. The tests are written in a way that they test the real behavior of the backend. The tests are run using `pytest`. The tests are run in the same event loop. This has pros and cons. The pros are that the tests are faster and that the database is only created once. The cons are that the tests are not isolated from each other. The practical implication is that you more or less need to know what the other tests are doing otherwise tests may pass or fail unexpectedly. I'm the only one working on this project, so I'm fine with this.

### Setup

The general strategy for integration tests is to test the interaction between different parts of the backend. FastAPI is only used to expose the endpoints, so the tests are not run through the API. Instead, the tests are run directly on the backend code. 

The tests are run using `pytest`. The test files are located in the `tests/integration` directory. The tests are run using the `pytest` command. 

`Testcontainers` is used to spin up a PostgreSQL database for the tests. The database is created and destroyed for each test run. The database is seeded with test data using the `database_fixtures` [fixture](/reference/tests/fixtures/#tests.integration.database_fixtures.database_session).

### Test structure

The main units that have to be tested are the `SQLRetrievalService`'s public methods as well as the `RetrievalAugmentedGeneration` service. The former is tested by using the fixtures that are provided and testing its real behavior. The latter is trickier because it depends on `EmbeddingService` and `GenerationService`. The concrete implementations require calling the real API and incurring costs, which is not desirable in a test. The solution around this is making stubs for these services and testing the behavior of the `RetrievalAugmentedGeneration` service.

You're encouraged to read the tests in the `tests/integration` [directory](https://github.com/ChidiRnweke/chatGITpt/tree/main/backend/tests/integration) to get a better understanding of how the tests work. I won't go into detail here because it's not the focus of this documentation. 


