#*****************************************************************************
#
#  System        : 
#  Module        : 
#  Object Name   : $RCSfile$
#  Revision      : $Revision$
#  Date          : $Date$
#  Author        : $Author$
#  Created By    : Robert Heller
#  Created       : Tue Jun 27 14:09:33 2023
#  Last Modified : <230627.1455>
#
#  Description	
#
#  Notes
#
#  History
#	
#*****************************************************************************
#
#    Copyright (C) 2023  Robert Heller D/B/A Deepwoods Software
#			51 Locke Hill Road
#			Wendell, MA 01379-9728
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# 
#
#*****************************************************************************


import Part
from FreeCAD import Base
import FreeCAD as App

from abc import ABCMeta, abstractmethod, abstractproperty  

import os
import sys
sys.path.append(os.path.dirname(__file__))

class COBLEDStripBase(object):
    __metaclass__ = ABCMeta
    @abstractproperty
    def Length(self):
        pass
    @property
    def Width(self):
        return 8/25.4
    @property
    def Thick(self):
        return 1.8/25.4
    @property
    def SectionLength(self):
        return 50/25.4
    @property
    def Color(self):
        return (255/255.0,255/255.0,224/255.0)
    def __init__(self,name,origin,orientation='H'):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
        self.origin = origin
        if orientation=='H':
            Norm=Base.Vector(0,0,-1)
            Extrude=Base.Vector(0,0,-self.Thick)
        elif orientation=='VL':
            Norm=Base.Vector(1,0,0)
            Extrude=Base.Vector(self.Thick,0,0)
        elif orientation=='VR':
            Norm=Base.Vector(-1,0,0)
            Extrude=Base.Vector(-self.Thick,0,0)
        else:
            raise RuntimeError("Unsupport orientation")
        self.strip = Part.makePlane(self.Length,self.Width,origin,Norm)\
                        .extrude(Extrude)
    def show(self,doc=None):
        if doc==None:
            doc = App.activeDocument()
        obj = doc.addObject("Part::Feature",self.name)
        obj.Shape = self.strip
        obj.Label = self.name
        obj.ViewObject.ShapeColor=self.Color

class COBLEDStripYard(COBLEDStripBase):
    @property
    def Length(self):
        return 17*self.SectionLength

if __name__ == '__main__':
    doc = App.newDocument('test')
    strip = COBLEDStripYard('teststrip',Base.Vector(0,0,0))
    strip.show(doc)
    App.ActiveDocument=doc
    Gui.ActiveDocument=doc
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewIsometric()
    

