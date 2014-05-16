import cv2
from PIL import Image
import json, glob
import os
import getpass
integer_id = 0
MAX_W = 2048
MAX_H = 2048
uname = getpass.getuser()
# Put your favorite photos here
ROOTPATH = '/Users/' + uname + '/ImageFolderSync'
# this where the photos are put temporarily for upload to gplus
SYNCPATH = '/Users/'+ uname + '/plusPhotos/'

if not os.path.exists(ROOTPATH):
    os.system('mkdir ' + ROOTPATH)
if not os.path.exists(SYNCPATH):
    os.system('mkdir ' + SYNCPATH)
#####################################################
class Tile(object):
    def __init__(self, src_photo, x,y,h,w):
        self.src_photo = src_photo
        self.x = x
        self.y = y
        self.h = h
        self.w = w
    @property
    def tile_id(self):
        return hash((self.src_photo.iid, self.x, self.y, self.h, self.w))
    def _create_tile_image(self):
        x,y,h,w = self.x, self.y, self.h, self.w
        return self.src_photo.img[y:y+h, x:x+w]
    ############
    def post(self):
        tilepath = SYNCPATH + self.src_photo.name + str(self.src_photo.iid) + '__' + str(self.tile_id) + '.jpg'
        tile_img = self._create_tile_image()
        cv2.imwrite(tilepath, tile_img)
    ####################
    def as_dict(self):
        return {
                'x':self.x,
                'y':self.y,
                'w':self.w,
                'h':self.h
                }
    ##########################################
class Photo(object):
    def __init__(self, imagepath, h,w, iid):
        self.imagepath = imagepath
        self.name = os.path.basename(imagepath)
        self.h = h
        self.w = w
        self.iid = iid
        self.tiling()
    ####################
    @classmethod
    def from_filepath(cls, imagepath):
        img = Image.open(imagepath)
        w, h = img.size
        global integer_id
        iid = integer_id
        integer_id +=1
        return cls(imagepath, h, w,iid)
    @classmethod
    def from_json(cls, args_dict):
        return cls(**args_dict)
    ###########
    def as_dict(self):
        return {'imagepath': self.imagepath,
                'h': self.h,
                'w': self.w,
                'id': self.iid,
                'tiles': [t.as_dict() for t in self.tiles]
                }
    ###############################
    def tiling(self):
        global MAX_H, MAX_W
        self.tiles = []
        if self.h <= MAX_H and self.w < MAX_W:
            hsegs = [(0,self.h)]
            wsegs = [(0, self.w)]
        else:
            # compute the intervals of horizontal division
            # no interval is greater than MAX_W
            num_wsegs = self.w / MAX_W
            wsegs = [(MAX_W*(k), MAX_W*(k+1)) for k in range(num_wsegs)]
            wsegs.append((MAX_W*num_wsegs, self.w))
            # compute the intervals of vertical division
            num_hsegs = self.h / MAX_H
            hsegs = [(MAX_H*(k), MAX_H*(k+1)) for k in range(num_hsegs)]
            hsegs.append((MAX_H*num_hsegs, self.h))
            ####
        # create the tiling by picking every vertical division
        # against every horizontal division
        for wt in wsegs:
            for ht in hsegs:
                self.tiles.append(Tile(self, 
                                     wt[0], ht[0], 
                                     ht[1] - ht[0],
                                     wt[1] - wt[0]))
    ################################################
    def post(self):
        self.img = cv2.imread(self.imagepath)
        for t in self.tiles:
            t.post()
        self.img = []
####################################################
def global_init():
    state = {}
    json.dump({'integer_id': integer_id}, open(ROOTPATH + '/.settings', 'w'))
    return state
########################################################
def global_finalize(state, photos):
    for p in photos:
        p.post()
    photodict = [p.as_dict() for p in photos]
    json.dump({'integer_id':integer_id,
                'photos': photodict}, open(ROOTPATH + '/.settings', 'w'))
#########################################################
os.system('rm '+ ROOTPATH + '/.settings')
os.system('rm '+ SYNCPATH + '*')
try:
    state = json.load(open(ROOTPATH + '/.settings'))
    integer_id = state['integer_id']
    photos = state['photos']
except IOError:
    state = global_init()
######
photos = []
jpg_files = glob.glob(ROOTPATH + '/*.jpg')
for jf in jpg_files:
    photos.append(Photo.from_filepath(jf))
###################################
global_finalize(state, photos)