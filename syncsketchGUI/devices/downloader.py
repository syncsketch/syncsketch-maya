import logging

from ..lib import user
from ..lib import database

logger = logging.getLogger("syncsketchGUI")


def download_greasepencil(current_user=None):
    if not current_user:
        current_user = user.SyncSketchUser()

    review_id = database.read_cache('target_review_id')
    media_id = database.read_cache('target_media_id')
    logger.info("current_user: {}, target_review_id: {}, target_media_id: {}".format(current_user, review_id, media_id))

    return current_user.download_greasepencil(review_id, media_id)


def download_video(current_user=None, media_id=None, review_id=None):
    if not current_user:
        current_user = user.SyncSketchUser()

    media_id = media_id or database.read_cache('target_media_id')
    review_id = review_id or database.read_cache('target_review_id')
    logger.info("current_user: {}, target_media_id: {}".format(current_user, media_id))

    return current_user.download_annotated_video(media_id, review_id)
