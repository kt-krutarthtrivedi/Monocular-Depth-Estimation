import glob

import cv2
import numpy as np
import os

main_dir = "/media/karterk/HDD/Classes/CS541/cityscapes/"
left = "leftImg8bit"
right = "rightImg8bit"
semantic = "gtFine"
semantic_subname = "gtFine_labelIds"

subfolders = ['train', 'val', 'test']

for subfolder in subfolders:
    left_imgs_set = set(glob.glob(os.path.join(main_dir, left, "{}/**/*.png".format(subfolder)), recursive=True))
    right_imgs_set = set(glob.glob(os.path.join(main_dir, right, "{}/**/*.png".format(subfolder)), recursive=True))
    semantic_imgs_set = set(
        glob.glob(os.path.join(main_dir, semantic, "{}/**/*.png".format(subfolder)), recursive=True))

    output_file = "cityscapes_fine_{}.txt".format(subfolder)

    f = open(output_file, 'w')

    i = 0
    for left_p in left_imgs_set:
        base_path = "/".join(left_p.split("/")[:-2])
        right_p = left_p.replace(left, right)
        semantic_p = left_p.replace(left, semantic, 1).replace(left, semantic_subname)
        try:
            a = cv2.imread(os.path.join(base_path, left_p))
            b = cv2.imread(os.path.join(base_path, right_p))
            if a.shape[2] < 3 or b.shape[2] < 3:
                print("bad")
                continue
        except:
            print("bad")
            continue
        # print("g", end='')
        if right_p in right_imgs_set and semantic_p in semantic_imgs_set:
            # print(left_p, right_p, semantic_p)
            f.write("{} {} {}\n".format(left_p.replace(main_dir, ""),
                                        right_p.replace(main_dir, ""),
                                        semantic_p.replace(main_dir, "")))
            i += 1

    print("Added {} names for {}".format(i, subfolder))
    f.close()
