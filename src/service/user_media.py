from typing import Dict, List

from src import tables
from src.database import Session
from src.models.user_media import CreateMedia


class MediaService:
    def __init__(self):
        self.session = Session()

    def create(self,  media_data: CreateMedia) -> tables.UserMedia:
        if media_data.media_type == 8:
            media = tables.UserMedia(
                username=media_data.username,
                user_id=media_data.user_id,
                media_pk=media_data.media_pk,
                media_type=media_data.media_type,
                caption=media_data.caption
            )
            self.session.add(media)
            self.session.commit()
            for item in media_data.url_list:
                media_type, url = item
                new_media = tables.Carousel(
                    media_id=media.id,
                    media_type=media_type,
                    url=url
                )
                self.session.add(new_media)
                self.session.commit()

        else:
            media = tables.UserMedia(
                username=media_data.username,
                user_id=media_data.user_id,
                media_pk=media_data.media_pk,
                media_type=media_data.media_type,
                url=media_data.url_list[0][-1],
                caption=media_data.caption
            )
            self.session.add(media)
            self.session.commit()

        return media

    def get_users_media_pk(self, user_id) -> List[int]:
        user_media = (
            self.session
            .query(tables.UserMedia)
            .filter_by(user_id=user_id)
            .all()
        )
        if not user_media:
            return False
        media_pk_list = [media.media_pk for media in user_media]
        return media_pk_list

    def get_by_media_pk(self, media_pk: int) -> Dict:
        media = (
            self.session
            .query(tables.UserMedia)
            .filter_by(media_pk=media_pk)
            .first()
        )
        if not media:
            return False
        result = dict()
        result["username"] = media.username
        result["link"] = f"https://www.instagram.com/{result['username']}/"
        result["caption"] = media.caption
        if media.media_type == 8:
            media_id = media.id
            carousel = (
                self.session
                .query(tables.Carousel)
                .filter_by(media_id=media_id)
                .all()
            )
            result["content"] = [(item.media_type, item.url) for item in carousel]
        else:
            result["content"] = [(media.media_type, media.url)]

        return result
