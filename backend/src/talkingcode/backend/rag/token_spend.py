from dataclasses import dataclass
from datetime import date
from typing import Protocol

from sqlalchemy import Date, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.backend.errors import map_errors
from talkingcode.shared.database import TokenSpendModel


class TokenSpendStore(Protocol):
    async def store_token_spent(
        self, session_id: str, token_count: int, model_name: str
    ):
        """

        Stores the token count spent for a given session ID and model name.
        This is necessary to track the token spend for the given session. This
        is used further down the line to calculate the current spend and enforce
        the spend limit.

        Args:
            session_id (str): The session ID.
            token_count (int): The number of tokens spent.
            model_name (str): The name of the model used for token count. Different
                models have different token costs. Embedding models are
                typically cheaper than generation models.
        """

        ...

    async def get_current_spend(self, date: date) -> float:
        """

        Retrieves the current spend for a given date. The date is
        mostly given as a parameter to facilitate testing, it keeps
        this method more pure than it is if it had to instantiate the date.

        Args:
            date (date): The date for which to retrieve the current spend.


        Returns:
            (float): The current spend for the given date.
        """
        ...


@dataclass(frozen=True, slots=True)
class SQLTokenStore(TokenSpendStore):
    async_session: AsyncSession

    async def store_token_spent(
        self,
        session_id: str,
        token_count: int,
        model_name: str,
    ) -> None:
        """
        In multiple steps of the RAG pipeline, we need to store the token count spent for a given session ID
        and model name. This is necessary to track the token spend for the given session. This is used further
        down the line to calculate the current spend and enforce the spend limit.

        The moments where we need to store the token count spent are:
        - After the embedding step.
        - After the generation step.

        The moments this is done may also increase as the RAG is further developed.


        Args:
            session_id (str): The session ID. Corresponds to a single conversation.
            token_count (int): The number of tokens spent.
            model_name (str): The name of the model used. Different models have different token costs.
        """
        token_spend = TokenSpendModel(
            session_id=session_id,
            token_count=token_count,
            model=model_name,
        )
        async with self.async_session.begin():
            with map_errors():
                self.async_session.add(token_spend)
                await self.async_session.commit()

    async def get_current_spend(self, date: date) -> float:
        """
        Retrieves the current spend for a given date. The date is mostly given as a parameter to facilitate
        testing, it keeps this method more pure than it is if it had to instantiate the date.

        The current spend is given as follows:
        - The token count spent for the given date is retrieved.
        - The token count spent is multiplied by 0.00001 to get the spend in dollars.
        - The sum of all the spends is returned.

        0.00001 is taken as a constant, it's the approximate cost, taking into account both model costs. It's a
        conservative estimate, the actual cost may be lower.


        Args:
            date (datetime.date): The date for which to retrieve the current spend.

        Returns:
            (float): The current spend for the given date.
        """
        stmt = select(TokenSpendModel.token_count).where(
            cast(TokenSpendModel.timestamp, Date) == cast(date, Date)
        )
        async with self.async_session.begin():
            with map_errors():
                result = (await self.async_session.scalars(stmt)).all()
        return sum(result) * 0.000003
