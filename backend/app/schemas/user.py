from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import Plan


class NotificationPrefs(BaseModel):
    """Matches the three toggles on the profile screen."""

    streak: bool = True
    weekly: bool = True
    bosses: bool = False


class AvatarOut(BaseModel):
    body: str
    head: str
    accent: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    toy_name: str
    trainee_no: str  # zero-padded for the "TRAINEE TOY · No. 0471" badge
    plan: Plan
    avatar: AvatarOut
    notifications: NotificationPrefs


class AccountUpdateIn(BaseModel):
    """The profile screen's "Save account" payload — every field optional.

    Deliberately excludes email, password and plan. The first two are credentials and
    require re-authentication (see PasswordChangeIn / EmailChangeIn); `plan` is a paid
    entitlement and must only ever be set by the billing flow, never by the account
    holder — otherwise every user can grant themselves the paid tier.
    """

    toy_name: str | None = Field(default=None, min_length=1, max_length=60)
    notifications: NotificationPrefs | None = None


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class EmailChangeIn(BaseModel):
    """Changing the address that can reset the account is a credential change."""

    current_password: str = Field(min_length=1, max_length=128)
    new_email: EmailStr


class PlanOut(BaseModel):
    key: str
    name: str
    price: str
    perk: str
