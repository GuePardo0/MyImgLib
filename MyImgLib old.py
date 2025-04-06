import zlib
import math
import matplotlib.colors as mcolors

class Image():
    def __init__(self, file_path):
        self.color_data=getColorData(file_path)

    def magicWand(self, selection_row=0, selection_collumn=0, tolerance=0.25, color="", bound=True):
        whole_selection=set()
        selection={(selection_row, selection_collumn)}
        border={(selection_row, selection_collumn)}
        color=self.color_data[selection_row][selection_collumn]
        for row in range(len(self.color_data)):
            for collumn in range(len(self.color_data[0])):
                if areColorsSimilar(color, self.color_data[row][collumn], tolerance=tolerance):
                    whole_selection.add((row, collumn))
        if bound:
            while True:
                new_border=set()
                for border_item in border:
                    neighbors=getNeighbors(self.color_data, border_item[0], border_item[1], function_return="indices")
                    for neighbor in neighbors:
                        if not neighbor in selection and neighbor in whole_selection:
                            selection.add(neighbor)
                            new_border.add(neighbor)
                if len(new_border) == 0:
                    break
                border=new_border
        else:
            selection=whole_selection
        return selection

class ColorPallet():
    def __init__(self, values, names=None):
        if names == None:
            names=getColorNames(values)
        self.values=values
        self.names=names

    def updateNames(self):
        self.names=getColorNames(self.values)

# Related to the class Image

def areColorsSimilar(color1, color2, tolerance=0.25):
    """
    Description:
        Tells if two colors are in a given tolerance range of each other. In other words, checks if two colors are alike.
        Returns True or False

    Parameters:
        color1:
            Type: string of a color either in RGB or hexadecimal.
            Description: color to be compared
        color2:
            Type: string of a color either in RGB or hexadecimal.
            Description: color to be compared
        tolerance:
            Type: float between 0 and 1
            Description: Determines how much the two colors must be alike for the function to return True.
    """

    # handling different types of colors
    if color1.__class__ == str:
        rgb_color1=hexadecimalToRgb(color1)
    else:
        rgb_color1=color1
    if color2.__class__ == str:
        rgb_color2=hexadecimalToRgb(color2)
    else:
        rgb_color2=color2

    # tolerance conversion
    # (percentage -> value between 0 and 255)
    tolerance=tolerance*255

    # euclidean distance
    sum=0
    for i in range(3):
        sum+=(rgb_color1[i]-rgb_color2[i])**2
    distance=math.sqrt(sum)

    # deciding similarity
    are_colors_similar=False
    if distance < tolerance:
        are_colors_similar=True

    return are_colors_similar

def getColorData(file_path):
    try:
        with open(file_path, 'rb') as file:
            signature=file.read(8) # Check for the PNG signature
            if signature != b'\x89PNG\r\n\x1a\n':
                raise ValueError("Expected PNG file.")

            chunk_length=int.from_bytes(file.read(4), byteorder='big') # should be 13
            if chunk_length != 13:
                raise ValueError("Expected 13 as the IHDR chunk length.")

            chunk_type=file.read(4) # should be 'IHDR'
            if chunk_type != b'IHDR':
                raise ValueError("Expected IHDR as the first chunk.")

            width=int.from_bytes(file.read(4), byteorder='big')
            height=int.from_bytes(file.read(4), byteorder='big')
            bit_depth=file.read(1)
            color_type=int.from_bytes(file.read(1))
            compression_method=file.read(1)
            filter_method=file.read(1)
            interlace_method=file.read(1)

            file.read(4) # Skip the CRC of the IHDR chunk
            compressed_data=b''
            while True: # Read the chunks until IDAT is found
                chunk_length=int.from_bytes(file.read(4), byteorder='big')
                chunk_type=file.read(4)
                if chunk_type == b'IDAT':
                    compressed_data+=file.read(chunk_length)
                elif chunk_type == b'IEND':
                    break
                else: # Skip the chunk data
                    file.read(chunk_length)
                file.read(4) # Skip the chunk's CRC
            unfiltered_data=zlib.decompress(compressed_data)
        color_data=[]
        color_length=0
        if color_type == 2: # RGB
            color_length=3
        elif color_type == 6: # RGBA
            color_length=4
        else:
            raise ValueError("Expected RGB or RGBA image. Other color types are not supported.")
        filter_types=[]
        for row in range(height):
            row_index=((width*color_length)+1)*row
            filter_type=unfiltered_data[row_index]
            if not filter_type in filter_types:
                filter_types.append(filter_type)
            color_data.append([])
            pixel=[]
            for collumn in range(width):
                for i in range(1, color_length+1):
                    pixel.append(unfiltered_data[row_index+(collumn*color_length)+i])
                if filter_type == 1: # Sub filter
                    if collumn != 0:
                        for color_index in range(color_length):
                            newvalue=color_data[row][collumn-1][color_index]+pixel[color_index]
                            if newvalue > 255:
                                newvalue-=256
                            pixel[color_index]=newvalue
                elif filter_type == 2: # Up filter
                    if row != 0:
                        for color_index in range(color_length):
                            newvalue=color_data[row-1][collumn][color_index]+pixel[color_index]
                            if newvalue > 255:
                                newvalue-=256
                            pixel[color_index]=newvalue
                elif filter_type == 3: # Average filter
                    if row != 0:
                        if collumn != 0:
                            for color_index in range(color_length):
                                newvalue=(color_data[row][collumn-1][color_index]+color_data[row-1][collumn][color_index])//2+pixel[color_index]
                                if newvalue > 255:
                                    newvalue-=256
                                pixel[color_index]=newvalue
                        else:
                            for color_index in range(color_length):
                                newvalue=(color_data[row-1][collumn][color_index])//2+pixel[color_index]
                                if newvalue > 255:
                                    newvalue-=256
                                pixel[color_index]=newvalue
                elif filter_type == 4: # Paeth filter
                    def paethPredictor(left, up, upper_left):
                        predictor=left+up-upper_left
                        pleft=abs(predictor-left)
                        pup=abs(predictor-up)
                        pupper_left=abs(predictor-upper_left)
                        if pleft <= pup and pleft <= pupper_left:
                            return left
                        elif pup <= pupper_left:
                            return up
                        else:
                            return upper_left
                    if row != 0 and collumn != 0:
                        for color_index in range(color_length):
                            newvalue=paethPredictor(color_data[row][collumn-1][color_index], color_data[row-1][collumn][color_index], color_data[row-1][collumn-1][color_index])+pixel[color_index]
                            if newvalue > 255:
                                newvalue-=256
                            pixel[color_index]=newvalue
                color_data[row].append(pixel)
                pixel=[]
        return color_data
    except:
        raise FileNotFoundError(f"{file_path} does not exist.")

