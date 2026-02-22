"""Tests for errors."""
import pytest

from talkingcode.errors import AppError, InputError, NotFoundError, InfraError, UnauthorisedError


class TestAppError:
    def test_basic_error(self):
        error = AppError("Test error")
        assert str(error) == "Test error"


class TestInputError:
    def test_creation(self):
        error = InputError("Invalid input")
        assert error.message == "Invalid input"
        assert str(error) == "Invalid input"


class TestNotFoundError:
    def test_creation(self):
        error = NotFoundError("User")
        assert error.resource == "User"
        assert "User not found" in str(error)


class TestInfraError:
    def test_creation(self):
        error = InfraError("Database connection failed")
        assert "Database connection failed" in str(error)


class TestUnauthorisedError:
    def test_creation(self):
        error = UnauthorisedError()
        assert isinstance(error, AppError)
