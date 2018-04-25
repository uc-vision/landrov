# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
###############################################
##      Open CV and Numpy integration        ##
###############################################
print('-1-')

import pyrealsense2 as rs
print('-2-')
import numpy as np
import cv2
import pickle,zmq

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
sx=1280//2
sy=720//2
fps=30
#dest_sink='tcpserversink host=0.0.0.0 port=8888'
config.enable_stream(rs.stream.depth, sx, sy, rs.format.z16, fps)
config.enable_stream(rs.stream.color, sx, sy, rs.format.bgr8, fps)

# Start streaming
cfg=pipeline.start(config)

profile_depth = cfg.get_stream(rs.stream.depth)
profile_rgb = cfg.get_stream(rs.stream.color)
intr_depth = profile_depth.as_video_stream_profile().get_intrinsics()
intr_rgb = profile_rgb.as_video_stream_profile().get_intrinsics()
print('intr_depth=',intr_depth)
print('intr_rgb=',intr_rgb)
print('extrinsics color2depth=',profile_rgb.get_extrinsics_to(profile_depth))
print('extrinsics depth2color=',profile_depth.get_extrinsics_to(profile_rgb))

align_to = rs.stream.color
align = rs.align(align_to)

cnt=0

port = "5557"
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)



try:
    while True:
        cnt+=1

        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        

        #depth_frame = frames.get_depth_frame()
        #color_frame = frames.get_color_frame()
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        

        #import ipdb;ipdb.set_trace()
        if not depth_frame or not color_frame:
            continue
        print(cnt,end='\r')

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        #depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        depth_8bit = cv2.convertScaleAbs(depth_image, alpha=0.03)

        # Stack both images horizontally
        #images = np.hstack((color_image, depth_colormap))

        encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),80]

        #socket.send(cv2.imencode('.jpg',images, encode_param)[1].tostring())
        socket.send_multipart([b'rgbimage',cv2.imencode('.jpg',color_image, encode_param)[1].tostring()])
        socket.send_multipart([b'depthimage',cv2.imencode('.jpg',depthimage, encode_param)[1].tostring()])
        


finally:

    # Stop streaming
    pipeline.stop()
