import random
import threading
from datetime import datetime

import requests
from asyncio import sleep
from typing import Dict, List
from src.models.user_media import CreateMedia
from src.service.user_media import MediaService


class DownloadService:
    def __init__(self, api_key: str):
        self.media_db = MediaService()
        self.api_key = f"&access_key={api_key}"
        self.url = "https://api.lamadava.com"
        self.stories = "/v1/user/stories/by/username?username={}"
        self.post = "/v1/media/by/url?url={}"
        self.highlight = "/v1/highlight/by/url?url={}"

    def user_exists(self, target_name: str):
        link = f"https://api.lamadava.com/v1/user/by/username?username={target_name}" + self.api_key
        user = requests.get(link).json()
        return user["pk"]

    # STORIES

    def get_stories(self, target_name: str) -> List:
        try:
            link = self.url + self.stories.format(target_name) + self.api_key
            stories = requests.get(link)
            user_stories = [
                (1, story["thumbnail_url"])
                if story["media_type"] == 1 or story["media_type"] == 0
                else (2, story["video_url"])
                for story in stories.json()
            ]
            return user_stories
        except:
            raise KeyError

    @classmethod
    def download_story(cls, story_info):
        result = [story_info]
        return result

    # POSTS
    @classmethod
    def __download(cls, media_info, media_type: int):
        if media_type == 1:
            return [(1, media_info["thumbnail_url"])]
        elif media_type == 2:
            return [(2, media_info["video_url"])]
        elif media_type == 8:
            resources = media_info["resources"]
            return [(1, item["thumbnail_url"]) if item["media_type"] == 1 else (2, item["video_url"]) for item in resources]
        elif media_type == 0:
            return [(1, media_info["thumbnail_url"])]
        return

    def download_post(self, url: str) -> Dict:
        try:
            link = self.url + self.post.format(url) + self.api_key
            media_info = requests.get(link).json()
            result = dict()
            media_type = media_info["media_type"]
            result["username"] = media_info["user"]["username"]
            result["link"] = f"https://www.instagram.com/{result['username']}/"
            result["content"] = self.__download(media_info, media_type)
            result["caption"] = media_info["caption_text"]
            return result
        except:
            raise KeyError

    def download_highlights(self, url: str) -> Dict:
        try:
            result = dict()
            link = self.url + self.highlight.format(url) + self.api_key
            highlight_info = requests.get(link).json()
            stories_list = highlight_info["items"]
            result["username"] = highlight_info["user"]["username"]
            result["link"] = f"https://www.instagram.com/{result['username']}/"
            result["content"] = list()
            result["caption"] = ""
            for story in stories_list:
                media_type = story["media_type"]
                result["content"] += self.__download(story, media_type)
            return result
        except:
            raise KeyError

    # WATCH UPDATES

    async def check_stories(self, target_name: str, last_watch):
        await sleep(random.randint(2, 8))
        link = self.url + self.stories.format(target_name) + self.api_key
        user_stories = requests.get(link).json()
        new_stories = list()
        for story in user_stories:
            pic_time = " ".join(story["taken_at"].split("T"))
            pic_time = pic_time[:-6]
            pic_time = datetime.strptime(pic_time, "%Y-%m-%d %H:%M:%S")
            if pic_time > last_watch:
                res = (1, story["thumbnail_url"]) if story["media_type"] == 1 or story["media_type"] == 0 else (2, story["video_url"])
                new_stories.append(res)
        return new_stories

    async def check_posts(self, user_id: str, last_watch):
        await sleep(random.randint(2, 8))
        link = self.url + f"/v1/user/medias?user_id={user_id}" + self.api_key
        user_media = requests.get(link).json()
        new_posts = list()
        for post in user_media:
            pic_time = " ".join(post["taken_at"].split("T"))
            pic_time = pic_time[:-6]
            pic_time = datetime.strptime(pic_time, "%Y-%m-%d %H:%M:%S")
            if pic_time > last_watch:
                new_posts += self.__download(post, post["media_type"])
        return new_posts
