import requests
import base64
import shutil
import json
import os


IMG_DIR = os.path.join('target', 'image', '')
RESOURCEPACK_DIR = os.path.join('target', 'resourcepack', '')
TEMPLATE_DIR = 'template'


def get_uuid(name: str) -> str:
    # GET https://api.mojang.com/users/profiles/minecraft/<username>
    # return
    # {
    #     "name": "401Unauthorized",
    #     "id": "0c3d72f4eab54223bfe226cd8af4bd56"
    # }
    print(f'Try to get the uuid of {name} from mojang...')
    response = requests.get("https://api.mojang.com/users/profiles/minecraft/" + name)
    data = response.json()
    print(f'Done! The uuid is {data["id"]}')
    return data['id']


def get_skin_url(uuid: str) -> str:
    # GET https://sessionserver.mojang.com/session/minecraft/profile/<UUID>
    # return:
    # {
    #   "id": "0c3d72f4eab54223bfe226cd8af4bd56",
    #   "name": "401Unauthorized",
    #   "properties": [
    #     {
    #       "name": "textures",
    #       "value": <base64 string>
    #     }
    #   ]
    # }
    print(f'Try to get the skin url of {uuid} from mojang...')
    response = requests.get("https://sessionserver.mojang.com/session/minecraft/profile/"+uuid)
    data = response.json()
    for item in data['properties']:
        if item['name'] != 'textures':
            continue
        print('Done!')
        return base64_decode(item['value'])
    raise RuntimeError("Couldn't get the skin url!")


def base64_decode(codes: str) -> str:
    # {
    #   "timestamp" : 1628239397975,
    #   "profileId" : "0c3d72f4eab54223bfe226cd8af4bd56",
    #   "profileName" : "401Unauthorized",
    #   "textures" : {
    #     "SKIN" : {
    #       "url" :
    #       "http://textures.minecraft.net/texture/853922da5b603f2f73edce2a991635620159206c45a0819fa9f7b4b23101639c"
    #     }
    #   }
    # }
    print('Conventing base64 string into plain text...')
    url_data = json.loads(base64.b64decode(codes))
    url = url_data['textures']['SKIN']['url']
    print(f'Done! The Convented URL is {url}')
    return url


def save_img(name: str) -> str:
    uuid = get_uuid(name)
    url = get_skin_url(uuid)
    skin_data = requests.get(url)
    if not os.path.exists(IMG_DIR):
        print('Clearing previous file...')
        os.makedirs(IMG_DIR)
    file_path = os.path.join(IMG_DIR, name + '.png')
    with open(file_path, 'ab') as f:
        print('Writing skin image ...')
        f.write(skin_data.content)
    return file_path


def update_meta(name, template_dir=TEMPLATE_DIR):
    meta_file = os.path.join(template_dir, 'pack.mcmeta')
    print('Loading meta file ...')
    meta = json.load(open(meta_file))
    print('Modifying meta file ...')
    meta['pack']['description'] = f'§e不死图腾手办 for §b{name}\n§3让不死图腾变成{name}的手办'
    with open(meta_file, 'w') as f:
        print('Saving meta file changes ...')
        f.write(json.dumps(meta))


def pack(name: str, target_dir: str = RESOURCEPACK_DIR):
    target_image = os.path.join(TEMPLATE_DIR, 'assets', 'customtotem', 'textures', 'entity', 'playerskin.png')
    if os.path.exists(target_image):
        print('Clearing previous build cache ...')
        os.remove(target_image)
    prev_img = os.path.join(IMG_DIR, name + '.png')
    print('Copy the image into build dir ...')
    shutil.copy(prev_img, target_image)
    print('Updating meta file ...')
    update_meta(name, TEMPLATE_DIR)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    resourcepack = os.path.join(target_dir, f'totem_model_for_{name}')
    print('Zipping ...')
    shutil.make_archive(resourcepack, 'zip', TEMPLATE_DIR)
    print('ALL DONE!')


def full_generate(name: str):
    save_img(name)
    pack(name)


if __name__ == '__main__':
    print('Please input the username:')
    username = input()
    full_generate(username)
    print('Bye!')
