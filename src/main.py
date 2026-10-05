import sys
from array import array

def myers_diff(a, b):
    """
    Myers shortest edit script.

    Returns:
        ("keep", value)
        ("delete", value)
        ("insert", value)
    """

    n = len(a)
    m = len(b)

    if n == 0:
        return [("insert", x) for x in b]

    if m == 0:
        return [("delete", x) for x in a]

    max_d = n + m
    offset = max_d + 1

    # V[k] = furthest x reached on diagonal k.
    # A list is much more memory-efficient than a dictionary.
    v = [0] * (2 * max_d + 3)

    # Store only the reachable diagonals for each D.
    # Each value is stored as a compact 32-bit integer.
    trace = []

    for d in range(max_d + 1):

        for k in range(-d, d + 1, 2):

            idx = k + offset

            # Choose insertion or deletion.
            if k == -d or (
                k != d
                and v[idx - 1] < v[idx + 1]
            ):
                # insertion
                x = v[idx + 1]
            else:
                # deletion
                x = v[idx - 1] + 1

            y = x - k

            # Follow the snake.
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[idx] = x

            # Reached the end.
            if x >= n and y >= m:
                trace.append(
                    array(
                        "i",
                        [v[offset + kk]
                         for kk in range(-d, d + 1, 2)]
                    )
                )
                return _backtrack(trace, a, b)

        # Store only valid diagonals:
        # -d, -d+2, ..., d
        trace.append(
            array(
                "i",
                [v[offset + kk]
                 for kk in range(-d, d + 1, 2)]
            )
        )

    return []


def _trace_value(trace, d, k):
    """
    Get V[k] from the compact trace.

    At depth d, only:
        -d, -d+2, ..., d
    are stored.
    """

    if d < 0 or d >= len(trace):
        return 0

    if abs(k) > d:
        return 0

    # Convert diagonal k to compact array index.
    index = (k + d) // 2

    return trace[d][index]


def _backtrack(trace, a, b):
    """Reconstruct the shortest edit script."""

    x = len(a)
    y = len(b)

    result = []

    # Walk backwards through the edit graph.
    for d in range(len(trace) - 1, 0, -1):

        k = x - y

        # Look at the previous D layer.
        previous_d = d - 1

        # Decide whether previous move was insertion or deletion.
        if k == -d or (
            k != d
            and _trace_value(
                trace,
                previous_d,
                k - 1
            )
            < _trace_value(
                trace,
                previous_d,
                k + 1
            )
        ):
            # Previous move was insertion.
            previous_k = k + 1

        else:
            # Previous move was deletion.
            previous_k = k - 1

        previous_x = _trace_value(
            trace,
            previous_d,
            previous_k
        )

        previous_y = previous_x - previous_k

        # Walk backwards through the snake.
        while x > previous_x and y > previous_y:
            result.append(("keep", a[x - 1]))
            x -= 1
            y -= 1

        if x == previous_x:
            # Insertion.
            result.append(("insert", b[y - 1]))
            y -= 1

        else:
            # Deletion.
            result.append(("delete", a[x - 1]))
            x -= 1

    # Remaining common prefix.
    while x > 0 and y > 0:
        result.append(("keep", a[x - 1]))
        x -= 1
        y -= 1

    while x > 0:
        result.append(("delete", a[x - 1]))
        x -= 1

    while y > 0:
        result.append(("insert", b[y - 1]))
        y -= 1

    result.reverse()

    return result


def normalize_change_blocks(ops):
    """
    The assignment requires:
    all '-' lines before all '+' lines
    inside every change block.
    """

    result = []
    i = 0

    while i < len(ops):

        if ops[i][0] == "keep":
            result.append(ops[i])
            i += 1
            continue

        # Collect one complete change block.
        deletes = []
        inserts = []

        while i < len(ops) and ops[i][0] != "keep":
            if ops[i][0] == "delete":
                deletes.append(ops[i][1])
            else:
                inserts.append(ops[i][1])
            i += 1

        # Delete-first rule.
        for value in deletes:
            result.append(("delete", value))

        for value in inserts:
            result.append(("insert", value))

    return result


def read_lines(path):
    """
    Read raw bytes exactly as required by the assignment.

    Split on b'\\n'.
    Remove final empty piece.
    Keep b'\\r' if present.
    """

    with open(path, "rb") as f:
        data = f.read()

    lines = data.split(b"\n")

    if lines and lines[-1] == b"":
        lines.pop()

    return lines


def print_lines_diff(a, b):
    ops = myers_diff(a, b)
    ops = normalize_change_blocks(ops)

    out = sys.stdout.buffer

    for operation, value in ops:

        if operation == "keep":
            out.write(b" " + value + b"\n")

        elif operation == "delete":
            out.write(b"-" + value + b"\n")

        else:
            out.write(b"+" + value + b"\n")


def ranges_to_string(positions):
    """Convert character positions to merged start-end ranges."""

    if not positions:
        return "."

    positions = sorted(positions)

    ranges = []

    start = positions[0]
    previous = positions[0]

    for p in positions[1:]:

        if p == previous + 1:
            previous = p
        else:
            ranges.append((start, previous + 1))
            start = p
            previous = p

    ranges.append((start, previous + 1))

    return ",".join(f"{s}-{e}" for s, e in ranges)


def character_highlight(old_line, new_line):
    """
    Find minimum changed character ranges using Myers again.
    """

    old_chars = list(old_line)
    new_chars = list(new_line)

    ops = myers_diff(old_chars, new_chars)
    ops = normalize_change_blocks(ops)

    old_positions = []
    new_positions = []

    old_index = 0
    new_index = 0

    for operation, value in ops:

        if operation == "keep":
            old_index += 1
            new_index += 1

        elif operation == "delete":
            old_positions.append(old_index)
            old_index += 1

        else:
            new_positions.append(new_index)
            new_index += 1

    old_ranges = ranges_to_string(old_positions)
    new_ranges = ranges_to_string(new_positions)

    return f"? {old_ranges} | {new_ranges}"


def print_highlight(a, b):
    ops = myers_diff(a, b)
    ops = normalize_change_blocks(ops)

    out = sys.stdout.buffer

    i = 0

    while i < len(ops):

        # Keep line.
        if ops[i][0] == "keep":
            out.write(b" " + ops[i][1] + b"\n")
            i += 1
            continue

        # One change block.
        deletes = []
        inserts = []

        while i < len(ops) and ops[i][0] != "keep":

            if ops[i][0] == "delete":
                deletes.append(ops[i][1])
            else:
                inserts.append(ops[i][1])

            i += 1

        # Print all deletions first.
        for line in deletes:
            out.write(b"-" + line + b"\n")

        # Pair 1st delete with 1st insert, etc.
        pair_count = min(len(deletes), len(inserts))

        for j, line in enumerate(inserts):

            out.write(b"+" + line + b"\n")

            if j < pair_count:
                old_text = deletes[j].decode("utf-8")
                new_text = line.decode("utf-8")

                highlight = character_highlight(
                    old_text,
                    new_text
                )

                out.write(highlight.encode("utf-8") + b"\n")


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: main.py lines A B OR main.py highlight A B",
            file=sys.stderr
        )
        return 2

    command = sys.argv[1]
    file_a = sys.argv[2]
    file_b = sys.argv[3]

    try:
        a = read_lines(file_a)
        b = read_lines(file_b)

    except (OSError, IOError) as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 2

    try:
        if command == "lines":
            print_lines_diff(a, b)

        elif command == "highlight":
            print_highlight(a, b)

        else:
            print(
                "Unknown command. Use lines or highlight.",
                file=sys.stderr
            )
            return 2

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())