from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from pydantic import AnyUrl, BaseModel, EmailStr, Extra, Field


class Plan(BaseModel):
    collaborators: int
    name: str
    space: int
    private_repos: int


class Model1(BaseModel):
    login: str = Field(..., examples=["octocat"])
    id: int = Field(..., examples=[1])
    user_view_type: Optional[str] = None
    node_id: str = Field(..., examples=["MDQ6VXNlcjE="])
    avatar_url: AnyUrl = Field(
        ..., examples=["https://github.com/images/error/octocat_happy.gif"]
    )
    gravatar_id: Optional[str] = Field(
        ..., examples=["41d064eb2195891e12d0413f63227ea7"]
    )
    url: AnyUrl = Field(..., examples=["https://api.github.com/users/octocat"])
    html_url: AnyUrl = Field(..., examples=["https://github.com/octocat"])
    followers_url: AnyUrl = Field(
        ..., examples=["https://api.github.com/users/octocat/followers"]
    )
    following_url: str = Field(
        ..., examples=["https://api.github.com/users/octocat/following{/other_user}"]
    )
    gists_url: str = Field(
        ..., examples=["https://api.github.com/users/octocat/gists{/gist_id}"]
    )
    starred_url: str = Field(
        ..., examples=["https://api.github.com/users/octocat/starred{/owner}{/repo}"]
    )
    subscriptions_url: AnyUrl = Field(
        ..., examples=["https://api.github.com/users/octocat/subscriptions"]
    )
    organizations_url: AnyUrl = Field(
        ..., examples=["https://api.github.com/users/octocat/orgs"]
    )
    repos_url: AnyUrl = Field(
        ..., examples=["https://api.github.com/users/octocat/repos"]
    )
    events_url: str = Field(
        ..., examples=["https://api.github.com/users/octocat/events{/privacy}"]
    )
    received_events_url: AnyUrl = Field(
        ..., examples=["https://api.github.com/users/octocat/received_events"]
    )
    type: str = Field(..., examples=["User"])
    site_admin: bool
    name: Optional[str] = Field(..., examples=["monalisa octocat"])
    company: Optional[str] = Field(..., examples=["GitHub"])
    blog: Optional[str] = Field(..., examples=["https://github.com/blog"])
    location: Optional[str] = Field(..., examples=["San Francisco"])
    email: Optional[EmailStr] = Field(..., examples=["octocat@github.com"])
    notification_email: Optional[EmailStr] = Field(
        None, examples=["octocat@github.com"]
    )
    hireable: Optional[bool]
    bio: Optional[str] = Field(..., examples=["There once was..."])
    twitter_username: Optional[str] = Field(None, examples=["monalisa"])
    public_repos: int = Field(..., examples=[2])
    public_gists: int = Field(..., examples=[1])
    followers: int = Field(..., examples=[20])
    following: int = Field(..., examples=[0])
    created_at: datetime = Field(..., examples=["2008-01-14T04:33:35Z"])
    updated_at: datetime = Field(..., examples=["2008-01-14T04:33:35Z"])
    private_gists: int = Field(..., examples=[81])
    total_private_repos: int = Field(..., examples=[100])
    owned_private_repos: int = Field(..., examples=[100])
    disk_usage: int = Field(..., examples=[10000])
    collaborators: int = Field(..., examples=[8])
    two_factor_authentication: bool = Field(..., examples=[True])
    plan: Optional[Plan] = None
    business_plus: Optional[bool] = None
    ldap_dn: Optional[str] = None


class Model2(BaseModel):
    class Config:
        extra = Extra.forbid

    login: str
    id: int
    user_view_type: Optional[str] = None
    node_id: str
    avatar_url: AnyUrl
    gravatar_id: Optional[str]
    url: AnyUrl
    html_url: AnyUrl
    followers_url: AnyUrl
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: AnyUrl
    organizations_url: AnyUrl
    repos_url: AnyUrl
    events_url: str
    received_events_url: AnyUrl
    type: str
    site_admin: bool
    name: Optional[str]
    company: Optional[str]
    blog: Optional[str]
    location: Optional[str]
    email: Optional[EmailStr]
    notification_email: Optional[EmailStr] = None
    hireable: Optional[bool]
    bio: Optional[str]
    twitter_username: Optional[str] = None
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: datetime
    updated_at: datetime
    plan: Optional[Plan] = None
    private_gists: Optional[int] = Field(None, examples=[1])
    total_private_repos: Optional[int] = Field(None, examples=[2])
    owned_private_repos: Optional[int] = Field(None, examples=[2])
    disk_usage: Optional[int] = Field(None, examples=[1])
    collaborators: Optional[int] = Field(None, examples=[3])


class Model(BaseModel):
    __root__: Union[Model1, Model2]
