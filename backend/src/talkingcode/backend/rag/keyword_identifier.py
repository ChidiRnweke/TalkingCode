from dataclasses import dataclass
from typing import Protocol

from openai import AsyncOpenAI
from pydantic import BaseModel


class KeywordIdentifier(Protocol):
    async def identify_keywords(self, text: str) -> list[str]:
        """
        Identifies the keywords in the given text.
        """
        ...


class IdentifiedKeywords(BaseModel):
    keywords: list[str]


@dataclass(frozen=True, slots=True)
class KeywordIdentifierService(KeywordIdentifier):
    """
    A class that performs keyword identification given a text.
    """

    client: AsyncOpenAI
    model_name: str
    prompt: str

    async def identify_keywords(self, text: str) -> list[str]:
        """
        Identifies the keywords in the given text.

        Args:
            text (str): The text for which to identify the keywords.

        Returns:
            list[str]: The keywords identified in the text.
        """
        response = await self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": text},
            ],
            response_format=IdentifiedKeywords,
        )
        keywords = response.choices[0].message.parsed
        if not keywords:
            keywords = IdentifiedKeywords(keywords=["None"])
        return keywords.keywords
