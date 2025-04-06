def decode_image(file_path):
    # Get the file content
    try:
        with open(file_path, "rb") as file:
            content = file.read()
    except:
        raise FileNotFoundError(f"{file_path} does not exist.")

    # Get the file type
    if content[:8] == b'\211PNG\r\n\032\n':
        file_type = "png"
    else:
        raise ValueError("Expected PNG file.")

    if file_type == "png":
        # Read chunks
        chunks = []
        chunk_type = b''
        compressed_data = b''
        i = 8
        while chunk_type != b'IEND':
            chunk_length = int.from_bytes(content[i:i+4])
            i += 4
            chunk_type = content[i:i+4].decode('ascii')
            i += 4
            __check_corrupted_chunk(i + chunk_length + 4, len(content))
            chunk_data = content[i:i+chunk_length]
            i += chunk_length
            chunk_crc = content[i:i+4]
            i += 4

            # [0]=length, [1]=type, [2]=data, [3]=crc
            chunk = [chunk_length, chunk_type, chunk_data, chunk_crc]
            chunks.append(chunk)

            if chunk_type == "IHDR":
                width = int.from_bytes(chunk_data[0:4])
                height = int.from_bytes(chunk_data[4:8])
                bit_depth = int.from_bytes(chunk_data[8])
                color_type = int.from_bytes(chunk_data[9])
                compression = int.from_bytes(chunk_data[10])
                filter_method = int.from_bytes(chunk_data[11])
                interlace = int.from_bytes(chunk_data[12])

            if chunk_type == "IDAT":
                compressed_data += chunk_data
        if color_type == 0:
            num_channels = 1
        elif color_type == 2:
            num_channels = 3
        elif color_type == 3:
            num_channels = 1
        elif color_type == 4:
            num_channels = 2
        elif color_type == 6:
            num_channels = 4
        if interlace == 0:
            if filter_method == 0:


def __check_corrupted_chunk(chunk_end, content_length):
    if chunk_end > content_length:
        raise ValueError("Corrupted PNG: chunk extends beyond file end.")