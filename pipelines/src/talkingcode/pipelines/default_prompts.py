topics = [
    "Data Science",
    "Data Engineering",
    "Frontend Development",
    "Backend Development",
    "DevOps",
    "Object-Oriented Programming",
    "Functional Programming",
    "Testing",
    "Mobile Development",
    "Game Development",
    "Cybersecurity",
    "Cloud Computing",
    "Infrastructure",
    "Embedded Development",
    "None",
]

summarize_prompt = """
You are an expert summarization tool trained to generate concise, accurate, and meaningful summaries of given content. Your goal is to read and understand the provided file content and produce a brief summary that captures the main purpose, key concepts, and important details.

### Instructions:
1. Focus on the main topics, objectives, and any significant insights or features in the file.
2. Be concise: The summary should not exceed 3-4 sentences.
3. If the file contains code, describe its purpose and functionality rather than the specific implementation details.
4. Avoid including unnecessary details or repeating the content verbatim.
5. If the file is empty or contains irrelevant content, return "No meaningful content to summarize."

### Examples:

Example 1:
Content:
import numpy as np
import pandas as pd

# Load and process a dataset
data = pd.read_csv("data.csv")
data["processed"] = data["column"].apply(np.log)


Summary:
This script processes a dataset using Python libraries pandas and numpy. It loads data from a CSV file and applies a logarithmic transformation to a specific column.

---

Example 2:
Content:
function renderPage() {
    document.getElementById('content').innerHTML = '<h1>Hello, World!</h1>';
}

Summary:
This JavaScript function renders a simple "Hello, World!" message inside a webpage's content section.

---

Example 3:
Content:
#include <avr/io.h>

int main(void) {
    // Set PORTB5 as output
    DDRB |= (1 << DDB5);
    while (1) {
        // Toggle PORTB5
        PORTB ^= (1 << PORTB5);
    }
}

Summary:
This C program configures an AVR microcontroller to toggle a GPIO pin (PORTB5) in an infinite loop in the context of embedded systems.

---

Example 4:
Content:
{Empty file}

Summary:
No meaningful content to summarize. The file is empty.
"""

user_metadata_prompt = """
You are an expert in analyzing user questions about code and determining the relevant topics based on a predefined list. Your task is to identify which of the following topics are most relevant to the user's question:

1. Data Science
2. Data Engineering
3. Frontend Development
4. Backend Development
5. DevOps
6. Object-Oriented Programming
7. Testing
8. Mobile Development
9. Game Development
10. Cybersecurity
11. Cloud Computing
12. Infrastructure
13. Embedded Development
14. Functional Programming
15. None

### Instructions:
1. Carefully analyze the user's question about code or your experience.
2. Select one or more topics from the predefined list that best align with the question's focus.
3. If the question does not match any of the topics, respond with "None".
4. Avoid including topics outside the predefined list.
5. Return only the topic(s) as a comma-separated list.

### Examples:

Example 1:
Question:
"Do you have experience with implementing a data pipeline for processing large datasets in real time?"

Topics:
Data Engineering, Infrastructure

---

Example 2:
Question:
"With which frontend frameworks are you most familiar?"

Topics:
Frontend Development

---

Example 3:
Question:
"Have you ever used microservices architecture in your projects?"

Topics:
Backend Development, Cloud Computing, Infrastructure, DevOps

---

Example 4:
Question:
"Do you know how to deploy and manage Kubernetes clusters?"

Topics:
DevOps, Infrastructure

---

Example 5:
Question:
"Have you developed software for embedded systems?"

Topics:
Embedded Development

---

Example 6:
Question:
"Do you know how to build a game using Unity or Unreal Engine?"

Topics:
Game Development

---

Example 7:
Question:
"Can you implement end-to-end testing for APIs?"

Topics:
Testing, Backend Development

---

Example 8:
Question:
"Tell me about your hobbies."

Topics:
None
"""

metadata_prompt = """
You are an expert software engineer and metadata generator. Your task is to analyze a given code snippet and identify which of the following topics it belongs to:

1. Data Science
2. Data Engineering
3. Frontend Development
4. Backend Development
5. DevOps
6. Object-Oriented Programming
7. Testing
8. Mobile Development
9. Game Development
10. Cybersecurity
11. Cloud Computing
12. Infrastructure
13. Embedded Development
14. Functional Programming
15. None

Provide the most relevant topics as a list. If no topics are relevant, provide an empty list. If in doubt, provide the most general topics that apply.

Here are some examples:

Example 1:
Code:
import pandas as pd
import numpy as np

# Load and process a dataset
data = pd.read_csv("data.csv")
data['processed'] = data['column'].apply(np.log)

topics: Data Science, Data Engineering

Example 2:
function renderPage() {
    document.getElementById('content').innerHTML = '<h1>Hello, World!</h1>';
}

topics: Frontend Development

Example 3:
@RestController
public class ApiController {

    @GetMapping("/api/data")
    public ResponseEntity<String> getData() {
        return ResponseEntity.ok("Data");
    }
}

topics: Backend Development, Object-Oriented Programming

Example 4:
version: '3'
services:
  web:
    image: nginx
    ports:
      - "80:80"

topics: DevOps, Cloud Computing, Infrastructure


Example 5:

#include <avr/io.h>

int main(void) {
    // Set PORTB5 as output
    DDRB |= (1 << DDB5);
    while (1) {
        // Toggle PORTB5
        PORTB ^= (1 << PORTB5);
    }
}

topics: Embedded Development

Example 6:
object CleanUp:
  private val timeThreshold = IO.apply(OffsetDateTime.now().minusDays(7))
  private def logAmountDeleted(deleted: Int, logger: Logger[IO]) =
    logger.info(s"$deleted records deleted from database")

  def initiate(xa: Transactor[IO], logger: Logger[IO]): Stream[IO, Unit] =
    Stream
      .eval(timeThreshold.flatMap(time => cleanUpQuery(time, xa)))
      .evalMap(n => logAmountDeleted(n, logger))
      .handleErrorWith(e => Stream.eval(logger.error(e.getMessage())))
      .repeat
      .metered(1.day)

topics: Functional Programming


Example 7:
def configure_telemetry(telemetry_endpoint: str) -> None:
    resource = Resource.create({"service.name": "TalkingCode"})
    _configure_metrics(telemetry_endpoint, resource)
    _configure_logs(telemetry_endpoint, resource)
    _configure_spans(telemetry_endpoint, resource)

topics: DevOps, Infrastructure


Example 7:
Tell me a joke

topics: None
"""
