from PIL import Image
import argparse
import os
from pathlib import Path
import pdb
import json

parser = argparse.ArgumentParser(description='Builds asset packs for dungeondraft')
parser.add_argument('assets', metavar='-a', type=str, help='Folder location of assets')
parser.add_argument('output', metavar='-o', type=str, help='Output folder location, if does not exist, will create')
parser.add_argument('type', metavar='-t', type=str, default='assets',choices=['assets', 'tileset', 'texture'], help='Type of output desired')
parser.add_argument('-q', '--quality', type=int, default=85, help='Quality of output images (%) 0 = nil quality, 100 = no compression')
parser.add_argument('-r', '--rotation', type=bool, default=True, help='Rotation for textures')
parser.add_argument('-v', '--vertical', type=bool, default=True, help='Vertical flip for textures')
parser.add_argument('-h', '--horizontal', type=bool, default=True, help='Horisontal flip for textures')

def build_tileset_sub_images(im, resize=(256, 256), rot=True, vert=True, hor=True):
    images = []
    base = im.resize(resize, Image.ANTIALIAS)
    for rot in [0, 90, 180, 270]:
        rotated = base.rotate(rot)
        images.append(rotated.transpose(Image.FLIP_LEFT_RIGHT))
        images.append(rotated.transpose(Image.FLIP_TOP_BOTTOM))
        images.append(base)
        images.append(rotated.transpose(Image.TRANSVERSE))
    return images

def build_tileset_image(images, height=4, width=4):
    tileset = Image.new('RGB', (images[0].width*width, images[0].height*height))
    index = 0
    image_w = images[0].width
    image_h = images[0].height
    for ii in range(height):
        for jj in range(width):
            tileset.paste(images[index], (image_w*jj, image_h*ii))
            index += 1
    return tileset

accepted_types = ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.PNG']
def accepted_file(path, types=accepted_types):
    return path.suffix in types

def create_dd_template(folder):
    if not os.path.isdir(folder):
        os.mkdir(folder)
    template = ['data', 'data/walls', 'data/tilesets', 'textures', 'textures/objects', 'textures/tilesets', 'textures/tilesets/simple']
    for item in template:
        if not os.path.isdir(os.path.join(folder, item)):
            os.mkdir(os.path.join(folder, item))
    files = ['data/default.dungeondraft_tags']
    for item in files:
        if not os.path.isfile(os.path.join(folder, item)):
            with open(os.path.join(folder, item), 'w') as outfile:
                json.dump({"tags": {}, "sets": {}}, outfile)

def get_tagfile(folder):
    filename = os.path.join(folder, 'data/default.dungeondraft_tags')
    with open(filename) as infile:
        data = json.load(infile)
    return data

def write_tagfile(folder, data):
    filename = os.path.join(folder, 'data/default.dungeondraft_tags')
    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

def write_texturefile(folder, filename, data):
    filename = os.path.join(folder, 'data/tilesets', filename + '.dungeondraft.tileset')
    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

if __name__ == "__main__":
    args = parser.parse_args()
    base = args.output
    create_dd_template(base)
    asset_folder = os.path.join(base, 'textures/objects')
    tileset_folder = os.path.join(base, 'textures/tilesets/simple')
    working_folder = asset_folder if args.type == 'assets' else tileset_folder
    set_name = args.assets.strip('/\\.') if args.type == 'assets' else None
    tags = {}
    for path in Path(args.assets).rglob('*.*'):
        current_folder = os.path.join(working_folder, *path.parts[:-1])
        if not os.path.isdir(current_folder):
            os.mkdir(current_folder)
        if not accepted_file(path):
            continue
        if (args.type == 'tileset'):
            try:
                im = Image.open(path)
                images = build_tileset_sub_images(im)
                tile = build_tileset_image(images)
                filename = os.path.join(current_folder, path.parts[-1])
                tile.save(filename, optimize=True, quality=args.quality)
                write_texturefile(base, path.stem, {
                    "path": "textures/tilesets/simple/" + path.name,
                    "name": path.stem,
                    "type": "normal",
                    "color": "5b797a"
                })
            except Exception as e:
                print(e)
        elif (args.type == 'assets'):
            try:
                im = Image.open(path)
                filename = os.path.join(current_folder, path.parts[-1])
                im.save(filename, optimize=True, quality=args.quality)
            except Exception as e:
                print(e)
            for item in path.parts[:-1]:
                if item not in tags:
                    tags[item] = []
                tag_filename = '/'.join(['textures/objects', *path.parts])
                tags[item].append(tag_filename)


    
    if args.type == 'assets':
        # clean tags. Check if there's more than 1 tag. Delete base tag if so, and if there aren't any other assets in it
        delete = False
        for item in tags[set_name]:
            split = item.split('/')
            if len(split) > 3:
                delete = True
        if delete:
            del tags[set_name]
        tagfile = get_tagfile(base)
        tagfile['tags'].update(tags)
        tagfile['sets'].update({set_name: list(tags.keys())})
        write_tagfile(base, tagfile)
