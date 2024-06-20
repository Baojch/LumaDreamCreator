import argparse
import os
import time
from http.cookies import SimpleCookie
from datetime import datetime
from urllib.parse import urlparse, unquote

from fake_useragent import UserAgent
import requests
from requests.utils import cookiejar_from_dict

browser_version = "chrome125"
ua = UserAgent(browsers=["chrome"])

class VideoGen:
    def __init__(self, cookie, proxies=None) -> None:
        self.session: requests.Session = requests.Session()
        self.cookie = cookie
        self.session.cookies = self.parse_cookie_string(self.cookie)
        self.session.proxies = proxies or {}

    @staticmethod
    def parse_cookie_string(cookie_string):
        cookie = SimpleCookie()
        cookie.load(cookie_string)
        cookies_dict = {}
        cookiejar = None
        for key, morsel in cookie.items():
            cookies_dict[key] = morsel.value
            cookiejar = cookiejar_from_dict(
                cookies_dict, cookiejar=None, overwrite=True
            )
        return cookiejar

    def get_limit_left(self) -> int:
        self.session.headers["user-agent"] = ua.random
        url = "https://internal-api.virginia.labs.lumalabs.ai/api/photon/v1/subscription/usage"
        try:
            r = self.session.get(url)
            print(f"Request URL: {url}")
            print(f"Response status code: {r.status_code}")
            if not r.ok:
                raise Exception("Can not get limit left.")
            data = r.json()
            return int(data["available"])
        except Exception as e:
            print(f"Error getting limit left: {e}")
            raise

    def get_signed_upload(self):
        url = "https://internal-api.virginia.labs.lumalabs.ai/api/photon/v1/generations/file_upload"
        params = {
            'file_type': 'image',
            'filename': 'file.jpg'
        }
        response = self.session.post(url, params=params)
        response.raise_for_status()
        return response.json()

    def upload_file(self, image_file):
        try:
            signed_upload = self.get_signed_upload()
            presigned_url = signed_upload['presigned_url']
            public_url = signed_upload['public_url']

            with open(image_file, 'rb') as file:
                response = self.session.put(presigned_url, data=file,
                                            headers={'Content-Type': "image/png", "Referer": "https://lumalabs.ai/",
                                                     "origin": "https://lumalabs.ai"})

            if response.status_code == 200:
                print("Upload successful:", public_url)
                return public_url
            else:
                print("Upload failed.")
        except Exception as e:
            print("Upload failed.")
            print("Error uploading image:", e)

    def refresh_dream_machine(self):
        url = "https://internal-api.virginia.labs.lumalabs.ai/api/photon/v1/user/generations/"
        querystring = {"offset": "0", "limit": "10"}

        response = self.session.get(url, params=querystring)
        return response.json()

    @staticmethod
    def generate_slug(url):
        path = urlparse(url).path
        filename = os.path.basename(unquote(path))
        slug, _ = os.path.splitext(filename)
        return slug

    def save_video(
        self,
        prompt: str,
        image_file: str,
        output_dir: str,
    ) -> str:
        url = "https://internal-api.virginia.labs.lumalabs.ai/api/photon/v1/generations/"

        if image_file:
            print("uploading image")
            img_url = self.upload_file(image_file)
            payload = {
                "aspect_ratio": "16:9",
                "expand_prompt": True,
                "image_url": img_url,
                "user_prompt": prompt
            }
        else:
            payload = {
                "user_prompt": prompt,
                "aspect_ratio": "16:9",
                "expand_prompt": True
            }

        headers = {
            "Origin": "https://lumalabs.ai",
            "Referer": "https://lumalabs.ai",
            "content-type": "application/json"
        }
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        try:
            r = self.session.post(url, json=payload, headers=headers).json()
            print(r)
            task_id = r[0]["id"]
        except Exception as e:
            print(e)
            print("Another try")
            r = self.session.post(url, json=payload, headers=headers).json()
            print(r)
            task_id = r[0]["id"]
        return task_id

    def wait_for_videos(self, task_ids: list, output_dir: str) -> list:
        start = time.time()
        video_paths = []

        while True:
            if int(time.time() - start) > 3000:
                raise Exception("Error: 50 minutes passed and not all videos are generated.")

            response_json = self.refresh_dream_machine()
            for it in response_json:
                if it["id"] in task_ids:
                    print(f"Proceeding state {it['state']} for task {it['id']}")
                    if it["state"] == "pending":
                        print("Pending in queue, will wait more time")
                    elif it["state"] == "failed":
                        print(f"Generation failed for task {it['id']}")
                        raise Exception(f"Generation failed for task {it['id']}")
                    elif it['video']:
                        print(f"New video link for task {it['id']}: {it['video']['url']}")
                        video_url = it['video']['url']
                        content = self.session.get(video_url)
                        slug = self.generate_slug(video_url)
                        video_path = f"{output_dir}/output_{slug}.mp4"
                        with open(video_path, "wb") as f:
                            f.write(content.content)
                        print(f"Video saved to {video_path}")
                        video_paths.append(video_path)
                        task_ids.remove(it["id"])  # Remove task ID from list since video is saved

            if not task_ids:
                break

            time.sleep(20)
            print("Sleeping for 20 seconds")

        return video_paths


def main():
    # Define external parameters directly in the main function
    cookie = "yourcookie"
    image_files = ["test_imgs/girl.png", "test_imgs/dog.png"]
    prompts = ["A Hanfu girl", "A cute corgi sitting on the grass"]
    output_dir = "./output"
    proxies = {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
    }
    # Create video generator
    video_generator = VideoGen(
        cookie,
        proxies=proxies
    )
    print(f"Left {video_generator.get_limit_left()} times.")
    task_ids = []
    video_generator.refresh_dream_machine()
    for image_file, prompt in zip(image_files, prompts):
        task_id = video_generator.save_video(
            prompt=prompt,
            image_file=image_file,
            output_dir=output_dir,
        )
        task_ids.append(task_id)
        time.sleep(0.5)
    
    print(task_ids)
    
    video_paths = video_generator.wait_for_videos(task_ids, output_dir)
    print("Generated video paths:", video_paths)

if __name__ == "__main__":
    main()
