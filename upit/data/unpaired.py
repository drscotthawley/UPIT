# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_data.unpaired.ipynb (unless otherwise specified).

__all__ = ['RandPair', 'TensorImage_', 'ToTensor_', 'CustomNormalize', 'get_dls']

# Cell
from fastai.vision.all import *
from fastai.basics import *
from typing import List
from fastai.vision.gan import *

# Cell
class RandPair(Transform):
    "Returns a random image from domain B, resulting in a random pair of images from domain A and B."
    def __init__(self,itemsB): self.itemsB = itemsB
    def encodes(self,i): return random.choice(self.itemsB)

# Cell
class TensorImage_(TensorImage): pass

# Cell
class ToTensor_(Transform):
    "Convert item to appropriate tensor class"
    order = 5
    def encodes(self, o:PILImage): return TensorImage_(image2tensor(o))

# Cell
class CustomNormalize(DisplayedTransform):
    "Normalize/denorm batch"
    parameters,order = L('mean', 'std', 'mean_', 'std_'),99
    def __init__(self, mean, std, mean_, std_, axes=(0,2,3)): store_attr()

    def encodes(self, x:TensorImage):
        return (x-self.mean) / self.std

    def decodes(self, x:TensorImage):
        f = to_cpu if x.device.type=='cpu' else noop
        return (x*f(self.std) + f(self.mean))

    def encodes(self, x:TensorImage_):
        return (x-self.mean_) / self.std_

    def decodes(self, x:TensorImage_):
        f = to_cpu if x.device.type=='cpu' else noop
        return (x*f(self.std_) + f(self.mean_))
    _docs=dict(encodes="Normalize batch", decodes="Denormalize batch")

# Cell
def get_dls(pathA, pathB, num_A=None, num_B=None, load_size=512, crop_size=256, item_tfms=None, batch_tfms=None, bs=4, num_workers=2, normalize=False):
    """
    Given image files from two domains (`pathA`, `pathB`), create `DataLoaders` object.
    Loading and randomly cropped sizes of `load_size` and `crop_size` are set to defaults of 512 and 256.
    Batch size is specified by `bs` (default=4).
    """
    filesA = get_image_files(pathA)
    filesB = get_image_files(pathB)
    filesA = filesA[:min(ifnone(num_A, len(filesA)),len(filesA))]
    filesB = filesB[:min(ifnone(num_B, len(filesB)),len(filesB))]

    if item_tfms is None: item_tfms = [Resize(load_size), RandomCrop(crop_size)]

    dsets = Datasets(filesA, tfms=[[PILImage.create, ToTensor, *item_tfms],
                                   [RandPair(filesB),PILImage.create, ToTensor_, *item_tfms]], splits=None)

    _batch_tfms = [IntToFloatTensor]
    if batch_tfms is None:
        if normalize == True:
            x = IntToFloatTensor()(torch.cat([torch.unsqueeze(i[0],0) for i in dsets]))
            mean,std = x.mean((0,2,3), keepdim=True),x.std((0,2,3), keepdim=True)+1e-7
            x_ = IntToFloatTensor()(torch.cat([torch.unsqueeze(i[1],0) for i in dsets]))
            mean_,std_ = x.mean((0,2,3), keepdim=True),x.std((0,2,3), keepdim=True)+1e-7
            normalize_tfm = CustomNormalize(mean,std,mean_,std_)

        else: normalize_tfm = Normalize.from_stats(mean=0.5, std=0.5)

        batch_tfms = [normalize_tfm, FlipItem(p=0.5)]

    _batch_tfms = _batch_tfms + batch_tfms

    dls = dsets.dataloaders(bs=bs, num_workers=num_workers, after_batch=_batch_tfms)

    return dls