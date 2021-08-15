import cv2 
import os
from consts import hero_id_dict, radiant_hero_coords, dire_hero_coords

def is_in_hero_coords(MPx, MPy, compare_coord, width, height):
    found = 0
    if MPx >= compare_coord['x_lower'] and MPx+width <= compare_coord['x_upper']:
        if MPy >= compare_coord['y_lower'] and MPy+height <= compare_coord['y_upper']:
            found = 1
    return found

folders = [x[0].replace('hero_imgs\\', '') for x in os.walk('hero_imgs')]
folders.pop(0)
#print(folders)

# Read the images from the file
def find_heroes_in_match(img_path, team):
    data_points = []
    width, height = 64, 36
    #team = 'R'
    all_coords = {'r' : radiant_hero_coords, 'd' :dire_hero_coords}

    compare_coords = all_coords[team.lower()]

    large_image = cv2.imread(img_path)
    large_image = cv2.cvtColor(large_image, cv2.COLOR_BGR2GRAY)

    for folder in folders:
        hero_imgs = [x for x in os.listdir(f'hero_imgs/{folder}')]
        for hero_img in hero_imgs:
            found = 0
            small_image = cv2.imread(f'hero_imgs/{folder}/{hero_img}')
            #print(f"{folder}/{hero_img}")
            # grayscaling
            small_image = cv2.cvtColor(small_image, cv2.COLOR_BGR2GRAY)
            # resize image
            small_image = cv2.resize(small_image, (width, height), interpolation = cv2.INTER_AREA)

            method = cv2.TM_SQDIFF_NORMED

            result = cv2.matchTemplate(small_image, large_image, method)
            mn,_,mnLoc,_ = cv2.minMaxLoc(result)

            # Extract the coordinates of our best match
            MPx,MPy = mnLoc
            #print(folder, MPx,MPy)

            for compare_coord in compare_coords:
                if is_in_hero_coords(MPx, MPy, compare_coord, width, height):
                    found = 1
                    hero_slot = compare_coord['hero_slot']

                    data = {'hero_slot' : hero_slot, 'hero_name' : folder, 'hero_id':hero_id_dict[folder]}
                    data_points.append(data)
                    break

            if found:
                break
    return data_points