def hexadecimalToRgb(hexadecimal):
    """
    Description:
        Converts a hexadecimal color to RGB
        Returns a list of 3 integers representing the rgb values of the given color.

    Parameters:
        hexadecimal:
            Type: string with a hexadecimal value, with or without a hashtag at the beginning (examples: "D87262", "#77C854")
            Description: hexadecimal to be converted to RGB
    """

    rgb=[]
    if hexadecimal[0] == "#": # exclude the hashtag
        hexadecimal=hexadecimal[1:7]
    rgb_value=0
    for i in range(6):
        digit_value=0
        if hexadecimal[i] == "F":
            digit_value=15
        elif hexadecimal[i] == "E":
            digit_value=14
        elif hexadecimal[i] == "D":
            digit_value=13
        elif hexadecimal[i] == "C":
            digit_value=12
        elif hexadecimal[i] == "B":
            digit_value=11
        elif hexadecimal[i] == "A":
            digit_value=10
        else:
            digit_value=int(hexadecimal[i])
        if i % 2 == 0:
            rgb_value=digit_value*16
        else:
            rgb_value+=digit_value
            rgb.append(rgb_value)
    return rgb

def rgbToHexadecimal(rgb):
    hexadecimal="#"
    for i in range(3):
        first_digit=rgb[i]//16
        if first_digit == 15:
            hexadecimal+="F"
        elif first_digit == 14:
            hexadecimal+="E"
        elif first_digit == 13:
            hexadecimal+="D"
        elif first_digit == 12:
            hexadecimal+="C"
        elif first_digit == 11:
            hexadecimal+="B"
        elif first_digit == 10:
            hexadecimal+="A"
        else:
            hexadecimal+=f"{first_digit}"
        last_digit=rgb[i]%16
        if last_digit == 15:
            hexadecimal+="F"
        elif last_digit == 14:
            hexadecimal+="E"
        elif last_digit == 13:
            hexadecimal+="D"
        elif last_digit == 12:
            hexadecimal+="C"
        elif last_digit == 11:
            hexadecimal+="B"
        elif last_digit == 10:
            hexadecimal+="A"
        else:
            hexadecimal+=f"{last_digit}"
    return hexadecimal

def getNeighbors(matrix, row, collumn, function_return="values"):
    neighbors=set()
    if function_return == "values":
        neighbors=[]
        if row-1 >= 0:
            neighbors.append(matrix[row-1][collumn])
        if collumn-1 >= 0:
            neighbors.append(matrix[row][collumn-1])
        if row+1 < len(matrix):
            neighbors.append(matrix[row+1][collumn])
        if collumn+1 < len(matrix[row]):
            neighbors.append(matrix[row][collumn+1])
    else:
        if row-1 >= 0:
            neighbors.add((row-1, collumn))
        if collumn-1 >= 0:
            neighbors.add((row, collumn-1))
        if row+1 < len(matrix):
            neighbors.add((row+1, collumn))
        if collumn+1 < len(matrix[row]):
            neighbors.add((row, collumn+1))
    return tuple(neighbors)

def euclideanDistance(vector1, vector2):
    sum=0
    for i in range(len(vector1)):
        sum+=(vector1[i]-vector2[i])**2
    return math.sqrt(sum)

def getSelectionCenter(selection):
    x=0
    y=0
    total=len(selection)
    for selection_item in selection:
        x+=selection_item[0]
        y+=selection_item[1]
    return int(x/total), int(y/total)

# Related to the class ColorPallet

def getColorNames(values):
    names=[]
    css4_keys=list(mcolors.CSS4_COLORS.keys())
    css4_values=list(mcolors.CSS4_COLORS.values())
    for i in range(len(values)):
        for j in range(len(css4_keys)):
            if values[i] == css4_values[j]:
                names.append(css4_keys[j])
                break
    return names

def getColorValues(names):
    values=[]
    for i in range(len(names)):
        values.append(mcolors.CSS4_COLORS[names[i]])
    return values