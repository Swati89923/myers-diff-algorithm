import sys


def myers(a, b):
    """
    Linear-space Myers diff (paper section 4b: middle snake + divide and conquer).

    Returns (del_a, ins_b): bytearrays of 0/1 flags.
      del_a[i] == 1  -> a[i] is deleted
      ins_b[j] == 1  -> b[j] is inserted
    Lines not flagged are kept (they pair up in order).
    """
    n, m = len(a), len(b)
    del_a = bytearray(n)
    ins_b = bytearray(m)

    # Two V arrays, allocated once and reused by every sub-problem.
    # vf[o + k] = furthest x on diagonal k (k = x - y) going forward from the start.
    # vb[o + k] = same, but going backward from the end (reversed coordinates).
    size = (n + m + 1) // 2 + 2
    o = size
    vf = [0] * (2 * size + 1)
    vb = [0] * (2 * size + 1)

    stack = [(0, n, 0, m)]
    while stack:
        alo, ahi, blo, bhi = stack.pop()

        # Strip common prefix and suffix (free snakes).
        while alo < ahi and blo < bhi and a[alo] == b[blo]:
            alo += 1
            blo += 1
        while alo < ahi and blo < bhi and a[ahi - 1] == b[bhi - 1]:
            ahi -= 1
            bhi -= 1

        if alo == ahi:                       # only insertions remain
            for j in range(blo, bhi):
                ins_b[j] = 1
            continue
        if blo == bhi:                       # only deletions remain
            for i in range(alo, ahi):
                del_a[i] = 1
            continue

        # ---- find the middle snake of this sub-problem ----
        N = ahi - alo
        M = bhi - blo
        delta = N - M
        odd = delta & 1
        vf[o + 1] = 0
        vb[o + 1] = 0
        found = None

        for d in range((N + M + 1) // 2 + 1):
            # forward wavefront
            for i in range(o - d, o + d + 1, 2):     # i = o + k
                k = i - o
                if k == -d or (k != d and vf[i - 1] < vf[i + 1]):
                    x = vf[i + 1]                # move down  (insert)
                else:
                    x = vf[i - 1] + 1            # move right (delete)
                y = x - k
                xs, ys = x, y
                while x < N and y < M and a[alo + x] == b[blo + y]:
                    x += 1
                    y += 1
                vf[i] = x
                if odd and delta - (d - 1) <= k <= delta + (d - 1):
                    if x + vb[o + delta - k] >= N:
                        # snake (xs,ys) -> (x,y)
                        found = (alo + xs, blo + ys, alo + x, blo + y)
                        break
            if found:
                break
            # backward wavefront (reversed coordinates)
            for i in range(o - d, o + d + 1, 2):
                k = i - o
                if k == -d or (k != d and vb[i - 1] < vb[i + 1]):
                    x = vb[i + 1]
                else:
                    x = vb[i - 1] + 1
                y = x - k
                xs, ys = x, y
                while x < N and y < M and a[ahi - 1 - x] == b[bhi - 1 - y]:
                    x += 1
                    y += 1
                vb[i] = x
                if not odd and -d <= delta - k <= d:
                    if x + vf[o + delta - k] >= N:
                        # snake in forward coordinates: (N-x,M-y) -> (N-xs,M-ys)
                        found = (ahi - x, bhi - y, ahi - xs, bhi - ys)
                        break
            if found:
                break

        sx, sy, ex, ey = found
        stack.append((alo, sx, blo, sy))     # before the snake
        stack.append((ex, ahi, ey, bhi))     # after the snake

    return del_a, ins_b


def read_lines(path):
    with open(path, "rb") as f:
        lines = f.read().split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def flags_to_ranges(flags):
    """0/1 flags per character -> 'start-end,start-end' (merged), or '.'."""
    parts = []
    i, n = 0, len(flags)
    while i < n:
        if flags[i]:
            s = i
            while i < n and flags[i]:
                i += 1
            parts.append(f"{s}-{i}")
        else:
            i += 1
    return ",".join(parts) if parts else "."


def character_highlight(old_text, new_text):
    d, ins = myers(old_text, new_text)       # str indexes by code point
    return f"? {flags_to_ranges(d)} | {flags_to_ranges(ins)}"


def print_diff(a, b, highlight):
    del_a, ins_b = myers(a, b)
    n, m = len(a), len(b)
    out = sys.stdout.buffer
    i = j = 0
    while i < n or j < m:
        # length of the run of KEEP lines starting here:
        # bytearray.find locates the next flagged line at C speed
        nd = del_a.find(1, i) if i < n else -1
        ni = ins_b.find(1, j) if j < m else -1
        run = min((n if nd < 0 else nd) - i, (m if ni < 0 else ni) - j)
        if run > 0:
            out.write(b" " + b"\n ".join(a[i:i + run]) + b"\n")
            i += run
            j += run
            continue
        # one change block: all deletes first, then all inserts
        dels = []
        while i < n and del_a[i]:
            dels.append(a[i])
            i += 1
        ins = []
        while j < m and ins_b[j]:
            ins.append(b[j])
            j += 1
        for line in dels:
            out.write(b"-" + line + b"\n")
        for t, line in enumerate(ins):
            out.write(b"+" + line + b"\n")
            if highlight and t < len(dels):
                h = character_highlight(dels[t].decode("utf-8"), line.decode("utf-8"))
                out.write(h.encode("utf-8") + b"\n")


def main():
    if len(sys.argv) != 4:
        print("Usage: main.py lines A B OR main.py highlight A B", file=sys.stderr)
        return 2
    command, file_a, file_b = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        a = read_lines(file_a)
        b = read_lines(file_b)
    except OSError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 2
    try:
        if command == "lines":
            print_diff(a, b, False)
        elif command == "highlight":
            print_diff(a, b, True)
        else:
            print("Unknown command. Use lines or highlight.", file=sys.stderr)
            return 2
        sys.stdout.buffer.flush()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())