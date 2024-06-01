from fastapi import APIRouter

from resources.authController import router as authRouter
from resources.userController import router as userRouter

router = APIRouter()

router.include_router(authRouter, prefix='/auth', tags=['Auth'])
router.include_router(userRouter, prefix='/user', tags=['User'])
