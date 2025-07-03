from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.models import User

from .schemas import UserCreateModel
from .utils import generate_passwd_hash


class UserService:
    
    async def _get_user_by_field(self, field_name: str, value: str, session: AsyncSession):
        statement = select(User).where(getattr(User, field_name) == value)
        result = await session.exec(statement)
        return result.first()

    async def _user_exists_by_field(self, field_name: str, value: str, session: AsyncSession):
        user = await self._get_user_by_field(field_name, value, session)
        return user is not None


    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        user_data_dict = user_data.model_dump()

        new_user = User(**user_data_dict)

        new_user.password_hash = generate_passwd_hash(user_data_dict["password"])
        new_user.role = "user"

        session.add(new_user)

        await session.commit()

        return new_user


    async def update_user(self, user:User , user_data: dict,session:AsyncSession):

        for k, v in user_data.items():
            setattr(user, k, v)

        await session.commit()

        return user