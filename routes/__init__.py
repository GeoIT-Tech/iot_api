from fastapi import APIRouter

from resources.authController import router as authRouter
from resources.userController import router as userRouter
from resources.settingController import router as settingRouter
from resources.postController import router as postRouter
from resources.certificateController import router as certificateRouter
from resources.ebattleController import router as ebattleRouter
from resources.reportController import router as reportRouter
from resources.coreController import router as coreRouter
from resources.reviewController import router as reviewRouter
from resources.boostController import router as boostRouter


router = APIRouter()

router.include_router(authRouter, prefix='/auth', tags=['Auth'])
router.include_router(userRouter, prefix='/user', tags=['User'])
router.include_router(settingRouter, prefix='/setting', tags=['Setting'])
router.include_router(postRouter, prefix='/post', tags=['Post'])
router.include_router(certificateRouter, prefix='/certificate', tags=['Certificate'])
router.include_router(ebattleRouter, prefix='/ebattle', tags=['EBattle'])
router.include_router(reportRouter, prefix='/report', tags=['Report'])
router.include_router(coreRouter, prefix='/core', tags=['Core'])
router.include_router(reviewRouter, prefix='/review', tags=['Review'])
router.include_router(boostRouter, prefix='/boost', tags=['Boost'])
