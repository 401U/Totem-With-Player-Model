import requests
import base64
import shutil
import json
import sys
import os
import re


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
    print(f'从 mojang api 获取玩家 {name} 的 uuid 中...')
    response = requests.get("https://api.mojang.com/users/profiles/minecraft/" + name)
    if response.status_code != 200:
        raise RuntimeError('无法获取 uuid!')
    data = response.json()
    print(f'成功! 获取到的 uuid 为 {data["id"]}')
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
    print(f'获取 {uuid} 的皮肤地址中...')
    response = requests.get("https://sessionserver.mojang.com/session/minecraft/profile/"+uuid)
    if response.status_code != 200:
        raise RuntimeError("获取皮肤地址失败!")
    data = response.json()
    for item in data['properties']:
        if item['name'] != 'textures':
            continue
        print('完成!')
        return base64_decode(item['value'])
    raise RuntimeError("获取皮肤地址失败!")


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
    print('解码base64中...')
    url_data = json.loads(base64.b64decode(codes))
    url = url_data['textures']['SKIN']['url']
    print(f'解码完成! 解码后的皮肤地址为: {url}')
    return url


def save_img(name: str) -> str:
    uuid = get_uuid(name)
    url = get_skin_url(uuid)
    skin_data = requests.get(url)
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)
    file_path = os.path.join(IMG_DIR, name + '.png')
    with open(file_path, 'ab') as f:
        print('写入皮肤图片中 ...')
        f.write(skin_data.content)
    return file_path


def update_meta(name, template_dir=TEMPLATE_DIR):
    meta_file = os.path.join(template_dir, 'pack.mcmeta')
    print('加载元数据中...')
    meta = json.load(open(meta_file))
    print('修改元数据中...')
    meta['pack']['description'] = f'§e不死图腾手办 for §b{name}'
    with open(meta_file, 'w', encoding='utf-8') as f:
        print('保存变更后的元数据文件中...')
        f.write(json.dumps(meta, indent=4, ensure_ascii=False))


def pack(name: str, target_dir: str = RESOURCEPACK_DIR):
    target_image = os.path.join(TEMPLATE_DIR, 'assets', 'customtotem', 'textures', 'entity', 'playerskin.png')
    if os.path.exists(target_image):
        print('清理上次构建...')
        os.remove(target_image)
    prev_img = os.path.join(IMG_DIR, name + '.png')
    shutil.copy(prev_img, target_image)
    update_meta(name, TEMPLATE_DIR)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    resourcepack = os.path.join(target_dir, f'Totem_for_{name}')
    print('打包中...')
    shutil.make_archive(resourcepack, 'zip', TEMPLATE_DIR)
    print('完成!')


def full_generate(name: str):
    name = name.strip()
    name_pattern = re.compile(r'^(\d|[a-zA-Z])(\d|[a-zA-Z]|_){3,15}$')
    if re.fullmatch(name_pattern, name):
        save_img(name)
        pack(name)
    else:
        print(f'不合法的昵称: {name}')


def full_generate_list(file):
    if not os.path.exists(file):
        raise RuntimeError('给定的文件不存在!')
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            name = line.strip().replace('\n', '')
            full_generate(name)


if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1:
        if args[1] == '-f' and len(args) >= 2:
            full_generate_list(file=args[2])
        exit()

    print('')
    print('请输入玩家的昵称:')
    username = input()
    full_generate(username)
    print('Bye!')
