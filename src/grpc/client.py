import json
from fastapi import Depends
import grpc
from src.grpc import user_pb2
from src.grpc import user_pb2_grpc
from google.protobuf.json_format import MessageToDict, MessageToJson
from src.db.redis import get_redis
from redis.asyncio import Redis
from src.core import config

class UserRpcService:
    API_RPC_HOST = config.API_RPC_HOST

    def __init__(self):
        channel = grpc.insecure_channel(self.API_RPC_HOST)
        self.stub = user_pb2_grpc.UsersStub(channel=channel)

    async def _put_to_cache(self, key, data, expire):
        redis: Redis = await get_redis()
        print('Set Object To Cache')
        data_json = json.dumps(data)
        await redis.set(
            key,
            data_json,
            expire
        )

    async def _object_from_cache(self, key: str):
        redis: Redis = await get_redis()
        print('Get Object From Cache')
        data = await redis.get(key)


        if not data:
            return None
        data = json.loads(data)
        return data

    async def _delete_object_from_cache(self, key: str):
        redis: Redis = await get_redis()
        await redis.delete(key)

    async def user_by_uid(self, uid):
        # user_json = await self._object_from_cache(f"user_{uid}")
        # if user_json:
        #     return user_json
        user_by_uid_request = user_pb2.GetUserByIdRequest()
        user_by_uid_request.id = uid

        try:
            rsp: user_pb2.UserInfoResponce = self.stub.GetUsersById(
                user_by_uid_request
            )
            user_json = MessageToDict(rsp)
            if not user_json:
                return None
            await self._put_to_cache(f"user_{uid}", user_json, 60*15)
            return user_json
        except Exception as e:
            print('An error occurred:', e)
            return None

    async def user_by_slug(self, slug):
        # user_json = await self._object_from_cache(f"user_{slug}")
        # if user_json:
        #     return user_json
        user_by_uid_request = user_pb2.GetUserBySlugRequest()
        user_by_uid_request.slug = slug

        try:
            rsp: user_pb2.UserInfoResponce = self.stub.GetUsersBySlug(
                user_by_uid_request
            )
            user_json = MessageToDict(rsp)
            if not user_json:
                return None
            await self._put_to_cache(f"user_{slug}", user_json, 60*15)
            return user_json
        except Exception as e:
            print('An error occurred:', e)
            return None


    async def get_users(self, page = 1, search=''):
        # user_json = await self._object_from_cache(f"users_{page}_{search}")
        # if user_json:
        #     return user_json
        users_request = user_pb2.GetUsersRequest()
        users_request.page = page
        users_request.search = search
        try:
            rsp: user_pb2.GetUserListResponce = self.stub.GetUserList(
                users_request
            )
            user_json = MessageToDict(rsp, including_default_value_fields=True)
            if not user_json:
                return None
            await self._put_to_cache(f"users_{page}_{search}", user_json, 60*15)
            return user_json
        except Exception as e:
            print('efeAn error occurred:', e)
            return {'message': 'error'}

    async def get_users_by_role(self, role_id, page=1, search=''):
        users_request = user_pb2.GetUserByFilterRequst()
        users_request.role_id = role_id
        users_request.page = page
        users_request.search = search
        try:
            rsp: user_pb2.GetUserListResponce = self.stub.GetUserListByRole(
                users_request
            )
            user_json = MessageToDict(rsp)
            return user_json
        except:
            print('ERROR')
            return {'message': 'error'}

user_rpc = UserRpcService()
