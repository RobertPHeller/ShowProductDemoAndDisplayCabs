#*****************************************************************************
#
#  System        : 
#  Module        : 
#  Object Name   : $RCSfile$
#  Revision      : $Revision$
#  Date          : $Date$
#  Author        : $Author$
#  Created By    : Robert Heller
#  Created       : Wed Jun 28 09:05:55 2023
#  Last Modified : <230629.0911>
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

class SingleGangUtilityBox(object):
    Width=2.125*25.4
    Height=4*25.4
    Depth=1.875*25.4
    Color=(.75,.75,.75)
    def __init__(self,name,origin,orientation='H'):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
        self.origin = origin
        if orientation=='H':
            w=self.Height
            l=self.Width
        elif orientation=='V':
            w=self.Width
            l=self.Height
        else:
            raise RuntimeError("Unsupport orientation")
        self.box = Part.makePlane(l,w,origin,Base.Vector(0,1,0))\
                .extrude(Base.Vector(0,-self.Depth,0))
    def show(self,doc=None):
        if doc==None:
            doc = App.activeDocument()
        obj = doc.addObject("Part::Feature",self.name)
        obj.Shape = self.box
        obj.Label = self.name
        obj.ViewObject.ShapeColor=self.Color

class SingleGangUtilityOutletCover(object):
    Width=2.125*25.4
    Height=4.*25.4
    Depth=.25*25.4
    Color=(.75,.75,.75)
    __OutletPoly__=[(-.375*25.4,0),(.375*25.4,0),(.625*25.4,.5625*25.4),\
                    (.375*25.4,1.125*25.4),(-.375*25.4,1.125*25.4),\
                    (-.625*25.4,.5625*25.4),(-.375*25.4,0)]
    __LowerOffset__=.67*25.4
    __UpperOffset__=2.08*25.4
    def __init__(self,name,origin,orientation='H'):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
        self.origin = origin
        if orientation=='H':
            w=self.Height
            l=self.Width
        elif orientation=='V':
            w=self.Width
            l=self.Height
        else:
            raise RuntimeError("Unsupport orientation")
        self.cover=Part.makePlane(l,w,origin,Base.Vector(0,1,0))\
                    .extrude(Base.Vector(0,-self.Depth,0))
        self.cover=self.cover.cut(self.__Outlet__(orientation,self.__LowerOffset__))
        self.cover=self.cover.cut(self.__Outlet__(orientation,self.__UpperOffset__))
    def __Outlet__(self,orientation,offset):
        polypoints = list()
        for tup in self.__OutletPoly__:
            if orientation=='H':
                z,x = tup
                polypoints.append(self.origin.add(Base.Vector(x+offset,\
                                                            0,\
                                                            z+(self.Width/2.0))))
            elif orientation=='V':
                x,z = tup
                polypoints.append(self.origin.add(Base.Vector(x+(self.Width/2.0),\
                                                            0,\
                                                            z+offset)))
        
            #lastindex = len(polypoints)-1
            #lastpoint = polypoints[lastindex]
            #sys.__stderr__.write("*** SingleGangUtilityOutletCover.__Outlet__(): point is (%f,%f,%f)\n"%(\
            #            lastpoint.x,\
            #            lastpoint.y,\
            #            lastpoint.z))
        return Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                .extrude(Base.Vector(0,-self.Depth,0))
    def show(self,doc=None):
        if doc==None:
            doc = App.activeDocument()
        obj = doc.addObject("Part::Feature",self.name)
        obj.Shape = self.cover
        obj.Label = self.name
        obj.ViewObject.ShapeColor=self.Color

if __name__ == '__main__':
    doc = App.newDocument('test')
    box=SingleGangUtilityBox('horizontalBox',Base.Vector(0,0,0))
    box.show(doc)
    cover = SingleGangUtilityOutletCover('outletCover',Base.Vector(0,box.Depth,0))
    cover.show(doc)
    App.ActiveDocument=doc
    Gui.ActiveDocument=doc
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewFront()
