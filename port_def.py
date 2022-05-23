class PortRTL():
    def __init__(self, name, objectRTL, type, iop, dir, bit, attr):
        self.name = name
        self.object = objectRTL
        self.type = type
        self.iop = iop
        self.direction = dir
        self.bitwidth = bit
        self.attribution = attr
    def __str__(self):
        return "name = {} object = {} type = {} iop = {} direction = {} bitwidth = {} attribution = {}".format(self.name, self.object,self.type, self.iop, self.direction, self.bitwidth, self.attribution)
        
class PortC():
    def __init__(self, name, type, is_array = 0, array_length = 0):
        self.name = name
        self.type = type
        self.is_array = is_array
        self.array_length = array_length
    def __str__(self):
        return "name = {} type = {} is_array = {} array_length = {}".format(self.name, self.type, self.is_array, self.array_length)
        
               