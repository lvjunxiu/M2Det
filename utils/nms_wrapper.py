# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from nms.cpu_nms import cpu_soft_nms
# from nms.gpu_nms import gpu_nms

# def nms(dets, thresh, force_cpu=False):
#     """Dispatch to either CPU or GPU NMS implementations."""
#
#     if dets.shape[0] == 0:
#         return []
#     if cfg.USE_GPU_NMS and not force_cpu:
#         return gpu_nms(dets, thresh, device_id=cfg.GPU_ID)
#     else:
#         return cpu_nms(dets, thresh)


def nms_wr(dets, thresh, force_cpu=False):
    """Dispatch to either CPU or GPU NMS implementations."""

    if dets.shape[0] == 0:
        return []
    if force_cpu:
        return cpu_soft_nms(dets, thresh, method=1)
        # return cpu_nms(dets, thresh)
    # return gpu_nms(dets, thresh)
    return cpu_soft_nms(dets, thresh, method=1)
