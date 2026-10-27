"""Fixed-width models and independently checkable bit algorithms."""
MASK64 = (1 << 64) - 1
H64 = 0x8080808080808080
L64 = 0x0101010101010101


def ctz(x, width):
    x &= (1 << width) - 1
    return width if x == 0 else (x & -x).bit_length() - 1


def popcount64(x):
    x &= MASK64
    x -= (x >> 1) & 0x5555555555555555
    x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F0F0F0F0F
    return ((x * L64) & MASK64) >> 56


def reverse_bits(x, width):
    assert width > 0 and width & (width - 1) == 0
    mask = (1 << width) - 1
    x &= mask
    shift = 1
    while shift < width:
        low = sum(((1 << shift) - 1) << k
                  for k in range(0, width, 2 * shift))
        x = ((x >> shift) & low) | ((x & low) << shift)
        shift *= 2
    return x & mask


def delta_swap(x, distance, low_mask):
    # Caller guarantees selected pairs do not overlap.
    t = (x ^ (x >> distance)) & low_mask
    return x ^ t ^ (t << distance)


def transpose8(x):
    # Bit 8*r+c is matrix entry (r,c).
    x &= MASK64
    for distance, mask in [(7, 0x00AA00AA00AA00AA),
                           (14, 0x0000CCCC0000CCCC),
                           (28, 0x00000000F0F0F0F0)]:
        x = delta_swap(x, distance, mask)
    return x


def extract_bits(x, mask):
    assert mask >= 0
    result, destination = 0, 1
    while mask:
        bit = mask & -mask
        if x & bit:
            result |= destination
        destination <<= 1
        mask &= mask - 1
    return result


def add_bytes64(x, y):
    x, y = x & MASK64, y & MASK64
    top = (x ^ y) & H64
    return (((x & ~H64) + (y & ~H64)) ^ top) & MASK64


def zero_byte_flags(x, width=64):
    assert width > 0 and width % 8 == 0
    mask = (1 << width) - 1
    low = sum(1 << k for k in range(0, width, 8))
    high = low << 7
    x &= mask
    return ((x - low) & ~x & high) & mask


def exact_zero_byte_flags(x, width=64):
    assert width > 0 and width % 8 == 0
    mask = (1 << width) - 1
    low = sum(1 << k for k in range(0, width, 8))
    high = low << 7
    x &= mask
    return high & ~(x | ((x | high) - low))


def reachable(successors, start):
    universe = (1 << len(successors)) - 1
    seen, done = start & universe, 0
    while seen & ~done:
        bit = (seen & ~done) & -(seen & ~done)
        v = bit.bit_length() - 1
        done |= bit
        seen |= successors[v] & universe
    return seen


def select_word(select, a, b, width=64):
    mask = (1 << width) - 1
    select_mask = (-int(bool(select))) & mask
    return (a ^ ((a ^ b) & select_mask)) & mask


if __name__ == '__main__':
    for x in range(1 << 16):
        assert popcount64(x) == x.bit_count()
        assert reverse_bits(x, 16) == int(f'{x:016b}'[::-1], 2)
        expected = sum(0x80 << (8 * k) for k in range(2)
                       if ((x >> (8 * k)) & 255) == 0)
        assert bool(zero_byte_flags(x, 16)) == bool(expected)
        assert exact_zero_byte_flags(x, 16) == expected
    assert zero_byte_flags(0x0100, 16) == 0x8080
    assert exact_zero_byte_flags(0x0100, 16) == 0x0080
    assert reachable([0b0010, 0b0100, 0b1000, 0], 1) == 15
    print('all 65536 unsigned 16-bit inputs: passed')
