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
    def init(self, cookie, image_file="", proxies=None) -> None:
        self.session: requests.Session = requests.Session()
        self.cookie = cookie
        self.session.cookies = self.parse_cookie_string(self.cookie)
        self.image_file = image_file
        self.session.proxies = proxies or {}
        print(self.image_file)
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

    def upload_file(self):
        try:
            signed_upload = self.get_signed_upload()
            presigned_url = signed_upload['presigned_url']
            public_url = signed_upload['public_url']

            with open(self.image_file, 'rb') as file:
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
        output_dir: str,
    ) -> None:
        url = "https://internal-api.virginia.labs.lumalabs.ai/api/photon/v1/generations/"

        if self.image_file:
            print("uploading image")
            img_url = self.upload_file()
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
            task_id = r[0]["id"]
        except Exception as e:
            print(e)
            print("Another try")
            r = self.session.post(url, json=payload, headers=headers).json()
            task_id = r[0]["id"]
        start = time.time()
        video_url = ""
        while True:
            if int(time.time() - start) > 1200:
                raise Exception("Error 20 minutes passed.")
            response_json = self.refresh_dream_machine()
            for it in response_json:
                if it["id"] == task_id:
                    print(f"proceeding state {it['state']}")
                    if it["state"] == "pending":
                        print("pending in queue will wait more time")
                        time.sleep(30)
                    if it["state"] == "failed":
                        print("generate failed")
                        raise
                    if it['video']:
                        print(f"New video link: {it['video']['url']}")
                        video_url = it['video']['url']
                    break
            if video_url:
                break
            time.sleep(3)
            print("sleep 3")
        content = self.session.get(video_url)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        slug = self.generate_slug(video_url)
        video_path = f"{output_dir}/output_{slug}.mp4"

        with open(video_path, "wb") as f:
            f.write(content.content)
        print(f"Video saved to {video_path}")
        return video_path
    
    
def main():
    # Define external parameters directly in the main function
    cookie = "_clck=xclaca%7C2%7Cfms%7C0%7C1632; _ga=GA1.1.1737580940.1718854727; b-user-id=9ebb8c50-b402-544f-f078-869503859ed2; access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOnsidXNlcl91dWlkIjoiYWVhMGMzMWEtNTE4MC00YTQzLWI2MzItMGIwMmE5YjA1NjgwIiwiY2xpZW50X2lkIjoiIn0sImV4cCI6MTcxOTQ2NTE5N30.NwsWMfS1mN2LCfgIWpeVQWt7hkIjU9mH53j3kFiWEjw; refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOnsidXNlcl91dWlkIjoiYWVhMGMzMWEtNTE4MC00YTQzLWI2MzItMGIwMmE5YjA1NjgwIiwiY2xpZW50X2lkIjoiIn0sImV4cCI6MTcxOTQ2NTE5N30.NwsWMfS1mN2LCfgIWpeVQWt7hkIjU9mH53j3kFiWEjw; _clsk=v22o9g%7C1718864309077%7C14%7C0%7Cy.clarity.ms%2Fcollect; _ga_67JX7C10DX=GS1.1.1718860390.2.1.1718864351.0.0.0"
    image_file = "test_imgs/cat.png"
    output_dir = "./output"
    prompt = "A "
    # access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOnsidXNlcl91dWlkIjoiYWVhMGMzMWEtNTE4MC00YTQzLWI2MzItMGIwMmE5YjA1NjgwIiwiY2xpZW50X2lkIjoiIn0sImV4cCI6MTcxOTQ2NTE5N30.NwsWMfS1mN2LCfgIWpeVQWt7hkIjU9mH53j3kFiWEjw"
    proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
    }
    # Create video generator
    video_generator = VideoGen(
        cookie,
        image_file=image_file,
        proxies=proxies
    )
    print(f"Left {video_generator.get_limit_left()} times.")
    video_generator.save_video(
        prompt=prompt,
        output_dir=output_dir,
    )

if __name__ == "__main__":
    main()