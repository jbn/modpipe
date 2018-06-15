def _encode_as_binary(x):  # Not in pipeline by default!
    return bin(x)[2:].rjust(32, '0')


def convert_seeds(seeds):
    return [_encode_as_binary(seed) for seed in seeds]
