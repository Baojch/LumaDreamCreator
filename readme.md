# Dream Machine API
Fork from https://github.com/danaigc/DreamMachineAPI
About High quality video generation by lumalabs.ai. Reverse engineered API.

![image](./a.png)


https://github.com/yihong0618/LumaDreamCreator/assets/15976103/a55ee848-ab50-4769-8014-76ace41e330b


## How to
- Login https://lumalabs.ai/ and generate video.
- Use `Chrome` or other browsers to inspect the network requests (F12 -> XHR).
- Clone this REPO -> `git clone https://github.com/yihong0618/LumaDreamCreator.git`
- Copy the cookie.
 Export LUMA_COOKIE='xxxxx'.

## Usage

```
python -m luma --prompt 'make this picture alive' -I a.png
```

or
```
pip install -U luma-creator 
```

```python
from luma import VideoGen
i = VideoGen('cookie', 'image_url' ) # Replace 'cookie', image_url with your own
print(i.get_limit_left())
i.save_video("a blue cyber dream", './output')
```

## Usage for several images and prompts
```python
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
```
- modify your ```cookie``` from F12 -> Network -> Fetch/XHR -> usage(Request Headers)
- add image_files' addresses and prompts
- modify your proxy

## Thanks

- [DreamMachineAPI](https://github.com/danaigc/DreamMachineAPI)
