def gen_mask(length: int):
    if not (0 <= length <= 32):
        raise ValueError("Mask length must be between 0 and 32.")

    # Create a 32-bit binary string with `mask_length` ones followed by zeros
    binary_mask = '1' * length + '0' * (32 - length)

    # Split the binary string into 8-bit chunks and convert each to decimal
    subnet_mask = [
        str(int(binary_mask[i:i + 8], 2)) for i in range(0, 32, 8)
    ]

    return '.'.join(subnet_mask)
