from __future__ import print_function
import os
import warnings
warnings.filterwarnings('ignore')
import torch
import pickle
import argparse
# import numpy as np
from m2det import build_net
from utils.timer import Timer
# import torch.backends.cudnn as cudnn
from layers.functions import Detect, PriorBox
from data.data_augment import BaseTransform
from configs.CC import Config
import cv2
from tqdm import tqdm
# import sys
from utils.core import *

parser = argparse.ArgumentParser(description='M2Det Testing')
parser.add_argument('-c', '--config', default='configs/m2det512_vgg.py', type=str)
parser.add_argument('-d', '--dataset', default='COCO', help='VOC or COCO version')
parser.add_argument('-m', '--trained_model', default='weights/m2det512_vgg.pth', type=str, help='Trained state_dict file path to open')
parser.add_argument('--test', action='store_true', help='to submit a test file')
args = parser.parse_args()

print('----------------------------------------------------------------------\n'
      '|                       M2Det Evaluation Program                     |\n'
      '----------------------------------------------------------------------', ['yellow', 'bold'])
global cfg
cfg = Config.fromfile(args.config)
if not os.path.exists(cfg.test_cfg.save_folder):
    os.mkdir(cfg.test_cfg.save_folder)
anchor_config = anchors(cfg)
print('The Anchor info: \n{}'.format(anchor_config))
priorbox = PriorBox(anchor_config)
with torch.no_grad():
    priors = priorbox.forward()
    if cfg.test_cfg.cuda:
        priors = priors.cuda()


def test_net(save_folder, net, detector, cuda, testset, transform, max_per_image=300, thresh=0.005):
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)

    num_images = len(testset)
    print('=> Total {} images to test.'.format(num_images), ['yellow', 'bold'])
    num_classes = cfg.model.m2det_config.num_classes
    all_boxes = [[[] for _ in range(num_images)] for _ in range(num_classes)]

    _t = {'im_detect': Timer(), 'misc': Timer()}
    det_file = os.path.join(save_folder, 'detections.pkl')
    tot_detect_time, tot_nms_time = 0, 0
    print('Begin to evaluate', ['yellow', 'bold'])
    for i in tqdm(range(num_images)):
        img = testset.pull_image(i)
        # step1: CNN detection
        _t['im_detect'].tic()
        boxes, scores = image_forward(img, net, cuda, priors, detector, transform)
        detect_time = _t['im_detect'].toc()
        # step2: Post-process: NMS
        _t['misc'].tic()
        nms_process(num_classes, i, scores, boxes, cfg, thresh, all_boxes, max_per_image)
        nms_time = _t['misc'].toc()

        tot_detect_time += detect_time if i > 0 else 0
        tot_nms_time += nms_time if i > 0 else 0

    with open(det_file, 'wb') as f:
        pickle.dump(all_boxes, f, pickle.HIGHEST_PROTOCOL)
    print('===> Evaluating detections', ['yellow', 'bold'])
    testset.evaluate_detections(all_boxes, save_folder)
    print('Detect time per image: {:.3f}s'.format(tot_detect_time / (num_images - 1)))
    print('Nms time per image: {:.3f}s'.format(tot_nms_time / (num_images - 1)))
    print('Total time per image: {:.3f}s'.format((tot_detect_time + tot_nms_time) / (num_images - 1)))
    print('FPS: {:.3f} fps'.format((num_images - 1) / (tot_detect_time + tot_nms_time)))


if __name__ == '__main__':
    net = build_net('test',
                    size=cfg.model.input_size,
                    config=cfg.model.m2det_config)
    init_net(net, cfg, args.trained_model)
    print('===> Finished constructing and loading model', ['yellow', 'bold'])
    net.eval()
    _set = 'eval_sets' if not args.test else 'test_sets'
    # testset = get_dataloader(cfg, args.dataset, _set)
    # if cfg.test_cfg.cuda:
    #     net = net.cuda()
    #     cudnn.benchmark = True
    # else:
    #     net = net.cpu()
    net = net.cpu()
    detector = Detect(cfg.model.m2det_config.num_classes, cfg.loss.bkg_label, anchor_config)
    save_folder = os.path.join(cfg.test_cfg.save_folder, args.dataset)
    _preprocess = BaseTransform(cfg.model.input_size, cfg.model.rgb_means, (2, 0, 1))

    # input_img_path = "E:/tool/Git/region_check_person/base_root/region_check_person/pic_back/9_2019-08-08_11-43-12.jpg"
    input_img_dir = "E:/tool/Git/region_check_person/base_root/region_check_person/pic_back/"
    for filename in os.listdir(input_img_dir):
        if filename.endswith("jpg"):
            input_img_path = os.path.join(input_img_dir, filename)
            img_bgr = cv2.imread(input_img_path)
            # img = img_bgr[..., ::-1]
            img = img_bgr
            boxes, scores = image_forward(img, net, cuda=False, priors=priors, detector=detector, transform=_preprocess)

            num_classes = cfg.model.m2det_config.num_classes
            all_boxes = [[[] for _ in range(1)] for _ in range(num_classes)]
            nms_process(num_classes, 0, scores, boxes, cfg, min_thresh=0.2, all_boxes=all_boxes, max_per_image=300)
            print(all_boxes[1])
            for box in all_boxes[1]:
                # print(box)
                for item in box:
                    print(item)
                    cv2.rectangle(img_bgr, ((int)(item[0]), (int)(item[1])), ((int)(item[2]), (int)(item[3])), (0, 0, 255), 3)

            output_img_path = "E:/tool/Git/region_check_person/base_root/region_check_person/pic_back/test_draw_face/" + filename
            cv2.imwrite(output_img_path, img_bgr)
