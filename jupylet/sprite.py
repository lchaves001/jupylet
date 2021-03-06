"""
    jupylet/sprite.py
    
    Copyright (c) 2020, Nir Aides - nir@winpdb.org

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
       list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import pyglet
import math

import PIL.Image

import numpy as np

from .collision import trbl, hitmap_and_outline_from_alpha, compute_collisions
from .resource import image_from, pil_open
from .state import State


_empty_array = np.array([])


class Sprite(pyglet.sprite.Sprite):
    
    def __init__(self,
                 img, x=0, y=0,
                 blend_src=pyglet.gl.GL_SRC_ALPHA,
                 blend_dest=pyglet.gl.GL_ONE_MINUS_SRC_ALPHA,
                 batch=None,
                 group=None,
                 usage='dynamic',
                 subpixel=True,
                 autocrop=False,
                 width=None,
                 height=None,
                 anchor_x='center',
                 anchor_y='center',
                 scale=1.0):

        self.autocrop = autocrop
        
        if type(img) is str:
            im = pil_open(img, self.autocrop)
            self.hitmap, self.outline = hitmap_and_outline_from_alpha(im)
        else:
            self.hitmap = None
            self.outline = None

        img = image_from(img, autocrop=self.autocrop)
            
        super(Sprite, self).__init__(img, x, y,
                 blend_src,
                 blend_dest,
                 batch,
                 group,
                 usage,
                 subpixel)

        self.scale = scale

        if width:
            self.width = width

        elif height:
            self.height = height

        self.anchor_x = anchor_x
        self.anchor_y = anchor_y        

        self._update_position()

    @property
    def image(self):
        return pyglet.sprite.Sprite.image.fget(self)
    
    @image.setter
    def image(self, img):
        
        width = self.width
        height = self.height

        anchor_x = self.anchor_x / self.width
        anchor_y = self.anchor_y / self.height

        if type(img) is str:
            im = pil_open(img, self.autocrop)
            self.hitmap, self.outline = hitmap_and_outline_from_alpha(im)
        else:
            self.hitmap = None
            self.outline = None

        img = image_from(img, autocrop=self.autocrop)
            
        pyglet.sprite.Sprite.image.fset(self, img)

        if width != self.width and height != self.height:
            self.width = width 

        self.anchor_x = anchor_x
        self.anchor_y = anchor_y

        self._update_position()

    def collisions_with(self, o, debug=False):
        
        #if self.distance_to(o) > self.radius + o.radius:
        #    return

        x0, y0 = self.x, self.y
        x1, y1 = o.x, o.y

        t0, r0, b0, l0 = self._trbl()
        t1, r1, b1, l1 = o._trbl()

        if t0 + y0 < b1 + y1 or t1 + y1 < b0 + y0:
            return _empty_array[:0]

        if r0 + x0 < l1 + x1 or r1 + x1 < l0 + x0:
            return _empty_array[:0]
        
        return compute_collisions(o, self, debug=debug)

    def distance_to(self, o, pos=None):

        x, y = pos or (o.x, o.y)
        
        dx = x - self.x
        dy = y - self.y

        return (dx ** 2 + dy ** 2) ** 0.5
    
    def angle_to(self, o, pos=None):
        
        qd = {
            (True, True): 0,
            (True, False): 180,
            (False, False): 180,
            (False, True): 360,
        }
        
        x, y = pos or (o.x, o.y)
        
        dx = x - self.x
        dy = y - self.y

        a0 = math.atan(dy / (dx or 1e-7)) / math.pi * 180 + qd[(dy >= 0, dx >= 0)]

        return -a0

    @property
    def anchor_x(self):
        """Scaled anchor_x of the sprite."""
        return self._texture.anchor_x / self._texture.width * self.width

    @anchor_x.setter
    def anchor_x(self, anchor):

        if anchor == 'left':
            anchor = 0
        elif anchor == 'center':
            anchor = 0.5
        elif anchor == 'right':
            anchor = 1.
        elif type(anchor) in (int, float) and not -1 <= anchor <= 1:
            anchor = anchor / self.width

        self._texture.anchor_x = anchor * self._texture.width

    @property
    def anchor_y(self):
        """Scaled anchor_y of the sprite."""
        return self._texture.anchor_y / self._texture.height * self.height
        
    @anchor_y.setter
    def anchor_y(self, anchor):

        if anchor == 'bottom':
            anchor = 0
        elif anchor == 'center':
            anchor = 0.5
        elif anchor == 'top':
            anchor = 1.
        elif type(anchor) in (int, float) and not -1 <= anchor <= 1:
            anchor = anchor / self.height

        self._texture.anchor_y = anchor * self._texture.height

    @property
    def width(self):
        return pyglet.sprite.Sprite.width.fget(self)

    @width.setter
    def width(self, width):
        self.scale = self.scale * width / self.width

    @property
    def height(self):
        return pyglet.sprite.Sprite.height.fget(self)

    @height.setter
    def height(self, height):
        self.scale = self.scale * height / self.height

    @property
    def top(self):
        t, r, b, l = self._trbl()
        return self._y + t
        
    @property
    def right(self):
        t, r, b, l = self._trbl()
        return self._x + r
        
    @property
    def bottom(self):
        t, r, b, l = self._trbl()
        return self._y + b
        
    @property
    def left(self):
        t, r, b, l = self._trbl()
        return self._x + l
        
    @property
    def radius(self):
        t, r, b, l = self._trbl()
        rs = max(t, b) ** 2 + max(r, l) ** 2
        return rs ** .5
        
    def _trbl(self):
        tx = self._texture
        return trbl(
            tx.width, 
            tx.height, 
            tx.anchor_x, 
            tx.anchor_y, 
            self._rotation,
            self._scale
        )

    def wrap_position(self, width, height, margin=50):
        self.x = (self.x + margin) % (width + 2 * margin) - margin
        self.y = (self.y + margin) % (height + 2 * margin) - margin

    def clip_position(self, width, height, margin=0):
        self.x = max(-margin, min(margin + width, self.x))
        self.y = max(-margin, min(margin + height, self.y))

    def show(self):
        id0 = self._texture.get_image_data()
        id1 = id0.get_data('RGBA', pitch=-id0.width*4)
        im0 = PIL.Image.frombytes('RGBA', (id0.width, id0.height), id1)
        return im0

    def get_state(self):

        return State(
            x = self.x,
            y = self.y,
            scale = self.scale,
            opacity = self.opacity,
            rotation = self.rotation,
            anchor_x = self.anchor_x,
            anchor_y = self.anchor_y,
        )

    def set_state(self, s):
        
        self.x = s.x
        self.y = s.y
        self.scale = s.scale
        self.opacity = s.opacity
        self.rotation = s.rotation
        self.anchor_x = s.anchor_x
        self.anchor_y = s.anchor_y

        self._update_position()


def canvas2sprite(c):
    
    a = c.get_image_data()
    b = a.tostring()
    x = ctypes.string_at(id(b)+20, len(b))
    d = pyglet.image.ImageData(a.shape[1], a.shape[0], 'RGBA', x)
    s = Sprite(d)
    
    return s

